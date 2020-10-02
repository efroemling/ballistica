// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/graphics/mesh/image_mesh.h"

namespace ballistica {

const uint16_t kImageMeshIndices[] = {0, 1, 2, 1, 3, 2};
const VertexSimpleSplitStatic kImageMeshVerticesStatic[] = {
    {0, 65535}, {65535, 65535}, {0, 0}, {65535, 0}};

ImageMesh::ImageMesh() {
  SetIndexData(Object::New<MeshIndexBuffer16>(6, kImageMeshIndices));
  SetStaticData(Object::New<MeshBuffer<VertexSimpleSplitStatic> >(
      4, kImageMeshVerticesStatic));
}

}  // namespace ballistica
