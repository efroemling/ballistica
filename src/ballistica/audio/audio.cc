// Released under the MIT License. See LICENSE for details.

#include "ballistica/audio/audio.h"

#include "ballistica/assets/data/sound_data.h"
#include "ballistica/audio/audio_server.h"
#include "ballistica/audio/audio_source.h"
#include "ballistica/core/thread.h"

namespace ballistica {

Audio::Audio() {}

void Audio::Reset() {
  assert(InLogicThread());
  g_audio_server->PushResetCall();
}

void Audio::SetVolumes(float music_volume, float sound_volume) {
  g_audio_server->PushSetVolumesCall(music_volume, sound_volume);
}

void Audio::SetSoundPitch(float pitch) {
  g_audio_server->PushSetSoundPitchCall(pitch);
}

void Audio::SetListenerPosition(const Vector3f& p) {
  g_audio_server->PushSetListenerPositionCall(p);
}

void Audio::SetListenerOrientation(const Vector3f& forward,
                                   const Vector3f& up) {
  g_audio_server->PushSetListenerOrientationCall(forward, up);
}

// This stops a particular sound play ID only.
void Audio::PushSourceStopSoundCall(uint32_t play_id) {
  g_audio_server->thread()->PushCall(
      [play_id] { g_audio_server->StopSound(play_id); });
}

void Audio::PushSourceFadeOutCall(uint32_t play_id, uint32_t time) {
  g_audio_server->thread()->PushCall(
      [play_id, time] { g_audio_server->FadeSoundOut(play_id, time); });
}

// Seems we get a false alarm here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "LocalValueEscapesScope"

auto Audio::SourceBeginNew() -> AudioSource* {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();

  AudioSource* s = nullptr;
  {
    // Got to make sure to hold this until we've locked the source.
    // Otherwise, theoretically, the audio thread could make our source
    // available again before we can use it.
    std::lock_guard lock(available_sources_mutex_);

    // If there's an available source, reserve and return it.
    auto i = available_sources_.begin();
    if (i != available_sources_.end()) {
      s = *i;
      available_sources_.erase(i);
      assert(s->available());
      assert(s->client_queue_size() == 0);
      s->set_available(false);
    }
    if (s) {
      s->Lock(1);
      assert(!s->available());
      s->set_client_queue_size(s->client_queue_size() + 1);
    }
  }
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
  return s;
}

#pragma clang diagnostic pop

auto Audio::IsSoundPlaying(uint32_t play_id) -> bool {
  uint32_t source_id = AudioServer::source_id_from_play_id(play_id);
  assert(client_sources_.size() > source_id);
  client_sources_[source_id]->Lock(2);
  bool result = (client_sources_[source_id]->play_id() == play_id);
  client_sources_[source_id]->Unlock();
  return result;
}

auto Audio::SourceBeginExisting(uint32_t play_id, int debug_id)
    -> AudioSource* {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  uint32_t source_id = AudioServer::source_id_from_play_id(play_id);

  // Ok, the audio thread fills in this source list,
  // so theoretically a client could call this before the audio thread
  // has set it up.  However, no one should be trying to get a playing
  // sound unless they've already started playing one which implies
  // everything was set up already. I think we're good.
  assert(g_audio->client_sources_.size() > source_id);

  // If this guy's still got the play id they're asking about, lock/return it.
  client_sources_[source_id]->Lock(debug_id);

  if (client_sources_[source_id]->play_id() == play_id) {
    assert(!client_sources_[source_id]->available());
    client_sources_[source_id]->set_client_queue_size(
        client_sources_[source_id]->client_queue_size() + 1);
    BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
    return client_sources_[source_id];
  }

  // No-go; unlock and return empty-handed.
  client_sources_[source_id]->Unlock();

  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
  return nullptr;
}

auto Audio::ShouldPlay(SoundData* sound) -> bool {
  millisecs_t time = GetRealTime();
  assert(sound);
  return (time - sound->last_play_time() > 50);
}

void Audio::PlaySound(SoundData* sound, float volume) {
  assert(InLogicThread());
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  assert(sound);
  if (!ShouldPlay(sound)) {
    return;
  }
  AudioSource* s = SourceBeginNew();
  if (s) {
    // In vr mode, play non-positional sounds positionally in space roughly
    // where the menu is.
    if (IsVRMode()) {
      s->SetGain(volume);
      s->SetPositional(true);
      float x = 0.0f;
      float y = 4.5f;
      float z = -3.0f;
      s->SetPosition(x, y, z);
      s->Play(sound);
      s->End();
    } else {
      s->SetGain(volume);
      s->SetPositional(false);
      s->Play(sound);
      s->End();
    }
  }
  BA_DEBUG_FUNCTION_TIMER_END(20);
}

void Audio::PlaySoundAtPosition(SoundData* sound, float volume, float x,
                                float y, float z) {
  assert(sound);
  if (!ShouldPlay(sound)) {
    return;
  }
  // Run locally.
  if (AudioSource* source = SourceBeginNew()) {
    source->SetGain(volume);
    source->SetPositional(true);
    source->SetPosition(x, y, z);
    source->Play(sound);
    source->End();
  }
}

void Audio::AddClientSource(AudioSource* source) {
  client_sources_.push_back(source);
}

void Audio::MakeSourceAvailable(AudioSource* source) {
  available_sources_.push_back(source);
}

}  // namespace ballistica
