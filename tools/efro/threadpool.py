# Released under the MIT License. See LICENSE for details.
#
"""Thread pool functionality."""

import time
import logging
import functools
import threading
from collections import Counter
from typing import TYPE_CHECKING, ParamSpec, TypeVar, override
from concurrent.futures import ThreadPoolExecutor

from efro.util import strip_exception_tracebacks

if TYPE_CHECKING:
    from typing import Any, Callable
    from concurrent.futures import Future

P = ParamSpec('P')
T = TypeVar('T')

logger = logging.getLogger(__name__)


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
        run_duration_warn_seconds: float = 5.0,
        log_throttle_seconds: float = 10.0,
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=initializer,
        )
        self.no_wait_count = 0

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

        fut = self.submit(call, *args, **keywds)
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
        """
        return super().submit(self._wrap_timed(fn), *args, **kwargs)

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
            try:
                return fn(*args, **kwargs)
            finally:
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
