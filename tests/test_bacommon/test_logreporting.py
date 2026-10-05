# Released under the MIT License. See LICENSE for details.
#
"""Tests for bacommon.logreporting.

Covers the pure logic the client log-reporter and the server ingest
path share: trigger matching, pre/post window-limit math, cursor
advancement, and overlap trimming. The threaded reporter machinery
itself lives client-side and is exercised by running the app; these
tests pin down the semantics it delegates to.
"""

import datetime

from efro.logging import LogLevel, LogEntry, LogArchive
from bacommon.logreporting import (
    LogReportSpec,
    LogReportWindow,
    trim_archive_overlap,
)


def _entry(message: str, level: LogLevel = LogLevel.INFO) -> LogEntry:
    return LogEntry(
        name='test',
        message=message,
        level=level,
        time=datetime.datetime.now(datetime.UTC),
    )


def _archive(start_index: int, count: int, log_size: int) -> LogArchive:
    return LogArchive(
        log_size=log_size,
        start_index=start_index,
        entries=[_entry(f'entry {start_index + i}') for i in range(count)],
    )


def test_spec_active() -> None:
    """Specs with no trigger at all can never trip."""
    assert not LogReportSpec().active
    assert LogReportSpec(trigger_level=LogLevel.WARNING).active
    assert LogReportSpec(trigger_phrases=['boom']).active


def test_match_by_level() -> None:
    """Level triggers fire at and above their level only."""
    spec = LogReportSpec(trigger_level=LogLevel.WARNING)
    assert spec.match_entry(LogLevel.WARNING, 'x') == (True, None)
    assert spec.match_entry(LogLevel.ERROR, 'x') == (True, None)
    assert spec.match_entry(LogLevel.INFO, 'x') == (False, None)


def test_match_by_phrase() -> None:
    """Phrase triggers fire on substring match regardless of level."""
    spec = LogReportSpec(trigger_phrases=['bad thing', 'other thing'])
    assert spec.match_entry(LogLevel.DEBUG, 'a bad thing happened') == (
        True,
        'bad thing',
    )
    assert spec.match_entry(LogLevel.ERROR, 'all is well') == (False, None)
    assert spec.match_entry(LogLevel.DEBUG, 'some other thing') == (
        True,
        'other thing',
    )


def test_match_level_and_phrase_or_together() -> None:
    """Level and phrase triggers OR; level match reports no phrase."""
    spec = LogReportSpec(
        trigger_level=LogLevel.ERROR, trigger_phrases=['needle']
    )
    # Phrase fires below the level threshold.
    assert spec.match_entry(LogLevel.DEBUG, 'has needle') == (True, 'needle')
    # Level fires without a phrase (checked first even if a phrase
    # is also present).
    assert spec.match_entry(LogLevel.ERROR, 'has needle') == (True, None)
    assert spec.match_entry(LogLevel.INFO, 'nothing here') == (False, None)


def test_window_both_limits() -> None:
    """Before/after limits bound the window on each side of the trigger."""
    spec = LogReportSpec(
        trigger_level=LogLevel.WARNING,
        max_before_entries=10,
        max_after_entries=5,
    )
    window = LogReportWindow.from_trigger(100, spec)
    # 10 before, the trigger itself, 5 after.
    assert window.start == 90
    assert window.end == 106
    assert window.cursor == 90
    assert window.gather_args() == (90, 16)
    assert not window.complete


def test_window_unlimited_before() -> None:
    """max_before_entries=None asks for everything back to the start."""
    spec = LogReportSpec(trigger_level=LogLevel.WARNING, max_after_entries=0)
    window = LogReportWindow.from_trigger(100, spec)
    assert window.start == 0
    assert window.end == 101
    assert window.gather_args() == (0, 101)


def test_window_unlimited_after() -> None:
    """max_after_entries=None keeps the window open indefinitely."""
    spec = LogReportSpec(trigger_level=LogLevel.WARNING, max_before_entries=2)
    window = LogReportWindow.from_trigger(100, spec)
    assert window.end is None
    assert window.gather_args() == (98, None)
    window.advance(98, 1000)
    assert not window.complete  # Never completes on its own.


def test_window_before_clamps_at_zero() -> None:
    """A before-limit larger than available history clamps to index 0."""
    spec = LogReportSpec(
        trigger_level=LogLevel.WARNING,
        max_before_entries=10,
        max_after_entries=0,
    )
    window = LogReportWindow.from_trigger(3, spec)
    assert window.start == 0
    assert window.end == 4


def test_window_incremental_delivery() -> None:
    """The cursor walks the window across multiple confirmed sends."""
    spec = LogReportSpec(
        trigger_level=LogLevel.WARNING,
        max_before_entries=10,
        max_after_entries=5,
    )
    window = LogReportWindow.from_trigger(100, spec)

    # First slice: pre-roll plus trigger (nothing after it exists yet).
    window.advance(90, 11)
    assert window.cursor == 101
    assert not window.complete
    assert window.gather_args() == (101, 5)

    # Post-trigger entries arrive and ship in two batches.
    window.advance(101, 3)
    assert window.gather_args() == (104, 2)
    window.advance(104, 2)
    assert window.complete


def test_window_advance_handles_eviction() -> None:
    """A gather that starts later than asked (eviction) still advances."""
    spec = LogReportSpec(
        trigger_level=LogLevel.WARNING,
        max_before_entries=50,
        max_after_entries=5,
    )
    window = LogReportWindow.from_trigger(100, spec)
    assert window.cursor == 50
    # Cache had already evicted entries 50-79; the archive we got
    # back starts at 80.
    window.advance(80, 21)
    assert window.cursor == 101

    # An advance that lands before the cursor (shouldn't happen, but)
    # never moves it backwards.
    window.advance(0, 3)
    assert window.cursor == 101


def test_window_empty_advance() -> None:
    """An empty gather leaves the cursor untouched."""
    spec = LogReportSpec(trigger_level=LogLevel.WARNING, max_after_entries=5)
    window = LogReportWindow.from_trigger(100, spec)
    cursor = window.cursor
    # get_cached clamps an out-of-range start down to log size and
    # returns no entries.
    window.advance(cursor, 0)
    assert window.cursor == cursor


def test_window_evicted_count() -> None:
    """Eviction gaps are counted, capped at the window's own end."""
    spec = LogReportSpec(
        trigger_level=LogLevel.WARNING,
        max_before_entries=50,
        max_after_entries=5,
    )
    window = LogReportWindow.from_trigger(100, spec)
    assert window.cursor == 50

    # Archive starts right where asked: nothing lost.
    assert window.evicted_count(50) == 0

    # Archive starts later: the difference was evicted.
    assert window.evicted_count(80) == 30

    # Cache start blew past the whole (bounded) window: only entries
    # the window covered count as lost.
    assert window.end == 106
    assert window.evicted_count(300) == 56

    # Unbounded windows count the full gap.
    spec_unbounded = LogReportSpec(
        trigger_level=LogLevel.WARNING, max_before_entries=50
    )
    window2 = LogReportWindow.from_trigger(100, spec_unbounded)
    assert window2.evicted_count(300) == 250

    # After a partial delivery the cursor has moved; only the
    # still-owed range counts.
    window.advance(50, 20)  # Delivered 50-69.
    assert window.evicted_count(90) == 20


def test_trim_archive_overlap() -> None:
    """Overlap trimming drops exactly the already-seen leading entries."""
    # No overlap: nothing dropped.
    archive = _archive(start_index=10, count=5, log_size=15)
    assert trim_archive_overlap(archive, 10) == 0
    assert archive.start_index == 10
    assert len(archive.entries) == 5

    # next-expected below the archive start: nothing dropped.
    archive = _archive(start_index=10, count=5, log_size=15)
    assert trim_archive_overlap(archive, 5) == 0
    assert len(archive.entries) == 5

    # Partial overlap: leading entries drop and start shifts.
    archive = _archive(start_index=10, count=5, log_size=15)
    assert trim_archive_overlap(archive, 12) == 2
    assert archive.start_index == 12
    assert len(archive.entries) == 3
    assert archive.entries[0].message == 'entry 12'

    # Full overlap: everything drops.
    archive = _archive(start_index=10, count=5, log_size=15)
    assert trim_archive_overlap(archive, 20) == 5
    assert archive.start_index == 15
    assert not archive.entries
