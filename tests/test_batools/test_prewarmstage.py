# Released under the MIT License. See LICENSE for details.
#
"""Tests for pycache_prewarm payload building."""

import sys
import json
import hashlib
from typing import TYPE_CHECKING

from batools._prewarmstage import (
    HASH_DIGEST_SIZE,
    MANIFEST_FILENAME,
    MANIFEST_VERSION,
    build_prewarm,
)

if TYPE_CHECKING:
    from pathlib import Path


def _build_roots(base: Path) -> list[tuple[str, str]]:
    app = base / 'app'
    (app / 'mypkg').mkdir(parents=True)
    (app / 'topmod.py').write_text('X = 1\n')
    (app / 'mypkg' / '__init__.py').write_text('Y = 2\n')
    pylib = base / 'pylib'
    pylib.mkdir()
    (pylib / 'somelib.py').write_text('Z = 3\n')
    return [('app', str(app)), ('pylib', str(pylib))]


def test_build_and_manifest(tmp_path: Path) -> None:
    """Full build: layout, names, manifest contents."""
    roots = _build_roots(tmp_path / 'src')
    out = tmp_path / 'prewarm'

    results = build_prewarm(str(out), roots, optimize=1, executor='serial')
    assert results.compiled == 3
    assert not results.errors

    tag = sys.implementation.cache_tag
    assert (out / 'app' / f'topmod.{tag}.opt-1.pyc').is_file()
    assert (out / 'app' / 'mypkg' / f'__init__.{tag}.opt-1.pyc').is_file()
    assert (out / 'pylib' / f'somelib.{tag}.opt-1.pyc').is_file()

    manifest = json.loads((out / MANIFEST_FILENAME).read_text())
    assert manifest['version'] == MANIFEST_VERSION
    assert manifest['cache_tag'] == tag
    assert manifest['optimize'] == 1
    entry = manifest['entries']['app/topmod.py']
    srcbytes = (tmp_path / 'src' / 'app' / 'topmod.py').read_bytes()
    assert entry['s'] == len(srcbytes)
    assert (
        entry['h']
        == hashlib.blake2b(srcbytes, digest_size=HASH_DIGEST_SIZE).hexdigest()
    )


def test_from_scratch_and_determinism(tmp_path: Path) -> None:
    """Rebuilds wipe stale content and produce identical bytes."""
    roots = _build_roots(tmp_path / 'src')
    out = tmp_path / 'prewarm'

    build_prewarm(str(out), roots, optimize=0, executor='serial')
    tag = sys.implementation.cache_tag
    pycpath = out / 'app' / f'topmod.{tag}.pyc'
    first = pycpath.read_bytes()

    # Drop a stray file; the from-scratch rebuild must remove it.
    stray = out / 'app' / 'stray.pyc'
    stray.write_bytes(b'junk')

    build_prewarm(str(out), roots, optimize=0, executor='serial')
    assert not stray.exists()
    # UNCHECKED_HASH pycs are deterministic (no mtimes baked in).
    assert pycpath.read_bytes() == first


def test_error_withholds_manifest(tmp_path: Path) -> None:
    """Compile failures are reported and leave no manifest."""
    roots = _build_roots(tmp_path / 'src')
    (tmp_path / 'src' / 'app' / 'broken.py').write_text('def nope(:\n')
    out = tmp_path / 'prewarm'

    results = build_prewarm(str(out), roots, optimize=1, executor='serial')
    assert len(results.errors) == 1
    assert 'broken.py' in results.errors[0]
    assert not (out / MANIFEST_FILENAME).exists()


def test_auto_executor(tmp_path: Path) -> None:
    """The default (auto) strategy builds correctly end to end."""
    roots = _build_roots(tmp_path / 'src')
    out = tmp_path / 'prewarm'

    results = build_prewarm(str(out), roots, optimize=1)
    assert results.compiled == 3
    assert not results.errors
    assert (out / MANIFEST_FILENAME).is_file()
