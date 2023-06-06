# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import ssl
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import socket

# Timeout for standard functions talking to the master-server/etc.
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60


class NetworkSubsystem:
    """Network related app subsystem."""

    def __init__(self) -> None:
        # Anyone accessing/modifying zone_pings should hold this lock,
        # as it is updated by a background thread.
        self.zone_pings_lock = threading.Lock()

        # Zone IDs mapped to average pings. This will remain empty
        # until enough pings have been run to be reasonably certain
        # that a nearby server has been pinged.
        self.zone_pings: dict[str, float] = {}

        self._sslcontext: ssl.SSLContext | None = None

        # For debugging.
        self.v1_test_log: str = ''
        self.v1_ctest_results: dict[int, str] = {}
        self.server_time_offset_hours: float | None = None

    @property
    def sslcontext(self) -> ssl.SSLContext:
        """Create/return our shared SSLContext.

        This can be reused for all standard urllib requests/etc.
        """
        # Note: I've run into older Android devices taking upwards of 1 second
        # to put together a default SSLContext, so recycling one can definitely
        # be a worthwhile optimization. This was suggested to me in this
        # thread by one of Python's SSL maintainers:
        # https://github.com/python/cpython/issues/94637
        if self._sslcontext is None:
            self._sslcontext = ssl.create_default_context()
        return self._sslcontext


def get_ip_address_type(addr: str) -> socket.AddressFamily:
    """Return socket.AF_INET6 or socket.AF_INET4 for the provided address."""
    import socket

    socket_type = None

    # First try it as an ipv4 address.
    try:
        socket.inet_pton(socket.AF_INET, addr)
        socket_type = socket.AF_INET
    except OSError:
        pass

    # Hmm apparently not ipv4; try ipv6.
    if socket_type is None:
        try:
            socket.inet_pton(socket.AF_INET6, addr)
            socket_type = socket.AF_INET6
        except OSError:
            pass
    if socket_type is None:
        raise ValueError(f'addr seems to be neither v4 or v6: {addr}')
    return socket_type
