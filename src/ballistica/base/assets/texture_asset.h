// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_H_
#define BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"

namespace ballistica::base {

// A lovely texture asset.
class TextureAsset : public Asset {
 public:
  TextureAsset();
  ~TextureAsset() override;
  // Pass a newly allocated TextPacker pointer here; TextureData takes ownership
  // and handles cleaning it up.
  explicit TextureAsset(TextPacker* packer);
  explicit TextureAsset(const std::string& file_in, TextureType type_in,
                        TextureMinQuality min_quality_in);
  explicit TextureAsset(const std::string& qr_url);

  auto GetName() const -> std::string override;
  auto GetNameFull() const -> std::string override;
  auto GetAssetType() const -> AssetType override;
  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;

  auto file_name() const -> const std::string& { return file_name_; }
  auto file_name_full() const -> const std::string& { return file_name_full_; }
  auto texture_type() const -> TextureType { return type_; }
  auto is_qr_code() const -> bool { return is_qr_code_; }
  auto preload_datas() const -> const std::vector<TextureAssetPreloadData>& {
    return preload_datas_;
  }
  auto renderer_data() const -> TextureAssetRendererData* {
    assert(renderer_data_.Exists());
    return renderer_data_.Get();
  }
  auto base_level() const -> int { return base_level_; }

 private:
  Object::Ref<TextPacker> packer_;
  bool is_qr_code_{};
  std::string file_name_;
  std::string file_name_full_;
  std::vector<TextureAssetPreloadData> preload_datas_;
  TextureType type_{TextureType::k2D};
  TextureMinQuality min_quality_{TextureMinQuality::kLow};
  Object::Ref<TextureAssetRendererData> renderer_data_;
  int base_level_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_H_
