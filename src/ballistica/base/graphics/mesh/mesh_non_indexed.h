// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_NON_INDEXED_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_NON_INDEXED_H_

#include "ballistica/base/graphics/mesh/mesh.h"
#include "ballistica/base/graphics/mesh/mesh_buffer.h"

namespace ballistica::base {

// Mesh using non-indexed vertex data.  Good for situations where vertices
// are never shared between primitives (such as drawing points/sprites/etc).
template <typename DATA, MeshDataType T>
class MeshNonIndexed : public Mesh {
 public:
  explicit MeshNonIndexed(MeshDrawType drawType = MeshDrawType::kDynamic)
      : Mesh(T, drawType), data_state_(0) {}
  // NOLINTNEXTLINE
  void SetData(const Object::Ref<MeshBuffer<DATA>>& data) {
    data_ = data;
    data_->state = ++data_state_;
  }

  // Call this if you have nothing to draw.
  void SetEmpty() { data_.clear(); }
  auto IsValid() const -> bool override {
#if BA_DEBUG_BUILD
    // Make extra sure that we're actually valid in debug mode.
    if (data_.exists()) {
      assert(data_->elements.size() > 0);
    }
#endif
    return (data_.exists());
  }

 private:
  Object::Ref<MeshBuffer<DATA>> data_{};
  uint32_t data_state_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_NON_INDEXED_H_
