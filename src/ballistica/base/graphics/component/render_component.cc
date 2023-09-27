// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

void RenderComponent::ScissorPush(const Rect& rect) {
  EnsureDrawing();
  cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScissorPush);
  cmd_buffer_->PutFloats(rect.l, rect.b, rect.r, rect.t);
}

#if BA_DEBUG_BUILD
void RenderComponent::ConfigForEmptyDebugChecks(bool transparent) {
  assert(g_base->InLogicThread());
  if (g_base->graphics->drawing_opaque_only() && transparent) {
    throw Exception("Transparent component submitted in opaque-only section");
  }
  if (g_base->graphics->drawing_transparent_only() && !transparent) {
    throw Exception("Opaque component submitted in transparent-only section");
  }
}

void RenderComponent::ConfigForShadingDebugChecks(ShadingType shading_type) {
  assert(g_base->InLogicThread());
  if (g_base->graphics->drawing_opaque_only()
      && Graphics::IsShaderTransparent(shading_type)) {
    throw Exception("Transparent component submitted in opaque-only section");
  }
  if (g_base->graphics->drawing_transparent_only()
      && !Graphics::IsShaderTransparent(shading_type)) {
    throw Exception("Opaque component submitted in transparent-only section");
  }
}
#endif  // BA_DEBUG_BUILD

}  // namespace ballistica::base
