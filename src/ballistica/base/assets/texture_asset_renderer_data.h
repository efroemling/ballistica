// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_RENDERER_DATA_H_
#define BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_RENDERER_DATA_H_

#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Renderer-specific data (gl tex, etc)
// this is extended by the renderer
class TextureAssetRendererData : public Object {
 public:
  auto GetDefaultOwnerThread() const -> EventLoopID override {
    return EventLoopID::kMain;
  }

  // Create the renderer data but don't load it in yet.
  TextureAssetRendererData() = default;

  // load the data.
  // if incremental is true, return whether the load was completed
  // (non-incremental loads should always complete)
  virtual void Load() = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_RENDERER_DATA_H_
