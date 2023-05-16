// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_FOUNDATION_EVENT_LOOP_H_
#define BALLISTICA_SHARED_FOUNDATION_EVENT_LOOP_H_

#include <condition_variable>
#include <list>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/generic/lambda_runnable.h"
#include "ballistica/shared/generic/timer_list.h"

namespace ballistica {

const int kThreadMessageSafetyThreshold{500};

// A thread with a built-in event loop.
class EventLoop {
 public:
  explicit EventLoop(EventLoopID id,
                     ThreadSource source = ThreadSource::kCreate);
  virtual ~EventLoop();

  void ClearCurrentThreadName();

  static auto CurrentThreadName() -> std::string;

  static void SetThreadsPaused(bool enable);
  static auto AreThreadsPaused() -> bool;

  auto ThreadIsCurrent() const -> bool {
    return std::this_thread::get_id() == thread_id();
  }

  // Used to quit the main thread.
  void Quit();

  void SetAcquiresPythonGIL();

  void PushSetPaused(bool paused);

  auto thread_id() const -> std::thread::id { return thread_id_; }

  // Needed in rare cases where we jump physical threads.
  // (Our 'main' thread on Android can switch under us as
  // rendering contexts are recreated in new threads/etc.)
  void set_thread_id(std::thread::id id) { thread_id_ = id; }

  auto RunEventLoop(bool single_cycle = false) -> int;
  auto identifier() const -> EventLoopID { return identifier_; }

  // Register a timer to run on the thread.
  auto NewTimer(millisecs_t length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> Timer*;

  Timer* GetTimer(int id);
  void DeleteTimer(int id);
  /// Add a runnable to this thread's event-loop.
  /// Pass a Runnable that has been allocated with NewUnmanaged().
  /// It will be owned and disposed of by the thread.
  void PushRunnable(Runnable* runnable);

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  void PushCall(const F& lambda) {
    PushRunnable(NewLambdaRunnableUnmanaged(lambda));
  }

  /// Add a runnable to this thread's event-loop and wait until it completes.
  void PushRunnableSynchronous(Runnable* runnable);

  /// Convenience function to push a lambda as a runnable.
  template <typename F>
  void PushCallSynchronous(const F& lambda) {
    PushRunnableSynchronous(NewLambdaRunnableUnmanaged(lambda));
  }

  /// Add a callback to be run on event-loop pauses.
  void AddPauseCallback(Runnable* runnable);

  /// Add a callback to be run on event-loop resumes.
  void AddResumeCallback(Runnable* runnable);

  auto has_pending_runnables() const -> bool { return !runnables_.empty(); }

  /// Returns true if there is plenty of buffer space available for
  /// PushCall/PushRunnable; can be used to avoid buffer-full errors
  /// by discarding non-essential calls. An example is calls scheduled
  /// due to receiving unreliable network packets; without watching
  /// buffer space it can be possible for an attacker to bring down
  /// the app through a flood of packets.
  auto CheckPushSafety() -> bool;

  static auto GetStillPausingThreads() -> std::vector<EventLoop*>;

  auto paused() { return paused_; }

 private:
  struct ThreadMessage {
    enum class Type { kShutdown = 999, kRunnable, kPause, kResume };
    Type type;
    union {
      Runnable* runnable{};
    };
    bool* completion_flag{};
    explicit ThreadMessage(Type type_in) : type(type_in) {}
    explicit ThreadMessage(Type type, Runnable* runnable, bool* completion_flag)
        : type(type), runnable(runnable), completion_flag{completion_flag} {}
  };
  auto CheckPushRunnableSafety() -> bool;
  void SetInternalThreadName(const std::string& name);
  void WaitForNextEvent(bool single_cycle);
  void LoopUpkeep(bool once);
  void LogThreadMessageTally(
      std::vector<std::pair<LogLevel, std::string>>* log_entries);
  void PushLocalRunnable(Runnable* runnable, bool* completion_flag);
  void PushCrossThreadRunnable(Runnable* runnable, bool* completion_flag);
  void NotifyClientListeners();

  bool writing_tally_{};
  bool paused_{};
  millisecs_t last_pause_time_{};
  int messages_since_paused_{};
  millisecs_t last_paused_message_report_time_{};
  bool done_{};
  ThreadSource source_;
  int listen_sd_{};
  std::thread::id thread_id_{};
  EventLoopID identifier_{EventLoopID::kInvalid};
  millisecs_t last_complaint_time_{};
  bool acquires_python_gil_{};

  // FIXME: Should generalize this to some sort of PlatformThreadData class.
#if BA_XCODE_BUILD
  void* auto_release_pool_{};
#endif

  // These are all exactly the same, but running different ones for
  // different threads can help identify threads in profilers, backtraces,
  // etc.
  static auto ThreadMainLogic(void* data) -> int;
  static auto ThreadMainLogicP(void* data) -> void*;
  static auto ThreadMainAudio(void* data) -> int;
  static auto ThreadMainAudioP(void* data) -> void*;
  static auto ThreadMainBGDynamics(void* data) -> int;
  static auto ThreadMainBGDynamicsP(void* data) -> void*;
  static auto ThreadMainNetworkWrite(void* data) -> int;
  static auto ThreadMainNetworkWriteP(void* data) -> void*;
  static auto ThreadMainStdInput(void* data) -> int;
  static auto ThreadMainStdInputP(void* data) -> void*;
  static auto ThreadMainAssets(void* data) -> int;
  static auto ThreadMainAssetsP(void* data) -> void*;

  auto ThreadMain() -> int;
  void GetThreadMessages(std::list<ThreadMessage>* messages);
  void PushThreadMessage(const ThreadMessage& t);

  void RunPendingRunnables();
  void RunPauseCallbacks();
  void RunResumeCallbacks();

  bool bootstrapped_{};
  std::list<std::pair<Runnable*, bool*>> runnables_;
  std::list<Runnable*> pause_callbacks_;
  std::list<Runnable*> resume_callbacks_;
  std::condition_variable thread_message_cv_;
  std::mutex thread_message_mutex_;
  std::list<ThreadMessage> thread_messages_;
  std::condition_variable client_listener_cv_;
  std::mutex client_listener_mutex_;
  std::list<std::vector<char>> data_to_client_;
  TimerList timers_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_FOUNDATION_EVENT_LOOP_H_
