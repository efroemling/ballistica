// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_STATIC_DYNAMIC_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_STATIC_DYNAMIC_H_

#include "ballistica/base/graphics/mesh/mesh_indexed_base.h"

namespace ballistica::base {

/// A mesh with static indices, some static vertex data, and some dynamic
/// vertex data.
template <typename STATICDATA, typename DYNAMICDATA, MeshDataType T>
class MeshIndexedStaticDynamic : public MeshIndexedBase {
 public:
  MeshIndexedStaticDynamic() : MeshIndexedBase(T) {}
  void SetStaticData(const Object::Ref<MeshBuffer<STATICDATA>>& data) {
    assert(data->elements.size() > 0);
    static_data_ = data;
    static_data_->state = ++static_state_;
  }
  void SetDynamicData(const Object::Ref<MeshBuffer<DYNAMICDATA>>& data) {
    assert(data->elements.size() > 0);
    dynamic_data_ = data;
    dynamic_data_->state = ++dynamic_state_;
  }
  auto IsValid() const -> bool override {
    if (!static_data_.Exists() || static_data_->elements.empty()
        || !dynamic_data_.Exists() || dynamic_data_->elements.empty()
        || !MeshIndexedBase::IsValid()) {
      return false;
    }

    // Static and dynamic data sizes should always match, right?
    if (static_data_->elements.size() != dynamic_data_->elements.size()) {
      BA_LOG_ONCE(LogLevel::kError,
                  "Mesh static and dynamic data sizes do not match");
      return false;
    }

    // Make sure our index size covers our element count.
    return IndexSizeIsValid(static_data_->elements.size());
  }
  auto static_data() const -> const Object::Ref<MeshBuffer<STATICDATA>>& {
    return static_data_;
  }
  auto dynamic_data() const -> const Object::Ref<MeshBuffer<DYNAMICDATA>>& {
    return dynamic_data_;
  }

 private:
  Object::Ref<MeshBuffer<STATICDATA>> static_data_;
  Object::Ref<MeshBuffer<DYNAMICDATA>> dynamic_data_;
  uint32_t static_state_{};
  uint32_t dynamic_state_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_STATIC_DYNAMIC_H_
