// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_SOUND_ASSET_H_
#define BALLISTICA_BASE_ASSETS_SOUND_ASSET_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/audio/al_sys.h"

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
