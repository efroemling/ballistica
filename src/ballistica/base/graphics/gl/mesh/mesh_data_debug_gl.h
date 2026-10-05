// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_DEBUG_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_DEBUG_GL_H_

#if BA_ENABLE_OPENGL

#include <vector>

#include "ballistica/base/graphics/gl/mesh/mesh_data_gl.h"

namespace ballistica::base {

/// Non-indexed, position+normal vertex data for debug-draw triangles
/// (kBeginDebugDrawTriangles..kEndDebugDraw). The renderer accumulates
/// verts, computes a face normal per triangle, and uploads here each
/// End; drawn with whatever object program is bound (normally the
/// facing-ratio one).
class RendererGL::MeshDataDebugTrianglesGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataDebugTrianglesGL(RendererGL* renderer)
      : MeshDataGL(renderer, 0) {
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
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

  void SetData(const std::vector<VertexObjectSplitDynamic>& verts) {
    assert(!verts.empty());
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    elem_count_ = static_cast<uint32_t>(verts.size());
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast<GLsizeiptr>(verts.size() * sizeof(verts[0])),
                 verts.data(), GL_STREAM_DRAW);
    have_primary_data_ = true;
    BA_DEBUG_CHECK_GL_ERROR;
  }
};

/// Non-indexed, position-only vertex data for debug-draw lines
/// (kBeginDebugDrawLines..kEndDebugDraw). Drawn with whatever simple
/// program is bound.
class RendererGL::MeshDataDebugLinesGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataDebugLinesGL(RendererGL* renderer)
      : MeshDataGL(renderer, 0) {
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    glVertexAttribPointer(kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                          3 * sizeof(float), nullptr);
    glEnableVertexAttribArray(kVertexAttrPosition);
  }

  /// Takes packed xyz floats; count must be a multiple of 3.
  void SetData(const std::vector<float>& xyz) {
    assert(!xyz.empty() && xyz.size() % 3 == 0);
    renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
    elem_count_ = static_cast<uint32_t>(xyz.size() / 3);
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast<GLsizeiptr>(xyz.size() * sizeof(xyz[0])),
                 xyz.data(), GL_STREAM_DRAW);
    have_primary_data_ = true;
    BA_DEBUG_CHECK_GL_ERROR;
  }
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_DEBUG_GL_H_
