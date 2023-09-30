// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/mesh/mesh_data.h"

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/renderer/renderer.h"

namespace ballistica::base {

void MeshData::Load(Renderer* renderer) {
  assert(g_base->app_adapter->InGraphicsContext());
  if (!renderer_data_) {
    renderer_data_ = renderer->NewMeshData(type(), draw_type());
  }
}

void MeshData::Unload(Renderer* renderer) {
  assert(g_base->app_adapter->InGraphicsContext());
  if (renderer_data_) {
    renderer->DeleteMeshData(renderer_data_, type());
    renderer_data_ = nullptr;
  }
}

}  // namespace ballistica::base
