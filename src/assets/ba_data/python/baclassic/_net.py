# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import copy
import threading
import weakref
from enum import Enum
from typing import TYPE_CHECKING

import _babase
import _bascenev1
from babase.internal import DEFAULT_REQUEST_TIMEOUT_SECONDS

if TYPE_CHECKING:
    from typing import Any, Callable
    import socket

    MasterServerCallback = Callable[[None | dict[str, Any]], None]


class MasterServerResponseType(Enum):
    """How to interpret responses from the v1 master-server."""

    JSON = 0


class MasterServerV1CallThread(threading.Thread):
    """Thread to communicate with the v1 master-server."""

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
        self._context = _babase.ContextRef()

        # Save and restore the context we were created from.
        activity = _bascenev1.getactivity(doraise=False)
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
        from babase._general import Call, utf8_all

        plus = _babase.app.plus
        assert plus is not None
        response_data: Any = None
        url: str | None = None
        try:
            assert _babase.app.classic is not None
            self._data = utf8_all(self._data)
            _babase.set_thread_name('BA_ServerCallThread')
            if self._request_type == 'get':
                url = (
                    plus.get_master_server_address()
                    + '/'
                    + self._request
                    + '?'
                    + urllib.parse.urlencode(self._data)
                )
                assert url is not None
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        url,
                        None,
                        {'User-Agent': _babase.app.classic.user_agent_string},
                    ),
                    context=_babase.app.net.sslcontext,
                    timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
                )
            elif self._request_type == 'post':
                url = plus.get_master_server_address() + '/' + self._request
                assert url is not None
                response = urllib.request.urlopen(
                    urllib.request.Request(
                        url,
                        urllib.parse.urlencode(self._data).encode(),
                        {'User-Agent': _babase.app.classic.user_agent_string},
                    ),
                    context=_babase.app.net.sslcontext,
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
            _babase.pushcall(
                Call(self._run_callback, response_data), from_other_thread=True
            )
