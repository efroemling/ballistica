// Released under the MIT License. See LICENSE for details.
#if BA_VR_BUILD

#include "ballistica/base/app_adapter/app_adapter_vr.h"

#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/graphics_vr.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

AppAdapterVR::AppAdapterVR() {}

auto AppAdapterVR::ManagesMainThreadEventLoop() const -> bool { return false; }

void AppAdapterVR::PushVRSimpleRemoteStateCall(
    const VRSimpleRemoteState& state) {
  g_base->app_adapter->PushGraphicsContextCall([this, state] {
    // Convert this to a full hands state, adding in some simple elbow
    // positioning of our own and left/right.
    VRHandsState s;
    s.l.tx = -0.2f;
    s.l.ty = -0.2f;
    s.l.tz = -0.3f;

    // Hmm; for now lets always assign this as right hand even when its in
    // left-handed mode to keep things simple on the back-end. Can change
    // later if there's a downside to that.
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

void AppAdapterVR::VRSetDrawDimensions(int w, int h) {
  FatalError("FIXME UPDATE SET-SCREEN-RESOLUTION");
  // g_base->graphics_server->SetScreenResolution(w, h);
}

void AppAdapterVR::VRPreDraw() {
  if (!g_base || !g_base->graphics_server
      || !g_base->graphics_server->renderer()) {
    return;
  }
  assert(g_base->app_adapter->InGraphicsContext());
  // FIXME - this is internal graphics-server details that the render-server
  // should handle.
  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kWarning,
                       "FIXME: Have GraphicsServer handle VR drawing.");
  // if (FrameDef* frame_def = g_base->graphics_server->GetRenderFrameDef()) {
  //   // Note: this could be part of PreprocessRenderFrameDef but the non-vr
  //   // path needs it to be separate since preprocess doesn't happen
  //   // sometimes. Should probably clean that up.
  //   g_base->graphics_server->RunFrameDefMeshUpdates(frame_def);

  //   // store this for the duration of this frame
  //   vr_render_frame_def_ = frame_def;
  //   g_base->graphics_server->PreprocessRenderFrameDef(frame_def);
  // }
}

void AppAdapterVR::VRPostDraw() {
  assert(g_base->app_adapter->InGraphicsContext());
  if (!g_base || !g_base->graphics_server
      || !g_base->graphics_server->renderer()) {
    return;
  }
  if (vr_render_frame_def_) {
    g_base->graphics_server->FinishRenderFrameDef(vr_render_frame_def_);
    vr_render_frame_def_ = nullptr;
  }
  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kWarning,
                       "WOULD RUN RENDER UPKEEP CYCLE");
  // RunRenderUpkeepCycle();
}

void AppAdapterVR::VRSetHead(float tx, float ty, float tz, float yaw,
                             float pitch, float roll) {
  assert(g_base->app_adapter->InGraphicsContext());
  Renderer* renderer = g_base->graphics_server->renderer();
  if (renderer == nullptr) return;
  renderer->VRSetHead(tx, ty, tz, yaw, pitch, roll);
}

void AppAdapterVR::VRSetHands(const VRHandsState& state) {
  assert(g_base->app_adapter->InGraphicsContext());

  // Pass this along to the renderer (in this same thread) for drawing (so
  // hands can be drawn at their absolute most up-to-date positions, etc).
  Renderer* renderer = g_base->graphics_server->renderer();
  if (renderer == nullptr) {
    return;
  }
  renderer->VRSetHands(state);

  // ALSO ship it off to the logic thread to actually handle input from it.
  //
  // FIXME: This should get shipped to a logic or input variant once we have
  // that for vr; not the graphics variant. Shipping it to the renderer
  // above covers graphics needs in a lower latency way.
  g_base->logic->event_loop()->PushCall(
      [state] { GraphicsVR::get()->set_vr_hands_state(state); });
}

void AppAdapterVR::VRDrawEye(int eye, float yaw, float pitch, float roll,
                             float tan_l, float tan_r, float tan_b, float tan_t,
                             float eye_x, float eye_y, float eye_z,
                             int viewport_x, int viewport_y) {
  if (!g_base || !g_base->graphics_server
      || !g_base->graphics_server->renderer()) {
    return;
  }
  assert(g_base->app_adapter->InGraphicsContext());
  if (vr_render_frame_def_) {
    // Set up VR eye stuff.
    Renderer* renderer = g_base->graphics_server->renderer();
    renderer->VRSetEye(eye, yaw, pitch, roll, tan_l, tan_r, tan_b, tan_t, eye_x,
                       eye_y, eye_z, viewport_x, viewport_y);
    g_base->graphics_server->DrawRenderFrameDef(vr_render_frame_def_);
  }
}

void AppAdapterVR::RunMainThreadEventLoopToCompletion() {
  // FIXME - can basically copy sdl path here methinks.
  FatalError(
      "FIXME: IMPLEMENT AppAdapterVR::RunMainThreadEventLoopToCompletion");
  // g_core->main_event_loop()->RunToCompletion();
}

void AppAdapterVR::DoPushMainThreadRunnable(Runnable* runnable) {
  FatalError("FIXME: DoPushMainThreadRunnable unimplemented here.");
}

void AppAdapterVR::DoExitMainThreadEventLoop() {
  FatalError("FIXME: IMPLEMENT AppAdapterVR::DoExitMainThreadEventLoop");
  // g_core->main_event_loop()->Exit();
}

}  // namespace ballistica::base

#endif  // BA_VR_BUILD
