// Released under the MIT License. See LICENSE for details.
#if BA_VR_BUILD

#include "ballistica/base/graphics/graphics_vr.h"

#include "ballistica/base/graphics/component/object_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/component/special_component.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/node/globals_node.h"

namespace ballistica::base {

static auto ValueTestFloat(float* storage, double* absval, double* deltaval)
    -> double {
  if (absval) {
    *storage = static_cast<float>(*absval);
  }
  if (deltaval) {
    *storage += static_cast<float>(*deltaval);
  }
  return *storage;
}

static auto ValueTestBool(bool* storage, double* absval, double* deltaval)
    -> double {
  if (absval) {
    *storage = static_cast<bool>(*absval);
  }
  if (deltaval) {
    *storage = (*deltaval > 0.5);
  }
  return static_cast<double>(*storage);
}

void GraphicsVR::DoDrawFade(FrameDef* frame_def, float amt) {
  SimpleComponent c(frame_def->vr_cover_pass());
  c.SetTransparent(false);
  Vector3f cam_pt = {0.0f, 0.0f, 0.0f};
  Vector3f cam_target_pt = {0.0f, 0.0f, 0.0f};
  cam_pt = Vector3f(frame_def->cam_original().x, frame_def->cam_original().y,
                    frame_def->cam_original().z);

  // In vr follow-mode the cam point gets tweaked.
  //
  // FIXME: should probably just do this on the camera end.
  if (frame_def->camera_mode() == CameraMode::kOrbit) {
    // fudge this one up a bit; looks better that way..
    cam_target_pt = Vector3f(frame_def->cam_target_original().x,
                             frame_def->cam_target_original().y + 6.0f,
                             frame_def->cam_target_original().z);
  } else {
    cam_target_pt = Vector3f(frame_def->cam_target_original().x,
                             frame_def->cam_target_original().y,
                             frame_def->cam_target_original().z);
  }
  Vector3f diff = cam_target_pt - cam_pt;
  diff.Normalize();
  Vector3f side = Vector3f::Cross(diff, Vector3f(0.0f, 1.0f, 0.0f));
  Vector3f up = Vector3f::Cross(diff, side);
  c.SetColor(0, 0, 0);
  {
    auto xf = c.ScopedTransform();
    // We start in vr-overlay screen space; get back to world.
    c.Translate(cam_pt.x, cam_pt.y, cam_pt.z);
    c.MultMatrix(Matrix44fOrient(diff, up).m);
    // At the very end we stay turned around so we get 100% black.
    if (amt < 0.98f) {
      c.Translate(0, 0, 40.0f * amt);
      c.Rotate(180, 1, 0, 0);
    }
    float inv_a = 1.0f - amt;
    float s = 100.0f * inv_a + 5.0f * amt;
    c.Scale(s, s, s);
    c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kVRFade));
  }
  c.Submit();
}

auto GraphicsVR::ValueTest(const std::string& arg, double* absval,
                           double* deltaval, double* outval) -> bool {
  if (arg == "vrOverlayScale") {
    *outval = ValueTestFloat(&vr_overlay_scale_, absval, deltaval);
  } else if (arg == "lockVROverlay") {
    *outval = ValueTestBool(&lock_vr_overlay_, absval, deltaval);
  } else if (arg == "showOverlayBounds") {
    *outval = ValueTestBool(&draw_overlay_bounds_, absval, deltaval);
  } else if (arg == "headScale") {
    *outval = ValueTestFloat(&vr_test_head_scale_, absval, deltaval);
  } else if (arg == "vrCamOffsetY") {
    Camera* camera = g_base->graphics->camera();
    if (camera) {
      Vector3f val = camera->vr_extra_offset();
      if (deltaval) {
        camera->set_vr_extra_offset(Vector3f(val.x, val.y + *deltaval, val.z));
      }
      if (absval) {
        camera->set_vr_extra_offset(Vector3f(val.x, *absval, val.z));
      }
      *outval = camera->vr_extra_offset().y;
    }
  } else if (arg == "vrCamOffsetZ") {
    Camera* camera = g_base->graphics->camera();
    if (camera) {
      Vector3f val = camera->vr_extra_offset();
      if (deltaval) {
        camera->set_vr_extra_offset(Vector3f(val.x, val.y, val.z + *deltaval));
      }
      if (absval) {
        camera->set_vr_extra_offset(Vector3f(val.x, val.y, *absval));
      }
      *outval = camera->vr_extra_offset().z;
    }
  } else {
    // Unhandled.
    return false;
  }
  return true;
}

void GraphicsVR::ApplyCamera(FrameDef* frame_def) {
  Graphics::ApplyCamera(frame_def);

  CalcVROverlayMatrices(frame_def);
}

void GraphicsVR::DrawWorld(FrameDef* frame_def) {
  // Draw the standard world.
  Graphics::DrawWorld(frame_def);

  // Draw extra VR-Only bits.
  DrawVRControllers(frame_def);
}

void GraphicsVR::DrawUI(FrameDef* frame_def) {
  // Draw the UI normally, but then blit its texture into 3d space.
  Graphics::DrawUI(frame_def);

  // In VR mode we have to draw our overlay-flat texture into space as
  // part of the regular overlay pass.
  DrawVROverlay(frame_def);

  // We may want to see the bounds of our overlay.
  DrawOverlayBounds(frame_def->overlay_pass());
}

void GraphicsVR::CalcVROverlayMatrices(FrameDef* frame_def) {
  // For VR mode, calc our overlay matrix for use in positioning overlay
  // elements.
  if (g_core->vr_mode()) {
    Vector3f cam_target_pt(frame_def->cam_target_original());
    Matrix44f vr_overlay_matrix{kMatrix44fIdentity};
    Matrix44f vr_overlay_matrix_fixed{kMatrix44fIdentity};

    // In orbit mode, we sit in the middle and face the camera.
    if (frame_def->camera_mode() == CameraMode::kOrbit) {
      Vector3f cam_pt(frame_def->cam_original());
      Vector3f cam_target_pt_2(0, 11, -3.3f);
      vr_overlay_matrix_fixed = vr_overlay_matrix =
          CalcVROverlayMatrix(cam_pt, cam_target_pt_2);

    } else {
      // Follow mode.

      // In vr follow-mode the cam point gets tweaked.
      // FIXME: Should probably just do this on the camera end.
      Vector3f cam_pt = frame_def->cam_original();

      // During gameplay lets just affix X to our camera (the camera tries to
      // match the target's x anyway).. this results in less shuffling.
      if (frame_def->camera_mode() == CameraMode::kFollow) {
        cam_target_pt.x = cam_pt.x;
      }

      // Calc y and z values that are completely fixed to the camera center.
      float fixed_y = cam_pt.y + kVRFixedOverlayOffsetY;
      float fixed_z = cam_pt.z + kVRFixedOverlayOffsetZ;

      // We smoothly blend our target point between the map-specific
      // center-point and our fixed point (between levels we want our two
      // overlays to line up since there may be elements coordinated across
      // them).

      // FIXME: This shouldn't be based on frames.
      {
        float this_y, this_z;
        if (vr_overlay_center_enabled_) {
          this_y = vr_overlay_center_.y;
          this_z = vr_overlay_center_.z;
        } else {
          this_y = fixed_y;
          this_z = fixed_z;
        }
        float smoothing = 0.93f;
        float smoothing_inv = 1.0f - smoothing;

        vr_cam_target_pt_smoothed_y_ =
            smoothing * vr_cam_target_pt_smoothed_y_ + smoothing_inv * this_y;
        vr_cam_target_pt_smoothed_z_ =
            smoothing * vr_cam_target_pt_smoothed_z_ + smoothing_inv * this_z;

        cam_target_pt.y = vr_cam_target_pt_smoothed_y_;
        cam_target_pt.z = vr_cam_target_pt_smoothed_z_;
      }

      vr_overlay_matrix = CalcVROverlayMatrix(cam_pt, cam_target_pt);

      // We also always calc a completely fixed matrix for some elements
      // that should *never* move such as score-screens.
      cam_target_pt.y = fixed_y;
      cam_target_pt.z = fixed_z;
      vr_overlay_matrix_fixed = CalcVROverlayMatrix(cam_pt, cam_target_pt);
    }

    // Calc a screen-matrix that gives us a drawing area of kBaseVirtualResX
    // by kBaseVirtualResY.
    frame_def->set_vr_overlay_screen_matrix(
        Matrix44fTranslate(-0.5f * kBaseVirtualResX, -0.5f * kBaseVirtualResY,
                           0.0f)
        * Matrix44fScale(
            Vector3f(1.0f / (kBaseVirtualResX * (1.0f + kVRBorder)),
                     1.0f / (kBaseVirtualResY * (1.0f + kVRBorder)),
                     1.0f / (kBaseVirtualResX * (1.0f + kVRBorder))))
        * vr_overlay_matrix);

    // If we have a fixed-version of the matrix, do the same calcs for it;
    // otherwise just copy the non-fixed.
    frame_def->set_vr_overlay_screen_matrix_fixed(
        Matrix44fTranslate(-0.5f * kBaseVirtualResX, -0.5f * kBaseVirtualResY,
                           0.0f)
        * Matrix44fScale(
            Vector3f(1.0f / (kBaseVirtualResX * (1.0f + kVRBorder)),
                     1.0f / (kBaseVirtualResY * (1.0f + kVRBorder)),
                     1.0f / (kBaseVirtualResX * (1.0f + kVRBorder))))
        * vr_overlay_matrix_fixed);

    if (lock_vr_overlay_) {
      frame_def->set_vr_overlay_screen_matrix(
          frame_def->vr_overlay_screen_matrix_fixed());
    }
  }
}

auto GraphicsVR::CalcVROverlayMatrix(const Vector3f& cam_pt,
                                     const Vector3f& cam_target_pt) const
    -> Matrix44f {
  Matrix44f m = Matrix44fTranslate(cam_target_pt);
  Vector3f diff = cam_pt - cam_target_pt;
  diff.Normalize();
  Vector3f side = Vector3f::Cross(diff, Vector3f(0.0f, -1.0f, 0.0f));
  Vector3f up = Vector3f::Cross(diff, side);
  m = Matrix44fOrient(diff, up) * m;

  // Push up and out towards the eye a bit.
  m = Matrix44fTranslate(0, 2, 1) * m;

  // Scale based on distance to the camera so we're always roughly the same size
  // in view.
  float dist = (cam_target_pt - cam_pt).Length();
  float base_scale = dist * 1.08f * 1.1f * vr_overlay_scale_;
  return Matrix44fScale(Vector3f(base_scale,
                                 base_scale
                                     * (static_cast<float>(kBaseVirtualResY)
                                        / static_cast<float>(kBaseVirtualResX)),
                                 base_scale))
         * m;
}

void GraphicsVR::DrawVROverlay(FrameDef* frame_def) {
  // In vr mode we have draw our overlay-flat texture in to space
  // as part of our regular overlay pass.
  //
  // NOTE: this assumes nothing after this point gets drawn into
  // the overlay-flat pass (otherwise it may get skipped).
  // This should be a safe assumption since this is pretty much just for
  // widgets.
  if (g_core->vr_mode() && frame_def->overlay_flat_pass()->HasDrawCommands()) {
    // Draw our overlay-flat stuff into our overlay pass.
    SpecialComponent c(frame_def->overlay_pass(),
                       SpecialComponent::Source::kVROverlayBuffer);
    {
      auto xf = c.ScopedTransform();
      c.Translate(0.5f * kBaseVirtualResX, 0.5f * kBaseVirtualResY, 0.0f);
      c.Scale(kBaseVirtualResX * (1.0f + kVRBorder),
              kBaseVirtualResY * (1.0f + kVRBorder),
              kBaseVirtualResX * (1.0f + kVRBorder));
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kVROverlay));
    }
    c.Submit();
  }
}

void GraphicsVR::DrawOverlayBounds(RenderPass* pass) {
  // We can optionally draw a guide to show the edges of the overlay pass
  if (draw_overlay_bounds_) {
    SimpleComponent c(pass);
    c.SetColor(1, 0, 0);
    {
      auto xf = c.ScopedTransform();
      float width = screen_virtual_width();
      float height = screen_virtual_height();

      // Slight offset in z to reduce z fighting.
      c.Translate(0.5f * width, 0.5f * height, 1.0f);
      c.Scale(width, height, 100.0f);
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kOverlayGuide));
    }
    c.Submit();
  }
}

void GraphicsVR::DrawVRControllers(FrameDef* frame_def) {
  if (!g_core->vr_mode()) {
    return;
  }

  // Disabling this for now.
  return;

  // DEBUG - draw boxing glove just in front of our head transform to verify
  // it's in the right place
  if (false) {
    ObjectComponent c(frame_def->beauty_pass());
    c.SetColor(1, 0, 0);
    c.SetTexture(g_base->assets->SysTexture(SysTextureID::kBoxingGlove));
    c.SetReflection(ReflectionType::kSoft);
    c.SetReflectionScale(0.4f, 0.4f, 0.4f);
    {
      auto xf = c.ScopedTransform();
      c.VRTransformToHead();
      c.Translate(0, 0, 5);
      c.Scale(2, 2, 2);
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBoxingGlove));
    }
    c.Submit();
  }

  // test right hand
  const VRHandsState& s(vr_hands_state());

  switch (s.r.type) {
    case VRHandType::kOculusTouchR:
    case VRHandType::kDaydreamRemote: {
      ObjectComponent c(frame_def->beauty_pass());
      c.SetColor(0, 1, 0);
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kBoxingGlove));
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.4f, 0.4f, 0.4f);
      {
        auto xf = c.ScopedTransform();
        c.VRTransformToRightHand();
        c.Scale(10, 10, 10);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBoxingGlove));
      }
      c.Submit();
      break;
    }
    default:
      break;
  }

  switch (s.l.type) {
    case VRHandType::kOculusTouchL: {
      ObjectComponent c(frame_def->beauty_pass());
      c.SetColor(0, 0, 1);
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kBoxingGlove));
      c.SetReflection(ReflectionType::kSoft);
      c.SetReflectionScale(0.4f, 0.4f, 0.4f);
      {
        auto xf = c.ScopedTransform();
        c.VRTransformToLeftHand();
        c.Scale(10, 10, 10);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBoxingGlove));
      }
      c.Submit();
      break;
    }
    default:
      break;
  }
}

}  // namespace ballistica::base

#endif  // BA_VR_BUILD
