// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_EVENT_LOOP_H_
#define BALLISTICA_SHARED_FOUNDATION_EVENT_LOOP_H_

#include <condition_variable>
#include <list>
#include <mutex>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include "ballistica/shared/generic/lambda_runnable.h"
#include "ballistica/shared/generic/timer_list.h"

namespace ballistica {

const int kThreadMessageSafetyThreshold{500};

class EventLoop {
 public:
  explicit EventLoop(EventLoopID id,
                     ThreadSource source = ThreadSource::kCreate);
  virtual ~EventLoop();

  static void SetEventLoopsSuspended(bool enable);
  static auto AreEventLoopsSuspended() -> bool;

  auto ThreadIsCurrent() const -> bool {
    return std::this_thread::get_id() == thread_id();
  }

  /// Flags the loop to exit at the end of the next cycle.
  void Exit();

  void SetAcquiresPythonGIL();

  void PushSetSuspended(bool suspended);

  auto thread_id() const -> std::thread::id {
    assert(this);
    return thread_id_;
  }

  void RunToCompletion();
  void RunSingleCycle();

  auto identifier() const -> EventLoopID { return identifier_; }

  /// Register a timer to run on the thread.
  auto NewTimer(microsecs_t length, bool repeat, Runnable* runnable) -> Timer*;

  Timer* GetTimer(int id);
  void DeleteTimer(int id);

  /// Add a runnable to this thread's event-loop. Pass a Runnable that has
  /// been allocated with NewUnmanaged(). It will be owned and disposed of
  /// by the thread.
  void PushRunnable(Runnable* runnable);

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  void PushCall(const F& lambda) {
    PushRunnable(NewLambdaRunnableUnmanaged(lambda));
  }

  /// Add a runnable to this thread's event-loop and wait until it
  /// completes.
  void PushRunnableSynchronous(Runnable* runnable);

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  void PushCallSynchronous(const F& lambda) {
    PushRunnableSynchronous(NewLambdaRunnableUnmanaged(lambda));
  }

  /// Add a callback to be run on event-loop suspends.
  void AddSuspendCallback(Runnable* runnable);

  /// Add a callback to be run on event-loop unsuspends.
  void AddUnsuspendCallback(Runnable* runnable);

  auto has_pending_runnables() const -> bool { return !runnables_.empty(); }

  /// Returns true if there is plenty of buffer space available for
  /// PushCall/PushRunnable; can be used to avoid buffer-full errors
  /// by discarding non-essential calls. An example is calls scheduled
  /// due to receiving unreliable network packets; without watching
  /// buffer space it can be possible for an attacker to bring down
  /// the app through a flood of packets.
  auto CheckPushSafety() -> bool;

  static auto GetStillSuspendingEventLoops() -> std::vector<EventLoop*>;

  auto suspended() { return suspended_; }
  auto done() -> bool { return done_; }

  auto name() const { return name_; }

 private:
  struct ThreadMessage_ {
    enum class Type { kShutdown = 999, kRunnable, kSuspend, kUnsuspend };
    Type type;
    union {
      Runnable* runnable{};
    };
    bool* completion_flag{};
    explicit ThreadMessage_(Type type_in) : type(type_in) {}
    explicit ThreadMessage_(Type type, Runnable* runnable,
                            bool* completion_flag)
        : type(type), runnable(runnable), completion_flag{completion_flag} {}
  };
  auto CheckPushRunnableSafety_() -> bool;
  void WaitForNextEvent_(bool single_cycle);
  void LogThreadMessageTally_(
      std::vector<std::pair<LogLevel, std::string>>* log_entries);
  void PushLocalRunnable_(Runnable* runnable, bool* completion_flag);
  void PushCrossThreadRunnable_(Runnable* runnable, bool* completion_flag);
  void NotifyClientListeners_();
  void Run_(bool single_cycle);

  // These are all exactly the same, but running different ones for
  // different threads can help identify threads in profilers, backtraces,
  // etc.
  static auto ThreadMainLogic_(void* data) -> int;
  static auto ThreadMainLogicP_(void* data) -> void*;
  static auto ThreadMainAudio_(void* data) -> int;
  static auto ThreadMainAudioP_(void* data) -> void*;
  static auto ThreadMainBGDynamics_(void* data) -> int;
  static auto ThreadMainBGDynamicsP_(void* data) -> void*;
  static auto ThreadMainNetworkWrite_(void* data) -> int;
  static auto ThreadMainNetworkWriteP_(void* data) -> void*;
  static auto ThreadMainStdInput_(void* data) -> int;
  static auto ThreadMainStdInputP_(void* data) -> void*;
  static auto ThreadMainAssets_(void* data) -> int;
  static auto ThreadMainAssetsP_(void* data) -> void*;

  auto ThreadMain_() -> int;
  void GetThreadMessages_(std::list<ThreadMessage_>* messages);
  void PushThreadMessage_(const ThreadMessage_& t);

  void RunPendingRunnables_();
  void RunSuspendCallbacks_();
  void RunUnsuspendCallbacks_();

  void AcquireGIL_();
  void ReleaseGIL_();

  void BootstrapThread_();

  EventLoopID identifier_{EventLoopID::kInvalid};
  ThreadSource source_{};
  bool bootstrapped_{};
  bool writing_tally_{};
  bool suspended_{};
  bool done_{};
  bool acquires_python_gil_{};
  std::thread::id thread_id_{};
  std::condition_variable thread_message_cv_;
  std::condition_variable client_listener_cv_;
  std::list<std::pair<Runnable*, bool*>> runnables_;
  std::list<Runnable*> suspend_callbacks_;
  std::list<Runnable*> unsuspend_callbacks_;
  std::list<ThreadMessage_> thread_messages_;
  std::mutex thread_message_mutex_;
  std::mutex client_listener_mutex_;
  std::list<std::vector<char>> data_to_client_;
  std::string name_;
  PyThreadState* py_thread_state_{};
  TimerList timers_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_EVENT_LOOP_H_
