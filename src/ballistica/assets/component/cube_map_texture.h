// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_COMPONENT_CUBE_MAP_TEXTURE_H_
#define BALLISTICA_ASSETS_COMPONENT_CUBE_MAP_TEXTURE_H_

#include <string>

#include "ballistica/assets/component/asset_component.h"
#include "ballistica/assets/data/texture_data.h"

namespace ballistica {

// user-facing texture class
class CubeMapTexture : public AssetComponent {
 public:
  CubeMapTexture(const std::string& name, Scene* s);

  // return the TextureData currently associated with this texture
  // note that a texture's data can change over time as different
  // versions are spooled in/out/etc
  auto GetTextureData() const -> TextureData* { return texture_data_.get(); }
  auto GetAssetComponentTypeName() const -> std::string override {
    return "CubeMapTexture";
  }

 private:
  Object::Ref<TextureData> texture_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_COMPONENT_CUBE_MAP_TEXTURE_H_
