import asyncio
import functools
from typing import Awaitable, Callable, Optional

from pkm_trade_spoofer import logger
from pkm_trade_spoofer.backend.bgb.bgb_link_server import BGBLinkCableServer
from pkm_trade_spoofer.models import Party
from pkm_trade_spoofer.trading_state_machine import (
    NotConnectedState,
    TradeStateMachineContext,
    TradingPokemonStateMachine,
)

LOGGER = logger.get_logger(__name__)


class BGBBackend(object):
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._server = BGBLinkCableServer(
            host=host,
            port=port,
            loop=loop,
            blocking=False,
        )

    async def start(self, party: Party) -> None:
        await self._server.run(
            functools.partial(self._master_data_handler_state_machine, party),
        )

    def stop(self) -> None:
        self._server.stop()

    async def _master_data_handler_state_machine(
        self,
        party: Party,
        reader: asyncio.Queue[int],
        writer: Callable[[int], Awaitable[None]],
    ) -> None:
        ctx = TradeStateMachineContext(
            reader=reader,
            writer=writer,
            pkm_party=party,
        )

        state_machine = TradingPokemonStateMachine(
            initial_state=NotConnectedState(),
            context=ctx,
        )

        await state_machine()
