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

from __future__ import annotations

import os
import json
import time
import base64
import hashlib
import asyncio
import tempfile
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import assetmanagerlog as logger

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

if TYPE_CHECKING:
    from collections.abc import Callable

    from bacommon import securedata
    from bacommon.locale import Locale
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

#: The canonical asset-package buckets, in registration order.
_BUCKETS = ('constant', 'language', 'textures')

#: Per-bucket fallback flavor coord (or None) — used ONLY for the
#: builtin/projectconfig bootstrap package, whose fallbacks are
#: guaranteed bundled. Every other package is exact-or-fail. Single
#: fallback per bucket for now; :meth:`AssetSubsystem._fallback_coord`
#: wraps this so a fallback *chain* is a non-breaking later change.
_BUCKET_FALLBACKS: dict[str, str | None] = {
    'constant': None,  # No flavor dimension; 'constant' is always present.
    'language': 'language/eng',
    'textures': 'textures/fallback_v1_regular',
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

        # Texture quality is hard-coded for now; language is wired from the
        # real locale at resolve time; texture profile comes from the
        # _texture_profile property (headless-aware).
        self._texture_quality = 'regular'

        # Debug/repair affordance: when bundle reuse is disabled, the diff
        # ignores the bundle root so even bundled blobs are (re)downloaded
        # into the writable cache — lets the download+write leg be
        # exercised against an otherwise-fully-bundled package. Set via
        # BA_ASSET_NO_BUNDLE_REUSE=1 (test_game_run --asset-no-bundle-reuse).
        self._reuse_bundle = os.environ.get('BA_ASSET_NO_BUNDLE_REUSE') != '1'

    @override
    def on_app_running(self) -> None:
        # Register the GC pass as a shutdown task. It runs concurrently
        # with the rest of shutdown (the threadpool is still alive then;
        # it's torn down later in the atexit phase, so atexit is the wrong
        # home). v1 trigger is shutdown-only; a future on_app_suspend()
        # trigger will matter on mobile where clean shutdowns are rare.
        _babase.app.add_shutdown_task(self._run_gc())

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
        return os.path.join(
            self._writable_assets_root, filehash[:2], filehash[2:]
        )

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

    def _desired_coords(self, language: Locale) -> dict[str, str]:
        """The desired ``bucket -> coord`` for the active dimensions.

        Coords must be formed exactly as the build pipeline stores them in
        the manifests: ``constant``, ``language/<locale>``,
        ``textures/<profile>_<quality>``.
        """
        return {
            'constant': 'constant',
            'language': f'language/{language.value}',
            'textures': (
                f'textures/{self._texture_profile}_{self._texture_quality}'
            ),
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
        from babase._asset_packages import loaded_asset_package_apverids

        return apverid in loaded_asset_package_apverids()

    # ---------------------------------------------------------------------
    # Public API.

    async def resolve(
        self,
        apverids: list[str],
        *,
        allow_downloads: bool = True,
        on_download_starting: Callable[[], None] | None = None,
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

        try:
            return await self._resolve(
                apverids, allow_downloads, on_download_starting
            )
        finally:
            self._busy_lock.release()

    # ---------------------------------------------------------------------
    # Resolve internals.

    async def _resolve(
        self,
        apverids: list[str],
        allow_downloads: bool,
        on_download_starting: Callable[[], None] | None = None,
    ) -> ResolveResult:
        language = _babase.app.locale.current_locale
        now = time.time()
        logger.info(
            'Resolving %d asset-package(s) (downloads=%s): %s',
            len(apverids),
            allow_downloads,
            ', '.join(apverids),
        )
        loop = _babase.app.asyncio_loop
        pool = _babase.app.threadpool
        t_start = _babase.apptime()

        # Warm fast-path: if every desired flavor is already local, resolve
        # the whole set in a single off-thread pass — no per-package round-
        # trips, no download machinery, no network. The per-package async
        # path below is used only when something must actually be fetched.
        offline = await loop.run_in_executor(
            pool, self._resolve_offline_sync, apverids, language
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
        for apverid, coords in manifest_pkgs.items():
            self._pinned_apverids.add(apverid)
            self._pinned_fm_hashes.update(coords.values())
        await loop.run_in_executor(
            pool, self._commit_manifest, manifest_pkgs, now
        )

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
        register_specs: list[tuple[str, str, dict[str, dict[str, str]]]] = []
        manifest_pkgs: dict[str, dict[str, str]] = {}
        fell_back: dict[str, str] = {}
        for apverid in apverids:
            local, missing = self._scan_local(apverid, desired)
            if missing:
                # Not fully local; let the online path handle this set
                # (download desired flavors / builtin fallback / fail).
                return None
            result = self._finalize_one(
                apverid, desired, local, self._is_builtin(apverid)
            )
            manifest_pkgs[apverid] = result.coords
            for coord in result.coords:
                register_specs.append((apverid, coord, result.entries[coord]))
            fell_back.update(result.fell_back)
        return register_specs, manifest_pkgs, fell_back

    async def _resolve_online(
        self, apverids: list[str], language: Locale, allow_downloads: bool
    ) -> _ResolveAccum:
        """Per-package resolve with optional Tier-1 downloads + fallback.

        Used when the warm fast-path can't satisfy the set locally. Each
        package scans, optionally fetches missing flavors, and finalizes.
        """
        register_specs: list[tuple[str, str, dict[str, dict[str, str]]]] = []
        manifest_pkgs: dict[str, dict[str, str]] = {}
        fell_back: dict[str, str] = {}
        for apverid in apverids:
            result = await self._resolve_one(apverid, language, allow_downloads)
            manifest_pkgs[apverid] = result.coords
            for coord in result.coords:
                register_specs.append((apverid, coord, result.entries[coord]))
            fell_back.update(result.fell_back)
        return register_specs, manifest_pkgs, fell_back

    async def _resolve_one(
        self, apverid: str, language: Locale, allow_downloads: bool
    ) -> _OneResult:
        """Resolve one apverid's buckets to local-or-fetched flavors.

        Scans local coords, optionally does one Tier-1 download to obtain
        any desired flavors not present locally, then picks per bucket:
        desired-if-complete, else (builtin only) bundled-fallback, else
        fail.
        """
        loop = _babase.app.asyncio_loop
        pool = _babase.app.threadpool
        is_builtin = self._is_builtin(apverid)
        desired = self._desired_coords(language)

        # Scan local state (off-thread): which desired coords are already
        # complete on disk, and the full local coord→hash map.
        local_coords, missing_buckets = await loop.run_in_executor(
            pool, self._scan_local, apverid, desired
        )

        # If any desired flavor isn't local and downloads are allowed, do
        # one Tier-1 resolve + fetch to obtain the desired flavors.
        downloaded: dict[str, str] = {}
        if allow_downloads and missing_buckets:
            try:
                downloaded = await self._tier1_download(apverid, language)
            except AssetResolveError as exc:
                # The builtin/bootstrap package must still come up offline;
                # other packages are exact-or-fail. Log the underlying
                # reason either way (it's otherwise swallowed).
                logger.warning('%s: online resolve failed (%s).', apverid, exc)
                if not is_builtin:
                    raise

        # Finalize per-bucket selection + read registry entries (off-thread).
        # local ∪ just-downloaded — what's actually available to choose from.
        available = {**local_coords, **downloaded}
        return await loop.run_in_executor(
            pool, self._finalize_one, apverid, desired, available, is_builtin
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
        """Locally-known ``coord -> flavor-manifest hash`` (bundle ∪ cache)."""
        coords: dict[str, str] = {}
        coords.update(self._read_bundle_manifest().get(apverid, {}))
        pkg = self._load_manifest().packages.get(apverid)
        if pkg is not None:
            coords.update(pkg.flavor_manifests)
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
        except Exception:
            logger.exception('Error reading bundle manifest %s.', path)
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
        except Exception:
            logger.exception('Error reading flavor-manifest %s.', fm_hash)
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
        loop = _babase.app.asyncio_loop
        pool = _babase.app.threadpool
        # Downloads route through the connected node, which comes up a beat
        # after boot; wait briefly for it rather than failing a resolve
        # that raced the connection.
        await self._wait_for_node()
        # Capture the signed-in account handle on the logic thread; the
        # off-thread send enters its context so the resolve carries our
        # account (see _resolve_tier1). None → anonymous (PROD/public).
        plus = _babase.app.plus
        primary = plus.accounts.primary if plus is not None else None
        response = await loop.run_in_executor(
            pool, self._resolve_tier1, apverid, language, primary
        )
        if response.error is not None:
            msg = f'{apverid}: {response.error}'
            code = response.error_code
            # Raise a specific subclass for the cases callers branch on
            # (e.g. construct-mode prompting for sign-in). Carry the
            # server's raw message too so callers can show its wording.
            if code is AssetPackageResolveError.AUTH_REQUIRED:
                raise AssetAuthRequiredError(msg, code, response.error)
            if code is AssetPackageResolveError.ACCESS_DENIED:
                raise AssetAccessDeniedError(msg, code, response.error)
            raise AssetResolveError(msg, code, response.error)
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
            for info in parsed['e'].values():
                for comp in info.values():
                    data_needed[comp['h']] = comp['s']

        if fm_writes:
            await asyncio.gather(
                *[
                    loop.run_in_executor(pool, self._cas_write, h, d)
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
            host = self._node_host()
            if host is None:
                raise AssetResolveError(
                    f'{apverid}: not connected to a node; cannot download.'
                )
            token_header = self._encode_token(response.token)
            await asyncio.gather(
                *[
                    loop.run_in_executor(
                        pool, self._acquire_data_blob, host, token_header, h, s
                    )
                    for h, s in to_fetch
                ]
            )
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
            texture_quality=self._texture_quality,
        )
        if primary is not None:
            with primary:
                response = plus.cloud.send_message(msg)
        else:
            response = plus.cloud.send_message(msg)
        assert isinstance(response, ResolveAssetPackageResponse)
        return response

    def _node_host(self) -> str | None:
        """Address of the connected basn node, or None if not connected."""
        plus = _babase.app.plus
        if plus is None:
            return None
        # plus.cloud is a soft-loaded interface (Any to the base layer),
        # so pin the expected type here to satisfy mypy's return-Any check.
        addr: str | None = plus.cloud.get_connected_node_address()
        return addr

    async def _wait_for_node(self) -> None:
        """Wait (up to a timeout) for a connected node to download through.

        No-op if already connected. Registers a connectivity-changed
        callback (rather than polling) so we proceed the instant the node
        connects. On timeout we return anyway and let the subsequent
        resolve/fetch fail with a clear "not connected" error.
        """
        if self._node_host() is not None:
            return
        plus = _babase.app.plus
        if plus is None:
            return

        event = asyncio.Event()

        def _on_changed(connected: bool) -> None:
            # When connectivity comes up the node address is already set
            # (the connected primary session is assigned before the
            # connectivity-changed signal fires).
            if connected and self._node_host() is not None:
                event.set()

        reg = plus.cloud.on_connectivity_changed_callbacks.register(_on_changed)
        try:
            # Re-check now that we're registered, in case it connected
            # between the initial check and the registration.
            if self._node_host() is None:
                await asyncio.wait_for(event.wait(), timeout=_NODE_WAIT_SECONDS)
        except asyncio.TimeoutError:
            pass
        finally:
            # Hold `reg` until here so the callback stays registered for the
            # whole wait; dropping it unregisters (CallbackSet is
            # weakref-based).
            del reg

    @staticmethod
    def _encode_token(token: securedata.Archive) -> str:
        """Encode a capability token for the ``X-Asset-Token`` header.

        base64-urlsafe of the Archive's canonical JSON (HTTP headers don't
        carry raw JSON cleanly); mirrors the streamcall token encoding.
        """
        return (
            base64.urlsafe_b64encode(dataclass_to_json(token).encode())
            .rstrip(b'=')
            .decode('ascii')
        )

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
        for root in roots:
            path = os.path.join(root, filehash[:2], filehash[2:])
            try:
                st = os.stat(path)
            except OSError:
                continue
            if st.st_size == size:
                return True
            # Present but wrong size in this root; treat as absent.
        return False

    def _acquire_data_blob(
        self, host: str, token_header: str, filehash: str, size: int
    ) -> None:
        """Fetch one data blob from the node and atomically write it.

        ``GET https://{host}/casblob/{hash}?size={size}`` with the
        capability token; the bytes are verified + written by the shared
        atomic writer. Off-thread; blocking.
        """
        pool = _babase.app.net.urllib3pool
        url = f'https://{host}/casblob/{filehash}?size={size}'
        response = pool.request(
            'GET', url, headers={'X-Asset-Token': token_header}
        )
        if response.status != 200:
            raise AssetResolveError(
                f'casblob GET for {filehash} failed: HTTP {response.status}.'
            )
        self._cas_write(filehash, response.data)

    def _cas_write(self, filehash: str, data: bytes) -> None:
        """Atomically write a CAS blob into the writable root.

        sha256-verify → temp in the destination dir → ``fsync`` →
        ``os.replace`` (atomic on the same filesystem). A file at its CAS
        path is therefore always whole-and-correct (the "exists ⇒ intact"
        contract): a crash mid-write leaves only a temp file, never a
        partial blob at the final path. Off-thread; blocking.
        """
        actual = hashlib.sha256(data).hexdigest()
        if actual != filehash:
            raise AssetResolveError(
                f'CAS write hash mismatch for {filehash}: got {actual}.'
            )
        dest = self._writable_blob_path(filehash)
        destdir = os.path.dirname(dest)
        os.makedirs(destdir, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=destdir, prefix='.tmp_')
        try:
            with os.fdopen(fd, 'wb') as outfile:
                outfile.write(data)
                outfile.flush()
                os.fsync(outfile.fileno())
            os.replace(tmp, dest)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ---------------------------------------------------------------------
    # Cache manifest IO (off-thread; blocking).

    def _load_manifest(self) -> _CacheManifest:
        path = self._manifest_path
        try:
            with open(path, encoding='utf-8') as infile:
                return dataclass_from_json(_CacheManifest, infile.read())
        except FileNotFoundError:
            return _CacheManifest()
        except Exception:
            logger.exception(
                'Error loading asset cache manifest %s; starting fresh.', path
            )
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
        the threadpool, which is still alive during the shutdown-task phase.
        """
        try:
            try:
                await asyncio.wait_for(
                    self._busy_lock.acquire(),
                    timeout=_GC_BUSY_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning('Asset GC skipped: subsystem busy.')
                return
            try:
                loop = _babase.app.asyncio_loop
                pool = _babase.app.threadpool
                await loop.run_in_executor(pool, self._gc_blocking)
            finally:
                self._busy_lock.release()
        except Exception:
            logger.exception('Error during asset GC.')

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
            except Exception:
                logger.exception(
                    'Asset GC: error reading flavor-manifest %s; skipping.',
                    fm_hash,
                )
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
        except (OSError, ValueError):
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
