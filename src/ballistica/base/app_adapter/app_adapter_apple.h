// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_

#if BA_XCODE_BUILD

#include "ballistica/base/app_adapter/app_adapter.h"

namespace ballistica::base {

class AppAdapterApple : public AppAdapter {
 public:
  auto ManagesMainThreadEventLoop() const -> bool override;

 protected:
  void DoPushMainThreadRunnable(Runnable* runnable) override;

 private:
};

}  // namespace ballistica::base

#endif  // BA_XCODE_BUILD

#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_APPLE_H_
