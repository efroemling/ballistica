// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/render_target.h"

#include "ballistica/graphics/graphics_server.h"

namespace ballistica {

RenderTarget::RenderTarget(Type type) : type_(type) {
  assert(InGraphicsThread());
}

RenderTarget::~RenderTarget() = default;

void RenderTarget::ScreenSizeChanged() {
  assert(type_ == Type::kScreen);
  physical_width_ = g_graphics_server->screen_pixel_width();
  physical_height_ = g_graphics_server->screen_pixel_height();
}

auto RenderTarget::GetScissorX(float x) const -> float {
  if (IsVRMode()) {
    // map -0.05f to 1.1f in logical coordinates to 0 to 1 physical ones
    float res_x_virtual = g_graphics_server->screen_virtual_width();
    return physical_width_
           * (((x / res_x_virtual) + (kVRBorder * 0.5f)) / (1.0f + kVRBorder));
  } else {
    if (g_graphics_server->tv_border()) {
      // map -0.05f to 1.1f in logical coordinates to 0 to 1 physical ones
      float res_x_virtual = g_graphics_server->screen_virtual_width();
      return physical_width_
             * (((x / res_x_virtual) + (kTVBorder * 0.5f))
                / (1.0f + kTVBorder));
    } else {
      return (physical_width_ / g_graphics_server->screen_virtual_width()) * x;
    }
  }
}
auto RenderTarget::GetScissorY(float y) const -> float {
  if (IsVRMode()) {
    // map -0.05f to 1.1f in logical coordinates to 0 to 1 physical ones
    float res_y_virtual = g_graphics_server->screen_virtual_height();
    return physical_height_
           * (((y / res_y_virtual) + (kVRBorder * 0.5f)) / (1.0f + kVRBorder));
  } else {
    if (g_graphics_server->tv_border()) {
      // map -0.05f to 1.1f in logical coordinates to 0 to 1 physical ones
      float res_y_virtual = g_graphics_server->screen_virtual_height();
      return physical_height_
             * (((y / res_y_virtual) + (kTVBorder * 0.5f))
                / (1.0f + kTVBorder));
    } else {
      return (physical_height_ / g_graphics_server->screen_virtual_height())
             * y;
    }
  }
}
auto RenderTarget::GetScissorScaleX() const -> float {
  if (IsVRMode()) {
    float f = physical_width_ / g_graphics_server->screen_virtual_width();
    return f / (1.0f + kVRBorder);
  } else {
    float f = physical_width_ / g_graphics_server->screen_virtual_width();
    if (g_graphics_server->tv_border()) {
      return f / (1.0f + kTVBorder);
    }
    return f;
  }
}

auto RenderTarget::GetScissorScaleY() const -> float {
  if (IsVRMode()) {
    float f = physical_height_ / g_graphics_server->screen_virtual_height();
    return f / (1.0f + kVRBorder);
  } else {
    float f = physical_height_ / g_graphics_server->screen_virtual_height();
    if (g_graphics_server->tv_border()) {
      return f / (1.0f + kTVBorder);
    }
    return f;
  }
}

}  // namespace ballistica
