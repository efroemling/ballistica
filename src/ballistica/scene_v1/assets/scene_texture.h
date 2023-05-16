// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_TEXTURE_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_TEXTURE_H_

#include <string>

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/scene_v1/assets/scene_asset.h"

namespace ballistica::scene_v1 {

// User-facing texture class.
class SceneTexture : public SceneAsset {
 public:
  SceneTexture(const std::string& name, Scene* scene);
  explicit SceneTexture(const std::string& qr_url);
  ~SceneTexture() override;

  // Return the TextureData currently associated with this texture.
  // Note that a texture's data can change over time as different
  // versions are spooled in/out/etc.
  auto texture_data() const -> base::TextureAsset* {
    return texture_data_.Get();
  }
  auto GetAssetTypeName() const -> std::string override { return "Texture"; }
  void MarkDead();

 protected:
  auto CreatePyObject() -> PyObject* override;

 private:
  Object::Ref<base::TextureAsset> texture_data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_TEXTURE_H_
