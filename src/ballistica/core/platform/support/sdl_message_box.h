// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PLATFORM_SUPPORT_SDL_MESSAGE_BOX_H_
#define BALLISTICA_CORE_PLATFORM_SUPPORT_SDL_MESSAGE_BOX_H_

#include <string>

namespace ballistica::core {

/// Show a blocking SDL fatal-error message box.
///
/// This keeps the lone remaining SDL message-box call in a single gated
/// spot instead of the cross-platform CorePlatform base, so SDL stays out
/// of shared core. SDL-build platform subclasses (Linux, Windows, cmake
/// macOS) call this from their BlockingFatalErrorDialog() overrides; it is
/// a no-op in non-SDL builds. (xcode macOS uses a native Cocoa dialog
/// instead; this is the 'option 3' interim until/unless those platforms
/// grow native dialogs too — see docs/initiatives/sdl-type-decoupling.md.)
void ShowSDLFatalErrorDialog(const std::string& message);

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_PLATFORM_SUPPORT_SDL_MESSAGE_BOX_H_
