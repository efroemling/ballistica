// Released under the MIT License. See LICENSE for details.
#if BA_VR_BUILD

#include "ballistica/app/app_flavor_vr.h"

#include "ballistica/core/thread.h"
#include "ballistica/game/game.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/renderer.h"

namespace ballistica {

AppFlavorVR::AppFlavorVR(Thread* thread) : AppFlavor(thread) {}

auto AppFlavorVR::PushVRSimpleRemoteStateCall(const VRSimpleRemoteState& state)
    -> void {
  thread()->PushCall([this, state] {
    // Convert this to a full hands state, adding in some simple elbow
    // positioning of our own and left/right.
    VRHandsState s;
    s.l.tx = -0.2f;
    s.l.ty = -0.2f;
    s.l.tz = -0.3f;

    // Hmm; for now lets always assign this as right hand even when its in
    // left-handed mode to keep things simple on the back-end.  Can change later
    // if there's a downside to that.
    s.r.type = VRHandType::kDaydreamRemote;
    s.r.tx = 0.2f;
    s.r.ty = -0.2f;
    s.r.tz = -0.3f;
    s.r.yaw = state.r0;
    s.r.pitch = state.r1;
    s.r.roll = state.r2;
    VRSetHands(s);
  });
}

auto AppFlavorVR::VRSetDrawDimensions(int w, int h) -> void {
  g_graphics_server->VideoResize(w, h);
}

void AppFlavorVR::VRPreDraw() {
  if (!g_graphics_server || !g_graphics_server->renderer()) {
    return;
  }
  assert(InMainThread());
  if (FrameDef* frame_def = g_graphics_server->GetRenderFrameDef()) {
    // Note: this could be part of PreprocessRenderFrameDef but
    // the non-vr path needs it to be separate since preprocess doesn't
    // happen sometimes. Should probably clean that up.
    g_graphics_server->RunFrameDefMeshUpdates(frame_def);

    // store this for the duration of this frame
    vr_render_frame_def_ = frame_def;
    g_graphics_server->PreprocessRenderFrameDef(frame_def);
  }
}

auto AppFlavorVR::VRPostDraw() -> void {
  assert(InMainThread());
  if (!g_graphics_server || !g_graphics_server->renderer()) {
    return;
  }
  if (vr_render_frame_def_) {
    g_graphics_server->FinishRenderFrameDef(vr_render_frame_def_);
    vr_render_frame_def_ = nullptr;
  }
  RunRenderUpkeepCycle();
}

auto AppFlavorVR::VRSetHead(float tx, float ty, float tz, float yaw,
                            float pitch, float roll) -> void {
  assert(InMainThread());
  Renderer* renderer = g_graphics_server->renderer();
  if (renderer == nullptr) return;
  renderer->VRSetHead(tx, ty, tz, yaw, pitch, roll);
}

auto AppFlavorVR::VRSetHands(const VRHandsState& state) -> void {
  assert(InMainThread());

  // Pass this along to the renderer (in this same thread) for drawing
  // (so hands can be drawn at their absolute most up-to-date positions, etc).
  Renderer* renderer = g_graphics_server->renderer();
  if (renderer == nullptr) return;
  renderer->VRSetHands(state);

  // ALSO ship it off to the game/ui thread to actually handle input from it.
  g_game->PushVRHandsState(state);
}

auto AppFlavorVR::VRDrawEye(int eye, float yaw, float pitch, float roll,
                            float tan_l, float tan_r, float tan_b, float tan_t,
                            float eye_x, float eye_y, float eye_z,
                            int viewport_x, int viewport_y) -> void {
  if (!g_graphics_server || !g_graphics_server->renderer()) {
    return;
  }
  assert(InMainThread());
  if (vr_render_frame_def_) {
    // set up VR eye stuff...
    Renderer* renderer = g_graphics_server->renderer();
    renderer->VRSetEye(eye, yaw, pitch, roll, tan_l, tan_r, tan_b, tan_t, eye_x,
                       eye_y, eye_z, viewport_x, viewport_y);
    g_graphics_server->DrawRenderFrameDef(vr_render_frame_def_);
  }
}

}  // namespace ballistica

#endif  // BA_VR_BUILD
