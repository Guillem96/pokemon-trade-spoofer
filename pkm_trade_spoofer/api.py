import asyncio
import functools

import pydantic
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from pkm_trade_spoofer import logger
from pkm_trade_spoofer._types import Backend, BackendTypes
from pkm_trade_spoofer.models import EVs, Party, Pokemon
from pkm_trade_spoofer.pokemon import pokemon_by_id

LOGGER = logger.get_logger(__name__)


class SimplePokemon(pydantic.BaseModel):
    """Simple pokemon schema transferred between front-end and back-end."""

    nickname: str
    dex_id: int = pydantic.Field(ge=0, le=251)  # type: ignore
    ivs: list[int] = pydantic.Field(min_items=5, max_items=5)
    held_item_id: int

    @pydantic.validator("ivs")
    def _ivs_validator(cls, ivs: list[int]) -> list[int]:
        if any(o > 15 or o < 0 for o in ivs):
            raise ValueError("IVs have to be lower or equal than 15")
        return ivs


class SimpleParty(pydantic.BaseModel):
    """Simplified pokemon party schema."""

    trainer_name: str
    pokemon: list[SimplePokemon] = pydantic.Field(min_items=0, max_items=6)


class StartBackendRequest(pydantic.BaseModel):
    """Schema of start-backend request body."""

    party: SimpleParty
    backend: BackendTypes


class StopBackendRequest(pydantic.BaseModel):
    """stop-backend request body schema."""

    backend: BackendTypes


class Response(pydantic.BaseModel):
    """Common response schema shared across all endpoints."""

    message: str


class HTTPError(pydantic.BaseModel):
    """HTTP Error message schema."""

    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised."},
        }


class ManagementAPI(object):
    """API to manage the execution of the backends."""

    def __init__(
        self,
        backends: dict[BackendTypes, Backend],
        host: str = "127.0.0.1",
        port: int = 8000,
        secret: str = "",
    ) -> None:
        self._host = host
        self._port = port
        self._backends = backends
        self._running_backends: set[BackendTypes] = set()
        self._lock = asyncio.Lock()

        self.app = FastAPI(title="Pokemon GSC Trade Spoofer")
        self.app.state.secret_token = secret

    def start(self) -> None:
        """Start the management api.

        This method is blocking.
        """
        self.app.add_api_route(
            "/start-backend",
            self._start_backend,
            responses={
                200: {"model": Response},
                400: {"model": Response},
                401: {"model": HTTPError},
                500: {"model": Response},
            },
            dependencies=[Depends(_check_secret)],
            methods=["POST"],
        )

        uvicorn.run(
            self.app,
            loop="none",
            host=self._host,
            port=self._port,
            # log_config=None,
        )

    def stop(self) -> None:
        """Stops the management API, as well as, the started backends."""

        for b in self._backends.values():
            b.stop()

    async def _start_backend(
        self,
        start_backend_req: StartBackendRequest,
    ) -> JSONResponse:
        if start_backend_req.backend in self._running_backends:
            res_msg = f"Backend {start_backend_req.backend} is already running."
            return _json_response(Response(message=res_msg), status_code=400)

        try:
            pkm_party = await _simple_party_to_complex(start_backend_req.party)
            LOGGER.info(pkm_party)
            await self._backends[start_backend_req.backend].start(pkm_party)
        except KeyError:
            res_msg = f"Backend {start_backend_req.backend} is not available."
            return _json_response(Response(message=res_msg), status_code=400)

        async with self._lock:
            self._running_backends.add(start_backend_req.backend)

        res_msg = f"Backend {start_backend_req.backend} start successfully."
        return _json_response(Response(message=res_msg), status_code=200)

    async def _stop_backend(
        self,
        stop_backend_req: StopBackendRequest,
    ) -> JSONResponse:
        if stop_backend_req.backend not in self._running_backends:
            res_msg = f"Backend {stop_backend_req.backend} is not running."
            return _json_response(Response(message=res_msg), status_code=400)

        self._backends[stop_backend_req.backend].stop()

        async with self._lock:
            self._running_backends.remove(stop_backend_req.backend)

        res_msg = f"Backend {stop_backend_req.backend} stopped successfully."
        return _json_response(Response(message=res_msg), status_code=400)


def _json_response(content: pydantic.BaseModel, status_code: int) -> JSONResponse:
    return JSONResponse(jsonable_encoder(content), status_code=status_code)


async def _simple_party_to_complex(sp: SimpleParty) -> Party:

    async with asyncio.TaskGroup() as tg:
        pkm_tasks = [tg.create_task(_simple_pkm_to_complex(pkm)) for pkm in sp.pokemon]

    return Party(
        trainer_name=sp.trainer_name,
        pokemon=[pkm_t.result() for pkm_t in pkm_tasks],
        ots_names=[sp.trainer_name] * 6,
        pokemon_nicknames=[pkm.nickname for pkm in sp.pokemon],
    )


async def _simple_pkm_to_complex(pkm: SimplePokemon) -> Pokemon:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(
            pokemon_by_id,
            pkm.dex_id,
            ivs=EVs(*pkm.ivs),
            item_held_id=pkm.held_item_id,
        ),
    )


async def _check_secret(request: Request, secret_token: str = Header(None)) -> None:
    """Dependency to check if a secret token is valid.

    This ensures only applications with the secret key specified when starting
    the server or in environment variable is able to post to the server.
    If no secret token is specified while starting or in environment variables
    this dependency does nothing.

    Args:
        secret_token: Secret token sent with request.  Defaults to None.

    Raises:
        HTTPException: Secret Token invalid
    """
    if request.app.state.secret_token != secret_token:
        raise HTTPException(status_code=401, detail="Secret Token invalid")
