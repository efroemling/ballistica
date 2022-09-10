// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_DATA_ASSET_COMPONENT_DATA_H_
#define BALLISTICA_ASSETS_DATA_ASSET_COMPONENT_DATA_H_

#include <mutex>
#include <string>

#include "ballistica/core/object.h"
#include "ballistica/platform/platform.h"

namespace ballistica {

/// Base class for loadable asset components.
class AssetComponentData : public Object {
 public:
  AssetComponentData();
  ~AssetComponentData() override;
  void Preload(bool already_locked = false);
  void Load(bool already_locked = false);
  void Unload(bool already_locked = false);
  auto preloaded() const -> bool { return preloaded_; }
  auto loaded() const -> bool { return preloaded_ && loaded_; }
  virtual auto GetAssetType() const -> AssetType = 0;

  // Return name or another identifier. For debugging purposes.
  virtual auto GetName() const -> std::string { return "invalid"; }
  virtual auto GetNameFull() const -> std::string { return GetName(); }

  // Used to lock asset payloads for modification in a RAII manner.
  // FIXME - need to better define the times when payloads need to
  //  be locked. For instance, we ensure everything is loaded at the
  //  beginning of drawing a frame, but technically is anything preventing
  //  it from being unloaded during the draw?..
  class LockGuard {
   public:
    enum Type { kLock, kInheritLock, kDontLock };
    explicit LockGuard(AssetComponentData* data, Type type = kLock);
    ~LockGuard();

    // Does this guard hold a lock?
    auto holds_lock() const -> bool { return holds_lock_; }

   private:
    AssetComponentData* data_ = nullptr;
    bool holds_lock_ = false;
  };

  // Attempt to lock the component without blocking.  returns true if
  // successful. In the case of success, use a LockGuard with
  // kInheritLock to release the lock.
  auto TryLock() -> bool {
    bool val = mutex_.try_lock();
    if (val) {
      assert(!locked_);
      locked_ = true;
    }
    return val;
  }

  auto locked() const -> bool { return locked_; }
  auto last_used_time() const -> millisecs_t { return last_used_time_; }
  void set_last_used_time(millisecs_t val) { last_used_time_ = val; }

  // Used by the renderer when adding component refs to frame_defs.
  auto last_frame_def_num() const -> int64_t { return last_frame_def_num_; }
  void set_last_frame_def_num(int64_t last) { last_frame_def_num_ = last; }
  auto preload_time() const -> millisecs_t {
    return preload_end_time_ - preload_start_time_;
  }
  auto load_time() const -> millisecs_t {
    return load_end_time_ - load_start_time_;
  }

  // Sanity testing.
  auto valid() const -> bool { return valid_; }

 protected:
  // Preload the component's data. This may be called from any thread so must
  // be safe regardless (ie: just load data into the component; don't make GL
  // calls, etc).
  virtual void DoPreload() = 0;

  // This is always called by the main thread that uses the component to finish
  // loading. ie: whatever thread is running opengl will call this for textures,
  // audio thread for sounds, etc as much heavy lifting as possible should be
  // done in DoPreload but interaction with the corresponding api (gl, al, etc)
  // is done here.
  virtual void DoLoad() = 0;

  // Unload the component. This is always called by the main component thread
  // (same as DoLoad).
  virtual void DoUnload() = 0;

  // Do we still use/need this?
  bool valid_ = false;

 private:
  // Lock the component - components must be locked whenever using them.
  void Lock() {
    BA_DEBUG_FUNCTION_TIMER_BEGIN();
    mutex_.lock();
    assert(!locked_);
    locked_ = true;
    BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(20, GetName());
  }

  // Unlock the component.  each call to lock must be accompanied by one of
  // these.
  void Unlock() {
    BA_DEBUG_FUNCTION_TIMER_BEGIN();
    assert(locked_);
    locked_ = false;
    mutex_.unlock();
    BA_DEBUG_FUNCTION_TIMER_END_THREAD_EX(20, GetName());
  }

  bool locked_ = false;
  millisecs_t preload_start_time_ = 0;
  millisecs_t preload_end_time_ = 0;
  millisecs_t load_start_time_ = 0;
  millisecs_t load_end_time_ = 0;

  // We keep track of what frame_def we've been added to so
  // we only include a single reference to ourself in it.
  int64_t last_frame_def_num_ = 0;
  millisecs_t last_used_time_ = 0;
  bool preloaded_ = false;
  bool loaded_ = false;
  std::mutex mutex_;
  BA_DISALLOW_CLASS_COPIES(AssetComponentData);
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_DATA_ASSET_COMPONENT_DATA_H_
