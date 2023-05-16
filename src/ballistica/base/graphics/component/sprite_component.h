// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_SPRITE_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_SPRITE_COMPONENT_H_

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

class SpriteComponent : public RenderComponent {
 public:
  explicit SpriteComponent(RenderPass* pass) : RenderComponent(pass) {}
  void SetColor(float r, float g, float b, float a = 1.0f) {
    EnsureConfiguring();
    color_r_ = r;
    color_g_ = g;
    color_b_ = b;
    color_a_ = a;
    have_color_ = true;
  }
  void SetCameraAligned(bool c) {
    EnsureConfiguring();
    camera_aligned_ = c;
  }
  void SetOverlay(bool enable) {
    EnsureConfiguring();
    overlay_ = enable;
  }
  void SetExponent(int i) {
    EnsureConfiguring();
    exponent_ = static_cast_check_fit<uint8_t>(i);
  }
  void SetTexture(TextureAsset* t) {
    EnsureConfiguring();
    texture_ = t;
  }

 protected:
  void WriteConfig() override;
  bool have_color_{};
  bool camera_aligned_{};
  bool overlay_{};
  uint8_t exponent_{1};
  float color_r_{1.0f};
  float color_g_{1.0f};
  float color_b_{1.0f};
  float color_a_{1.0f};
  Object::Ref<TextureAsset> texture_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_SPRITE_COMPONENT_H_
