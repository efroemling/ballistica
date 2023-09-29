// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_

#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"

namespace ballistica::base {

/// A mesh set up to draw images as 9-patches. Border values are provided
/// as ratios of total width/height. For example, setting all borders
/// to 0.3333 will result in a mesh that looks like a uniform 3x3 grid.
class NinePatchMesh : public MeshIndexedSimpleFull {
 public:
  NinePatchMesh(float x, float y, float z, float width, float height,
                float border_left, float border_bottom, float border_right,
                float border_top);

  /// Calculate a border value for a NinePatchMesh based on dimensions and a
  /// desired max corner radius.
  static auto BorderForRadius(float corner_radius, float matching_dimension,
                              float other_dimension) -> float;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_
