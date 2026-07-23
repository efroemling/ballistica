# Released under the MIT License. See LICENSE for details.
#
"""Bounded background-thread runner for doc-ui request prep.

Doc-ui prep (fetch + asset-package resolve + page prep) runs in a
background thread. It is long and blocking -- an asset-package
construct/download during resolve can tie a thread up for many seconds
-- so it must stay off the shared app efficiency pool
(:attr:`babase.App.threadpool`), which is for short parallel work (and
doubles as the asyncio default executor).

Rather than a persistent pool -- whose worker threads would linger idle
between our infrequent, bursty requests and clutter thread dumps -- this
spawns a fresh thread per burst of work and lets it exit as soon as it
runs out of queued work. So in steady state no doc-ui prep threads exist
at all. A small cap bounds how many run at once; work submitted past the
cap queues cheaply (as callables, not as blocked threads) until a
running thread frees up to drain it. Submission never blocks the caller
(the logic thread).
"""

import threading
from collections import deque
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable

#: Max doc-ui prep threads running at once. Real in-flight concurrency
#: is usually 1 (a single window fetching or refreshing); the extra slot
#: covers a refresh overlapping a fresh navigation. Work past this queues
#: rather than spawning more threads.
_MAX_IN_FLIGHT = 2

#: Warn once when the pending-work backlog exceeds this -- a sign
#: something is submitting prep faster than it completes (e.g. a runaway
#: refresh loop), which the cap would otherwise hide as a silent queue.
_BACKLOG_WARN = 16


class _BgRunner:
    """Runs submitted callables on capped, self-retiring bg threads."""

    # pylint: disable=too-few-public-methods

    def __init__(self, max_in_flight: int, backlog_warn: int) -> None:
        self._max_in_flight = max_in_flight
        self._backlog_warn = backlog_warn
        self._lock = threading.Lock()
        self._pending: deque[Callable[[], None]] = deque()
        self._in_flight = 0
        self._backlog_warned = False

    def submit(self, call: Callable[[], None]) -> None:
        """Run ``call`` on a bounded bg thread; never blocks.

        Exceptions escaping ``call`` are caught and logged, so callers
        need no error handling of their own (fire-and-forget).
        """
        with self._lock:
            self._pending.append(call)
            if len(self._pending) > self._backlog_warn:
                if not self._backlog_warned:
                    self._backlog_warned = True
                    bui.uilog.warning(
                        'doc-ui bg-prep backlog is %d; prep is being'
                        ' submitted faster than it completes.',
                        len(self._pending),
                    )
            # At the cap already: an existing thread will drain this. It
            # can't have retired without seeing it -- retirement and this
            # append both happen under the lock (see _drain).
            if self._in_flight >= self._max_in_flight:
                return
            self._in_flight += 1

        # Spawn outside the lock. The thread drains queued work then
        # retires, so nothing lingers idle between bursts.
        threading.Thread(
            target=self._drain, name='docuiprep', daemon=True
        ).start()

    def _drain(self) -> None:
        while True:
            with self._lock:
                if not self._pending:
                    self._in_flight -= 1
                    self._backlog_warned = False
                    return
                call = self._pending.popleft()
            try:
                call()
            except Exception:
                bui.uilog.exception('Error in doc-ui bg-prep task.')


#: Shared runner for all doc-ui controllers. Holds no threads until work
#: is submitted, so eager module-level creation costs nothing.
_g_runner = _BgRunner(max_in_flight=_MAX_IN_FLIGHT, backlog_warn=_BACKLOG_WARN)


def submit(call: Callable[[], None]) -> None:
    """Run doc-ui prep work on a capped, self-retiring bg thread.

    Never blocks the caller. See the module docstring for the design.
    """
    _g_runner.submit(call)
