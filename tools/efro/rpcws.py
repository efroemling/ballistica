# Released under the MIT License. See LICENSE for details.
#
"""Remote procedure call functionality over WebSockets."""

from __future__ import annotations

import time
import asyncio
import logging
from typing import TYPE_CHECKING, Protocol

from efro.error import CommunicationError
from efro.util import gather_strip

if TYPE_CHECKING:
    from typing import Awaitable, Callable, Literal

logger = logging.getLogger(__name__)


class WebSocketTransport(Protocol):
    """Minimal interface for a WebSocket connection.

    This allows the RPC layer to work with any WebSocket library
    (websockets, aiohttp, etc.) via a thin adapter.
    """

    async def send(self, data: bytes) -> None:
        """Send binary data."""

    async def recv(self) -> bytes:
        """Receive binary data."""

    async def close(self) -> None:
        """Close the connection."""


class _InFlightMessage:
    """Represents a message that is out on the wire."""

    def __init__(self, message_id: int) -> None:
        self._response: bytes | None = None
        self._got_response = asyncio.Event()
        self.wait_task = asyncio.create_task(
            self._wait(), name=f'rpcws in-flight-msg {message_id} wait'
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


# Packet type bytes prepended to each WebSocket message.
_TYPE_MESSAGE: int = 0
_TYPE_RESPONSE: int = 1

_BYTE_ORDER: Literal['big'] = 'big'


class RPCWSEndpoint:
    """Facilitates asynchronous multiplexed remote procedure calls
    over WebSockets.

    Similar to RPCEndpoint but leverages WebSocket framing for message
    boundaries and WebSocket ping/pong for keepalive, resulting in a
    simpler implementation.
    """

    # How long we should wait before giving up on a message by default.
    # Note this includes processing time on the other end.
    DEFAULT_MESSAGE_TIMEOUT = 60.0

    def __init__(
        self,
        handle_raw_message_call: Callable[[bytes], Awaitable[bytes]],
        transport: WebSocketTransport,
        label: str,
        *,
        debug_print: bool = False,
        debug_print_call: Callable[[str], None] | None = None,
    ) -> None:
        self._handle_raw_message_call: (
            Callable[[bytes], Awaitable[bytes]] | None
        ) = handle_raw_message_call
        self._transport = transport
        self._label = label
        self.debug_print = debug_print
        if debug_print_call is None:
            debug_print_call = print
        self.debug_print_call: Callable[[str], None] = debug_print_call
        self._closing = False
        self._did_wait_closed = False
        self._event_loop = asyncio.get_running_loop()
        self._run_called = False
        self._create_time = time.monotonic()

        self._tasks: list[asyncio.Task] = []
        self._transport_close_task: asyncio.Task | None = None

        # (Start near the end to make sure our looping logic is sound).
        self._next_message_id = 65530

        self._in_flight_messages: dict[int, _InFlightMessage] = {}

        if self.debug_print:
            self.debug_print_call(f'{self._label}: connected at {self._tm()}.')

    async def run(self) -> None:
        """Run the endpoint until the connection is lost or closed."""
        if self._run_called:
            raise RuntimeError('Run can be called only once per endpoint.')
        self._run_called = True

        try:
            await self._run_read_loop()
        except asyncio.CancelledError:
            logger.warning(
                'RPCWSEndpoint.run cancelled; want to try and avoid this.'
            )
            raise
        except CommunicationError:
            if self.debug_print:
                self.debug_print_call(f'{self._label}: connection ended.')
        except Exception:
            logger.exception(
                'Unexpected error in rpcws %s read loop (age=%.1f).',
                self._label,
                time.monotonic() - self._create_time,
            )
        finally:
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
        if self._closing:
            raise CommunicationError('Endpoint is closed.')

        # message_id is a 16 bit looping value.
        message_id = self._next_message_id
        self._next_message_id = (self._next_message_id + 1) % 65536

        # Make an entry so we know this message is out there.
        assert message_id not in self._in_flight_messages
        msgobj = self._in_flight_messages[message_id] = _InFlightMessage(
            message_id
        )

        # Also add its task to our list so we properly cancel it if we
        # die.
        self._prune_tasks()
        self._tasks.append(msgobj.wait_task)

        if timeout is None:
            timeout = self.DEFAULT_MESSAGE_TIMEOUT
        assert timeout is not None

        return self._send_message(
            message, timeout, close_on_error, msgobj.wait_task, message_id
        )

    async def _send_message(
        self,
        message: bytes,
        timeout: float,
        close_on_error: bool,
        bytes_awaitable: asyncio.Task[bytes],
        message_id: int,
    ) -> bytes:
        # pylint: disable=too-many-positional-arguments

        # Build the wire frame: type(1b) + message_id(2b) + payload.
        frame = (
            _TYPE_MESSAGE.to_bytes(1, _BYTE_ORDER)
            + message_id.to_bytes(2, _BYTE_ORDER)
            + message
        )

        try:
            await self._transport.send(frame)
        except Exception as exc:
            bytes_awaitable.cancel()
            del self._in_flight_messages[message_id]
            if close_on_error:
                self.close()
            raise CommunicationError() from exc

        if self.debug_print:
            self.debug_print_call(
                f'{self._label}: sent message {message_id}'
                f' of size {len(message)} at {self._tm()}.'
            )

        try:
            return await asyncio.wait_for(bytes_awaitable, timeout=timeout)
        except asyncio.CancelledError as exc:
            current_task = asyncio.current_task()
            if current_task is not None and current_task.cancelling() > 0:
                raise
            if self.debug_print:
                self.debug_print_call(
                    f'{self._label}: message {message_id} was cancelled.'
                )
            if close_on_error:
                self.close()
            raise CommunicationError() from exc
        except asyncio.TimeoutError as exc:
            if self.debug_print:
                self.debug_print_call(
                    f'{self._label}: message {message_id} timed out.'
                )
            bytes_awaitable.cancel()
            del self._in_flight_messages[message_id]
            if close_on_error:
                self.close()
            raise CommunicationError() from exc

    def close(self) -> None:
        """Begin closing the endpoint."""
        if self._closing:
            return

        if self.debug_print:
            self.debug_print_call(f'{self._label}: closing...')

        self._closing = True

        # Kill all of our in-flight tasks.
        for task in self._get_live_tasks():
            task.cancel()

        # Close the underlying transport so our read loop unblocks
        # immediately and any peer blocked in recv() notices the
        # disconnect right away instead of waiting for a message
        # timeout. This matches rpc.py's synchronous writer.close().
        self._transport_close_task = asyncio.create_task(
            self._transport.close(),
            name=f'{self._label} transport close',
        )

        # Drop our reference to the user-supplied handler so we don't
        # keep a dependency loop alive. Set to None rather than deleting
        # so dispatched-but-not-yet-run handler tasks can see we're
        # closed instead of hitting AttributeError.
        self._handle_raw_message_call = None

    def is_closing(self) -> bool:
        """Have we begun the process of closing?"""
        return self._closing

    async def wait_closed(self) -> None:
        """Wait for the endpoint to finish closing.

        This is called by run() so generally does not need to be
        explicitly called.
        """
        if self._did_wait_closed:
            return
        self._did_wait_closed = True

        if not self._closing:
            raise RuntimeError('Must be called after close()')

        live_tasks = self._get_live_tasks()
        self._tasks = []

        if live_tasks:
            results = await gather_strip(*live_tasks)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(
                        'Got unexpected error cleaning up %s task: %s',
                        self._label,
                        result,
                    )

        # Wait for the transport close scheduled by close().
        if self._transport_close_task is not None:
            try:
                await asyncio.wait_for(self._transport_close_task, timeout=10.0)
            except Exception:
                pass

    async def _run_read_loop(self) -> None:
        """Read incoming WebSocket messages and dispatch them."""
        while not self._closing:
            try:
                raw = await self._transport.recv()
            except Exception as exc:
                # If we're closing, the recv error is expected.
                if self.is_closing():
                    return
                raise CommunicationError() from exc

            if len(raw) < 3:
                raise CommunicationError('Invalid rpcws frame.')

            ptype = raw[0]
            message_id = int.from_bytes(raw[1:3], _BYTE_ORDER)
            payload = raw[3:]

            if ptype == _TYPE_MESSAGE:
                if self.debug_print:
                    self.debug_print_call(
                        f'{self._label}: received message {message_id}'
                        f' of size {len(payload)} at {self._tm()}.'
                    )
                self._prune_tasks()
                self._tasks.append(
                    asyncio.create_task(
                        self._handle_raw_message(
                            message_id=message_id, message=payload
                        ),
                        name='rpcws message handle',
                    )
                )

            elif ptype == _TYPE_RESPONSE:
                if self.debug_print:
                    self.debug_print_call(
                        f'{self._label}: received response {message_id}'
                        f' of size {len(payload)} at {self._tm()}.'
                    )
                msgobj = self._in_flight_messages.get(message_id)
                if msgobj is None:
                    if self.debug_print:
                        self.debug_print_call(
                            f'{self._label}: got response for nonexistent'
                            f' message id {message_id};'
                            f' perhaps it timed out?'
                        )
                else:
                    msgobj.set_response(payload)

            else:
                raise CommunicationError(f'Invalid rpcws packet type: {ptype}.')

    async def _handle_raw_message(
        self, message_id: int, message: bytes
    ) -> None:
        handler = self._handle_raw_message_call
        if handler is None:
            # Endpoint closed between dispatch and this task running.
            return
        try:
            response = await handler(message)
        except Exception:
            logger.exception('Error handling raw rpcws message')
            return

        # Send back the response.
        frame = (
            _TYPE_RESPONSE.to_bytes(1, _BYTE_ORDER)
            + message_id.to_bytes(2, _BYTE_ORDER)
            + response
        )
        try:
            await self._transport.send(frame)
        except Exception:
            if not self._closing:
                logger.warning(
                    'Error sending rpcws response for message %d.',
                    message_id,
                )

    def _tm(self) -> str:
        """Simple readable time value for debugging."""
        tval = time.monotonic() % 100.0
        return f'{tval:.2f}'

    def _prune_tasks(self) -> None:
        self._tasks = self._get_live_tasks()

    def _get_live_tasks(self) -> list[asyncio.Task]:
        return [t for t in self._tasks if not t.done()]
