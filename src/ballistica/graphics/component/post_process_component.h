// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_COMPONENT_POST_PROCESS_COMPONENT_H_
#define BALLISTICA_GRAPHICS_COMPONENT_POST_PROCESS_COMPONENT_H_

#include "ballistica/graphics/component/render_component.h"

namespace ballistica {

class PostProcessComponent : public RenderComponent {
 public:
  explicit PostProcessComponent(RenderPass* pass)
      : RenderComponent(pass), normal_distort_(0.0f), eyes_(false) {}
  void setNormalDistort(float d) {
    EnsureConfiguring();
    normal_distort_ = d;
  }
  void setEyes(bool enable) {
    EnsureConfiguring();
    eyes_ = enable;
  }

 protected:
  void WriteConfig() override;
  bool eyes_;
  float normal_distort_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_COMPONENT_POST_PROCESS_COMPONENT_H_
