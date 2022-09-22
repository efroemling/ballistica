// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_ASSETS_DATA_COLLIDE_MODEL_DATA_H_
#define BALLISTICA_ASSETS_DATA_COLLIDE_MODEL_DATA_H_

#include <string>
#include <vector>

#include "ballistica/assets/data/asset_component_data.h"
#include "ode/ode.h"

namespace ballistica {

// Loadable model for collision detection.
class CollideModelData : public AssetComponentData {
 public:
  CollideModelData() = default;
  explicit CollideModelData(const std::string& file_name_in);
  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;
  auto GetAssetType() const -> AssetType override {
    return AssetType::kCollideModel;
  }
  auto GetName() const -> std::string override {
    if (!file_name_full_.empty()) {
      return file_name_full_;
    } else {
      return "invalid CollideModel";
    }
  }
  auto GetMeshData() -> dTriMeshDataID;
  auto GetBGMeshData() -> dTriMeshDataID;

 private:
  std::string file_name_;
  std::string file_name_full_;
  std::vector<dReal> vertices_;
  std::vector<uint32_t> indices_;
  std::vector<dReal> normals_;
  dTriMeshDataID tri_mesh_data_{};
  dTriMeshDataID tri_mesh_data_bg_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_ASSETS_DATA_COLLIDE_MODEL_DATA_H_
