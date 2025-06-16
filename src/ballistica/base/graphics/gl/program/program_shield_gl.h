// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SHIELD_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SHIELD_GL_H_

#if BA_ENABLE_OPENGL

#include <string>

#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"

namespace ballistica::base {

class RendererGL::ProgramShieldGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kDepthTexUnit,
  };

  ProgramShieldGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
            renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
            Object::New<FragmentShaderGL>(GetFragmentCode(flags)),
            GetName(flags), GetPFlags(flags)),
        flags_(flags) {
    SetTextureUnit("depthTex", kDepthTexUnit);
  }
  void SetDepthTexture(GLuint t) {
    renderer()->BindTexture_(GL_TEXTURE_2D, t, kDepthTexUnit);
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("ShieldProgramGL");
  }

  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR;
    return pflags;
  }

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n" BA_GLSL_VERTEX_IN
        " vec4 position;\n" BA_GLSL_VERTEX_OUT " " BA_GLSL_HIGHP
        "vec4 vScreenCoord;\n"
        "void main() {\n"
        "   gl_Position = modelViewProjectionMatrix * position;\n"
        "   vScreenCoord = vec4(gl_Position.xy / gl_Position.w,"
        " gl_Position.zw);\n"
        "   vScreenCoord.xy += vec2(1.0);\n"
        "   vScreenCoord.xy *= vec2(0.5 * vScreenCoord.w);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " BA_GLSL_HIGHP "sampler2D depthTex;\n" BA_GLSL_FRAG_IN
        " " BA_GLSL_HIGHP
        "vec4 vScreenCoord;\n"
        "void main() {\n"
        "    " BA_GLSL_HIGHP "float depth = " BA_GLSL_TEXTURE2DPROJ
        "(depthTex, vScreenCoord).r;\n";

    // Work around Adreno bug where depth is returned as 0..1 instead of
    // glDepthRange().
    if (GetFunkyDepthIssue_()) {
      s += "    depth = " + std::to_string(kBackingDepth3) + " + depth * ("
           + std::to_string(kBackingDepth4) + "-"
           + std::to_string(kBackingDepth3) + ");\n";
    }
    // s+= "    depth =
    // "+std::to_string(kBackingDepth3)+"0.15+depth*(0.9-0.15);\n"; "    depth
    // *=
    // 0.936;\n" "    depth = 1.0/(65535.0*((1.0/depth)/16777216.0));\n" " depth
    //= 1.0/((1.0/depth)+0.08);\n" "    depth += 0.1f;\n"
    s += "    " BA_GLSL_HIGHP
         "float d = abs(depth - gl_FragCoord.z);\n"
         "    d = 1.0 - smoothstep(0.0, 0.0006, d);\n"
         "    d = 0.2 * smoothstep(0.96, 1.0, d)"
         " + 0.2 * d + 0.4 * d * d * d;\n";

    // Some mali chips seem to have no high precision and thus this looks
    // terrible; in those cases lets done down the intersection effect
    // significantly
    // if (GetDrawsShieldsFunny_()) {
    //   s += "    " BA_GLSL_FRAGCOLOR " = vec4(d*0.13,d*0.1,d,0);\n";
    // } else {
    s += "    " BA_GLSL_FRAGCOLOR " = vec4(d*0.5, d*0.4, d, 0);\n";
    // }
    s += "}";

    // This shows msaa depth error on bridgit.
    //"    " BA_GLSL_FRAGCOLOR " =
    // vec4(smoothstep(0.73,0.77,depth),0.0,0.0,0.5);\n"

    // "    d = 1.0 - smoothstep(0.0,0.0006,d);\n"
    // "    d = 0.2*smoothstep(0.96,1.0,d)+0.2*d+0.4*d*d*d;\n"
    //"    if (d < 0.01) " BA_GLSL_FRAGCOLOR " = vec4(0.0,1.0,0.0,0.5);\n"

    //"    " BA_GLSL_FRAGCOLOR " =
    // vec4(vec3(10.0*abs(depth-gl_FragCoord.z)),1);\n"
    // "    " BA_GLSL_FRAGCOLOR " =
    // vec4(0,10.0*abs(depth-gl_FragCoord.z),0,0.1);\n" "    if (depth <
    // gl_FragCoord.z) " BA_GLSL_FRAGCOLOR " =
    // vec4(1.0-10.0*(gl_FragCoord.z-depth),0,0,1);\n" "    else "
    // BA_GLSL_FRAGCOLOR " = vec4(0,1.0-10.0*(depth-gl_FragCoord.z),0,1);\n"
    //"    " BA_GLSL_FRAGCOLOR " = vec4(vec3(depth),1);\n"

    if (flags & SHD_DEBUG_PRINT)
      g_core->logging->Log(
          LogName::kBaGraphics, LogLevel::kInfo,
          "\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  int flags_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_PROGRAM_PROGRAM_SHIELD_GL_H_
