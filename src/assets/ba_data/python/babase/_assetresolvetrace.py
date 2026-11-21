# Released under the MIT License. See LICENSE for details.
#
"""Where an asset resolve's time goes, for diagnosing slow resolves.

Resolves are serialized, so a slow one stalls everything queued behind
it -- including UI that is just waiting to show a page. When that
happens in the field, the one log line that reaches us has to say on
its own *why*: no connection (node waits, not-connected attempts), a
struggling server (``INTERNAL`` errors, long build polls), or simply a
big download. :class:`ResolveTrace` gathers exactly that per resolve;
:class:`~babase.AssetSubsystem` keeps one for the running resolve and
logs its summary when a resolve is slow or troubled.
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum
    from bacommon.assetcas import CasDownloadStats

#: A resolve taking at least this long (from request to finish) gets a
#: summary line logged; see :meth:`ResolveTrace.summary_level_name`.
SLOW_RESOLVE_SECONDS = 10.0

#: Queue wait (behind other resolves) that alone counts as troubled.
_TROUBLED_QUEUE_SECONDS = 5.0

#: A resolve that downloaded nothing yet took at least this long (once
#: through the queue) gets its stages logged; see
#: :class:`LocalResolveTimes`.
SLOW_LOCAL_RESOLVE_SECONDS = 1.0

#: Slow-local-resolve reports logged per run, at most. A slow device
#: would otherwise log one for every package it resolves.
_MAX_LOCAL_REPORTS = 5

_g_local_report_count = 0


@dataclass
class LocalResolveTimes:
    """Where a resolve that needed no downloads spent its time.

    Such a resolve touches only this device: a scan of what is on disk,
    a registration with the engine, a rebuild of the string table and a
    manifest write. It should take a fraction of a second. When it
    doesn't, the cause is local -- slow storage, a busy thread pool, a
    busy logic thread -- and which of those shows in how each stage's
    time splits between waiting for a pool thread, running, and getting
    back onto the logic thread afterwards.

    A stage's run time is further told apart by its cpu time and, for
    the scan, its blob-check time:

    - Cpu close to the run time: the stage really had that much to do.
    - Little cpu, but blob checks account for the run: slow storage.
    - Little cpu and quick blob checks: the thread spent the run
      waiting to execute at all. Python code on a pool thread only
      advances while the logic thread (or other Python threads) leave
      the interpreter free, so a busy logic thread stretches it.
    """

    #: ``(stage, pool wait, run, cpu, wake)`` for each stage run on the
    #: pool. ``cpu`` is how much of ``run`` the thread was executing.
    pooled: list[tuple[str, float, float, float, float]] = field(
        default_factory=list
    )

    #: ``(stage, seconds)`` for each stage run on the logic thread.
    inline: list[tuple[str, float]] = field(default_factory=list)

    #: Data blobs the scan checked for on disk, and how long that took
    #: in all (wall time, so it includes waiting on storage).
    blob_checks: int = 0
    blob_check_seconds: float = 0.0

    def summary(
        self,
        label: str,
        apvernums: list[ApverNum],
        seconds: float,
        *,
        pool: str,
        modding: str,
    ) -> str | None:
        """A one-line account, or None if this one isn't worth logging.

        ``pool`` describes the app threadpool's current load and
        ``modding`` what user code this run carries.
        """
        global _g_local_report_count  # pylint: disable=global-statement

        if (
            seconds < SLOW_LOCAL_RESOLVE_SECONDS
            or _g_local_report_count >= _MAX_LOCAL_REPORTS
        ):
            return None
        _g_local_report_count += 1
        stages = [
            f'{name} {run:.2f}s (cpu {cpu:.2f}s, pool wait {wait:.2f}s,'
            f' wake {wake:.2f}s)'
            for name, wait, run, cpu, wake in self.pooled
        ] + [f'{name} {secs:.2f}s (logic thread)' for name, secs in self.inline]
        if self.blob_checks:
            stages.append(
                f'{self.blob_checks} blob check(s) in the scan'
                f' {self.blob_check_seconds:.2f}s'
            )
        return (
            f"Asset resolve '{label}' took {seconds:.2f}s with nothing to"
            f' download ({len(apvernums)} pkg(s): {apvernums}): '
            + '; '.join(stages)
            + f'. App threadpool: {pool}. Modding: {modding}.'
            + (
                ' (Further slow-local-resolve reports are suppressed'
                ' this run.)'
                if _g_local_report_count >= _MAX_LOCAL_REPORTS
                else ''
            )
        )


@dataclass
class Tier1Attempt:
    """One Tier-1 resolve attempt for one package."""

    apvernum: ApverNum
    attempt: int
    seconds: float
    #: 'ok', or a short failure description.
    outcome: str


@dataclass
class BlobAttempt:
    """One attempt at downloading one CAS blob.

    :meta private:
    """

    #: 'ok', or the failure's kind (see
    #: ``bacommon.assetcas.classify_download_error``).
    outcome: str
    #: Whether it connected to the transport's address (skipping a DNS
    #: lookup) rather than looking the node's host up.
    via_address: bool
    seconds: float
    bytes_received: int
    content_length: int | None

    @classmethod
    def make(
        cls,
        outcome: str,
        via_address: bool,
        started: float,
        stats: CasDownloadStats,
    ) -> BlobAttempt:
        """An attempt that started at ``started`` (monotonic) and just ended."""
        return cls(
            outcome=outcome,
            via_address=via_address,
            seconds=time.monotonic() - started,
            bytes_received=stats.bytes_received,
            content_length=stats.content_length,
        )


def describe_blob_attempts(attempts: list[BlobAttempt]) -> str:
    """Blob attempts in brief: ``#1 dns via ip 0.1s 0/12345B; ...``.

    :meta private:
    """
    parts: list[str] = []
    for i, att in enumerate(attempts):
        total = '?' if att.content_length is None else str(att.content_length)
        via = 'ip' if att.via_address else 'dns'
        parts.append(
            f'#{i + 1} {att.outcome} via {via}'
            f' {att.seconds:.1f}s {att.bytes_received}/{total}B'
        )
    return '; '.join(parts)


@dataclass
class ResolveTrace:
    """Timing and outcome bookkeeping for one gated resolve.

    Written on the logic thread only (resolve coroutines run there);
    :meth:`describe_now` may be read from any thread as a best-effort
    snapshot.
    """

    label: str
    apvernums: list[ApverNum]
    background: bool
    requested_at: float = field(default_factory=time.monotonic)
    admitted_at: float | None = None
    finished_at: float | None = None
    #: What the resolve is doing right now (free-form, short).
    phase: str = 'queued'
    #: 'ok', 'failed: ...', 'cancelled', or None while running.
    outcome: str | None = None
    #: Wall-clock time with at least one package waiting for the node
    #: (packages wait in parallel, so per-wait times would overcount).
    node_wait_seconds: float = 0.0
    node_wait_timeouts: int = 0
    node_waiters: int = 0
    node_wait_since: float | None = None
    tier1_attempts: list[Tier1Attempt] = field(default_factory=list)
    build_poll_seconds: float = 0.0
    fetch_bytes: int = 0
    #: Blob downloads that succeeded, and failed for good.
    blobs_ok: int = 0
    blobs_failed: int = 0
    #: Blob downloads that needed more than one attempt (either way).
    blobs_retried: int = 0
    #: Blob downloads that went to the transport's address.
    blobs_via_address: int = 0
    #: Failed blob-download attempts by kind (dns, read-timeout, ...).
    blob_failure_kinds: dict[str, int] = field(default_factory=dict)
    fetch_started_at: float | None = None
    fetch_seconds: float = 0.0
    network_available_start: bool | None = None
    transport_connected_start: bool | None = None
    network_available_end: bool | None = None
    transport_connected_end: bool | None = None

    def admitted(self) -> None:
        """Note admission through the serial gate."""
        self.admitted_at = time.monotonic()
        self.phase = 'starting'

    def node_wait_begin(self) -> None:
        """Note one package starting to wait for the node."""
        if self.node_waiters == 0:
            self.node_wait_since = time.monotonic()
        self.node_waiters += 1
        self.phase = 'waiting for node'

    def node_wait_end(self, timed_out: bool) -> None:
        """Note one package done waiting for the node."""
        self.node_waiters -= 1
        if timed_out:
            self.node_wait_timeouts += 1
        if self.node_waiters == 0 and self.node_wait_since is not None:
            self.node_wait_seconds += time.monotonic() - self.node_wait_since
            self.node_wait_since = None

    def blob_done(self, attempts: list[BlobAttempt], ok: bool) -> None:
        """Note one blob download finished, and how its attempts went."""
        if ok:
            self.blobs_ok += 1
        else:
            self.blobs_failed += 1
        if len(attempts) > 1:
            self.blobs_retried += 1
        if attempts and attempts[0].via_address:
            self.blobs_via_address += 1
        for att in attempts:
            if att.outcome != 'ok':
                self.blob_failure_kinds[att.outcome] = (
                    self.blob_failure_kinds.get(att.outcome, 0) + 1
                )

    def _blobs_summary(self) -> str:
        """Blob downloads in brief."""
        kinds = ', '.join(
            f'{kind} {count}'
            for kind, count in sorted(self.blob_failure_kinds.items())
        )
        return (
            f'blobs {self.blobs_ok} ok, {self.blobs_failed} failed,'
            f' {self.blobs_retried} retried, {self.blobs_via_address} via ip'
            + (f' (failed attempts: {kinds})' if kinds else '')
        )

    def _attempts_summary(self) -> str:
        """Tier-1 attempts grouped by attempt number and outcome."""
        groups: dict[tuple[int, str], list[float]] = {}
        for att in self.tier1_attempts:
            groups.setdefault((att.attempt, att.outcome), []).append(
                att.seconds
            )
        parts: list[str] = []
        for (attempt, outcome), secs in sorted(groups.items()):
            lo, hi = f'{min(secs):.1f}', f'{max(secs):.1f}'
            span = f'{lo}s' if lo == hi else f'{lo}-{hi}s'
            parts.append(f'#{attempt} {len(secs)}x {outcome} {span}')
        return ', '.join(parts) or 'none'

    def finished(self, outcome: str) -> None:
        """Note the resolve's end and how it went."""
        self.finished_at = time.monotonic()
        self.outcome = outcome
        if self.fetch_started_at is not None:
            self.fetch_seconds = self.finished_at - self.fetch_started_at

    @property
    def queue_seconds(self) -> float:
        """Time spent waiting behind other resolves."""
        end = (
            self.admitted_at
            if self.admitted_at is not None
            else (
                self.finished_at
                if self.finished_at is not None
                else time.monotonic()
            )
        )
        return end - self.requested_at

    @property
    def total_seconds(self) -> float:
        """Time from request to finish (or to now, while running)."""
        end = (
            self.finished_at
            if self.finished_at is not None
            else time.monotonic()
        )
        return end - self.requested_at

    def troubled(self) -> bool:
        """Did anything other than plain work slow this resolve down?"""
        return (
            self.node_wait_timeouts > 0
            or any(a.outcome != 'ok' for a in self.tier1_attempts)
            or bool(self.blob_failure_kinds)
            or self.queue_seconds >= _TROUBLED_QUEUE_SECONDS
            or (self.outcome is not None and self.outcome != 'ok')
        )

    def summary_level_name(self) -> str | None:
        """Log level for this resolve's summary, or None to skip it.

        Slow *and* troubled resolves get a WARNING, so the line reaches
        us in client log reports; slow but healthy ones (a big download
        on a slow link) only an INFO.
        """
        if self.total_seconds < SLOW_RESOLVE_SECONDS:
            return None
        return 'WARNING' if self.troubled() else 'INFO'

    def describe_now(self) -> str:
        """A one-line snapshot of where this resolve stands."""
        state = (
            f'queued {self.queue_seconds:.1f}s'
            if self.admitted_at is None
            else f'{self.phase}, {self.total_seconds:.1f}s in'
        )
        return (
            f"'{self.label}' ({len(self.apvernums)} pkg(s), {state},"
            f' node-wait {self.node_wait_seconds:.1f}s'
            f' ({self.node_wait_timeouts} timeout(s)),'
            f' {len(self.tier1_attempts)} tier-1 attempt(s))'
        )

    def summary(self) -> str:
        """A one-line account of where the resolve's time went."""
        attempts = self._attempts_summary()
        return (
            f"Asset resolve '{self.label}' {self.outcome or 'running'}"
            f' after {self.total_seconds:.1f}s'
            f' ({len(self.apvernums)} pkg(s): {self.apvernums}):'
            f' queued {self.queue_seconds:.1f}s;'
            f' node-wait {self.node_wait_seconds:.1f}s'
            f' ({self.node_wait_timeouts} timeout(s));'
            f' tier-1 attempts [{attempts}];'
            f' build-poll {self.build_poll_seconds:.1f}s;'
            f' fetched {self.fetch_bytes} bytes in'
            f' {self.fetch_seconds:.1f}s;'
            f' {self._blobs_summary()};'
            f' network available {self.network_available_start}'
            f'->{self.network_available_end},'
            f' transport connected {self.transport_connected_start}'
            f'->{self.transport_connected_end}.'
        )
