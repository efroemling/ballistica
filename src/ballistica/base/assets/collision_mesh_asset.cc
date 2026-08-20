// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/collision_mesh_asset.h"

#include <cstdio>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::base {

// When true, the bg-dynamics sim shares the main sim's dxTriMeshData
// (including its OPCODE AABB tree) instead of building its own duplicate
// from the same source arrays; this halves collision-mesh runtime memory
// and preload tree-build time.
//
// Why this should be safe: both sims only ever *read* the structure
// during collide queries. The only mutable state in a dxTriMeshData is
// (a) last_trans, written solely via
// dGeomTriMeshDataSet(TRIMESH_LAST_TRANSFORMATION), which nothing in
// ballistica calls, and (b) MeshInterface::VertexCache, which is written
// only on the double-precision fetch path - with dSINGLE,
// MeshInterface::GetTriangle is pure reads. The BVTree is immutable
// after build, and per-geom mutable state lives in the dxTriMesh geoms,
// which each sim still creates separately. Our bundled ODE fork also has
// no temporal-coherence cache compiled in. Flip this off if it somehow
// proves problematic (and re-evaluate if we ever upgrade ODE or switch
// to double precision; we hard-disable sharing for the latter below).
#ifdef dSINGLE
constexpr bool kShareTriMeshDataBetweenSims = true;
#else
constexpr bool kShareTriMeshDataBetweenSims = false;
#endif

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
  return (!file_name_.empty()) ? file_name_ : "invalid collision mesh";
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

  if (version != kCobFileID && version != kCobFileID2) {
    throw Exception("File '" + file_name_full_
                    + " is in an old format or not a cob file (got id "
                    + std::to_string(version) + "; expected "
                    + std::to_string(kCobFileID) + " or "
                    + std::to_string(kCobFileID2) + ")");
  }

  // Legacy cobs carry a trailing face-normals block; current ones
  // don't (see notes in ballistica.h). We keep loading legacy files
  // since modder-made ones exist in the wild.
  bool legacy_format = (version == kCobFileID);

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

  if (fread(&(vertices_[0]), vertices_.size() * sizeof(dReal), 1, f) != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }
  if (fread(&(indices_[0]), indices_.size() * sizeof(uint32_t), 1, f) != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }
  if (legacy_format) {
    // Need 3 floats per face-normal.
    normals_.resize(tri_count * 3);
    if (fread(&(normals_[0]), normals_.size() * sizeof(dReal), 1, f) != 1) {
      throw Exception("Read failed for " + file_name_full_);
    }
  }

  fclose(f);

  tri_mesh_data_ = dGeomTriMeshDataCreate();
  BA_PRECONDITION(tri_mesh_data_);

  if (!g_core->HeadlessMode() && !kShareTriMeshDataBetweenSims) {
    tri_mesh_data_bg_ = dGeomTriMeshDataCreate();
    BA_PRECONDITION(tri_mesh_data_bg_);
  }

  // Null normals are fine with ODE; they're only consumed by the
  // trimesh-vs-trimesh collider, which we never invoke (see notes in
  // ballistica.h).
  dReal* normals = normals_.empty() ? nullptr : &(normals_[0]);

#ifdef dSINGLE
  dGeomTriMeshDataBuildSingle1(
      tri_mesh_data_, &(vertices_[0]), 3 * sizeof(dReal),
      static_cast_check_fit<int>(vertex_count), &(indices_[0]),
      static_cast<int>(indices_.size()), 3 * sizeof(uint32_t), normals);
  if (tri_mesh_data_bg_) {
    dGeomTriMeshDataBuildSingle1(tri_mesh_data_bg_, &(vertices_[0]),
                                 3 * sizeof(dReal), i_vals[0], &(indices_[0]),
                                 static_cast<int>(indices_.size()),
                                 3 * sizeof(uint32_t), normals);
  }
#else
#ifndef dDOUBLE
#error single or double precition not defined
#endif
  dGeomTriMeshDataBuildDouble1(tri_mesh_data_, &(vertices_[0]),
                               3 * sizeof(dReal), vertex_count, &(indices_[0]),
                               indices_.size(), 3 * sizeof(uint32_t), normals);
  if (tri_mesh_data_bg_) {
    dGeomTriMeshDataBuildDouble1(
        tri_mesh_data_bg_, &(vertices_[0]), 3 * sizeof(dReal), i_vals[0],
        &(indices_[0]), indices_.size(), 3 * sizeof(uint32_t), normals);
  }
#endif  // dSINGLE
}

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
  if (kShareTriMeshDataBetweenSims) {
    return tri_mesh_data_;
  }
  return tri_mesh_data_bg_;
}

}  // namespace ballistica::base
