// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_POST_PROCESS_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_POST_PROCESS_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"

namespace ballistica::base {

class RendererGL::ProgramPostProcessGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
    kDepthTexUnit,
    kColorSlightBlurredTexUnit,
    kColorBlurredTexUnit,
    kColorBlurredMoreTexUnit
  };

  ProgramPostProcessGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
            renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
            Object::New<FragmentShaderGL>(GetFragmentCode(flags)),
            GetName(flags), GetPFlags(flags)),
        flags_(flags),
        dof_near_min_(0),
        dof_near_max_(0),
        dof_far_min_(0),
        dof_far_max_(0),
        distort_(0.0f) {
    SetTextureUnit("colorTex", kColorTexUnit);

    if (UsesSlightBlurredTex()) {
      SetTextureUnit("colorSlightBlurredTex", kColorSlightBlurredTexUnit);
    }
    if (UsesBlurredTexture()) {
      SetTextureUnit("colorBlurredTex", kColorBlurredTexUnit);
    }
    SetTextureUnit("colorBlurredMoreTex", kColorBlurredMoreTexUnit);
    SetTextureUnit("depthTex", kDepthTexUnit);

    dof_location_ = glGetUniformLocation(program(), "dofRange");
    assert(dof_location_ != -1);

    if (flags & SHD_DISTORT) {
      distort_location_ = glGetUniformLocation(program(), "distort");
      assert(distort_location_ != -1);
    }
  }

  auto UsesSlightBlurredTex() -> bool {
    return static_cast<bool>(flags_ & SHD_EYES);
  }
  auto UsesBlurredTexture() -> bool {
    return static_cast<bool>(flags_ & (SHD_HIGHER_QUALITY | SHD_EYES));
  }
  void SetColorTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetColorSlightBlurredTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorSlightBlurredTexUnit);
  }
  void SetColorBlurredMoreTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorBlurredMoreTexUnit);
  }
  void SetColorBlurredTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kColorBlurredTexUnit);
  }
  void SetDepthTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kDepthTexUnit);
  }

  void SetDepthOfFieldRanges(float near_min, float near_max, float far_min,
                             float far_max) {
    assert(IsBound());
    if (near_min != dof_near_min_ || near_max != dof_near_max_
        || far_min != dof_far_min_ || far_max != dof_far_max_) {
      BA_DEBUG_CHECK_GL_ERROR;
      dof_near_min_ = near_min;
      dof_near_max_ = near_max;
      dof_far_min_ = far_min;
      dof_far_max_ = far_max;
      float vals[4] = {dof_near_min_, dof_near_max_, dof_far_min_,
                       dof_far_max_};
      glUniform1fv(dof_location_, 4, vals);
      BA_DEBUG_CHECK_GL_ERROR;
    }
  }

  void SetDistort(float distort) {
    assert(IsBound());
    assert(flags_ & SHD_DISTORT);
    if (distort != distort_) {
      BA_DEBUG_CHECK_GL_ERROR;
      distort_ = distort;
      glUniform1f(distort_location_, distort_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("PostProcessProgramGL");
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR;
    if (flags & SHD_DISTORT) {
      pflags |= (PFLAG_USES_NORMAL_ATTR | PFLAG_USES_MODEL_VIEW_MATRIX);
    }
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n" BA_GLSL_VERTEX_IN
        " vec4 position;\n";
    if (flags & SHD_DISTORT)
      s += BA_GLSL_VERTEX_IN " " BA_GLSL_LOWP
                             "vec3 normal;\n"
                             "uniform mat4 modelViewMatrix;\n"
                             "uniform float distort;\n";
    if (flags & SHD_EYES) {
      s += BA_GLSL_VERTEX_OUT " " BA_GLSL_HIGHP "float calcedDepth;\n";
    }

    s += BA_GLSL_VERTEX_OUT
        " " BA_GLSL_MEDIUMP
        "vec4 vScreenCoord;\n"
        "void main() {\n"
        "   gl_Position = modelViewProjectionMatrix*position;\n";
    if (flags & SHD_DISTORT) {
      s += "   float eyeDot = "
           "abs(normalize(modelViewMatrix*vec4(normal,0.0))).z;\n"
           "   vec4 posDistorted = "
           "modelViewProjectionMatrix*(position-eyeDot*distort*vec4(normal,0));"
           "\n"
           "   vScreenCoord = "
           "vec4(posDistorted.xy/posDistorted.w,posDistorted.zw);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    } else {
      s += "   vScreenCoord = "
           "vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    }
    if (flags & SHD_EYES) {
      s += "   calcedDepth = " + std::to_string(kBackingDepth3) + "+"
           + std::to_string(kBackingDepth4 - kBackingDepth3)
           + "*(0.5*(gl_Position.z/gl_Position.w)+0.5);\n";
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
        "sampler2D colorBlurredMoreTex;\n"
        "uniform " BA_GLSL_HIGHP "sampler2D depthTex;\n" BA_GLSL_FRAG_IN
        " " BA_GLSL_MEDIUMP
        "vec4 vScreenCoord;\n"
        "uniform " BA_GLSL_LOWP "float dofRange[4];\n";
    if (flags & (SHD_HIGHER_QUALITY | SHD_EYES)) {
      s += "uniform " BA_GLSL_LOWP "sampler2D colorBlurredTex;\n";
    }
    if (flags & SHD_EYES) {
      s += "uniform " BA_GLSL_LOWP
           "sampler2D colorSlightBlurredTex;\n" BA_GLSL_FRAG_IN
           " " BA_GLSL_HIGHP "float calcedDepth;\n";
    }

    s += "void main() {\n"
         "   " BA_GLSL_MEDIUMP "float depth = " BA_GLSL_TEXTURE2DPROJ
         "(depthTex,vScreenCoord).r;\n";

    bool doConditional = ((flags & SHD_CONDITIONAL) && !(flags & (SHD_EYES)));

    if (doConditional) {
      // special-case completely out of focus areas and completely in-focus
      // areas.
      s += "  if (depth > dofRange[1] && depth < dofRange[2]) {\n";
      if (flags & SHD_HIGHER_QUALITY) {
        s += "   " BA_GLSL_LOWP "vec4 color = " BA_GLSL_TEXTURE2DPROJ
             "(colorTex,vScreenCoord);\n"
             "   " BA_GLSL_LOWP "vec4 colorBlurred = " BA_GLSL_TEXTURE2DPROJ
             "(colorBlurredTex,vScreenCoord);\n"
             "   " BA_GLSL_LOWP
             "vec4 colorBlurredMore = "
             "0.4*" BA_GLSL_TEXTURE2DPROJ
             "(colorBlurredMoreTex,vScreenCoord);\n"
             "   " BA_GLSL_MEDIUMP
             "vec4 diff = colorBlurred-color;\n"
             "    diff = sign(diff) * max(vec4(0.0),abs(diff)-0.12);\n"
             "   " BA_GLSL_FRAGCOLOR
             " = (0.55*colorBlurredMore) + "
             "(0.62+colorBlurredMore)*(color-diff);\n\n";
      } else {
        s += "      " BA_GLSL_FRAGCOLOR " = " BA_GLSL_TEXTURE2DPROJ
             "(colorTex,vScreenCoord);\n";
      }
      s += "   }\n"
           "   else if (depth < dofRange[0] || depth > dofRange[3]) {\n";
      if (flags & SHD_HIGHER_QUALITY) {
        s += "   " BA_GLSL_LOWP "vec4 colorBlurred = " BA_GLSL_TEXTURE2DPROJ
             "(colorBlurredTex,vScreenCoord);\n"
             "   " BA_GLSL_LOWP
             "vec4 colorBlurredMore = "
             "0.4*" BA_GLSL_TEXTURE2DPROJ
             "(colorBlurredMoreTex,vScreenCoord);\n"
             "   " BA_GLSL_FRAGCOLOR
             " = (0.55*colorBlurredMore) + "
             "(0.62+colorBlurredMore)*colorBlurred;\n\n";
      } else {
        s += "      " BA_GLSL_FRAGCOLOR
             " = "
             "" BA_GLSL_TEXTURE2DPROJ "(colorBlurredMoreTex,vScreenCoord);\n";
      }
      s += "   }\n"
           "   else{\n";
    }

    // Transition areas.
    s += "   " BA_GLSL_LOWP "vec4 color = " BA_GLSL_TEXTURE2DPROJ
         "(colorTex,vScreenCoord);\n";
    if (flags & SHD_EYES)
      s += "   " BA_GLSL_LOWP
           "vec4 colorSlightBlurred = "
           "" BA_GLSL_TEXTURE2DPROJ "(colorSlightBlurredTex,vScreenCoord);\n";

// FIXME: Should make proper blur work in VR (perhaps just pass a uniform?
// FIXME2: This will break 2D mode on the VR build.
// #if BA_VR_BUILD
// #define BLURSCALE "0.3 * "
// #else
#define BLURSCALE
    // #endif

    if (flags & (SHD_HIGHER_QUALITY | SHD_EYES)) {
      s += "   " BA_GLSL_LOWP "vec4 colorBlurred = " BA_GLSL_TEXTURE2DPROJ
           "(colorBlurredTex,vScreenCoord);\n"
           "   " BA_GLSL_LOWP
           "vec4 colorBlurredMore = "
           "0.4*" BA_GLSL_TEXTURE2DPROJ
           "(colorBlurredMoreTex,vScreenCoord);\n"
           "   " BA_GLSL_LOWP "float blur = " BLURSCALE
           " (smoothstep(dofRange[2],dofRange[3],depth)\n"
           "                      +  1.0 - "
           "smoothstep(dofRange[0],dofRange[1],depth));\n"
           "   " BA_GLSL_MEDIUMP
           "vec4 diff = colorBlurred-color;\n"
           "    diff = sign(diff) * max(vec4(0.0),abs(diff)-0.12);\n"
           "   " BA_GLSL_FRAGCOLOR
           " = (0.55*colorBlurredMore) + "
           "(0.62+colorBlurredMore)*mix(color-diff,colorBlurred,blur);\n\n";
    } else {
      s += "   " BA_GLSL_LOWP
           "vec4 colorBlurredMore = "
           "" BA_GLSL_TEXTURE2DPROJ
           "(colorBlurredMoreTex,vScreenCoord);\n"
           "   " BA_GLSL_LOWP "float blur = " BLURSCALE
           " (smoothstep(dofRange[2],dofRange[3],depth)\n"
           "                      +  1.0 - "
           "smoothstep(dofRange[0],dofRange[1],depth));\n"
           "   " BA_GLSL_FRAGCOLOR " = mix(color,colorBlurredMore,blur);\n\n";
    }

#undef BLURSCALE

    if (flags & SHD_EYES) {
      s += "   " BA_GLSL_MEDIUMP "vec4 diffEye = colorBlurred-color;\n";
      s += "    diffEye = sign(diffEye) * max(vec4(0.0),abs(diffEye)-0.06);\n";
      s += "   " BA_GLSL_LOWP
           "vec4 baseColorEye = "
           "mix(color-10.0*(diffEye),colorSlightBlurred,0.83);\n";
      s += "   " BA_GLSL_LOWP
           "vec4 eyeColor = (0.55*colorBlurredMore) + "
           "(0.62+colorBlurredMore)*mix(baseColorEye,colorBlurred,blur);\n\n";
      s += "   " BA_GLSL_LOWP
           "float dBlend = smoothstep(-0.0004,-0.0001,depth-calcedDepth);\n"
           "   " BA_GLSL_FRAGCOLOR " = mix(" BA_GLSL_FRAGCOLOR
           ",eyeColor,dBlend);\n";
    }
    if (doConditional) {
      s += "   }\n";
    }

    // Demonstrates MSAA striation issue:
    // s += "   gl_FragColor =
    // mix(gl_FragColor,vec4(vec3(14.0*(depth-0.76)),1),0.999);\n";
    // s += "   gl_FragColor =
    // vec4(vec3(14.0*(" BA_GLSL_TEXTURE2DPROJ
    // "(depthTex,vScreenCoord).r-0.76)),1);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  int flags_;
  float dof_near_min_;
  float dof_near_max_;
  float dof_far_min_;
  float dof_far_max_;
  GLint dof_location_;
  float distort_;
  GLint distort_location_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_POST_PROCESS_GL_H_
