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


def test_self_submit_runs_inline_and_logs_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Waiting on a pool from one of its own workers must not deadlock.

    Regression for the 2026-09-11 DEV bamaster freeze: cloud-file ensures
    ran on the shared pool and each waited on hash jobs submitted to that
    same pool; with every worker holding such a task, nothing could run.
    With one worker, the unguarded version of this test hangs forever.
    """

    threadpool = ThreadPoolExecutorEx(max_workers=1)

    def _inner() -> int:
        return threading.get_ident()

    def _outer() -> tuple[int, int]:
        inner_id = threadpool.submit(_inner).result(timeout=5.0)
        return threading.get_ident(), inner_id

    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            outer_id, inner_id = threadpool.submit(_outer).result(timeout=10.0)
        # Ran inline, on the submitting worker itself.
        assert inner_id == outer_id
        assert any(
            'this same pool' in r.getMessage() and '_inner' in r.getMessage()
            for r in caplog.records
        )
    finally:
        threadpool.shutdown(wait=True)


def test_self_submit_propagates_exceptions() -> None:
    """An inline self-submit hands its exception to the returned future."""

    threadpool = ThreadPoolExecutorEx(max_workers=1)

    def _inner() -> None:
        raise ValueError('boom')

    def _outer() -> str:
        try:
            threadpool.submit(_inner).result(timeout=5.0)
        except ValueError as exc:
            return str(exc)
        return 'no exception'

    try:
        assert threadpool.submit(_outer).result(timeout=10.0) == 'boom'
    finally:
        threadpool.shutdown(wait=True)


def test_cross_pool_submit_is_not_inlined(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A worker of one pool submitting to another pool queues normally."""

    pool_a = ThreadPoolExecutorEx(max_workers=1)
    pool_b = ThreadPoolExecutorEx(max_workers=1)

    def _inner() -> int:
        return threading.get_ident()

    def _outer() -> tuple[int, int]:
        inner_id = pool_b.submit(_inner).result(timeout=5.0)
        return threading.get_ident(), inner_id

    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            outer_id, inner_id = pool_a.submit(_outer).result(timeout=10.0)
        assert inner_id != outer_id
        assert 'this same pool' not in caplog.text
    finally:
        pool_a.shutdown(wait=True)
        pool_b.shutdown(wait=True)


def test_no_wait_from_worker_still_queues(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """submit_no_wait from a pool's own worker queues rather than inlining."""

    threadpool = ThreadPoolExecutorEx(max_workers=1)
    ran = threading.Event()
    ran_before_outer_returned: list[bool] = []

    def _inner() -> None:
        ran.set()

    def _outer() -> None:
        threadpool.submit_no_wait(_inner)
        # Our only worker is busy right here, so a queued _inner can't
        # have run yet; an inlined one would have.
        ran_before_outer_returned.append(ran.is_set())

    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            threadpool.submit(_outer).result(timeout=10.0)
            assert ran.wait(timeout=10.0)
        assert ran_before_outer_returned == [False]
        assert 'this same pool' not in caplog.text
    finally:
        threadpool.shutdown(wait=True)
    assert threadpool.no_wait_count == 0


def test_tier2_routes_worker_submits(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A tier-1 worker's submit queues on tier 2, with no error."""

    threadpool = ThreadPoolExecutorEx(max_workers=1, tier2_max_workers=1)
    outer_thread: list[int] = []

    def _inner() -> int:
        return threading.get_ident()

    def _outer() -> int:
        outer_thread.append(threading.get_ident())
        # Our only tier-1 worker is busy right here; an inner that
        # queued on tier 1 would deadlock, an inlined one would share
        # our thread.
        return threadpool.submit(_inner).result(timeout=10.0)

    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            inner_thread = threadpool.submit(_outer).result(timeout=10.0)
        assert inner_thread != outer_thread[0]
        assert 'ThreadPoolExecutorEx' not in caplog.text
    finally:
        threadpool.shutdown(wait=True)


def test_tier2_worker_submit_runs_inline_and_logs_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A tier-2 worker's submit (to either tier) runs inline + errors."""

    threadpool = ThreadPoolExecutorEx(max_workers=1, tier2_max_workers=1)
    threads: dict[str, int] = {}

    def _leaf(key: str) -> None:
        threads[key] = threading.get_ident()

    def _tier2_task() -> None:
        threads['tier2'] = threading.get_ident()
        # Depth three: tier 1 would route this to tier 2 again.
        threadpool.submit(_leaf, 'depth3').result(timeout=10.0)

    def _tier1_task() -> None:
        threadpool.submit(_tier2_task).result(timeout=10.0)

    try:
        with caplog.at_level(logging.ERROR, logger='efro.threadpool'):
            threadpool.submit(_tier1_task).result(timeout=10.0)
        assert threads['depth3'] == threads['tier2']
        assert "this pool's own tier-2 pool" in caplog.text
    finally:
        threadpool.shutdown(wait=True)


def test_tier2_shuts_down_with_pool() -> None:
    """Shutting a pool down also shuts down its tier 2."""

    threadpool = ThreadPoolExecutorEx(max_workers=1, tier2_max_workers=1)
    tier2_done = threading.Event()

    def _leaf() -> None:
        tier2_done.set()

    def _outer() -> None:
        threadpool.submit(_leaf).result(timeout=10.0)

    threadpool.submit(_outer).result(timeout=10.0)
    threadpool.shutdown(wait=True)
    assert tier2_done.is_set()
    # pylint: disable=protected-access
    assert threadpool._tier2 is not None
    with pytest.raises(RuntimeError):
        threadpool._tier2.submit(_leaf)


def test_map_bounded_orders_results_and_caps_concurrency() -> None:
    """Results keep item order; concurrency never exceeds the cap."""

    threadpool = ThreadPoolExecutorEx(max_workers=8)
    lock = threading.Lock()
    active = [0, 0]  # [current, peak]

    def _work(val: int) -> int:
        with lock:
            active[0] += 1
            active[1] = max(active[1], active[0])
        time.sleep(0.01)
        with lock:
            active[0] -= 1
        return val * 2

    try:
        out = threadpool.map_bounded(_work, range(60), max_concurrency=3)
        assert out == [v * 2 for v in range(60)]
        # Caller plus two helpers; it should actually go parallel too.
        assert 2 <= active[1] <= 3
        assert not threadpool.map_bounded(_work, [], max_concurrency=3)
    finally:
        threadpool.shutdown(wait=True)


def test_map_bounded_progresses_on_saturated_pool() -> None:
    """With every worker busy, the caller does the work itself."""

    threadpool = ThreadPoolExecutorEx(max_workers=1)
    release = threading.Event()
    threadpool.submit(release.wait, 10.0)
    caller = threading.get_ident()
    try:
        out = threadpool.map_bounded(
            lambda _val: threading.get_ident(), range(5), max_concurrency=4
        )
        assert out == [caller] * 5
    finally:
        release.set()
        threadpool.shutdown(wait=True)


def test_map_bounded_helpers_yield_their_worker() -> None:
    """Helpers re-queue each slice so other queued work interleaves."""

    threadpool = ThreadPoolExecutorEx(max_workers=1)
    other_ran_at: list[int] = []
    finished = [0]
    lock = threading.Lock()
    started = threading.Event()

    def _work(_val: int) -> None:
        started.set()
        time.sleep(0.01)
        with lock:
            finished[0] += 1

    def _other() -> None:
        with lock:
            other_ran_at.append(finished[0])

    def _submit_other() -> None:
        started.wait(10.0)
        threadpool.submit(_other)

    submitter = threading.Thread(target=_submit_other)
    submitter.start()
    try:
        threadpool.map_bounded(
            _work, range(80), max_concurrency=2, slice_seconds=0.05
        )
        submitter.join()
        threadpool.submit(lambda: None).result(timeout=10.0)
        # Queued behind the lone worker's helper, the other task still
        # got in well before the fan-out finished.
        assert other_ran_at and other_ran_at[0] < 80
    finally:
        threadpool.shutdown(wait=True)


def test_map_bounded_raises_first_error_and_stops() -> None:
    """An exception stops new items and is raised to the caller."""

    threadpool = ThreadPoolExecutorEx(max_workers=4)
    calls = [0]
    lock = threading.Lock()

    def _work(val: int) -> int:
        with lock:
            calls[0] += 1
        if val == 3:
            raise ValueError('boom')
        time.sleep(0.005)
        return val

    try:
        with pytest.raises(ValueError, match='boom'):
            threadpool.map_bounded(_work, range(200), max_concurrency=2)
        assert calls[0] < 200
    finally:
        threadpool.shutdown(wait=True)


def test_map_bounded_routes_by_caller_tier() -> None:
    """Tier-1 callers get tier-2 helpers; tier-2 callers go it alone."""

    threadpool = ThreadPoolExecutorEx(
        max_workers=1, thread_name_prefix='mb', tier2_max_workers=2
    )

    def _work(_val: int) -> str:
        time.sleep(0.01)
        return threading.current_thread().name

    def _from_tier1() -> list[str]:
        return threadpool.map_bounded(_work, range(30), max_concurrency=3)

    def _from_tier2() -> list[str]:
        return threadpool.map_bounded(_work, range(5), max_concurrency=3)

    def _tier1_runs_tier2() -> list[str]:
        return threadpool.submit(_from_tier2).result(timeout=10.0)

    try:
        names = set(threadpool.submit(_from_tier1).result(timeout=10.0))
        # The lone tier-1 worker was the caller; helpers must be tier 2.
        assert any('-t2' in name for name in names)
        assert sum('-t2' not in name for name in names) == 1

        names = set(threadpool.submit(_tier1_runs_tier2).result(timeout=10.0))
        assert len(names) == 1 and '-t2' in next(iter(names))
    finally:
        threadpool.shutdown(wait=True)
