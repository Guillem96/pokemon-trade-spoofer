import enum
from typing import Protocol

from pkm_trade_spoofer.models import Party


class BackendTypes(enum.StrEnum):
    bgb_emulator: str = "BGB"


class Backend(Protocol):
    async def start(self, party: Party) -> None:
        ...

    def stop(self) -> None:
        ...
