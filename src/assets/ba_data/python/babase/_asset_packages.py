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

from __future__ import annotations

import json
import logging
import os

import _babase

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
    """Populate the C++ asset-package registry from the bundled manifest.

    Called once during native bootstrapping. A missing ``manifest.json``
    is treated as "no bundled CAS assets" and logged at debug level —
    headless/server builds and tests may run without one.
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

    pkg_count = 0
    bucket_count = 0
    entry_count = 0
    for pkg in bundle.get('asset_packages', []):
        apverid = pkg['apverid']
        pkg_count += 1
        _loaded_apverids.append(apverid)
        for bucket_id, bucket_hash in pkg.get('bundled_buckets', {}).items():
            bucket_path = _cas_blob_path(data_dir, bucket_hash)
            with open(bucket_path, encoding='utf-8') as bfile:
                bucket = json.load(bfile)
            entries = bucket.get('h', {})
            _babase.register_asset_package_bucket(apverid, bucket_id, entries)
            bucket_count += 1
            entry_count += len(entries)

    _lifecyclelog.info(
        'asset-package CAS registry: loaded %d package(s),'
        ' %d bucket(s), %d entry(ies).',
        pkg_count,
        bucket_count,
        entry_count,
    )


def _cas_blob_path(data_dir: str, filehash: str) -> str:
    """Return the on-disk path for a CAS blob under the bundle root.

    Mirrors :func:`bacommon.bacloud.asset_file_cache_path` (single-level
    sharding by the first 2 hex chars). The C++ side derives the same
    path via :meth:`AssetPackageRegistry.CasBlobPath`; we duplicate the
    formula here only for the small subset of blobs we read at
    startup (bucket manifests).
    """
    return os.path.join(
        data_dir, 'ba_data', 'assets', filehash[:2], filehash[2:]
    )
