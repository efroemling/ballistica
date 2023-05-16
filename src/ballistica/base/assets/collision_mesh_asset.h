// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_COLLISION_MESH_ASSET_H_
#define BALLISTICA_BASE_ASSETS_COLLISION_MESH_ASSET_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ode/ode.h"

namespace ballistica::base {

// Loadable mesh for collision detection.
class CollisionMeshAsset : public Asset {
 public:
  CollisionMeshAsset() = default;
  explicit CollisionMeshAsset(const std::string& file_name_in);

  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;
  auto GetAssetType() const -> AssetType override;
  auto GetName() const -> std::string override;

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

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_COLLISION_MESH_ASSET_H_
