# Released under the MIT License. See LICENSE for details.
#
"""Tests for the ``# ba_meta`` directive scanner."""

import zipfile
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from bacommon.metascan import DirectoryScan, get_source_api_requirement

if TYPE_CHECKING:
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

# ba_meta require asset-package acct.pkg.260101a
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
    assert results.asset_packages == {'acct.pkg.260101a': ['mypkg']}
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
