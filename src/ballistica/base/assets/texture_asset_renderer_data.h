// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_RENDERER_DATA_H_
#define BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_RENDERER_DATA_H_

#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Renderer-specific data (gl tex, etc). To be extended by the renderer.
class TextureAssetRendererData : public Object {
 public:
  auto GetThreadOwnership() const -> ThreadOwnership override {
    return ThreadOwnership::kGraphicsContext;
  }

  // Create the renderer data but don't load it in yet.
  TextureAssetRendererData() = default;

  // Load the data.
  virtual void Load() = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_RENDERER_DATA_H_
