// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_AUDIO_AUDIO_H_
#define BALLISTICA_AUDIO_AUDIO_H_

#include <map>
#include <mutex>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

/// Client class for audio operations;
/// used by the game and/or other threads.
class Audio {
 public:
  Audio();
  auto Reset() -> void;

  auto SetVolumes(float music_volume, float sound_volume) -> void;

  auto SetListenerPosition(const Vector3f& p) -> void;
  auto SetListenerOrientation(const Vector3f& forward, const Vector3f& up)
      -> void;
  auto SetSoundPitch(float pitch) -> void;

  // Return a pointer to a locked sound source, or nullptr if they're all busy.
  // The sound source will be reset to standard settings (no loop, fade 1, pos
  // 0,0,0, etc.).
  // Send the source any immediate commands and then unlock it.
  // For later modifications, re-retrieve the sound with GetPlayingSound()
  auto SourceBeginNew() -> AudioSource*;

  // If a sound play id is playing, locks and returns its sound source.
  // on success, you must unlock the source once done with it.
  auto SourceBeginExisting(uint32_t play_id, int debug_id) -> AudioSource*;

  // Return true if the sound id is currently valid.  This is not guaranteed
  // to be super accurate, but can be used to determine if a sound is still
  // playing.
  auto IsSoundPlaying(uint32_t play_id) -> bool;

  // Simple one-shot play functions.
  auto PlaySound(SoundData* s, float volume = 1.0f) -> void;
  auto PlaySoundAtPosition(SoundData* sound, float volume, float x, float y,
                           float z) -> void;

  // Call this if you want to prevent repeated plays of the same sound. It'll
  // tell you if the sound has been played recently.  The one-shot sound-play
  // functions use this under the hood. (PlaySound, PlaySoundAtPosition).
  auto ShouldPlay(SoundData* s) -> bool;

  // Hmm; shouldn't these be accessed through the Source class?
  auto PushSourceFadeOutCall(uint32_t play_id, uint32_t time) -> void;
  auto PushSourceStopSoundCall(uint32_t play_id) -> void;

  auto AddClientSource(AudioSource* source) -> void;

  auto MakeSourceAvailable(AudioSource* source) -> void;
  auto available_sources_mutex() -> std::mutex& {
    return available_sources_mutex_;
  }

 private:
  // Flat list of client sources indexed by id.
  std::vector<AudioSource*> client_sources_;

  // List of sources that are ready to use.
  // This is kept filled by the audio thread
  // and used by the client.
  std::vector<AudioSource*> available_sources_;

  // This must be locked whenever accessing the availableSources list.
  std::mutex available_sources_mutex_;
};

}  // namespace ballistica

#endif  // BALLISTICA_AUDIO_AUDIO_H_
