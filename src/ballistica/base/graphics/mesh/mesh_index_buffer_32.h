// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEX_BUFFER_32_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEX_BUFFER_32_H_

#include "ballistica/base/graphics/mesh/mesh_buffer.h"

namespace ballistica::base {

// Standard buffer for indices.
class MeshIndexBuffer32 : public MeshBuffer<uint32_t> {
  using MeshBuffer::MeshBuffer;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEX_BUFFER_32_H_
