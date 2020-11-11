// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_MESH_SPRITE_MESH_H_
#define BALLISTICA_GRAPHICS_MESH_SPRITE_MESH_H_

#include "ballistica/graphics/mesh/mesh_indexed.h"

namespace ballistica {

// an indexed sprite-mesh
class SpriteMesh : public MeshIndexed<VertexSprite, MeshDataType::kSprite> {
  using MeshIndexed::MeshIndexed;  // wheeee c++11 magic
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_MESH_SPRITE_MESH_H_
