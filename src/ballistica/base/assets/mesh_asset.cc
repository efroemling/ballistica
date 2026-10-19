// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/mesh_asset.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "ballistica/base/assets/asset_blob.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"

namespace ballistica::base {

MeshAsset::MeshAsset(const std::string& file_name_in)
    : file_name_(file_name_in) {
  file_name_full_ =
      g_base->assets->FindAssetFile(Assets::FileType::kMesh, file_name_in);
  valid_ = true;
}

auto MeshAsset::GetAssetType() const -> AssetType { return AssetType::kMesh; }

auto MeshAsset::GetName() const -> std::string {
  return (!file_name_.empty()) ? file_name_ : "invalid mesh";
}

void MeshAsset::DoPreload() {
  // In headless, don't load anything.
#if !BA_HEADLESS_BUILD

  assert(!file_name_.empty());
  auto blob = AssetBlob::FromFile(file_name_full_);
  if (!blob.exists()) {
    throw Exception("Can't open mesh file: '" + file_name_full_ + "'");
  }
  AssetBlobReader reader(blob);

  // We currently read/write in little-endian since that's all we run on at the
  // moment.
#if WORDS_BIGENDIAN
#error FIX THIS FOR BIG ENDIAN
#endif

  uint32_t version;
  if (!reader.ReadInto(&version, sizeof(version))) {
    throw Exception("Error reading file header for '" + file_name_full_ + "'");
  }
  if (version != kBobFileID) {
    throw Exception("File: '" + file_name_full_
                    + "' is an old format or not a bob file (got id "
                    + std::to_string(version) + ", "
                    + std::to_string(kBobFileID) + ")");
  }

  uint32_t mesh_format;
  if (!reader.ReadInto(&mesh_format, sizeof(mesh_format))) {
    throw Exception("Error reading mesh_format for '" + file_name_full_ + "'");
  }
  format_ = static_cast<MeshFormat>(mesh_format);
  BA_PRECONDITION((format_ == MeshFormat::kUV16N8Index8)
                  || (format_ == MeshFormat::kUV16N8Index16)
                  || (format_ == MeshFormat::kUV16N8Index32));

  uint32_t vertex_count;
  if (!reader.ReadInto(&vertex_count, sizeof(vertex_count))) {
    throw Exception("Error reading vertex_count for '" + file_name_full_ + "'");
  }

  uint32_t face_count;
  if (!reader.ReadInto(&face_count, sizeof(face_count))) {
    throw Exception("Error reading face_count for '" + file_name_full_ + "'");
  }

  vertices_.resize(vertex_count);
  if (!reader.ReadInto(vertices_.data(),
                       vertices_.size() * sizeof(VertexObjectFull))) {
    throw Exception("Read failed for " + file_name_full_);
  }
  switch (GetIndexSize()) {
    case 1: {
      indices8_.resize(face_count * 3);
      if (!reader.ReadInto(indices8_.data(),
                           indices8_.size() * sizeof(uint8_t))) {
        throw Exception("Read failed for " + file_name_full_);
      }
      break;
    }
    case 2: {
      indices16_.resize(face_count * 3);
      if (!reader.ReadInto(indices16_.data(),
                           indices16_.size() * sizeof(uint16_t))) {
        throw Exception("Read failed for " + file_name_full_);
      }
      break;
    }
    case 4: {
      indices32_.resize(face_count * 3);
      if (!reader.ReadInto(indices32_.data(),
                           indices32_.size() * sizeof(uint32_t))) {
        throw Exception("Read failed for " + file_name_full_);
      }
      break;
    }
    default:
      throw Exception();
  }

  // Derived data (bounds and such) follows in newer files; work out
  // whatever a file doesn't carry while we still have its vertices.
  ReadTrailer_(&reader);
  DeriveMissingTrailerData_();

#endif  // BA_HEADLESS_BUILD
}

void MeshAsset::ReadTrailer_(AssetBlobReader* reader) {
  uint32_t magic{};
  if (reader->remaining() == 0) {
    return;  // A file from before the trailer.
  }
  if (!reader->ReadInto(&magic, sizeof(magic)) || magic != kBobTrailerMagic) {
    // Anything else after the indices is something we don't
    // understand; the mesh itself is fine without it.
    g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                         "Unrecognized trailing data in mesh '"
                             + file_name_full_ + "'; ignoring it.");
    return;
  }
  while (reader->remaining() > 0) {
    uint32_t tag{};
    uint32_t length{};
    if (!reader->ReadInto(&tag, sizeof(tag))
        || !reader->ReadInto(&length, sizeof(length))
        || length > reader->remaining()) {
      g_core->logging->Log(LogName::kBaAssets, LogLevel::kWarning,
                           "Truncated trailer in mesh '" + file_name_full_
                               + "'; ignoring the rest of it.");
      return;
    }
    // Read this section whole; then interpret it if we know it (and it
    // holds at least what we expect -- later versions may append).
    std::vector<uint8_t> data(length);
    if (length > 0) {
      reader->ReadInto(data.data(), length);
    }
    if (tag == kBobTrailerTagBounds && length >= 7 * sizeof(float)) {
      float vals[7];
      memcpy(vals, data.data(), sizeof(vals));
      Bounds bounds;
      bounds.box_min = {vals[0], vals[1], vals[2]};
      bounds.box_max = {vals[3], vals[4], vals[5]};
      bounds.radius = vals[6];
      bounds_ = bounds;
    } else if (tag == kBobTrailerTagUVRange && length >= 4 * sizeof(float)) {
      std::array<float, 4> range{};
      memcpy(range.data(), data.data(), sizeof(float) * 4);
      uv_range_ = range;
    }
  }
}

void MeshAsset::DeriveMissingTrailerData_() {
  if (vertices_.empty()) {
    return;
  }
  if (!bounds_) {
    // As the mesh compiler computes it: a box, then the farthest any
    // vertex sits from its center.
    Bounds bounds;
    bounds.box_min = {vertices_[0].position[0], vertices_[0].position[1],
                      vertices_[0].position[2]};
    bounds.box_max = bounds.box_min;
    for (const auto& v : vertices_) {
      bounds.box_min.x = std::min(bounds.box_min.x, v.position[0]);
      bounds.box_min.y = std::min(bounds.box_min.y, v.position[1]);
      bounds.box_min.z = std::min(bounds.box_min.z, v.position[2]);
      bounds.box_max.x = std::max(bounds.box_max.x, v.position[0]);
      bounds.box_max.y = std::max(bounds.box_max.y, v.position[1]);
      bounds.box_max.z = std::max(bounds.box_max.z, v.position[2]);
    }
    Vector3f center = bounds.center();
    float radius_sq{};
    for (const auto& v : vertices_) {
      float dx = v.position[0] - center.x;
      float dy = v.position[1] - center.y;
      float dz = v.position[2] - center.z;
      radius_sq = std::max(radius_sq, dx * dx + dy * dy + dz * dz);
    }
    bounds.radius = sqrtf(radius_sq);
    bounds_ = bounds;
  }
  if (!uv_range_) {
    uint16_t umin{0xFFFF}, vmin{0xFFFF}, umax{}, vmax{};
    for (const auto& v : vertices_) {
      umin = std::min(umin, v.uv[0]);
      vmin = std::min(vmin, v.uv[1]);
      umax = std::max(umax, v.uv[0]);
      vmax = std::max(vmax, v.uv[1]);
    }
    const float scale = 1.0f / 65535.0f;
    uv_range_ = std::array<float, 4>{umin * scale, vmin * scale, umax * scale,
                                     vmax * scale};
  }
}

void MeshAsset::DoLoad() {
  assert(!renderer_data_.exists());
  renderer_data_ = g_base->graphics_server->renderer()->NewMeshAssetData(*this);

  // once we're loaded lets free up our vert data memory
  std::vector<VertexObjectFull>().swap(vertices_);
  std::vector<uint8_t>().swap(indices8_);
  std::vector<uint16_t>().swap(indices16_);
  std::vector<uint32_t>().swap(indices32_);
}

void MeshAsset::DoUnload() {
  assert(valid_);
  assert(renderer_data_.exists());
  std::vector<VertexObjectFull>().swap(vertices_);
  std::vector<uint8_t>().swap(indices8_);
  std::vector<uint16_t>().swap(indices16_);
  std::vector<uint32_t>().swap(indices32_);
  renderer_data_.Clear();
}

}  // namespace ballistica::base
