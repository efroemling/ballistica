// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/foundation/object.h"

#include <algorithm>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica {

// Note: Functionality here assumes that someone has imported core and will
// fail hard if not (hence us using core's internal globals below).
using core::g_base_soft;
using core::g_core;

Object::Object() {
#if BA_DEBUG_BUILD
  // Mark when we were born.
  assert(g_core);
  object_birth_time_ = g_core->AppTimeMillisecs();

  // Add ourself to the global object list.
  {
    std::scoped_lock lock(g_core->object_list_mutex);
    object_prev_ = nullptr;
    object_next_ = g_core->object_list_first;
    g_core->object_list_first = this;
    if (object_next_) {
      object_next_->object_prev_ = this;
    }
    g_core->object_count++;
  }
#endif  // BA_DEBUG_BUILD
}

Object::~Object() {
#if BA_DEBUG_BUILD
  {
    assert(g_core);
    // Pull ourself from the global obj list.
    std::scoped_lock lock(g_core->object_list_mutex);
    if (object_next_) {
      object_next_->object_prev_ = object_prev_;
    }
    if (object_prev_) {
      object_prev_->object_next_ = object_next_;
    } else {
      g_core->object_list_first = object_next_;
    }
    g_core->object_count--;
  }

  // Objects should never be dying with non-zero reference counts.
  if (object_strong_ref_count_ != 0) {
    FatalError("Object is dying with non-zero ref-count.");
  }

  // Objects set up as ref-counted shouldn't be dying before getting reffed.
  if (object_is_ref_counted_ && !object_has_been_strong_reffed_) {
    FatalError(
        "Object set as ref-counted but dying without ever having a ref.");
  }

#endif  // BA_DEBUG_BUILD

  // Invalidate all our weak refs.
  //
  // We could call Release() on each but we'd have to deactivate the
  // thread-check since virtual functions won't work as expected in a
  // destructor. Also we can take a few shortcuts here since we know
  // we're deleting the entire list, not just one object.
  while (object_weak_refs_) {
    auto tmp{object_weak_refs_};
    object_weak_refs_ = tmp->next_;
    tmp->prev_ = nullptr;
    tmp->next_ = nullptr;
    tmp->obj_ = nullptr;
  }
}

void Object::ObjectPostInit() {
#if BA_DEBUG_BUILD
  // Flag this here in the top level post-init so we can ensure that classes
  // are properly calling parent class post-inits.
  object_is_post_inited_ = true;
#endif
}

auto Object::GetObjectTypeName() const -> std::string {
  // Default implementation just returns type name.
  if (g_core) {
    return g_core->platform->DemangleCXXSymbol(typeid(*this).name());
  }
  return "(unknown-no-core)";
}

auto Object::GetObjectDescription() const -> std::string {
  return "<" + GetObjectTypeName() + " object at " + Utils::PtrToString(this)
         + ">";
}

auto Object::GetDefaultOwnerThread() const -> EventLoopID {
  return EventLoopID::kLogic;
}

auto Object::GetThreadOwnership() const -> Object::ThreadOwnership {
#if BA_DEBUG_BUILD
  return thread_ownership_;
#else
  FatalError("Should not be called in release builds.");
  return ThreadOwnership::kClassDefault;
#endif
}

void Object::LsObjects() {
#if BA_DEBUG_BUILD
  assert(g_core);
  std::string s;
  {
    std::scoped_lock lock(g_core->object_list_mutex);
    s = std::to_string(g_core->object_count) + " Objects at time "
        + std::to_string(g_core->AppTimeMillisecs()) + ";";

    if (explicit_bool(true)) {
      std::unordered_map<std::string, int> obj_map;

      // Tally up counts for all types.
      int count = 0;
      for (Object* o = g_core->object_list_first; o != nullptr;
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
      std::sort(sorted.rbegin(), sorted.rend());
      for (auto&& i : sorted) {
        s += "\n   " + std::to_string(i.first) + ": " + i.second;
      }
      assert(count == g_core->object_count);
    }
  }
  g_core->logging->Log(LogName::kBa, LogLevel::kInfo, s);
#else
  g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                       "LsObjects() only functions in debug builds.");
#endif  // BA_DEBUG_BUILD
}

#if BA_DEBUG_BUILD

static auto GetCurrentEventLoopID() -> EventLoopID {
  if (g_core->InMainThread()) {
    return EventLoopID::kMain;
  } else if (g_base_soft && g_base_soft->InLogicThread()) {
    return EventLoopID::kLogic;
  } else if (g_base_soft && g_base_soft->InAudioThread()) {
    return EventLoopID::kAudio;
  } else if (g_base_soft && g_base_soft->InNetworkWriteThread()) {
    return EventLoopID::kNetworkWrite;
  } else if (g_base_soft && g_base_soft->InAssetsThread()) {
    return EventLoopID::kAssets;
  } else if (g_base_soft && g_base_soft->InBGDynamicsThread()) {
    return EventLoopID::kBGDynamics;
  } else {
    throw Exception(std::string("unrecognized thread: ")
                    + g_core->CurrentThreadName());
  }
}

void Object::ObjectUpdateForAcquire() {
  ThreadOwnership thread_ownership = GetThreadOwnership();

  // If we're set to use the next-referencing thread and haven't set one
  // yet, do so.
  if (thread_ownership == ThreadOwnership::kNextReferencing
      && owner_thread_ == EventLoopID::kInvalid) {
    owner_thread_ = GetCurrentEventLoopID();
  }
}

void Object::ObjectThreadCheck() const {
  if (!thread_checks_enabled_) {
    return;
  }

  auto thread_ownership = GetThreadOwnership();

  // Special case; graphics context (not simply a thread so have to handle
  // specially).
  if (thread_ownership == ThreadOwnership::kGraphicsContext) {
    if (!(g_base_soft && g_base_soft->InGraphicsContext())) {
      throw Exception("ObjectThreadCheck failed for " + GetObjectDescription()
                      + "; expected graphics context.");
    }
    return;
  }

  EventLoopID t;
  if (thread_ownership == ThreadOwnership::kClassDefault) {
    t = GetDefaultOwnerThread();
  } else {
    t = owner_thread_;
  }
#define DO_FAIL(THREADNAME)                                                \
  throw Exception("ObjectThreadCheck failed for " + GetObjectDescription() \
                  + "; expected " THREADNAME " thread; got "               \
                  + g_core->CurrentThreadName())
  switch (t) {
    case EventLoopID::kMain:
      if (!g_core->InMainThread()) {
        DO_FAIL("Main");
      }
      break;
    case EventLoopID::kLogic:
      if (!(g_base_soft && g_base_soft->InLogicThread())) {
        DO_FAIL("Logic");
      }
      break;
    case EventLoopID::kAudio:
      if (!(g_base_soft && g_base_soft->InAudioThread())) {
        DO_FAIL("Audio");
      }
      break;
    case EventLoopID::kNetworkWrite:
      if (!(g_base_soft && g_base_soft->InNetworkWriteThread())) {
        DO_FAIL("NetworkWrite");
      }
      break;
    case EventLoopID::kAssets:
      if (!(g_base_soft && g_base_soft->InAssetsThread())) {
        DO_FAIL("Assets");
      }
      break;
    case EventLoopID::kBGDynamics:
      if (!(g_base_soft && g_base_soft->InBGDynamicsThread())) {
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
