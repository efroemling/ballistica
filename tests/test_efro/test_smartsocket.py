# Released under the MIT License. See LICENSE for details.
#
"""Tests for the SmartSocket endpoint.

The invariant under test is **gapless or dead**: every payload
arrives in order exactly once, or the session ends and says why.
These drive a real :class:`SmartSocketEndpoint` against a scripted
fake relay, which is what makes the interesting rows cheap -- silent
loss, refused reconnects, duplicate and out-of-order injection, and
backpressure are all a few lines here and a manual browser exercise
otherwise.

One fake deliberately serves frames without ever behaving like a
socket (:class:`_BatchTransport`), so the endpoint can't quietly
grow a dependency on connection continuity -- that would foreclose
the poll-mode intermediary later.
"""

import asyncio
from typing import TYPE_CHECKING

from efro.dataclassio import dataclass_from_json, dataclass_to_json
from efro.smartsocket import (
    AckFrame,
    HelloFrame,
    MsgFrame,
    PingFrame,
    PongFrame,
    SmartSocketAction,
    SmartSocketClosed,
    SmartSocketEndpoint,
    SmartSocketFrame,
    SmartSocketChannelPolicy,
    SmartSocketEndpointPolicy,
    SmartSocketSlot,
    SS_CLOSE_CHANNEL_ENDED,
    SS_CLOSE_MAX_DURATION,
    SS_CLOSE_TOKEN_EXPIRED,
    action_for_close_code,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

#: Compressed windows so a whole recovery scenario runs in well
#: under a second. Real defaults are 30s ping / 120s linger.
_FAST_POLICY = SmartSocketEndpointPolicy(
    linger_seconds=1.0,
    max_duration_seconds=30.0,
    ping_interval_seconds=0.1,
)

#: For tests that ride out several reconnect attempts. The reconnect
#: budget is bounded by linger *by design* -- there's no point
#: retrying past the point the relay would drop our slot -- so a
#: linger comparable to the backoff schedule gives up almost at once.
#: Real policy keeps linger far larger than backoff; this mirrors
#: that relationship while staying fast.
_PATIENT_POLICY = SmartSocketEndpointPolicy(
    linger_seconds=10.0,
    max_duration_seconds=30.0,
    ping_interval_seconds=0.1,
)


class _FakeRelay:
    """A scripted peer speaking the relay's half of the wire.

    Holds the session state a relay would (what it has heard from
    us), so resume across a reconnect is exercised for real rather
    than simulated.
    """

    def __init__(self, policy: SmartSocketEndpointPolicy | None = None) -> None:
        self.policy = policy if policy is not None else _FAST_POLICY
        #: Highest contiguous seq we've accepted from the endpoint.
        self.recv = 0
        #: Every payload we ever accepted, in order -- the record
        #: that duplicate and gap assertions are made against.
        self.accepted: list[str] = []
        #: Connections made, so tests can count reattaches.
        self.connects = 0
        #: Reject the next connect outright with this code.
        self.reject_with: int | None = None
        #: Refuse to connect at all this many more times.
        self.refuse_count = 0
        #: Stop answering (a black hole; the connection looks fine).
        self.silent = False
        self.transports: list[_FakeTransport] = []

    async def connect(self) -> '_FakeTransport':
        """Produce a fresh connection, or refuse to."""
        if self.refuse_count > 0:
            self.refuse_count -= 1
            raise ConnectionError('refused')
        if self.reject_with is not None:
            code = self.reject_with
            self.reject_with = None
            raise SmartSocketClosed(code, 'rejected')
        self.connects += 1
        transport = _FakeTransport(self)
        self.transports.append(transport)
        return transport

    @property
    def live(self) -> '_FakeTransport':
        """The most recent connection."""
        return self.transports[-1]

    def handle(self, transport: '_FakeTransport', raw: str) -> None:
        """React to one frame from the endpoint."""
        frame = dataclass_from_json(SmartSocketFrame, raw)
        if isinstance(frame, HelloFrame):
            # Reply with our cursor + policy exactly as a relay does;
            # the endpoint retransmits from there.
            transport.deliver(
                HelloFrame(last_recv=self.recv, policy=self.policy)
            )
        elif isinstance(frame, MsgFrame):
            if frame.seq <= self.recv:
                return  # Dupe from a resume overlap.
            assert (
                frame.seq == self.recv + 1
            ), f'gap: expected {self.recv + 1}, got {frame.seq}'
            self.recv = frame.seq
            self.accepted.append(frame.payload)
            transport.deliver(AckFrame(recv=self.recv))
        elif isinstance(frame, PingFrame):
            transport.deliver(PongFrame())

    def push(self, payload: str, seq: int | None = None) -> None:
        """Send a payload down to the endpoint."""
        transport = self.live
        transport.push_seq = seq if seq is not None else transport.push_seq + 1
        transport.deliver(MsgFrame(seq=transport.push_seq, payload=payload))


class _FakeTransport:
    """One connection between the endpoint and the fake relay."""

    def __init__(self, relay: _FakeRelay) -> None:
        self._relay = relay
        self._inbox: asyncio.Queue[str] = asyncio.Queue()
        self.closed_code: int | None = None
        self.closed_reason = ''
        self.push_seq = 0

    def deliver(self, frame: SmartSocketFrame) -> None:
        """Queue a frame for the endpoint to read."""
        if self._relay.silent:
            return
        self._inbox.put_nowait(dataclass_to_json(frame))

    async def send(self, data: str) -> None:
        """Endpoint -> relay."""
        if self.closed_code is not None:
            raise SmartSocketClosed(self.closed_code, self.closed_reason)
        self._relay.handle(self, data)

    async def recv(self) -> str:
        """Relay -> endpoint."""
        while True:
            if self.closed_code is not None:
                raise SmartSocketClosed(self.closed_code, self.closed_reason)
            data = await self._inbox.get()
            if data:
                return data
            # Empty is the wakeup a close pushes; loop to raise.

    async def close(self, code: int = 1000, reason: str = '') -> None:
        """Close from the endpoint's side."""
        if self.closed_code is None:
            self.closed_code = code
            self.closed_reason = reason
        self._inbox.put_nowait('')  # Unblock a pending recv.

    def drop(self, code: int = 1006, reason: str = 'abnormal') -> None:
        """Kill this connection from the relay's side."""
        self.closed_code = code
        self.closed_reason = reason
        self._inbox.put_nowait('')


class _BatchTransport:
    """A transport with no connection continuity at all.

    Serves a fixed script and then reports closed; nothing about it
    resembles a socket. An endpoint that passes with this one has not
    assumed one -- which is what keeps a poll-mode intermediary open
    to us later.
    """

    def __init__(self, frames: list[SmartSocketFrame]) -> None:
        self.pending = [dataclass_to_json(f) for f in frames]
        self.sent: list[str] = []

    async def send(self, data: str) -> None:
        """Record what the endpoint would have sent."""
        self.sent.append(data)

    async def recv(self) -> str:
        """Serve the next scripted frame."""
        if not self.pending:
            raise SmartSocketClosed(1000, 'batch exhausted')
        return self.pending.pop(0)

    async def close(self, code: int = 1000, reason: str = '') -> None:
        """Discard anything left."""
        del code, reason  # Unused.
        self.pending.clear()


def _endpoint(relay: _FakeRelay, received: list[str]) -> SmartSocketEndpoint:
    """An endpoint wired to append inbound payloads to a list."""

    async def _on_message(payload: str) -> None:
        received.append(payload)

    return SmartSocketEndpoint(
        relay.connect, on_message=_on_message, attach_timeout_seconds=0.5
    )


def _run(coro: 'Coroutine[Any, Any, None]') -> None:
    """Run one async test body."""
    asyncio.run(coro)


async def _wait_for(cond: 'Callable[[], bool]', timeout: float = 5.0) -> None:
    """Poll until a condition holds, or fail the test."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if cond():
            return
        await asyncio.sleep(0.01)
    raise AssertionError('timed out waiting for condition')


# ---------------------------------------------------------------- #
# Close-code interpretation.
# ---------------------------------------------------------------- #


def test_close_code_actions_by_table_and_range() -> None:
    """Unknown codes stay actionable via their range."""
    act = action_for_close_code
    assert act(1000) is SmartSocketAction.DONE
    assert act(SS_CLOSE_TOKEN_EXPIRED) is SmartSocketAction.REFRESH

    # Auth/policy/protocol blocks are fatal...
    assert act(SS_CLOSE_MAX_DURATION) is SmartSocketAction.DEAD
    assert act(SS_CLOSE_CHANNEL_ENDED) is SmartSocketAction.DEAD
    assert act(4202) is SmartSocketAction.DEAD
    # ...including codes this build has never heard of.
    assert act(4155) is SmartSocketAction.DEAD

    # Relay-requested reattach, known and unknown.
    assert act(4300) is SmartSocketAction.RESUME
    assert act(4399) is SmartSocketAction.RESUME

    # Abnormal loss and anything unrecognized: assume the connection
    # died, not the session.
    assert act(1006) is SmartSocketAction.RESUME
    assert act(1011) is SmartSocketAction.RESUME
    assert act(0) is SmartSocketAction.RESUME


def test_per_slot_linger_and_narrowing() -> None:
    """Each slot gets its own window, and endpoints see only theirs."""
    policy = SmartSocketChannelPolicy(
        peer_a_linger_seconds=30.0,
        peer_b_linger_seconds=300.0,
        ping_interval_seconds=15.0,
        max_duration_seconds=1800.0,
    )
    assert policy.linger_for(SmartSocketSlot.PEER_A) == 30.0
    assert policy.linger_for(SmartSocketSlot.PEER_B) == 300.0

    # What an endpoint receives is narrowed to its own slot -- it
    # can't select a per-slot value itself, since it doesn't know
    # which slot it holds.
    for slot, expected in (
        (SmartSocketSlot.PEER_A, 30.0),
        (SmartSocketSlot.PEER_B, 300.0),
    ):
        narrowed = policy.for_slot(slot)
        assert isinstance(narrowed, SmartSocketEndpointPolicy)
        assert narrowed.linger_seconds == expected
        # Shared values ride along unchanged.
        assert narrowed.ping_interval_seconds == 15.0
        assert narrowed.max_duration_seconds == 1800.0

    # And the narrowed form is a distinct type, so it can't be handed
    # back somewhere a channel policy belongs.
    assert not isinstance(
        policy.for_slot(SmartSocketSlot.PEER_A), SmartSocketChannelPolicy
    )


# ---------------------------------------------------------------- #
# Happy path.
# ---------------------------------------------------------------- #


def test_send_and_receive_in_order() -> None:
    """Payloads cross both ways, in order, exactly once."""
    _run(_send_and_receive_in_order())


async def _send_and_receive_in_order() -> None:
    relay = _FakeRelay()
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())

    await _wait_for(lambda: endpoint.connected)
    for i in range(5):
        await endpoint.send(f'up-{i}')
    for i in range(5):
        relay.push(f'down-{i}')

    await _wait_for(lambda: len(received) == 5)
    await _wait_for(lambda: len(relay.accepted) == 5)
    assert relay.accepted == [f'up-{i}' for i in range(5)]
    assert received == [f'down-{i}' for i in range(5)]

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)
    assert endpoint.close_code == 1000


def test_policy_comes_from_the_relay() -> None:
    """Clients take their windows from the hello, not their handle."""
    _run(_policy_comes_from_the_relay())


async def _policy_comes_from_the_relay() -> None:
    relay = _FakeRelay()
    endpoint = _endpoint(relay, [])
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    assert endpoint.policy is not None
    assert endpoint.policy.ping_interval_seconds == 0.1

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


# ---------------------------------------------------------------- #
# Recovery matrix.
# ---------------------------------------------------------------- #


def test_reconnect_resumes_gaplessly() -> None:
    """A dropped connection loses nothing and duplicates nothing."""
    _run(_reconnect_resumes_gaplessly())


async def _reconnect_resumes_gaplessly() -> None:
    relay = _FakeRelay()
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    await endpoint.send('before')
    await _wait_for(lambda: relay.accepted == ['before'])

    # Kill the connection out from under it.
    relay.live.drop()
    await _wait_for(lambda: relay.connects == 2, timeout=10.0)
    await _wait_for(lambda: endpoint.connected, timeout=10.0)

    await endpoint.send('after')
    await _wait_for(lambda: len(relay.accepted) == 2, timeout=10.0)
    # The relay's own gap assertion would have fired on a skipped
    # seq; this catches the other failure, a replay.
    assert relay.accepted == ['before', 'after']

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


def test_unacked_payloads_survive_a_drop() -> None:
    """Sent-into-the-void payloads are retransmitted on resume."""
    _run(_unacked_payloads_survive_a_drop())


async def _unacked_payloads_survive_a_drop() -> None:
    relay = _FakeRelay()
    endpoint = _endpoint(relay, [])
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    # Sever first, then send: the payload can only reach the relay by
    # riding the un-acked buffer through a reattach.
    relay.live.drop()
    await endpoint.send('into-the-void')

    await _wait_for(lambda: relay.accepted == ['into-the-void'], timeout=10.0)

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


def test_duplicate_inbound_seqs_are_dropped() -> None:
    """Redelivery is deduped rather than shown twice."""
    _run(_duplicate_inbound_seqs_are_dropped())


async def _duplicate_inbound_seqs_are_dropped() -> None:
    relay = _FakeRelay()
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.push('one', seq=1)
    await _wait_for(lambda: received == ['one'])
    # The same seq again (what a resume overlap looks like), plus an
    # older one for good measure.
    relay.push('one-again', seq=1)
    relay.push('older', seq=0)
    relay.push('two', seq=2)

    await _wait_for(lambda: received == ['one', 'two'])

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


def test_silent_loss_is_detected_and_recovered() -> None:
    """A black-holed connection is noticed by timeout alone."""
    _run(_silent_loss_is_detected_and_recovered())


async def _silent_loss_is_detected_and_recovered() -> None:
    # No close, no error -- the relay simply stops answering, which
    # is what real wifi loss looks like from a client.
    relay = _FakeRelay(_PATIENT_POLICY)
    endpoint = _endpoint(relay, [])
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.silent = True
    # Detection is 1.5x the 0.1s ping interval; then it reattaches.
    await _wait_for(lambda: relay.connects >= 2, timeout=10.0)
    relay.silent = False
    await _wait_for(lambda: endpoint.connected, timeout=10.0)

    await endpoint.send('post-recovery')
    await _wait_for(lambda: relay.accepted == ['post-recovery'], timeout=10.0)

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


def test_refused_reconnects_back_off_then_recover() -> None:
    """Transient connect failures are retried, not fatal."""
    _run(_refused_reconnects_back_off_then_recover())


async def _refused_reconnects_back_off_then_recover() -> None:
    relay = _FakeRelay(_PATIENT_POLICY)
    endpoint = _endpoint(relay, [])
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.refuse_count = 2
    relay.live.drop()
    # Wait for the reattach itself; 'connected' is still true for an
    # instant after the drop, so waiting on it alone proves nothing.
    await _wait_for(lambda: relay.connects == 2, timeout=15.0)
    await _wait_for(lambda: endpoint.connected, timeout=15.0)

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


def test_dead_close_codes_stop_the_session() -> None:
    """A dead-range code ends things instead of reconnecting."""
    _run(_dead_close_codes_stop_the_session())


async def _dead_close_codes_stop_the_session() -> None:
    relay = _FakeRelay()
    endpoint = _endpoint(relay, [])
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.reject_with = SS_CLOSE_CHANNEL_ENDED
    relay.live.drop()

    await asyncio.wait_for(runner, timeout=15.0)
    assert endpoint.close_code == SS_CLOSE_CHANNEL_ENDED
    assert action_for_close_code(endpoint.close_code) is SmartSocketAction.DEAD
    # And it did not keep hammering a dead channel.
    assert relay.connects == 1


def test_expired_token_triggers_refresh_then_resumes() -> None:
    """4001 refreshes and reattaches, rather than giving up."""
    _run(_expired_token_triggers_refresh_then_resumes())


async def _expired_token_triggers_refresh_then_resumes() -> None:
    relay = _FakeRelay()
    refreshes: list[int] = []

    async def _refresh() -> None:
        refreshes.append(1)

    endpoint = SmartSocketEndpoint(
        relay.connect, refresh=_refresh, attach_timeout_seconds=0.5
    )
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.reject_with = SS_CLOSE_TOKEN_EXPIRED
    relay.live.drop()

    await _wait_for(lambda: len(refreshes) == 1, timeout=10.0)
    await _wait_for(lambda: endpoint.connected, timeout=10.0)

    await endpoint.end()
    await asyncio.wait_for(runner, timeout=5.0)


# ---------------------------------------------------------------- #
# Backpressure.
# ---------------------------------------------------------------- #


def test_send_blocks_when_in_flight_buffer_is_full() -> None:
    """Reliability's mechanism is also its flow control."""
    _run(_send_blocks_when_in_flight_buffer_is_full())


async def _send_blocks_when_in_flight_buffer_is_full() -> None:
    # With nobody acking, the un-acked buffer fills and the writer
    # waits -- it does not silently drop, which would break
    # gapless-or-dead from the inside.
    relay = _FakeRelay()
    endpoint = SmartSocketEndpoint(
        relay.connect, in_flight_cap_bytes=64, attach_timeout_seconds=0.5
    )
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.silent = True  # No acks from here on.
    await endpoint.send('x' * 60)

    blocked = asyncio.ensure_future(endpoint.send('y' * 60))
    await asyncio.sleep(0.2)
    assert not blocked.done(), 'send should have blocked on a full buffer'

    blocked.cancel()
    runner.cancel()
    await asyncio.gather(runner, blocked, return_exceptions=True)


# ---------------------------------------------------------------- #
# No dependence on connection continuity.
# ---------------------------------------------------------------- #


def test_endpoint_works_over_a_discontinuous_transport() -> None:
    """The endpoint must not assume a socket exists continuously."""
    _run(_endpoint_works_over_a_discontinuous_transport())


async def _endpoint_works_over_a_discontinuous_transport() -> None:
    # This transport is a batch of frames and then 'closed' -- no
    # continuity whatsoever. Passing here is what keeps a poll-mode
    # intermediary open to us later.
    received: list[str] = []

    async def _on_message(payload: str) -> None:
        received.append(payload)

    batch = _BatchTransport(
        [
            HelloFrame(last_recv=0, policy=_FAST_POLICY),
            MsgFrame(seq=1, payload='a'),
            MsgFrame(seq=2, payload='b'),
        ]
    )
    served = False

    async def _connect() -> _BatchTransport:
        nonlocal served
        if served:
            raise SmartSocketClosed(1000, 'batch done')
        served = True
        return batch

    endpoint = SmartSocketEndpoint(
        _connect, on_message=_on_message, attach_timeout_seconds=0.5
    )
    await asyncio.wait_for(endpoint.run(), timeout=10.0)

    assert received == ['a', 'b']
    # And it led with a hello, before anything else.
    first = dataclass_from_json(SmartSocketFrame, batch.sent[0])
    assert isinstance(first, HelloFrame)
