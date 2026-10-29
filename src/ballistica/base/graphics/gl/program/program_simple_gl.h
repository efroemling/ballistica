// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SIMPLE_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SIMPLE_GL_H_

#if BA_ENABLE_OPENGL

#include <algorithm>
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
      colorize3_color_location_ =
          glGetUniformLocation(program(), "colorize3Color");
      assert(colorize3_color_location_ != -1);
    }
    if (flags & SHD_COLORIZE) {
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
      shadow_color_location_ = glGetUniformLocation(program(), "shadowColor");
      assert(shadow_color_location_ != -1);
      if (flags & SHD_TEXT_GLOW) {
        text_glow_location_ = glGetUniformLocation(program(), "textGlow");
        assert(text_glow_location_ != -1);
      }
    }
    if (flags & SHD_GLOW) {
      glow_params_location_ = glGetUniformLocation(program(), "glowParams");
      assert(glow_params_location_ != -1);
    }
    if (flags & SHD_FLATNESS) {
      flatness_location = glGetUniformLocation(program(), "flatness");
      assert(flatness_location != -1);
    }
    // texPremultiplied selects premult-vs-straight handling in the
    // flatness lerp, the shadow-compositing path, and the masked-draw
    // additive frame term, so it exists whenever any of those are present.
    if ((flags & SHD_FLATNESS) || (flags & SHD_SHADOW)
        || ((flags & SHD_MASKED) && (flags & SHD_MODULATE))) {
      tex_premultiplied_location_ =
          glGetUniformLocation(program(), "texPremultiplied");
      assert(tex_premultiplied_location_ != -1);
    }
    if ((flags & SHD_MASKED) && (flags & SHD_MODULATE)) {
      mask_straight_location_ = glGetUniformLocation(program(), "maskStraight");
      assert(mask_straight_location_ != -1);
      mask_add_mult_location_ = glGetUniformLocation(program(), "maskAddMult");
      assert(mask_add_mult_location_ != -1);
    }
    if (flags & SHD_MASKED) {
      SetTextureUnit("maskTex", kMaskTexUnit);
    }
    if (flags & SHD_MASK_UV2) {
      SetTextureUnit("maskUV2Tex", kMaskUV2TexUnit);
    }
    if (flags & SHD_UV2_FADE) {
      premult_blend_location_ = glGetUniformLocation(program(), "premultBlend");
      assert(premult_blend_location_ != -1);
    }
    if (flags & SHD_LAYERED_MASK) {
      SetTextureUnit("maskTex", kMaskTexUnit);
      underlay_color_location_ =
          glGetUniformLocation(program(), "underlayColor");
      assert(underlay_color_location_ != -1);
      layer1_color_location_ = glGetUniformLocation(program(), "layer1Color");
      assert(layer1_color_location_ != -1);
      layer2_color_location_ = glGetUniformLocation(program(), "layer2Color");
      assert(layer2_color_location_ != -1);
      layer_params_location_ = glGetUniformLocation(program(), "layerParams");
      assert(layer_params_location_ != -1);
    }
  }

  /// A layered mask's colors (see GetLayeredMaskFragmentCode_): the
  /// underlay (premultiplied) and the two painted layers (straight).
  void SetLayerColors(const float* underlay, const float* layer1,
                      const float* layer2) {
    assert(flags_ & SHD_LAYERED_MASK);
    assert(IsBound());
    SetVec4_(underlay_color_location_, underlay_color_, underlay);
    SetVec4_(layer1_color_location_, layer1_color_, layer1);
    SetVec4_(layer2_color_location_, layer2_color_, layer2);
  }

  /// A layered mask's settings: an opacity applied to all of it, and
  /// whether its color and mask textures are premultiplied (1.0) or
  /// straight (0.0).
  void SetLayerParams(float opacity, float tex_premultiplied,
                      float mask_premultiplied) {
    assert(flags_ & SHD_LAYERED_MASK);
    assert(IsBound());
    float vals[4]{opacity, tex_premultiplied, mask_premultiplied, 0.0f};
    SetVec4_(layer_params_location_, layer_params_, vals);
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

  /// The shadow's color, and its spread: extra blur (as mip bias) on
  /// top of the shadow's own.
  void SetShadowColor(float r, float g, float b, float spread) {
    assert(flags_ & SHD_SHADOW);
    assert(IsBound());
    if (r != shadow_r_ || g != shadow_g_ || b != shadow_b_
        || spread != shadow_spread_) {
      shadow_r_ = r;
      shadow_g_ = g;
      shadow_b_ = b;
      shadow_spread_ = spread;
      glUniform4f(shadow_color_location_, shadow_r_, shadow_g_, shadow_b_,
                  shadow_spread_);
    }
  }

  /// How strong a text-glow program's neon look is (0 = none, 1 =
  /// standard).
  void SetTextGlow(float amount) {
    assert(flags_ & SHD_TEXT_GLOW);
    assert(IsBound());
    if (amount != text_glow_) {
      text_glow_ = amount;
      glUniform1f(text_glow_location_, text_glow_);
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

  // 1.0 if the bound color texture is premultiplied-alpha, else 0.0. Selects
  // the flatness lerp target and the shadow-compositing path so premult and
  // straight-alpha textures both render correctly (see GetFragmentCode).
  void SetTexPremultiplied(float premultiplied) {
    assert((flags_ & SHD_FLATNESS) || (flags_ & SHD_SHADOW)
           || ((flags_ & SHD_MASKED) && (flags_ & SHD_MODULATE)));
    assert(IsBound());
    if (premultiplied != tex_premultiplied_) {
      tex_premultiplied_ = premultiplied;
      glUniform1f(tex_premultiplied_location_, tex_premultiplied_);
    }
  }

  // 1.0 if this is a premult-blended draw whose mask texture is NOT
  // premultiplied (a data-role mask, or a straight-alpha one from a mod),
  // else 0.0. The shader then scales the mask's color contribution by the
  // mask's alpha itself -- the factor straight blending applies for free
  // and a premultiplied mask already has baked in.
  void SetMaskStraight(float mask_straight) {
    assert((flags_ & SHD_MASKED) && (flags_ & SHD_MODULATE));
    assert(IsBound());
    if (mask_straight != mask_straight_) {
      mask_straight_ = mask_straight;
      glUniform1f(mask_straight_location_, mask_straight_);
    }
  }

  // An rgb multiplier on what the mask *adds* (its g-channel frame and
  // b-channel highlight), which the modulate color's rgb otherwise
  // doesn't reach. (1,1,1) leaves the legacy look; depictions pass their
  // brightness/color_multiply so a whole masked icon follows them.
  void SetMaskAddMult(float r, float g, float b) {
    assert((flags_ & SHD_MASKED) && (flags_ & SHD_MODULATE));
    assert(IsBound());
    if (r != mask_add_mult_[0] || g != mask_add_mult_[1]
        || b != mask_add_mult_[2]) {
      mask_add_mult_[0] = r;
      mask_add_mult_[1] = g;
      mask_add_mult_[2] = b;
      glUniform3f(mask_add_mult_location_, r, g, b);
    }
  }

  // 1.0 if this draw blends premultiplied, else 0.0. A UV2 fade then
  // scales the whole color rather than just its alpha.
  void SetPremultBlend(float premult_blend) {
    assert(flags_ & SHD_UV2_FADE);
    assert(IsBound());
    if (premult_blend != premult_blend_) {
      premult_blend_ = premult_blend;
      glUniform1f(premult_blend_location_, premult_blend_);
    }
  }

  void SetColorize2Color(float r, float g, float b, float a = 1.0f) {
    assert(flags_ & SHD_COLORIZE);
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

  void SetColorize3Color(float r, float g, float b, float a = 1.0f) {
    assert(flags_ & SHD_COLORIZE);
    assert(IsBound());
    if (r != colorize3_r_ || g != colorize3_g_ || b != colorize3_b_
        || a != colorize3_a_) {
      colorize3_r_ = r;
      colorize3_g_ = g;
      colorize3_b_ = b;
      colorize3_a_ = a;
      glUniform4f(colorize3_color_location_, colorize3_r_, colorize3_g_,
                  colorize3_b_, colorize3_a_);
    }
  }

  void SetColorizeTexture(const TextureAsset* t) {
    assert(flags_ & SHD_COLORIZE);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorizeTexUnit);
  }

  void SetMaskTexture(const TextureAsset* t) {
    assert((flags_ & SHD_MASKED) || (flags_ & SHD_LAYERED_MASK));
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kMaskTexUnit);
  }

  void SetMaskUV2Texture(const TextureAsset* t) {
    assert(flags_ & SHD_MASK_UV2);
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kMaskUV2TexUnit);
  }

 private:
  /// Upload a vec4 uniform if it differs from what we last sent.
  static void SetVec4_(GLint location, float* cached, const float* vals) {
    if (vals[0] != cached[0] || vals[1] != cached[1] || vals[2] != cached[2]
        || vals[3] != cached[3]) {
      std::copy(vals, vals + 4, cached);
      glUniform4f(location, vals[0], vals[1], vals[2], vals[3]);
    }
  }

  /// A layered mask: a picture (colorTex x color) shown over an
  /// underlay color, then two flat colors painted over that, all within
  /// a silhouette. The mask's channels, each a coverage from 0 to 1:
  ///   red: how much of the content (picture over underlay) shows.
  ///   green: layer1Color painted over that (default black: shadows).
  ///   blue: layer2Color painted over that (default white: highlights).
  ///   alpha: how much of the whole result is drawn.
  /// Layers paint over rather than multiply, so they can add coverage
  /// where the content has none: a shadow cast over a clear underlay
  /// darkens whatever is behind the draw. A layer color's alpha scales
  /// its coverage. Output is premultiplied (premult blend only).
  static auto GetLayeredMaskFragmentCode_() -> std::string {
    // clang-format off
    return
        "uniform " BA_GLSL_MEDIUMP "sampler2D colorTex;\n"
        "uniform " BA_GLSL_MEDIUMP "sampler2D maskTex;\n"
        "uniform " BA_GLSL_MEDIUMP "vec4 color;\n"
        "uniform " BA_GLSL_MEDIUMP "vec4 underlayColor;\n"
        "uniform " BA_GLSL_MEDIUMP "vec4 layer1Color;\n"
        "uniform " BA_GLSL_MEDIUMP "vec4 layer2Color;\n"
        // x: opacity; y: colorTex premultiplied; z: maskTex
        // premultiplied.
        "uniform " BA_GLSL_MEDIUMP "vec4 layerParams;\n"
        BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP "vec2 vUV;\n"
        "void main() {\n"
        "   " BA_GLSL_MEDIUMP "vec4 tex = "
            BA_GLSL_TEXTURE2D "(colorTex, vUV);\n"
        "   tex.rgb *= mix(tex.a, 1.0, layerParams.y);\n"
        "   " BA_GLSL_MEDIUMP "vec4 content = color * tex;\n"
        "   content += underlayColor * (1.0 - content.a);\n"
        "   " BA_GLSL_MEDIUMP "vec4 mask = "
            BA_GLSL_TEXTURE2D "(maskTex, vUV);\n"
        // Channels are coverages; a premultiplied mask has them
        // scaled by its alpha, so undo that.
        "   " BA_GLSL_MEDIUMP "vec3 m = mix(mask.rgb,"
            " mask.rgb / max(mask.a, 0.001), layerParams.z);\n"
        "   " BA_GLSL_MEDIUMP "vec4 l = content * m.r;\n"
        "   " BA_GLSL_MEDIUMP "float c1 = m.g * layer1Color.a;\n"
        "   l = vec4(layer1Color.rgb * c1, c1) + l * (1.0 - c1);\n"
        "   " BA_GLSL_MEDIUMP "float c2 = m.b * layer2Color.a;\n"
        "   l = vec4(layer2Color.rgb * c2, c2) + l * (1.0 - c2);\n"
        "   " BA_GLSL_FRAGCOLOR " = l * (mask.a * layerParams.x);\n"
        "}";
    // clang-format on
  }

  auto GetName(int flags) -> std::string {
    return "SimpleProgramGL texture:"
           + std::to_string((flags & SHD_TEXTURE) != 0)
           + " modulate:" + std::to_string((flags & SHD_MODULATE) != 0)
           + " colorize:" + std::to_string((flags & SHD_COLORIZE) != 0)
           + " premultiply:" + std::to_string((flags & SHD_PREMULTIPLY) != 0)
           + " shadow:" + std::to_string((flags & SHD_SHADOW) != 0)
           + " glow:" + std::to_string((flags & SHD_GLOW) != 0) + " masked:"
           + std::to_string((flags & SHD_MASKED) != 0) + " maskedUV2:"
           + std::to_string((flags & SHD_MASK_UV2) != 0) + " depthBugTest:"
           + std::to_string((flags & SHD_DEPTH_BUG_TEST) != 0)
           + " flatness:" + std::to_string((flags & SHD_FLATNESS) != 0)
           + " textGlow:" + std::to_string((flags & SHD_TEXT_GLOW) != 0)
           + " uv2Fade:" + std::to_string((flags & SHD_UV2_FADE) != 0)
           + " layeredMask:" + std::to_string((flags & SHD_LAYERED_MASK) != 0);
  }

  static auto UsesUV2(int flags) -> bool {
    return (flags & SHD_MASK_UV2) || (flags & SHD_UV2_FADE);
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR;
    if (flags & SHD_TEXTURE) {
      pflags |= PFLAG_USES_UV_ATTR;
    }
    if (UsesUV2(flags)) {
      pflags |= PFLAG_USES_UV2_ATTR;
    }
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    // clang-format off
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
    BA_GLSL_VERTEX_IN " vec4 position;\n";
    if ((flags & SHD_TEXTURE) || (flags & SHD_COLORIZE)) {
      s += BA_GLSL_VERTEX_IN " vec2 uv;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUV;\n";
    }
    if (UsesUV2(flags)) {
      s += BA_GLSL_VERTEX_IN " vec2 uv2;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUV2;\n";
    }
    if (flags & SHD_SHADOW) {
      s += BA_GLSL_VERTEX_OUT " vec2 vUVShadow;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUVShadow2;\n"
           BA_GLSL_VERTEX_OUT " vec2 vUVShadow3;\n"
           "uniform " BA_GLSL_MEDIUMP "vec4 shadowParams;\n";
    }
    s += "void main() {\n";
    if (flags & SHD_TEXTURE) {
      s += "   vUV = uv;\n";
    }
    if (UsesUV2(flags)) {
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
    if (flags & SHD_LAYERED_MASK) {
      // A shader of its own; no other flags combine with it.
      assert(flags == (SHD_TEXTURE | SHD_MODULATE | SHD_LAYERED_MASK));
      return GetLayeredMaskFragmentCode_();
    }
    // clang-format off
    std::string s;
    if (flags & SHD_TEXTURE) {
      s += "uniform " BA_GLSL_MEDIUMP "sampler2D colorTex;\n";
    }
    if ((flags & SHD_COLORIZE)) {
      s += "uniform " BA_GLSL_MEDIUMP "sampler2D colorizeTex;\n"
           "uniform " BA_GLSL_MEDIUMP "vec4 colorizeColor;\n"
           "uniform " BA_GLSL_MEDIUMP "vec4 colorize2Color;\n"
           "uniform " BA_GLSL_MEDIUMP "vec4 colorize3Color;\n";
    }
    if ((flags & SHD_TEXTURE) || (flags & SHD_COLORIZE)) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP "vec2 vUV;\n";
    }
    if (UsesUV2(flags)) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP "vec2 vUV2;\n";
    }
    if (flags & SHD_UV2_FADE) {
      s += "uniform " BA_GLSL_MEDIUMP "float premultBlend;\n";
    }
    if (flags & SHD_FLATNESS) {
      s += "uniform " BA_GLSL_MEDIUMP "float flatness;\n";
    }
    if ((flags & SHD_FLATNESS) || (flags & SHD_SHADOW)
        || ((flags & SHD_MASKED) && (flags & SHD_MODULATE))) {
      s += "uniform " BA_GLSL_MEDIUMP "float texPremultiplied;\n";
    }
    if ((flags & SHD_MASKED) && (flags & SHD_MODULATE)) {
      s += "uniform " BA_GLSL_MEDIUMP "float maskStraight;\n";
      s += "uniform " BA_GLSL_MEDIUMP "vec3 maskAddMult;\n";
    }
    if (flags & SHD_SHADOW) {
      s += BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP "vec2 vUVShadow;\n"
           BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP "vec2 vUVShadow2;\n"
           BA_GLSL_FRAG_IN " " BA_GLSL_MEDIUMP "vec2 vUVShadow3;\n"
           "uniform " BA_GLSL_MEDIUMP "vec4 shadowParams;\n"
           "uniform " BA_GLSL_MEDIUMP "vec4 shadowColor;\n";
    if (flags & SHD_TEXT_GLOW) {
      s += "uniform " BA_GLSL_MEDIUMP "float textGlow;\n";
    }
    }
    if (flags & SHD_GLOW) {
      s += "uniform " BA_GLSL_MEDIUMP "vec2 glowParams;\n";
    }
    if ((flags & SHD_MODULATE) || (!(flags & SHD_TEXTURE))) {
      s += "uniform " BA_GLSL_MEDIUMP "vec4 color;\n";
    }
    if (flags & SHD_MASKED) {
      s += "uniform " BA_GLSL_MEDIUMP "sampler2D maskTex;\n";
    }
    if (flags & SHD_MASK_UV2) {
      s += "uniform " BA_GLSL_MEDIUMP "sampler2D maskUV2Tex;\n";
    }
    s += "void main() {\n";
    if (!(flags & SHD_TEXTURE)) {
      s += "   " BA_GLSL_FRAGCOLOR " = color;\n";
    } else {
      std::string blur_arg;
      if (flags & SHD_GLOW) {
        s += "   " BA_GLSL_MEDIUMP
             "vec4 cVal = " BA_GLSL_TEXTURE2D "(colorTex, vUV, glowParams.g);\n"
             "      " BA_GLSL_FRAGCOLOR
             " = vec4(color.rgb * cVal.rgb * cVal.a * "
             "glowParams.r, 0.0)";  // we premultiply this.
        if (flags & SHD_MASK_UV2) {
          s += " * vec4(" BA_GLSL_TEXTURE2D "(maskUV2Tex, vUV2).a)";
        }
        s += ";\n";
      } else {
        if (flags & SHD_COLORIZE) {
          // TEMP TEST
          s += "   " BA_GLSL_MEDIUMP
               "vec4 colorizeVal = " BA_GLSL_TEXTURE2D "(colorizeTex, vUV);\n";
        }
        if (flags & SHD_COLORIZE) {
          s += "   " BA_GLSL_MEDIUMP "float colorizeA = colorizeVal.r;\n";
          s += "   " BA_GLSL_MEDIUMP "float colorizeB = colorizeVal.g;\n";
          s += "   " BA_GLSL_MEDIUMP "float colorizeC = colorizeVal.b;\n";
        }
        if (flags & SHD_MASKED) {
          s += "   " BA_GLSL_MEDIUMP "vec4 mask = "
                     BA_GLSL_TEXTURE2D "(maskTex, vUV);";
          if (flags & SHD_MODULATE) {
            // A mask that is not premultiplied (a data-role mask, or a
            // straight one from a mod) in a premult-blended draw needs its
            // color contribution scaled by its own alpha here: straight
            // blending used to apply that factor at blend time and a
            // premultiplied mask has it baked in. maskStraight is 0/1.
            s += "   " BA_GLSL_MEDIUMP
                 "float maskMult = mix(1.0, mask.a, maskStraight);";
          }
        }

        if (flags & SHD_MODULATE) {
          if (flags & SHD_FLATNESS) {
            // Flatness lerps the texture rgb toward 'flat white' to flatten
            // clay-textured glyphs. For straight-alpha textures that target is
            // vec3(1.0); for premultiplied textures (decision #23) it must be
            // vec3(rawTexColor.a) instead -- i.e. unpremultiply, push toward
            // white, re-premultiply, which simplifies to swapping the lerp
            // target (no divide). Otherwise transparent premult texels get
            // pushed toward white and premult-blend renders them as a glow.
            // texPremultiplied (0/1) preserves the exact legacy path for
            // straight-alpha textures (incl. modder customs).
            s += "   " BA_GLSL_MEDIUMP
                 "vec4 rawTexColor = " BA_GLSL_TEXTURE2D "(colorTex, vUV);\n"
                 "   " BA_GLSL_MEDIUMP
                 "vec3 flatTarget = mix(vec3(1.0), vec3(rawTexColor.a),"
                 " texPremultiplied);\n"
                 "   " BA_GLSL_FRAGCOLOR " = color * "
                       "vec4(mix(rawTexColor.rgb, flatTarget, flatness),"
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
          s += " * (vec4(1.0 - colorizeB) + colorize2Color * colorizeB)";
          s += " * (vec4(1.0 - colorizeC) + colorize3Color * colorizeC)";
        }
        if (flags & SHD_MASKED) {
          // The mask's g/b channels *add* frame-tint and white-highlight
          // rgb with zero alpha. Under straight blend the hardware weights
          // that rgb by fragment alpha at blend time so it fades with the
          // modulate alpha for free; under premult blend (GL_ONE) it would
          // stay full-brightness forever, so scale it by the modulate
          // color's alpha ourselves (decision #23). texPremultiplied (0/1)
          // preserves the exact legacy path for straight-alpha textures.
          if (flags & SHD_MODULATE) {
            s += " * vec4(vec3(mask.r) * maskMult, mask.a) + "
                 "vec4((vec3(mask.g) * colorizeColor.rgb + vec3(mask.b))"
                 " * maskMult * mix(1.0, color.a, texPremultiplied)"
                 " * maskAddMult, 0.0)";
          } else {
            s += " * vec4(vec3(mask.r), mask.a) + "
                 "vec4(vec3(mask.g) * colorizeColor.rgb + vec3(mask.b), 0.0)";
          }
        }
        s += ";\n";

        if (flags & SHD_UV2_FADE) {
          // Each uv2 axis runs from 0 at an outer edge (fully drawn) to
          // 1 at the inner end of the fade (gone); we ease along each
          // and multiply them, so corners where two fades meet fall off
          // along both. Premult blending scales the whole color;
          // straight blending just its alpha.
          s += "   " BA_GLSL_MEDIUMP
               "vec2 fadeAmt = smoothstep(0.0, 1.0, vUV2);\n"
               "   " BA_GLSL_MEDIUMP
               "float fade = 1.0 - fadeAmt.x * fadeAmt.y;\n"
               "   " BA_GLSL_FRAGCOLOR " *= mix(vec4(1.0, 1.0, 1.0, fade),"
               " vec4(fade), premultBlend);\n";
        }

        if (flags & SHD_TEXT_GLOW) {
          // Text glow (a neon look) of strength textGlow (0 = none, 1 =
          // standard), drawn as a single layer in place of the glyph:
          // a blurred copy of the glyph's alpha, the average of four
          // samples, one out along each diagonal by a quarter of the
          // shadow offset (shadowParams.xy) x textGlow. That offset is
          // in the text's own space, so the glow is the same width
          // relative to the text at any size (mip-bias blur is not: it
          // is roughly fixed in screen pixels).
          //  * Its alpha is the blurred alpha x (1 + textGlow)
          //    (capped at 1), so it spills past the glyph's edges.
          //  * Its color runs from the text's own to white as the
          //    blurred alpha goes from 0.7 to 0.9, so interiors go
          //    white-hot while edges keep the text color. The white
          //    scales with textGlow (full white at strength 1).
          // All three fall away with textGlow, so strength 0 would be
          // the plain glyph: no offset, alpha as is, no white.
          s += "   " BA_GLSL_MEDIUMP "vec2 glowOffs = 0.25 * textGlow *"
               " shadowParams.xy;\n"
               "   " BA_GLSL_MEDIUMP "vec2 glowOffs2 = vec2("
               "glowOffs.x, -glowOffs.y);\n"
               // Each sample is blurred (mip bias) to cover the gap to
               // its neighbors: they sit twice the offset apart, a
               // sample at bias b covers about 2^b screen pixels, so b
               // is log2 of that gap in pixels (never sharper than
               // normal). Without this the four show as separate
               // copies once the offset spans several pixels.
               "   " BA_GLSL_MEDIUMP "vec2 glowOffsPx = abs(glowOffs)"
               " / max(fwidth(vUV), vec2(0.000001));\n"
               "   " BA_GLSL_MEDIUMP "float glowBias = max(0.0, log2(2.0"
               " * max(glowOffsPx.x, glowOffsPx.y)));\n"
               "   " BA_GLSL_MEDIUMP "float glowBlur = 0.25 * ("
               BA_GLSL_TEXTURE2D "(colorTex, vUV + glowOffs, glowBias).a + "
               BA_GLSL_TEXTURE2D "(colorTex, vUV - glowOffs, glowBias).a + "
               BA_GLSL_TEXTURE2D "(colorTex, vUV + glowOffs2, glowBias).a + "
               BA_GLSL_TEXTURE2D "(colorTex, vUV - glowOffs2, glowBias).a);\n"
               "   " BA_GLSL_MEDIUMP "float glowA = min(glowBlur * (1.0 +"
               " textGlow), 1.0)"
               // Faded out toward the glyph quad's edges like shadows are,
               // so the glow never shows the quad's outline.
               " * " BA_GLSL_TEXTURE2D "(maskUV2Tex, vUV2).a;\n"
               "   " BA_GLSL_MEDIUMP "float glowWhite = min(clamp((glowBlur"
               " - 0.7) / 0.2, 0.0, 1.0) * textGlow, 1.0);\n"
               // (A premultiplied text's color arrives scaled by its
               // alpha, so its white is that alpha.)
               "   " BA_GLSL_MEDIUMP "vec3 glowRGB = mix(color.rgb,"
               " mix(vec3(1.0), vec3(color.a), texPremultiplied),"
               " glowWhite);\n"
               "   " BA_GLSL_FRAGCOLOR " = vec4(glowRGB * mix(1.0, glowA,"
               " texPremultiplied), glowA * color.a);\n";
        }

        if (flags & SHD_SHADOW) {
          s += "   " BA_GLSL_MEDIUMP
                     "float shadowA = ("
                     BA_GLSL_TEXTURE2D "(colorTex, vUVShadow, shadowColor.a).a"
                     " + " BA_GLSL_TEXTURE2D
                     "(colorTex, vUVShadow2, 1.0 + shadowColor.a).a + "
                     "" BA_GLSL_TEXTURE2D
                     "(colorTex, vUVShadow3, 2.0 + shadowColor.a).a)"
                     " * shadowParams.a";

          if (flags & SHD_MASK_UV2) {
            s += " * " BA_GLSL_TEXTURE2D "(maskUV2Tex, vUV2).a";
          }
          s += ";\n";
          // Composite the glyph over a soft drop-shadow in shadowColor
          // (black for classic shadows; a bright color with no offset
          // reads as a glow). Two cases, selected by texPremultiplied
          // (decision #23):
          //   * Straight-alpha (legacy): the running fragColor is straight
          //     color. Premultiply it, lay it over the premultiplied
          //     shadow, then un-premultiply back to straight -- straight-alpha
          //     textures use straight-alpha blending.
          //   * Premultiplied: fragColor is already premultiplied (the caller
          //     premultiplies the modulate color by its alpha for premult
          //     textures), so composite the premultiplied shadow under it and
          //     leave the result premultiplied to match the active premult
          //     blend (no premultiply, no divide).
          s += "   " BA_GLSL_MEDIUMP "vec4 shadowPremultTerm = "
               "vec4(shadowColor.rgb * shadowA, shadowA);\n";
          s += "   " BA_GLSL_MEDIUMP "vec4 shadowPremultComposite = vec4("
               BA_GLSL_FRAGCOLOR ".rgb * " BA_GLSL_FRAGCOLOR ".a, "
               BA_GLSL_FRAGCOLOR ".a) + (1.0 - " BA_GLSL_FRAGCOLOR
               ".a) * shadowPremultTerm;\n";
          s += "   " BA_GLSL_MEDIUMP
               "vec4 shadowStraight = vec4(shadowPremultComposite.rgb"
               " / max(0.001, shadowPremultComposite.a),"
               " shadowPremultComposite.a);\n";
          s += "   " BA_GLSL_MEDIUMP "vec4 shadowPremult = "
               BA_GLSL_FRAGCOLOR " + (1.0 - " BA_GLSL_FRAGCOLOR
               ".a) * shadowPremultTerm;\n";
          s += "   " BA_GLSL_FRAGCOLOR
               " = mix(shadowStraight, shadowPremult, texPremultiplied);\n";
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
  float colorize3_r_{}, colorize3_g_{}, colorize3_b_{}, colorize3_a_{};
  float shadow_offset_x_{}, shadow_offset_y_{}, shadow_blur_{},
      shadow_density_{};
  // GL zero-initializes uniforms, so black with no spread (the default)
  // needs no initial upload.
  float shadow_r_{}, shadow_g_{}, shadow_b_{}, shadow_spread_{};
  float text_glow_{};
  float glow_amount_{}, glow_blur_{};
  float flatness_{};
  float tex_premultiplied_{};
  float mask_straight_{};
  // (Matches GL's zeroed start; every masked draw sets it, so its first
  // (1,1,1) uploads.)
  float mask_add_mult_[3]{};
  float premult_blend_{};
  float underlay_color_[4]{};
  float layer1_color_[4]{};
  float layer2_color_[4]{};
  float layer_params_[4]{};
  GLint color_location_{};
  GLint colorize_color_location_{};
  GLint colorize2_color_location_{};
  GLint colorize3_color_location_{};
  GLint shadow_params_location_{};
  GLint shadow_color_location_{};
  GLint text_glow_location_{};
  GLint glow_params_location_{};
  GLint flatness_location{};
  GLint tex_premultiplied_location_{};
  GLint mask_straight_location_{};
  GLint mask_add_mult_location_{};
  GLint premult_blend_location_{};
  GLint underlay_color_location_{};
  GLint layer1_color_location_{};
  GLint layer2_color_location_{};
  GLint layer_params_location_{};
  int flags_{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SIMPLE_GL_H_
