# Released under the MIT License. See LICENSE for details.
#
"""Thread pool functionality."""

from __future__ import annotations

import time
import logging
import threading
from typing import TYPE_CHECKING, ParamSpec
from concurrent.futures import ThreadPoolExecutor

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
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=initializer,
        )
        self.no_wait_count = 0

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

        Any errors occurring in the passed callable will be logged. This
        call will block and log a warning if the threadpool reaches its
        max queued no-wait call count.
        """
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
        except Exception:
            logger.exception('Error in work submitted via submit_no_wait().')
