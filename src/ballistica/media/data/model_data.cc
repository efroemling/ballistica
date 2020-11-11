// Released under the MIT License. See LICENSE for details.

#include "ballistica/media/data/model_data.h"

#include <string>
#include <vector>

#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/media/media.h"

namespace ballistica {

ModelData::ModelData(const std::string& file_name_in)
    : file_name_(file_name_in) {
  file_name_full_ =
      g_media->FindMediaFile(Media::FileType::kModel, file_name_in);
  valid_ = true;
}

void ModelData::DoPreload() {
  // In headless, don't load anything.
#if !BA_HEADLESS_BUILD

  assert(!file_name_.empty());
  FILE* f = g_platform->FOpen(file_name_full_.c_str(), "rb");
  if (!f) {
    throw Exception("Can't open model: '" + file_name_full_ + "'");
  }

  // We currently read/write in little-endian since that's all we run on at the
  // moment.
#if WORDS_BIGENDIAN
#error FIX THIS FOR BIG ENDIAN
#endif

  uint32_t version;
  if (fread(&version, sizeof(version), 1, f) != 1) {
    throw Exception("Error reading file header for '" + file_name_full_ + "'");
  }
  if (version != kBobFileID) {
    throw Exception("File: '" + file_name_full_
                    + "' is an old format or not a bob file (got id "
                    + std::to_string(version) + ", "
                    + std::to_string(kBobFileID) + ")");
  }

  uint32_t mesh_format;
  if (fread(&mesh_format, sizeof(mesh_format), 1, f) != 1) {
    throw Exception("Error reading mesh_format for '" + file_name_full_ + "'");
  }
  format_ = static_cast<MeshFormat>(mesh_format);
  BA_PRECONDITION((format_ == MeshFormat::kUV16N8Index8)
                  || (format_ == MeshFormat::kUV16N8Index16)
                  || (format_ == MeshFormat::kUV16N8Index32));

  uint32_t vertex_count;
  if (fread(&vertex_count, sizeof(vertex_count), 1, f) != 1) {
    throw Exception("Error reading vertex_count for '" + file_name_full_ + "'");
  }

  uint32_t face_count;
  if (fread(&face_count, sizeof(face_count), 1, f) != 1) {
    throw Exception("Error reading face_count for '" + file_name_full_ + "'");
  }

  vertices_.resize(vertex_count);
  if (fread(&(vertices_[0]), vertices_.size() * sizeof(VertexObjectFull), 1, f)
      != 1) {
    throw Exception("Read failed for " + file_name_full_);
  }
  switch (GetIndexSize()) {
    case 1: {
      indices8_.resize(face_count * 3);
      if (fread(indices8_.data(), indices8_.size() * sizeof(uint8_t), 1, f)
          != 1) {
        throw Exception("Read failed for " + file_name_full_);
      }
      break;
    }
    case 2: {
      indices16_.resize(face_count * 3);
      if (fread(indices16_.data(), indices16_.size() * sizeof(uint16_t), 1, f)
          != 1) {
        throw Exception("Read failed for " + file_name_full_);
      }
      break;
    }
    case 4: {
      indices32_.resize(face_count * 3);
      if (fread(indices32_.data(), indices32_.size() * sizeof(uint32_t), 1, f)
          != 1) {
        throw Exception("Read failed for " + file_name_full_);
      }
      break;
    }
    default:
      throw Exception();
  }

  fclose(f);

#endif  // BA_HEADLESS_BUILD
}

void ModelData::DoLoad() {
  assert(!renderer_data_.exists());
  renderer_data_ = Object::MakeRefCounted(
      g_graphics_server->renderer()->NewModelData(*this));

  // once we're loaded lets free up our vert data memory
  std::vector<VertexObjectFull>().swap(vertices_);
  std::vector<uint8_t>().swap(indices8_);
  std::vector<uint16_t>().swap(indices16_);
  std::vector<uint32_t>().swap(indices32_);
}

void ModelData::DoUnload() {
  assert(valid_);
  assert(renderer_data_.exists());
  std::vector<VertexObjectFull>().swap(vertices_);
  std::vector<uint8_t>().swap(indices8_);
  std::vector<uint16_t>().swap(indices16_);
  std::vector<uint32_t>().swap(indices32_);
  renderer_data_.Clear();
}

}  // namespace ballistica
