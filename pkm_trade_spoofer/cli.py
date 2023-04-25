import asyncio
import functools
import logging
import signal
from typing import Any

import typer

from pkm_trade_spoofer import ManagementAPI, logger
from pkm_trade_spoofer._types import Backend, BackendTypes
from pkm_trade_spoofer.backend import BGBBackend
from pkm_trade_spoofer.models import EVs, Party
from pkm_trade_spoofer.pokemon import pokemon_by_id

app = typer.Typer(name="Pokemon GSC Trade Spoofer", no_args_is_help=True)


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
    pokemon_nicknames=[
        "Bulbasaur",
        "Charmander",
        "Squirtle",
        "Gatito",
        "Gato",
        "Hoja",
    ],
)


@app.command("api")
def admin_api_cmd(
    host: str = "127.0.0.1",
    port: int = 8000,
    bgb_host: str = "127.0.0.1",
    bgb_port: int = 9999,
    secret: str = "",
) -> None:
    cli_logger = logger.get_logger(__name__)
    cli_logger.setLevel(logging.INFO)

    loop = _setup_event_loop(cli_logger)

    backends: dict[BackendTypes, Backend] = {
        BackendTypes.bgb_emulator: BGBBackend(bgb_host, bgb_port, loop),
    }

    admin_api = ManagementAPI(backends, loop=loop, host=host, port=port, secret=secret)
    try:
        admin_api.start()
    except KeyboardInterrupt:
        cli_logger.info("Stopping spoofer with CTRL+C")
    finally:
        cli_logger.info("Graceful shutdown...")
        admin_api.stop()
        loop.close()


@app.command("bgb")
def bgb_cmd(
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    cli_logger = logger.get_logger(__name__)
    cli_logger.setLevel(logging.INFO)

    loop = _setup_event_loop(cli_logger)

    backend = BGBBackend(host, port, loop)

    try:
        loop.run_until_complete(backend.start(PARTY))
        loop.run_forever()
    except KeyboardInterrupt:
        cli_logger.info("Stopping spoofer with CTRL+C")
    finally:
        cli_logger.info("Graceful shutdown...")
        loop.run_until_complete(backend.stop())
        loop.close()


def _setup_event_loop(cli_logger: logging.Logger) -> asyncio.AbstractEventLoop:
    cli_logger.info("Setting up asynchronous loop...")
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(functools.partial(_exception_handler, cli_logger))
    loop.add_signal_handler(
        signal.SIGTERM,
        lambda: _signal_handler(cli_logger, "SIGTERM", loop),
    )
    return loop


def _signal_handler(
    cli_logger: logging.Logger,
    signal: str,
    loop: asyncio.AbstractEventLoop,
) -> None:
    cli_logger.info(f"Received {signal}. Stopping execution...")
    loop.stop()


def _exception_handler(
    cli_logger: logging.Logger,
    loop: asyncio.AbstractEventLoop,
    ctx: dict[str, Any],
) -> None:
    # Log the exception and stop the asyncio loop
    cli_logger.error("Unexpected exception received, stopping the event loop...")
    cli_logger.exception(ctx.get("exception"))
    loop.stop()
