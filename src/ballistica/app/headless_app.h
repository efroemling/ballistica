// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_APP_HEADLESS_APP_H_
#define BALLISTICA_APP_HEADLESS_APP_H_
#if BA_HEADLESS_BUILD

#include "ballistica/app/app.h"
#include "ballistica/core/thread.h"

namespace ballistica {

class HeadlessApp : public App {
 public:
  explicit HeadlessApp(Thread* thread);
};

}  // namespace ballistica

#endif  // BA_HEADLESS_BUILD
#endif  // BALLISTICA_APP_HEADLESS_APP_H_
