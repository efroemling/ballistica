// Released under the MIT License. See LICENSE for details.

#include "ballistica/audio/audio_server.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/audio/al_sys.h"
#include "ballistica/audio/audio.h"
#include "ballistica/audio/audio_source.h"
#include "ballistica/audio/audio_streamer.h"
#include "ballistica/audio/ogg_stream.h"
#include "ballistica/game/game.h"
#include "ballistica/generic/timer.h"
#include "ballistica/math/vector3f.h"
#include "ballistica/media/data/sound_data.h"
#include "ballistica/media/media.h"

// Need to move away from OpenAL on Apple stuff.
#if __clang__
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif

namespace ballistica {

// FIXME:  move these to platform.
extern "C" void opensl_pause_playback();
extern "C" void opensl_resume_playback();

#if BA_RIFT_BUILD
extern std::string g_rift_audio_device_name;
#endif

const int kAudioProcessIntervalNormal = 500;
const int kAudioProcessIntervalFade = 50;
const int kAudioProcessIntervalPendingLoad = 1;
const bool kShowInUseSounds = false;

int AudioServer::al_source_count_ = 0;

struct AudioServer::Impl {
  Impl() = default;
  ~Impl() = default;

#if BA_ENABLE_AUDIO
  ALCcontext* alc_context_{};
#endif
};

/// Location for sound emission (server version).
class AudioServer::ThreadSource : public Object {
 public:
  // The id is returned as the lo-word of the identifier
  // returned by "play". If valid is returned as false, there are no
  // hardware channels available (or another error) and the source should
  // not be used.
  ThreadSource(AudioServer* audio_thread, int id, bool* valid);
  ~ThreadSource() override;
  void Reset() {
    SetIsMusic(false);
    SetPositional(true);
    SetPosition(0, 0, 0);
    SetGain(1.0f);
    SetFade(1);
    SetLooping(false);
  }

  /// Set whether a sound is "music".
  /// This influences which volume controls affect it.
  void SetIsMusic(bool m);

  /// Set whether a source is positional.
  /// A non-positional source's position coords are always relative to the
  /// listener - ie: 0, 0, 0 will always be centered.
  void SetPositional(bool p);
  void SetPosition(float x, float y, float z);
  void SetGain(float g);
  void SetFade(float f);
  void SetLooping(bool loop);
  auto Play(const Object::Ref<SoundData>* s) -> uint32_t;
  void Stop();
  auto play_count() -> uint32_t { return play_count_; }
  auto is_streamed() const -> bool { return is_streamed_; }
  auto current_is_music() const -> bool { return current_is_music_; }
  auto want_to_play() const -> bool { return want_to_play_; }
  auto is_actually_playing() const -> bool { return is_actually_playing_; }
  auto play_id() const -> uint32_t {
    return (play_count_ << 16u) | (static_cast<uint32_t>(id_) & 0xFFFFu);
  }
  void UpdateAvailability();
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override;
  auto client_source() const -> AudioSource* { return client_source_.get(); }
  auto source_sound() const -> SoundData* {
    return source_sound_ ? source_sound_->get() : nullptr;
  }

  void UpdatePitch();
  void UpdateVolume();
  void ExecStop();
  void ExecPlay();
  void Update();

 private:
  bool looping_ = false;
  std::unique_ptr<AudioSource> client_source_;
  float fade_ = 1.0f;
  float gain_ = 1.0f;
  AudioServer* audio_thread_;
  bool valid_ = false;
  const Object::Ref<SoundData>* source_sound_ = nullptr;
  int id_;
  uint32_t play_count_ = 0;
  bool is_actually_playing_ = false;
  bool want_to_play_ = false;
#if BA_ENABLE_AUDIO
  ALuint source_ = 0;
#endif
  bool is_streamed_ = false;

  /// Whether we should be designated as "music" next time we play.
  bool is_music_ = false;

  /// Whether currently playing as music.
  bool current_is_music_ = false;

#if BA_ENABLE_AUDIO
  Object::Ref<AudioStreamer> streamer_;
#endif

  friend class AudioServer;
};  // ThreadSource

struct AudioServer::SoundFadeNode {
  uint32_t play_id;
  millisecs_t starttime;
  millisecs_t endtime;
  bool out;
  SoundFadeNode(uint32_t play_id_in, millisecs_t duration_in, bool out_in)
      : play_id(play_id_in),
        starttime(GetRealTime()),
        endtime(GetRealTime() + duration_in),
        out(out_in) {}
};

void AudioServer::SetPaused(bool pause) {
  if (!paused_) {
    if (!pause) {
      Log("Error: got audio unpause request when already unpaused.");
    } else {
#if BA_OSTYPE_IOS_TVOS
      // apple recommends this during audio-interruptions..
      // http://developer.apple.com/library/ios/#documentation/Audio/Conceptual/AudioSessionProgrammingGuide/Cookbook/
      // Cookbook.html#//apple_ref/doc/uid/TP40007875-CH6-SW38
      alcMakeContextCurrent(nullptr);
#endif

// On android lets tell open-sl to stop its processing.
#if BA_OSTYPE_ANDROID
      opensl_pause_playback();
#endif  // BA_OSTYPE_ANDROID

      paused_ = true;
    }
  } else {
    // unpause if requested..
    if (pause) {
      Log("Error: Got audio pause request when already paused.");
    } else {
#if BA_OSTYPE_IOS_TVOS
      // apple recommends this during audio-interruptions..
      // http://developer.apple.com/library/ios/#documentation/Audio/
      // Conceptual/AudioSessionProgrammingGuide/Cookbook/
      // Cookbook.html#//apple_ref/doc/uid/TP40007875-CH6-SW38
#if BA_ENABLE_AUDIO
      alcMakeContextCurrent(impl_->alc_context_);  // hmm is this necessary?..
#endif
#endif
// On android lets tell openal-soft to stop processing.
#if BA_OSTYPE_ANDROID
      opensl_resume_playback();
#endif  // BA_OSTYPE_ANDROID

      paused_ = false;
#if BA_ENABLE_AUDIO
      CHECK_AL_ERROR;
#endif  // BA_ENABLE_AUDIO

      // Go through all of our sources and stop any we've wanted to stop while
      // paused.
      for (auto&& i : sources_) {
        if ((!i->want_to_play()) && (i->is_actually_playing())) {
          i->ExecStop();
        }
      }
    }
  }
}

void AudioServer::PushSourceSetIsMusicCall(uint32_t play_id, bool val) {
  PushCall([this, play_id, val] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->SetIsMusic(val);
    }
  });
}

void AudioServer::PushSourceSetPositionalCall(uint32_t play_id, bool val) {
  PushCall([this, play_id, val] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->SetPositional(val);
    }
  });
}

void AudioServer::PushSourceSetPositionCall(uint32_t play_id,
                                            const Vector3f& p) {
  PushCall([this, play_id, p] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->SetPosition(p.x, p.y, p.z);
    }
  });
}

void AudioServer::PushSourceSetGainCall(uint32_t play_id, float val) {
  PushCall([this, play_id, val] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->SetGain(val);
    }
  });
}

void AudioServer::PushSourceSetFadeCall(uint32_t play_id, float val) {
  PushCall([this, play_id, val] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->SetFade(val);
    }
  });
}

void AudioServer::PushSourceSetLoopingCall(uint32_t play_id, bool val) {
  PushCall([this, play_id, val] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->SetLooping(val);
    }
  });
}

void AudioServer::PushSourcePlayCall(uint32_t play_id,
                                     Object::Ref<SoundData>* sound) {
  PushCall([this, play_id, sound] {
    ThreadSource* s = GetPlayingSound(play_id);

    // If this play command is valid, pass it along.
    // Otherwise, return it immediately for deletion.
    if (s) {
      s->Play(sound);
    } else {
      AddSoundRefDelete(sound);
    }

    // Let's take this opportunity to pass on newly available sources.
    // This way the more things clients are playing, the more
    // tight our source availability checking gets (instead of solely relying on
    // our periodic process() calls).
    UpdateAvailableSources();
  });
}

void AudioServer::PushSourceStopCall(uint32_t play_id) {
  PushCall([this, play_id] {
    ThreadSource* s = GetPlayingSound(play_id);
    if (s) {
      s->Stop();
    }
  });
}

void AudioServer::PushSourceEndCall(uint32_t play_id) {
  PushCall([this, play_id] {
    ThreadSource* s = GetPlayingSound(play_id);
    assert(s);
    s->client_source()->Lock(5);
    s->client_source()->set_client_queue_size(
        s->client_source()->client_queue_size() - 1);
    assert(s->client_source()->client_queue_size() >= 0);
    s->client_source()->Unlock();
  });
}

void AudioServer::PushResetCall() {
  PushCall([this] { Reset(); });
}

void AudioServer::PushSetListenerPositionCall(const Vector3f& p) {
  PushCall([this, p] {
#if BA_ENABLE_AUDIO
    if (!paused_) {
      ALfloat lpos[3] = {p.x, p.y, p.z};
      alListenerfv(AL_POSITION, lpos);
      CHECK_AL_ERROR;
    }
#endif  // BA_ENABLE_AUDIO
  });
}

void AudioServer::PushSetListenerOrientationCall(const Vector3f& forward,
                                                 const Vector3f& up) {
  PushCall([this, forward, up] {
#if BA_ENABLE_AUDIO
    if (!paused_) {
      ALfloat lorient[6] = {forward.x, forward.y, forward.z, up.x, up.y, up.z};
      alListenerfv(AL_ORIENTATION, lorient);
      CHECK_AL_ERROR;
    }
#endif  // BA_ENABLE_AUDIO
  });
}

AudioServer::AudioServer(Thread* thread)
    : Module("audio", thread),
      impl_{new AudioServer::Impl()}
// impl_{std::make_unique<AudioServer::Impl>()}
{
  // we're a singleton...
  assert(g_audio_server == nullptr);
  g_audio_server = this;

  // Get our thread to give us periodic processing time.
  process_timer_ = NewThreadTimer(kAudioProcessIntervalNormal, true,
                                  NewLambdaRunnable([this] { Process(); }));

#if BA_ENABLE_AUDIO

  // Bring up OpenAL stuff.
  {
    const char* alDeviceName = nullptr;

// On the rift build in vr mode we need to make sure we open the rift audio
// device.
#if BA_RIFT_BUILD
    if (IsVRMode()) {
      ALboolean enumeration =
          alcIsExtensionPresent(nullptr, "ALC_ENUMERATE_ALL_EXT");
      if (enumeration == AL_FALSE) {
        Log("OpenAL enumeration extensions missing.");
      } else {
        const ALCchar* devices =
            alcGetString(nullptr, ALC_ALL_DEVICES_SPECIFIER);
        const ALCchar *device = devices, *next = devices + 1;
        size_t len = 0;

        // If the string is blank, we weren't able to find the oculus
        // audio device.  In that case we'll just go with default.
        if (g_rift_audio_device_name != "") {
          // Log("AL Devices list:");
          // Log("----------");
          while (device && *device != '\0' && next && *next != '\0') {
            // These names seem to be things like "OpenAL Soft on FOO"
            // ..we should be able to search for FOO.
            if (strstr(device, g_rift_audio_device_name.c_str())) {
              alDeviceName = device;
            }
            len = strlen(device);
            device += (len + 1);
            next += (len + 2);
          }
          // Log("----------");
        }
      }
    }
#endif  // BA_RIFT_BUILD

    ALCdevice* device;
    device = alcOpenDevice(alDeviceName);
    BA_PRECONDITION(device);
    impl_->alc_context_ = alcCreateContext(device, nullptr);
    BA_PRECONDITION(impl_->alc_context_);
    BA_PRECONDITION(alcMakeContextCurrent(impl_->alc_context_));
    CHECK_AL_ERROR;
  }

  ALfloat listener_pos[] = {0.0f, 0.0f, 0.0f};
  ALfloat listener_vel[] = {0.0f, 0.0f, 0.0f};
  ALfloat listener_ori[] = {0.0f, 0.0f, -1.0f, 0.0f, 1.0f, 0.0f};

  alListenerfv(AL_POSITION, listener_pos);
  alListenerfv(AL_VELOCITY, listener_vel);
  alListenerfv(AL_ORIENTATION, listener_ori);
  CHECK_AL_ERROR;

  // Create our sources.
  int target_source_count = 30;
  for (int i = 0; i < target_source_count; i++) {
    bool valid = false;
    auto s(Object::New<AudioServer::ThreadSource>(this, i, &valid));
    if (valid) {
      s->client_source_ = std::make_unique<AudioSource>(i);
      g_audio->AddClientSource(&(*s->client_source_));
      sound_source_refs_.push_back(s);
      sources_.push_back(&(*s));
    } else {
      Log("Error: Made " + std::to_string(i) + " sources; (wanted "
          + std::to_string(target_source_count) + ").");
      break;
    }
  }
  CHECK_AL_ERROR;

  // Now make available any stopped sources (should be all of them).
  UpdateAvailableSources();

#endif  // BA_ENABLE_AUDIO
}

AudioServer::~AudioServer() {
#if BA_ENABLE_AUDIO
  sound_source_refs_.clear();

  // Take down AL stuff.
  {
    ALCdevice* device;
    BA_PRECONDITION_LOG(alcMakeContextCurrent(nullptr));
    device = alcGetContextsDevice(impl_->alc_context_);
    alcDestroyContext(impl_->alc_context_);
    assert(alcGetError(device) == ALC_NO_ERROR);
    alcCloseDevice(device);
  }
  assert(streaming_sources_.empty());
  assert(al_source_count_ == 0);

#endif  // BA_ENABLE_AUDIO
  delete impl_;
}

void AudioServer::UpdateAvailableSources() {
  for (auto&& i : sources_) {
    i->UpdateAvailability();
  }

// Some sanity checking. Occasionally lets go through our sources
// and see how many are in use, how many are currently locked by the client,
// etc.
#if (BA_DEBUG_BUILD || BA_TEST_BUILD)
  millisecs_t t = GetRealTime();
  if (t - last_sanity_check_time_ > 5000) {
    last_sanity_check_time_ = t;

    int source_count = 0;
    int in_use_source_count = 0;
    std::list<std::string> sounds;
    for (auto&& i : sources_) {
      source_count++;

      if (!i->client_source()->TryLock(4)) {
        in_use_source_count++;

        // If this source has been locked for a long time,
        // that probably means somebody's grabbing a source but never
        // resubmitting it.
        if (t - i->client_source()->last_lock_time() > 10000) {
          Log("Error: Client audio source has been locked for too long; "
              "probably leaked. (debug id "
              + std::to_string(i->client_source()->lock_debug_id()) + ")");
        }
        continue;
      }
      if (!i->client_source()->available()) {
        in_use_source_count++;

        if (explicit_bool(kShowInUseSounds) && i->source_sound()) {
          sounds.push_back((*i->source_sound()).file_name());
        }
      }
      i->client_source()->Unlock();
    }

    if (explicit_bool(kShowInUseSounds)) {
      printf(
          "------------------------------------------\n"
          "%d out of %d sources in use\n",
          in_use_source_count, source_count);
      for (auto&& i : sounds) {
        printf("%s\n", i.c_str());
      }
      fflush(stdout);
    }
  }
#endif
}

void AudioServer::StopSound(uint32_t play_id) {
  uint32_t source = source_id_from_play_id(play_id);
  uint32_t count = play_count_from_play_id(play_id);
  if (source < sources_.size()) {
    if (count == sources_[source]->play_count()) sources_[source]->Stop();
  }
}

auto AudioServer::GetPlayingSound(uint32_t play_id)
    -> AudioServer::ThreadSource* {
  uint32_t source = source_id_from_play_id(play_id);
  uint32_t count = play_count_from_play_id(play_id);
  assert(source < sources_.size());
  if (source < sources_.size()) {
    // If the sound has finished playing or whatnot, we
    // want to make it available to the client as a new sound,
    // not return it here.
    sources_[source]->UpdateAvailability();

    // If it still looks like it's ours, return it...
    if (count == sources_[source]->play_count()) {
      return sources_[source];
    }
  }
  return nullptr;
}

void AudioServer::UpdateTimerInterval() {
  // If we've got pending loads, go into uber-hyperactive mode.
  if (have_pending_loads_) {
    assert(process_timer_);
    process_timer_->SetLength(kAudioProcessIntervalPendingLoad);
  } else {
    // If we're processing fades, run a bit higher-speed than usual
    // for smoothness' sake.
    if (!sound_fade_nodes_.empty()) {
      assert(process_timer_);
      process_timer_->SetLength(kAudioProcessIntervalFade);
    } else {
      // Nothing but normal activity; just run enough to keep
      // buffers filled and whatnot.
      assert(process_timer_);
      process_timer_->SetLength(kAudioProcessIntervalNormal);
    }
  }
}

void AudioServer::SetSoundPitch(float pitch) {
  sound_pitch_ = pitch;
  if (sound_pitch_ < 0.01f) sound_pitch_ = 0.01f;
  for (auto&& i : sources_) {
    i->UpdatePitch();
  }
}

void AudioServer::SetSoundVolume(float volume) {
  sound_volume_ = volume;
  if (sound_volume_ > 3.0f) {
    sound_volume_ = 3.0f;
  }
  if (sound_volume_ < 0) {
    sound_volume_ = 0;
  }
  for (auto&& i : sources_) {
    i->UpdateVolume();
  }
}

void AudioServer::SetMusicVolume(float volume) {
  music_volume_ = volume;
  if (music_volume_ > 3.0f) music_volume_ = 3.0f;
  if (music_volume_ < 0) music_volume_ = 0;
  UpdateMusicPlayState();
  for (auto&& i : sources_) {
    i->UpdateVolume();
  }
}

// Start or stop music playback based on volume/pause-state/etc.
void AudioServer::UpdateMusicPlayState() {
  bool should_be_playing = ((music_volume_ > 0.000001f) && !paused_);

  // Flip any playing music off.
  if (!should_be_playing) {
    for (auto&& i : sources_) {
      if (i->current_is_music() && i->is_actually_playing()) {
        i->ExecStop();
      }
    }
  } else {
    // Flip music back on that should be playing.
    for (auto&& i : sources_) {
      if (i->current_is_music() && i->want_to_play()
          && (!i->is_actually_playing())) {
        i->ExecPlay();
      }
    }
  }
}

void AudioServer::Process() {
  millisecs_t real_time = GetRealTime();

  assert(InAudioThread());

  // If we're paused we don't do nothin'.
  if (!paused_) {
    // Do some loading...
    have_pending_loads_ = g_media->RunPendingAudioLoads();

    // Keep that available-sources list filled.
    UpdateAvailableSources();

    // Update our fading sound volumes.
    if (real_time - last_sound_fade_process_time_ > 50) {
      ProcessSoundFades();
      last_sound_fade_process_time_ = real_time;
    }

    // Update streaming sources.
    if (real_time - last_stream_process_time_ > 100) {
      last_stream_process_time_ = real_time;
      for (auto&& i : streaming_sources_) {
        i->Update();
      }
    }
#if BA_ENABLE_AUDIO
    CHECK_AL_ERROR;
#endif
  }
  UpdateTimerInterval();
}

void AudioServer::Reset() {
  // Stop all playing sounds.
  for (auto&& i : sources_) {
    i->Stop();
  }
  SetSoundPitch(1.0f);
}

void AudioServer::ProcessSoundFades() {
  auto i = sound_fade_nodes_.begin();
  decltype(i) i_next;
  while (i != sound_fade_nodes_.end()) {
    i_next = i;
    i_next++;

    AudioServer::ThreadSource* s = GetPlayingSound(i->second.play_id);
    if (s) {
      if (GetRealTime() > i->second.endtime) {
        StopSound(i->second.play_id);
        sound_fade_nodes_.erase(i);
      } else {
        float fade_val =
            1
            - (static_cast<float>(GetRealTime() - i->second.starttime)
               / static_cast<float>(i->second.endtime - i->second.starttime));
        s->SetFade(fade_val);
      }
    } else {
      sound_fade_nodes_.erase(i);
    }
    i = i_next;
  }
}

void AudioServer::FadeSoundOut(uint32_t play_id, uint32_t time) {
  // Pop a new node on the list (this won't overwrite the old if there is one).
  sound_fade_nodes_.insert(
      std::make_pair(play_id, SoundFadeNode(play_id, time, true)));
}

void AudioServer::DeleteMediaComponent(MediaComponentData* c) {
  assert(InAudioThread());
  c->Unload();
  delete c;
}

AudioServer::ThreadSource::ThreadSource(AudioServer* audio_thread_in, int id_in,
                                        bool* valid_out)
    : id_(id_in), audio_thread_(audio_thread_in) {
#if BA_ENABLE_AUDIO
  assert(valid_out != nullptr);
  CHECK_AL_ERROR;

  // Generate our sources.
  alGenSources(1, &source_);
  ALenum err = alGetError();
  valid_ = (err == AL_NO_ERROR);
  if (!valid_) {
    Log(std::string("Error: AL Error ") + GetALErrorString(err)
        + " on source creation.");
  } else {
    // In vr mode we keep the microphone a bit closer to the camera
    // for realism purposes, so we need stuff louder in general.
    if (IsVRMode()) {
      alSourcef(source_, AL_MAX_DISTANCE, 100);
      alSourcef(source_, AL_REFERENCE_DISTANCE, 7.5f);
    } else {
      // In regular mode our mic is stuck closer to the action
      // so less loudness is needed.
      alSourcef(source_, AL_MAX_DISTANCE, 100);
      alSourcef(source_, AL_REFERENCE_DISTANCE, 5.0f);
    }
    alSourcef(source_, AL_ROLLOFF_FACTOR, 0.3f);
    CHECK_AL_ERROR;
  }
  *valid_out = valid_;
  if (valid_) al_source_count_++;

#endif  // BA_ENABLE_AUDIO
}

AudioServer::ThreadSource::~ThreadSource() {
#if BA_ENABLE_AUDIO

  if (!valid_) {
    return;
  }
  Stop();

  // Remove us from sources list.
  for (auto i = audio_thread_->sources_.begin();
       i != audio_thread_->sources_.end(); ++i) {
    if (*i == this) {
      audio_thread_->sources_.erase(i);
      break;
    }
  }

  assert(!is_actually_playing_ && !want_to_play_);
  assert(!source_sound_);

  alDeleteSources(1, &source_);
  CHECK_AL_ERROR;
  al_source_count_--;

#endif  // BA_ENABLE_AUDIO
}

auto AudioServer::ThreadSource::GetDefaultOwnerThread() const
    -> ThreadIdentifier {
  return ThreadIdentifier::kAudio;
}

void AudioServer::ThreadSource::UpdateAvailability() {
#if BA_ENABLE_AUDIO

  assert(InAudioThread());

  // If it's waiting to be picked up by a client or has pending client commands,
  // skip.
  if (!client_source_->TryLock(6)) {
    return;
  }

  // Already available or has pending client commands; don't change anything.
  if (client_source_->available() || client_source_->client_queue_size() > 0) {
    client_source_->Unlock();
    return;
  }

  // We consider ourselves busy if there's an active looping play command
  // (regardless of its actual physical play state - music could be turned off,
  // stuttering, etc.).
  // If it's non-looping, we check its play state and snatch it if it's not
  // playing.
  bool busy;
  if (looping_ || (is_streamed_ && streamer_.exists() && streamer_->loops())) {
    busy = want_to_play_;
  } else {
    // If our context is paused, we know nothing is playing
    // (and we can't ask AL cuz we have no context).
    if (g_audio_server->paused()) {
      busy = false;
    } else {
      ALint state;
      alGetSourcei(source_, AL_SOURCE_STATE, &state);
      CHECK_AL_ERROR;
      busy = (state == AL_PLAYING);
    }
  }

  // Ok, now if we can get a lock on the availability list, go ahead and
  // make this guy available; give him a new play id and reset his state.
  // If we can't get a lock it's no biggie... we'll come back to this guy later.

  if (!busy) {
    if (g_audio->available_sources_mutex().try_lock()) {
      std::lock_guard<std::mutex> lock(g_audio->available_sources_mutex(),
                                       std::adopt_lock);
      Stop();
      Reset();
#if BA_DEBUG_BUILD
      uint32_t old_play_id = play_id();
#endif
      // Needs to always be a 16 bit value.
      play_count_ = (play_count_ + 1) % 30000;
      assert(old_play_id != play_id());
      client_source_->MakeAvailable(play_id());
    }
  }
  client_source_->Unlock();

#endif  // BA_ENABLE_AUDIO
}

void AudioServer::ThreadSource::Update() {
#if BA_ENABLE_AUDIO
  assert(is_streamed_ && is_actually_playing_);
  streamer_->Update();
#endif
}

void AudioServer::ThreadSource::SetIsMusic(bool m) { is_music_ = m; }

void AudioServer::ThreadSource::SetGain(float g) {
  gain_ = g;
  UpdateVolume();
}

void AudioServer::ThreadSource::SetFade(float f) {
  fade_ = f;
  UpdateVolume();
}

void AudioServer::ThreadSource::SetLooping(bool loop) {
  looping_ = loop;
  if (!g_audio_server->paused()) {
#if BA_ENABLE_AUDIO
    alSourcei(source_, AL_LOOPING, loop);
    CHECK_AL_ERROR;
#endif
  }
}

void AudioServer::ThreadSource::SetPositional(bool p) {
#if BA_ENABLE_AUDIO
  if (!g_audio_server->paused()) {
    // TODO(ericf): Don't allow setting of positional
    //  on stereo sounds - we check this at initial play()
    //  but should do it here too.
    alSourcei(source_, AL_SOURCE_RELATIVE, !p);
    CHECK_AL_ERROR;
  }
#endif
}

void AudioServer::ThreadSource::SetPosition(float x, float y, float z) {
#if BA_ENABLE_AUDIO
  if (!g_audio_server->paused()) {
    bool oob = false;
    if (x < -500) {
      oob = true;
      x = -500;
    } else if (x > 500) {
      oob = true;
      x = 500;
    }
    if (y < -500) {
      oob = true;
      y = -500;
    } else if (y > 500) {
      oob = true;
      y = 500;
    }
    if (z < -500) {
      oob = true;
      z = -500;
    } else if (z > 500) {
      oob = true;
      z = 500;
    }
    if (oob) {
      BA_LOG_ONCE(
          "Error: AudioServer::ThreadSource::SetPosition"
          " got out-of-bounds value.");
    }
    ALfloat source_pos[] = {x, y, z};
    alSourcefv(source_, AL_POSITION, source_pos);
    CHECK_AL_ERROR;
  }
#endif  // BA_ENABLE_AUDIO
}

// Actually begin playback.
void AudioServer::ThreadSource::ExecPlay() {
#if BA_ENABLE_AUDIO

  assert(source_sound_->exists());
  assert((**source_sound_).valid());
  assert((**source_sound_).loaded());
  assert(!is_actually_playing_);
  CHECK_AL_ERROR;

  if (is_streamed_) {
    // Turn off looping on the source - the streamer handles looping for us.
    alSourcei(source_, AL_LOOPING, false);
    CHECK_AL_ERROR;
    looping_ = false;

    // Push us on the list of streaming sources if we're not on it.
    for (auto&& i : audio_thread_->streaming_sources_) {
      if (i == this) {
        throw Exception();
      }
    }
    audio_thread_->streaming_sources_.push_back(this);

    // Make sure stereo sounds aren't positional.
    // This is default behavior on Mac/Win, but we enforce it for linux.
    // (though currently linux stereo sounds play in mono... eww))

    bool do_normal = true;
    // In vr mode, play non-positional sounds positionally in space roughly
    // where the menu is.
    if (IsVRMode()) {
      do_normal = false;
      SetPositional(true);
      SetPosition(0.0f, 4.5f, -3.0f);
    }

    if (do_normal) {
      SetPositional(false);
      SetPosition(0, 0, 0);
    }

    // Play if we're supposed to.
    if (!streamer_->Play()) {
      throw Exception();
    }

  } else {  // Not streamed
    // Make sure stereo sounds aren't positional.
    // This is default behavior on Mac/Win, but we enforce it for linux.
    // (though currently linux stereo sounds play in mono... eww))
    if ((**source_sound_).format() == AL_FORMAT_STEREO16) {
      SetPositional(false);
      SetPosition(0, 0, 0);
    }
    alSourcePlay(source_);
    CHECK_AL_ERROR;
  }
  is_actually_playing_ = true;

#endif  // BA_ENABLE_AUDIO
}

auto AudioServer::ThreadSource::Play(const Object::Ref<SoundData>* sound)
    -> uint32_t {
#if BA_ENABLE_AUDIO

  // FatalError("Testing other thread.");

  assert(InAudioThread());
  assert(sound->exists());

  // Stop whatever we were doing.
  Stop();

  assert(source_sound_ == nullptr);
  source_sound_ = sound;

  if (!g_audio_server->paused()) {
    // Ok, here's where we might start needing to access our media... can't hold
    // off any longer...
    (**source_sound_).Load();

    is_streamed_ = (**source_sound_).is_streamed();
    current_is_music_ = is_music_;

    if (is_streamed_) {
      streamer_ = Object::New<AudioStreamer, OggStream>(
          (**source_sound_).file_name_full().c_str(), source_, looping_);
    } else {
      alSourcei(source_, AL_BUFFER, (**source_sound_).buffer());
    }
    CHECK_AL_ERROR;

    // Always update our volume and pitch here (we may be changing from music to
    // nonMusic, etc.)
    UpdateVolume();
    UpdatePitch();

    bool music_should_play = ((g_audio_server->music_volume_ > 0.000001f)
                              && !g_audio_server->paused());
    if ((!current_is_music_) || music_should_play) {
      ExecPlay();
    }
  }
  want_to_play_ = true;

#endif  // BA_ENABLE_AUDIO

  return play_id();
}

void AudioServer::ThreadSource::ExecStop() {
#if BA_ENABLE_AUDIO
  assert(InAudioThread());
  assert(!g_audio_server->paused());
  assert(is_actually_playing_);
  if (streamer_.exists()) {
    assert(is_streamed_);
    streamer_->Stop();
    for (auto i = audio_thread_->streaming_sources_.begin();
         i != audio_thread_->streaming_sources_.end(); ++i) {
      if (*i == this) {
        audio_thread_->streaming_sources_.erase(i);
        break;
      }
    }
  } else {
    alSourceStop(source_);
    CHECK_AL_ERROR;
  }
  CHECK_AL_ERROR;
  is_actually_playing_ = false;

#endif  // BA_ENABLE_AUDIO
}

// Do a complete stop... take us off the music list, detach our source, etc.
void AudioServer::ThreadSource::Stop() {
#if BA_ENABLE_AUDIO
  assert(g_audio_server);

  // If our context is paused we can't actually stop now; just record our
  // intent.
  if (g_audio_server->paused()) {
    want_to_play_ = false;
  } else {
    if (is_actually_playing_) ExecStop();
    if (streamer_.exists()) {
      streamer_.Clear();
    }
    // If we've got an attached sound, toss it back to the main thread
    // to free up...
    // (we can't kill media-refs outside the main thread)
    if (source_sound_) {
      assert(g_media);
      g_audio_server->AddSoundRefDelete(source_sound_);
      source_sound_ = nullptr;
    }
    want_to_play_ = false;
  }
#endif  // BA_ENABLE_AUDIO
}

void AudioServer::ThreadSource::UpdateVolume() {
#if BA_ENABLE_AUDIO
  assert(InAudioThread());
  if (!g_audio_server->paused()) {
    float val = gain_ * fade_;
    if (current_is_music()) {
      val *= audio_thread_->music_volume() / 7.0f;
    } else {
      val *= audio_thread_->sound_volume();
    }
    alSourcef(source_, AL_GAIN, std::max(0.0f, val));
    CHECK_AL_ERROR;
  }
#endif  // BA_ENABLE_AUDIO
}

void AudioServer::ThreadSource::UpdatePitch() {
#if BA_ENABLE_AUDIO
  assert(InAudioThread());
  if (!g_audio_server->paused()) {
    float val = 1.0f;
    if (current_is_music()) {
    } else {
      val *= audio_thread_->sound_pitch();
    }
    alSourcef(source_, AL_PITCH, val);
    CHECK_AL_ERROR;
  }
#endif  // BA_ENABLE_AUDIO
}

void AudioServer::PushSetVolumesCall(float music_volume, float sound_volume) {
  PushCall([this, music_volume, sound_volume] {
    SetSoundVolume(sound_volume);
    SetMusicVolume(music_volume);
  });
}

void AudioServer::PushSetSoundPitchCall(float val) {
  PushCall([this, val] { SetSoundPitch(val); });
}

void AudioServer::PushSetPausedCall(bool pause) {
  PushCall([this, pause] {
    if (g_buildconfig.ostype_android()) {
      Log("Error: Shouldn't be getting SetPausedCall on android.");
    }
    SetPaused(pause);
  });
}

void AudioServer::PushComponentUnloadCall(
    const std::vector<Object::Ref<MediaComponentData>*>& components) {
  PushCall([this, components] {
    // Unload all components we were passed...
    for (auto&& i : components) {
      (**i).Unload();
    }
    // ...and then ship these pointers back to the game thread, so it can free
    // the references.
    g_game->PushFreeMediaComponentRefsCall(components);
  });
}

void AudioServer::PushHavePendingLoadsCall() {
  PushCall([this] {
    have_pending_loads_ = true;
    UpdateTimerInterval();
  });
}

void AudioServer::AddSoundRefDelete(const Object::Ref<SoundData>* c) {
  {
    std::lock_guard<std::mutex> lock(sound_ref_delete_list_mutex_);
    sound_ref_delete_list_.push_back(c);
  }
  // Now push a call to the game thread to do the deletes.
  g_game->PushCall([] { g_audio_server->ClearSoundRefDeleteList(); });
}

void AudioServer::ClearSoundRefDeleteList() {
  assert(InGameThread());
  std::lock_guard<std::mutex> lock(sound_ref_delete_list_mutex_);
  for (const Object::Ref<SoundData>* i : sound_ref_delete_list_) {
    delete i;
  }
  sound_ref_delete_list_.clear();
}

void AudioServer::BeginInterruption() {
  assert(!InAudioThread());
  g_audio_server->PushSetPausedCall(true);

  // Wait a reasonable amount of time for the thread to act on it.
  millisecs_t t = GetRealTime();
  while (true) {
    if (g_audio_server->paused()) {
      break;
    }
    if (GetRealTime() - t > 1000) {
      Log("Error: Timed out waiting for audio pause.");
      break;
    }
    Platform::SleepMS(2);
  }
}

void AudioServer::HandleThreadPause() { SetPaused(true); }

void AudioServer::HandleThreadResume() { SetPaused(false); }

void AudioServer::EndInterruption() {
  assert(!InAudioThread());
  g_audio_server->PushSetPausedCall(false);

  // Wait a reasonable amount of time for the thread to act on it.
  millisecs_t t = GetRealTime();
  while (true) {
    if (!g_audio_server->paused()) {
      break;
    }
    if (GetRealTime() - t > 1000) {
      Log("Error: Timed out waiting for audio unpause.");
      break;
    }
    Platform::SleepMS(2);
  }
}

}  // namespace ballistica
