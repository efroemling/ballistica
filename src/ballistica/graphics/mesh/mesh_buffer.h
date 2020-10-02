// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_MESH_MESH_BUFFER_H_
#define BALLISTICA_GRAPHICS_MESH_MESH_BUFFER_H_

#include <cstring>
#include <vector>

#include "ballistica/graphics/mesh/mesh_buffer_base.h"

namespace ballistica {

// Buffer for arbitrary mesh data.
template <typename T>
class MeshBuffer : public MeshBufferBase {
 public:
  MeshBuffer() = default;
  explicit MeshBuffer(size_t initial_size) : elements(initial_size) {}
  MeshBuffer(size_t initial_size, const T* initial_data)
      : elements(initial_size) {
    memcpy(&elements[0], initial_data, initial_size * sizeof(T));
  }
  std::vector<T> elements;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_MESH_MESH_BUFFER_H_
