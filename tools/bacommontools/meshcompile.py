# Released under the MIT License. See LICENSE for details.
#
"""Compilers for Ballistica's binary mesh formats.

Currently covers collision meshes (``.cob``); display meshes
(``.bob``) should land here too once we retire the legacy ``make_bob``
binary for them.

This module is intentionally stdlib-only and side-effect free so it
can run anywhere it gets efrosynced to (game repo asset builds now,
master-server cloud-build recipes later).
"""

from __future__ import annotations

import struct
from pathlib import Path
from dataclasses import dataclass

# Binary format magics. C++ source of truth is
# ballistica-internal:src/ballistica/shared/ballistica.h (kCobFileID /
# kCobFileID2); keep these in sync with it.
COB_FILE_ID_LEGACY = 13466
COB_FILE_ID = 13467

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
    with path.open(encoding='utf-8') as infile:
        for lineno, line in enumerate(infile, start=1):
            parts = line.split()
            if not parts or parts[0].startswith('#'):
                continue
            if parts[0] == 'v':
                if len(parts) < 4:
                    raise ValueError(f'Malformed vertex at {path}:{lineno}.')
                positions.append(
                    (float(parts[1]), float(parts[2]), float(parts[3]))
                )
            elif parts[0] == 'f':
                corners: list[int] = []
                for corner in parts[1:]:
                    # Accept v, v/t, v//n, and v/t/n forms; we only
                    # care about the position index.
                    vstr = corner.split('/', 1)[0]
                    vidx = int(vstr)
                    if vidx <= 0:
                        # Negative (relative) obj indices are valid obj
                        # but nothing in our pipeline produces them.
                        raise ValueError(
                            f'Unsupported face index {vidx} at'
                            f' {path}:{lineno}.'
                        )
                    if vidx > len(positions):
                        raise ValueError(
                            f'Out-of-range face index {vidx} at'
                            f' {path}:{lineno}.'
                        )
                    corners.append(vidx - 1)
                if len(corners) < 3:
                    raise ValueError(
                        f'Face with fewer than 3 corners at {path}:{lineno}.'
                    )
                # Fan-triangulate (no-op for plain tris).
                for i in range(1, len(corners) - 1):
                    faces.append((corners[0], corners[i], corners[i + 1]))
            # Ignore everything else (vt, vn, o, g, s, usemtl, ...).
    return positions, faces


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
