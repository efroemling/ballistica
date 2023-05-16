// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_ASSETS_SCENE_CUBE_MAP_TEXTURE_H_
#define BALLISTICA_SCENE_V1_ASSETS_SCENE_CUBE_MAP_TEXTURE_H_

#include <string>

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/scene_v1/assets/scene_asset.h"

namespace ballistica::scene_v1 {

class SceneCubeMapTexture : public SceneAsset {
 public:
  SceneCubeMapTexture(const std::string& name, Scene* s);

  // return the TextureData currently associated with this texture
  // note that a texture's data can change over time as different
  // versions are spooled in/out/etc
  auto GetTextureData() const -> base::TextureAsset* {
    return texture_data_.Get();
  }
  auto GetAssetTypeName() const -> std::string override {
    return "CubeMapTexture";
  }

 private:
  Object::Ref<base::TextureAsset> texture_data_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_ASSETS_SCENE_CUBE_MAP_TEXTURE_H_
