// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_OBJECT_SPLIT_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_OBJECT_SPLIT_GL_H_

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/mesh/mesh_data_gl.h"

namespace ballistica::base {

class RendererGL::MeshDataObjectSplitGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataObjectSplitGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesSecondaryBuffer | kUsesIndexBuffer) {
    // Set up our static vertex data.
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    glVertexAttribPointer(
        kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
        sizeof(VertexObjectSplitStatic),
        reinterpret_cast<void*>(offsetof(VertexObjectSplitStatic, uv)));
    glEnableVertexAttribArray(kVertexAttrUV);

    // ..and our dynamic vertex data.
    renderer_->BindArrayBuffer(vbos_[kVertexBufferSecondary]);
    glVertexAttribPointer(
        kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
        sizeof(VertexObjectSplitDynamic),
        reinterpret_cast<void*>(offsetof(VertexObjectSplitDynamic, position)));
    glEnableVertexAttribArray(kVertexAttrPosition);
    glVertexAttribPointer(
        kVertexAttrNormal, 3, GL_SHORT, GL_TRUE,
        sizeof(VertexObjectSplitDynamic),
        reinterpret_cast<void*>(offsetof(VertexObjectSplitDynamic, normal)));
    glEnableVertexAttribArray(kVertexAttrNormal);
  }
  void SetStaticData(MeshBuffer<VertexObjectSplitStatic>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_, GL_STATIC_DRAW);
  }
  void SetDynamicData(MeshBuffer<VertexObjectSplitDynamic>* data) {
    assert(uses_secondary_data_);
    UpdateBufferData(kVertexBufferSecondary, data, &secondary_state_,
                     &have_secondary_data_,
                     GL_DYNAMIC_DRAW);  // this is *always* dynamic
  }
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_OBJECT_SPLIT_GL_H_
