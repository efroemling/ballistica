// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_SPRITE_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_SPRITE_GL_H_

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/mesh/mesh_data_gl.h"

namespace ballistica::base {

class RendererGL::MeshDataSpriteGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataSpriteGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    glVertexAttribPointer(
        kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
        reinterpret_cast<void*>(offsetof(VertexSprite, position)));
    glEnableVertexAttribArray(kVertexAttrPosition);
    glVertexAttribPointer(kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
                          sizeof(VertexSprite),
                          reinterpret_cast<void*>(offsetof(VertexSprite, uv)));
    glEnableVertexAttribArray(kVertexAttrUV);
    glVertexAttribPointer(
        kVertexAttrSize, 1, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
        reinterpret_cast<void*>(offsetof(VertexSprite, size)));
    glEnableVertexAttribArray(kVertexAttrSize);
    glVertexAttribPointer(
        kVertexAttrColor, 4, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
        reinterpret_cast<void*>(offsetof(VertexSprite, color)));
    glEnableVertexAttribArray(kVertexAttrColor);
  }
  void SetData(MeshBuffer<VertexSprite>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_SPRITE_GL_H_
