// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_H_

#include "ballistica/base/graphics/mesh/mesh_data.h"
#include "ballistica/base/graphics/mesh/mesh_data_client_handle.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// A dynamically defined mesh (unlike a mesh asset which is completely static).
class Mesh : public Object {
 public:
  auto type() const -> MeshDataType { return type_; }
  auto mesh_data_client_handle() -> Object::Ref<MeshDataClientHandle>& {
    return mesh_data_client_handle_;
  }

  // Return whether it is safe to attempt drawing with present data.
  virtual auto IsValid() const -> bool = 0;
  auto last_frame_def_num() const -> int64_t { return last_frame_def_num_; }
  void set_last_frame_def_num(int64_t f) { last_frame_def_num_ = f; }

 protected:
  explicit Mesh(MeshDataType type,
                MeshDrawType draw_type = MeshDrawType::kStatic)
      : valid_(false), type_(type), last_frame_def_num_(0) {
    mesh_data_client_handle_ =
        Object::New<MeshDataClientHandle>(new MeshData(type, draw_type));
  }

 private:
  int64_t last_frame_def_num_{};
  MeshDataType type_{};

  // Renderer data for this mesh. We keep this as a shared pointer
  // so that frame_defs or other things using this mesh can keep it alive
  // even if we go away.
  Object::Ref<MeshDataClientHandle> mesh_data_client_handle_;
  bool valid_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_H_
