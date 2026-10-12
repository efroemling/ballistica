// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/mesh_asset.h"

#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/assets/asset_blob.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/core/core.h"
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

#endif  // BA_HEADLESS_BUILD
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
