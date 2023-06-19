// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/app/app_mode_empty.h"

namespace ballistica::base {

static AppModeEmpty* g_app_mode_empty{};

AppModeEmpty::AppModeEmpty() = default;

auto AppModeEmpty::GetSingleton() -> AppModeEmpty* {
  assert(g_base == nullptr || g_base->InLogicThread());

  if (g_app_mode_empty == nullptr) {
    g_app_mode_empty = new AppModeEmpty();
  }
  return g_app_mode_empty;
}

void AppModeEmpty::Reset() {
  // Nothing here currently.
}

}  // namespace ballistica::base
