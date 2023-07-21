// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_CMAKE_H_
#define BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_CMAKE_H_

// For cmake builds, attempt to figure out what architecture we're running on
// and define stuff accordingly.
#if __APPLE__

// Yes Apple, I know GL is deprecated. I don't need constant reminders. You're
// stressing me out.
#define GL_SILENCE_DEPRECATION

// We currently support regular and client builds on 64 bit mac posix
#if __amd64__
#define BA_PLATFORM_STRING "x86_64_macos"
#elif __aarch64__
#define BA_PLATFORM_STRING "arm64_macos"
#else
#error Unknown processor architecture.
#endif

#define BA_OSTYPE_MACOS 1
#define HAVE_FRAMEWORK_OPENAL 1

#elif __linux__

#if __amd64__
#define BA_PLATFORM_STRING "x86_64_linux"
#define BA_OSTYPE_LINUX 1
#elif __i386__
#define BA_PLATFORM_STRING "x86_32_linux"
#define BA_OSTYPE_LINUX 1
#elif __arm__
#define BA_PLATFORM_STRING "arm_linux"
#define BA_OSTYPE_LINUX 1
#elif __aarch64__
#define BA_PLATFORM_STRING "arm64_linux"
#define BA_OSTYPE_LINUX 1

#else
#error unknown linux variant
#endif

#else
#error config_cmake.h: unknown architecture
#endif

#define dTRIMESH_ENABLED 1

#if !BA_HEADLESS_BUILD
#define BA_ENABLE_AUDIO 1
#define BA_ENABLE_OPENGL 1
#define BA_SDL_BUILD 1
#define BA_SDL2_BUILD 1
#define BA_ENABLE_SDL_JOYSTICKS 1
#else
#define BA_MINSDL_BUILD 1
#endif

// Yup we've got that.
#define BA_ENABLE_EXECINFO_BACKTRACES 1

// Allow stdin commands too.
#define BA_ENABLE_STDIO_CONSOLE 1

#ifndef BA_DEFINE_MAIN
#define BA_DEFINE_MAIN 1
#endif

#if !BA_DEBUG_BUILD

// Used by ODE.
#define dNODEBUG 1

// Used by assert.
#ifndef NDEBUG
#define NDEBUG
#endif
#endif  // !BA_DEBUG_BUILD

// Include some stuff here for once we get precompiling going.
#ifdef __cplusplus
#endif  // __cplusplus

// This must always be last.
#include "ballistica/shared/buildconfig/buildconfig_common.h"

#endif  // BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_CMAKE_H_
