// Released under the MIT License. See LICENSE for details.

#if BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS
#include "ballistica/base/graphics/gl/gl_sys_windows.h"

#include "SDL.h"
#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/shared/ballistica.h"

// Link against ANGLE import libs. The corresponding DLLs (libEGL.dll,
// libGLESv2.dll) must be present alongside the executable at runtime.
#pragma comment(lib, "libEGL.lib")
#pragma comment(lib, "libGLESv2.lib")

namespace ballistica::base {

void SysGLInit(RendererGL* renderer) {
  assert(!g_sys_gl_inited);

  // Let SDL locate the EGL/GLES library. With SDL_GL_CONTEXT_PROFILE_ES and
  // SDL_HINT_OPENGL_ES_DRIVER set, SDL will look for libEGL.dll rather than
  // opengl32.dll.
  SDL_GL_LoadLibrary(nullptr);

  // Verify the GLES version before we try to use any GL calls.
  renderer->CheckGLVersion();
}

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS
