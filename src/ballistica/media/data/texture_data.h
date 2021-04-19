// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_DATA_TEXTURE_DATA_H_
#define BALLISTICA_MEDIA_DATA_TEXTURE_DATA_H_

#include <string>
#include <vector>

#include "ballistica/media/data/media_component_data.h"

namespace ballistica {

// Loadable texture media component.
class TextureData : public MediaComponentData {
 public:
  TextureData();
  ~TextureData() override;

  // pass a newly allocated TextPacker pointer here; TextureData takes ownership
  // and handles cleaning it up
  explicit TextureData(TextPacker* packer);
  explicit TextureData(const std::string& file_in, TextureType type_in,
                       TextureMinQuality min_quality_in);
  explicit TextureData(const std::string& qr_url);
  auto GetName() const -> std::string override {
    return (!file_name_.empty()) ? file_name_ : "invalid texture";
  }
  auto GetNameFull() const -> std::string override { return file_name_full(); }
  auto file_name() const -> const std::string& { return file_name_; }
  auto file_name_full() const -> const std::string& { return file_name_full_; }
  auto GetMediaType() const -> MediaType override {
    return MediaType::kTexture;
  }
  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;
  auto texture_type() const -> TextureType { return type_; }
  auto is_qr_code() const -> bool { return is_qr_code_; }
  auto preload_datas() const -> const std::vector<TexturePreloadData>& {
    return preload_datas_;
  }
  auto renderer_data() const -> TextureRendererData* {
    assert(renderer_data_.exists());
    return renderer_data_.get();
  }
  auto base_level() const -> int { return base_level_; }

 private:
  Object::Ref<TextPacker> packer_;
  bool is_qr_code_ = false;
  std::string file_name_;
  std::string file_name_full_;
  std::vector<TexturePreloadData> preload_datas_;
  TextureType type_ = TextureType::k2D;
  TextureMinQuality min_quality_ = TextureMinQuality::kLow;
  Object::Ref<TextureRendererData> renderer_data_;
  int base_level_ = 0;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_DATA_TEXTURE_DATA_H_
