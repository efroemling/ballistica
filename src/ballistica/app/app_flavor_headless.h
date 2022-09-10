// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_APP_FLAVOR_HEADLESS_H_
#define BALLISTICA_APP_APP_FLAVOR_HEADLESS_H_
#if BA_HEADLESS_BUILD

#include "ballistica/app/app_flavor.h"
#include "ballistica/core/thread.h"

namespace ballistica {

class AppFlavorHeadless : public AppFlavor {
 public:
  explicit AppFlavorHeadless(Thread* thread);
};

}  // namespace ballistica

#endif  // BA_HEADLESS_BUILD
#endif  // BALLISTICA_APP_APP_FLAVOR_HEADLESS_H_
