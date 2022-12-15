import asyncio
import logging
import signal
from typing import Any

import typer

from pkm_trade_spoofer import logger
from pkm_trade_spoofer.bgb_link_server import BGBLinkCableServer
from pkm_trade_spoofer.models import EVs, Party
from pkm_trade_spoofer.pokemon import pokemon_by_id
from pkm_trade_spoofer.trading_state_machine import (
    NotConnectedState,
    TradeStateMachineContext,
    TradingPokemonStateMachine,
)

LOGGER = logger.get_logger(__name__)

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
    ots_names=["GOLD"] * 6,
    pokemon_nicknames=["Bulbasaur", "Charmander", "Squirtle", "Gatito", "Gato", "Hoja"],
).serialize()


def main(
    host: str = "127.0.0.1",
    port: int = 8000,
    bgb_host: str = "127.0.0.1",
    bgb_port: int = 9999,
    secret: str = "",
) -> None:
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(_exception_handler)
    loop.add_signal_handler(signal.SIGTERM, lambda: _signal_handler("SIGTERM", loop))

    LOGGER.setLevel(logging.INFO)

    server = BGBLinkCableServer(host=bgb_host, port=bgb_port, loop=loop)
    try:
        server.run(_master_data_handler_state_machine)
    except KeyboardInterrupt:
        LOGGER.info("Stopping server with CTRL+C")
    finally:
        LOGGER.info("Graceful shutdown...")
        server.stop()
        loop.close()


async def _master_data_handler_state_machine(reader, writer) -> None:
    ctx = TradeStateMachineContext(
        reader=reader,
        writer=writer,
        pkm_party=Party.from_bytes(PARTY),
    )

    state_machine = TradingPokemonStateMachine(
        initial_state=NotConnectedState(),
        context=ctx,
    )

    await state_machine()


def _signal_handler(signal: str, loop: asyncio.AbstractEventLoop) -> None:
    LOGGER.info(f"Received {signal}. Stopping execution...")
    loop.stop()


def _exception_handler(loop: asyncio.AbstractEventLoop, ctx: dict[str, Any]) -> None:
    # Log the exception and stop the asyncio loop
    LOGGER.error("Unexpected exception received, stopping the event loop...")
    LOGGER.exception(ctx.get("exception"))
    loop.stop()


if __name__ == "__main__":
    typer.run(main)
