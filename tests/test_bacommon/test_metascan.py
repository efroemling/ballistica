# Released under the MIT License. See LICENSE for details.
#
"""Tests for the ``# ba_meta`` directive scanner."""

import os
import zipfile
import zipimport
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from bacommon.metascan import (
    DirectoryScan,
    get_source_api_requirement,
    write_seed,
)
from bacommon.metascancache import ScanCache

if TYPE_CHECKING:
    import pytest

    from bacommon.metascan import ScanResults

API = 9

_WELL_FORMED_MOD = f"""# ba_meta require api {API}

# ba_meta export babase.Plugin
class BarePlugin:
    pass


# ba_meta export babase.Plugin
class BasedPlugin(BaseThing):
    pass


# ba_meta export babase.Plugin
class GenericPlugin[T](BaseThing):
    pass
"""

_PKG_INIT = f"""# ba_meta require api {API}

# ba_meta require asset-package 4321
"""

_NESTED_EXPORT = """# ba_meta export babase.Plugin
class NestedPlugin(BaseThing):
    pass
"""


def _build_tree(root: Path) -> None:
    """Lay down a representative scan tree under root."""
    root.mkdir(parents=True, exist_ok=True)
    (root / 'checkmod.py').write_text(_WELL_FORMED_MOD)
    pkg = root / 'mypkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text(_PKG_INIT)
    (pkg / 'nested.py').write_text(_NESTED_EXPORT)
    # Wrong-api module: skipped & recorded.
    (root / 'oldapi.py').write_text(f'# ba_meta require api {API - 1}\n')
    # Top-level module with no meta lines at all: ignored.
    (root / 'nometa.py').write_text('x = 1\n')
    # Namespace-style dir (no __init__): not scanned.
    nspkg = root / 'nspkg'
    nspkg.mkdir()
    (nspkg / 'x.py').write_text(f'# ba_meta require api {API}\n')


def _check_tree_results(results: ScanResults) -> None:
    assert results.exports.get('babase.Plugin') == [
        'checkmod.BarePlugin',
        'checkmod.BasedPlugin',
        'checkmod.GenericPlugin',
        'mypkg.nested.NestedPlugin',
    ]
    assert results.asset_packages == {4321: ['mypkg']}
    assert results.incorrect_api_modules == ['oldapi']
    assert not results.announce_errors_occurred


def _scan(paths: list[str]) -> ScanResults:
    scan = DirectoryScan(paths=paths, expected_api_version=API)
    scan.run()
    return scan.results


def test_directory_scan(tmp_path: Path) -> None:
    """Scan a plain directory tree."""
    _build_tree(tmp_path / 'python')
    _check_tree_results(_scan([str(tmp_path / 'python')]))


def test_zip_scan(tmp_path: Path) -> None:
    """Scanning inside a zip archive must match the dir scan."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)

    # Both forms: modules at archive root and under a subdir.
    zsub = tmp_path / 'bundle.zip'
    with zipfile.ZipFile(zsub, 'w') as zf:
        for fpath in srcdir.rglob('*.py'):
            zf.write(fpath, Path('python') / fpath.relative_to(srcdir))
    _check_tree_results(_scan([f'{zsub}/python']))

    zflat = tmp_path / 'flat.zip'
    with zipfile.ZipFile(zflat, 'w') as zf:
        for fpath in srcdir.rglob('*.py'):
            zf.write(fpath, fpath.relative_to(srcdir))
    _check_tree_results(_scan([str(zflat)]))


def test_missing_paths_ignored(tmp_path: Path) -> None:
    """Nonexistent dirs and non-zip files are skipped quietly."""
    notzip = tmp_path / 'notazip.zip'
    notzip.write_text('nope')
    results = _scan([str(tmp_path / 'nonexistent'), str(notzip)])
    assert not results.exports
    assert not results.announce_errors_occurred


def test_bad_content_announces(tmp_path: Path) -> None:
    """Malformed tags and unreadable modules set the announce flag."""
    root = tmp_path / 'python'
    pkg = root / 'mypkg'
    pkg.mkdir(parents=True)
    (pkg / '__init__.py').write_text(f'# ba_meta require api {API}\n')
    # Bare directive-less tag: unrecognized-statement warning.
    (pkg / 'bare.py').write_text('# ba_meta\n')
    # Top-level module with meta lines but no valid api line:
    # ignored with a warning.
    (root / 'noapi.py').write_text('# ba_meta export babase.Plugin\n')
    results = _scan([str(root)])
    assert results.announce_errors_occurred
    assert 'babase.Plugin' not in results.exports

    # Undecodable module: error logged + announced; rest still scans.
    root2 = tmp_path / 'python2'
    root2.mkdir()
    (root2 / 'good.py').write_text(_WELL_FORMED_MOD)
    (root2 / 'bad.py').write_bytes(b'# ba_meta require api 9\n\xff\xfe\n')
    results2 = _scan([str(root2)])
    assert results2.announce_errors_occurred
    assert results2.exports.get('babase.Plugin') == [
        'good.BarePlugin',
        'good.BasedPlugin',
        'good.GenericPlugin',
    ]


def test_extras_event(tmp_path: Path) -> None:
    """expects_extras blocks run() until set_extras() arrives."""
    base = tmp_path / 'base'
    _build_tree(base)
    extra = tmp_path / 'extra'
    extra.mkdir()
    (extra / 'extramod.py').write_text(
        f'# ba_meta require api {API}\n'
        '\n'
        '# ba_meta export babase.Plugin\n'
        'class ExtraPlugin(BaseThing):\n'
        '    pass\n'
    )
    scan = DirectoryScan(
        paths=[str(base)], expected_api_version=API, expects_extras=True
    )
    timer = threading.Timer(0.2, scan.set_extras, args=[[str(extra)]])
    timer.start()
    scan.run()
    assert 'extramod.ExtraPlugin' in scan.results.exports['babase.Plugin']


def _cached_scan(
    paths: list[str],
    cachefile: Path,
    frozen_salt: str | None = 'build 1',
    api: int = API,
) -> tuple[ScanResults, ScanCache]:
    """Scan through a cache persisted at cachefile (as the app does)."""
    cache = ScanCache.load(str(cachefile), frozen_salt)
    scan = DirectoryScan(paths=paths, expected_api_version=api, cache=cache)
    scan.run()
    cache.save(str(cachefile))
    return scan.results, cache


def _zip_tree(srcdir: Path, zpath: Path) -> None:
    with zipfile.ZipFile(zpath, 'w') as zf:
        for fpath in sorted(srcdir.rglob('*.py')):
            zf.write(fpath, Path('python') / fpath.relative_to(srcdir))


def test_cache_matches_uncached(tmp_path: Path) -> None:
    """Cached scans give exactly the uncached results (dirs and zips)."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    zpath = tmp_path / 'bundle.zip'
    _zip_tree(srcdir, zpath)
    cachefile = tmp_path / 'cache.json'
    for paths in ([str(srcdir)], [f'{zpath}/python']):
        cachefile.unlink(missing_ok=True)
        uncached = _scan(paths)
        first, cache1 = _cached_scan(paths, cachefile)
        second, cache2 = _cached_scan(paths, cachefile)
        assert first == uncached
        assert second == uncached
        _check_tree_results(second)
        assert cache1.hits == 0 and cache1.misses > 0
        # Everything quiet comes from the cache the second time; only
        # the wrong-api module (which warns) gets read again.
        assert cache2.misses == 1
        assert cache2.hits == cache1.misses - 1


def test_cache_skips_reads(tmp_path: Path) -> None:
    """A fully cached scan doesn't read module sources at all."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    (srcdir / 'oldapi.py').unlink()  # (Warns, so is never cached.)
    cachefile = tmp_path / 'cache.json'
    _cached_scan([str(srcdir)], cachefile)

    # Make every source unreadable; a cached scan must not care.
    pyfiles = list(srcdir.rglob('*.py'))
    for fpath in pyfiles:
        fpath.chmod(0)
    try:
        results, cache = _cached_scan([str(srcdir)], cachefile)
    finally:
        for fpath in pyfiles:
            fpath.chmod(0o644)
    assert cache.misses == 0
    assert results.exports['babase.Plugin'] == [
        'checkmod.BarePlugin',
        'checkmod.BasedPlugin',
        'checkmod.GenericPlugin',
        'mypkg.nested.NestedPlugin',
    ]


def test_cache_sees_edits(tmp_path: Path) -> None:
    """Edited files get rescanned (size or mtime changes)."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    cachefile = tmp_path / 'cache.json'
    _cached_scan([str(srcdir)], cachefile)

    # Different size.
    (srcdir / 'mypkg' / 'nested.py').write_text(
        _NESTED_EXPORT.replace('NestedPlugin', 'RenamedNestedPlugin')
    )
    results, _ = _cached_scan([str(srcdir)], cachefile)
    assert (
        'mypkg.nested.RenamedNestedPlugin' in results.exports['babase.Plugin']
    )

    # Same size, different contents; only the mtime moves.
    nested = srcdir / 'mypkg' / 'nested.py'
    stat = nested.stat()
    nested.write_text(
        _NESTED_EXPORT.replace('NestedPlugin', 'ReNamedNestedPlugin')
    )
    assert nested.stat().st_size == stat.st_size
    os.utime(nested, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    results, _ = _cached_scan([str(srcdir)], cachefile)
    assert (
        'mypkg.nested.ReNamedNestedPlugin' in results.exports['babase.Plugin']
    )

    # A new module shows up; a deleted one goes away.
    (srcdir / 'checkmod.py').unlink()
    (srcdir / 'newmod.py').write_text(_WELL_FORMED_MOD)
    results, _ = _cached_scan([str(srcdir)], cachefile)
    exports = results.exports['babase.Plugin']
    assert not any(e.startswith('checkmod.') for e in exports)
    assert 'newmod.BarePlugin' in exports


def test_cache_zip_content_change(tmp_path: Path) -> None:
    """A rebuilt archive with changed contents gets rescanned."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    zpath = tmp_path / 'bundle.zip'
    _zip_tree(srcdir, zpath)
    cachefile = tmp_path / 'cache.json'
    _cached_scan([f'{zpath}/python'], cachefile)

    # Same-size edit, rebuilt in place: only the entry's CRC differs.
    (srcdir / 'mypkg' / 'nested.py').write_text(
        _NESTED_EXPORT.replace('NestedPlugin', 'ReNamedNestedPlugin')
    )
    zpath.unlink()
    _zip_tree(srcdir, zpath)
    # zipimport caches archive directories by path; a real reinstall
    # comes with a fresh process, so drop that here.
    # pylint: disable=protected-access
    zipimport._zip_directory_cache.pop(str(zpath), None)  # type: ignore
    results, cache = _cached_scan([f'{zpath}/python'], cachefile)
    assert (
        'mypkg.nested.ReNamedNestedPlugin' in results.exports['babase.Plugin']
    )
    # Untouched entries still came from the cache.
    assert cache.hits > 0


def test_cache_frozen_mtimes(tmp_path: Path) -> None:
    """Frozen mtimes (flatpak 0, nix 1) key by the salt instead."""
    for frozen_ns in (0, 1_000_000_000):
        srcdir = tmp_path / f'python{frozen_ns}'
        _build_tree(srcdir)
        for fpath in srcdir.rglob('*.py'):
            os.utime(fpath, ns=(frozen_ns, frozen_ns))
        cachefile = tmp_path / f'cache{frozen_ns}.json'

        # Without a salt, frozen files are never cached.
        _cached_scan([str(srcdir)], cachefile, None)
        results, cache = _cached_scan([str(srcdir)], cachefile, None)
        assert cache.hits == 0
        _check_tree_results(results)

        # With one, they're cached for as long as it stays the same.
        _cached_scan([str(srcdir)], cachefile, 'build 1')
        results, cache = _cached_scan([str(srcdir)], cachefile, 'build 1')
        assert cache.hits > 0
        _check_tree_results(results)

        # A same-size, same-mtime edit only shows up with a new salt
        # (frozen installs only change along with their version).
        nested = srcdir / 'mypkg' / 'nested.py'
        nested.write_text(
            _NESTED_EXPORT.replace('NestedPlugin', 'ReNamedNestedPlugin')
        )
        os.utime(nested, ns=(frozen_ns, frozen_ns))
        results, _ = _cached_scan([str(srcdir)], cachefile, 'build 2')
        assert 'mypkg.nested.ReNamedNestedPlugin' in (
            results.exports['babase.Plugin']
        )


def test_cache_repeats_warnings(tmp_path: Path) -> None:
    """Modules that warn are never cached, so they warn every scan."""
    root = tmp_path / 'python'
    pkg = root / 'mypkg'
    pkg.mkdir(parents=True)
    (pkg / '__init__.py').write_text(f'# ba_meta require api {API}\n')
    (pkg / 'bare.py').write_text('# ba_meta\n')
    (root / 'oldapi.py').write_text(f'# ba_meta require api {API - 1}\n')
    cachefile = tmp_path / 'cache.json'
    for _ in range(2):
        results, _cache = _cached_scan([str(root)], cachefile)
        assert results.announce_errors_occurred
        assert results.incorrect_api_modules == ['oldapi']


def test_cache_invalidation(tmp_path: Path) -> None:
    """Scanner-setting changes start fresh; junk is ignored."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    cachefile = tmp_path / 'cache.json'
    _cached_scan([str(srcdir)], cachefile, 'build 1')

    # A new app version (salt) doesn't matter for ordinary files: their
    # own identities say whether they changed.
    _, cache = _cached_scan([str(srcdir)], cachefile, 'build 2')
    assert cache.hits > 0

    # Different expected api version: outcomes differ, so no reuse.
    results, cache = _cached_scan(
        [str(srcdir)], cachefile, 'build 2', api=API - 1
    )
    assert cache.hits == 0
    assert 'oldapi' not in results.incorrect_api_modules

    cachefile.write_text('{not json')
    results, cache = _cached_scan([str(srcdir)], cachefile)
    assert cache.hits == 0
    _check_tree_results(results)


def _aliased_scan(
    path: str, cache: ScanCache, alias: str = 'app'
) -> ScanResults:
    scan = DirectoryScan(
        paths=[path],
        expected_api_version=API,
        cache=cache,
        path_aliases={path: alias},
    )
    scan.run()
    return scan.results


def test_cache_survives_moves(tmp_path: Path) -> None:
    """Aliased entries still apply after their scan dir moves."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    cachefile = tmp_path / 'cache.json'
    cache = ScanCache.load(str(cachefile))
    _aliased_scan(str(srcdir), cache)
    cache.save(str(cachefile))

    moved = tmp_path / 'elsewhere' / 'python'
    moved.parent.mkdir()
    srcdir.rename(moved)  # (Keeps mtimes.)
    cache = ScanCache.load(str(cachefile))
    results = _aliased_scan(str(moved), cache)
    _check_tree_results(results)
    assert cache.misses == 1  # (Just the warning-emitting oldapi.)


def test_seed(tmp_path: Path) -> None:
    """A build-time seed warms a cacheless scan of the zipped files."""
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    seedfile = tmp_path / 'seed.json'
    count = write_seed(
        str(srcdir), 'app', str(seedfile), expected_api_version=API
    )
    assert count > 0

    # Ship it zipped, somewhere else entirely (like an apk install).
    zpath = tmp_path / 'install-x7f' / 'base.apk'
    zpath.parent.mkdir()
    _zip_tree(srcdir, zpath)
    cachefile = tmp_path / 'cache.json'
    cache = ScanCache.load(str(cachefile))
    assert cache.empty
    assert cache.load_seed(str(seedfile))
    results = _aliased_scan(f'{zpath}/python', cache)
    _check_tree_results(results)
    assert cache.seed_hits == count
    assert cache.misses == 1  # (Just the warning-emitting oldapi.)

    # The seed's entries carry on in the cache proper.
    cache.save(str(cachefile))
    cache = ScanCache.load(str(cachefile))
    assert not cache.empty
    _aliased_scan(f'{zpath}/python', cache)
    assert cache.hits == count and cache.seed_hits == 0

    # A seed that doesn't match a file's contents just doesn't apply.
    nested = srcdir / 'mypkg' / 'nested.py'
    nested.write_text(
        _NESTED_EXPORT.replace('NestedPlugin', 'ReNamedNestedPlugin')
    )
    zpath2 = tmp_path / 'install-q2z' / 'base.apk'
    zpath2.parent.mkdir()
    _zip_tree(srcdir, zpath2)
    cache = ScanCache()
    cache.load_seed(str(seedfile))
    results = _aliased_scan(f'{zpath2}/python', cache)
    assert 'mypkg.nested.ReNamedNestedPlugin' in (
        results.exports['babase.Plugin']
    )
    assert cache.seed_hits == count - 1

    # Nor does one computed under other scan settings.
    seedfile2 = tmp_path / 'seed2.json'
    write_seed(str(srcdir), 'app', str(seedfile2), expected_api_version=API - 1)
    cache = ScanCache()
    cache.load_seed(str(seedfile2))
    _aliased_scan(f'{zpath2}/python', cache)
    assert cache.hits == 0

    # Seeds can be read from inside an archive too (as from an apk).
    zseed = tmp_path / 'seeded.apk'
    with zipfile.ZipFile(zseed, 'w') as zf:
        zf.write(seedfile, 'ba_data/metascan_seed.json')
    cache = ScanCache()
    assert cache.load_seed(f'{zseed}/ba_data/metascan_seed.json')


def test_seed_after_update(tmp_path: Path) -> None:
    """After an app update, the new build's seed fills in what changed.

    Unchanged app files and the user's mods keep coming from the cache;
    nothing gets rescanned.
    """
    srcdir = tmp_path / 'python'
    _build_tree(srcdir)
    mods = tmp_path / 'mods'
    mods.mkdir()
    (mods / 'mymod.py').write_text(_WELL_FORMED_MOD)

    def _scan_install(apkdir: Path, cache: ScanCache) -> ScanResults:
        apppath = str(apkdir / 'base.apk' / 'python')
        scan = DirectoryScan(
            paths=[apppath, str(mods)],
            expected_api_version=API,
            cache=cache,
            path_aliases={apppath: 'app', str(mods): 'user'},
        )
        scan.run()
        return scan.results

    # Build 1, installed and launched once (from its seed).
    seed1 = tmp_path / 'seed1.json'
    write_seed(str(srcdir), 'app', str(seed1), expected_api_version=API)
    install1 = tmp_path / 'install1'
    install1.mkdir()
    _zip_tree(srcdir, install1 / 'base.apk')
    cachefile = tmp_path / 'cache.json'
    cache = ScanCache.load(str(cachefile), 'build 1')
    assert cache.empty
    cache.load_seed(str(seed1))
    _scan_install(install1, cache)
    cache.save(str(cachefile))

    # Same build again: no install change, so no seed needed.
    cache = ScanCache.load(str(cachefile), 'build 1')
    assert not cache.install_changed

    # Build 2 changes one app file and ships its own seed.
    (srcdir / 'mypkg' / 'nested.py').write_text(
        _NESTED_EXPORT.replace('NestedPlugin', 'ReNamedNestedPlugin')
    )
    seed2 = tmp_path / 'seed2.json'
    write_seed(str(srcdir), 'app', str(seed2), expected_api_version=API)
    install2 = tmp_path / 'install2'
    install2.mkdir()
    _zip_tree(srcdir, install2 / 'base.apk')

    cache = ScanCache.load(str(cachefile), 'build 2')
    assert not cache.empty and cache.install_changed
    cache.load_seed(str(seed2))
    results = _scan_install(install2, cache)
    exports = results.exports['babase.Plugin']
    assert 'mypkg.nested.ReNamedNestedPlugin' in exports
    assert 'mymod.BarePlugin' in exports
    assert cache.seed_hits == 1  # (Just the changed file.)
    assert cache.misses == 1  # (Just the warning-emitting oldapi.)

    # And it records the new install, so next time is seed-free.
    cache.save(str(cachefile))
    cache = ScanCache.load(str(cachefile), 'build 2')
    assert not cache.install_changed
    _scan_install(install2, cache)
    assert cache.seed_hits == 0 and cache.misses == 1


def test_cache_warnings(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Things going wrong in the wild get noted, not silently eaten."""
    import bacommon.metascan

    srcdir = tmp_path / 'python'
    _build_tree(srcdir)

    # Missing cache file: normal, quiet.
    caplog.clear()
    cache = ScanCache.load(str(tmp_path / 'nope.json'))
    assert cache.empty and not caplog.records

    # Corrupt one: warned about.
    bad = tmp_path / 'bad.json'
    bad.write_text('{not json')
    caplog.clear()
    ScanCache.load(str(bad))
    assert any('corrupt' in r.getMessage() for r in caplog.records)

    # Misses get tallied per scan-path alias.
    cache = ScanCache()
    _aliased_scan(str(srcdir), cache, alias='app')
    assert cache.misses_by_alias == {'app': cache.misses}

    # zipimport internals not looking as expected: scanning still works,
    # caching of zip contents doesn't, and we say so (once).
    zpath = tmp_path / 'bundle.zip'
    _zip_tree(srcdir, zpath)

    def _broken_toc(finder: zipimport.zipimporter) -> dict:
        del finder  # Unused.
        raise RuntimeError('internals changed')

    monkeypatch.setattr(bacommon.metascan, '_zip_toc', _broken_toc)
    monkeypatch.setattr(bacommon.metascan, '_g_warned_zip_identity', False)
    caplog.clear()
    cache = ScanCache()
    results = _aliased_scan(f'{zpath}/python', cache)
    _check_tree_results(results)
    assert cache.hits == 0 and cache.misses == 0  # (No keys at all.)
    warnings = [
        r for r in caplog.records if 'zipimport internals' in r.getMessage()
    ]
    assert len(warnings) == 1


def test_get_source_api_requirement() -> None:
    """String-level api-requirement parsing."""
    assert get_source_api_requirement('# ba_meta require api 9\n') == 9
    assert get_source_api_requirement('x = 1\n') is None
    # Indented / embedded / malformed / ambiguous forms don't count.
    assert get_source_api_requirement('  # ba_meta require api 9\n') is None
    assert get_source_api_requirement("s = '# ba_meta require api 9'\n") is None
    assert get_source_api_requirement('# ba_meta require api 10x\n') is None
    assert (
        get_source_api_requirement(
            '# ba_meta require api 9\n# ba_meta require api 8\n'
        )
        is None
    )
