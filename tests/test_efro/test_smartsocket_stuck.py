# Released under the MIT License. See LICENSE for details.
#
"""Ways a SmartSocket could get stuck instead of failing.

The sibling suite covers "gapless or dead" -- that a message arrives
exactly once or the session says why it didn't. These cover the third
outcome that is supposed to be impossible: neither, forever.

That outcome is not theoretical. A relay buffers each frame for
resume, so anything that makes serving a connection fail *because of
a buffered frame* reproduces on every reconnect; and the reconnect
budget cannot bound it, because a successful hello resets the budget
before the failure happens. Endpoints whose logger is silenced
(bacloud's is, unless BACLOUD_VERBOSE) then spin with nothing to
show. A ~1.5 MB response hitting a mismatched socket size limit did
exactly this for half an hour, and the only thing the user saw was
"closed mid-command".
"""

import asyncio

# Before the efro import on purpose: repos lay this package out
# differently (legacy keeps efro under src/, so pylint reads efro as
# first-party and this as third-party there), and third-party-first is
# the order that satisfies every one of them.
from test_efro.test_smartsocket import (
    _FakeRelay,
    _endpoint,
    _run,
    _send,
    _wait_for,
)

from efro.smartsocket import (
    MAX_CONSECUTIVE_SERVE_FAILURES,
    MAX_MESSAGE_BYTES,
    MAX_PAYLOAD_BYTES,
    SS_CLOSE_BAD_FRAME,
    SS_CLOSE_RECONNECT_EXHAUSTED,
    SS_CLOSE_SERVE_FAILED,
    SmartSocketAction,
    SmartSocketPayloadTooLarge,
    action_for_close_code,
    framed_size,
)


def test_an_undecodable_frame_kills_rather_than_reconnects() -> None:
    """A frame we can't decode must not be retried into forever."""
    _run(_an_undecodable_frame_kills_rather_than_reconnects())


async def _an_undecodable_frame_kills_rather_than_reconnects() -> None:
    # The relay holds each frame in its resend buffer and replays it
    # on reconnect, so a frame we cannot decode reproduces on every
    # attempt. Treating that as a dead *connection* reattaches into
    # the identical frame forever -- and an endpoint whose logger is
    # silenced (bacloud's is, unless BACLOUD_VERBOSE) spins with
    # nothing to show for it. It has to die the way the relay already
    # dies for our frames.
    relay = _FakeRelay()
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    relay.live.deliver_raw('this is not a frame at all')

    await asyncio.wait_for(runner, timeout=5.0)
    assert endpoint.done
    assert endpoint.close_code == SS_CLOSE_BAD_FRAME
    assert action_for_close_code(endpoint.close_code) is SmartSocketAction.DEAD
    # The point: it stopped instead of reattaching over and over.
    assert relay.connects == 1, f'reattached {relay.connects} times'


def test_a_deterministic_serve_failure_gives_up() -> None:
    """Repeated identical failures stop, rather than loop forever."""
    _run(_a_deterministic_serve_failure_gives_up())


async def _a_deterministic_serve_failure_gives_up() -> None:
    # The reconnect budget cannot bound this on its own: it resets on
    # every successful hello, so a connection that attaches fine and
    # then throws gets a fresh budget each time. Without a separate
    # count of consecutive serve failures this reattaches forever.
    relay = _FakeRelay()
    relay.throw_after_hello = True
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())

    await asyncio.wait_for(runner, timeout=10.0)
    assert endpoint.done
    assert endpoint.close_code == SS_CLOSE_SERVE_FAILED
    assert action_for_close_code(endpoint.close_code) is SmartSocketAction.DEAD
    assert relay.connects == MAX_CONSECUTIVE_SERVE_FAILURES, (
        f'attached {relay.connects} times, expected to stop at'
        f' {MAX_CONSECUTIVE_SERVE_FAILURES}'
    )


def test_a_transient_serve_failure_still_recovers() -> None:
    """The give-up must not fire on an error that clears itself."""
    _run(_a_transient_serve_failure_still_recovers())


async def _a_transient_serve_failure_still_recovers() -> None:
    # The counter is only allowed to end sessions that are genuinely
    # stuck; one bad connection followed by a good one is the ordinary
    # case a reconnecting transport exists for.
    relay = _FakeRelay()
    relay.throw_after_hello = True
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: relay.connects >= 1)
    relay.throw_after_hello = False

    await _wait_for(lambda: endpoint.connected)
    assert not endpoint.done
    await _send(endpoint, 'still working')
    await _wait_for(lambda: relay.accepted_text == ['still working'])

    runner.cancel()
    await asyncio.gather(runner, return_exceptions=True)


def test_give_ups_record_a_code_a_consumer_will_report() -> None:
    """Every give-up needs a truthy code in the dead band.

    Consumers commonly guard on ``if close_code`` before reporting a
    reason. Recording a give-up as 0 therefore threw away the only
    diagnostic string it had -- 'reconnect budget exhausted' became a
    bare 'closed', which is what made these failures so hard to read.
    """
    for code in (SS_CLOSE_SERVE_FAILED, SS_CLOSE_RECONNECT_EXHAUSTED):
        assert code, 'a give-up code must be truthy'
        assert action_for_close_code(code) is SmartSocketAction.DEAD


def test_sendability_is_measured_not_assumed() -> None:
    """A payload's real framed cost decides it, not a worst case."""
    _run(_sendability_is_measured_not_assumed())


async def _sendability_is_measured_not_assumed() -> None:
    # A payload is JSON-escaped into its frame, so what it costs
    # depends on content: quote-heavy JSON nearly doubles, base64 does
    # not grow at all. Rejecting everything past the always-safe size
    # would turn away payloads that fit with room to spare -- and the
    # consumer that notices is the automation channel, which ships
    # screenshots as base64 and reports 'image_too_large' on a refusal.
    import base64

    # ~700 KB of base64: past the always-safe size, under the wire cap.
    # (Sized from raw bytes: base64 is 4 chars per 3 bytes.)
    blob = base64.b64encode(b'\x00\xff' * 262500).decode()
    assert len(blob) > MAX_PAYLOAD_BYTES, 'fixture is not past the safe size'
    assert framed_size(blob) <= MAX_MESSAGE_BYTES, 'fixture cannot fit at all'

    relay = _FakeRelay()
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    # The assertion that matters: this goes through. Judging it by the
    # always-safe size instead would refuse it.
    await _send(endpoint, blob)
    await _wait_for(lambda: relay.accepted_text == [blob])

    runner.cancel()
    await asyncio.gather(runner, return_exceptions=True)


def test_an_unsendable_payload_raises_rather_than_hangs() -> None:
    """Too big for the far socket is a refusal, never a wait."""
    _run(_an_unsendable_payload_raises_rather_than_hangs())


async def _an_unsendable_payload_raises_rather_than_hangs() -> None:
    # The far socket refuses an over-cap message and the relay keeps
    # replaying it, so this has to be stopped at the sender. It is a
    # usage error, not a transport failure: the session stays alive.
    relay = _FakeRelay()
    received: list[str] = []
    endpoint = _endpoint(relay, received)
    runner = asyncio.ensure_future(endpoint.run())
    await _wait_for(lambda: endpoint.connected)

    raised = False
    try:
        await _send(endpoint, '"' * MAX_MESSAGE_BYTES)
    except SmartSocketPayloadTooLarge as exc:
        raised = True
        assert exc.size > MAX_MESSAGE_BYTES
    assert raised, 'an unsendable payload must raise, not block'

    assert not endpoint.done
    await _send(endpoint, 'ok')
    await _wait_for(lambda: relay.accepted_text == ['ok'])

    runner.cancel()
    await asyncio.gather(runner, return_exceptions=True)
