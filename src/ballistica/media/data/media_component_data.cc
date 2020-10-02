// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/media/data/media_component_data.h"

namespace ballistica {

MediaComponentData::MediaComponentData() {
  assert(InGameThread());
  assert(g_media);
  last_used_time_ = GetRealTime();
}

MediaComponentData::~MediaComponentData() {
  // at the moment whoever owns the last reference to us
  // needs to make sure to unload us before we die..
  // I feel like there should be a more elegant solution to that.
  assert(g_media);
  assert(!locked());
  assert(!loaded());
}

void MediaComponentData::Preload(bool already_locked) {
  LockGuard lock(this, already_locked ? LockGuard::Type::kDontLock
                                      : LockGuard::Type::kLock);
  if (!preloaded_) {
    assert(!loaded_);
#if BA_SHOW_LOADS_UNLOADS
    printf("pre-loading %s\n", GetName().c_str());
#endif
    BA_PRECONDITION(locked());
    preload_start_time_ = GetRealTime();
    DoPreload();
    preload_end_time_ = GetRealTime();
    preloaded_ = true;
  }
}

void MediaComponentData::Load(bool already_locked) {
  LockGuard lock(this, already_locked ? LockGuard::Type::kDontLock
                                      : LockGuard::Type::kLock);
  if (!preloaded_) {
    Preload(true);
  }

  if (!loaded_) {
#if BA_SHOW_LOADS_UNLOADS
    printf("loading %s\n", GetName().c_str());
#endif
    assert(preloaded_ && !loaded_);
    BA_DEBUG_FUNCTION_TIMER_BEGIN();
    BA_PRECONDITION(locked());
    load_start_time_ = GetRealTime();
    DoLoad();
    load_end_time_ = GetRealTime();
    BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(50, GetName());
    loaded_ = true;
  }
}

void MediaComponentData::Unload(bool already_locked) {
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
#if BA_SHOW_LOADS_UNLOADS
    printf("unloading %s\n", GetName().c_str());
#endif
    BA_PRECONDITION(locked());
    DoUnload();
    preloaded_ = false;
    loaded_ = false;
  }
}

MediaComponentData::LockGuard::LockGuard(MediaComponentData* data, Type type)
    : data_(data) {
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

MediaComponentData::LockGuard::~LockGuard() {
  if (holds_lock_) {
    data_->Unlock();
  }
}
}  // namespace ballistica
