// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_FRAME_DEF_VIEW_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_FRAME_DEF_VIEW_H_

#include <memory>

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/support/depth_of_field.h"
#include "ballistica/base/graphics/support/render_view.h"
#include "ballistica/shared/math/vector2f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// One RenderView's share of a frame-def: the passes its world gets
/// drawn into for the frame, along with everything about the view the
/// renderer needs in order to draw them (captured from the view when
/// its share of the frame is started, as the frame is rendered later
/// and on another thread).
///
/// Passes that belong to the screen rather than to any one world
/// (overlays, ui) stay with the FrameDef itself.
///
/// Design: docs/initiatives/render-views.md.
class FrameDefView {
 public:
  explicit FrameDefView(FrameDef* frame_def);
  ~FrameDefView();

  /// Ready ourself for a new frame of the provided view. The quality
  /// passed is the app's current one; we draw at that or the view's
  /// maximum, whichever is lower.
  void Reset(RenderView* view, GraphicsQuality app_quality);

  /// Called when all drawing for the frame has been submitted.
  void Complete();

  auto light_pass() const -> RenderPass* { return light_pass_.get(); }
  auto light_shadow_pass() const -> RenderPass* {
    return light_shadow_pass_.get();
  }
  auto beauty_pass() const -> RenderPass* { return beauty_pass_.get(); }
  auto beauty_pass_bg() const -> RenderPass* { return beauty_pass_bg_.get(); }
  auto overlay_3d_pass() const -> RenderPass* { return overlay_3d_pass_.get(); }
  auto blit_pass() const -> RenderPass* { return blit_pass_.get(); }

  /// The id of the view we are a frame of.
  auto view_id() const -> int { return view_id_; }
  auto output() const -> RenderView::Output { return output_; }

  /// Size in pixels of the texture we draw to (texture views only).
  auto width() const -> int {
    assert(output_ == RenderView::Output::kTexture);
    return width_;
  }
  auto height() const -> int {
    assert(output_ == RenderView::Output::kTexture);
    return height_;
  }

  /// The graphics quality we are drawn at. Drawing code choosing what
  /// to draw by quality wants this one, not the app's.
  auto quality() const -> GraphicsQuality { return quality_; }

  /// What is in focus. Reset to following areas of interest for each
  /// frame; a camera wanting otherwise says so as it is applied.
  auto depth_of_field() const -> const DepthOfField& { return depth_of_field_; }
  void set_depth_of_field(const DepthOfField& val) { depth_of_field_ = val; }

  auto clear_color() const -> const Vector3f& { return clear_color_; }
  auto orbiting() const -> bool { return orbiting_; }
  auto shadow_offset() const -> const Vector3f& { return shadow_offset_; }
  auto shadow_scale() const -> const Vector2f& { return shadow_scale_; }
  auto shadow_ortho() const -> bool { return shadow_ortho_; }
  auto tint() const -> const Vector3f& { return tint_; }
  auto ambient_color() const -> const Vector3f& { return ambient_color_; }
  auto vignette_outer() const -> const Vector3f& { return vignette_outer_; }
  auto vignette_inner() const -> const Vector3f& { return vignette_inner_; }

 private:
  int view_id_{};
  RenderView::Output output_{RenderView::Output::kScreen};
  int width_{};
  int height_{};
  GraphicsQuality quality_{};
  DepthOfField depth_of_field_;
  bool orbiting_{};
  bool shadow_ortho_{};
  Vector3f clear_color_{0.0f, 0.0f, 0.0f};
  Vector3f shadow_offset_{0.0f, 0.0f, 0.0f};
  Vector2f shadow_scale_{1.0f, 1.0f};
  Vector3f tint_{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_inner_{1.0f, 1.0f, 1.0f};
  std::unique_ptr<RenderPass> light_pass_;
  std::unique_ptr<RenderPass> light_shadow_pass_;
  std::unique_ptr<RenderPass> beauty_pass_;
  std::unique_ptr<RenderPass> beauty_pass_bg_;
  std::unique_ptr<RenderPass> overlay_3d_pass_;
  std::unique_ptr<RenderPass> blit_pass_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_FRAME_DEF_VIEW_H_
