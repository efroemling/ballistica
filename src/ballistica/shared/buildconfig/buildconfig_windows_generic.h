// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_GENERIC_H_
#define BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_GENERIC_H_

// note: define overrides BEFORE common makefile

#define BA_ENABLE_STDIO_CONSOLE 1

#define BA_SDL_BUILD 1
// #define BA_SDL2_BUILD 1
#define BA_ENABLE_SDL_JOYSTICKS 1

#include "ballistica/shared/buildconfig/buildconfig_windows_common.h"

// This must always be last.
#include "ballistica/shared/buildconfig/buildconfig_common.h"

#endif  // BALLISTICA_SHARED_BUILDCONFIG_BUILDCONFIG_WINDOWS_GENERIC_H_
