// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_SOUND_ASSET_H_
#define BALLISTICA_BASE_ASSETS_SOUND_ASSET_H_

#include <atomic>
#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/audio/al_sys.h"
#include "ballistica/base/audio/audio.h"

namespace ballistica::base {

class SoundAsset : public Asset {
 public:
  SoundAsset() = default;
  explicit SoundAsset(const std::string& file_name_in);

  void DoPreload() override;
  void DoLoad() override;
  // FIXME: Should make sure the sound_data isn't in use before unloading
  // it.
  void DoUnload() override;
  auto GetAssetType() const -> AssetType override;
  auto GetName() const -> std::string override;
#if BA_ENABLE_AUDIO
  auto format() const -> ALenum { return format_; }
  auto buffer() const -> ALuint {
    assert(!is_streamed_);
    return buffer_;
  }
#endif  // BA_ENABLE_AUDIO
  auto is_streamed() const { return is_streamed_; }

  /// Whether this is an authored mix (BA_ROLE=pre_mixed vorbis comment
  /// tag); such sounds always play listener-space.
  auto pre_mixed() const { return pre_mixed_; }

  /// Audio-server-side flag for warning once per asset when a positional
  /// play is requested on a pre-mixed sound (audio thread only).
  auto pre_mixed_positional_warned() const {
    return pre_mixed_positional_warned_;
  }
  void set_pre_mixed_positional_warned(bool val) {
    pre_mixed_positional_warned_ = val;
  }

  /// The play group our plays count toward by default (see
  /// Audio::SourceBeginNew). Starts out as the one our name implies
  /// (Audio::AutoPlayGroupName); what our file says, if anything, takes
  /// over once we've been preloaded.
  auto play_group() const -> int { return play_group_; }

  /// How much our plays matter by default when sources are contended.
  auto priority() const -> AudioPriority {
    return static_cast<AudioPriority>(priority_.load());
  }

  /// Apply play group and priority settings as carried by our file: a
  /// group of "unique" or "custom:<name>" (anything else, empty
  /// included, leaves the name-implied one) and a priority of "lower",
  /// "low", "high" or "higher" (anything else is the default).
  void ApplyPlaySettings(const std::string& group, const std::string& priority);

  const auto& file_name() const { return file_name_; }
  const auto& file_name_full() const { return file_name_full_; }
  void UpdatePlayTime();
  auto last_play_time() const { return last_play_time_; }

 private:
  std::string file_name_;
  std::string file_name_full_;
  bool is_streamed_{};
  bool pre_mixed_{};
  bool pre_mixed_positional_warned_{};
  // Read on the logic thread; may be set from an asset thread at
  // preload.
  std::atomic<int> play_group_{-1};
  std::atomic<int> priority_{static_cast<int>(AudioPriority::kDefault)};
#if BA_ENABLE_AUDIO
  ALuint buffer_{};
  ALenum format_{};
  ALsizei freq_{};
#endif  // BA_ENABLE_AUDIO
  std::vector<char> load_buffer_;
  millisecs_t last_play_time_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_SOUND_ASSET_H_
