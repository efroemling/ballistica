// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/collision_mesh_asset.h"

#include "ballistica/base/assets/assets.h"
#include "ballistica/core/core.h"

namespace ballistica::base {

CollisionMeshAsset::CollisionMeshAsset(const std::string& file_name_in)
    : file_name_(file_name_in) {
  assert(g_base && g_base->assets);
  file_name_full_ = g_base->assets->FindAssetFile(
      Assets::FileType::kCollisionMesh, file_name_in);
  valid_ = true;
}

auto CollisionMeshAsset::GetAssetType() const -> AssetType {
  return AssetType::kCollisionMesh;
}

auto CollisionMeshAsset::GetName() const -> std::string {
  if (!file_name_full_.empty()) {
    return file_name_full_;
  } else {
    return "invalid CollisionMesh";
  }
}

void CollisionMeshAsset::DoPreload() {
  assert(!file_name_.empty());

  FILE* f = g_core->platform->FOpen(file_name_full_.c_str(), "rb");
  uint32_t i_vals[2];
  if (!f) {
    throw Exception("Can't open collision mesh file: '" + file_name_full_
                    + "'");
  }

  uint32_t version;
  if (fread(&version, sizeof(version), 1, f) != 1) {
    throw Exception("Error reading file header for '" + file_name_full_ + "'");
  }

  if (version != kCobFileID) {
    throw Exception("File '" + file_name_full_
                    + " is in an old format or not a cob file (got id "
                    + std::to_string(version) + ", "
                    + std::to_string(kCobFileID) + ")");
  }

  // Read the vertex count and face count.
  if (fread(i_vals, sizeof(i_vals), 1, f) != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }

  size_t vertex_count = i_vals[0];
  size_t tri_count = i_vals[1];

  // Need 3 floats per vertex.
  vertices_.resize(vertex_count * 3);

  // Need 3 indices per face.
  indices_.resize(tri_count * 3);

  // Need 3 floats per face-normal.
  normals_.resize(tri_count * 3);

  if (fread(&(vertices_[0]), vertices_.size() * sizeof(dReal), 1, f) != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }
  if (fread(&(indices_[0]), indices_.size() * sizeof(uint32_t), 1, f) != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }
  if (fread(&(normals_[0]), normals_.size() * sizeof(dReal), 1, f) != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }

  fclose(f);

  tri_mesh_data_ = dGeomTriMeshDataCreate();
  BA_PRECONDITION(tri_mesh_data_);

  if (!g_core->HeadlessMode()) {
    tri_mesh_data_bg_ = dGeomTriMeshDataCreate();
    BA_PRECONDITION(tri_mesh_data_bg_);
  }

#ifdef dSINGLE
  dGeomTriMeshDataBuildSingle1(
      tri_mesh_data_, &(vertices_[0]), 3 * sizeof(dReal),
      static_cast_check_fit<int>(vertex_count), &(indices_[0]),
      static_cast<int>(indices_.size()), 3 * sizeof(uint32_t), &(normals_[0]));
  if (!g_core->HeadlessMode()) {
    dGeomTriMeshDataBuildSingle1(tri_mesh_data_bg_, &(vertices_[0]),
                                 3 * sizeof(dReal), i_vals[0], &(indices_[0]),
                                 static_cast<int>(indices_.size()),
                                 3 * sizeof(uint32_t), &(normals_[0]));
  }
#else
#ifndef dDOUBLE
#error single or double precition not defined
#endif
  dGeomTriMeshDataBuildDouble1(
      tri_mesh_data_, &(vertices_[0]), 3 * sizeof(dReal), vertex_count,
      &(indices_[0]), indices_.size(), 3 * sizeof(uint32_t), &(normals_[0]));
  if (!HeadlessMode()) {
    dGeomTriMeshDataBuildDouble1(
        tri_mesh_data_bg_, &(vertices_[0]), 3 * sizeof(dReal), i_vals[0],
        &(indices_[0]), indices_.size(), 3 * sizeof(uint32_t), &(normals_[0]));
  }
#endif  // dSINGLE
}  // namespace ballistica

void CollisionMeshAsset::DoLoad() { assert(g_base->InLogicThread()); }

void CollisionMeshAsset::DoUnload() {
  // TODO(ericf): if we want to support in-game reloading we need
  //  to keep track of what ODE trimeshes are using our data and update
  //  them all accordingly on unload/loads...

  // we should still be fine for regular pruning unloads though;
  // if there are no references remaining to us then nothing in the
  // game should be using us.

  if (!valid_) {
    return;
  }

  dGeomTriMeshDataDestroy(tri_mesh_data_);
  if (tri_mesh_data_bg_) {
    dGeomTriMeshDataDestroy(tri_mesh_data_bg_);
  }
}

auto CollisionMeshAsset::GetMeshData() -> dTriMeshDataID {
  assert(tri_mesh_data_);
  return tri_mesh_data_;
}

auto CollisionMeshAsset::GetBGMeshData() -> dTriMeshDataID {
  assert(loaded());
  assert(!g_core->HeadlessMode());
  return tri_mesh_data_bg_;
}

}  // namespace ballistica::base
