# Released under the MIT License. See LICENSE for details.
#
"""bacloud's live session to a basn node.

One SmartSocket session replaces the request-per-HTTPS-handshake
conversation bacloud used to have. There is no mint step and no HTTPS
request at all: the client dials ``/bacloudsession`` on the node it
already resolved, and the handshake itself creates the channel. Every
command after that rides the session -- including each
``end_command`` continuation and every streamed command's output.

What the session buys, measured rather than assumed (2026-08-15):
streamed output pushed as produced instead of on a 0.25-5s poll
cadence, one connection instead of two for a streamed command, one
recovery implementation instead of several (reconnects are invisible
here; deaths are not), and a far end that finds out when we quit.
Notably *not* per-command latency -- that measured the same as the
request-per-connection path it replaced, because urllib3 pooling had
already amortized the TLS handshake across a run.

**Sequential by contract.** Send a request, read until its response,
repeat. No correlation ids and no multiplexing: bulk transfers were
never on this channel -- uploads and downloads go direct to storage
on their own connections -- so nothing here needs to overlap.

**Threading.** bacloud is synchronous and stays that way. The session
runs an asyncio loop on its own thread and :meth:`BacloudSession.request`
is an ordinary blocking call, so nothing above it has to know a socket
is involved.

**Credentials and resume.** Our bearer rides the WS upgrade's
``Authorization`` header on every attach, exactly as it rode every
HTTPS request before. The node answers a freshly created channel with
a ``SessionHandleResponse`` carrying a resume token, which we
hold and present as ``X-WS-Token`` if we ever have to reconnect. It
needs no refreshing -- it is minted to outlive the session itself.

That response also tells us *where* to reconnect, and we must use it
rather than re-dialing the host we opened with. In prod that host is a
regional endpoint which routes each connection to some node, and a
session lives in exactly one node's process -- so re-dialing it would
usually reach a node with nothing to resume. (This is the one place
bacloud is node-bound; streamcall is not, because its state is
bamaster's.)

Canonical design: ``efrohome:docs/global_design/
streamcall-smartsocket.md`` ("Consumer #2").
"""

import os
import queue
import asyncio
import logging
import threading
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.smartsocket import (
    SmartSocketClosed,
    SmartSocketEndpoint,
)
from bacommon.bacloud import (
    BACLOUD_VERSION,
    RequestData,
    ResponseData,
    SessionHandleResponse,
    StandardResponseData,
    StreamOutputResponse,
)

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection
    from websockets.exceptions import ConnectionClosed

    from bacommon.bacloud import StandardRequestData

VERBOSE = os.environ.get('BACLOUD_VERBOSE') == '1'

#: WS subprotocol the relay selects. Must be offered or the
#: handshake is rejected before any token is looked at.
_WS_SUBPROTOCOL = 'basmartsocket'

#: Header carrying our protocol version. A handshake has no body to
#: put it in, and the node captures it once for the session's life.
_VERSION_HEADER = 'X-Bacloud-Version'

#: How long to wait for the first attach. Past this the run fails
#: with an error naming WebSockets: one is a prerequisite for the
#: game itself, so bacloud does not carry a second transport for
#: environments that cannot open one.
_OPEN_TIMEOUT_SECONDS = 15.0

#: Bound on saying goodbye. Telling the far end we're going is worth a
#: moment; it is never worth hanging an exit.
_END_TIMEOUT_SECONDS = 2.0


class BacloudSession:
    """A live conversation with the bacloud server.

    Constructed via :meth:`open`, which returns ``None`` rather than
    raising when a session can't be had -- not because that is
    survivable (it is not; the caller turns it into a hard error) but
    so the message the user sees is written where the surrounding
    context is, rather than here.
    """

    def __init__(self, ws_url: str, bearer: str | None) -> None:
        self._ws_url = ws_url
        self._bearer = bearer
        #: Handed to us in-band once the channel exists; presented on
        #: any reconnect. None until then, which is fine -- a first
        #: attach is the one that doesn't need it.
        self._token: str | None = None
        #: Where to reconnect, once the node has told us. Not the host
        #: we dialed: in prod that is a regional endpoint that would
        #: route a reconnect to an arbitrary node, and this session
        #: only exists on one of them.
        self._reconnect_url: str | None = None
        #: The node's id for this session. We never send it anywhere;
        #: it exists so a failure can name the session it happened on,
        #: which is the only thing that ties a user's report to the
        #: node-side log lines for the same conversation.
        self._channel_id: str | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._endpoint: (
            SmartSocketEndpoint[RequestData, ResponseData] | None
        ) = None
        self._inbox: queue.Queue[ResponseData | None] = queue.Queue()
        #: Set once a connection has actually completed its hello.
        #: Until then a dial failure means 'no session here', not 'a
        #: session to recover'.
        self._ever_connected = False
        self._ready = threading.Event()
        self._ended = threading.Event()
        self._thread = threading.Thread(
            target=self._thread_main, name='bacloud-session', daemon=True
        )
        self._closed_error: str | None = None

    @classmethod
    def open(cls, server: str, bearer: str | None) -> BacloudSession | None:
        """Open a session to ``server``, or return None.

        ``server`` is the host bacloud already resolved -- the same
        one its requests went to before -- so this adds no lookup and
        no hop.
        """
        ws_url = f'wss://{server}/bacloudsession'
        session = cls(ws_url, bearer)
        session._thread.start()
        session._ready.wait(timeout=_OPEN_TIMEOUT_SECONDS)
        if not session._ready.is_set() or session._ended.is_set():
            if VERBOSE:
                import sys

                why = session._closed_error or 'attach timed out'
                print(
                    f'bacloud: session unavailable ({why}).',
                    file=sys.stderr,
                )
            session.end()
            return None
        if VERBOSE:
            import sys

            print(f'bacloud: session open to {ws_url}', file=sys.stderr)
        return session

    @property
    def alive(self) -> bool:
        """Is the session still usable?"""
        return not self._ended.is_set()

    def request(self, request: StandardRequestData) -> StandardResponseData:
        """Send one request and block for its response.

        Blocks without a deadline of its own on purpose: the session's
        own liveness machinery is the authority on whether the far end
        is still there, and a second timeout here could only disagree
        with it. A dead session raises rather than hanging.

        The one gap in that, stated so it isn't rediscovered: liveness
        watches the *leg*, not the outstanding request. A response
        dropped on a connection that then stays healthy is only
        retransmitted by a resume hello, which never fires because the
        leg looks fine -- so this would block forever. Real transports
        cannot produce that (TCP delivers or the connection breaks);
        only the relay's chaos hook can, by silencing frames on a live
        connection. If that ever stops being true, the fix is a
        request-scoped deadline here, not a shorter liveness window.
        """
        loop = self._loop
        endpoint = self._endpoint
        if loop is None or endpoint is None or self._ended.is_set():
            raise CleanError(self._death_message('is closed'))

        try:
            asyncio.run_coroutine_threadsafe(
                endpoint.send(request), loop
            ).result()
        except SmartSocketClosed as exc:
            raise CleanError(self._death_message('closed')) from exc

        while True:
            response = self._inbox.get()
            if response is None:
                raise CleanError(self._death_message('closed mid-command'))

            if isinstance(response, StreamOutputResponse):
                # A streamed command talking while it works. Print it
                # and keep waiting: the command's actual answer is
                # still coming, on this same channel, and telling the
                # two apart is what the response hierarchy is for.
                print(response.text, end='', flush=True)
                continue

            if not isinstance(response, StandardResponseData):
                raise CleanError(
                    'Server sent a response type this client does not'
                    ' understand; please update it.'
                )
            return response

    def _death_message(self, what: str) -> str:
        """Explain a dead session, naming it.

        The channel id is the whole point: a user pasting this line
        into a report gives us the exact string to grep the serving
        node's logs for.
        """
        detail = self._closed_error or f'bacloud session {what}.'
        if self._channel_id is None:
            return detail
        return f'{detail} (session {self._channel_id})'

    def end(self) -> None:
        """Tell the far end we're done, briefly and best-effort.

        ``end`` rather than ``detach``: a process that is exiting is
        not coming back, and a relay that is told so releases the
        channel (and its node-side task) now instead of holding the
        slot through the whole linger window.
        """
        loop = self._loop
        endpoint = self._endpoint
        if (
            loop is not None
            and endpoint is not None
            and not self._ended.is_set()
        ):
            # Build the coroutine only once we know we can schedule
            # it, and close it by hand if we can't. A session that
            # died on its own (refused, unreachable node) leaves a
            # loop that has already stopped, and handing it a
            # coroutine there produces a 'never awaited' RuntimeWarning
            # on the user's terminal -- on what is a completely normal
            # path, since the run just falls back to the other
            # transport.
            coro = endpoint.end('client exiting')
            try:
                future = asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception:  # pylint: disable=broad-except
                coro.close()
            else:
                try:
                    future.result(timeout=_END_TIMEOUT_SECONDS)
                except Exception:  # pylint: disable=broad-except
                    pass
        self._thread.join(timeout=_END_TIMEOUT_SECONDS)

    # --- session thread ----------------------------------------

    def _thread_main(self) -> None:
        try:
            asyncio.run(self._run())
        except Exception as exc:  # pylint: disable=broad-except
            self._closed_error = f'bacloud session failed: {exc}'
        finally:
            self._ended.set()
            self._ready.set()
            # Unblock anyone waiting on a response that will never come.
            self._inbox.put(None)

    async def _run(self) -> None:
        self._loop = asyncio.get_running_loop()
        endpoint = SmartSocketEndpoint(
            self._connect,
            send_type=RequestData,
            recv_type=ResponseData,
            on_message=self._on_message,
            logger=_session_logger(),
        )
        self._endpoint = endpoint

        # The endpoint is usable the moment it exists -- sends buffer
        # until the relay accepts them -- but reporting 'open' before
        # a first attach succeeds would hide an unreachable node
        # behind a hang. Wait for the connection, then let the caller
        # go.
        waiter = asyncio.create_task(self._await_connected(endpoint))
        try:
            await endpoint.run()
        finally:
            waiter.cancel()
            if endpoint.close_code and not _is_clean_close(endpoint.close_code):
                self._closed_error = (
                    f'bacloud session closed'
                    f' ({endpoint.close_code} {endpoint.close_reason}).'
                )

    async def _await_connected(
        self, endpoint: SmartSocketEndpoint[RequestData, ResponseData]
    ) -> None:
        """Release :meth:`open` once we're actually attached."""
        while not endpoint.done:
            if endpoint.connected:
                self._ever_connected = True
                self._ready.set()
                return
            await asyncio.sleep(0.05)

    async def _on_message(self, response: ResponseData) -> None:
        if isinstance(response, SessionHandleResponse):
            # Not an answer to anything -- the node telling us how to
            # get back in. Hold it; don't hand it to a waiting caller.
            self._token = response.token
            self._channel_id = response.channel_id
            if response.ws_url:
                self._reconnect_url = response.ws_url
            if VERBOSE:
                import sys

                print(
                    f'bacloud: session {response.channel_id}'
                    f' (resume via {response.ws_url})',
                    file=sys.stderr,
                )
            return
        self._inbox.put(response)

    async def _connect(self) -> _WsTransport:
        """Dial the relay for one attach."""
        headers = {
            'User-Agent': f'bacloud/{BACLOUD_VERSION}',
            _VERSION_HEADER: str(BACLOUD_VERSION),
        }
        if self._bearer is not None:
            headers['Authorization'] = f'Bearer {self._bearer}'
        if self._token is not None:
            # Present only on a reconnect: its absence is exactly what
            # tells the node to create a channel rather than find one.
            headers['X-WS-Token'] = self._token

        try:
            sock = await self._dial(headers)
        except Exception as exc:
            if self._ever_connected:
                raise
            # Nothing has ever answered here: an older node without
            # the endpoint, or a host we can't reach. Either way this
            # run belongs on the other transport, and retrying the
            # dial for the whole reconnect budget would just delay
            # that. Report a clean end so the endpoint stops now.
            self._closed_error = f'no bacloud session endpoint ({exc})'
            raise SmartSocketClosed(1000, 'no session endpoint') from exc

        return _WsTransport(sock)

    async def _dial(self, headers: dict[str, str]) -> ClientConnection:
        """One websockets dial, with our handshake headers."""
        import websockets

        return await websockets.connect(
            self._reconnect_url or self._ws_url,
            subprotocols=[websockets.Subprotocol(_WS_SUBPROTOCOL)],
            additional_headers=headers,
            open_timeout=_OPEN_TIMEOUT_SECONDS,
            # SmartSocket runs its own app-level ping/pong on a
            # policy-driven interval; a second liveness mechanism
            # would only add ways to disagree.
            ping_interval=None,
        )


def _session_logger() -> logging.Logger:
    """Logger for the endpoint's own diagnostics.

    Silent unless ``BACLOUD_VERBOSE``. The session is an optimization
    over a transport that still works without it, so its internal
    trouble -- a dial that failed, a connection that dropped and
    recovered -- is diagnostics rather than something to put in a
    user's face mid-command. Real failures still surface: they end the
    session, and the caller reports that.
    """
    logger = logging.getLogger('bacloud.session')
    if not VERBOSE:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
    return logger


class _WsTransport:
    """Adapts a websockets connection to the endpoint's seam."""

    def __init__(self, sock: ClientConnection) -> None:
        self._sock = sock

    async def send(self, data: str) -> None:
        """Send one frame."""
        import websockets

        try:
            await self._sock.send(data)
        except websockets.exceptions.ConnectionClosed as exc:
            raise _closed_from(exc) from exc

    async def recv(self) -> str:
        """Receive one frame."""
        import websockets

        try:
            data = await self._sock.recv()
        except websockets.exceptions.ConnectionClosed as exc:
            # The close code is the whole recovery signal; a transport
            # that only says 'it broke' can't tell resume from dead.
            raise _closed_from(exc) from exc
        return data if isinstance(data, str) else data.decode()

    async def close(self, code: int = 1000, reason: str = '') -> None:
        """Close with a code."""
        try:
            await self._sock.close(code=code, reason=reason)
        except Exception:  # pylint: disable=broad-except
            pass


def _closed_from(exc: ConnectionClosed) -> SmartSocketClosed:
    """Translate a websockets close into the endpoint's exception."""
    return SmartSocketClosed(
        exc.rcvd.code if exc.rcvd is not None else 1006,
        exc.rcvd.reason if exc.rcvd is not None else '',
    )


def _is_clean_close(code: int) -> bool:
    """Was this close an ordinary end rather than a failure?"""
    return code in (1000, 1001)
