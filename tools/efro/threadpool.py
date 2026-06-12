# Released under the MIT License. See LICENSE for details.
#
"""Thread pool functionality."""

import time
import logging
import threading
from typing import TYPE_CHECKING, ParamSpec
from concurrent.futures import ThreadPoolExecutor

from efro.util import strip_exception_tracebacks

if TYPE_CHECKING:
    from typing import Any, Callable
    from concurrent.futures import Future

P = ParamSpec('P')

logger = logging.getLogger(__name__)


class ThreadPoolExecutorEx(ThreadPoolExecutor):
    """A ThreadPoolExecutor with additional functionality added."""

    def __init__(
        self,
        max_workers: int | None = None,
        thread_name_prefix: str = '',
        initializer: Callable[[], None] | None = None,
        max_no_wait_count: int | None = None,
        *,
        allow_submit_no_wait: bool = True,
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
        self._last_no_wait_warn_time: float | None = None
        self._no_wait_count_lock = threading.Lock()

    def submit_no_wait(
        self, call: Callable[P, Any], *args: P.args, **keywds: P.kwargs
    ) -> None:
        """Submit work to the threadpool with no expectation of waiting.

        Any exceptions raised by the callable are automatically caught
        and logged via ``logger.exception()``, so callers do not need
        their own error handling for fire-and-forget work. This call will
        block and log a warning if the threadpool reaches its max queued
        no-wait call count.

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
        # If we're too backlogged, issue a warning and block until we
        # aren't. We don't bother with the lock here since this can be
        # slightly inexact. In general we should aim to not hit this
        # limit but it is good to have backpressure to avoid runaway
        # queues in cases of network outages/etc.
        if self.no_wait_count > self._max_no_wait_count:
            now = time.monotonic()
            if (
                self._last_no_wait_warn_time is None
                or now - self._last_no_wait_warn_time > 10.0
            ):
                logger.warning(
                    'ThreadPoolExecutorEx hit max no-wait limit of %s;'
                    ' blocking.',
                    self._max_no_wait_count,
                )
                self._last_no_wait_warn_time = now
            while self.no_wait_count > self._max_no_wait_count:
                time.sleep(0.01)

        fut = self.submit(call, *args, **keywds)
        with self._no_wait_count_lock:
            self.no_wait_count += 1
        fut.add_done_callback(self._no_wait_done)

    def _no_wait_done(self, fut: Future) -> None:
        with self._no_wait_count_lock:
            self.no_wait_count -= 1
        try:
            fut.result()
        except Exception as exc:
            logger.exception('Error in work submitted via submit_no_wait().')
            # We're done with this exception, so strip its traceback to
            # avoid reference cycles.
            strip_exception_tracebacks(exc)


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
