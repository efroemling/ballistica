// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_MESH_ASSET_RENDERER_DATA_H_
#define BALLISTICA_BASE_ASSETS_MESH_ASSET_RENDERER_DATA_H_

#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Renderer-specific data (gl display list, etc)
// this is provided by the renderer
class MeshAssetRendererData : public Object {
 public:
  auto GetDefaultOwnerThread() const -> EventLoopID override {
    return EventLoopID::kMain;
  }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_MESH_ASSET_RENDERER_DATA_H_
