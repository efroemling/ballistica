# Released under the MIT License. See LICENSE for details.
#
"""Compilers for Ballistica's binary mesh formats.

Covers display meshes (``.bob``) and collision meshes (``.cob``).

This module is intentionally stdlib-only and side-effect free so it
can run anywhere it gets efrosynced to (game repo asset builds now,
master-server cloud-build recipes later).
"""

import math
import struct
from pathlib import Path
from dataclasses import dataclass

# Binary format magics. C++ source of truth is
# ballistica-internal:src/ballistica/shared/ballistica.h (kBobFileID /
# kCobFileID / kCobFileID2); keep these in sync with it.
BOB_FILE_ID = 45623
COB_FILE_ID_LEGACY = 13466
COB_FILE_ID = 13467

# Bob vertex formats; mirrors the C++ MeshFormat enum in
# src/ballistica/base/base.h. (Note: the 'N8' in those names is
# historical drift; normals are actually 16 bit.)
MESH_FORMAT_UV16_N8_INDEX8 = 0
MESH_FORMAT_UV16_N8_INDEX16 = 1
MESH_FORMAT_UV16_N8_INDEX32 = 2

# Bob vertex layout: mirrors the C++ VertexObjectFull struct
# (f32 position[3], u16 uv[2], s16 normal[3], 2 pad bytes = 24 byte
# stride; the GL renderer feeds this directly to glVertexAttribPointer).
_BOB_VERTEX_PACK = '<3f2H3h2x'

# Format notes:
#
# Legacy .cob (COB_FILE_ID_LEGACY, written by the old make_bob binary),
# all little-endian:
#   u32 magic, u32 vertex_count, u32 tri_count,
#   f32 positions[vertex_count * 3],
#   u32 indices[tri_count * 3],
#   f32 face_normals[tri_count * 3]
#
# Current .cob (COB_FILE_ID): identical minus the trailing face-normals
# block. The normals were consumed only by ODE's trimesh-vs-trimesh
# collider, which the engine can never hit (trimeshes are static and
# only ever collide against moving sphere/box/capsule bodies), so they
# were pure dead weight (~40% of file and resident size).
#
# The writer additionally lays data out for runtime cache friendliness;
# ODE/OPCODE uses these arrays in place (zero-copy) during narrow-phase
# collision. See compile_collision_mesh() for specifics.


@dataclass
class CobCompileResult:
    """Stats from a collision-mesh compile."""

    vertex_count_in: int
    vertex_count_out: int
    tri_count_in: int
    tri_count_out: int

    @property
    def vertices_welded(self) -> int:
        """How many exact-duplicate vertices were merged away."""
        return self.vertex_count_in - self.vertex_count_out

    @property
    def tris_dropped(self) -> int:
        """How many degenerate triangles were dropped."""
        return self.tri_count_in - self.tri_count_out


def compile_collision_mesh(
    src: str | Path, dst: str | Path
) -> CobCompileResult:
    """Compile a wavefront ``.obj`` file to a binary ``.cob`` file.

    Reads a constrained subset of the obj format: ``v`` records and
    ``f`` records (``v``, ``v/t``, ``v//n``, and ``v/t/n`` corner forms
    are all accepted; texture-coordinate and normal references are
    ignored). Faces with more than 3 corners are fan-triangulated.

    Output is deterministic for a given input, which matters for
    content-addressed asset storage.

    Beyond straight conversion this applies a few optimizations:

    - Exact-duplicate vertex positions are welded (compared at float32
      precision, matching what gets written).
    - Degenerate triangles (two or more corners sharing a vertex) are
      dropped.
    - Triangles are sorted along a Morton curve of their centroids and
      vertices are then ordered by first use, so triangles that are
      near each other in space are also near each other in memory.
      ODE/OPCODE reads these arrays in place during collision queries;
      spatially-local queries thus touch fewer cache lines. (Tree
      *shape* is unaffected; OPCODE splits on geometry, not input
      order.)
    - Unreferenced vertices are pruned (they would otherwise inflate
      both memory use and ODE's model-space AABB).
    """
    positions, faces = _parse_obj(Path(src))

    vertex_count_in = len(positions)
    tri_count_in = len(faces)

    if not faces:
        raise ValueError(f"No triangles found in '{src}'.")

    # Weld exact-duplicate positions. Compare at float32 precision
    # (the precision we write) so weld results don't depend on
    # higher-precision parse artifacts.
    posbits = [struct.pack('<fff', p[0], p[1], p[2]) for p in positions]
    weldmap: dict[bytes, int] = {}
    remap: list[int] = []
    for bits in posbits:
        existing = weldmap.get(bits)
        if existing is None:
            weldmap[bits] = len(weldmap)
            remap.append(len(weldmap) - 1)
        else:
            remap.append(existing)
    welded_posbits = list(weldmap.keys())

    # Rewrite faces against welded verts; drop degenerates. Corner
    # order within each face is preserved (winding determines ODE's
    # contact normals).
    tris: list[tuple[int, int, int]] = []
    for face in faces:
        tri = (remap[face[0]], remap[face[1]], remap[face[2]])
        if tri[0] == tri[1] or tri[1] == tri[2] or tri[0] == tri[2]:
            continue
        tris.append(tri)

    if not tris:
        raise ValueError(f"Only degenerate triangles found in '{src}'.")

    # Sort triangles along a Morton curve of their centroids. Sort is
    # stable, so equal codes keep input order (determinism).
    positions_f32: list[tuple[float, ...]] = [
        struct.unpack('<fff', bits) for bits in welded_posbits
    ]
    mins = [min(p[axis] for p in positions_f32) for axis in range(3)]
    maxs = [max(p[axis] for p in positions_f32) for axis in range(3)]
    spans = [
        (maxs[axis] - mins[axis]) if maxs[axis] > mins[axis] else 1.0
        for axis in range(3)
    ]
    tris.sort(key=lambda t: _morton_code_for_tri(t, positions_f32, mins, spans))

    # Re-number vertices by first use; this also prunes orphans.
    order: dict[int, int] = {}
    for tri in tris:
        for vert in tri:
            if vert not in order:
                order[vert] = len(order)
    out_posbits = [b''] * len(order)
    for old_index, new_index in order.items():
        out_posbits[new_index] = welded_posbits[old_index]

    # Write it out.
    out = bytearray()
    out += struct.pack('<III', COB_FILE_ID, len(order), len(tris))
    out += b''.join(out_posbits)
    out += b''.join(
        struct.pack('<III', order[tri[0]], order[tri[1]], order[tri[2]])
        for tri in tris
    )
    Path(dst).write_bytes(out)

    return CobCompileResult(
        vertex_count_in=vertex_count_in,
        vertex_count_out=len(order),
        tri_count_in=tri_count_in,
        tri_count_out=len(tris),
    )


@dataclass
class CobData:
    """Parsed contents of a ``.cob`` file."""

    file_id: int
    # Flat [x, y, z, x, y, z, ...] float32 values.
    positions: list[float]
    # Flat [a, b, c, a, b, c, ...] vertex indices.
    indices: list[int]
    # Flat per-tri face normals; only present in legacy files.
    normals: list[float] | None


def read_collision_mesh(path: str | Path) -> CobData:
    """Read a binary ``.cob`` file (current or legacy format)."""
    data = Path(path).read_bytes()
    file_id, vertex_count, tri_count = struct.unpack_from('<III', data, 0)
    if file_id not in (COB_FILE_ID, COB_FILE_ID_LEGACY):
        raise ValueError(f"'{path}' is not a cob file (got id {file_id}).")
    offset = 12
    positions = list(struct.unpack_from(f'<{vertex_count * 3}f', data, offset))
    offset += vertex_count * 12
    indices = list(struct.unpack_from(f'<{tri_count * 3}I', data, offset))
    offset += tri_count * 12
    normals: list[float] | None = None
    if file_id == COB_FILE_ID_LEGACY:
        normals = list(struct.unpack_from(f'<{tri_count * 3}f', data, offset))
        offset += tri_count * 12
    if offset != len(data):
        raise ValueError(f"Unexpected trailing data in '{path}'.")
    return CobData(
        file_id=file_id, positions=positions, indices=indices, normals=normals
    )


def _parse_obj(
    path: Path,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Parse the obj subset we support: positions and triangulated faces."""
    positions: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for lineno, line in enumerate(_read_obj_lines(path), start=1):
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        try:
            if parts[0] == 'v':
                positions.append(
                    (float(parts[1]), float(parts[2]), float(parts[3]))
                )
            elif parts[0] == 'f':
                _parse_face_corners_v(
                    parts, len(positions), path, lineno, faces
                )
            # Ignore everything else (vt, vn, o, g, s, usemtl, ...).
        except _ObjError:
            raise
        except (ValueError, IndexError) as exc:
            raise _obj_record_error(path, lineno, line, exc) from exc
    return positions, faces


def _parse_face_corners_v(
    parts: list[str],
    position_count: int,
    path: Path,
    lineno: int,
    faces: list[tuple[int, int, int]],
) -> None:
    """Parse one collision-mesh ``f`` record (position indices only).

    Accepts v, v/t, v//n, and v/t/n corner forms; only the position
    index is used.
    """
    corners: list[int] = []
    for corner in parts[1:]:
        vidx = int(corner.split('/', 1)[0])
        if vidx <= 0:
            # Negative (relative) obj indices are valid obj but nothing
            # in our pipeline produces them.
            raise _ObjError(
                f'{path}:{lineno}: negative/relative obj indices are not'
                f' supported (corner {corner!r}); re-export with absolute'
                ' indices.'
            )
        if vidx > position_count:
            raise _ObjError(
                f'{path}:{lineno}: face index {vidx} is out of range.'
            )
        corners.append(vidx - 1)
    if len(corners) < 3:
        raise _ObjError(f'{path}:{lineno}: face has fewer than 3 corners.')
    # Fan-triangulate (no-op for plain tris).
    for i in range(1, len(corners) - 1):
        faces.append((corners[0], corners[i], corners[i + 1]))


def _morton_code_for_tri(
    tri: tuple[int, int, int],
    positions: list[tuple[float, ...]],
    mins: list[float],
    spans: list[float],
) -> int:
    """30-bit Morton code for a triangle's centroid.

    Centroids are normalized against the mesh AABB described by
    ``mins``/``spans``.
    """
    code = 0
    for axis in range(3):
        centroid = (
            positions[tri[0]][axis]
            + positions[tri[1]][axis]
            + positions[tri[2]][axis]
        ) / 3.0
        normalized = (centroid - mins[axis]) / spans[axis]
        quantized = min(1023, max(0, int(normalized * 1024.0)))
        code |= _part1by2(quantized) << axis
    return code


def _part1by2(val: int) -> int:
    """Spread a 10 bit int's bits out to every 3rd bit of a 30 bit int."""
    val &= 0x3FF
    val = (val | (val << 16)) & 0x30000FF
    val = (val | (val << 8)) & 0x300F00F
    val = (val | (val << 4)) & 0x30C30C3
    val = (val | (val << 2)) & 0x9249249
    return val


@dataclass
class BobCompileResult:
    """Stats from a display-mesh compile."""

    corner_count: int
    vertex_count: int
    tri_count: int
    index_size: int

    @property
    def vertex_reuse(self) -> float:
        """Verts per triangle; lower is better (0.5 = perfect grid reuse).

        Values near 3.0 mean almost no corner sharing (hard edges / UV
        seams splitting most vertices) - an art/export property no index
        reordering can fix.
        """
        return self.vertex_count / max(1, self.tri_count)


def compile_mesh(src: str | Path, dst: str | Path) -> BobCompileResult:
    """Compile a wavefront ``.obj`` file to a binary ``.bob`` file.

    Reads the obj subset our exporters produce: ``v``/``vt``/``vn``
    records plus ``f`` records with full ``v/t/n`` corners. Faces with
    more than 3 corners are fan-triangulated. The obj V texture
    coordinate is flipped (``1 - v``) per GL convention. UVs and normal
    components meaningfully outside their encodable ranges ([0, 1] /
    [-1, 1]) are errors; values within a 0.05 tolerance are treated as
    authoring noise and clamped silently by the quantization.

    Output is deterministic for a given input, which matters for
    content-addressed asset storage.

    Optimizations applied:

    - Corners are quantized to the final vertex encoding and welded
      (exact-match on all attributes), so identical corners share one
      vertex.
    - Degenerate triangles (two or more corners welding to the same
      vertex) are dropped.
    - Triangle order is optimized for the GPU post-transform vertex
      cache (Forsyth's linear-speed algorithm), then vertices are
      renumbered by first use for fetch locality. This also prunes
      unreferenced vertices.
    - Index width is chosen per mesh: u16 when vertices fit, u32
      otherwise (the engine supports both; this removes the old
      make_bob 21845-face limit).
    """
    positions, tex_coords, normals, faces = _parse_obj_mesh(Path(src))

    if not faces:
        raise ValueError(f"No triangles found in '{src}'.")

    # Quantize each face-corner to its final byte encoding and weld
    # exact duplicates. (All data for a vertex shares one index; there
    # are no separate position/uv/normal indices in the output.)
    vertices, indices = _weld_corners(positions, tex_coords, normals, faces)

    if not indices:
        raise ValueError(f"Only degenerate triangles found in '{src}'.")

    # Optimize triangle order for the post-transform vertex cache.
    indices = _optimize_vcache(indices, len(vertices))

    # Renumber vertices by first use (fetch locality); prunes orphans.
    order: dict[int, int] = {}
    for index in indices:
        if index not in order:
            order[index] = len(order)
    out_vertices = [b''] * len(order)
    for old_index, new_index in order.items():
        out_vertices[new_index] = vertices[old_index]
    indices = [order[i] for i in indices]

    # Pick the narrowest index encoding the engine supports that fits.
    # (Engine handles INDEX8 too but its u8 win is negligible; the old
    # make_bob also always skipped it.)
    if len(out_vertices) <= 0xFFFF:
        mesh_format = MESH_FORMAT_UV16_N8_INDEX16
        index_char = 'H'
        index_size = 2
    else:
        mesh_format = MESH_FORMAT_UV16_N8_INDEX32
        index_char = 'I'
        index_size = 4

    tri_count = len(indices) // 3
    out = bytearray()
    out += struct.pack(
        '<IIII', BOB_FILE_ID, mesh_format, len(out_vertices), tri_count
    )
    out += b''.join(out_vertices)
    out += struct.pack(f'<{len(indices)}{index_char}', *indices)
    Path(dst).write_bytes(out)

    return BobCompileResult(
        corner_count=len(faces) * 3,
        vertex_count=len(out_vertices),
        tri_count=tri_count,
        index_size=index_size,
    )


@dataclass
class BobData:
    """Parsed contents of a ``.bob`` file."""

    mesh_format: int
    # Per-vertex (px, py, pz, u, v, nx, ny, nz) tuples; positions are
    # float32, uvs u16, normals s16 (raw encoded values).
    vertices: list[tuple[float, float, float, int, int, int, int, int]]
    # Flat [a, b, c, a, b, c, ...] vertex indices.
    indices: list[int]


def read_mesh(path: str | Path) -> BobData:
    """Read a binary ``.bob`` file."""
    data = Path(path).read_bytes()
    file_id, mesh_format, vertex_count, tri_count = struct.unpack_from(
        '<IIII', data, 0
    )
    if file_id != BOB_FILE_ID:
        raise ValueError(f"'{path}' is not a bob file (got id {file_id}).")
    index_char = {
        MESH_FORMAT_UV16_N8_INDEX8: 'B',
        MESH_FORMAT_UV16_N8_INDEX16: 'H',
        MESH_FORMAT_UV16_N8_INDEX32: 'I',
    }[mesh_format]
    index_size = {'B': 1, 'H': 2, 'I': 4}[index_char]
    offset = 16
    vertices = list(
        struct.iter_unpack(
            _BOB_VERTEX_PACK, data[offset : offset + vertex_count * 24]
        )
    )
    offset += vertex_count * 24
    indices = list(
        struct.unpack_from(f'<{tri_count * 3}{index_char}', data, offset)
    )
    offset += tri_count * 3 * index_size
    if offset != len(data):
        raise ValueError(f"Unexpected trailing data in '{path}'.")
    return BobData(mesh_format=mesh_format, vertices=vertices, indices=indices)


def _weld_corners(
    positions: list[tuple[float, float, float]],
    tex_coords: list[tuple[float, float]],
    normals: list[tuple[float, float, float]],
    faces: list[list[tuple[int, int, int]]],
) -> tuple[list[bytes], list[int]]:
    """Quantize face-corners to final encoding and weld duplicates.

    Returns (vertices-as-packed-bytes, flat-tri-indices). Degenerate
    tris (corners welding together) are dropped.
    """
    weldmap: dict[bytes, int] = {}
    indices: list[int] = []
    for face in faces:
        tri: list[int] = []
        for v_i, t_i, n_i in face:
            vbits = struct.pack(
                _BOB_VERTEX_PACK,
                positions[v_i][0],
                positions[v_i][1],
                positions[v_i][2],
                _ftou16(tex_coords[t_i][0]),
                _ftou16(tex_coords[t_i][1]),
                _ftos16(normals[n_i][0]),
                _ftos16(normals[n_i][1]),
                _ftos16(normals[n_i][2]),
            )
            index = weldmap.get(vbits)
            if index is None:
                index = len(weldmap)
                weldmap[vbits] = index
            tri.append(index)
        # Drop degenerates (zero area in all attributes).
        if tri[0] == tri[1] or tri[1] == tri[2] or tri[0] == tri[2]:
            continue
        indices.extend(tri)
    return list(weldmap.keys()), indices


class _ObjError(ValueError):
    """An obj parsing error already carrying user-facing context."""


def _read_obj_lines(path: Path) -> list[str]:
    """Read an obj file's text lines with friendly failure modes.

    Catches the most likely modder mistakes (binary files, wrong
    formats) up front with actionable messages instead of letting raw
    decode errors surface.
    """
    data = path.read_bytes()
    if b'\0' in data[:8192]:
        raise _ObjError(
            f"'{path}' does not look like a text .obj file (it contains"
            ' binary data). Export meshes as plain-text Wavefront .obj.'
        )
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise _ObjError(
            f"'{path}' is not valid utf-8 text (problem at byte"
            f' {exc.start}). Export meshes as plain-text Wavefront .obj.'
        ) from exc
    return text.splitlines()


def _obj_record_error(
    path: Path, lineno: int, line: str, exc: Exception
) -> _ObjError:
    """Build a contextual error for a record we failed to parse."""
    return _ObjError(
        f'{path}:{lineno}: malformed {line.split()[0]!r} record:'
        f' {line.strip()[:80]!r} ({exc}).'
    )


def _parse_obj_mesh(path: Path) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float]],
    list[tuple[float, float, float]],
    list[list[tuple[int, int, int]]],
]:
    """Parse the obj subset display meshes use.

    Returns (positions, tex_coords, normals, faces); faces are lists of
    (v, t, n) zero-based index triples, fan-triangulated. All float
    values are rounded to float32 precision (matching what a float-based
    C parser would hold, which keeps quantization results stable).
    """
    positions: list[tuple[float, float, float]] = []
    tex_coords: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    faces: list[list[tuple[int, int, int]]] = []
    for lineno, line in enumerate(_read_obj_lines(path), start=1):
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        try:
            if parts[0] == 'v':
                positions.append(
                    (
                        _f32(float(parts[1])),
                        _f32(float(parts[2])),
                        _f32(float(parts[3])),
                    )
                )
            elif parts[0] == 'vt':
                uvs = (float(parts[1]), float(parts[2]))
                # The u16 encoding can only represent [0, 1]; treat
                # anything meaningfully outside that as an error.
                # (Within tolerance counts as authoring noise and gets
                # clamped silently by the quantization.)
                if any(not -0.05 <= val <= 1.05 for val in uvs):
                    raise _ObjError(
                        f'{path}:{lineno}: texture coordinate'
                        f' {line.strip()[:80]!r} is outside the supported'
                        ' [0, 1] range. Tiling/wrapping UVs are not'
                        ' supported; keep UVs within the texture.'
                    )
                # Flip V per GL convention (in float32, as the old
                # C tool did).
                tex_coords.append(
                    (
                        _f32(uvs[0]),
                        _f32(1.0 - _f32(uvs[1])),
                    )
                )
            elif parts[0] == 'vn':
                nrm = (float(parts[1]), float(parts[2]), float(parts[3]))
                # The s16 encoding can only represent [-1, 1]; same
                # tolerance policy as UVs above.
                if any(not -1.05 <= val <= 1.05 for val in nrm):
                    raise _ObjError(
                        f'{path}:{lineno}: normal {line.strip()[:80]!r}'
                        ' has components outside [-1, 1]; normals must'
                        ' be normalized.'
                    )
                normals.append((_f32(nrm[0]), _f32(nrm[1]), _f32(nrm[2])))
            elif parts[0] == 'f':
                _parse_face_corners_vtn(
                    parts,
                    (len(positions), len(tex_coords), len(normals)),
                    path,
                    lineno,
                    faces,
                )
            # Ignore everything else (o, g, s, usemtl, mtllib, ...).
        except _ObjError:
            raise
        except (ValueError, IndexError) as exc:
            raise _obj_record_error(path, lineno, line, exc) from exc
    return positions, tex_coords, normals, faces


def _parse_face_corners_vtn(
    parts: list[str],
    counts: tuple[int, int, int],
    path: Path,
    lineno: int,
    faces: list[list[tuple[int, int, int]]],
) -> None:
    """Parse one display-mesh ``f`` record (strict v/t/n corners)."""
    corners: list[tuple[int, int, int]] = []
    for corner in parts[1:]:
        fields = corner.split('/')
        if len(fields) != 3 or not all(fields):
            raise _ObjError(
                f'{path}:{lineno}: face corner {corner!r} is not in the'
                ' v/t/n form. Display meshes need a position, texture'
                ' coordinate, and normal for every corner; make sure UVs'
                ' and normals are enabled in the export.'
            )
        vrefs = tuple(int(f) for f in fields)
        if any(r <= 0 for r in vrefs):
            raise _ObjError(
                f'{path}:{lineno}: negative/relative obj indices are not'
                f' supported (corner {corner!r}); re-export with absolute'
                ' indices.'
            )
        if any(vrefs[i] > counts[i] for i in range(3)):
            raise _ObjError(
                f'{path}:{lineno}: face index out of range in corner'
                f' {corner!r}.'
            )
        corners.append((vrefs[0] - 1, vrefs[1] - 1, vrefs[2] - 1))
    if len(corners) < 3:
        raise _ObjError(f'{path}:{lineno}: face has fewer than 3 corners.')
    # Fan-triangulate (no-op for plain tris).
    for i in range(1, len(corners) - 1):
        faces.append([corners[0], corners[i], corners[i + 1]])


# Forsyth linear-speed vertex cache optimization
# (https://tomforsyth1000.github.io/papers/fast_vert_cache_opt.html).
# Constants from the paper.
_VCACHE_SIZE = 32
_VCACHE_DECAY_POWER = 1.5
_VCACHE_LAST_TRI_SCORE = 0.75
_VCACHE_VALENCE_SCALE = 2.0
_VCACHE_VALENCE_POWER = -0.5

# Score for each cache position, precomputed.
_VCACHE_POS_SCORES = [
    (
        _VCACHE_LAST_TRI_SCORE
        if pos < 3
        else (1.0 - (pos - 3) / (_VCACHE_SIZE - 3)) ** _VCACHE_DECAY_POWER
    )
    for pos in range(_VCACHE_SIZE)
]


def _vcache_vertex_score(cache_pos: int, active_tris: int) -> float:
    if active_tris == 0:
        return -1.0
    score = (
        _VCACHE_POS_SCORES[cache_pos] if 0 <= cache_pos < _VCACHE_SIZE else 0.0
    )
    return score + _VCACHE_VALENCE_SCALE * math.pow(
        active_tris, _VCACHE_VALENCE_POWER
    )


def _optimize_vcache(indices: list[int], vertex_count: int) -> list[int]:
    """Reorder triangles to maximize post-transform vertex cache hits.

    ``indices`` is a flat triangle list; returns a reordered flat list
    containing the same triangles (winding untouched). Deterministic.
    """
    tri_count = len(indices) // 3

    # Per-vertex adjacency + active (not-yet-emitted) tri counts.
    vert_tris: list[list[int]] = [[] for _ in range(vertex_count)]
    for tri in range(tri_count):
        for corner in indices[tri * 3 : tri * 3 + 3]:
            vert_tris[corner].append(tri)
    active = [len(t) for t in vert_tris]

    vert_score = [
        _vcache_vertex_score(-1, active[v]) for v in range(vertex_count)
    ]
    tri_score = [
        vert_score[indices[t * 3]]
        + vert_score[indices[t * 3 + 1]]
        + vert_score[indices[t * 3 + 2]]
        for t in range(tri_count)
    ]

    emitted = [False] * tri_count
    cache: list[int] = []  # Most-recently-used first.
    out: list[int] = []
    scan_pos = 0  # Resume point for fallback scans.

    def _rescore(vert: int, cache_pos: int) -> None:
        # Rescore one vertex and its not-yet-emitted tris.
        new_score = _vcache_vertex_score(cache_pos, active[vert])
        delta = new_score - vert_score[vert]
        if delta:
            vert_score[vert] = new_score
            for tri in vert_tris[vert]:
                if not emitted[tri]:
                    tri_score[tri] += delta

    for _ in range(tri_count):
        best_tri, scan_pos = _vcache_pick_tri(
            cache, vert_tris, emitted, tri_score, scan_pos
        )

        # Emit it.
        emitted[best_tri] = True
        corners = indices[best_tri * 3 : best_tri * 3 + 3]
        out.extend(corners)

        # Update the simulated LRU cache.
        for corner in reversed(corners):
            if corner in cache:
                cache.remove(corner)
            cache.insert(0, corner)
        evicted = cache[_VCACHE_SIZE:]
        del cache[_VCACHE_SIZE:]

        # Rescore affected vertices and their not-yet-emitted tris.
        for corner in corners:
            active[corner] -= 1
        for pos, vert in enumerate(cache):
            _rescore(vert, pos)
        for vert in evicted:
            _rescore(vert, -1)

    return out


def _vcache_pick_tri(
    cache: list[int],
    vert_tris: list[list[int]],
    emitted: list[bool],
    tri_score: list[float],
    scan_pos: int,
) -> tuple[int, int]:
    """Pick the best next triangle to emit; returns (tri, scan_pos)."""
    best_tri = -1
    best_score = -1e30

    # Best candidate among triangles touching the cache.
    for vert in cache:
        for tri in vert_tris[vert]:
            if not emitted[tri] and tri_score[tri] > best_score:
                best_score = tri_score[tri]
                best_tri = tri
    if best_tri >= 0:
        return best_tri, scan_pos

    # Cache exhausted (start, or isolated component): take the
    # best-scoring remaining triangle.
    while emitted[scan_pos]:
        scan_pos += 1
    best_tri = scan_pos
    for tri in range(scan_pos + 1, len(emitted)):
        if not emitted[tri] and tri_score[tri] > best_score:
            best_score = tri_score[tri]
            best_tri = tri
    return best_tri, scan_pos


def _f32(val: float) -> float:
    """Round a python float to float32 precision."""
    return float(struct.unpack('<f', struct.pack('<f', val))[0])


def _round_half_away(val: float) -> int:
    """C-style round(): half rounds away from zero."""
    return int(val + 0.5) if val >= 0 else -int(-val + 0.5)


def _ftou16(val: float) -> int:
    """Encode a [0,1] float as u16 (clamping; matches the old C tool)."""
    if val > 1.0:
        return 65535
    if val < 0.0:
        return 0
    return _round_half_away(65535.0 * val)


def _ftos16(val: float) -> int:
    """Encode a [-1,1] float as s16.

    Symmetric 32767 scale, matching GL's snorm decode (``c / 32767``)
    and the shipped make_bob binaries. (The make_bob *source* later
    grew a 32768 scale for negatives, but the checked-in binaries
    producing all shipped assets predate that; 32767 is also the
    spec-correct inverse.)
    """
    return _round_half_away(32767.0 * max(-1.0, min(1.0, val)))
