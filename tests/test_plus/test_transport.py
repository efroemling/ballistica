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


def _run_until(
    config_dir: str,
    env: Mapping[str, str],
    pattern: str,
    hard_timeout: float = 10.0,
) -> str:
    """Stream binary stdout until ``pattern`` appears, then terminate.

    Returns all captured output. If ``pattern`` never appears before
    ``hard_timeout``, returns whatever was captured so the caller can
    produce a useful failure message.
    """
    binpath = os.path.abspath(apprun.acquire_binary(purpose='transport test'))
    bindir = os.path.dirname(binpath)

    env_final = dict(os.environ)
    env_final.update(env)
    env_final.setdefault(
        'BA_LOG_LEVELS', 'ba.v2transport=DEBUG,ba.connectivity=DEBUG'
    )
    # Transport tests only connect outbound to basn; binding UDP to
    # INADDR_ANY isn't needed and gets denied under network sandboxes.
    env_final.setdefault('BA_BIND_LOOPBACK_ONLY', '1')

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
        try:
            for raw in iter(proc.stdout.readline, b''):
                line = raw.decode(errors='replace')
                captured.append(line)
                if pattern in line:
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
