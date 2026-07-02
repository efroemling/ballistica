# Released under the MIT License. See LICENSE for details.
#
"""Bundle-manifest loading for the asset-packages CAS pipeline.

The native build pipeline stages a top-level ``ba_data/manifest.json``
plus per-bucket manifest blobs in the CAS store
(``ba_data/assets/<aa>/<rest>``). At startup we parse those and push
the resolved ``logical_path → CAS hash`` mappings into the C++
:class:`AssetPackageRegistry` via
:func:`_babase.register_asset_package_bucket`, so subsequent
``gettexture(``'apverid:asset'``)``-style lookups can resolve
GIL-free in C++.
"""

import json
import logging
import os
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Any

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
