// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/audio.h"

#include <cstdio>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

Audio::Audio() = default;

auto Audio::UseLowQualityAudio() -> bool {
  assert(g_base->InLogicThread());

  // Currently just piggybacking off graphics quality here.
  if (g_core->HeadlessMode() || !g_base->graphics->has_client_context()) {
    return true;
  }

  // We don't have a frame-def to look at so need to calc this ourself; ugh.
  auto quality = Graphics::GraphicsQualityFromRequest(
      g_base->graphics->settings()->graphics_quality,
      g_base->graphics->client_context()->auto_graphics_quality);
  return quality < GraphicsQuality::kMedium;
}

void Audio::Reset() {
  assert(g_base->InLogicThread());
  g_base->audio_server->PushResetCall();
}

void Audio::OnAppStart() { assert(g_base->InLogicThread()); }

void Audio::OnAppSuspend() { assert(g_base->InLogicThread()); }

void Audio::OnAppUnsuspend() { assert(g_base->InLogicThread()); }

void Audio::OnAppShutdown() { assert(g_base->InLogicThread()); }

void Audio::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }

void Audio::StepDisplayTime() { assert(g_base->InLogicThread()); }

void Audio::ApplyAppConfig() {
  assert(g_base->InLogicThread());
  SetVolumes(g_base->app_config->Resolve(AppConfig::FloatID::kMusicVolume),
             g_base->app_config->Resolve(AppConfig::FloatID::kSoundVolume));
}

void Audio::OnScreenSizeChange() { assert(g_base->InLogicThread()); }

void Audio::SetVolumes(float music_volume, float sound_volume) {
  g_base->audio_server->PushSetVolumesCall(music_volume, sound_volume);
}

void Audio::SetSoundPitch(float pitch) {
  sound_pitch_ = pitch;
  g_base->audio_server->PushSetSoundPitchCall(pitch);
}

void Audio::SetListenerPosition(const Vector3f& p) {
  g_base->audio_server->PushSetListenerPositionCall(p);
}

void Audio::SetListenerOrientation(const Vector3f& forward,
                                   const Vector3f& up) {
  g_base->audio_server->PushSetListenerOrientationCall(forward, up);
}

// This stops a particular sound play ID only.
void Audio::PushSourceStopSoundCall(uint32_t play_id) {
  g_base->audio_server->event_loop()->PushCall(
      [play_id] { g_base->audio_server->StopSound(play_id); });
}

void Audio::PushSourceFadeOutCall(uint32_t play_id, uint32_t time) {
  g_base->audio_server->event_loop()->PushCall(
      [play_id, time] { g_base->audio_server->FadeSoundOut(play_id, time); });
}

// Seems we get a false alarm here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "LocalValueEscapesScope"

auto Audio::SourceBeginNew(SoundAsset* for_sound) -> AudioSource* {
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

      // Sources get reused; start each use without a listener of its
      // own.
      s->ClearListenerSpace();
    }
  }
  if (!s) {
    WarnNoSourceAvailable_(for_sound);
  }
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
  return s;
}

void Audio::WarnNoSourceAvailable_(SoundAsset* for_sound) {
  // Nothing to say on headless or a null audio device (no sources ever
  // exist there).
  if (source_pool_empty()) {
    return;
  }
  // Count every drop, including the ones the rate limit below keeps
  // quiet, so a warning can say how many it stands for.
  dropped_plays_since_warn_++;
  // Callers drop the play when we come up empty. One-shot sounds are
  // re-requested on the next event so a dropped one is harmless, but keep
  // this visible: it is the tell for the startup race where sounds get
  // requested before the audio server has finished opening its device
  // (which is what the internal-music retry in ClassicAppMode covers).
  millisecs_t now = g_core->AppTimeMillisecs();
  if (now - last_no_source_warn_time_ < 5000) {
    return;
  }
  last_no_source_warn_time_ = now;
  int dropped = dropped_plays_since_warn_.exchange(0);
  if (!server_ready_) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kWarning,
        "No audio source available; the audio server is still starting up "
        "(device open in progress). Dropping this play request.");
  } else {
    char pitch[16];
    snprintf(pitch, sizeof(pitch), "%.2f", sound_pitch_.load());
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kWarning,
        "No audio source available (all "
            + std::to_string(client_sources_.size())
            + " sources busy). Dropping play of "
            + (for_sound ? "'" + for_sound->GetName() + "'" : "(unnamed)")
            + "; " + std::to_string(dropped)
            + " play(s) dropped since the last report; sound pitch " + pitch
            + ".");
    // Have the audio thread say what they are all doing; this alone
    // doesn't tell a busy moment from a leak.
    g_base->audio_server->PushSourceCensusCall();
  }
}

#pragma clang diagnostic pop

auto Audio::IsSoundPlaying(uint32_t play_id) -> bool {
  uint32_t source_id = AudioServer::SourceIdFromPlayId(play_id);
  assert(client_sources_.size() > source_id);
  client_sources_[source_id]->Lock(2);
  bool result = (client_sources_[source_id]->play_id() == play_id);
  client_sources_[source_id]->Unlock();
  return result;
}

auto Audio::SourceBeginExisting(uint32_t play_id, int debug_id)
    -> AudioSource* {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  uint32_t source_id = AudioServer::SourceIdFromPlayId(play_id);

  // Ok, the audio thread fills in this source list,
  // so theoretically a client could call this before the audio thread
  // has set it up.  However, no one should be trying to get a playing
  // sound unless they've already started playing one which implies
  // everything was set up already. I think we're good.
  assert(g_base->audio->client_sources_.size() > source_id);

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

auto Audio::ShouldPlay(SoundAsset* sound) -> bool {
  millisecs_t time = g_core->AppTimeMillisecs();
  assert(sound);
  return (time - sound->last_play_time() > 50);
}

auto Audio::SafePlayBuiltinSound(BuiltinSoundID sound_id)
    -> std::optional<uint32_t> {
  // Save some time on headless.
  if (g_core->HeadlessMode()) {
    return {};
  }
  if (!g_base->InLogicThread()) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kError,
        "Audio::SafePlayBuiltinSound called from non-logic thread. id="
            + std::to_string(static_cast<int>(sound_id)));
    return {};
  }
  if (!g_base->assets->sys_assets_loaded()) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kWarning,
        "Audio::SafePlayBuiltinSound called before sys assets loaded. id="
            + std::to_string(static_cast<int>(sound_id)));
    return {};
  }
  if (!g_base->assets->IsValidBuiltinSound(sound_id)) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kWarning,
        "Audio::SafePlayBuiltinSound called with invalid sound_id. id="
            + std::to_string(static_cast<int>(sound_id)));
    return {};
  }
  return PlaySound(g_base->assets->BuiltinSound(sound_id));
}

auto Audio::SafePlaySound(SoundAsset* sound) -> std::optional<uint32_t> {
  // Save some time on headless.
  if (g_core->HeadlessMode()) {
    return {};
  }
  if (!g_base->InLogicThread()) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         "Audio::SafePlaySound called from non-logic thread.");
    return {};
  }
  if (!g_base->assets->sys_assets_loaded()) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kWarning,
        "Audio::SafePlaySound called before sys assets loaded.");
    return {};
  }
  return PlaySound(sound);
}

auto Audio::PlaySound(SoundAsset* sound, float volume)
    -> std::optional<uint32_t> {
  assert(g_core);
  assert(g_base->InLogicThread());
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  assert(sound);
  std::optional<uint32_t> play_id{};
  if (!ShouldPlay(sound)) {
    return play_id;
  }
  AudioSource* s = SourceBeginNew(sound);
  if (s) {
    // In vr mode, play non-positional sounds positionally in space roughly
    // where the menu is.
    if (g_core->vr_mode()) {
      s->SetGain(volume);
      s->SetPositional(true);
      float x = 0.0f;
      float y = 4.5f;
      float z = -3.0f;
      s->SetPosition(x, y, z);
      play_id = s->Play(sound);
      s->End();
    } else {
      s->SetGain(volume);
      s->SetPositional(false);
      play_id = s->Play(sound);
      s->End();
    }
  }
  BA_DEBUG_FUNCTION_TIMER_END(20);
  return play_id;
}

auto Audio::PlaySoundAtPosition(SoundAsset* sound, float volume, float x,
                                float y, float z) -> std::optional<uint32_t> {
  assert(g_base->InLogicThread());
  assert(sound);
  std::optional<uint32_t> play_id{};
  if (!ShouldPlay(sound)) {
    return play_id;
  }
  // Run locally.
  if (AudioSource* source = SourceBeginNew(sound)) {
    source->SetGain(volume);
    source->SetPositional(true);
    source->SetPosition(x, y, z);
    play_id = source->Play(sound);
    source->End();
  }
  return play_id;
}

void Audio::AddClientSource(AudioSource* source) {
  client_sources_.push_back(source);
}

void Audio::MakeSourceAvailable(AudioSource* source) {
  available_sources_.push_back(source);
}

}  // namespace ballistica::base
