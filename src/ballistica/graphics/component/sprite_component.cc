// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/graphics/component/sprite_component.h"

namespace ballistica {

void SpriteComponent::WriteConfig() {
  // if they didn't give us a texture, just use a blank white texture;
  // this is not a common case and easier than forking all our shaders
  // to create non-textured versions.
  if (!texture_.exists()) {
    texture_ = g_media->GetTexture(SystemTextureID::kWhite);
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
