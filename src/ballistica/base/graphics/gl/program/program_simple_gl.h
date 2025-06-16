// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SIMPLE_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SIMPLE_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"

namespace ballistica::base {
class RendererGL::ProgramSimpleGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
    kColorizeTexUnit,
    kMaskTexUnit,
    kMaskUV2TexUnit,
    kBlurTexUnit
  };

  ProgramSimpleGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
            renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
            Object::New<FragmentShaderGL>(GetFragmentCode(flags)),
            GetName(flags), GetPFlags(flags)),
        flags_(flags) {
    if (flags & SHD_TEXTURE) {
      SetTextureUnit("colorTex", kColorTexUnit);
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
    if ((!(flags & SHD_TEXTURE)) || (flags & SHD_MODULATE)) {
      color_location_ = glGetUniformLocation(program(), "color");
      assert(color_location_ != -1);
    }
    if (flags & SHD_SHADOW) {
      shadow_params_location_ = glGetUniformLocation(program(), "shadowParams");
      assert(shadow_params_location_ != -1);
    }
    if (flags & SHD_GLOW) {
      glow_params_location_ = glGetUniformLocation(program(), "glowParams");
      assert(glow_params_location_ != -1);
    }
    if (flags & SHD_FLATNESS) {
      flatness_location = glGetUniformLocation(program(), "flatness");
      assert(flatness_location != -1);
    }
    if (flags & SHD_MASKED) {
      SetTextureUnit("maskTex", kMaskTexUnit);
    }
    if (flags & SHD_MASK_UV2) {
      SetTextureUnit("maskUV2Tex", kMaskUV2TexUnit);
    }
  }

  void SetColorTexture(const TextureAsset* t) {
    assert(flags_ & SHD_TEXTURE);
    assert(IsBound());
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

  void SetColorTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }

  void SetColor(float r, float g, float b, float a = 1.0f) {
    assert((flags_ & SHD_MODULATE) || !(flags_ & SHD_TEXTURE));
    assert(IsBound());
    if (r != r_ || g != g_ || b != b_ || a != a_) {
      r_ = r;
      g_ = g;
      b_ = b;
      a_ = a;
      glUniform4f(color_location_, r_, g_, b_, a_);
    }
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

  void SetShadow(float shadow_offset_x, float shadow_offset_y,
                 float shadow_blur, float shadow_density) {
    assert(flags_ & SHD_SHADOW);
    assert(IsBound());
    if (shadow_offset_x != shadow_offset_x_
        || shadow_offset_y != shadow_offset_y_ || shadow_blur != shadow_blur_
        || shadow_density != shadow_density_) {
      shadow_offset_x_ = shadow_offset_x;
      shadow_offset_y_ = shadow_offset_y;
      shadow_blur_ = shadow_blur;
      shadow_density_ = shadow_density;
      glUniform4f(shadow_params_location_, shadow_offset_x_, shadow_offset_y_,
                  shadow_blur_, shadow_density_ * 0.4f);
    }
  }

  void SetGlow(float glow_amount, float glow_blur) {
    assert(flags_ & SHD_GLOW);
    assert(IsBound());
    if (glow_amount != glow_amount_ || glow_blur != glow_blur_) {
      glow_amount_ = glow_amount;
      glow_blur_ = glow_blur;
      glUniform2f(glow_params_location_, glow_amount_, glow_blur_);
    }
  }

  void SetFlatness(float flatness) {
    assert(flags_ & SHD_FLATNESS);
    assert(IsBound());
    if (flatness != flatness_) {
      flatness_ = flatness;
      glUniform1f(flatness_location, flatness_);
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

  void SetMaskTexture(const TextureAsset* t) {
    assert(flags_ & SHD_MASKED);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kMaskTexUnit);
  }

  void SetMaskUV2Texture(const TextureAsset* t) {
    assert(flags_ & SHD_MASK_UV2);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kMaskUV2TexUnit);
  }

 private:
  auto GetName(int flags) -> std::string {
    return "SimpleProgramGL texture:"
           + std::to_string((flags & SHD_TEXTURE) != 0)
           + " modulate:" + std::to_string((flags & SHD_MODULATE) != 0)
           + " colorize:" + std::to_string((flags & SHD_COLORIZE) != 0)
           + " colorize2:" + std::to_string((flags & SHD_COLORIZE2) != 0)
           + " premultiply:" + std::to_string((flags & SHD_PREMULTIPLY) != 0)
           + " shadow:" + std::to_string((flags & SHD_SHADOW) != 0)
           + " glow:" + std::to_string((flags & SHD_GLOW) != 0) + " masked:"
           + std::to_string((flags & SHD_MASKED) != 0) + " maskedUV2:"
           + std::to_string((flags & SHD_MASK_UV2) != 0) + " depthBugTest:"
           + std::to_string((flags & SHD_DEPTH_BUG_TEST) != 0)
           + " flatness:" + std::to_string((flags & SHD_FLATNESS) != 0);
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR;
    if (flags & SHD_TEXTURE) {
      pflags |= PFLAG_USES_UV_ATTR;
    }
    if (flags & SHD_MASK_UV2) {
      pflags |= PFLAG_USES_UV2_ATTR;
    }
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    // clang-format off
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
    BA_GLSL_VERTEX_IN " vec4 position;\n";
    if ((flags & SHD_TEXTURE) || (flags & SHD_COLORIZE)
        || (flags & SHD_COLORIZE2)) {
      s += BA_GLSL_VERTEX_IN " vec2 uv;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUV;\n";
    }
    if (flags & SHD_MASK_UV2) {
      s += BA_GLSL_VERTEX_IN " vec2 uv2;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUV2;\n";
    }
    if (flags & SHD_SHADOW) {
      s += BA_GLSL_VERTEX_OUT " vec2 vUVShadow;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUVShadow2;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUVShadow3;\n"
           "uniform " BA_GLSL_LOWP "vec4 shadowParams;\n";
    }
    s += "void main() {\n";
    if (flags & SHD_TEXTURE) {
      s += "   vUV = uv;\n";
    }
    if (flags & SHD_MASK_UV2) {
      s += "   vUV2 = uv2;\n";
    }
    if (flags & SHD_SHADOW) {
      s += "   vUVShadow = uv + 0.4 *"
           " vec2(shadowParams.x, shadowParams.y);\n";
    }
    if (flags & SHD_SHADOW) {
      s += "   vUVShadow2 = uv + 0.8 *"
           " vec2(shadowParams.x, shadowParams.y);\n";
    }
    if (flags & SHD_SHADOW) {
      s += "   vUVShadow3 = uv + 1.3 * vec2(shadowParams.x, shadowParams.y);\n";
    }
    s += "   gl_Position = modelViewProjectionMatrix * position;\n"
         "}";

    if (flags & SHD_DEBUG_PRINT) {
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kInfo,
          "\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    }

    // clang-format off
    return s;
  }

  auto GetFragmentCode(int flags) -> std::string {
    // clang-format off
    std::string s;
    if (flags & SHD_TEXTURE) {
      s += "uniform " BA_GLSL_LOWP "sampler2D colorTex;\n";
    }
    if ((flags & SHD_COLORIZE)) {
      s += "uniform " BA_GLSL_LOWP "sampler2D colorizeTex;\n"
           "uniform " BA_GLSL_LOWP "vec4 colorizeColor;\n";
    }
    if ((flags & SHD_COLORIZE2)) {
      s += "uniform " BA_GLSL_LOWP "vec4 colorize2Color;\n";
    }
    if ((flags & SHD_TEXTURE) || (flags & SHD_COLORIZE)
        || (flags & SHD_COLORIZE2)) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_LOWP "vec2 vUV;\n";
    }
    if (flags & SHD_MASK_UV2) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_LOWP "vec2 vUV2;\n";
    }
    if (flags & SHD_FLATNESS) {
      s += "uniform " BA_GLSL_LOWP "float flatness;\n";
    }
    if (flags & SHD_SHADOW) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_LOWP "vec2 vUVShadow;\n"
           BA_GLSL_FRAG_IN " " BA_GLSL_LOWP "vec2 vUVShadow2;\n"
           BA_GLSL_FRAG_IN " " BA_GLSL_LOWP "vec2 vUVShadow3;\n"
           "uniform " BA_GLSL_LOWP "vec4 shadowParams;\n";
    }
    if (flags & SHD_GLOW) {
      s += "uniform " BA_GLSL_LOWP "vec2 glowParams;\n";
    }
    if ((flags & SHD_MODULATE) || (!(flags & SHD_TEXTURE))) {
      s += "uniform " BA_GLSL_LOWP "vec4 color;\n";
    }
    if (flags & SHD_MASKED) {
      s += "uniform " BA_GLSL_LOWP "sampler2D maskTex;\n";
    }
    if (flags & SHD_MASK_UV2) {
      s += "uniform " BA_GLSL_LOWP "sampler2D maskUV2Tex;\n";
    }
    s += "void main() {\n";
    if (!(flags & SHD_TEXTURE)) {
      s += "   " BA_GLSL_FRAGCOLOR " = color;\n";
    } else {
      std::string blur_arg;
      if (flags & SHD_GLOW) {
        s += "   " BA_GLSL_LOWP
             "vec4 cVal = " BA_GLSL_TEXTURE2D "(colorTex, vUV, glowParams.g);\n"
             "      " BA_GLSL_FRAGCOLOR
             " = vec4(color.rgb * cVal.rgb * cVal.a * "
             "glowParams.r, 0.0)";  // we premultiply this.
        if (flags & SHD_MASK_UV2) {
          s += " * vec4(" BA_GLSL_TEXTURE2D "(maskUV2Tex, vUV2).a)";
        }
        s += ";\n";
      } else {
        if ((flags & SHD_COLORIZE) || (flags & SHD_COLORIZE2)) {
          // TEMP TEST
          s += "   " BA_GLSL_LOWP
               "vec4 colorizeVal = " BA_GLSL_TEXTURE2D "(colorizeTex, vUV);\n";
        }
        if (flags & SHD_COLORIZE) {
          s += "   " BA_GLSL_LOWP "float colorizeA = colorizeVal.r;\n";
        }
        if (flags & SHD_COLORIZE2) {
          s += "   " BA_GLSL_LOWP "float colorizeB = colorizeVal.g;\n";
        }
        if (flags & SHD_MASKED) {
          s += "   " BA_GLSL_MEDIUMP "vec4 mask = "
                     BA_GLSL_TEXTURE2D "(maskTex, vUV);";
        }

        if (flags & SHD_MODULATE) {
          if (flags & SHD_FLATNESS) {
            s += "   " BA_GLSL_LOWP
                 "vec4 rawTexColor = " BA_GLSL_TEXTURE2D "(colorTex, vUV);\n"
                 "   " BA_GLSL_FRAGCOLOR " = color * "
                       "vec4(mix(rawTexColor.rgb, vec3(1.0), flatness),"
                       " rawTexColor.a)";
          } else {
            s += "   " BA_GLSL_FRAGCOLOR " = color * "
                       BA_GLSL_TEXTURE2D "(colorTex, vUV)";
          }
        } else {
          s += "   " BA_GLSL_FRAGCOLOR " = "
                     BA_GLSL_TEXTURE2D "(colorTex, vUV)";
        }

        if (flags & SHD_COLORIZE) {
          s += " * (vec4(1.0 - colorizeA) + colorizeColor * colorizeA)";
        }
        if (flags & SHD_COLORIZE2) {
          s += " * (vec4(1.0 - colorizeB) + colorize2Color * colorizeB)";
        }
        if (flags & SHD_MASKED) {
          s += " * vec4(vec3(mask.r), mask.a) + "
               "vec4(vec3(mask.g) * colorizeColor.rgb + vec3(mask.b), 0.0)";
        }
        s += ";\n";

        if (flags & SHD_SHADOW) {
          s += "   " BA_GLSL_LOWP
                     "float shadowA = ("
                     BA_GLSL_TEXTURE2D "(colorTex, vUVShadow).a + "
                     "" BA_GLSL_TEXTURE2D "(colorTex, vUVShadow2, 1.0).a + "
                     "" BA_GLSL_TEXTURE2D
                     "(colorTex, vUVShadow3, 2.0).a) * shadowParams.a";

          if (flags & SHD_MASK_UV2) {
            s += " * " BA_GLSL_TEXTURE2D "(maskUV2Tex, vUV2).a";
          }
          s += ";\n";
          s += "   " BA_GLSL_FRAGCOLOR
               " = "
               "vec4(" BA_GLSL_FRAGCOLOR ".rgb * " BA_GLSL_FRAGCOLOR
               ".a," BA_GLSL_FRAGCOLOR
               ".a) + "
               "(1.0 - " BA_GLSL_FRAGCOLOR ".a) * vec4(0, 0, 0, shadowA);\n";
          s += "   " BA_GLSL_FRAGCOLOR
                      " = "
                     "vec4(" BA_GLSL_FRAGCOLOR
                     ".rgb / max(0.001, " BA_GLSL_FRAGCOLOR ".a), "
                     BA_GLSL_FRAGCOLOR ".a);\n";
        }
      }

      if (flags & SHD_DEPTH_BUG_TEST) {
        s += "   " BA_GLSL_FRAGCOLOR " = vec4(abs(gl_FragCoord.z - "
                   BA_GLSL_FRAGCOLOR ".r));\n";
      }

      if (flags & SHD_PREMULTIPLY) {
        s += "   " BA_GLSL_FRAGCOLOR " = vec4(" BA_GLSL_FRAGCOLOR
             ".rgb * "
             "" BA_GLSL_FRAGCOLOR ".a, " BA_GLSL_FRAGCOLOR ".a);";
      }
    }
    s += "}";

    if (flags & SHD_DEBUG_PRINT) {
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    }

    // clang-format on
    return s;
  }

  float r_{}, g_{}, b_{}, a_{};
  float colorize_r_{}, colorize_g_{}, colorize_b_{}, colorize_a_{};
  float colorize2_r_{}, colorize2_g_{}, colorize2_b_{}, colorize2_a_{};
  float shadow_offset_x_{}, shadow_offset_y_{}, shadow_blur_{},
      shadow_density_{};
  float glow_amount_{}, glow_blur_{};
  float flatness_{};
  GLint color_location_{};
  GLint colorize_color_location_{};
  GLint colorize2_color_location_{};
  GLint shadow_params_location_{};
  GLint glow_params_location_{};
  GLint flatness_location{};
  int flags_{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SIMPLE_GL_H_
