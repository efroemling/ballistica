// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_COMPONENT_CUBE_MAP_TEXTURE_H_
#define BALLISTICA_MEDIA_COMPONENT_CUBE_MAP_TEXTURE_H_

#include <string>

#include "ballistica/media/component/media_component.h"
#include "ballistica/media/data/texture_data.h"

namespace ballistica {

// user-facing texture class
class CubeMapTexture : public MediaComponent {
 public:
  CubeMapTexture(const std::string& name, Scene* s);

  // return the TextureData currently associated with this texture
  // note that a texture's data can change over time as different
  // versions are spooled in/out/etc
  auto GetTextureData() const -> TextureData* { return texture_data_.get(); }
  auto GetMediaComponentTypeName() const -> std::string override {
    return "CubeMapTexture";
  }

 private:
  Object::Ref<TextureData> texture_data_;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_COMPONENT_CUBE_MAP_TEXTURE_H_
