// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_GL_H_

#if BA_ENABLE_OPENGL

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_16.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_32.h"
#include "ballistica/base/graphics/mesh/mesh_renderer_data.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

class RendererGL::MeshDataGL : public MeshRendererData {
 public:
  enum BufferType {
    kVertexBufferPrimary,
    kIndexBuffer,
    kVertexBufferSecondary
  };

  enum Flags {
    kUsesIndexBuffer = 1u,
    kUsesSecondaryBuffer = 1u << 1u,
    kUsesDynamicDraw = 1u << 2u
  };

  MeshDataGL(RendererGL* renderer, uint32_t flags)
      : renderer_(renderer),
        uses_secondary_data_(static_cast<bool>(flags & kUsesSecondaryBuffer)),
        uses_index_data_(static_cast<bool>(flags & kUsesIndexBuffer)) {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;

    // Create our vertex array to hold all this state.

    glGenVertexArrays(1, &vao_);
    BA_DEBUG_CHECK_GL_ERROR;
    renderer->BindVertexArray_(vao_);
    BA_DEBUG_CHECK_GL_ERROR;

    glGenBuffers(GetBufferCount(), vbos_);
    BA_DEBUG_CHECK_GL_ERROR;

    if (uses_index_data_) {
      renderer_->BindVertexArray_(vao_);
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbos_[kIndexBuffer]);
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

  auto uses_index_data() const -> bool { return uses_index_data_; }

  // Set us up to be recycled.
  void Reset() {
    index_state_ = primary_state_ = secondary_state_ = 0;
    have_index_data_ = have_secondary_data_ = have_primary_data_ = false;
  }

  void Bind() {
    renderer_->BindVertexArray_(vao_);
    BA_DEBUG_CHECK_GL_ERROR;
  }

  void Draw(DrawType draw_type) {
    BA_DEBUG_CHECK_GL_ERROR;
    assert(have_primary_data_);
    assert(have_index_data_ || !uses_index_data_);
    assert(have_secondary_data_ || !uses_secondary_data_);
    GLuint gl_draw_type;
    switch (draw_type) {
      case DrawType::kTriangles:
        gl_draw_type = GL_TRIANGLES;
        break;
      case DrawType::kPoints:
        gl_draw_type = GL_POINTS;
        break;
      default:
        throw Exception();
    }
    if (uses_index_data_) {
      glDrawElements(gl_draw_type, elem_count_, index_type_, nullptr);
    } else {
      glDrawArrays(gl_draw_type, 0, elem_count_);
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

  ~MeshDataGL() override {
    assert(g_base->app_adapter->InGraphicsContext());
    // Unbind if we're bound; otherwise we might prevent a new vao that
    // reuses our ID from binding.
    if (vao_ == renderer_->current_vertex_array_) {
      renderer_->BindVertexArray_(0);
    }
    if (!g_base->graphics_server->renderer_context_lost()) {
      glDeleteVertexArrays(1, &vao_);
    }

    // Make sure our dying buffer isn't current (don't wanna prevent binding
    // to a new buffer with a recycled id).
    for (int i = 0; i < GetBufferCount(); i++) {
      if (vbos_[i] == renderer_->active_array_buffer_) {
        renderer_->active_array_buffer_ = -1;
      }
    }
    if (!g_base->graphics_server->renderer_context_lost()) {
      glDeleteBuffers(GetBufferCount(), vbos_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
  }

  void SetIndexData(MeshIndexBuffer32* data) {
    assert(uses_index_data_);
    if (data->state != index_state_) {
      renderer_->BindVertexArray_(vao_);
      elem_count_ = static_cast<uint32_t>(data->elements.size());
      assert(elem_count_ > 0);
      glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                   static_cast_check_fit<GLsizeiptr>(
                       data->elements.size() * sizeof(data->elements[0])),
                   &data->elements[0],
                   dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
      index_state_ = data->state;
      have_index_data_ = true;
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kWarning,
                  "GL WARNING - USING 32 BIT INDICES WHICH WONT WORK IN ES2!!");
      index_type_ = GL_UNSIGNED_INT;
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

  void SetIndexData(MeshIndexBuffer16* data) {
    assert(uses_index_data_);
    if (data->state != index_state_) {
      renderer_->BindVertexArray_(vao_);
      elem_count_ = static_cast<uint32_t>(data->elements.size());
      assert(elem_count_ > 0);
      glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                   static_cast_check_fit<GLsizeiptr>(
                       data->elements.size() * sizeof(data->elements[0])),
                   &data->elements[0],
                   dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
      index_state_ = data->state;
      have_index_data_ = true;
      index_type_ = GL_UNSIGNED_SHORT;
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

  // When dynamic-draw is on, it means *all* buffers should be flagged as
  // dynamic.
  void set_dynamic_draw(bool enable) { dynamic_draw_ = enable; }

  auto vao() const -> GLuint { return vao_; }

 protected:
  template <typename T>
  void UpdateBufferData(BufferType buffer_type, MeshBuffer<T>* data,
                        uint32_t* state, bool* have, GLuint draw_type) {
    assert(state && have);
    if (data->state != *state) {
      BA_DEBUG_CHECK_GL_ERROR;

      // Hmmm didnt think we had to have vao bound here but causes problems
      // on qualcomm if not.
      // #if BA_PLATFORM_ANDROID
      //       if (g_vao_support && renderer_->is_adreno_) {
      //         renderer_->BindVertexArray(vao_);
      //       }
      // #endif
      renderer_->BindArrayBuffer(vbos_[buffer_type]);
      assert(!data->elements.empty());
      if (!uses_index_data_ && buffer_type == kVertexBufferPrimary) {
        elem_count_ = static_cast<uint32_t>(data->elements.size());
      }
      glBufferData(GL_ARRAY_BUFFER,
                   static_cast<GLsizeiptr>(data->elements.size()
                                           * sizeof(data->elements[0])),
                   &(data->elements[0]), draw_type);
      BA_DEBUG_CHECK_GL_ERROR;
      *state = data->state;
      *have = true;
    } else {
      assert(*have);
    }
  }

  // FIXME: Should do some sort of ring-buffer system.
  GLuint vbos_[3]{};
  GLuint vao_{};
  auto GetBufferCount() const -> int {
    return uses_secondary_data_ ? 3 : (uses_index_data_ ? 2 : 1);
  }
  uint32_t index_state_{};
  uint32_t primary_state_{};
  uint32_t secondary_state_{};
  bool uses_index_data_{};
  bool uses_secondary_data_{};
  bool dynamic_draw_{};
  bool have_index_data_{};
  bool have_primary_data_{};
  bool have_secondary_data_{};
  RendererGL* renderer_{};
  uint32_t elem_count_{};
  GLuint index_type_{GL_UNSIGNED_SHORT};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_MESH_MESH_DATA_GL_H_
