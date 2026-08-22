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

# The wire protocol and the endpoint that speaks it, deliberately in
# one module: they are one contract, and the frames are meaningless
# apart from the state machine that interprets them. Splitting would
# mean an ``efro/smartsocket/`` package (the convention used by
# ``bacommon/langstr`` and friends, which keeps importers unchanged) --
# worth doing when this grows again, but it adds files to a module
# synced across six repos, so it is not a drive-by.
# pylint: disable=too-many-lines

import time
import asyncio
import logging
from typing import TYPE_CHECKING, Annotated, Protocol, assert_never, override
from enum import Enum
from dataclasses import dataclass

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
class SmartSocketEndpointPolicy:
    """The parts of a session's policy that apply to *one* endpoint.

    This is what the relay echoes in its hello reply, and it holds
    only what an endpoint can act on -- notably its own linger, which
    is its reconnect budget. Endpoints can't select a per-slot value
    themselves (a client doesn't know which slot it holds; its token
    is opaque to it), so the relay resolves before sending.
    """

    #: How long the relay will hold this endpoint's slot while it is
    #: away -- so, how long reconnecting is still worth trying.
    linger_seconds: Annotated[float, IOAttrs('lg', soft_default=120.0)] = 120.0

    #: App-level ping cadence for endpoints that can't observe
    #: WS-protocol pongs (browsers). The loss-detection window is
    #: 1.5x this: no inbound frames for that long means the leg is
    #: silently dead and the endpoint should close and resume.
    ping_interval_seconds: Annotated[
        float, IOAttrs('pi', soft_default=30.0)
    ] = 30.0

    #: The session's absolute lifetime cap, for endpoints that want to
    #: show or anticipate it. Reaching it is a clean policy end
    #: (MAX_DURATION), enforced by the relay.
    max_duration_seconds: Annotated[
        float, IOAttrs('mx', soft_default=7200.0)
    ] = 7200.0


@ioprepped
@dataclass
class SmartSocketChannelPolicy:
    """Creation-time policy for a whole session, as its issuer sets it.

    Rides inside both slots' capability tokens (a session is created
    lazily at first validated attach, so the token is the policy's
    vehicle). Deliberately *not* the type endpoints receive -- see
    :meth:`for_slot`, which narrows it to one slot's point of view.
    Keeping the two distinct means a resolved policy can never be
    mistaken for a channel policy, which matters because their
    ``linger`` fields would otherwise read identically and mean
    different things.
    """

    #: Linger per slot, i.e. how long the session holds state for
    #: that peer while it is silently gone before dying with
    #: PEER_LOST. Per-slot because the two ends can have opposite
    #: cost profiles: where one is a device that may vanish into a
    #: pocket, minutes are right and nearly free (only the other
    #: end's small messages queue while it's away), while for a
    #: viewer of a chatty stream the same window would instead fill
    #: the resend buffer and kill the session. Linger is one knob
    #: deliberately -- it is also that direction's resend-buffer
    #: window and the owner-task lifetime extension, and there is no
    #: point holding one longer than another.
    peer_a_linger_seconds: Annotated[
        float, IOAttrs('la', soft_default=120.0)
    ] = 120.0
    peer_b_linger_seconds: Annotated[
        float, IOAttrs('lb', soft_default=120.0)
    ] = 120.0

    #: Absolute session lifetime cap; reaching it is a clean policy
    #: end (MAX_DURATION), not a failure.
    max_duration_seconds: Annotated[
        float, IOAttrs('mx', soft_default=7200.0)
    ] = 7200.0

    #: App-level ping cadence handed to both endpoints.
    ping_interval_seconds: Annotated[
        float, IOAttrs('pi', soft_default=30.0)
    ] = 30.0

    def linger_for(self, slot: SmartSocketSlot) -> float:
        """Return the linger window applying to ``slot``."""
        if slot is SmartSocketSlot.PEER_A:
            return self.peer_a_linger_seconds
        return self.peer_b_linger_seconds

    def for_slot(self, slot: SmartSocketSlot) -> SmartSocketEndpointPolicy:
        """Narrow this to what one slot's endpoint should be told."""
        return SmartSocketEndpointPolicy(
            linger_seconds=self.linger_for(slot),
            ping_interval_seconds=self.ping_interval_seconds,
            max_duration_seconds=self.max_duration_seconds,
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
        SmartSocketEndpointPolicy | None, IOAttrs('p', store_default=False)
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


#: Sizing frames uses a seq wide enough that a real one is never
#: longer, so the measurement can only over-estimate.
_SIZING_SEQ = 2**53


def framed_size(payload: str) -> int:
    """Bytes one payload will occupy as a wire message.

    Not ``len(payload)``: a payload is JSON-escaped into its frame, so
    what it costs depends on what is in it. Quote-heavy JSON nearly
    doubles while base64 does not grow at all -- a 2x difference, and
    assuming the worst of it would reject payloads that fit with room
    to spare (an automation screenshot is base64 and inflates ~0%).

    Measuring is cheap here because the frame gets serialized on the
    way out regardless.
    """
    return len(dataclass_to_json(MsgFrame(seq=_SIZING_SEQ, payload=payload)))


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
SS_CLOSE_BAD_PAYLOAD = 4204  # not of the endpoint's declared type

# The two below are never sent on the wire; an endpoint records them
# locally when it gives up. They live in the registry so they cannot
# collide with a real code and so they land in the DEAD band, which
# reads as "do not reconnect" anywhere that interprets a code. Being
# nonzero matters too: consumers commonly test the code for truthiness
# before reporting a reason, so a give-up recorded as 0 gets silently
# dropped along with the only diagnostic string it had.
SS_CLOSE_SERVE_FAILED = 4205  # serving kept throwing
SS_CLOSE_RECONNECT_EXHAUSTED = 4206  # never got back in


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


#: Default minimum silent-loss detection window, regardless of how
#: fast a channel's policy pings. Pings faster than ~10s exist for
#: freshness reporting, not because loss needs detecting that fast;
#: without this floor a 3s ping cadence would cycle the connection
#: over any 5s hiccup. Overridable per endpoint (tests compress
#: every window to run the recovery matrix in seconds).
LOSS_DETECTION_FLOOR_SECONDS = 15.0

#: Consecutive connections that may die from an unexpected exception
#: before the endpoint stops trying.
#:
#: The reconnect budget cannot bound this: a successful hello resets
#: it, so a connection that attaches fine and *then* throws gets a
#: fresh budget every attempt -- and the relay replays its buffered
#: frames on resume, so a failure caused by one reproduces forever.
#: Small on purpose: a transient error clears on the next attempt.
MAX_CONSECUTIVE_SERVE_FAILURES = 3

#: Largest WebSocket message the protocol puts on the wire, in bytes.
#:
#: Every leg's socket-level receive limit is configured to exactly
#: this, explicitly. Left to library defaults they disagree --
#: ``websockets`` caps incoming messages at 1 MiB, ``aiohttp`` at 4 MB
#: -- and a disagreement here does not surface as an error: the relay
#: buffers each frame for resume, so a message the far socket refuses
#: is *retained and retried*, not dropped. A ~1.5 MB bacloud response
#: landed in exactly that gap and presented as a 30-minute hang with
#: the server-side work done in 13 seconds.
MAX_MESSAGE_BYTES = 1024 * 1024

#: Room reserved for the frame envelope around a payload (seq, type
#: id, JSON punctuation). Tiny next to the cap; explicit so the
#: subtraction below is not a mystery constant.
_FRAME_OVERHEAD_BYTES = 1024

#: Largest app payload a single message may carry, in bytes.
#:
#: Smaller than :data:`MAX_MESSAGE_BYTES` because a payload is
#: JSON-escaped *into* its frame, and the payloads here are themselves
#: JSON -- every ``"`` becomes ``\\"``. Measured inflation is ~1.03x
#: for typical bodies and ~1.0x for base64, but the worst case (a
#: payload that is all quotes) is 2.02x, so the halving is what makes
#: "this payload fits" true regardless of content rather than true for
#: the bodies we happen to send today.
#:
#: This is the number a *chunker* splits on -- not one senders check.
#: A sender is guarded against the real framed cost of its payload
#: (see :func:`framed_size` and the checks in
#: :meth:`SmartSocketEndpoint.send`), which lets base64-ish content
#: through at close to the full :data:`MAX_MESSAGE_BYTES`; this value
#: is the pessimistic size that fits regardless of content, so it is
#: what a splitter should use when it already knows a payload is too
#: big. Note a chunker embedding slices in an envelope of its own
#: incurs the 2x escape a second time, so it wants half of this again
#: (see basn's ``_RESPONSE_SLICE_BYTES`` and the automation channel's
#: ``_EVENT_SLICE_BYTES``).
#:
#: It is load-bearing for the relay's resend-buffer and linger math,
#: so it does not grow to fit one caller's message: anything larger
#: must be split *above* this layer.
MAX_PAYLOAD_BYTES = MAX_MESSAGE_BYTES // 2 - _FRAME_OVERHEAD_BYTES


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


class SmartSocketPayloadTooLarge(Exception):
    """A single message exceeds what one send can carry.

    A message must fit within the endpoint's in-flight buffer (it sits
    there un-acked until the relay accepts it), so one larger than the
    whole buffer could never be sent -- without this guard,
    :meth:`SmartSocketEndpoint.send` would wait for space that can
    never appear and block forever. This is a usage error, not a
    transport failure: the session stays alive, and a caller with a
    payload this big must split it above this layer (the small
    per-message caps are load-bearing for the relay's resend buffer
    and linger math, so they don't grow to fit one message).
    """

    def __init__(self, size: int, cap: int) -> None:
        super().__init__(
            f'payload of {size} bytes exceeds the in-flight cap of'
            f' {cap} bytes; split it into smaller messages.'
        )
        self.size = size
        self.cap = cap


class SmartSocketSendWouldDeadlock(Exception):
    """A message handler tried to send past the in-flight cap.

    Inbound messages and acks arrive on one reader loop, and
    :attr:`SmartSocketEndpoint.on_message` runs inside it. So a
    handler that waits for in-flight space is waiting for acks that
    only its own -- now blocked -- reader could consume: a permanent
    wedge, not a slowdown. The endpoint knows when it is inside its
    own dispatch, so it says so here instead of hanging.

    This is the cumulative-send counterpart to
    :class:`SmartSocketPayloadTooLarge`, which catches the same
    hazard for a single oversized message; sending several smaller
    ones from a handler adds up to the same wait with nobody left to
    end it.

    Fixes, in preference order: size the endpoint's
    ``in_flight_cap_bytes`` past anything a handler may send; bound
    what a handler sends and refuse the rest cleanly (a caller told
    'too big' can do something about it; a wedged channel cannot);
    or move the send off the reader loop entirely -- queue the work
    in the handler and serve it from a task of its own.

    Detection is scoped to the dispatching task, so it catches the
    send a handler makes itself (directly or down its own await
    chain) and not one made by some other task that merely happens
    to be sending while a handler runs -- that one has a reader loop
    to un-block it. A handler that hands its send to a task and then
    waits on that task is the same deadlock wearing a disguise, and
    is not detectable here.
    """

    def __init__(self, size: int, unacked: int, cap: int) -> None:
        super().__init__(
            f'sending {size} bytes with {unacked} un-acked would block'
            f' past the in-flight cap of {cap} bytes, from inside a'
            f' message handler -- the acks that would unblock it are'
            f' read by the loop this handler is running on, so it'
            f' would never return.'
        )
        self.size = size
        self.unacked = unacked
        self.cap = cap


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


class SmartSocketEndpoint[SendT: IOMultiType, RecvT: IOMultiType]:
    """One endpoint of a SmartSocket session.

    Owns the state that survives connections -- seq spaces, the
    un-acked buffer, the log position of what it has received -- and
    the reconnect loop that keeps the session alive across them.
    Reconnects are invisible to the caller; deaths are not.

    The caller supplies ``connect``, which produces a fresh transport
    each attach. That is the whole extension point: it can dial a
    WebSocket, refresh a token first (see ``refresh``), or hand back
    a fake in tests.

    **Typed to one channel kind.** A kind declares a root pair of
    :class:`~efro.dataclassio.IOMultiType` hierarchies, one per
    direction, and an endpoint is generic over that pair: it accepts
    only ``SendT`` and hands back only ``RecvT``. Encoding and
    decoding happen here rather than at call sites, so the payload
    types are the contract instead of a convention two ends have to
    remember separately.

    The roots are also passed as ordinary arguments, because Python
    erases generics at runtime and the inbound decode needs the real
    class. A payload that doesn't decode as ``RecvT`` kills the
    session (``SS_CLOSE_BAD_PAYLOAD``) rather than being skipped
    -- 'gapless or dead' leaves no third option for a message we
    cannot deliver.
    """

    def __init__(
        self,
        connect: Callable[[], Awaitable[SmartSocketTransport]],
        *,
        send_type: type[SendT],
        recv_type: type[RecvT],
        on_message: Callable[[RecvT], Awaitable[None]] | None = None,
        refresh: Callable[[], Awaitable[None]] | None = None,
        in_flight_cap_bytes: int = MAX_MESSAGE_BYTES,
        attach_timeout_seconds: float = 10.0,
        loss_detection_floor_seconds: float = (LOSS_DETECTION_FLOOR_SECONDS),
        logger: logging.Logger | None = None,
    ) -> None:
        self._connect = connect
        self._send_type = send_type
        self._recv_type = recv_type
        self._refresh = refresh
        self._logger = logger or logging.getLogger(__name__)
        self._in_flight_cap = in_flight_cap_bytes
        self._attach_timeout = attach_timeout_seconds
        self._loss_detection_floor = loss_detection_floor_seconds

        #: Called with each inbound payload, decoded, in order,
        #: exactly once.
        #:
        #: Runs on the reader loop, which is also what consumes
        #: inbound acks -- so a handler that blocks stops the acks
        #: too, and one that blocks *waiting* on them deadlocks. See
        #: :class:`SmartSocketSendWouldDeadlock`; sending from a
        #: handler is fine, sending more than the in-flight cap's
        #: worth from one is not.
        self.on_message = on_message

        self.policy: SmartSocketEndpointPolicy | None = None
        self.connected = False
        self.done = False
        self.close_code = 0
        self.close_reason = ''
        #: Connections that died from an unexpected exception
        #: since the last one that ended the normal way; see
        #: MAX_CONSECUTIVE_SERVE_FAILURES.
        self._serve_failures = 0

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
        #: Failed dials since the last successful one, and what they
        #: looked like. An outage is logged once and then summarized,
        #: not narrated attempt by attempt; see
        #: :meth:`_note_connect_failure`.
        self._connect_failures = 0
        self._connect_failure_signature: str | None = None
        self._connect_failures_start = 0.0
        self._stopping = False
        #: The task running :attr:`on_message` right now, if any.
        #: Identity, not a bool: only a send made *by* the handler
        #: can be the deadlock, and a send from elsewhere during a
        #: dispatch is an ordinary wait. See
        #: :class:`SmartSocketSendWouldDeadlock`.
        self._dispatch_task: asyncio.Task | None = None
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
            # Seed the budget before the first attach, not just on a
            # hello. Otherwise a first connection that dies before the
            # relay's hello (a refused dial, a TLS hiccup, an attach
            # timeout) finds the deadline still at its 0.0 initial
            # value, reads that as 'budget exhausted', and gives up
            # without ever retrying -- so a session could never
            # survive a bad first attach, only a bad later one.
            self._reset_reconnect_budget()
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

    async def send(self, message: SendT) -> None:
        """Queue a message for the peer.

        Buffered until the relay accepts it, so this survives a
        reconnect rather than being dropped. Blocks while the
        in-flight buffer is full -- that back-pressure is the same
        mechanism that provides reliability, so a caller that must
        not block should shed load above this layer (and say so, if
        its contract has a way to).

        Raises :class:`TypeError` for anything outside this
        endpoint's declared send hierarchy. Static typing catches
        that for typed callers; the check is here for the untyped
        ones, and catches it at the sender rather than as a session
        death on the far end.

        Raises :class:`SmartSocketPayloadTooLarge` for a message
        bigger than the whole in-flight buffer -- it could never be
        sent, so we say so instead of blocking forever waiting for
        space that can't appear.

        Raises :class:`SmartSocketSendWouldDeadlock` when the block
        would happen inside this endpoint's own
        :attr:`on_message` dispatch, where the acks that would end
        it can never arrive.
        """
        if not isinstance(message, self._send_type):
            raise TypeError(
                f'Expected a {self._send_type.__name__} payload;'
                f' got a {type(message).__name__}.'
            )
        payload = dataclass_to_json(message)

        # Two ways one message can be impossible, both of which would
        # otherwise hang: too big for the far socket to receive (it
        # refuses the frame, and the relay replays it forever), or
        # bigger than the whole un-acked buffer (the wait below would
        # never end). Fail loudly instead, at the real framed cost
        # rather than a worst-case guess.
        framed = framed_size(payload)
        if framed > MAX_MESSAGE_BYTES:
            raise SmartSocketPayloadTooLarge(framed, MAX_MESSAGE_BYTES)
        if len(payload) > self._in_flight_cap:
            raise SmartSocketPayloadTooLarge(len(payload), self._in_flight_cap)

        # The third way a send can never finish, and the only one
        # the sizes alone cannot show: a handler's sends adding up
        # past the cap. Waiting would park the reader loop that the
        # acks have to come through, so say so rather than wedging
        # the session in a state where it cannot even notice the
        # peer leaving.
        if (
            not self.done
            and self._unacked_bytes + len(payload) > self._in_flight_cap
            and self._dispatch_task is not None
            and asyncio.current_task() is self._dispatch_task
        ):
            raise SmartSocketSendWouldDeadlock(
                len(payload), self._unacked_bytes, self._in_flight_cap
            )

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
        except Exception as exc:  # pylint: disable=broad-except
            self._note_connect_failure(exc)
            return SmartSocketAction.RESUME
        self._note_connect_success()

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
            self._serve_failures += 1
            self._logger.exception('smartsocket connection')
            if self._serve_failures >= MAX_CONSECUTIVE_SERVE_FAILURES:
                # Reconnecting has reproduced this the same way every
                # time; it is not the connection. Stop, and say so at
                # a level that survives -- looping here is invisible
                # to anyone whose logger is silenced.
                self._logger.error(
                    'smartsocket giving up: %d consecutive failures'
                    ' serving the connection. Reconnecting reproduces'
                    ' this, so it is not a transport problem.',
                    self._serve_failures,
                )
                self._note_close(
                    SS_CLOSE_SERVE_FAILED,
                    f'{self._serve_failures} consecutive failures serving'
                    f' the connection',
                )
                return SmartSocketAction.DEAD
            return SmartSocketAction.RESUME
        finally:
            for task in tasks:
                task.cancel()
            self.connected = False
            self._transport = None
        # Ended by a close code rather than by throwing: whatever the
        # code says, the serving path itself worked.
        self._serve_failures = 0
        return self._action_for(self.close_code)

    def _note_connect_failure(self, exc: BaseException) -> None:
        """Log one failed dial -- once per outage, not once per try.

        A dial failing because the network went away is the expected
        case for a session built to survive exactly that: we retry on
        a backoff until the reconnect budget runs out, so a sleeping
        phone or a dropped wifi produces a dozen identical failures
        by design. Logging each at exception level buries whatever
        else is in the log under a stack of tracebacks that all say
        the same thing, and formatting them is expensive enough to
        show up in log-handler timings on a mobile device.

        So: the first failure of an outage is said once, repeats of
        it go to debug, and the count arrives with the summary on
        recovery or give-up. A failure the retry loop can't be
        expected to fix keeps its traceback -- that one may be a bug
        in the transport we were handed rather than the network.
        """
        signature = f'{type(exc).__name__}: {exc}'
        if not self._connect_failures:
            self._connect_failures_start = time.monotonic()
        self._connect_failures += 1

        if signature == self._connect_failure_signature:
            self._logger.debug(
                'smartsocket connect failed again: %s', signature
            )
            return
        self._connect_failure_signature = signature

        # An errno-bearing failure (DNS, refused, unreachable, reset)
        # or a timeout describes itself completely; its traceback is
        # just our own dial call stack and adds nothing.
        if isinstance(exc, OSError | TimeoutError):
            self._logger.info('smartsocket connect failed: %s', signature)
        else:
            self._logger.error(
                'smartsocket connect failed: %s', signature, exc_info=exc
            )

    def _note_connect_success(self) -> None:
        """Close out an outage the dial just ended."""
        if not self._connect_failures:
            return
        self._logger.info(
            'smartsocket connected after %d failed attempt(s) over %.1fs;'
            ' last failure: %s',
            self._connect_failures,
            time.monotonic() - self._connect_failures_start,
            self._connect_failure_signature,
        )
        self._connect_failures = 0
        self._connect_failure_signature = None

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
            try:
                frame = dataclass_from_json(SmartSocketFrame, data)
            except Exception:  # pylint: disable=broad-except
                # Die rather than resume: the relay replays this
                # frame on reconnect, so retrying reproduces it
                # exactly -- what the close-code table sends to DEAD,
                # arriving as an exception instead of a code. This is
                # how the relay already handles ours.
                self._logger.exception('smartsocket: undecodable frame')
                await self._fail(SS_CLOSE_BAD_FRAME, 'undecodable frame')
                return

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
                if not await self._on_msg(frame):
                    return
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

    async def _on_msg(self, frame: MsgFrame) -> bool:
        """Dedupe, ack, decode, deliver. False means the leg is done."""
        if frame.seq <= self._last_recv:
            self._pending_acks += 1  # Resume overlap; ack and drop.
            return True
        self._last_recv = frame.seq
        self._pending_acks += 1
        if self.on_message is None:
            return True

        try:
            message = dataclass_from_json(self._recv_type, frame.payload)
        except Exception:  # pylint: disable=broad-except
            # Undeliverable, and we may not skip it: a gapless channel
            # that quietly drops one message is worse than a dead one,
            # because the far end has no way to know.
            self._logger.exception(
                'smartsocket: undecodable %s payload', self._recv_type.__name__
            )
            await self._fail(SS_CLOSE_BAD_PAYLOAD, 'undecodable payload')
            return False

        # Marked so a send from inside the handler can tell that
        # its back-pressure has nobody left to relieve it; see
        # SmartSocketSendWouldDeadlock.
        self._dispatch_task = asyncio.current_task()
        try:
            await self.on_message(message)
        finally:
            self._dispatch_task = None
        return True

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

        The detection window is decoupled from the ping cadence via a
        floor: channels may ping fast purely as a *freshness* signal
        (streamcall's end-to-end last-contact reporting pings every
        few seconds), and deriving the window as a bare multiple of
        that would declare silent loss on any brief hiccup and churn
        the connection for nothing.
        """
        interval = self.policy.ping_interval_seconds if self.policy else 30.0
        window = max(1.5 * interval, self._loss_detection_floor)
        while True:
            await asyncio.sleep(interval)
            if time.monotonic() - self._last_inbound > window:
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
            if self._connect_failures:
                # The one line worth a warning in an outage: the
                # quiet retrying above is expected and recoverable,
                # while this is the session actually ending.
                self._logger.warning(
                    'smartsocket giving up after %d failed connect'
                    ' attempt(s) over %.1fs; last failure: %s',
                    self._connect_failures,
                    time.monotonic() - self._connect_failures_start,
                    self._connect_failure_signature,
                )
            self._note_close(
                SS_CLOSE_RECONNECT_EXHAUSTED, 'reconnect budget exhausted'
            )
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
