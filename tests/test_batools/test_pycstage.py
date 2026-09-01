# Released under the MIT License. See LICENSE for details.
#
"""Tests for side-by-side .pyc staging."""

import os
import struct
import importlib.util
from pathlib import Path

from batools._pycstage import STAMP_FILENAME, update_pycs


def _build_tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / 'topmod.py').write_text('X = 1\n')
    pkg = root / 'mypkg'
    pkg.mkdir()
    (pkg / '__init__.py').write_text('Y = 2\n')
    (pkg / 'submod.py').write_text('Z = 3\n')


def test_create_update_prune(tmp_path: Path) -> None:
    """Full create/no-op/touch/prune lifecycle."""
    root = tmp_path / 'payload'
    _build_tree(root)

    results = update_pycs(str(root))
    assert results.compiled == 3
    assert results.pruned == 0
    assert not results.errors

    # Side-by-side pycs exist, mtime-pinned to their sources, with
    # correct magic and PEP 552 unchecked-hash flags (0b01).
    for pypath in root.rglob('*.py'):
        pycpath = Path(str(pypath) + 'c')
        assert pycpath.is_file()
        assert pycpath.stat().st_mtime_ns == pypath.stat().st_mtime_ns
        header = pycpath.read_bytes()[:8]
        assert header[:4] == importlib.util.MAGIC_NUMBER
        assert struct.unpack('<L', header[4:8])[0] == 0b01

    # Deterministic output: pyc content embeds root-relative paths, so
    # identical trees at different locations yield identical bytes.
    root2 = tmp_path / 'payload2'
    _build_tree(root2)
    update_pycs(str(root2))
    assert (root2 / 'topmod.pyc').read_bytes() == (
        root / 'topmod.pyc'
    ).read_bytes()

    # No-op pass compiles nothing.
    results = update_pycs(str(root))
    assert results.compiled == 0
    assert results.up_to_date == 3

    # Touch one source; exactly it recompiles.
    os.utime(root / 'mypkg' / 'submod.py')
    results = update_pycs(str(root))
    assert results.compiled == 1
    assert results.up_to_date == 2

    # Remove a source; its pyc gets pruned.
    (root / 'topmod.py').unlink()
    results = update_pycs(str(root))
    assert results.pruned == 1
    assert not (root / 'topmod.pyc').exists()
    assert results.up_to_date == 2


def test_stamp_forces_regen(tmp_path: Path) -> None:
    """A stale/foreign stamp (e.g. interpreter change) regenerates all."""
    root = tmp_path / 'payload'
    _build_tree(root)
    update_pycs(str(root))

    (root / STAMP_FILENAME).write_text('0 deadbeef\n')
    results = update_pycs(str(root))
    assert results.compiled == 3
    assert results.up_to_date == 0


def test_compile_error_reported(tmp_path: Path) -> None:
    """Broken source is reported and leaves the stamp uncertified."""
    root = tmp_path / 'payload'
    _build_tree(root)
    (root / 'broken.py').write_text('def nope(:\n')

    results = update_pycs(str(root))
    assert len(results.errors) == 1
    assert 'broken.py' in results.errors[0]
    assert results.compiled == 3
    # Stamp withheld so the next pass retries everything.
    assert not (root / STAMP_FILENAME).exists()
