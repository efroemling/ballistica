# Released under the MIT License. See LICENSE for details.
#
"""Build-time seeding of the app's meta-scan cache."""

from efro.error import CleanError
from efro.terminal import Clr


def stage_seed(
    stagedir: str, projroot: str, asset_bundle_dir: str | None
) -> None:
    """Seed a staged apk's meta-scan cache, if it's a store build.

    Like the store asset bundle (and the pyc prewarm payload on other
    platforms), the seed is only worth its build time and package size
    for builds that go out to players. ``asset_bundle_dir`` is the
    staged bundle's cache-dir name (``store-mobile`` and the like),
    which is what staging tracks.
    """
    from batools.assetbundleprofiles import (
        get_profile,
        bundle_cache_dirname,
        form_factor_for_staging_platform,
    )

    store_dir = bundle_cache_dirname(
        get_profile('store'), form_factor_for_staging_platform('-android')
    )
    if asset_bundle_dir == store_dir:
        build_metascan_seed(stagedir, projroot)


def build_metascan_seed(stagedir: str, projroot: str) -> int:
    """Precompute a meta-scan cache seed for a staged build's Python.

    For builds that serve their Python straight out of a zip archive
    (Android apks). Entries are keyed by file contents, as the
    archive's entries will be, under the alias the app uses for its
    Python dir, so at runtime they match exactly the files they came
    from and give a first launch (no cache yet) a warm start; see
    ``bacommon.metascancache.ScanCache``. Returns the entry count.
    """
    from bacommon.metascan import (
        APP_SCAN_ALIAS,
        DEPRECATED_EXPORT_SHORTCUTS,
        write_seed,
    )
    from batools.version import get_current_api_version

    count = write_seed(
        f'{stagedir}/ba_data/python',
        APP_SCAN_ALIAS,
        f'{stagedir}/ba_data/metascan_seed.json',
        expected_api_version=get_current_api_version(projroot),
        deprecated_export_shortcuts=DEPRECATED_EXPORT_SHORTCUTS,
    )
    # The app ships hundreds of modules (409 as of 10/2026); a nearly
    # empty seed means the scan found the wrong dir or nothing cached.
    if count < 100:
        raise CleanError(
            f'Meta-scan seed has only {count} entries; expected hundreds.'
            f' Is {stagedir}/ba_data/python staged correctly?'
        )
    print(f'{Clr.BLU}Wrote meta-scan seed ({count} entries).{Clr.RST}')
    return count
