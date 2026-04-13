// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_GL_H_

#if BA_ENABLE_OPENGL

#include <string>
#include <utility>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"

namespace ballistica::base {

// Base class for fragment/vertex shaders.
class RendererGL::ShaderGL : public Object {
 public:
  auto GetThreadOwnership() const -> ThreadOwnership override {
    return ThreadOwnership::kGraphicsContext;
  }

  ShaderGL(GLenum type_in, const std::string& src_in) : type_(type_in) {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;
    assert(type_ == GL_FRAGMENT_SHADER || type_ == GL_VERTEX_SHADER);
    shader_ = glCreateShader(type_);
    BA_DEBUG_CHECK_GL_ERROR;
    BA_PRECONDITION(shader_);

    std::string src_fin = src_in;
    if (type_ == GL_FRAGMENT_SHADER) {
      src_fin = "out " BA_GLSL_HIGHP "vec4 " BA_GLSL_FRAGCOLOR ";\n" + src_fin;
    }

#if BA_OPENGL_IS_ES
    // Shader version for 3.0 ES
    src_fin = "#version 300 es\n" + src_fin;
#else
    // Shader version for 3.2 GL core profile.
    src_fin = "#version 150 core\n" + src_fin;
#endif

    const char* s = src_fin.c_str();
    glShaderSource(shader_, 1, &s, nullptr);
    glCompileShader(shader_);
    GLint compile_status;
    glGetShaderiv(shader_, GL_COMPILE_STATUS, &compile_status);
    if (compile_status == GL_FALSE) {
      const char* version = (const char*)glGetString(GL_VERSION);
      const char* vendor = (const char*)glGetString(GL_VENDOR);
      const char* renderer = (const char*)glGetString(GL_RENDERER);
      // Let's not crash here. We have a better chance of calling home this
      // way and theres a chance the game will still be playable.
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kError,
          std::string("Compile failed for ") + GetTypeName()
              + " shader:\n------------SOURCE BEGIN-------------\n" + src_fin
              + "\n-----------SOURCE END-------------\n" + GetInfo()
              + "\nrenderer: " + renderer + "\nvendor: " + vendor
              + "\nversion:" + version);
    } else {
      assert(compile_status == GL_TRUE);
      std::string info = GetInfo();
      if (!info.empty()
          && (strstr(info.c_str(), "error:") || strstr(info.c_str(), "warning:")
              || strstr(info.c_str(), "Error:")
              || strstr(info.c_str(), "Warning:"))) {
        const char* version = (const char*)glGetString(GL_VERSION);
        const char* vendor = (const char*)glGetString(GL_VENDOR);
        const char* renderer = (const char*)glGetString(GL_RENDERER);
        g_core->logging->Log(
            LogName::kBaGraphics, LogLevel::kError,
            std::string("WARNING: info returned for ") + GetTypeName()
                + " shader:\n------------SOURCE BEGIN-------------\n" + src_fin
                + "\n-----------SOURCE END-------------\n" + info
                + "\nrenderer: " + renderer + "\nvendor: " + vendor
                + "\nversion:" + version);
      }
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

  ~ShaderGL() override {
    assert(g_base->app_adapter->InGraphicsContext());
    if (!g_base->graphics_server->renderer_context_lost()) {
      glDeleteShader(shader_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
  }

  auto shader() const -> GLuint { return shader_; }

 private:
  auto GetTypeName() const -> const char* {
    if (type_ == GL_VERTEX_SHADER) {
      return "vertex";
    } else {
      return "fragment";
    }
  }

  auto GetInfo() -> std::string {
    static char log[1024];
    GLsizei log_size;
    glGetShaderInfoLog(shader_, sizeof(log), &log_size, log);
    return log;
  }

  std::string name_;
  GLuint shader_{};
  GLenum type_{};
  BA_DISALLOW_CLASS_COPIES(ShaderGL);
};

class RendererGL::FragmentShaderGL : public RendererGL::ShaderGL {
 public:
  explicit FragmentShaderGL(const std::string& src_in)
      : ShaderGL(GL_FRAGMENT_SHADER, src_in) {}
};

class RendererGL::VertexShaderGL : public RendererGL::ShaderGL {
 public:
  explicit VertexShaderGL(const std::string& src_in)
      : ShaderGL(GL_VERTEX_SHADER, src_in) {}
};

class RendererGL::ProgramGL {
 public:
  ProgramGL(RendererGL* renderer,
            const Object::Ref<VertexShaderGL>& vertex_shader_in,
            const Object::Ref<FragmentShaderGL>& fragment_shader_in,
            std::string name, int pflags)
      : fragment_shader_(fragment_shader_in),
        vertex_shader_(vertex_shader_in),
        renderer_(renderer),
        pflags_(pflags),
        name_(std::move(name)) {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;
    program_ = glCreateProgram();
    BA_PRECONDITION(program_);
    glAttachShader(program_, fragment_shader_->shader());
    glAttachShader(program_, vertex_shader_->shader());
    assert(pflags_ & PFLAG_USES_POSITION_ATTR);
    if (pflags_ & PFLAG_USES_POSITION_ATTR) {
      glBindAttribLocation(program_, kVertexAttrPosition, "position");
    }
    if (pflags_ & PFLAG_USES_UV_ATTR) {
      glBindAttribLocation(program_, kVertexAttrUV, "uv");
    }
    if (pflags_ & PFLAG_USES_NORMAL_ATTR) {
      glBindAttribLocation(program_, kVertexAttrNormal, "normal");
    }
    if (pflags_ & PFLAG_USES_ERODE_ATTR) {
      glBindAttribLocation(program_, kVertexAttrErode, "erode");
    }
    if (pflags_ & PFLAG_USES_COLOR_ATTR) {
      glBindAttribLocation(program_, kVertexAttrColor, "color");
    }
    if (pflags_ & PFLAG_USES_SIZE_ATTR) {
      glBindAttribLocation(program_, kVertexAttrSize, "size");
    }
    if (pflags_ & PFLAG_USES_DIFFUSE_ATTR) {
      glBindAttribLocation(program_, kVertexAttrDiffuse, "diffuse");
    }
    if (pflags_ & PFLAG_USES_UV2_ATTR) {
      glBindAttribLocation(program_, kVertexAttrUV2, "uv2");
    }
    glLinkProgram(program_);
    GLint linkStatus;
    glGetProgramiv(program_, GL_LINK_STATUS, &linkStatus);
    if (linkStatus == GL_FALSE) {
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kError,
          "Link failed for program '" + name_ + "':\n" + GetInfo());
    } else {
      assert(linkStatus == GL_TRUE);

      std::string info = GetInfo();
      if (!info.empty()
          && (strstr(info.c_str(), "error:") || strstr(info.c_str(), "warning:")
              || strstr(info.c_str(), "Error:")
              || strstr(info.c_str(), "Warning:"))) {
        g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                             "WARNING: program using frag shader '" + name_
                                 + "' returned info:\n" + info);
      }
    }

    // Go ahead and bind ourself so child classes can config uniforms and
    // whatnot.
    Bind();
    mvp_uniform_ = glGetUniformLocation(program_, "modelViewProjectionMatrix");
    assert(mvp_uniform_ != -1);
    if (pflags_ & PFLAG_USES_MODEL_WORLD_MATRIX) {
      model_world_matrix_uniform_ =
          glGetUniformLocation(program_, "modelWorldMatrix");
      assert(model_world_matrix_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_MODEL_VIEW_MATRIX) {
      model_view_matrix_uniform_ =
          glGetUniformLocation(program_, "modelViewMatrix");
      assert(model_view_matrix_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_CAM_POS) {
      cam_pos_uniform_ = glGetUniformLocation(program_, "camPos");
      assert(cam_pos_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_CAM_ORIENT_MATRIX) {
      cam_orient_matrix_uniform_ =
          glGetUniformLocation(program_, "camOrientMatrix");
      assert(cam_orient_matrix_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_SHADOW_PROJECTION_MATRIX) {
      light_shadow_projection_matrix_uniform_ =
          glGetUniformLocation(program_, "lightShadowProjectionMatrix");
      assert(light_shadow_projection_matrix_uniform_ != -1);
    }
  }

  virtual ~ProgramGL() {
    assert(g_base->app_adapter->InGraphicsContext());
    if (!g_base->graphics_server->renderer_context_lost()) {
      glDetachShader(program_, fragment_shader_->shader());
      glDetachShader(program_, vertex_shader_->shader());
      glDeleteProgram(program_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
  }

  auto IsBound() const -> bool {
    return (renderer()->GetActiveProgram_() == this);
  }

  auto program() const -> GLuint { return program_; }

  void Bind() { renderer_->UseProgram_(this); }

  auto name() const -> const std::string& { return name_; }

  // Should grab matrices from the renderer or whatever else it needs in
  // prep for drawing.
  void PrepareToDraw() {
    BA_DEBUG_CHECK_GL_ERROR;

    assert(IsBound());

    // Update matrices as necessary.

    int mvp_state =
        g_base->graphics_server->GetModelViewProjectionMatrixState();
    if (mvp_state != mvp_state_) {
      mvp_state_ = mvp_state;
      glUniformMatrix4fv(
          mvp_uniform_, 1, 0,
          g_base->graphics_server->GetModelViewProjectionMatrix().m);
    }
    BA_DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_MODEL_WORLD_MATRIX) {
      // With world space points this would be identity; don't waste time.
      assert(!(pflags_ & PFLAG_WORLD_SPACE_PTS));
      int state = g_base->graphics_server->GetModelWorldMatrixState();
      if (state != model_world_matrix_state_) {
        model_world_matrix_state_ = state;
        glUniformMatrix4fv(model_world_matrix_uniform_, 1, 0,
                           g_base->graphics_server->GetModelWorldMatrix().m);
      }
    }
    BA_DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_MODEL_VIEW_MATRIX) {
      // With world space points this would be identity; don't waste time.
      assert(!(pflags_ & PFLAG_WORLD_SPACE_PTS));
      // There's no state for just modelview but this works.
      int state = g_base->graphics_server->GetModelViewProjectionMatrixState();
      if (state != model_view_matrix_state_) {
        model_view_matrix_state_ = state;
        glUniformMatrix4fv(model_view_matrix_uniform_, 1, 0,
                           g_base->graphics_server->model_view_matrix().m);
      }
    }
    BA_DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_CAM_POS) {
      int state = g_base->graphics_server->cam_pos_state();
      if (state != cam_pos_state_) {
        cam_pos_state_ = state;
        const Vector3f& p(g_base->graphics_server->cam_pos());
        glUniform4f(cam_pos_uniform_, p.x, p.y, p.z, 1.0f);
      }
    }
    BA_DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_CAM_ORIENT_MATRIX) {
      int state = g_base->graphics_server->GetCamOrientMatrixState();
      if (state != cam_orient_matrix_state_) {
        cam_orient_matrix_state_ = state;
        glUniformMatrix4fv(cam_orient_matrix_uniform_, 1, 0,
                           g_base->graphics_server->GetCamOrientMatrix().m);
      }
    }
    BA_DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_SHADOW_PROJECTION_MATRIX) {
      int state =
          g_base->graphics_server->light_shadow_projection_matrix_state();
      if (state != light_shadow_projection_matrix_state_) {
        light_shadow_projection_matrix_state_ = state;
        glUniformMatrix4fv(
            light_shadow_projection_matrix_uniform_, 1, 0,
            g_base->graphics_server->light_shadow_projection_matrix().m);
      }
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

 protected:
  void SetTextureUnit(const char* tex_name, int unit) {
    assert(IsBound());
    int c = glGetUniformLocation(program_, tex_name);
    if (c == -1) {
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                           "ShaderGL: " + name_
                               + ": Can't set texture unit for texture '"
                               + tex_name + "'");
      BA_DEBUG_CHECK_GL_ERROR;
    } else {
      glUniform1i(c, unit);
    }
  }

  auto GetInfo() -> std::string {
    static char log[1024];
    GLsizei log_size;
    glGetProgramInfoLog(program_, sizeof(log), &log_size, log);
    return log;
  }

  auto renderer() const -> RendererGL* { return renderer_; }

 private:
  RendererGL* renderer_{};
  Object::Ref<FragmentShaderGL> fragment_shader_;
  Object::Ref<VertexShaderGL> vertex_shader_;
  std::string name_;
  GLuint program_{};
  GLint mvp_uniform_{};
  GLint model_world_matrix_uniform_{};
  GLint model_view_matrix_uniform_{};
  GLint light_shadow_projection_matrix_uniform_{};
  GLint cam_pos_uniform_{};
  GLint cam_orient_matrix_uniform_{};
  int cam_orient_matrix_state_{};
  int light_shadow_projection_matrix_state_{};
  int pflags_{};
  int mvp_state_{};
  int cam_pos_state_{};
  int model_world_matrix_state_{};
  int model_view_matrix_state_{};
  BA_DISALLOW_CLASS_COPIES(ProgramGL);
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_GL_H_
