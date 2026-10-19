// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/collision_mesh_asset.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_blob.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_16.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_32.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/math/vector3f.h"

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

  auto blob = AssetBlob::FromFile(file_name_full_);
  uint32_t i_vals[2];
  if (!blob.exists()) {
    throw Exception("Can't open collision mesh file: '" + file_name_full_
                    + "'");
  }
  AssetBlobReader reader(blob);

  uint32_t version;
  if (!reader.ReadInto(&version, sizeof(version))) {
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
  if (!reader.ReadInto(i_vals, sizeof(i_vals))) {
    throw Exception("Read failed for " + file_name_full_);
  }

  size_t vertex_count = i_vals[0];
  size_t tri_count = i_vals[1];

  // Need 3 floats per vertex.
  vertices_.resize(vertex_count * 3);

  // Need 3 indices per face.
  indices_.resize(tri_count * 3);

  if (!reader.ReadInto(vertices_.data(), vertices_.size() * sizeof(dReal))) {
    throw Exception("Read failed for " + file_name_full_);
  }
  if (!reader.ReadInto(indices_.data(), indices_.size() * sizeof(uint32_t))) {
    throw Exception("Read failed for " + file_name_full_);
  }
  if (legacy_format) {
    // Need 3 floats per face-normal.
    normals_.resize(tri_count * 3);
    if (!reader.ReadInto(normals_.data(), normals_.size() * sizeof(dReal))) {
      throw Exception("Read failed for " + file_name_full_);
    }
  }

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
  debug_mesh_.Clear();
  debug_wire_mesh_.Clear();
}

auto CollisionMeshAsset::GetDebugWireMesh() -> MeshIndexedSimpleFull* {
  assert(g_base->InLogicThread());
  if (debug_wire_mesh_.exists()) {
    return debug_wire_mesh_.get();
  }
  size_t vert_count = vertices_.size() / 3;
  size_t tri_count = indices_.size() / 3;
  if (vert_count == 0 || tri_count == 0) {
    return nullptr;
  }

  // Shared verts as-is; one line per unique edge.
  auto verts = Object::New<MeshBuffer<VertexSimpleFull>>(vert_count);
  for (size_t i = 0; i < vert_count; ++i) {
    auto& v = verts->elements[i];
    v.position[0] = static_cast<float>(vertices_[i * 3]);
    v.position[1] = static_cast<float>(vertices_[i * 3 + 1]);
    v.position[2] = static_cast<float>(vertices_[i * 3 + 2]);
    v.uv[0] = v.uv[1] = 0;
  }
  std::unordered_set<uint64_t> seen;
  std::vector<uint32_t> edges;
  edges.reserve(tri_count * 6);
  for (size_t t = 0; t < tri_count; ++t) {
    for (size_t j = 0; j < 3; ++j) {
      uint32_t a = indices_[t * 3 + j];
      uint32_t b = indices_[t * 3 + (j + 1) % 3];
      uint64_t key = (static_cast<uint64_t>(std::min(a, b)) << 32u)
                     | static_cast<uint64_t>(std::max(a, b));
      if (seen.insert(key).second) {
        edges.push_back(a);
        edges.push_back(b);
      }
    }
  }

  debug_wire_mesh_ = Object::New<MeshIndexedSimpleFull>();
  if (vert_count <= 65535) {
    auto indices = Object::New<MeshIndexBuffer16>(edges.size());
    for (size_t i = 0; i < edges.size(); ++i) {
      indices->elements[i] = static_cast<uint16_t>(edges[i]);
    }
    debug_wire_mesh_->SetIndexData(indices);
  } else {
    auto indices = Object::New<MeshIndexBuffer32>(edges.size(), edges.data());
    debug_wire_mesh_->SetIndexData(indices);
  }
  debug_wire_mesh_->SetData(verts);
  return debug_wire_mesh_.get();
}

auto CollisionMeshAsset::GetDebugMesh() -> MeshIndexedObjectSplit* {
  assert(g_base->InLogicThread());
  if (debug_mesh_.exists()) {
    return debug_mesh_.get();
  }
  size_t tri_count = indices_.size() / 3;
  if (tri_count == 0) {
    return nullptr;
  }
  size_t vert_count = tri_count * 3;

  auto v_static = Object::New<MeshBuffer<VertexObjectSplitStatic>>(vert_count);
  auto v_dynamic =
      Object::New<MeshBuffer<VertexObjectSplitDynamic>>(vert_count);
  for (size_t t = 0; t < tri_count; ++t) {
    Vector3f p[3];
    for (size_t j = 0; j < 3; ++j) {
      size_t vi = indices_[t * 3 + j];
      assert(vi * 3 + 2 < vertices_.size());
      p[j] = Vector3f(static_cast<float>(vertices_[vi * 3]),
                      static_cast<float>(vertices_[vi * 3 + 1]),
                      static_cast<float>(vertices_[vi * 3 + 2]));
    }
    Vector3f n = Vector3f::Cross(p[1] - p[0], p[2] - p[0]);
    if (n.LengthSquared() > 0.0f) {
      n = n.Normalized();
    } else {
      n = Vector3f(0.0f, 1.0f, 0.0f);
    }
    for (size_t j = 0; j < 3; ++j) {
      auto& vs = v_static->elements[t * 3 + j];
      vs.uv[0] = vs.uv[1] = 0;
      auto& vd = v_dynamic->elements[t * 3 + j];
      vd.position[0] = p[j].x;
      vd.position[1] = p[j].y;
      vd.position[2] = p[j].z;
      vd.normal[0] = static_cast<int16_t>(n.x * 32767.0f);
      vd.normal[1] = static_cast<int16_t>(n.y * 32767.0f);
      vd.normal[2] = static_cast<int16_t>(n.z * 32767.0f);
      vd.padding[0] = vd.padding[1] = 0;
    }
  }

  debug_mesh_ = Object::New<MeshIndexedObjectSplit>();
  if (vert_count <= 65535) {
    auto indices = Object::New<MeshIndexBuffer16>(vert_count);
    for (size_t i = 0; i < vert_count; ++i) {
      indices->elements[i] = static_cast<uint16_t>(i);
    }
    debug_mesh_->SetIndexData(indices);
  } else {
    auto indices = Object::New<MeshIndexBuffer32>(vert_count);
    for (size_t i = 0; i < vert_count; ++i) {
      indices->elements[i] = static_cast<uint32_t>(i);
    }
    debug_mesh_->SetIndexData(indices);
  }
  debug_mesh_->SetStaticData(v_static);
  debug_mesh_->SetDynamicData(v_dynamic);
  return debug_mesh_.get();
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
