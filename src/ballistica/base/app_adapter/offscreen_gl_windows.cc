// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/app_adapter/offscreen_gl_windows.h"

#if BA_PLATFORM_WINDOWS && BA_OPENGL_IS_ES && BA_ENABLE_OPENGL

#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <EGL/eglext_angle.h>
#include <GLES3/gl3.h>

#include <algorithm>
#include <cstdio>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/ballistica.h"

// Normally SDL owns EGL and we don't link it (see gl_sys_windows.cc); this
// path makes its own context, so it needs the EGL entry points directly.
// libEGL.dll ships beside the exe either way.
#pragma comment(lib, "libEGL.lib")

namespace ballistica::base {

static auto OffscreenGLEnv_() -> std::string {
  auto val = g_core->platform->GetEnv("BA_OFFSCREEN_GL");
  return val ? *val : std::string();
}

auto OffscreenGLWindows::Requested() -> bool {
  auto val = OffscreenGLEnv_();
  return !val.empty() && val != "0";
}

void OffscreenGLWindows::Fail_(const std::string& what) {
  char buf[32];
  snprintf(buf, sizeof(buf), "0x%04X", static_cast<unsigned>(eglGetError()));
  FatalError("Offscreen GL (BA_OFFSCREEN_GL): " + what + " failed (EGL error "
             + buf + ").");
}

void OffscreenGLWindows::Create(int width, int height) {
  bool warp = OffscreenGLEnv_() == "warp";

  // Forcing WARP means pinning D3D11. Otherwise we take ANGLE's default
  // backend (D3D11 on Windows), which also honors ANGLE_DEFAULT_PLATFORM
  // (test_game_run --angle-backend) like the windowed path does.
  EGLAttrib warp_attrs[] = {
      EGL_PLATFORM_ANGLE_TYPE_ANGLE, EGL_PLATFORM_ANGLE_TYPE_D3D11_ANGLE,
      EGL_PLATFORM_ANGLE_DEVICE_TYPE_ANGLE,
      EGL_PLATFORM_ANGLE_DEVICE_TYPE_D3D_WARP_ANGLE, EGL_NONE};
  EGLAttrib default_attrs[] = {EGL_NONE};
  auto display = eglGetPlatformDisplay(
      EGL_PLATFORM_ANGLE_ANGLE, reinterpret_cast<void*>(EGL_DEFAULT_DISPLAY),
      warp ? warp_attrs : default_attrs);
  if (display == EGL_NO_DISPLAY) {
    Fail_("eglGetPlatformDisplay");
  }
  EGLint major{}, minor{};
  if (!eglInitialize(display, &major, &minor)) {
    Fail_("eglInitialize");
  }
  display_ = display;

  EGLint config_attrs[] = {EGL_SURFACE_TYPE,
                           EGL_PBUFFER_BIT,
                           EGL_RENDERABLE_TYPE,
                           EGL_OPENGL_ES3_BIT,
                           EGL_RED_SIZE,
                           8,
                           EGL_GREEN_SIZE,
                           8,
                           EGL_BLUE_SIZE,
                           8,
                           EGL_ALPHA_SIZE,
                           8,
                           EGL_DEPTH_SIZE,
                           24,
                           EGL_STENCIL_SIZE,
                           8,
                           EGL_NONE};
  EGLConfig config{};
  EGLint num_configs{};
  if (!eglChooseConfig(display, config_attrs, &config, 1, &num_configs)
      || num_configs < 1) {
    Fail_("eglChooseConfig");
  }
  config_ = config;

  if (!eglBindAPI(EGL_OPENGL_ES_API)) {
    Fail_("eglBindAPI");
  }
  EGLint context_attrs[] = {EGL_CONTEXT_MAJOR_VERSION, 3,
                            EGL_CONTEXT_MINOR_VERSION, 0, EGL_NONE};
  auto context =
      eglCreateContext(display, config, EGL_NO_CONTEXT, context_attrs);
  if (context == EGL_NO_CONTEXT) {
    Fail_("eglCreateContext");
  }
  context_ = context;

  CreateSurface_(width, height);

  // Frames are never presented, so nothing should wait on vsync.
  eglSwapInterval(display, 0);

  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kInfo, [=] {
    return "Offscreen GL: rendering to a " + std::to_string(width) + "x"
           + std::to_string(height) + " ANGLE pbuffer (EGL "
           + std::to_string(major) + "." + std::to_string(minor) + ", "
           + (warp ? "D3D11 WARP forced" : "default backend/adapter") + ").";
  });
}

void OffscreenGLWindows::CreateSurface_(int width, int height) {
  width = std::max(1, width);
  height = std::max(1, height);
  EGLint surface_attrs[] = {EGL_WIDTH, width, EGL_HEIGHT, height, EGL_NONE};
  auto surface = eglCreatePbufferSurface(display_, config_, surface_attrs);
  if (surface == EGL_NO_SURFACE) {
    Fail_("eglCreatePbufferSurface");
  }
  if (!eglMakeCurrent(display_, surface, surface, context_)) {
    Fail_("eglMakeCurrent");
  }
  surface_ = surface;
  width_ = width;
  height_ = height;
}

void OffscreenGLWindows::Resize(int width, int height) {
  if (width == width_ && height == height_) {
    return;
  }
  auto old_surface = surface_;
  CreateSurface_(width, height);
  eglDestroySurface(display_, old_surface);
}

void OffscreenGLWindows::Swap() {
  eglSwapBuffers(display_, surface_);

  // A window swap chain stops the CPU from queueing more than a few frames
  // ahead of the GPU; a pbuffer has no such limit. Without one the CPU
  // submits hundreds of frames a second while a software rasterizer (WARP)
  // draws far fewer, the backlog grows without bound, and anything that
  // waits on the GPU (screenshot readback's glFinish) stalls for tens of
  // seconds draining it. So hold ourselves to one frame in flight: fence
  // this frame, then wait for the previous one to finish.
  auto fence = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0);
  if (prev_fence_) {
    auto prev = static_cast<GLsync>(prev_fence_);
    glClientWaitSync(prev, GL_SYNC_FLUSH_COMMANDS_BIT, GL_TIMEOUT_IGNORED);
    glDeleteSync(prev);
  }
  prev_fence_ = fence;
}

}  // namespace ballistica::base

#endif  // BA_PLATFORM_WINDOWS && BA_OPENGL_IS_ES && BA_ENABLE_OPENGL
