// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_BUFFER_BASE_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_BUFFER_BASE_H_

#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// Buffers used by the logic thread to pass indices/vertices/etc. to meshes
// in the graphics thread. Note that it is safe to create these in other
// threads; you just need to turn off thread-checks until you pass ownership
// to the game thread. (or just avoid creating references outside of the
// logic thread).
class MeshBufferBase : public Object {
 public:
  uint32_t state;  // which dynamicState value on the mesh this corresponds to
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_BUFFER_BASE_H_
