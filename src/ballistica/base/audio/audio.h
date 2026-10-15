// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AUDIO_H_
#define BALLISTICA_BASE_AUDIO_AUDIO_H_

#include <atomic>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// How much a play matters when audio sources are contended: with every
/// source busy, a new play takes the source of the oldest one-shot of the
/// lowest priority at or below its own.
///
/// Assets (and hosts, over the wire) can ask for kLower through kHigher.
/// The tiers above that are for the engine alone, so that nothing a
/// package or a server sets can outrank local ui sounds or music.
enum class AudioPriority : int {
  kLower = 0,
  kLow = 1,
  kDefault = 2,
  kHigh = 3,
  kHigher = 4,
  kEngineUI = 5,
  kEngineMusic = 6,
};

/// The highest priority an asset or a host may ask for.
const AudioPriority kAudioPriorityAssetMax = AudioPriority::kHigher;

/// Most plays of one play group allowed at once unless a play says
/// otherwise.
const int kDefaultPlayGroupCap = 4;

/// The most a play arriving from elsewhere (a host) may raise its cap to.
const int kMaxRemotePlayGroupCap = 8;

/// Longest play group name we accept.
const int kMaxPlayGroupNameLength = 64;

/// Per-play overrides of what a sound asset says about itself.
struct AudioPlayOverrides {
  /// Play group to count the play in (see Audio::InternPlayGroup); unset
  /// for the sound's own.
  std::optional<int> group;
  /// Most plays of the group to allow at once; 0 for the default.
  int group_cap{};
  /// Unset for the sound's own.
  std::optional<AudioPriority> priority;
};

/// What is about to be played, for deciding whether it gets a source
/// (and at whose expense).
struct AudioPlaySpec {
  /// May be null (no group, default priority), but pass it when there is
  /// one.
  SoundAsset* sound{};
  /// Whether this will be a looping play. Loops wait at their group cap
  /// where one-shots replace the oldest, and are never taken away once
  /// playing.
  bool looping{};
  AudioPlayOverrides overrides;
};

/// Client class for audio operations;
/// used by the game and/or other threads.
class Audio {
 public:
  Audio();
  void Reset();

  virtual void OnAppStart();
  virtual void OnAppSuspend();
  virtual void OnAppUnsuspend();
  virtual void OnAppShutdown();
  virtual void OnAppShutdownComplete();
  virtual void ApplyAppConfig();
  virtual void OnScreenSizeChange();
  virtual void StepDisplayTime();

  /// Can be keyed off of to cut corners in audio (leaving sounds out, etc.)
  /// Currently just piggybacks off graphics quality settings but this logic
  /// may get fancier in the future.
  auto UseLowQualityAudio() -> bool;

  void SetVolumes(float music_volume, float sound_volume);

  void SetListenerPosition(const Vector3f& p);
  void SetListenerOrientation(const Vector3f& forward, const Vector3f& up);
  void SetSoundPitch(float pitch);

  /// Return a pointer to a locked sound source, or nullptr if they're all busy.
  /// The sound source will be reset to standard settings (no loop, fade 1, pos
  /// 0,0,0, etc.).
  /// Send the source any immediate commands and then unlock it.
  /// For later modifications, re-retrieve the sound with GetPlayingSound()
  ///
  /// Which plays get sources when they are contended:
  ///
  /// - Every play counts toward its play group, and a group has a cap.
  ///   At the cap a one-shot replaces the group's oldest one-shot; a
  ///   loop gets nothing (its owner asks again later).
  /// - With every source busy, the play takes the source of the oldest
  ///   one-shot of the lowest priority at or below its own, if any.
  /// - A playing loop is never taken away.
  ///
  /// To whoever held a source that gets taken, this looks exactly like
  /// its sound having finished: its play id goes stale.
  auto SourceBeginNew(const AudioPlaySpec& spec) -> AudioSource*;

  /// Shorthand for a one-shot of a sound with nothing overridden.
  auto SourceBeginNew(SoundAsset* for_sound = nullptr) -> AudioSource*;

  /// Return the id for a play group name, creating it if need be. Names
  /// are compared as given (see NormalizePlayGroupName). Callable from
  /// any thread.
  auto InternPlayGroup(const std::string& name) -> int;

  /// Return a fresh play group that nothing else is in.
  auto NewUniquePlayGroup() -> int;

  /// The name of a play group (empty for unique ones).
  auto PlayGroupName(int group) -> std::string;

  /// Tidy a play group name from an asset or a peer: trimmed, lowercased
  /// and held to kMaxPlayGroupNameLength.
  static auto NormalizePlayGroupName(const std::string& name) -> std::string;

  /// The play group name a sound gets by default: its asset's base name
  /// less any trailing number, so numbered variants of one sound share a
  /// group ('590:audio/explosion01' -> 'explosion'). Empty when nothing
  /// is left (such sounds get a group of their own).
  static auto AutoPlayGroupName(const std::string& asset_name) -> std::string;

  /// Called by sources as their looping state gets set (a looping play
  /// can't be taken away, whatever was said when it was begun).
  void OnSourceLoopingSet(int source_id, uint32_t play_id, bool looping);

  /// If a sound play id is playing, locks and returns its sound source.
  /// on success, you must unlock the source once done with it.
  auto SourceBeginExisting(uint32_t play_id, int debug_id) -> AudioSource*;

  /// Return true if the sound id is currently valid.  This is not guaranteed
  /// to be super accurate, but can be used to determine if a sound is still
  /// playing.
  auto IsSoundPlaying(uint32_t play_id) -> bool;

  /// Simple one-shot play functions.
  ///
  /// The bare form is for the app's own sounds (ui and such); those play
  /// at AudioPriority::kEngineUI. Sounds played on behalf of content (a
  /// scene, a host) go through the forms taking overrides, which leave
  /// the priority to the sound unless told otherwise.
  auto PlaySound(SoundAsset* s, float volume = 1.0f) -> std::optional<uint32_t>;
  auto PlaySound(SoundAsset* s, float volume,
                 const AudioPlayOverrides& overrides)
      -> std::optional<uint32_t>;
  auto PlaySoundAtPosition(SoundAsset* sound, float volume, float x, float y,
                           float z, const AudioPlayOverrides& overrides = {})
      -> std::optional<uint32_t>;

  /// Overrides for the app's own sounds (see PlaySound).
  static auto EngineUIOverrides() -> AudioPlayOverrides {
    AudioPlayOverrides overrides;
    overrides.priority = AudioPriority::kEngineUI;
    return overrides;
  }

  /// Load and play a builtin sound if possible. Gracefully fail if
  /// not (possibly logging warnings or errors).
  auto SafePlayBuiltinSound(BuiltinSoundID sound_id) -> std::optional<uint32_t>;

  /// SafePlayBuiltinSound's sibling for arbitrary loaded sounds (e.g.
  /// base-asset-set slots): same guards (headless no-op, logic-thread
  /// and sys-assets-loaded checks) without the builtin-id table.
  auto SafePlaySound(SoundAsset* sound) -> std::optional<uint32_t>;

  /// Call this if you want to prevent repeated plays of the same sound. It'll
  /// tell you if the sound has been played recently.  The one-shot sound-play
  /// functions use this under the hood. (PlaySound, PlaySoundAtPosition).
  auto ShouldPlay(SoundAsset* s) -> bool;

  // Hmm; shouldn't these be accessed through the Source class?
  void PushSourceFadeOutCall(uint32_t play_id, uint32_t time);
  void PushSourceStopSoundCall(uint32_t play_id);

  void AddClientSource(AudioSource* source);

  void MakeSourceAvailable(AudioSource* source);
  auto available_sources_mutex() -> std::mutex& {
    return available_sources_mutex_;
  }

  /// Called by the audio server (from the audio thread) once its device is
  /// open and its sources are claimable. Device bring-up runs asynchronously
  /// and can take seconds on some routes (Bluetooth on iOS, for instance),
  /// so until this flips, SourceBeginNew() can only come up empty.
  void set_server_ready() { server_ready_ = true; }
  auto server_ready() const -> bool { return server_ready_; }

  /// True once the server is ready but owns no sources at all (headless
  /// builds and the null-device fallback). No play can ever land there, so
  /// callers should drop quietly rather than wait, retry, or warn.
  /// (client_sources_ is only written before server_ready_ flips, so reading
  /// it after observing the flag is safe.)
  auto source_pool_empty() const -> bool {
    return server_ready_ && client_sources_.empty();
  }

 private:
  /// Log (rate-limited) that SourceBeginNew() found nothing, so dropped
  /// plays are visible instead of silent. Drops below default priority
  /// are the priority system working as designed and only log at debug.
  void WarnNoSourceAvailable_(SoundAsset* for_sound, AudioPriority priority);

  /// What we last started on a source. Current only while the source is
  /// still out with the play id recorded here (sources come back, and
  /// get new play ids, as their sounds finish).
  struct SourceUse_ {
    uint32_t play_id{};
    bool valid{};
    bool looping{};
    int group{-1};
    AudioPriority priority{AudioPriority::kDefault};
    millisecs_t start_time{};
  };
  /// Whether a source is still out on the play we recorded for it
  /// (available_sources_mutex_ must be held).
  auto SourceUseLive_(size_t index) const -> bool;
  /// Take over a source that is out on a play, giving it a fresh play id
  /// (available_sources_mutex_ must be held). Returns it locked.
  auto StealSource_(size_t index) -> AudioSource*;

  /// Indexed by source id; guarded by available_sources_mutex_.
  std::vector<SourceUse_> source_uses_;
  std::mutex play_groups_mutex_;
  std::unordered_map<std::string, int> play_groups_;
  std::vector<std::string> play_group_names_;

  std::atomic<bool> server_ready_{};
  std::atomic<millisecs_t> last_no_source_warn_time_{-99999};
  /// Plays dropped for want of a source since the last warning.
  std::atomic<int> dropped_plays_since_warn_{};
  /// Last value given to SetSoundPitch() (0.4 in slow motion).
  std::atomic<float> sound_pitch_{1.0f};
  /// Flat list of client sources indexed by id.
  std::vector<AudioSource*> client_sources_;

  /// List of sources that are ready to use.
  /// This is kept filled by the audio thread
  /// and used by the client.
  std::vector<AudioSource*> available_sources_;

  /// This must be locked whenever accessing the availableSources list.
  std::mutex available_sources_mutex_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_AUDIO_AUDIO_H_
