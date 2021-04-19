// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_COMPONENT_SMOKE_COMPONENT_H_
#define BALLISTICA_GRAPHICS_COMPONENT_SMOKE_COMPONENT_H_

#include "ballistica/graphics/component/render_component.h"

namespace ballistica {

class SmokeComponent : public RenderComponent {
 public:
  explicit SmokeComponent(RenderPass* pass)
      : RenderComponent(pass),
        color_r_(1.0f),
        color_g_(1.0f),
        color_b_(1.0f),
        color_a_(1.0f),
        overlay_(false) {}
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
  float color_r_, color_g_, color_b_, color_a_;
  bool overlay_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_COMPONENT_SMOKE_COMPONENT_H_
