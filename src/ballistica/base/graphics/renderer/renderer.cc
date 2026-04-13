// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/renderer/renderer.h"

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/core/core.h"

#if BA_VR_BUILD
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/graphics_vr.h"
#endif

namespace ballistica::base {

#if BA_VR_BUILD
const float kBaseVRWorldScale = 1.38f;
const float kInvVRHeadScale = 1.0f / (kBaseVRWorldScale * kDefaultVRHeadScale);
#endif

// There can be only one!.. at a time.
static bool have_renderer = false;

Renderer::Renderer() {
  assert(!have_renderer);
  have_renderer = true;
}

Renderer::~Renderer() {
  assert(have_renderer);
  have_renderer = false;
}

void Renderer::PreprocessFrameDef(FrameDef* frame_def) {
  assert(g_base->app_adapter->InGraphicsContext());

  // If this frame_def was made in a different quality mode than we're
  // currently in, don't attempt to render it.
  // UPDATE - scratch that; we now set our quality FROM the frame def.
  // if (frame_def->quality() != g_base->graphics_server->quality()) {
  //   frame_def->set_rendering(false);
  //   return;
  // }

  frame_def->set_rendering(true);

  // Some VR environments muck with render states before/after
  // they call us; resync as needed....
#if BA_VR_BUILD
  if (g_core->vr_mode()) {
    VRSyncRenderStates();
  }
#endif  // BA_VR_BUILD

  // Setup various high level stuff to match the frame_def
  // (tint colors, resolutions, etc).
  UpdateSizesQualitiesAndColors(frame_def);

  // Handle a weird gamma reset issue on our legacy mac build (SDL 1.2).
  // #if BA_PLATFORM_MACOS && BA_SDL_BUILD && !BA_SDL2_BUILD
  //   HandleFunkyMacGammaIssue(frame_def);
  // #endif

  // In some cases we draw to a lower-res backing buffer instead of native
  // screen res.
  UpdatePixelScaleAndBackingBuffer(frame_def);

  // Update the buffers for world drawing, blurred versions of that, etc.
  UpdateCameraRenderTargets(frame_def);

  // (re)create our light/shadow buffers if need be
  UpdateLightAndShadowBuffers(frame_def);

  // Update various VR values such as clip planes and head positions.
#if BA_VR_BUILD
  VRPreprocess(frame_def);
#endif  // BA_VR_BUILD

  // Pull latest mesh data in from this frame_def.
  UpdateMeshes(frame_def->meshes(), frame_def->mesh_index_sizes(),
               frame_def->mesh_buffers());

  // Ensure all media used by this frame_def is loaded.
  LoadMedia(frame_def);

  // Draw our light/shadow textures.
  RenderLightAndShadowPasses(frame_def);

  // In vr mode we draw our UI into a buffer.
#if BA_VR_BUILD
  VRDrawOverlayFlatPass(frame_def);
#endif  // BA_VR_BUILD
}

// actually render one of these frame_def suckers...
// (called within the graphics thread)
void Renderer::RenderFrameDef(FrameDef* frame_def) {
  assert(g_base->app_adapter->InGraphicsContext());

  // If preprocess decided not to render this.
  if (!frame_def->rendering()) return;

  // Set camera/hand/etc positioning with latest VR data if applicable.
  // (we do this here at render time as opposed to frame construction time
  // so we have the most up-to-date data possible).
#if BA_VR_BUILD
  VRUpdateForEyeRender(frame_def);
#endif  // BA_VR_BUILD

  // In higher-quality modes we draw the world into the camera buffer
  // which we'll later render into the backing buffer with depth-of-field
  // and other stuff added.
  if (camera_render_target_.exists()) {
    DrawWorldToCameraBuffer(frame_def);
  }

  // ..now draw everything into our backing target; either our camera
  // buffer (high qual modes) or the world (med/low qual).
  PushGroupMarker("Backing Opaque Pass");
  SetDepthWriting(true);
  SetDepthTesting(true);
  RenderTarget* backing;
  if (backing_render_target_.exists()) {
    backing = backing_render_target();
  } else {
    backing = screen_render_target();
  }

  bool backing_needs_clear = frame_def->needs_clear();
#if BA_VARIANT_CARDBOARD
  // On cardboard, our two eyes are drawn into the same FBO,
  // so we can't invalidate the buffer when drawing our second eye
  // (since that could wipe out the first eye which has already been drawn)
  // ..so for the second eye we force a clear, which nicely stays within the
  // already-set-up scissor-rect
  if (vr_eye_ == 1) {
    backing_needs_clear = true;
  }
#endif
  backing->DrawBegin(backing_needs_clear);

  bool overlays_in_3d = g_core->vr_mode();
  bool overlays_in_2d = !overlays_in_3d;

  // Draw opaque stuff front-to-back.
  if (overlays_in_2d) {
    frame_def->overlay_front_pass()->Render(backing, false);
    frame_def->overlay_pass()->Render(backing, false);
  }

  // In vr mode, the front section of the depth buffer that would have been
  // used for our 2d ortho overlays is instead used for our vr-fade pass,
  // which is nothing but our little bomb shaped transition wipe thing
  // (it needs its own depth section otherwise it intersects with stuff out in
  // the world).
  if (overlays_in_3d) {
    frame_def->vr_cover_pass()->Render(backing, false);
    frame_def->overlay_front_pass()->Render(backing, false);
    frame_def->overlay_pass()->Render(backing, false);
    frame_def->overlay_fixed_pass()->Render(backing, false);
  }
  if (camera_render_target_.exists()) {
    UpdateDOFParams(frame_def);
    // We've already drawn the world.
    // Now just draw our blit shapes (opaque shapes which blit portions of the
    // camera render to the screen) ..these is so we can do things like
    // distortion on large areas without blitting any part of the bg more than
    // once. (unlike if we did that in the overlay-3d pass or whatnot).
    frame_def->blit_pass()->Render(backing, false);
  } else {
    // Otherwise just draw the world straight to the backing
    // (lower quality modes).
    frame_def->beauty_pass()->Render(backing, false);
    frame_def->beauty_pass_bg()->Render(backing, false);
  }
  PopGroupMarker();
  PushGroupMarker("Backing Transparent Pass");
  SetDepthWriting(false);

  // We may run out of precision in our depth buffer for deeply nested UI stuff
  // and whatnot. This ensures overlay stuff never gets occluded by stuff
  // 'behind' it because of this lack of precision.
  SetDrawAtEqualDepth(true);

  // Now draw transparent stuff back to front.
  if (camera_render_target_.exists()) {
    // When copying camera buffer to the backing there's nothing transparent
    // to draw.
  } else {
    frame_def->beauty_pass_bg()->Render(backing, true);
    frame_def->beauty_pass()->Render(backing, true);
  }
  frame_def->overlay_3d_pass()->Render(backing, true);
  if (overlays_in_3d) {
    frame_def->overlay_fixed_pass()->Render(backing, true);
    frame_def->overlay_pass()->Render(backing, true);
    frame_def->overlay_front_pass()->Render(backing, true);
  }
  if (overlays_in_2d) {
    frame_def->overlay_pass()->Render(backing, true);
    frame_def->overlay_front_pass()->Render(backing, true);
  }

  // In vr mode, the front section of the depth buffer that would have been
  // used for our 2d ortho overlays is instead used for our vr-fade pass,
  // which is nothing but our little bomb shaped transition wipe thing
  // (it needs its own depth section otherwise it intersects with stuff out
  // in the world).
  if (overlays_in_3d) {
    frame_def->vr_cover_pass()->Render(backing, true);
  }

  // For debugging our DOF passes, etc.
  DrawDebug();
  PopGroupMarker();

  // If we've been drawing to a backing buffer, blit it to the screen.
  if (backing_render_target_.exists()) {
    // FIXME - should we just be discarding both depth and color
    //  after the blit?.. (of course, this code path shouldn't be used on
    //  mobile/slow-stuff so maybe it doesn't matter)

    // We're now done with the depth buffer on our backing; just need to copy
    // color to the screen buffer.
    InvalidateFramebuffer(false, true, false);

    // Note: We're forcing a shader-based blit for the moment; hardware blit
    // seems to be flaky on qualcomm hardware as of jan 14 (adreno 330, adreno
    // 320).
    BlitBuffer(backing, screen_render_target(), false, true, true, true);
  }

  // Lastly, we no longer need depth on our screen target.
  InvalidateFramebuffer(false, true, false);

  RenderFrameDefEnd();
}

void Renderer::FinishFrameDef(FrameDef* frame_def) {
  frames_rendered_count_++;

  // Give the renderer a chance to check for/report errors.
  CheckForErrors();
}

#if BA_VR_BUILD

void Renderer::VRPreprocess(FrameDef* frame_def) {
  if (!g_core->vr_mode()) {
    return;
  }

  // if we're in VR mode, make sure we've got our VR overlay target
  if (!vr_overlay_flat_render_target_.exists()) {
    // find this res to be ideal on current gen equipment
    // (2017-ish, 1st gen rift/gear-vr/etc)
    // ..can revisit once higher-res stuff is commonplace
    int base_res = 1024;
    vr_overlay_flat_render_target_ = NewFramebufferRenderTarget(
        base_res,
        base_res
            * (static_cast<float>(kBaseVirtualResY)
               / static_cast<float>(kBaseVirtualResX)),
        true,   // linear_interp
        true,   // depth
        true,   // tex
        false,  // depthTex
        true,   // high-quality
        false,  // msaa
        true    // alpha
    );          // NOLINT(whitespace/parens)
  }
  auto* vrgraphics = GraphicsVR::get();

  // Also store our custom near clip plane dist.
  frame_def->set_vr_near_clip(vrgraphics->vr_near_clip());

  Vector3f cam_pt(frame_def->cam_original().x, frame_def->cam_original().y,
                  frame_def->cam_original().z);

  float world_scale =
      kBaseVRWorldScale * GraphicsVR::get()->vr_test_head_scale();

  float extra_yaw =
      (frame_def->camera_mode() == CameraMode::kOrbit) ? -0.3f : 0.0f;
  vr_base_transform_ = Matrix44fRotate(Vector3f(0, 1, 0), extra_yaw * kDegPi)
                       * Matrix44fScale(world_scale)
                       * Matrix44fTranslate(cam_pt.x, cam_pt.y, cam_pt.z);

  // given our raw VR head/hand transforms, calc our in-game transforms
  vr_transform_right_hand_ =
      Matrix44fRotate(Vector3f(0, 0, 1), -vr_raw_hands_state_.r.roll * kDegPi)
      * Matrix44fRotate(Vector3f(1, 0, 0),
                        -vr_raw_hands_state_.r.pitch * kDegPi)
      * Matrix44fRotate(Vector3f(0, 1, 0),
                        180.0f + vr_raw_hands_state_.r.yaw * kDegPi)
      * Matrix44fScale(kInvVRHeadScale)
      * Matrix44fTranslate(vr_raw_hands_state_.r.tx, vr_raw_hands_state_.r.ty,
                           vr_raw_hands_state_.r.tz)
      * vr_base_transform_;
  vr_transform_left_hand_ =
      Matrix44fRotate(Vector3f(0, 0, 1), -vr_raw_hands_state_.l.roll * kDegPi)
      * Matrix44fRotate(Vector3f(1, 0, 0),
                        -vr_raw_hands_state_.l.pitch * kDegPi)
      * Matrix44fRotate(Vector3f(0, 1, 0),
                        180.0f + vr_raw_hands_state_.l.yaw * kDegPi)
      * Matrix44fScale(kInvVRHeadScale)
      * Matrix44fTranslate(vr_raw_hands_state_.l.tx, vr_raw_hands_state_.l.ty,
                           vr_raw_hands_state_.l.tz)
      * vr_base_transform_;
  vr_transform_head_ =
      Matrix44fRotate(Vector3f(0, 0, 1), -vr_raw_head_roll_ * kDegPi)
      * Matrix44fRotate(Vector3f(1, 0, 0), -vr_raw_head_pitch_ * kDegPi)
      * Matrix44fRotate(Vector3f(0, 1, 0), 180.0f + vr_raw_head_yaw_ * kDegPi)
      * Matrix44fScale(kInvVRHeadScale)
      * Matrix44fTranslate(vr_raw_head_tx_, vr_raw_head_ty_, vr_raw_head_tz_)
      * vr_base_transform_;

  if (g_core->reset_vr_orientation) {
    g_core->reset_vr_orientation = false;
  }

  Vector3f translate = vr_transform_head_.GetTranslate();
  Vector3f forward = vr_transform_head_.LocalZAxis();
  Vector3f up = vr_transform_head_.LocalYAxis();

  // stuff this into our graphics state for rendered stuff to use
  vrgraphics->set_vr_head_forward(forward);
  vrgraphics->set_vr_head_up(up);
  vrgraphics->set_vr_head_translate(translate);
}

void Renderer::VRUpdateForEyeRender(FrameDef* frame_def) {
  if (!g_core->vr_mode()) {
    return;
  }
  VREyeRenderBegin();
  float world_scale =
      kBaseVRWorldScale * GraphicsVR::get()->vr_test_head_scale();
  Matrix44f eye_transform =
      Matrix44fRotate(Vector3f(0, 0, 1), -vr_eye_roll_ * kDegPi)
      * Matrix44fRotate(Vector3f(1, 0, 0), -vr_eye_pitch_ * kDegPi)
      * Matrix44fRotate(Vector3f(0, 1, 0), 180.0f + (vr_eye_yaw_)*kDegPi)
      * Matrix44fScale(kInvVRHeadScale)
      * Matrix44fTranslate(vr_eye_x_, vr_eye_y_, vr_eye_z_)
      * vr_base_transform_;

  // lastly, plug our eye_transform into our render pass cameras
  // NOTE - because VR has different clipping requirements,
  // we may be setting a different near plane than our usual drawing
  // which currently throws off some of our hard-coded shaders such as DOF..
  // need to look into refactoring those to behave with varied clip ranges.
  // For now we work around it by minimizing DOF effects in VR mode.
  Vector3f offs = eye_transform * Vector3f(0, 0, 0);
  // shaking in VR is odd; turn it off for now.
  float shake_amt = 0.00f;
  float shake_pos_x = frame_def->shake_original().x * shake_amt;
  float shake_pos_y = frame_def->shake_original().y * shake_amt;
  float shake_pos_z = frame_def->shake_original().z * shake_amt;
  Vector3f target_offs =
      eye_transform
      * Vector3f(0 + shake_pos_x, 0 + shake_pos_y, 1 + shake_pos_z);
  Vector3f up = (eye_transform * Vector3f(0, 1, 0)) - offs;
  float near_clip = frame_def->vr_near_clip();
  // if we're doing VR cameras, overwrite the default camera with
  // the eye cam here..
  RenderPass* passes[] = {frame_def->beauty_pass(),
                          frame_def->beauty_pass_bg(),
                          frame_def->overlay_3d_pass(),
                          frame_def->blit_pass(),
                          frame_def->overlay_pass(),
                          frame_def->overlay_front_pass(),
                          frame_def->vr_cover_pass(),
                          frame_def->GetOverlayFixedPass(),
                          nullptr};
  for (RenderPass** p = passes; *p != nullptr; p++) {
    (**p).SetCamera(offs, target_offs, up, near_clip, 1000.0f,
                    vr_fov_degrees_x_, vr_fov_degrees_y_, vr_use_fov_tangents_,
                    vr_fov_l_tan_, vr_fov_r_tan_, vr_fov_b_tan_, vr_fov_t_tan_,
                    passes[0]->cam_area_of_interest_points());
  }
}

void Renderer::VRDrawOverlayFlatPass(FrameDef* frame_def) {
  if (g_core->vr_mode()) {
    // The overlay-flat pass should generally only have commands in it
    // when UI is visible; skip rendering it if not.
    if (frame_def->overlay_flat_pass()->HasDrawCommands()) {
      PushGroupMarker("VR Overlay Flat Pass");
      SetDepthWriting(true);
      SetDepthTesting(true);
      RenderTarget* r_target = vr_overlay_flat_render_target();
      r_target->DrawBegin(true, 0, 0, 0, 0);
      frame_def->overlay_flat_pass()->Render(r_target, false);  // opaque stuff
      SetDepthWriting(false);

      // So our transparent stuff matching opaque stuff in depth gets drawn.
      SetDrawAtEqualDepth(true);

      // Transparent stuff.
      frame_def->overlay_flat_pass()->Render(r_target, true);
      PopGroupMarker();
      SetDepthWriting(false);
      SetDepthTesting(false);
      SetDrawAtEqualDepth(false);
    }
  }
}

void Renderer::VRTransformToRightHand() {
  g_base->graphics_server->MultMatrix(vr_transform_right_hand_);
}

void Renderer::VRTransformToLeftHand() {
  g_base->graphics_server->MultMatrix(vr_transform_left_hand_);
}
void Renderer::VRTransformToHead() {
  g_base->graphics_server->MultMatrix(vr_transform_head_);
}

#endif  // BA_VR_BUILD

void Renderer::UpdateSizesQualitiesAndColors(FrameDef* frame_def) {
  // If screen-size has changed, handle that.
  if (screen_size_dirty_) {
    msaa_enabled_dirty_ = true;
    screen_render_target()->OnScreenSizeChange();

    // These render targets are dependent on screen size so they need to be
    // remade.
    camera_render_target_.Clear();
    camera_msaa_render_target_.Clear();
    backing_render_target_.Clear();
    screen_size_dirty_ = false;
  }

  // Update quality settings to match this frame_def.
  if (last_render_quality_ != frame_def->quality()) {
    light_render_target_.Clear();
    light_shadow_render_target_.Clear();
    if (g_core->vr_mode()) {
      vr_overlay_flat_render_target_.Clear();
    }
  }
  last_render_quality_ = frame_def->quality();
  set_shadow_offset(Vector3f(frame_def->shadow_offset().x,
                             frame_def->shadow_offset().y,
                             frame_def->shadow_offset().z));
  set_shadow_scale(frame_def->shadow_scale().x, frame_def->shadow_scale().y);
  set_shadow_ortho(frame_def->shadow_ortho());
  set_tint(1.5f * frame_def->tint());  // FIXME; why the 1.5?
  set_ambient_color(frame_def->ambient_color());
  set_vignette_inner(frame_def->vignette_inner());
  if (g_core->vr_mode()) {
    // In VR mode we dont want vignetting;
    // just use the inner color for both in and out.
    set_vignette_outer(frame_def->vignette_inner());
  } else {
    set_vignette_outer(frame_def->vignette_outer());
  }
  UpdateVignetteTex_(false);
}

void Renderer::UpdateLightAndShadowBuffers(FrameDef* frame_def) {
  if (!light_render_target_.exists() || !light_shadow_render_target_.exists()) {
    assert(screen_render_target_.exists());

    // Base shadow res on quality.
    if (frame_def->quality() >= GraphicsQuality::kHigher) {
      shadow_res_ = 1024;
      // NOLINTNEXTLINE(bugprone-branch-clone)
    } else if (frame_def->quality() >= GraphicsQuality::kHigh) {
      shadow_res_ = 512;
    } else if (frame_def->quality() >= GraphicsQuality::kMedium) {
      shadow_res_ = 512;
    } else {
      shadow_res_ = 256;
    }

    // 16 bit dithering is a bit noticeable here..
    bool high_qual = true;
    light_render_target_ = NewFramebufferRenderTarget(
        shadow_res_ / kLightResDiv, shadow_res_ / kLightResDiv,
        true,       // linear_interp
        false,      // depth
        true,       // tex
        false,      // depthTex
        high_qual,  // high-quality
        false,      // msaa
        false       // alpha
    );              // NOLINT(whitespace/parens)
    light_shadow_render_target_ =
        NewFramebufferRenderTarget(shadow_res_, shadow_res_,
                                   true,       // linear_interp
                                   false,      // depth
                                   true,       // tex
                                   false,      // depthTex
                                   high_qual,  // high-quality
                                   false,      // msaa
                                   false       // alpha
        );                                     // NOLINT(whitespace/parens)
  }
}

void Renderer::RenderLightAndShadowPasses(FrameDef* frame_def) {
  float light_pitch = 90;
  float light_heading = 0;
  float light_tz = -22;
  SetLight(light_pitch, light_heading, light_tz);

  // Draw our light/shadow buffers.
  SetDepthWriting(false);
  SetDepthTesting(false);
  SetDrawAtEqualDepth(false);
  PushGroupMarker("Light Pass");
  RenderTarget* r_target = light_render_target();
  r_target->DrawBegin(true, kShadowNeutral, kShadowNeutral, kShadowNeutral,
                      1.0f);
  frame_def->light_pass()->Render(r_target, true);
  PopGroupMarker();
  PushGroupMarker("LightShadow Pass");
  r_target = light_shadow_render_target();
  r_target->DrawBegin(true, kShadowNeutral, kShadowNeutral, kShadowNeutral,
                      1.0f);
  frame_def->light_shadow_pass()->Render(r_target, true);
  PopGroupMarker();
}

void Renderer::UpdateCameraRenderTargets(FrameDef* frame_def) {
  // Create or destroy our camera render-target as necessary.
  // In higher-quality modes we render the world into a buffer
  // so we can do depth-of-field filtering and whatnot.
  if (frame_def->quality() >= GraphicsQuality::kHigh) {
    if (!camera_render_target_.exists()) {
      float pixel_scale_fin = std::min(1.0f, std::max(0.1f, pixel_scale_));
      int w = static_cast<int>(screen_render_target_->physical_width()
                               * pixel_scale_fin);
      int h = static_cast<int>(screen_render_target_->physical_height()
                               * pixel_scale_fin);

      // Calc and store the number of blur levels we'll want
      // based on this resolution.
      int max_res = std::max(w, h);
      blur_res_count_ = 0;
      int blur_res = max_res;
      while (blur_res > 250) {
        blur_res_count_++;
        blur_res /= 2;
      }

      // Enforce a minimum.
      if (blur_res_count_ < 4) {
        blur_res_count_ = 4;
      }

      // We limit to a single blur pass in high-quality.
      if (frame_def->quality() == GraphicsQuality::kHigh
          && blur_res_count_ > 1) {
        blur_res_count_ = 1;
      }

      // Now tweak our cam render target res so that its evenly divisible by
      // 2 for that many levels.
      int foo = 1;
      for (int i = 0; i < blur_res_count_; i++) {
        foo *= 2;
      }
      w = ((w % foo == 0) ? w : (w + (foo - (w % foo))));
      h = ((h % foo == 0) ? h : (h + (foo - (h % foo))));
      camera_render_target_ = NewFramebufferRenderTarget(w, h,
                                                         true,  // linear-interp
                                                         true,  // depth
                                                         true,  // tex
                                                         true,  // depth-tex
                                                         false,  // high-qual
                                                         false,  // msaa
                                                         false   // alpha
      );  // NOLINT(whitespace/parens)

      // If screen size just changed or whatnot,
      // update whether we should do msaa.
      if (msaa_enabled_dirty_) {
        UpdateMSAAEnabled_();
        msaa_enabled_dirty_ = false;
      }

      // If we're doing msaa, also create a multi-sample version of the same.
      // We'll draw into this and then blit it to our normal texture-backed
      // camera-target.
      if (IsMSAAEnabled()) {
        camera_msaa_render_target_ =
            NewFramebufferRenderTarget(w, h,
                                       false,  // linear-interp
                                       true,   // depth
                                       false,  // tex
                                       false,  // depth-tex
                                       false,  // high-qual
                                       true,   // msaa
                                       false   // alpha
            );                                 // NOLINT(whitespace/parens)
      }
    }
  } else {
    camera_render_target_.Clear();
    camera_msaa_render_target_.Clear();
    blur_res_count_ = 0;
  }
}

void Renderer::UpdatePixelScaleAndBackingBuffer(FrameDef* frame_def) {
  // If our pixel-scale is changing its essentially the same as a resolution
  // change, so we wanna rebuild our light/shadow buffers and all that.
  if (pixel_scale_requested_ != pixel_scale_) {
    OnScreenSizeChange();
  }

  // Create or destroy our backing render-target as necessary.
  // We need our backing buffer for non-1.0 pixel-scales.
  if (pixel_scale_requested_ != 1.0f) {
    if (pixel_scale_requested_ != pixel_scale_
        || !backing_render_target_.exists()) {
      float pixel_scale_fin =
          std::min(1.0f, std::max(0.1f, pixel_scale_requested_));
      int w = static_cast<int>(screen_render_target_->physical_width()
                               * pixel_scale_fin);
      int h = static_cast<int>(screen_render_target_->physical_height()
                               * pixel_scale_fin);
      backing_render_target_ =
          NewFramebufferRenderTarget(w, h,
                                     true,   // linear interp
                                     true,   // depth
                                     true,   // tex
                                     false,  // depth tex
                                     false,  // highquality
                                     false,  // msaa,
                                     false   // alpha
          );                                 // NOLINT(whitespace/parens)
    }
  } else {
    // Otherwise we don't need backing buffer. Kill it if it exists.
    if (backing_render_target_.exists()) {
      backing_render_target_.Clear();
    }
  }
  pixel_scale_ = pixel_scale_requested_;
}

void Renderer::LoadMedia(FrameDef* frame_def) {
  millisecs_t t = g_core->AppTimeMillisecs();
  for (auto&& i : frame_def->media_components()) {
    Asset* mc = i.get();
    assert(mc);
    mc->Load();

    // Also mark them as used so they get kept around for a bit.
    mc->set_last_used_time(t);
  }
}

// #if BA_PLATFORM_MACOS && BA_SDL_BUILD && !BA_SDL2_BUILD
// void Renderer::HandleFunkyMacGammaIssue(FrameDef* frame_def) {
//   // FIXME - for some reason, on mac, gamma is getting switched back to
//   //  default about 1 second after a res change, etc...
//   //  so if we're using a non-1.0 gamma, lets keep setting it periodically
//   //  to force the issue
//   millisecs_t t = g_core->AppTimeMillisecs();
//   if (screen_gamma_requested_ != screen_gamma_
//       || (t - last_screen_gamma_update_time_ > 300 && screen_gamma_ != 1.0f))
//       {
//     screen_gamma_ = screen_gamma_requested_;
//     SDL_SetGamma(screen_gamma_, screen_gamma_, screen_gamma_);
//     last_screen_gamma_update_time_ = t;
//   }
// }
// #endif

void Renderer::DrawWorldToCameraBuffer(FrameDef* frame_def) {
#if BA_VARIANT_CARDBOARD
  // On cardboard theres a scissor setup enabled when we come in;
  // we need to turn that off while drawing to our other framebuffer since it
  // screws things up there.
  CardboardDisableScissor();
#endif

  PushGroupMarker("Camera Opaque Pass");
  SetDepthWriting(true);
  SetDepthTesting(true);
  RenderTarget* cam_target = has_camera_msaa_render_target()
                                 ? camera_msaa_render_target()
                                 : camera_render_target();
  cam_target->DrawBegin(frame_def->needs_clear());

  // Draw opaque stuff front-to-back.
  frame_def->beauty_pass()->Render(cam_target, false);
  frame_def->beauty_pass_bg()->Render(cam_target, false);
  PopGroupMarker();
  PushGroupMarker("Camera Transparent Pass");

  // Draw transparent stuff back-to-front.
  SetDepthWriting(false);
  frame_def->beauty_pass_bg()->Render(cam_target, true);
  frame_def->beauty_pass()->Render(cam_target, true);

  // If we drew into the MSAA version, blit it over to the texture version.
  if (has_camera_msaa_render_target()) {
    BlitBuffer(camera_msaa_render_target(), camera_render_target(),
               true,   // Depth.
               false,  // linear_interpolation
               false,  // force_shader_blit
               true    // invalidate_source
    );                 // NOLINT(whitespace/parens)
  }
  GenerateCameraBufferBlurPasses();
  PopGroupMarker();

#if BA_VARIANT_CARDBOARD
  CardboardEnableScissor();
#endif
}

void Renderer::UpdateDOFParams(FrameDef* frame_def) {
  RenderPass* beauty_pass = frame_def->beauty_pass();
  assert(beauty_pass);
  const std::vector<Vector3f>& areas_of_interest(
      beauty_pass->cam_area_of_interest_points());
  float min_z, max_z;
  if (!areas_of_interest.empty()) {
    // find min/max z for our areas of interest
    min_z = 9999.0f;
    max_z = -9999.0f;
    for (auto i : areas_of_interest) {
      float z = (beauty_pass->model_view_projection_matrix() * i).z;
      if (z > max_z) {
        max_z = z;
      }
      if (z < min_z) {
        min_z = z;
      }
    }
  } else {
    min_z = max_z = 0;
  }

  if ((frame_def->app_time_millisecs() - dof_update_time_ > 100)) {
    dof_update_time_ = frame_def->app_time_millisecs() - 100;
  }
  float smoothing = 0.995f;
  while (dof_update_time_ < frame_def->app_time_millisecs()) {
    dof_update_time_++;
    dof_near_smoothed_ =
        smoothing * dof_near_smoothed_ + (1.0f - smoothing) * min_z;
    dof_far_smoothed_ =
        smoothing * dof_far_smoothed_ + (1.0f - smoothing) * max_z;
  }
}

void Renderer::OnScreenSizeChange() {
  assert(g_base->app_adapter->InGraphicsContext());

  // We can actually get these events at times when we don't have a valid
  // gl context, so instead of doing any GL work here let's just make a note to
  // do so next time we render.
  screen_size_dirty_ = true;
}

void Renderer::Unload() {
  light_render_target_.Clear();
  light_shadow_render_target_.Clear();
  vr_overlay_flat_render_target_.Clear();
  screen_render_target_.Clear();
  backing_render_target_.Clear();
}

void Renderer::Load() {
  screen_render_target_ = Object::CompleteDeferred(NewScreenRenderTarget());

  // Restore current gamma value.
  //   if (screen_gamma_ != 1.0f) {
  // #if BA_SDL2_BUILD
  //     // Not supporting gamma in SDL2 currently.
  // #elif BA_SDL_BUILD
  //     SDL_SetGamma(screen_gamma_, screen_gamma_, screen_gamma_);
  // #endif
  //   }
}

void Renderer::PostLoad() {
  // This is called after all loading is done;
  // the renderer may choose to do any final setting up here.
}

void Renderer::SetLight(float pitch, float heading, float tz) {
  light_pitch_ = pitch;
  light_heading_ = heading;
  light_tz_ = tz;
}

#if BA_VR_BUILD
void Renderer::VRSetHead(float tx, float ty, float tz, float yaw, float pitch,
                         float roll) {
  vr_raw_head_tx_ = tx;
  vr_raw_head_ty_ = ty;
  vr_raw_head_tz_ = tz;
  vr_raw_head_yaw_ = yaw;
  vr_raw_head_pitch_ = pitch;
  vr_raw_head_roll_ = roll;
}
void Renderer::VRSetEye(int eye, float yaw, float pitch, float roll,
                        float tan_l, float tan_r, float tan_b, float tan_t,
                        float eye_x, float eye_y, float eye_z, int viewport_x,
                        int viewport_y) {
  // these are flipped for whatever reason... grumble grumble math grumble
  vr_fov_l_tan_ = tan_r;
  vr_fov_r_tan_ = tan_l;
  vr_fov_b_tan_ = tan_b;
  vr_fov_t_tan_ = tan_t;
  vr_eye_x_ = eye_x;
  vr_eye_y_ = eye_y;
  vr_eye_z_ = eye_z;
  vr_use_fov_tangents_ = true;
  vr_fov_degrees_x_ = vr_fov_degrees_y_ = 30.0f;
  vr_eye_ = eye;
  vr_eye_yaw_ = yaw;
  vr_eye_pitch_ = pitch;
  vr_eye_roll_ = roll;
  vr_viewport_x_ = viewport_x;
  vr_viewport_y_ = viewport_y;
}
#endif  // BA_VR_BUILD

auto Renderer::GetZBufferValue(RenderPass* pass, float dist) -> float {
  float z = std::min(1.0f, std::max(-1.0f, dist));
  // Remap from -1,1 to our depth-buffer-range.
  z = 0.5f * (z + 1.0f);
  z = kBackingDepth3 + z * (kBackingDepth4 - kBackingDepth3);
  return z;
}

auto Renderer::GetAutoAndroidRes() -> std::string {
  throw Exception("This should be overridden.");
}

}  // namespace ballistica::base
