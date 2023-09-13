// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GRAPHICS_VR_H_
#define BALLISTICA_BASE_GRAPHICS_GRAPHICS_VR_H_

#include <string>

#include "ballistica/base/graphics/graphics.h"

namespace ballistica::base {

const float kDefaultVRHeadScale = 18.0f;
const float kVRFixedOverlayOffsetY = -7.0f;
const float kVRFixedOverlayOffsetZ = -22.0f;

#if BA_VR_BUILD

class GraphicsVR : public Graphics {
 public:
  /// Return g_graphics as a GraphicsVR. (assumes it actually is one).
  static GraphicsVR* get() {
    assert(g_base && g_base->graphics != nullptr);
    assert(dynamic_cast<GraphicsVR*>(g_base->graphics)
           == static_cast<GraphicsVR*>(g_base->graphics));
    return static_cast<GraphicsVR*>(g_base->graphics);
  }
  void ApplyCamera(FrameDef* frame_def) override;

  void DrawWorld(FrameDef* frame_def) override;
  void DrawUI(FrameDef* frame_def) override;

  auto vr_head_forward() const -> const Vector3f& { return vr_head_forward_; }
  auto vr_head_up() const -> const Vector3f& { return vr_head_up_; }
  auto vr_head_translate() const -> const Vector3f& {
    return vr_head_translate_;
  }
  void set_vr_head_forward(const Vector3f& v) { vr_head_forward_ = v; }
  void set_vr_head_up(const Vector3f& v) { vr_head_up_ = v; }
  void set_vr_head_translate(const Vector3f& v) { vr_head_translate_ = v; }
  void set_vr_overlay_center(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vr_overlay_center_ = val;
  }
  auto vr_overlay_center() const -> const Vector3f& {
    return vr_overlay_center_;
  }
  void set_vr_overlay_center_enabled(bool val) {
    assert(g_base->InLogicThread());
    vr_overlay_center_enabled_ = val;
  }
  auto vr_overlay_center_enabled() const -> bool {
    return vr_overlay_center_enabled_;
  }
  auto vr_near_clip() const -> float { return vr_near_clip_; }
  void set_vr_near_clip(float val) { vr_near_clip_ = val; }
  auto ValueTest(const std::string& arg, double* absval, double* deltaval,
                 double* outval) -> bool override;

  float vr_test_head_scale() const { return vr_test_head_scale_; }

  auto vr_hands_state() const -> VRHandsState { return vr_hands_state_; }
  void set_vr_hands_state(const VRHandsState& state) {
    vr_hands_state_ = state;
  }

 protected:
  void DoDrawFade(FrameDef* frame_def, float amt) override;

 private:
  void CalcVROverlayMatrices(FrameDef* frame_def);
  auto CalcVROverlayMatrix(const Vector3f& cam_pt,
                           const Vector3f& cam_target_pt) const -> Matrix44f;
  void DrawVROverlay(FrameDef* frame_def);
  void DrawOverlayBounds(RenderPass* pass);
  void DrawVRControllers(FrameDef* frame_def);

  float vr_overlay_scale_{1.0f};
  float vr_near_clip_{4.0f};
  float vr_cam_target_pt_smoothed_y_{};
  float vr_cam_target_pt_smoothed_z_{};
  Vector3f vr_head_forward_{0.0f, 0.0f, -1.0f};
  Vector3f vr_head_up_{0.0f, 1.0f, 0.0f};
  Vector3f vr_head_translate_{0.0f, 0.0f, 0.0f};
  Vector3f vr_overlay_center_{0.0f, 0.0f, 0.0f};
  bool vr_overlay_center_enabled_{};
  bool lock_vr_overlay_{};
  bool draw_overlay_bounds_{};
  float vr_test_head_scale_{kDefaultVRHeadScale};
  VRHandsState vr_hands_state_;
};
#endif  // BA_VR_BUILD

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_GRAPHICS_VR_H_
