// Released under the MIT License. See LICENSE for details.
#if BA_HEADLESS_BUILD

#include "ballistica/base/app_adapter/app_adapter_headless.h"

#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

// We could technically use the vanilla App class here since we're not
// changing anything.
AppAdapterHeadless::AppAdapterHeadless() {
  // Handle a few misc things like stress-test updates.
  // (SDL builds set up a similar timer so we need to also).
  // This can probably go away at some point.
  g_core->main_event_loop()->NewTimer(10, true, NewLambdaRunnable([this] {
                                        assert(g_base->app_adapter);
                                        g_base->app_adapter->RunEvents();
                                      }));
}

}  // namespace ballistica::base

#endif  // BA_HEADLESS_BUILD
