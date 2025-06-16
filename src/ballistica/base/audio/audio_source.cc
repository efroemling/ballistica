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

void AudioSource::SetPositional(bool val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
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
  g_base->audio_server->PushSourceSetPositionCall(play_id_, Vector3f(x, y, z));
}

void AudioSource::SetGain(float val) {
  assert(g_base->audio_server);
  assert(client_queue_size_ > 0);
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
#if BA_DEBUG_BUILD
  last_lock_time_ = g_core->AppTimeMillisecs();
  lock_debug_id_ = debug_id;
  locked_ = true;
#endif
  BA_DEBUG_FUNCTION_TIMER_END_THREAD(20);
}

auto AudioSource::TryLock(int debug_id) -> bool {
  bool locked = mutex_.try_lock();
#if (BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD)
  if (locked) {
    locked_ = true;
    last_lock_time_ = g_core->AppTimeMillisecs();
    lock_debug_id_ = debug_id;
  }
#endif
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
