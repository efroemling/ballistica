// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/repeater.h"

#include "ballistica/base/support/display_timer.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {
Repeater::Repeater(seconds_t initial_delay, seconds_t repeat_delay,
                   Runnable* runnable)
    : initial_delay_(initial_delay),
      repeat_delay_(repeat_delay),
      runnable_(runnable) {
  assert(g_base->InLogicThread());
  assert(initial_delay >= 0.0);
  assert(repeat_delay >= 0.0);

  // Let's go ahead and run our initial time in a deferred call;
  // this is generally safer than running in the middle of whatever UI
  // code set this up.
  auto weak_this = Object::WeakRef<Repeater>(this);
  g_base->logic->event_loop()->PushCall([weak_this] {
    if (weak_this.Exists()) {
      weak_this->runnable_->RunAndLogErrors();
      if (!weak_this.Exists()) {
        // Runnable might have killed us.
        return;
      }
      // Kick off our initial delay timer (generally the longer one).
      weak_this->timer_ =
          DisplayTimer::New(weak_this->initial_delay_, false, [weak_this] {
            // Timer should not have fired if we died.
            assert(weak_this.Exists());
            weak_this->runnable_->RunAndLogErrors();
            if (!weak_this.Exists()) {
              // Runnable might have killed us.
              return;
            }
            // Kick off our repeat timer (generally the short one).
            weak_this->timer_ =
                DisplayTimer::New(weak_this->repeat_delay_, true, [weak_this] {
                  // Timer should not have fired if we died.
                  assert(weak_this.Exists());
                  weak_this->runnable_->RunAndLogErrors();
                  // Doesn't matter if Runnable killed us since we don't
                  // touch anything for the remainder of this function.
                });
          });
    }
  });
}

Repeater::~Repeater() { assert(g_base->InLogicThread()); }

}  // namespace ballistica::base
