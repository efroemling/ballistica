# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import copy
import threading
import weakref
from enum import Enum
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, Dict, Union, Callable, Optional
    import socket
    import ba
    MasterServerCallback = Callable[[Union[None, Dict[str, Any]]], None]

# Timeout for standard functions talking to the master-server/etc.
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60


class NetworkSubsystem:
    """Network related app subsystem."""

    def __init__(self) -> None:
        self.region_pings: Dict[str, float] = {}


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


class MasterServerResponseType(Enum):
    """How to interpret responses from the master-server."""
    JSON = 0


class MasterServerCallThread(threading.Thread):
    """Thread to communicate with the master-server."""

    def __init__(self, request: str, request_type: str,
                 data: Optional[Dict[str, Any]],
                 callback: Optional[MasterServerCallback],
                 response_type: MasterServerResponseType):
        super().__init__()
        self._request = request
        self._request_type = request_type
        if not isinstance(response_type, MasterServerResponseType):
            raise TypeError(f'Invalid response type: {response_type}')
        self._response_type = response_type
        self._data = {} if data is None else copy.deepcopy(data)
        self._callback: Optional[MasterServerCallback] = callback
        self._context = _ba.Context('current')

        # Save and restore the context we were created from.
        activity = _ba.getactivity(doraise=False)
        self._activity = weakref.ref(
            activity) if activity is not None else None

    def _run_callback(self, arg: Union[None, Dict[str, Any]]) -> None:
        # If we were created in an activity context and that activity has
        # since died, do nothing.
        # FIXME: Should we just be using a ContextCall instead of doing
        # this check manually?
        if self._activity is not None:
            activity = self._activity()
            if activity is None or activity.expired:
                return

        # Technically we could do the same check for session contexts,
        # but not gonna worry about it for now.
        assert self._context is not None
        assert self._callback is not None
        with self._context:
            self._callback(arg)

    def run(self) -> None:
        # pylint: disable=too-many-branches, consider-using-with
        import urllib.request
        import urllib.error
        import json
        from ba import _general
        try:
            self._data = _general.utf8_all(self._data)
            _ba.set_thread_name('BA_ServerCallThread')
            parse = urllib.parse
            if self._request_type == 'get':
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        (_ba.get_master_server_address() + '/' +
                         self._request + '?' + parse.urlencode(self._data)),
                        None, {'User-Agent': _ba.app.user_agent_string}),
                    timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS)
            elif self._request_type == 'post':
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        _ba.get_master_server_address() + '/' + self._request,
                        parse.urlencode(self._data).encode(),
                        {'User-Agent': _ba.app.user_agent_string}),
                    timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS)
            else:
                raise TypeError('Invalid request_type: ' + self._request_type)

            # If html request failed.
            if response.getcode() != 200:
                response_data = None
            elif self._response_type == MasterServerResponseType.JSON:
                raw_data = response.read()

                # Empty string here means something failed server side.
                if raw_data == b'':
                    response_data = None
                else:
                    response_data = json.loads(raw_data)
            else:
                raise TypeError(f'invalid responsetype: {self._response_type}')

        except Exception as exc:
            do_print = False
            response_data = None

            # Ignore common network errors; note unexpected ones.
            if is_urllib_network_error(exc):
                pass
            elif (self._response_type == MasterServerResponseType.JSON
                  and isinstance(exc, json.decoder.JSONDecodeError)):
                # FIXME: should handle this better; could mean either the
                # server sent us bad data or it got corrupted along the way.
                pass
            else:
                do_print = True

            if do_print:
                # Any other error here is unexpected,
                # so let's make a note of it,
                print(f'Error in MasterServerCallThread'
                      f' (response-type={self._response_type},'
                      f' response-data={response_data}):')
                import traceback
                traceback.print_exc()

        if self._callback is not None:
            _ba.pushcall(_general.Call(self._run_callback, response_data),
                         from_other_thread=True)


def master_server_get(
    request: str,
    data: Dict[str, Any],
    callback: Optional[MasterServerCallback] = None,
    response_type: MasterServerResponseType = MasterServerResponseType.JSON
) -> None:
    """Make a call to the master server via a http GET."""
    MasterServerCallThread(request, 'get', data, callback,
                           response_type).start()


def master_server_post(
    request: str,
    data: Dict[str, Any],
    callback: Optional[MasterServerCallback] = None,
    response_type: MasterServerResponseType = MasterServerResponseType.JSON
) -> None:
    """Make a call to the master server via a http POST."""
    MasterServerCallThread(request, 'post', data, callback,
                           response_type).start()
