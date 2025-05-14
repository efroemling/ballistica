// Released under the MIT License. See LICENSE for details.

#if BA_ENABLE_OPENGL
#include "ballistica/base/graphics/gl/gl_sys.h"

#include "ballistica/shared/ballistica.h"

// #include "ballistica/base/app_adapter/app_adapter_sdl.h"
// #include "ballistica/base/base.h"
// #include "ballistica/core/core.h"

// #if BA_PLATFORM_ANDROID
// #include <EGL/egl.h>
// #if !BA_USE_ES3_INCLUDES
// #include "ballistica/core/platform/android/android_gl3.h"
// #endif
// #endif

// #if BA_PLATFORM_MACOS
// #include <OpenGL/CGLContext.h>
// #include <OpenGL/CGLTypes.h>
// #include <OpenGL/OpenGL.h>
// #endif

// #if BA_PLATFORM_IOS
// void (*glInvalidateFramebuffer)(GLenum target, GLsizei num_attachments,
//                                 const GLenum* attachments) = nullptr;
// #endif

// #if BA_PLATFORM_ANDROID
// PFNGLDISCARDFRAMEBUFFEREXTPROC _glDiscardFramebufferEXT = nullptr;
// #endif

namespace ballistica::base {

bool g_sys_gl_inited{};

// #if 0
//   // Fetch needed android gl stuff.
// #if BA_PLATFORM_ANDROID
// #define GET(PTRTYPE, FUNC, REQUIRED)                         \
//   FUNC = (PTRTYPE)eglGetProcAddress(#FUNC);                  \
//   if (!FUNC) FUNC = (PTRTYPE)eglGetProcAddress(#FUNC "EXT"); \
//   if (REQUIRED) {                                            \
//     BA_PRECONDITION(FUNC != nullptr);                        \
//   }
//   GET(PFNGLDISCARDFRAMEBUFFEREXTPROC, _glDiscardFramebufferEXT, false);
// #endif  // BA_PLATFORM_ANDROID

// #endif  // 0

// Provide an empty implementation of this if noone provided a real one.
#ifndef BA_HAS_SYS_GL_INIT

void SysGLInit(RendererGL* renderer) { assert(!g_sys_gl_inited); }

#endif  // BA_HAS_SYS_GL_INIT

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL
