// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_TEXT_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_TEXT_MESH_H_

#include <string>

#include "ballistica/base/graphics/mesh/mesh_indexed_dual_texture_full.h"

namespace ballistica::base {

// A mesh set up to draw text. In general you should not use this directly;
// use TextGroup, which will automatically handle switching meshes/textures
// in order to support the full unicode range.
class TextMesh : public MeshIndexedDualTextureFull {
 public:
  enum class HAlign { kLeft, kCenter, kRight };
  enum class VAlign { kNone, kBottom, kCenter, kTop };
  TextMesh();
  void SetText(const std::string& text, HAlign alignment_h, VAlign alignment_v,
               bool big, uint32_t min_val, uint32_t max_val,
               TextMeshEntryType entry_type, TextPacker* packer);
  auto text() const -> const std::string& { return text_; }

 private:
  std::string text_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_TEXT_MESH_H_
