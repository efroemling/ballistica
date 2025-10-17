// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_COMMON_H_
#define BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_COMMON_H_

#if _DEBUG
#define BA_DEBUG_BUILD 1
#endif

#ifndef M_PI
#define M_PI (3.1415926536f)
#endif

// disable warnings about strcpy/fopen/etc being unsafe
#define _CRT_SECURE_NO_WARNINGS

// Windows defines min/max macros which screw up the ability
// to use std::min and std::max. Don't want.
#define NOMINMAX

// Disable warnings about converting double to float, etc.
// 4068: Don't warn on unrecognized pragmas
#pragma warning(disable : 4800 4244 4355 4305 4068)

// Map gcc's __PRETTY_FUNCTION__ macro to the closest thing VC has
#define __PRETTY_FUNCTION__ __FUNCSIG__

#include "targetver.h"  // NOLINT

#define WIN32_LEAN_AND_MEAN  // Exclude rarely-used stuff from Windows headers

#define BA_PLATFORM "windows"

#if defined(_M_ARM64)
#define BA_ARCH "arm64"
#elif defined(_M_IX86)
#define BA_ARCH "x86"
#elif defined(_M_X64)
#define BA_ARCH "x86_64"
#else
#error unknown cpu architecture
#endif

#define BA_PLATFORM_WINDOWS 1

#define BA_SOCKET_SEND_DATA_TYPE char
#define BA_SOCKET_SEND_LENGTH_TYPE int
#define BA_SOCKET_SETSOCKOPT_VAL_TYPE char

#define BA_SOCKET_POLL WSAPoll
#define BA_SOCKET_POLL_FD POLLFD

#define BA_SOCKET_ERROR_RETURN SOCKET_ERROR

// On windows we always bundle python.
#define BA_CONTAINS_PYTHON_DIST 1

// Make ssize_t available (copy/paste from mMinGW)
#ifdef _MSC_VER
#ifndef _SSIZE_T_DEFINED
#define _SSIZE_T_DEFINED
#undef ssize_t
#ifdef _WIN64
typedef __int64 ssize_t;
#else
typedef int ssize_t;
#endif /* _WIN64 */
#endif /* _SSIZE_T_DEFINED */
#endif /* _MSC_VER */

#define BA_STAT _stat

// Some ODE stuff.
#define dTRIMESH_ENABLED 1
#define PENTIUM 1
#if !BA_DEBUG_BUILD
#define dNODEBUG 1
#endif

#if !BA_HEADLESS_BUILD
#define BA_ENABLE_AUDIO 1
#define BA_ENABLE_OPENGL 1
#endif

// We want main() by default.
// In our SDL builds, main is #defined as SDL_main which is called
// by SDLMain.lib regardless if whether we're built as a console or gui app.

#ifndef BA_DEFINE_MAIN
#define BA_DEFINE_MAIN 1
#endif

// By default we run as a console-mode app which conveniently exposes our
// python interpreter.
#ifndef BA_WINDOWS_CONSOLE_BUILD
#define BA_WINDOWS_CONSOLE_BUILD 1
#endif

// Include some common stuff for our precompiled header.
#include <malloc.h>
#include <tchar.h>

#include <cstdlib>

#endif  // BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_COMMON_H_
