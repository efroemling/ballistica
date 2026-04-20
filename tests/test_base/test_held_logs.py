# Released under the MIT License. See LICENSE for details.
#
"""Tests for the early-log drain that runs on fatal errors.

When C++ code logs something before the Python LogHandler is wired up
(i.e. before baenv.configure() has returned and
CorePython::OnLogHandlerReady has been called), those log calls are
buffered into ``CorePython::early_logs_`` and replayed through Python
logging later. If a fatal error fires *before* that replay happens,
``FatalErrorHandling::ReportFatalError`` calls
``CorePython::DrainEarlyLogsToStderr`` so the buffered messages aren't
silently lost. This test exercises that drain path.

Uses the ``BA_CRASH_TEST=held_logs`` hook wired into ``MonolithicMain``
in ``src/ballistica/shared/ballistica.cc``, which logs three known
lines and then calls ``FatalError``. We launch the binary with that
env var, capture its output, and assert that the drain emitted the
known lines with the expected prefix.
"""

from __future__ import annotations

import os
import subprocess

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

_HELD_LOG_PREFIX = '[held-log]'
_EXPECTED_LINES = [
    'held-log-test: line 1',
    'held-log-test: line 2',
    'held-log-test: line 3',
]


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_fatal_error_drains_held_logs() -> None:
    """Fatal-error drain emits buffered early logs before aborting."""
    binpath = os.path.abspath(apprun.acquire_binary(purpose='held-log test'))
    bindir = os.path.dirname(binpath)

    env = dict(os.environ)
    env['BA_CRASH_TEST'] = 'held_logs'

    proc = subprocess.run(
        [binpath],
        cwd=bindir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30.0,
        check=False,
    )
    out = proc.stdout.decode(errors='replace')

    assert proc.returncode != 0, (
        f'Expected non-zero exit from BA_CRASH_TEST=held_logs, '
        f'got {proc.returncode}.\n--- output ---\n{out}'
    )

    # Each of our test lines should appear prefixed by [held-log],
    # confirming DrainEarlyLogsToStderr ran and preserved content.
    for line in _EXPECTED_LINES:
        needle = f'{_HELD_LOG_PREFIX} {line}'
        assert (
            needle in out
        ), f'Expected {needle!r} in drain output.\n--- output ---\n{out}'

    # Verify order (buffer should replay in log order, not reversed).
    positions = [
        out.index(f'{_HELD_LOG_PREFIX} {line}') for line in _EXPECTED_LINES
    ]
    assert positions == sorted(positions), (
        f'Held logs emitted out of order: positions={positions}.\n'
        f'--- output ---\n{out}'
    )
