// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_SPLIT_H_
#define BALLISTICA_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_SPLIT_H_

#include "ballistica/graphics/mesh/mesh_indexed_static_dynamic.h"

namespace ballistica {

// a mesh with static indices and UVs and dynamic positions
class MeshIndexedSimpleSplit
    : public MeshIndexedStaticDynamic<VertexSimpleSplitStatic,
                                      VertexSimpleSplitDynamic,
                                      MeshDataType::kIndexedSimpleSplit> {
  using MeshIndexedStaticDynamic::MeshIndexedStaticDynamic;  // c++11 magic!
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_SPLIT_H_
