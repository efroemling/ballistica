# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""

import json
import zlib
import time
import base64
import weakref
import urllib.parse
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING

from efro.error import CommunicationError
from efro.util import strip_exception_tracebacks
import bacommon.classic
import babase
import bascenev1

if TYPE_CHECKING:
    import concurrent.futures
    from typing import Any, Callable

    MasterServerCallback = Callable[[None | dict[str, Any]], None]


class MasterServerResponseType(Enum):
    """How to interpret responses from the v1 master-server."""

    JSON = 0


def master_server_v1_request(
    request: str,
    request_type: str,
    data: dict[str, Any] | None,
    callback: MasterServerCallback | None,
    response_type: MasterServerResponseType,
) -> None:
    """Make a call to the v1 master-server.

    The callback fires in the logic thread, in the context this was
    submitted from, and is passed the decoded response data (or None
    on errors). Replaces the old thread-per-request
    MasterServerV1CallThread; the request rides the v2 transport via
    a response future so no OS thread is needed.

    :meta private:
    """
    plus = babase.app.plus
    assert plus is not None
    classic = babase.app.classic
    assert classic is not None

    if not isinstance(response_type, MasterServerResponseType):
        raise TypeError(f'Invalid response type: {response_type}')

    appstate = babase.app.state
    if appstate.value < type(appstate).LOADING.value:
        raise RuntimeError(
            'Cannot make v1-master-server requests until app'
            ' reaches LOADING state.'
        )

    # Capture the context we were submitted from (and the current
    # activity, if any, so we can silently drop the callback if that
    # activity dies before the response arrives).
    context_ref = babase.ContextRef()
    activity = bascenev1.getactivity(doraise=False)
    activity_ref = None if activity is None else weakref.ref(activity)

    # Disallow shutdown while the request is in flight. If shutdown
    # has already begun we no-op — the callback is never called
    # (matching the old thread-based behavior).
    if not babase.shutdown_suppress_begin():
        return
    try:
        starttime = time.monotonic()
        fut = plus.cloud.send_message_future(
            bacommon.classic.LegacyRequest(
                request,
                request_type,
                classic.legacy_user_agent_string,
                urllib.parse.urlencode(_utf8_all({} if data is None else data)),
            )
        )
        fut.add_done_callback(
            partial(
                _on_master_server_v1_response,
                request,
                response_type,
                callback,
                activity_ref,
                context_ref,
                starttime,
            )
        )
    except Exception:
        babase.shutdown_suppress_end()
        raise


def _on_master_server_v1_response(
    request: str,
    response_type: MasterServerResponseType,
    callback: MasterServerCallback | None,
    activity_ref: weakref.ref[bascenev1.Activity] | None,
    context_ref: babase.ContextRef,
    starttime: float,
    fut: concurrent.futures.Future[Any],
) -> None:
    """Decode a completed v1 request and deliver its callback.

    Runs on whatever thread resolved the future (normally the
    transport thread).
    """
    # pylint: disable=too-many-positional-arguments
    response_data: None | dict[str, Any] = None
    try:
        try:
            mresponse = fut.result()
            assert isinstance(mresponse, bacommon.classic.LegacyResponse)
            mrdata: str | None
            if mresponse.data is None:
                mrdata = None
            elif mresponse.zipped:
                mrdata = zlib.decompress(
                    base64.b85decode(mresponse.data)
                ).decode()
            else:
                mrdata = mresponse.data
            if mrdata is not None:
                assert response_type is MasterServerResponseType.JSON
                response_data = json.loads(mrdata)
        except Exception as exc:
            duration = time.monotonic() - starttime
            # Ignore common network errors; note unexpected ones.
            if isinstance(exc, CommunicationError):
                babase.netlog.debug(
                    'Legacy %s request failed in %.3fs (communication error).',
                    request,
                    duration,
                )
            else:
                babase.netlog.exception(
                    'Legacy %s request failed in %.3fs.', request, duration
                )
            # We're done with the exception, so strip its tracebacks to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)
            response_data = None
    finally:
        babase.shutdown_suppress_end()

    if response_data is not None:
        babase.netlog.debug(
            'Legacy %s request succeeded in %.3fs.',
            request,
            time.monotonic() - starttime,
        )

    if callback is not None:
        babase.pushcall(
            babase.CallStrict(
                _run_master_server_v1_callback,
                callback,
                activity_ref,
                context_ref,
                response_data,
            ),
            from_other_thread=True,
            suppress_other_thread_warning=True,
        )


def _run_master_server_v1_callback(
    callback: MasterServerCallback,
    activity_ref: weakref.ref[bascenev1.Activity] | None,
    context_ref: babase.ContextRef,
    arg: None | dict[str, Any],
) -> None:
    """Run a v1 request callback in the logic thread."""
    assert babase.in_logic_thread()

    # If we were submitted from an activity context and that activity
    # has since died, do nothing.
    if activity_ref is not None:
        activity = activity_ref()
        if activity is None or activity.expired:
            return

    # Technically we could do the same check for session contexts,
    # but not gonna worry about it for now.
    with context_ref:
        callback(arg)


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
        return data.encode()
    return data
