// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_COMPONENT_SPECIAL_COMPONENT_H_
#define BALLISTICA_GRAPHICS_COMPONENT_SPECIAL_COMPONENT_H_

#include "ballistica/graphics/component/render_component.h"

namespace ballistica {

// handles special cases such as drawing light/shadow/back buffers.
class SpecialComponent : public RenderComponent {
 public:
  enum class Source { kLightBuffer, kLightShadowBuffer, kVROverlayBuffer };
  SpecialComponent(RenderPass* pass, Source s)
      : RenderComponent(pass), source_(s) {}

 protected:
  void WriteConfig() override;

 private:
  Source source_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_COMPONENT_SPECIAL_COMPONENT_H_
