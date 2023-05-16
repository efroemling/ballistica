// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_H_

#include "ballistica/base/graphics/mesh/mesh_indexed_base.h"

namespace ballistica::base {

// Mesh using indices and vertex data (all either static or dynamic).
// Supports both 16 and 32 bit indices.
template <typename DATA, MeshDataType T>
class MeshIndexed : public MeshIndexedBase {
 public:
  explicit MeshIndexed(MeshDrawType draw_type = MeshDrawType::kDynamic)
      : MeshIndexedBase(T, draw_type) {}
  void SetData(const Object::Ref<MeshBuffer<DATA>>& data) {
    assert(!data->elements.empty());
    data_ = data;
    data_->state = ++data_state_;
  }
  auto data() const -> const Object::Ref<MeshBuffer<DATA>>& { return data_; }

  auto IsValid() const -> bool override {
    if (!data_.Exists() || data_->elements.empty()
        || !MeshIndexedBase::IsValid()) {
      return false;
    }

    // Make sure our index size covers our element count.
    return IndexSizeIsValid(data_->elements.size());
  }

 private:
  Object::Ref<MeshBuffer<DATA>> data_;
  uint32_t data_state_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_H_
