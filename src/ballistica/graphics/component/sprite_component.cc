// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/component/sprite_component.h"

namespace ballistica {

void SpriteComponent::WriteConfig() {
  // if they didn't give us a texture, just use a blank white texture;
  // this is not a common case and easier than forking all our shaders
  // to create non-textured versions.
  if (!texture_.exists()) {
    texture_ = g_assets->GetTexture(SystemTextureID::kWhite);
  }
  if (exponent_ == 1) {
    ConfigForShading(ShadingType::kSprite);
    cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
    cmd_buffer_->PutInt(overlay_);
    cmd_buffer_->PutInt(camera_aligned_);
    cmd_buffer_->PutTexture(texture_);
  } else {
    throw Exception();
  }
}

}  // namespace ballistica
