// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AUDIO_SOURCE_H_
#define BALLISTICA_BASE_AUDIO_AUDIO_SOURCE_H_

#include <mutex>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Location for sound emission (client version)
class AudioSource {
 public:
  // Sets whether a source is "music".
  // This mainly just influences which volume controls
  // affect it.
  void SetIsMusic(bool m);

  // Sets whether a source is positional.
  // A non-positional source's position coords are always
  // relative to the listener. ie: 0,0,0 will always be centered.
  void SetPositional(bool p);
  void SetPosition(float x, float y, float z);
  void SetGain(float g);
  void SetFade(float f);
  void SetLooping(bool loop);
  auto Play(SoundAsset* ptr) -> uint32_t;
  void Stop();

  // Always call this when done sending commands to the source.
  void End();
  ~AudioSource();

  // Lock the source. Sources must be locked whenever calling any public func.
  void Lock(int debug_id);

  // Attempt to lock the source, but will not block.  Returns true if
  // successful.
  auto TryLock(int debug_id) -> bool;
  void Unlock();
  explicit AudioSource(int id);
  auto id() const -> int { return id_; }
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
  auto last_lock_time() const -> millisecs_t { return last_lock_time_; }
  auto lock_debug_id() const -> int { return lock_debug_id_; }
  auto locked() const -> bool { return locked_; }
#endif
  auto available() const -> bool { return available_; }
  void set_available(bool val) { available_ = val; }
  void MakeAvailable(uint32_t play_id);
  auto client_queue_size() const -> int { return client_queue_size_; }
  void set_client_queue_size(int val) { client_queue_size_ = val; }
  auto play_id() const -> uint32_t { return play_id_; }

 private:
  std::mutex mutex_;
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
  millisecs_t last_lock_time_{};
  int lock_debug_id_{};
  bool locked_{};
#endif
  int client_queue_size_{};
  bool available_{};
  int id_{};
  uint32_t play_id_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_AUDIO_AUDIO_SOURCE_H_
