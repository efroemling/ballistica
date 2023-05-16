// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/mesh/mesh_data_client_handle.h"

#include "ballistica/base/graphics/graphics.h"

namespace ballistica::base {

MeshDataClientHandle::MeshDataClientHandle(MeshData* d) : mesh_data(d) {
  g_base->graphics->AddMeshDataCreate(mesh_data);
}

MeshDataClientHandle::~MeshDataClientHandle() {
  g_base->graphics->AddMeshDataDestroy(mesh_data);
}

}  // namespace ballistica::base
