// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/core/object.h"

#include <algorithm>
#include <map>
#include <mutex>
#include <string>
#include <utility>

#include "ballistica/app/app_globals.h"
#include "ballistica/generic/utils.h"
#include "ballistica/platform/min_sdl.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

void Object::PrintObjects() {
#if BA_DEBUG_BUILD
  std::string s;
  {
    std::lock_guard<std::mutex> lock(g_app_globals->object_list_mutex);
    s = std::to_string(g_app_globals->object_count) + " Objects at time "
        + std::to_string(GetRealTime()) + ";";

    if (explicit_bool(true)) {
      std::map<std::string, int> obj_map;

      // Tally up counts for all types.
      int count = 0;
      for (Object* o = g_app_globals->object_list_first; o != nullptr;
           o = o->object_next_) {
        count++;
        std::string obj_name = o->GetObjectTypeName();
        auto i = obj_map.find(obj_name);
        if (i == obj_map.end()) {
          obj_map[obj_name] = 1;
        } else {
          // Getting complaints that 'second' is unused, but we sort and print
          // using this value like 10 lines down. Hmmm.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnusedValue"
          i->second++;
#pragma clang diagnostic pop
        }
      }

      // Now sort them by count and print.
      std::vector<std::pair<int, std::string> > sorted;
      sorted.reserve(obj_map.size());
      for (auto&& i : obj_map) {
        sorted.emplace_back(i.second, i.first);
      }
      std::sort(sorted.begin(), sorted.end());
      for (auto&& i : sorted) {
        s += "\n   " + std::to_string(i.first) + ": " + i.second;
      }
      assert(count == g_app_globals->object_count);
    }
  }
  Log(s);
#else
  Log("PrintObjects() only functions in debug builds.");
#endif  // BA_DEBUG_BUILD
}

Object::Object() {
#if BA_DEBUG_BUILD
  // Mark when we were born.
  object_birth_time_ = GetRealTime();

  // Add ourself to the global object list.
  std::lock_guard<std::mutex> lock(g_app_globals->object_list_mutex);
  object_prev_ = nullptr;
  object_next_ = g_app_globals->object_list_first;
  g_app_globals->object_list_first = this;
  if (object_next_) {
    object_next_->object_prev_ = this;
  }
  g_app_globals->object_count++;
#endif  // BA_DEBUG_BUILD
}

Object::~Object() {
#if BA_DEBUG_BUILD
  // Pull ourself from the global obj list.
  std::lock_guard<std::mutex> lock(g_app_globals->object_list_mutex);
  if (object_next_) {
    object_next_->object_prev_ = object_prev_;
  }
  if (object_prev_) {
    object_prev_->object_next_ = object_next_;
  } else {
    g_app_globals->object_list_first = object_next_;
  }
  g_app_globals->object_count--;

  // More sanity checks.
  if (object_strong_ref_count_ != 0) {
    // Avoiding Log for these low level errors; can lead to deadlock.
    printf(
        "Warning: Object is dying with non-zero ref-count; this is bad. "
        "(this "
        "might mean the object raised an exception in its constructor after "
        "being strong-referenced first).\n");
  }

#endif  // BA_DEBUG_BUILD

  // Invalidate all our weak refs.
  // We could call Release() on each but we'd have to deactivate the
  // thread-check since virtual functions won't work right in a destructor.
  // Also we can take a few shortcuts here since we know we're deleting the
  // entire list, not just one object.
  while (object_weak_refs_) {
    auto tmp = object_weak_refs_;
    object_weak_refs_ = tmp->next_;
    tmp->prev_ = nullptr;
    tmp->next_ = nullptr;
    tmp->obj_ = nullptr;
  }
}

auto Object::GetObjectTypeName() const -> std::string {
  // Default implementation just returns type name.
  return g_platform->DemangleCXXSymbol(typeid(*this).name());
}

auto Object::GetObjectDescription() const -> std::string {
  return "<" + GetObjectTypeName() + " object at " + Utils::PtrToString(this)
         + ">";
}

auto Object::GetThreadOwnership() const -> Object::ThreadOwnership {
#if BA_DEBUG_BUILD
  return thread_ownership_;
#else
  // Not used in release build so doesn't matter.
  return ThreadOwnership::kAny;
#endif
}

auto Object::GetDefaultOwnerThread() const -> ThreadIdentifier {
  return ThreadIdentifier::kGame;
}

#if BA_DEBUG_BUILD

static auto GetCurrentThreadIdentifier() -> ThreadIdentifier {
  if (InMainThread()) {
    return ThreadIdentifier::kMain;
  } else if (InGameThread()) {
    return ThreadIdentifier::kGame;
  } else if (InAudioThread()) {
    return ThreadIdentifier::kAudio;
  } else if (InNetworkWriteThread()) {
    return ThreadIdentifier::kNetworkWrite;
  } else if (InMediaThread()) {
    return ThreadIdentifier::kMedia;
  } else if (InBGDynamicsThread()) {
    return ThreadIdentifier::kBGDynamics;
  } else {
    throw Exception(std::string("unrecognized thread: ")
                    + GetCurrentThreadName());
  }
}

void Object::ObjectThreadCheck() {
  if (!thread_checks_enabled_) {
    return;
  }

  ThreadOwnership thread_ownership = GetThreadOwnership();
  if (thread_ownership == ThreadOwnership::kAny) {
    return;
  }

  // If we're set to use the next-referencing thread
  // and haven't set that yet, do so.
  if (thread_ownership == ThreadOwnership::kNextReferencing
      && owner_thread_ == ThreadIdentifier::kInvalid) {
    owner_thread_ = GetCurrentThreadIdentifier();
  }

  ThreadIdentifier t;
  if (thread_ownership == ThreadOwnership::kClassDefault) {
    t = GetDefaultOwnerThread();
  } else {
    t = owner_thread_;
  }
#define DO_FAIL(THREADNAME)                                                \
  throw Exception("ObjectThreadCheck failed for " + GetObjectDescription() \
                  + "; expected " THREADNAME " thread; got "               \
                  + GetCurrentThreadName())
  switch (t) {
    case ThreadIdentifier::kMain:
      if (!InMainThread()) {
        DO_FAIL("Main");
      }
      break;
    case ThreadIdentifier::kGame:
      if (!InGameThread()) {
        DO_FAIL("Game");
      }
      break;
    case ThreadIdentifier::kAudio:
      if (!InAudioThread()) {
        DO_FAIL("Audio");
      }
      break;
    case ThreadIdentifier::kNetworkWrite:
      if (!InNetworkWriteThread()) {
        DO_FAIL("NetworkWrite");
      }
      break;
    case ThreadIdentifier::kMedia:
      if (!InMediaThread()) {
        DO_FAIL("Media");
      }
      break;
    case ThreadIdentifier::kBGDynamics:
      if (!InBGDynamicsThread()) {
        DO_FAIL("BGDynamics");
      }
      break;
    default:
      throw Exception();
  }
#undef DO_FAIL
}
#endif  // BA_DEBUG_BUILD

}  // namespace ballistica
