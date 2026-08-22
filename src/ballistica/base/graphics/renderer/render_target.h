// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_TARGET_H_
#define BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_TARGET_H_

#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/rect.h"
#include "ballistica/shared/math/vector4f.h"

namespace ballistica::base {

// Encapsulates framebuffers, main windows, etc.
class RenderTarget : public Object {
 public:
  auto GetThreadOwnership() const -> ThreadOwnership override {
    return ThreadOwnership::kGraphicsContext;
  }
  enum class Type : uint8_t { kScreen, kFramebuffer };
  explicit RenderTarget(Type type);
  ~RenderTarget() override;

  // Clear depth, color, etc and get set to draw. Callers whose drawing
  // does not rely on depth (color-only blits, etc.) should pass false
  // for clear_depth; depth-buffer contents are then undefined.
  virtual void DrawBegin(bool clear, float clear_r, float clear_g,
                         float clear_b, float clear_a, bool clear_depth) = 0;
  void DrawBegin(bool clear,
                 const Vector4f& clear_color = {0.0f, 0.0f, 0.0f, 1.0f},
                 bool clear_depth = true) {
    DrawBegin(clear, clear_color.x, clear_color.y, clear_color.z, clear_color.a,
              clear_depth);
  }

  void OnScreenSizeChange();
  auto physical_width() const -> float { return physical_width_; }
  auto physical_height() const -> float { return physical_height_; }

  /// The region of this target that game content occupies (pixels,
  /// bottom-left origin). For the screen target this can be an inset
  /// sub-rect (tv-border mode / aspect-ratio limiting); everything
  /// outside it is kept cleared to black. For offscreen targets it is
  /// always the full target.
  auto content_rect() const -> Rect;
  auto content_rect_is_full() const -> bool;

  /// The sub-region of this target that our virtual coord system maps
  /// onto (pixels, bottom-left origin) - content_rect() inset by the
  /// virtual-bounds margins. Equal to content_rect() unless the bounds
  /// are inset. Drawing is NOT confined to this; it just establishes
  /// what virtual coords mean. See Graphics::virtual_bounds_rect.
  auto virtual_bounds_content_rect() const -> Rect;
  auto GetScissorScaleX() const -> float;
  auto GetScissorScaleY() const -> float;
  auto GetScissorX(float x) const -> float;
  auto GetScissorY(float y) const -> float;

 protected:
  bool depth_{};
  Type type_{};
  float physical_width_{};
  float physical_height_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_TARGET_H_
