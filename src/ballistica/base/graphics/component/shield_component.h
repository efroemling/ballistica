// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_SHIELD_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_SHIELD_COMPONENT_H_

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

// handles special cases such as drawing light/shadow/back buffers.
class ShieldComponent : public RenderComponent {
 public:
  explicit ShieldComponent(RenderPass* pass) : RenderComponent(pass) {}

 protected:
  void WriteConfig() override;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_SHIELD_COMPONENT_H_
