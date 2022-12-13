import asyncio
from typing import Any

from pkm_trade_spoofer import logger
from pkm_trade_spoofer.bgb_link_server import BGBLinkCableServer
from pkm_trade_spoofer.models import EVs, Party
from pkm_trade_spoofer.pokemon import pokemon_by_id
from pkm_trade_spoofer.trading_state_machine import (
    Context,
    NotConnectedState,
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


def main():
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(_exception_handler)

    server = BGBLinkCableServer(host="127.0.0.1", port=9999, loop=loop)
    try:
        server.run(_master_data_handler_state_machine)
    except KeyboardInterrupt:
        LOGGER.info("Stopping server with CTRL+C")
    finally:
        LOGGER.info("Graceful shutdown...")
        server.stop()
        loop.close()


async def _master_data_handler_state_machine(reader, writer) -> None:
    ctx = Context(reader=reader, writer=writer, pkm_party=Party.from_bytes(PARTY))
    state_machine = TradingPokemonStateMachine(
        initial_state=NotConnectedState(),
        context=ctx,
    )
    await state_machine()


def _exception_handler(loop: asyncio.AbstractEventLoop, ctx: dict[str, Any]) -> None:
    # Log the exception and stop the asyncio loop
    LOGGER.error("Unexpected exception received, stopping the event loop...")
    LOGGER.exception(ctx.get("exception"))
    loop.stop()


if __name__ == "__main__":
    main()
