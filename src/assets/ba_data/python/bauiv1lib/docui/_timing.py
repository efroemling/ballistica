# Released under the MIT License. See LICENSE for details.
#
"""Where the time goes when a doc-ui page is put on screen.

A page that needs nothing from the network -- a client-local page, a
cached one being shown again -- should appear almost at once. When one
doesn't, something on this device is in the way: a busy thread pool, a
busy logic thread, slow storage. :class:`PageTiming` follows one
request from submission to the built page and logs a breakdown when
the purely local part of that ran long.

Time spent waiting on the network (fetching the page from a server,
downloading its asset-packages, queueing behind someone else's
resolve) is expected to be slow at times and is left out of that
judgement, though it is still shown in the breakdown.
"""

import time
import threading
from dataclasses import dataclass, field

import bauiv1 as bui

#: Local time (see :meth:`PageTiming.local_seconds`) at or past which a
#: page's breakdown is logged.
SLOW_LOCAL_SECONDS = 1.0

#: Breakdowns logged per run, at most. One slow device would otherwise
#: log one for every page it opens.
_MAX_REPORTS = 5

_g_report_count = 0

_tls = threading.local()


@dataclass
class PageTiming:
    """Timings for one doc-ui request; all values in seconds."""

    # pylint: disable=too-many-instance-attributes

    #: What is being built (controller and path), for the log line.
    description: str

    submitted_at: float = field(default_factory=time.monotonic)

    #: Waiting for a doc-ui prep thread.
    queue: float = 0.0

    #: The controller producing its response.
    fulfill: float = 0.0

    #: Whether producing the response went to the network.
    fulfill_used_network: bool = False

    #: The asset-package resolve as a whole, including the two below.
    resolve: float = 0.0

    #: The part of the resolve spent queued behind other resolves.
    resolve_queue: float = 0.0

    #: Whether the resolve had to download anything (or failed or timed
    #: out, which we can't tell apart from network trouble).
    resolve_used_network: bool = False

    #: Copying and de-indexing the response.
    deindex: float = 0.0

    #: Laying the page out.
    prep: float = 0.0

    #: Getting from the prep thread back onto the logic thread.
    hop: float = 0.0

    #: Creating the page's widgets.
    instantiate: float = 0.0

    #: When the prep thread handed off to the logic thread.
    handed_off_at: float | None = None

    def local_seconds(self) -> float:
        """Time that went to this device alone, network waits left out."""
        total = self.queue + self.deindex + self.prep + self.hop
        total += self.instantiate
        if not self.fulfill_used_network:
            total += self.fulfill
        if not self.resolve_used_network:
            total += max(0.0, self.resolve - self.resolve_queue)
        return total

    def report_if_slow(self) -> None:
        """Log a breakdown if the local part of this page ran long."""
        global _g_report_count  # pylint: disable=global-statement

        local = self.local_seconds()
        if local < SLOW_LOCAL_SECONDS or _g_report_count >= _MAX_REPORTS:
            return
        _g_report_count += 1

        from efro.threadpool import (
            queue_depth,
            live_thread_count,
            busy_workers,
        )

        pool = bui.app.threadpool
        bui.uilog.warning(
            'Doc-ui page %s took %.2fs of local (non-network) time:'
            ' prep-thread wait %.2fs, fulfill %.2fs%s, asset resolve'
            ' %.2fs%s (of which %.2fs queued behind other resolves),'
            ' de-index %.2fs, prep %.2fs, logic-thread hop %.2fs,'
            ' instantiate %.2fs. App threadpool: %s busy of %s threads,'
            ' %s queued. Modding: %s.%s',
            self.description,
            local,
            self.queue,
            self.fulfill,
            ' (network; not counted)' if self.fulfill_used_network else '',
            self.resolve,
            ' (network; not counted)' if self.resolve_used_network else '',
            self.resolve_queue,
            self.deindex,
            self.prep,
            self.hop,
            self.instantiate,
            busy_workers(pool),
            live_thread_count(pool),
            queue_depth(pool),
            bui.app.plugins.user_code_summary(),
            (
                ' (Further slow-page reports are suppressed this run.)'
                if _g_report_count >= _MAX_REPORTS
                else ''
            ),
        )


def set_current(timing: PageTiming | None) -> None:
    """Set the timing that this thread's doc-ui prep work belongs to."""
    _tls.timing = timing


def current() -> PageTiming | None:
    """The timing this thread's doc-ui prep work belongs to, if any."""
    return getattr(_tls, 'timing', None)


def note_network_fulfill() -> None:
    """Note that the response being produced here comes off the network.

    Called by whatever fetches a page from a server, so a slow fetch
    isn't mistaken for a slow device.
    """
    timing = current()
    if timing is not None:
        timing.fulfill_used_network = True
