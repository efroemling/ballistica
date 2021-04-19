// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_MESH_MESH_INDEX_BUFFER_32_H_
#define BALLISTICA_GRAPHICS_MESH_MESH_INDEX_BUFFER_32_H_

#include "ballistica/graphics/mesh/mesh_buffer.h"

namespace ballistica {

// standard buffer for indices
class MeshIndexBuffer32 : public MeshBuffer<uint32_t> {
  using MeshBuffer::MeshBuffer;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_MESH_MESH_INDEX_BUFFER_32_H_
