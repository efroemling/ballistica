// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/component/smoke_component.h"

namespace ballistica {

void SmokeComponent::WriteConfig() {
  if (overlay_) {
    ConfigForShading(ShadingType::kSmokeOverlay);
    cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
    cmd_buffer_->PutTexture(g_assets->GetTexture(SystemTextureID::kSmoke));
  } else {
    ConfigForShading(ShadingType::kSmoke);
    cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
    cmd_buffer_->PutTexture(g_assets->GetTexture(SystemTextureID::kSmoke));
  }
}

}  // namespace ballistica
