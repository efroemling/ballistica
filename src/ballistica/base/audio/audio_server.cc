// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/audio_server.h"

#include <algorithm>
#include <cstdio>
#include <list>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/shared/buildconfig/buildconfig_common.h"

// Ew fixme.
#if BA_PLATFORM_ANDROID
#include <android/log.h>
#endif

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/al_sys.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_source.h"
#include "ballistica/base/audio/audio_streamer.h"
#include "ballistica/base/audio/ogg_stream.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/math/vector3f.h"

// Need to move away from OpenAL on Apple stuff.
#if __clang__
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif

namespace ballistica::base {

#if BA_RIFT_BUILD
extern std::string g_rift_audio_device_name;
#endif

#if BA_OPENAL_IS_SOFT
LPALCDEVICEPAUSESOFT alcDevicePauseSOFT{};
LPALCDEVICERESUMESOFT alcDeviceResumeSOFT{};
LPALCRESETDEVICESOFT alcResetDeviceSOFT{};
LPALEVENTCALLBACKSOFT alEventCallbackSOFT{};
LPALEVENTCONTROLSOFT alEventControlSOFT{};
// LPALSOFTSETLOGCALLBACK alsoft_set_log_callback{};

#endif

const int kAudioProcessIntervalNormal{500 * 1000};
const int kAudioProcessIntervalFade{50 * 1000};
const int kAudioProcessIntervalPendingLoad{1 * 1000};

#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
const bool kShowInUseSounds{};
#endif

struct AudioServer::Impl_ {
  Impl_() = default;
  ~Impl_() = default;

#if BA_ENABLE_AUDIO
  ALCcontext* alc_context{};
#endif
};

/// Location for sound emission (server version).
class AudioServer::ThreadSource_ : public Object {
 public:
  // The id is returned as the lo-word of the identifier
  // returned by "play". If valid is returned as false, there are no
  // hardware channels available (or another error) and the source should
  // not be used.
  ThreadSource_(AudioServer* audio_thread, int id, bool* valid);
  ~ThreadSource_() override;
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
  auto Play(const Object::Ref<SoundAsset>* s) -> uint32_t;
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
  auto GetDefaultOwnerThread() const -> EventLoopID override;
  auto client_source() const -> AudioSource* { return client_source_.get(); }
  auto source_sound() const -> SoundAsset* {
    return source_sound_ ? source_sound_->get() : nullptr;
  }

  void UpdatePitch();
  void UpdateVolume();
  void ExecStop();
  void ExecPlay();
  void Update();

  void CreateClientSource(int id) {
    client_source_ = std::make_unique<AudioSource>(id);
  }

 private:
  int id_{};
  bool looping_{};
  bool valid_{};
  bool is_actually_playing_{};
  bool want_to_play_{};
  bool is_streamed_{};
  /// Whether we should be designated as "music" next time we play.
  bool is_music_{};
  /// Whether currently playing as music.
  bool current_is_music_{};
  uint32_t play_count_{};
  float fade_{1.0f};
  float gain_{1.0f};
  std::unique_ptr<AudioSource> client_source_;
  AudioServer* audio_server_{};
  const Object::Ref<SoundAsset>* source_sound_{};
#if BA_ENABLE_AUDIO
  ALuint source_{};
  Object::Ref<AudioStreamer> streamer_;
#endif
};  // ThreadSource

AudioServer::AudioServer() : impl_{std::make_unique<AudioServer::Impl_>()} {}

AudioServer::~AudioServer() = default;

void AudioServer::OnMainThreadStartApp() {
  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kAudio);
  g_core->suspendable_event_loops.push_back(event_loop_);

  event_loop_->PushCallSynchronous([this] { StartSync_(); });
  event_loop_->PushCall([this] { Start_(); });
}

#if BA_OPENAL_IS_SOFT
static void ALEventCallback_(ALenum eventType, ALuint object, ALuint param,
                             ALsizei length, const ALchar* message,
                             ALvoid* userParam) noexcept {
  if (eventType == AL_EVENT_TYPE_DISCONNECTED_SOFT) {
    if (g_base->audio_server) {
      g_base->audio_server->event_loop()->PushCall(
          [] { g_base->audio_server->OnDeviceDisconnected(); });
    }
  } else {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                         "Got unexpected OpenAL callback event "
                             + std::to_string(static_cast<int>(eventType)));
  }
}

// FIXME: Should convert this to a generalized OpenALSoft log handler since
// we might want to wire it up on other platforms too.
#if BA_PLATFORM_ANDROID
static void ALCustomAndroidLogCallback_(int severity, const char* msg) {
  // Let's log everything directly that is a warning or worse and store
  // everything else (up to some size limit). We can then explicitly ship
  // the full log if a serious problem occurs.
  if (severity >= ANDROID_LOG_WARN) {
    __android_log_print(severity, "BallisticaKit", "openal-log: %s", msg);
  }
  g_base->audio_server->OpenALSoftLogCallback(msg);
}
#endif  // BA_PLATFORM_ANDROID

void ALCustomLogCallback_(void* userptr, char level, const char* message,
                          int length) noexcept {
  // Log(LogLevel::kInfo, "HELLO FROM GENERIC CUSTOM LOGGER");
}

#endif  // BA_OPENAL_IS_SOFT

void AudioServer::OpenALSoftLogCallback(const std::string& msg) {
  size_t log_cap{1024 * 11};
  std::scoped_lock lock(openalsoft_android_log_mutex_);

  if (openalsoft_android_log_.size() < log_cap) {
    openalsoft_android_log_ += "openal-log("
                               + std::to_string(g_core->AppTimeSeconds())
                               + "s): " + msg + "\n";
    if (openalsoft_android_log_.size() >= log_cap) {
      openalsoft_android_log_ +=
          "\n<max openalsoft log storage size reached>\n";
    }
  }
}
void AudioServer::StartSync_() {
  assert(g_base->InAudioThread());
  // We want to be informed when our event-loop is pausing and unpausing.
  event_loop()->AddSuspendCallback(
      NewLambdaRunnableUnmanaged([this] { OnThreadSuspend_(); }));
  event_loop()->AddUnsuspendCallback(
      NewLambdaRunnableUnmanaged([this] { OnThreadUnsuspend_(); }));
}

void AudioServer::Start_() {
  assert(g_base->InAudioThread());

  // Get our thread to give us periodic processing time.
  process_timer_ =
      event_loop()->NewTimer(kAudioProcessIntervalNormal, true,
                             NewLambdaRunnable([this] { Process_(); }).get());

#if BA_ENABLE_AUDIO

  // Bring up OpenAL stuff.
  {
    // Android-specific workaround; seeing lots of random crashes on Xiaomi
    // Android 11 since switching from OpenALSoft's OpenSL backend to it's
    // Oboe backend (which itself uses AAudio on newer Androids). Trying
    // Oboe's OpenSL backend to see if it heads off the crashes.
    {
      std::string prefix = "Xiaomi ";
      if (g_core->platform->GetDeviceName().compare(0, prefix.size(), prefix)
          == 0) {
        std::string prefix2 = "11";
        if (g_core->platform->GetOSVersionString().compare(0, prefix2.size(),
                                                           prefix2)
            == 0) {
          g_core->logging->Log(
              LogName::kBaAudio, LogLevel::kInfo,
              "Xiaomi Android 11 detected; using OpenSL instead of AAudio.");
          g_core->platform->SetEnv("BA_OBOE_USE_OPENSLES", "1");
        }
      }
    }

    const char* al_device_name{};

// On the rift build in vr mode we need to make sure we open the rift audio
// device.
#if BA_RIFT_BUILD
    if (g_core->vr_mode()) {
      ALboolean enumeration =
          alcIsExtensionPresent(nullptr, "ALC_ENUMERATE_ALL_EXT");
      if (enumeration == AL_FALSE) {
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                             "OpenAL enumeration extensions missing.");
      } else {
        const ALCchar* devices =
            alcGetString(nullptr, ALC_ALL_DEVICES_SPECIFIER);
        const ALCchar *device = devices, *next = devices + 1;
        size_t len = 0;

        // If the string is blank, we weren't able to find the oculus
        // audio device.  In that case we'll just go with default.
        if (g_rift_audio_device_name != "") {
          // Log(LogLevel::kInfo, "AL Devices list:");
          // Log(LogLevel::kInfo, "----------");
          while (device && *device != '\0' && next && *next != '\0') {
            // These names seem to be things like "OpenAL Soft on FOO"
            // ..we should be able to search for FOO.
            if (strstr(device, g_rift_audio_device_name.c_str())) {
              al_device_name = device;
            }
            len = strlen(device);
            device += (len + 1);
            next += (len + 2);
          }
          // Log(LogLevel::kInfo, "----------");
        }
      }
    }
#endif  // BA_RIFT_BUILD

    // Wire up our custom log callback where applicable.
#if BA_PLATFORM_ANDROID
    // alsoft_set_log_callback(ALCustomLogCallback_, nullptr);
    alcSetCustomAndroidLogger(ALCustomAndroidLogCallback_);
#endif

    auto* device = alcOpenDevice(al_device_name);
    if (!device) {
      if (g_buildconfig.platform_android()) {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
            "------------------------"
            " OPENALSOFT-FATAL-ERROR-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-FATAL-ERROR-LOG-END -----------------------");
        openalsoft_android_log_.clear();
      }
      FatalError(
          "No audio devices found. Do you have speakers/headphones/etc. "
          "connected?");
    }

    impl_->alc_context = alcCreateContext(device, nullptr);

    // Android special case: if we fail, try again after a few seconds.
    if (!impl_->alc_context && g_buildconfig.platform_android()) {
      g_core->logging->Log(
          LogName::kBaAudio, LogLevel::kError,
          "Failed creating AL context; waiting and trying again.");
      {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
            "------------------------"
            " OPENALSOFT-ERROR-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-ERROR-LOG-END -----------------------");
        openalsoft_android_log_.clear();
      }
      alcCloseDevice(device);
      g_core->platform->SleepSeconds(2.0);
      device = alcOpenDevice(al_device_name);
      alGetError();  // Clear any errors.

      if (!device) {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
            "------------------------"
            " OPENALSOFT-FATAL-ERROR-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-FATAL-ERROR-LOG-END -----------------------");
        openalsoft_android_log_.clear();
        FatalError("Fallback attempt device create failed.");
      }
      impl_->alc_context = alcCreateContext(device, nullptr);
      if (impl_->alc_context) {
        // For now want to explicitly know if this works.
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                             "Backup AL context creation successful!");
      }
    }

    // Android special case: if we fail, try OpenSL back-end.
    if (!impl_->alc_context && g_buildconfig.platform_android()) {
      g_core->logging->Log(
          LogName::kBaAudio, LogLevel::kError,
          "Failed second time creating AL context; trying OpenSL backend.");
      {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
            "------------------------"
            " OPENALSOFT-ERROR-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-ERROR-LOG-END -----------------------");
        openalsoft_android_log_.clear();
      }
      alcCloseDevice(device);
      g_core->platform->SetEnv("BA_OBOE_USE_OPENSLES", "1");
      device = alcOpenDevice(al_device_name);
      alGetError();  // Clear any errors.
      if (!device) {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
            "------------------------"
            " OPENALSOFT-FATAL-ERROR-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-FATAL-ERROR-LOG-END -----------------------");
        openalsoft_android_log_.clear();
        FatalError("Fallback attempt 2 device create failed.");
      }
      impl_->alc_context = alcCreateContext(device, nullptr);
      if (impl_->alc_context) {
        // For now want to explicitly know if this works.
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                             "Backup AL context creation 2 successful!");
      }
    }

    // Fail at this point if we've got nothing.
    if (!impl_->alc_context) {
      if (g_buildconfig.platform_android()) {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
            "------------------------"
            " OPENALSOFT-FATAL-ERROR-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-FATAL-ERROR-LOG-END -----------------------");
        openalsoft_android_log_.clear();
      }
      FatalError(
          "Unable to init audio. Do you have speakers/headphones/etc. "
          "connected?");
    }
    BA_PRECONDITION_FATAL(impl_->alc_context);
    BA_PRECONDITION_FATAL(alcMakeContextCurrent(impl_->alc_context));
    CHECK_AL_ERROR;

#if BA_OPENAL_IS_SOFT
    // Currently assuming the pause/resume and reset extensions are present.
    // if (alcIsExtensionPresent(device, "ALC_SOFT_pause_device")) {
    alcDevicePauseSOFT = reinterpret_cast<LPALCDEVICEPAUSESOFT>(
        alcGetProcAddress(device, "alcDevicePauseSOFT"));
    BA_PRECONDITION_FATAL(alcDevicePauseSOFT != nullptr);
    alcDeviceResumeSOFT = reinterpret_cast<LPALCDEVICERESUMESOFT>(
        alcGetProcAddress(device, "alcDeviceResumeSOFT"));
    BA_PRECONDITION_FATAL(alcDeviceResumeSOFT != nullptr);
    alcResetDeviceSOFT = reinterpret_cast<LPALCRESETDEVICESOFT>(
        alcGetProcAddress(device, "alcResetDeviceSOFT"));
    BA_PRECONDITION_FATAL(alcResetDeviceSOFT != nullptr);
    alEventCallbackSOFT = reinterpret_cast<LPALEVENTCALLBACKSOFT>(
        alcGetProcAddress(device, "alEventCallbackSOFT"));
    BA_PRECONDITION_FATAL(alEventCallbackSOFT != nullptr);
    alEventControlSOFT = reinterpret_cast<LPALEVENTCONTROLSOFT>(
        alcGetProcAddress(device, "alEventControlSOFT"));
    BA_PRECONDITION_FATAL(alEventControlSOFT != nullptr);
    // alsoft_set_log_callback = reinterpret_cast<LPALSOFTSETLOGCALLBACK>(
    //     alcGetProcAddress(device, "alsoft_set_log_callback"));
    // BA_PRECONDITION_FATAL(alsoft_set_log_callback != nullptr);

    // Ask to be notified when a device is disconnected.
    alEventCallbackSOFT(ALEventCallback_, nullptr);
    CHECK_AL_ERROR;
    ALenum types[] = {AL_EVENT_TYPE_DISCONNECTED_SOFT};
    alEventControlSOFT(1, types, AL_TRUE);
    // } else {
    //   FatalError("ALC_SOFT pause/resume functionality not found.");
    // }
#endif
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
    auto s(Object::New<AudioServer::ThreadSource_>(this, i, &valid));
    if (valid) {
      s->CreateClientSource(i);
      g_base->audio->AddClientSource(&(*s->client_source()));
      sound_source_refs_.push_back(s);
      sources_.push_back(&(*s));
    } else {
      g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                           "Made " + std::to_string(i) + " sources; (wanted "
                               + std::to_string(target_source_count) + ").");
      break;
    }
  }
  CHECK_AL_ERROR;

  // Now make available any stopped sources (should be all of them).
  UpdateAvailableSources_();

  last_started_playing_time_ = g_core->AppTimeSeconds();
#endif  // BA_ENABLE_AUDIO
}

void AudioServer::Shutdown() {
  BA_PRECONDITION(g_base->InAudioThread());
  if (shutting_down_) {
    return;
  }
  shutting_down_ = true;
  shutdown_start_time_ = g_core->AppTimeSeconds();

  // Stop all playing sounds and note the time. We'll then give everything a
  // moment to come to a halt before we tear down the audio context to
  // hopefully minimize errors/pops/etc.
  for (auto&& i : sources_) {
    i->Stop();
  }
  UpdateTimerInterval_();
}

void AudioServer::CompleteShutdown_() {
  assert(g_base->InAudioThread());
  assert(shutting_down_);
  assert(!shutdown_completed_);

#if BA_ENABLE_AUDIO
  ALCboolean check = alcMakeContextCurrent(nullptr);
  if (!check) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                         "Error on alcMakeContextCurrent at shutdown.");
  }
  auto* device = alcGetContextsDevice(impl_->alc_context);
  if (!device) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                         "Unable to get ALCdevice at shutdown.");
  } else {
    alcDestroyContext(impl_->alc_context);
    ALenum err = alcGetError(device);
    if (err != ALC_NO_ERROR) {
      g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                           "Error on AL shutdown.");
    }
    check = alcCloseDevice(device);
    if (!check) {
      g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
                           "Error on alcCloseDevice at shutdown.");
    }
  }
#endif

  shutdown_completed_ = true;
}

struct AudioServer::SoundFadeNode_ {
  uint32_t play_id;
  millisecs_t starttime;
  millisecs_t endtime;
  bool out;
  SoundFadeNode_(uint32_t play_id_in, millisecs_t duration_in, bool out_in)
      : play_id(play_id_in),
        starttime(g_core->AppTimeMillisecs()),
        endtime(g_core->AppTimeMillisecs() + duration_in),
        out(out_in) {}
};

void AudioServer::SetSuspended_(bool suspend) {
  if (!suspended_) {
    if (!suspend) {
      g_core->logging->Log(
          LogName::kBaAudio, LogLevel::kError,
          "Got audio unsuspend request when already unsuspended.");
    } else {
#if BA_PLATFORM_IOS_TVOS
      // apple recommends this during audio-interruptions..
      // http://developer.apple.com/library/ios/#documentation/Audio/Conceptual/AudioSessionProgrammingGuide/Cookbook/
      // Cookbook.html#//apple_ref/doc/uid/TP40007875-CH6-SW38
      alcMakeContextCurrent(nullptr);
#endif

      // Pause OpenALSoft.
#if BA_OPENAL_IS_SOFT
      BA_PRECONDITION_FATAL(alcDevicePauseSOFT != nullptr);
      BA_PRECONDITION_FATAL(impl_ != nullptr && impl_->alc_context != nullptr);
      auto* device = alcGetContextsDevice(impl_->alc_context);
      BA_PRECONDITION_FATAL(device != nullptr);

      try {
        g_core->platform->LowLevelDebugLog(
            "Calling alcDevicePauseSOFT at "
            + std::to_string(g_core->AppTimeSeconds()));
        alcDevicePauseSOFT(device);
      } catch (const std::exception& e) {
        g_core->logging->Log(
            LogName::kBaAudio, LogLevel::kError,
            "Error in alcDevicePauseSOFT at time "
                + std::to_string(g_core->AppTimeSeconds()) + "( playing since "
                + std::to_string(last_started_playing_time_)
                + "): " + g_core->platform->DemangleCXXSymbol(typeid(e).name())
                + " " + e.what());
      } catch (...) {
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                             "Unknown error in alcDevicePauseSOFT");
      }
#endif

      suspended_ = true;
    }
  } else {
    // Unsuspend if requested.
    if (suspend) {
      g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                           "Got audio suspend request when already suspended.");
    } else {
#if BA_PLATFORM_IOS_TVOS
      // Apple recommends this during audio-interruptions.
      // http://developer.apple.com/library/ios/#documentation/Audio/
      // Conceptual/AudioSessionProgrammingGuide/Cookbook/
      // Cookbook.html#//apple_ref/doc/uid/TP40007875-CH6-SW38
#if BA_ENABLE_AUDIO
      alcMakeContextCurrent(impl_->alc_context);  // hmm is this necessary?..
#endif
#endif

// With OpenALSoft lets tell openal-soft to resume processing.
#if BA_OPENAL_IS_SOFT
      BA_PRECONDITION_FATAL(alcDeviceResumeSOFT != nullptr);
      BA_PRECONDITION_FATAL(impl_ != nullptr && impl_->alc_context != nullptr);
      auto* device = alcGetContextsDevice(impl_->alc_context);
      BA_PRECONDITION_FATAL(device != nullptr);
      try {
        g_core->platform->LowLevelDebugLog(
            "Calling alcDeviceResumeSOFT at "
            + std::to_string(g_core->AppTimeSeconds()));
        alcDeviceResumeSOFT(device);
      } catch (const std::exception& e) {
        g_core->logging->Log(
            LogName::kBaAudio, LogLevel::kError,
            "Error in alcDeviceResumeSOFT at time "
                + std::to_string(g_core->AppTimeSeconds()) + ": "
                + g_core->platform->DemangleCXXSymbol(typeid(e).name()) + " "
                + e.what());
      } catch (...) {
        g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                             "Unknown error in alcDeviceResumeSOFT");
      }
#endif
      last_started_playing_time_ = g_core->AppTimeSeconds();
      suspended_ = false;
#if BA_ENABLE_AUDIO
      CHECK_AL_ERROR;
#endif

      // Go through all of our sources and stop any we've wanted to stop
      // while we were suspended.
      for (auto&& i : sources_) {
        if ((!i->want_to_play()) && (i->is_actually_playing())) {
          i->ExecStop();
        }
      }
    }
  }
}

void AudioServer::PushSourceSetIsMusicCall(uint32_t play_id, bool val) {
  event_loop()->PushCall([this, play_id, val] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->SetIsMusic(val);
    }
  });
}

void AudioServer::PushSourceSetPositionalCall(uint32_t play_id, bool val) {
  event_loop()->PushCall([this, play_id, val] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->SetPositional(val);
    }
  });
}

void AudioServer::PushSourceSetPositionCall(uint32_t play_id,
                                            const Vector3f& p) {
  event_loop()->PushCall([this, play_id, p] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->SetPosition(p.x, p.y, p.z);
    }
  });
}

void AudioServer::PushSourceSetGainCall(uint32_t play_id, float val) {
  event_loop()->PushCall([this, play_id, val] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->SetGain(val);
    }
  });
}

void AudioServer::PushSourceSetFadeCall(uint32_t play_id, float val) {
  event_loop()->PushCall([this, play_id, val] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->SetFade(val);
    }
  });
}

void AudioServer::PushSourceSetLoopingCall(uint32_t play_id, bool val) {
  event_loop()->PushCall([this, play_id, val] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->SetLooping(val);
    }
  });
}

void AudioServer::PushSourcePlayCall(uint32_t play_id,
                                     Object::Ref<SoundAsset>* sound) {
  event_loop()->PushCall([this, play_id, sound] {
    ThreadSource_* s = GetPlayingSound_(play_id);

    // If this play command is valid, pass it along.
    // Otherwise, return it immediately for deletion.
    if (s) {
      s->Play(sound);
    } else {
      AddSoundRefDelete(sound);
    }

    // Let's take this opportunity to pass on newly available sources.
    // This way the more things clients are playing, the more
    // tight our source availability checking gets (instead of solely relying
    // on our periodic process() calls).
    UpdateAvailableSources_();
  });
}

void AudioServer::PushSourceStopCall(uint32_t play_id) {
  event_loop()->PushCall([this, play_id] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    if (s) {
      s->Stop();
    }
  });
}

void AudioServer::PushSourceEndCall(uint32_t play_id) {
  event_loop()->PushCall([this, play_id] {
    ThreadSource_* s = GetPlayingSound_(play_id);
    assert(s);
    s->client_source()->Lock(5);
    s->client_source()->set_client_queue_size(
        s->client_source()->client_queue_size() - 1);
    assert(s->client_source()->client_queue_size() >= 0);
    s->client_source()->Unlock();
  });
}

void AudioServer::PushResetCall() {
  event_loop()->PushCall([this] { Reset_(); });
}

void AudioServer::PushSetListenerPositionCall(const Vector3f& p) {
  event_loop()->PushCall([this, p] {
#if BA_ENABLE_AUDIO
    if (!suspended_ && !shutting_down_) {
      ALfloat lpos[3] = {p.x, p.y, p.z};
      alListenerfv(AL_POSITION, lpos);
      CHECK_AL_ERROR;
    }
#endif  // BA_ENABLE_AUDIO
  });
}

void AudioServer::PushSetListenerOrientationCall(const Vector3f& forward,
                                                 const Vector3f& up) {
  event_loop()->PushCall([this, forward, up] {
#if BA_ENABLE_AUDIO
    if (!suspended_ && !shutting_down_) {
      ALfloat lorient[6] = {forward.x, forward.y, forward.z, up.x, up.y, up.z};
      alListenerfv(AL_ORIENTATION, lorient);
      CHECK_AL_ERROR;
    }
#endif  // BA_ENABLE_AUDIO
  });
}

void AudioServer::UpdateAvailableSources_() {
  for (auto&& i : sources_) {
    i->UpdateAvailability();
  }

// Some sanity checking. Occasionally lets go through our sources
// and see how many are in use, how many are currently locked by the client,
// etc.
#if (BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD)
  millisecs_t t = g_core->AppTimeMillisecs();
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
          g_core->logging->Log(
              LogName::kBaAudio, LogLevel::kError,
              "Client audio source has been locked for too long; "
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
  uint32_t source = SourceIdFromPlayId(play_id);
  uint32_t count = PlayCountFromPlayId(play_id);
  if (source < sources_.size()) {
    if (count == sources_[source]->play_count()) {
      sources_[source]->Stop();
    }
  }
}

auto AudioServer::GetPlayingSound_(uint32_t play_id)
    -> AudioServer::ThreadSource_* {
  uint32_t source = SourceIdFromPlayId(play_id);
  uint32_t count = PlayCountFromPlayId(play_id);
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

void AudioServer::UpdateTimerInterval_() {
  // If we've got pending loads or are shutting down, go into
  // uber-hyperactive mode.
  if (have_pending_loads_ || shutting_down_) {
    assert(process_timer_);
    process_timer_->SetLength(kAudioProcessIntervalPendingLoad);
  } else {
    // If we're processing fades, run a bit higher-speed than usual
    // for smoothness' sake.
    if (!sound_fade_nodes_.empty()) {
      assert(process_timer_);
      process_timer_->SetLength(kAudioProcessIntervalFade);
    } else {
      // Nothing but normal activity; just run often enough to keep buffers
      // filled and whatnot.
      assert(process_timer_);
      process_timer_->SetLength(kAudioProcessIntervalNormal);
    }
  }
}

void AudioServer::SetSoundPitch_(float pitch) {
  sound_pitch_ = std::clamp(pitch, 0.1f, 10.0f);
  for (auto&& i : sources_) {
    i->UpdatePitch();
  }
}

void AudioServer::SetSoundVolume_(float volume) {
  sound_volume_ = std::clamp(volume, 0.0f, 3.0f);
  for (auto&& i : sources_) {
    i->UpdateVolume();
  }
}

void AudioServer::SetMusicVolume_(float volume) {
  music_volume_ = std::clamp(volume, 0.0f, 3.0f);
  UpdateMusicPlayState_();
  for (auto&& i : sources_) {
    i->UpdateVolume();
  }
}

// Start or stop music playback based on volume/suspend-state/etc.
void AudioServer::UpdateMusicPlayState_() {
  bool should_be_playing =
      (music_volume_ > 0.000001f && !suspended_ && !shutting_down_);

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

void AudioServer::ProcessDeviceDisconnects_(seconds_t real_time_seconds) {
#if BA_OPENAL_IS_SOFT
  // If our device has been disconnected, try to reconnect it
  // periodically.
  auto* device = alcGetContextsDevice(impl_->alc_context);
  BA_PRECONDITION_FATAL(device != nullptr);
  ALCint connected{-1};
  alcGetIntegerv(device, ALC_CONNECTED, sizeof(connected), &connected);
  CHECK_AL_ERROR;
  if (connected != 0) {
    last_connected_time_ = real_time_seconds;
    // reconnect_fail_count_ = 0;
  }
  // else {
  // reconnect_fail_count_ = 0;
  // }

  // Retry less often once we've been failing for a while.
  seconds_t retry_interval =
      real_time_seconds - last_connected_time_ > 20.0 ? 10.0 : 3.0;

  if (connected == 0
      && real_time_seconds - last_reset_attempt_time_ >= retry_interval) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kInfo,
                         "OpenAL device disconnected; resetting...");
    if (g_buildconfig.platform_android()) {
      std::scoped_lock lock(openalsoft_android_log_mutex_);
      openalsoft_android_log_ +=
          "DEVICE DISCONNECT DETECTED; ATTEMPTING RESET\n";
    }
    last_reset_attempt_time_ = real_time_seconds;
    BA_PRECONDITION_FATAL(alcResetDeviceSOFT != nullptr);
    auto result = alcResetDeviceSOFT(device, nullptr);
    CHECK_AL_ERROR;

    // Log(LogLevel::kInfo, std::string("alcResetDeviceSOFT returned ")
    //                          + (result == ALC_TRUE ? "ALC_TRUE" :
    //                          "ALC_FALSE"));

    // Check to see if this brought the device back.
    // ALCint connected{-1};
    // alcGetIntegerv(device, ALC_CONNECTED, sizeof(connected), &connected);
    // CHECK_AL_ERROR;

    // If we were successful, clear out the wait for the next reset.
    // Otherwise plugging in headphones and then unplugging them immediately
    // will result in 10 seconds of silence.
    if (result == ALC_TRUE) {
      // last_reset_attempt_time_ = -999.0;
      if (g_buildconfig.platform_android()) {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        openalsoft_android_log_ += "DEVICE RESET CALL SUCCESSFUL\n";
      }
    } else {
      if (g_buildconfig.platform_android()) {
        std::scoped_lock lock(openalsoft_android_log_mutex_);
        openalsoft_android_log_ += "DEVICE RESET CALL FAILED\n";
      }
    }

    // If we're ever *not* immediately successful, flip on reporting to try
    // and figure out what's going on. After that point we'll report subsequent
    // if (connected == 0) {
    //   report_reset_results_ = true;
    // }
    // if (report_reset_results_ && reset_result_reports_remaining_ > 0) {
    //   reset_result_reports_remaining_ -= 1;
    //   if (connected != 0) {
    //     Log(LogLevel::kInfo,
    //         "alcResetDeviceSOFT successfully reconnected device.");
    //   } else {
    //     Log(LogLevel::kError, "alcResetDeviceSOFT failed to reconnect
    //     device.");
    //   }
    //   if (g_buildconfig.platform_android()) {
    //     std::scoped_lock lock(openalsoft_android_log_mutex_);
    //     Log(LogLevel::kWarning,
    //         "------------------------"
    //         " OPENALSOFT-RECONNECT-LOG-BEGIN ----------------------\n"
    //             + openalsoft_android_log_
    //         + "\n-------------------------"
    //           " OPENALSOFT-RECONNECT-LOG-END -----------------------");
    //     openalsoft_android_log_.clear();
    //   }
    // }
  }

  // If we've failed at reconnecting for a while, ship logs once.
  if (real_time_seconds - last_connected_time_ > 20.0
      && !shipped_reconnect_logs_) {
    shipped_reconnect_logs_ = true;
    if (g_buildconfig.platform_android()) {
      std::scoped_lock lock(openalsoft_android_log_mutex_);
      g_core->logging->Log(LogName::kBaAudio, LogLevel::kWarning,
            "Have been disconnected for a while; dumping OpenAL log.\n"
            "------------------------"
            " OPENALSOFT-RECONNECT-LOG-BEGIN ----------------------\n"
                + openalsoft_android_log_
            + "\n-------------------------"
              " OPENALSOFT-RECONNECT-LOG-END -----------------------");
      openalsoft_android_log_.clear();
    }
  }
#endif  // BA_OPENAL_IS_SOFT
}

void AudioServer::OnDeviceDisconnected() {
  assert(g_base->InAudioThread());
  // All we do here is run an explicit Process_. This only saves us a half
  // second or so over letting the timer do it, but hey we'll take it.
  Process_();
}

void AudioServer::Process_() {
  assert(g_base->InAudioThread());
  seconds_t real_time_seconds = g_core->AppTimeSeconds();
  millisecs_t real_time_millisecs = real_time_seconds * 1000;

  // Only do real work if we're in normal running mode.
  if (!suspended_ && !shutting_down_) {
    ProcessDeviceDisconnects_(real_time_seconds);

    // Do some loading...
    have_pending_loads_ = g_base->assets->RunPendingAudioLoads();

    // Keep that available-sources list filled.
    UpdateAvailableSources_();

    // Update our fading sound volumes.
    if (real_time_millisecs - last_sound_fade_process_time_ > 50) {
      ProcessSoundFades_();
      last_sound_fade_process_time_ = real_time_millisecs;
    }

    // Update streaming sources.
    if (real_time_millisecs - last_stream_process_time_ > 100) {
      last_stream_process_time_ = real_time_millisecs;
      for (auto&& i : streaming_sources_) {
        i->Update();
      }
    }

    // If the app has switched active/inactive state, update our volumes (we
    // may silence our audio in these cases).
    auto app_active = g_base->app_active();
    if (app_active != app_active_) {
      app_active_ = app_active;
      app_active_volume_ =
          (!app_active && g_base->app_adapter->ShouldSilenceAudioForInactive())
              ? 0.0f
              : 1.0f;
      for (auto&& i : sources_) {
        i->UpdateVolume();
      }
    }

#if BA_ENABLE_AUDIO
    CHECK_AL_ERROR;
#endif
  }
  UpdateTimerInterval_();

  // In my brief unscientific testing with my airpods, a 0.2 second delay
  // between stopping sounds and killing the sound-system seems to be enough
  // for the mixer to spit out some silence so we don't hear sudden cut-offs
  // in one or both ears.
  if (shutting_down_ && !shutdown_completed_) {
    if (g_core->AppTimeSeconds() - shutdown_start_time_ > 0.2) {
      CompleteShutdown_();
    }
  }
}

void AudioServer::Reset_() {
  // Note: up until version 1.7.20, the audio server would stop all playing
  // sounds when reset. This would prevent against long sounds playing at
  // the end of a game session 'bleeding' into the main menu/etc. However,
  // these days, resets are becoming more common due to app-mode switches
  // and whatnot, and the chances of cutting off an intended ui sound are
  // growing. In particular, a 'power down' sound at launch when a plugin is
  // no longer found is being cut off by the initial app-mode switch.

  // So I'm disabling the stop behavior for now and hoping that doesn't bite
  // us. Ideally we should have sounds contexts so that we can stop sounds
  // for a particular scene when that scene ends/etc. This could also
  // address our current problem where epic mode screws up the pitch on our
  // UI sounds.

  if (explicit_bool(false)) {
    // Stop all playing sounds.
    for (auto&& i : sources_) {
      i->Stop();
    }
  }
  // Still need to reset this though or epic-mode will screw us up.
  SetSoundPitch_(1.0f);
}

void AudioServer::ProcessSoundFades_() {
  auto i = sound_fade_nodes_.begin();
  decltype(i) i_next;
  while (i != sound_fade_nodes_.end()) {
    i_next = i;
    i_next++;

    AudioServer::ThreadSource_* s = GetPlayingSound_(i->second.play_id);
    if (s) {
      if (g_core->AppTimeMillisecs() > i->second.endtime) {
        StopSound(i->second.play_id);
        sound_fade_nodes_.erase(i);
      } else {
        float fade_val =
            1
            - (static_cast<float>(g_core->AppTimeMillisecs()
                                  - i->second.starttime)
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
  // Pop a new node on the list (this won't overwrite the old if there is
  // one).
  sound_fade_nodes_.insert(
      std::make_pair(play_id, SoundFadeNode_(play_id, time, true)));
}

// void AudioServer::DeleteAssetComponent_(Asset* c) {
//   assert(g_base->InAudioThread());
//   c->Unload();
//   delete c;
// }

AudioServer::ThreadSource_::ThreadSource_(AudioServer* audio_server_in,
                                          int id_in, bool* valid_out)
    : id_(id_in), audio_server_(audio_server_in) {
#if BA_ENABLE_AUDIO
  assert(g_core);
  assert(valid_out != nullptr);
  CHECK_AL_ERROR;

  // Generate our sources.
  alGenSources(1, &source_);
  ALenum err = alGetError();
  valid_ = (err == AL_NO_ERROR);
  if (!valid_) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         std::string("AL Error ") + GetALErrorString(err)
                             + " on source creation.");
  } else {
    // In vr mode we keep the microphone a bit closer to the camera
    // for realism purposes, so we need stuff louder in general.
    if (g_core->vr_mode()) {
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
  if (valid_) {
    g_base->audio_server->al_source_count_++;
  }

#endif  // BA_ENABLE_AUDIO
}

AudioServer::ThreadSource_::~ThreadSource_() {
#if BA_ENABLE_AUDIO

  if (!valid_) {
    return;
  }
  Stop();

  // Remove us from sources list.
  for (auto i = audio_server_->sources_.begin();
       i != audio_server_->sources_.end(); ++i) {
    if (*i == this) {
      audio_server_->sources_.erase(i);
      break;
    }
  }

  assert(!is_actually_playing_ && !want_to_play_);
  assert(!source_sound_);

  alDeleteSources(1, &source_);
  CHECK_AL_ERROR;
  g_base->audio_server->al_source_count_--;

#endif  // BA_ENABLE_AUDIO
}

auto AudioServer::ThreadSource_::GetDefaultOwnerThread() const -> EventLoopID {
  return EventLoopID::kAudio;
}

void AudioServer::ThreadSource_::UpdateAvailability() {
#if BA_ENABLE_AUDIO

  assert(g_base->InAudioThread());

  // If it's waiting to be picked up by a client or has pending client
  // commands, skip.
  if (!client_source_->TryLock(6)) {
    return;
  }

  // Already available or has pending client commands; don't change anything.
  if (client_source_->available() || client_source_->client_queue_size() > 0) {
    client_source_->Unlock();
    return;
  }

  // We consider ourselves busy if there's an active looping play command
  // (regardless of its actual physical play state - music could be turned
  // off, stuttering, etc.). If it's non-looping, we check its play state and
  // snatch it if it's not playing.
  bool busy;
  if (looping_ || (is_streamed_ && streamer_.exists() && streamer_->loops())) {
    busy = want_to_play_;
  } else {
    // If our context is suspended, we know nothing is playing
    // (and we can't ask AL cuz we have no context).
    if (g_base->audio_server->suspended_
        || g_base->audio_server->shutting_down_) {
      busy = false;
    } else {
      ALint state;
      alGetSourcei(source_, AL_SOURCE_STATE, &state);
      CHECK_AL_ERROR;
      busy = (state == AL_PLAYING);
    }
  }

  // Ok, now if we can get a lock on the availability list, go ahead and
  // make this guy available; give him a new play id and reset his state. If
  // we can't get a lock it's no biggie... we'll come back to this guy
  // later.

  if (!busy) {
    if (g_base->audio->available_sources_mutex().try_lock()) {
      std::lock_guard lock(g_base->audio->available_sources_mutex(),
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

void AudioServer::ThreadSource_::Update() {
#if BA_ENABLE_AUDIO
  assert(is_streamed_ && is_actually_playing_);
  streamer_->Update();
#endif
}

void AudioServer::ThreadSource_::SetIsMusic(bool m) { is_music_ = m; }

void AudioServer::ThreadSource_::SetGain(float g) {
  gain_ = g;
  UpdateVolume();
}

void AudioServer::ThreadSource_::SetFade(float f) {
  fade_ = f;
  UpdateVolume();
}

void AudioServer::ThreadSource_::SetLooping(bool loop) {
  looping_ = loop;
#if BA_ENABLE_AUDIO
  if (g_base->audio_server->suspended_
      || g_base->audio_server->shutting_down_) {
    return;
  }
  alSourcei(source_, AL_LOOPING, loop);
  CHECK_AL_ERROR;
#endif
}

void AudioServer::ThreadSource_::SetPositional(bool p) {
#if BA_ENABLE_AUDIO
  if (g_base->audio_server->suspended_
      || g_base->audio_server->shutting_down_) {
    return;
  }
  // TODO(ericf): Don't allow setting of positional
  //  on stereo sounds - we check this at initial play()
  //  but should do it here too.
  alSourcei(source_, AL_SOURCE_RELATIVE, !p);
  CHECK_AL_ERROR;

#endif
}

void AudioServer::ThreadSource_::SetPosition(float x, float y, float z) {
#if BA_ENABLE_AUDIO
  if (g_base->audio_server->suspended_
      || g_base->audio_server->shutting_down_) {
    return;
  }
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
    BA_LOG_ONCE(LogName::kBaAudio, LogLevel::kError,
                "AudioServer::ThreadSource::SetPosition"
                " got out-of-bounds value.");
  }
  ALfloat source_pos[] = {x, y, z};
  alSourcefv(source_, AL_POSITION, source_pos);
  CHECK_AL_ERROR;

#endif  // BA_ENABLE_AUDIO
}

auto AudioServer::ThreadSource_::Play(const Object::Ref<SoundAsset>* sound)
    -> uint32_t {
#if BA_ENABLE_AUDIO

  assert(g_base->InAudioThread());
  assert(sound->exists());

  // Stop whatever we were doing.
  Stop();

  assert(source_sound_ == nullptr);
  source_sound_ = sound;

  if (!g_base->audio_server->suspended_
      && !g_base->audio_server->shutting_down_) {
    // Ok, here's where we might start needing to access our media... can't
    // hold off any longer...
    (**source_sound_).Load();

    is_streamed_ = (**source_sound_).is_streamed();
    current_is_music_ = is_music_;

    if (is_streamed_) {
      streamer_ = Object::New<AudioStreamer, OggStream>(
          (**source_sound_).file_name_full().c_str(), source_, looping_);
    } else {
      alSourcei(source_, AL_BUFFER,
                static_cast<ALint>((**source_sound_).buffer()));
    }
    CHECK_AL_ERROR;

    // Always update our volume and pitch here (we may be changing from
    // music to nonMusic, etc.)
    UpdateVolume();
    UpdatePitch();

    bool music_should_play = ((g_base->audio_server->music_volume_ > 0.000001f)
                              && !g_base->audio_server->suspended_
                              && !g_base->audio_server->shutting_down_);
    if ((!current_is_music_) || music_should_play) {
      ExecPlay();
    }
  }
  want_to_play_ = true;

#endif  // BA_ENABLE_AUDIO

  return play_id();
}

// Actually begin playback.
void AudioServer::ThreadSource_::ExecPlay() {
#if BA_ENABLE_AUDIO

  assert(g_core);
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
    for (auto&& i : audio_server_->streaming_sources_) {
      if (i == this) {
        throw Exception();
      }
    }
    audio_server_->streaming_sources_.push_back(this);

    // Make sure stereo sounds aren't positional.
    // This is default behavior on Mac/Win, but we enforce it for linux.
    // (though currently linux stereo sounds play in mono... eww))

    bool do_normal = true;
    // In vr mode, play non-positional sounds positionally in space roughly
    // where the menu is.
    if (g_core->vr_mode()) {
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

// Do a complete stop... take us off the music list, detach our source, etc.
void AudioServer::ThreadSource_::Stop() {
#if BA_ENABLE_AUDIO
  assert(g_base->audio_server);

  // If our context is suspended we can't actually stop now; just record our
  // intent.
  if (g_base->audio_server->suspended_) {
    want_to_play_ = false;
  } else {
    if (is_actually_playing_) {
      ExecStop();
    }
    if (streamer_.exists()) {
      streamer_.Clear();
    }
    // If we've got an attached sound, toss it back to the main thread
    // to free up...
    // (we can't kill media-refs outside the main thread)
    if (source_sound_) {
      assert(g_base->assets);
      g_base->audio_server->AddSoundRefDelete(source_sound_);
      source_sound_ = nullptr;
    }
    want_to_play_ = false;
  }
#endif  // BA_ENABLE_AUDIO
}

void AudioServer::ThreadSource_::ExecStop() {
#if BA_ENABLE_AUDIO
  assert(g_base->InAudioThread());
  assert(!g_base->audio_server->suspended_);
  assert(is_actually_playing_);
  if (streamer_.exists()) {
    assert(is_streamed_);
    streamer_->Stop();
    for (auto i = audio_server_->streaming_sources_.begin();
         i != audio_server_->streaming_sources_.end(); ++i) {
      if (*i == this) {
        audio_server_->streaming_sources_.erase(i);
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

void AudioServer::ThreadSource_::UpdateVolume() {
#if BA_ENABLE_AUDIO
  assert(g_base->InAudioThread());
  if (audio_server_->suspended_ || audio_server_->shutting_down_) {
    return;
  }
  float val = gain_ * fade_;
  val *= audio_server_->app_active_volume_;

  if (current_is_music()) {
    val *= audio_server_->music_volume_ / 7.0f;
  } else {
    val *= audio_server_->sound_volume_;
  }
  alSourcef(source_, AL_GAIN, std::max(0.0f, val));
  CHECK_AL_ERROR;

#endif  // BA_ENABLE_AUDIO
}

void AudioServer::ThreadSource_::UpdatePitch() {
#if BA_ENABLE_AUDIO
  assert(g_base->InAudioThread());
  if (g_base->audio_server->suspended_
      || g_base->audio_server->shutting_down_) {
    return;
  }
  float val = 1.0f;
  if (current_is_music()) {
  } else {
    val *= audio_server_->sound_pitch_;
  }
  alSourcef(source_, AL_PITCH, val);
  CHECK_AL_ERROR;

#endif  // BA_ENABLE_AUDIO
}

void AudioServer::PushSetVolumesCall(float music_volume, float sound_volume) {
  event_loop()->PushCall([this, music_volume, sound_volume] {
    SetSoundVolume_(sound_volume);
    SetMusicVolume_(music_volume);
  });
}

void AudioServer::PushSetSoundPitchCall(float val) {
  event_loop()->PushCall([this, val] { SetSoundPitch_(val); });
}

void AudioServer::PushComponentUnloadCall(
    const std::vector<Object::Ref<Asset>*>& components) {
  event_loop()->PushCall([components] {
    // Unload the components.
    for (auto&& i : components) {
      (**i).Unload();
    }
    // Then kick them over to the logic thread for deletion.
    g_base->logic->event_loop()->PushCall([components] {
      for (auto&& i : components) {
        delete i;
      }
    });
  });
}

void AudioServer::PushHavePendingLoadsCall() {
  event_loop()->PushCall([this] {
    have_pending_loads_ = true;
    UpdateTimerInterval_();
  });
}

void AudioServer::AddSoundRefDelete(const Object::Ref<SoundAsset>* c) {
  {
    std::scoped_lock lock(sound_ref_delete_list_mutex_);
    sound_ref_delete_list_.push_back(c);
  }
  // Now push a call to the logic thread to do the deletes.
  g_base->logic->event_loop()->PushCall(
      [] { g_base->audio_server->ClearSoundRefDeleteList(); });
}

void AudioServer::ClearSoundRefDeleteList() {
  assert(g_base->InLogicThread());
  std::scoped_lock lock(sound_ref_delete_list_mutex_);
  for (const Object::Ref<SoundAsset>* i : sound_ref_delete_list_) {
    delete i;
  }
  sound_ref_delete_list_.clear();
}

// void AudioServer::BeginInterruption() {
//   assert(!g_base->InAudioThread());
//   g_base->audio_server->PushSetSuspendedCall(true);

//   // Wait a reasonable amount of time for the thread to act on it.
//   millisecs_t t = g_core->AppTimeMillisecs();
//   while (true) {
//     if (g_base->audio_server->suspended()) {
//       break;
//     }
//     if (g_core->AppTimeMillisecs() - t > 1000) {
//       Log(LogLevel::kError, "Timed out waiting for audio suspend.");
//       break;
//     }
//     core::CorePlatform::SleepMillisecs(2);
//   }
// }

// void AudioServer::EndInterruption() {
//   assert(!g_base->InAudioThread());
//   g_base->audio_server->PushSetSuspendedCall(false);

//   // Wait a reasonable amount of time for the thread to act on it.
//   millisecs_t t = g_core->AppTimeMillisecs();
//   while (true) {
//     if (!g_base->audio_server->suspended()) {
//       break;
//     }
//     if (g_core->AppTimeMillisecs() - t > 1000) {
//       Log(LogLevel::kError, "Timed out waiting for audio unsuspend.");
//       break;
//     }
//     core::CorePlatform::SleepMillisecs(2);
//   }
// }

void AudioServer::OnThreadSuspend_() { SetSuspended_(true); }

void AudioServer::OnThreadUnsuspend_() { SetSuspended_(false); }

}  // namespace ballistica::base
