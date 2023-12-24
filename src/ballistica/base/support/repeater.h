// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_SUPPORT_REPEATER_H_
#define BALLISTICA_BASE_SUPPORT_REPEATER_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/generic/lambda_runnable.h"

namespace ballistica::base {

/// Runs some code immediately and then repeatedly after a delay. Useful for
/// jobs such as selecting ui elements while keys or buttons are held.
/// Uses display-time so emphasizes visual smoothness over accuracy.
class Repeater : public Object {
 public:
  Repeater(seconds_t initial_delay, seconds_t repeat_delay, Runnable* runnable);
  ~Repeater();

  template <typename F>
  static auto New(seconds_t initial_delay, seconds_t repeat_delay,
                  const F& lambda) {
    return Object::New<Repeater>(initial_delay, repeat_delay,
                                 NewLambdaRunnable<F>(lambda).Get());
  }

 private:
  seconds_t initial_delay_;
  seconds_t repeat_delay_;
  Object::Ref<DisplayTimer> timer_;
  Object::Ref<Runnable> runnable_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_SUPPORT_REPEATER_H_
