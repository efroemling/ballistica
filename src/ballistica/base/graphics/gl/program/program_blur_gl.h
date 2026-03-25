// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_BLUR_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_BLUR_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"

namespace ballistica::base {

class RendererGL::ProgramBlurGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
  };

  ProgramBlurGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
            renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
            Object::New<FragmentShaderGL>(GetFragmentCode(flags)),
            GetName(flags), GetPFlags(flags)),
        flags_(flags),
        pixel_size_x_(0.0f),
        pixel_size_y_(0.0f) {
    SetTextureUnit("colorTex", kColorTexUnit);
    pixel_size_location_ = glGetUniformLocation(program(), "pixelSize");
    assert(pixel_size_location_ != -1);
  }

  void SetPixelSize(float x, float y) {
    assert(IsBound());
    if (x != pixel_size_x_ || y != pixel_size_y_) {
      pixel_size_x_ = x;
      pixel_size_y_ = y;
      glUniform2f(pixel_size_location_, pixel_size_x_, pixel_size_y_);
    }
  }

  void SetColorTexture(const TextureAsset* t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

  void SetColorTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("BlurProgramGL");
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_UV_ATTR;
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n" BA_GLSL_VERTEX_IN
        " vec4 position;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
        "vec2 uv;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV1;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV2;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV3;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV4;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV5;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV6;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV7;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec2 vUV8;\n"
        "uniform " BA_GLSL_MEDIUMP
        "vec2 pixelSize;\n"
        "void main() {\n"
        "   gl_Position = modelViewProjectionMatrix*position;\n"
        "   vUV1 = uv+vec2(-0.5,0)*pixelSize;\n"
        "   vUV2 = uv+vec2(-1.5,0)*pixelSize;\n"
        "   vUV3 = uv+vec2(0.5,0)*pixelSize;\n"
        "   vUV4 = uv+vec2(1.5,0)*pixelSize;\n"
        "   vUV5 = uv+vec2(-0.5,1.0)*pixelSize;\n"
        "   vUV6 = uv+vec2(0.5,1.0)*pixelSize;\n"
        "   vUV7 = uv+vec2(-0.5,-1.0)*pixelSize;\n"
        "   vUV8 = uv+vec2(0.5,-1.0)*pixelSize;\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " BA_GLSL_MEDIUMP "sampler2D colorTex;\n" BA_GLSL_FRAG_IN
        " " BA_GLSL_MEDIUMP "vec2 vUV1;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV2;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV3;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV4;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV5;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV6;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV7;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec2 vUV8;\n"
        "void main() {\n"
        "   " BA_GLSL_FRAGCOLOR " = 0.125*(" BA_GLSL_TEXTURE2D
        "(colorTex,vUV1)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV2)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV3)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV4)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV5)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV6)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV7)\n"
        "                     + " BA_GLSL_TEXTURE2D
        "(colorTex,vUV8));\n"
        "}";
    if (flags & SHD_DEBUG_PRINT) {
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    }
    return s;
  }

  int flags_;
  GLint pixel_size_location_;
  float pixel_size_x_, pixel_size_y_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_BLUR_GL_H_
