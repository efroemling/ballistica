// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_SUPPORT_MIN_SDL_H_
#define BALLISTICA_CORE_PLATFORM_SUPPORT_MIN_SDL_H_

// Note to self: This needs to remain in core. It would seem like it could
// go to base since it deals mostly in high level app type stuff. However we
// need it in core because SDL provides things such as fatal error dialogs
// which may be required before base is even spun up. Also the SDLMain
// mechanism affects our main() definition so that is needed where we define
// main.

// A bit of history:
//
// Ballistica originally used SDL as its sole library for events,
// window-management, etc. on all platforms. This means a lot of the low
// level event handling code was written with SDL types.
//
// Over time, for various reasons, I started converting bits of
// functionality over to native platform APIs, to the point where nowadays
// SDL's role is largely vestigial in some builds; SDL types are getting
// passed around but not actually being supplied by SDL.
//
// At this point many builds no longer depend on SDL at all, though some SDL
// types are still used. That's where this header comes in.
//
// The minimum bits of SDL still needed to compile the game have been copied
// here for use by 'non-sdl' platforms. This mainly includes things like
// event types and keysyms.
//
// On platforms using 'full' SDL, this header simply includes the full sdl
// headers.
//
// The theory is that, over time, the SDL types contained here can be
// replaced with ballistica-specific types. The 'full' SDL platform layer
// can then translate its SDL types to ballistica types in the same way that
// other platform code translates their native types, and eventually SDL
// usage can be nicely contained to platform and/or app-adapter classes.

/*
  Simple DirectMedia Layer
  Copyright (C) 1997-2012 Sam Lantinga <slouken@libsdl.org>

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.
*/

#if BA_SDL_BUILD
// We supply our own main() (see shared/ballistica.cc and the Oculus
// main_rift.cc) and call SDL_SetMainReady() before SDL_Init rather than
// letting SDL inject a platform entry-point shim. SDL3's header-only shim
// assumes a particular subsystem/entry signature (e.g. wmain/WinMain on a
// UNICODE Windows build) which clashes with our Console-subsystem `main`, so
// we opt out via SDL_MAIN_HANDLED. This must be defined before SDL_main.h.
#define SDL_MAIN_HANDLED
// SDL3's master header pulls in events/keyboard/keycode/messagebox/etc., so
// the individual includes we used under SDL2 are no longer needed.
#include <SDL3/SDL.h>  // IWYU pragma: export
// For SDL_SetMainReady(); SDL_MAIN_HANDLED above suppresses the main-redefine
// and the entry-point shim, leaving just the declaration.
#include <SDL3/SDL_main.h>  // IWYU pragma: export
#endif                      // BA_SDL_BUILD

#endif  // BALLISTICA_CORE_PLATFORM_SUPPORT_MIN_SDL_H_
