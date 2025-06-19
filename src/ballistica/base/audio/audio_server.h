// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AUDIO_SERVER_H_
#define BALLISTICA_BASE_AUDIO_AUDIO_SERVER_H_

#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

/// Wrangles audio off in its own thread.
class AudioServer {
 public:
  static auto SourceIdFromPlayId(uint32_t play_id) -> uint32_t {
    return play_id & 0xFFFFu;
  }

  static auto PlayCountFromPlayId(uint32_t play_id) -> uint32_t {
    return play_id >> 16u;
  }

  AudioServer();
  void OnMainThreadStartApp();

  void PushSetVolumesCall(float music_volume, float sound_volume);
  void PushSetSoundPitchCall(float val);

  void PushSetListenerPositionCall(const Vector3f& p);
  void PushSetListenerOrientationCall(const Vector3f& forward,
                                      const Vector3f& up);
  void PushResetCall();
  void PushHavePendingLoadsCall();
  void PushComponentUnloadCall(
      const std::vector<Object::Ref<Asset>*>& components);

  void ClearSoundRefDeleteList();

  auto paused() const -> bool { return suspended_; }

  void Shutdown();
  auto shutdown_completed() const { return shutdown_completed_; }

  // Client sources use these to pass settings to the server.
  void PushSourceSetIsMusicCall(uint32_t play_id, bool val);
  void PushSourceSetPositionalCall(uint32_t play_id, bool val);
  void PushSourceSetPositionCall(uint32_t play_id, const Vector3f& p);
  void PushSourceSetGainCall(uint32_t play_id, float val);
  void PushSourceSetFadeCall(uint32_t play_id, float val);
  void PushSourceSetLoopingCall(uint32_t play_id, bool val);
  void PushSourcePlayCall(uint32_t play_id, Object::Ref<SoundAsset>* sound);
  void PushSourceStopCall(uint32_t play_id);
  void PushSourceEndCall(uint32_t play_id);

  // Fade a playing sound out over the given time.  If it is already
  // fading or does not exist, does nothing.
  void FadeSoundOut(uint32_t play_id, uint32_t time);

  // Stop a sound from playing if it exists.
  void StopSound(uint32_t play_id);

  auto event_loop() const -> EventLoop* { return event_loop_; }

  void OnDeviceDisconnected();
  void OpenALSoftLogCallback(const std::string& msg);

 private:
  class ThreadSource_;
  struct Impl_;

  void StartSync_();
  void Start_();

  ~AudioServer();

  void OnThreadSuspend_();
  void OnThreadUnsuspend_();

  void SetSuspended_(bool suspended);

  void SetMusicVolume_(float volume);
  void SetSoundVolume_(float volume);
  void SetSoundPitch_(float pitch);

  void CompleteShutdown_();

  /// If a sound play id is currently playing, return the sound.
  auto GetPlayingSound_(uint32_t play_id) -> ThreadSource_*;

  void Reset_();
  void Process_();
  void ProcessDeviceDisconnects_(seconds_t real_time_seconds);

  void UpdateTimerInterval_();
  void UpdateAvailableSources_();
  void UpdateMusicPlayState_();
  void ProcessSoundFades_();

  // Some threads such as audio hold onto allocated Media-Component-Refs to
  // keep media components alive that they need. Media-Component-Refs,
  // however, must be disposed of in the logic thread, so they are passed
  // back to it through this function.
  void AddSoundRefDelete(const Object::Ref<SoundAsset>* c);

  std::unique_ptr<Impl_> impl_{};
  EventLoop* event_loop_{};
  Timer* process_timer_{};
  float sound_volume_{1.0f};
  float sound_pitch_{1.0f};
  float music_volume_{1.0f};
  float app_active_volume_{1.0f};
  bool have_pending_loads_{};
  bool app_active_{true};
  bool suspended_{};
  bool shutdown_completed_{};
  bool shutting_down_{};
  bool shipped_reconnect_logs_{};
  int al_source_count_{};
  seconds_t last_connected_time_{};
  seconds_t last_reset_attempt_time_{-999.0};
  seconds_t shutdown_start_time_{};
  seconds_t last_started_playing_time_{};
  millisecs_t last_sound_fade_process_time_{};

  std::mutex openalsoft_android_log_mutex_;
  std::string openalsoft_android_log_;

  /// Indexed list of sources.
  std::vector<ThreadSource_*> sources_;
  std::vector<ThreadSource_*> streaming_sources_;
  millisecs_t last_stream_process_time_{};
  millisecs_t last_sanity_check_time_{};

  // Holds refs to all sources.
  // Use sources, not this, for faster iterating.
  std::vector<Object::Ref<ThreadSource_>> sound_source_refs_;
  struct SoundFadeNode_;

  // NOTE: would use unordered_map here but gcc doesn't seem to allow
  // forward-declared template params with them.
  std::map<int, SoundFadeNode_> sound_fade_nodes_;

  // This mutex controls access to our list of media component shared ptrs
  // to delete in the main thread.
  std::mutex sound_ref_delete_list_mutex_;

  // Our list of sound media components to delete via the main thread.
  std::vector<const Object::Ref<SoundAsset>*> sound_ref_delete_list_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_AUDIO_AUDIO_SERVER_H_
