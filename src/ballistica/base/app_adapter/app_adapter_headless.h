// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_HEADLESS_H_
#define BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_HEADLESS_H_
#if BA_HEADLESS_BUILD

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

class AppAdapterHeadless : public AppAdapter {
 public:
  AppAdapterHeadless();
};

}  // namespace ballistica::base

#endif  // BA_HEADLESS_BUILD
#endif  // BALLISTICA_BASE_APP_ADAPTER_APP_ADAPTER_HEADLESS_H_
