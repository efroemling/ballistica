// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_VR_H_
#define BALLISTICA_BASE_APP_APP_VR_H_

#if BA_VR_BUILD

#include "ballistica/base/app/app.h"

namespace ballistica::base {

class AppVR : public App {
 public:
  /// For passing in state of Daydream remote (and maybe gear vr?..).
  struct VRSimpleRemoteState {
    bool right_handed = true;
    float r0 = 0.0f;
    float r1 = 0.0f;
    float r2 = 0.0f;
  };

  /// Return g_app as a AppVR. (assumes it actually is one).
  static auto get() -> AppVR* {
    assert(g_base != nullptr && g_base->app != nullptr);
    assert(dynamic_cast<AppVR*>(g_base->app)
           == static_cast<AppVR*>(g_base->app));
    return static_cast<AppVR*>(g_base->app);
  }

  AppVR();
  void PushVRSimpleRemoteStateCall(const VRSimpleRemoteState& state);
  void VRSetDrawDimensions(int w, int h);
  void VRPreDraw();
  void VRPostDraw();
  void VRSetHead(float tx, float ty, float tz, float yaw, float pitch,
                 float roll);
  void VRSetHands(const VRHandsState& state);
  void VRDrawEye(int eye, float yaw, float pitch, float roll, float tan_l,
                 float tan_r, float tan_b, float tan_t, float eye_x,
                 float eye_y, float eye_z, int viewport_x, int viewport_y);

 private:
  FrameDef* vr_render_frame_def_{};
};

}  // namespace ballistica::base

#endif  // BA_VR_BUILD
#endif  // BALLISTICA_BASE_APP_APP_VR_H_
