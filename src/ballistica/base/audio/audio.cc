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
  AudioPlaySpec spec;
  spec.sound = for_sound;
  return SourceBeginNew(spec);
}

auto Audio::SourceBeginNew(const AudioPlaySpec& spec) -> AudioSource* {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();

  SoundAsset* sound = spec.sound;
  int group = spec.overrides.group.value_or(sound ? sound->play_group() : -1);
  AudioPriority priority = spec.overrides.priority.value_or(
      sound ? sound->priority() : AudioPriority::kDefault);
  int cap = spec.overrides.group_cap > 0 ? spec.overrides.group_cap
                                         : kDefaultPlayGroupCap;

  AudioSource* s = nullptr;
  // Why we came up empty, if we did.
  bool at_group_cap = false;
  // What we took the source from, if anything (for the debug log).
  int stolen_from_group = -1;
  bool stolen = false;
  {
    // Got to make sure to hold this until we've locked the source.
    // Otherwise, theoretically, the audio thread could make our source
    // available again before we can use it.
    std::lock_guard lock(available_sources_mutex_);

    if (source_uses_.size() != client_sources_.size()) {
      source_uses_.resize(client_sources_.size());
    }

    // First the group cap: at it, a one-shot replaces the group's oldest
    // one-shot and a loop gets nothing. (Loops are never taken away, so
    // a group that is all loops has nothing to give a one-shot either.)
    int victim = -1;
    if (group >= 0) {
      int count = 0;
      int oldest = -1;
      for (size_t i = 0; i < source_uses_.size(); ++i) {
        const SourceUse_& use = source_uses_[i];
        if (use.group != group || !SourceUseLive_(i)) {
          continue;
        }
        count++;
        if (!use.looping
            && (oldest < 0
                || use.start_time < source_uses_[oldest].start_time)) {
          oldest = static_cast<int>(i);
        }
      }
      if (count >= cap) {
        if (spec.looping || oldest < 0) {
          at_group_cap = true;
        } else {
          victim = oldest;
        }
      }
    }

    if (!at_group_cap && victim < 0) {
      // If there's an available source, reserve and return it.
      auto i = available_sources_.begin();
      if (i != available_sources_.end()) {
        s = *i;
        available_sources_.erase(i);
        assert(s->available());
        assert(s->client_queue_size() == 0);
        s->set_available(false);
        s->Lock(1);
        assert(!s->available());
        s->set_client_queue_size(s->client_queue_size() + 1);
      } else {
        // Everything is busy: go for the oldest one-shot of the lowest
        // priority at or below ours.
        for (size_t i = 0; i < source_uses_.size(); ++i) {
          const SourceUse_& use = source_uses_[i];
          if (use.looping || use.priority > priority || !SourceUseLive_(i)) {
            continue;
          }
          if (victim < 0 || use.priority < source_uses_[victim].priority
              || (use.priority == source_uses_[victim].priority
                  && use.start_time < source_uses_[victim].start_time)) {
            victim = static_cast<int>(i);
          }
        }
      }
    }

    if (victim >= 0) {
      stolen = true;
      stolen_from_group = source_uses_[victim].group;
      s = StealSource_(victim);
    }

    if (s) {
      // Sources get reused; start each use without a listener of its
      // own.
      s->ClearListenerSpace();

      SourceUse_& use = source_uses_[s->id()];
      use.play_id = s->play_id();
      use.valid = true;
      use.looping = spec.looping;
      use.group = group;
      use.priority = priority;
      use.start_time = g_core->AppTimeMillisecs();
    }
  }
  if (stolen) {
    g_core->logging->Log(
        LogName::kBaAudio, LogLevel::kDebug,
        [this, sound, group, stolen_from_group, priority] {
          return std::string("Took a source from play group '")
                 + PlayGroupName(stolen_from_group) + "' for "
                 + (sound ? "'" + sound->GetName() + "'" : "(unnamed)")
                 + " (group '" + PlayGroupName(group) + "', priority "
                 + std::to_string(static_cast<int>(priority)) + ").";
        });
  }
  // A loop that came up empty waits its turn (its owner asks again), and
  // a group at its cap with nothing to replace is working as intended;
  // only a one-shot that found every source spoken for is a lost sound.
  if (!s && !spec.looping && !at_group_cap) {
    WarnNoSourceAvailable_(sound, priority);
  }
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
  return s;
}

auto Audio::SourceUseLive_(size_t index) const -> bool {
  const SourceUse_& use = source_uses_[index];
  const AudioSource* source = client_sources_[index];
  // (A source's availability and play id only change with
  // available_sources_mutex_ held, which our caller has.)
  return use.valid && !source->available() && source->play_id() == use.play_id;
}

auto Audio::StealSource_(size_t index) -> AudioSource* {
  AudioSource* s = client_sources_[index];

  // The audio thread only hands a source back with this lock and with
  // no client commands pending on it, so from here to our End() being
  // processed it stays ours.
  s->Lock(8);
  assert(!s->available());
  assert(s->play_id() == source_uses_[index].play_id);
  s->set_client_queue_size(s->client_queue_size() + 1);

  // Play ids normally get issued by the audio thread as it hands sources
  // back. Here we issue the next one ourselves and tell it so; the
  // message lands ahead of anything we go on to send for the new play,
  // and behind everything sent for the old one.
  uint32_t old_play_id = s->play_id();
  uint32_t new_play_id = AudioServer::NextPlayId(old_play_id);
  s->Retarget(new_play_id);
  g_base->audio_server->PushSourceRetargetCall(old_play_id, new_play_id);
  return s;
}

void Audio::OnSourceLoopingSet(int source_id, uint32_t play_id, bool looping) {
  std::lock_guard lock(available_sources_mutex_);
  if (static_cast<size_t>(source_id) < source_uses_.size()) {
    SourceUse_& use = source_uses_[source_id];
    if (use.valid && use.play_id == play_id) {
      use.looping = looping;
    }
  }
}

auto Audio::InternPlayGroup(const std::string& name) -> int {
  std::lock_guard lock(play_groups_mutex_);
  auto i = play_groups_.find(name);
  if (i != play_groups_.end()) {
    return i->second;
  }
  // Names can come from hosts; don't let one grow this without end.
  // Past a count nothing real gets near, further names share a group.
  const size_t kMaxNamedPlayGroups = 10000;
  if (play_groups_.size() >= kMaxNamedPlayGroups) {
    return play_groups_.begin()->second;
  }
  int id = static_cast<int>(play_group_names_.size());
  play_group_names_.push_back(name);
  play_groups_[name] = id;
  return id;
}

auto Audio::NewUniquePlayGroup() -> int {
  std::lock_guard lock(play_groups_mutex_);
  int id = static_cast<int>(play_group_names_.size());
  play_group_names_.emplace_back();
  return id;
}

auto Audio::PlayGroupName(int group) -> std::string {
  if (group < 0) {
    return "(none)";
  }
  std::lock_guard lock(play_groups_mutex_);
  if (static_cast<size_t>(group) >= play_group_names_.size()) {
    return "(invalid)";
  }
  const std::string& name = play_group_names_[group];
  return name.empty() ? "(unique " + std::to_string(group) + ")" : name;
}

auto Audio::NormalizePlayGroupName(const std::string& name) -> std::string {
  size_t begin = 0;
  size_t end = name.size();
  while (begin < end && isspace(static_cast<unsigned char>(name[begin]))) {
    begin++;
  }
  while (end > begin && isspace(static_cast<unsigned char>(name[end - 1]))) {
    end--;
  }
  std::string out = name.substr(begin, end - begin);
  if (out.size() > static_cast<size_t>(kMaxPlayGroupNameLength)) {
    out.resize(kMaxPlayGroupNameLength);
  }
  for (char& c : out) {
    c = static_cast<char>(tolower(static_cast<unsigned char>(c)));
  }
  return out;
}

auto Audio::AutoPlayGroupName(const std::string& asset_name) -> std::string {
  // Past any package prefix and directories...
  size_t start = asset_name.find_last_of("/\\:");
  std::string base =
      start == std::string::npos ? asset_name : asset_name.substr(start + 1);
  // ...less any extension (loose files can have one)...
  size_t dot = base.find_last_of('.');
  if (dot != std::string::npos) {
    base.resize(dot);
  }
  // ...and less a trailing number and whatever set it off.
  while (!base.empty() && isdigit(static_cast<unsigned char>(base.back()))) {
    base.pop_back();
  }
  while (!base.empty()
         && (base.back() == '_' || base.back() == '-' || base.back() == ' '
             || base.back() == '.')) {
    base.pop_back();
  }
  return NormalizePlayGroupName(base);
}

void Audio::WarnNoSourceAvailable_(SoundAsset* for_sound,
                                   AudioPriority priority) {
  // Nothing to say on headless or a null audio device (no sources ever
  // exist there).
  if (source_pool_empty()) {
    return;
  }
  // Below-default sounds (footsteps, debris, swishes) are the ones the
  // priority scheme exists to drop when every source is busy; in a big
  // fight that happens constantly and is fine. Only losing something at
  // default priority or above is worth a warning (and a census).
  if (server_ready_ && priority < AudioPriority::kDefault) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kDebug, [for_sound] {
      return "No audio source available; dropping low-priority play of "
             + (for_sound ? "'" + for_sound->GetName() + "'"
                          : std::string("(unnamed)"))
             + ".";
    });
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
  return PlaySound(sound, volume, EngineUIOverrides());
}

auto Audio::PlaySound(SoundAsset* sound, float volume,
                      const AudioPlayOverrides& overrides)
    -> std::optional<uint32_t> {
  assert(g_core);
  assert(g_base->InLogicThread());
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  assert(sound);
  std::optional<uint32_t> play_id{};
  if (!ShouldPlay(sound)) {
    return play_id;
  }
  AudioPlaySpec spec;
  spec.sound = sound;
  spec.overrides = overrides;
  AudioSource* s = SourceBeginNew(spec);
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
                                float y, float z,
                                const AudioPlayOverrides& overrides)
    -> std::optional<uint32_t> {
  assert(g_base->InLogicThread());
  assert(sound);
  std::optional<uint32_t> play_id{};
  if (!ShouldPlay(sound)) {
    return play_id;
  }
  AudioPlaySpec spec;
  spec.sound = sound;
  spec.overrides = overrides;
  // Run locally.
  if (AudioSource* source = SourceBeginNew(spec)) {
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
