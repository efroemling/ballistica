// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/thread.h"

#include <map>

#include "ballistica/app/app.h"
#include "ballistica/core/fatal_error.h"
#include "ballistica/core/module.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

bool Thread::threads_paused_ = false;

void Thread::AddCurrentThreadName(const std::string& name) {
  std::lock_guard<std::mutex> lock(g_app_globals->thread_name_map_mutex);
  std::thread::id thread_id = std::this_thread::get_id();
  auto i = g_app_globals->thread_name_map.find(thread_id);
  std::string s;
  if (i != g_app_globals->thread_name_map.end()) {
    s = i->second;
  }
  if (!strstr(s.c_str(), name.c_str())) {
    if (s.empty()) {
      s = name;
    } else {
      s = s + "+" + name;
    }
  }
  g_app_globals->thread_name_map[std::this_thread::get_id()] = s;
}

void Thread::ClearCurrentThreadName() {
  std::lock_guard<std::mutex> lock(g_app_globals->thread_name_map_mutex);
  auto i = g_app_globals->thread_name_map.find(std::this_thread::get_id());
  if (i != g_app_globals->thread_name_map.end()) {
    g_app_globals->thread_name_map.erase(i);
  }
}

void Thread::UpdateMainThreadID() {
  auto current_id = std::this_thread::get_id();

  // This gets called a lot and it may happen before we are spun up,
  // so just ignore it in that case..
  if (g_app_globals) {
    g_app_globals->main_thread_id = current_id;
  }
  if (g_app) {
    g_app->thread()->set_thread_id(current_id);
  }
}

void Thread::KillModule(const Module& module) {
  for (auto i = modules_.begin(); i != modules_.end(); i++) {
    if (*i == &module) {
      delete *i;
      modules_.erase(i);
      return;
    }
  }
  throw Exception("Module not found on this thread");
}

void Thread::KillModules() {
  for (auto i : modules_) {
    delete i;
  }
  modules_.clear();
}

// These are all exactly the same, but by running different ones for
// different thread groups makes its easy to see which thread is which
// in profilers, backtraces, etc.
auto Thread::RunGameThread(void* data) -> int {
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

auto Thread::RunMediaThread(void* data) -> int {
  return static_cast<Thread*>(data)->ThreadMain();
}

void Thread::SetPaused(bool paused) {
  // Can be toggled from the main thread only.
  assert(std::this_thread::get_id() == g_app_globals->main_thread_id);
  PushThreadMessage(ThreadMessage(paused ? ThreadMessage::Type::kPause
                                         : ThreadMessage::Type::kResume));
}

void Thread::WaitForNextEvent(bool single_cycle) {
  // If we're running a single cycle we never stop to wait.
  if (single_cycle) {
    return;
  }

  // We also never wait if any of our modules have pending runnables.
  // (we run all existing runnables in each loop cycle, but one of those
  // may have enqueued more).
  for (auto&& i : modules_) {
    if (i->has_pending_runnables()) {
      return;
    }
  }

  // While we're waiting, allow other python threads to run.
  if (owns_python_) {
    g_python->ReleaseGIL();
  }

  // If we've got active timers, wait for messages with a timeout so we can
  // run the next timer payload.
  if ((!paused_) && timers_.active_timer_count() > 0) {
    millisecs_t real_time = GetRealTime();
    millisecs_t wait_time = timers_.GetTimeToNextExpire(real_time);
    if (wait_time > 0) {
      std::unique_lock<std::mutex> lock(thread_message_mutex_);
      if (thread_message_count_ == 0) {
        thread_message_cv_.wait_for(lock, std::chrono::milliseconds(wait_time),
                                    [this] {
                                      // Go back to sleep on spurious wakeups
                                      // if we didn't wind up with any new
                                      // messages.
                                      return (thread_message_count_ > 0);
                                    });
      }
    }
  } else {
    // Not running timers; just wait indefinitely for the next message.
    std::unique_lock<std::mutex> lock(thread_message_mutex_);
    if (thread_message_count_ == 0) {
      thread_message_cv_.wait(lock, [this] {
        // Go back to sleep on spurious wakeups
        // (if we didn't wind up with any new messages).
        return (thread_message_count_ > 0);
      });
    }
  }

  if (owns_python_) {
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
        case ThreadMessage::Type::kNewModule: {
          // Launch a new module and unlock.
          ModuleLauncher* tl;
          tl = static_cast<ModuleLauncher*>(thread_message.pval);
          tl->Launch(this);
          auto cmd =
              static_cast<uint32_t>(ThreadMessage::Type::kNewModuleConfirm);
          WriteToOwner(&cmd, sizeof(cmd));
          break;
        }
        case ThreadMessage::Type::kRunnable: {
          auto module_id = thread_message.ival;
          Module* t = GetModule(module_id);
          assert(t);
          auto e = static_cast<Runnable*>(thread_message.pval);

          // Add the event to our list.
          t->PushLocalRunnable(e);
          RunnablesWhilePausedSanityCheck(e);

          break;
        }
        case ThreadMessage::Type::kShutdown: {
          // Shutdown; die!
          done_ = true;
          break;
        }
        case ThreadMessage::Type::kResume: {
          assert(paused_);

          // Let all modules do pause-related stuff.
          for (auto&& i : modules_) {
            i->HandleThreadResume();
          }
          paused_ = false;
          break;
        }
        case ThreadMessage::Type::kPause: {
          assert(!paused_);

          // Let all modules do pause-related stuff.
          for (auto&& i : modules_) {
            i->HandleThreadPause();
          }
          paused_ = true;
          last_pause_time_ = GetRealTime();
          messages_since_paused_ = 0;
          break;
        }
        default: {
          throw Exception();
        }
      }

      // If the thread is going down.
      if (done_) {
        break;
      }
    }

    // Run timers && queued module runnables unless we're paused.
    if (!paused_) {
      // Run timers.
      timers_.Run(GetRealTime());

      // Run module-messages.
      for (auto& module_entry : modules_) {
        module_entry->RunPendingRunnables();
      }
    }
    if (done_ || single_cycle) {
      break;
    }
  }
  return 0;
}

void Thread::RunnablesWhilePausedSanityCheck(Runnable* e) {
  // We generally shouldn't be getting messages while paused..
  // (check both our pause-state and the global one; wanna ignore things
  // that might slip through if some just-unlocked thread msgs us but we
  // haven't been unlocked yet)

  // UPDATE - we are migrating away from distinct message classes and towards
  // LambdaRunnables for everything, which means that we can't easily
  // see details of what is coming through.  Disabling this check for now.
}

void Thread::GetThreadMessages(std::list<ThreadMessage>* messages) {
  assert(messages);
  assert(std::this_thread::get_id() == thread_id());

  // Make sure they passed an empty one in.
  assert(messages->empty());
  if (thread_message_count_ > 0) {
    std::unique_lock<std::mutex> lock(thread_message_mutex_);
    assert(thread_messages_.size() == thread_message_count_);
    messages->swap(thread_messages_);
    thread_message_count_ = 0;
  }
}

void Thread::WriteToOwner(const void* data, uint32_t size) {
  assert(std::this_thread::get_id() == thread_id());
  {
    std::unique_lock<std::mutex> lock(data_to_client_mutex_);
    data_to_client_.emplace_back(size);
    memcpy(&(data_to_client_.back()[0]), data, size);
  }
  data_to_client_cv_.notify_all();
}

Thread::Thread(ThreadIdentifier identifier_in, ThreadType type_in)
    : type_(type_in), identifier_(identifier_in) {
  switch (type_) {
    case ThreadType::kStandard: {
      // Lock down until the thread is up and running. It'll unlock us when
      // it's ready to go.
      int (*func)(void*);
      switch (identifier_) {
        case ThreadIdentifier::kGame:
          func = RunGameThread;
          break;
        case ThreadIdentifier::kMedia:
          func = RunMediaThread;
          break;
        case ThreadIdentifier::kMain:
          // Shouldn't happen; this thread gets wrapped; not launched.
          throw Exception();
        case ThreadIdentifier::kAudio:
          func = RunAudioThread;
          break;
        case ThreadIdentifier::kBGDynamics:
          func = RunBGDynamicThread;
          break;
        case ThreadIdentifier::kNetworkWrite:
          func = RunNetworkWriteThread;
          break;
        case ThreadIdentifier::kStdin:
          func = RunStdInputThread;
          break;
        default:
          throw Exception();
      }

      // Let 'er rip.
      thread_ = new std::thread(func, this);

      // The thread lets us know when its up and running.
      std::unique_lock<std::mutex> lock(data_to_client_mutex_);

      uint32_t cmd;
      ReadFromThread(&lock, &cmd, sizeof(cmd));
      assert(static_cast<ThreadMessage::Type>(cmd)
             == ThreadMessage::Type::kNewThreadConfirm);
      break;
    }
    case ThreadType::kMain: {
      // We've got no thread of our own to launch
      // so we run our setup stuff right here instead of off in some.
      assert(std::this_thread::get_id() == g_app_globals->main_thread_id);
      thread_id_ = std::this_thread::get_id();

      // Hmmm we might want to set our thread name here,
      // as we do for other threads?
      // However on linux that winds up being what we see in top/etc
      // so maybe shouldn't.
      break;
    }
  }
}

auto Thread::ThreadMain() -> int {
  try {
    assert(type_ == ThreadType::kStandard);
    thread_id_ = std::this_thread::get_id();

    const char* id_string;
    switch (identifier_) {
      case ThreadIdentifier::kGame:
        id_string = "ballistica game";
        break;
      case ThreadIdentifier::kStdin:
        id_string = "ballistica stdin";
        break;
      case ThreadIdentifier::kMedia:
        id_string = "ballistica media";
        break;
      case ThreadIdentifier::kFileOut:
        id_string = "ballistica file-out";
        break;
      case ThreadIdentifier::kMain:
        id_string = "ballistica main";
        break;
      case ThreadIdentifier::kAudio:
        id_string = "ballistica audio";
        break;
      case ThreadIdentifier::kBGDynamics:
        id_string = "ballistica bg-dynamics";
        break;
      case ThreadIdentifier::kNetworkWrite:
        id_string = "ballistica network writing";
        break;
      default:
        throw Exception();
    }
    g_platform->SetCurrentThreadName(id_string);

    // Send our owner a confirmation that we're alive.
    auto cmd = static_cast<uint32_t>(ThreadMessage::Type::kNewThreadConfirm);
    WriteToOwner(&cmd, sizeof(cmd));

    // Now just run our loop until we die.
    int result = RunEventLoop();

    KillModules();
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
    return 0;
  }
}

void Thread::SetOwnsPython() {
  owns_python_ = true;
  g_python->AcquireGIL();
}

// Explicitly kill the main thread.
void Thread::Quit() {
  assert(type_ == ThreadType::kMain);
  if (type_ == ThreadType::kMain) {
    done_ = true;
  }
}

Thread::~Thread() = default;

void Thread::LogThreadMessageTally() {
  // Prevent recursion.
  if (!writing_tally_) {
    writing_tally_ = true;

    std::map<std::string, int> tally;
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
        case ThreadMessage::Type::kNewModule:
          s += "kNewModule";
          break;
        case ThreadMessage::Type::kNewModuleConfirm:
          s += "kNewModuleConfirm";
          break;
        case ThreadMessage::Type::kNewThreadConfirm:
          s += "kNewThreadConfirm";
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
        // Runnable* e;
        // e = static_cast<Runnable*>(m.pval);
        {
          std::string m_name = g_platform->DemangleCXXSymbol(
              typeid(*(static_cast<Runnable*>(m.pval))).name());
          s += std::string(": ") + m_name;
        }
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

void Thread::PushThreadMessage(const ThreadMessage& t) {
  {
    std::unique_lock<std::mutex> lock(thread_message_mutex_);

    // Plop the data on to the list; we're assuming the mutex is locked.
    thread_messages_.push_back(t);

    // Keep our own count; apparently size() on an stl list involves
    // iterating.
    // FIXME: Actually I don't think this is the case anymore; should check.
    thread_message_count_++;
    assert(thread_message_count_ == thread_messages_.size());

    // Show message count states.
    if (explicit_bool(false)) {
      static int one_off = 0;
      static int foo = 0;
      foo++;
      one_off++;

      // Show momemtary spikes.
      if (thread_message_count_ > 100 && one_off > 100) {
        one_off = 0;
        foo = 999;
      }

      // Show count periodically.
      if ((std::this_thread::get_id() == g_app_globals->main_thread_id)
          && foo > 100) {
        foo = 0;
        Log("MSG COUNT " + std::to_string(thread_message_count_));
      }
    }

    if (thread_message_count_ > 1000) {
      static bool sent_error = false;
      if (!sent_error) {
        sent_error = true;
        Log("Error: ThreadMessage list > 1000 in thread: "
            + GetCurrentThreadName());
        LogThreadMessageTally();
      }
    }

    // Prevent runaway mem usage if the list gets out of control.
    if (thread_message_count_ > 10000) {
      throw Exception("KILLING APP: ThreadMessage list > 10000 in thread: "
                      + GetCurrentThreadName());
    }

    // Unlock thread-message list and inform thread that there's something
    // available.
  }
  thread_message_cv_.notify_all();
}

void Thread::ReadFromThread(std::unique_lock<std::mutex>* lock, void* buffer,
                            uint32_t size) {
  // Threads cant read from themselves.. could load to lock-deadlock.
  assert(std::this_thread::get_id() != thread_id());
  data_to_client_cv_.wait(*lock, [this] {
    // Go back to sleep on spurious wakeups
    // (if we didn't wind up with any new messages)
    return (!data_to_client_.empty());
  });

  // Read the oldest thing on our in-data list.
  assert(!data_to_client_.empty());
  assert(data_to_client_.front().size() == size);
  memcpy(buffer, &(data_to_client_.front()[0]), size);
  data_to_client_.pop_front();
}

void Thread::SetThreadsPaused(bool paused) {
  threads_paused_ = paused;
  for (auto&& i : g_app_globals->pausable_threads) {
    i->SetPaused(paused);
  }
}

auto Thread::AreThreadsPaused() -> bool { return threads_paused_; }

auto Thread::RegisterModule(const std::string& name, Module* module) -> int {
  AddCurrentThreadName(name);
  // This should assure we were properly launched.
  // (the ModuleLauncher will set the index to what ours will be)
  int index = static_cast<int>(modules_.size());
  // module_entries_.emplace_back(module, name, index);
  modules_.push_back(module);
  return index;
}

auto Thread::NewTimer(millisecs_t length, bool repeat,
                      const Object::Ref<Runnable>& runnable) -> Timer* {
  assert(IsCurrent());
  assert(runnable.exists());
  return timers_.NewTimer(GetRealTime(), length, 0, repeat ? -1 : 0, runnable);
}

auto Thread::GetCurrentThreadName() -> std::string {
  if (g_app_globals == nullptr) {
    return "unknown(not-yet-inited)";
  }
  {
    std::lock_guard<std::mutex> lock(g_app_globals->thread_name_map_mutex);
    auto i = g_app_globals->thread_name_map.find(std::this_thread::get_id());
    if (i != g_app_globals->thread_name_map.end()) {
      return i->second;
    }
  }
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

}  // namespace ballistica
