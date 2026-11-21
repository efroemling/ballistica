// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_OFFSCREEN_GL_WINDOWS_H_
#define BALLISTICA_BASE_APP_ADAPTER_OFFSCREEN_GL_WINDOWS_H_

#include "ballistica/shared/buildconfig/buildconfig_common.h"

#if BA_PLATFORM_WINDOWS && BA_OPENGL_IS_ES && BA_ENABLE_OPENGL

// For call sites to gate on.
#define BA_HAVE_OFFSCREEN_GL_WINDOWS 1

#include <string>

namespace ballistica::base {

/// Renders the GUI build into an offscreen ANGLE pbuffer instead of the
/// window.
///
/// For running GUI builds where Windows can't present to a window at all:
/// session 0 (services, ssh), which has no desktop compositor, so every
/// D3D11 window swap chain fails ('Could not create GLES window surface').
/// The SDL window still exists for events and sizing; we just never draw
/// to it. Rendering is otherwise the real shipping path (ANGLE -> D3D11),
/// on whatever adapter D3D picks -- WARP (software) on a GPU-less box.
///
/// Opt-in via the BA_OFFSCREEN_GL env var: '1' takes ANGLE's default
/// backend and adapter (honoring ANGLE_DEFAULT_PLATFORM), 'warp' forces
/// D3D11 on the WARP software rasterizer.
class OffscreenGLWindows {
 public:
  /// Whether this run asked for offscreen rendering.
  static auto Requested() -> bool;

  /// Create display, pbuffer and context and make them current. Fatal
  /// error on failure (there is nothing to fall back to).
  void Create(int width, int height);

  /// Recreate the pbuffer at a new size (window resizes).
  void Resize(int width, int height);

  /// End-of-frame (the equivalent of a window swap).
  void Swap();

 private:
  void CreateSurface_(int width, int height);
  [[noreturn]] void Fail_(const std::string& what);

  void* display_{};
  void* config_{};
  void* surface_{};
  void* context_{};
  void* prev_fence_{};  // GLsync of the previous frame (see Swap()).
  int width_{};
  int height_{};
};

}  // namespace ballistica::base

#endif  // BA_PLATFORM_WINDOWS && BA_OPENGL_IS_ES && BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_APP_ADAPTER_OFFSCREEN_GL_WINDOWS_H_
