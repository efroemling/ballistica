# Released under the MIT License. See LICENSE for details.
#
"""Remote procedure call related functionality."""

from __future__ import annotations

import time
import asyncio
import logging
from enum import Enum
from collections import deque
from dataclasses import dataclass
from threading import current_thread
from typing import TYPE_CHECKING, Annotated, assert_never

from efro.util import strip_exception_tracebacks
from efro.error import (
    CommunicationError,
    is_asyncio_streams_communication_error,
)
from efro.dataclassio import (
    dataclass_to_json,
    dataclass_from_json,
    ioprepped,
    IOAttrs,
)

if TYPE_CHECKING:
    from typing import Literal, Awaitable, Callable

logger = logging.getLogger(__name__)

# Terminology:
# Packet: A chunk of data consisting of a type and some type-dependent
#         payload. Even though we use streams we organize our transmission
#         into 'packets'.
# Message: User data which we transmit using one or more packets.


class _PacketType(Enum):
    HANDSHAKE = 0
    KEEPALIVE = 1
    MESSAGE = 2
    RESPONSE = 3
    MESSAGE_BIG = 4
    RESPONSE_BIG = 5


_BYTE_ORDER: Literal['big'] = 'big'


@ioprepped
@dataclass
class _PeerInfo:
    # So we can gracefully evolve how we communicate in the future.
    protocol: Annotated[int, IOAttrs('p')]

    # How often we'll be sending out keepalives (in seconds).
    keepalive_interval: Annotated[float, IOAttrs('k')]


# Note: we are expected to be forward and backward compatible; we can
# increment protocol freely and expect everyone else to still talk to us.
# Likewise we should retain logic to communicate with older protocols.
# Protocol history:
# 1 - initial release
# 2 - gained big (32-bit len val) package/response packets
OUR_PROTOCOL = 2


def ssl_stream_writer_underlying_transport_info(
    writer: asyncio.StreamWriter,
) -> str:
    """For debugging SSL Stream connections; returns raw transport info."""
    # Note: accessing internals here so just returning info and not
    # actual objs to reduce potential for breakage.
    transport = getattr(writer, '_transport', None)
    if transport is not None:
        sslproto = getattr(transport, '_ssl_protocol', None)
        if sslproto is not None:
            raw_transport = getattr(sslproto, '_transport', None)
            if raw_transport is not None:
                return str(raw_transport)
    return '(not found)'


# def ssl_stream_writer_force_close_check(writer: asyncio.StreamWriter) -> None:
#     """Ensure a writer is closed; hacky workaround for odd hang."""
#     from threading import Thread

#     # Disabling for now..
#     if bool(True):
#         return

#     # Hopefully can remove this in Python 3.11?...
#     # see issue with is_closing() below for more details.
#     transport = getattr(writer, '_transport', None)
#     if transport is not None:
#         sslproto = getattr(transport, '_ssl_protocol', None)
#         if sslproto is not None:
#             raw_transport = getattr(sslproto, '_transport', None)
#             if raw_transport is not None:
#                 Thread(
#                     target=partial(
#                         _do_writer_force_close_check,
#                          weakref.ref(raw_transport),
#                     ),
#                     daemon=True,
#                 ).start()


# def _do_writer_force_close_check(transport_weak: weakref.ref) -> None:
#     try:
#         # Attempt to bail as soon as the obj dies. If it hasn't done so
#         # by our timeout, force-kill it.
#         starttime = time.monotonic()
#         while time.monotonic() - starttime < 10.0:
#             time.sleep(0.1)
#             if transport_weak() is None:
#                 return
#         transport = transport_weak()
#         if transport is not None:
#             logging.info('Forcing abort on stuck transport %s.', transport)
#             transport.abort()
#     except Exception:
#         logging.warning('Error in writer-force-close-check', exc_info=True)


class _InFlightMessage:
    """Represents a message that is out on the wire."""

    def __init__(self) -> None:
        self._response: bytes | None = None
        self._got_response = asyncio.Event()
        self.wait_task = asyncio.create_task(
            self._wait(), name='rpc in flight msg wait'
        )

    async def _wait(self) -> bytes:
        await self._got_response.wait()
        assert self._response is not None
        return self._response

    def set_response(self, data: bytes) -> None:
        """Set response data."""
        assert self._response is None
        self._response = data
        self._got_response.set()


class _KeepaliveTimeoutError(Exception):
    """Raised if we time out due to not receiving keepalives."""


class RPCEndpoint:
    """Facilitates asynchronous multiplexed remote procedure calls.

    Be aware that, while multiple calls can be in flight in either direction
    simultaneously, packets are still sent serially in a single
    stream. So excessively long messages/responses will delay all other
    communication. If/when this becomes an issue we can look into breaking up
    long messages into multiple packets.
    """

    # Set to True on an instance to test keepalive failures.
    test_suppress_keepalives: bool = False

    # How long we should wait before giving up on a message by default.
    # Note this includes processing time on the other end.
    DEFAULT_MESSAGE_TIMEOUT = 60.0

    # How often we send out keepalive packets by default.
    DEFAULT_KEEPALIVE_INTERVAL = 10.73  # (avoid too regular of values)

    # How long we can go without receiving a keepalive packet before we
    # disconnect.
    DEFAULT_KEEPALIVE_TIMEOUT = 30.0

    def __init__(
        self,
        handle_raw_message_call: Callable[[bytes], Awaitable[bytes]],
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        label: str,
        *,
        debug_print: bool = False,
        debug_print_io: bool = False,
        debug_print_call: Callable[[str], None] | None = None,
        keepalive_interval: float = DEFAULT_KEEPALIVE_INTERVAL,
        keepalive_timeout: float = DEFAULT_KEEPALIVE_TIMEOUT,
    ) -> None:
        self._handle_raw_message_call = handle_raw_message_call
        self._reader = reader
        self._writer = writer
        self.debug_print = debug_print
        self.debug_print_io = debug_print_io
        if debug_print_call is None:
            debug_print_call = print
        self.debug_print_call: Callable[[str], None] = debug_print_call
        self._label = label
        self._thread = current_thread()
        self._closing = False
        self._did_wait_closed = False
        self._event_loop = asyncio.get_running_loop()
        self._out_packets = deque[bytes]()
        self._have_out_packets = asyncio.Event()
        self._run_called = False
        self._peer_info: _PeerInfo | None = None
        self._keepalive_interval = keepalive_interval
        self._keepalive_timeout = keepalive_timeout
        self._did_close_writer = False
        self._did_wait_closed_writer = False
        self._did_out_packets_buildup_warning = False
        self._total_bytes_read = 0
        self._create_time = time.monotonic()

        # Need to hold weak-refs to these otherwise it creates dep-loops
        # which keeps us alive.
        self._tasks: list[asyncio.Task] = []

        # When we last got a keepalive or equivalent (time.monotonic value)
        self._last_keepalive_receive_time: float | None = None

        # (Start near the end to make sure our looping logic is sound).
        self._next_message_id = 65530

        self._in_flight_messages: dict[int, _InFlightMessage] = {}

        if self.debug_print:
            peername = self._writer.get_extra_info('peername')
            self.debug_print_call(
                f'{self._label}: connected to {peername} at {self._tm()}.'
            )

    def __del__(self) -> None:
        if self._run_called:
            if not self._did_close_writer:
                logger.warning(
                    'RPCEndpoint %d dying with run'
                    ' called but writer not closed (transport=%s).',
                    id(self),
                    ssl_stream_writer_underlying_transport_info(self._writer),
                )
            elif not self._did_wait_closed_writer:
                logger.warning(
                    'RPCEndpoint %d dying with run called'
                    ' but writer not wait-closed (transport=%s).',
                    id(self),
                    ssl_stream_writer_underlying_transport_info(self._writer),
                )

        # Currently seeing rare issue where sockets don't go down;
        # let's add a timer to force the issue until we can figure it out.
        # ssl_stream_writer_force_close_check(self._writer)

    async def run(self) -> None:
        """Run the endpoint until the connection is lost or closed.

        Handles closing the provided reader/writer on close.
        """
        try:
            await self._do_run()
        except asyncio.CancelledError:
            # We aren't really designed to be cancelled so let's warn
            # if it happens.
            logger.warning(
                'RPCEndpoint.run got CancelledError;'
                ' want to try and avoid this.'
            )
            raise

    async def _do_run(self) -> None:
        self._check_env()

        if self._run_called:
            raise RuntimeError('Run can be called only once per endpoint.')
        self._run_called = True

        core_tasks = [
            asyncio.create_task(
                self._run_core_task('keepalive', self._run_keepalive_task()),
                name='rpc keepalive',
            ),
            asyncio.create_task(
                self._run_core_task('read', self._run_read_task()),
                name='rpc read',
            ),
            asyncio.create_task(
                self._run_core_task('write', self._run_write_task()),
                name='rpc write',
            ),
        ]
        self._tasks += core_tasks

        # Run our core tasks until they all complete.
        results = await asyncio.gather(*core_tasks, return_exceptions=True)

        # Core tasks should handle their own errors; the only ones
        # we expect to bubble up are CancelledError.
        for result in results:
            # We want to know if any errors happened aside from
            # CancelledError (which are BaseExceptions, not Exception).
            if isinstance(result, Exception):
                logger.warning(
                    'Got unexpected error from %s core task: %s',
                    self._label,
                    result,
                )
            if isinstance(result, BaseException):
                # We're done with these exceptions, so strip their
                # tracebacks to avoid reference cycles.
                strip_exception_tracebacks(result)

        if not all(task.done() for task in core_tasks):
            logger.warning(
                'RPCEndpoint %d: not all core tasks marked done after gather.',
                id(self),
            )

        # Shut ourself down.
        try:
            self.close()
            await self.wait_closed()
        except Exception:
            logger.exception('Error closing %s.', self._label)

        if self.debug_print:
            self.debug_print_call(f'{self._label}: finished.')

    def send_message(
        self,
        message: bytes,
        timeout: float | None = None,
        close_on_error: bool = True,
    ) -> Awaitable[bytes]:
        """Send a message to the peer and return a response.

        If timeout is not provided, the default will be used.
        Raises a CommunicationError if the round trip is not completed
        for any reason.

        By default, the entire endpoint will go down in the case of
        errors. This allows messages to be treated as 'reliable' with
        respect to a given endpoint. Pass close_on_error=False to
        override this for a particular message.
        """
        # Note: This call is synchronous so that the first part of it
        # (enqueueing outgoing messages) happens synchronously. If it were
        # a pure async call it could be possible for send order to vary
        # based on how the async tasks get processed.

        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: sending message of size {len(message)}'
                f' at {self._tm()}.'
            )

        self._check_env()

        if self._closing:
            raise CommunicationError('Endpoint is closed.')

        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: have peerinfo? {self._peer_info is not None}.'
            )

        # message_id is a 16 bit looping value.
        message_id = self._next_message_id
        self._next_message_id = (self._next_message_id + 1) % 65536

        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: will enqueue at {self._tm()}.'
            )

        # FIXME - should handle backpressure (waiting here if there are
        # enough packets already enqueued).

        if len(message) > 65535:
            # Payload consists of type (1b), message_id (2b),
            # len (4b), and data.
            self._enqueue_outgoing_packet(
                _PacketType.MESSAGE_BIG.value.to_bytes(1, _BYTE_ORDER)
                + message_id.to_bytes(2, _BYTE_ORDER)
                + len(message).to_bytes(4, _BYTE_ORDER)
                + message
            )
        else:
            # Payload consists of type (1b), message_id (2b),
            # len (2b), and data.
            self._enqueue_outgoing_packet(
                _PacketType.MESSAGE.value.to_bytes(1, _BYTE_ORDER)
                + message_id.to_bytes(2, _BYTE_ORDER)
                + len(message).to_bytes(2, _BYTE_ORDER)
                + message
            )

        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: enqueued message of size {len(message)}'
                f' at {self._tm()}.'
            )

        # Make an entry so we know this message is out there.
        assert message_id not in self._in_flight_messages
        msgobj = self._in_flight_messages[message_id] = _InFlightMessage()

        # Also add its task to our list so we properly cancel it if we die.
        self._prune_tasks()  # Keep our list from filling with dead tasks.
        self._tasks.append(msgobj.wait_task)

        # Note: we always want to incorporate a timeout. Individual
        # messages may hang or error on the other end and this ensures
        # we won't build up lots of zombie tasks waiting around for
        # responses that will never arrive.
        if timeout is None:
            timeout = self.DEFAULT_MESSAGE_TIMEOUT
        assert timeout is not None

        bytes_awaitable = msgobj.wait_task

        # Now complete the send asynchronously.
        return self._send_message(
            message, timeout, close_on_error, bytes_awaitable, message_id
        )

    async def _send_message(
        self,
        message: bytes,
        timeout: float | None,
        close_on_error: bool,
        bytes_awaitable: asyncio.Task[bytes],
        message_id: int,
    ) -> bytes:
        # pylint: disable=too-many-positional-arguments
        # We need to know their protocol, so if we haven't gotten a handshake
        # from them yet, just wait.
        while self._peer_info is None:
            await asyncio.sleep(0.01)
        assert self._peer_info is not None

        if self._peer_info.protocol == 1:
            if len(message) > 65535:
                raise RuntimeError('Message cannot be larger than 65535 bytes')

        try:
            return await asyncio.wait_for(bytes_awaitable, timeout=timeout)
        except asyncio.CancelledError as exc:
            # Question: we assume this means the above wait_for() was
            # cancelled; how do we distinguish between this and *us* being
            # cancelled though?
            if self.debug_print:
                self.debug_print_call(
                    f'{self._label}: message {message_id} was cancelled.'
                )
            if close_on_error:
                self.close()

            raise CommunicationError() from exc
        except Exception as exc:
            # If our timer timed-out or anything else went wrong with
            # the stream, lump it in as a communication error.
            if isinstance(
                exc, asyncio.TimeoutError
            ) or is_asyncio_streams_communication_error(exc):
                if self.debug_print:
                    self.debug_print_call(
                        f'{self._label}: got {type(exc)} sending message'
                        f' {message_id}; raising CommunicationError.'
                    )

                # Stop waiting on the response.
                bytes_awaitable.cancel()

                # Remove the record of this message.
                del self._in_flight_messages[message_id]

                if close_on_error:
                    self.close()

                # Let the user know something went wrong.
                raise CommunicationError() from exc

            # Some unexpected error; let it bubble up.
            raise

    def close(self) -> None:
        """I said seagulls; mmmm; stop it now."""
        self._check_env()

        if self._closing:
            return

        if self.debug_print:
            self.debug_print_call(f'{self._label}: closing...')

        self._closing = True

        # Kill all of our in-flight tasks.
        if self.debug_print:
            self.debug_print_call(f'{self._label}: cancelling tasks...')

        for task in self._get_live_tasks():
            task.cancel()

        # Close our writer.
        assert not self._did_close_writer
        if self.debug_print:
            self.debug_print_call(f'{self._label}: closing writer...')
        self._writer.close()
        self._did_close_writer = True

        # We don't need this anymore and it is likely to be creating a
        # dependency loop.
        del self._handle_raw_message_call

    def is_closing(self) -> bool:
        """Have we begun the process of closing?"""
        return self._closing

    async def wait_closed(self) -> None:
        """I said seagulls; mmmm; stop it now.

        Wait for the endpoint to finish closing. This is called by run()
        so generally does not need to be explicitly called.
        """
        # pylint: disable=too-many-branches
        self._check_env()

        # Make sure we only *enter* this call once.
        if self._did_wait_closed:
            return
        self._did_wait_closed = True

        if not self._closing:
            raise RuntimeError('Must be called after close()')

        if not self._did_close_writer:
            logger.warning(
                'RPCEndpoint wait_closed() called but never'
                ' explicitly closed writer.'
            )

        live_tasks = self._get_live_tasks()

        # Don't need our task list anymore; this should
        # break any cyclical refs from tasks referring to us.
        self._tasks = []

        if self.debug_print:
            self.debug_print_call(
                f'{self._label}: waiting for tasks to finish: '
                f' ({live_tasks=})...'
            )

        # Wait for all of our in-flight tasks to wrap up.
        results = await asyncio.gather(*live_tasks, return_exceptions=True)
        for result in results:
            # We want to know if any errors happened aside from CancelledError
            # (which are BaseExceptions, not Exception).
            if isinstance(result, Exception):
                logger.warning(
                    'Got unexpected error cleaning up %s task: %s',
                    self._label,
                    result,
                )

        if not all(task.done() for task in live_tasks):
            logger.warning(
                'RPCEndpoint %d: not all live tasks marked done after gather.',
                id(self),
            )

        if self.debug_print:
            self.debug_print_call(
                f'{self._label}: tasks finished; waiting for writer close...'
            )

        # Now wait for our writer to finish going down.
        # When we close our writer it generally triggers errors
        # in our current blocked read/writes. However that same
        # error is also sometimes returned from _writer.wait_closed().
        # See connection_lost() in asyncio/streams.py to see why.
        # So let's silently ignore it when that happens.
        assert self._writer.is_closing()
        try:
            # It seems that as of Python 3.9.x it is possible for this to hang
            # indefinitely. See https://github.com/python/cpython/issues/83939
            # It sounds like this should be fixed in 3.11 but for now just
            # forcing the issue with a timeout here.
            await asyncio.wait_for(
                self._writer.wait_closed(),
                # timeout=60.0 * 6.0,
                timeout=30.0,
            )
        except asyncio.TimeoutError as exc:
            logger.info(
                'Timeout on _writer.wait_closed() for %s rpc (transport=%s).',
                self._label,
                ssl_stream_writer_underlying_transport_info(self._writer),
            )
            if self.debug_print:
                self.debug_print_call(
                    f'{self._label}: got timeout in _writer.wait_closed();'
                    ' This should be fixed in future Python versions.'
                )
            # We're done with these exceptions, so strip their
            # tracebacks to avoid reference cycles.
            strip_exception_tracebacks(exc)
        except Exception as exc:
            if not self._is_expected_connection_error(exc):
                logger.exception('Error closing _writer for %s.', self._label)
            else:
                if self.debug_print:
                    self.debug_print_call(
                        f'{self._label}: silently ignoring error in'
                        f' _writer.wait_closed(): {exc}.'
                    )
            # We're done with the exception, so strip its tracebacks to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)

        except asyncio.CancelledError:
            logger.warning(
                'RPCEndpoint.wait_closed()'
                ' got asyncio.CancelledError; not expected.'
            )
            raise
        assert not self._did_wait_closed_writer
        self._did_wait_closed_writer = True

    def _tm(self) -> str:
        """Simple readable time value for debugging."""
        tval = time.monotonic() % 100.0
        return f'{tval:.2f}'

    async def _run_read_task(self) -> None:
        """Read from the peer."""
        self._check_env()
        assert self._peer_info is None

        # Bug fix: if we don't have this set we will never time out
        # if we never receive any data from the other end.
        self._last_keepalive_receive_time = time.monotonic()

        # The first thing they should send us is their handshake; then
        # we'll know if/how we can talk to them.
        mlen = await self._read_int_32()
        message = await self._reader.readexactly(mlen)
        self._total_bytes_read += mlen
        self._peer_info = dataclass_from_json(_PeerInfo, message.decode())
        self._last_keepalive_receive_time = time.monotonic()
        if self.debug_print:
            self.debug_print_call(
                f'{self._label}: received handshake at {self._tm()}.'
            )

        # Now just sit and handle stuff as it comes in.
        while True:
            if self._closing:
                return

            # Read message type.
            mtype = _PacketType(await self._read_int_8())
            if mtype is _PacketType.HANDSHAKE:
                raise RuntimeError('Got multiple handshakes')

            if mtype is _PacketType.KEEPALIVE:
                if self.debug_print_io:
                    self.debug_print_call(
                        f'{self._label}: received keepalive'
                        f' at {self._tm()}.'
                    )
                self._last_keepalive_receive_time = time.monotonic()

            elif mtype is _PacketType.MESSAGE:
                await self._handle_message_packet(big=False)

            elif mtype is _PacketType.MESSAGE_BIG:
                await self._handle_message_packet(big=True)

            elif mtype is _PacketType.RESPONSE:
                await self._handle_response_packet(big=False)

            elif mtype is _PacketType.RESPONSE_BIG:
                await self._handle_response_packet(big=True)

            else:
                assert_never(mtype)

    async def _handle_message_packet(self, big: bool) -> None:
        assert self._peer_info is not None
        msgid = await self._read_int_16()
        if big:
            msglen = await self._read_int_32()
        else:
            msglen = await self._read_int_16()
        msg = await self._reader.readexactly(msglen)
        self._total_bytes_read += msglen
        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: received message {msgid}'
                f' of size {msglen} at {self._tm()}.'
            )

        # Create a message-task to handle this message and return
        # a response (we don't want to block while that happens).
        assert not self._closing
        self._prune_tasks()  # Keep from filling with dead tasks.
        self._tasks.append(
            asyncio.create_task(
                self._handle_raw_message(message_id=msgid, message=msg),
                name='efro rpc message handle',
            )
        )
        if self.debug_print:
            self.debug_print_call(
                f'{self._label}: done handling message at {self._tm()}.'
            )

    async def _handle_response_packet(self, big: bool) -> None:
        assert self._peer_info is not None
        msgid = await self._read_int_16()
        # Protocol 2 gained 32 bit data lengths.
        if big:
            rsplen = await self._read_int_32()
        else:
            rsplen = await self._read_int_16()
        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: received response {msgid}'
                f' of size {rsplen} at {self._tm()}.'
            )
        rsp = await self._reader.readexactly(rsplen)
        self._total_bytes_read += rsplen
        msgobj = self._in_flight_messages.get(msgid)
        if msgobj is None:
            # It's possible for us to get a response to a message
            # that has timed out. In this case we will have no local
            # record of it.
            if self.debug_print:
                self.debug_print_call(
                    f'{self._label}: got response for nonexistent'
                    f' message id {msgid}; perhaps it timed out?'
                )
        else:
            msgobj.set_response(rsp)

    async def _run_write_task(self) -> None:
        """Write to the peer."""

        self._check_env()

        # Introduce ourself so our peer knows how it can talk to us.
        data = dataclass_to_json(
            _PeerInfo(
                protocol=OUR_PROTOCOL,
                keepalive_interval=self._keepalive_interval,
            )
        ).encode()
        self._writer.write(len(data).to_bytes(4, _BYTE_ORDER) + data)

        # Now just write out-messages as they come in.
        while True:
            # Wait until some data comes in.
            await self._have_out_packets.wait()

            assert self._out_packets
            data = self._out_packets.popleft()

            # Important: only clear this once all packets are sent.
            if not self._out_packets:
                self._have_out_packets.clear()

            self._writer.write(data)

            # This should keep our writer from buffering huge amounts
            # of outgoing data. We must remember though that we also
            # need to prevent _out_packets from growing too large and
            # that part's on us.
            await self._writer.drain()

            # For now we're not applying backpressure, but let's make
            # noise if this gets out of hand.
            if len(self._out_packets) > 200:
                if not self._did_out_packets_buildup_warning:
                    logger.warning(
                        '_out_packets building up too'
                        ' much on RPCEndpoint %s.',
                        id(self),
                    )
                    self._did_out_packets_buildup_warning = True

    async def _run_keepalive_task(self) -> None:
        """Send periodic keepalive packets."""
        self._check_env()

        # We explicitly send our own keepalive packets so we can stay
        # more on top of the connection state and possibly decide to
        # kill it when contact is lost more quickly than the OS would
        # do itself (or at least keep the user informed that the
        # connection is lagging). It sounds like we could have the TCP
        # layer do this sort of thing itself but that might be
        # OS-specific so gonna go this way for now.
        while True:
            assert not self._closing
            await asyncio.sleep(self._keepalive_interval)
            if not self.test_suppress_keepalives:
                self._enqueue_outgoing_packet(
                    _PacketType.KEEPALIVE.value.to_bytes(1, _BYTE_ORDER)
                )

            # Also go ahead and handle dropping the connection if we
            # haven't heard from the peer in a while.
            # NOTE: perhaps we want to do something more exact than
            # this which only checks once per keepalive-interval?..
            now = time.monotonic()
            if (
                self._last_keepalive_receive_time is not None
                and now - self._last_keepalive_receive_time
                > self._keepalive_timeout
            ):
                if self.debug_print:
                    since = now - self._last_keepalive_receive_time
                    self.debug_print_call(
                        f'{self._label}: reached keepalive time-out'
                        f' ({since:.1f}s).'
                    )
                raise _KeepaliveTimeoutError()

    async def _run_core_task(self, tasklabel: str, call: Awaitable) -> None:
        try:
            await call
        except Exception as exc:
            # We expect connection errors to put us here, but make noise
            # if something else does.
            if not self._is_expected_connection_error(exc):
                logger.exception(
                    'Unexpected error in rpc %s %s task'
                    ' (age=%.1f, total_bytes_read=%d).',
                    self._label,
                    tasklabel,
                    time.monotonic() - self._create_time,
                    self._total_bytes_read,
                )
            else:
                if self.debug_print:
                    self.debug_print_call(
                        f'{self._label}: {tasklabel} task will exit cleanly'
                        f' due to {exc!r}.'
                    )
            # We're done with the exception, so strip its tracebacks to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)

        finally:
            # Any core task exiting triggers shutdown.
            if self.debug_print:
                self.debug_print_call(
                    f'{self._label}: {tasklabel} task exiting...'
                )
            self.close()

    async def _handle_raw_message(
        self, message_id: int, message: bytes
    ) -> None:
        try:
            response = await self._handle_raw_message_call(message)
        except Exception as exc:
            # We expect local message handler to always succeed.
            # If that doesn't happen, make a fuss so we know to fix it.
            # The other end will simply never get a response to this
            # message.
            logger.exception('Error handling raw rpc message')
            # We're done with the exception, so strip its tracebacks to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)
            return

        assert self._peer_info is not None

        if self._peer_info.protocol == 1:
            if len(response) > 65535:
                raise RuntimeError('Response cannot be larger than 65535 bytes')

        # Now send back our response.
        # Payload consists of type (1b), msgid (2b), len (2b), and data.
        if len(response) > 65535:
            self._enqueue_outgoing_packet(
                _PacketType.RESPONSE_BIG.value.to_bytes(1, _BYTE_ORDER)
                + message_id.to_bytes(2, _BYTE_ORDER)
                + len(response).to_bytes(4, _BYTE_ORDER)
                + response
            )
        else:
            self._enqueue_outgoing_packet(
                _PacketType.RESPONSE.value.to_bytes(1, _BYTE_ORDER)
                + message_id.to_bytes(2, _BYTE_ORDER)
                + len(response).to_bytes(2, _BYTE_ORDER)
                + response
            )

    async def _read_int_8(self) -> int:
        out = int.from_bytes(await self._reader.readexactly(1), _BYTE_ORDER)
        self._total_bytes_read += 1
        return out

    async def _read_int_16(self) -> int:
        out = int.from_bytes(await self._reader.readexactly(2), _BYTE_ORDER)
        self._total_bytes_read += 2
        return out

    async def _read_int_32(self) -> int:
        out = int.from_bytes(await self._reader.readexactly(4), _BYTE_ORDER)
        self._total_bytes_read += 4
        return out

    @classmethod
    def _is_expected_connection_error(cls, exc: Exception) -> bool:
        """Stuff we expect to end our connection in normal circumstances."""

        if isinstance(exc, _KeepaliveTimeoutError):
            return True

        return is_asyncio_streams_communication_error(exc)

    def _check_env(self) -> None:
        # I was seeing that asyncio stuff wasn't working as expected if
        # created in one thread and used in another (and have verified
        # that this is part of the design), so let's enforce a single
        # thread for all use of an instance.
        if current_thread() is not self._thread:
            raise RuntimeError(
                'This must be called from the same thread'
                ' that the endpoint was created in.'
            )

        # This should always be the case if thread is the same.
        assert asyncio.get_running_loop() is self._event_loop

    def _enqueue_outgoing_packet(self, data: bytes) -> None:
        """Enqueue a raw packet to be sent. Must be called from our loop."""
        self._check_env()

        if self.debug_print_io:
            self.debug_print_call(
                f'{self._label}: enqueueing outgoing packet'
                f' {data[:50]!r} at {self._tm()}.'
            )

        # Add the data and let our write task know about it.
        self._out_packets.append(data)
        self._have_out_packets.set()

    def _prune_tasks(self) -> None:
        self._tasks = self._get_live_tasks()

    def _get_live_tasks(self) -> list[asyncio.Task]:
        return [t for t in self._tasks if not t.done()]
