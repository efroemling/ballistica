// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/app/app_mode_empty.h"

namespace ballistica::base {

static AppModeEmpty* g_app_mode_empty{};

AppModeEmpty::AppModeEmpty() = default;

auto AppModeEmpty::GetSingleton() -> AppModeEmpty* {
  // TODO(ericf): Turn this back on once we're creating in logic thread.

  // assert(g_base->InLogicThread());  // Can relax this if need be.
  if (g_app_mode_empty == nullptr) {
    g_app_mode_empty = new AppModeEmpty();
  }
  return g_app_mode_empty;
}

}  // namespace ballistica::base
