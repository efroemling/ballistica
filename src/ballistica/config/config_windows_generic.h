// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CONFIG_CONFIG_WINDOWS_GENERIC_H_
#define BALLISTICA_CONFIG_CONFIG_WINDOWS_GENERIC_H_

// note: define overrides BEFORE common makefile

#define BA_ENABLE_STDIO_CONSOLE 1

#define BA_SDL_BUILD 1
#define BA_SDL2_BUILD 1
#define BA_ENABLE_SDL_JOYSTICKS 1

#include "ballistica/config/config_windows_common.h"

// This must always be last.
#include "ballistica/config/config_common.h"

#endif  // BALLISTICA_CONFIG_CONFIG_WINDOWS_GENERIC_H_
