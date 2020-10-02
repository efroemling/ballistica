// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_COMPONENT_EMPTY_COMPONENT_H_
#define BALLISTICA_GRAPHICS_COMPONENT_EMPTY_COMPONENT_H_

#include "ballistica/graphics/component/render_component.h"

namespace ballistica {

// Empty component - has no shader but can be useful for spitting out
// transform/scissor/etc state changes.
class EmptyComponent : public RenderComponent {
 public:
  explicit EmptyComponent(RenderPass* pass)
      : RenderComponent(pass), transparent_(false) {}
  void SetTransparent(bool val) {
    EnsureConfiguring();
    transparent_ = val;
  }

 protected:
  void WriteConfig() override { ConfigForEmpty(transparent_); }

 private:
  bool transparent_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_COMPONENT_EMPTY_COMPONENT_H_
