# Released under the MIT License. See LICENSE for details.
#
"""Testing rpcws functionality."""

from __future__ import annotations

import os
import time
import random
import asyncio
from enum import unique, Enum
from typing import TYPE_CHECKING
from dataclasses import dataclass

import pytest
import websockets.asyncio.client
import websockets.asyncio.connection
import websockets.asyncio.server
from websockets.asyncio.server import serve

from efro.rpcws import RPCWSEndpoint
from efro.error import CommunicationError
from efro.dataclassio import ioprepped, dataclass_from_json, dataclass_to_json

if TYPE_CHECKING:
    from typing import Awaitable

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

ADDR = '127.0.0.1'
# Randomize this a bit to avoid failing on parallel testing.
PORT = random.randrange(8000, 16000)

SLOW_WAIT = 1.0


@unique
class _MessageType(Enum):
    TEST1 = 't1'
    RESPONSE1 = 'r1'
    TEST2 = '2'
    RESPONSE2 = 'r2'
    TEST_SLOW = 'ts'
    RESPONSE_SLOW = 'rs'
    TEST_BIG = 'tb'
    RESPONSE_BIG = 'rb'


@ioprepped
@dataclass
class _Message:
    messagetype: _MessageType
    extradata: bytes = b''


class _WSAdapter:
    """Adapts a websockets connection to WebSocketTransport."""

    def __init__(self, ws: websockets.asyncio.connection.Connection) -> None:
        self._ws = ws

    async def send(self, data: bytes) -> None:
        """Send binary data."""
        await self._ws.send(data)

    async def recv(self) -> bytes:
        """Receive binary data."""
        data = await self._ws.recv()
        assert isinstance(data, bytes)
        return data

    async def close(self) -> None:
        """Close the connection."""
        await self._ws.close()


class _ServerClientCommon:
    def __init__(self, debug_print: bool) -> None:
        self._endpoint: RPCWSEndpoint | None = None
        self._debug_print = debug_print

    def has_endpoint(self) -> bool:
        """Is our endpoint up yet?"""
        return self._endpoint is not None

    @property
    def endpoint(self) -> RPCWSEndpoint:
        """Our endpoint."""
        if self._endpoint is None:
            raise RuntimeError('Expected endpoint to exist.')
        return self._endpoint

    async def send_message(
        self,
        message: _Message,
        timeout: float | None = None,
        close_on_error: bool = True,
    ) -> _Message:
        """Send high level messages."""
        assert self._endpoint is not None
        response = await self._endpoint.send_message(
            dataclass_to_json(message).encode(),
            timeout=timeout,
            close_on_error=close_on_error,
        )
        return dataclass_from_json(_Message, response.decode())

    async def handle_message(self, msg: _Message) -> _Message:
        """Handle a high-level message."""

        if msg.messagetype is _MessageType.TEST1:
            return _Message(_MessageType.RESPONSE1)

        if msg.messagetype is _MessageType.TEST2:
            return _Message(_MessageType.RESPONSE2)

        if msg.messagetype is _MessageType.TEST_SLOW:
            await asyncio.sleep(SLOW_WAIT)
            return _Message(_MessageType.RESPONSE_SLOW)

        if msg.messagetype is _MessageType.TEST_BIG:
            # 5 Mb Response
            return _Message(
                _MessageType.RESPONSE_BIG,
                extradata=bytes(bytearray(1024 * 1024 * 5)),
            )

        raise RuntimeError(f'Got unexpected message type: {msg.messagetype}')

    async def _handle_raw_message(self, message: bytes) -> bytes:
        msgobj = dataclass_from_json(_Message, message.decode())
        rspobj = await self.handle_message(msgobj)
        return dataclass_to_json(rspobj).encode()


class _Server(_ServerClientCommon):
    def __init__(self, debug_print: bool) -> None:
        super().__init__(debug_print=debug_print)
        self._server: websockets.asyncio.server.Server | None = None
        self._started = asyncio.Event()

    async def run(self) -> None:
        """Run the websocket server."""
        assert self._server is None
        self._server = await serve(
            self._handle_client, ADDR, PORT, max_size=10 * 1024 * 1024
        )
        self._started.set()
        try:
            await self._server.serve_forever()
        except asyncio.CancelledError:
            pass

    async def wait_started(self) -> None:
        """Wait until the server is accepting connections."""
        await self._started.wait()

    def stop(self) -> None:
        """Stop the server."""
        if self._server is not None:
            self._server.close()

    async def _handle_client(
        self, ws: websockets.asyncio.server.ServerConnection
    ) -> None:
        assert self._endpoint is None
        adapter = _WSAdapter(ws)
        self._endpoint = RPCWSEndpoint(
            self._handle_raw_message,
            adapter,
            debug_print=self._debug_print,
            label='test_rpcws_server',
        )
        await self._endpoint.run()


class _Client(_ServerClientCommon):
    def __init__(self, debug_print: bool) -> None:
        super().__init__(debug_print=debug_print)

    async def run(self) -> None:
        """Connect and run."""
        ws = await websockets.asyncio.client.connect(
            f'ws://{ADDR}:{PORT}', max_size=10 * 1024 * 1024
        )
        adapter = _WSAdapter(ws)
        self._endpoint = RPCWSEndpoint(
            self._handle_raw_message,
            adapter,
            debug_print=self._debug_print,
            label='test_rpcws_client',
        )
        await self._endpoint.run()


class _Tester:
    def __init__(
        self,
        server_debug_print: bool = True,
        client_debug_print: bool = True,
    ) -> None:
        self.client = _Client(debug_print=client_debug_print)
        self.server = _Server(debug_print=server_debug_print)

    def run(self, testcall: Awaitable[None]) -> None:
        """Run our test."""
        asyncio.run(self._run(testcall), debug=True)

    async def _run(self, testcall: Awaitable[None]) -> None:
        # Run server, client, and tests simultaneously.
        await asyncio.gather(
            self.server.run(),
            self._run_client_and_test(testcall),
        )

    async def _run_client_and_test(self, testcall: Awaitable[None]) -> None:
        """Wait for server, then run client + test."""
        await self.server.wait_started()
        await asyncio.gather(
            self.client.run(),
            self._run_test(testcall),
        )

    async def _run_test(self, testcall: Awaitable[None]) -> None:
        """Set up before and tear down after a test call."""

        # Wait until both endpoints are up.
        while not (self.server.has_endpoint() and self.client.has_endpoint()):
            await asyncio.sleep(0.01)

        print('test_rpcws test call starting...')

        # Do the thing.
        await testcall

        print('test_rpcws test call completed; tearing down...')

        # Close the endpoint and stop the server.
        self.server.endpoint.close()
        await self.server.endpoint.wait_closed()
        self.server.stop()


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_simple_messages() -> None:
    """Test basic messages and responses."""
    tester = _Tester()

    async def _do_it() -> None:
        # Send some messages both directions and make sure we get the
        # expected response types.

        resp = await tester.server.send_message(_Message(_MessageType.TEST1))
        assert resp.messagetype is _MessageType.RESPONSE1

        resp = await tester.client.send_message(_Message(_MessageType.TEST1))
        assert resp.messagetype is _MessageType.RESPONSE1

        resp = await tester.server.send_message(_Message(_MessageType.TEST2))
        assert resp.messagetype is _MessageType.RESPONSE2

        resp = await tester.client.send_message(_Message(_MessageType.TEST2))
        assert resp.messagetype is _MessageType.RESPONSE2

        resp = await tester.server.send_message(
            _Message(
                _MessageType.TEST_BIG,
                extradata=bytes(bytearray(1024 * 1024 * 5)),
            )
        )
        assert resp.messagetype is _MessageType.RESPONSE_BIG

        resp = await tester.client.send_message(
            _Message(
                _MessageType.TEST_BIG,
                extradata=bytes(bytearray(1024 * 1024 * 5)),
            )
        )
        assert resp.messagetype is _MessageType.RESPONSE_BIG

    tester.run(_do_it())


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_simultaneous_messages() -> None:
    """Test multiplexed messages and responses."""
    tester = _Tester()

    async def _do_it() -> None:
        # Send a bunch of messages both ways at once and make sure
        # they all come through simultaneously-ish.
        starttime = time.monotonic()
        results = await asyncio.gather(
            tester.client.send_message(_Message(_MessageType.TEST_SLOW)),
            tester.server.send_message(_Message(_MessageType.TEST_SLOW)),
            tester.client.send_message(_Message(_MessageType.TEST_SLOW)),
            tester.server.send_message(_Message(_MessageType.TEST_SLOW)),
            tester.client.send_message(_Message(_MessageType.TEST_SLOW)),
            tester.server.send_message(_Message(_MessageType.TEST_SLOW)),
        )

        # This should all go through in roughly the same time that 1
        # goes through in. Using 2x to allow headroom on slow CI
        # runners (Windows, etc.).
        assert (time.monotonic() - starttime) < 2.0 * SLOW_WAIT

        # Make sure we got all correct responses.
        assert all(r.messagetype is _MessageType.RESPONSE_SLOW for r in results)

        # They should all be uniquely created message objects.
        assert len(set(id(r) for r in results)) == len(results)

    tester.run(_do_it())


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_message_timeout() -> None:
    """Test sends timing out."""
    tester = _Tester()

    async def _do_it() -> None:
        # This message should return after a short wait.
        resp = await tester.server.send_message(
            _Message(_MessageType.TEST_SLOW)
        )
        assert resp.messagetype is _MessageType.RESPONSE_SLOW

        # This message should time out but not close the connection.
        with pytest.raises(CommunicationError):
            resp = await tester.server.send_message(
                _Message(_MessageType.TEST_SLOW),
                timeout=0.5,
                close_on_error=False,
            )
        assert not tester.server.endpoint.is_closing()

        # This message should time out and close the connection as a
        # result.
        with pytest.raises(CommunicationError):
            resp = await tester.server.send_message(
                _Message(_MessageType.TEST_SLOW),
                timeout=0.5,
                close_on_error=True,
            )
        assert tester.server.endpoint.is_closing()

    tester.run(_do_it())


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_server_interrupt() -> None:
    """Test server dying during message send."""
    tester = _Tester()

    async def _do_it() -> None:
        async def _kill_connection() -> None:
            await asyncio.sleep(0.2)
            tester.server.endpoint.close()

        _task = asyncio.create_task(_kill_connection())
        starttime = time.monotonic()
        with pytest.raises(CommunicationError):
            await tester.server.send_message(_Message(_MessageType.TEST_SLOW))
        # Interrupt should abort the in-flight send promptly via the
        # peer's transport close, not wait out DEFAULT_MESSAGE_TIMEOUT.
        assert (time.monotonic() - starttime) < 5.0

    tester.run(_do_it())


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_client_interrupt() -> None:
    """Test client dying during message send."""
    tester = _Tester()

    async def _do_it() -> None:
        async def _kill_connection() -> None:
            await asyncio.sleep(0.2)
            tester.client.endpoint.close()

        _task = asyncio.create_task(_kill_connection())
        starttime = time.monotonic()
        with pytest.raises(CommunicationError):
            await tester.server.send_message(_Message(_MessageType.TEST_SLOW))
        # Interrupt should abort the in-flight send promptly via the
        # peer's transport close, not wait out DEFAULT_MESSAGE_TIMEOUT.
        assert (time.monotonic() - starttime) < 5.0

    tester.run(_do_it())
