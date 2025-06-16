// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_DATA_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_DATA_H_

#include <list>

#include "ballistica/base/base.h"

namespace ballistica::base {

/// The portion of a mesh that is owned by the graphics server. This
/// contains the renderer-specific data (GL buffers, etc).
class MeshData {
 public:
  MeshData(MeshDataType type, MeshDrawType draw_type)
      : type_(type), draw_type_(draw_type) {}
  virtual ~MeshData();
  std::list<MeshData*>::iterator iterator_;
  auto type() -> MeshDataType { return type_; }
  auto draw_type() -> MeshDrawType { return draw_type_; }
  void Load(Renderer* renderer);
  void Unload(Renderer* renderer);
  auto renderer_data() const -> MeshRendererData* {
    assert(renderer_data_);
    return renderer_data_;
  }

 private:
  MeshRendererData* renderer_data_{};
  MeshDataType type_{};
  MeshDrawType draw_type_{};
  BA_DISALLOW_CLASS_COPIES(MeshData);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_DATA_H_
