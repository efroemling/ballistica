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
  /// desired max corner radius. For calculating left or right borders,
  /// `matching_dimension` should be width and `other_dimension` should be
  /// height. For top or bottom borders it is the opposite.
  static auto BorderForRadius(float corner_radius, float matching_dimension,
                              float other_dimension) -> float {
    // Limit the radius to no more than half the shortest side.
    corner_radius = std::min(
        corner_radius, std::min(matching_dimension, other_dimension) * 0.5f);
    if (matching_dimension <= 0.0f) {
      return 0.0f;
    }
    return corner_radius / matching_dimension;
  }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_NINE_PATCH_MESH_H_
