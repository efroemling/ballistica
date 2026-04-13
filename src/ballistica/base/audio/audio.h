// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AUDIO_H_
#define BALLISTICA_BASE_AUDIO_AUDIO_H_

#include <map>
#include <mutex>
#include <optional>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

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
  auto SourceBeginNew() -> AudioSource*;

  /// If a sound play id is playing, locks and returns its sound source.
  /// on success, you must unlock the source once done with it.
  auto SourceBeginExisting(uint32_t play_id, int debug_id) -> AudioSource*;

  /// Return true if the sound id is currently valid.  This is not guaranteed
  /// to be super accurate, but can be used to determine if a sound is still
  /// playing.
  auto IsSoundPlaying(uint32_t play_id) -> bool;

  /// Simple one-shot play functions.
  auto PlaySound(SoundAsset* s, float volume = 1.0f) -> std::optional<uint32_t>;
  auto PlaySoundAtPosition(SoundAsset* sound, float volume, float x, float y,
                           float z) -> std::optional<uint32_t>;

  /// Load and play a sys sound if possible. Gracefully fail if not
  /// (possibly logging warnings or errors).
  auto SafePlaySysSound(SysSoundID sound_id) -> std::optional<uint32_t>;

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

 private:
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
