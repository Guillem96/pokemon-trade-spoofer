import asyncio
import enum
import logging
import sys
from pathlib import Path
from typing import Any

from bgb_link_server import BGBLinkCableServer
from models import EVs, Party
from pokemon import pokemon_by_id
from trading_state_machine import NotConnectedState, TradingPokemonStateMachine, Context

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stdout_formatter = logging.Formatter(
    "[%(levelname)s] - %(asctime)s - %(name)s: %(message)s",
    "%Y-%m-%d %H:%M:%S",
)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(stdout_formatter)
logger.addHandler(stdout_handler)
LOG_FILE = Path("log.csv").open("w")

# GameBoy "Magic" Packets
MASTER_MAGIC = 0x01
SLAVE_MAGIC = 0x02
CONNECTED_MAGIC = 0x61
TERMINATOR_MAGIC = 0xFD
IN_TRADE_ROOM_MAGIC = 0xD1
FIRST_POKEMON_MAGIC = 0x70
LAST_POKEMON_MAGIC = 0x75
CANCEL_MAGIC = 0x71
CONFIRM_MAGIC = 0x72


class TradingState(enum.Enum):
    NOT_CONNECTED = "NOT_CONNECTED"
    WAITING_FOR_SELECTION = "WAITING_FOR_SELECTION"
    WAITING_IN_TRADE_ROOM = "WAITING_IN_TRADE_ROOM"
    WAITING_FOR_RANDOM_SEED = "WAITING_FOR_RANDOM_SEED"
    SENDING_RANDOM_SEED = "SENDING_RANDOM_SEED"
    GETTING_POKEMON_TEAM = "GETTING_POKEMON_TEAM"

    SELECTING_POKEMON = "SELECTING_POKEMON"

    WAITING_FOR_TRADE_CONFIRMATION = "WAITING_FOR_TRADE_CONFIRMATION"
    TRADE_INITIATED = "TRADE_INITIATED"

    WAITING_FOR_TERMINATOR = "WAITING_FOR_TERMINATOR"
    WAITING_FOR = "WAITING_FOR"


# Trading state machine state
STATUS = TradingState.NOT_CONNECTED
NEXT_STATUS = TradingState.NOT_CONNECTED
WAIT_FOR_VALUE = 0
SEND_MEANWHILE = None
PARTY = Party(
    trainer_name="GOLD",
    pokemon=[
        pokemon_by_id(1, ivs=EVs(15, 15, 15, 15, 15)),
        pokemon_by_id(4, ivs=EVs(15, 15, 15, 15, 15)),
        pokemon_by_id(7, ivs=EVs(15, 15, 15, 15, 15)),
        pokemon_by_id(151, ivs=EVs(15, 15, 15, 15, 15)),
        pokemon_by_id(150, ivs=EVs(15, 15, 15, 15, 15)),
        pokemon_by_id(251, ivs=EVs(15, 15, 15, 15, 15)),
    ],
    ots_names=["GOLD", "GOLD", "GOLD", "GOLD", "GOLD", "GOLD"],
    pokemon_nicknames=["Bulbasaur", "Charmander", "Squirtle", "Gatito", "Gato", "Hoja"],
).serialize()
other_sends = 0
buffer: list[int] = []
buffer_idx = 0


def main():
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(_exception_handler)

    server = BGBLinkCableServer(verbose=True, host="127.0.0.1", port=9999, loop=loop)

    try:
        # server.run(master_data_handler)
        server.run(master_data_handler_state_machine)
    except KeyboardInterrupt:
        print("Stopping server with CTRL+C")
    finally:
        print("Graceful shutdown...")
        server.stop()
        loop.close()
        LOG_FILE.close()


async def master_data_handler_state_machine(reader, writer) -> None:
    ctx = Context(reader=reader, writer=writer, pkm_party=Party.from_bytes(PARTY))
    state_machine = TradingPokemonStateMachine(initial_state=NotConnectedState(), context=ctx)
    await state_machine()


async def master_data_handler(reader, writer) -> None:
    global STATUS, NEXT_STATUS, buffer_idx, PARTY, buffer, WAIT_FOR_VALUE, SEND_MEANWHILE, other_sends

    while True:
        data = await reader.get()
        to_send = data

        if STATUS == TradingState.WAITING_FOR_TERMINATOR:
            if data != TERMINATOR_MAGIC:
                STATUS = NEXT_STATUS

        if STATUS == TradingState.WAITING_FOR:
            to_send = SEND_MEANWHILE or data
            if data != WAIT_FOR_VALUE:
                STATUS = NEXT_STATUS

        if STATUS == TradingState.NOT_CONNECTED:
            to_send = _handle_not_connected(data)

        elif STATUS == TradingState.WAITING_FOR_SELECTION:
            if data == IN_TRADE_ROOM_MAGIC:
                STATUS = TradingState.WAITING_IN_TRADE_ROOM

        elif STATUS == TradingState.WAITING_IN_TRADE_ROOM:
            if data == TERMINATOR_MAGIC:
                STATUS = TradingState.WAITING_FOR_TERMINATOR
                NEXT_STATUS = TradingState.SENDING_RANDOM_SEED

        elif STATUS == TradingState.SENDING_RANDOM_SEED:
            if data == TERMINATOR_MAGIC:
                STATUS = TradingState.WAITING_FOR_TERMINATOR
                NEXT_STATUS = TradingState.GETTING_POKEMON_TEAM
                buffer.clear()
                buffer_idx = 0

        elif STATUS == TradingState.GETTING_POKEMON_TEAM:
            if len(buffer) < 11 + 10 + 48 * 6 + 11 * 6 * 2:
                buffer.append(data)
                to_send = PARTY[buffer_idx]
                buffer_idx += 1
            elif data == TERMINATOR_MAGIC:
                STATUS = TradingState.WAITING_FOR_TERMINATOR
                NEXT_STATUS = TradingState.SELECTING_POKEMON

        elif STATUS == TradingState.SELECTING_POKEMON:
            if data == 0x7F:
                STATUS = TradingState.WAITING_FOR
                SEND_MEANWHILE = None
                WAIT_FOR_VALUE = 0x7F
                NEXT_STATUS = TradingState.WAITING_IN_TRADE_ROOM

            elif data >= FIRST_POKEMON_MAGIC and data <= LAST_POKEMON_MAGIC:
                to_send = FIRST_POKEMON_MAGIC
                other_sends = data - FIRST_POKEMON_MAGIC
                STATUS = TradingState.WAITING_FOR
                SEND_MEANWHILE = FIRST_POKEMON_MAGIC
                WAIT_FOR_VALUE = data
                NEXT_STATUS = TradingState.WAITING_FOR_TRADE_CONFIRMATION

        elif STATUS == TradingState.WAITING_FOR_TRADE_CONFIRMATION:
            if data == CANCEL_MAGIC:
                STATUS = TradingState.WAITING_FOR
                WAIT_FOR_VALUE = CANCEL_MAGIC
                SEND_MEANWHILE = CANCEL_MAGIC
                NEXT_STATUS = TradingState.SELECTING_POKEMON
                STATUS = TradingState.SELECTING_POKEMON

            elif data == CONFIRM_MAGIC:
                STATUS = TradingState.WAITING_FOR
                WAIT_FOR_VALUE = CONFIRM_MAGIC
                SEND_MEANWHILE = CONFIRM_MAGIC
                NEXT_STATUS = TradingState.TRADE_INITIATED

        elif STATUS == TradingState.TRADE_INITIATED:
            if data == TERMINATOR_MAGIC:
                STATUS = TradingState.WAITING_FOR_TERMINATOR
                NEXT_STATUS = TradingState.SENDING_RANDOM_SEED

                other_party = Party.from_bytes(bytearray(buffer))

                my_party = Party.from_bytes(PARTY)
                my_party.pokemon[0] = other_party.pokemon[other_sends]
                my_party.ots_names[0] = other_party.ots_names[other_sends]
                my_party.pokemon_nicknames[0] = other_party.pokemon_nicknames[
                    other_sends
                ]

                PARTY = my_party.serialize()
                buffer.clear()
                buffer_idx = 0

        if STATUS == TradingState.WAITING_FOR:
            LOG_FILE.write(
                f"0x{data:02x},0x{to_send:02x},{STATUS.value}(0x{WAIT_FOR_VALUE:02x})\n",
            )
        else:
            LOG_FILE.write(f"0x{data:02x},0x{to_send:02x},{STATUS.value}\n")

        LOG_FILE.flush()

        await writer(to_send)


def _handle_not_connected(data):
    global STATUS

    if data == MASTER_MAGIC:
        return SLAVE_MAGIC

    if data == CONNECTED_MAGIC:
        STATUS = TradingState.WAITING_FOR_SELECTION
        return CONNECTED_MAGIC

    return data


def _exception_handler(loop: asyncio.AbstractEventLoop, ctx: dict[str, Any]) -> None:
    # Log the exception and stop the asyncio loop
    logger.error("Unexpected exception received, stopping the event loop...")
    logger.exception(ctx.get("exception"))
    loop.stop()


if __name__ == "__main__":
    main()
