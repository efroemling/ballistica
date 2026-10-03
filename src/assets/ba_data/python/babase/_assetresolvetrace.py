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

#: A resolve taking at least this long (from request to finish) gets a
#: summary line logged; see :meth:`ResolveTrace.summary_level_name`.
SLOW_RESOLVE_SECONDS = 10.0

#: Queue wait (behind other resolves) that alone counts as troubled.
_TROUBLED_QUEUE_SECONDS = 5.0


@dataclass
class Tier1Attempt:
    """One Tier-1 resolve attempt for one package."""

    apvernum: ApverNum
    attempt: int
    seconds: float
    #: 'ok', or a short failure description.
    outcome: str


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
            f' network available {self.network_available_start}'
            f'->{self.network_available_end},'
            f' transport connected {self.transport_connected_start}'
            f'->{self.transport_connected_end}.'
        )
