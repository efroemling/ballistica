// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/graphics/mesh/mesh_data_client_handle.h"

#include "ballistica/graphics/graphics.h"

namespace ballistica {

MeshDataClientHandle::MeshDataClientHandle(MeshData* d) : mesh_data(d) {
  g_graphics->AddMeshDataCreate(mesh_data);
}

MeshDataClientHandle::~MeshDataClientHandle() {
  g_graphics->AddMeshDataDestroy(mesh_data);
}

}  // namespace ballistica
