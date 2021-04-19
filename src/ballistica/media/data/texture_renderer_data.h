// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_DATA_TEXTURE_RENDERER_DATA_H_
#define BALLISTICA_MEDIA_DATA_TEXTURE_RENDERER_DATA_H_

namespace ballistica {

// Renderer-specific data (gl tex, etc)
// this is extended by the renderer
class TextureRendererData : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
    return ThreadIdentifier::kMain;
  }

  // Create the renderer data but don't load it in yet.
  TextureRendererData() = default;

  // load the data.
  // if incremental is true, return whether the load was completed
  // (non-incremental loads should always complete)
  virtual void Load() = 0;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_DATA_TEXTURE_RENDERER_DATA_H_
