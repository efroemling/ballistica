// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/asset.h"

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

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

void Asset::Preload(bool already_locked) {
  LockGuard lock(this, already_locked ? LockGuard::Type::kDontLock
                                      : LockGuard::Type::kLock);
  if (!preloaded_) {
    assert(!loaded_);
    BA_PRECONDITION(locked());
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kDebug, [this] {
      return std::string("preloading ") + AssetTypeName(GetAssetType()) + " "
             + GetName();
    });
    preload_start_time_ = g_core->AppTimeMillisecs();
    DoPreload();
    preload_end_time_ = g_core->AppTimeMillisecs();
    preloaded_ = true;
  }
}

void Asset::Load(bool already_locked) {
  LockGuard lock(this, already_locked ? LockGuard::Type::kDontLock
                                      : LockGuard::Type::kLock);
  if (!preloaded_) {
    Preload(true);
  }

  if (!loaded_) {
    assert(preloaded_ && !loaded_);
    BA_DEBUG_FUNCTION_TIMER_BEGIN();
    BA_PRECONDITION(locked());
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kDebug, [this] {
      return std::string("loading ") + AssetTypeName(GetAssetType()) + " "
             + GetName();
    });
    load_start_time_ = g_core->AppTimeMillisecs();
    DoLoad();
    load_end_time_ = g_core->AppTimeMillisecs();
    BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(50, GetName());
    loaded_ = true;
  }
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
    Load(true);
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
  BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(20, GetName());
}

void Asset::Unlock() {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  assert(locked_);
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
