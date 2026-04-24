# Released under the MIT License. See LICENSE for details.
#
"""Tests for the ``Insecure Connections`` tri-state config.

Expected selection matrix:

=======  ==========  =========================
mode     directive?  expected scheme
=======  ==========  =========================
always   no          ``ws://`` (config forces)
always   yes         ``ws://`` (config still forces)
auto     no          ``wss://`` (default secure)
auto     yes         ``ws://`` (directive applies)
never    no          ``wss://`` (config forces)
never    yes         ``wss://`` (config overrides directive)
=======  ==========  =========================

Every cell is covered by a live end-to-end run. The test pre-seeds
``Insecure Connections`` into a fresh silo's ``config.json``, launches
the headless client with the relevant loggers turned up, and greps
the combined stdout/stderr for the first ``Trying WS connection to
ws[s]://`` line — that is the scheme v2transport actually picked via
``ConnectivityManager.effective_use_insecure()``.

The directive-present cells additionally set
``BA_DEBUG_SERVERNODEQUERY_INSECURE_DIRECTIVE=force``. That env var
makes the client attach ``&test_insecure_directive=force`` to its
``/servernodequery`` URL (the same mechanism ``test_insecure_directive.py``
uses from the pytest process). The master server responds with a
real signed :class:`bacommon.net.InsecureDirective` over whatever
scheme the client's mode naturally picked — so we never need to
force-downgrade the bootstrap ourselves, and the ``never`` test
genuinely observes "client was told to go insecure and went secure
anyway." The directive-present rows additionally grep for the
``insecure-directive verified: use_insecure=True`` log line to prove
the directive actually reached the client.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

# Project root (two levels up from this test file).
_PROJROOT = Path(__file__).resolve().parents[2]

# test_game_run hard-timeout; comfortably past boot + initial
# transport connect (~0.5s).
_TEST_GAME_RUN_TIMEOUT_SECONDS = 10

# Outer subprocess timeout — needs headroom for binary-build on
# a fresh checkout.
_SUBPROCESS_TIMEOUT_SECONDS = 180

# Give the transport enough time to complete its first connect
# attempt and log the scheme; the directive-present rows also need
# time for the /servernodequery response to arrive and be verified.
_EXEC_QUICK_QUIT = '''
import _babase
_babase.apptimer(5.0, _babase.quit)
'''

_WS_ATTEMPT_RE = re.compile(r'Trying WS connection to (wss?)://', re.MULTILINE)
_DIRECTIVE_VERIFIED_RE = re.compile(
    r'insecure-directive verified: use_insecure=True'
)


# --- Live-test helpers --------------------------------------------------


def _silo_dir(instance: str) -> Path:
    """Path to the per-instance silo under build/test_run/."""
    return _PROJROOT / 'build' / 'test_run' / instance


def _run_vanilla_with_config(
    instance: str, mode: str, *, with_directive: bool
) -> str:
    """Run a fresh headless client with a pre-seeded config mode.

    Removes the per-instance silo so each invocation starts clean,
    writes just ``config.json`` with ``Insecure Connections`` set to
    ``mode``, invokes ``test_game_run`` with a quick-quit ``--exec``
    and ``--log ba.v2transport=INFO,ba.connectivity=INFO`` (both loggers
    are below the default threshold; we need v2transport to see the
    ``Trying WS connection`` line and connectivity to see the
    directive-verification line). When ``with_directive`` is set, we
    also export ``BA_DEBUG_SERVERNODEQUERY_INSECURE_DIRECTIVE=force``
    so the client's ``/servernodequery`` fetch asks the master server
    to attach a signed directive on the response. Returns combined
    stdout/stderr.
    """
    silo = _silo_dir(instance)
    shutil.rmtree(silo, ignore_errors=True)
    ba_root = silo / 'ba_root'
    ba_root.mkdir(parents=True, exist_ok=True)
    (ba_root / 'config.json').write_text(
        json.dumps({'Insecure Connections': mode}, indent=2)
    )

    apprun.acquire_binary(purpose=f'insecure-mode {instance}')

    env = os.environ.copy()
    if with_directive:
        env['BA_DEBUG_SERVERNODEQUERY_INSECURE_DIRECTIVE'] = 'force'

    proc = subprocess.run(
        [
            'tools/pcommand',
            'test_game_run',
            '--instance',
            instance,
            '--timeout',
            str(_TEST_GAME_RUN_TIMEOUT_SECONDS),
            '--log',
            'ba.v2transport=INFO,ba.connectivity=INFO',
            '--exec',
            _EXEC_QUICK_QUIT,
        ],
        cwd=_PROJROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        env=env,
        check=False,
    )
    return proc.stdout.decode(errors='replace')


def _first_ws_scheme(output: str) -> str:
    """Extract the scheme of the first WS connect attempt."""
    matches: list[str] = _WS_ATTEMPT_RE.findall(output)
    assert matches, (
        'No "Trying WS connection to ws[s]://" log line found in'
        f' output.\n--- output (tail) ---\n{output[-4000:]}'
    )
    return matches[0]


# --- Live tests ---------------------------------------------------------


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
@pytest.mark.parametrize(
    'mode,with_directive,expected_scheme',
    [
        ('always', False, 'ws'),
        ('always', True, 'ws'),
        ('auto', False, 'wss'),
        ('auto', True, 'ws'),
        ('never', False, 'wss'),
        ('never', True, 'wss'),
    ],
)
def test_insecure_mode_live(
    mode: str, with_directive: bool, expected_scheme: str
) -> None:
    """End-to-end pick of WS scheme in a fresh client run."""
    suffix = 'dir' if with_directive else 'nodir'
    instance = f'insecure-{mode}-{suffix}'
    output = _run_vanilla_with_config(
        instance, mode, with_directive=with_directive
    )
    actual_scheme = _first_ws_scheme(output)
    assert actual_scheme == expected_scheme, (
        f'mode={mode!r} with_directive={with_directive!r}: expected'
        f' {expected_scheme!r}, got {actual_scheme!r}.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )

    # For directive-present cells, prove the directive actually
    # reached the client. Otherwise a silent server-side regression
    # (e.g. no signing key configured, or the force-arg quietly
    # dropped) would let these tests pass while covering nothing.
    if with_directive:
        assert _DIRECTIVE_VERIFIED_RE.search(output), (
            f'mode={mode!r}: BA_DEBUG_SERVERNODEQUERY_INSECURE_DIRECTIVE'
            ' was set but no "insecure-directive verified: use_insecure=True"'
            f' marker appeared.\n--- output (tail) ---\n{output[-4000:]}'
        )
