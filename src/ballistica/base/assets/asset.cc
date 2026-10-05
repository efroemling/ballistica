// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset.h"

#include <chrono>
#include <condition_variable>
#include <mutex>
#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::base {

// Shared waiter machinery for all assets. Waiting on a claimed asset is
// rare (the hot paths are single atomic reads and uncontended claims), so
// one global mutex/cv pair beats paying per-asset memory for an event;
// publishes wake all waiters and each re-checks its own asset's state.
static std::mutex g_asset_state_wait_mutex;
static std::condition_variable g_asset_state_wait_cv;

// How long a waiter sits on the cv before logging a possible-stall
// warning and parking again. Generous; real claims are milliseconds.
const millisecs_t kAssetWaitWarnIntervalMillisecs{5000};

Asset::Asset() {
  assert(g_base);
  assert(g_base->InLogicThread());
  set_last_used_time(g_core->AppTimeMillisecs());
}

auto Asset::AssetTypeName(AssetType assettype) -> const char* {
  const char* asset_type_name{"unknown"};
  switch (assettype) {
    case AssetType::kCollisionMesh:
      asset_type_name = "collision-mesh";
      break;
    case AssetType::kMesh:
      asset_type_name = "mesh";
      break;
    case AssetType::kData:
      asset_type_name = "data";
      break;
    case AssetType::kSound:
      asset_type_name = "sound";
      break;
    case AssetType::kTexture:
      asset_type_name = "texture";
      break;
    case AssetType::kLast:
      break;
  }
  return asset_type_name;
}

auto Asset::StateName(State s) -> const char* {
  switch (s) {
    case State::kUnloaded:
      return "unloaded";
    case State::kPreloading:
      return "preloading";
    case State::kPreloaded:
      return "preloaded";
    case State::kLoading:
      return "loading";
    case State::kLoaded:
      return "loaded";
    case State::kUnloading:
      return "unloading";
    case State::kReresolving:
      return "reresolving";
    case State::kFailed:
      return "failed";
  }
  return "unknown";
}

void Asset::ObjectPostInit() {
  g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, [this] {
    return std::string("allocating ") + AssetTypeName(GetAssetType()) + " "
           + GetName();
  });
  Object::ObjectPostInit();
}

Asset::~Asset() {
  // At the moment whoever owns the last reference to us needs to make sure
  // to unload us before we die. I feel like there should be a more elegant
  // solution to that.
  assert(g_base && g_base->assets);
  State s = state();
  // Dying mid-claim means some thread is actively working on us and is
  // about to touch freed memory; dying loaded means GPU/AL/etc payloads
  // leak. Both are bugs in our owner's bookkeeping.
  assert(!IsTransientState(s));
  assert(s != State::kLoaded);
  (void)s;
}

// --- Claim machinery -------------------------------------------------------

auto Asset::TryClaim_(State from, State to) -> bool {
  // Claims may only go from a stable state into a transient one; these are
  // the legal pairs (kPreloaded -> kUnloading is the finish-load-then-
  // unload path; see Unload()).
  assert((from == State::kUnloaded && to == State::kPreloading)
         || (from == State::kPreloaded && to == State::kLoading)
         || (from == State::kLoaded && to == State::kUnloading)
         || (from == State::kPreloaded && to == State::kUnloading)
         || (from == State::kLoaded && to == State::kReresolving));
  State expected = from;
  if (!state_.compare_exchange_strong(expected, to, std::memory_order_acq_rel,
                                      std::memory_order_acquire)) {
    return false;
  }
#if BA_DEBUG_BUILD
  claim_owner_.store(std::this_thread::get_id(), std::memory_order_relaxed);
#endif
  // While holding a claim we must never *block* acquiring the GIL (the
  // logic thread may hold the GIL while waiting on this very claim); arm
  // the debug guard that fatals on violations. See the class-level notes.
  Python::PushNoGilLockZone();
  return true;
}

void Asset::ChainOwned_(State from, State to) {
  AssertIsClaimOwner_();
  // Only legal chain: a Load() that had to preload first.
  assert(from == State::kPreloading && to == State::kLoading);
  assert(state_.load(std::memory_order_relaxed) == from);
  // Still transient afterwards, so waiters stay parked; no wake needed.
  state_.store(to, std::memory_order_release);
}

void Asset::PublishOwned_(State from, State to) {
  AssertIsClaimOwner_();
  assert((from == State::kPreloading && to == State::kPreloaded)
         || (from == State::kLoading && to == State::kLoaded)
         || (from == State::kUnloading && to == State::kUnloaded)
         || (from == State::kReresolving && to == State::kLoaded));
  assert(state_.load(std::memory_order_relaxed) == from);
#if BA_DEBUG_BUILD
  claim_owner_.store(std::thread::id{}, std::memory_order_relaxed);
#endif
  Python::PopNoGilLockZone();
  // Release-store publishes all payload written during the claim to
  // threads that acquire-read the new state.
  state_.store(to, std::memory_order_release);
  // Wake waiters. The empty lock/unlock pairs with the waiters'
  // check-state-then-wait under this mutex so no waiter can park between
  // our store and our notify.
  {
    std::scoped_lock lock(g_asset_state_wait_mutex);
  }
  g_asset_state_wait_cv.notify_all();
}

void Asset::FailOwned_(State from, const std::string& message) {
  AssertIsClaimOwner_();
  assert(IsTransientState(from));
  assert(state_.load(std::memory_order_relaxed) == from);
  // Written before the kFailed release-store; immutable afterwards, so
  // anyone acquire-reading kFailed can safely read it.
  fail_message_ = message;
#if BA_DEBUG_BUILD
  claim_owner_.store(std::thread::id{}, std::memory_order_relaxed);
#endif
  Python::PopNoGilLockZone();
  state_.store(State::kFailed, std::memory_order_release);
  {
    std::scoped_lock lock(g_asset_state_wait_mutex);
  }
  g_asset_state_wait_cv.notify_all();
}

auto Asset::WaitForStableState_() -> State {
  State s = state_.load(std::memory_order_acquire);
  if (!IsTransientState(s)) {
    return s;
  }
  millisecs_t start_time = g_core->AppTimeMillisecs();
  {
    std::unique_lock<std::mutex> lock(g_asset_state_wait_mutex);
    while (true) {
      s = state_.load(std::memory_order_acquire);
      if (!IsTransientState(s)) {
        break;
      }
      auto result = g_asset_state_wait_cv.wait_for(
          lock, std::chrono::milliseconds(kAssetWaitWarnIntervalMillisecs));
      if (result == std::cv_status::timeout) {
        s = state_.load(std::memory_order_acquire);
        if (!IsTransientState(s)) {
          break;
        }
        // We've been stuck a suspiciously long time; make noise. NOTE:
        // must log with the wait-mutex released -- logging can block
        // acquiring the GIL, the GIL may be held by another waiter parked
        // on this same cv, and publishers need this mutex to wake that
        // waiter; logging under the mutex would close that cycle into a
        // deadlock.
        millisecs_t waited = g_core->AppTimeMillisecs() - start_time;
        lock.unlock();
        g_core->logging->Log(
            LogName::kBaAssets, LogLevel::kWarning,
            std::string("Still waiting for ") + AssetTypeName(GetAssetType())
                + " '" + GetName() + "' to leave state '" + StateName(s)
                + "' after " + std::to_string(waited)
                + "ms; possible asset state-machine stall.");
        lock.lock();
      }
    }
  }
  millisecs_t waited = g_core->AppTimeMillisecs() - start_time;
  if (waited > 0) {
    // Visibility into what used to be silent mutex contention.
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kDebug, [this, waited] {
      return std::string("waited ") + std::to_string(waited) + "ms for "
             + AssetTypeName(GetAssetType()) + " '" + GetName()
             + "' to reach a stable state ('" + StateName(state()) + "').";
    });
  }
  return s;
}

auto Asset::PreloadOwned_(bool* did_preload) -> bool {
  AssertIsClaimOwner_();
  assert(state_.load(std::memory_order_relaxed) == State::kPreloading);
  try {
    preload_start_time_ = g_core->AppTimeMillisecs();
    DoPreload();
    preload_end_time_ = g_core->AppTimeMillisecs();
    *did_preload = true;
    return true;
  } catch (const std::exception& exc) {
    FailOwned_(State::kPreloading, std::string("preload error: ") + exc.what());
    LogFailure_("preload");
    return false;
  }
}

auto Asset::LoadOwned_(State claim_state, bool* did_load, millisecs_t* load_ms)
    -> bool {
  AssertIsClaimOwner_();
  // kLoading is the normal load; kUnloading covers Unload()'s
  // finish-the-load-first quirk.
  assert(claim_state == State::kLoading || claim_state == State::kUnloading);
  assert(state_.load(std::memory_order_relaxed) == claim_state);
  try {
    load_start_time_ = g_core->AppTimeMillisecs();
    DoLoad();
    load_end_time_ = g_core->AppTimeMillisecs();
    *did_load = true;
    *load_ms = load_end_time_ - load_start_time_;
    return true;
  } catch (const std::exception& exc) {
    FailOwned_(claim_state, std::string("load error: ") + exc.what());
    LogFailure_("load");
    return false;
  }
}

auto Asset::UnloadOwned_() -> bool {
  AssertIsClaimOwner_();
  assert(state_.load(std::memory_order_relaxed) == State::kUnloading);
  try {
    DoUnload();
    return true;
  } catch (const std::exception& exc) {
    FailOwned_(State::kUnloading, std::string("unload error: ") + exc.what());
    LogFailure_("unload");
    return false;
  }
}

void Asset::LogFailure_(const char* phase) {
  // Called just after FailOwned_ published kFailed (claim released, so
  // taking the GIL to log is safe now). This is the one-and-only verbose
  // report for this asset; later Load() attempts throw cheaply and never
  // re-run the work (no retry/log storms for permanently-missing data).
  g_core->logging->Log(
      LogName::kBaAssets, LogLevel::kError,
      std::string("Failed to ") + phase + " " + AssetTypeName(GetAssetType())
          + " '" + GetNameFull()
          + "'; marking asset failed (will not retry): " + fail_message_);
}

void Asset::ThrowFailure_() {
  throw Exception(std::string("Asset '") + GetNameFull() + "' ("
                  + AssetTypeName(GetAssetType()) + ") is in failed state ("
                  + fail_message_ + ").");
}

void Asset::EmitLoadLogs_(bool did_preload, bool did_load,
                          millisecs_t load_ms) {
  // MUST be called with no claim held: logging routes through Python and
  // may block acquiring the GIL (see the class-level invariant).
  if (did_preload) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kDebug, [this] {
      return std::string("preloading ") + AssetTypeName(GetAssetType()) + " "
             + GetName();
    });
  }
  if (did_load) {
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kDebug, [this] {
      return std::string("loading ") + AssetTypeName(GetAssetType()) + " "
             + GetName();
    });
    // Slow-load warning (debug builds only; skipped on test builds).
    if (g_buildconfig.debug_build() && !g_buildconfig.variant_test_build()
        && load_ms > 50) {
      g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                           std::to_string(load_ms) + " milliseconds spent by "
                               + g_core->CurrentThreadName()
                               + " thread loading " + GetName());
    }
  }
}

#if BA_DEBUG_BUILD
void Asset::AssertIsClaimOwner_() {
  assert(claim_owner_.load(std::memory_order_relaxed)
         == std::this_thread::get_id());
}
#endif

// --- Public load-state operations ------------------------------------------

void Asset::Preload() {
  bool did_preload{};
  switch (state_.load(std::memory_order_acquire)) {
    case State::kUnloaded:
      if (TryClaim_(State::kUnloaded, State::kPreloading)) {
        if (PreloadOwned_(&did_preload)) {
          PublishOwned_(State::kPreloading, State::kPreloaded);
          EmitLoadLogs_(did_preload, false, 0);
        }
        // On failure, FailOwned_/LogFailure_ already said everything;
        // Preload() itself never throws so pipeline queues keep draining.
      }
      // Lost the claim race: someone else is driving this asset; fine.
      break;
    default:
      // Already preloaded/loaded/failed, or a transition is in flight on
      // another thread. Either way there's nothing useful for us to do;
      // downstream Load() calls do any waiting needed.
      break;
  }
}

void Asset::Load() {
  bool did_preload{};
  bool did_load{};
  millisecs_t load_ms{};
  while (true) {
    State s = state_.load(std::memory_order_acquire);
    switch (s) {
      case State::kLoaded:
      case State::kReresolving:
        // Fully loaded (kReresolving only mutates source-identity fields;
        // the loaded payload remains valid). The common already-loaded
        // case lands here on the first loop with zero locking.
        EmitLoadLogs_(did_preload, did_load, load_ms);
        return;
      case State::kFailed:
        ThrowFailure_();
        break;  // (unreachable)
      case State::kUnloaded:
        // Nobody has even preloaded this; claim and do the whole thing
        // here (matches old behavior where Load() preloaded under the
        // same lock hold if needed).
        if (TryClaim_(State::kUnloaded, State::kPreloading)) {
          if (!PreloadOwned_(&did_preload)) {
            ThrowFailure_();
          }
          ChainOwned_(State::kPreloading, State::kLoading);
          if (!LoadOwned_(State::kLoading, &did_load, &load_ms)) {
            ThrowFailure_();
          }
          PublishOwned_(State::kLoading, State::kLoaded);
        }
        // Claim raced away from us; loop and re-evaluate.
        break;
      case State::kPreloaded:
        if (TryClaim_(State::kPreloaded, State::kLoading)) {
          if (!LoadOwned_(State::kLoading, &did_load, &load_ms)) {
            ThrowFailure_();
          }
          PublishOwned_(State::kLoading, State::kLoaded);
        }
        break;
      case State::kPreloading:
      case State::kLoading:
      case State::kUnloading:
        // In flight on another thread; wait for it to settle then
        // re-evaluate. (This is the visible version of what used to be
        // silent blocking on the asset mutex.)
        WaitForStableState_();
        break;
    }
  }
}

void Asset::Unload() {
  while (true) {
    State s = state_.load(std::memory_order_acquire);
    switch (s) {
      case State::kUnloaded:
      case State::kFailed:
        // Nothing loaded (failed assets never got payloads published).
        return;
      case State::kLoaded:
        if (TryClaim_(State::kLoaded, State::kUnloading)) {
          if (!UnloadOwned_()) {
            ThrowFailure_();
          }
          PublishOwned_(State::kUnloading, State::kUnloaded);
          return;
        }
        break;
      case State::kPreloaded:
        if (TryClaim_(State::kPreloaded, State::kUnloading)) {
          // Quirk preserved from the old implementation: if we're told to
          // unload after preload but before load, finish the load first so
          // DoUnload() always tears down a fully-loaded asset. (Old code
          // wondered whether this is still necessary; keeping behavior
          // identical through this refactor.)
          bool did_load{};
          millisecs_t load_ms{};
          if (!LoadOwned_(State::kUnloading, &did_load, &load_ms)) {
            ThrowFailure_();
          }
          if (!UnloadOwned_()) {
            ThrowFailure_();
          }
          PublishOwned_(State::kUnloading, State::kUnloaded);
          return;
        }
        break;
      case State::kPreloading:
      case State::kLoading:
      case State::kUnloading:
      case State::kReresolving:
        WaitForStableState_();
        break;
    }
  }
}

auto Asset::ReResolveSourceClaimed() -> bool {
  while (true) {
    State s = state_.load(std::memory_order_acquire);
    if (IsTransientState(s)) {
      WaitForStableState_();
      continue;
    }
    if (s != State::kLoaded) {
      // Not currently loaded; nothing to re-resolve (the next preload
      // resolves fresh from the registry anyway).
      return false;
    }
    if (TryClaim_(State::kLoaded, State::kReresolving)) {
      // ReResolveSource mutates source-identity fields that preloads
      // read, so it must run inside a claim like any other mutation.
      bool changed{};
      try {
        changed = ReResolveSource();
      } catch (...) {
        // The loaded payload is still fully intact/usable, so restore
        // kLoaded (not kFailed) and let the error surface to the caller.
        PublishOwned_(State::kReresolving, State::kLoaded);
        throw;
      }
      PublishOwned_(State::kReresolving, State::kLoaded);
      return changed;
    }
    // Claim raced away from us; loop and re-evaluate.
  }
}

}  // namespace ballistica::base
