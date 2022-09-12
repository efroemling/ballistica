// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_RENDER_TARGET_H_
#define BALLISTICA_GRAPHICS_RENDER_TARGET_H_

#include "ballistica/core/object.h"
#include "ballistica/math/vector4f.h"

namespace ballistica {

// Encapsulates framebuffers, main windows, etc.
class RenderTarget : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadTag override {
    return ThreadTag::kMain;
  }
  enum class Type { kScreen, kFramebuffer };
  explicit RenderTarget(Type type);
  ~RenderTarget() override;

  // Clear depth, color, etc and get set to draw.
  virtual void DrawBegin(bool clear, float clear_r, float clear_g,
                         float clear_b, float clear_a) = 0;
  void DrawBegin(bool clear,
                 const Vector4f& clear_color = {0.0f, 0.0f, 0.0f, 1.0f}) {
    DrawBegin(clear, clear_color.x, clear_color.y, clear_color.z,
              clear_color.w);
  }

  void ScreenSizeChanged();
  auto physical_width() const -> float { return physical_width_; }
  auto physical_height() const -> float { return physical_height_; }
  auto GetScissorScaleX() const -> float;
  auto GetScissorScaleY() const -> float;
  auto GetScissorX(float x) const -> float;
  auto GetScissorY(float y) const -> float;

 protected:
  float physical_width_{};
  float physical_height_{};
  bool depth_{};
  Type type_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_RENDER_TARGET_H_
