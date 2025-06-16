// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SPRITE_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SPRITE_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics.h"

namespace ballistica::base {

class RendererGL::ProgramSpriteGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit { kColorTexUnit, kDepthTexUnit };

  ProgramSpriteGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
            renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
            Object::New<FragmentShaderGL>(GetFragmentCode(flags)),
            GetName(flags), GetPFlags(flags)),
        flags_(flags),
        r_(0),
        g_(0),
        b_(0),
        a_(0) {
    SetTextureUnit("colorTex", kColorTexUnit);

    if (flags & SHD_OVERLAY) {
      SetTextureUnit("depthTex", kDepthTexUnit);
    }

    if (flags & SHD_COLOR) {
      color_location_ = glGetUniformLocation(program(), "colorU");
      assert(color_location_ != -1);
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

  void SetColorTexture(const TextureAsset* t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

  void SetDepthTexture(GLuint t) {
    assert(flags_ & SHD_OVERLAY);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kDepthTexUnit);
  }

  void SetColor(float r, float g, float b, float a = 1.0f) {
    assert(flags_ & SHD_COLOR);
    assert(IsBound());
    if (r != r_ || g != g_ || b != b_ || a != a_) {
      r_ = r;
      g_ = g;
      b_ = b;
      a_ = a;
      glUniform4f(color_location_, r_, g_, b_, a_);
    }
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("SpriteProgramGL");
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_SIZE_ATTR
                 | PFLAG_USES_COLOR_ATTR | PFLAG_USES_UV_ATTR;
    if (flags & SHD_CAMERA_ALIGNED) pflags |= PFLAG_USES_CAM_ORIENT_MATRIX;
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s += "uniform mat4 modelViewProjectionMatrix;\n" BA_GLSL_VERTEX_IN
         " vec4 position;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
         "vec2 uv;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
         "float size;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP "vec2 vUV;\n";

    if (flags & SHD_COLOR) {
      s += "uniform " BA_GLSL_LOWP "vec4 colorU;\n";
    }

    if (flags & SHD_CAMERA_ALIGNED) {
      s += "uniform mat4 camOrientMatrix;\n";
    }

    if (flags & SHD_OVERLAY) {
      s += BA_GLSL_VERTEX_OUT " " BA_GLSL_LOWP "vec4 vScreenCoord;\n";
    }

    s += BA_GLSL_VERTEX_IN " " BA_GLSL_LOWP "vec4 color;\n" BA_GLSL_VERTEX_OUT
                           " " BA_GLSL_LOWP
                           "vec4 vColor;\n"
                           "void main() {\n";

    if (flags & SHD_CAMERA_ALIGNED) {
      s += "   " BA_GLSL_HIGHP
           "vec4 pLocal = "
           "(position+camOrientMatrix*vec4((uv.s-0.5)*size,0,(uv.t-0.5)*size,0)"
           ");\n";
    } else {
      s += "   " BA_GLSL_HIGHP
           "vec4 pLocal = "
           "(position+vec4((uv.s-0.5)*size,0,(uv.t-0.5)*size,0));\n";
    }
    s += "   gl_Position = modelViewProjectionMatrix*pLocal;\n"
         "   vUV = uv;\n";
    if (flags & SHD_COLOR) {
      s += "   vColor = color*colorU;\n";
    } else {
      s += "   vColor = color;\n";
    }
    if (flags & SHD_OVERLAY)
      s += "   vScreenCoord = "
           "vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT) {
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    }
    return s;
  }

  auto GetFragmentCode(int flags) -> std::string {
    std::string s;

    s += "uniform " BA_GLSL_LOWP "sampler2D colorTex;\n" BA_GLSL_FRAG_IN
         " " BA_GLSL_MEDIUMP "vec2 vUV;\n" BA_GLSL_FRAG_IN " " BA_GLSL_LOWP
         "vec4 vColor;\n";
    if (flags & SHD_OVERLAY) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
                           "vec4 vScreenCoord;\n"
                           "uniform " BA_GLSL_MEDIUMP "sampler2D depthTex;\n";
    }

    s += "void main() {\n"
         "   " BA_GLSL_FRAGCOLOR " = vColor*vec4(" BA_GLSL_TEXTURE2D
         "(colorTex,vUV).r);\n";
    if (flags & SHD_EXP2)
      s += "   " BA_GLSL_FRAGCOLOR
           " = vec4(vUV,0,0) + "
           "vec4(" BA_GLSL_FRAGCOLOR ".rgb*" BA_GLSL_FRAGCOLOR
           ".rgb," BA_GLSL_FRAGCOLOR ".a);\n";
    if (flags & SHD_OVERLAY) {
      s += "   " BA_GLSL_MEDIUMP "float depth = " BA_GLSL_TEXTURE2DPROJ
           "(depthTex,vScreenCoord).r;\n";
      // Adreno 320 bug where depth is returned as 0..1 instead of
      // glDepthRange().
      if (GetFunkyDepthIssue_()) {
        s += "    depth = " + std::to_string(kBackingDepth3) + "+depth*("
             + std::to_string(kBackingDepth4) + "-"
             + std::to_string(kBackingDepth3) + ");\n";
      }
      s += "   " BA_GLSL_FRAGCOLOR
           " *= "
           "(1.0-smoothstep(0.0,0.001,gl_FragCoord.z-depth));\n";
    }
    s += "}";
    if (flags & SHD_DEBUG_PRINT) {
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    }
    return s;
  }

  float r_, g_, b_, a_;
  GLint color_location_;
  int flags_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SPRITE_GL_H_
