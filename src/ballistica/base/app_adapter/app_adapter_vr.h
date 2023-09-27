// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_VR_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_VR_H_

#if BA_VR_BUILD

#include "ballistica/base/app_adapter/app_adapter.h"

namespace ballistica::base {

class AppAdapterVR : public AppAdapter {
 public:
  /// For passing in state of Daydream remote (and maybe gear vr?..).
  struct VRSimpleRemoteState {
    bool right_handed = true;
    float r0 = 0.0f;
    float r1 = 0.0f;
    float r2 = 0.0f;
  };

  auto ManagesMainThreadEventLoop() const -> bool override;

  /// Return g_app as a AppAdapterVR. (assumes it actually is one).
  static auto Get() -> AppAdapterVR* {
    assert(g_base != nullptr && g_base->app_adapter != nullptr);
    assert(dynamic_cast<AppAdapterVR*>(g_base->app_adapter)
           == static_cast<AppAdapterVR*>(g_base->app_adapter));
    return static_cast<AppAdapterVR*>(g_base->app_adapter);
  }

  AppAdapterVR();
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

 protected:
  void DoPushMainThreadRunnable(Runnable* runnable) override;
  void RunMainThreadEventLoopToCompletion() override;
  void DoExitMainThreadEventLoop() override;

 private:
  FrameDef* vr_render_frame_def_{};
};

}  // namespace ballistica::base

#endif  // BA_VR_BUILD
#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_VR_H_
