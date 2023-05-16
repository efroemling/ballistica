# Released under the MIT License. See LICENSE for details.
#
"""Testing rpc functionality."""

from __future__ import annotations

import time
import random
import asyncio
import weakref
from enum import unique, Enum
from typing import TYPE_CHECKING
from dataclasses import dataclass

import pytest

from efro.rpc import RPCEndpoint
from efro.error import CommunicationError
from efro.dataclassio import ioprepped, dataclass_from_json, dataclass_to_json

if TYPE_CHECKING:
    from typing import Awaitable

ADDR = '127.0.0.1'
# Randomize this a bit to avoid failing on parallel testing.
# Ideally we should let the OS pick the address and pass the
# resulting one to the client.
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


class _ServerClientCommon:
    def __init__(
        self,
        keepalive_interval: float,
        keepalive_timeout: float,
        debug_print: bool,
    ) -> None:
        self._endpoint: RPCEndpoint | None = None
        self._keepalive_interval = keepalive_interval
        self._keepalive_timeout = keepalive_timeout
        self._debug_print = debug_print

    def has_endpoint(self) -> bool:
        """Is our endpoint up yet?"""
        return self._endpoint is not None

    @property
    def endpoint(self) -> RPCEndpoint:
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
    def __init__(
        self,
        keepalive_interval: float,
        keepalive_timeout: float,
        debug_print: bool,
    ) -> None:
        super().__init__(
            keepalive_interval=keepalive_interval,
            keepalive_timeout=keepalive_timeout,
            debug_print=debug_print,
        )
        self.listener: asyncio.base_events.Server | None = None

    async def start(self) -> None:
        """Start serving. Call this before run()."""
        assert self.listener is None
        self.listener = await asyncio.start_server(
            self._handle_client, ADDR, PORT
        )

    async def run(self) -> None:
        """Do the thing."""
        assert self.listener is not None
        assert self._endpoint is None
        async with self.listener:
            try:
                await self.listener.serve_forever()
            except asyncio.CancelledError:
                pass

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        assert self._endpoint is None

        # Note to self: passing ourself as a handler creates a dependency
        # loop; in production code we'd probably want to store this as a
        # weak ref or whatnot to keep teardown deterministic.
        self._endpoint = RPCEndpoint(
            self._handle_raw_message,
            reader,
            writer,
            keepalive_interval=self._keepalive_interval,
            keepalive_timeout=self._keepalive_timeout,
            debug_print=self._debug_print,
            label='test_rpc_server',
        )

        await self._endpoint.run()


class _Client(_ServerClientCommon):
    def __init__(
        self,
        keepalive_interval: float,
        keepalive_timeout: float,
        debug_print: bool,
    ) -> None:
        super().__init__(
            keepalive_interval=keepalive_interval,
            keepalive_timeout=keepalive_timeout,
            debug_print=debug_print,
        )

    async def run(self) -> None:
        """Do the thing."""
        reader, writer = await asyncio.open_connection(ADDR, PORT)
        # Note to self: passing ourself as a handler creates a dependency
        # loop; in production code we'd probably want to store this as a
        # weak ref or whatnot to keep teardown deterministic.
        self._endpoint = RPCEndpoint(
            self._handle_raw_message,
            reader,
            writer,
            keepalive_interval=self._keepalive_interval,
            keepalive_timeout=self._keepalive_timeout,
            debug_print=self._debug_print,
            label='test_rpc_client',
        )
        await self._endpoint.run()


class _Tester:
    def __init__(
        self,
        keepalive_interval: float = RPCEndpoint.DEFAULT_KEEPALIVE_INTERVAL,
        keepalive_timeout: float = RPCEndpoint.DEFAULT_KEEPALIVE_TIMEOUT,
        server_debug_print: bool = True,
        client_debug_print: bool = True,
    ) -> None:
        self.client = _Client(
            keepalive_interval=keepalive_interval,
            keepalive_timeout=keepalive_timeout,
            debug_print=client_debug_print,
        )
        self.server = _Server(
            keepalive_interval=keepalive_interval,
            keepalive_timeout=keepalive_timeout,
            debug_print=server_debug_print,
        )

    # noinspection PyProtectedMember
    def run(self, testcall: Awaitable[None]) -> None:
        """Run our test."""

        asyncio.run(self._run(testcall), debug=True)

        # Disabling this for now; need to get to the bottom of why it is
        # failing in some cases or make it more lenient.
        if bool(False):
            # Make sure the endpoints go down immediately when we remove our
            # only refs to them.
            server_endpoint_ref = weakref.ref(self.server.endpoint)
            client_endpoint_ref = weakref.ref(self.client.endpoint)
            del self.client._endpoint
            del self.server._endpoint

            for name, endpoint in [
                ('server', server_endpoint_ref()),
                ('client', client_endpoint_ref()),
            ]:
                if endpoint is not None:
                    import gc

                    print('referrers:', gc.get_referrers(endpoint))
                    raise RuntimeError(f'{name} did not go down cleanly')

    async def _run(self, testcall: Awaitable[None]) -> None:
        # Give server a chance to spin up before kicking off client.
        await self.server.start()

        # Now run our server, our client, and our tests simultaneously.
        await asyncio.gather(
            self.server.run(),
            self.client.run(),
            self._run_test(testcall),
        )

    async def _run_test(self, testcall: Awaitable[None]) -> None:
        """Set up before and tear down after a test call."""
        assert self.server.listener is not None

        # Wait until the client has connected.
        while not self.server.has_endpoint():
            await asyncio.sleep(0.01)

        print('test_rpc test call starting...')

        # Do the thing.
        await testcall

        print('test_rpc test call completed; tearing down...')

        # Close both our listener socket and our established endpoint;
        # this should break us out of our loop.
        self.server.endpoint.close()
        await self.server.endpoint.wait_closed()

        self.server.listener.close()
        await self.server.listener.wait_closed()


def test_keepalive_fail() -> None:
    """Test keepalive timeout."""
    kinterval = 0.05
    ktimeout = 0.25
    tester = _Tester(keepalive_interval=kinterval, keepalive_timeout=ktimeout)

    async def _do_it() -> None:
        # Tell our client to not send keepalives.
        tester.client.endpoint.test_suppress_keepalives = True

        # Make sure the endpoint goes down sometime soon-ish after the
        # keepalive timeout.
        await asyncio.sleep(ktimeout)
        starttime = time.monotonic()
        while (
            not tester.server.endpoint.is_closing()
            and time.monotonic() - starttime < 5.0
        ):
            await asyncio.sleep(0.01)
        assert tester.server.endpoint.is_closing()

    tester.run(_do_it())


def test_keepalive_success() -> None:
    """Test keepalive non-timeout."""
    kinterval = 0.05
    ktimeout = 0.25
    tester = _Tester(keepalive_interval=kinterval, keepalive_timeout=ktimeout)

    async def _do_it() -> None:
        # Sleep just past the keepalive timeout and make sure the endpoint
        # is NOT going down
        await asyncio.sleep(ktimeout * 1.25)
        assert not tester.server.endpoint.is_closing()

    tester.run(_do_it())


def test_simple_messages() -> None:
    """Test basic messages and responses."""
    tester = _Tester()

    async def _do_it() -> None:
        # Send some messages both directions and make sure we get the expected
        # response types.

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


def test_simultaneous_messages() -> None:
    """Test basic messages and responses."""
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

        # This should all go through in the same time that 1 goes through in.
        assert (time.monotonic() - starttime) < 1.25 * SLOW_WAIT

        # Make sure we got all correct responses.
        assert all(r.messagetype is _MessageType.RESPONSE_SLOW for r in results)

        # They should all be uniquely created message objects.
        assert len(set(id(r) for r in results)) == len(results)

    tester.run(_do_it())


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

        # This message should time out and close the connection as a result.
        with pytest.raises(CommunicationError):
            resp = await tester.server.send_message(
                _Message(_MessageType.TEST_SLOW),
                timeout=0.5,
                close_on_error=True,
            )
        assert tester.server.endpoint.is_closing()

    tester.run(_do_it())


def test_server_interrupt() -> None:
    """Test server dying during message send."""
    tester = _Tester()

    async def _do_it() -> None:
        async def _kill_connection() -> None:
            await asyncio.sleep(0.2)
            tester.server.endpoint.close()

        _task = asyncio.create_task(_kill_connection())
        with pytest.raises(CommunicationError):
            await tester.server.send_message(_Message(_MessageType.TEST_SLOW))

    tester.run(_do_it())


def test_client_interrupt() -> None:
    """Test client dying during message send."""
    tester = _Tester()

    async def _do_it() -> None:
        async def _kill_connection() -> None:
            await asyncio.sleep(0.2)
            tester.client.endpoint.close()

        _task = asyncio.create_task(_kill_connection())
        with pytest.raises(CommunicationError):
            await tester.server.send_message(_Message(_MessageType.TEST_SLOW))

    tester.run(_do_it())
