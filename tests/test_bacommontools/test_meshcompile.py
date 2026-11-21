# Released under the MIT License. See LICENSE for details.
#
"""Testing display-mesh (.bob) compiling, its trailer in particular."""

import math
import struct
from typing import TYPE_CHECKING

import pytest

from bacommontools import meshcompile

if TYPE_CHECKING:
    from pathlib import Path

# A unit cube off to one side, with uvs over part of the texture.
_CUBE_OBJ = """
v 1 0 0
v 3 0 0
v 3 2 0
v 1 2 0
v 1 0 2
v 3 0 2
v 3 2 2
v 1 2 2
vt 0.25 0.25
vt 0.75 0.25
vt 0.75 0.5
vt 0.25 0.5
vn 0 0 1
f 1/1/1 2/2/1 3/3/1 4/4/1
f 5/1/1 6/2/1 7/3/1 8/4/1
f 1/1/1 2/2/1 6/3/1 5/4/1
f 4/1/1 3/2/1 7/3/1 8/4/1
"""


def _compile(tmp_path: Path) -> Path:
    src = tmp_path / 'cube.obj'
    src.write_text(_CUBE_OBJ)
    dst = tmp_path / 'cube.bob'
    meshcompile.compile_mesh(src, dst)
    return dst


def test_trailer_round_trip(tmp_path: Path) -> None:
    """A compiled mesh carries bounds and uv range that read back."""
    data = meshcompile.read_mesh(_compile(tmp_path))

    assert data.bounds is not None
    assert data.bounds.box_min == (1.0, 0.0, 0.0)
    assert data.bounds.box_max == (3.0, 2.0, 2.0)
    # Every corner of a 2-unit cube sits sqrt(3) from its center; the
    # stored radius holds them all.
    assert data.bounds.radius >= math.sqrt(3.0)
    assert data.bounds.radius == pytest.approx(math.sqrt(3.0), abs=1e-5)

    # (V is flipped on compile, so 0.25..0.5 becomes 0.5..0.75.)
    assert data.uv_range is not None
    umin, vmin, umax, vmax = data.uv_range
    assert umin == pytest.approx(0.25, abs=1e-4)
    assert umax == pytest.approx(0.75, abs=1e-4)
    assert vmin == pytest.approx(0.5, abs=1e-4)
    assert vmax == pytest.approx(0.75, abs=1e-4)


def test_unknown_sections_skipped(tmp_path: Path) -> None:
    """Readers skip trailer sections they don't know."""
    path = _compile(tmp_path)
    path.write_bytes(path.read_bytes() + struct.pack('<II', 999, 3) + b'abc')
    data = meshcompile.read_mesh(path)
    assert data.bounds is not None
    assert data.uv_range is not None


def test_no_trailer(tmp_path: Path) -> None:
    """Files from before the trailer still read (with no derived data)."""
    path = _compile(tmp_path)
    raw = path.read_bytes()
    offset = raw.index(struct.pack('<I', meshcompile.BOB_TRAILER_MAGIC))
    path.write_bytes(raw[:offset])
    data = meshcompile.read_mesh(path)
    assert data.bounds is None
    assert data.uv_range is None


def test_junk_trailer(tmp_path: Path) -> None:
    """Trailing bytes that aren't a trailer are an error."""
    path = _compile(tmp_path)
    raw = path.read_bytes()
    offset = raw.index(struct.pack('<I', meshcompile.BOB_TRAILER_MAGIC))
    path.write_bytes(raw[:offset] + b'junkjunk')
    with pytest.raises(ValueError):
        meshcompile.read_mesh(path)
