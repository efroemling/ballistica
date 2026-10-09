// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_RECT_OUTLINE_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_RECT_OUTLINE_MESH_H_

#include <algorithm>

#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"

namespace ballistica::base {

/// A rectangle's outline as real geometry: a ring ``thickness`` wide
/// just inside the given rect (left, bottom, width, height), for
/// drawing bounds and guides. Lines of a set width aren't something
/// every renderer gives us, and separate rects per side overlap at the
/// corners (which shows once anything is translucent); the ring covers
/// each pixel once. Texture coords are all (0, 0), so draw it with a
/// flat texture (the builtin white one) and a color.
///
/// Thickness is in the rect's own units, so a caller wanting a set
/// width on screen works it out from its scale; it is limited to half
/// the rect's shorter side (where the ring closes up into a solid
/// rect).
class RectOutlineMesh : public MeshIndexedSimpleFull {
 public:
  RectOutlineMesh(float x, float y, float z, float width, float height,
                  float thickness) {
    width = std::max(0.0f, width);
    height = std::max(0.0f, height);
    float t =
        std::max(0.0f, std::min(thickness, std::min(width, height) * 0.5f));
    float x1 = x + width;
    float y1 = y + height;
    // Outer corners then inner ones, both counter-clockwise from the
    // bottom left.
    const VertexSimpleFull verts[8] = {
        {{x, y, z}, {0, 0}},           {{x1, y, z}, {0, 0}},
        {{x1, y1, z}, {0, 0}},         {{x, y1, z}, {0, 0}},
        {{x + t, y + t, z}, {0, 0}},   {{x1 - t, y + t, z}, {0, 0}},
        {{x1 - t, y1 - t, z}, {0, 0}}, {{x + t, y1 - t, z}, {0, 0}},
    };
    // One quad per side, each running corner to corner along the
    // outside and meeting its neighbors along the diagonals.
    const uint16_t indices[24] = {
        0, 1, 5, 0, 5, 4,  // Bottom.
        1, 2, 6, 1, 6, 5,  // Right.
        2, 3, 7, 2, 7, 6,  // Top.
        3, 0, 4, 3, 4, 7,  // Left.
    };
    SetIndexData(Object::New<MeshIndexBuffer16>(24, indices));
    SetData(Object::New<MeshBuffer<VertexSimpleFull>>(8, verts));
  }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_RECT_OUTLINE_MESH_H_
