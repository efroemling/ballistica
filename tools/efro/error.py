# Released under the MIT License. See LICENSE for details.
#
"""Common errors and related functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING
import errno

if TYPE_CHECKING:
    pass


class CleanError(Exception):
    """An error that can be presented to the user as a simple message.

    These errors should be completely self-explanatory, to the point where
    a traceback or other context would not be useful.

    A CleanError with no message can be used to inform a script to fail
    without printing any message.

    This should generally be limited to errors that will *always* be
    presented to the user (such as those in high level tool code).
    Exceptions that may be caught and handled by other code should use
    more descriptive exception types.
    """

    def pretty_print(self, flush: bool = False) -> None:
        """Print the error to stdout, using red colored output if available.

        If the error has an empty message, prints nothing (not even a newline).
        """
        from efro.terminal import Clr

        errstr = str(self)
        if errstr:
            print(f'{Clr.SRED}{errstr}{Clr.RST}', flush=flush)


class CommunicationError(Exception):
    """A communication related error has occurred.

    This covers anything network-related going wrong in the sending
    of data or receiving of a response. Basically anything that is out
    of our control should get lumped in here. This error does not imply
    that data was not received on the other end; only that a full
    acknowledgement round trip was not completed.

    These errors should be gracefully handled whenever possible, as
    occasional network issues are unavoidable.
    """


class RemoteError(Exception):
    """An error occurred on the other end of some connection.

    This occurs when communication succeeds but another type of error
    occurs remotely. The error string can consist of a remote stack
    trace or a simple message depending on the context.

    Communication systems should raise more specific error types locally
    when more introspection/control is needed; this is intended somewhat
    as a catch-all.
    """

    def __init__(self, msg: str, peer_desc: str):
        super().__init__(msg)
        self._peer_desc = peer_desc

    def __str__(self) -> str:
        s = ''.join(str(arg) for arg in self.args)
        # Indent so we can more easily tell what is the remote part when
        # this is in the middle of a long exception chain.
        padding = '  '
        s = ''.join(padding + line for line in s.splitlines(keepends=True))
        return f'The following occurred on {self._peer_desc}:\n{s}'


class IntegrityError(ValueError):
    """Data has been tampered with or corrupted in some form."""


def is_urllib_communication_error(exc: BaseException, url: str | None) -> bool:
    """Is the provided exception from urllib a communication-related error?

    Url, if provided can provide extra context for when to treat an error
    as such an error.

    This should be passed an exception which resulted from opening or
    reading a urllib Request. It returns True for any errors that could
    conceivably arise due to unavailable/poor network connections,
    firewall/connectivity issues, or other issues out of our control.
    These errors can often be safely ignored or presented to the user
    as general 'network-unavailable' states.
    """
    import urllib.error
    import http.client
    import socket

    if isinstance(
        exc,
        (
            urllib.error.URLError,
            ConnectionError,
            http.client.IncompleteRead,
            http.client.BadStatusLine,
            http.client.RemoteDisconnected,
            socket.timeout,
        ),
    ):

        # Special case: although an HTTPError is a subclass of URLError,
        # we don't consider it a communication error. It generally means we
        # have successfully communicated with the server but what we are asking
        # for is not there/etc.
        if isinstance(exc, urllib.error.HTTPError):

            # Special sub-case: appspot.com hosting seems to give 403 errors
            # (forbidden) to some countries. I'm assuming for legal reasons?..
            # Let's consider that a communication error since its out of our
            # control so we don't fill up logs with it.
            if exc.code == 403 and url is not None and '.appspot.com' in url:
                return True

            return False

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


def is_requests_communication_error(exc: BaseException) -> bool:
    """Is the provided exception a communication-related error from requests?"""
    import requests

    # Looks like this maps pretty well onto requests' ConnectionError
    return isinstance(exc, requests.ConnectionError)


def is_udp_communication_error(exc: BaseException) -> bool:
    """Should this udp-related exception be considered a communication error?

    This should be passed an exception which resulted from creating and
    using a socket.SOCK_DGRAM type socket. It should return True for any
    errors that could conceivably arise due to unavailable/poor network
    conditions, firewall/connectivity issues, etc. These issues can often
    be safely ignored or presented to the user as general
    'network-unavailable' states.
    """
    if isinstance(exc, ConnectionRefusedError | TimeoutError):
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


def is_asyncio_streams_communication_error(exc: BaseException) -> bool:
    """Should this streams error be considered a communication error?

    This should be passed an exception which resulted from creating and
    using asyncio streams. It should return True for any errors that could
    conceivably arise due to unavailable/poor network connections,
    firewall/connectivity issues, etc. These issues can often be safely
    ignored or presented to the user as general 'connection-lost' events.
    """
    import ssl

    if isinstance(
        exc,
        (
            ConnectionError,
            TimeoutError,
            EOFError,
        ),
    ):
        return True

    # Also some specific errno ones.
    if isinstance(exc, OSError):
        if exc.errno == 10051:  # Windows unreachable network error.
            return True
        if exc.errno in {
            errno.ETIMEDOUT,
            errno.EHOSTUNREACH,
            errno.ENETUNREACH,
        }:
            return True

    # Am occasionally getting a specific SSL error on shutdown which I
    # believe is harmless (APPLICATION_DATA_AFTER_CLOSE_NOTIFY).
    # It sounds like it may soon be ignored by Python (as of March 2022).
    # Let's still complain, however, if we get any SSL errors besides
    # this one. https://bugs.python.org/issue39951
    if isinstance(exc, ssl.SSLError):
        excstr = str(exc)
        if 'APPLICATION_DATA_AFTER_CLOSE_NOTIFY' in excstr:
            return True

        # Also occasionally am getting WRONG_VERSION_NUMBER ssl errors;
        # Assuming this just means client is attempting to connect from some
        # outdated browser or whatnot.
        if 'SSL: WRONG_VERSION_NUMBER' in excstr:
            return True

    return False
