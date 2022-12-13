import abc
import asyncio
import pathlib
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from models import Party

_MASTER_MAGIC = 0x01
_SLAVE_MAGIC = 0x02
_CONNECTED_MAGIC = 0x61
_TERMINATOR_MAGIC = 0xFD
_IN_TRADE_ROOM_MAGIC = 0xD1
_FIRST_POKEMON_MAGIC = 0x70
_LAST_POKEMON_MAGIC = 0x75
_EXIT_SELECTION_MAGIC = 0x7F
_CANCEL_MAGIC = 0x71
_CONFIRM_MAGIC = 0x72

LOG_FILE = pathlib.Path("log.csv").open("w")

@dataclass
class Context:
    reader: asyncio.Queue[int]
    writer: Callable[[int], Awaitable[None]]
    pkm_party: Party
    other_pkm_party: Optional[Party] = None
    me_sends: Optional[int] = None
    other_sends: Optional[int] = None


class State(abc.ABC):
    @abc.abstractmethod
    async def run(self, ctx: Context) -> Optional["State"]:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        return repr(self)


class TradingPokemonStateMachine(object):
    def __init__(self, initial_state: "State", context: Context) -> None:
        self._initial_state = initial_state
        self._context = context

    async def __call__(self) -> None:
        prev_state = self._initial_state
        next_state = await self._initial_state.run(self._context)
        if prev_state is not next_state:
            print(f"Switching state from {prev_state} to {next_state}")

        while next_state is not None:
            prev_state = next_state
            next_state = await next_state.run(self._context)
            if prev_state is not next_state:
                print(f"Switching state from {prev_state} to {next_state}")


class NotConnectedState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        data = await ctx.reader.get()
        ctx.reader.task_done()
        if data == _MASTER_MAGIC:
            await ctx.writer(_SLAVE_MAGIC)
            LOG_FILE.write(f"0x{data:02x},0x{_SLAVE_MAGIC:02x},{self}\n")

        elif data == _SLAVE_MAGIC:
            await ctx.writer(_MASTER_MAGIC)
            LOG_FILE.write(f"0x{data:02x},0x{_MASTER_MAGIC:02x},{self}\n")

        elif data == _CONNECTED_MAGIC:
            await ctx.writer(_CONNECTED_MAGIC)
            LOG_FILE.write(f"0x{data:02x},0x{_CONNECTED_MAGIC:02x},{self}\n")
            return WaitForState(_IN_TRADE_ROOM_MAGIC, next_state=InTradeRoomState())
        
        # echo
        await ctx.writer(data)
        LOG_FILE.write(f"0x{data:02x},0x{data:02x},{self}\n")

        return self


class InTradeRoomState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        return WaitForState(_TERMINATOR_MAGIC, next_state=SendingRandomSeedState())


class SendingRandomSeedState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        return WaitForState(
            _TERMINATOR_MAGIC, 
            next_state=InterchangePokemonTeamsState(),
        )


class InterchangePokemonTeamsState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        other_party_bs = []
        for pb in ctx.pkm_party.serialize():
            opb = await ctx.reader.get()
            other_party_bs.append(opb)
            await ctx.writer(pb)
            LOG_FILE.write(f"0x{opb:02x},0x{pb:02x},{self}\n")
            ctx.reader.task_done()

        ctx.other_pkm_party = Party.from_bytes(other_party_bs)

        return WaitWhileState(_TERMINATOR_MAGIC, next_state=SelectingPokemonState())


class SelectingPokemonState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        data = await ctx.reader.get()
        if data >= _FIRST_POKEMON_MAGIC and data <= _LAST_POKEMON_MAGIC:
            ctx.me_sends = random.choice(list(range(len(ctx.pkm_party.pokemon))))
            await ctx.writer(ctx.me_sends + _FIRST_POKEMON_MAGIC)
            LOG_FILE.write(f"0x{data:02x},0x{ctx.me_sends + _FIRST_POKEMON_MAGIC:02x},{self}\n")

            ctx.reader.task_done()
            ctx.other_sends = data - _FIRST_POKEMON_MAGIC
            return WaitWhileState(
                data,
                echo_value=ctx.me_sends + _FIRST_POKEMON_MAGIC,
                next_state=WaitingTradeConfirmState(),
            )

        if data == _EXIT_SELECTION_MAGIC:
            await ctx.writer(_EXIT_SELECTION_MAGIC)
            ctx.reader.task_done()
            return WaitWhileState(data, next_state=InTradeRoomState())

        # echo
        LOG_FILE.write(f"0x{data:02x},0x{data:02x},{self}\n")

        await ctx.writer(data)

        ctx.reader.task_done()
        return self


class WaitingTradeConfirmState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        data = await ctx.reader.get()
        if data == _CANCEL_MAGIC:
            await ctx.writer(_CANCEL_MAGIC)
            LOG_FILE.write(f"0x{data:02x},0x{_CANCEL_MAGIC:02x},{self}\n")
            return WaitWhileState(
                _CANCEL_MAGIC,
                echo_value=_CANCEL_MAGIC,
                next_state=SelectingPokemonState(),
            )

        if data == _CONFIRM_MAGIC:
            await ctx.writer(_CONFIRM_MAGIC)
            LOG_FILE.write(f"0x{data:02x},0x{_CONFIRM_MAGIC:02x},{self}\n")
            return WaitWhileState(
                _CONFIRM_MAGIC,
                echo_value=_CONFIRM_MAGIC,
                next_state=TradingPokemonState(),
            )

        LOG_FILE.write(f"0x{data:02x},0x{data:02x},{self}\n")
        ctx.reader.task_done()
        await ctx.writer(data)
        return self


class TradingPokemonState(State):
    async def run(self, ctx: Context) -> Optional[State]:
        data = await ctx.reader.get()
        await ctx.writer(data)
        ctx.reader.task_done()

        if data == _TERMINATOR_MAGIC:
            if ctx.me_sends is None:
                raise ValueError("ctx.me_sends cannot be None in TradingPokemonState.")

            if ctx.other_sends is None:
                raise ValueError(
                    "ctx.other_sends cannot be None in TradingPokemonState.",
                )

            if ctx.other_pkm_party is None:
                raise ValueError(
                    "ctx.other_pkm_party cannot be None in TradingPokemonState.",
                )

            ctx.pkm_party.pokemon[ctx.me_sends] = ctx.other_pkm_party.pokemon[
                ctx.other_sends
            ]
            ctx.pkm_party.pokemon_nicknames[
                ctx.me_sends
            ] = ctx.other_pkm_party.pokemon_nicknames[ctx.other_sends]
            ctx.pkm_party.ots_names[ctx.me_sends] = ctx.other_pkm_party.ots_names[
                ctx.other_sends
            ]

            # Restart context data
            ctx.me_sends = None
            ctx.other_pkm_party = None
            ctx.other_pkm_party = None

            return WaitWhileState(
                _TERMINATOR_MAGIC, next_state=SendingRandomSeedState(),
            )

        return self


class WaitForState(State):
    def __init__(
        self,
        wait_for_value: int,
        next_state: State,
        echo_value: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.wait_for_value = wait_for_value
        self.next_state = next_state
        self.echo_value = echo_value

    async def run(self, ctx: Context) -> Optional[State]:
        value = await ctx.reader.get()
        await ctx.writer(value if self.echo_value is None else self.echo_value)
        
        LOG_FILE.write(f"0x{value:02x},0x{value if self.echo_value is None else self.echo_value:02x},{self}\n")

        ctx.reader.task_done()

        # If value is different from `wait_while_value` do not pop it
        # and move to the next state
        if value == self.wait_for_value:
            return WaitWhileState(self.wait_for_value, self.next_state, self.echo_value)

        # Echo
        return self

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"wait_for_value=0x{self.wait_for_value:02x},"
            f"next_state={self.next_state},"
            f"echo_value={self.echo_value})")


class WaitWhileState(State):
    def __init__(
        self,
        wait_while_value: int,
        next_state: State,
        echo_value: Optional[int] = None,
        delay: float = 0.001,
    ) -> None:
        super().__init__()
        self.wait_while_value = wait_while_value
        self.next_state = next_state
        self.delay = delay
        self.echo_value = echo_value

    async def run(self, ctx: Context) -> Optional[State]:
        if ctx.reader.empty():
            await asyncio.sleep(self.delay)
            return self

        # Hack to peek a value
        value = ctx.reader._queue[0] # type: ignore

        # echo
        await ctx.writer(value if self.echo_value is None else self.echo_value)
        LOG_FILE.write(f"0x{value:02x},0x{value if self.echo_value is None else self.echo_value:02x},{self}\n")

        # If value is different from `wait_while_value` do not pop it
        # and move to the next state
        if value != self.wait_while_value:
            return self.next_state

        # Consume the value from the reader
        ctx.reader.get_nowait()
        ctx.reader.task_done()

        # Echo same value
        return self

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"wait_while_value=0x{self.wait_while_value:02x}, "
            f"next_state={self.next_state}, "
            f"echo_value={self.echo_value})")
