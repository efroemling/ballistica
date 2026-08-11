# Released under the MIT License. See LICENSE for details.
#
"""Shared bits for triggered client log reporting.

The server hands a client a :class:`LogReportSpec` (via transient
cloud-vals) describing when to trip a log report and how much
surrounding context to ship. The client then ships the resulting
entry range incrementally, tracking its progress with a
:class:`LogReportWindow`.

Everything here is pure logic shared by the client reporter, the
server's ingest path, and tests; nothing engine-specific belongs in
this module.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from efro.logging import LogLevel
from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    from efro.logging import LogArchive


@ioprepped
@dataclass
class LogReportSpec:
    """When a client should ship log history, and how much of it.

    An entry trips the report if it matches *either* the level
    trigger or any phrase trigger (the two OR together, and each is
    optional). A spec with neither is inactive. There is no
    re-arming: a client reports at most one triggered window per app
    run.
    """

    #: Trip when an entry at or above this level is logged, or None
    #: to disable level triggering (phrases may still trip).
    trigger_level: Annotated[
        LogLevel | None, IOAttrs('tl', store_default=False)
    ] = None

    #: Trip when an entry's message contains any of these substrings
    #: (case-sensitive; ORed together and with the level trigger).
    #: Keep these few and plain - each is tested against every log
    #: message on targeted clients.
    trigger_phrases: Annotated[
        list[str], IOAttrs('tp', store_default=False)
    ] = field(default_factory=list)

    #: Max entries preceding the trigger to include, or None to
    #: include everything still in the client's log cache. Composes
    #: with the cache's own size limit; the smaller set wins.
    max_before_entries: Annotated[
        int | None, IOAttrs('mb', store_default=False)
    ] = None

    #: Max entries after the trigger to ship, or None to keep
    #: shipping new entries for the remainder of the run.
    max_after_entries: Annotated[
        int | None, IOAttrs('ma', store_default=False)
    ] = None

    @property
    def active(self) -> bool:
        """Whether this spec can ever trip (has any trigger)."""
        return self.trigger_level is not None or bool(self.trigger_phrases)

    def match_entry(
        self, level: LogLevel, message: str
    ) -> tuple[bool, str | None]:
        """Test an entry against our triggers.

        Returns ``(matched, phrase)`` where ``phrase`` is the
        trigger phrase that matched or None if the level trigger
        (or nothing) did. Runs on the client's log-handling thread
        for every entry once reporting is enabled, so it stays a
        couple of comparisons.
        """
        if (
            self.trigger_level is not None
            and level.value >= self.trigger_level.value
        ):
            return (True, None)
        for phrase in self.trigger_phrases:
            if phrase in message:
                return (True, phrase)
        return (False, None)


@dataclass
class LogReportWindow:
    """The entry-index range a tripped report ships, and its progress.

    Indices are the log cache's absolute entry indices (see
    :class:`~efro.logging.LogArchive`). ``cursor`` is the next index
    not yet confirmed delivered; it only ever advances after a
    confirmed send, so a failed send leaves the range to be re-sent
    (the server dedupes overlap by index).
    """

    #: First index to ship.
    start: int

    #: Index to stop shipping at (exclusive), or None to keep
    #: shipping for the rest of the run.
    end: int | None

    #: Next index not yet confirmed delivered.
    cursor: int

    @classmethod
    def from_trigger(
        cls, trigger_index: int, spec: LogReportSpec
    ) -> 'LogReportWindow':
        """Build the window for a trigger at the given entry index.

        The window covers up to ``max_before_entries`` entries before
        the trigger, the triggering entry itself, and up to
        ``max_after_entries`` after it. The before side is a request,
        not a promise: entries already evicted from the client's log
        cache simply won't be there to gather.
        """
        start = (
            0
            if spec.max_before_entries is None
            else max(0, trigger_index - spec.max_before_entries)
        )
        end = (
            None
            if spec.max_after_entries is None
            else trigger_index + 1 + spec.max_after_entries
        )
        return cls(start=start, end=end, cursor=start)

    def gather_args(self) -> tuple[int, int | None]:
        """Return ``(start_index, max_entries)`` for the next gather.

        Suitable for passing to
        :meth:`~efro.logging.LogHandler.get_cached`.
        """
        if self.end is None:
            return (self.cursor, None)
        return (self.cursor, max(0, self.end - self.cursor))

    def advance(self, archive_start_index: int, entry_count: int) -> None:
        """Advance the cursor past a confirmed-delivered archive slice.

        Uses the archive's own start index rather than assuming it
        matches the cursor - cache eviction can hand back a slice
        starting later than asked for.
        """
        self.cursor = max(self.cursor, archive_start_index + entry_count)

    def evicted_count(self, archive_start_index: int) -> int:
        """How many window entries a gather revealed as lost.

        A gather handing back a slice starting past the cursor means
        entries the window still owed were evicted from the cache
        before they could ship. Returns how many, counting only
        entries the window actually covered (a bounded window ends at
        ``end`` no matter how far past it the cache start moved).
        Call before :meth:`advance` (which moves the cursor past the
        gap).
        """
        reachable = (
            archive_start_index
            if self.end is None
            else min(archive_start_index, self.end)
        )
        return max(0, reachable - self.cursor)

    @property
    def complete(self) -> bool:
        """Whether everything this window covers has been delivered."""
        return self.end is not None and self.cursor >= self.end


def trim_archive_overlap(archive: LogArchive, next_expected_index: int) -> int:
    """Drop leading archive entries at indices before ``next_expected_index``.

    Server-side dedup helper: a client re-sends its unacknowledged
    range after a failed send, so a receiver that remembers the next
    index it expects from an app instance can trim the overlap here.
    Mutates ``archive`` in place and returns the number of entries
    dropped.
    """
    drop = min(
        len(archive.entries), max(0, next_expected_index - archive.start_index)
    )
    if drop:
        archive.entries = archive.entries[drop:]
        archive.start_index += drop
    return drop
