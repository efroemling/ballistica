# Released under the MIT License. See LICENSE for details.
#
"""Network related functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def is_urllib_network_error(exc: BaseException) -> bool:
    """Is the provided exception a network-related error?

    This should be passed an exception which resulted from opening or
    reading a urllib Request. It should return True for any errors that
    could conceivably arise due to unavailable/poor network connections,
    firewall/connectivity issues, etc. These issues can often be safely
    ignored or presented to the user as general 'network-unavailable'
    states.
    """
    import urllib.request
    import urllib.error
    import http.client
    import errno
    import socket
    if isinstance(
            exc,
        (urllib.error.URLError, ConnectionError, http.client.IncompleteRead,
         http.client.BadStatusLine, socket.timeout)):
        return True
    if isinstance(exc, OSError):
        if exc.errno == 10051:  # Windows unreachable network error.
            return True
        if exc.errno in {
                errno.ETIMEDOUT,
                errno.EHOSTUNREACH,
                errno.ENETUNREACH,
        }:
            return True
    return False


def is_udp_network_error(exc: BaseException) -> bool:
    """Is the provided exception a network-related error?

    This should be passed an exception which resulted from creating and
    using a socket.SOCK_DGRAM type socket. It should return True for any
    errors that could conceivably arise due to unavailable/poor network
    connections, firewall/connectivity issues, etc. These issues can often
    be safely ignored or presented to the user as general
    'network-unavailable' states.
    """
    import errno
    if isinstance(exc, ConnectionRefusedError):
        return True
    if isinstance(exc, OSError):
        if exc.errno == 10051:  # Windows unreachable network error.
            return True
        if exc.errno in {
                errno.EADDRNOTAVAIL,
                errno.ETIMEDOUT,
                errno.EHOSTUNREACH,
                errno.ENETUNREACH,
                errno.EINVAL,
                errno.EPERM,
                errno.EACCES,
                # Windows 'invalid argument' error.
                10022,
                # Windows 'a socket operation was attempted to'
                #         'an unreachable network' error.
                10051,
        }:
            return True
    return False
