# Released under the MIT License. See LICENSE for details.
#
"""Tests for shutdown-hang diagnostics.

Two complementary mechanisms produce useful info when shutdown
misbehaves:

1. **Faulthandler watchdog.** A ``faulthandler.dump_traceback_later``
   timer is armed by :meth:`babase.App.shutdown_fault_handler_arm`
   (called from C++ alongside ``Logic::OnAppShutdown``'s suicide-timer
   arm). If shutdown hasn't completed by the 15-second hard deadline,
   every thread's traceback is dumped to fd 2 and the C++ suicide
   timer then kills the process a couple seconds later.

2. **Per-task timeout + stack snapshot.** Each coroutine in
   :attr:`babase.App._shutdown_tasks` is awaited with a
   :attr:`SHUTDOWN_TASK_TIMEOUT_SECONDS` budget; if it overruns,
   :meth:`babase.App._run_shutdown_task` snapshots
   ``task.print_stack()`` and emits an ERROR log naming the hung
   coroutine and its suspended frames *before* cancelling the task.

Three tests cover the observed real-world failure modes on BASN:

* ``test_shutdown_watchdog_pre_interpreter_shutdown_hang`` — something
  inside :meth:`babase.App._pre_interpreter_shutdown` blocks (e.g. a
  threadpool worker ignoring engine-done, so ``threadpool.shutdown()``
  can't return). The faulthandler watchdog catches it.
* ``test_shutdown_watchdog_orchestrator_hang`` — a shutdown task
  blocks the asyncio event loop (synchronous ``time.sleep``), so even
  the per-task 12s ``asyncio.wait`` can't fire before the 15s
  deadline. The faulthandler watchdog catches it.
* ``test_shutdown_task_timeout_logs_stack`` — a shutdown task is
  merely slow (``await asyncio.sleep(3600)``) rather than loop-
  blocking, so the per-task timeout fires cleanly and the error log
  is expected to include a capture of the coroutine's suspended
  stack. Shutdown then completes without the faulthandler or C++
  suicide firing.

Each test launches a siloed headless server via ``test_game_run`` with
an ``--exec`` snippet that deliberately wedges the relevant phase and
then asserts on markers in the combined output.
"""

from __future__ import annotations

import os
import subprocess

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

# Project root (two levels up from this file's dir).
_PROJROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# test_game_run hard-timeout. Needs to be comfortably past 3s boot +
# 3s arm-delay + 17s (15s dump + 2s suicide runway).
_TEST_GAME_RUN_TIMEOUT_SECONDS = 30

# Subprocess timeout wrapping test_game_run. Larger than
# _TEST_GAME_RUN_TIMEOUT_SECONDS so a binary-build on the first run
# doesn't falsely trip the outer timeout.
_SUBPROCESS_TIMEOUT_SECONDS = 120


# --- Exec snippets ------------------------------------------------------

# Submits a long-running threadpool worker then triggers quit. The
# worker will still be sleeping when _pre_interpreter_shutdown calls
# self.threadpool.shutdown(), blocking the main thread there until the
# 15s dump fires.
_PRE_INTERPRETER_HANG_EXEC = '''
import _babase
import time

def _trigger() -> None:
    _babase.app.threadpool.submit(lambda: time.sleep(60))
    _babase.apptimer(0.2, _babase.quit)

_babase.apptimer(3.0, _trigger)
'''

# Registers a shutdown task that does a synchronous ``time.sleep``.
# Because it blocks the asyncio event loop, the per-task 12s
# ``asyncio.wait`` timeout can't fire — the orchestrator wedges until
# the 15s dump fires and the C++ suicide finishes us off.
_ORCHESTRATOR_HANG_EXEC = '''
import _babase
import time

async def _hang() -> None:
    time.sleep(60)

def _trigger() -> None:
    _babase.app.add_shutdown_task(_hang())
    _babase.apptimer(0.2, _babase.quit)

_babase.apptimer(3.0, _trigger)
'''

# Registers a shutdown task that awaits ``asyncio.sleep`` (cancellable)
# so the per-task 12s timeout fires cleanly — _run_shutdown_task is
# expected to snapshot the hung coroutine's stack via
# ``task.print_stack()`` and include it in the ERROR log before
# cancelling. Shutdown then completes normally without the 15s
# faulthandler watchdog or the C++ suicide firing.
_TASK_TIMEOUT_STACK_EXEC = '''
import _babase
import asyncio

async def _slow_shutdown_task() -> None:
    await asyncio.sleep(3600)

def _trigger() -> None:
    _babase.app.add_shutdown_task(_slow_shutdown_task())
    _babase.apptimer(0.2, _babase.quit)

_babase.apptimer(3.0, _trigger)
'''


# --- Helpers ------------------------------------------------------------


def _run_shutdown_scenario(instance: str, exec_code: str) -> str:
    """Run a siloed headless server that wedges shutdown; return output."""
    # Prime the binary cache; later test_game_run invocations are noop
    # on this step.
    apprun.acquire_binary(purpose=f'shutdown-watchdog {instance}')

    # Skip the UDP listener: these tests don't exercise inbound
    # networking, and binding the default game port fatals when
    # multiple smoke jobs run in parallel on the same CI host.
    env = {**os.environ, 'BA_NO_UDP_LISTENER': '1'}

    proc = subprocess.run(
        [
            'tools/pcommand',
            'test_game_run',
            '--instance',
            instance,
            '--timeout',
            str(_TEST_GAME_RUN_TIMEOUT_SECONDS),
            '--exec',
            exec_code,
        ],
        cwd=_PROJROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )
    return proc.stdout.decode(errors='replace')


def _assert_in(out: str, needle: str, desc: str) -> None:
    """Assert that ``needle`` appears in ``out`` with a helpful failure."""
    if needle in out:
        return
    raise AssertionError(
        f'Missing expected marker ({desc}): {needle!r}\n'
        f'--- output (tail) ---\n{out[-4000:]}'
    )


# --- Tests --------------------------------------------------------------


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_shutdown_watchdog_pre_interpreter_shutdown_hang() -> None:
    """Dump fires when threadpool.shutdown wedges _pre_interpreter_shutdown."""
    out = _run_shutdown_scenario(
        instance='shutdown_wd_pis', exec_code=_PRE_INTERPRETER_HANG_EXEC
    )

    _assert_in(out, 'Shutting down...', 'shutdown initiated')
    _assert_in(out, 'app exiting (main thread)', 'main thread reached exit log')
    _assert_in(
        out,
        'Timeout (0:00:15)!',
        'faulthandler dump fired at the 15s deadline',
    )
    # Presence of at least one thread dump header.
    assert 'Thread 0x' in out, (
        f'Expected at least one thread dump header.\n'
        f'--- output (tail) ---\n{out[-4000:]}'
    )
    # The stuck worker's lambda (sleeping) should appear in the dump.
    _assert_in(out, 'in <lambda>', 'stuck threadpool worker lambda in the dump')
    # Main thread wedge site.
    _assert_in(
        out,
        'concurrent/futures/thread.py',
        'main thread wedged in concurrent.futures shutdown',
    )
    # C++ suicide still fires (we diagnose, we don't prevent).
    _assert_in(
        out,
        'FATAL ERROR: Timed out waiting for shutdown.',
        'C++ suicide timer fired as expected',
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_shutdown_watchdog_orchestrator_hang() -> None:
    """Dump fires when a shutdown task blocks the asyncio event loop."""
    out = _run_shutdown_scenario(
        instance='shutdown_wd_orch', exec_code=_ORCHESTRATOR_HANG_EXEC
    )

    _assert_in(out, 'Shutting down...', 'shutdown initiated')
    _assert_in(
        out,
        'Timeout (0:00:15)!',
        'faulthandler dump fired at the 15s deadline',
    )
    assert 'Thread 0x' in out, (
        f'Expected at least one thread dump header.\n'
        f'--- output (tail) ---\n{out[-4000:]}'
    )
    # The stuck coroutine should be visible in the main thread's
    # Python stack.
    _assert_in(
        out,
        'in _hang',
        "orchestrator's main thread still running the _hang coroutine",
    )
    _assert_in(
        out,
        'asyncio/base_events.py',
        'main thread in the asyncio event loop',
    )
    _assert_in(
        out,
        'FATAL ERROR: Timed out waiting for shutdown.',
        'C++ suicide timer fired as expected',
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_shutdown_task_timeout_logs_stack() -> None:
    """Per-task timeout log snapshots the hung coroutine's stack."""
    out = _run_shutdown_scenario(
        instance='shutdown_tt_stk', exec_code=_TASK_TIMEOUT_STACK_EXEC
    )

    # The standard per-task-timeout error must still fire, naming the
    # hung coroutine.
    _assert_in(
        out,
        'Timed out waiting for shutdown task',
        'per-task timeout error log fired',
    )
    _assert_in(
        out,
        '_slow_shutdown_task',
        'error log names the hung coroutine',
    )
    # The added stack-snapshot section must be present.
    _assert_in(
        out,
        'Current task stack:',
        'error log includes the stack snapshot section',
    )
    # Task.print_stack()'s normal preamble on a live (not-yet-cancelled)
    # task — its absence would indicate we dropped back to wait_for or
    # otherwise snapshot too late.
    _assert_in(
        out,
        'Stack for <Task pending',
        'stack snapshot captured before task was cancelled',
    )
    # And the snapshot should actually contain a frame for the
    # suspended coroutine body.
    _assert_in(
        out,
        'in _slow_shutdown_task',
        'snapshot frame for the hung coroutine body',
    )

    # This scenario is *not* supposed to trip the faulthandler or the
    # C++ suicide — shutdown completes normally after the cancel.
    assert 'Timeout (0:00:15)!' not in out, (
        'Faulthandler should not have fired on a cooperatively-'
        'cancellable shutdown task.\n--- output (tail) ---\n' + out[-4000:]
    )
    assert 'FATAL ERROR: Timed out waiting for shutdown.' not in out, (
        'C++ suicide timer should not have fired when shutdown '
        'completed normally after cancel.\n--- output (tail) ---\n'
        + out[-4000:]
    )
