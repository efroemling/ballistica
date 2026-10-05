// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_COLLISION_MESH_ASSET_H_
#define BALLISTICA_BASE_ASSETS_COLLISION_MESH_ASSET_H_

#include <string>
#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_object_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
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

  /// A flat-shaded renderable version of the collision geometry (unshared
  /// verts, one face normal per triangle) for debug drawing. Built lazily
  /// on first call; logic thread only.
  auto GetDebugMesh() -> MeshIndexedObjectSplit*;

  /// The collision geometry's unique edges as a line mesh (draw with
  /// kMeshDrawFlagLines) for debug wireframes. Built lazily on first
  /// call; logic thread only.
  auto GetDebugWireMesh() -> MeshIndexedSimpleFull*;

 private:
  std::string file_name_;
  std::string file_name_full_;
  std::vector<dReal> vertices_;
  std::vector<uint32_t> indices_;
  std::vector<dReal> normals_;
  dTriMeshDataID tri_mesh_data_{};
  dTriMeshDataID tri_mesh_data_bg_{};
  Object::Ref<MeshIndexedObjectSplit> debug_mesh_;
  Object::Ref<MeshIndexedSimpleFull> debug_wire_mesh_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_COLLISION_MESH_ASSET_H_
