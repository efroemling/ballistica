// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GROUP_H_
#define BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GROUP_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/graphics/mesh/text_mesh.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Encapsulates the multiple meshes and textures necessary to draw arbitrary
// text. To actually draw the text, iterate over the meshes and textures
// this class provides to you, drawing each in the same manner.
class TextGroup : public Object {
 public:
  // The number of meshes needing to be drawn for this text.
  auto GetElementCount() -> int { return static_cast<int>(entries_.size()); }

  auto GetElementMesh(int index) const -> TextMesh* {
    assert(index < static_cast<int>(entries_.size()));
    return &(entries_[index]->mesh);
  }

  auto GetElementTexture(int index) const -> TextureAsset* {
    assert(index < static_cast<int>(entries_.size()));
    return entries_[index]->tex.Get();
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

  auto GetElementMaskUV2Texture(int index) const -> TextureAsset* {
    assert(index < static_cast<int>(entries_.size()));
    return g_base->assets->SysTexture(entries_[index]->type
                                              == TextMeshEntryType::kOSRendered
                                          ? SysTextureID::kSoftRect2
                                          : SysTextureID::kSoftRect);
  }

  void SetText(const std::string& text,
               TextMesh::HAlign alignment_h = TextMesh::HAlign::kLeft,
               TextMesh::VAlign alignment_v = TextMesh::VAlign::kNone,
               bool big = false, float resolution_scale = 1.0f);

  auto text() const -> const std::string& { return text_; }

  void GetCaratPts(const std::string& text_in, TextMesh::HAlign alignment_h,
                   TextMesh::VAlign alignment_v, int carat_pos, float* carat_x,
                   float* carat_y);

 private:
  struct TextMeshEntry {
    TextMeshEntryType type;
    Object::Ref<TextureAsset> tex;
    TextMesh mesh;
    float u_scale;
    float v_scale;
    bool can_color;
    float max_flatness;
  };
  Object::Ref<TextureAsset> os_texture_;
  std::vector<std::unique_ptr<TextMeshEntry>> entries_;
  std::string text_;
  bool big_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_TEXT_TEXT_GROUP_H_
