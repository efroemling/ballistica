// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_MODE_EMPTY_H_
#define BALLISTICA_BASE_APP_APP_MODE_EMPTY_H_

#include <vector>

#include "ballistica/base/app/app_mode.h"

namespace ballistica::base {

class AppModeEmpty : public AppMode {
 public:
  AppModeEmpty();

  static auto GetSingleton() -> AppModeEmpty*;
  void Reset();
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_APP_APP_MODE_EMPTY_H_
