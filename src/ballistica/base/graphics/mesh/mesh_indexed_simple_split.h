// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_SPLIT_H_
#define BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_SPLIT_H_

#include "ballistica/base/graphics/mesh/mesh_indexed_static_dynamic.h"

namespace ballistica::base {

// A mesh with static indices and UVs and dynamic positions.
class MeshIndexedSimpleSplit
    : public MeshIndexedStaticDynamic<VertexSimpleSplitStatic,
                                      VertexSimpleSplitDynamic,
                                      MeshDataType::kIndexedSimpleSplit> {
  using MeshIndexedStaticDynamic::MeshIndexedStaticDynamic;  // c++11 magic!
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_MESH_MESH_INDEXED_SIMPLE_SPLIT_H_
