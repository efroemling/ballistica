// Released under the MIT License. See LICENSE for details.
#if BA_HEADLESS_BUILD

#include "ballistica/base/app/app_headless.h"

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

// We could technically use the vanilla App class here since we're not
// changing anything.
AppHeadless::AppHeadless(EventLoop* event_loop) : App(event_loop) {
  // Handle a few misc things like stress-test updates.
  // (SDL builds set up a similar timer so we need to also).
  // This can probably go away at some point.
  this->event_loop()->NewTimer(10, true, NewLambdaRunnable([this] {
                                 assert(g_base->app);
                                 g_base->app->RunEvents();
                               }));
}

}  // namespace ballistica::base

#endif  // BA_HEADLESS_BUILD
