# Released under the MIT License. See LICENSE for details.
#
"""Connectivity + v2transport gating and recovery on network-availability.

Connectivity and v2transport both listen to the platform's network-
availability signal. They (a) skip outbound work while the OS reports
no usable network path, (b) wake immediately on the False -> True
transition rather than waiting for their next scheduled tick, and
(c) treat gating-caused failures as non-failures for retry-backoff
purposes (so a brief offline window doesn't inflate later wait times).

This file boots a fresh headless client with the
``BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE=1`` env var, which makes the
platform layer flip the reported availability between False and True
every 5 seconds (starting in False). The toggle exists exactly so we
can exercise this code path deterministically without actually
severing the network. We then look at the log stream to verify:

- No ``Fetching ping-target-list`` log fires during the initial
  unavailable window (connectivity gating works).
- A fetch attempt fires shortly after the first ``Network
  availability changed: true`` log (connectivity kick works).
- No ``Trying WS connection`` log fires during the initial
  unavailable window (v2transport gating works).
- A WS-connect attempt fires shortly after the flip (v2transport
  wake-event works).
- v2transport's pre-flip backoff sleeps stay in the tier-0 range,
  proving gated failures aren't escalating the retry-backoff.

The test stops as soon as it sees the recovery WS-connect attempt
(which lands a few ms after the connectivity fetch attempt),
typically completing in ~5.5 seconds.
"""

import os
import re
import shutil
from pathlib import Path

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

# Project root (two levels up from this test file).
_PROJROOT = Path(__file__).resolve().parents[2]

# Hard timeout. The toggle flips True at ~5s after launch and the
# kick should fire a fetch within tens of milliseconds; this is the
# safety net.
_HEADLESS_TIMEOUT_SECONDS = 15

# Maximum acceptable latency between the False->True availability
# flip and the resulting recovery action. Should be tens of
# milliseconds in practice; this generous bound allows for CI variance
# and asyncio scheduling overhead. If recovery takes noticeably
# longer, the wake mechanism is likely broken and the subsystem is
# waiting for its next scheduled iteration.
_RECOVERY_LATENCY_MAX_SECONDS = 2.0

# v2transport's tier-0 backoff base is 2.4s with ±25% jitter, so
# tier-0 sleeps fall in [1.8, 3.0]s. Tier-1 (errors >= 2) is 5.12s
# with ±25% jitter -> [3.84, 6.4]s. A pre-flip sleep > this threshold
# means gated failures escalated us out of tier 0 — exactly the
# regression we're guarding against.
_TIER_0_MAX_SLEEP_SECONDS = 3.5

# Log lines look like ``5.473 INFO ba.connectivity: Fetching ...``.
# The leading number is seconds-since-launch.
_LOG_LINE_RE = re.compile(
    r'^(\d+\.\d+)\s+\S+\s+ba\.\S+:\s*(.+?)\s*$', re.MULTILINE
)
_AVAIL_CHANGED_TRUE_RE = re.compile(r'Network availability changed: true')
_FETCHING_RE = re.compile(r'Fetching ping-target-list from ')
_WS_CONNECT_RE = re.compile(r'Trying WS connection to ')
_BACKOFF_SLEEP_RE = re.compile(
    r'No transport-sessions remain; will spawn new one in ([\d.]+)s'
)


def _silo_dir(instance: str) -> Path:
    """Path to the per-instance silo under build/test_run/."""
    return _PROJROOT / 'build' / 'test_run' / instance


def _first_match(
    output: str, content_re: re.Pattern[str]
) -> re.Match[str] | None:
    """Return the first log line whose content matches ``content_re``."""
    for m in _LOG_LINE_RE.finditer(output):
        if content_re.search(m.group(2)):
            return m
    return None


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_network_availability_gating_and_recovery() -> None:
    """End-to-end gating + recovery for connectivity and v2transport."""
    instance = 'network-availability-gating'
    silo = _silo_dir(instance)
    shutil.rmtree(silo, ignore_errors=True)
    ba_root = silo / 'ba_root'
    ba_root.mkdir(parents=True, exist_ok=True)

    proc = apprun.run_headless_capture(
        purpose='network-availability gating',
        config_dir=str(ba_root),
        env={
            # Make the platform layer toggle availability deterministically.
            'BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE': '1',
            # Capture connectivity-side gating logs, v2transport-side
            # backoff/connect logs, and the platform-side change log
            # together.
            'BA_LOG_LEVELS': (
                'ba.connectivity=DEBUG,ba.v2transport=DEBUG,ba.net=DEBUG'
            ),
        },
        timeout=_HEADLESS_TIMEOUT_SECONDS,
        # Stop on the first WS-connect attempt — that's the
        # latest-firing of the recovery actions we want to see, so
        # everything earlier (flip log, fetch log, backoff sleep
        # logs) is already in the captured output by then.
        stop_pattern=_WS_CONNECT_RE,
    )
    output = proc.stdout.decode(errors='replace')

    # --- Locate marker events --------------------------------------------

    flip_match = _first_match(output, _AVAIL_CHANGED_TRUE_RE)
    assert flip_match is not None, (
        'No "Network availability changed: true" log line found.'
        ' The debug toggle thread should flip the value to True'
        ' ~5s after launch; check that'
        ' BA_NETWORK_AVAILABILITY_DEBUG_TOGGLE is being honored by'
        ' the platform layer.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    flip_time = float(flip_match.group(1))

    fetch_match = _first_match(output, _FETCHING_RE)
    assert fetch_match is not None, (
        'No "Fetching ping-target-list" log line found. The'
        ' connectivity kick on availability=True should have'
        ' triggered an immediate fetch.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    fetch_time = float(fetch_match.group(1))

    ws_match = _first_match(output, _WS_CONNECT_RE)
    assert ws_match is not None, (
        'No "Trying WS connection" log line found. The v2transport'
        ' wake event on availability=True should have interrupted'
        ' its sleep and produced a real WS-connect attempt.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    ws_time = float(ws_match.group(1))

    # --- Gating: no recovery actions before the flip ---------------------

    # ``finditer`` walks the string in order, so the first match is
    # the chronologically-earliest occurrence. If it lands before the
    # flip, gating failed to suppress it.
    assert fetch_time > flip_time, (
        f'Fetch ({fetch_time:.3f}s) appeared BEFORE the True flip'
        f' ({flip_time:.3f}s); connectivity gating failed to'
        f' suppress fetches during the initial unavailable window.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    assert ws_time > flip_time, (
        f'WS-connect ({ws_time:.3f}s) appeared BEFORE the True flip'
        f' ({flip_time:.3f}s); v2transport gating failed to suppress'
        f' connect attempts during the initial unavailable window.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )

    # --- Recovery latency ------------------------------------------------

    fetch_latency = fetch_time - flip_time
    assert fetch_latency < _RECOVERY_LATENCY_MAX_SECONDS, (
        f'Connectivity fetch latency {fetch_latency:.3f}s exceeds the'
        f' {_RECOVERY_LATENCY_MAX_SECONDS}s budget. The kick on'
        ' False->True availability flip likely is not waking the'
        ' connectivity cycle promptly.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    ws_latency = ws_time - flip_time
    assert ws_latency < _RECOVERY_LATENCY_MAX_SECONDS, (
        f'v2transport WS-connect latency {ws_latency:.3f}s exceeds'
        f' the {_RECOVERY_LATENCY_MAX_SECONDS}s budget. The wake'
        ' event on False->True availability flip likely is not'
        ' interrupting v2transport\'s sleep promptly.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )

    # --- Backoff doesn't escalate during gated period --------------------

    # Each session that fails during gating bumps a sleep entry in
    # the v2transport log: "No transport-sessions remain; will spawn
    # new one in N.NNs". If our "don't count gated failures toward
    # backoff" logic regressed, sleeps would escalate from tier-0
    # (~2.4s base) to tier-1 (~5.12s base) and beyond. Verify all
    # pre-flip sleeps stay in tier-0 range.
    pre_flip_sleeps: list[float] = []
    for m in _LOG_LINE_RE.finditer(output):
        if float(m.group(1)) >= flip_time:
            break
        sleep_match = _BACKOFF_SLEEP_RE.search(m.group(2))
        if sleep_match is not None:
            pre_flip_sleeps.append(float(sleep_match.group(1)))

    assert pre_flip_sleeps, (
        'Expected at least one v2transport backoff sleep log entry'
        ' before the flip (sessions should have failed via the gate'
        ' during the initial unavailable window).\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    for sleep_seconds in pre_flip_sleeps:
        assert sleep_seconds <= _TIER_0_MAX_SLEEP_SECONDS, (
            f'v2transport backoff sleep {sleep_seconds:.2f}s exceeds'
            f' tier-0 max ({_TIER_0_MAX_SLEEP_SECONDS}s); gated'
            ' failures appear to be escalating backoff. Check that'
            ' on_session_finished only increments _consecutive_errors'
            ' when network_available is True.\n'
            f'pre-flip sleeps: {pre_flip_sleeps}\n'
            f'--- output (tail) ---\n{output[-4000:]}'
        )
