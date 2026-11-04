# Released under the MIT License. See LICENSE for details.
#
"""Placeholder remote-app client: finds a game and sends it input."""

import random
import struct
import asyncio
import logging
import threading
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from efro.util import strip_exception_tracebacks

import _baremote
import babase

if TYPE_CHECKING:
    from typing import Callable

logger = logging.getLogger('ba.net')

# Remote-app packet types (BA_PACKET_REMOTE_* in networking.h).
_PACKET_ID_REQUEST = 2
_PACKET_ID_RESPONSE = 3
_PACKET_DISCONNECT = 4
_PACKET_STATE_ACK = 6
_PACKET_DISCONNECT_ACK = 7
_PACKET_STATE2 = 10

# kRemoteAppProtocolVersion in remote_app_server.h.
_PROTOCOL_VERSION = 121

# Sent in an id request to ask for 24-bit (v2) states; a server that
# supports them answers with _PROTOCOL_V2_RESPONSE.
_PROTOCOL_V2_REQUEST = 50
_PROTOCOL_V2_RESPONSE = 100

# Button bits in a v2 state (kRemoteState* in remote_app_server.h).
_BUTTON_JUMP = 1 << 1
_BUTTON_PUNCH = 1 << 2
_BUTTON_THROW = 1 << 3
_BUTTON_BOMB = 1 << 4
_RANDOM_BUTTONS = (_BUTTON_JUMP, _BUTTON_PUNCH, _BUTTON_THROW, _BUTTON_BOMB)

# Axis values are 0-255; this is (close enough to) centered.
_AXIS_CENTER = 128

# Most states we resend in one packet (matches the old remote apps).
_MAX_STATES_PER_PACKET = 11

_ID_REQUEST_INTERVAL = 0.5
_CONNECT_TIMEOUT = 5.0
_RESEND_INTERVAL = 0.1
_KEEPALIVE_INTERVAL = 3.0
_CONNECTION_TIMEOUT = 5.0
_WATCHDOG_INTERVAL = 1.0
_REPORT_INTERVAL = 5.0
_RESCAN_DELAY = 2.0

# How long stop() waits for the network thread. It never blocks on
# anything, so this only guards against a bug.
_STOP_TIMEOUT = 2.0

_COLOR_INFO = (0.6, 0.8, 1.0)
_COLOR_GOOD = (0.4, 1.0, 0.4)
_COLOR_BAD = (1.0, 0.5, 0.3)


@dataclass
class _MessageEvent:
    """Show a screen-message."""

    text: str
    color: tuple[float, float, float]


@dataclass
class _ConnectedEvent:
    """We connected to (or lost) a game."""

    connected: bool


@dataclass
class _IdleEvent:
    """We're free to connect to something (again)."""


type _Event = _MessageEvent | _ConnectedEvent | _IdleEvent


class RemoteClient:
    """Finds a game on the local network and drives it as a controller.

    A placeholder until the remote app-mode has real UI: it connects to
    the nearby game with the best round trip and, while connected,
    forwards the device's controller state (touch controls, keyboard,
    gamepads; combined by the native layer) to it, reporting progress
    as screen-messages and ``ba.net`` log lines.

    Finding games is :attr:`babase.App.nearby`'s job (broadcast plus
    DNS-SD where available; old games are found too). Pass
    ``scan_targets`` to check only specific addresses instead (useful in
    testing so we don't latch onto some other game on the network).
    Pass ``random_input`` to send random presses and stick moves
    instead of real input (for headless testing).

    The protocol runs on a dedicated network thread with its own asyncio
    loop, so packets are handled the moment they arrive and every
    interval is an asyncio timer (nothing polls or blocks). This class is
    the logic-thread side: it hands input and connect requests to that
    thread and applies what comes back (screen-messages, connection
    state). The two only talk through
    :meth:`asyncio.loop.call_soon_threadsafe` one way and
    :func:`babase.pushcall` the other.
    """

    def __init__(
        self,
        scan_targets: list[tuple[str, int]] | None = None,
        random_input: bool = False,
    ) -> None:
        self._random_input = random_input
        self._scan_targets = (
            None if scan_targets is None else list(scan_targets)
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._protocol: _RemoteProtocol | None = None
        self._stop_event: asyncio.Event | None = None
        self._running = False

        # Set while we're looking for a game to connect to.
        self._scan: babase.NearbyScan | None = None

    def start(self) -> None:
        """Spin up the network thread and start scanning."""
        assert babase.in_logic_thread()
        assert self._thread is None
        self._running = True

        # Events from the network thread land here in the logic thread;
        # a weak call so pending ones don't keep us alive.
        on_event = babase.WeakCallPartial(self._on_event)

        def _post(event: _Event) -> None:
            babase.pushcall(
                babase.CallStrict(on_event, event), from_other_thread=True
            )

        self._loop = asyncio.new_event_loop()

        # Made here (it binds to a loop only when first awaited) so a
        # stop() arriving before the thread gets going isn't lost.
        self._stop_event = asyncio.Event()
        self._protocol = _RemoteProtocol(
            loop=self._loop,
            post=_post,
            random_input=self._random_input,
        )
        self._thread = threading.Thread(
            target=self._thread_main, name='remote-client'
        )
        self._thread.start()

        if not self._random_input:
            _baremote.remote_set_input_callback(
                babase.WeakCallPartial(self._on_input_state)
            )
        self._start_scan()

    def stop(self) -> None:
        """Say goodbye to any game we're attached to and shut down.

        Blocks until the network thread has exited (promptly; it never
        waits on anything but its own loop).
        """
        assert babase.in_logic_thread()
        self._running = False
        self._stop_scan()
        _baremote.remote_set_input_callback(None)
        _baremote.remote_set_connected(False)
        if self._thread is None:
            return
        assert self._loop is not None
        try:
            self._loop.call_soon_threadsafe(self._request_stop)
        except RuntimeError:
            pass  # Loop already closed (thread exited on its own).
        self._thread.join(timeout=_STOP_TIMEOUT)
        if self._thread.is_alive():
            logger.error('Remote network thread did not exit in time.')
        self._thread = None
        self._protocol = None
        self._loop = None

    def _thread_main(self) -> None:
        loop = self._loop
        assert loop is not None
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
        except Exception as exc:
            logger.exception('Remote network thread failed.')
            strip_exception_tracebacks(exc)
        finally:
            loop.close()

    async def _run(self) -> None:
        """The network thread's whole life."""
        assert self._protocol is not None
        assert self._stop_event is not None
        protocol = self._protocol

        # IPv4 and IPv6 sockets, so whichever kind of route discovery
        # picks for a game works.
        endpoint = babase.DualStackUDPEndpoint(
            on_datagram=protocol.datagram_received,
            on_error=protocol.error_received,
        )
        if not await endpoint.open():
            logger.warning('Remote: could not open sockets.')
            return
        protocol.begin(endpoint)
        await self._stop_event.wait()
        protocol.end()

        # Let the transports' close callbacks run before the loop goes.
        await asyncio.sleep(0)

    def _request_stop(self) -> None:
        # (Runs on the network thread.)
        assert self._stop_event is not None
        self._stop_event.set()

    def _on_input_state(self, buttons: int, h: int, v: int) -> None:
        """Controller state changed (called from the native layer)."""
        if not self._running or self._loop is None:
            return
        assert self._protocol is not None
        try:
            self._loop.call_soon_threadsafe(
                self._protocol.set_input, buttons, h, v
            )
        except RuntimeError:
            pass  # Loop closed under us; nothing to send to.

    def _on_event(self, event: _Event) -> None:
        """Apply something the network thread told us (logic thread)."""
        if not self._running:
            return
        match event:
            case _MessageEvent():
                babase.screenmessage(
                    event.text, color=event.color, literal=True
                )
            case _ConnectedEvent():
                # Input devices count as attached (and touch controls
                # show) exactly while we're connected.
                _baremote.remote_set_connected(event.connected)
            case _IdleEvent():
                self._start_scan()
            case _:
                assert_never(event)

    def _start_scan(self) -> None:
        if self._scan is not None:
            return
        babase.screenmessage(
            'Remote: scanning for games...', color=_COLOR_INFO, literal=True
        )
        logger.info('Remote: scanning for games...')
        self._scan = babase.app.nearby.scan(
            {babase.NearbyService.REMOTE},
            targets=self._scan_targets,
            on_change=babase.WeakCallPartial(self._on_scan_change),
        )
        # Something may already be known.
        self._on_scan_change()

    def _stop_scan(self) -> None:
        if self._scan is not None:
            self._scan.stop()
            self._scan = None

    def _on_scan_change(self) -> None:
        """Hosts changed while we're looking; maybe connect."""
        if not self._running or self._scan is None or not self._scan.hosts:
            return
        assert self._loop is not None and self._protocol is not None

        # The game with the best round trip (unmeasured ones last).
        host = min(
            self._scan.hosts,
            key=lambda h: 1.0e9 if h.route.rtt is None else h.route.rtt,
        )
        assert host.remote is not None
        route = host.route
        match route.type:
            case babase.NearbyRouteType.UDP:
                addr = (route.address, route.port)
            case _:
                assert_never(route.type)
        self._stop_scan()
        try:
            self._loop.call_soon_threadsafe(
                self._protocol.connect_to, addr, host.remote.name
            )
        except RuntimeError:
            pass  # Loop closed under us.


class _Phase(Enum):
    IDLE = 'idle'
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    WAITING = 'waiting'


class _RemoteProtocol:
    """The remote-app protocol itself; lives on the network thread.

    Everything here runs on that thread's loop, so none of it needs
    locks. It talks to the logic thread only through ``post``.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        post: Callable[[_Event], None],
        random_input: bool,
    ) -> None:
        self._loop = loop
        self._post = post
        self._random_input = random_input
        self._endpoint: babase.DualStackUDPEndpoint | None = None

        self._phase = _Phase.IDLE
        self._pending_target: tuple[tuple[str, int], str] | None = None

        # Bumped on each phase change (see _after/_every).
        self._phase_gen = 0
        self._resend_timer: asyncio.TimerHandle | None = None
        self._keepalive_timer: asyncio.TimerHandle | None = None

        # Identifies us across reconnects; the game shows everything
        # before the '#' as our name.
        self._name = f'Remote#{random.randrange(1 << 32):08x}'
        self._request_id = random.randrange(10000)

        # Connection state.
        self._target: tuple[str, int] | None = None
        self._target_name = ''
        self._client_id = -1
        self._last_heard_time = 0.0

        # Outgoing input states, by 8-bit state id.
        self._states = [0] * 256
        self._state_send_times: list[float | None] = [None] * 256
        self._next_state_id = 0
        self._acked_state_id = 0
        self._buttons = 0
        self._h = _AXIS_CENTER
        self._v = _AXIS_CENTER

        # Stats.
        self._rtts: list[float] = []
        self._presses = 0

    # -- Entry points (all on the network thread) -------------------------

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """A datagram arrived on one of our sockets."""
        if data:
            self._handle_packet(data, addr)

    def error_received(
        self, exc: Exception, addr: tuple[str, int] | None
    ) -> None:
        """A socket reported an error (for a send to ``addr`` if known)."""
        # Expected on some networks (no route, local-network permission
        # denied, etc.); we just keep trying.
        if addr is None:
            logger.debug('Remote socket error: %s', exc)
        else:
            logger.debug(
                'Remote socket error sending to %s:%d: %s',
                addr[0],
                addr[1],
                exc,
            )
        strip_exception_tracebacks(exc)

    def begin(self, endpoint: babase.DualStackUDPEndpoint) -> None:
        """Our sockets are up."""
        self._endpoint = endpoint
        if self._pending_target is not None:
            addr, name = self._pending_target
            self._pending_target = None
            self._start_connecting(addr, name)

    def connect_to(self, addr: tuple[str, int], name: str) -> None:
        """Try to connect to a game (from the logic thread)."""
        if self._phase is not _Phase.IDLE:
            return
        if self._endpoint is None:
            # Our sockets aren't up yet; begin() picks this up.
            self._pending_target = (addr, name)
            return
        self._start_connecting(addr, name)

    def end(self) -> None:
        """Say goodbye and shut down (we're stopping)."""
        if self._phase is _Phase.CONNECTED:
            # One-shot; we don't stick around for the ack.
            for _i in range(3):
                self._send_disconnect()
        self._cancel_phase_timers()
        if self._endpoint is not None:
            self._endpoint.close()
            self._endpoint = None

    def set_input(self, buttons: int, h: int, v: int) -> None:
        """New controller state from the logic thread."""
        if self._phase is not _Phase.CONNECTED:
            return
        if buttons & ~self._buttons:
            self._presses += 1
        self._buttons = buttons
        self._h = h
        self._v = v
        self._add_state()

    # -- Plumbing -------------------------------------------------------------

    def _message(
        self, text: str, color: tuple[float, float, float] = _COLOR_INFO
    ) -> None:
        logger.info('%s', text)
        self._post(_MessageEvent(text, color))

    def _send(self, data: bytes, addr: tuple[str, int]) -> None:
        # Datagram sends never block; failures arrive in error_received.
        if self._endpoint is not None:
            self._endpoint.sendto(data, addr)

    # Phase timers: each phase change bumps _phase_gen, and a timer
    # scheduled in an earlier phase quietly does nothing when it fires.

    # (Plain methods with args rather than closures: a self-referencing
    # closure is a reference cycle, and we avoid those.)

    def _after(self, delay: float, call: Callable[[], None]) -> None:
        """Run ``call`` once after ``delay``, unless the phase ends first."""
        self._loop.call_later(delay, self._fire, self._phase_gen, call)

    def _fire(self, gen: int, call: Callable[[], None]) -> None:
        if self._phase_gen == gen:
            call()

    def _every(self, interval: float, call: Callable[[], None]) -> None:
        """Run ``call`` now and then every ``interval`` for this phase."""
        self._loop.call_soon(self._tick, self._phase_gen, interval, call)

    def _tick(
        self, gen: int, interval: float, call: Callable[[], None]
    ) -> None:
        if self._phase_gen != gen:
            return
        call()
        # (call may have ended the phase.)
        if self._phase_gen == gen:
            self._loop.call_later(interval, self._tick, gen, interval, call)

    def _cancel_phase_timers(self) -> None:
        self._phase_gen += 1
        for timer in (self._resend_timer, self._keepalive_timer):
            if timer is not None:
                timer.cancel()
        self._resend_timer = None
        self._keepalive_timer = None

    def _set_phase(self, phase: _Phase) -> None:
        was_connected = self._phase is _Phase.CONNECTED
        self._cancel_phase_timers()
        self._phase = phase
        connected = phase is _Phase.CONNECTED
        if connected != was_connected:
            self._post(_ConnectedEvent(connected))

    # -- Phases -------------------------------------------------------------

    def _go_idle(self) -> None:
        self._target = None
        self._client_id = -1
        self._set_phase(_Phase.IDLE)
        self._post(_IdleEvent())

    def _wait_then_rescan(self) -> None:
        self._client_id = -1
        self._set_phase(_Phase.WAITING)
        self._after(_RESCAN_DELAY, self._go_idle)

    def _start_connecting(self, addr: tuple[str, int], name: str) -> None:
        self._target = addr
        self._target_name = name
        self._set_phase(_Phase.CONNECTING)
        self._message(
            f"Remote: connecting to '{name}' at {addr[0]}:{addr[1]}..."
        )
        self._every(_ID_REQUEST_INTERVAL, self._send_id_request)
        self._after(_CONNECT_TIMEOUT, self._connect_timed_out)

    def _send_id_request(self) -> None:
        assert self._target is not None
        packet = (
            struct.pack(
                '<BBhB',
                _PACKET_ID_REQUEST,
                _PROTOCOL_VERSION,
                self._request_id,
                _PROTOCOL_V2_REQUEST,
            )
            + self._name.encode()[:99]
        )
        self._send(packet, self._target)

    def _connect_timed_out(self) -> None:
        self._message(
            f"Remote: no answer from '{self._target_name}'.", _COLOR_BAD
        )
        self._wait_then_rescan()

    def _start_connected(self, client_id: int) -> None:
        self._client_id = client_id
        self._set_phase(_Phase.CONNECTED)
        self._last_heard_time = self._loop.time()
        self._next_state_id = 0
        self._acked_state_id = 0
        self._state_send_times = [None] * 256
        self._buttons = 0
        self._h = self._v = _AXIS_CENTER
        self._rtts.clear()
        self._presses = 0
        self._message(
            f"Remote: connected to '{self._target_name}'"
            f' (controller {client_id}).',
            _COLOR_GOOD,
        )
        self._schedule_keepalive()
        self._every(_WATCHDOG_INTERVAL, self._check_connection)
        self._after(_REPORT_INTERVAL, self._report)
        if self._random_input:
            self._after(1.0, self._random_action)

    def _check_connection(self) -> None:
        if self._loop.time() - self._last_heard_time > _CONNECTION_TIMEOUT:
            self._message(
                f"Remote: lost connection to '{self._target_name}'.",
                _COLOR_BAD,
            )
            self._wait_then_rescan()

    def _report(self) -> None:
        if self._rtts:
            avg = sum(self._rtts) / len(self._rtts)
            rtt = f'avg round trip {avg * 1000.0:.1f}ms'
        else:
            rtt = 'no round trips measured'
        self._message(f'Remote: {self._presses} presses sent; {rtt}.')
        self._rtts.clear()
        self._after(_REPORT_INTERVAL, self._report)

    # -- Incoming packets -----------------------------------------------------

    def _handle_packet(self, data: bytes, addr: tuple[str, int]) -> None:
        ptype = data[0]

        # Everything should come from the game we're talking to.
        if addr != self._target:
            return
        self._last_heard_time = self._loop.time()

        if ptype == _PACKET_ID_RESPONSE:
            self._handle_id_response(data)
        elif ptype == _PACKET_STATE_ACK:
            if len(data) == 2 and self._phase is _Phase.CONNECTED:
                self._handle_ack(data[1])
        elif ptype == _PACKET_DISCONNECT:
            if self._phase is _Phase.WAITING:
                return
            reason = _disconnect_reason(data[1] if len(data) > 1 else None)
            self._message(
                f"Remote: '{self._target_name}' disconnected us ({reason}).",
                _COLOR_BAD,
            )
            self._wait_then_rescan()
        elif ptype == _PACKET_DISCONNECT_ACK:
            pass

    def _handle_id_response(self, data: bytes) -> None:
        if len(data) != 3 or self._phase is not _Phase.CONNECTING:
            return
        if data[2] != _PROTOCOL_V2_RESPONSE:
            self._message(
                f"Remote: '{self._target_name}' does not speak protocol v2.",
                _COLOR_BAD,
            )
            self._wait_then_rescan()
            return
        self._start_connected(data[1])

    def _handle_ack(self, next_wanted: int) -> None:
        # The ack names the next state the game wants; everything before
        # it has arrived.
        newly_acked = (next_wanted - self._acked_state_id) & 0xFF
        if newly_acked == 0 or newly_acked > self._unacked_count():
            return
        sent = self._state_send_times[(next_wanted - 1) & 0xFF]
        if sent is not None:
            self._rtts.append(self._loop.time() - sent)
        self._acked_state_id = next_wanted
        if self._unacked_count() == 0 and self._resend_timer is not None:
            self._resend_timer.cancel()
            self._resend_timer = None

    # -- Outgoing states ------------------------------------------------------

    def _unacked_count(self) -> int:
        return (self._next_state_id - self._acked_state_id) & 0xFF

    def _add_state(self, force: bool = False) -> None:
        state = self._buttons | (self._h << 8) | (self._v << 16)
        last = self._states[(self._next_state_id - 1) & 0xFF]
        if state == last and not force:
            return
        sid = self._next_state_id
        self._states[sid] = state
        self._state_send_times[sid] = None
        self._next_state_id = (sid + 1) & 0xFF
        self._schedule_keepalive()

        # Ship right away unless we're already well behind on acks (the
        # resend timer will catch us up then).
        if self._unacked_count() < 3:
            self._ship_states()
        self._schedule_resend()

    def _schedule_keepalive(self) -> None:
        # Keep the game hearing from us even when nothing changes.
        if self._keepalive_timer is not None:
            self._keepalive_timer.cancel()
        self._keepalive_timer = self._loop.call_later(
            _KEEPALIVE_INTERVAL, self._keepalive
        )

    def _keepalive(self) -> None:
        self._keepalive_timer = None
        if self._phase is _Phase.CONNECTED:
            self._add_state(force=True)

    def _schedule_resend(self) -> None:
        if self._resend_timer is None and self._unacked_count() > 0:
            self._resend_timer = self._loop.call_later(
                _RESEND_INTERVAL, self._resend
            )

    def _resend(self) -> None:
        self._resend_timer = None
        if self._phase is _Phase.CONNECTED and self._unacked_count() > 0:
            self._ship_states()
            self._schedule_resend()

    def _ship_states(self) -> None:
        assert self._target is not None
        count = min(self._unacked_count(), _MAX_STATES_PER_PACKET)
        if count < 1:
            return
        now = self._loop.time()
        start = (self._next_state_id - count) & 0xFF
        packet = bytearray([_PACKET_STATE2, self._client_id, count, start])
        for i in range(count):
            sid = (start + i) & 0xFF
            state = self._states[sid]
            packet += bytes(
                [state & 0xFF, (state >> 8) & 0xFF, (state >> 16) & 0xFF]
            )
            if self._state_send_times[sid] is None:
                self._state_send_times[sid] = now
        self._send(bytes(packet), self._target)

    def _send_disconnect(self) -> None:
        if self._target is None or self._client_id < 0:
            return
        self._send(bytes([_PACKET_DISCONNECT, self._client_id]), self._target)

    # -- Random input (testing) ----------------------------------------------

    def _random_action(self) -> None:
        if random.random() < 0.6:
            self._buttons = random.choice(_RANDOM_BUTTONS)
            hold = 0.15
        else:
            self._h = random.choice((0, 255, _AXIS_CENTER))
            self._v = random.choice((0, 255, _AXIS_CENTER))
            hold = 0.5
        self._presses += 1
        self._add_state()
        self._after(hold, self._random_release)

    def _random_release(self) -> None:
        self._buttons = 0
        self._h = self._v = _AXIS_CENTER
        self._add_state()
        self._after(random.uniform(0.3, 1.0), self._random_action)


def _disconnect_reason(code: int | None) -> str:
    # RemoteError in remote_app_server.h.
    match code:
        case 0:
            return 'version mismatch'
        case 1:
            return 'game shutting down'
        case 2:
            return 'not accepting connections'
        case 3:
            return 'not connected'
        case _:
            return f'code {code}'
