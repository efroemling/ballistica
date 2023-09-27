// Released under the MIT License. See LICENSE for details.
#if BA_XCODE_BUILD

#include "ballistica/base/app_adapter/app_adapter_apple.h"

#include <BallisticaKit-Swift.h>

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

auto AppAdapterApple::ManagesMainThreadEventLoop() const -> bool {
  // Nope; we run under a standard Cocoa/UIKit environment and they call us; we
  // don't call them.
  return false;
}

void AppAdapterApple::DoPushMainThreadRunnable(Runnable* runnable) {
  // Kick this along to swift.
  BallisticaKit::PushRawRunnableToMain(runnable);
}

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD
