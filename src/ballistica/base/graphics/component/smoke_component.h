// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_SMOKE_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_SMOKE_COMPONENT_H_

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

class SmokeComponent : public RenderComponent {
 public:
  explicit SmokeComponent(RenderPass* pass) : RenderComponent(pass) {}

  void SetColor(float r, float g, float b, float a = 1.0f) {
    EnsureConfiguring();
    color_r_ = r;
    color_g_ = g;
    color_b_ = b;
    color_a_ = a;
  }

  void SetOverlay(bool overlay) {
    EnsureConfiguring();
    overlay_ = overlay;
  }

 protected:
  void WriteConfig() override;

  bool overlay_{};
  float color_r_{1.0f};
  float color_g_{1.0f};
  float color_b_{1.0f};
  float color_a_{1.0f};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_SMOKE_COMPONENT_H_
