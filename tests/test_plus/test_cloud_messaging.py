# Released under the MIT License. See LICENSE for details.
#
"""Live end-to-end tests for the client's cloud message-send forms.

Pre-work for the cloud-message-futures refactor (see
``docs/initiatives/cloud-message-futures.md``): these tests pin down
the observable behavior of the public send APIs so the messaging
internals can be reworked with confidence.

Covered per run (a single headless boot against the live master
server, driven by an ``--exec`` snippet that logs grep-friendly
markers):

- ``send_message_cb`` round-trips a ``PingMessage`` and delivers the
  response in the logic thread.
- ``send_message_async`` round-trips from a logic-thread asyncio task.
- ``send_message`` (blocking) round-trips from a background thread.
- A small burst of cb sends all resolve (no drops).
- The legacy V1 path (``master_server_v1_get('bsAccessCheck')``)
  round-trips — a deletion guard for the thread-per-request wrappers.
- Pre-connectivity sends deliver ``CommunicationError`` as *values*
  through the same channels (skipped gracefully in the unlikely case
  connectivity wins the race).

A second test quits the app with a message still in flight and
asserts a clean shutdown: no plus-runtime straggler tasks and no
v2transport in-flight-message tripwire.

Both tests also assert the absence of ``AssertionError`` output so
the transport's cb-send ordering assert (debug builds) gets teeth
here, and the first asserts the presence of the ``msgio:``
submit/resolve trace lines so the lifecycle logging can't silently
rot.
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

# Project root (two levels up from this test file).
_PROJROOT = Path(__file__).resolve().parents[2]

# Hard timeout per run. Happy path is a few seconds on a warm cache;
# this is the safety net for slow live-server days.
_TIMEOUT_SECONDS = 60

# All-forms exec snippet. Logs 'cloudmsgtest-<name>-ok' markers (or
# '...-BAD...' on unexpected results) and quits once everything has
# resolved. print() is buffered when stdout is not a terminal, so all
# output goes through logging.
_EXEC_ALL_FORMS = """
import logging
import threading

import babase
import bacommon.cloud
from efro.error import CommunicationError

_pending = {'cb', 'async', 'sync', 'burst', 'v1'}
_burst_state = [0, True]  # (count, all-ok)


def _done(name):
    assert babase.in_logic_thread()
    _pending.discard(name)
    if not _pending:
        logging.warning('cloudmsgtest-all-done')
        babase.quit()


def _fail_timeout():
    logging.warning('cloudmsgtest-timeout-BAD pending=%s', sorted(_pending))
    babase.quit()


def _phase1():
    plus = babase.app.plus
    if plus is None:
        babase.apptimer(0.05, _phase1)
        return
    if plus.cloud.is_connected():
        # Connectivity won the race; not-connected paths untestable
        # this run.
        logging.warning('cloudmsgtest-pre-skipped')
        _phase2_wait()
        return

    def _precb(resp):
        if isinstance(resp, CommunicationError) and babase.in_logic_thread():
            logging.warning('cloudmsgtest-precb-ok')
        else:
            logging.warning(
                'cloudmsgtest-precb-BAD resp=%s logicthread=%s',
                type(resp).__name__,
                babase.in_logic_thread(),
            )

    plus.cloud.send_message_cb(bacommon.cloud.PingMessage(), _precb)

    def _presync():
        try:
            plus.cloud.send_message(bacommon.cloud.PingMessage())
            logging.warning('cloudmsgtest-presync-BAD got-response')
        except CommunicationError:
            logging.warning('cloudmsgtest-presync-ok')
        except Exception as exc:
            logging.warning('cloudmsgtest-presync-BAD %s', type(exc).__name__)

    threading.Thread(target=_presync).start()
    _phase2_wait()


def _phase2_wait():
    plus = babase.app.plus
    if plus is None or not plus.cloud.is_connected():
        babase.apptimer(0.25, _phase2_wait)
        return
    _phase2()


def _phase2():
    plus = babase.app.plus
    assert plus is not None

    # --- cb form.
    def _cbresp(resp):
        if isinstance(
            resp, bacommon.cloud.PingResponse
        ) and babase.in_logic_thread():
            logging.warning('cloudmsgtest-cb-ok')
        else:
            logging.warning('cloudmsgtest-cb-BAD resp=%s', type(resp).__name__)
        _done('cb')

    plus.cloud.send_message_cb(bacommon.cloud.PingMessage(), _cbresp)

    # --- async form.
    async def _asyncrun():
        try:
            resp = await plus.cloud.send_message_async(
                bacommon.cloud.PingMessage()
            )
            if isinstance(
                resp, bacommon.cloud.PingResponse
            ) and babase.in_logic_thread():
                logging.warning('cloudmsgtest-async-ok')
            else:
                logging.warning(
                    'cloudmsgtest-async-BAD resp=%s', type(resp).__name__
                )
        except Exception as exc:
            logging.warning('cloudmsgtest-async-BAD %s', type(exc).__name__)
        _done('async')

    babase.app.create_async_task(_asyncrun(), name='cloudmsgtest async')

    # --- blocking form (bg thread).
    def _syncrun():
        try:
            resp = plus.cloud.send_message(bacommon.cloud.PingMessage())
            if isinstance(
                resp, bacommon.cloud.PingResponse
            ) and not babase.in_logic_thread():
                logging.warning('cloudmsgtest-sync-ok')
            else:
                logging.warning(
                    'cloudmsgtest-sync-BAD resp=%s', type(resp).__name__
                )
        except Exception as exc:
            logging.warning('cloudmsgtest-sync-BAD %s', type(exc).__name__)
        babase.pushcall(lambda: _done('sync'), from_other_thread=True)

    threading.Thread(target=_syncrun).start()

    # --- burst of cb sends (no-drop check).
    def _burstresp(resp):
        _burst_state[0] += 1
        if not isinstance(resp, bacommon.cloud.PingResponse):
            _burst_state[1] = False
        if _burst_state[0] == 5:
            if _burst_state[1]:
                logging.warning('cloudmsgtest-burst-ok')
            else:
                logging.warning('cloudmsgtest-burst-BAD')
            _done('burst')

    for _ in range(5):
        plus.cloud.send_message_cb(bacommon.cloud.PingMessage(), _burstresp)

    # --- legacy V1 path (thread-per-request wrapper deletion guard).
    classic = babase.app.classic
    assert classic is not None

    def _v1resp(data):
        if data is not None and babase.in_logic_thread():
            logging.warning('cloudmsgtest-v1-ok')
        else:
            logging.warning('cloudmsgtest-v1-BAD data=%s', type(data).__name__)
        _done('v1')

    classic.master_server_v1_get(
        'bsAccessCheck', {'b': babase.app.env.engine_build_number}, _v1resp
    )


babase.apptimer(40.0, _fail_timeout)
_phase1()
"""

# Quit-mid-send exec snippet: fire a cb send and quit in the same
# breath; the shutdown checks in the test body do the real asserting.
_EXEC_QUIT_MID_SEND = """
import logging

import babase
import bacommon.cloud


def _quitwait():
    plus = babase.app.plus
    if plus is None or not plus.cloud.is_connected():
        babase.apptimer(0.25, _quitwait)
        return

    def _resp(resp):
        logging.warning('cloudmsgtest-midquit-resp %s', type(resp).__name__)

    plus.cloud.send_message_cb(bacommon.cloud.PingMessage(), _resp)
    logging.warning('cloudmsgtest-midquit-sent')
    babase.quit()


_quitwait()
"""

# Failure signatures that must never appear in any run's output.
_FORBIDDEN_OUTPUT = [
    # The v2transport cb-send ordering assert (or any other assert).
    'AssertionError',
    # V2Transport.on_runtime_shutdown in-flight tripwire.
    'still in flight after task drain',
    # PlusRuntime straggler-task check.
    'still running after tenant shutdown',
    # Connectivity's shutdown backstop; hung pings must not stall the
    # quit long enough for this to fire (the ping-batch drain races
    # against the shutdown event).
    'did not exit in 5s',
]


def _run_exec(instance: str, exec_code: str) -> tuple[str, int | None]:
    """Run a fresh headless client with the given exec snippet.

    Returns (combined-output, returncode).
    """
    silo = _PROJROOT / 'build' / 'test_run' / instance
    shutil.rmtree(silo, ignore_errors=True)
    ba_root = silo / 'ba_root'
    ba_root.mkdir(parents=True, exist_ok=True)
    (ba_root / 'config.json').write_text(json.dumps({}))

    proc = apprun.run_headless_capture(
        purpose=f'cloud-messaging {instance}',
        config_dir=str(ba_root),
        exec_code=exec_code,
        env={'BA_LOG_LEVELS': 'ba.v2transport=DEBUG'},
        timeout=_TIMEOUT_SECONDS,
    )
    return proc.stdout.decode(errors='replace'), proc.returncode


def _assert_no_forbidden(output: str) -> None:
    for needle in _FORBIDDEN_OUTPUT:
        assert needle not in output, (
            f'Forbidden output {needle!r} found in run output.\n'
            f'--- output (tail) ---\n{output[-4000:]}'
        )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_cloud_message_forms_live() -> None:
    """All public send forms round-trip against the live master."""
    output, returncode = _run_exec('cloudmsg-forms', _EXEC_ALL_FORMS)

    tail = f'--- output (tail) ---\n{output[-6000:]}'

    # Everything resolved and the app quit itself.
    assert 'cloudmsgtest-all-done' in output, f'Run never finished.\n{tail}'
    assert returncode == 0, f'Expected clean exit; got {returncode}.\n{tail}'

    # Happy-path markers, one per form.
    for marker in (
        'cloudmsgtest-cb-ok',
        'cloudmsgtest-async-ok',
        'cloudmsgtest-sync-ok',
        'cloudmsgtest-burst-ok',
        'cloudmsgtest-v1-ok',
    ):
        assert marker in output, f'Missing marker {marker!r}.\n{tail}'

    # Pre-connectivity error paths (or the explicit race-skip marker).
    if 'cloudmsgtest-pre-skipped' not in output:
        assert 'cloudmsgtest-precb-ok' in output, tail
        assert 'cloudmsgtest-presync-ok' in output, tail

    # No unexpected-result markers anywhere.
    bad = [
        line
        for line in output.splitlines()
        if 'cloudmsgtest' in line and 'BAD' in line
    ]
    assert not bad, f'Unexpected-result markers: {bad}\n{tail}'

    # The msgio lifecycle tracing must be alive for each form.
    for needle in (
        'msgio: submit PingMessage form=cb',
        'msgio: submit PingMessage form=sync',
        'msgio: submit PingMessage form=async',
        'msgio: resolve PingMessage form=cb outcome=response',
        'msgio: resolve PingMessage form=sync outcome=response',
        'msgio: resolve PingMessage form=async outcome=response',
    ):
        assert needle in output, f'Missing msgio trace {needle!r}.\n{tail}'

    _assert_no_forbidden(output)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_cloud_message_quit_mid_send() -> None:
    """Quitting with a message in flight shuts down cleanly."""
    output, returncode = _run_exec('cloudmsg-midquit', _EXEC_QUIT_MID_SEND)

    tail = f'--- output (tail) ---\n{output[-6000:]}'

    assert (
        'cloudmsgtest-midquit-sent' in output
    ), f'Run never got to the mid-quit send.\n{tail}'
    assert returncode == 0, f'Expected clean exit; got {returncode}.\n{tail}'

    _assert_no_forbidden(output)
