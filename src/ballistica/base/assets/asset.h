// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSET_H_
#define BALLISTICA_BASE_ASSETS_ASSET_H_

#include <atomic>
#include <string>
#include <thread>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// Base class for loadable assets.
/// This represents the actual underlying data for the assets.
/// Representations of assets in scenes/ui-systems/etc.
/// will generally be other classes containing one of these.
///
/// Load-state concurrency model (claimed state machine):
///
/// An asset's load-state lives in a single std::atomic<State>. States come
/// in two kinds:
///
/// - *Stable* states (kUnloaded, kPreloaded, kLoaded, kFailed): the asset
///   is at rest; its payload for that state is fully published and
///   immutable until some thread claims a transition away from it.
/// - *Claim* states (kPreloading, kLoading, kUnloading, kReresolving): a
///   specific thread owns the asset and is doing work on it.
///
/// The only way to start work is to CAS from a stable state into a claim
/// state. There is deliberately NO transition whose expected-value is a
/// claim state, so once a thread wins a claim nobody else can touch the
/// state; the owner does its work holding no locks at all and finishes by
/// release-storing the next stable state (or chaining to a further claim
/// state it still owns, e.g. kPreloading -> kLoading inside Load()).
/// Threads that observe a claim state and need the result wait on a shared
/// condition-variable that publishers signal; the hot already-loaded path
/// is a single atomic acquire-load.
///
/// All payload and source-identity mutation happens inside claims; this
/// includes ReResolveSource(), which runs under its own kReresolving claim
/// (kLoaded -> kLoaded) since it mutates fields that preloads read.
///
/// kFailed is terminal: a preload/load that throws publishes kFailed (with
/// a one-time error log) and the asset is never retried, preventing
/// retry/log storms from permanently-missing data. Load() on a failed
/// asset throws a (cheap) descriptive exception; Preload()/Unload() no-op.
/// Pruning may evict an unreferenced failed asset from the asset maps, so
/// a later fresh use can retry via re-creation.
///
/// GIL-ordering invariant (unchanged in spirit from the old per-asset
/// mutex): a thread that holds a claim must never *block* acquiring the
/// Python GIL (logging routes through Python!), because the logic thread
/// may hold the GIL while waiting for that very claim to resolve. Already
/// holding the GIL is fine (e.g. DataAsset::DoLoad on the logic thread).
/// Claims arm the Python::PushNoGilLockZone debug guard, which fatals on
/// violations in debug builds. Preload()/Load() therefore emit their logs
/// only after publishing (see asset.cc).
class Asset : public Object {
 public:
  /// Asset load-state. See the class-level concurrency notes.
  enum class State : uint8_t {
    kUnloaded,     // Stable: no payload.
    kPreloading,   // Claim: DoPreload() in progress.
    kPreloaded,    // Stable: preload payload ready; api-thread load pending.
    kLoading,      // Claim: DoLoad() in progress.
    kLoaded,       // Stable: fully loaded and usable.
    kUnloading,    // Claim: DoUnload() in progress.
    kReresolving,  // Claim: ReResolveSource() in progress (Loaded->Loaded).
    kFailed,       // Stable+terminal: preload/load threw; never retried.
  };
  static auto IsTransientState(State s) -> bool {
    return s == State::kPreloading || s == State::kLoading
           || s == State::kUnloading || s == State::kReresolving;
  }
  static auto StateName(State s) -> const char*;

  Asset();
  void ObjectPostInit() override;
  ~Asset() override;

  virtual auto GetAssetType() const -> AssetType = 0;

  /// Get a human readable name for an AssetType.
  static auto AssetTypeName(AssetType assettype) -> const char*;

  /// Ensure this asset's preload step has at least been started by
  /// somebody. If the asset is sitting kUnloaded, claims and runs the
  /// preload on the calling thread. If another thread is already driving
  /// the asset (or it is preloaded/loaded/failed already) this is a no-op
  /// -- downstream Load() calls do any waiting needed. Never throws; a
  /// preload error publishes kFailed (logged once).
  void Preload();

  /// Ensure this asset is fully loaded, blocking if another thread is
  /// mid-transition. May run preload+load itself on the calling thread (so
  /// only call from a thread allowed to run this asset type's DoLoad()).
  /// Throws if the asset is (or becomes) kFailed.
  void Load();

  /// Ensure this asset is unloaded (no-op for kUnloaded/kFailed); blocks
  /// on in-flight transitions. Must be called from this asset type's api
  /// thread (same as DoLoad()).
  void Unload();

  /// Run ReResolveSource() under a kReresolving claim if the asset is
  /// currently loaded; returns whether the resolved source changed (the
  /// caller then flags the asset for unload+reload). Returns false without
  /// resolving for non-loaded assets (their next preload resolves fresh).
  /// Blocks on in-flight transitions like Load()/Unload() do.
  auto ReResolveSourceClaimed() -> bool;

  /// This asset's current load-state (atomic acquire read; the value can
  /// of course change the moment it's read unless you're the claim owner).
  auto state() const -> State { return state_.load(std::memory_order_acquire); }

  /// Preload payload is published and readable (and not being torn down).
  auto preloaded() const -> bool {
    State s = state();
    return s == State::kPreloaded || s == State::kLoading || s == State::kLoaded
           || s == State::kReresolving;
  }

  /// Fully-loaded payload is published and readable. (kReresolving counts:
  /// it only mutates source-identity fields, not the loaded payload.)
  auto loaded() const -> bool {
    State s = state();
    return s == State::kLoaded || s == State::kReresolving;
  }

  // Flag set on the logic thread (by Assets::ReloadChangedAssets, after
  // ReResolveSourceClaimed reports a changed source) and consumed on the
  // asset's load thread (which unloads + reloads this asset). Lets the
  // cross-thread reload pass the work along without passing refs across
  // threads.
  auto reload_pending() const -> bool {
    return reload_pending_.load(std::memory_order_relaxed);
  }
  void set_reload_pending(bool val) {
    reload_pending_.store(val, std::memory_order_relaxed);
  }

  // Return name or another identifier. For debugging purposes.
  virtual auto GetName() const -> std::string { return "invalid"; }
  virtual auto GetNameFull() const -> std::string { return GetName(); }

  // Re-resolve this asset's underlying source from its name -- e.g. after
  // the asset-package registry is re-resolved to a different flavor
  // (fallback -> desktop, a language swap, etc.) so the same logical asset
  // now maps to a different CAS blob. If the resolved source changed,
  // update it and return true (the caller then unloads + reloads this
  // asset to pick it up). The default is a no-op returning false, for
  // asset types whose source can't change at runtime. Only called via
  // ReResolveSourceClaimed() (under the kReresolving claim) -- never call
  // directly.
  virtual auto ReResolveSource() -> bool { return false; }

  auto last_used_time() const -> millisecs_t {
    return last_used_time_.load(std::memory_order_relaxed);
  }
  void set_last_used_time(millisecs_t val) {
    last_used_time_.store(val, std::memory_order_relaxed);
  }

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
  // Preload the component's data. CONTRACT: this may run on *any* thread
  // (the assets thread on the pipeline path, but also inline on whatever
  // thread calls Load()/Preload() on-demand -- graphics, audio, logic,
  // bg-dynamics), and preloads of *different* assets may run concurrently
  // on different threads (per-asset claims serialize only this asset).
  // This is deliberate: it covers today's on-demand path and reserves the
  // option of parallel preload workers later. So implementations -- and
  // anything they call transitively, platform code especially -- must not
  // assume a particular thread or exclusive execution; code that touches
  // genuinely non-thread-safe shared state must wrangle its own mutex.
  // Don't interact with per-thread APIs here (no GL calls etc); that
  // belongs in DoLoad().
  virtual void DoPreload() = 0;

  // This is always called by the main thread that uses the component to
  // finish loading. ie: whatever thread is running opengl will call this
  // for textures, audio thread for sounds, etc. As much heavy lifting as
  // possible should be done in DoPreload, but interaction with the
  // corresponding api (gl, al, etc) is done here. (Unlike DoPreload, this
  // *is* thread-pinned by design; that's what the per-type pending-load
  // queues exist for.)
  virtual void DoLoad() = 0;

  // Unload the component. This is always called by the main component
  // thread (same as DoLoad).
  virtual void DoUnload() = 0;

  // Do we still use/need this?
  bool valid_ = false;

 private:
  // --- Claim machinery (all bodies in asset.cc). ---

  // Attempt to CAS from stable state `from` into claim state `to`; on
  // success the calling thread owns the asset (debug: owner recorded,
  // no-GIL-zone armed) and MUST finish via ChainOwned_/PublishOwned_/
  // FailOwned_ on this same thread.
  auto TryClaim_(State from, State to) -> bool;

  // Owner-only: move between claim states (e.g. kPreloading -> kLoading)
  // without releasing ownership.
  void ChainOwned_(State from, State to);

  // Owner-only: finish a claim by publishing stable state `to` and waking
  // any waiters. Releases ownership.
  void PublishOwned_(State from, State to);

  // Owner-only: record `message` as this asset's failure reason, publish
  // kFailed, wake waiters, release ownership. (The caller logs afterwards,
  // outside the claim.)
  void FailOwned_(State from, const std::string& message);

  // Block until the state is stable, returning the stable state observed.
  // Logs a WARNING periodically while stuck waiting (visibility into
  // stalls that used to be silent mutex contention) and a debug log of the
  // total wait afterwards. Returns immediately if already stable.
  auto WaitForStableState_() -> State;

  // Run DoPreload() inside our held kPreloading claim. On success returns
  // true with the claim still held (caller publishes kPreloaded or chains
  // to kLoading). On exception publishes kFailed + logs (once) + returns
  // false (claim released).
  auto PreloadOwned_(bool* did_preload) -> bool;

  // Same shape as PreloadOwned_ for DoLoad() inside a held kLoading (or
  // kUnloading finish-load) claim. Does NOT publish on success.
  auto LoadOwned_(State claim_state, bool* did_load, millisecs_t* load_ms)
      -> bool;

  // Same shape for DoUnload() inside a held kUnloading claim.
  auto UnloadOwned_() -> bool;

  // One-time ERROR log for a just-published failure; call right after
  // FailOwned_ (claim released, so logging is GIL-safe).
  void LogFailure_(const char* phase);

  // Throw a (cheap) exception describing this asset's recorded failure.
  [[noreturn]] void ThrowFailure_();

  // Emits the preload/load logs (and slow-load warning) for steps that
  // just ran. MUST be called with no claim held -- it may take the GIL.
  void EmitLoadLogs_(bool did_preload, bool did_load, millisecs_t load_ms);

#if BA_DEBUG_BUILD
  // Owner-thread bookkeeping for asserts.
  std::atomic<std::thread::id> claim_owner_{};
  void AssertIsClaimOwner_();
#else
  void AssertIsClaimOwner_() {}
#endif

  std::atomic<State> state_{State::kUnloaded};
  std::atomic<bool> reload_pending_{};
  std::atomic<millisecs_t> last_used_time_{};

  // Failure reason; written by the failing claim owner before kFailed is
  // published (so readers observing kFailed see it) and immutable after.
  std::string fail_message_;

  millisecs_t preload_start_time_ = 0;
  millisecs_t preload_end_time_ = 0;
  millisecs_t load_start_time_ = 0;
  millisecs_t load_end_time_ = 0;

  // We keep track of what frame_def we've been added to so we only include
  // a single reference to ourself in it. (Touched only from the logic
  // thread during frame-def construction.)
  int64_t last_frame_def_num_ = 0;

  BA_DISALLOW_CLASS_COPIES(Asset);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSET_H_
