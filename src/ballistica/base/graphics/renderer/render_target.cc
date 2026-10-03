// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/renderer/render_target.h"

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/core/core.h"

namespace ballistica::base {

RenderTarget::RenderTarget(Type type) : type_(type) {
  assert(g_base->app_adapter->InGraphicsContext());
}

RenderTarget::~RenderTarget() = default;

void RenderTarget::OnScreenSizeChange() {
  assert(type_ == Type::kScreen);
  physical_width_ = g_base->graphics_server->screen_pixel_width();
  physical_height_ = g_base->graphics_server->screen_pixel_height();
}

auto RenderTarget::content_rect() const -> Rect {
  if (type_ == Type::kScreen && !g_core->vr_mode()) {
    return g_base->graphics_server->screen_active_rect();
  }
  return {0.0f, 0.0f, physical_width_, physical_height_};
}

auto RenderTarget::virtual_bounds_content_rect() const -> Rect {
  Rect content = content_rect();

  // A target's content region corresponds to the screen's active render
  // rect (either literally, for the screen itself, or scaled to its own
  // dims for offscreen buffers). So find where the virtual bounds sit
  // within that render rect and apply the same fractions here. Reduces
  // to content_rect() whenever the bounds aren't inset.
  const Rect& rrect = g_base->graphics_server->screen_active_rect();
  const Rect& brect = g_base->graphics_server->screen_virtual_bounds_rect();
  float rw = rrect.width();
  float rh = rrect.height();
  if (rw <= 0.0f || rh <= 0.0f) {
    return content;
  }
  float cw = content.width();
  float ch = content.height();
  return Rect{content.l + cw * ((brect.l - rrect.l) / rw),
              content.b + ch * ((brect.b - rrect.b) / rh),
              content.l + cw * ((brect.r - rrect.l) / rw),
              content.b + ch * ((brect.t - rrect.b) / rh)};
}

auto RenderTarget::content_rect_is_full() const -> bool {
  Rect rect = content_rect();
  return rect.l == 0.0f && rect.b == 0.0f && rect.r == physical_width_
         && rect.t == physical_height_;
}

auto RenderTarget::GetScissorX(float x) const -> float {
  assert(g_core);
  if (g_core->vr_mode()) {
    // map -0.05f to 1.1f in logical coordinates to 0 to 1 physical ones
    float res_x_virtual = g_base->graphics_server->screen_virtual_width();
    return physical_width_
           * (((x / res_x_virtual) + (kVRBorder * 0.5f)) / (1.0f + kVRBorder));
  } else {
    // Map virtual coords onto the region our virtual coord system
    // covers. Coords outside the virtual bounds land outside that
    // region (out in the margins), which is correct - a scissor there
    // should clip where the drawing it is clipping actually lands.
    Rect rect = virtual_bounds_content_rect();
    return rect.l
           + rect.width()
                 * (x / g_base->graphics_server->screen_virtual_width());
  }
}

auto RenderTarget::GetScissorY(float y) const -> float {
  assert(g_core);
  if (g_core->vr_mode()) {
    // map -0.05f to 1.1f in logical coordinates to 0 to 1 physical ones
    float res_y_virtual = g_base->graphics_server->screen_virtual_height();
    return physical_height_
           * (((y / res_y_virtual) + (kVRBorder * 0.5f)) / (1.0f + kVRBorder));
  } else {
    Rect rect = virtual_bounds_content_rect();
    return rect.b
           + rect.height()
                 * (y / g_base->graphics_server->screen_virtual_height());
  }
}

auto RenderTarget::GetScissorScaleX() const -> float {
  assert(g_core);
  if (g_core->vr_mode()) {
    float f = physical_width_ / g_base->graphics_server->screen_virtual_width();
    return f / (1.0f + kVRBorder);
  } else {
    return virtual_bounds_content_rect().width()
           / g_base->graphics_server->screen_virtual_width();
  }
}

auto RenderTarget::GetScissorScaleY() const -> float {
  assert(g_core);
  if (g_core->vr_mode()) {
    float f =
        physical_height_ / g_base->graphics_server->screen_virtual_height();
    return f / (1.0f + kVRBorder);
  } else {
    return virtual_bounds_content_rect().height()
           / g_base->graphics_server->screen_virtual_height();
  }
}

}  // namespace ballistica::base
