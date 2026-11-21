# Released under the MIT License. See LICENSE for details.
#
"""A UDP endpoint spanning IPv4 and IPv6."""

import sys
import socket
import asyncio
import logging
from typing import TYPE_CHECKING, override

from efro.util import strip_exception_tracebacks

if TYPE_CHECKING:
    from typing import Any, Callable

logger = logging.getLogger('ba.net')


class DualStackUDPEndpoint:
    """An IPv4 and (where available) an IPv6 UDP socket used as one.

    Sends go out whichever socket matches the destination's family,
    scoped link-local IPv6 addresses such as ``fe80::1%en0`` included.
    Everything received on either lands in ``on_datagram`` with the
    sender as a plain ``(address, port)`` pair, link-local senders
    carrying their interface the same way. The IPv4 socket allows
    broadcast. Errors land in ``on_error`` along with the address being
    sent to when the error came from that send (as most do), or None.
    Use it from the thread running its asyncio loop.
    """

    def __init__(
        self,
        on_datagram: Callable[[bytes, tuple[str, int]], None],
        on_error: Callable[[Exception, tuple[str, int] | None], None],
    ) -> None:
        self._on_datagram = on_datagram
        self._on_error = on_error
        self._transport4: asyncio.DatagramTransport | None = None
        self._transport6: asyncio.DatagramTransport | None = None
        # Where the send in progress is going (a failed send reports
        # its error to the protocol from inside the transport's sendto).
        self._sending_to: tuple[str, int] | None = None

    async def open(self) -> bool:
        """Open the sockets; return whether at least one opened."""
        loop = asyncio.get_running_loop()
        try:
            transport4, _ = await loop.create_datagram_endpoint(
                lambda: _EndpointProtocol(self),
                local_addr=('0.0.0.0', 0),
                allow_broadcast=True,
            )
            assert isinstance(transport4, asyncio.DatagramTransport)
            self._transport4 = transport4
        except OSError as exc:
            logger.debug('Unable to open IPv4 UDP socket: %s', exc)
            strip_exception_tracebacks(exc)
        try:
            transport6, _ = await loop.create_datagram_endpoint(
                lambda: _EndpointProtocol(self),
                local_addr=('::', 0),
                family=socket.AF_INET6,
            )
            assert isinstance(transport6, asyncio.DatagramTransport)
            self._transport6 = transport6
        except OSError as exc:
            # (No IPv6 on this system; IPv4 alone is fine.)
            logger.debug('Unable to open IPv6 UDP socket: %s', exc)
            strip_exception_tracebacks(exc)
        return self._transport4 is not None or self._transport6 is not None

    def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
        """Send a datagram (never blocks; errors go to ``on_error``)."""
        self._sending_to = addr
        try:
            self._sendto(data, addr)
        finally:
            self._sending_to = None

    def _sendto(self, data: bytes, addr: tuple[str, int]) -> None:
        host, port = addr
        if ':' not in host:
            if self._transport4 is not None:
                self._transport4.sendto(data, addr)
            return
        if self._transport6 is None:
            return
        # Always the 4-tuple form: Python's socket layer ignores a
        # '%iface' scope in the address text (it must ride in the
        # scope-id slot), and Windows' proactor loop reads any 2-tuple as
        # IPv4 (so IPv6 text in one fails with WSAEINVAL).
        scope_id = 0
        if '%' in host:
            host, scope = host.split('%', 1)
            try:
                scope_id = (
                    int(scope)
                    if scope.isdigit()
                    else socket.if_nametoindex(scope)
                )
            except OSError as exc:
                self._on_error(exc, addr)
                return
        self._transport6.sendto(data, (host, port, 0, scope_id))

    def close(self) -> None:
        """Close the sockets."""
        for transport in (self._transport4, self._transport6):
            if transport is not None:
                transport.close()
        self._transport4 = self._transport6 = None

    def handle_datagram(self, data: bytes, addr: Any) -> None:
        """Called by our sockets.

        :meta private:
        """
        # IPv6 senders arrive as 4-tuples whose last slot is the scope
        # (interface) for link-local ones; fold that into the text form
        # used everywhere else ('fe80::1%en0'), which some platforms
        # already give us.
        # (Windows scopes stay numeric, as native code there writes and
        # parses them.)
        host = str(addr[0])
        if len(addr) >= 4 and addr[3] and '%' not in host:
            if sys.platform == 'win32':
                host = f'{host}%{addr[3]}'
            else:
                try:
                    host = f'{host}%{socket.if_indextoname(addr[3])}'
                except OSError:
                    host = f'{host}%{addr[3]}'
        self._on_datagram(data, (host, int(addr[1])))

    def handle_error(self, exc: Exception) -> None:
        """Called by our sockets.

        :meta private:
        """
        self._on_error(exc, self._sending_to)


class _EndpointProtocol(asyncio.DatagramProtocol):
    """Feeds one of a DualStackUDPEndpoint's sockets into it."""

    def __init__(self, endpoint: DualStackUDPEndpoint) -> None:
        # (The endpoint closes our transport before it goes away, which
        # ends this reference.)
        self._endpoint = endpoint

    @override
    def datagram_received(self, data: bytes, addr: Any) -> None:
        self._endpoint.handle_datagram(data, addr)

    @override
    def error_received(self, exc: Exception) -> None:
        self._endpoint.handle_error(exc)
