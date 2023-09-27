// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_SMOKE_FULL_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_SMOKE_FULL_GL_H_

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/mesh/mesh_data_gl.h"

namespace ballistica::base {

class RendererGL::MeshDataSmokeFullGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataSmokeFullGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    glVertexAttribPointer(
        kVertexAttrUV, 2, GL_FLOAT, GL_FALSE, sizeof(VertexSmokeFull),
        reinterpret_cast<void*>(offsetof(VertexSmokeFull, uv)));
    glEnableVertexAttribArray(kVertexAttrUV);
    glVertexAttribPointer(
        kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexSmokeFull),
        reinterpret_cast<void*>(offsetof(VertexSmokeFull, position)));
    glEnableVertexAttribArray(kVertexAttrPosition);
    glVertexAttribPointer(
        kVertexAttrErode, 1, GL_UNSIGNED_BYTE, GL_TRUE, sizeof(VertexSmokeFull),
        reinterpret_cast<void*>(offsetof(VertexSmokeFull, erode)));
    glEnableVertexAttribArray(kVertexAttrErode);
    glVertexAttribPointer(
        kVertexAttrDiffuse, 1, GL_UNSIGNED_BYTE, GL_TRUE,
        sizeof(VertexSmokeFull),
        reinterpret_cast<void*>(offsetof(VertexSmokeFull, diffuse)));
    glEnableVertexAttribArray(kVertexAttrDiffuse);
    glVertexAttribPointer(
        kVertexAttrColor, 4, GL_UNSIGNED_BYTE, GL_TRUE, sizeof(VertexSmokeFull),
        reinterpret_cast<void*>(offsetof(VertexSmokeFull, color)));
    glEnableVertexAttribArray(kVertexAttrColor);
  }
  void SetData(MeshBuffer<VertexSmokeFull>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_SMOKE_FULL_GL_H_
