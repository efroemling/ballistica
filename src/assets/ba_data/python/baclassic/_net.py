# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import copy
import weakref
import threading
from enum import Enum
from typing import TYPE_CHECKING, override

from efro.util import strip_exception_tracebacks
import babase
import bascenev1

if TYPE_CHECKING:
    from typing import Any, Callable

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
        # pylint: disable=too-many-positional-arguments

        super().__init__()
        self._request = request
        self._request_type = request_type
        if not isinstance(response_type, MasterServerResponseType):
            raise TypeError(f'Invalid response type: {response_type}')
        self._response_type = response_type
        self._data = {} if data is None else copy.deepcopy(data)
        self._callback: MasterServerCallback | None = callback
        self._context = babase.ContextRef()

        appstate = babase.app.state
        if appstate.value < type(appstate).LOADING.value:
            raise RuntimeError(
                'Cannot use MasterServerV1CallThread'
                ' until app reaches LOADING state.'
            )

        # Save and restore the context we were created from.
        activity = bascenev1.getactivity(doraise=False)
        self._activity = weakref.ref(activity) if activity is not None else None

    def _run_callback(self, arg: None | dict[str, Any]) -> None:
        # If we were created in an activity context and that activity
        # has since died, do nothing.

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

    @override
    def run(self) -> None:
        # pylint: disable=too-many-branches
        import urllib.parse
        import json

        from efro.error import is_urllib3_communication_error

        plus = babase.app.plus
        assert plus is not None
        response_data: Any = None
        url: str | None = None

        # Tearing the app down while this is running can lead to
        # rare crashes in LibSSL, so avoid that if at all possible.
        if not babase.shutdown_suppress_begin():
            # App is already shutting down, so we're a no-op.
            return

        upool = babase.app.net.urllib3pool

        try:
            classic = babase.app.classic
            assert classic is not None
            self._data = _utf8_all(self._data)
            babase.set_thread_name('BA_ServerCallThread')
            if self._request_type == 'get':
                msaddr = plus.get_master_server_address()
                dataenc = urllib.parse.urlencode(self._data)
                url = f'{msaddr}/{self._request}?{dataenc}'
                assert url is not None
                response = upool.request(
                    'GET',
                    url,
                    headers={'User-Agent': classic.legacy_user_agent_string},
                )
            elif self._request_type == 'post':
                url = f'{plus.get_master_server_address()}/{self._request}'
                assert url is not None

                # Note: we could use 'fields' here instead of
                # urlencoding ourself, but we'd need to convert
                # self._data to strings/bytes.
                response = upool.request(
                    'POST',
                    url,
                    body=urllib.parse.urlencode(self._data).encode(),
                    headers={
                        'User-Agent': classic.legacy_user_agent_string,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                )

            else:
                raise TypeError('Invalid request_type: ' + self._request_type)

            # If html request failed.
            if response.status != 200:
                response_data = None
            elif self._response_type == MasterServerResponseType.JSON:
                raw_data = response.data

                # Empty string here means something failed server side.
                if raw_data == b'':
                    response_data = None
                else:
                    response_data = json.loads(raw_data)
            else:
                raise TypeError(f'invalid responsetype: {self._response_type}')

        except Exception as exc:
            # Ignore common network errors; note unexpected ones.
            if not is_urllib3_communication_error(exc, url=url):
                print(
                    f'Error in MasterServerCallThread'
                    f' (url={url},'
                    f' response-type={self._response_type},'
                    f' response-data={response_data}):'
                )
                import traceback

                traceback.print_exc()

            response_data = None

            # We're done with the exception, so strip its tracebacks to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)

        finally:
            babase.shutdown_suppress_end()

        if self._callback is not None:
            babase.pushcall(
                babase.Call(self._run_callback, response_data),
                from_other_thread=True,
            )


def _utf8_all(data: Any) -> Any:
    """Convert all strings in provided data to utf-8 bytes."""
    if isinstance(data, dict):
        return dict(
            (_utf8_all(key), _utf8_all(value))
            for key, value in list(data.items())
        )
    if isinstance(data, list):
        return [_utf8_all(element) for element in data]
    if isinstance(data, tuple):
        return tuple(_utf8_all(element) for element in data)
    if isinstance(data, str):
        # return data.encode('utf-8', errors='ignore')
        return data.encode()
    return data
