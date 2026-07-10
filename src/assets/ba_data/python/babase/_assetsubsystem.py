# Released under the MIT License. See LICENSE for details.
#
"""The client-side asset-package subsystem (``app.assets``).

The runtime acquire/track/prune manager for downloadable asset packages
(initiative: asset-packages CAS migration, Phase 4). It consumes the
Tier-1 resolve message + Tier-2 ``/casblob`` transport (already built and
dev-validated) and turns it into the ``app.assets.resolve([apverids])``
contract: given a set of asset-package-version ids, make every one of
them available to the C++ asset layer — pulling any missing CAS blobs
from the connected basn node and committing the resolved packages into
the runtime registry.

This module implements build-order step 2 of the consolidated design:
the subsystem skeleton, the ``resolve()`` loop, the shared atomic
CAS-writer, and the two-location diff. GC/prune (step 3), fallback
policy + ``allow_downloads`` semantics (step 4), and real dimension
selection (step 5) layer on top of this in later steps.
"""

# This is a cohesive single-class subsystem (writable-CAS management,
# resolve loop, fallback policy, and GC), so it legitimately runs long;
# we keep it as one primary module rather than fracturing the class.
# pylint: disable=too-many-lines

import os
import json
import time
import asyncio
import tempfile
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Annotated, override

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import assetmanagerlog as logger

from efro.error import CommunicationError
from efro.util import strip_exception_tracebacks
from efro.dataclassio import (
    ioprepped,
    IOAttrs,
    dataclass_from_json,
    dataclass_to_json,
)
from bacommon.cloud import (
    ResolveAssetPackageMessage,
    ResolveAssetPackageResponse,
    AssetPackageResolveError,
)
from bacommon import assetcas

if TYPE_CHECKING:
    from collections.abc import Callable

    from bacommon import securedata
    from bacommon.cloud import AssetPackageBuildProgress
    from bacommon.locale import Locale
    from bacommon.loctext import StringSelector
    from babase._accountv2 import AccountV2Handle

#: Accumulated resolve output: ``(register_specs, manifest_pkgs, fell_back)``
#: where ``register_specs`` is ``[(apverid, coord, entries), ...]``,
#: ``manifest_pkgs`` is ``{apverid: {coord: fm_hash}}`` and ``fell_back`` is
#: ``{desired_coord: fallback_coord}``.
_ResolveAccum = tuple[
    list[tuple[str, str, dict[str, dict[str, str]]]],
    dict[str, dict[str, str]],
    dict[str, str],
]

#: Max concurrent CAS-blob downloads, run on a dedicated thread pool (NOT the
#: shared app threadpool). Each in-flight download buffers its whole blob in
#: RAM, so peak download memory is roughly this times blob-size -- a real
#: constraint on low-end Android (scarce RAM + an aggressive low-memory killer).
#: Set to 8 from measured numbers: a warm-node sweep showed near-linear speedup
#: through 4 and a further ~20% at 8 (download throughput still climbing, not
#: yet bandwidth-saturated), so 8 meaningfully cuts time-to-first-menu while
#: staying under the urllib3 pool's per-host maxsize (10) so connections get
#: reused rather than churned. Overridable via BA_BLOB_DOWNLOAD_CONCURRENCY for
#: testing; if you raise it past 10, bump that maxsize in _env.py to match.
_BLOB_DOWNLOAD_CONCURRENCY = int(
    os.environ.get('BA_BLOB_DOWNLOAD_CONCURRENCY', '8')
)

#: Per-request timeout for individual CAS-blob downloads. The shared
#: urllib3 pool's default total timeout (10s) is sized for small API
#: calls; blob fetches can legitimately take longer when the node is
#: cold for a blob (cache miss -> upstream fetch before headers) or the
#: link is slow, so they get their own more generous budget. Still a
#: *total* cap so a wedged request can't hang a resolve indefinitely.
_BLOB_DOWNLOAD_TIMEOUT_SECONDS = 60.0


def _init_blob_download_thread() -> None:
    """Name dedicated blob-download threads for profiling clarity."""
    _babase.set_thread_name('ballistica asset-dl')


#: Grace period a second resolve waits for an in-flight one to finish
#: before erroring out (single-in-flight guard).
_RESOLVE_GRACE_SECONDS = 5.0

#: How long a download leg waits for the connected node to come up before
#: giving up. Downloads route through the node, which connects a beat
#: after boot, so a resolve kicked at boot (e.g. construct-mode) would
#: otherwise race the connection. Only waited when a download is actually
#: needed (fully-local/bundled resolves never reach this).
_NODE_WAIT_SECONDS = 20.0

#: How long an asset-package may go untouched before GC may evict it.
#: A package/flavor-manifest survives a GC pass if it was registered
#: this process lifetime (pinned) or its ``last_used`` is within this
#: window. Pure-reachability data blobs ignore this (they live iff some
#: surviving flavor-manifest references them).
_GC_CUTOFF_SECONDS = 30.0 * 24.0 * 3600.0  # 30 days.

#: Self-imposed GC wall-clock budget. Kept under the shutdown-task
#: cancel (12s) / suicide (15s) so a slow sweep exits cleanly and
#: resumes next run rather than tripping the shutdown timeout path.
_GC_BUDGET_SECONDS = 8.0

#: How long the GC pass waits to acquire the single-in-flight guard
#: before skipping (best-effort; at shutdown nothing competes).
_GC_BUSY_TIMEOUT_SECONDS = 2.0

#: Number of single-level CAS shard dirs (first 2 hex chars of a hash).
_CAS_SHARD_COUNT = 256

#: The canonical asset-package buckets, in registration order. A bucket is
#: a delivery-variation coordinate (everything that varies together in how
#: it's delivered), not an asset-kind namespace -- so e.g. cube maps ride
#: 'textures' (same profile/render_space/tier dimensions as 2D textures)
#: and collision meshes ride 'constant'. See the bucketing-model rules in
#: the asset-packages design doc.
_BUCKETS = (
    'constant',
    'language',
    'textures',
    'audio',
    'meshes',
)

#: Per-bucket fallback flavor coord (or None) — used ONLY for the
#: builtin/projectconfig bootstrap package, whose fallbacks are
#: guaranteed bundled. Every other package is exact-or-fail. Single
#: fallback per bucket for now; :meth:`AssetSubsystem._fallback_coord`
#: wraps this so a fallback *chain* is a non-breaking later change.
_BUCKET_FALLBACKS: dict[str, str | None] = {
    'constant': None,  # No flavor dimension; 'constant' is always present.
    'language': 'language/eng',
    # Serves cube maps too -- they share the textures bucket (decision #24).
    'textures': 'textures/fallback_v1.gamma.regular',
    # vorbis_v1 is audio's only real profile (decision #25), so desired
    # == fallback for GUI builds today; this entry matters only if a
    # non-bundled audio dimension (e.g. an ultra tier) appears later.
    'audio': 'audio/vorbis_v1.regular',
    # Same story for meshes (decision #26): bob_v1 is the only real
    # profile, so desired == fallback for GUI builds today.
    'meshes': 'meshes/bob_v1.regular',
}


class AssetResolveError(Exception):
    """A call to :meth:`AssetSubsystem.resolve` failed.

    The resolve is all-or-nothing: when this is raised nothing was
    committed to the native asset registry (some CAS blobs may have
    landed on disk as harmless garbage that a later resolve reuses or
    GC reclaims).

    ``code`` carries the server's structured reason when the failure
    came from a Tier-1 resolve response, or ``None`` for client-side /
    transport failures.
    """

    def __init__(
        self,
        message: str,
        code: AssetPackageResolveError | None = None,
        server_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        #: The server's raw human-readable error (without the client-added
        #: ``apverid:`` prefix), when this came from a Tier-1 resolve
        #: response; else None. Lets callers surface the server's own
        #: wording (e.g. an access-denied message naming the account).
        self.server_message = server_message


class AssetAuthRequiredError(AssetResolveError):
    """Tier-1 resolve failed: a non-public version needs a signed-in account.

    Signing in with an account that has access (and retrying) may
    succeed. Raised when the server returns
    :attr:`~bacommon.cloud.AssetPackageResolveError.AUTH_REQUIRED`.
    """


class AssetAccessDeniedError(AssetResolveError):
    """Tier-1 resolve failed: the signed-in account lacks access.

    The account is authenticated but isn't the owner / on the package's
    dev team. Raised when the server returns
    :attr:`~bacommon.cloud.AssetPackageResolveError.ACCESS_DENIED`.
    """


class AssetClientTooOldError(AssetResolveError):
    """Tier-1 resolve refused: this app build is too old for current assets.

    The server's asset manifests use logical paths this build can't
    address; the user must update. Raised when the server returns
    :attr:`~bacommon.cloud.AssetPackageResolveError.CLIENT_TOO_OLD`.
    """


class AssetContentError(AssetResolveError):
    """Tier-1 resolve failed: the package's own source content is bad.

    The package failed to build due to a problem in its source assets
    (e.g. a malformed sound or texture file) — something the package
    author can fix. ``server_message`` names the offending source
    file(s), so surface it verbatim. Raised when the server returns
    :attr:`~bacommon.cloud.AssetPackageResolveError.CONTENT`.
    """


class AssetResolveAbortedError(AssetResolveError):
    """An asset-subsystem operation was abandoned because we're shutting down.

    Raised when off-thread work can no longer be dispatched because the
    app has begun shutting down (e.g. the threadpool was torn down out
    from under an in-flight resolve or GC). It is a benign, expected
    outcome -- not a real failure -- so callers should bow out quietly
    rather than logging it as an error.
    """


#: Which :class:`AssetResolveError` subclass a Tier-1 resolve raises for
#: each structured server code (codes without an entry get the base
#: class).
_RESOLVE_ERROR_TYPES: dict[
    AssetPackageResolveError, type[AssetResolveError]
] = {
    AssetPackageResolveError.AUTH_REQUIRED: AssetAuthRequiredError,
    AssetPackageResolveError.ACCESS_DENIED: AssetAccessDeniedError,
    AssetPackageResolveError.CLIENT_TOO_OLD: AssetClientTooOldError,
    AssetPackageResolveError.CONTENT: AssetContentError,
}


@dataclass
class _GcSweepStats:
    """Outcome of one GC sweep (internal)."""

    freed_files: int
    freed_bytes: int
    shards_done: int
    cut_off: bool
    next_shard: int
    sweep_secs: float


@dataclass
class _OneResult:
    """Per-apverid resolve outcome (internal)."""

    #: Chosen ``coord -> flavor-manifest hash`` to register for this package.
    coords: dict[str, str]
    #: Chosen ``coord -> {logical_path: {part: data-hash}}`` registry
    #: entries (part-keyed component files per logical asset; decision
    #: #16). A null asset is an empty part map ``{}``.
    entries: dict[str, dict[str, dict[str, str]]]
    #: Buckets that fell back: ``desired_coord -> chosen_fallback_coord``.
    fell_back: dict[str, str]


@dataclass
class ResolveResult:
    """Outcome of a successful :meth:`AssetSubsystem.resolve`."""

    #: The apverids that were resolved + committed.
    apverids: list[str]

    #: Buckets that fell back to a different flavor than requested,
    #: as ``coord -> flavor`` (always empty until step 4 lands the
    #: fallback policy; kept here so callers can wire UI/observability
    #: against it now).
    fell_back: dict[str, str] = field(default_factory=dict)


class ResolvePhase(Enum):
    """Coarse phase of an in-flight resolve, for progress feedback."""

    #: Talking to the server to resolve the requested flavor(s).
    RESOLVING = 'resolving'
    #: The server is assembling/compiling the package (not emitted by the
    #: client today -- a slot for the server to report build status into;
    #: see :attr:`ResolveProgress.detail`).
    BUILDING = 'building'
    #: Fetching data blobs from the connected node.
    DOWNLOADING = 'downloading'


@dataclass
class ResolveProgress:
    """A snapshot of an in-flight resolve, for progress feedback.

    Handed to the ``on_progress`` callback of :meth:`AssetSubsystem.resolve`
    (on the logic thread) whenever progress advances. Counts are cumulative
    across the whole resolve; the totals grow as each package's manifest
    reveals its blobs, so ``done``/``total`` is a moving target rather than a
    value known up front -- fine for a status line and good enough for a
    simple progress bar.

    Intentionally minimal scaffolding; a richer model can extend it later.
    """

    #: What the resolve is doing right now.
    phase: ResolvePhase = ResolvePhase.RESOLVING

    #: The package currently being resolved/downloaded, if any.
    apverid: str | None = None

    #: Optional human-readable status line. The allowance for the server to
    #: report what it's doing (e.g. ``'Compiling 5 assets…'``) during a
    #: resolve -- nothing populates it from the server yet (the Tier-1
    #: resolve is a single blocking request today), but consumers should
    #: prefer it over the phase when present so it lights up for free once
    #: the server-side reporting lands.
    detail: str | None = None

    #: Server-side build progress for the package currently building
    #: (the BUILDING phase): buckets built so far and the total for that
    #: one package. Per-package (the server builds one package at a time);
    #: ``None`` when not building or when the server hasn't reported counts
    #: yet (e.g. the initial 'preparing' sub-phase).
    build_units_done: int | None = None
    build_units_total: int | None = None

    #: Data blobs fetched so far, and the number known to need fetching.
    #: Unlike the build counts, these are a running total across ALL
    #: packages in the resolve (they only grow), so a single
    #: "N remaining" download readout spans the whole resolve.
    blobs_done: int = 0
    blobs_total: int = 0

    #: Bytes fetched so far, and the total of the blobs known to need
    #: fetching (from the manifests; the on-disk write may differ slightly).
    bytes_done: int = 0
    bytes_total: int = 0


#: Min seconds between throttled progress updates. The resolve emits one
#: event per blob / build-unit completed (see :meth:`_emit_progress`); this
#: caps how often those reach the dialog. Kept low (20/sec) so the meter
#: advances smoothly through a many-item resolve -- a ~500-blob download
#: otherwise batches into only a few visible jumps -- while still coalescing
#: a burst of fast-completing tiny blobs into at most one text-mesh rebuild
#: per tick. (Phase/package changes and the final caught-up frame bypass
#: the throttle entirely, so the bar still reaches 100%.)
_PROGRESS_UPDATE_INTERVAL = 0.05

#: Seconds between Tier-1 resolve polls while the server reports it's
#: still building the requested flavors.
_BUILD_POLL_INTERVAL_SECONDS = 1.0


def _package_display_name(apverid: str | None) -> str:
    """Package name from an apverid, for progress messages.

    ``a-0.babuiltinassets.dev260605g`` -> ``babuiltinassets``. Falls back
    to the raw apverid (or a generic word) if it isn't the expected
    ``account.package.version`` shape.
    """
    if not apverid:
        return 'package'
    parts = apverid.split('.')
    return parts[1] if len(parts) == 3 and parts[1] else apverid


def make_progress_reporter(
    on_update: Callable[[str, float | None], None],
) -> Callable[[ResolveProgress], None]:
    """Build a throttled progress reporter.

    Pass the returned callable as ``on_progress`` to
    :meth:`AssetSubsystem.resolve`. It calls ``on_update(message, progress)``
    immediately on a phase or package change and then at most once per
    :data:`_PROGRESS_UPDATE_INTERVAL` seconds (so a slow download keeps
    the user informed without spamming). ``progress`` is a ``0.0``–``1.0``
    fraction for a progress bar — ``0.0`` during phases with no known count
    (the bar is held at zero rather than hidden, so the display doesn't resize
    between phases). A server-provided :attr:`ResolveProgress.detail` is shown
    verbatim when present.
    """
    last_time = -1.0e9
    last_phase: ResolvePhase | None = None
    last_apverid: str | None = None

    def report(progress: ResolveProgress) -> None:
        nonlocal last_time, last_phase, last_apverid
        downloading = progress.phase is ResolvePhase.DOWNLOADING
        # Always let the "caught up" point through (e.g. the final X/X), even
        # under the throttle, so a quick download doesn't appear stuck at its
        # starting 0/X count.
        caught_up = (
            downloading
            and progress.blobs_total > 0
            and progress.blobs_done >= progress.blobs_total
        )
        now = _babase.apptime()
        # Update immediately on a phase change OR a package change (so a
        # per-package build line's package name updates promptly); else
        # throttle to avoid spamming a slow download.
        if (
            progress.phase is last_phase
            and progress.apverid == last_apverid
            and now - last_time < _PROGRESS_UPDATE_INTERVAL
            and not caught_up
        ):
            logger.debug(
                'progress: throttled update (phase=%s build=%s/%s'
                ' blobs=%d/%d apverid=%s)',
                progress.phase.value,
                progress.build_units_done,
                progress.build_units_total,
                progress.blobs_done,
                progress.blobs_total,
                progress.apverid,
            )
            return
        last_time = now
        last_phase = progress.phase
        last_apverid = progress.apverid

        # Build the message + bar fraction for this phase. A server-provided
        # detail is an escape hatch (unused by the standard flow) and wins if
        # present. The bar sits at 0.0 unless we have a real count.
        message: str | None
        fraction = 0.0
        if progress.detail:
            message = progress.detail
        elif progress.phase is ResolvePhase.BUILDING:
            # Per-package build (the server builds one package at a time);
            # name the package so successive packages don't look like a
            # single bar restarting, and count its buckets down.
            pkg = _package_display_name(progress.apverid)
            done = progress.build_units_done
            total = progress.build_units_total
            if done is not None and total is not None and total > 0:
                remaining = max(total - done, 0)
                message = f'Building {pkg} assets ({remaining} remaining)…'
                fraction = done / total
            else:
                # Counts not reported yet (the initial 'preparing' step:
                # workspace compile + leaf-build queue, before any leaf
                # build reports). A distinct "Preparing to build…" verb
                # (vs. the counted "Building … (N remaining)…" line) so a
                # stuck/looping prepare reads as stuck rather than
                # masquerading as build progress.
                message = f'Preparing to build {pkg}…'
        elif downloading and progress.blobs_total:
            # Single running total across the whole resolve (all packages).
            remaining = max(progress.blobs_total - progress.blobs_done, 0)
            message = f'Downloading assets ({remaining} remaining)…'
            fraction = progress.blobs_done / progress.blobs_total
        else:
            # RESOLVING with no detail: nothing to add (the display's own
            # title/initial state covers it).
            logger.debug(
                'progress: no message for update (phase=%s apverid=%s)',
                progress.phase.value,
                progress.apverid,
            )
            return
        # Diagnostic trace (DEBUG; available under ``ba.assetmanager=DEBUG``):
        # log every update with the structured fields behind it, so the exact
        # sequence and timing are reconstructable. (The message text itself is
        # logged at INFO by the on_update consumer -- the headless record.)
        logger.debug(
            'progress: update %r (phase=%s build=%s/%s'
            ' blobs=%d/%d bytes=%d/%d apverid=%s)',
            message,
            progress.phase.value,
            progress.build_units_done,
            progress.build_units_total,
            progress.blobs_done,
            progress.blobs_total,
            progress.bytes_done,
            progress.bytes_total,
            progress.apverid,
        )
        on_update(message, fraction)

    return report


@ioprepped
@dataclass
class _CachedPackage:
    """One downloaded asset-package-version's entry in the cache manifest."""

    #: ``bucket/flavor`` coord -> flavor-manifest blob hash. Mirrors the
    #: bundled manifest's per-package ``flavor_manifests`` shape so the
    #: cache stores flavor-manifests as hash-referenced CAS blobs exactly
    #: like the bundle.
    flavor_manifests: Annotated[dict[str, str], IOAttrs('fm')]

    #: Cache-only: wall-clock seconds of the last successful resolve that
    #: touched this package (consumed by GC in step 3; the bundle loader
    #: has no such field).
    last_used: Annotated[float, IOAttrs('lu')]


@ioprepped
@dataclass
class _CacheManifest:
    """App-maintained top-level manifest for the writable CAS cache.

    Lives at ``<cache_dir>/manifest.json``. References downloaded
    flavor-manifest blobs by hash (same blob layout as the bundle) plus
    cache-only timestamp tables for GC.
    """

    #: apverid -> cached package entry.
    packages: Annotated[dict[str, _CachedPackage], IOAttrs('p')] = field(
        default_factory=dict
    )

    #: Cache-only: flavor-manifest blob hash -> last-used wall-clock
    #: seconds. Keyed by hash (a hash is shared across coords/apverids) so
    #: GC has one timestamp per flavor-manifest blob. Consumed in step 3.
    flavor_manifest_last_used: Annotated[dict[str, float], IOAttrs('f')] = (
        field(default_factory=dict)
    )


class AssetSubsystem(AppSubsystem):
    """Subsystem for acquiring + tracking downloadable asset packages.

    Accessed as ``babase.app.assets``. The public entry point is the
    async :meth:`resolve`; see the module docstring for scope.
    """

    def __init__(self) -> None:
        super().__init__()

        # Single-in-flight guard covering resolve and GC. An asyncio.Lock
        # binds to the logic-thread loop on first use.
        self._busy_lock = asyncio.Lock()

        # Pinned set: the monotonic union of every apverid + flavor-manifest
        # hash committed into the native registry this process lifetime.
        # Never un-pinned until exit, so once we've told the engine an asset
        # is available GC/cap can never retract it (kills the un-pin-race
        # bug class). Reachable data blobs are pinned transitively (a pinned
        # flavor-manifest is present on disk, so GC's mark enumerates its
        # data blobs). Reset each process; not persisted.
        self._pinned_apverids: set[str] = set()
        self._pinned_fm_hashes: set[str] = set()

        # Progress for the in-flight resolve. Single-in-flight (see
        # _busy_lock), so one running snapshot is enough; the callback is set
        # per-resolve by resolve(on_progress=...).
        self._progress = ResolveProgress()
        self._progress_cb: Callable[[ResolveProgress], None] | None = None

        # Texture tier is hard-coded for now; language is wired from the
        # real locale at resolve time; texture profile comes from the
        # _texture_profile property (headless-aware).
        self._texture_tier = 'regular'

        # Audio tier is likewise hard-coded for now (decision #25; no
        # preview tier — vorbis encodes are too cheap to need one). The
        # audio profile comes from the _audio_profile property
        # (headless-aware).
        self._audio_tier = 'regular'

        # Mesh tier is likewise hard-coded for now (decision #26;
        # REGULAR is the only tier — the dimension exists for a future
        # subdiv ULTRA). The mesh profile comes from the _mesh_profile
        # property (headless-aware).
        self._mesh_tier = 'regular'

        # Render-space (compositing space) flavor dimension (decision
        # #23). Hard-coded to 'gamma' — the only space the renderer
        # composites in today. Becomes runtime-toggleable when the
        # linear renderer lands; for now every client requests gamma.
        self._render_space = 'gamma'

        # Debug/repair affordance: when bundle reuse is disabled, the diff
        # ignores the bundle root so even bundled blobs are (re)downloaded
        # into the writable cache — lets the download+write leg be
        # exercised against an otherwise-fully-bundled package. Set via
        # BA_ASSET_NO_BUNDLE_REUSE=1 (test_game_run --asset-no-bundle-reuse).
        self._reuse_bundle = os.environ.get('BA_ASSET_NO_BUNDLE_REUSE') != '1'

        # Dedicated, deliberately-small pool for CAS-blob downloads, kept
        # separate from the shared app threadpool so a big download burst can't
        # starve other background work (and vice versa). Bounded at
        # _BLOB_DOWNLOAD_CONCURRENCY -- see that constant for why low.
        #
        # Created on demand per resolve (see _download_executor) and torn down
        # in resolve()'s finally, so its worker threads exist ONLY while a
        # download batch is actually in flight -- nothing lingers idle between
        # our infrequent, bursty downloads (construct-mode boot + occasional
        # acquisition). Keeps the steady-state footprint minimal on the
        # low-end-Android target this pool is tuned for, and sidesteps the
        # leftover-threads-at-shutdown problem entirely (no app-lifetime pool
        # to spin down -- which matters on mobile, where clean shutdowns are
        # rare and a hook might not fire). The re-spawn cost per download batch
        # is negligible next to the network IO it wraps.
        self._download_pool: ThreadPoolExecutor | None = None

    @override
    def on_app_running(self) -> None:
        # Register the GC pass as a shutdown task. It runs concurrently
        # with the rest of shutdown (the threadpool is still alive then;
        # it's torn down later in the atexit phase, so atexit is the wrong
        # home). v1 trigger is shutdown-only; a future on_app_suspend()
        # trigger will matter on mobile where clean shutdowns are rare.
        _babase.app.add_shutdown_task(self._run_gc())

    def _download_executor(self) -> ThreadPoolExecutor:
        """Return the CAS-blob download pool, creating it on first use.

        Lazily spun up the first time a resolve needs to download, and
        torn down in resolve()'s finally (see __init__ for the rationale),
        so worker threads exist only while a batch is in flight. Resolves
        are single-in-flight, so there's no concurrency on this attribute.
        """
        if self._download_pool is None:
            logger.info(
                'Creating blob-download pool (%d workers).',
                _BLOB_DOWNLOAD_CONCURRENCY,
            )
            self._download_pool = ThreadPoolExecutor(
                max_workers=_BLOB_DOWNLOAD_CONCURRENCY,
                thread_name_prefix='baassetdl',
                initializer=_init_blob_download_thread,
            )
        return self._download_pool

    # ---------------------------------------------------------------------
    # Paths.

    @property
    def _writable_assets_root(self) -> str:
        """Writable CAS root where downloaded blobs land."""
        return os.path.join(_babase.app.env.cache_directory, 'assets')

    @property
    def _bundle_assets_root(self) -> str:
        """Bundle CAS root holding shipped blobs."""
        return os.path.join(_babase.app.env.data_directory, 'ba_data', 'assets')

    @property
    def _manifest_path(self) -> str:
        """The app-maintained top-level cache manifest path."""
        return os.path.join(_babase.app.env.cache_directory, 'manifest.json')

    @property
    def _gc_cursor_path(self) -> str:
        """Persisted rotating GC shard cursor path."""
        return os.path.join(_babase.app.env.cache_directory, 'gc_resume_shard')

    def _writable_blob_path(self, filehash: str) -> str:
        """Path a CAS blob would occupy in the writable root."""
        return assetcas.cas_blob_path(self._writable_assets_root, filehash)

    def _locate_blob(self, filehash: str) -> str | None:
        """Path of a CAS blob if present (writable then bundle), else None.

        Existence probe used by GC's mark phase to read flavor-manifest
        blobs and to honor "a live flavor-manifest absent on disk → drop
        the ref". Unlike :meth:`_present` this needs no expected size.
        """
        roots = [self._writable_assets_root]
        if self._reuse_bundle:
            roots.append(self._bundle_assets_root)
        for root in roots:
            path = os.path.join(root, filehash[:2], filehash[2:])
            if os.path.isfile(path):
                return path
        return None

    # ---------------------------------------------------------------------
    # Dimensions, bucket coords, fallback policy.

    @property
    def _texture_profile(self) -> str:
        """The active texture profile for resolves.

        Sourced from native :func:`_babase.preferred_texture_profile`,
        which owns texture-format/preference policy: ``null`` in headless
        and otherwise ``fallback_v1`` for now (real GPU-caps selection
        activates there in step 6 with native-format bundles + KTX2
        BC/ASTC decode).
        """
        return _babase.preferred_texture_profile()

    @property
    def _audio_profile(self) -> str:
        """The active audio profile for resolves (decision #25).

        Rides the texture profile's NULL-ness: headless builds (null
        textures) want no audio bytes either; everything else gets
        ``vorbis_v1``, the only real audio profile today. Mirrors the
        server-side derivation in ``standard_bucket_requests()``.
        """
        return 'null' if self._texture_profile == 'null' else 'vorbis_v1'

    @property
    def _mesh_profile(self) -> str:
        """The active display-mesh profile for resolves (decision #26).

        Rides the texture profile's NULL-ness exactly like audio:
        headless builds never load display-mesh bytes (collision
        meshes ride the constant bucket instead). Mirrors the
        server-side derivation in ``standard_bucket_requests()``.
        """
        return 'null' if self._texture_profile == 'null' else 'bob_v1'

    def _desired_coords(self, language: Locale) -> dict[str, str]:
        """The desired ``bucket -> coord`` for the active dimensions.

        Coords must be formed exactly as the build pipeline stores them in
        the manifests: ``constant``, ``language/<locale>``,
        ``textures/<profile>.<render_space>.<quality>``. The textures
        coordinate is ``.``-delimited (decision #23): ``/`` separates the
        asset-type from the flavor and ``.`` separates flavor dimensions,
        so neither may appear inside a value (``_`` is free, keeping
        ``desktop_v1``). Kept strictly one-way (built, never parsed).
        """
        return {
            'constant': 'constant',
            'language': f'language/{language.value}',
            # Cube maps share this bucket -- same profile/render_space/tier
            # dimensions as 2D textures (decision #24).
            'textures': (
                f'textures/{self._texture_profile}'
                f'.{self._render_space}'
                f'.{self._texture_tier}'
            ),
            # Audio has its own profile/tier dimensions (decision #25).
            'audio': f'audio/{self._audio_profile}.{self._audio_tier}',
            # Display meshes likewise (decision #26); collision meshes
            # need no entry — they ride 'constant'.
            'meshes': f'meshes/{self._mesh_profile}.{self._mesh_tier}',
        }

    @staticmethod
    def _fallback_coord(bucket: str) -> str | None:
        """The fallback flavor coord for a bucket (builtin package only)."""
        return _BUCKET_FALLBACKS.get(bucket)

    @staticmethod
    def _is_builtin(apverid: str) -> bool:
        """Is this the builtin/bootstrap package (fallback-eligible)?

        Fallback applies only to bundled packages — their fallback flavors
        are guaranteed present on disk. Every other (download-only) package
        is exact-or-fail.
        """
        # pylint: disable=cyclic-import
        # Builtin-only set on purpose: a runtime-resolved non-builtin
        # package is also "loaded" (its strings merge) but is NOT
        # fallback-eligible -- it has no bundled flavor on disk.
        from babase._asset_packages import builtin_asset_package_apverids

        return apverid in builtin_asset_package_apverids()

    # ---------------------------------------------------------------------
    # Public API.

    async def resolve(
        self,
        apverids: list[str],
        *,
        allow_downloads: bool = True,
        on_download_starting: Callable[[], None] | None = None,
        on_progress: Callable[[ResolveProgress], None] | None = None,
        language: Locale | None = None,
    ) -> ResolveResult:
        """Make every requested asset-package-version available natively.

        For each apverid, each bucket resolves to its *desired* flavor
        (from the active dimensions) if that flavor's blobs are present
        locally (writable cache ∪ bundle); else, when ``allow_downloads``
        is set, the desired flavor is fetched from the connected node (one
        Tier-1 resolve + parallel Tier-2 blob fetches); else, for the
        builtin/bootstrap package only, the bucket's bundled fallback
        flavor is used; otherwise the resolve fails. Only if *every*
        requested apverid fully succeeds are they committed into the C++
        registry in a single atomic swap and the cache manifest persisted;
        any failure raises :class:`AssetResolveError` and leaves the native
        registry untouched (all-or-nothing).

        When everything is already local (the warm path) the whole resolve
        runs in a single off-thread pass with no network and no per-package
        round-trips. ``on_download_starting`` (if given) is called once,
        on the logic thread, only when a real download is about to begin —
        letting callers surface download UI without a separate pre-scan.

        With ``allow_downloads=False`` the resolve is **offline** — entirely
        from local manifests, no Tier-1, no network, no plus subsystem
        needed.

        Must be awaited on the logic thread (kick from non-async code via
        :meth:`babase.App.create_async_task`). Blocking legs (the cloud
        resolve, ``/casblob`` fetches, file IO) are dispatched to
        :attr:`babase.App.threadpool`.
        """
        assert _babase.in_logic_thread()

        # Single-in-flight: wait a short grace for any in-flight resolve,
        # then give up rather than pile on.
        try:
            await asyncio.wait_for(
                self._busy_lock.acquire(), timeout=_RESOLVE_GRACE_SECONDS
            )
        except asyncio.TimeoutError:
            raise AssetResolveError(
                'Another asset resolve is already in progress.'
            ) from None

        self._progress = ResolveProgress()
        self._progress_cb = on_progress
        try:
            return await self._resolve(
                apverids, allow_downloads, on_download_starting, language
            )
        except Exception as exc:
            # TLS cert-verify failures against our own nodes are
            # generally either a wrong system clock or something
            # *between* us and the node (TLS-intercepting antivirus/
            # proxy/DPI) — log context that lets a pasted user log
            # distinguish those before the error continues upward.
            await self._maybe_log_tls_diagnostics(exc)
            raise
        finally:
            # Tear down the per-resolve download pool (if this resolve
            # created one) so its worker threads don't outlive the batch.
            # cancel_futures drops any unstarted fetches; idle workers (the
            # state once the fetch gather has drained) exit immediately.
            # Done before releasing the busy-lock so the pool is fully gone
            # before any next resolve could spin up a fresh one.
            if self._download_pool is not None:
                self._download_pool.shutdown(wait=True, cancel_futures=True)
                self._download_pool = None
            self._progress_cb = None
            self._busy_lock.release()

    def _emit_progress(self) -> None:
        """Hand the current progress snapshot to the on_progress callback.

        A copy is passed so a consumer can stash it without aliasing our
        mutable running state.
        """
        cb = self._progress_cb
        if cb is not None:
            cb(replace(self._progress))

    async def _run_in_pool[T](
        self,
        call: Callable[..., T],
        *args: object,
        executor: ThreadPoolExecutor | None = None,
    ) -> T:
        """Dispatch a blocking call to a thread pool (app pool by default).

        Pass ``executor`` to target a dedicated pool (e.g. the bounded
        blob-download pool) instead of the shared app threadpool.

        Central chokepoint for all our off-thread work so the shutdown
        race is handled in one place. Shutdown tears down the facilities
        this work relies on -- the threadpool (dispatch then raises
        ``cannot schedule new futures after shutdown``), the cloud
        transport and its event loop (an in-flight send gets cancelled,
        surfacing as :class:`~efro.error.CommunicationError`), etc. Any
        such failure once we're shutting down is collateral damage of
        teardown, not a real resolve/GC failure, so we translate it into
        a clean :class:`AssetResolveAbortedError` -- both proactively
        (skip the dispatch entirely if we already know we're shutting
        down) and as a backstop for the dispatch-vs-shutdown race -- so
        callers can bow out quietly. A failure raised while *not*
        shutting down is a real error and propagates unchanged.
        (``CancelledError`` is a ``BaseException``, so a genuine task
        cancellation still propagates rather than being swallowed here.)
        """
        if _babase.app.shutting_down:
            raise AssetResolveAbortedError(
                'Asset operation skipped; app is shutting down.'
            )
        loop = _babase.app.asyncio_loop
        pool = executor if executor is not None else _babase.app.threadpool
        try:
            return await loop.run_in_executor(pool, call, *args)
        except Exception as exc:
            if _babase.app.shutting_down:
                raise AssetResolveAbortedError(
                    'Asset operation aborted; app is shutting down.'
                ) from exc
            raise

    def _apply_build_progress(
        self, apverid: str, bp: AssetPackageBuildProgress
    ) -> None:
        """Reflect a server-side build-progress update into the UI.

        The server sends structured progress (phase + optional counts +
        optional detail) while it (re)builds the requested flavors; we
        surface it as the BUILDING phase for the named package and carry
        its per-package bucket counts so the reporter can render a
        ``Building <pkg> assets (N remaining)…`` line. We deliberately do
        NOT pass the server's ``detail`` through as the display string --
        it's internal jargon (``Building N asset bucket(s)…``) and would
        also shadow the download readout once we move on; the structured
        ``phase``/``units`` are the source of truth. (``detail`` remains
        on the wire as a future escape hatch.)
        """
        self._progress.phase = ResolvePhase.BUILDING
        self._progress.apverid = apverid
        self._progress.detail = None
        self._progress.build_units_done = bp.units_done
        self._progress.build_units_total = bp.units_total
        logger.debug(
            'resolve build-progress %s: phase=%s units=%s/%s detail=%r',
            apverid,
            bp.phase.value,
            bp.units_done,
            bp.units_total,
            bp.detail,
        )
        self._emit_progress()

    def resolve_local(self, apverids: list[str]) -> ResolveResult:
        """Synchronously register the best LOCAL flavor of each package.

        A downloads-disabled, fully-synchronous resolve: for each apverid it
        registers the desired flavor when that flavor's blobs are already on
        disk (cache ∪ bundle), else -- for builtin packages -- the bundled
        fallback. No network, executor, or asyncio, so it is safe to call
        from the boot path *before any asset loads* -- so builtin assets come
        up at their ideal flavor on warm starts instead of loading a fallback
        that a later downloading resolve has to swap back out.

        Shares the per-package scan/finalize, accumulation, and register/pin
        with the async :meth:`resolve`; it differs only in doing no downloads
        and running inline rather than on the threadpool. Does not persist the
        cache manifest (it registers only already-present blobs; a later
        downloading :meth:`resolve` owns the on-disk manifest).

        Must be called on the logic thread.
        """
        assert _babase.in_logic_thread()
        desired = self._desired_coords(_babase.app.locale.current_locale)
        results = [self._resolve_one_local(apv, desired) for apv in apverids]
        register_specs, manifest_pkgs, fell_back = self._accumulate_results(
            apverids, results
        )
        _babase.register_asset_package_buckets(register_specs)
        self._pin(manifest_pkgs)
        self._reload_language()
        logger.info(
            'Registered %d builtin package(s) at best-local flavor%s.',
            len(apverids),
            f' ({len(fell_back)} on fallback)' if fell_back else '',
        )
        return ResolveResult(apverids=list(apverids), fell_back=fell_back)

    def get_package_strings(
        self, apverid: str, locale: Locale
    ) -> dict[str, 'str | StringSelector']:
        """Per-locale language-string values for an already-resolved package.

        Returns ``{logical-name: value}`` (a plain ``str`` or a
        :class:`~bacommon.loctext.StringSelector`) read from the package's
        resolved ``language/<locale>`` blob -- the Python side of what the
        native ``ReloadLanguage`` consumes, for the language-agnostic
        (``Lstr``) doc-ui decode path. ``locale`` must be the one the package
        was :meth:`resolve`\\ d for (the coord is ``language/<locale.value>``,
        matching the ``_desired_coords`` bucket map).

        Reads local blobs only (no network); does blocking file IO, so call
        it off the logic thread. Missing/absent data fails soft -- an empty
        map -- leaving the caller's decode to surface per-string sentinels.
        """
        # Deferred: keep bacommon.langstr out of babase's module-load graph.
        from bacommon.langstr import parse_language_blob

        coord = f'language/{locale.value}'

        # The language flavor-manifest hash: downloaded packages live in the
        # cache manifest, builtin ones in the bundle manifest.
        cached = self._load_manifest().packages.get(apverid)
        fm_hash = (
            cached.flavor_manifests.get(coord) if cached is not None else None
        )
        if fm_hash is None:
            fm_hash = self._read_bundle_manifest().get(apverid, {}).get(coord)
        if fm_hash is None or self._locate_blob(fm_hash) is None:
            return {}

        # The blob lives at logical path 'language.json' part 'j' (the same
        # one native ReloadLanguage looks up).
        parts = self._read_entries(fm_hash).get('language.json')
        blob_hash = parts.get('j') if parts else None
        if blob_hash is None:
            return {}
        path = self._locate_blob(blob_hash)
        if path is None:
            return {}
        with open(path, 'rb') as infile:
            return parse_language_blob(infile.read().decode())

    @staticmethod
    def _reload_language() -> None:
        """(Re)build the native language string table from the registered
        ``language`` buckets.

        Called right after any bucket commit (boot ``resolve_local``,
        construct-mode resolve, an elective language switch), so the
        native table always tracks the currently-registered locale flavor
        — a resolve that swaps ``language/<locale>`` is immediately
        reflected in on-screen text via the resulting language-change
        cascade.
        """
        from babase._asset_packages import loaded_asset_package_apverids

        _babase.reload_language(loaded_asset_package_apverids())

    # ---------------------------------------------------------------------
    # Resolve internals.

    async def _resolve(
        self,
        apverids: list[str],
        allow_downloads: bool,
        on_download_starting: Callable[[], None] | None = None,
        language: Locale | None = None,
    ) -> ResolveResult:
        # An explicit target locale (used by an elective language switch
        # to resolve a flavor *before* committing it) overrides the active
        # one; otherwise resolve for the current locale.
        if language is None:
            language = _babase.app.locale.current_locale
        now = time.time()
        logger.info(
            'Resolving %d asset-package(s) (downloads=%s): %s',
            len(apverids),
            allow_downloads,
            ', '.join(apverids),
        )
        t_start = _babase.apptime()

        # Warm fast-path: if every desired flavor is already local, resolve
        # the whole set in a single off-thread pass — no per-package round-
        # trips, no download machinery, no network. The per-package async
        # path below is used only when something must actually be fetched.
        offline = await self._run_in_pool(
            self._resolve_offline_sync, apverids, language
        )
        if offline is not None:
            register_specs, manifest_pkgs, fell_back = offline
            mode = 'offline'
        else:
            # Something isn't fully local. Signal the caller a download is
            # starting (progress UI), then run the per-package path which
            # scans, fetches if allowed, and falls back as appropriate.
            if allow_downloads and on_download_starting is not None:
                on_download_starting()
            register_specs, manifest_pkgs, fell_back = (
                await self._resolve_online(apverids, language, allow_downloads)
            )
            mode = 'online'

        # Commit point: everything resolved + landed on disk. Register all
        # buckets into native in one atomic swap, then persist the manifest.
        _babase.register_asset_package_buckets(register_specs)
        # Pin everything we just told the engine about — never retracted
        # this process lifetime (GC-/cap-immune).
        self._pin(manifest_pkgs)
        # Record these as loaded so _reload_language (next line) merges any
        # newly-resolved package's strings into the native table -- and a
        # later locale switch re-resolves them. Builtins are skipped.
        # pylint: disable-next=cyclic-import
        from babase._asset_packages import register_resolved_apverids

        register_resolved_apverids(apverids)
        self._reload_language()
        await self._run_in_pool(self._commit_manifest, manifest_pkgs, now)

        logger.info(
            'Resolved %d package(s): %d bucket(s) registered%s (%s, %.0f ms).',
            len(apverids),
            len(register_specs),
            f', {len(fell_back)} fell back' if fell_back else '',
            mode,
            (_babase.apptime() - t_start) * 1000.0,
        )
        return ResolveResult(apverids=list(apverids), fell_back=fell_back)

    def _resolve_offline_sync(
        self, apverids: list[str], language: Locale
    ) -> _ResolveAccum | None:
        """Resolve the whole set from local state, in one off-thread pass.

        Returns the accumulated ``(register_specs, manifest_pkgs,
        fell_back)`` when *every* desired flavor for *every* apverid is
        already complete locally (the warm path — no network, no per-package
        round-trips). Returns ``None`` if anything is missing, in which case
        the caller falls back to the per-package online path (which handles
        downloads + builtin fallback exactly as before). Synchronous; runs
        in a single executor hop.
        """
        desired = self._desired_coords(language)
        results: list[_OneResult] = []
        for apverid in apverids:
            local, missing = self._scan_local(apverid, desired)
            if missing:
                # Not fully local; let the online path handle this set
                # (download desired flavors / builtin fallback / fail).
                return None
            results.append(
                self._finalize_one(
                    apverid, desired, local, self._is_builtin(apverid)
                )
            )
        return self._accumulate_results(apverids, results)

    async def _resolve_online(
        self, apverids: list[str], language: Locale, allow_downloads: bool
    ) -> _ResolveAccum:
        """Per-package resolve with optional Tier-1 downloads + fallback.

        Used when the warm fast-path can't satisfy the set locally. Each
        package scans, optionally fetches missing flavors, and finalizes.
        """
        results: list[_OneResult] = []
        for apverid in apverids:
            results.append(
                await self._resolve_one(apverid, language, allow_downloads)
            )
        return self._accumulate_results(apverids, results)

    @staticmethod
    def _accumulate_results(
        apverids: list[str], results: list[_OneResult]
    ) -> _ResolveAccum:
        """Fold per-package results into the resolve accumulator.

        Builds ``(register_specs, manifest_pkgs, fell_back)`` from the
        :class:`_OneResult` for each apverid. Shared by every resolve path
        (offline fast-path, online, and the synchronous boot resolve).
        """
        register_specs: list[tuple[str, str, dict[str, dict[str, str]]]] = []
        manifest_pkgs: dict[str, dict[str, str]] = {}
        fell_back: dict[str, str] = {}
        for apverid, result in zip(apverids, results):
            manifest_pkgs[apverid] = result.coords
            for coord in result.coords:
                register_specs.append((apverid, coord, result.entries[coord]))
            fell_back.update(result.fell_back)
        return register_specs, manifest_pkgs, fell_back

    def _pin(self, manifest_pkgs: dict[str, dict[str, str]]) -> None:
        """Pin resolved packages + flavor-manifest hashes (GC-/cap-immune).

        Once pinned, an apverid and its flavor-manifest blobs are never
        retracted for this process lifetime. Shared by the sync + async
        resolve commits.
        """
        for apverid, coords in manifest_pkgs.items():
            self._pinned_apverids.add(apverid)
            self._pinned_fm_hashes.update(coords.values())

    async def _resolve_one(
        self, apverid: str, language: Locale, allow_downloads: bool
    ) -> _OneResult:
        """Resolve one apverid's buckets to local-or-fetched flavors.

        Scans local coords, optionally does one Tier-1 download to obtain
        any desired flavors not present locally, then picks per bucket:
        desired-if-complete, else (builtin only) bundled-fallback, else
        fail.
        """
        is_builtin = self._is_builtin(apverid)
        desired = self._desired_coords(language)

        self._progress.phase = ResolvePhase.RESOLVING
        self._progress.apverid = apverid
        self._progress.detail = None
        # Clear any prior package's build counts as we start this one.
        self._progress.build_units_done = None
        self._progress.build_units_total = None
        self._emit_progress()

        # Scan local state (off-thread): which desired coords are already
        # complete on disk, and the full local coord→hash map.
        local_coords, missing_buckets = await self._run_in_pool(
            self._scan_local, apverid, desired
        )

        # If any desired flavor isn't local and downloads are allowed, do
        # one Tier-1 resolve + fetch to obtain the desired flavors.
        downloaded: dict[str, str] = {}
        if allow_downloads and missing_buckets:
            try:
                downloaded = await self._tier1_download(apverid, language)
            except AssetResolveAbortedError:
                # App is shutting down -- not a resolve failure; don't
                # fall back to bundled, just abandon the whole resolve.
                raise
            except AssetResolveError as exc:
                # The builtin/bootstrap package must still come up offline;
                # other packages are exact-or-fail. Log the underlying
                # reason either way (it's otherwise swallowed).
                logger.warning('%s: online resolve failed (%s).', apverid, exc)
                if not is_builtin:
                    raise
                strip_exception_tracebacks(exc)

        # Finalize per-bucket selection + read registry entries (off-thread).
        # local ∪ just-downloaded — what's actually available to choose from.
        available = {**local_coords, **downloaded}
        return await self._run_in_pool(
            self._finalize_one, apverid, desired, available, is_builtin
        )

    def _resolve_one_local(
        self, apverid: str, desired: dict[str, str]
    ) -> _OneResult:
        """Best-local resolve of one package: scan local + finalize.

        The fully-synchronous, no-download core (no executor, no Tier-1):
        picks the desired flavor when its blobs are local, else (builtin
        only) the bundled fallback, else raises. Building block of
        :meth:`resolve_local`; ``available`` is just the local coords.
        """
        local, _missing = self._scan_local(apverid, desired)
        return self._finalize_one(
            apverid, desired, local, self._is_builtin(apverid)
        )

    def _scan_local(
        self, apverid: str, desired: dict[str, str]
    ) -> tuple[dict[str, str], set[str]]:
        """Local coord→hash map + which desired buckets aren't fully local.

        Off-thread; reads the bundle + cache manifests and the referenced
        flavor-manifest blobs.
        """
        local = self._local_coords(apverid)
        missing: set[str] = set()
        for bucket, coord in desired.items():
            fm_hash = local.get(coord)
            if fm_hash is None or not self._coord_complete(fm_hash):
                missing.add(bucket)
        return local, missing

    def _finalize_one(
        self,
        apverid: str,
        desired: dict[str, str],
        available: dict[str, str],
        is_builtin: bool,
    ) -> _OneResult:
        """Per-bucket flavor selection + registry-entry read. Off-thread.

        For each bucket: the desired flavor if its blobs are all present
        (``available`` = local ∪ just-downloaded), else — builtin package
        only — the bundled fallback flavor, else raise. Reads the chosen
        flavor's flavor-manifest to build the ``{logical_path: data-hash}``
        entries.
        """
        coords: dict[str, str] = {}
        entries: dict[str, dict[str, dict[str, str]]] = {}
        fell_back: dict[str, str] = {}
        for bucket, desired_coord in desired.items():
            fm_hash = available.get(desired_coord)
            if fm_hash is not None and self._coord_complete(fm_hash):
                coords[desired_coord] = fm_hash
                entries[desired_coord] = self._read_entries(fm_hash)
                continue
            if is_builtin:
                fallback = self._fallback_coord(bucket)
                fb_hash = (
                    available.get(fallback) if fallback is not None else None
                )
                if (
                    fallback is not None
                    and fb_hash is not None
                    and self._coord_complete(fb_hash)
                ):
                    coords[fallback] = fb_hash
                    entries[fallback] = self._read_entries(fb_hash)
                    fell_back[desired_coord] = fallback
                    continue
            raise AssetResolveError(
                f'{apverid}: bucket {bucket!r}: neither the desired flavor'
                f' ({desired_coord}) nor a usable fallback is available.'
            )
        return _OneResult(coords=coords, entries=entries, fell_back=fell_back)

    def _local_coords(self, apverid: str) -> dict[str, str]:
        """Locally-known ``coord -> flavor-manifest hash`` (bundle ∪ cache).

        The cache's (downloaded/ideal) hash supersedes the bundle's for a
        coord -- but ONLY when that cached flavor is actually complete on
        disk. The writable cache can have blobs pruned out from under a
        committed entry (e.g. the cache-ninja prunes random cache files
        before spinup), so a cached flavor-manifest pointing at now-missing
        files must NOT shadow the bundle's complete copy of the same coord;
        it has to fall through to it. The bundle is read-only and never
        pruned, so it is a reliable floor for builtin packages -- surviving
        a flavor-manifest that references nonexistent files is a core
        design constraint of the asset system.

        Coords the bundle doesn't carry are taken from the cache as-is
        (there's no floor to fall through to); their completeness is
        checked downstream by :meth:`_scan_local` / :meth:`_finalize_one`.
        """
        coords: dict[str, str] = {}
        coords.update(self._read_bundle_manifest().get(apverid, {}))
        pkg = self._load_manifest().packages.get(apverid)
        if pkg is not None:
            for coord, fm_hash in pkg.flavor_manifests.items():
                if coord not in coords or self._coord_complete(fm_hash):
                    coords[coord] = fm_hash
        return coords

    def _read_bundle_manifest(self) -> dict[str, dict[str, str]]:
        """Parse the bundled ``ba_data/manifest.json`` → apverid→coords→hash."""
        path = os.path.join(
            _babase.app.env.data_directory, 'ba_data', 'manifest.json'
        )
        try:
            with open(path, encoding='utf-8') as infile:
                manifest = json.load(infile)
        except FileNotFoundError:
            return {}
        except Exception as exc:
            logger.exception('Error reading bundle manifest %s.', path)
            strip_exception_tracebacks(exc)
            return {}
        return {
            apv: entry.get('flavor_manifests', {})
            for apv, entry in manifest.get('asset_package_versions', {}).items()
        }

    def _coord_complete(self, fm_hash: str) -> bool:
        """Is this flavor fully present? (fm blob + all its data blobs)."""
        fm_path = self._locate_blob(fm_hash)
        if fm_path is None:
            return False
        try:
            with open(fm_path, 'rb') as infile:
                parsed = json.loads(infile.read())
        except Exception as exc:
            logger.exception('Error reading flavor-manifest %s.', fm_hash)
            strip_exception_tracebacks(exc)
            return False
        return all(
            self._present(comp['h'], comp['s'])
            for info in parsed['e'].values()
            for comp in info.values()
        )

    def _read_entries(self, fm_hash: str) -> dict[str, dict[str, str]]:
        """Read a flavor-manifest blob → ``{logical_path: data-blob hash}``.

        Caller must have confirmed the flavor is complete (see
        :meth:`_coord_complete`).
        """
        fm_path = self._locate_blob(fm_hash)
        assert fm_path is not None
        with open(fm_path, 'rb') as infile:
            parsed = json.loads(infile.read())
        # logical_path -> {part -> data-hash}. A null asset is {}.
        return {
            p: {part: comp['h'] for part, comp in info.items()}
            for p, info in parsed['e'].items()
        }

    async def _tier1_download(
        self, apverid: str, language: Locale
    ) -> dict[str, str]:
        """One Tier-1 resolve + parallel Tier-2 fetch of the desired flavors.

        Returns the resolved ``coord -> flavor-manifest hash`` map; the
        flavor-manifest blobs are written and all referenced data blobs
        fetched (those not already present) before returning. Raises
        :class:`AssetResolveError` on any resolve/fetch failure.
        """
        # Downloads route through the connected node, which comes up a beat
        # after boot; wait briefly for it rather than failing a resolve
        # that raced the connection.
        await self._wait_for_node()
        # Capture the signed-in account handle on the logic thread; the
        # off-thread send enters its context so the resolve carries our
        # account (see _resolve_tier1). None → anonymous (PROD/public).
        plus = _babase.app.plus
        primary = plus.accounts.primary if plus is not None else None
        # Resolve, polling while the master is (re)building the requested
        # flavors. While build_progress is set the manifest isn't ready;
        # render the progress and re-send the same resolve (same nonce)
        # after a short wait until it resolves to a manifest (or errors).
        while True:
            response = await self._run_in_pool(
                self._resolve_tier1, apverid, language, primary
            )
            if response.build_progress is None:
                break
            self._apply_build_progress(apverid, response.build_progress)
            await asyncio.sleep(_BUILD_POLL_INTERVAL_SECONDS)
        if response.error is not None:
            msg = f'{apverid}: {response.error}'
            code = response.error_code
            # Raise a specific subclass for the cases callers branch on
            # (e.g. construct-mode prompting for sign-in). Carry the
            # server's raw message too so callers can show its wording.
            errcls = AssetResolveError
            if code is not None:
                errcls = _RESOLVE_ERROR_TYPES.get(code, AssetResolveError)
            raise errcls(msg, code, response.error)
        if not response.buckets:
            raise AssetResolveError(f'{apverid}: resolve returned no buckets.')

        coords: dict[str, str] = {}
        fm_writes: dict[str, bytes] = {}
        data_needed: dict[str, int] = {}
        for coord, flavor_manifest in response.buckets.items():
            coords[coord] = flavor_manifest.hash
            # Dedupe by hash: a flavor-manifest blob is often shared across
            # coords (e.g. an empty 'constant' and 'language/eng').
            if not self._present(
                flavor_manifest.hash, len(flavor_manifest.data)
            ):
                fm_writes[flavor_manifest.hash] = flavor_manifest.data
            parsed = json.loads(flavor_manifest.data)
            # The manifest carries only canonical content identity (hash +
            # size); a blob's transfer encoding is negotiated per /casblob
            # download (see _acquire_data_blob), not recorded here.
            for info in parsed['e'].values():
                for comp in info.values():
                    data_needed[comp['h']] = comp['s']

        if fm_writes:
            await asyncio.gather(
                *[
                    self._run_in_pool(self._cas_write, h, d)
                    for h, d in fm_writes.items()
                ]
            )

        to_fetch = [
            (h, s) for h, s in data_needed.items() if not self._present(h, s)
        ]
        if to_fetch:
            if response.token is None:
                raise AssetResolveError(
                    f'{apverid}: resolve returned no download token.'
                )
            base_url = self._node_base_url()
            if base_url is None:
                raise AssetResolveError(
                    f'{apverid}: not connected to a node; cannot download.'
                )
            token_header = self._encode_token(response.token)

            # Progress: bump the running totals, then count each blob off as
            # its fetch completes (each _fetch resumes on the logic thread
            # after the off-thread fetch, so updating progress there is safe).
            self._progress.phase = ResolvePhase.DOWNLOADING
            self._progress.apverid = apverid
            self._progress.blobs_total += len(to_fetch)
            self._progress.bytes_total += sum(s for _h, s in to_fetch)
            self._emit_progress()

            # gather() surfaces only the first failure to our caller;
            # sibling fetches failing after that get consumed *inside*
            # gather with tracebacks (and thus ref cycles) intact. So
            # be the terminal consumer for those ourselves: first
            # failure propagates untouched, later ones are stripped and
            # swallowed (the resolve is already doomed at that point).
            have_failure = False

            async def _fetch(h: str, s: int) -> None:
                nonlocal have_failure
                try:
                    await self._run_in_pool(
                        self._acquire_data_blob,
                        base_url,
                        token_header,
                        (h, s),
                        executor=self._download_executor(),
                    )
                except Exception as exc:
                    if have_failure:
                        strip_exception_tracebacks(exc)
                        return
                    have_failure = True
                    raise
                self._progress.blobs_done += 1
                self._progress.bytes_done += s
                self._emit_progress()

            await asyncio.gather(*[_fetch(h, s) for h, s in to_fetch])
        return coords

    def _resolve_tier1(
        self,
        apverid: str,
        language: Locale,
        primary: AccountV2Handle | None,
    ) -> ResolveAssetPackageResponse:
        """Blocking Tier-1 resolve via the connected node. Off-thread.

        ``primary`` is the signed-in account handle (captured on the logic
        thread by the caller) or None. We send the resolve *within* its
        context manager so the request carries our account: entering the
        handle sets the active-handle thread-local that drives the
        account-session-channel sidecar basn reads. Without it the resolve
        goes out anonymous and non-public (DEV/TEST) versions fail with an
        auth error even when signed in. A None primary sends anonymously
        (only PROD/public versions resolve).
        """
        plus = _babase.app.plus
        if plus is None:
            raise AssetResolveError(
                'plus subsystem unavailable; cannot resolve asset packages.'
            )
        msg = ResolveAssetPackageMessage(
            apverid=apverid,
            language=language,
            texture_profile=self._texture_profile,
            texture_tier=self._texture_tier,
            build_number=_babase.app.env.engine_build_number,
        )
        # A transport-level hiccup (node mid-rollout, flaky link, etc.)
        # surfaces as CommunicationError. Convert it to an AssetResolveError
        # so the per-package handler can do the right thing -- fall back to
        # bundled flavors for the builtin/bootstrap package, exact-or-fail
        # for the rest -- with a clean logged reason rather than an
        # unhandled traceback. (Server-side resolve errors arrive as
        # structured fields on the response and are handled by the caller.)
        try:
            if primary is not None:
                with primary:
                    response = plus.cloud.send_message(msg)
            else:
                response = plus.cloud.send_message(msg)
        except CommunicationError as exc:
            raise AssetResolveError(
                f'{apverid}: communication error during resolve: {exc}'
            ) from exc
        assert isinstance(response, ResolveAssetPackageResponse)
        return response

    def _node_base_url(self) -> str | None:
        """Base url for fetches from the connected basn node, or None.

        Scheme mirrors the transport session's security (``https`` for
        wss, ``http`` for insecure ws) so blob fetches avoid TLS exactly
        when the transport does; blob integrity comes from CAS sha256
        verification, not the channel.
        """
        plus = _babase.app.plus
        if plus is None:
            return None
        # plus.cloud is a soft-loaded interface (Any to the base layer),
        # so pin the expected type here to satisfy mypy's return-Any check.
        url: str | None = plus.cloud.get_connected_node_base_url()
        return url

    async def _wait_for_node(self) -> None:
        """Wait (up to a timeout) for a connected node to download through.

        No-op if already connected. Registers a connectivity-changed
        callback (rather than polling) so we proceed the instant the node
        connects. On timeout we return anyway and let the subsequent
        resolve/fetch fail with a clear "not connected" error.
        """
        if self._node_base_url() is not None:
            return
        plus = _babase.app.plus
        if plus is None:
            return

        event = asyncio.Event()

        def _on_changed(connected: bool) -> None:
            # When connectivity comes up the node address is already set
            # (the connected primary session is assigned before the
            # connectivity-changed signal fires).
            if connected and self._node_base_url() is not None:
                event.set()

        reg = plus.cloud.on_connectivity_changed_callbacks.register(_on_changed)
        try:
            # Re-check now that we're registered, in case it connected
            # between the initial check and the registration.
            if self._node_base_url() is None:
                await asyncio.wait_for(event.wait(), timeout=_NODE_WAIT_SECONDS)
        except asyncio.TimeoutError:
            pass
        finally:
            # Hold `reg` until here so the callback stays registered for the
            # whole wait; dropping it unregisters (CallbackSet is
            # weakref-based).
            del reg

    async def _maybe_log_tls_diagnostics(self, exc: Exception) -> None:
        """Log one-shot diagnostics if a resolve died on TLS cert verify.

        Our node certs are renewed weekly, so 'certificate verify
        failed' from a client almost always means a wrong system clock
        or a TLS-intercepting middlebox (antivirus 'https scanning',
        school/work proxies, DPI). Both are invisible in the bare
        traceback; log absolute clock values, the node's clock fetched
        over plain http (immune to the TLS tampering itself), and the
        TLS environment so a pasted user log can tell them apart.
        Best-effort; never raises.
        """
        import ssl

        # Walk the cause/context chain for a cert-verify error.
        seen: set[int] = set()
        cur: BaseException | None = exc
        found: ssl.SSLCertVerificationError | None = None
        while cur is not None and id(cur) not in seen:
            seen.add(id(cur))
            if isinstance(cur, ssl.SSLCertVerificationError):
                found = cur
                break
            cur = cur.__cause__ or cur.__context__
        if found is None:
            return

        base_url = self._node_base_url()
        try:
            details = await self._run_in_pool(
                self._tls_diagnostics_blocking, base_url
            )
        except Exception as diagexc:
            details = f'diagnostics gathering failed: {diagexc!r}'
            strip_exception_tracebacks(diagexc)
        logger.warning(
            'TLS certificate verification failed talking to'
            ' node %s (%s). Diagnostics: %s.',
            base_url,
            found,
            details,
        )

    @staticmethod
    def _tls_diagnostics_blocking(base_url: str | None) -> str:
        """Gather TLS-failure diagnostic info. Off-thread; blocking.

        Returns a single human-readable summary string: local clock
        (UTC + local timezone), local-minus-node clock skew measured
        via a plain-http Date header from the node (nodes are
        NTP-synced, and plain http works even on networks where TLS is
        being tampered with), and the OpenSSL/root-cert setup in use.
        """
        import ssl
        from datetime import datetime, UTC
        from email.utils import parsedate_to_datetime

        bits: list[str] = []
        now = datetime.now(UTC)
        bits.append(f'utc-now={now.isoformat(timespec='seconds')}')
        bits.append(
            f'local-now={now.astimezone().isoformat(timespec='seconds')}'
        )
        if base_url is not None:
            try:
                host = base_url.split('://', 1)[-1]
                response = _babase.app.net.urllib3pool.request(
                    'GET', f'http://{host}/', timeout=5.0, retries=False
                )
                # getlist, not get: duplicate Date headers happen in the
                # wild (our own nodes currently send two) and get() would
                # comma-join them into an unparseable mess.
                date_headers = response.headers.getlist('Date')
                if date_headers:
                    nodetime = parsedate_to_datetime(date_headers[0])
                    if nodetime.tzinfo is None:
                        # RFC 5322 '-0000' parses as naive but means UTC.
                        nodetime = nodetime.replace(tzinfo=UTC)
                    # Compare against a fresh local reading (the request
                    # itself may have taken a while). Date-header
                    # granularity is 1s, which is plenty: we care about
                    # minutes-to-years of skew, not sub-second.
                    skew = (datetime.now(UTC) - nodetime).total_seconds()
                    bits.append(f'local-clock-minus-node-clock={skew:+.1f}s')
                else:
                    bits.append('node-clock=unavailable (no Date header)')
            except Exception as exc:
                bits.append(f'node-clock=unavailable ({exc!r})')
                strip_exception_tracebacks(exc)
        bits.append(f'openssl={ssl.OPENSSL_VERSION}')
        bits.append(f'ssl-cert-file={os.environ.get('SSL_CERT_FILE')}')
        try:
            import certifi

            # getattr: __version__ exists at runtime but not in some
            # type-stub sets, and a diagnostics line isn't worth a hard
            # dependency on either.
            certifi_ver = getattr(certifi, '__version__', '?')
            bits.append(f'certifi={certifi_ver}')
        except ImportError:
            bits.append('certifi=unavailable')
        return '; '.join(bits)

    @staticmethod
    def _encode_token(token: securedata.Archive) -> str:
        """Encode a capability token for the ``X-Asset-Token`` header."""
        return assetcas.encode_asset_token(token)

    # ---------------------------------------------------------------------
    # CAS blob IO (off-thread; blocking).

    def _present(self, filehash: str, size: int) -> bool:
        """Is this CAS blob already present at the expected size?

        Probes the writable cache root and (unless bundle reuse is
        disabled) the bundle root. Present-but-wrong-size counts as absent
        so it gets refetched/overwritten. The free ``st_size`` check is a
        cheap catch for external truncation/tampering, not a content proof.
        """
        roots = [self._writable_assets_root]
        if self._reuse_bundle:
            roots.append(self._bundle_assets_root)
        return assetcas.blob_present(roots, filehash, size)

    def _acquire_data_blob(
        self,
        base_url: str,
        token_header: str,
        blob: tuple[str, int],
    ) -> None:
        """Fetch one data blob from the node and atomically write it.

        ``blob`` is ``(canonical-hash, canonical-size)``. Delegates to the
        shared :func:`bacommon.assetcas.download_cas_blob`, which
        advertises the encodings we can decode, decodes per the encoding
        the node reports it served (``X-Cas-Compression``), then
        sha256-verifies + atomically writes the canonical bytes.
        ``base_url``'s scheme mirrors the transport session's security
        (see :meth:`_node_base_url`); integrity is guaranteed by the CAS
        hash check either way. The local cache always stores uncompressed
        blobs. Off-thread; blocking.
        """
        filehash, size = blob
        try:
            assetcas.download_cas_blob(
                _babase.app.net.urllib3pool,
                base_url,
                filehash,
                size,
                token_header=token_header,
                dest_root=self._writable_assets_root,
                timeout_seconds=_BLOB_DOWNLOAD_TIMEOUT_SECONDS,
            )
        except assetcas.CasDownloadError as exc:
            raise AssetResolveError(str(exc)) from exc

    def _cas_write(self, filehash: str, data: bytes) -> None:
        """Atomically write a CAS blob into the writable root.

        Delegates to the shared :func:`bacommon.assetcas.cas_write`
        (sha256-verify, temp + ``fsync`` + ``os.replace``). Off-thread;
        blocking.
        """
        try:
            assetcas.cas_write(self._writable_assets_root, filehash, data)
        except assetcas.CasDownloadError as exc:
            raise AssetResolveError(str(exc)) from exc

    # ---------------------------------------------------------------------
    # Cache manifest IO (off-thread; blocking).

    def _load_manifest(self) -> _CacheManifest:
        path = self._manifest_path
        try:
            with open(path, encoding='utf-8') as infile:
                return dataclass_from_json(_CacheManifest, infile.read())
        except FileNotFoundError:
            return _CacheManifest()
        except Exception as exc:
            logger.exception(
                'Error loading asset cache manifest %s; starting fresh.', path
            )
            strip_exception_tracebacks(exc)
            return _CacheManifest()

    def _commit_manifest(
        self, manifest_pkgs: dict[str, dict[str, str]], now: float
    ) -> None:
        """Fold the just-resolved packages into the cache manifest + persist.

        Loads the current manifest (preserving other packages' entries),
        updates each resolved package's coords + ``last_used`` and bumps
        the per-flavor-manifest-hash timestamp table, then atomically
        rewrites ``manifest.json``.
        """
        manifest = self._load_manifest()
        for apverid, coords in manifest_pkgs.items():
            manifest.packages[apverid] = _CachedPackage(
                flavor_manifests=dict(coords), last_used=now
            )
            for fm_hash in coords.values():
                manifest.flavor_manifest_last_used[fm_hash] = now
        self._persist_manifest(manifest)

    def _persist_manifest(self, manifest: _CacheManifest) -> None:
        path = self._manifest_path
        destdir = os.path.dirname(path)
        os.makedirs(destdir, exist_ok=True)
        data = dataclass_to_json(manifest)
        fd, tmp = tempfile.mkstemp(dir=destdir, prefix='.tmp_manifest_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as outfile:
                outfile.write(data)
                outfile.flush()
                os.fsync(outfile.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ---------------------------------------------------------------------
    # GC / prune (shutdown-task).

    async def _run_gc(self) -> None:
        """Run one GC pass. Registered as a shutdown task in on_app_running.

        Holds the single-in-flight guard (best-effort: skips if a resolve
        is somehow still running) and dispatches the blocking mark+sweep to
        the threadpool. The threadpool is normally still alive during the
        shutdown-task phase, but a fast shutdown can tear it down first; in
        that case the dispatch surfaces as :class:`AssetResolveAbortedError`
        and we abandon the pass quietly (the next launch's GC resumes it).
        """
        try:
            try:
                await asyncio.wait_for(
                    self._busy_lock.acquire(),
                    timeout=_GC_BUSY_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError as exc:
                logger.warning('Asset GC skipped: subsystem busy.')
                strip_exception_tracebacks(exc)
                return
            try:
                await self._run_in_pool(self._gc_blocking)
            finally:
                self._busy_lock.release()
        except AssetResolveAbortedError as exc:
            # Threadpool went away mid-GC because we're shutting down --
            # benign; the next launch's GC picks up where this left off.
            logger.debug('Asset GC abandoned; app is shutting down.')
            strip_exception_tracebacks(exc)
        except Exception as exc:
            logger.exception('Error during asset GC.')
            strip_exception_tracebacks(exc)

    def _gc_blocking(self) -> None:
        """The whole GC pass (mark + manifest rewrite + sweep). Off-thread.

        Mark computes the live blob set from the manifest survivor rule +
        the pinned set and atomically rewrites the manifest FIRST (so it
        never references a blob we're about to delete); then the writable
        CAS root is swept under a wall-clock budget. Safe to be cut off at
        any point (interleaved unlink + persisted rotating cursor ⇒ durable
        monotonic progress that converges over a run or two).
        """
        deadline = time.monotonic() + _GC_BUDGET_SECONDS

        root = self._writable_assets_root
        if not os.path.isdir(root):
            logger.debug('Asset GC: no writable CAS root; nothing to do.')
            return

        live, mark_secs = self._gc_mark()
        stats = self._gc_sweep(root, live, deadline)

        if stats.cut_off:
            logger.info(
                'Asset GC (cut off at budget): freed %d file(s) / %d bytes,'
                ' %d/%d shard(s); resuming next run at shard %02x.'
                ' mark %.3fs, sweep %.3fs.',
                stats.freed_files,
                stats.freed_bytes,
                stats.shards_done,
                _CAS_SHARD_COUNT,
                stats.next_shard,
                mark_secs,
                stats.sweep_secs,
            )
        else:
            logger.info(
                'Asset GC: freed %d file(s) / %d bytes (full sweep,'
                ' %d non-empty shard(s)). mark %.3fs, sweep %.3fs.',
                stats.freed_files,
                stats.freed_bytes,
                stats.shards_done,
                mark_secs,
                stats.sweep_secs,
            )

    def _gc_mark(self) -> tuple[set[str], float]:
        """Compute the live blob set and atomically rewrite the manifest.

        Returns ``(live_blob_hashes, mark_wall_seconds)``. The manifest is
        the source of truth, so it's rewritten here (before any sweep) to
        keep only surviving packages/refs + only-live timestamps.
        """
        start = time.monotonic()
        manifest = self._load_manifest()
        now = time.time()
        cutoff = now - _GC_CUTOFF_SECONDS

        live_fm, new_packages = self._gc_survivors(manifest, cutoff)
        live = self._gc_reachable(live_fm)

        # Prune the timestamp table to only-live flavor-manifests.
        new_fmlu = {
            h: manifest.flavor_manifest_last_used.get(h, now) for h in live_fm
        }
        self._persist_manifest(
            _CacheManifest(
                packages=new_packages, flavor_manifest_last_used=new_fmlu
            )
        )
        return live, time.monotonic() - start

    def _gc_survivors(
        self, manifest: _CacheManifest, cutoff: float
    ) -> tuple[set[str], dict[str, _CachedPackage]]:
        """Apply the survivor rule → (live flavor-manifest hashes, packages).

        An apverid entry survives iff pinned or recently used; within a
        survivor, each ``coord→hash`` ref survives iff its hash is pinned or
        recently used AND the flavor-manifest blob is still on disk
        (existence-aware: a vanished blob's ref is dropped + re-fetched
        later, and we avoid over-deleting the data of a manifest we can't
        enumerate).
        """
        live_fm: set[str] = set(self._pinned_fm_hashes)
        new_packages: dict[str, _CachedPackage] = {}
        for apverid, pkg in manifest.packages.items():
            if not (
                apverid in self._pinned_apverids or pkg.last_used >= cutoff
            ):
                continue
            new_coords: dict[str, str] = {}
            for coord, fm_hash in pkg.flavor_manifests.items():
                fm_survives = (
                    fm_hash in self._pinned_fm_hashes
                    or manifest.flavor_manifest_last_used.get(fm_hash, 0.0)
                    >= cutoff
                )
                if not fm_survives or self._locate_blob(fm_hash) is None:
                    continue
                new_coords[coord] = fm_hash
                live_fm.add(fm_hash)
            if new_coords:
                new_packages[apverid] = _CachedPackage(
                    flavor_manifests=new_coords, last_used=pkg.last_used
                )
        return live_fm, new_packages

    def _gc_reachable(self, live_fm: set[str]) -> set[str]:
        """Live set = live flavor-manifest blobs ∪ their reachable data blobs.

        Reachable data is discovered by reading each present flavor-manifest
        blob and collecting the data-blob hashes it references.
        """
        live: set[str] = set(live_fm)
        for fm_hash in live_fm:
            fm_path = self._locate_blob(fm_hash)
            if fm_path is None:
                continue
            try:
                with open(fm_path, 'rb') as infile:
                    parsed = json.loads(infile.read())
                for info in parsed['e'].values():
                    for comp in info.values():
                        live.add(comp['h'])
            except Exception as exc:
                logger.exception(
                    'Asset GC: error reading flavor-manifest %s; skipping.',
                    fm_hash,
                )
                strip_exception_tracebacks(exc)
        return live

    def _gc_sweep(
        self, root: str, live: set[str], deadline: float
    ) -> _GcSweepStats:
        """Delete writable-root blobs not in ``live``, within the budget.

        Shards are visited in rotated order from the persisted cursor;
        unlink is interleaved with the scan (visited garbage is gone even if
        cut off) and the cursor is advanced + persisted per shard so
        progress survives a cutoff and a fixed order can't perpetually stall.
        """
        sweep_start = time.monotonic()
        freed_files = 0
        freed_bytes = 0
        shards_done = 0
        cut_off = False
        cursor = self._read_gc_cursor()
        next_shard = cursor
        for i in range(_CAS_SHARD_COUNT):
            shard = (cursor + i) % _CAS_SHARD_COUNT
            shard_hex = f'{shard:02x}'
            shard_dir = os.path.join(root, shard_hex)
            if os.path.isdir(shard_dir):
                try:
                    entries = list(os.scandir(shard_dir))
                except OSError:
                    entries = []
                for entry in entries:
                    if shard_hex + entry.name in live:
                        continue
                    try:
                        size = entry.stat().st_size
                        os.unlink(entry.path)
                        freed_files += 1
                        freed_bytes += size
                    except OSError:
                        pass
                shards_done += 1
            next_shard = (shard + 1) % _CAS_SHARD_COUNT
            self._write_gc_cursor(next_shard)
            if time.monotonic() >= deadline:
                cut_off = True
                break
        return _GcSweepStats(
            freed_files=freed_files,
            freed_bytes=freed_bytes,
            shards_done=shards_done,
            cut_off=cut_off,
            next_shard=next_shard,
            sweep_secs=time.monotonic() - sweep_start,
        )

    def _read_gc_cursor(self) -> int:
        """Read the persisted rotating shard cursor (0 if absent/invalid)."""
        try:
            with open(self._gc_cursor_path, encoding='utf-8') as infile:
                value = int(infile.read().strip(), 16)
            if 0 <= value < _CAS_SHARD_COUNT:
                return value
        except OSError, ValueError:
            pass
        return 0

    def _write_gc_cursor(self, shard: int) -> None:
        """Persist the rotating shard cursor.

        Advisory only — losing it just re-scans already-clean shards next
        run (which re-confirm-live and delete nothing), so no ``fsync`` and
        failures are swallowed.
        """
        path = self._gc_cursor_path
        destdir = os.path.dirname(path)
        try:
            os.makedirs(destdir, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=destdir, prefix='.tmp_gc_')
            with os.fdopen(fd, 'w', encoding='utf-8') as outfile:
                outfile.write(f'{shard:02x}')
            os.replace(tmp, path)
        except OSError:
            pass
