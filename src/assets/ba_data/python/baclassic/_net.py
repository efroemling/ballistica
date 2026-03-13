# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""

from __future__ import annotations

import zlib
import copy
import time
import base64
import weakref
import threading
from enum import Enum
from typing import TYPE_CHECKING, override

from efro.error import CommunicationError
from efro.util import strip_exception_tracebacks
import bacommon.classic
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
        self._activity = None if activity is None else weakref.ref(activity)

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
    def __str__(self) -> str:
        return (
            f'<MasterServerV1CallThread id={id(self)}'
            f' request={self._request}>'
        )

    @override
    def run(self) -> None:
        import urllib.parse
        import json

        plus = babase.app.plus
        assert plus is not None
        response_data: Any = None

        starttime = time.monotonic()

        # Disallow shutdown while we're working.
        if not babase.shutdown_suppress_begin():
            # App is already shutting down, so we're a no-op.
            return

        try:
            classic = babase.app.classic
            assert classic is not None
            self._data = _utf8_all(self._data)
            babase.set_thread_name('BA_ServerCallThread')
            dataenc = urllib.parse.urlencode(self._data)

            mresponse = plus.cloud.send_message(
                bacommon.classic.LegacyRequest(
                    self._request,
                    self._request_type,
                    classic.legacy_user_agent_string,
                    dataenc,
                )
            )
            mrdata: str | None
            if mresponse.data is None:
                mrdata = None
            elif mresponse.zipped:
                mrdata = zlib.decompress(
                    base64.b85decode(mresponse.data)
                ).decode()
            else:
                mrdata = mresponse.data

            if mrdata is None:
                response_data = None
            else:
                assert self._response_type == MasterServerResponseType.JSON
                response_data = json.loads(mrdata)

        except Exception as exc:
            duration = time.monotonic() - starttime
            # Ignore common network errors; note unexpected ones.
            if isinstance(exc, CommunicationError):
                babase.netlog.debug(
                    'Legacy %s request failed in %.3fs (communication error).',
                    self._request,
                    duration,
                )
            else:
                babase.netlog.exception(
                    'Legacy %s request failed in %.3fs.',
                    self._request,
                    duration,
                )
            response_data = None

            # We're done with the exception, so strip its tracebacks to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)

        finally:
            babase.shutdown_suppress_end()

        if response_data is not None:
            duration = time.monotonic() - starttime
            babase.netlog.debug(
                'Legacy %s request succeeded in %.3fs.', self._request, duration
            )

        if self._callback is not None:
            babase.pushcall(
                babase.CallStrict(self._run_callback, response_data),
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
