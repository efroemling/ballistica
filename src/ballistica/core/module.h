// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_MODULE_H_
#define BALLISTICA_CORE_MODULE_H_

#include <list>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/generic/lambda_runnable.h"
#include "ballistica/generic/runnable.h"

namespace ballistica {

/// A logical entity that can be added to a thread and make use of its
/// event loop.
class Module {
 public:
  /// Add a runnable to this module's queue.
  /// Pass a Runnable that has been allocated with new().
  /// There must be no existing strong refs to it.
  /// It will be owned and disposed of by the module from this point.
  auto PushRunnable(Runnable* runnable) -> void;

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  auto PushCall(const F& lambda) -> void {
    PushRunnable(NewLambdaRunnableRaw(lambda));
  }

  /// Returns true if there is plenty of buffer space available for
  /// PushCall/PushRunnable; can be used to avoid buffer-full errors
  /// by discarding non-essential calls. An example is calls scheduled
  /// due to receiving unreliable network packets; without watching
  /// buffer space it can be possible for an attacker to bring down
  /// the app through a flood of packets.
  auto CheckPushSafety() -> bool;

  /// Return the thread this module is running on.
  auto thread() const -> Thread* { return thread_; }

  virtual ~Module();

  /// Push a runnable from the same thread as the module.
  auto PushLocalRunnable(Runnable* runnable) -> void;

  /// Called for each module when its thread is about to be suspended
  /// (on platforms such as mobile).
  virtual auto HandleThreadPause() -> void {}

  /// Called for each module when its thread is about to be resumed
  /// (on platforms such as mobile).
  virtual auto HandleThreadResume() -> void {}

  /// Whether this module has pending runnables.
  auto has_pending_runnables() const -> bool { return !runnables_.empty(); }

  /// Used by the module's owner thread to let it do its thing.
  auto RunPendingRunnables() -> void;

  auto name() const -> const std::string& { return name_; }

 protected:
  Module(std::string name, Thread* thread);
  auto NewThreadTimer(millisecs_t length, bool repeat,
                      const Object::Ref<Runnable>& runnable) -> Timer*;

 private:
  std::string name_;
  int id_{};
  std::list<Runnable*> runnables_;
  Thread* thread_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_CORE_MODULE_H_
