# Released under the MIT License. See LICENSE for details.
#
"""Shipping log history to the cloud after something goes wrong."""

import time
import json
import threading
from typing import TYPE_CHECKING

import _babase
from babase._logging import logreportlog
from babase._apputils import should_submit_debug_info

if TYPE_CHECKING:
    from typing import Callable

    from efro.call import CallbackRegistration
    from efro.logging import LogLevel, LogEntry, LogArchive, LogHandler

    from babase._accountv2 import AccountV2Handle

    import bacommon.cloud

#: How long to sleep between retries when we have a report ready but
#: cannot send it (no transport). Also the idle tick of the worker
#: thread, which is why it doubles as our connectivity poll -- there is
#: no edge notification to miss this way, just a state re-check.
_RETRY_INTERVAL_SECONDS = 10.0

#: Ceiling on how long shutdown waits for the worker. A send in flight
#: is not worth stalling app exit for; the thread is a daemon so the
#: process can leave without it if it overruns.
_SHUTDOWN_JOIN_SECONDS = 2.0


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
    """Ships a slice of our log history to the cloud after a bad log.

    Disabled unless the server turns it on for this client via
    :attr:`~bacommon.cloud.CloudValsTransient.log_report_min_level`, so
    the default state for the fleet is silence.

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

        # Config, copied from CloudValsTransient as it arrives.
        self._min_level: LogLevel | None = None
        self._arm_time = 2.0
        self._rearm_time: float | None = 600.0
        self._max_entries: int | None = None

        # A trigger is waiting to be shipped; the level that caused it.
        self._pending_level: LogLevel | None = None

        # apptime-independent monotonic deadlines.
        self._send_after: float | None = None
        self._cooldown_until: float | None = None

        # Set once we have shipped and re-arming is disabled.
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

        with self._cond:
            self._min_level = vals.log_report_min_level
            self._arm_time = vals.log_report_arm_time.total_seconds()
            self._rearm_time = (
                None
                if vals.log_report_rearm_time is None
                else vals.log_report_rearm_time.total_seconds()
            )
            self._max_entries = vals.log_report_max_entries
            enabled = self._min_level is not None
            self._cond.notify()

        # Honor the user's debug-info preference. Nothing in the
        # current UI writes this, but it can still be sitting False in
        # a config.json from an older build that did expose it, and it
        # is consent for precisely this behavior -- so an explicit
        # opt-out keeps working rather than being quietly dropped along
        # with the v1 log path that used to check it.
        if enabled and not should_submit_debug_info():
            with self._cond:
                self._min_level = None
            enabled = False

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

        with self._cond:
            if self._done or self._shutting_down:
                return

            min_level = self._min_level
            if min_level is None or entry.level.value < min_level.value:
                return

            # Already waiting to ship; this entry will be included in
            # that report anyway, so nothing to do.
            if self._pending_level is not None:
                return

            self._pending_level = entry.level
            self._send_after = time.monotonic() + self._arm_time
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

        # Join off the logic thread: a send in flight should not stall
        # shutdown, and the join is bounded regardless.
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

        Started lazily so a run that never logs a warning never pays for
        a thread at all.
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
        """Worker loop: wait for work, then ship it."""
        while True:
            with self._cond:
                if self._stopping_locked():
                    return

                wait = self._seconds_until_ready_locked()
                if wait is None:
                    # Nothing to do; sleep until notified.
                    self._cond.wait()
                    continue
                if wait > 0.0:
                    self._cond.wait(timeout=wait)
                    continue

                # Ready to ship. Snapshot what we need and drop the
                # lock -- gathering and sending must not hold it.
                level = self._pending_level
                max_entries = self._max_entries
                assert level is not None

            sent = self._build_and_send(level, max_entries)

            with self._cond:
                if self._stopping_locked():
                    return
                if not sent:
                    # Most likely no transport yet. Keep the trigger
                    # pending and try again shortly; a report that
                    # arrives late still beats one that never does.
                    self._send_after = (
                        time.monotonic() + _RETRY_INTERVAL_SECONDS
                    )
                    continue

                self._pending_level = None
                self._send_after = None
                if self._rearm_time is None:
                    # One report per run.
                    self._done = True
                    return
                self._cooldown_until = time.monotonic() + self._rearm_time

    def _seconds_until_ready_locked(self) -> float | None:
        """How long until we may ship, or None if there's nothing to.

        Caller holds the lock.
        """
        if self._pending_level is None:
            return None

        now = time.monotonic()
        deadlines = [self._send_after or 0.0]

        # A trigger that landed during a cooldown waits it out rather
        # than being dropped, then goes immediately.
        if self._cooldown_until is not None:
            if now >= self._cooldown_until:
                self._cooldown_until = None
            else:
                deadlines.append(self._cooldown_until)

        return max(0.0, max(deadlines) - now)

    def _build_and_send(self, level: LogLevel, max_entries: int | None) -> bool:
        """Gather, compress and ship. Returns whether it went out.

        Runs on the worker thread with no lock held.
        """
        try:
            plus = _babase.app.plus
            if plus is None or not plus.cloud.is_connected():
                return False

            archive = self._gather(max_entries)
            if archive is None or not archive.entries:
                # Nothing to say; treat as sent so we don't spin.
                return True

            payload = self._compress(archive)

            import bacommon.cloud

            report = bacommon.cloud.ClientLogReportMessage(
                archive_zstd=payload, trigger_level=level
            )

            # Blocking send from our own bg thread, which is exactly
            # what this send form wants. We ignore the result: there is
            # no response, and a failed report is not worth retrying
            # (the next trigger ships a superset of this history).
            #
            # Send under the account when we have one so the report is
            # attributable, and plainly when we don't -- reports from
            # signed-out clients are still worth having. Passing the
            # handle across threads like this is the same shape
            # _workspace.py uses for its background sync.
            with self._cond:
                account = self._account
            if account is not None:
                with account:
                    plus.cloud.send_message(report)
            else:
                plus.cloud.send_message(report)
            return True
        except Exception:
            # Note this goes to our own logger, which handle_log_entry
            # ignores -- so a failure here cannot arm another report.
            logreportlog.exception('Error shipping log report.')
            return True

    def _gather(self, max_entries: int | None) -> LogArchive | None:
        """Pull the tail of the log cache as a LogArchive.

        Re-sends the whole cache each time rather than only what is
        new since the last report, so consecutive reports overlap.
        That is fine for now and buys something real: it is why a
        failed send needs no retry -- whatever a dropped report would
        have carried simply turns up in the next one.

        Worth revisiting if report volume ever makes the duplication
        cost real. The shape would be to ship from a last-sent marker
        and advance it only on a confirmed send, so a failure leaves
        the gap for the next report to cover rather than dropping it.
        :class:`~efro.logging.LogArchive` already carries ``log_size``
        and ``start_index``, so the receiver can tell what range it
        got either way.
        """
        log_handler = self._log_handler

        if max_entries is None:
            return log_handler.get_cached()

        # Ask for the size first (cheap -- an empty slice) so we can
        # start the real request at the right offset and get the most
        # recent entries rather than the oldest.
        size = log_handler.get_cached(start_index=0, max_entries=0).log_size
        return log_handler.get_cached(
            start_index=max(0, size - max_entries), max_entries=max_entries
        )

    def _compress(self, archive: LogArchive) -> bytes:
        """Serialize and zstd-compress an archive."""
        from compression import zstd
        from efro.dataclassio import dataclass_to_dict

        raw = json.dumps(
            dataclass_to_dict(archive), separators=(',', ':')
        ).encode()
        return zstd.compress(raw)
