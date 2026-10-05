# Released under the MIT License. See LICENSE for details.
#
"""Thread pool functionality."""

import time
import logging
import functools
import threading
from collections import Counter
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast, override
from concurrent.futures import Future, ThreadPoolExecutor

from efro.util import strip_exception_tracebacks

if TYPE_CHECKING:
    from typing import Any, Callable, Iterable

P = ParamSpec('P')
T = TypeVar('T')
S = TypeVar('S')

logger = logging.getLogger(__name__)

#: Which ThreadPoolExecutorEx (if any) the current thread is running a
#: task for. A pool's task wrapper sets it for the duration of each
#: task, which is how :meth:`ThreadPoolExecutorEx.submit` recognizes a
#: call coming from one of that pool's own workers.
_g_tls = threading.local()


class ThreadPoolExecutorEx(ThreadPoolExecutor):
    """A ThreadPoolExecutor with extra diagnostics.

    Intended for **efficiency**: parallelizing pieces of a single task so
    it finishes faster. It is **not** a queue for long-running or blocking
    work -- a worker tied up on a slow task can't run anything else, so
    long/blocking work starves the pool and delays everything queued
    behind it (and ``submit_no_wait`` callers can pile up a backlog).

    To make misuse easy to spot, submitted work is timed: a task that
    waits too long in the queue before starting, or runs too long, logs a
    (rate-limited) warning naming the callable. ``submit_no_wait`` also
    logs when its backlog exceeds a soft limit. None of these block.

    Waiting on a pool from one of its *own* workers can deadlock it:
    once every worker holds a task that waits on work queued behind
    other such tasks, nothing can ever run. :meth:`submit` detects that
    case, logs an error naming the callable, and runs the call inline
    instead (a DEV bamaster froze this way on 2026-09-11).
    ``submit_no_wait`` from a worker is fine and still queues normally,
    since nothing waits on fire-and-forget work.

    Pass ``tier2_max_workers`` to give the pool a private second tier
    for work that legitimately fans out from inside pool tasks (for
    example a request-path task that fetches several things in
    parallel). :meth:`submit` then routes automatically by caller:

    - From a thread outside the pool: queued on the pool (tier 1).
    - From a tier-1 worker: queued on tier 2 instead, so the waiting
      tier-1 task never waits on its own workers.
    - From a tier-2 worker (to either tier): run inline with an error
      logged, as above. Tier-2 tasks must be leaves; a third level of
      waiting could deadlock tier 2 the same way.

    Waits therefore only ever point from tier 1 down to tier 2. The
    tier-2 pool is never handed out; it is reachable only through this
    routing. Pools without it (the default) keep the plain
    single-tier behavior.
    """

    def __init__(
        self,
        max_workers: int | None = None,
        thread_name_prefix: str = '',
        initializer: Callable[[], None] | None = None,
        max_no_wait_count: int | None = None,
        *,
        allow_submit_no_wait: bool = True,
        queue_wait_warn_seconds: float = 10.0,
        # 10s rather than 5s: legitimate pool work includes things like
        # DNS lookups, which can reasonably take several seconds on a
        # slow or flaky network without indicating any misuse. Warning
        # at 5s mostly reported slow networks rather than long/blocking
        # work, which is what this is meant to catch.
        run_duration_warn_seconds: float = 10.0,
        log_throttle_seconds: float = 10.0,
        tier2_max_workers: int | None = None,
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=initializer,
        )
        self.no_wait_count = 0

        #: Private second tier for submits made from our own workers
        #: (see the class docstring), or None for a single-tier pool.
        self._tier2: ThreadPoolExecutorEx | None = (
            None
            if tier2_max_workers is None
            else ThreadPoolExecutorEx(
                max_workers=tier2_max_workers,
                thread_name_prefix=(thread_name_prefix or 'pool') + '-t2',
                initializer=initializer,
                allow_submit_no_wait=allow_submit_no_wait,
                queue_wait_warn_seconds=queue_wait_warn_seconds,
                run_duration_warn_seconds=run_duration_warn_seconds,
                log_throttle_seconds=log_throttle_seconds,
            )
        )

        #: Whether submit_no_wait() may be used on this pool. Pass
        #: False on hosts with no background CPU (e.g. Cloud Run
        #: request-based billing), where fire-and-forget work would
        #: stall between requests; submit_no_wait() then raises
        #: RuntimeError so offending call sites surface loudly.
        #: Callers with legitimate fire-and-forget needs can branch
        #: on this attr to do the work synchronously instead.
        self.allow_submit_no_wait = allow_submit_no_wait

        self._max_no_wait_count = (
            max_no_wait_count
            if max_no_wait_count is not None
            else 50 if max_workers is None else max_workers * 2
        )

        #: Warn if a submitted task waits longer than this in the queue
        #: before a worker picks it up (pool saturation), or runs longer
        #: than the run threshold (likely misuse -- long work on an
        #: efficiency pool).
        self._queue_wait_warn_seconds = queue_wait_warn_seconds
        self._run_duration_warn_seconds = run_duration_warn_seconds

        #: Min seconds between repeats of any one throttled log line, so a
        #: bad spell can't saturate the logs. Keyed by a short kind string.
        self._log_throttle_seconds = log_throttle_seconds
        self._last_log_times: dict[str, float] = {}

        self._no_wait_count_lock = threading.Lock()

        #: Count of in-flight no-wait calls keyed by callable name, so an
        #: over-soft-limit log can name the spike's likely source.
        #: Guarded by ``_no_wait_count_lock``.
        self._no_wait_calls: Counter[str] = Counter()

    def submit_no_wait(
        self, call: Callable[P, Any], *args: P.args, **keywds: P.kwargs
    ) -> None:
        """Submit fire-and-forget work to the threadpool.

        Any exceptions raised by the callable are automatically caught
        and logged via ``logger.exception()``, so callers do not need
        their own error handling for fire-and-forget work.

        This call **never blocks**. If the pool's queued no-wait backlog
        exceeds its soft limit we log an error (naming the most common
        in-flight callables, to help pinpoint the source of a spike) but
        still submit. A blocking backpressure was used here previously,
        but it could self-deadlock when ``submit_no_wait`` was called from
        one of this pool's own workers — the backlog only drains via those
        same workers, so blocking them stalled it forever. A loud,
        non-blocking warning gives the same visibility without that risk.

        Raises RuntimeError if the pool was created with
        ``allow_submit_no_wait=False`` (hosts with no background CPU).
        """
        if not self.allow_submit_no_wait:
            raise RuntimeError(
                'submit_no_wait() is disabled for this threadpool'
                ' (no background processing available on this host).'
                ' Do the work synchronously instead; see the'
                ' allow_submit_no_wait attr.'
            )

        key = _stable_callable_name(call)
        with self._no_wait_count_lock:
            self.no_wait_count += 1
            self._no_wait_calls[key] += 1
            count = self.no_wait_count

        # Over the soft limit: log (rate-limited) but never block.
        if count > self._max_no_wait_count and self._should_log('backlog'):
            logger.error(
                'ThreadPoolExecutorEx no-wait backlog (%d) exceeds soft'
                ' limit (%d); not blocking. Top in-flight no-wait'
                ' callables: %s.',
                count,
                self._max_no_wait_count,
                self._top_no_wait_calls(),
            )

        # Always queue, even from one of our own workers: nothing waits
        # on fire-and-forget work so it can't deadlock us, and running it
        # inline would needlessly stall the calling worker.
        fut = self._submit_queued(call, *args, **keywds)
        fut.add_done_callback(functools.partial(self._no_wait_done, key=key))

    def _top_no_wait_calls(self, count: int = 5) -> str:
        """Compact ``name=N, ...`` of the top in-flight no-wait calls."""
        with self._no_wait_count_lock:
            top = self._no_wait_calls.most_common(count)
        return ', '.join(f'{name}={num}' for name, num in top) or '(none)'

    @override
    def submit(
        self, fn: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs
    ) -> Future[T]:
        """Submit work, timing its queue-wait and run duration.

        See the class docstring: this pool is for short parallel work,
        not long-running or blocking tasks. Submitted callables are timed
        and a slow wait-to-start or a slow run logs a rate-limited warning
        naming the callable, so misuse is easy to spot.

        Called from one of this pool's own workers, the call instead runs
        inline on that worker and the returned future is already done,
        with an error logged naming the callable: a worker that waits on
        its own pool can deadlock it. Treat that error as a bug to fix
        (do the work inline or on a dedicated executor), not as a
        supported path. Pools with a second tier route a tier-1 worker's
        submit there instead; see the class docstring.
        """
        # Typed local: comparing the untyped thread-local attr directly
        # against self would narrow self to Any here.
        current_pool: ThreadPoolExecutor | None = getattr(_g_tls, 'pool', None)
        if current_pool is self:
            if self._tier2 is not None:
                return self._tier2.submit(fn, *args, **kwargs)
            return self._run_self_submit_inline(
                'a worker of this same pool', fn, *args, **kwargs
            )
        if current_pool is not None and current_pool is self._tier2:
            return self._run_self_submit_inline(
                "a worker of this pool's own tier-2 pool", fn, *args, **kwargs
            )
        return self._submit_queued(fn, *args, **kwargs)

    @override
    def shutdown(
        self, wait: bool = True, *, cancel_futures: bool = False
    ) -> None:
        """Shut down the pool, and its tier-2 pool if it has one.

        Tier 1 goes first: its tasks may still be feeding tier 2.
        """
        super().shutdown(wait=wait, cancel_futures=cancel_futures)
        if self._tier2 is not None:
            self._tier2.shutdown(wait=wait, cancel_futures=cancel_futures)

    def _submit_queued(
        self, fn: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs
    ) -> Future[T]:
        """Queue ``fn`` on the pool, wrapped for timing diagnostics."""
        return super().submit(self._wrap_timed(fn), *args, **kwargs)

    def _run_self_submit_inline(
        self,
        submitter: str,
        fn: Callable[P, T],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Future[T]:
        """Run a call submitted from one of our own workers, inline.

        See :meth:`submit`. ``submitter`` describes the calling worker
        for the log line. Logged at error (rate-limited per callable,
        with the submitting stack) so offending call sites get fixed.
        """
        name = _stable_callable_name(fn)
        if self._should_log(f'self_submit:{name}'):
            logger.error(
                'ThreadPoolExecutorEx: %s was submitted from %s; running'
                ' it inline. A worker that waits on its own pool can'
                ' deadlock it (every worker holding a task that waits on'
                ' work queued behind other such tasks), and tier-2 tasks'
                ' must not wait on anything in the pool. Fix the caller:'
                ' do this work inline or on a dedicated executor.',
                name,
                submitter,
                stack_info=True,
            )
        fut: Future[T] = Future()
        try:
            fut.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # pylint: disable=broad-exception-caught
            # Mirror ThreadPoolExecutor, which hands any exception from
            # submitted work to whoever collects its future.
            fut.set_exception(exc)
        return fut

    def _wrap_timed(self, fn: Callable[P, T]) -> Callable[P, T]:
        """Wrap ``fn`` to warn on excessive queue-wait / run duration."""
        enqueue_time = time.monotonic()
        name = _stable_callable_name(fn)

        def _timed(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.monotonic()
            wait = start - enqueue_time
            if wait > self._queue_wait_warn_seconds and self._should_log(
                'queue_wait'
            ):
                logger.warning(
                    'ThreadPoolExecutorEx: %s waited %.1fs in the queue'
                    ' before starting (over %.0fs). This pool is for short'
                    ' parallel work; long/blocking tasks or floods saturate'
                    ' it and delay everything queued behind them.',
                    name,
                    wait,
                    self._queue_wait_warn_seconds,
                )
            # Mark this thread as serving us for the duration of the task
            # so a nested submit() back into this pool is recognized.
            prev_pool = getattr(_g_tls, 'pool', None)
            _g_tls.pool = self
            try:
                return fn(*args, **kwargs)
            finally:
                _g_tls.pool = prev_pool
                duration = time.monotonic() - start
                if (
                    duration > self._run_duration_warn_seconds
                    and self._should_log('run_duration')
                ):
                    logger.warning(
                        'ThreadPoolExecutorEx: %s ran %.1fs (over %.0fs).'
                        ' This pool is for short parallel work to speed a'
                        ' task up, not long-running or blocking work -- that'
                        ' ties up a worker and starves the pool. Move long'
                        ' work elsewhere.',
                        name,
                        duration,
                        self._run_duration_warn_seconds,
                    )

        return _timed

    def _should_log(self, kind: str) -> bool:
        """Return True at most once per throttle window for ``kind``.

        Lock-free and thus slightly inexact under races (an occasional
        extra line), which is fine for diagnostics.
        """
        now = time.monotonic()
        last = self._last_log_times.get(kind)
        if last is None or now - last > self._log_throttle_seconds:
            self._last_log_times[kind] = now
            return True
        return False

    def map_bounded(
        self,
        fn: Callable[[S], T],
        items: Iterable[S],
        *,
        max_concurrency: int,
        slice_seconds: float = 0.25,
    ) -> list[T]:
        """Run ``fn`` over ``items`` in parallel; return ordered results.

        The bounded alternative to a ``submit()`` per item. However many
        items there are, this call occupies at most ``max_concurrency -
        1`` pool workers at once, so one large fan-out can't take the
        whole pool and stall everything queued behind it.

        The calling thread works through the items too instead of
        idling on futures. That makes it one of the ``max_concurrency``
        lanes, and guarantees progress on a saturated pool: the call
        degrades toward serial rather than waiting in the queue.

        Helpers hand their worker back every ``slice_seconds`` and
        re-queue, so a long fan-out interleaves with other queued work
        and stays within the pool's short-task contract. That yielding,
        not a narrow ``max_concurrency``, is what keeps the pool
        responsive: measured on a 10-worker pool under a 1000-item
        fan-out of ~40ms network calls, a trivial task waited a median
        2.6s behind the ``submit()``-per-item shape, 0.3s with 1s
        slices at full width, and 0.02s with 0.25s slices. So prefer a
        ``max_concurrency`` near the pool's width for latency-bound
        work, and keep items small -- a helper can't yield mid-item.

        Routing follows :meth:`submit`: from a tier-1 worker the helpers
        run on tier 2; from a tier-2 worker (or a worker of a
        single-tier pool) no helpers are used and the caller runs every
        item itself, which is always safe.

        If any call raises, no further items are started and the first
        exception is raised here once in-flight calls have finished.
        """
        if max_concurrency < 1:
            raise ValueError('max_concurrency must be at least 1.')
        itemlist = list(items)
        count = len(itemlist)
        if count == 0:
            return []

        # Where helpers may run; None means the caller goes it alone.
        current_pool: ThreadPoolExecutor | None = getattr(_g_tls, 'pool', None)
        target: ThreadPoolExecutorEx | None
        if current_pool is None:
            target = self
        elif current_pool is self:
            target = self._tier2
        else:
            # A tier-2 worker (must stay a leaf) or a foreign pool's
            # worker; either way don't wait on pool work from here.
            target = None if current_pool is self._tier2 else self

        results: list[T | None] = [None] * count
        lock = threading.Lock()
        done = threading.Event()
        # [next index to hand out, calls in flight]
        state = [0, 0]
        errors: list[BaseException] = []

        def _take() -> int | None:
            with lock:
                if errors or state[0] >= count:
                    return None
                index = state[0]
                state[0] += 1
                state[1] += 1
                return index

        def _run_one(index: int) -> None:
            try:
                results[index] = fn(itemlist[index])
            except BaseException as exc:  # pylint: disable=broad-except
                # Handed to the caller below, which owns it from there.
                with lock:
                    errors.append(exc)
            with lock:
                state[1] -= 1
                if state[1] == 0 and (errors or state[0] >= count):
                    done.set()

        def _helper() -> None:
            # pylint: disable=protected-access
            assert target is not None
            slice_end = time.monotonic() + slice_seconds
            while (index := _take()) is not None:
                _run_one(index)
                if time.monotonic() >= slice_end:
                    # Yield our worker; nothing waits on this future so
                    # re-queueing from a worker here is deadlock-safe.
                    try:
                        target._submit_queued(_helper)
                    except RuntimeError:
                        pass  # Pool shut down; the caller finishes up.
                    return

        # Name helpers after the real work in pool diagnostics.
        setattr(_helper, '__wrapped__', fn)

        if target is not None:
            for _ in range(min(max_concurrency, count) - 1):
                # pylint: disable-next=protected-access
                target._submit_queued(_helper)

        while (index := _take()) is not None:
            _run_one(index)
        done.wait()

        if errors:
            raise errors[0]
        # Every slot was filled (None only if fn itself returned it).
        return cast('list[T]', results)

    def submit_no_wait_or_run(
        self, call: Callable[P, Any], *args: P.args, **keywds: P.kwargs
    ) -> None:
        """Fire-and-forget ``call`` off-thread, or run it inline.

        Equivalent to :meth:`submit_no_wait` on pools that allow it, but
        on pools that don't (``allow_submit_no_wait=False`` — hosts with
        no background CPU, e.g. Cloud Run request-based billing / BEEF) it
        runs ``call`` synchronously instead of raising. Either way the work
        is **best-effort**: exceptions are caught and logged, never
        propagated (the inline path mirrors ``submit_no_wait``'s
        off-thread handling).

        This is the one-call form of the common
        "``if pool.allow_submit_no_wait: submit_no_wait(...) else: <run
        inline>``" branch. Use it for cheap, latency-shaving side effects
        (e.g. cache writes) where the inline fallback's brief synchronous
        cost is acceptable; for heavier work, branch explicitly so you
        notice when you're blocking a request.
        """
        if self.allow_submit_no_wait:
            self.submit_no_wait(call, *args, **keywds)
            return
        # No background CPU on this pool -- run inline, best-effort.
        try:
            call(*args, **keywds)
        except Exception as exc:
            logger.exception('Error in work run via submit_no_wait_or_run().')
            # Terminal consumer of this exception; strip to avoid cycles.
            strip_exception_tracebacks(exc)

    def _no_wait_done(self, fut: Future, *, key: str) -> None:
        with self._no_wait_count_lock:
            self.no_wait_count -= 1
            self._no_wait_calls[key] -= 1
            # Keep the Counter from accumulating stale zero entries.
            if self._no_wait_calls[key] <= 0:
                del self._no_wait_calls[key]
        try:
            fut.result()
        except Exception as exc:
            logger.exception('Error in work submitted via submit_no_wait().')
            # We're done with this exception, so strip its traceback to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)


def _stable_callable_name(call: Callable[..., Any]) -> str:
    """Short, stable, address-free name for a submitted callable.

    Serves two roles: display label in diagnostic warnings, and
    aggregation key for the in-flight no-wait call Counter. The second
    role is why this extracts a name instead of using ``str()`` or
    ``repr()``:

    - For anything but a plain function, ``str()`` embeds a memory
      address and/or instance state (``<bound method Foo.bar of <Foo
      object at 0x...>>``), so the same logical callable invoked on N
      different objects would fragment into N distinct Counter keys of
      count 1, rendering the top-callables report useless. Extracted
      names collapse them all to ``Foo.bar`` — the granularity the
      diagnostics want. (Addresses are also display noise that varies
      per process, hurting log grouping and grepping.)
    - ``str()`` of a :class:`functools.partial` (or any wrapper whose
      ``__repr__`` shows its stored args) drags arg reprs into the log
      line: unbounded length, and in server pools possibly sensitive
      data.

    Wrappers are unwrapped to the real target through the two stdlib
    conventions: :class:`functools.partial`'s ``func`` attr and the
    ``__wrapped__`` attr set by :func:`functools.wraps` (and by
    callable wrapper classes such as babase's ``CallStrict``). Without
    unwrapping, such wrappers expose no ``__name__`` and would all
    collapse into a useless bare wrapper-class name (``partial``,
    ``CallStrict``). The ``type(target).__name__`` fallback remains
    for wrapper classes that don't participate in either convention.
    """
    target: Any = call
    # Depth-capped so a pathological __wrapped__ cycle can't spin.
    for _ in range(10):
        if isinstance(target, functools.partial):
            target = target.func
        else:
            wrapped = getattr(target, '__wrapped__', None)
            if wrapped is None:
                break
            target = wrapped
    return (
        getattr(target, '__qualname__', None)
        or getattr(target, '__name__', None)
        or type(target).__name__
    )


# ---- Threadpool introspection ----
#
# These accessors let monitoring code sample a pool's live state.
# They reach into ``concurrent.futures.thread``'s private attributes
# (``_work_queue`` / ``_threads`` / ``_idle_semaphore``) because the
# public API doesn't expose queue depth or busy-count. Each access
# is wrapped in a try/except and falls back to ``None`` with a
# one-shot WARNING log if the internals change shape — that warning
# is the canary that this code needs an update for the current
# CPython version. Free functions (rather than methods on
# ``ThreadPoolExecutorEx``) so they work on any
# ``concurrent.futures.ThreadPoolExecutor``, including the asyncio
# loop's default executor (which is a plain ``ThreadPoolExecutor``).

#: Tracks per-(executor-id, attr) keys we've already warned about,
#: so a single broken introspection produces one log line per
#: process rather than spamming. ``id(executor)`` keys lets multiple
#: pools coexist with independent warning state.
_g_introspection_warned: set[tuple[int, str]] = set()
_g_introspection_warned_lock = threading.Lock()


def _warn_introspection_broken(executor: ThreadPoolExecutor, what: str) -> None:
    key = (id(executor), what)
    with _g_introspection_warned_lock:
        if key in _g_introspection_warned:
            return
        _g_introspection_warned.add(key)
    logger.warning(
        'Threadpool introspection broken: %s on %r.'
        ' CPython internals may have changed shape;'
        ' efro/threadpool.py needs an update.',
        what,
        type(executor).__name__,
    )


def queue_depth(executor: ThreadPoolExecutor) -> int | None:
    """Return the current count of pending work items in ``executor``.

    Best-effort: reads the underlying ``ThreadPoolExecutor``'s
    ``_work_queue`` (a :class:`queue.SimpleQueue`) and calls its
    public ``qsize()``. Returns ``None`` and logs a one-shot warning
    (per-executor, per-attr) if the shape doesn't match expectations.
    """
    try:
        wq = getattr(executor, '_work_queue', None)
        if wq is None or not hasattr(wq, 'qsize'):
            _warn_introspection_broken(executor, '_work_queue.qsize')
            return None
        return int(wq.qsize())
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception('queue_depth() introspection failed.')
        return None


def live_thread_count(executor: ThreadPoolExecutor) -> int | None:
    """Return the count of worker threads currently alive in ``executor``.

    ``ThreadPoolExecutor`` spawns workers on demand and keeps them
    alive until ``shutdown()``, so this is a high-water rather than
    instantaneous-busy count. Pair with :func:`busy_workers` or
    :func:`queue_depth` to interpret saturation. Returns ``None`` and
    logs a one-shot warning on internals breakage.
    """
    try:
        threads = getattr(executor, '_threads', None)
        if not isinstance(threads, set):
            _warn_introspection_broken(executor, '_threads not a set')
            return None
        return len(threads)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception('live_thread_count() introspection failed.')
        return None


def busy_workers(executor: ThreadPoolExecutor) -> int | None:
    """Return the count of worker threads currently executing work.

    Computed as ``live_thread_count - idle_workers``, where
    ``idle_workers`` reads ``_idle_semaphore._value`` (the
    Semaphore's remaining permits — workers ``release()`` when they
    go idle and ``acquire()`` when they pick up new work). Touching
    ``Semaphore._value`` is the most fragile of these accessors; on
    any breakage we return ``None`` and log a one-shot warning
    rather than guessing.
    """
    live = live_thread_count(executor)
    if live is None:
        return None
    try:
        idle_sem = getattr(executor, '_idle_semaphore', None)
        if idle_sem is None:
            _warn_introspection_broken(executor, '_idle_semaphore missing')
            return None
        idle_count = getattr(idle_sem, '_value', None)
        if not isinstance(idle_count, int):
            _warn_introspection_broken(executor, '_idle_semaphore._value')
            return None
        # Clamp: under transient races between sampling and workers
        # transitioning, idle could exceed live by an off-by-one.
        # Floor at zero so we never report negative.
        return max(0, live - idle_count)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception('busy_workers() introspection failed.')
        return None
