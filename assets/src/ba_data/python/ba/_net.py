# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import ssl
import copy
import threading
import weakref
from enum import Enum
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, Callable
    import socket

    MasterServerCallback = Callable[[None | dict[str, Any]], None]

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


class MasterServerResponseType(Enum):
    """How to interpret responses from the master-server."""

    JSON = 0


class MasterServerCallThread(threading.Thread):
    """Thread to communicate with the master-server."""

    def __init__(
        self,
        request: str,
        request_type: str,
        data: dict[str, Any] | None,
        callback: MasterServerCallback | None,
        response_type: MasterServerResponseType,
    ):
        super().__init__()
        self._request = request
        self._request_type = request_type
        if not isinstance(response_type, MasterServerResponseType):
            raise TypeError(f'Invalid response type: {response_type}')
        self._response_type = response_type
        self._data = {} if data is None else copy.deepcopy(data)
        self._callback: MasterServerCallback | None = callback
        self._context = _ba.Context('current')

        # Save and restore the context we were created from.
        activity = _ba.getactivity(doraise=False)
        self._activity = weakref.ref(activity) if activity is not None else None

    def _run_callback(self, arg: None | dict[str, Any]) -> None:
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
        # pylint: disable=consider-using-with
        import urllib.request
        import urllib.parse
        import urllib.error
        import json

        from efro.error import is_urllib_communication_error
        from ba._general import Call, utf8_all
        from ba._internal import get_master_server_address

        response_data: Any = None
        url: str | None = None
        try:
            self._data = utf8_all(self._data)
            _ba.set_thread_name('BA_ServerCallThread')
            if self._request_type == 'get':
                url = (
                    get_master_server_address()
                    + '/'
                    + self._request
                    + '?'
                    + urllib.parse.urlencode(self._data)
                )
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        url, None, {'User-Agent': _ba.app.user_agent_string}
                    ),
                    context=_ba.app.net.sslcontext,
                    timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
                )
            elif self._request_type == 'post':
                url = get_master_server_address() + '/' + self._request
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        url,
                        urllib.parse.urlencode(self._data).encode(),
                        {'User-Agent': _ba.app.user_agent_string},
                    ),
                    context=_ba.app.net.sslcontext,
                    timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
                )
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

            # Ignore common network errors; note unexpected ones.
            if not is_urllib_communication_error(exc, url=url):
                print(
                    f'Error in MasterServerCallThread'
                    f' (url={url},'
                    f' response-type={self._response_type},'
                    f' response-data={response_data}):'
                )
                import traceback

                traceback.print_exc()

            response_data = None

        if self._callback is not None:
            _ba.pushcall(
                Call(self._run_callback, response_data), from_other_thread=True
            )


def master_server_get(
    request: str,
    data: dict[str, Any],
    callback: MasterServerCallback | None = None,
    response_type: MasterServerResponseType = MasterServerResponseType.JSON,
) -> None:
    """Make a call to the master server via a http GET."""
    MasterServerCallThread(
        request, 'get', data, callback, response_type
    ).start()


def master_server_post(
    request: str,
    data: dict[str, Any],
    callback: MasterServerCallback | None = None,
    response_type: MasterServerResponseType = MasterServerResponseType.JSON,
) -> None:
    """Make a call to the master server via a http POST."""
    MasterServerCallThread(
        request, 'post', data, callback, response_type
    ).start()
