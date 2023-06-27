// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/event_loop.h"

#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/fatal_error.h"
#include "ballistica/shared/python/python.h"

namespace ballistica {

// Note: implicitly using core here so will fail spectacularly if that has
// not been imported by someone.
using core::g_base_soft;
using core::g_core;

EventLoop::EventLoop(EventLoopID identifier_in, ThreadSource source)
    : source_(source), identifier_(identifier_in) {
  switch (source_) {
    case ThreadSource::kCreate: {
      int (*func)(void*);
      void* (*funcp)(void*);
      switch (identifier_) {
        case EventLoopID::kLogic:
          func = ThreadMainLogic;
          funcp = ThreadMainLogicP;
          break;
        case EventLoopID::kAssets:
          func = ThreadMainAssets;
          funcp = ThreadMainAssetsP;
          break;
        case EventLoopID::kMain:
          // Shouldn't happen; this thread gets wrapped; not launched.
          throw Exception();
        case EventLoopID::kAudio:
          func = ThreadMainAudio;
          funcp = ThreadMainAudioP;
          break;
        case EventLoopID::kBGDynamics:
          func = ThreadMainBGDynamics;
          funcp = ThreadMainBGDynamicsP;
          break;
        case EventLoopID::kNetworkWrite:
          func = ThreadMainNetworkWrite;
          funcp = ThreadMainNetworkWriteP;
          break;
        case EventLoopID::kStdin:
          func = ThreadMainStdInput;
          funcp = ThreadMainStdInputP;
          break;
        default:
          throw Exception();
      }

        // Let 'er rip.

        // NOTE: Apple platforms have a default secondary thread stack size
        // of 512k which I've found to be insufficient in cases of heavy
        // Python recursion or large simulations. It sounds like Windows
        // and Android might have 1mb as default; let's try to standardize
        // on that across the board. Unfortunately we have to use pthreads
        // to get custom stack sizes; std::thread stupidly doesn't support it.

        // FIXME - move this to platform.
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS || BA_OSTYPE_LINUX
      pthread_attr_t attr;
      BA_PRECONDITION(pthread_attr_init(&attr) == 0);
      BA_PRECONDITION(pthread_attr_setstacksize(&attr, 1024 * 1024) == 0);
      pthread_t thread;
      pthread_create(&thread, &attr, funcp, this);
#else
      new std::thread(func, this);
#endif

      // Block until the thread is bootstrapped.
      // (maybe not necessary, but let's be cautious in case we'd
      // try to use things like thread_id before they're known).
      if (identifier_ == EventLoopID::kLogic) {
        g_core->LifecycleLog("logic thread bootstrap wait begin");
      }

      std::unique_lock lock(client_listener_mutex_);
      client_listener_cv_.wait(lock, [this] { return bootstrapped_; });

      if (identifier_ == EventLoopID::kLogic) {
        g_core->LifecycleLog("logic thread bootstrap wait end");
      }

      break;
    }
    case ThreadSource::kWrapMain: {
      // We've got no thread of our own to launch
      // so we run our setup stuff right here instead of off in some.
      assert(std::this_thread::get_id() == g_core->main_thread_id);
      thread_id_ = std::this_thread::get_id();

      // Set our own thread-id-to-name mapping.
      SetInternalThreadName("main");

      // Hmmm we might want to set our OS thread name here,
      // as we do for other threads? (SetCurrentThreadName).
      // However on linux that winds up being what we see in top/etc
      // so maybe shouldn't.
      break;
    }
  }
}

void EventLoop::SetInternalThreadName(const std::string& name) {
  assert(g_core);
  std::scoped_lock lock(g_core->thread_name_map_mutex);
  g_core->thread_name_map[std::this_thread::get_id()] = name;
}

void EventLoop::ClearCurrentThreadName() {
  assert(g_core);
  std::scoped_lock lock(g_core->thread_name_map_mutex);
  auto i = g_core->thread_name_map.find(std::this_thread::get_id());
  if (i != g_core->thread_name_map.end()) {
    g_core->thread_name_map.erase(i);
  }
}

// These are all exactly the same; its just a way to try and clarify
// in stack traces which thread is running in case it is not otherwise
// evident.

auto EventLoop::ThreadMainLogic(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain();
}

auto EventLoop::ThreadMainLogicP(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain();
  return nullptr;
}

auto EventLoop::ThreadMainAudio(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain();
}

auto EventLoop::ThreadMainAudioP(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain();
  return nullptr;
}

auto EventLoop::ThreadMainBGDynamics(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain();
}

auto EventLoop::ThreadMainBGDynamicsP(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain();
  return nullptr;
}

auto EventLoop::ThreadMainNetworkWrite(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain();
}

auto EventLoop::ThreadMainNetworkWriteP(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain();
  return nullptr;
}

auto EventLoop::ThreadMainStdInput(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain();
}

auto EventLoop::ThreadMainStdInputP(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain();
  return nullptr;
}

auto EventLoop::ThreadMainAssets(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain();
}

auto EventLoop::ThreadMainAssetsP(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain();
  return nullptr;
}

void EventLoop::PushSetPaused(bool paused) {
  assert(g_core);
  // Can be toggled from the main thread only.
  assert(std::this_thread::get_id() == g_core->main_thread_id);
  PushThreadMessage(ThreadMessage(paused ? ThreadMessage::Type::kPause
                                         : ThreadMessage::Type::kResume));
}

void EventLoop::WaitForNextEvent(bool single_cycle) {
  assert(g_core);

  // If we're running a single cycle we never stop to wait.
  if (single_cycle) {
    // Need to revisit this if we ever do single-cycle for
    // the gil-holding thread so we don't starve other Python threads.
    assert(!acquires_python_gil_);
    return;
  }

  // We also never wait if we have pending runnables; we want to run
  // things as soon as we can. We chew through all runnables at the end
  // of the loop so it might seem like there should never be any here,
  // but runnables can add other runnables that won't get processed until
  // the next time through.
  // BUG FIX: We now skip this if we're paused since we don't run runnables
  //  in that case. This was preventing us from releasing the GIL while paused
  //  (and I assume causing us to spin full-speed through the loop; ugh).
  // NOTE: It is theoretically possible for a runnable to add another runnable
  //  each time through the loop which would effectively starve the GIL as
  //  well; do we need to worry about that case?
  if (has_pending_runnables() && !paused_) {
    return;
  }

  // While we're waiting, allow other python threads to run.
  if (acquires_python_gil_) {
    g_core->python->ReleaseGIL();
  }

  // If we've got active timers, wait for messages with a timeout so we can
  // run the next timer payload.
  if (!paused_ && timers_.ActiveTimerCount() > 0) {
    millisecs_t apptime = g_core->GetAppTimeMillisecs();
    millisecs_t wait_time = timers_.TimeToNextExpire(apptime);
    if (wait_time > 0) {
      std::unique_lock<std::mutex> lock(thread_message_mutex_);
      if (thread_messages_.empty()) {
        thread_message_cv_.wait_for(lock, std::chrono::milliseconds(wait_time),
                                    [this] {
                                      // Go back to sleep on spurious wakeups
                                      // if we didn't wind up with any new
                                      // messages.
                                      return !thread_messages_.empty();
                                    });
      }
    }
  } else {
    // Not running timers; just wait indefinitely for the next message.
    std::unique_lock<std::mutex> lock(thread_message_mutex_);
    if (thread_messages_.empty()) {
      thread_message_cv_.wait(lock, [this] {
        // Go back to sleep on spurious wakeups
        // (if we didn't wind up with any new messages).
        return !(thread_messages_.empty());
      });
    }
  }

  if (acquires_python_gil_) {
    g_core->python->AcquireGIL();
  }
}

void EventLoop::LoopUpkeep(bool single_cycle) {
  assert(g_core);
  // Keep our autorelease pool clean on mac/ios
  // FIXME: Should define a CorePlatform::ThreadHelper or something
  //  so we don't have platform-specific code here.
#if BA_XCODE_BUILD
  // Let's not do autorelease pools when being called ad-hoc,
  // since in that case we're part of another run loop
  // (and its crashing on drain for some reason)
  if (!single_cycle) {
    if (auto_release_pool_) {
      g_core->platform->DrainAutoReleasePool(auto_release_pool_);
      auto_release_pool_ = nullptr;
    }
    auto_release_pool_ = g_core->platform->NewAutoReleasePool();
  }
#endif
}

auto EventLoop::RunEventLoop(bool single_cycle) -> int {
  assert(g_core);
  while (true) {
    LoopUpkeep(single_cycle);

    WaitForNextEvent(single_cycle);

    // Process all queued thread messages.
    std::list<ThreadMessage> thread_messages;
    GetThreadMessages(&thread_messages);
    for (auto& thread_message : thread_messages) {
      switch (thread_message.type) {
        case ThreadMessage::Type::kRunnable: {
          PushLocalRunnable(thread_message.runnable,
                            thread_message.completion_flag);
          break;
        }
        case ThreadMessage::Type::kShutdown: {
          done_ = true;
          break;
        }
        case ThreadMessage::Type::kPause: {
          assert(!paused_);
          RunPauseCallbacks();
          paused_ = true;
          last_pause_time_ = g_core->GetAppTimeMillisecs();
          messages_since_paused_ = 0;
          break;
        }
        case ThreadMessage::Type::kResume: {
          assert(paused_);
          RunResumeCallbacks();
          paused_ = false;
          break;
        }
        default: {
          throw Exception();
        }
      }

      if (done_) {
        break;
      }
    }

    if (!paused_) {
      timers_.Run(g_core->GetAppTimeMillisecs());
      RunPendingRunnables();
    }

    if (done_ || single_cycle) {
      break;
    }
  }
  return 0;
}

void EventLoop::GetThreadMessages(std::list<ThreadMessage>* messages) {
  assert(messages);
  assert(std::this_thread::get_id() == thread_id());

  // Make sure they passed an empty one in.
  assert(messages->empty());
  std::scoped_lock lock(thread_message_mutex_);
  if (!thread_messages_.empty()) {
    messages->swap(thread_messages_);
  }
}

auto EventLoop::ThreadMain() -> int {
  assert(g_core);
  try {
    assert(source_ == ThreadSource::kCreate);
    thread_id_ = std::this_thread::get_id();
    const char* name;
    const char* id_string;

    switch (identifier_) {
      case EventLoopID::kLogic:
        name = "logic";
        id_string = "ballistica logic";
        break;
      case EventLoopID::kStdin:
        name = "stdin";
        id_string = "ballistica stdin";
        break;
      case EventLoopID::kAssets:
        name = "assets";
        id_string = "ballistica assets";
        break;
      case EventLoopID::kFileOut:
        name = "fileout";
        id_string = "ballistica file-out";
        break;
      case EventLoopID::kMain:
        name = "main";
        id_string = "ballistica main";
        break;
      case EventLoopID::kAudio:
        name = "audio";
        id_string = "ballistica audio";
        break;
      case EventLoopID::kBGDynamics:
        name = "bgdynamics";
        id_string = "ballistica bg-dynamics";
        break;
      case EventLoopID::kNetworkWrite:
        name = "networkwrite";
        id_string = "ballistica network writing";
        break;
      default:
        throw Exception();
    }
    assert(name && id_string);
    SetInternalThreadName(name);
    g_core->platform->SetCurrentThreadName(id_string);

    // Mark ourself as bootstrapped and signal listeners so
    // anyone waiting for us to spin up can move along.
    bootstrapped_ = true;
    client_listener_cv_.notify_all();

    // Now just run our loop until we die.
    int result = RunEventLoop();

    ClearCurrentThreadName();
    return result;
  } catch (const std::exception& e) {
    auto error_msg = std::string("Unhandled exception in ")
                     + CurrentThreadName() + " thread:\n" + e.what();

    FatalError::ReportFatalError(error_msg, true);

    // Exiting the app via an exception leads to crash reports on various
    // platforms. If it seems we're not on an official live build then we'd
    // rather just exit cleanly with an error code and avoid polluting crash
    // report logs with reports from dev builds.
    bool try_to_exit_cleanly =
        !(g_base_soft && g_base_soft->IsUnmodifiedBlessedBuild());
    bool handled = FatalError::HandleFatalError(try_to_exit_cleanly, true);

    // Do the default thing if platform didn't handle it.
    if (!handled) {
      if (try_to_exit_cleanly) {
        exit(1);
      } else {
        throw;
      }
    }

    // Silence some lint complaints about always returning 0.
    if (explicit_bool(false)) {
      return 1;
    }
    return 0;
  }
}

void EventLoop::SetAcquiresPythonGIL() {
  assert(g_core);
  assert(!acquires_python_gil_);  // This should be called exactly once.
  assert(ThreadIsCurrent());
  acquires_python_gil_ = true;
  g_core->python->AcquireGIL();
}

// Explicitly kill the main thread.
void EventLoop::Quit() {
  assert(source_ == ThreadSource::kWrapMain);
  if (source_ == ThreadSource::kWrapMain) {
    done_ = true;
  }
}

EventLoop::~EventLoop() = default;

void EventLoop::LogThreadMessageTally(
    std::vector<std::pair<LogLevel, std::string>>* log_entries) {
  assert(g_core);
  // Prevent recursion.
  if (!writing_tally_) {
    writing_tally_ = true;

    std::unordered_map<std::string, int> tally;
    log_entries->emplace_back(std::make_pair(
        LogLevel::kError, "EventLoop message tally ("
                              + std::to_string(thread_messages_.size())
                              + " in list):"));
    for (auto&& m : thread_messages_) {
      std::string s;
      switch (m.type) {
        case ThreadMessage::Type::kShutdown:
          s += "kShutdown";
          break;
        case ThreadMessage::Type::kRunnable:
          s += "kRunnable";
          break;
        case ThreadMessage::Type::kPause:
          s += "kPause";
          break;
        case ThreadMessage::Type::kResume:
          s += "kResume";
          break;
        default:
          s += "UNKNOWN(" + std::to_string(static_cast<int>(m.type)) + ")";
          break;
      }
      if (m.type == ThreadMessage::Type::kRunnable) {
        std::string m_name =
            g_core->platform->DemangleCXXSymbol(typeid(*(m.runnable)).name());
        s += std::string(": ") + m_name;
      }
      auto j = tally.find(s);
      if (j == tally.end()) {
        tally[s] = 1;
      } else {
        tally[s]++;
      }
    }
    int entry = 1;
    for (auto&& i : tally) {
      log_entries->emplace_back(std::make_pair(
          LogLevel::kError, "  #" + std::to_string(entry++) + " ("
                                + std::to_string(i.second) + "x): " + i.first));
    }
    writing_tally_ = false;
  }
}

void EventLoop::PushThreadMessage(const ThreadMessage& t) {
  assert(g_core);
  // We don't want to make log calls while holding this mutex;
  // log calls acquire the GIL and if the GIL-holder (generally
  // the logic thread) is trying to send a thread message to the
  // thread doing the logging we would get deadlock.
  // So tally up any logs and send them after.
  std::vector<std::pair<LogLevel, std::string>> log_entries;
  {
    std::unique_lock lock(thread_message_mutex_);

    // Plop the data on to the list; we're assuming the mutex is locked.
    thread_messages_.push_back(t);

    // Debugging: show message count states.
    if (explicit_bool(false)) {
      static int one_off = 0;
      static int foo = 0;
      foo++;
      one_off++;

      // Show momemtary spikes.
      if (thread_messages_.size() > 100 && one_off > 100) {
        one_off = 0;
        foo = 999;
      }

      // Show count periodically.
      if ((std::this_thread::get_id() == g_core->main_thread_id) && foo > 100) {
        foo = 0;
        log_entries.emplace_back(
            LogLevel::kInfo,
            "MSG COUNT " + std::to_string(thread_messages_.size()));
      }
    }

    if (thread_messages_.size() > 1000) {
      static bool sent_error = false;
      if (!sent_error) {
        sent_error = true;
        log_entries.emplace_back(
            LogLevel::kError,
            "ThreadMessage list > 1000 in thread: " + CurrentThreadName());

        LogThreadMessageTally(&log_entries);
      }
    }

    // Prevent runaway mem usage if the list gets out of control.
    if (thread_messages_.size() > 10000) {
      FatalError("ThreadMessage list > 10000 in thread: "
                 + CurrentThreadName());
    }

    // Unlock thread-message list and inform thread that there's something
    // available.
  }
  thread_message_cv_.notify_all();

  // Now log anything we accumulated safely outside of the locked section.
  for (auto&& log_entry : log_entries) {
    Log(log_entry.first, log_entry.second);
  }
}

void EventLoop::SetThreadsPaused(bool paused) {
  assert(g_core);
  assert(std::this_thread::get_id() == g_core->main_thread_id);
  g_core->threads_paused = paused;
  for (auto&& i : g_core->pausable_event_loops) {
    i->PushSetPaused(paused);
  }
}

auto EventLoop::GetStillPausingThreads() -> std::vector<EventLoop*> {
  assert(g_core);
  std::vector<EventLoop*> threads;
  assert(std::this_thread::get_id() == g_core->main_thread_id);

  // Only return results if an actual pause is in effect.
  if (g_core->threads_paused) {
    for (auto&& i : g_core->pausable_event_loops) {
      if (!i->paused()) {
        threads.push_back(i);
      }
    }
  }
  return threads;
}

auto EventLoop::AreThreadsPaused() -> bool {
  assert(g_core);
  return g_core->threads_paused;
}

auto EventLoop::NewTimer(millisecs_t length, bool repeat,
                         const Object::Ref<Runnable>& runnable) -> Timer* {
  assert(g_core);
  assert(ThreadIsCurrent());
  assert(runnable.Exists());
  return timers_.NewTimer(g_core->GetAppTimeMillisecs(), length, 0,
                          repeat ? -1 : 0, runnable);
}

Timer* EventLoop::GetTimer(int id) {
  assert(ThreadIsCurrent());
  return timers_.GetTimer(id);
}

void EventLoop::DeleteTimer(int id) {
  assert(ThreadIsCurrent());
  timers_.DeleteTimer(id);
}

auto EventLoop::CurrentThreadName() -> std::string {
  if (g_core == nullptr) {
    return "unknown(not-yet-inited)";
  }
  {
    std::scoped_lock lock(g_core->thread_name_map_mutex);
    auto i = g_core->thread_name_map.find(std::this_thread::get_id());
    if (i != g_core->thread_name_map.end()) {
      return i->second;
    }
  }

  // Ask pthread for the thread name if we don't have one.
  // FIXME - move this to platform.
#if BA_OSTYPE_MACOS || BA_OSTYPE_IOS_TVOS || BA_OSTYPE_LINUX
  std::string name = "unknown (sys-name=";
  char buffer[256];
  int result = pthread_getname_np(pthread_self(), buffer, sizeof(buffer));
  if (result == 0) {
    name += std::string("\"") + buffer + "\")";
  } else {
    name += "<error " + std::to_string(result) + ">";
  }
  return name;
#else
  return "unknown";
#endif
}

void EventLoop::RunPendingRunnables() {
  // Pull all runnables off the list first (its possible for one of these
  // runnables to add more) and then process them.
  assert(std::this_thread::get_id() == thread_id());
  std::list<std::pair<Runnable*, bool*>> runnables;
  runnables_.swap(runnables);
  bool do_notify_listeners{};
  for (auto&& i : runnables) {
    i.first->Run();
    delete i.first;

    // If this runnable wanted to be flagged when done, set its flag
    // and make a note to wake all client listeners.
    if (i.second != nullptr) {
      *(i.second) = true;
      do_notify_listeners = true;
    }
  }
  if (do_notify_listeners) {
    client_listener_cv_.notify_all();
  }
}

void EventLoop::RunPauseCallbacks() {
  for (Runnable* i : pause_callbacks_) {
    i->Run();
  }
}

void EventLoop::RunResumeCallbacks() {
  for (Runnable* i : resume_callbacks_) {
    i->Run();
  }
}

void EventLoop::PushLocalRunnable(Runnable* runnable, bool* completion_flag) {
  assert(std::this_thread::get_id() == thread_id());
  runnables_.emplace_back(runnable, completion_flag);
}

void EventLoop::PushCrossThreadRunnable(Runnable* runnable,
                                        bool* completion_flag) {
  PushThreadMessage(EventLoop::ThreadMessage(
      EventLoop::ThreadMessage::Type::kRunnable, runnable, completion_flag));
}

void EventLoop::AddPauseCallback(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread_id());
  pause_callbacks_.push_back(runnable);
}

void EventLoop::AddResumeCallback(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread_id());
  resume_callbacks_.push_back(runnable);
}

void EventLoop::PushRunnable(Runnable* runnable) {
  assert(Object::IsValidUnmanagedObject(runnable));
  // If we're being called from withing our thread, just drop it in the list.
  // otherwise send it as a message to the other thread.
  if (std::this_thread::get_id() == thread_id()) {
    PushLocalRunnable(runnable, nullptr);
  } else {
    PushCrossThreadRunnable(runnable, nullptr);
  }
}

void EventLoop::PushRunnableSynchronous(Runnable* runnable) {
  bool complete{};
  bool* complete_ptr{&complete};
  if (std::this_thread::get_id() == thread_id()) {
    FatalError(
        "PushRunnableSynchronous called from target thread;"
        " would deadlock.");
  } else {
    PushCrossThreadRunnable(runnable, &complete);
  }

  if (identifier_ == EventLoopID::kLogic) {
    g_core->LifecycleLog("logic thread sync run push begin");
  }

  // Now listen until our completion flag gets set.
  std::unique_lock lock(client_listener_mutex_);
  client_listener_cv_.wait(lock, [complete_ptr] {
    // Go back to sleep on spurious wakeups
    // (if we're not actually complete yet).
    return *complete_ptr;
  });

  if (identifier_ == EventLoopID::kLogic) {
    g_core->LifecycleLog("logic thread sync run push end");
  }
}

auto EventLoop::CheckPushSafety() -> bool {
  if (std::this_thread::get_id() == thread_id()) {
    // behave the same as the thread-message safety check.
    return (runnables_.size() < kThreadMessageSafetyThreshold);
  } else {
    return CheckPushRunnableSafety();
  }
}
auto EventLoop::CheckPushRunnableSafety() -> bool {
  std::unique_lock lock(thread_message_mutex_);
  return thread_messages_.size() < kThreadMessageSafetyThreshold;
}

}  // namespace ballistica
