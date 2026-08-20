// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/platform/support/sdl_message_box.h"

#include <string>

#include "ballistica/core/core.h"

#if BA_SDL_BUILD
#include "ballistica/core/platform/support/min_sdl.h"
#endif

namespace ballistica::core {

void ShowSDLFatalErrorDialog(const std::string& message) {
#if BA_SDL_BUILD
  assert(g_core->InMainThread());
  if (!g_core->HeadlessMode()) {
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Fatal Error",
                             message.c_str(), nullptr);
  }
#else
  // No SDL in this build; non-SDL platforms use native dialogs instead.
  (void)message;
#endif
}

}  // namespace ballistica::core
