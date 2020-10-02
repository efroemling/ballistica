// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_FULL_H_
#define BALLISTICA_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_FULL_H_

#include "ballistica/graphics/mesh/mesh_indexed.h"

namespace ballistica {

// a simple mesh with all data provided together (either static or dynamic)
class MeshIndexedSimpleFull
    : public MeshIndexed<VertexSimpleFull, MeshDataType::kIndexedSimpleFull> {
  using MeshIndexed::MeshIndexed;  // wheee c++11 magic
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_FULL_H_
