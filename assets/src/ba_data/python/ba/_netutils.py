# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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
    ServerCallbackType = Callable[[Union[None, Dict[str, Any]]], None]


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
        raise ValueError('addr seems to be neither v4 or v6: ' + str(addr))
    return socket_type


class ServerResponseType(Enum):
    """How to interpret responses from the server."""
    JSON = 0


class ServerCallThread(threading.Thread):
    """Thread to communicate with the master server."""

    def __init__(self, request: str, request_type: str,
                 data: Optional[Dict[str, Any]],
                 callback: Optional[ServerCallbackType],
                 response_type: ServerResponseType):
        super().__init__()
        self._request = request
        self._request_type = request_type
        if not isinstance(response_type, ServerResponseType):
            raise TypeError(f'Invalid response type: {response_type}')
        self._response_type = response_type
        self._data = {} if data is None else copy.deepcopy(data)
        self._callback: Optional[ServerCallbackType] = callback
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
        # pylint: disable=too-many-branches
        import urllib.request
        import urllib.error
        import json
        import http.client
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
                        None, {'User-Agent': _ba.app.user_agent_string}))
            elif self._request_type == 'post':
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        _ba.get_master_server_address() + '/' + self._request,
                        parse.urlencode(self._data).encode(),
                        {'User-Agent': _ba.app.user_agent_string}))
            else:
                raise TypeError('Invalid request_type: ' + self._request_type)

            # If html request failed.
            if response.getcode() != 200:
                response_data = None
            elif self._response_type == ServerResponseType.JSON:
                raw_data = response.read()

                # Empty string here means something failed server side.
                if raw_data == b'':
                    response_data = None
                else:
                    # Json.loads requires str in python < 3.6.
                    raw_data_s = raw_data.decode()
                    response_data = json.loads(raw_data_s)
            else:
                raise TypeError(f'invalid responsetype: {self._response_type}')

        except Exception as exc:
            import errno
            do_print = False
            response_data = None

            # Ignore common network errors; note unexpected ones.
            if isinstance(exc, (urllib.error.URLError, ConnectionError,
                                http.client.IncompleteRead)):
                pass
            elif isinstance(exc, OSError):
                if exc.errno == 10051:  # Windows unreachable network error.
                    pass
                elif exc.errno in [
                        errno.ETIMEDOUT, errno.EHOSTUNREACH, errno.ENETUNREACH
                ]:
                    pass
                else:
                    do_print = True
            elif (self._response_type == ServerResponseType.JSON
                  and isinstance(exc, json.decoder.JSONDecodeError)):
                pass
            else:
                do_print = True

            if do_print:
                # Any other error here is unexpected,
                # so let's make a note of it,
                print(f'Error in ServerCallThread'
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
        callback: Optional[ServerCallbackType] = None,
        response_type: ServerResponseType = ServerResponseType.JSON) -> None:
    """Make a call to the master server via a http GET."""
    ServerCallThread(request, 'get', data, callback, response_type).start()


def master_server_post(
        request: str,
        data: Dict[str, Any],
        callback: Optional[ServerCallbackType] = None,
        response_type: ServerResponseType = ServerResponseType.JSON) -> None:
    """Make a call to the master server via a http POST."""
    ServerCallThread(request, 'post', data, callback, response_type).start()
