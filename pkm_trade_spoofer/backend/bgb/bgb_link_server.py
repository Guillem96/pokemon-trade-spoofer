import asyncio
import enum
import functools
import logging
import struct
from typing import Any, Awaitable, Callable, Coroutine, NamedTuple, Optional

PACKET_SIZE_BYTES = 8
PACKET_FORMAT = "<4BI"
LOGGER = logging.getLogger(__name__)


HandlerFn = Callable[["GameBoyPacket"], Awaitable[None]]
WriterFn = Callable[[int], Awaitable[None]]
SlaveMasterDataTaskFn = Callable[
    [asyncio.Queue[int], WriterFn],
    Coroutine[Any, Any, None],
]


class GBPacketType(enum.IntEnum):
    VERSION = 1
    JOYPAD_UPDATE = 101
    SYNC1 = 104
    MASTER = 104
    SYNC2 = 105
    SLAVE = 105
    SYNC3 = 106
    STATUS = 108
    WANT_DISCONNECT = 109


class GameBoyPacket(NamedTuple):
    type_: GBPacketType
    b2: int
    b3: int = 0
    b4: int = 0
    timestamp: Optional[int] = None

    def with_timestamp(self, timestamp: int) -> "GameBoyPacket":
        return GameBoyPacket(self.type_, self.b2, self.b3, self.b4, timestamp)


class GameBoyLinkStreamReader(object):
    def __init__(self, r: asyncio.StreamReader) -> None:
        self.r = r

    async def read(self) -> GameBoyPacket:
        data = await self.r.readexactly(PACKET_SIZE_BYTES)
        return GameBoyPacket(*struct.unpack(PACKET_FORMAT, data))


class GameBoyLinkStreamWriter(object):
    def __init__(self, w: asyncio.StreamWriter) -> None:
        self.w = w
        self._lock = asyncio.Lock()
        self._last_received_timestamp = 0

    def update_timestamp(self, ntsp: int) -> None:
        self._last_received_timestamp = ntsp

    async def write(self, packet: GameBoyPacket) -> None:
        packet = packet.with_timestamp(self._last_received_timestamp)

        async with self._lock:
            self.w.write(
                struct.pack(
                    PACKET_FORMAT,
                    packet.type_,
                    packet.b2,
                    packet.b3,
                    packet.b4,
                    packet.timestamp or 0,
                ),
            )
            await self.w.drain()

    async def write_status(self) -> None:
        await self.write(
            GameBoyPacket(
                GBPacketType.STATUS,
                1,  # Running
            ),
        )

    async def write_version(self) -> None:
        await self.write(
            GameBoyPacket(
                GBPacketType.VERSION,  # Version packet
                1,  # Major
                4,  # Minor
                0,  # Patch
            ),
        )

    async def write_master(self, data: int) -> None:
        await self.write(
            GameBoyPacket(
                GBPacketType.MASTER,  # Master data packet
                data,  # Data value
                0x81,  # Control value
            ),
        )

    async def write_slave(self, data: int) -> None:
        await self.write(
            GameBoyPacket(
                GBPacketType.SLAVE,  # Slave data packet
                data,  # Data value
                0x80,  # Control value
            ),
        )

    async def write_sync3(self, packet: GameBoyPacket) -> None:
        await self.write(
            GameBoyPacket(
                GBPacketType.SYNC3,
                packet.b2,
                packet.b3,
                packet.b4,
            ),
        )


class BGBLinkCableConnection(object):
    def __init__(
        self,
        reader: GameBoyLinkStreamReader,
        writer: GameBoyLinkStreamWriter,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        master_data_task_fn: Optional[SlaveMasterDataTaskFn] = None,
        slave_data_task_fn: Optional[SlaveMasterDataTaskFn] = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self._loop = loop or asyncio.get_running_loop()
        self.master_data_task_fn = master_data_task_fn
        self.slave_data_task_fn = slave_data_task_fn

        self._handlers: dict[GBPacketType, HandlerFn] = {
            GBPacketType.VERSION: self._handle_version,
            GBPacketType.SYNC3: self._handle_sync3,
            GBPacketType.STATUS: self._handle_status,
            GBPacketType.JOYPAD_UPDATE: self._handle_joypad,
            GBPacketType.WANT_DISCONNECT: self._handle_want_disconnect,
        }

        # Initializing queues
        self._queues: dict[GBPacketType, asyncio.Queue[GameBoyPacket]] = {
            k: asyncio.Queue() for k in self._handlers
        }

        self._master_slave_queues: dict[GBPacketType, asyncio.Queue[int]] = {
            GBPacketType.MASTER: asyncio.Queue(),
            GBPacketType.SLAVE: asyncio.Queue(),
        }

    async def __call__(self) -> None:
        try:
            await self._run()
        except* Exception as exc_group:
            self._loop.call_exception_handler(
                {
                    "exception": exc_group,
                    "message": (
                        f"{self.__class__.__name__} task group has unhandled "
                        "exceptions."
                    ),
                },
            )

    async def _run(self) -> None:
        await self.writer.write_version()

        async with asyncio.TaskGroup() as tg:
            for k, handler in self._handlers.items():
                tg.create_task(self._handler_tasks(handler, self._queues[k]))

            if self.master_data_task_fn is not None:
                tg.create_task(
                    self.master_data_task_fn(
                        self._master_slave_queues[GBPacketType.MASTER],
                        self.writer.write_slave,
                    ),
                )

            if self.slave_data_task_fn is not None:
                tg.create_task(
                    self.slave_data_task_fn(
                        self._master_slave_queues[GBPacketType.SLAVE],
                        self.writer.write_master,
                    ),
                )

            while True:
                try:
                    packet = await self.reader.read()
                except asyncio.IncompleteReadError:
                    break

                # Cheat, and say we are exactly in sync with the client
                self.writer.update_timestamp(packet.timestamp or 0)

                if packet.type_ in {GBPacketType.SLAVE, GBPacketType.MASTER}:
                    await self._master_slave_queues[packet.type_].put(packet.b2)
                else:
                    await self._queues[packet.type_].put(packet)

    async def _handler_tasks(
        self,
        handler: HandlerFn,
        queue: asyncio.Queue[GameBoyPacket],
    ) -> None:
        try:
            while True:
                packet = await queue.get()
                await handler(packet)
                queue.task_done()
        except asyncio.CancelledError:
            print("Cancelled task:", handler.__name__)

    async def _handle_version(self, packet: GameBoyPacket) -> None:
        major, minor, patch = packet.b2, packet.b3, packet.b4
        print(f"Received version packet: {major}.{minor}.{patch}")
        if (major, minor, patch) != (1, 4, 0):
            raise ValueError(f"Unsupported protocol version {major}.{minor}.{patch}")

        await self.writer.write_version()

    async def _handle_sync3(self, packet: GameBoyPacket) -> None:
        await self.writer.write_sync3(packet)

    async def _handle_joypad(self, _: GameBoyPacket) -> None:
        ...

    async def _handle_status(self, packet: GameBoyPacket) -> None:
        # TODO: stop logic when client is paused
        print("Received status packet:")
        print("\tRunning:", (packet.b2 & 1) == 1)
        print("\tPaused:", (packet.b2 & 2) == 2)
        print("\tSupports reconnect:", (packet.b2 & 4) == 4)

        # The docs say not to respond to status with status, but not doing this
        # causes link instability. An alternative is to send sync3 packets
        # periodically, but this way is easier.
        await self.writer.write_status()

    async def _handle_want_disconnect(self, _: GameBoyPacket) -> None:
        print("Client has initiated disconnect")


# Implements the BGB link cable protocol
# See https://bgb.bircd.org/bgblink.html
class BGBLinkCableServer:
    PACKET_SIZE_BYTES = 8

    def __init__(
        self,
        host: str = "",
        port: int = 8765,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        blocking: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self._connections: list[asyncio.Task] = []
        self._loop = loop or asyncio.get_running_loop()
        self._blocking = blocking
        self._server: Optional[asyncio.AbstractServer] = None

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        master_data_handler: Optional[SlaveMasterDataTaskFn] = None,
        slave_data_handler: Optional[SlaveMasterDataTaskFn] = None,
    ) -> None:
        connection = BGBLinkCableConnection(
            GameBoyLinkStreamReader(reader),
            GameBoyLinkStreamWriter(writer),
            self._loop,
            master_data_handler,
            slave_data_handler,
        )
        self._connections.append(self._loop.create_task(connection()))

    async def run(
        self,
        master_data_handler: Optional[SlaveMasterDataTaskFn] = None,
        slave_data_handler: Optional[SlaveMasterDataTaskFn] = None,
    ) -> None:
        self._server = await asyncio.start_server(
            functools.partial(
                self._handle_connection,
                master_data_handler=master_data_handler,
                slave_data_handler=slave_data_handler,
            ),
            self.host or "0.0.0.0",
            self.port,
        )

        addrs = ", ".join(str(sock.getsockname()) for sock in self._server.sockets)
        LOGGER.info(f"BGB Server listening at {addrs}")
        if self._blocking:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._connections:
            for c in self._connections:
                c.cancel()

            _, pending = await asyncio.wait(self._connections)
            if pending:
                raise asyncio.InvalidStateError(
                    f"Unexpected state, {pending} should be done.",
                )

        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
