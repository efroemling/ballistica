// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/thread.h"

#include "ballistica/app/app_flavor.h"
#include "ballistica/core/fatal_error.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

void Thread::SetInternalThreadName(const std::string& name) {
  std::scoped_lock lock(g_app->thread_name_map_mutex);
  g_app->thread_name_map[std::this_thread::get_id()] = name;
}

void Thread::ClearCurrentThreadName() {
  std::scoped_lock lock(g_app->thread_name_map_mutex);
  auto i = g_app->thread_name_map.find(std::this_thread::get_id());
  if (i != g_app->thread_name_map.end()) {
    g_app->thread_name_map.erase(i);
  }
}

void Thread::UpdateMainThreadID() {
  auto current_id = std::this_thread::get_id();

  // This gets called a lot and it may happen before we are spun up,
  // so just ignore it in that case..
  if (g_app) {
    g_app->main_thread_id = current_id;
  }
  if (g_app_flavor) {
    g_app_flavor->thread()->set_thread_id(current_id);
  }
}

// These are all exactly the same; its just a way to try and clarify
// in stack traces which thread is running in case it is not otherwise
// evident.

auto Thread::RunLogicThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

auto Thread::RunAudioThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

auto Thread::RunBGDynamicThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

auto Thread::RunNetworkWriteThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

auto Thread::RunStdInputThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

auto Thread::RunAssetsThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

void Thread::SetPaused(bool paused) {
  // Can be toggled from the main thread only.
  assert(std::this_thread::get_id() == g_app->main_thread_id);
  PushThreadMessage(ThreadMessage(paused ? ThreadMessage::Type::kPause
                                         : ThreadMessage::Type::kResume));
}

void Thread::WaitForNextEvent(bool single_cycle) {
  // If we're running a single cycle we never stop to wait.
  if (single_cycle) {
    return;
  }

  // We also never wait if we have pending runnables.
  // (we run all existing runnables in each loop cycle, but one of those
  // may have enqueued more).
  if (has_pending_runnables()) {
    return;
  }

  // While we're waiting, allow other python threads to run.
  if (acquires_python_gil_) {
    g_python->ReleaseGIL();
  }

  // If we've got active timers, wait for messages with a timeout so we can
  // run the next timer payload.
  if (!paused_ && timers_.active_timer_count() > 0) {
    millisecs_t real_time = GetRealTime();
    millisecs_t wait_time = timers_.GetTimeToNextExpire(real_time);
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
    g_python->AcquireGIL();
  }
}

void Thread::LoopUpkeep(bool single_cycle) {
  // Keep our autorelease pool clean on mac/ios
  // FIXME: Should define a Platform::ThreadHelper or something
  //  so we don't have platform-specific code here.
#if BA_XCODE_BUILD
  // Let's not do autorelease pools when being called ad-hoc,
  // since in that case we're part of another run loop
  // (and its crashing on drain for some reason)
  if (!single_cycle) {
    if (auto_release_pool_) {
      g_platform->DrainAutoReleasePool(auto_release_pool_);
      auto_release_pool_ = nullptr;
    }
    auto_release_pool_ = g_platform->NewAutoReleasePool();
  }
#endif
}

auto Thread::RunEventLoop(bool single_cycle) -> int {
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
          last_pause_time_ = GetRealTime();
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
      timers_.Run(GetRealTime());
      RunPendingRunnables();
    }

    if (done_ || single_cycle) {
      break;
    }
  }
  return 0;
}

void Thread::GetThreadMessages(std::list<ThreadMessage>* messages) {
  assert(messages);
  assert(std::this_thread::get_id() == thread_id());

  // Make sure they passed an empty one in.
  assert(messages->empty());
  std::scoped_lock lock(thread_message_mutex_);
  if (!thread_messages_.empty()) {
    messages->swap(thread_messages_);
  }
}

Thread::Thread(ThreadTag identifier_in, ThreadSource source)
    : source_(source), identifier_(identifier_in) {
  switch (source_) {
    case ThreadSource::kCreate: {
      int (*func)(void*);
      switch (identifier_) {
        case ThreadTag::kLogic:
          func = RunLogicThread;
          break;
        case ThreadTag::kAssets:
          func = RunAssetsThread;
          break;
        case ThreadTag::kMain:
          // Shouldn't happen; this thread gets wrapped; not launched.
          throw Exception();
        case ThreadTag::kAudio:
          func = RunAudioThread;
          break;
        case ThreadTag::kBGDynamics:
          func = RunBGDynamicThread;
          break;
        case ThreadTag::kNetworkWrite:
          func = RunNetworkWriteThread;
          break;
        case ThreadTag::kStdin:
          func = RunStdInputThread;
          break;
        default:
          throw Exception();
      }

      // Let 'er rip.
      thread_ = new std::thread(func, this);

      // Block until the thread is bootstrapped.
      // (maybe not necessary, but let's be cautious in case we'd
      // try to use things like thread_id before they're known).
      std::unique_lock lock(client_listener_mutex_);
      client_listener_cv_.wait(lock, [this] { return bootstrapped_; });

      break;
    }
    case ThreadSource::kWrapMain: {
      // We've got no thread of our own to launch
      // so we run our setup stuff right here instead of off in some.
      assert(std::this_thread::get_id() == g_app->main_thread_id);
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

auto Thread::ThreadMain() -> int {
  try {
    assert(source_ == ThreadSource::kCreate);
    thread_id_ = std::this_thread::get_id();
    const char* name;
    const char* id_string;

    switch (identifier_) {
      case ThreadTag::kLogic:
        name = "logic";
        id_string = "ballistica logic";
        break;
      case ThreadTag::kStdin:
        name = "stdin";
        id_string = "ballistica stdin";
        break;
      case ThreadTag::kAssets:
        name = "assets";
        id_string = "ballistica assets";
        break;
      case ThreadTag::kFileOut:
        name = "fileout";
        id_string = "ballistica file-out";
        break;
      case ThreadTag::kMain:
        name = "main";
        id_string = "ballistica main";
        break;
      case ThreadTag::kAudio:
        name = "audio";
        id_string = "ballistica audio";
        break;
      case ThreadTag::kBGDynamics:
        name = "bgdynamics";
        id_string = "ballistica bg-dynamics";
        break;
      case ThreadTag::kNetworkWrite:
        name = "networkwrite";
        id_string = "ballistica network writing";
        break;
      default:
        throw Exception();
    }
    assert(name && id_string);
    SetInternalThreadName(name);
    g_platform->SetCurrentThreadName(id_string);

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
                     + GetCurrentThreadName() + " thread:\n" + e.what();

    FatalError::ReportFatalError(error_msg, true);
    bool exit_cleanly = !IsUnmodifiedBlessedBuild();
    bool handled = FatalError::HandleFatalError(exit_cleanly, true);

    // Do the default thing if platform didn't handle it.
    if (!handled) {
      if (exit_cleanly) {
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

void Thread::SetAcquiresPythonGIL() {
  assert(!acquires_python_gil_);  // This should be called exactly once.
  assert(IsCurrent());
  acquires_python_gil_ = true;
  g_python->AcquireGIL();
}

// Explicitly kill the main thread.
void Thread::Quit() {
  assert(source_ == ThreadSource::kWrapMain);
  if (source_ == ThreadSource::kWrapMain) {
    done_ = true;
  }
}

Thread::~Thread() = default;

#pragma clang diagnostic push
#pragma ide diagnostic ignored "ConstantConditionsOC"

void Thread::LogThreadMessageTally() {
  // Prevent recursion.
  if (!writing_tally_) {
    writing_tally_ = true;

    std::unordered_map<std::string, int> tally;
    Log("Thread message tally (" + std::to_string(thread_messages_.size())
        + " in list):");
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
            g_platform->DemangleCXXSymbol(typeid(*(m.runnable)).name());
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
      Log("  #" + std::to_string(entry++) + " (" + std::to_string(i.second)
          + "x): " + i.first);
    }
    writing_tally_ = false;
  }
}
#pragma clang diagnostic pop

void Thread::PushThreadMessage(const ThreadMessage& t) {
  {
    std::unique_lock<std::mutex> lock(thread_message_mutex_);

    // Plop the data on to the list; we're assuming the mutex is locked.
    thread_messages_.push_back(t);

    // Keep our own count; apparently size() on an stl list involves iterating.
    // FIXME: Actually I don't think this is the case anymore; should check.

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
      if ((std::this_thread::get_id() == g_app->main_thread_id) && foo > 100) {
        foo = 0;
        Log("MSG COUNT " + std::to_string(thread_messages_.size()));
      }
    }

    if (thread_messages_.size() > 1000) {
      static bool sent_error = false;
      if (!sent_error) {
        sent_error = true;
        Log("Error: ThreadMessage list > 1000 in thread: "
            + GetCurrentThreadName());
        LogThreadMessageTally();
      }
    }

    // Prevent runaway mem usage if the list gets out of control.
    if (thread_messages_.size() > 10000) {
      FatalError("ThreadMessage list > 10000 in thread: "
                 + GetCurrentThreadName());
    }

    // Unlock thread-message list and inform thread that there's something
    // available.
  }
  thread_message_cv_.notify_all();
}

void Thread::SetThreadsPaused(bool paused) {
  g_app->threads_paused = paused;
  for (auto&& i : g_app->pausable_threads) {
    i->SetPaused(paused);
  }
}

auto Thread::AreThreadsPaused() -> bool { return g_app->threads_paused; }

auto Thread::NewTimer(millisecs_t length, bool repeat,
                      const Object::Ref<Runnable>& runnable) -> Timer* {
  assert(IsCurrent());
  assert(runnable.exists());
  return timers_.NewTimer(GetRealTime(), length, 0, repeat ? -1 : 0, runnable);
}

auto Thread::GetCurrentThreadName() -> std::string {
  if (g_app == nullptr) {
    return "unknown(not-yet-inited)";
  }
  {
    std::scoped_lock lock(g_app->thread_name_map_mutex);
    auto i = g_app->thread_name_map.find(std::this_thread::get_id());
    if (i != g_app->thread_name_map.end()) {
      return i->second;
    }
  }

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

void Thread::RunPendingRunnables() {
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

void Thread::RunPauseCallbacks() {
  for (Runnable* i : pause_callbacks_) {
    i->Run();
  }
}

void Thread::RunResumeCallbacks() {
  for (Runnable* i : resume_callbacks_) {
    i->Run();
  }
}

void Thread::PushLocalRunnable(Runnable* runnable, bool* completion_flag) {
  assert(std::this_thread::get_id() == thread_id());
  runnables_.push_back(std::make_pair(runnable, completion_flag));
}

void Thread::PushCrossThreadRunnable(Runnable* runnable,
                                     bool* completion_flag) {
  PushThreadMessage(Thread::ThreadMessage(
      Thread::ThreadMessage::Type::kRunnable, runnable, completion_flag));
}

void Thread::AddPauseCallback(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread_id());
  pause_callbacks_.push_back(runnable);
}

void Thread::AddResumeCallback(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread_id());
  resume_callbacks_.push_back(runnable);
}

void Thread::PushRunnable(Runnable* runnable) {
  // If we're being called from withing our thread, just drop it in the list.
  // otherwise send it as a message to the other thread.
  if (std::this_thread::get_id() == thread_id()) {
    PushLocalRunnable(runnable, nullptr);
  } else {
    PushCrossThreadRunnable(runnable, nullptr);
  }
}

void Thread::PushRunnableSynchronous(Runnable* runnable) {
  bool complete{};
  bool* complete_ptr{&complete};
  if (std::this_thread::get_id() == thread_id()) {
    FatalError(
        "PushRunnableSynchronous called from target thread;"
        " would deadlock.");
  } else {
    PushCrossThreadRunnable(runnable, &complete);
  }

  // Now listen until our completion flag gets set.
  std::unique_lock lock(client_listener_mutex_);
  client_listener_cv_.wait(lock, [complete_ptr] {
    // Go back to sleep on spurious wakeups
    // (if we're not actually complete yet).
    return *complete_ptr;
  });
}

auto Thread::CheckPushSafety() -> bool {
  if (std::this_thread::get_id() == thread_id()) {
    // behave the same as the thread-message safety check.
    return (runnables_.size() < kThreadMessageSafetyThreshold);
  } else {
    return CheckPushRunnableSafety();
  }
}
auto Thread::CheckPushRunnableSafety() -> bool {
  std::scoped_lock lock(client_listener_mutex_);

  // We first complain when we get to 1000 queued messages so
  // let's consider things unsafe when we're halfway there.
  return (thread_messages_.size() < kThreadMessageSafetyThreshold);
}

}  // namespace ballistica
