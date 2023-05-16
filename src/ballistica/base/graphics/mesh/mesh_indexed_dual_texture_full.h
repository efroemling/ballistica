// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_DUAL_TEXTURE_FULL_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_DUAL_TEXTURE_FULL_H_

#include "ballistica/base/graphics/mesh/mesh_indexed.h"

namespace ballistica::base {

class MeshIndexedDualTextureFull
    : public MeshIndexed<VertexDualTextureFull,
                         MeshDataType::kIndexedDualTextureFull> {
  using MeshIndexed::MeshIndexed;  // wheee c++11 magic
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_DUAL_TEXTURE_FULL_H_
