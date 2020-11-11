// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_MESH_MESH_BUFFER_BASE_H_
#define BALLISTICA_GRAPHICS_MESH_MESH_BUFFER_BASE_H_

#include "ballistica/core/object.h"

namespace ballistica {

// Buffers used by the game thread to pass indices/vertices/etc. to meshes in
// the graphics thread.  Note that it is safe to create these in other threads;
// you just need to turn off thread-checks until you pass ownership to the game
// thread. (or just avoid creating references outside of the game thread)
class MeshBufferBase : public Object {
 public:
  uint32_t state;  // which dynamicState value on the mesh this corresponds to
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_MESH_MESH_BUFFER_BASE_H_
