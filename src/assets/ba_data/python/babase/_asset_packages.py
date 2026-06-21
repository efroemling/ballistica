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

# Apverids loaded by :func:`load_bundled_asset_packages` (one per
# bundled package). Test/wrapper code that needs to construct a
# qualified asset ref (``<apverid>:<asset>``) can read from here
# rather than hard-coding the date-suffixed dev snapshot.
_loaded_apverids: list[str] = []


def loaded_asset_package_apverids() -> list[str]:
    """Return the list of apverids registered from the bundle.

    Populated by ``load_bundled_asset_packages`` at startup; empty
    until the native bootstrapping handoff has run.
    """
    return list(_loaded_apverids)


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
        if apverid not in _loaded_apverids:
            _loaded_apverids.append(apverid)
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
