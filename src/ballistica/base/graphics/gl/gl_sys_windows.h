// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_WINDOWS_H_
#define BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_WINDOWS_H_

// System GL bits for windows.

#if BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS

// ANGLE provides OpenGL ES via Direct3D 11 on Windows. All core GLES3
// functions are resolved through the libGLESv2 import library; no manual
// function-pointer loading is needed.
#include <GLES3/gl3.h>

// We run some init code (SDL_GL_LoadLibrary + version check).
#define BA_HAS_SYS_GL_INIT

#endif  // BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS

#endif  // BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_WINDOWS_H_
