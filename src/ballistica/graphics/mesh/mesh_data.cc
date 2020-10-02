// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/graphics/mesh/mesh_data.h"

#include "ballistica/graphics/renderer.h"

namespace ballistica {

void MeshData::Load(Renderer* renderer) {
  assert(InGraphicsThread());
  if (!renderer_data_) {
    renderer_data_ = renderer->NewMeshData(type(), draw_type());
  }
}

void MeshData::Unload(Renderer* renderer) {
  assert(InGraphicsThread());
  if (renderer_data_) {
    renderer->DeleteMeshData(renderer_data_, type());
    renderer_data_ = nullptr;
  }
}

}  // namespace ballistica
