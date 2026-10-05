// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/frame_def_view.h"

#include <algorithm>

#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/camera.h"

namespace ballistica::base {

FrameDefView::FrameDefView(FrameDef* frame_def)
    : light_pass_(
          new RenderPass(RenderPass::Type::kLightPass, frame_def, this)),
      light_shadow_pass_(
          new RenderPass(RenderPass::Type::kLightShadowPass, frame_def, this)),
      beauty_pass_(
          new RenderPass(RenderPass::Type::kBeautyPass, frame_def, this)),
      beauty_pass_bg_(
          new RenderPass(RenderPass::Type::kBeautyPassBG, frame_def, this)),
      overlay_3d_pass_(
          new RenderPass(RenderPass::Type::kOverlay3DPass, frame_def, this)),
      blit_pass_(new RenderPass(RenderPass::Type::kBlitPass, frame_def, this)) {
}

FrameDefView::~FrameDefView() = default;

void FrameDefView::Reset(RenderView* view, GraphicsQuality app_quality) {
  assert(g_base->InLogicThread());
  assert(view);

  view_id_ = view->id();
  output_ = view->output();
  if (output_ == RenderView::Output::kTexture) {
    width_ = view->width();
    height_ = view->height();
  } else {
    width_ = height_ = 0;
  }
  quality_ = view->GetQuality(app_quality);
  depth_of_field_ = DepthOfField();
  clear_color_ = view->clear_color();

  orbiting_ = (view->camera()->mode() == CameraMode::kOrbit);

  shadow_offset_ = view->shadow_offset();
  shadow_scale_ = view->shadow_scale();
  shadow_ortho_ = view->shadow_ortho();
  tint_ = view->tint();
  ambient_color_ = view->ambient_color();

  vignette_outer_ = view->vignette_outer();
  vignette_inner_ = view->vignette_inner();

  // Note: passes look to us for their size and quality, so this needs
  // to come after those are set.
  light_pass_->Reset();
  light_shadow_pass_->Reset();
  beauty_pass_->Reset();
  beauty_pass_bg_->Reset();
  overlay_3d_pass_->Reset();
  blit_pass_->Reset();
  beauty_pass_->set_floor_reflection(view->floor_reflection());
}

void FrameDefView::Complete() {
  light_pass_->Complete();
  light_shadow_pass_->Complete();
  beauty_pass_->Complete();
  beauty_pass_bg_->Complete();
  overlay_3d_pass_->Complete();
  blit_pass_->Complete();
}

}  // namespace ballistica::base
