// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SMOKE_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SMOKE_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"

namespace ballistica::base {

class RendererGL::ProgramSmokeGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit { kColorTexUnit, kDepthTexUnit, kBlurTexUnit };

  ProgramSmokeGL(RendererGL* renderer, int flags)
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
      SetTextureUnit("blurTex", kBlurTexUnit);
    }
    color_location_ = glGetUniformLocation(program(), "colorMult");
    assert(color_location_ != -1);
  }

  void SetColorTexture(const TextureAsset* t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

  void SetDepthTexture(GLuint t) {
    assert(flags_ & SHD_OVERLAY);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kDepthTexUnit);
  }

  void SetBlurTexture(GLuint t) {
    assert(flags_ & SHD_OVERLAY);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kBlurTexUnit);
  }

  void SetColor(float r, float g, float b, float a = 1.0f) {
    assert(IsBound());
    // include tint..
    if (r * renderer()->tint().x != r_ || g * renderer()->tint().y != g_
        || b * renderer()->tint().z != b_ || a != a_) {
      r_ = r * renderer()->tint().x;
      g_ = g * renderer()->tint().y;
      b_ = b * renderer()->tint().z;
      a_ = a;
      glUniform4f(color_location_, r_, g_, b_, a_);
    }
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("SmokeProgramGL");
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_DIFFUSE_ATTR
                 | PFLAG_USES_UV_ATTR | PFLAG_WORLD_SPACE_PTS
                 | PFLAG_USES_ERODE_ATTR | PFLAG_USES_COLOR_ATTR;
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n" BA_GLSL_VERTEX_IN
        " vec4 position;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
        "vec2 uv;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_LOWP
        "float erode;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
        "float diffuse;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_LOWP
        "float vErode;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
        "vec4 color;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_LOWP
        "vec4 vColor;\n"
        "uniform " BA_GLSL_MEDIUMP "vec4 colorMult;\n";
    if (flags & SHD_OVERLAY) {
      s += BA_GLSL_VERTEX_OUT " " BA_GLSL_LOWP
                              "vec4 cDiffuse;\n" BA_GLSL_VERTEX_OUT
                              " " BA_GLSL_MEDIUMP "vec4 vScreenCoord;\n";
    }
    s += "void main() {\n"
         "   vUV = uv;\n"
         "   gl_Position = modelViewProjectionMatrix*position;\n"
         "   vErode = erode;\n";
    // in overlay mode we pass color/diffuse to the pixel-shader since we
    // combine them there with a blurred bg image to get a soft look.  In the
    // simple version we just use a flat ambient color here.
    if (flags & SHD_OVERLAY) {
      s += "   vScreenCoord = "
           "vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
           "   vColor = vec4(vec3(7.0*diffuse),0.7) * color * colorMult;\n"
           "   cDiffuse = colorMult*(0.3+0.8*diffuse);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    } else {
      s += "   vColor = "
           "(vec4(vec3(7.0),1.0)*color+vec4(vec3(0.4),0))*vec4(vec3(diffuse),0."
           "4) * colorMult;\n";
    }
    s += "   vColor *= vec4(vec3(vColor.a),1.0);\n";  // premultiply
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " BA_GLSL_LOWP "sampler2D colorTex;\n" BA_GLSL_FRAG_IN
        " " BA_GLSL_MEDIUMP "vec2 vUV;\n" BA_GLSL_FRAG_IN " " BA_GLSL_LOWP
        "float vErode;\n" BA_GLSL_FRAG_IN " " BA_GLSL_LOWP "vec4 vColor;\n";
    if (flags & SHD_OVERLAY) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
                           "vec4 vScreenCoord;\n"
                           "uniform " BA_GLSL_LOWP
                           "sampler2D depthTex;\n"
                           "uniform " BA_GLSL_LOWP
                           "sampler2D blurTex;\n" BA_GLSL_FRAG_IN
                           " " BA_GLSL_LOWP "vec4 cDiffuse;\n";
    }
    s += "void main() {\n";
    s += "   " BA_GLSL_LOWP
         "float erodeMult = smoothstep(vErode,1.0," BA_GLSL_TEXTURE2D
         "(colorTex,vUV).r);\n"
         "   " BA_GLSL_FRAGCOLOR " = (vColor*vec4(erodeMult));";
    if (flags & SHD_OVERLAY) {
      s += "   " BA_GLSL_FRAGCOLOR " += vec4(vec3(" BA_GLSL_FRAGCOLOR
           ".a),0) * cDiffuse * "
           "(0.11+0.8*" BA_GLSL_TEXTURE2DPROJ "(blurTex,vScreenCoord));\n";
      s += "   " BA_GLSL_MEDIUMP " float depth =" BA_GLSL_TEXTURE2DPROJ
           "(depthTex,vScreenCoord).r;\n";

      // Work around Adreno bug where depth is returned as 0..1 instead of
      // glDepthRange().
      if (GetFunkyDepthIssue_()) {
        s += "    depth = " + std::to_string(kBackingDepth3) + "+depth*("
             + std::to_string(kBackingDepth4) + "-"
             + std::to_string(kBackingDepth3) + ");\n";
      }
      s += "   " BA_GLSL_FRAGCOLOR
           " *= "
           "(1.0-smoothstep(0.0,0.002,gl_FragCoord.z-depth));\n";
    }

    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  float r_, g_, b_, a_;
  GLint color_location_;
  int flags_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SMOKE_GL_H_
