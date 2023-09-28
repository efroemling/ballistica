// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_

#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"

namespace ballistica::base {

// A mesh set up to draw images as 9-patches.
class NinePatchMesh : public MeshIndexedSimpleFull {
 public:
  NinePatchMesh(float x, float y, float z, float width, float height,
                float border_left, float border_bottom, float border_right,
                float border_top);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_
