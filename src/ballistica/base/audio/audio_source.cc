// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/audio/audio_source.h"

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/audio/audio_server.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

AudioSource::AudioSource(int id_in) : id_(id_in) {}

AudioSource::~AudioSource() { assert(client_queue_size_ == 0); }

void AudioSource::MakeAvailable(uint32_t play_id_new) {
  assert(AudioServer::SourceIdFromPlayId(play_id_new) == id_);
  assert(client_queue_size_ == 0);
  assert(locked());
  play_id_ = play_id_new;
  assert(!available_);
  assert(g_base->audio);
  g_base->audio->MakeSourceAvailable(this);
  available_ = true;
}

void AudioSource::SetIsMusic(bool val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
  g_base->audio_server->PushSourceSetIsMusicCall(play_id_, val);
}

void AudioSource::SetListenerSpace(const AudioListenerSpace& space) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
  listener_space_ = space;
  has_listener_space_ = true;
  wants_positional_ = true;
  g_base->audio_server->PushSourceSetPositionalCall(play_id_, false);
  SetGain(1.0f);
}

void AudioSource::SetPositional(bool val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);

  // With a listener of our own we always play listener-relative, and
  // just note whether positions are world ones for us to place.
  if (has_listener_space_) {
    wants_positional_ = val;
    return;
  }
  g_base->audio_server->PushSourceSetPositionalCall(play_id_, val);
}

void AudioSource::SetPosition(float x, float y, float z) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
#if BA_DEBUG_BUILD
  if (std::isnan(x) || std::isnan(y) || std::isnan(z)) {
    g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                         "Got nan value in AudioSource::SetPosition.");
  }
#endif
  Vector3f pos{x, y, z};
  if (has_listener_space_ && wants_positional_) {
    const AudioListenerSpace& s{listener_space_};
    Vector3f offs = pos - s.origin;
    pos = Vector3f(offs.Dot(s.right) * s.pan_scale, offs.Dot(s.up),
                   offs.Dot(s.back));
  }
  g_base->audio_server->PushSourceSetPositionCall(play_id_, pos);
}

void AudioSource::SetGain(float val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
  if (has_listener_space_) {
    val *= listener_space_.gain;
  }
  g_base->audio_server->PushSourceSetGainCall(play_id_, val);
}

void AudioSource::SetFade(float val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
  g_base->audio_server->PushSourceSetFadeCall(play_id_, val);
}

void AudioSource::SetLooping(bool val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
  g_base->audio_server->PushSourceSetLoopingCall(play_id_, val);
}

auto AudioSource::Play(SoundAsset* ptr_in) -> uint32_t {
  assert(ptr_in);
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);

  // Allocate a new reference to this guy and pass it along to the thread
  // (these refs can't be created or destroyed or have their ref-counts
  // changed outside the main thread). The thread will then send back this
  // allocated ptr when it's done with it for the main thread to destroy.

  ptr_in->UpdatePlayTime();
  auto ptr = new Object::Ref<SoundAsset>(ptr_in);
  g_base->audio_server->PushSourcePlayCall(play_id_, ptr);
  return play_id_;
}

void AudioSource::Stop() {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
  g_base->audio_server->PushSourceStopCall(play_id_);
}

void AudioSource::End() {
  assert(client_queue_size_ > 0);
  // send the thread a "this source is potentially free now" message
  assert(g_base->audio_server);
  g_base->audio_server->PushSourceEndCall(play_id_);
  Unlock();
}

void AudioSource::Lock(int debug_id) {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  mutex_.lock();
  last_lock_time_ = g_core->AppTimeMillisecs();
  lock_debug_id_ = debug_id;
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
  locked_ = true;
#endif
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
}

auto AudioSource::TryLock(int debug_id) -> bool {
  bool locked = mutex_.try_lock();
  if (locked) {
    last_lock_time_ = g_core->AppTimeMillisecs();
    lock_debug_id_ = debug_id;
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
    locked_ = true;
#endif
  }
  return locked;
}

void AudioSource::Unlock() {
  BA_DEBUG_FUNCTION_TIMER_BEGIN();
  mutex_.unlock();
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
  locked_ = false;
#endif
}

}  // namespace ballistica::base
