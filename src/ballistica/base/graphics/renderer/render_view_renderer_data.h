// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_VIEW_RENDERER_DATA_H_
#define BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_VIEW_RENDERER_DATA_H_

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/renderer/render_target.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// What a Renderer holds on behalf of one RenderView: the buffers that
/// view's world is drawn through and the look it is set up to draw
/// with.
///
/// Each view gets its own so that views share nothing: drawing one
/// world can't disturb another's shadows, depth, or blur. This is
/// plain state for the renderer's use (the renderer reaches what it
/// needs of the view being drawn through Renderer::view_data());
/// particular renderers extend it with their own per-view resources.
///
/// Design: docs/initiatives/render-views.md.
struct RenderViewRendererData : public Object {
  auto GetThreadOwnership() const -> ThreadOwnership override {
    return ThreadOwnership::kGraphicsContext;
  }

  // The quality our buffers were last set up for; they get rebuilt if
  // the view comes to be drawn at another.
  GraphicsQuality quality{GraphicsQuality::kUnset};

  // For views drawing to a texture, what their world ends up in; its
  // color buffer is that texture. (The main view's ends up on the
  // screen and has none of this.)
  Object::Ref<RenderTarget> output_render_target;
  int output_width{};
  int output_height{};

  // Light and shadow get drawn into these and then projected onto the
  // world as it is drawn.
  Object::Ref<RenderTarget> light_render_target;
  Object::Ref<RenderTarget> light_shadow_render_target;
  int shadow_res{-1};

  // In higher-quality modes the world is drawn into these (the
  // multisampled one, if present, gets resolved into the plain one) so
  // that depth-of-field and the like can be applied as it is copied to
  // wherever it is headed.
  Object::Ref<RenderTarget> camera_render_target;
  Object::Ref<RenderTarget> camera_msaa_render_target;
  int blur_res_count{};

  // For views drawing to a texture, the output size and quality their
  // camera targets were made for (the main view's follow the screen's,
  // which are kept track of elsewhere).
  int camera_for_width{};
  int camera_for_height{};
  GraphicsQuality camera_for_quality{GraphicsQuality::kUnset};

  // The look we're set to draw with (from the frame-def).
  bool shadow_ortho{};
  float shadow_scale_x{1.0f};
  float shadow_scale_z{1.0f};
  Vector3f shadow_offset{0.0f, 0.0f, 0.0f};
  Vector3f tint{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer{0.0f, 0.0f, 0.0f};
  Vector3f vignette_inner{1.0f, 1.0f, 1.0f};

  float light_pitch{};
  float light_heading{};
  float light_tz{-22.0f};

  // Depth-of-field range, eased toward where the areas of interest
  // are.
  float dof_near_smoothed{};
  float dof_far_smoothed{};
  millisecs_t dof_update_time{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_VIEW_RENDERER_DATA_H_
