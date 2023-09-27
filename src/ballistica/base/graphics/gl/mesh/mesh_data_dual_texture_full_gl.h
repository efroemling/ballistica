// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_DUAL_TEXTURE_FULL_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_DUAL_TEXTURE_FULL_GL_H_

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/mesh/mesh_data_gl.h"

namespace ballistica::base {

class RendererGL::MeshDataDualTextureFullGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataDualTextureFullGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    glVertexAttribPointer(
        kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
        sizeof(VertexDualTextureFull),
        reinterpret_cast<void*>(offsetof(VertexDualTextureFull, uv)));
    glEnableVertexAttribArray(kVertexAttrUV);
    glVertexAttribPointer(
        kVertexAttrUV2, 2, GL_UNSIGNED_SHORT, GL_TRUE,
        sizeof(VertexDualTextureFull),
        reinterpret_cast<void*>(offsetof(VertexDualTextureFull, uv2)));
    glEnableVertexAttribArray(kVertexAttrUV2);
    glVertexAttribPointer(
        kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
        sizeof(VertexDualTextureFull),
        reinterpret_cast<void*>(offsetof(VertexDualTextureFull, position)));
    glEnableVertexAttribArray(kVertexAttrPosition);
  }
  void SetData(MeshBuffer<VertexDualTextureFull>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};
}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_DUAL_TEXTURE_FULL_GL_H_
