# Released under the MIT License. See LICENSE for details.
#
"""SmartSocket protocol: reliable reconnectable two-peer sessions.

A SmartSocket is a reliable, reconnectable, bidirectional session
between exactly two endpoints, relayed by an intermediary. Core
invariant: **gapless or dead** -- every message is delivered in
order exactly once, or the session closes with a reason; it never
silently gaps.

This module is the wire protocol only: the two identity slots, the
session policy, the envelope frames, and the shared close-code
registry. It knows nothing about who issues capability tokens or
what a channel is *for* -- those live with whoever mints channels.
Payloads ride the envelope as opaque strings; the typed per-channel
layer sits above this one.

**These definitions are shipped inside app builds**, so the wire
they describe is public and permanent: storage names, type-id
values, and close-code numbers may never be repurposed, and removed
ones stay retired. Add rather than change.

Canonical design (rationale, tradeoffs, defaults):
``efrohome:docs/global_design/streamcall-smartsocket.md``, the
"SmartSocket v1 wire contract" section.
"""

import time
import asyncio
import logging
from typing import TYPE_CHECKING, Annotated, Protocol, assert_never, override
from enum import Enum
from dataclasses import dataclass, replace

from efro.dataclassio import (
    ioprepped,
    IOMultiType,
    IOAttrs,
    dataclass_from_json,
    dataclass_to_json,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class SmartSocketSlot(Enum):
    """The two peer identity slots of a session.

    A slot is an identity, not a permission set: each owns one seq
    space, one relay-side resend buffer, and one linger clock, and
    reconnect/supersede semantics are per-slot.
    """

    PEER_A = 'a'
    PEER_B = 'b'


@ioprepped
@dataclass
class SmartSocketPolicy:
    """Creation-time policy for a session.

    Rides inside both slots' capability tokens (a session is created
    lazily at first validated attach, so the token is the policy's
    vehicle). The relay echoes it in its hello reply so client
    behavior (reconnect budgets etc.) is server-authoritative -- but
    see :meth:`resolved_for`: what a client receives is the policy
    *as it applies to that slot*, since a client cannot know which
    slot it holds (its token is opaque to it).
    """

    #: How long the session holds state for a silently-lost peer
    #: before dying with PEER_LOST. This is one knob deliberately:
    #: it is also the resend-buffer window and the owner-task
    #: lifetime extension, and there is no point holding one longer
    #: than another. An explicit clean close bypasses it entirely.
    linger_seconds: Annotated[float, IOAttrs('lg', soft_default=120.0)] = 120.0

    #: Absolute session lifetime cap; reaching it is a clean policy
    #: end (MAX_DURATION), not a failure.
    max_duration_seconds: Annotated[
        float, IOAttrs('mx', soft_default=7200.0)
    ] = 7200.0

    #: App-level ping cadence for endpoints that can't observe
    #: WS-protocol pongs (browsers). The loss-detection window is
    #: 1.5x this: no inbound frames for that long means the leg is
    #: silently dead and the client should close and resume.
    ping_interval_seconds: Annotated[
        float, IOAttrs('pi', soft_default=30.0)
    ] = 30.0

    #: Optional peer_b-specific linger, since the two ends can have
    #: opposite cost profiles. Where peer_b is a device that may
    #: vanish into a pocket, minutes are right and nearly free (only
    #: the other end's small commands queue while it's away); where
    #: peer_a is a viewer of a chatty stream, the same window would
    #: instead fill the resend buffer and kill the session. None
    #: means 'use linger_seconds', which is also what a relay too old
    #: to know this field does.
    peer_b_linger_seconds: Annotated[
        float | None, IOAttrs('lgb', soft_default=None)
    ] = None

    def linger_for(self, slot: SmartSocketSlot) -> float:
        """Return the linger window applying to ``slot``."""
        if slot is SmartSocketSlot.PEER_B and (
            self.peer_b_linger_seconds is not None
        ):
            return self.peer_b_linger_seconds
        return self.linger_seconds

    def resolved_for(self, slot: SmartSocketSlot) -> 'SmartSocketPolicy':
        """Return this policy flattened for one slot's point of view.

        Clients read a single ``linger_seconds`` (their reconnect
        budget), and can't select a per-slot value themselves since
        they don't know their own slot. So the relay resolves before
        echoing, and endpoints stay simple.
        """
        return replace(
            self,
            linger_seconds=self.linger_for(slot),
            peer_b_linger_seconds=None,
        )


# ---------------------------------------------------------------- #
# Envelope frames.
# ---------------------------------------------------------------- #
#
# One shared envelope for all SmartSocket channel kinds; per-kind
# typing applies to the (opaque-here) msg payload string. Frames
# travel as dataclassio-json text messages, one frame per message.
# There is no in-band close frame -- closes are native WS
# close(code, reason) per the registry below.


class SmartSocketFrameTypeID(Enum):
    """Type IDs for envelope-frame subclasses."""

    HELLO = 'h'
    MSG = 'm'
    ACK = 'a'
    PING = 'i'
    PONG = 'o'


class SmartSocketFrame(IOMultiType[SmartSocketFrameTypeID]):
    """One envelope frame on a SmartSocket leg."""

    @override
    @classmethod
    def get_type_id(cls) -> SmartSocketFrameTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: SmartSocketFrameTypeID
    ) -> type['SmartSocketFrame']:
        # pylint: disable=cyclic-import
        t = SmartSocketFrameTypeID
        if type_id is t.HELLO:
            return HelloFrame
        if type_id is t.MSG:
            return MsgFrame
        if type_id is t.ACK:
            return AckFrame
        if type_id is t.PING:
            return PingFrame
        if type_id is t.PONG:
            return PongFrame
        assert_never(type_id)


@ioprepped
@dataclass
class HelloFrame(SmartSocketFrame):
    """Sent both directions on every attach; the resume protocol.

    Each side declares the highest contiguous seq it has received on
    its inbound direction; the other side retransmits from
    ``last_recv + 1``. A first connect is simply resume-from-0. The
    relay's hello reply additionally carries the session policy
    snapshot (server-authoritative; clients read reconnect budgets
    etc. from here, never from their handle).
    """

    last_recv: Annotated[int, IOAttrs('r')] = 0
    policy: Annotated[
        SmartSocketPolicy | None, IOAttrs('p', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> SmartSocketFrameTypeID:
        return SmartSocketFrameTypeID.HELLO


@ioprepped
@dataclass
class MsgFrame(SmartSocketFrame):
    """One application message.

    ``seq`` is sender-assigned, session-scoped, starting at 1,
    contiguous per direction. ``payload`` is opaque at this layer;
    the per-channel-kind typed layer encodes/decodes it.
    """

    seq: Annotated[int, IOAttrs('s')]
    payload: Annotated[str, IOAttrs('p')] = ''

    @override
    @classmethod
    def get_type_id(cls) -> SmartSocketFrameTypeID:
        return SmartSocketFrameTypeID.MSG


@ioprepped
@dataclass
class AckFrame(SmartSocketFrame):
    """Cumulative ack: highest contiguous seq received.

    Cumulative-only on purpose -- legs are WS/TCP-ordered, so gaps
    within a connection are impossible and gaps across reconnects are
    handled by the hello exchange. No NACKs, no reassembly.
    """

    recv: Annotated[int, IOAttrs('r')] = 0

    @override
    @classmethod
    def get_type_id(cls) -> SmartSocketFrameTypeID:
        return SmartSocketFrameTypeID.ACK


@ioprepped
@dataclass
class PingFrame(SmartSocketFrame):
    """App-level liveness probe.

    Browsers can't observe WS-protocol pongs, so their loss detection
    is app-level: send a ping every ``ping_interval_seconds``, and
    treat no-inbound-frames-for-1.5x-that as silent leg death. The
    relay answers with :class:`PongFrame`. Non-browser endpoints may
    rely on WS-protocol ping/pong instead and never send these.
    """

    @override
    @classmethod
    def get_type_id(cls) -> SmartSocketFrameTypeID:
        return SmartSocketFrameTypeID.PING


@ioprepped
@dataclass
class PongFrame(SmartSocketFrame):
    """Reply to a :class:`PingFrame`."""

    @override
    @classmethod
    def get_type_id(cls) -> SmartSocketFrameTypeID:
        return SmartSocketFrameTypeID.PONG


# ---------------------------------------------------------------- #
# Shared close-code registry.
# ---------------------------------------------------------------- #
#
# Ranges encode the required client action, so unknown codes remain
# actionable: 40xx = auth (grandfathered streamcall block -- the one
# block handled by table rather than range; 4001 is its lone
# refresh-and-retry member), 41xx = policy end (dead), 42xx =
# protocol error (dead), 43xx = relay-requested reattach (resume).
# Standard codes: 1000 done; 1006/absent = abnormal loss (resume);
# 1011 internal (resume -- a dead session cheaply rejects the hello).
# Codes are the contract; close *reasons* are diagnostics only.

# Auth (shared values with basn.streamcall's WS_CLOSE_* -- one wire
# vocabulary).
SS_CLOSE_TOKEN_EXPIRED = 4001  # refresh token, then resume
SS_CLOSE_TOKEN_INVALID = 4002  # dead
SS_CLOSE_SLOT_MISMATCH = 4003  # dead
SS_CLOSE_NO_TOKEN = 4004  # dead

# Client-sent detach: leg down, may resume; starts the linger clock.
# (A client-sent 1000 instead means "I'm ending the session" -- the
# relay ends it and the surviving peer sees SS_CLOSE_PEER_ENDED.)
SS_CLOSE_DETACH = 4100

# Policy ends (dead).
SS_CLOSE_MAX_DURATION = 4101
SS_CLOSE_PEER_LOST = 4102  # linger exhausted
SS_CLOSE_NODE_DRAINING = 4103
SS_CLOSE_SUPERSEDED = 4104  # a newer attach took this slot
SS_CLOSE_KILLED = 4105  # admin/chaos
SS_CLOSE_PEER_ENDED = 4106  # the other peer ended the session

# Attach against a channel that already ended. Session death is
# permanent per channel_id: the relay tombstones dead ids until token
# expiry so a still-valid token can't silently spring up a *fresh*
# session with reset seq spaces while its holder carries state from
# the dead one. Re-establishing is app-level and always means asking
# the issuer for a new handle, never reusing the old one.
SS_CLOSE_CHANNEL_ENDED = 4107

# Protocol errors (dead; retrying reproduces the bug).
SS_CLOSE_BAD_FRAME = 4201
SS_CLOSE_ROLE_VIOLATION = 4202
SS_CLOSE_SEQ_VIOLATION = 4203


# ---------------------------------------------------------------- #
# Close-code interpretation.
# ---------------------------------------------------------------- #


class SmartSocketAction(Enum):
    """What a close code asks an endpoint to do next.

    Ranges decide this, so a code an endpoint has never heard of is
    still actionable. The browser client library mirrors this in
    about twenty lines of TypeScript; keep the two in step.
    """

    #: Reconnect and hello; the session may still be alive.
    RESUME = 'resume'

    #: Get a fresh token, then resume.
    REFRESH = 'refresh'

    #: The session ended as intended.
    DONE = 'done'

    #: The session is gone. Re-establishing means asking the issuer
    #: for a new handle, never reusing this one.
    DEAD = 'dead'


def action_for_close_code(code: int) -> SmartSocketAction:
    """Interpret a close code by table, then by range."""
    if code == 1000:
        return SmartSocketAction.DONE
    if code == SS_CLOSE_TOKEN_EXPIRED:
        # The lone refresh-and-retry member of an otherwise fatal
        # block; grandfathered from streamcall.
        return SmartSocketAction.REFRESH
    if 4000 <= code < 4300:
        # Auth failures, policy ends, protocol errors. Retrying
        # reproduces them.
        return SmartSocketAction.DEAD
    if 4300 <= code < 4400:
        return SmartSocketAction.RESUME
    # 1006/1011/absent and anything unrecognized: assume the
    # connection died rather than the session. A session that really
    # is gone rejects our hello cheaply.
    return SmartSocketAction.RESUME


# ---------------------------------------------------------------- #
# Endpoint.
# ---------------------------------------------------------------- #


class SmartSocketClosed(Exception):
    """Raised by a transport when its connection has closed.

    Carries the close code, because a SmartSocket's whole recovery
    model is driven by it -- an endpoint that only learns 'the socket
    broke' cannot tell resume from dead.
    """

    def __init__(self, code: int, reason: str = '') -> None:
        detail = reason if reason else '(none)'
        super().__init__(f'closed: code={code} reason={detail}')
        self.code = code
        self.reason = reason


class SmartSocketTransport(Protocol):
    """One connection attempt's worth of plumbing.

    Deliberately similar to :class:`efro.rpcws.WebSocketTransport`,
    but not the same: closes here carry a code both ways, which that
    one has no room for. Keeping it this small is what lets tests
    drive the endpoint with a fake -- and what will let a future
    poll-mode transport stand in for a socket without the endpoint
    noticing.
    """

    async def send(self, data: str) -> None:
        """Send one frame."""

    async def recv(self) -> str:
        """Receive one frame.

        Raises :class:`SmartSocketClosed` when the connection ends.
        """

    async def close(self, code: int = 1000, reason: str = '') -> None:
        """Close the connection with a code."""


class SmartSocketEndpoint:
    """One endpoint of a SmartSocket session.

    Owns the state that survives connections -- seq spaces, the
    un-acked buffer, the log position of what it has received -- and
    the reconnect loop that keeps the session alive across them.
    Reconnects are invisible to the caller; deaths are not.

    The caller supplies ``connect``, which produces a fresh transport
    each attach. That is the whole extension point: it can dial a
    WebSocket, refresh a token first (see ``refresh``), or hand back
    a fake in tests.
    """

    def __init__(
        self,
        connect: Callable[[], Awaitable[SmartSocketTransport]],
        *,
        on_message: Callable[[str], Awaitable[None]] | None = None,
        refresh: Callable[[], Awaitable[None]] | None = None,
        in_flight_cap_bytes: int = 1024 * 1024,
        attach_timeout_seconds: float = 10.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._connect = connect
        self._refresh = refresh
        self._logger = logger or logging.getLogger(__name__)
        self._in_flight_cap = in_flight_cap_bytes
        self._attach_timeout = attach_timeout_seconds

        #: Called with each inbound payload, in order, exactly once.
        self.on_message = on_message

        self.policy: SmartSocketPolicy | None = None
        self.connected = False
        self.done = False
        self.close_code = 0
        self.close_reason = ''

        self._transport: SmartSocketTransport | None = None
        self._next_seq = 1
        self._last_recv = 0
        self._unacked: dict[int, str] = {}
        self._unacked_bytes = 0
        self._space = asyncio.Event()
        self._space.set()
        self._pending_acks = 0
        self._last_inbound = 0.0
        self._reconnect_deadline = 0.0
        self._reconnect_delay = 0.5
        self._stopping = False
        #: Set when *we* close a connection in order to recover.
        #: Our own close code must never be run through the inbound
        #: action table -- SS_CLOSE_DETACH is a code we *send*, and
        #: reading it back as an inbound close says 'dead'.
        self._recovering = False
        self._ended = asyncio.Event()

    # --- caller surface ----------------------------------------

    async def run(self) -> None:
        """Drive the session until it ends.

        Returns when the session is over; ``close_code`` says why
        and :func:`action_for_close_code` says what it means.
        """
        try:
            while not self._stopping:
                action = await self._run_one_connection()
                if action is SmartSocketAction.DONE:
                    break
                if action is SmartSocketAction.DEAD:
                    break
                if action is SmartSocketAction.REFRESH:
                    if self._refresh is None:
                        break
                    try:
                        await self._refresh()
                    except Exception:  # pylint: disable=broad-except
                        self._logger.exception('smartsocket token refresh')
                        break
                    continue
                # RESUME.
                if not await self._await_reconnect_slot():
                    break
        finally:
            self.done = True
            self._ended.set()
            # Unblock anyone waiting on buffer space; nothing will
            # drain it now.
            self._space.set()

    async def send(self, payload: str) -> None:
        """Queue a payload for the peer.

        Buffered until the relay accepts it, so this survives a
        reconnect rather than being dropped. Blocks while the
        in-flight buffer is full -- that back-pressure is the same
        mechanism that provides reliability, so a caller that must
        not block should shed load above this layer (and say so, if
        its contract has a way to).
        """
        while (
            not self.done
            and self._unacked_bytes + len(payload) > self._in_flight_cap
        ):
            self._space.clear()
            await self._space.wait()
        if self.done:
            raise SmartSocketClosed(self.close_code, self.close_reason)

        seq = self._next_seq
        self._next_seq += 1
        self._unacked[seq] = payload
        self._unacked_bytes += len(payload)
        await self._send_frame(MsgFrame(seq=seq, payload=payload))

    async def detach(self, reason: str = 'detaching') -> None:
        """Drop this connection politely, ending the session's wait.

        Tells the relay to start the linger clock rather than sitting
        out a ping timeout. This ends our participation; it does not
        end the session for the peer.
        """
        self._stopping = True
        await self._close_transport(SS_CLOSE_DETACH, reason)

    async def end(self, reason: str = 'done') -> None:
        """End the session for both peers."""
        self._stopping = True
        await self._close_transport(1000, reason)

    async def wait_ended(self) -> None:
        """Wait until the session is over."""
        await self._ended.wait()

    # --- connection lifecycle ----------------------------------

    async def _run_one_connection(self) -> SmartSocketAction:
        """Attach, serve until the connection ends, report why."""
        try:
            self._transport = await self._connect()
        except SmartSocketClosed as exc:
            self._note_close(exc.code, exc.reason)
            return self._action_for(exc.code)
        except Exception:  # pylint: disable=broad-except
            self._logger.exception('smartsocket connect')
            return SmartSocketAction.RESUME

        tasks: list[asyncio.Task] = []
        try:
            # A handshake that never completes would otherwise park us
            # in recv() forever, since liveness doesn't start until the
            # relay's hello arrives.
            tasks.append(asyncio.create_task(self._attach_watchdog()))
            await self._send_frame(HelloFrame(last_recv=self._last_recv))
            await self._read_until_closed(tasks)
        except SmartSocketClosed as exc:
            self._note_close(exc.code, exc.reason)
            return self._action_for(exc.code)
        except Exception:  # pylint: disable=broad-except
            self._logger.exception('smartsocket connection')
            return SmartSocketAction.RESUME
        finally:
            for task in tasks:
                task.cancel()
            self.connected = False
            self._transport = None
        return self._action_for(self.close_code)

    def _action_for(self, code: int) -> SmartSocketAction:
        """Interpret a close, accounting for who caused it.

        A close we initiated to recover is not the relay telling us
        anything -- reading our own SS_CLOSE_DETACH back through the
        inbound table would say 'dead' and throw away a session that
        is fine.
        """
        if self._recovering:
            self._recovering = False
            return SmartSocketAction.RESUME
        return action_for_close_code(code)

    async def _read_until_closed(self, tasks: list[asyncio.Task]) -> None:
        """Frame loop for one connection."""
        transport = self._transport
        assert transport is not None
        helloed = False
        self._last_inbound = time.monotonic()

        while True:
            data = await transport.recv()
            self._last_inbound = time.monotonic()
            frame = dataclass_from_json(SmartSocketFrame, data)

            if isinstance(frame, HelloFrame):
                if helloed:
                    await self._fail(SS_CLOSE_BAD_FRAME, 'duplicate hello')
                    return
                helloed = True
                await self._on_hello(frame)
                # Liveness only starts once we know the policy.
                tasks.append(asyncio.create_task(self._liveness_loop()))
                tasks.append(asyncio.create_task(self._ack_loop()))
            elif isinstance(frame, MsgFrame):
                await self._on_msg(frame)
            elif isinstance(frame, AckFrame):
                self._trim(frame.recv)
            elif isinstance(frame, PingFrame):
                await self._send_frame(PongFrame())
            elif isinstance(frame, PongFrame):
                pass  # Its arrival was the point.
            else:
                # Not assert_never: a newer relay may know frame types
                # we don't, and dying over one would make every future
                # addition a breaking change. (Today an unknown type-id
                # fails earlier, in decode -- worth revisiting if we
                # ever want frames to be additive on the wire.)
                self._logger.debug(
                    'smartsocket ignoring unknown frame %s',
                    type(frame).__name__,
                )

    async def _on_hello(self, frame: HelloFrame) -> None:
        """Relay's hello: adopt policy, retransmit what it lacks."""
        if frame.policy is not None:
            self.policy = frame.policy
        for seq in sorted(self._unacked):
            if seq > frame.last_recv:
                await self._send_frame(
                    MsgFrame(seq=seq, payload=self._unacked[seq])
                )
        # Anything at or below the relay's cursor is safe with it.
        self._trim(frame.last_recv)
        # A working connection: the budget starts over, so a long
        # session isn't penalized for old churn.
        self._reset_reconnect_budget()
        self._reconnect_delay = 0.5
        self.connected = True

    async def _on_msg(self, frame: MsgFrame) -> None:
        """Dedupe, ack, deliver."""
        if frame.seq <= self._last_recv:
            self._pending_acks += 1  # Resume overlap; ack and drop.
            return
        self._last_recv = frame.seq
        self._pending_acks += 1
        if self.on_message is not None:
            await self.on_message(frame.payload)

    def _trim(self, acked: int) -> None:
        for seq in [s for s in self._unacked if s <= acked]:
            self._unacked_bytes -= len(self._unacked[seq])
            del self._unacked[seq]
        self._space.set()

    # --- timers ------------------------------------------------

    async def _liveness_loop(self) -> None:
        """Timeout-driven loss detection.

        No inbound frames within the window IS the signal. Closes and
        errors only get us here sooner; recovery must never depend on
        receiving one, or it works in tests and hangs on real wifi.
        """
        interval = self.policy.ping_interval_seconds if self.policy else 30.0
        while True:
            await asyncio.sleep(interval)
            if time.monotonic() - self._last_inbound > 1.5 * interval:
                # Black-holed: the connection looks fine and is not.
                # Tell the relay we're detaching (so it lingers rather
                # than waiting out a ping timeout) and reattach.
                self._recovering = True
                await self._close_transport(
                    SS_CLOSE_DETACH, 'silent loss detected'
                )
                return
            await self._send_frame(PingFrame())

    async def _attach_watchdog(self) -> None:
        """Give up on a handshake that never completes."""
        await asyncio.sleep(self._attach_timeout)
        if not self.connected:
            self._recovering = True
            await self._close_transport(SS_CLOSE_DETACH, 'attach timeout')

    async def _ack_loop(self) -> None:
        """Lazy ack cadence: flush on a quiet moment or a burst."""
        while True:
            await asyncio.sleep(0.3)
            if self._pending_acks:
                self._pending_acks = 0
                await self._send_frame(AckFrame(recv=self._last_recv))

    async def _await_reconnect_slot(self) -> bool:
        """Back off before reattaching. False means give up."""
        if time.monotonic() > self._reconnect_deadline:
            # Past the point where the relay would have given up on
            # us anyway; call it rather than retry into a tombstone.
            self._note_close(0, 'reconnect budget exhausted')
            return False
        delay = self._reconnect_delay * (1.0 + 0.3 * _jitter())
        self._reconnect_delay = min(self._reconnect_delay * 2.0, 10.0)
        await asyncio.sleep(delay)
        return True

    def _reset_reconnect_budget(self) -> None:
        # Keep trying about as long as the relay will hold our slot.
        linger = self.policy.linger_seconds if self.policy else 120.0
        self._reconnect_deadline = time.monotonic() + linger

    # --- plumbing ----------------------------------------------

    async def _send_frame(self, frame: SmartSocketFrame) -> None:
        transport = self._transport
        if transport is None:
            return  # Detached; it rides the un-acked buffer instead.
        try:
            await transport.send(dataclass_to_json(frame))
        except Exception:  # pylint: disable=broad-except
            # A send failing IS a dead connection -- including a
            # SmartSocketClosed from the transport. Let the read loop
            # observe it and drive recovery; raising here would push a
            # dead *connection* at a caller whose payload is safely
            # buffered for the next one. Only a dead *session* is the
            # caller's problem, and send() checks that itself.
            pass

    async def _fail(self, code: int, reason: str) -> None:
        self._stopping = True
        await self._close_transport(code, reason)

    async def _close_transport(self, code: int, reason: str) -> None:
        transport = self._transport
        self._note_close(code, reason)
        if transport is None:
            return
        try:
            await transport.close(code, reason)
        except Exception:  # pylint: disable=broad-except
            pass

    def _note_close(self, code: int, reason: str) -> None:
        self.close_code = code
        self.close_reason = reason
        self.connected = False


def _jitter() -> float:
    """Reconnect jitter, so a fleet's clients don't sync up."""
    import random

    return random.random()
