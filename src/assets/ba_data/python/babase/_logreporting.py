# Released under the MIT License. See LICENSE for details.
#
"""Shipping log history to the cloud after something goes wrong."""

import time
import json
import threading
from typing import TYPE_CHECKING

import _babase
from efro.util import utc_now, strip_exception_tracebacks
from efro.error import CommunicationError
from bacommon.logreporting import LogReportWindow
from babase._logging import logreportlog, userlog
from babase._apputils import should_submit_debug_info

if TYPE_CHECKING:
    from typing import Callable

    from efro.call import CallbackRegistration
    from efro.logging import LogLevel, LogEntry, LogArchive, LogHandler
    from bacommon.logreporting import LogReportSpec

    from babase._accountv2 import AccountV2Handle

    import bacommon.cloud

#: How long to sleep between retries when we have entries ready but
#: cannot send them (no transport, or a send failed). Also the idle
#: tick of the worker thread, which is why it doubles as our
#: connectivity poll -- there is no edge notification to miss this
#: way, just a state re-check.
_RETRY_INTERVAL_SECONDS = 10.0

#: How long to wait between checks for new post-trigger entries once
#: a window is open and all current entries have shipped. Batches a
#: trickle of entries into periodic slices instead of a send per
#: entry.
_FLUSH_INTERVAL_SECONDS = 5.0

#: Ceiling on how long shutdown waits for the worker. A send in flight
#: is not worth stalling app exit for; the thread is a daemon so the
#: process can leave without it if it overruns.
_SHUTDOWN_JOIN_SECONDS = 2.0

#: Ceiling on the final at-shutdown send attempt. Kept under
#: _SHUTDOWN_JOIN_SECONDS so a hung send times out and lets the
#: worker exit inside the join budget instead of showing up as a
#: stray thread in the engine's end-of-run checks.
_SHUTDOWN_SEND_SECONDS = 1.5


#: The app's single reporter. Process-global like the log handler it
#: feeds off, and for the same reason: the things that need to reach it
#: (the log callback, the cloud subsystem, app shutdown) come up at
#: very different points in bring-up.
_g_log_reporter: LogReporter | None = None


def get_log_reporter() -> LogReporter | None:
    """Return the app's log reporter, or None if none was created.

    :meta private:
    """
    return _g_log_reporter


def create_log_reporter(log_handler: LogHandler) -> LogReporter:
    """Create the app's log reporter. Called once during env setup."""
    global _g_log_reporter  # pylint: disable=global-statement

    assert _g_log_reporter is None
    _g_log_reporter = LogReporter(log_handler)
    return _g_log_reporter


class LogReporter:
    """Ships a window of our log history to the cloud when triggered.

    Disabled unless the server hands this client a
    :class:`~bacommon.logreporting.LogReportSpec` via
    :attr:`~bacommon.cloud.CloudValsTransient.log_report`, so the
    default state for the fleet is silence.

    A matching entry (by level or phrase) opens a capture window: up
    to ``max_before_entries`` of context, the trigger, and up to
    ``max_after_entries`` after it. The pre-trigger slice ships
    immediately; post-trigger entries ship in periodic follow-up
    slices as they accumulate. Progress is tracked with a cursor that
    only advances after a send's round trip completes, so a failed
    send re-sends its range rather than dropping it (the server
    dedupes overlap). One window per run; there is no re-arming.

    **Threading.** Three threads touch this, and keeping them straight
    is the whole design:

    - :meth:`handle_log_entry` runs on the :class:`~efro.logging.
      LogHandler`'s thread. It must stay trivial -- that thread
      processes *all* logging, so blocking it (on a JSON encode, let
      alone a network round trip) would stall logging app-wide.
    - :meth:`set_config` runs on the logic thread, from the cloud
      subsystem's transient-vals callback. It only copies values in.
    - Everything expensive -- gathering, encoding, compressing,
      sending -- happens on our own worker thread, which exists only
      once something has actually triggered a report.

    The worker is deliberately *not* a threadpool thread: a send can
    outlast the pool's patience, and this work has no deadline worth
    complaining about.
    """

    def __init__(self, log_handler: LogHandler) -> None:
        # Handed in rather than fetched from baenv: importing baenv
        # from here would close an import cycle back through babase.
        self._log_handler = log_handler

        # Everything below is guarded by _cond's lock. NEVER log while
        # holding it: our log would come back through
        # handle_log_entry() on the LogHandler thread, which wants the
        # same lock.
        self._cond = threading.Condition()

        # Config, copied from CloudValsTransient as it arrives. None
        # until the server enables reporting for us.
        self._spec: LogReportSpec | None = None

        # The open capture window and its trigger details; set once
        # when an entry trips the spec.
        self._window: LogReportWindow | None = None
        self._trigger_level: LogLevel | None = None
        self._trigger_phrase: str | None = None

        # apptime-independent monotonic deadline for the worker's next
        # gather/send attempt.
        self._next_attempt_time: float | None = None

        # Set once the window has fully shipped.
        self._done = False

        # Current primary account, refreshed on the logic thread.
        # Kept current rather than captured once: we live for the whole
        # run, so a handle grabbed at startup would keep attributing
        # reports to an account the player has since left.
        self._account: AccountV2Handle | None = None

        self._shutting_down = False
        self._thread: threading.Thread | None = None
        self._shutdown_task_registered = False
        self._account_watch_registered = False
        self._account_registration: (
            CallbackRegistration[Callable[[AccountV2Handle | None], None]]
            | None
        ) = None

    def set_config(self, vals: bacommon.cloud.CloudValsTransient) -> None:
        """Adopt log-reporting config. Call from the logic thread."""
        assert _babase.in_logic_thread()

        spec = vals.log_report

        # Ignore specs that could never trip.
        if spec is not None and not spec.active:
            spec = None

        # Honor the user's debug-info preference. Nothing in the
        # current UI writes this, but it can still be sitting False in
        # a config.json from an older build that did expose it, and it
        # is consent for precisely this behavior -- so an explicit
        # opt-out keeps working rather than being quietly dropped along
        # with the v1 log path that used to check it.
        if spec is not None and not should_submit_debug_info():
            spec = None

        enabled = spec is not None

        with self._cond:
            # Note that swapping config does not disturb a window that
            # already tripped; its bounds were fixed at trigger time.
            self._spec = spec
            self._cond.notify()

        # Our worker can only ever exist once reporting is enabled, and
        # enabling only happens here -- on the logic thread, with an App
        # in place. So this is the one spot where we can register a
        # shutdown task, and it covers every case where a thread might
        # need stopping. (We are created during native module import,
        # long before an App exists, so we cannot register at birth.)
        if enabled and not self._shutdown_task_registered:
            self._shutdown_task_registered = True
            _babase.app.add_shutdown_task(self._shutdown_task())

        # Track the primary account so reports from a signed-in player
        # are attributable. Without an account context the server
        # cannot tell who sent a report -- it resolves identity from a
        # token attached to the message, not from the channel -- so a
        # signed-in player's reports would otherwise look anonymous.
        if enabled and not self._account_watch_registered:
            plus = _babase.app.plus
            if plus is not None:
                self._account_watch_registered = True
                self._account_registration = (
                    plus.accounts.on_primary_account_changed_callbacks.register(
                        self._set_account
                    )
                )
                # Seed with whatever is current; the callback only
                # fires on change.
                self._set_account(plus.accounts.primary)

    def handle_log_entry(self, entry: LogEntry) -> None:
        """Consider an entry as a trigger. Runs on the LogHandler thread.

        Kept to a lock acquire and a couple of comparisons; all real
        work is handed to the worker.
        """
        # Never let our own output trigger us. Without this, a failed
        # send that logs a warning would arm the next report, which
        # would fail and log again -- a slow self-sustaining loop.
        if entry.name == logreportlog.name:
            return

        # User-specific issues (a playlist naming a map they deleted,
        # a mod of theirs that won't import) are worth telling *them*
        # about at whatever level fits, but they say nothing about
        # engine health, so they never arm a report. Entries still
        # reach the log cache, so they remain as context in windows
        # tripped by something else. Hard-coded for now; if this needs
        # to grow, the natural home is an exclusion list on
        # LogReportSpec so it can be tuned from the cloud.
        if entry.name == userlog.name or entry.name.startswith(
            f'{userlog.name}.'
        ):
            return

        with self._cond:
            if self._done or self._shutting_down:
                return

            # Entries after the trigger need nothing from us here; the
            # worker's periodic gathers pick them up.
            if self._window is not None:
                return

            spec = self._spec
            if spec is None:
                return
            matched, phrase = spec.match_entry(entry.level, entry.message)
            if not matched:
                return

            # Tripped. This entry's index is the cache's current end:
            # emits and callbacks share the LogHandler thread, and the
            # handler appends before running callbacks. (get_cached
            # takes the handler's cache lock, which is safe here: the
            # handler never runs callbacks while holding it. Config
            # also cannot be set until well after our callback was
            # registered, so replayed pre-registration entries -- for
            # which this index math would be wrong -- can never trip.)
            trigger_index = (
                self._log_handler.get_cached(
                    start_index=0, max_entries=0
                ).log_size
                - 1
            )
            self._window = LogReportWindow.from_trigger(trigger_index, spec)
            self._trigger_level = entry.level
            self._trigger_phrase = phrase

            # Ship the trigger and its pre-roll immediately; the
            # explicit follow-up gathers are what pick up the burst
            # that tends to follow a bad log, so there is no need to
            # linger here for it.
            self._next_attempt_time = 0.0
            self._ensure_thread_locked()
            self._cond.notify()

    async def _shutdown_task(self) -> None:
        """Stop the worker as part of app shutdown.

        Registered via :meth:`~babase.App.add_shutdown_task` rather
        than :func:`babase.atexit` so the thread is gone before the
        engine's end-of-run check for stray threads -- atexit runs
        after it, so a still-running worker showed up there as an
        "unexpected thread".
        """
        import asyncio

        with self._cond:
            self._shutting_down = True
            thread = self._thread
            self._cond.notify()

        if thread is None:
            return

        # Join off the logic thread: the worker's final bounded send
        # attempt should not stall shutdown, and the join is bounded
        # regardless.
        await asyncio.get_running_loop().run_in_executor(
            None, thread.join, _SHUTDOWN_JOIN_SECONDS
        )

    def _set_account(self, account: AccountV2Handle | None) -> None:
        """Note the current primary account. Logic thread only."""
        assert _babase.in_logic_thread()
        with self._cond:
            self._account = account

    def _stopping_locked(self) -> bool:
        """Whether shutdown has been requested. Caller holds the lock.

        A method rather than a bare attribute read on purpose: the flag
        is set from another thread, so a checked-once-stays-false
        assumption is wrong (and mypy makes exactly that assumption
        when narrowing a plain attribute across statements).
        """
        return self._shutting_down

    def _ensure_thread_locked(self) -> None:
        """Spin up the worker if it isn't running. Caller holds the lock.

        Started lazily so a run that never trips a trigger never pays
        for a thread at all.
        """
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._worker_main,
            name='logreport',
            daemon=True,
        )
        self._thread.start()

    def _worker_main(self) -> None:
        """Worker loop: ship window slices until the window completes."""
        while True:
            with self._cond:
                if self._stopping_locked():
                    break

                wait = self._seconds_until_ready_locked()
                if wait is None:
                    # Nothing to do; sleep until notified.
                    self._cond.wait()
                    continue
                if wait > 0.0:
                    self._cond.wait(timeout=wait)
                    continue

                # Ready for a gather/send attempt. Snapshot what we
                # need and drop the lock -- gathering and sending must
                # not hold it. (Reading the window outside the lock
                # after this is fine; we are its only mutator once it
                # exists.)
                window = self._window
                trigger_level = self._trigger_level
                trigger_phrase = self._trigger_phrase
                assert window is not None
                assert trigger_level is not None

            archive = self._gather_and_send(
                window,
                trigger_level,
                trigger_phrase,
                wait_seconds=None,
            )

            with self._cond:
                if self._stopping_locked():
                    break
                if archive is None:
                    # Most likely no transport yet. Try again shortly;
                    # a slice that arrives late still beats one that
                    # never does.
                    self._next_attempt_time = (
                        time.monotonic() + _RETRY_INTERVAL_SECONDS
                    )
                    continue

                window.advance(archive.start_index, len(archive.entries))
                if window.complete:
                    # Everything the window covers has shipped.
                    self._done = True
                    return

                # Check back in a bit for freshly-logged entries.
                self._next_attempt_time = (
                    time.monotonic() + _FLUSH_INTERVAL_SECONDS
                )

        # Shutting down; get in one last bounded-time flush attempt if
        # the window still owes entries.
        self._final_flush()

    def _seconds_until_ready_locked(self) -> float | None:
        """How long until the next attempt, or None if there's nothing to.

        Caller holds the lock.
        """
        if self._window is None or self._done:
            return None
        assert self._next_attempt_time is not None
        return max(0.0, self._next_attempt_time - time.monotonic())

    def _final_flush(self) -> None:
        """Attempt one last send of any unshipped entries at shutdown.

        Runs on the worker thread. Bounded: gives the send
        _SHUTDOWN_SEND_SECONDS and then abandons it, so shutdown's
        thread-join budget always holds. Failures here are quietly
        dropped -- shutdown is no place for retries.
        """
        with self._cond:
            if self._window is None or self._done:
                return
            window = self._window
            trigger_level = self._trigger_level
            trigger_phrase = self._trigger_phrase
            assert trigger_level is not None

        self._gather_and_send(
            window,
            trigger_level,
            trigger_phrase,
            wait_seconds=_SHUTDOWN_SEND_SECONDS,
        )

    def _gather_and_send(
        self,
        window: LogReportWindow,
        trigger_level: LogLevel,
        trigger_phrase: str | None,
        *,
        wait_seconds: float | None,
    ) -> LogArchive | None:
        """Gather a window slice and ship it. Runs on the worker thread.

        Returns the gathered archive on success so the caller can
        advance past exactly what shipped (an empty archive counts as
        success and simply means nothing new to send yet). Returns
        None when the slice could not be delivered and should be
        retried later. ``wait_seconds`` bounds the send's round-trip
        wait; None waits indefinitely.
        """
        archive: LogArchive | None = None
        try:
            plus = _babase.app.plus
            if plus is None or not plus.cloud.is_connected():
                return None

            start_index, max_entries = window.gather_args()
            archive = self._log_handler.get_cached(
                start_index=start_index, max_entries=max_entries
            )

            # Entries the window still owed that the cache evicted
            # before we could gather them. Shipped in the report so
            # the receiver can mark the gap explicitly - a hole in
            # the record must never read as a quiet moment. (A slice
            # that is *only* a gap notification still ships; there is
            # nothing to retry later that could fill it.)
            entries_lost = window.evicted_count(archive.start_index)
            if not archive.entries and not entries_lost:
                # Nothing new to say.
                return archive

            payload = self._compress(archive)

            import bacommon.cloud

            # Our own clock goes along so the receiver can spot a
            # wrong one and shift our entry times onto its timeline
            # rather than filing them wherever our clock claims.
            report = bacommon.cloud.ClientLogReportMessage(
                archive_zstd=payload,
                trigger_level=trigger_level,
                trigger_phrase=trigger_phrase,
                entries_lost=entries_lost,
                client_time=utc_now(),
            )

            # Send under the account when we have one so the report is
            # attributable, and plainly when we don't -- reports from
            # signed-out clients are still worth having. Passing the
            # handle across threads like this is the same shape
            # _workspace.py uses for its background sync.
            with self._cond:
                account = self._account
            if account is not None:
                with account:
                    fut = plus.cloud.send_message_future(report)
            else:
                fut = plus.cloud.send_message_future(report)

            # The send only counts once its round trip completes;
            # advancing on anything less would let a dropped slice
            # vanish silently.
            fut.result(timeout=wait_seconds)
            return archive
        except (CommunicationError, TimeoutError) as exc:
            # Routine transport trouble; the slice stays owed and a
            # later attempt re-sends it. Strip tracebacks since we're
            # the terminal consumer: the send future's exception
            # otherwise retains frames whose locals reach back to it
            # (and to the whole transport-session graph at shutdown),
            # leaving cycles only cyclic gc can break.
            strip_exception_tracebacks(exc)
            return None
        except Exception as exc:
            # Note this goes to our own logger, which handle_log_entry
            # ignores -- so a failure here cannot trip another report.
            logreportlog.exception('Error shipping log report.')

            # Non-transport errors are likely deterministic for this
            # slice, so retrying would loop forever; skip past it if
            # we managed to gather one.
            strip_exception_tracebacks(exc)
            return archive

    def _compress(self, archive: LogArchive) -> bytes:
        """Serialize and zstd-compress an archive."""
        from compression import zstd
        from efro.dataclassio import dataclass_to_dict

        raw = json.dumps(
            dataclass_to_dict(archive), separators=(',', ':')
        ).encode()
        return zstd.compress(raw)
