// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_SMOKE_FULL_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_SMOKE_FULL_H_

#include "ballistica/base/graphics/mesh/mesh_indexed.h"

namespace ballistica::base {

// A mesh with all data provided together (either static or dynamic).
class MeshIndexedSmokeFull
    : public MeshIndexed<VertexSmokeFull, MeshDataType::kIndexedSmokeFull> {
  using MeshIndexed::MeshIndexed;  // wheee c++11 magic
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_SMOKE_FULL_H_
