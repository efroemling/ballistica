// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_AUDIO_AUDIO_SERVER_H_
#define BALLISTICA_AUDIO_AUDIO_SERVER_H_

#include <map>
#include <mutex>
#include <vector>

#include "ballistica/core/object.h"

namespace ballistica {

/// A module that handles audio processing.
class AudioServer {
 public:
  static auto source_id_from_play_id(uint32_t play_id) -> uint32_t {
    return play_id & 0xFFFFu;
  }

  static auto play_count_from_play_id(uint32_t play_id) -> uint32_t {
    return play_id >> 16u;
  }

  AudioServer();
  auto OnAppStart() -> void;

  auto PushSetVolumesCall(float music_volume, float sound_volume) -> void;
  auto PushSetSoundPitchCall(float val) -> void;
  auto PushSetPausedCall(bool pause) -> void;

  static auto BeginInterruption() -> void;
  static auto EndInterruption() -> void;

  auto PushSetListenerPositionCall(const Vector3f& p) -> void;
  auto PushSetListenerOrientationCall(const Vector3f& forward,
                                      const Vector3f& up) -> void;
  auto PushResetCall() -> void;
  auto PushHavePendingLoadsCall() -> void;
  auto PushComponentUnloadCall(
      const std::vector<Object::Ref<AssetComponentData>*>& components) -> void;

  /// For use by g_logic_module().
  auto ClearSoundRefDeleteList() -> void;

  auto paused() const -> bool { return paused_; }

  // Client sources use these to pass settings to the server.
  auto PushSourceSetIsMusicCall(uint32_t play_id, bool val) -> void;
  auto PushSourceSetPositionalCall(uint32_t play_id, bool val) -> void;
  auto PushSourceSetPositionCall(uint32_t play_id, const Vector3f& p) -> void;
  auto PushSourceSetGainCall(uint32_t play_id, float val) -> void;
  auto PushSourceSetFadeCall(uint32_t play_id, float val) -> void;
  auto PushSourceSetLoopingCall(uint32_t play_id, bool val) -> void;
  auto PushSourcePlayCall(uint32_t play_id, Object::Ref<SoundData>* sound)
      -> void;
  auto PushSourceStopCall(uint32_t play_id) -> void;
  auto PushSourceEndCall(uint32_t play_id) -> void;

  // Fade a playing sound out over the given time.  If it is already
  // fading or does not exist, does nothing.
  auto FadeSoundOut(uint32_t play_id, uint32_t time) -> void;

  // Stop a sound from playing if it exists.
  auto StopSound(uint32_t play_id) -> void;

  auto thread() const -> Thread* { return thread_; }

 private:
  class ThreadSource;
  struct Impl;

  auto OnAppStartInThread() -> void;
  ~AudioServer();

  auto OnThreadPause() -> void;
  auto OnThreadResume() -> void;

  auto SetPaused(bool paused) -> void;

  auto SetMusicVolume(float volume) -> void;
  auto SetSoundVolume(float volume) -> void;
  auto SetSoundPitch(float pitch) -> void;
  auto music_volume() -> float { return music_volume_; }
  auto sound_volume() -> float { return sound_volume_; }
  auto sound_pitch() -> float { return sound_pitch_; }

  /// If a sound play id is currently playing, return the sound.
  auto GetPlayingSound(uint32_t play_id) -> ThreadSource*;

  auto Reset() -> void;
  auto Process() -> void;

  /// Send a component to the audio thread to delete.
  auto DeleteAssetComponent(AssetComponentData* c) -> void;

  auto UpdateTimerInterval() -> void;
  auto UpdateAvailableSources() -> void;
  auto UpdateMusicPlayState() -> void;
  auto ProcessSoundFades() -> void;

  // Some threads such as audio hold onto allocated Media-Component-Refs to keep
  // media components alive that they need.  Media-Component-Refs, however, must
  // be disposed of in the game thread, so they are passed back to it through
  // this function.
  auto AddSoundRefDelete(const Object::Ref<SoundData>* c) -> void;

  // Note: should use unique_ptr for this, but build fails on raspberry pi
  // (gcc 8.3.0). Works on Ubuntu 9.3 so should try again later.
  // std::unique_ptr<Impl> impl_{};
  Impl* impl_{};

  Thread* thread_{};
  Timer* process_timer_{};
  bool have_pending_loads_{};
  bool paused_{};
  millisecs_t last_sound_fade_process_time_{};

  float sound_volume_{1.0f};
  float sound_pitch_{1.0f};
  float music_volume_{1.0f};

  /// Indexed list of sources.
  std::vector<ThreadSource*> sources_;
  std::vector<ThreadSource*> streaming_sources_;
  millisecs_t last_stream_process_time_{};

  // Holds refs to all sources.
  // Use sources, not this, for faster iterating.
  std::vector<Object::Ref<ThreadSource> > sound_source_refs_;
  struct SoundFadeNode;

  // NOTE: would use unordered_map here but gcc doesn't seem to allow
  // forward-declared template params with them.
  std::map<int, SoundFadeNode> sound_fade_nodes_;

  // This mutex controls access to our list of media component shared ptrs to
  // delete in the main thread.
  std::mutex sound_ref_delete_list_mutex_;

  // Our list of sound media components to delete via the main thread.
  std::vector<const Object::Ref<SoundData>*> sound_ref_delete_list_;

  millisecs_t last_sanity_check_time_{};

  static int al_source_count_;
};

}  // namespace ballistica

#endif  // BALLISTICA_AUDIO_AUDIO_SERVER_H_
