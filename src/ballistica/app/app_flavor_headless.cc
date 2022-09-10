// Released under the MIT License. See LICENSE for details.
#if BA_HEADLESS_BUILD

#include "ballistica/app/app_flavor_headless.h"

#include "ballistica/ballistica.h"

namespace ballistica {

// We could technically use the vanilla App class here since we're not
// changing anything.
AppFlavorHeadless::AppFlavorHeadless(Thread* thread) : AppFlavor(thread) {
  // Handle a few misc things like stress-test updates.
  // (SDL builds set up a similar timer so we need to also).
  // This can probably go away at some point.
  this->thread()->NewTimer(10, true, NewLambdaRunnable([this] {
                             assert(g_app_flavor);
                             g_app_flavor->RunEvents();
                           }));
}

}  // namespace ballistica

#endif  // BA_HEADLESS_BUILD
