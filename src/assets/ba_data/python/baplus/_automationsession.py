# Released under the MIT License. See LICENSE for details.
#
"""Our end of the automation channel.

An automation-enabled build offers itself up to be driven: it holds a
SmartSocket to the basn node its transport is already talking to, and
a driver elsewhere attaches to the other end of that channel to send
Python and read results back. The two ends find each other through a
locator line this module logs on every transport connect.

Three things make this the *device's* channel rather than something
handed to us like the console's:

- **We create it.** The node is the issuer, the way it is for a
  bacloud session: we dial, it mints, no bamaster in the path and no
  round trip in front of the session.
- **We mint the credential.** A random key per app run, whose hash we
  register with the node; presenting the key is what authorizes a
  driver. That is deliberately not account ownership -- test devices
  are signed out, shared, or signed into throwaway accounts, and
  automation has to work anyway.
- **The address is not the credential.** Knowing the channel id gets
  you nothing without the key, so a locator line in a pasted log is
  harmless on its own.

The key itself is a bearer credential for remote code execution on
this device, and we log it. That is acceptable only because the
whole capability is compiled out of everything but developer builds
and additionally requires a runtime opt-in; see
``automation-over-transport.md`` decision 8.
"""

import os
import json
import time
import base64
import hashlib
import asyncio
import logging
import tempfile
from functools import partial
from typing import TYPE_CHECKING

import babase
import baenv

from efro.util import break_websocket_logger_cycle
from efro.smartsocket import (
    SmartSocketClosed,
    SmartSocketEndpoint,
    SmartSocketPayloadTooLarge,
)
from bacommon.automationchannel import (
    AutomationCommand,
    # Runtime import, not TYPE_CHECKING: the endpoint takes the root
    # types as real arguments, since generics are erased at runtime.
    AutomationEvent,
    ExecCommand,
    GapEvent,
    HelloCommand,
    HelloEvent,
    ImageFormat,
    LogEntriesEvent,
    ResultEvent,
    ScreenshotCommand,
    ScreenshotEvent,
)

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger('ba.automationsession')

#: Env var that turns the channel on. The capability is compiled into
#: developer builds only, but even there it stays off until asked
#: for: a dev build left running should not be quietly drivable.
_ENABLE_ENV_VAR = 'BA_AUTOMATION_CHANNEL'

#: Env var supplying a persistent key instead of a per-run one, for a
#: test device driven repeatedly across restarts.
_KEY_ENV_VAR = 'BA_AUTOMATION_KEY'

#: How often we look for new log entries to push. Local in-memory
#: check, so it can be brisk.
_POLL_SECONDS = 0.1

#: Cap on log entries pushed at once. A log tail is lossy by nature
#: and must stay that way: pushing an unbounded stream into a
#: gapless-or-dead channel lets a slow reader kill the session rather
#: than merely miss scrollback.
_MAX_PENDING_ENTRIES = 400

#: How long to wait for a capture to land on disk before giving up.
_SCREENSHOT_TIMEOUT_SECONDS = 10.0

#: How long a shutdown waits for the channel's polite close. Short on
#: purpose -- telling the relay we're gone is worth a moment, never
#: worth stalling the app's exit.
_SHUTDOWN_CLOSE_TIMEOUT = 2.0


def _make_key() -> str:
    """Mint (or read) this run's automation key."""
    from secrets import token_hex

    supplied = os.environ.get(_KEY_ENV_VAR)
    if supplied:
        return supplied
    # 128 bits, per decision 8.
    return token_hex(16)


class AutomationSessionManager:
    """Holds this app's automation channel, if it has one."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._endpoint: (
            SmartSocketEndpoint[AutomationEvent, AutomationCommand] | None
        ) = None
        self._channel_id: str | None = None
        self._key: str | None = None
        self._log_index = 0
        self._node_url: str | None = None
        #: Set at app shutdown so the recreate loop stops offering
        #: fresh channels while the runtime is going away.
        self._shutting_down = False
        #: Supplied by the caller, which has the private-api access
        #: to read it (baplus may not reach ``_babase``).
        self._app_instance_id = ''

    @property
    def enabled(self) -> bool:
        """Whether this build+run offers an automation channel.

        Both halves matter, and neither is stripped-attribute-shaped
        (reading one of those from code that reaches public builds is
        how you break every public build at once): the native hooks
        are simply *absent* when automation was not compiled in, so
        ``hasattr`` is a legitimate question in any build, and the
        env var is the runtime opt-in.
        """
        if not os.environ.get(_ENABLE_ENV_VAR):
            return False
        from babase import _automation

        return _automation.available()

    def on_transport_connected(
        self, node_base_url: str | None, app_instance_id: str
    ) -> None:
        """Start (or restart) our channel against a node.

        Called on every transport connect, so a reconnect or a
        node retirement re-establishes and re-advertises rather than
        leaving a dead locator in the log. Cheap and safe to call
        when disabled.
        """
        if not self.enabled or node_base_url is None or self._shutting_down:
            return

        self._app_instance_id = app_instance_id
        ws_url = _ws_url_for(node_base_url)
        if ws_url == self._node_url and self._task is not None:
            # Same node, still running; nothing to do.
            return

        self._stop()
        self._node_url = ws_url
        if self._key is None:
            self._key = _make_key()
        self._task = asyncio.create_task(self._run(ws_url))

    def _stop(self) -> None:
        """Tear down any live channel."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._endpoint = None

    async def shutdown(self) -> None:
        """End the channel before the runtime goes away.

        Mirrors the console (see ``ConsoleSessionManager.shutdown``):
        end the channel cleanly so the relay releases it (and its
        basn task) now instead of waiting out the linger for a device
        that has quit, and await the task's cancellation so we hand
        the runtime no straggler -- an abandoned session task torn
        down by loop-close raises ``Event loop is closed`` and, worse,
        drags a pile of cancellation-cycle garbage. Best-effort: a
        shutdown must never hang on a socket that stopped answering.
        """
        self._shutting_down = True
        endpoint = self._endpoint
        self._endpoint = None
        if endpoint is not None:
            try:
                await asyncio.wait_for(
                    endpoint.end('app shutting down'),
                    timeout=_SHUTDOWN_CLOSE_TIMEOUT,
                )
            except Exception:  # pylint: disable=broad-except
                logger.debug(
                    'automation channel: close on shutdown failed',
                    exc_info=True,
                )
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except BaseException:  # pylint: disable=broad-except
                pass  # Cancelled (or already failing) -- we're leaving.

    async def _run(self, ws_url: str) -> None:
        """Offer a channel, and a fresh one each time one ends.

        A SmartSocket channel is one device + one driver over its
        life: seq numbers are session-scoped and end-to-end, so a
        second *driver process* can't reuse a channel a previous one
        used (its fresh seqs would collide and get deduped). So each
        driver ends its channel when done, and we immediately offer a
        new one under a new id + locator. A single driver's own wifi
        blip is invisible to this loop -- the endpoint resumes the
        same channel internally and only returns here on a real end.
        """
        while not self._shutting_down:
            started = time.monotonic()
            channel_dead = await self._run_one_channel(ws_url)
            if not channel_dead or self._shutting_down:
                # Cancelled (node change / shutdown); stop entirely.
                return
            # A channel ended (a driver finished, or it timed out).
            # Offer another so the device stays drivable. Recreate at
            # once when the channel actually lived a bit -- a driver
            # racing to read the fresh locator right after ending the
            # old one must not find a gap. Back off only when a
            # channel dies almost immediately, which means something
            # is wrong (an unreachable node) rather than a drive
            # having finished.
            if time.monotonic() - started < 2.0:
                await asyncio.sleep(2.0)

    async def _run_one_channel(self, ws_url: str) -> bool:
        """Hold one channel until it dies. True if it died on its own.

        Returns False only if we were cancelled, so the caller knows
        to stop rather than offer another.
        """
        from secrets import token_hex

        assert self._key is not None
        key = self._key
        channel_id = token_hex(16)
        self._channel_id = channel_id
        self._log_index = 0
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        endpoint = SmartSocketEndpoint(
            lambda: _connect(ws_url, channel_id, key_hash),
            send_type=AutomationEvent,
            recv_type=AutomationCommand,
            on_message=self._on_command,
        )
        self._endpoint = endpoint

        # Advertise before we even know the dial worked: the locator
        # is what a human reads out of the log to drive us, and a
        # failed dial retries behind the scenes anyway.
        _log_locator(ws_url, channel_id, key)

        pump = asyncio.create_task(self._pump_log())
        try:
            # No unsolicited hello: a driver asks with HelloCommand on
            # attach. An unprompted one would just sit in the resend
            # buffer until the first driver, then arrive alongside
            # that driver's requested one -- two hellos for no gain.
            await endpoint.run()
        except asyncio.CancelledError:
            pump.cancel()
            raise
        except Exception:  # pylint: disable=broad-except
            logger.exception('automation channel failed')
        finally:
            pump.cancel()
            logger.debug(
                'automation channel ended (code %s)', endpoint.close_code
            )
            if self._endpoint is endpoint:
                self._endpoint = None
        return True

    async def _emit(self, event: AutomationEvent) -> None:
        """Send one event, tolerating a channel that just died."""
        endpoint = self._endpoint
        if endpoint is None:
            return
        try:
            await endpoint.send(event)
        except SmartSocketClosed:
            pass  # The run loop observes this and winds up.

    async def _pump_log(self) -> None:
        """Push new log entries as they appear."""
        envconfig = baenv.get_env_config()
        if envconfig.log_handler is None:
            return

        while True:
            await asyncio.sleep(_POLL_SECONDS)
            endpoint = self._endpoint
            if endpoint is None or not endpoint.connected:
                continue

            archive = envconfig.log_handler.get_cached(
                start_index=self._log_index
            )
            dropped = max(0, archive.start_index - self._log_index)
            if dropped:
                await self._emit(GapEvent(dropped=dropped))
            if not archive.entries:
                continue

            entries = archive.entries
            if len(entries) > _MAX_PENDING_ENTRIES:
                skipped = len(entries) - _MAX_PENDING_ENTRIES
                entries = entries[-_MAX_PENDING_ENTRIES:]
                await self._emit(GapEvent(dropped=skipped))

            self._log_index = archive.start_index + len(archive.entries)
            await self._emit(LogEntriesEvent(entries=entries))

    async def _on_command(self, command: AutomationCommand) -> None:
        """Handle one command from a driver.

        Arrives decoded: the endpoint owns the automation root pair,
        so anything that isn't an AutomationCommand has already
        killed the channel rather than reaching us.
        """
        if isinstance(command, HelloCommand):
            # A driver introducing itself. Our unsolicited hello went
            # out at channel birth and was consumed by whoever was
            # attached then, so this is how every later driver learns
            # what it has reached.
            await self._emit(_hello_event(self._app_instance_id))
        elif isinstance(command, ExecCommand):
            await self._handle_exec(command)
        elif isinstance(command, ScreenshotCommand):
            await self._handle_screenshot(command)
        else:
            logger.warning(
                'unhandled automation command %s', type(command).__name__
            )

    async def _handle_exec(self, command: ExecCommand) -> None:
        """Run driver-supplied code on the logic thread."""
        babase.user_ran_commands()  # disable tourneys/etc.
        babase.pushcall(
            partial(_exec_code, command.code),
            from_other_thread=True,
            other_thread_use_fg_context=True,
        )
        await self._emit(
            ResultEvent(
                tag=command.tag,
                status='ok',
                payload=f'exec {len(command.code.splitlines())} line(s)',
            )
        )
        # Give resulting output a moment to reach the log cache so it
        # rides out with this exec rather than a poll later.
        await asyncio.sleep(0.05)

    async def _handle_screenshot(self, command: ScreenshotCommand) -> None:
        """Capture a frame and send the bytes back.

        Writing a file on the device is no use to a driver somewhere
        else, so we capture to a temp path, read it, and ship it.
        """
        suffix = '.png' if command.lossless else '.jpg'
        path = os.path.join(
            tempfile.gettempdir(), f'ba_automation_shot{suffix}'
        )
        # The device writes a '.meta' JSON sidecar next to the image
        # with the pixel->virtual mapping (see automation.cc
        # WriteScreenshotMeta_); clear both from any prior capture.
        meta_path = path + '.meta'
        for stale in (path, meta_path):
            try:
                os.remove(stale)
            except OSError:
                pass

        from babase import _automation

        if not _automation.available():
            await self._emit(
                ResultEvent(
                    tag=command.tag,
                    status='fail',
                    payload='not_compiled_in',
                )
            )
            return

        # Through babase's own helper rather than the native hook:
        # baplus may not reach the private module, and the helper is
        # where absolute-vs-silo path resolution lives anyway.
        babase.pushcall(
            partial(_automation.screenshot, path, command.tag),
            from_other_thread=True,
        )

        # The capture happens in the graphics context between frames,
        # so wait for the file rather than assuming it is there.
        deadline = time.monotonic() + _SCREENSHOT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            await asyncio.sleep(0.1)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                break
        else:
            await self._emit(
                ResultEvent(
                    tag=command.tag, status='fail', payload='capture_timeout'
                )
            )
            return

        try:
            with open(path, 'rb') as infile:
                data = infile.read()
        except OSError as exc:
            await self._emit(
                ResultEvent(
                    tag=command.tag, status='fail', payload=f'read_failed:{exc}'
                )
            )
            return

        # Read the mapping sidecar. It is written right after the image
        # (same graphics-context call), so it is effectively always
        # present by the time we see the image; allow a couple of brief
        # retries for the microscopic race, then fall back to no mapping
        # (the ScreenshotEvent's content-rect defaults describe the
        # whole image as content).
        meta = await self._read_screenshot_meta(meta_path)

        # A lossless PNG of a large screen can exceed what one channel
        # message may carry. Answer with a clean failure rather than
        # letting the too-large error tear through the dispatch path;
        # the fix if this ever matters is chunking (deferred), not a
        # bigger cap. (JPEG -- the default -- never gets close.)
        try:
            await self._emit(
                ScreenshotEvent(
                    tag=command.tag,
                    data=base64.b64encode(data).decode(),
                    image_format=(
                        ImageFormat.PNG
                        if command.lossless
                        else ImageFormat.JPEG
                    ),
                    width=int(meta.get('iw', 0)),
                    height=int(meta.get('ih', 0)),
                    virtual_width=float(meta.get('vw', 0.0)),
                    virtual_height=float(meta.get('vh', 0.0)),
                    content_l=float(meta.get('cl', 0.0)),
                    content_t=float(meta.get('ct', 0.0)),
                    content_w=float(meta.get('cw', 1.0)),
                    content_h=float(meta.get('ch', 1.0)),
                )
            )
        except SmartSocketPayloadTooLarge as exc:
            await self._emit(
                ResultEvent(
                    tag=command.tag,
                    status='fail',
                    payload=f'image_too_large:{exc.size}',
                )
            )

    async def _read_screenshot_meta(self, meta_path: str) -> dict[str, float]:
        """Read the screenshot mapping sidecar, or {} if unavailable.

        Written right after the image in the same graphics-context call,
        so a couple of brief retries covers the microscopic
        image-exists-but-sidecar-not-yet race. Returns {} on timeout or
        a malformed/absent file; callers fall back to the
        ScreenshotEvent mapping defaults.
        """
        for _ in range(5):
            try:
                with open(meta_path, 'rb') as infile:
                    raw = infile.read()
                if raw:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        return parsed
            except OSError, ValueError:
                pass
            await asyncio.sleep(0.02)
        return {}


def _exec_code(code: str) -> None:
    """Run driver-supplied code on the logic thread.

    Bare exec in this module's globals -- driver-supplied code runs
    with the same freedom a dev-console line does.
    """
    try:
        exec(code)  # pylint: disable=exec-used
    except Exception:  # pylint: disable=broad-except
        logger.exception('error in automation exec')


def _hello_event(app_instance_id: str) -> HelloEvent:
    """Describe ourselves for whoever attaches."""
    env = babase.app.env
    return HelloEvent(
        build_number=env.engine_build_number,
        platform=str(env.platform),
        app_instance_id=app_instance_id,
        gui=env.gui,
    )


def _ws_url_for(node_base_url: str) -> str:
    """Turn the node's http base url into our attach url."""
    if node_base_url.startswith('https://'):
        return 'wss://' + node_base_url[len('https://') :] + '/automationdevice'
    if node_base_url.startswith('http://'):
        return 'ws://' + node_base_url[len('http://') :] + '/automationdevice'
    return node_base_url + '/automationdevice'


def _log_locator(ws_url: str, channel_id: str, key: str) -> None:
    """Log the one string a driver needs to reach us.

    A single opaque handle rather than a URL plus fields: the driver
    side is ``connect(handle)`` and the encoding can grow without
    teaching anyone a new line format. The ephemeral key rides inside
    it so the logged line is a complete copy-paste; a persistent key
    never does (it would outlive the log line it leaked into).
    """
    payload = {
        'v': 1,
        'kind': 'auto',
        'url': ws_url,
        'session_id': channel_id,
    }
    if not os.environ.get(_KEY_ENV_VAR):
        payload['key'] = key
    encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode())
        .decode()
        .rstrip('=')
    )
    # On ba.app, not our own logger: this is the one line a human has
    # to be able to read out of the log to drive us, and ba.app is
    # the only logger at INFO by default. (Same reason the
    # ``[automation]`` result lines use it.) A locator on a
    # suppressed logger is a locator nobody can find.
    logging.getLogger('ba.app').info('automation-channel: %s', encoded)


async def _connect(ws_url: str, channel_id: str, key_hash: str) -> Any:
    """Dial the node for one attach.

    We present our channel id and the hash of our key; the node
    registers them on first contact and checks them on every
    reattach, so a channel is only ever fed by whoever created it.
    """
    import websockets

    from baplus._consolesession import _WsTransport

    sock = await websockets.connect(
        ws_url,
        # ssl only for a wss:// node. When the transport is in insecure
        # mode (the 'Insecure Connections' config / a server downgrade
        # directive for a broken-TLS region) the node url comes through
        # as ws://, and passing an ssl context to a ws:// uri raises.
        # We mirror the transport's own scheme (see v2transport
        # get_connected_node_base_url + its ssl=None-when-insecure).
        ssl=(
            babase.app.net.sslcontext if ws_url.startswith('wss://') else None
        ),
        subprotocols=[websockets.Subprotocol('basmartsocket')],
        additional_headers={
            'User-Agent': babase.user_agent_string(),
            'X-BA-Automation-Id': channel_id,
            'X-BA-Automation-Key-Hash': key_hash,
        },
        open_timeout=10.0,
        # SmartSocket runs its own app-level ping/pong; a second
        # liveness mechanism would only cost us garbage.
        ping_interval=None,
    )
    break_websocket_logger_cycle(sock)
    return _WsTransport(sock)


#: Process-level singleton; an app holds at most one of these.
automation_session_manager = AutomationSessionManager()
