// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_MESH_ASSET_H_
#define BALLISTICA_BASE_ASSETS_MESH_ASSET_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/mesh_asset_renderer_data.h"

namespace ballistica::base {

class MeshAsset : public Asset {
 public:
  MeshAsset() = default;
  explicit MeshAsset(const std::string& file_name_in);
  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;
  auto GetAssetType() const -> AssetType override;
  auto GetName() const -> std::string override;

  auto renderer_data() const -> MeshAssetRendererData* {
    assert(renderer_data_.Exists());
    return renderer_data_.Get();
  }
  auto vertices() const -> const std::vector<VertexObjectFull>& {
    return vertices_;
  }
  auto indices8() const -> const std::vector<uint8_t>& { return indices8_; }
  auto indices16() const -> const std::vector<uint16_t>& { return indices16_; }
  auto indices32() const -> const std::vector<uint32_t>& { return indices32_; }
  auto GetIndexSize() const -> int {
    switch (format_) {
      case MeshFormat::kUV16N8Index8:
        return 1;
      case MeshFormat::kUV16N8Index16:
        return 2;
      case MeshFormat::kUV16N8Index32:
        return 4;
      default:
        throw Exception();
    }
  }

 private:
  Object::Ref<MeshAssetRendererData> renderer_data_;
  std::string file_name_;
  std::string file_name_full_;
  MeshFormat format_{};
  std::vector<VertexObjectFull> vertices_;
  std::vector<uint8_t> indices8_;
  std::vector<uint16_t> indices16_;
  std::vector<uint32_t> indices32_;
  friend class MeshAssetRendererData;
  BA_DISALLOW_CLASS_COPIES(MeshAsset);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_MESH_ASSET_H_
