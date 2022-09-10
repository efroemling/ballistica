// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_APP_FLAVOR_VR_H_
#define BALLISTICA_APP_APP_FLAVOR_VR_H_

#if BA_VR_BUILD

#include "ballistica/app/app_flavor.h"

namespace ballistica {

class AppFlavorVR : public AppFlavor {
 public:
  /// For passing in state of Daydream remote (and maybe gear vr?..).
  struct VRSimpleRemoteState {
    bool right_handed = true;
    float r0 = 0.0f;
    float r1 = 0.0f;
    float r2 = 0.0f;
  };

  /// Return g_app_flavor as a AppFlavorVR. (assumes it actually is one).
  static auto get() -> AppFlavorVR* {
    assert(g_app_flavor != nullptr);
    assert(dynamic_cast<AppFlavorVR*>(g_app_flavor)
           == static_cast<AppFlavorVR*>(g_app_flavor));
    return static_cast<AppFlavorVR*>(g_app_flavor);
  }

  explicit AppFlavorVR(Thread* thread);
  auto PushVRSimpleRemoteStateCall(const VRSimpleRemoteState& state) -> void;
  auto VRSetDrawDimensions(int w, int h) -> void;
  auto VRPreDraw() -> void;
  auto VRPostDraw() -> void;
  auto VRSetHead(float tx, float ty, float tz, float yaw, float pitch,
                 float roll) -> void;
  auto VRSetHands(const VRHandsState& state) -> void;
  auto VRDrawEye(int eye, float yaw, float pitch, float roll, float tan_l,
                 float tan_r, float tan_b, float tan_t, float eye_x,
                 float eye_y, float eye_z, int viewport_x, int viewport_y)
      -> void;

 private:
  FrameDef* vr_render_frame_def_{};
};

}  // namespace ballistica

#endif  // BA_VR_BUILD
#endif  // BALLISTICA_APP_APP_FLAVOR_VR_H_
