// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_TEXT_TEXT_GROUP_H_
#define BALLISTICA_GRAPHICS_TEXT_TEXT_GROUP_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/assets/assets.h"
#include "ballistica/assets/data/texture_data.h"
#include "ballistica/core/object.h"
#include "ballistica/graphics/mesh/text_mesh.h"

namespace ballistica {

// encapsulates the multiple meshes and textures necessary to
// draw arbitrary text. To actually draw the text, iterate over the meshes
// and textures this class provides to you, drawing each in the same manner
class TextGroup : public Object {
 public:
  // the number of meshes needing to be drawn for this text
  auto GetElementCount() -> int { return static_cast<int>(entries_.size()); }
  auto GetElementMesh(int index) const -> TextMesh* {
    assert(index < static_cast<int>(entries_.size()));
    return &(entries_[index]->mesh);
  }
  auto GetElementTexture(int index) const -> TextureData* {
    assert(index < static_cast<int>(entries_.size()));
    return entries_[index]->tex.get();
  }
  // if you are doing any shader effects in UV-space (such as drop-shadows),
  // scale them by this ..this will account for different character sheets
  // with different sized characters
  auto GetElementUScale(int index) -> float {
    assert(index < static_cast<int>(entries_.size()));
    return entries_[index]->u_scale;
  }
  auto GetElementVScale(int index) -> float {
    assert(index < static_cast<int>(entries_.size()));
    return entries_[index]->v_scale;
  }
  auto GetElementMaxFlatness(int index) const -> float {
    assert(index < static_cast<int>(entries_.size()));
    return entries_[index]->max_flatness;
  }
  auto GetElementCanColor(int index) const -> bool {
    assert(index < static_cast<int>(entries_.size()));
    return entries_[index]->can_color;
  }
  auto GetElementMaskUV2Texture(int index) const -> TextureData* {
    assert(index < static_cast<int>(entries_.size()));
    return g_assets->GetTexture(entries_[index]->type
                                        == TextMeshEntryType::kOSRendered
                                    ? SystemTextureID::kSoftRect2
                                    : SystemTextureID::kSoftRect);
  }
  void SetText(const std::string& text,
               TextMesh::HAlign alignment_h = TextMesh::HAlign::kLeft,
               TextMesh::VAlign alignment_v = TextMesh::VAlign::kNone,
               bool big = false, float resolution_scale = 1.0f);
  auto getText() const -> const std::string& { return text_; }
  void GetCaratPts(const std::string& text_in, TextMesh::HAlign alignment_h,
                   TextMesh::VAlign alignment_v, int carat_pos, float* carat_x,
                   float* carat_y);

 private:
  struct TextMeshEntry {
    TextMeshEntryType type;
    Object::Ref<TextureData> tex;
    TextMesh mesh;
    float u_scale;
    float v_scale;
    bool can_color;
    float max_flatness;
  };
  Object::Ref<TextureData> os_texture_;
  std::vector<std::unique_ptr<TextMeshEntry>> entries_;
  std::string text_;
  bool big_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_TEXT_TEXT_GROUP_H_
