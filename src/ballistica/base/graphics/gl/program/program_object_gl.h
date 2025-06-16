// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_OBJECT_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_OBJECT_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"

namespace ballistica::base {

class RendererGL::ProgramObjectGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
    kReflectionTexUnit,
    kVignetteTexUnit,
    kLightShadowTexUnit,
    kColorizeTexUnit
  };

  ProgramObjectGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
            renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
            Object::New<FragmentShaderGL>(GetFragmentCode(flags)),
            GetName(flags), GetPFlags(flags)),
        flags_(flags),
        r_(0),
        g_(0),
        b_(0),
        a_(0),
        colorize_r_(0),
        colorize_g_(0),
        colorize_b_(0),
        colorize_a_(0),
        colorize2_r_(0),
        colorize2_g_(0),
        colorize2_b_(0),
        colorize2_a_(0),
        add_r_(0),
        add_g_(0),
        add_b_(0),
        r_mult_r_(0),
        r_mult_g_(0),
        r_mult_b_(0),
        r_mult_a_(0) {
    SetTextureUnit("colorTex", kColorTexUnit);
    SetTextureUnit("vignetteTex", kVignetteTexUnit);
    color_location_ = glGetUniformLocation(program(), "color");
    assert(color_location_ != -1);
    if (flags & SHD_REFLECTION) {
      SetTextureUnit("reflectionTex", kReflectionTexUnit);
      reflect_mult_location_ = glGetUniformLocation(program(), "reflectMult");
      assert(reflect_mult_location_ != -1);
    }
    if (flags & SHD_LIGHT_SHADOW) {
      SetTextureUnit("lightShadowTex", kLightShadowTexUnit);
    }
    if (flags & SHD_ADD) {
      color_add_location_ = glGetUniformLocation(program(), "colorAdd");
      assert(color_add_location_ != -1);
    }
    if (flags & SHD_COLORIZE) {
      SetTextureUnit("colorizeTex", kColorizeTexUnit);
      colorize_color_location_ =
          glGetUniformLocation(program(), "colorizeColor");
      assert(colorize_color_location_ != -1);
    }
    if (flags & SHD_COLORIZE2) {
      colorize2_color_location_ =
          glGetUniformLocation(program(), "colorize2Color");
      assert(colorize2_color_location_ != -1);
    }
  }

  void SetColorTexture(const TextureAsset* t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

  void SetReflectionTexture(const TextureAsset* t) {
    assert(flags_ & SHD_REFLECTION);
    renderer()->BindTexture_(GL_TEXTURE_CUBE_MAP, t, kReflectionTexUnit);
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

  void SetAddColor(float r, float g, float b) {
    assert(IsBound());
    if (r != add_r_ || g != add_g_ || b != add_b_) {
      add_r_ = r;
      add_g_ = g;
      add_b_ = b;
      glUniform4f(color_add_location_, add_r_, add_g_, add_b_, 0.0f);
    }
  }

  void SetReflectionMult(float r, float g, float b, float a = 0.0f) {
    assert(IsBound());
    // include tint and ambient color...
    auto renderer = this->renderer();
    float rFin = r * renderer->tint().x * renderer->ambient_color().x;
    float gFin = g * renderer->tint().y * renderer->ambient_color().y;
    float bFin = b * renderer->tint().z * renderer->ambient_color().z;
    if (rFin != r_mult_r_ || gFin != r_mult_g_ || bFin != r_mult_b_
        || a != r_mult_a_) {
      r_mult_r_ = rFin;
      r_mult_g_ = gFin;
      r_mult_b_ = bFin;
      r_mult_a_ = a;
      assert(flags_ & SHD_REFLECTION);
      glUniform4f(reflect_mult_location_, r_mult_r_, r_mult_g_, r_mult_b_,
                  r_mult_a_);
    }
  }

  void SetVignetteTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kVignetteTexUnit);
  }

  void SetLightShadowTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kLightShadowTexUnit);
  }

  void SetColorizeColor(float r, float g, float b, float a = 1.0f) {
    assert(flags_ & SHD_COLORIZE);
    assert(IsBound());
    if (r != colorize_r_ || g != colorize_g_ || b != colorize_b_
        || a != colorize_a_) {
      colorize_r_ = r;
      colorize_g_ = g;
      colorize_b_ = b;
      colorize_a_ = a;
      glUniform4f(colorize_color_location_, colorize_r_, colorize_g_,
                  colorize_b_, colorize_a_);
    }
  }

  void SetColorize2Color(float r, float g, float b, float a = 1.0f) {
    assert(flags_ & SHD_COLORIZE2);
    assert(IsBound());
    if (r != colorize2_r_ || g != colorize2_g_ || b != colorize2_b_
        || a != colorize2_a_) {
      colorize2_r_ = r;
      colorize2_g_ = g;
      colorize2_b_ = b;
      colorize2_a_ = a;
      glUniform4f(colorize2_color_location_, colorize2_r_, colorize2_g_,
                  colorize2_b_, colorize2_a_);
    }
  }

  void SetColorizeTexture(const TextureAsset* t) {
    assert(flags_ & SHD_COLORIZE);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorizeTexUnit);
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("ProgramObjectGL")
           + " reflect:" + std::to_string((flags & SHD_REFLECTION) != 0)
           + " lightShadow:" + std::to_string((flags & SHD_LIGHT_SHADOW) != 0)
           + " add:" + std::to_string((flags & SHD_ADD) != 0) + " colorize:"
           + std::to_string((flags & SHD_COLORIZE) != 0) + " colorize2:"
           + std::to_string((flags & SHD_COLORIZE2) != 0) + " transparent:"
           + std::to_string((flags & SHD_OBJ_TRANSPARENT) != 0) + " worldSpace:"
           + std::to_string((flags & SHD_WORLD_SPACE_PTS) != 0);
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_UV_ATTR;
    if (flags & SHD_REFLECTION)
      pflags |= (PFLAG_USES_NORMAL_ATTR | PFLAG_USES_CAM_POS);
    if (((flags & SHD_REFLECTION) || (flags & SHD_LIGHT_SHADOW))
        && !(flags & SHD_WORLD_SPACE_PTS))
      pflags |= PFLAG_USES_MODEL_WORLD_MATRIX;
    if (flags & SHD_LIGHT_SHADOW) pflags |= PFLAG_USES_SHADOW_PROJECTION_MATRIX;
    if (flags & SHD_WORLD_SPACE_PTS) pflags |= PFLAG_WORLD_SPACE_PTS;
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "uniform vec4 camPos;\n" BA_GLSL_VERTEX_IN
        " vec4 position;\n" BA_GLSL_VERTEX_IN " " BA_GLSL_LOWP
        "vec2 uv;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_LOWP
        "vec2 vUV;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_MEDIUMP
        "vec4 vScreenCoord;\n";
    if ((flags & SHD_REFLECTION) || (flags & SHD_LIGHT_SHADOW))
      s += "uniform mat4 modelWorldMatrix;\n";
    if (flags & SHD_REFLECTION)
      s += BA_GLSL_VERTEX_IN " " BA_GLSL_MEDIUMP
                             "vec3 normal;\n" BA_GLSL_VERTEX_OUT
                             " " BA_GLSL_MEDIUMP "vec3 vReflect;\n";
    if (flags & SHD_LIGHT_SHADOW)
      s += "uniform mat4 lightShadowProjectionMatrix;\n" BA_GLSL_VERTEX_OUT
           " " BA_GLSL_MEDIUMP "vec4 vLightShadowUV;\n";
    s +=
        "void main() {\n"
        "   vUV = uv;\n"
        "   gl_Position = modelViewProjectionMatrix*position;\n"
        "   vScreenCoord = vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
        "   vScreenCoord.xy += vec2(1.0);\n"
        "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    if (((flags & SHD_LIGHT_SHADOW) || (flags & SHD_REFLECTION))
        && !(flags & SHD_WORLD_SPACE_PTS)) {
      s += "   vec4 worldPos = modelWorldMatrix*position;\n";
    }
    if (flags & SHD_LIGHT_SHADOW) {
      if (flags & SHD_WORLD_SPACE_PTS)
        s += "   vLightShadowUV = (lightShadowProjectionMatrix*position);\n";
      else
        s += "   vLightShadowUV = (lightShadowProjectionMatrix*worldPos);\n";
    }
    if (flags & SHD_REFLECTION) {
      if (flags & SHD_WORLD_SPACE_PTS)
        s += "   vReflect = reflect(vec3(position - camPos),normal);\n";
      else
        s += "   vReflect = reflect(vec3(worldPos - "
             "camPos),normalize(vec3(modelWorldMatrix * vec4(normal,0.0))));\n";
    }
    s += "}";
    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " BA_GLSL_LOWP
        "sampler2D colorTex;\n"
        "uniform " BA_GLSL_LOWP
        "sampler2D vignetteTex;\n"
        "uniform " BA_GLSL_LOWP "vec4 color;\n" BA_GLSL_FRAG_IN " " BA_GLSL_LOWP
        "vec2 vUV;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
        "vec4 vScreenCoord;\n";
    if (flags & SHD_ADD) {
      s += "uniform " BA_GLSL_LOWP "vec4 colorAdd;\n";
    }
    if (flags & SHD_REFLECTION) {
      s += "uniform " BA_GLSL_LOWP
           "samplerCube reflectionTex;\n" BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP
           "vec3 vReflect;\n"
           "uniform " BA_GLSL_LOWP "vec4 reflectMult;\n";
    }
    if (flags & SHD_COLORIZE) {
      s += "uniform " BA_GLSL_LOWP
           "sampler2D colorizeTex;\n"
           "uniform " BA_GLSL_LOWP "vec4 colorizeColor;\n";
    }
    if (flags & SHD_COLORIZE2) {
      s += "uniform " BA_GLSL_LOWP "vec4 colorize2Color;\n";
    }
    if (flags & SHD_LIGHT_SHADOW) {
      s += "uniform " BA_GLSL_LOWP "sampler2D lightShadowTex;\n" BA_GLSL_FRAG_IN
           " " BA_GLSL_MEDIUMP "vec4 vLightShadowUV;\n";
    }
    s += "void main() {\n";
    if (flags & SHD_LIGHT_SHADOW) {
      s += "   " BA_GLSL_LOWP "vec4 lightShadVal = " BA_GLSL_TEXTURE2DPROJ
           "(lightShadowTex, vLightShadowUV);\n";
    }
    if ((flags & SHD_COLORIZE) || (flags & SHD_COLORIZE2)) {
      s += "   " BA_GLSL_LOWP "vec4 colorizeVal = " BA_GLSL_TEXTURE2D
           "(colorizeTex, vUV);\n";
    }
    if (flags & SHD_COLORIZE) {
      s += "   " BA_GLSL_LOWP "float colorizeA = colorizeVal.r;\n";
    }
    if (flags & SHD_COLORIZE2) {
      s += "   " BA_GLSL_LOWP "float colorizeB = colorizeVal.g;\n";
    }
    s += "   " BA_GLSL_FRAGCOLOR " = (color * " BA_GLSL_TEXTURE2D
         "(colorTex, vUV)";
    if (flags & SHD_COLORIZE) {
      s += " * (vec4(1.0-colorizeA)+colorizeColor*colorizeA)";
    }
    if (flags & SHD_COLORIZE2) {
      s += " * (vec4(1.0-colorizeB)+colorize2Color*colorizeB)";
    }
    s += ")";

    // add in lights/shadows
    if (flags & SHD_LIGHT_SHADOW) {
      if (flags & SHD_OBJ_TRANSPARENT) {
        s += " * vec4((2.0 * lightShadVal).rgb, 1) + "
             "vec4((lightShadVal - 0.5).rgb,0)";
      } else {
        s += " * (2.0 * lightShadVal) + (lightShadVal - 0.5)";
      }
    }

    // add glow and reflection
    if (flags & SHD_REFLECTION)
      s += " + (reflectMult*" BA_GLSL_TEXTURECUBE "(reflectionTex, vReflect))";
    if (flags & SHD_ADD) s += " + colorAdd";

    // subtract vignette
    s += " - vec4(" BA_GLSL_TEXTURE2DPROJ "(vignetteTex, vScreenCoord).rgb,0)";

    s += ";\n";
    // s +=  BA_GLSL_FRAGCOLOR " = 0.999 * " BA_GLSL_TEXTURE2DPROJ
    // "(vignetteTex,vScreenCoord)
    // + 0.01 *  BA_GLSL_FRAGCOLOR ";";

    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  float r_, g_, b_, a_;
  float colorize_r_, colorize_g_, colorize_b_, colorize_a_;
  float colorize2_r_, colorize2_g_, colorize2_b_, colorize2_a_;
  float add_r_, add_g_, add_b_;
  float r_mult_r_, r_mult_g_, r_mult_b_, r_mult_a_;
  GLint color_location_;
  GLint colorize_color_location_;
  GLint colorize2_color_location_;
  GLint color_add_location_;
  GLint reflect_mult_location_;
  int flags_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_OBJECT_GL_H_
