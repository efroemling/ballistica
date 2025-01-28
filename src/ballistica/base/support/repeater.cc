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
}

void Repeater::PostInit_() {
  assert(g_base->InLogicThread());

  // Let's go ahead and run our initial time in a deferred call;
  // this is generally safer than running in the middle of whatever UI
  // code called us. Note that we use a strong ref here - if we use a
  // weak ref then it is possible for our initial key press to get lost
  // if the repeater gets canceled due to other keypresses/etc before
  // the initial call runs.

  auto strong_this = Object::Ref<Repeater>(this);
  g_base->logic->event_loop()->PushCall(
      [strong_this] { strong_this->runnable_->RunAndLogErrors(); });

  auto weak_this = Object::WeakRef<Repeater>(this);
  timer_ = DisplayTimer::New(weak_this->initial_delay_, false, [weak_this] {
    // Timer should not have fired if we died.
    assert(weak_this.exists());
    weak_this->runnable_->RunAndLogErrors();
    if (!weak_this.exists()) {
      // Runnable we just ran might have killed us.
      return;
    }
    // Kick off our repeat timer (generally the short one).
    weak_this->timer_ =
        DisplayTimer::New(weak_this->repeat_delay_, true, [weak_this] {
          // Timer should not have fired if we died.
          assert(weak_this.exists());
          weak_this->runnable_->RunAndLogErrors();
          // Doesn't matter if Runnable killed us since we don't
          // touch anything for the remainder of this function.
        });
  });
}

Repeater::~Repeater() { assert(g_base->InLogicThread()); }

}  // namespace ballistica::base
