// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_AUDIO_AUDIO_SOURCE_H_
#define BALLISTICA_BASE_AUDIO_AUDIO_SOURCE_H_

#include <atomic>
#include <mutex>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// A listener of our own for some sounds, in place of the audio
/// system's single one (which follows the game camera). Sounds using
/// one play listener-relative, placed where they sit relative to it.
/// For scenes seen through a view of their own (ui viewers) so they
/// sound as that view shows them.
struct AudioListenerSpace {
  Vector3f origin{0.0f, 0.0f, 0.0f};
  Vector3f right{1.0f, 0.0f, 0.0f};
  Vector3f up{0.0f, 1.0f, 0.0f};
  /// Pointing back out of the view (the way it looks is -back).
  Vector3f back{0.0f, 0.0f, 1.0f};
  /// Scales how far to the sides sounds sit (so how widely they pan).
  float pan_scale{1.0f};
  /// Scales the gain of everything played.
  float gain{1.0f};
};

// Location for sound emission (client version)
class AudioSource {
 public:
  /// Play relative to a listener of our own (see AudioListenerSpace):
  /// positions given for positional play get placed relative to it,
  /// and gains get scaled by its gain. Sources get handed out without
  /// one.
  void SetListenerSpace(const AudioListenerSpace& space);
  void ClearListenerSpace() { has_listener_space_ = false; }

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
  /// When we were last locked and by which call site. Readable without
  /// holding the lock (that is the point: it says who has held us for a
  /// long time).
  auto last_lock_time() const -> millisecs_t { return last_lock_time_; }
  auto lock_debug_id() const -> int { return lock_debug_id_; }
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
  auto locked() const -> bool { return locked_; }
#endif
  auto available() const -> bool { return available_; }
  void set_available(bool val) { available_ = val; }
  void MakeAvailable(uint32_t play_id);
  auto client_queue_size() const -> int { return client_queue_size_; }
  void set_client_queue_size(int val) { client_queue_size_ = val; }
  auto play_id() const -> uint32_t { return play_id_; }

 private:
  AudioListenerSpace listener_space_;
  bool has_listener_space_{};
  /// With a listener space: whether positional play was asked for (we
  /// always actually play listener-relative then).
  bool wants_positional_{true};
  std::mutex mutex_;
  std::atomic<millisecs_t> last_lock_time_{};
  std::atomic<int> lock_debug_id_{};
#if BA_DEBUG_BUILD || BA_VARIANT_TEST_BUILD
  bool locked_{};
#endif
  int client_queue_size_{};
  bool available_{};
  int id_{};
  uint32_t play_id_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_AUDIO_AUDIO_SOURCE_H_
