// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_THREAD_H_
#define BALLISTICA_CORE_THREAD_H_

#include <condition_variable>
#include <list>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/app/app_globals.h"
#include "ballistica/ballistica.h"
#include "ballistica/generic/timer_list.h"
#include "ballistica/platform/min_sdl.h"

namespace ballistica {

const int kThreadMessageSafetyThreadhold{500};

// A thread with a built-in event loop.
class Thread {
 public:
  explicit Thread(ThreadIdentifier id,
                  ThreadType type_in = ThreadType::kStandard);
  virtual ~Thread();

  /// Register a name for the current thread (should generally describe its
  /// purpose). If called multiple times, names will be combined with a '+'. ie:
  /// "graphics+animation+audio".
  void AddCurrentThreadName(const std::string& name);
  void ClearCurrentThreadName();

  static auto GetCurrentThreadName() -> std::string;

  /// Call this if the main thread changes.
  static void UpdateMainThreadID();

  static void SetThreadsPaused(bool enable);
  static auto AreThreadsPaused() -> bool;

  auto IsCurrent() const -> bool {
    return std::this_thread::get_id() == thread_id();
  }

  // Used to quit the main thread.
  void Quit();

  struct ModuleLauncher {
    virtual void Launch(Thread* g) = 0;
    virtual ~ModuleLauncher() = default;
  };

  template <class MODULETYPE>
  struct ModuleLauncherTemplate : public ModuleLauncher {
    void Launch(Thread* g) override { new MODULETYPE(g); }
  };

  template <class MODULETYPE, class ARGTYPE>
  struct ModuleLauncherArgTemplate : public ModuleLauncher {
    explicit ModuleLauncherArgTemplate(ARGTYPE arg_in) : arg(arg_in) {}
    ARGTYPE arg;
    void Launch(Thread* g) override { new MODULETYPE(g, arg); }
  };

  void SetOwnsPython();

  // Add a new module to a thread. This doesn't return anything. If you need
  // a pointer to the module, have it store itself somewhere in its constructor
  // or whatnot. Returning a pointer made it too easy to introduce race
  // conditions with the thread trying to access itself via this pointer
  // before it was set up.
  template <class THREADTYPE>
  void AddModule() {
    switch (type_) {
      case ThreadType::kStandard: {
        // Launching a module in the current thread: do it immediately.
        if (IsCurrent()) {
          ModuleLauncherTemplate<THREADTYPE> launcher;
          launcher.Launch(this);
        } else {
          // Launching a module in another thread;
          // send a module-launcher and wait for the confirmation.
          ModuleLauncherTemplate<THREADTYPE> launcher;
          ModuleLauncher* tl = &launcher;
          PushThreadMessage(
              ThreadMessage(ThreadMessage::Type::kNewModule, 0, tl));
          std::unique_lock<std::mutex> lock(data_to_client_mutex_);
          uint32_t cmd;
          ReadFromThread(&lock, &cmd, sizeof(cmd));
          assert(static_cast<ThreadMessage::Type>(cmd)
                 == ThreadMessage::Type::kNewModuleConfirm);
        }
        break;
      }
      case ThreadType::kMain: {
        assert(std::this_thread::get_id() == g_app_globals->main_thread_id);
        new THREADTYPE(this);
        break;
      }
      default: {
        throw Exception();
      }
    }
  }

  // An alternate version of AddModule that passes an argument along
  // to the thread's constructor.
  template <class THREADTYPE, class ARGTYPE>
  void AddModule(ARGTYPE arg) {
    switch (type_) {
      case ThreadType::kStandard: {
        // Launching a module in the current thread: do it immediately.
        if (IsCurrent()) {
          ModuleLauncherArgTemplate<THREADTYPE, ARGTYPE> launcher(arg);
          launcher.Launch(this);
        } else {
          // Launching a module in another thread;
          // send a module-launcher and wait for the confirmation.
          ModuleLauncherArgTemplate<THREADTYPE, ARGTYPE> launcher(arg);
          ModuleLauncher* tl = &launcher;
          PushThreadMessage(
              ThreadMessage(ThreadMessage::Type::kNewModule, 0, tl));

          std::unique_lock<std::mutex> lock(data_to_client_mutex_);

          uint32_t cmd;

          ReadFromThread(&lock, &cmd, sizeof(cmd));

          assert(static_cast<ThreadMessage::Type>(cmd)
                 == ThreadMessage::Type::kNewModuleConfirm);
        }
        break;
      }
      case ThreadType::kMain: {
        assert(std::this_thread::get_id() == g_app_globals->main_thread_id);
        new THREADTYPE(this, arg);
        break;
      }
      default: {
        throw Exception();
      }
    }
  }
  void KillModule(const Module& module);

  void SetPaused(bool paused);
  auto thread_id() const -> std::thread::id { return thread_id_; }

  // Needed in rare cases where we jump physical threads.
  // (Our 'main' thread on Android can switch under us as
  // rendering contexts are recreated in new threads/etc.)
  void set_thread_id(std::thread::id id) { thread_id_ = id; }

  auto RunEventLoop(bool single_cycle = false) -> int;
  auto identifier() const -> ThreadIdentifier { return identifier_; }

  // For use by modules.
  auto RegisterModule(const std::string& name, Module* module) -> int;
  void PushModuleRunnable(Runnable* runnable, int module_index) {
    PushThreadMessage(Thread::ThreadMessage(
        Thread::ThreadMessage::Type::kRunnable, module_index, runnable));
  }

  auto CheckPushModuleRunnableSafety() -> bool {
    // We first complain when we get to 1000 queued messages so
    // let's consider things unsafe when we're halfway there.
    return (thread_message_count_ < kThreadMessageSafetyThreadhold);
  }

  // Register a timer to run on the thread.
  auto NewTimer(millisecs_t length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> Timer*;

 private:
  struct ThreadMessage {
    enum class Type {
      kShutdown = 999,
      kRunnable,
      kNewModule,
      kNewModuleConfirm,
      kNewThreadConfirm,
      kPause,
      kResume
    };
    Type type;
    void* pval;
    int ival;
    explicit ThreadMessage(Type type_in, int ival_in = 0,
                           void* pval_in = nullptr)
        : type(type_in), ival(ival_in), pval(pval_in) {}
  };
  static void RunnablesWhilePausedSanityCheck(Runnable* r);
  void WaitForNextEvent(bool single_cycle);
  void LoopUpkeep(bool once);
  void LogThreadMessageTally();
  void ReadFromThread(std::unique_lock<std::mutex>* lock, void* buffer,
                      uint32_t size);

  void WriteToOwner(const void* data, uint32_t size);
  bool writing_tally_ = false;
  bool paused_ = false;
  millisecs_t last_pause_time_ = 0;
  int messages_since_paused_ = 0;
  millisecs_t last_paused_message_report_time_ = 0;
  bool done_ = false;
  ThreadType type_;
  int listen_sd_ = 0;
  std::thread::id thread_id_{};
  ThreadIdentifier identifier_ = ThreadIdentifier::kInvalid;
  millisecs_t last_complaint_time_ = 0;
  bool owns_python_ = false;

  // FIXME: Should generalize this to some sort of PlatformThreadData class.
#if BA_XCODE_BUILD
  void* auto_release_pool_ = nullptr;
#endif

  void KillModules();

  // These are all exactly the same, but by running different ones for
  // different thread groups makes its easy to see which thread is which
  // in profilers, backtraces, etc.
  static auto RunGameThread(void* data) -> int;
  static auto RunAudioThread(void* data) -> int;
  static auto RunBGDynamicThread(void* data) -> int;
  static auto RunNetworkWriteThread(void* data) -> int;
  static auto RunStdInputThread(void* data) -> int;
  static auto RunMediaThread(void* data) -> int;

  auto ThreadMain() -> int;
  std::thread* thread_;
  void GetThreadMessages(std::list<ThreadMessage>* messages);
  void PushThreadMessage(const ThreadMessage& t);
  std::condition_variable thread_message_cv_;
  std::mutex thread_message_mutex_;
  std::list<ThreadMessage> thread_messages_;
  int thread_message_count_ = 0;
  std::condition_variable data_to_client_cv_;
  std::mutex data_to_client_mutex_;
  std::list<std::vector<char> > data_to_client_;
  std::vector<Module*> modules_;
  auto GetModule(int id) -> Module* {
    assert(id >= 0 && id < static_cast<int>(modules_.size()));
    return modules_[id];
  }

  // Complete list of all timers created by this group's modules.
  TimerList timers_;
  static bool threads_paused_;
};

}  // namespace ballistica

#endif  // BALLISTICA_CORE_THREAD_H_
