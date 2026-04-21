# Released under the MIT License. See LICENSE for details.
#
"""Runtime tests for the V2 transport connection lifecycle.

Exercises the end-to-end session lifecycle (connect → handoff) by
launching the real binary and scraping stdout.

Runs against the binary's compiled-in fleet (prod) by default.
Set ``BA_FLEET=dev`` + ``BA_BOOTSTRAP_OVERRIDE=https://<host>``
externally to test against dev — useful during development before
new server endpoints have rolled to prod. ``apprun.acquire_binary``
provides a headless-server binary (prefab or locally built depending
on ``BA_APP_RUN_ENABLE_BUILDS``) which is sufficient for transport
tests.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from typing import TYPE_CHECKING

import pytest

from batools import apprun

if TYPE_CHECKING:
    from typing import Mapping


FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

# Log-line substrings we assert on. Keep in sync with v2transport.py.
#
# Logged when a session completes its WS handshake against a basn
# host. Presence of this line confirms the full connect flow
# (servernodequery fetch → host list → WS connect → handshake)
# succeeded end-to-end.
_LOG_SESSION_0_CONNECTED = 'session_0: Connected to '
# Handoff sequence: session_0 gets a shutdown warning near end of
# its duration; V2Transport spins up session_1 as a preload; once
# session_1 connects, it takes over as primary when session_0 closes.
_LOG_SHUTDOWN_WARNING = 'Got transport-agent-shutdown-warning'
_LOG_PRELOAD_SPAWN = 'Spinning up preload transport-session'
_LOG_SESSION_1_CONNECTED = 'session_1: Connected to '
# ClientRejection path (see ConnectivityManager._handle_rejection):
# connectivitylog.info(...) always fires; V2Transport.enter_vegetable_mode
# emits the vegetable-mode line only for PERMANENT kind.
_LOG_REJECTION_PERMANENT = 'Got ClientRejection kind=PERMANENT'
_LOG_REJECTION_TRANSIENT = 'Got ClientRejection kind=TRANSIENT'
_LOG_VEGETABLE_MODE = 'Entering vegetable mode.'


def _run_until(
    config_dir: str,
    env: Mapping[str, str],
    pattern: str,
    *,
    hard_timeout: float = 10.0,
    gate_pattern: str | None = None,
    min_occurrences: int = 1,
) -> str:
    """Stream binary stdout until ``pattern`` appears, then terminate.

    Returns all captured output. If ``pattern`` never appears before
    ``hard_timeout``, returns whatever was captured so the caller can
    produce a useful failure message.

    If ``gate_pattern`` is supplied, ``pattern`` matches are only
    treated as terminators after ``gate_pattern`` has appeared at
    least once. This is how the handoff test avoids terminating on a
    retry-spawned session that happens to match the same
    ``session_1: Connected to`` line the real handoff produces — we
    gate on ``_LOG_PRELOAD_SPAWN``, which only fires on a genuine
    shutdown-warning-driven preload.

    ``min_occurrences`` raises the match bar — useful for verifying
    retry loops that re-fire the same log line. Default 1.
    """
    binpath = os.path.abspath(apprun.acquire_binary(purpose='transport test'))
    bindir = os.path.dirname(binpath)

    env_final = dict(os.environ)
    env_final.update(env)
    env_final.setdefault(
        'BA_LOG_LEVELS', 'ba.v2transport=DEBUG,ba.connectivity=DEBUG'
    )
    # Transport tests only exercise outbound connections; skip the
    # UDP listener entirely. Avoids port-conflict fatals on shared CI
    # hosts, OS firewall prompts, and wasted file descriptors.
    env_final.setdefault('BA_NO_UDP_LISTENER', '1')

    cmd = [binpath, '--config-dir', config_dir]
    captured: list[str] = []
    with subprocess.Popen(
        cmd,
        cwd=bindir,
        env=env_final,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ) as proc:
        assert proc.stdout is not None
        deadline = time.monotonic() + hard_timeout
        gate_passed = gate_pattern is None
        match_count = 0
        try:
            for raw in iter(proc.stdout.readline, b''):
                line = raw.decode(errors='replace')
                captured.append(line)
                if (
                    not gate_passed
                    and gate_pattern is not None
                    and gate_pattern in line
                ):
                    gate_passed = True
                if gate_passed and pattern in line:
                    match_count += 1
                    if match_count >= min_occurrences:
                        break
                if time.monotonic() > deadline:
                    break
        finally:
            proc.send_signal(signal.SIGTERM)
            try:
                rest, _ = proc.communicate(timeout=5.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                rest, _ = proc.communicate()
            captured.append(rest.decode(errors='replace'))
    return ''.join(captured)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_session_connects() -> None:
    """Basic end-to-end: launch binary, session_0 reaches basn.

    Smoke test over the whole connect plumbing — servernodequery
    fetch, host list, WS connect, handshake. Fast-feedback signal
    (~seconds) for the common class of regressions (endpoint broken,
    auth wrong, host unreachable, etc.); ``test_session_handoff``
    covers the same path implicitly but takes ~45 s.
    """
    with tempfile.TemporaryDirectory() as cfgdir:
        out = _run_until(
            cfgdir,
            env={},
            pattern=_LOG_SESSION_0_CONNECTED,
            hard_timeout=15.0,
        )
    assert _LOG_SESSION_0_CONNECTED in out, (
        f'Expected {_LOG_SESSION_0_CONNECTED!r} in connect output.\n'
        f'--- stdout ---\n{out}'
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_session_handoff() -> None:
    """Short-duration sessions exercise the preload/handoff cycle.

    With ``BA_DEBUG_V2_TRANSPORT_SHORT_DURATION=1`` the client asks
    basn for 40-second sessions (the basn-side minimum). basn sends
    a shutdown-warning 30s before the session's close, and the
    client reacts by spawning a preload session (``session_1``) that
    takes over as primary when ``session_0`` closes. The test runs
    long enough to observe at least one full handoff.

    Timeout is generous enough to cover basn versions that still
    enforce the older 60s floor (in which case session_1 appears
    at ~30s instead of ~10s) so the test remains stable during any
    server-side rollout.
    """
    with tempfile.TemporaryDirectory() as cfgdir:
        out = _run_until(
            cfgdir,
            env={'BA_DEBUG_V2_TRANSPORT_SHORT_DURATION': '1'},
            pattern=_LOG_SESSION_1_CONNECTED,
            # Gate on preload spawn so a retry-after-failure session
            # (e.g. from basn capacity rejection) doesn't falsely
            # trigger termination — only the preload-driven session_1
            # connect counts.
            gate_pattern=_LOG_PRELOAD_SPAWN,
            hard_timeout=45.0,
        )
    assert _LOG_SHUTDOWN_WARNING in out, (
        f'Expected {_LOG_SHUTDOWN_WARNING!r} in handoff output.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_PRELOAD_SPAWN in out, (
        f'Expected {_LOG_PRELOAD_SPAWN!r} in handoff output.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_SESSION_1_CONNECTED in out, (
        f'Expected {_LOG_SESSION_1_CONNECTED!r} in handoff output'
        f' (preload session never connected).\n--- stdout ---\n{out}'
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_reject_permanent() -> None:
    """Server ``debug_reject=too_old`` → PERMANENT → vegetable mode.

    Two contracts matter here:
      1. Vegetable-mode fires, and the ``serverResponses`` message
         gets logged (message path exercised).
      2. No transport session ever connects — vegetable mode means
         the client permanently stops trying to reach transport.
    """
    with tempfile.TemporaryDirectory() as cfgdir:
        out = _run_until(
            cfgdir,
            env={'BA_DEBUG_SERVERNODEQUERY_REJECT': 'too_old'},
            pattern=_LOG_VEGETABLE_MODE,
            hard_timeout=15.0,
        )
    assert _LOG_REJECTION_PERMANENT in out, (
        f'Expected {_LOG_REJECTION_PERMANENT!r} in output.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_VEGETABLE_MODE in out, (
        f'Expected {_LOG_VEGETABLE_MODE!r} in output.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_SESSION_0_CONNECTED not in out, (
        f'Unexpected {_LOG_SESSION_0_CONNECTED!r} in output'
        f' (permanent rejection must prevent any transport connect).\n'
        f'--- stdout ---\n{out}'
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_reject_permanent_silent() -> None:
    """``permanent_silent`` preset: PERMANENT rejection, no message.

    Confirms the no-message path still triggers vegetable mode and
    still blocks all transport connects.
    """
    with tempfile.TemporaryDirectory() as cfgdir:
        out = _run_until(
            cfgdir,
            env={'BA_DEBUG_SERVERNODEQUERY_REJECT': 'permanent_silent'},
            pattern=_LOG_VEGETABLE_MODE,
            hard_timeout=15.0,
        )
    assert _LOG_REJECTION_PERMANENT in out, (
        f'Expected {_LOG_REJECTION_PERMANENT!r} in output.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_VEGETABLE_MODE in out, (
        f'Expected {_LOG_VEGETABLE_MODE!r} in output.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_SESSION_0_CONNECTED not in out, (
        f'Unexpected {_LOG_SESSION_0_CONNECTED!r} in output'
        f' (permanent rejection must prevent any transport connect).\n'
        f'--- stdout ---\n{out}'
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_reject_transient() -> None:
    """``transient`` preset: retries quickly, never vegetable-modes.

    Transient rejections should behave like comm errors — the
    connectivity cycle treats the attempt as unsuccessful and retries
    on its next tick (~4s), NOT on the normal
    ``FETCH_INTERVAL_SECONDS`` cadence (5 min). Seeing two rejection
    logs within the hard timeout is the evidence — the second proves
    the retry loop fired a fresh fetch, not just that one fetch
    produced multiple log lines.
    """
    with tempfile.TemporaryDirectory() as cfgdir:
        out = _run_until(
            cfgdir,
            env={'BA_DEBUG_SERVERNODEQUERY_REJECT': 'transient'},
            pattern=_LOG_REJECTION_TRANSIENT,
            min_occurrences=2,
            hard_timeout=20.0,
        )
    assert out.count(_LOG_REJECTION_TRANSIENT) >= 2, (
        f'Expected at least 2 {_LOG_REJECTION_TRANSIENT!r} lines'
        f' (retry cadence check); got {out.count(_LOG_REJECTION_TRANSIENT)}.\n'
        f'--- stdout ---\n{out}'
    )
    assert _LOG_VEGETABLE_MODE not in out, (
        f'Unexpected {_LOG_VEGETABLE_MODE!r} in output'
        f' (transient rejection should NOT trigger vegetable mode).\n'
        f'--- stdout ---\n{out}'
    )
