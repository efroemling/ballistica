# Released under the MIT License. See LICENSE for details.
#
"""Testing threadpool functionality."""

import os
import time
import logging
import threading

import pytest

from efro.threadpool import ThreadPoolExecutorEx

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'


def test_no_wait_over_limit_logs_without_blocking(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Over the soft no-wait limit we log (naming callables), never block."""

    # Hold submitted tasks open so the no-wait backlog actually builds.
    release = threading.Event()

    def _blocked_call() -> None:
        release.wait(timeout=10.0)

    # One worker + a tiny limit: the worker is busy on the first task so
    # the rest pile up well past the soft limit.
    threadpool = ThreadPoolExecutorEx(max_workers=1, max_no_wait_count=2)
    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            starttime = time.monotonic()
            for _i in range(10):
                threadpool.submit_no_wait(_blocked_call)
            duration = time.monotonic() - starttime

        # The whole point: submitting never blocks, so this returns fast
        # even though the backlog is way over the limit.
        assert duration < 1.0

        # We logged that we're over the soft limit AND named the
        # offending callable so a spike is diagnosable.
        assert any(
            'no-wait backlog' in r.getMessage()
            and '_blocked_call' in r.getMessage()
            for r in caplog.records
        )
    finally:
        release.set()
        threadpool.shutdown(wait=True)

    # The backlog (and the per-callable counter) drains cleanly.
    assert threadpool.no_wait_count == 0
    assert not threadpool._no_wait_calls  # pylint: disable=protected-access


def test_no_wait_under_limit_does_not_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Staying under the soft limit logs nothing."""

    threadpool = ThreadPoolExecutorEx(max_workers=4, max_no_wait_count=20)
    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            for _i in range(5):
                threadpool.submit_no_wait(lambda: None)
        assert 'no-wait backlog' not in caplog.text
    finally:
        threadpool.shutdown(wait=True)
    assert threadpool.no_wait_count == 0


def test_no_wait_from_pool_worker_no_deadlock() -> None:
    """submit_no_wait from a pool's own worker must not deadlock.

    Regression for the 2026-06 incident: the old blocking backpressure,
    combined with a ``submit_no_wait`` issued from inside a pool worker,
    self-deadlocked — the backlog could only drain via the same workers
    that were now blocked waiting for it to drain.
    """

    threadpool = ThreadPoolExecutorEx(max_workers=1, max_no_wait_count=1)
    done = threading.Event()

    def _worker() -> None:
        # Far over the limit, from the single pool worker. Pre-fix this
        # blocked forever; now it returns and the tasks queue behind us.
        for _i in range(20):
            threadpool.submit_no_wait(lambda: None)
        done.set()

    try:
        threadpool.submit(_worker)
        assert done.wait(
            timeout=10.0
        ), 'submit_no_wait deadlocked when called from a pool worker'
    finally:
        threadpool.shutdown(wait=True)
    assert threadpool.no_wait_count == 0


@pytest.mark.skipif(FAST_MODE, reason='fast mode (uses real sleeps)')
def test_submit_warns_on_long_run(caplog: pytest.LogCaptureFixture) -> None:
    """A task that runs too long logs a warning naming the callable."""

    def _slow_task() -> None:
        time.sleep(0.3)

    # Low run threshold so a short sleep trips it quickly.
    threadpool = ThreadPoolExecutorEx(
        max_workers=2, run_duration_warn_seconds=0.1
    )
    try:
        with caplog.at_level(logging.WARNING, logger='efro.threadpool'):
            threadpool.submit(_slow_task).result()
        assert any(
            ' ran ' in r.getMessage() and '_slow_task' in r.getMessage()
            for r in caplog.records
        )
    finally:
        threadpool.shutdown(wait=True)


@pytest.mark.skipif(FAST_MODE, reason='fast mode (uses real sleeps)')
def test_submit_warns_on_long_queue_wait(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A task that waits too long in the queue logs a warning naming it."""

    release = threading.Event()

    def _waiter() -> None:
        pass

    # Single worker + low wait threshold: occupy the worker, then submit
    # a task that must sit in the queue past the threshold before running.
    threadpool = ThreadPoolExecutorEx(
        max_workers=1, queue_wait_warn_seconds=0.1
    )
    try:
        with caplog.at_level(logging.WARNING, logger='efro.threadpool'):
            # Occupy the single worker until we release it.
            threadpool.submit(lambda: release.wait(timeout=5.0))
            queued = threadpool.submit(_waiter)
            time.sleep(0.3)  # let _waiter sit in the queue past 0.1s
            release.set()  # free the worker; _waiter starts (late)
            queued.result()
        assert any(
            'waited' in r.getMessage() and '_waiter' in r.getMessage()
            for r in caplog.records
        )
    finally:
        release.set()
        threadpool.shutdown(wait=True)
