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
  auto ReResolveSource() -> bool override;
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
    assert(renderer_data_.exists());
    return renderer_data_.get();
  }
  auto base_level() const -> int { return base_level_; }

  /// Whether this texture's RGB is premultiplied by its alpha (read from
  /// the KTX2 DFD at load; asset-packages decision #23). Drives per-draw
  /// premult-blend selection in the graphics components. False for
  /// straight-alpha textures and for loaders that don't carry the flag
  /// (only the KTX2 path sets it). Re-read on every (re)load, mirroring
  /// base_level_.
  auto premultiplied() const -> bool { return premultiplied_; }

 private:
  Object::Ref<TextPacker> packer_;
  bool is_qr_code_{};
  std::string file_name_;
  std::string file_name_full_;
  /// Whether ``file_name_full_`` is an asset-package CAS blob (named
  /// by content hash — bare or with the bundled transport suffix —
  /// never by a content extension). CAS blobs dispatch on content
  /// magic bytes at preload; legacy on-disk assets dispatch on the
  /// path's suffix (``.dds``, ``.android_dds``, ``.ktx``, ``.pvr``,
  /// ``.nop``).
  bool is_cas_blob_{};
  std::vector<TextureAssetPreloadData> preload_datas_;
  TextureType type_{TextureType::k2D};
  TextureMinQuality min_quality_{TextureMinQuality::kLow};
  Object::Ref<TextureAssetRendererData> renderer_data_;
  int base_level_{};
  bool premultiplied_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_TEXTURE_ASSET_H_
