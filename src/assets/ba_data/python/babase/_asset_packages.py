# Released under the MIT License. See LICENSE for details.
#
"""Bundle-manifest loading for the asset-packages CAS pipeline.

The native build pipeline stages a top-level ``ba_data/manifest.json``
plus per-bucket manifest blobs in the CAS store
(``ba_data/assets/<aa>/<rest>``). At startup we parse those and push
the resolved ``logical_path → CAS hash`` mappings into the C++
:class:`AssetPackageRegistry` via
:func:`_babase.register_asset_package_bucket`, so subsequent
``aptextureget(``'apverid:asset'``)``-style lookups can resolve
GIL-free in C++.
"""

import json
import logging
import os
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Any

    from bacommon.assetspec import AssetBucketKind

_lifecyclelog = logging.getLogger('ba.lifecycle')

# Apverids of the BUILTIN (bundled) packages, populated at startup by
# :func:`load_bundled_asset_packages` (one per bundled package).
# Membership here means "builtin", which drives builtin-only resolve
# semantics (bundled-fallback flavor; see ``AssetSubsystem._is_builtin``)
# and qualified-ref construction -- so a runtime-resolved *non-builtin*
# package must NOT land here (see ``_resolved_apverids``).
_builtin_apverids: list[str] = []

# Apverids of non-builtin packages brought in by a runtime resolve
# (``babase.App.assets.resolve``). Tracked separately so the language
# table merges their strings too WITHOUT making them count as builtin.
_resolved_apverids: list[str] = []


# Set once construct-mode has resolved every required asset-package (see
# :func:`mark_construct_complete`). Until then, only the construct package
# itself is legitimately loadable.
_g_construct_complete = False

# The construct/builtin package's apverid, cached on first check.
_g_construct_apverid: str | None = None


def mark_construct_complete() -> None:
    """Note that construct-mode has finished resolving asset-packages.

    Called from construct-mode's hand-off to the real app-mode -- the one
    point at which every package the meta-scan requires is guaranteed
    resolved and registered. Opens the gate enforced by
    :func:`check_asset_package_load`.

    Also opens the native gate
    (``AssetPackageRegistry::CheckPreConstructAccess``), which covers the
    load paths that never touch Python: direct C++ ``Assets::Get*``
    calls, and scene_v1 wire traffic / replays arriving as legacy bare
    names. Both open here so they cannot disagree about when bring-up
    ended.
    """
    global _g_construct_complete  # pylint: disable=global-statement
    _g_construct_complete = True
    _babase.mark_construct_assets_complete()

    # Logged because this is otherwise an invisible state change on a
    # load-ordering invariant -- and because it is the marker to key any
    # 'did bring-up finish?' check on: it sits on ba.lifecycle alongside
    # the rest of the boot trace, where construct-mode's own hand-off
    # log is over on ba.assetmanager.
    _lifecyclelog.debug('Construct-mode asset gate opened.')


def construct_assets_complete() -> bool:
    """Whether construct-mode has finished resolving asset-packages.

    For callers that need to *avoid* doing something too early rather
    than be scolded for it -- notably the dev console's AppModes tab,
    which would otherwise exec app-mode modules (wrapper modules
    included) while their packages are still unresolved.
    """
    return _g_construct_complete


def check_asset_package_load(apverid: str, path: str) -> None:
    """Flag an asset load from a package that is not up yet.

    Before construct-mode hands off, the only package guaranteed
    registered is the construct/builtin one; loading from any other is a
    bug even when it happens to work. It works whenever the package is
    *bundled* into this particular build (bundled packages register
    during native bootstrapping, via
    ``load_bundled_asset_packages()``), so the same code silently
    succeeds or fails depending on the build's bundle profile -- and
    headless never notices at all, since texture loads there
    short-circuit before the package registry is consulted. Hence this
    check keys on the construct package rather than on what is merely
    registered.

    Raises on debug builds so the offending call site fails loudly in
    dev and CI; logs an error elsewhere. The underlying failure is worse
    either way -- a dead ``on_app_loading`` hook, or an asset that goes
    permanently ``kFailed`` and draws blank forever.

    Hold the wrapper's *reference* and load it later (on first access,
    once the ui that wants it exists) rather than loading at
    construction time; see :class:`bascenev1.Level`.
    """
    if _g_construct_complete:
        return

    global _g_construct_apverid  # pylint: disable=global-statement
    if _g_construct_apverid is None:
        # Deferred: this module is imported while babase itself is still
        # coming up, well before the wrapper is importable.
        # pylint: disable-next=cyclic-import
        from babase import _builtinassets

        # Package identity for the construct pin, not a path.
        # pylint: disable-next=protected-access
        _g_construct_apverid = _builtinassets._ASSET_PACKAGE

    if apverid == _g_construct_apverid:
        return

    msg = (
        f"Asset '{apverid}:{path}' loaded before construct-mode finished"
        f' resolving asset-packages; only {_g_construct_apverid} is'
        f' available this early. Hold the wrapper reference and load it'
        f' on first use instead.'
    )
    # Keyed on debug-build, matching the native gate
    # (``AssetPackageRegistry::CheckPreConstructAccess``) so the two
    # cannot disagree about how loud to be. Note the *check* itself runs
    # everywhere -- release builds log this error rather than skipping
    # it; only the raise-vs-log severity varies.
    if _babase.app.env.debug_build:
        raise RuntimeError(msg)
    _lifecyclelog.error(msg)


def builtin_asset_package_apverids() -> list[str]:
    """Apverids of the bundled/builtin packages (registered at startup).

    The builtin-only set: drives ``_is_builtin`` (bundled-fallback resolve
    semantics) and qualified-ref construction. Use
    :func:`loaded_asset_package_apverids` instead for "every loaded
    package" (e.g. rebuilding the language table).
    """
    return list(_builtin_apverids)


def loaded_asset_package_apverids() -> list[str]:
    """Return every currently-loaded apverid: builtin + runtime-resolved.

    This is the set the native language table is rebuilt from (so every
    loaded package's strings merge) and that a locale switch re-resolves.
    Builtins are populated at startup by ``load_bundled_asset_packages``;
    runtime-resolved packages are added by ``register_resolved_apverids``
    after a successful ``resolve``. Distinct from
    ``builtin_asset_package_apverids``, which alone must drive
    builtin-only behavior.
    """
    out = list(_builtin_apverids)
    out.extend(a for a in _resolved_apverids if a not in _builtin_apverids)
    return out


def asset_package_bucket_paths(
    apverid: str, kind: 'AssetBucketKind'
) -> list[str] | None:
    """Canonical sorted logical paths in a loaded package's bucket.

    This is the list integer asset references address -- doc-ui's flat
    refs and scene_v1's indexed wire refs both index into it -- and it
    is portable across flavors by the identical-key-set invariant
    (asset-packages D23/D24), so two ends holding different texture
    profiles still agree on what an index means.

    ``None`` means the package isn't registered, which is a
    resolve-ordering fault worth surfacing; distinguish it from ``[]``,
    a package that genuinely has no assets of that kind.
    """
    return _babase.get_asset_package_bucket_paths(apverid, kind.value)


def asset_package_string_count(apverid: str) -> int | None:
    """How many language-strings a loaded package holds, this locale.

    The size of the canonical sorted name list that string indices
    address -- enough to fold a flat wire index back into the
    ``(package, string)`` pair the native decoder consumes, without
    surfacing the names themselves.

    ``None`` when the package has no language table loaded, which must
    be distinguished from a package holding zero strings: treating the
    first as zero would silently shift every later package's offset.
    """
    return _babase.get_asset_package_string_count(apverid)


def register_resolved_apverids(apverids: list[str]) -> None:
    """Record runtime-resolved (non-builtin) packages as loaded.

    Called after a successful downloading/offline ``resolve`` commit so
    :meth:`~babase.AssetSubsystem._reload_language` merges the package's
    ``language`` bucket into the native table automatically (no caller-side
    reload needed). Builtins are skipped (already loaded) and duplicates
    ignored, so it's safe to pass the whole resolve batch.
    """
    for apverid in apverids:
        if apverid in _builtin_apverids or apverid in _resolved_apverids:
            continue
        _resolved_apverids.append(apverid)


def load_bundled_asset_packages() -> None:
    """Register builtin asset-packages at their best LOCAL flavor.

    Called once during native bootstrapping, *before* ``StartLoading``'s
    builtin asset loads. Discovers the builtin packages from the bundled
    ``manifest.json`` (its keys) and hands them to
    :meth:`~babase.AssetSubsystem.resolve_local`, which registers the ideal
    flavor of each when its blobs are already cached (warm starts) and the
    bundled fallback otherwise (cold starts -- until a later downloading
    resolve fetches and swaps the ideal flavor in).

    A missing ``manifest.json`` is treated as "no bundled CAS assets" and
    logged at debug level -- headless/server builds and tests may run without
    one.
    """
    data_dir = _babase.app.env.data_directory
    bundle_path = os.path.join(data_dir, 'ba_data', 'manifest.json')
    if not os.path.isfile(bundle_path):
        _lifecyclelog.debug(
            'No bundled asset-package manifest at %s; skipping CAS init.',
            bundle_path,
        )
        return

    with open(bundle_path, encoding='utf-8') as infile:
        bundle = json.load(infile)

    # The bundled packages are builtin by definition. Record them (so
    # _is_builtin and ref-construction see them) before resolving, then let
    # the AssetSubsystem register the best-local flavor of each.
    apverids = [apverid for apverid, _ in _iter_manifest_packages(bundle)]
    for apverid in apverids:
        if apverid not in _builtin_apverids:
            _builtin_apverids.append(apverid)
    if apverids:
        # resolve_local registers the packages' buckets (including
        # ``language/<locale>``) and rebuilds the native language string
        # table from them — so this is what actually populates the table
        # at startup (the boot-time ``setlanguage`` may have run earlier,
        # before any packages were loaded).
        _babase.app.assets.resolve_local(apverids)


def _iter_manifest_packages(
    bundle: dict[str, Any],
) -> list[tuple[str, dict[str, str]]]:
    """Return ``(apverid, flavor_manifests)`` pairs from a parsed manifest."""
    return [
        (apverid, entry['flavor_manifests'])
        for apverid, entry in bundle.get('asset_package_versions', {}).items()
    ]
