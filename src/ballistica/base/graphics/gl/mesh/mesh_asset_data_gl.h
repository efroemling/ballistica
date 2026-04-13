// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_ASSET_DATA_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_ASSET_DATA_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics_server.h"

namespace ballistica::base {

class RendererGL::MeshAssetDataGL : public MeshAssetRendererData {
 public:
  enum BufferType { kVertices, kIndices, kBufferCount };

  MeshAssetDataGL(const MeshAsset& model, RendererGL* renderer)
      : renderer_(renderer) {
#if BA_DEBUG_BUILD
    name_ = model.GetName();
#endif

    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;

    // Create our vertex array to hold all this state.

    glGenVertexArrays(1, &vao_);
    BA_DEBUG_CHECK_GL_ERROR;
    renderer->BindVertexArray_(vao_);
    BA_DEBUG_CHECK_GL_ERROR;

    glGenBuffers(kBufferCount, vbos_);

    BA_DEBUG_CHECK_GL_ERROR;

    // Fill our vertex data buffer.
    renderer_->BindArrayBuffer(vbos_[kVertices]);
    BA_DEBUG_CHECK_GL_ERROR;
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast_check_fit<GLsizeiptr>(model.vertices().size()
                                                   * sizeof(VertexObjectFull)),
                 &(model.vertices()[0]), GL_STATIC_DRAW);
    BA_DEBUG_CHECK_GL_ERROR;

    glVertexAttribPointer(
        kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexObjectFull),
        reinterpret_cast<void*>(offsetof(VertexObjectFull, position)));
    glEnableVertexAttribArray(kVertexAttrPosition);
    glVertexAttribPointer(
        kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE, sizeof(VertexObjectFull),
        reinterpret_cast<void*>(offsetof(VertexObjectFull, uv)));
    glEnableVertexAttribArray(kVertexAttrUV);
    glVertexAttribPointer(
        kVertexAttrNormal, 3, GL_SHORT, GL_TRUE, sizeof(VertexObjectFull),
        reinterpret_cast<void*>(offsetof(VertexObjectFull, normal)));
    glEnableVertexAttribArray(kVertexAttrNormal);
    BA_DEBUG_CHECK_GL_ERROR;

    // Fill our index data buffer.
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbos_[kIndices]);

    const GLvoid* index_data;
    switch (model.GetIndexSize()) {
      case 1: {
        elem_count_ = static_cast<uint32_t>(model.indices8().size());
        index_type_ = GL_UNSIGNED_BYTE;
        index_data = static_cast<const GLvoid*>(model.indices8().data());
        break;
      }
      case 2: {
        elem_count_ = static_cast<uint32_t>(model.indices16().size());
        index_type_ = GL_UNSIGNED_SHORT;
        index_data = static_cast<const GLvoid*>(model.indices16().data());
        break;
      }
      case 4: {
        elem_count_ = static_cast<uint32_t>(model.indices32().size());
        index_type_ = GL_UNSIGNED_INT;
        index_data = static_cast<const GLvoid*>(model.indices32().data());
        break;
      }
      default:
        throw Exception();
    }
    glBufferData(
        GL_ELEMENT_ARRAY_BUFFER,
        static_cast_check_fit<GLsizeiptr>(elem_count_ * model.GetIndexSize()),
        index_data, GL_STATIC_DRAW);

    BA_DEBUG_CHECK_GL_ERROR;
  }

  ~MeshAssetDataGL() override {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;

    // Unbind if we're bound; otherwise if a new vao pops up with our same
    // ID it'd be prevented from binding.
    if (vao_ == renderer_->current_vertex_array_) {
      renderer_->BindVertexArray_(0);
    }
    if (!g_base->graphics_server->renderer_context_lost()) {
      glDeleteVertexArrays(1, &vao_);
    }

    // Make sure our dying buffer isn't current (don't wanna prevent binding
    // to a new buffer with a recycled id).
    for (unsigned int vbo : vbos_) {
      if (vbo == renderer_->active_array_buffer_) {
        renderer_->active_array_buffer_ = -1;
      }
    }
    if (!g_base->graphics_server->renderer_context_lost()) {
      glDeleteBuffers(kBufferCount, vbos_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
  }

  void Bind() {
    renderer_->BindVertexArray_(vao_);
    BA_DEBUG_CHECK_GL_ERROR;
  }
  void Draw() {
    BA_DEBUG_CHECK_GL_ERROR;
    if (elem_count_ > 0) {
      glDrawElements(GL_TRIANGLES, elem_count_, index_type_, nullptr);
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

#if BA_DEBUG_BUILD
  auto name() const -> const std::string& { return name_; }
#endif

 private:
#if BA_DEBUG_BUILD
  std::string name_;
#endif

  RendererGL* renderer_{};
  uint32_t elem_count_{};
  GLuint index_type_{};
  GLuint vao_{};
  GLuint vbos_[kBufferCount]{};
  // FakeVertexArrayObject* fake_vao_{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_ASSET_DATA_GL_H_
