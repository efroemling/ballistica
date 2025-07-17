// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/event_loop.h"

#include <Python.h>

#include <list>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/foundation/fatal_error.h"

namespace ballistica {

// Note: implicitly using core here so will fail spectacularly if that has
// not been imported by someone.
using core::g_base_soft;
using core::g_core;

EventLoop::EventLoop(EventLoopID identifier_in, ThreadSource source)
    : source_(source), identifier_(identifier_in) {
  switch (source_) {
    case ThreadSource::kCreate: {
      // IMPORTANT: We grab this lock *before* kicking off our thread, and
      // we hold it until we're actively listening for the completion
      // notification. The new thread waits until it can grab the lock
      // before notifying us of its completion, which ensures that we've
      // reached the waiting state before that notification arrives.
      // Otherwise it is possible for them to push out a notification
      // *before* we start waiting for it, which means we hang when we do
      // start listening and nothing comes in.
      std::unique_lock lock(client_listener_mutex_);

      int (*func)(void*);
      void* (*funcp)(void*);
      switch (identifier_) {
        case EventLoopID::kLogic:
          func = ThreadMainLogic_;
          funcp = ThreadMainLogicP_;
          break;
        case EventLoopID::kAssets:
          func = ThreadMainAssets_;
          funcp = ThreadMainAssetsP_;
          break;
        case EventLoopID::kMain:
          // Shouldn't happen; this thread gets wrapped; not launched.
          throw Exception();
        case EventLoopID::kAudio:
          func = ThreadMainAudio_;
          funcp = ThreadMainAudioP_;
          break;
        case EventLoopID::kBGDynamics:
          func = ThreadMainBGDynamics_;
          funcp = ThreadMainBGDynamicsP_;
          break;
        case EventLoopID::kNetworkWrite:
          func = ThreadMainNetworkWrite_;
          funcp = ThreadMainNetworkWriteP_;
          break;
        case EventLoopID::kStdin:
          func = ThreadMainStdInput_;
          funcp = ThreadMainStdInputP_;
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
#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS || BA_PLATFORM_LINUX
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
      client_listener_cv_.wait(lock, [this] { return bootstrapped_; });

      break;
    }
    case ThreadSource::kWrapCurrent: {
      BootstrapThread_();
      break;
    }
  }
}

// These are all exactly the same; its just a way to try and clarify
// in stack traces which thread is running in case it is not otherwise
// evident.

auto EventLoop::ThreadMainLogic_(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain_();
}

auto EventLoop::ThreadMainLogicP_(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain_();
  return nullptr;
}

auto EventLoop::ThreadMainAudio_(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain_();
}

auto EventLoop::ThreadMainAudioP_(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain_();
  return nullptr;
}

auto EventLoop::ThreadMainBGDynamics_(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain_();
}

auto EventLoop::ThreadMainBGDynamicsP_(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain_();
  return nullptr;
}

auto EventLoop::ThreadMainNetworkWrite_(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain_();
}

auto EventLoop::ThreadMainNetworkWriteP_(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain_();
  return nullptr;
}

auto EventLoop::ThreadMainStdInput_(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain_();
}

auto EventLoop::ThreadMainStdInputP_(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain_();
  return nullptr;
}

auto EventLoop::ThreadMainAssets_(void* data) -> int {
  return static_cast<EventLoop*>(data)->ThreadMain_();
}

auto EventLoop::ThreadMainAssetsP_(void* data) -> void* {
  static_cast<EventLoop*>(data)->ThreadMain_();
  return nullptr;
}

void EventLoop::PushSetSuspended(bool suspended) {
  assert(g_core);
  // Can be toggled from the main thread only.
  assert(std::this_thread::get_id() == g_core->main_thread_id());
  PushThreadMessage_(ThreadMessage_(suspended
                                        ? ThreadMessage_::Type::kSuspend
                                        : ThreadMessage_::Type::kUnsuspend));
}

void EventLoop::WaitForNextEvent_(bool single_cycle) {
  assert(g_core);

  // If we're running a single cycle we never stop to wait.
  if (single_cycle) {
    // Need to revisit this if we ever do single-cycle for the gil-holding
    // thread so we don't starve other Python threads.
    assert(!acquires_python_gil_);
    return;
  }

  // We also never wait if we have pending runnables; we want to run things
  // as soon as we can. We chew through all runnables at the end of the loop
  // so it might seem like there should never be any here, but runnables can
  // add other runnables that won't get processed until the next time
  // through.
  //
  // BUG FIX: We now skip this if we're suspended since we don't run
  //  runnables in that case. This was preventing us from releasing the GIL
  //  while suspended (and I assume causing us to spin full-speed through
  //  the loop; ugh).
  //
  // NOTE: It is theoretically possible for a runnable to add another
  //  runnable each time through the loop which would effectively starve the
  //  GIL as well; do we need to worry about that case?
  if (has_pending_runnables() && !suspended_) {
    return;
  }

  // While we're waiting, allow other python threads to run.
  if (acquires_python_gil_) {
    ReleaseGIL_();
  }

  // If we've got active timers, wait for messages with a timeout so we can
  // run the next timer payload.
  if (!suspended_ && timers_.ActiveTimerCount() > 0) {
    microsecs_t apptime = g_core->AppTimeMicrosecs();
    microsecs_t wait_time = timers_.TimeToNextExpire(apptime);
    if (wait_time > 0) {
      std::unique_lock<std::mutex> lock(thread_message_mutex_);
      if (thread_messages_.empty()) {
        thread_message_cv_.wait_for(lock, std::chrono::microseconds(wait_time),
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
    AcquireGIL_();
  }
}

// Note to self (Oct '23): can probably kill this at some point,
// but am still using some non-ARC objc stuff from logic thread
// so should keep it around just a bit longer just in case.
// void EventLoop::LoopUpkeep_(bool single_cycle) {
//  assert(g_core);
//  // Keep our autorelease pool clean on mac/ios
//  // FIXME: Should define a CorePlatform::ThreadHelper or something
//  //  so we don't have platform-specific code here.
// #if BA_XCODE_BUILD
//  // Let's not do autorelease pools when being called ad-hoc,
//  // since in that case we're part of another run loop
//  // (and its crashing on drain for some reason)
//  if (!single_cycle) {
//    if (auto_release_pool_) {
//      g_core->platform->DrainAutoReleasePool(auto_release_pool_);
//      auto_release_pool_ = nullptr;
//    }
//    auto_release_pool_ = g_core->platform->NewAutoReleasePool();
//  }
// #endif
//}

void EventLoop::RunToCompletion() { Run_(false); }
void EventLoop::RunSingleCycle() { Run_(true); }

void EventLoop::Run_(bool single_cycle) {
  assert(g_core);
  while (true) {
    // LoopUpkeep_(single_cycle);

    WaitForNextEvent_(single_cycle);

    // Process all queued thread messages.
    std::list<ThreadMessage_> thread_messages;
    GetThreadMessages_(&thread_messages);
    for (auto& thread_message : thread_messages) {
      switch (thread_message.type) {
        case ThreadMessage_::Type::kRunnable: {
          PushLocalRunnable_(thread_message.runnable,
                             thread_message.completion_flag);
          break;
        }
        case ThreadMessage_::Type::kShutdown: {
          done_ = true;
          break;
        }
        case ThreadMessage_::Type::kSuspend: {
          assert(!suspended_);
          RunSuspendCallbacks_();
          suspended_ = true;
          break;
        }
        case ThreadMessage_::Type::kUnsuspend: {
          assert(suspended_);
          RunUnsuspendCallbacks_();
          suspended_ = false;
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

    if (!suspended_) {
      timers_.Run(g_core->AppTimeMicrosecs());
      RunPendingRunnables_();
    }

    if (done_ || single_cycle) {
      break;
    }
  }
}

void EventLoop::GetThreadMessages_(std::list<ThreadMessage_>* messages) {
  assert(messages);
  assert(std::this_thread::get_id() == thread_id());

  // Make sure they passed an empty one in.
  assert(messages->empty());
  std::scoped_lock lock(thread_message_mutex_);
  if (!thread_messages_.empty()) {
    messages->swap(thread_messages_);
  }
}

void EventLoop::BootstrapThread_() {
  assert(!bootstrapped_);
  assert(g_core);
  thread_id_ = std::this_thread::get_id();

  switch (identifier_) {
    case EventLoopID::kLogic:
      name_ = "logic";
      break;
    case EventLoopID::kStdin:
      name_ = "stdin";
      break;
    case EventLoopID::kAssets:
      name_ = "assets";
      break;
    case EventLoopID::kFileOut:
      name_ = "fileout";
      break;
    case EventLoopID::kMain:
      name_ = "main";
      break;
    case EventLoopID::kAudio:
      name_ = "audio";
      break;
    case EventLoopID::kBGDynamics:
      name_ = "bgdynamics";
      break;
    case EventLoopID::kNetworkWrite:
      name_ = "networkwrite";
      break;
    default:
      throw Exception();
  }
  assert(!name_.empty());
  g_core->RegisterThread(name_);
  bootstrapped_ = true;
}

auto EventLoop::ThreadMain_() -> int {
  assert(g_core);
  try {
    assert(source_ == ThreadSource::kCreate);

    BootstrapThread_();

    {
      // Momentarily grab this lock. This pauses if need be until whoever
      // launched us releases their lock, which means they're now actively
      // waiting for our notification. If we skipped this, it would be
      // possible to zip through and send the notification before they
      // start listening for it which would lead to a hang.
      std::scoped_lock lock(client_listener_mutex_);
    }
    client_listener_cv_.notify_all();

    RunToCompletion();

    g_core->UnregisterThread();
    return 0;
  } catch (const std::exception& e) {
    auto error_msg = std::string("Unhandled exception in ")
                     + g_core->CurrentThreadName() + " thread:\n" + e.what();

    FatalErrorHandling::ReportFatalError(error_msg, true);

    // Exiting the app via an exception leads to crash reports on various
    // platforms. If it seems we're not on an official live build then we'd
    // rather just exit cleanly with an error code and avoid polluting crash
    // report logs with reports from dev builds.
    bool try_to_exit_cleanly =
        !(g_base_soft && g_base_soft->IsUnmodifiedBlessedBuild());

    bool handled =
        FatalErrorHandling::HandleFatalError(try_to_exit_cleanly, true);

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
  AcquireGIL_();
}

// Explicitly kill the main thread.
void EventLoop::Exit() { done_ = true; }

EventLoop::~EventLoop() = default;

void EventLoop::LogThreadMessageTally_(
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
        case ThreadMessage_::Type::kShutdown:
          s += "kShutdown";
          break;
        case ThreadMessage_::Type::kRunnable:
          s += "kRunnable";
          break;
        case ThreadMessage_::Type::kSuspend:
          s += "kSuspend";
          break;
        case ThreadMessage_::Type::kUnsuspend:
          s += "kUnsuspend";
          break;
        default:
          s += "UNKNOWN(" + std::to_string(static_cast<int>(m.type)) + ")";
          break;
      }
      if (m.type == ThreadMessage_::Type::kRunnable) {
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

void EventLoop::PushThreadMessage_(const ThreadMessage_& t) {
  assert(g_core);
  // We don't want to make log calls while holding this mutex;
  // log calls acquire the GIL and if the GIL-holder (generally
  // the logic thread) is trying to send a thread message to the
  // thread doing the logging we would get deadlock.
  // So tally up any logs and send them after.
  std::vector<std::pair<LogLevel, std::string>> log_entries;
  {
    std::scoped_lock lock(thread_message_mutex_);

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
      if ((std::this_thread::get_id() == g_core->main_thread_id())
          && foo > 100) {
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
            LogLevel::kError, "ThreadMessage list > 1000 in thread: " + name_);

        LogThreadMessageTally_(&log_entries);
      }
    }

    // Prevent runaway mem usage if the list gets out of control.
    if (thread_messages_.size() > 10000) {
      FatalError("ThreadMessage list > 10000 in thread: " + name_);
    }

    // Unlock thread-message list and inform thread that there's something
    // available.
  }
  thread_message_cv_.notify_all();

  // Now log anything we accumulated safely outside of the locked section.
  for (auto&& log_entry : log_entries) {
    g_core->logging->Log(LogName::kBa, log_entry.first, log_entry.second);
  }
}

void EventLoop::SetEventLoopsSuspended(bool suspended) {
  assert(g_core);
  assert(std::this_thread::get_id() == g_core->main_thread_id());
  g_core->set_event_loops_suspended(suspended);
  for (auto&& i : g_core->suspendable_event_loops) {
    i->PushSetSuspended(suspended);
  }
}

auto EventLoop::GetStillSuspendingEventLoops() -> std::vector<EventLoop*> {
  assert(g_core);
  std::vector<EventLoop*> event_loops;
  assert(std::this_thread::get_id() == g_core->main_thread_id());

  // Only return results if an actual suspend is in effect.
  if (g_core->event_loops_suspended()) {
    for (auto&& i : g_core->suspendable_event_loops) {
      if (!i->suspended()) {
        event_loops.push_back(i);
      }
    }
  }
  return event_loops;
}

auto EventLoop::AreEventLoopsSuspended() -> bool {
  assert(g_core);
  return g_core->event_loops_suspended();
}

auto EventLoop::NewTimer(microsecs_t length, bool repeat, Runnable* runnable)
    -> Timer* {
  assert(g_core);
  assert(ThreadIsCurrent());
  assert(Object::IsValidManagedObject(runnable));
  return timers_.NewTimer(g_core->AppTimeMicrosecs(), length, 0,
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

void EventLoop::RunPendingRunnables_() {
  // Pull all runnables off the list first (its possible for one of these
  // runnables to add more) and then process them.
  assert(std::this_thread::get_id() == thread_id());
  std::list<std::pair<Runnable*, bool*>> runnables;
  runnables_.swap(runnables);
  bool do_notify_listeners{};
  for (auto&& i : runnables) {
    i.first->RunAndLogErrors();
    delete i.first;

    // If this runnable wanted to be flagged when done, set its flag and
    // make a note to wake all client listeners.
    if (i.second != nullptr) {
      *(i.second) = true;
      do_notify_listeners = true;
    }
  }
  if (do_notify_listeners) {
    {
      // Momentarily grab this lock. This ensures that whoever pushed us is
      // now actively waiting for completion notification. If we skipped
      // this it would be possible to notify before they start listening
      // which leads to a hang.
      std::scoped_lock lock(client_listener_mutex_);
    }
    client_listener_cv_.notify_all();
  }
}

void EventLoop::RunSuspendCallbacks_() {
  for (Runnable* i : suspend_callbacks_) {
    i->RunAndLogErrors();
  }
}

void EventLoop::RunUnsuspendCallbacks_() {
  for (Runnable* i : unsuspend_callbacks_) {
    i->RunAndLogErrors();
  }
}

void EventLoop::PushLocalRunnable_(Runnable* runnable, bool* completion_flag) {
  assert(std::this_thread::get_id() == thread_id());
  runnables_.emplace_back(runnable, completion_flag);
}

void EventLoop::PushCrossThreadRunnable_(Runnable* runnable,
                                         bool* completion_flag) {
  PushThreadMessage_(EventLoop::ThreadMessage_(
      EventLoop::ThreadMessage_::Type::kRunnable, runnable, completion_flag));
}

void EventLoop::AddSuspendCallback(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread_id());
  suspend_callbacks_.push_back(runnable);
}

void EventLoop::AddUnsuspendCallback(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread_id());
  unsuspend_callbacks_.push_back(runnable);
}

void EventLoop::PushRunnable(Runnable* runnable) {
  assert(Object::IsValidUnmanagedObject(runnable));
  // If we're being called from withing our thread, just drop it in the
  // list. otherwise send it as a message to the other thread.
  if (std::this_thread::get_id() == thread_id()) {
    PushLocalRunnable_(runnable, nullptr);
  } else {
    PushCrossThreadRunnable_(runnable, nullptr);
  }
}

void EventLoop::PushRunnableSynchronous(Runnable* runnable) {
  bool complete{};
  bool* complete_ptr{&complete};

  // IMPORTANT: We grab this lock *before* pushing our runnable, and we hold
  // it until we're actively listening for the completion notification. The
  // receiver also grabs the lock before notifying us, which ensures that
  // we've reached the waiting state before the notification happens.
  // Otherwise it is possible for them to push out a notification before we
  // start waiting for it, which means we hang when we do start listening
  // and nothing comes in.
  std::unique_lock lock(client_listener_mutex_);

  if (std::this_thread::get_id() == thread_id()) {
    FatalError(
        "PushRunnableSynchronous called from target thread;"
        " would deadlock.");
  } else {
    PushCrossThreadRunnable_(runnable, &complete);
  }

  // Now listen until our completion flag gets set.
  client_listener_cv_.wait(lock, [complete_ptr] {
    // Go back to sleep on spurious wakeups (if we're not actually complete
    // yet).
    return *complete_ptr;
  });
}

auto EventLoop::CheckPushSafety() -> bool {
  if (std::this_thread::get_id() == thread_id()) {
    // Behave the same as the thread-message safety check.
    return (runnables_.size() < kThreadMessageSafetyThreshold);
  } else {
    return CheckPushRunnableSafety_();
  }
}
auto EventLoop::CheckPushRunnableSafety_() -> bool {
  std::scoped_lock lock(thread_message_mutex_);

  auto have_space{thread_messages_.size() < kThreadMessageSafetyThreshold};

  // If we've hit the safety threshold, log the traceback once so we can
  // hopefully fix the problem at the call site instead of dropping calls.
  if (!have_space) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE(
        "CheckPushSafety threshold reached; are you calling something too "
        "much?");
  }
  return have_space;
}

void EventLoop::AcquireGIL_() {
  assert(g_base_soft && g_base_soft->InLogicThread());
  auto debug_timing{g_core->core_config().debug_timing};
  millisecs_t startmillisecs{
      debug_timing ? core::CorePlatform::TimeMonotonicMillisecs() : 0};

  if (py_thread_state_) {
    PyEval_RestoreThread(py_thread_state_);
    py_thread_state_ = nullptr;
  }

  if (debug_timing) {
    auto duration{core::CorePlatform::TimeMonotonicMillisecs()
                  - startmillisecs};
    if (duration > (1000 / 120)) {
      g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                           "GIL acquire took too long ("
                               + std::to_string(duration) + " millisecs).");
    }
  }
}

void EventLoop::ReleaseGIL_() {
  assert(g_base_soft && g_base_soft->InLogicThread());
  assert(py_thread_state_ == nullptr);
  py_thread_state_ = PyEval_SaveThread();
}

}  // namespace ballistica
