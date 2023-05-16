// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_APP_APP_HEADLESS_H_
#define BALLISTICA_BASE_APP_APP_HEADLESS_H_
#if BA_HEADLESS_BUILD

#include "ballistica/base/app/app.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

class AppHeadless : public App {
 public:
  explicit AppHeadless(EventLoop* event_loop);
};

}  // namespace ballistica::base

#endif  // BA_HEADLESS_BUILD
#endif  // BALLISTICA_BASE_APP_APP_HEADLESS_H_
