// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_H_
#define BALLISTICA_BASE_ASSETS_ASSET_H_

#include <mutex>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// Base class for loadable assets.
/// This represents the actual underlying data for the assets.
/// Representations of assets in scenes/ui-systems/etc.
/// will generally be other classes containing one of these.
class Asset : public Object {
 public:
  Asset();
  void ObjectPostInit() override;
  ~Asset() override;

  virtual auto GetAssetType() const -> AssetType = 0;

  /// Get a human readable name for an AssetType.
  static auto AssetTypeName(AssetType assettype) -> const char*;

  // Lock-ordering invariant: NEVER acquire the GIL (call into Python --
  // including logging, which routes through Python's logging module) while
  // holding an Asset lock. The GIL is the outer lock and per-asset mutexes
  // are leaf locks: the logic thread holds the GIL and then takes asset
  // locks when scene nodes load their assets, so an asset-loader thread that
  // took an asset lock and then blocked on the GIL would deadlock against it.
  // Preload()/Load() honor this by doing their work under the lock but
  // emitting their logs only after releasing it (see asset.cc).
  void Preload();
  void Load();
  void Unload(bool already_locked = false);
  auto preloaded() const -> bool { return preloaded_; }
  auto loaded() const -> bool { return preloaded_ && loaded_; }

  // Flag set on the logic thread (by Assets::ReloadChangedAssets, after
  // ReResolveSource reports a changed source) and consumed on the asset's
  // load thread (which unloads + reloads this asset). Lets the cross-thread
  // reload pass the work along without passing refs across threads.
  auto reload_pending() const -> bool { return reload_pending_; }
  void set_reload_pending(bool val) { reload_pending_ = val; }

  // Return name or another identifier. For debugging purposes.
  virtual auto GetName() const -> std::string { return "invalid"; }
  virtual auto GetNameFull() const -> std::string { return GetName(); }

  // Re-resolve this asset's underlying source from its name -- e.g. after the
  // asset-package registry is re-resolved to a different flavor (fallback ->
  // desktop, a language swap, etc.) so the same logical asset now maps to a
  // different CAS blob. If the resolved source changed, update it and return
  // true (the caller then unloads + reloads this asset to pick it up). The
  // default is a no-op returning false, for asset types whose source can't
  // change at runtime. MUST be called with the asset locked.
  virtual auto ReResolveSource() -> bool { return false; }

  // Used to lock asset payloads for modification in a RAII manner.
  // FIXME - need to better define the times when payloads need to
  //  be locked. For instance, we ensure everything is loaded at the
  //  beginning of drawing a frame, but technically is anything preventing
  //  it from being unloaded during the draw?..
  class LockGuard {
   public:
    enum Type { kLock, kInheritLock, kDontLock };
    explicit LockGuard(Asset* data, Type type = kLock);
    ~LockGuard();

    // Does this guard hold a lock?
    auto holds_lock() const -> bool { return holds_lock_; }

   private:
    Asset* data_ = nullptr;
    bool holds_lock_ = false;
  };

  // Attempt to lock the component without blocking.  returns true if
  // successful. In the case of success, use a LockGuard with
  // kInheritLock to release the lock. (Out-of-line because, like Lock(), a
  // successful acquire must arm the no-GIL-lock-zone debug guard -- see
  // asset.cc and the lock-ordering invariant above.)
  auto TryLock() -> bool;

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
  // Does the actual preload/load work with the asset lock held; emits no logs
  // and takes no GIL (see the lock-ordering invariant above). Reports which
  // steps ran so the unlocked caller can log them via EmitLoadLogs_.
  void DoLoadWork_(bool want_load, bool* did_preload, bool* did_load,
                   millisecs_t* load_ms);

  // Emits the preload/load logs (and slow-load warning) for steps that just
  // ran. MUST be called with no asset lock held -- it takes the GIL.
  void EmitLoadLogs_(bool did_preload, bool did_load, millisecs_t load_ms);

  // Lock the component - components must be locked whenever using them.
  void Lock();

  // Unlock the component.  each call to lock must be accompanied by one of
  // these.
  void Unlock();

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
  bool reload_pending_ = false;
  std::mutex mutex_;
  BA_DISALLOW_CLASS_COPIES(Asset);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_H_
