// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset.h"

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::base {

Asset::Asset() {
  assert(g_base);
  assert(g_base->InLogicThread());
  last_used_time_ = g_core->AppTimeMillisecs();
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

void Asset::ObjectPostInit() {
  g_core->logging->Log(LogName::kBaAssets, LogLevel::kInfo, [this] {
    return std::string("allocating ") + AssetTypeName(GetAssetType()) + " "
           + GetName();
  });
  Object::ObjectPostInit();
}

Asset::~Asset() {
  // at the moment whoever owns the last reference to us needs to make sure
  // to unload us before we die. I feel like there should be a more elegant
  // solution to that.
  assert(g_base && g_base->assets);
  assert(!locked());
  assert(!loaded());
}

// Performs preload, and (when want_load) load, of this asset's data. MUST be
// called with the asset lock held. Emits NO logs and takes NO GIL (logging
// routes through Python and must happen outside the asset lock -- see the
// lock-ordering invariant on Asset::Lock). Reports via out-params which steps
// actually ran this call so the unlocked caller can emit their log lines.
void Asset::DoLoadWork_(bool want_load, bool* did_preload, bool* did_load,
                        millisecs_t* load_ms) {
  *did_preload = false;
  *did_load = false;
  *load_ms = 0;
  if (!preloaded_) {
    assert(!loaded_);
    BA_PRECONDITION(locked());
    preload_start_time_ = g_core->AppTimeMillisecs();
    DoPreload();
    preload_end_time_ = g_core->AppTimeMillisecs();
    preloaded_ = true;
    *did_preload = true;
  }
  if (want_load && !loaded_) {
    assert(preloaded_ && !loaded_);
    BA_PRECONDITION(locked());
    load_start_time_ = g_core->AppTimeMillisecs();
    DoLoad();
    load_end_time_ = g_core->AppTimeMillisecs();
    loaded_ = true;
    *did_load = true;
    *load_ms = load_end_time_ - load_start_time_;
  }
}

// Emits the preload/load debug logs (and the slow-load warning) for whichever
// steps just ran. MUST be called with NO asset lock held: these calls route
// through Python logging and therefore acquire the GIL, and taking the GIL
// under an asset lock deadlocks against the logic thread (see the invariant on
// Asset::Lock).
void Asset::EmitLoadLogs_(bool did_preload, bool did_load,
                          millisecs_t load_ms) {
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
    // Slow-load warning. This was previously a BA_DEBUG_FUNCTION_TIMER_END
    // macro wrapping DoLoad *under the lock*; it logs at WARNING (always
    // enabled) so it was an always-on GIL-under-lock hazard in debug builds.
    // Moved out here to honor the no-GIL-under-asset-lock invariant; same
    // debug-build-only, skip-on-test-build gating as the old macro.
    if (g_buildconfig.debug_build() && !g_buildconfig.variant_test_build()
        && load_ms > 50) {
      g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                           std::to_string(load_ms) + " milliseconds spent by "
                               + g_core->CurrentThreadName()
                               + " thread loading " + GetName());
    }
  }
}

void Asset::Preload() {
  bool did_preload;
  bool did_load;
  millisecs_t load_ms;
  {
    LockGuard lock(this);
    DoLoadWork_(false, &did_preload, &did_load, &load_ms);
  }
  // Emit logs only after releasing the asset lock (logging takes the GIL --
  // see the invariant on Asset::Lock).
  EmitLoadLogs_(did_preload, did_load, load_ms);
}

void Asset::Load() {
  bool did_preload;
  bool did_load;
  millisecs_t load_ms;
  {
    LockGuard lock(this);
    DoLoadWork_(true, &did_preload, &did_load, &load_ms);
  }
  EmitLoadLogs_(did_preload, did_load, load_ms);
}

void Asset::Unload(bool already_locked) {
  LockGuard lock(this, already_locked ? LockGuard::Type::kDontLock
                                      : LockGuard::Type::kLock);

  // if somehow we're told to unload after we've preloaded but before load,
  // finish the load first... (don't wanna worry about guarding against that
  // case)
  // UPDATE: is this still necessary?  It's a holdover from when we had
  // potentially-multi-stage loads... now we just have a single load always.
  if (preloaded_ && !loaded_) {
    // Finish the load before unloading. We already hold the lock, so do the
    // work directly via the locked helper (no logging -- this load is about
    // to be undone, and logging here would take the GIL under the lock).
    bool did_preload;
    bool did_load;
    millisecs_t load_ms;
    DoLoadWork_(true, &did_preload, &did_load, &load_ms);
  }
  if (loaded_ && preloaded_) {
    BA_PRECONDITION(locked());
    DoUnload();
    preloaded_ = false;
    loaded_ = false;
  }
}

void Asset::Lock() {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  mutex_.lock();
  assert(!locked_);
  locked_ = true;
  // Mark that we now hold a leaf lock that must never be held while blocking
  // to acquire the GIL (logging, etc.). In debug builds this arms a check
  // that fires if anything takes the GIL before we Unlock(). See the
  // lock-ordering invariant on Asset::Lock in asset.h.
  Python::PushNoGilLockZone();
  BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(20, GetName());
}

auto Asset::TryLock() -> bool {
  bool val = mutex_.try_lock();
  if (val) {
    assert(!locked_);
    locked_ = true;
    // Same no-GIL-lock-zone bookkeeping as Lock() -- this is a parallel
    // lock-acquisition path (the lock is released via Unlock() through a
    // kInheritLock LockGuard). Without arming the guard here the depth would
    // underflow at that Unlock(). See the invariant on Asset::Lock in asset.h.
    Python::PushNoGilLockZone();
  }
  return val;
}

void Asset::Unlock() {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  assert(locked_);
  Python::PopNoGilLockZone();
  locked_ = false;
  mutex_.unlock();
  BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(20, GetName());
}

Asset::LockGuard::LockGuard(Asset* data, Type type) : data_(data) {
  switch (type) {
    case kLock: {
      BA_DEBUG_FUNCTION_TIMER_BEGIN();
      data_->Lock();
      holds_lock_ = true;
      BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
      break;
    }
    case kInheritLock:
      holds_lock_ = true;
      break;
    case kDontLock:
      break;
    default:
      throw Exception();
  }
}

Asset::LockGuard::~LockGuard() {
  if (holds_lock_) {
    data_->Unlock();
  }
}
}  // namespace ballistica::base
