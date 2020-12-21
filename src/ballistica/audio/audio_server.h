// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_AUDIO_AUDIO_SERVER_H_
#define BALLISTICA_AUDIO_AUDIO_SERVER_H_

#include <map>
#include <memory>
#include <vector>

#include "ballistica/core/module.h"

namespace ballistica {

/// A module that handles audio processing.
class AudioServer : public Module {
 public:
  static auto source_id_from_play_id(uint32_t play_id) -> uint32_t {
    return play_id & 0xFFFFu;
  }

  static auto play_count_from_play_id(uint32_t play_id) -> uint32_t {
    return play_id >> 16u;
  }

  explicit AudioServer(Thread* o);

  void PushSetVolumesCall(float music_volume, float sound_volume);
  void PushSetSoundPitchCall(float val);
  void PushSetPausedCall(bool pause);

  void HandleThreadPause() override;
  void HandleThreadResume() override;

  static void BeginInterruption();
  static void EndInterruption();

  void PushSetListenerPositionCall(const Vector3f& p);
  void PushSetListenerOrientationCall(const Vector3f& forward,
                                      const Vector3f& up);
  void PushResetCall();
  void PushHavePendingLoadsCall();
  void PushComponentUnloadCall(
      const std::vector<Object::Ref<MediaComponentData>*>& components);

  /// For use by g_game_module().
  void ClearSoundRefDeleteList();

  auto paused() const -> bool { return paused_; }

  // Client sources use these to pass settings to the server.
  void PushSourceSetIsMusicCall(uint32_t play_id, bool val);
  void PushSourceSetPositionalCall(uint32_t play_id, bool val);
  void PushSourceSetPositionCall(uint32_t play_id, const Vector3f& p);
  void PushSourceSetGainCall(uint32_t play_id, float val);
  void PushSourceSetFadeCall(uint32_t play_id, float val);
  void PushSourceSetLoopingCall(uint32_t play_id, bool val);
  void PushSourcePlayCall(uint32_t play_id, Object::Ref<SoundData>* sound);
  void PushSourceStopCall(uint32_t play_id);
  void PushSourceEndCall(uint32_t play_id);

  // Fade a playing sound out over the given time.  If it is already
  // fading or does not exist, does nothing.
  void FadeSoundOut(uint32_t play_id, uint32_t time);

  // Stop a sound from playing if it exists.
  void StopSound(uint32_t play_id);

 private:
  class ThreadSource;
  struct Impl;

  ~AudioServer() override;

  void SetPaused(bool paused);

  void SetMusicVolume(float volume);
  void SetSoundVolume(float volume);
  void SetSoundPitch(float pitch);
  auto music_volume() -> float { return music_volume_; }
  auto sound_volume() -> float { return sound_volume_; }
  auto sound_pitch() -> float { return sound_pitch_; }

  /// If a sound play id is currently playing, return the sound.
  auto GetPlayingSound(uint32_t play_id) -> ThreadSource*;

  void Reset();
  void Process();

  /// Send a component to the audio thread to delete.
  void DeleteMediaComponent(MediaComponentData* c);

  void UpdateTimerInterval();
  void UpdateAvailableSources();
  void UpdateMusicPlayState();
  void ProcessSoundFades();

  // Some threads such as audio hold onto allocated Media-Component-Refs to keep
  // media components alive that they need.  Media-Component-Refs, however, must
  // be disposed of in the game thread, so they are passed back to it through
  // this function.
  void AddSoundRefDelete(const Object::Ref<SoundData>* c);

  std::unique_ptr<Impl> impl_{};
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
