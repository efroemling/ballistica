// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_THREAD_H_
#define BALLISTICA_CORE_THREAD_H_

#include <condition_variable>
#include <list>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/app/app.h"
#include "ballistica/ballistica.h"
#include "ballistica/generic/lambda_runnable.h"
#include "ballistica/generic/timer_list.h"
#include "ballistica/platform/min_sdl.h"

namespace ballistica {

const int kThreadMessageSafetyThreshold{500};

// A thread with a built-in event loop.
class Thread {
 public:
  explicit Thread(ThreadTag id, ThreadSource source = ThreadSource::kCreate);
  virtual ~Thread();

  auto ClearCurrentThreadName() -> void;

  static auto GetCurrentThreadName() -> std::string;

  /// Call this if the main thread changes.
  static auto UpdateMainThreadID() -> void;

  static auto SetThreadsPaused(bool enable) -> void;
  static auto AreThreadsPaused() -> bool;

  auto IsCurrent() const -> bool {
    return std::this_thread::get_id() == thread_id();
  }

  // Used to quit the main thread.
  void Quit();

  void SetAcquiresPythonGIL();

  void SetPaused(bool paused);
  auto thread_id() const -> std::thread::id { return thread_id_; }

  // Needed in rare cases where we jump physical threads.
  // (Our 'main' thread on Android can switch under us as
  // rendering contexts are recreated in new threads/etc.)
  void set_thread_id(std::thread::id id) { thread_id_ = id; }

  auto RunEventLoop(bool single_cycle = false) -> int;
  auto identifier() const -> ThreadTag { return identifier_; }

  // Register a timer to run on the thread.
  auto NewTimer(millisecs_t length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> Timer*;

  /// Add a runnable to this thread's event-loop.
  /// Pass a Runnable that has been allocated with new().
  /// There must be no existing strong refs to it.
  /// It will be owned by the thread
  auto PushRunnable(Runnable* runnable) -> void;

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  auto PushCall(const F& lambda) -> void {
    PushRunnable(NewLambdaRunnableRaw(lambda));
  }

  /// Add a runnable to this thread's event-loop and wait until it completes.
  auto PushRunnableSynchronous(Runnable* runnable) -> void;

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  auto PushCallSynchronous(const F& lambda) -> void {
    PushRunnableSynchronous(NewLambdaRunnableRaw(lambda));
  }

  /// Add a callback to be run on event-loop pauses.
  auto AddPauseCallback(Runnable* runnable) -> void;

  /// Add a callback to be run on event-loop resumes.
  auto AddResumeCallback(Runnable* runnable) -> void;

  auto has_pending_runnables() const -> bool { return !runnables_.empty(); }

  /// Returns true if there is plenty of buffer space available for
  /// PushCall/PushRunnable; can be used to avoid buffer-full errors
  /// by discarding non-essential calls. An example is calls scheduled
  /// due to receiving unreliable network packets; without watching
  /// buffer space it can be possible for an attacker to bring down
  /// the app through a flood of packets.
  auto CheckPushSafety() -> bool;

 private:
  struct ThreadMessage {
    enum class Type { kShutdown = 999, kRunnable, kPause, kResume };
    Type type;
    union {
      Runnable* runnable;
    };
    bool* completion_flag{};
    explicit ThreadMessage(Type type_in) : type(type_in) {}
    explicit ThreadMessage(Type type, Runnable* runnable, bool* completion_flag)
        : type(type), runnable(runnable), completion_flag{completion_flag} {}
  };
  auto CheckPushRunnableSafety() -> bool;
  auto SetInternalThreadName(const std::string& name) -> void;
  auto WaitForNextEvent(bool single_cycle) -> void;
  auto LoopUpkeep(bool once) -> void;
  auto LogThreadMessageTally() -> void;
  auto PushLocalRunnable(Runnable* runnable, bool* completion_flag) -> void;
  auto PushCrossThreadRunnable(Runnable* runnable, bool* completion_flag)
      -> void;
  auto NotifyClientListeners() -> void;

  bool writing_tally_{};
  bool paused_{};
  millisecs_t last_pause_time_{};
  int messages_since_paused_{};
  millisecs_t last_paused_message_report_time_{};
  bool done_{};
  ThreadSource source_;
  int listen_sd_{};
  std::thread::id thread_id_{};
  ThreadTag identifier_{ThreadTag::kInvalid};
  millisecs_t last_complaint_time_{};
  bool acquires_python_gil_{};

  // FIXME: Should generalize this to some sort of PlatformThreadData class.
#if BA_XCODE_BUILD
  void* auto_release_pool_{};
#endif

  // These are all exactly the same, but by running different ones for
  // different thread groups makes its easy to see which thread is which
  // in profilers, backtraces, etc.
  static auto RunLogicThread(void* data) -> int;
  static auto RunAudioThread(void* data) -> int;
  static auto RunBGDynamicThread(void* data) -> int;
  static auto RunNetworkWriteThread(void* data) -> int;
  static auto RunStdInputThread(void* data) -> int;
  static auto RunAssetsThread(void* data) -> int;

  auto ThreadMain() -> int;
  auto GetThreadMessages(std::list<ThreadMessage>* messages) -> void;
  auto PushThreadMessage(const ThreadMessage& t) -> void;

  auto RunPendingRunnables() -> void;
  auto RunPauseCallbacks() -> void;
  auto RunResumeCallbacks() -> void;

  bool bootstrapped_{};
  std::list<std::pair<Runnable*, bool*>> runnables_;
  std::list<Runnable*> pause_callbacks_;
  std::list<Runnable*> resume_callbacks_;
  std::thread* thread_{};
  std::condition_variable thread_message_cv_;
  std::mutex thread_message_mutex_;
  std::list<ThreadMessage> thread_messages_;
  std::condition_variable client_listener_cv_;
  std::mutex client_listener_mutex_;
  std::list<std::vector<char>> data_to_client_;
  TimerList timers_;
};

}  // namespace ballistica

#endif  // BALLISTICA_CORE_THREAD_H_
