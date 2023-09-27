// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_SPRITE_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_SPRITE_MESH_H_

#include "ballistica/base/graphics/mesh/mesh_indexed.h"

namespace ballistica::base {

// An indexed sprite-mesh.
class SpriteMesh : public MeshIndexed<VertexSprite, MeshDataType::kSprite> {
  using MeshIndexed::MeshIndexed;  // wheeee c++11 magic
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_SPRITE_MESH_H_
