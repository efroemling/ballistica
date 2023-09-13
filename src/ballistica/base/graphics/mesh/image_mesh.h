// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_IMAGE_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_IMAGE_MESH_H_

#include "ballistica/base/graphics/mesh/mesh_indexed_simple_split.h"

namespace ballistica::base {

// A mesh set up to draw images.
class ImageMesh : public MeshIndexedSimpleSplit {
 public:
  ImageMesh();
  void SetPositionAndSize(float x, float y, float z, float width,
                          float height) {
    VertexSimpleSplitDynamic vdynamic[] = {{x, y, z},
                                           {x + width, y, z},
                                           {x, y + height, z},
                                           {x + width, y + height, z}};
    SetDynamicData(
        Object::New<MeshBuffer<VertexSimpleSplitDynamic>>(4, vdynamic));
  }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_IMAGE_MESH_H_
