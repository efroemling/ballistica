# Released under the MIT License. See LICENSE for details.
#
"""WebSocket-based stream consumer for bacloud (Phase 2).

A stream-mode bacloud kickoff lands at a basn node, which injects a
``StreamWS`` into the response pointing at its own
``/streamcall/<call_id>`` WebSocket endpoint. We open that WS, print
``StreamOutput`` frames live as they arrive, and return the terminal
``StreamFinal`` so the caller can splice it back into bacloud's
existing response-handling flow.

On a non-terminal close (network blip, abnormal close, expired
token) we reconnect — refreshing the token via ``POST
/streamcall/<call_id>/refresh-token`` first if the close code says
the token is expired (4001). Reconnects use exponential backoff up
to a configurable wall-clock budget (default 60s, override via
``BACLOUD_RECONNECT_BUDGET_SECONDS``); past the budget we surface
``CleanError``. Token-bad / call-id-mismatch / no-token closes
(4002/4003/4004) are fatal — no retry.

v0 reconnect doesn't ask basn to replay the cursor: a reconnecting
client may miss frames that landed during the disconnect window. In
practice the stream still completes (the basn-side subscription
keeps polling regardless of WS attachments), and bacloud renders the
terminal ``StreamFinal`` correctly. Cursor-aware resume is
Phase 3 territory.

Test-only env vars:

- ``BACLOUD_TEST_FORCE_DROP_AFTER_SECONDS=N`` — force the WS closed
  N seconds after open; the reconnect path then runs as it would on
  a real drop.
- ``BACLOUD_TEST_BREAK_RECONNECT=1`` — point the reconnect URL at a
  guaranteed-unreachable host (``127.0.0.1:1``); reconnects fail
  until the budget expires.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.dataclassio import dataclass_from_json
from bacommon.bacloud import (
    BACLOUD_VERSION,
    ResponseData,
    StreamFinal,
    StreamFrame,
    StreamOutput,
)

if TYPE_CHECKING:
    import urllib.request

    from bacommon.bacloud import StreamWS


_DEFAULT_RECONNECT_BUDGET_SECONDS = 60.0
_RECONNECT_BACKOFF_MIN = 0.5
_RECONNECT_BACKOFF_MAX = 10.0
# A guaranteed-unreachable address used by the
# ``BACLOUD_TEST_BREAK_RECONNECT`` test hook.
_BROKEN_RECONNECT_HOST = '127.0.0.1:1'


def consume_via_ws(
    response: ResponseData, *, bearer: str | None
) -> ResponseData:
    """Drain a stream over WebSocket and return a terminal-only response.

    The returned ``ResponseData`` carries the terminal ``StreamFinal``
    in ``stream_frames`` so bacloud's existing ``stream_frames`` loop
    falls through to the usual terminal handling
    (message/error/end_command).

    Caller must check ``response.stream_ws is not None`` first.
    Raises :class:`~efro.error.CleanError` on unrecoverable WS
    failure (token-bad, reconnect-budget exhausted, etc.).
    """
    assert response.stream_ws is not None
    terminal = asyncio.run(_consume_with_reconnect(response.stream_ws, bearer))
    return ResponseData(stream_frames=[terminal])


def _reconnect_budget_seconds() -> float:
    raw = os.environ.get('BACLOUD_RECONNECT_BUDGET_SECONDS')
    if raw is None:
        return _DEFAULT_RECONNECT_BUDGET_SECONDS
    try:
        return float(raw)
    except ValueError:
        return _DEFAULT_RECONNECT_BUDGET_SECONDS


def _force_drop_after_seconds() -> float | None:
    raw = os.environ.get('BACLOUD_TEST_FORCE_DROP_AFTER_SECONDS')
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _refresh_url_for(ws_url: str) -> str:
    """Compute the refresh-token endpoint URL from the WS URL."""
    https = ws_url.replace('wss://', 'https://').replace('ws://', 'http://')
    return f'{https}/refresh-token'


def _ws_url_for_reconnect(ws_url: str) -> str:
    """Apply the ``BACLOUD_TEST_BREAK_RECONNECT`` hook if set."""
    if os.environ.get('BACLOUD_TEST_BREAK_RECONNECT') == '1':
        # Strip the host but preserve the path. The path includes
        # ``/streamcall/<call_id>``; we want websockets to connect
        # to a definitely-unreachable host on that path.
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(ws_url)
        return urlunparse(parsed._replace(netloc=_BROKEN_RECONNECT_HOST))
    return ws_url


def _resolve_ws_url(sw: 'StreamWS') -> str:
    """Determine the WS URL the client should connect to.

    When ``sw.basn_url`` is set the producer pinned the stream to
    a specific basn (Phase 3 case); we honor that. Otherwise we
    construct the URL from the bacloud client's own kickoff
    hostname (``BACLOUD_SERVER`` env var or its default), so the
    LB routes us to a healthy basn anywhere in the fleet.
    """
    if sw.basn_url is not None:
        return sw.basn_url
    # pylint: disable=cyclic-import
    from bacommontools.bacloud import BACLOUD_SERVER

    return f'wss://{BACLOUD_SERVER}/streamcall/{sw.call_id}'


async def _consume_with_reconnect(
    sw: StreamWS, bearer: str | None
) -> StreamFinal:
    """Open the WS (with reconnect on transient failure)."""
    import websockets

    # The ws_token field is now a securedata.Archive nested in the
    # response. We pass it on the WS handshake as an HTTP header
    # value, which means we encode it as base64-of-canonical-JSON
    # — HTTP headers don't carry raw JSON cleanly, and basn does
    # the inverse decode on receipt.
    current_token = _encode_archive_for_header(sw.ws_token)
    base_ws_url = _resolve_ws_url(sw)
    deadline = time.monotonic() + _reconnect_budget_seconds()
    backoff = _RECONNECT_BACKOFF_MIN
    is_first_connection = True
    # Force-drop is meant to simulate a single mid-stream drop and
    # then let reconnect succeed naturally; firing it on every
    # reconnect would just stall the test forever.
    force_drop_seconds = _force_drop_after_seconds()

    while True:
        url = (
            base_ws_url
            if is_first_connection
            else _ws_url_for_reconnect(base_ws_url)
        )
        try:
            terminal = await _consume_once(
                url=url,
                token=current_token,
                bearer=bearer,
                websockets_module=websockets,
                force_drop_seconds=force_drop_seconds,
            )
        except _NeedsTokenRefresh:
            try:
                current_token = await _refresh_token(
                    base_ws_url, current_token, bearer
                )
            except _RefreshFailed as exc:
                raise CleanError(
                    f'Stream WS token refresh failed: {exc}'
                ) from exc
            print(
                '[bacloud] WS token refreshed; reconnecting...',
                file=sys.stderr,
            )
            is_first_connection = False
            force_drop_seconds = None
            backoff = _RECONNECT_BACKOFF_MIN
            continue
        except _FatalAuth as exc:
            raise CleanError(f'Stream WS auth failed: {exc}') from exc
        except _Reconnectable as exc:
            if time.monotonic() >= deadline:
                raise CleanError(
                    f'Stream WS reconnect budget exhausted: {exc}'
                ) from exc
            print(
                f'[bacloud] WS dropped ({exc}); '
                f'reconnecting in {backoff:.1f}s...',
                file=sys.stderr,
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, _RECONNECT_BACKOFF_MAX)
            is_first_connection = False
            force_drop_seconds = None
            continue
        else:
            return terminal


async def _consume_once(
    *,
    url: str,
    token: str,
    bearer: str | None,
    websockets_module: object,
    force_drop_seconds: float | None,
) -> StreamFinal:
    """One WS-open-to-close cycle. Raises classification exceptions."""
    websockets = websockets_module  # for readability
    from websockets.exceptions import (
        ConnectionClosed,
        InvalidStatus,
        WebSocketException,
    )

    headers: list[tuple[str, str]] = [('X-WS-Token', token)]
    if bearer is not None:
        headers.append(('Authorization', f'Bearer {bearer}'))
    headers.append(('User-Agent', f'bacloud/{BACLOUD_VERSION}'))

    drop_task: asyncio.Task[None] | None = None

    try:
        async with websockets.connect(  # type: ignore[attr-defined]
            url, additional_headers=headers
        ) as ws:
            if force_drop_seconds is not None:
                drop_task = asyncio.create_task(
                    _force_drop_at(ws, force_drop_seconds)
                )
            async for raw in ws:
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
                frame = dataclass_from_json(StreamFrame, raw)
                if isinstance(frame, StreamOutput):
                    print(frame.text, end='', flush=True)
                elif isinstance(frame, StreamFinal):
                    return frame
            # Loop ended without a StreamFinal — treat as
            # reconnectable; basn's subscription is still
            # alive server-side (or has cleanly ended without
            # us seeing the terminal frame).
            raise _Reconnectable('WS closed without terminal frame')
    except InvalidStatus as exc:
        # Handshake-time HTTP error — basn rejected the upgrade
        # before we got an app-level close code. Treat as fatal:
        # likely a versioning / routing problem.
        raise _FatalAuth(f'handshake rejected: {exc}') from exc
    except ConnectionClosed as exc:
        if exc.code == 4001:  # token expired
            raise _NeedsTokenRefresh(str(exc)) from exc
        if exc.code in (4002, 4003, 4004):  # token bad / mismatch / missing
            raise _FatalAuth(f'code={exc.code} reason={exc.reason!r}') from exc
        raise _Reconnectable(
            f'closed: code={exc.code} reason={exc.reason!r}'
        ) from exc
    except WebSocketException as exc:
        raise _Reconnectable(f'protocol error: {exc}') from exc
    except OSError as exc:
        raise _Reconnectable(f'connect failed: {exc}') from exc
    finally:
        if drop_task is not None:
            drop_task.cancel()


async def _force_drop_at(ws: object, after_seconds: float) -> None:
    """Test-only: close the WS after ``after_seconds``."""
    try:
        await asyncio.sleep(after_seconds)
        print(
            f'[bacloud] BACLOUD_TEST_FORCE_DROP_AFTER_SECONDS=:'
            f' force-closing WS after {after_seconds}s',
            file=sys.stderr,
        )
        # Close the underlying transport, which surfaces in the
        # consumer loop as a ConnectionClosed (typically code 1006).
        await ws.close()  # type: ignore[attr-defined]
    except asyncio.CancelledError:
        pass


async def _refresh_token(
    basn_url: str, current_token: str, bearer: str | None
) -> str:
    """POST to refresh-token. Returns the new token string."""
    import json
    import urllib.error
    import urllib.request

    url = _refresh_url_for(basn_url)
    req = urllib.request.Request(url, method='POST')
    req.add_header('X-WS-Token', current_token)
    if bearer is not None:
        req.add_header('Authorization', f'Bearer {bearer}')
    req.add_header('User-Agent', f'bacloud/{BACLOUD_VERSION}')

    # urllib is sync; run in a thread to avoid blocking the loop.
    loop = asyncio.get_running_loop()
    try:
        body = await loop.run_in_executor(
            None, lambda: _http_post(req).decode('utf-8')
        )
    except urllib.error.HTTPError as exc:
        body_str = exc.read().decode(errors='replace')
        raise _RefreshFailed(f'HTTP {exc.code} from {url}: {body_str}') from exc
    except urllib.error.URLError as exc:
        raise _RefreshFailed(f'connect failed to {url}: {exc.reason}') from exc

    try:
        data = json.loads(body)
        return str(data['ws_token'])
    except (ValueError, KeyError) as exc:
        raise _RefreshFailed(f'unparseable response: {body!r}') from exc


def _encode_archive_for_header(archive: object) -> str:
    """Encode a :class:`bacommon.securedata.Archive` for an HTTP
    header.

    Header value is base64-of-canonical-JSON. basn's
    :func:`_decode_token_header` is the inverse.
    """
    import base64

    from efro.dataclassio import dataclass_to_json

    return (
        base64.urlsafe_b64encode(dataclass_to_json(archive).encode())
        .rstrip(b'=')
        .decode('ascii')
    )


def _http_post(req: urllib.request.Request) -> bytes:
    """Sync HTTP POST helper for use under ``run_in_executor``."""
    import urllib.request

    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()  # type: ignore[no-any-return]


class _Reconnectable(Exception):
    """Internal: WS dropped on a recoverable signal; retry with backoff."""


class _NeedsTokenRefresh(Exception):
    """Internal: WS closed with 4001 (expired); refresh & retry."""


class _FatalAuth(Exception):
    """Internal: WS closed with an unrecoverable auth code; give up."""


class _RefreshFailed(Exception):
    """Internal: refresh-token endpoint failed."""
