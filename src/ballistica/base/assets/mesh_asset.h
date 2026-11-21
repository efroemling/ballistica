// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_MESH_ASSET_H_
#define BALLISTICA_BASE_ASSETS_MESH_ASSET_H_

#include <array>
#include <optional>
#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/mesh_asset_renderer_data.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

class AssetBlobReader;

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
    assert(renderer_data_.exists());
    return renderer_data_.get();
  }
  auto vertices() const -> const std::vector<VertexObjectFull>& {
    return vertices_;
  }
  auto indices8() const -> const std::vector<uint8_t>& { return indices8_; }
  auto indices16() const -> const std::vector<uint16_t>& { return indices16_; }
  auto indices32() const -> const std::vector<uint32_t>& { return indices32_; }
  /// Our extent in the mesh's own space: a box, and the radius of the
  /// sphere about the box's center that holds every vertex. Read from
  /// the file's trailer, or worked out from the vertices for files
  /// without one. Set once preloaded and kept after our vertex data is
  /// let go (unlike vertices()); unset in headless builds.
  struct Bounds {
    Vector3f box_min{0.0f, 0.0f, 0.0f};
    Vector3f box_max{0.0f, 0.0f, 0.0f};
    float radius{};
    auto center() const -> Vector3f { return (box_min + box_max) * 0.5f; }
  };
  auto bounds() const -> const std::optional<Bounds>& { return bounds_; }

  /// The range of texture coordinates we use: u min, v min, u max, v
  /// max. Available as bounds() is.
  auto uv_range() const -> const std::optional<std::array<float, 4>>& {
    return uv_range_;
  }

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
  void ReadTrailer_(AssetBlobReader* reader);
  void DeriveMissingTrailerData_();

  Object::Ref<MeshAssetRendererData> renderer_data_;
  std::optional<Bounds> bounds_;
  std::optional<std::array<float, 4>> uv_range_;
  std::string file_name_;
  std::string file_name_full_;
  MeshFormat format_{};
  std::vector<VertexObjectFull> vertices_;
  std::vector<uint8_t> indices8_;
  std::vector<uint16_t> indices16_;
  std::vector<uint32_t> indices32_;
  BA_DISALLOW_CLASS_COPIES(MeshAsset);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_MESH_ASSET_H_
