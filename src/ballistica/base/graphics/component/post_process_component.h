// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_POST_PROCESS_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_POST_PROCESS_COMPONENT_H_

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

class PostProcessComponent : public RenderComponent {
 public:
  explicit PostProcessComponent(RenderPass* pass) : RenderComponent(pass) {}
  void SetNormalDistort(float d) {
    EnsureConfiguring();
    normal_distort_ = d;
  }
  void setEyes(bool enable) {
    EnsureConfiguring();
    eyes_ = enable;
  }

 protected:
  void WriteConfig() override;
  bool eyes_{};
  float normal_distort_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_POST_PROCESS_COMPONENT_H_
