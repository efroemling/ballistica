// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_BASE_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_BASE_H_

#include "ballistica/base/graphics/mesh/mesh.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_16.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_32.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

// Mesh supporting index data.
class MeshIndexedBase : public Mesh {
 public:
  explicit MeshIndexedBase(MeshDataType type,
                           MeshDrawType draw_type = MeshDrawType::kDynamic)
      : Mesh(type, draw_type) {}

  auto index_data_size() const -> int {
    assert(index_data_size_ != 0);
    return index_data_size_;
  }

  void SetIndexData(const Object::Ref<MeshIndexBuffer32>& data) {
    assert(data.exists() && !data->elements.empty());
    // unlike vertex data, index data might often remain the same, so lets test
    // for that and avoid some gl updates..
    if (index_data_32_.exists()) {
      assert(data.exists() && index_data_32_.get());
      if (data->elements == index_data_32_->elements) {
        return;  // just keep our existing one
      }
    }
    index_data_32_ = data;
    index_data_32_->state = ++index_state_;
    index_data_size_ = 4;
    // kill any other index data we have
    index_data_16_.Clear();
  }

  void SetIndexData(const Object::Ref<MeshIndexBuffer16>& data) {
    assert(data.exists() && !data->elements.empty());
    // unlike vertex data, index data might often remain the same, so lets test
    // for that and avoid some gl updates..
    if (index_data_16_.exists()) {
      assert(index_data_16_.get());
      if (data->elements == index_data_16_->elements) {
        return;  // just keep our existing one
      }
    }
    // FIXME - we should probably just pass in a strong ref as an arg?...
    index_data_16_ = data;
    index_data_16_->state = ++index_state_;
    index_data_size_ = 2;
    // kill any other index data we have
    index_data_32_.Clear();
  }

  // call this if you have nothing to draw
  void SetEmpty() {
    index_data_16_.Clear();
    index_data_32_.Clear();
  }
  auto IsValid() const -> bool override {
    switch (index_data_size()) {
      case 4:
        return (index_data_32_.exists() && !index_data_32_->elements.empty());
      case 2:
        return (index_data_16_.exists() && !index_data_16_->elements.empty());
      default:
        return false;
    }
  }
  // Checks for valid index sizes given a data length.
  // Will print a one-time warning and return false if invalid.
  // For use by subclasses in their IsValid() overrides
  auto IndexSizeIsValid(size_t data_size) const -> bool {
    if (index_data_size() == 2 && data_size > 65535) {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                  "Got mesh data with > 65535 elems and 16 bit indices: "
                      + GetObjectDescription()
                      + ". This case requires 32 bit indices.");
      return false;
    }
    return true;
  }
  auto GetIndexData() const -> MeshBufferBase* {
    switch (index_data_size()) {
      case 4:
        return index_data_32_.get();
      case 2:
        return index_data_16_.get();
      default:
        throw Exception();
    }
  }

 private:
  Object::Ref<MeshIndexBuffer32> index_data_32_;
  Object::Ref<MeshIndexBuffer16> index_data_16_;
  int index_data_size_ = 0;
  uint32_t index_state_ = 0;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_BASE_H_
