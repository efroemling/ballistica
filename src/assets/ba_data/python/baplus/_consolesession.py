# Released under the MIT License. See LICENSE for details.
#
"""Our end of a cloud-console session.

When someone opens a console aimed at this app, the server mints a
SmartSocket channel and hands us the peer_b end. We hold it and push
log output as it happens, rather than being polled for it.

Three lifetimes nest here, and keeping them distinct is what makes
the rest coherent:

- the **connection**, which any network blip ends;
- the **channel**, which ends when our transport cycles to another
  node, when it hits its max-duration, or when a peer stays away past
  its linger;
- the **session**, which spans both. It is identified by a
  server-minted id, and it is the thing a user would grant permission
  to. A fresh handle carrying an id we already know is a
  continuation, so we re-attach silently; one carrying a new id is a
  new ask.

That last distinction exists for a permission prompt we have not
built yet. Re-prompting every time a transport connection cycled
would be unusable, and worse, would train people to click through
it.
"""

import time
import asyncio
import logging
import contextlib
from functools import partial
from typing import TYPE_CHECKING

import babase
import baenv

from efro.util import break_websocket_logger_cycle
from efro.smartsocket import SmartSocketClosed, SmartSocketEndpoint
from efro.dataclassio import dataclass_from_json, dataclass_to_json
from bacommon.consolechannel import (
    ConsolePermission,
    PermissionEvent,
    ConsoleCommand,
    ExecAckEvent,
    ExecCommand,
    GapEvent,
    InstanceEvent,
    LogEntriesEvent,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    from bacommon.consolechannel import ConsoleEvent

logger = logging.getLogger('ba.consolesession')

#: How often we look for new log entries to push. This is a local
#: check against an in-memory cache -- no network, no lock -- so it
#: can be brisk; it is the difference between 'as it happens' and
#: 'within a second'. (A hook on the log handler would be tighter
#: still; this stays out of that machinery for now.)
_POLL_SECONDS = 0.1

#: Cap on how much log we'll hold un-acked before we start skipping.
#: A console is a lossy tail by nature -- our archive is bounded and
#: the display has always been able to say 'skipping N lines' -- and
#: it must stay that way: pushing an unbounded stream into a
#: gapless-or-dead channel would let a slow reader kill the session
#: instead of merely missing some scrollback.
_MAX_PENDING_ENTRIES = 400

#: How long a held request waits for some app-mode able to ask before
#: we give up and treat it as a refusal. Without this, a mode that
#: never gains a prompt would leave the console waiting forever; with
#: it we still fail closed, just patiently.
_PERMISSION_TIMEOUT_SECONDS = 120.0

#: How long we'll wait for a polite close while shutting down. Short
#: on purpose -- telling the relay we're gone is worth a moment, but
#: never worth stalling the app's exit.
_SHUTDOWN_CLOSE_TIMEOUT = 2.0


class _Session:
    """One console session, spanning channels and connections."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.endpoint: SmartSocketEndpoint | None = None
        self.task: asyncio.Task | None = None

        #: Where we are in our own log. Survives channel changes, so
        #: a re-attach resumes rather than replaying.
        self.log_index = 0

        #: The instance we last told the far end about. Ours never
        #: changes within a process, so this only matters across a
        #: re-handle onto a restarted app.
        self.announced_uuid: str | None = None

        #: Entries we skipped because the far end wasn't keeping up.
        self.dropped = 0

        #: Our app-instance id. Supplied by the caller, which has the
        #: private-api access to read it.
        self.instance_uuid = ''

        #: Where permission stands. Until it is granted we hold the
        #: channel but push no log and run no commands -- permission
        #: gates the session's *capabilities* rather than its
        #: creation, because a human can't answer inside the request
        #: that offered it.
        self.permission = ConsolePermission.PENDING

        #: What we last told the console. Cleared per channel so a
        #: reconnecting console is re-told where things stand.
        self.announced_permission: ConsolePermission | None = None

        #: Detail worth adding to the state, when there is any. The
        #: console can word the states themselves; this is only for
        #: what it couldn't know, like nobody having answered.
        self.permission_message: str | None = None

        #: Set once we've put the question somewhere, so a mode
        #: change doesn't ask twice.
        self.asked = False

        #: Who is on the other end, as the server vouches for them.
        #: Shown in the prompt, and what a remembered grant hangs off.
        self.requester_tag: str | None = None
        self.requester_key: str | None = None

        #: When we first asked, for the patience limit above.
        #: Monotonic wall-clock rather than app-time: app-time
        #: pauses while the app is suspended, and the console at
        #: the other end is waiting in real seconds either way.
        self.ask_start_time = time.monotonic()

    @property
    def permitted(self) -> bool:
        """Whether we may act on this session at all."""
        return self.permission is ConsolePermission.GRANTED

    def stop(self) -> None:
        """Tear this session down."""
        if self.task is not None:
            self.task.cancel()
            self.task = None
        self.endpoint = None


class ConsoleSessionManager:
    """Holds at most one live console session for this app."""

    def __init__(self) -> None:
        self._session: _Session | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def handle_offer(
        self,
        *,
        session_id: str,
        ws_url: str,
        token: str,
        app_instance_uuid: str,
        requester_tag: str | None,
        requester_key: str | None,
    ) -> tuple[bool, str | None]:
        """Take up (or decline) an offered console session.

        Returns ``(accepted, error)``. Declining is a normal outcome,
        not a failure -- the server falls back to polling us.
        """
        self._loop = asyncio.get_running_loop()

        envconfig = baenv.get_env_config()
        if envconfig.log_handler is None:
            # Without a log handler there is nothing to stream; say so
            # rather than accepting and going quiet.
            return False, 'no log handler in this environment'

        existing = self._session
        if existing is not None and existing.session_id == session_id:
            # A continuation: same session, new channel. Keep our log
            # position so the console picks up where it left off.
            logger.debug('console session %s: re-attaching', session_id)
            existing.stop()
            session = existing
        else:
            if existing is not None:
                logger.debug(
                    'console session %s: replaced by %s',
                    existing.session_id,
                    session_id,
                )
                existing.stop()
            session = _Session(session_id)
            self._session = session

        endpoint = SmartSocketEndpoint(
            lambda: _connect(ws_url, token),
            on_message=lambda payload: self._on_command(session, payload),
        )
        session.announced_permission = None
        session.instance_uuid = app_instance_uuid
        session.requester_tag = requester_tag
        session.requester_key = requester_key
        session.endpoint = endpoint
        session.task = asyncio.create_task(self._run(session))

        # We take the channel either way; permission gates what the
        # session may *do*. It can't gate acceptance, because a person
        # can't answer inside the request that offered it. Ask once per
        # session, not per channel -- a reconnect is the same console.
        if not session.permitted:
            self._request_permission(session)
        return True, None

    def _request_permission(self, session: _Session) -> None:
        """Put the control question to the active app-mode."""
        if session.asked:
            return
        session.asked = True
        logger.debug(
            'console session %s: asking for control permission',
            session.session_id,
        )

        def _on_result(result: babase.ControlPermission) -> None:
            # The answer arrives on the logic thread (a dialog button);
            # hop it back to our loop before touching session state.
            loop = self._loop
            if loop is None:
                return
            loop.call_soon_threadsafe(
                partial(self._apply_permission, session, result)
            )

        request = babase.ControlPermissionRequest(
            requester_name=session.requester_tag,
            requester_key=session.requester_key,
        )
        # No fg context here, unlike the exec path below: an app-mode
        # that answers by drawing a dialog needs an empty context, and
        # UI calls hard-error under a set one.
        babase.pushcall(
            partial(self._ask_app_mode, request, _on_result),
            from_other_thread=True,
        )

    @staticmethod
    def _ask_app_mode(
        request: babase.ControlPermissionRequest,
        on_result: Callable[[babase.ControlPermission], None],
    ) -> None:
        """Hand the question to whatever app-mode is active.

        Runs on the logic thread, which is the only place an app-mode
        can be touched at all.
        """
        try:
            mode = babase.app.mode
        except ValueError:
            # Boot isn't far enough along to have a mode. That's a
            # hold, not a refusal -- the first activation re-asks.
            on_result(babase.ControlPermission.CANNOT_ASK)
            return
        mode.on_control_permission_request(request, on_result)

    def _apply_permission(
        self, session: _Session, result: babase.ControlPermission
    ) -> None:
        """Act on an app-mode's answer."""
        if session is not self._session:
            return  # Answered after we moved on.

        if result is babase.ControlPermission.ALLOW:
            logger.debug('console session %s permitted', session.session_id)
            session.permission = ConsolePermission.GRANTED
            return

        if result is babase.ControlPermission.CANNOT_ASK:
            # Held, not refused: a mode able to ask may activate in a
            # moment (construct-mode hands off during bring-up), and
            # on_app_mode_activated will put the question again.
            logger.debug(
                'console session %s: no app-mode able to ask yet',
                session.session_id,
            )
            session.asked = False
            return

        # Leave the teardown to the pump, which gets the refusal out
        # to the console before the channel drops -- a session that
        # just goes quiet looks like a bug from the other end.
        logger.debug('console session %s denied', session.session_id)
        session.permission = ConsolePermission.DENIED

    async def shutdown(self) -> None:
        """End any live session before the runtime goes away.

        Two things depend on this. The relay is holding a channel and
        a basn task open for us, and without a close it waits out the
        whole linger window for a peer that no longer exists -- so we
        end the session rather than detaching, because this app
        instance genuinely is not coming back and the console should
        go looking for its replacement now. And the runtime expects
        tenants to leave no tasks behind; an abandoned session task
        is both a straggler and a pile of cyclic garbage (a websocket
        client torn down by cancellation drags its keepalive task,
        that task's CancelledError, and the traceback frames holding
        it into a cycle).

        Best-effort by design: a shutdown must not hang on a socket
        that has already stopped answering.
        """
        session = self._session
        self._session = None
        if session is None:
            return

        endpoint = session.endpoint
        if endpoint is not None:
            try:
                await asyncio.wait_for(
                    endpoint.end('app shutting down'),
                    timeout=_SHUTDOWN_CLOSE_TIMEOUT,
                )
            except Exception:  # pylint: disable=broad-except
                logger.debug(
                    'console session %s: close on shutdown failed',
                    session.session_id,
                    exc_info=True,
                )

        task = session.task
        session.stop()
        if task is not None:
            # Await the cancellation so we hand the runtime a loop
            # with nothing of ours still pending on it.
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    def notify_app_mode_activated(self) -> None:
        """Note that an app-mode just became active.

        Safe to call from any thread; the work hops to our loop.
        """
        loop = self._loop
        if loop is None:
            return  # No session has ever run, so nothing is waiting.
        loop.call_soon_threadsafe(self._on_app_mode_activated)

    def _on_app_mode_activated(self) -> None:
        """Re-put a held question now that some mode may answer it.

        Only touches a session still waiting on an answer, so an
        app-mode that flaps can't turn into repeated prompts.
        """
        session = self._session
        if session is None or session.permitted or session.asked:
            return
        self._request_permission(session)

    async def _run(self, session: _Session) -> None:
        """Drive one channel: pump log out until it ends."""
        endpoint = session.endpoint
        assert endpoint is not None
        pump = asyncio.create_task(self._pump_log(session))
        try:
            await endpoint.run()
        except Exception:  # pylint: disable=broad-except
            logger.exception('console session %s failed', session.session_id)
        finally:
            pump.cancel()
            logger.debug(
                'console session %s channel ended (code %d)',
                session.session_id,
                endpoint.close_code,
            )
            # The channel is done, but the *session* isn't: the server
            # re-handles and offers us a fresh one under the same id.
            if self._session is session:
                session.endpoint = None

    async def _pump_log(self, session: _Session) -> None:
        """Push new log entries as they appear."""
        envconfig = baenv.get_env_config()
        assert envconfig.log_handler is not None

        while True:
            await asyncio.sleep(_POLL_SECONDS)
            endpoint = session.endpoint
            if endpoint is None or not endpoint.connected:
                continue

            # Nobody answered. Fail closed rather than holding a
            # channel open forever on the chance someone will.
            if (
                session.permission is ConsolePermission.PENDING
                and time.monotonic() - session.ask_start_time
                > _PERMISSION_TIMEOUT_SECONDS
            ):
                logger.debug(
                    'console session %s: permission timed out',
                    session.session_id,
                )
                session.permission = ConsolePermission.DENIED
                session.permission_message = 'Nobody answered.'

            if session.announced_permission is not session.permission:
                await self._emit(
                    session,
                    PermissionEvent(
                        state=session.permission,
                        message=session.permission_message,
                    ),
                )
                session.announced_permission = session.permission

            # No output leaves this app until the user says so.
            if not session.permitted:
                if session.permission is ConsolePermission.DENIED:
                    if self._session is session:
                        self._session = None
                    session.stop()
                    return
                continue

            if session.announced_uuid is None:
                session.announced_uuid = session.instance_uuid
                await self._emit(
                    session,
                    InstanceEvent(
                        target_uuid=session.announced_uuid,
                        replaced_previous=False,
                    ),
                )

            archive = envconfig.log_handler.get_cached(
                start_index=session.log_index
            )
            dropped = max(0, archive.start_index - session.log_index)
            if dropped:
                await self._emit(session, GapEvent(dropped=dropped))
            if not archive.entries:
                continue

            entries = archive.entries
            if len(entries) > _MAX_PENDING_ENTRIES:
                # Shed rather than let a backlog wedge the channel;
                # loss is expressed in the payload, never by the
                # transport silently gapping.
                skipped = len(entries) - _MAX_PENDING_ENTRIES
                entries = entries[-_MAX_PENDING_ENTRIES:]
                await self._emit(session, GapEvent(dropped=skipped))

            session.log_index = archive.start_index + len(archive.entries)
            await self._emit(
                session,
                LogEntriesEvent(entries=entries, next_index=session.log_index),
            )

    async def _emit(self, session: _Session, event: ConsoleEvent) -> None:
        """Send one event, tolerating a channel that just died."""
        endpoint = session.endpoint
        if endpoint is None:
            return
        try:
            await endpoint.send(dataclass_to_json(event))
        except SmartSocketClosed:
            pass  # The run loop observes this and winds up.

    async def _on_command(self, session: _Session, payload: str) -> None:
        """Handle one command from the console."""
        from baplus._cloud import cloud_console_exec

        try:
            command = dataclass_from_json(ConsoleCommand, payload)
        except Exception:  # pylint: disable=broad-except
            logger.exception('undecodable console command')
            return

        if not isinstance(command, ExecCommand):
            logger.warning(
                'unhandled console command %s', type(command).__name__
            )
            return

        if not session.permitted:
            # Refuse rather than queue: a command that runs minutes
            # later, when someone finally taps Allow, is a surprise.
            logger.warning('console exec refused (not permitted)')
            await self._emit(
                session,
                PermissionEvent(
                    state=session.permission,
                    message='Not running that; control was not granted.',
                ),
            )
            return

        babase.user_ran_commands()  # disable tourneys/etc.
        babase.pushcall(
            partial(cloud_console_exec, command.code),
            from_other_thread=True,
            other_thread_use_fg_context=True,
        )
        # Tell the console we took it. Worth its own event because
        # code that prints nothing is otherwise indistinguishable
        # from code that never arrived.
        await self._emit(
            session,
            ExecAckEvent(
                line_count=len(command.code.splitlines()),
                target_time=babase.apptime(),
            ),
        )
        # Give resulting output a moment to reach the log cache, so
        # the exec and its output arrive together rather than a poll
        # apart.
        await asyncio.sleep(0.05)


class _WsTransport:
    """Adapts a websockets connection to the endpoint's seam.

    The seam is deliberately three methods, so this is all it takes
    to put the same endpoint over a real socket here, a fake in
    tests, and (later) something that isn't a socket at all.
    """

    def __init__(self, sock: Any) -> None:
        self._sock = sock

    async def send(self, data: str) -> None:
        """Send one frame."""
        import websockets

        try:
            await self._sock.send(data)
        except websockets.exceptions.ConnectionClosed as exc:
            raise SmartSocketClosed(
                exc.rcvd.code if exc.rcvd is not None else 1006,
                exc.rcvd.reason if exc.rcvd is not None else '',
            ) from exc

    async def recv(self) -> str:
        """Receive one frame."""
        import websockets

        try:
            data = await self._sock.recv()
        except websockets.exceptions.ConnectionClosed as exc:
            # The close code is the whole recovery signal; a transport
            # that only says 'it broke' can't tell resume from dead.
            raise SmartSocketClosed(
                exc.rcvd.code if exc.rcvd is not None else 1006,
                exc.rcvd.reason if exc.rcvd is not None else '',
            ) from exc
        return data if isinstance(data, str) else data.decode()

    async def close(self, code: int = 1000, reason: str = '') -> None:
        """Close with a code."""
        try:
            await self._sock.close(code=code, reason=reason)
        except Exception:  # pylint: disable=broad-except
            pass


async def _connect(ws_url: str, token: str) -> _WsTransport:
    """Dial the relay for one attach."""
    import websockets

    # Token rides as a subprotocol entry rather than a header --
    # browsers can't set handshake headers, so the relay accepts it
    # this way, and using the same form here keeps one code path
    # server-side. Reuses the app's shared SSL context for its
    # bundled-root-cert policy.
    sock = await websockets.connect(
        ws_url,
        ssl=babase.app.net.sslcontext,
        subprotocols=[
            websockets.Subprotocol('basmartsocket'),
            websockets.Subprotocol(f'token.{token}'),
        ],
        additional_headers={'User-Agent': babase.user_agent_string()},
        open_timeout=10.0,
        # No library-level keepalive: SmartSocket runs its own
        # app-level ping/pong (PingFrame/PongFrame on a policy-driven
        # interval), so this would be a second, redundant liveness
        # mechanism. It also costs us garbage -- the keepalive task is
        # cancelled on every close, and its CancelledError holds a
        # traceback holding the frames holding the task, which only a
        # cyclic collection can free.
        ping_interval=None,
    )

    # Otherwise every connection we open stays alive as a cycle until
    # a cyclic collection; we never read the 'websocket' log field.
    break_websocket_logger_cycle(sock)

    return _WsTransport(sock)


#: The manager is a process-level singleton; the app holds at most
#: one console session at a time.
console_session_manager = ConsoleSessionManager()
