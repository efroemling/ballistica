// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_DATA_SOUND_DATA_H_
#define BALLISTICA_MEDIA_DATA_SOUND_DATA_H_

#include <string>
#include <vector>

#include "ballistica/audio/al_sys.h"
#include "ballistica/media/data/media_component_data.h"

namespace ballistica {

class SoundData : public MediaComponentData {
 public:
  SoundData() = default;
  explicit SoundData(const std::string& file_name_in);
  void DoPreload() override;
  void DoLoad() override;

  // FIXME: Should make sure the sound_data isn't in use before unloading it.
  void DoUnload() override;
  auto GetMediaType() const -> MediaType override { return MediaType::kSound; }
  auto GetName() const -> std::string override {
    if (!file_name_full_.empty())
      return file_name_full_;
    else
      return "invalid sound";
  }
#if BA_ENABLE_AUDIO
  auto format() const -> ALenum { return format_; }
  auto buffer() const -> ALuint {
    assert(!is_streamed_);
    return buffer_;
  }
#endif  // BA_ENABLE_AUDIO
  auto is_streamed() const -> bool { return is_streamed_; }
  auto file_name() const -> const std::string& { return file_name_; }
  auto file_name_full() const -> const std::string& { return file_name_full_; }
  void UpdatePlayTime() { last_play_time_ = GetRealTime(); }
  auto last_play_time() const -> millisecs_t { return last_play_time_; }

 private:
  std::string file_name_;
  std::string file_name_full_;
  bool is_streamed_{};
#if BA_ENABLE_AUDIO
  ALuint buffer_{};
  ALenum format_{};
  ALsizei freq_{};
#endif  // BA_ENABLE_AUDIO
  std::vector<char> load_buffer_;
  millisecs_t last_play_time_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_DATA_SOUND_DATA_H_
