// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/graphics/component/smoke_component.h"

namespace ballistica {

void SmokeComponent::WriteConfig() {
  if (overlay_) {
    ConfigForShading(ShadingType::kSmokeOverlay);
    cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
    cmd_buffer_->PutTexture(g_media->GetTexture(SystemTextureID::kSmoke));
  } else {
    ConfigForShading(ShadingType::kSmoke);
    cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
    cmd_buffer_->PutTexture(g_media->GetTexture(SystemTextureID::kSmoke));
  }
}

}  // namespace ballistica
