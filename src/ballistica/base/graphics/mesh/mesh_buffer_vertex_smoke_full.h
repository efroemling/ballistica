// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_BUFFER_VERTEX_SMOKE_FULL_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_BUFFER_VERTEX_SMOKE_FULL_H_

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/mesh/mesh_buffer.h"

namespace ballistica::base {

// Just make this a vanilla child class of our template (simply so we could
// predeclare this).
class MeshBufferVertexSmokeFull : public MeshBuffer<VertexSmokeFull> {
  using MeshBuffer::MeshBuffer;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_BUFFER_VERTEX_SMOKE_FULL_H_
