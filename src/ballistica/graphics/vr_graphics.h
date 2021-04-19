// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_VR_GRAPHICS_H_
#define BALLISTICA_GRAPHICS_VR_GRAPHICS_H_

#include <string>

#include "ballistica/graphics/graphics.h"

namespace ballistica {

const float kDefaultVRHeadScale = 18.0f;
const float kVRFixedOverlayOffsetY = -7.0f;
const float kVRFixedOverlayOffsetZ = -22.0f;

#if BA_VR_BUILD

class VRGraphics : public Graphics {
 public:
  /// Return g_graphics as a VRGraphics. (assumes it actually is one).
  static VRGraphics* get() {
    assert(g_graphics != nullptr);
    assert(dynamic_cast<VRGraphics*>(g_graphics)
           == static_cast<VRGraphics*>(g_graphics));
    return static_cast<VRGraphics*>(g_graphics);
  }
  auto ApplyCamera(FrameDef* frame_def) -> void override;
  auto ApplyGlobals(GlobalsNode* globals) -> void override;

  void DrawWorld(Session* session, FrameDef* frame_def) override;
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
    assert(InGameThread());
    vr_overlay_center_ = val;
  }
  auto vr_overlay_center() const -> const Vector3f& {
    return vr_overlay_center_;
  }
  void set_vr_overlay_center_enabled(bool val) {
    assert(InGameThread());
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
};
#endif  // BA_VR_BUILD

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_VR_GRAPHICS_H_
