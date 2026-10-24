# Released under the MIT License. See LICENSE for details.
#
"""Tests that the app shuts down cleanly once shutdown completes.

When the app reaches :attr:`babase.AppState.SHUTDOWN_COMPLETE`, the
logic thread stops its event loop and the main thread waits for that
before finalizing Python. Before this was the case, app timers kept
firing into Python during finalization, which surfaced on servers as
``Fatal Python error: _enter_buffered_busy`` aborts.

* ``test_no_app_timers_after_shutdown_complete`` - a repeating 1ms app
  timer reports any firing after shutdown completes; there must be
  none, and the process must exit 0.
* ``test_wedged_logic_thread_exits_without_finalizing`` - with the
  logic thread deliberately stalled (``BA_CRASH_TEST`` hook), the main
  thread gives up after its wait, reports an unclean shutdown, and
  exits 1 instead of hanging or crashing in finalization.
"""

import os
import tempfile

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

_RUN_TIMEOUT_SECONDS = 40

# Reports timer firings via raw fd writes, which don't depend on
# Python's stderr machinery (which is going away at that point).
_LATE_TIMER_EXEC = '''
import os
import babase

def _tick() -> None:
    if babase.app.state is babase.AppState.SHUTDOWN_COMPLETE:
        os.write(2, b'LATE-TIMER-FIRED\\n')

babase.app.late_timer_probe = babase.AppTimer(0.001, _tick, repeat=True)

def _quit() -> None:
    os.write(2, b'LATE-TIMER-PROBE-QUITTING\\n')
    babase.quit()

babase.apptimer(3.0, _quit)
'''

_QUIT_EXEC = '''
import os
import babase

def _quit() -> None:
    os.write(2, b'STALL-PROBE-QUITTING\\n')
    babase.quit()

babase.apptimer(3.0, _quit)
'''


def _run(
    instance: str, exec_code: str, env: dict[str, str] | None = None
) -> tuple[int | None, str]:
    with tempfile.TemporaryDirectory(
        prefix=f'shutdown_clean_{instance}_'
    ) as tmpdir:
        config_dir = os.path.join(tmpdir, 'ba_root')
        os.makedirs(config_dir)
        proc = apprun.run_headless_capture(
            purpose=f'shutdown-clean {instance}',
            config_dir=config_dir,
            exec_code=exec_code,
            env=env,
            timeout=_RUN_TIMEOUT_SECONDS,
        )
    return proc.returncode, proc.stdout.decode(errors='replace')


def _fail(desc: str, out: str) -> str:
    return f'{desc}\n--- output (tail) ---\n{out[-4000:]}'


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_no_app_timers_after_shutdown_complete() -> None:
    """No app timer fires once the app reaches SHUTDOWN_COMPLETE."""
    code, out = _run(
        'late_timer',
        _LATE_TIMER_EXEC,
        # For the leftover-threads line.
        env={'BA_LOG_LEVELS': 'ba.lifecycle=INFO'},
    )
    assert 'LATE-TIMER-PROBE-QUITTING' in out, _fail('Probe never ran.', out)
    assert 'LATE-TIMER-FIRED' not in out, _fail(
        'App timer fired after SHUTDOWN_COMPLETE.', out
    )
    assert 'did not stop after shutdown completed' not in out, _fail(
        'Main thread gave up waiting on a thread.', out
    )

    # Threads we stop and join at shutdown must not show up as still
    # running at Python finalization.
    for line in out.splitlines():
        if 'Threads still running at Python finalization:' in line:
            leftover = line.split(':', 3)[-1]
            for name in ('logic', 'assets', 'audio', 'networkwrite'):
                assert name not in leftover, _fail(
                    f'Thread {name!r} still running at finalization.', out
                )
    assert code == 0, _fail(f'Unexpected exit code {code}.', out)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_wedged_logic_thread_exits_without_finalizing() -> None:
    """A stalled logic thread leads to a clean exit, not a hang/crash."""
    code, out = _run(
        'logic_stall',
        _QUIT_EXEC,
        env={
            'BA_CRASH_TEST': 'shutdown_logic_stall',
            # Keep its unclean-shutdown report off the real servers;
            # delivery is covered in test_fatal_report_delivery.py.
            'BA_FATAL_REPORT_URL': 'http://127.0.0.1:9',
        },
    )
    assert 'STALL-PROBE-QUITTING' in out, _fail('Probe never ran.', out)
    assert (
        'UNCLEAN-SHUTDOWN: Thread(s) did not stop after shutdown'
        ' completed: logic;' in out
    ), _fail('Main thread did not take its give-up path.', out)
    # (No 'Still waiting...' warning to check for here: it goes through
    # Python logging, which the stalled thread blocks by holding the
    # GIL.) We must give up before the shutdown watchdog's traceback
    # dump or its fatal error.
    assert 'Timeout (0:00:' not in out, _fail(
        'Watchdog traceback dump fired before we gave up.', out
    )
    assert 'FATAL ERROR' not in out, _fail('Hit a fatal error.', out)
    assert code == 1, _fail(f'Unexpected exit code {code}.', out)
