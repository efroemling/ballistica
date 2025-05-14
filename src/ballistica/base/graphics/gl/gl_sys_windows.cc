// Released under the MIT License. See LICENSE for details.

#if BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS
#include "ballistica/base/graphics/gl/gl_sys_windows.h"

#include <string>

#include "SDL.h"
#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/shared/ballistica.h"

#pragma comment(lib, "opengl32.lib")

PFNGLGETINTERNALFORMATIVPROC glGetInternalformativ{};
PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC
glGetFramebufferAttachmentParameteriv{};
PFNGLBLENDFUNCSEPARATEPROC glBlendFuncSeparate{};

PFNGLCOMPRESSEDTEXIMAGE2DPROC glCompressedTexImage2DBA{};
PFNGLACTIVETEXTUREPROC glActiveTextureBA{};
// PFNGLCOMPRESSEDTEXIMAGE2DPROC glCompressedTexImageARB{};
// PFNGLCLIENTACTIVETEXTUREARBPROC glClientActiveTextureARB{};

PFNGLPOINTPARAMETERFVARBPROC glPointParameterfvARB{};
PFNWGLSWAPINTERVALEXTPROC wglSwapIntervalEXT{};
PFNGLCREATEPROGRAMPROC glCreateProgram{};
PFNGLCREATESHADERPROC glCreateShader{};
PFNGLSHADERSOURCEPROC glShaderSource{};
PFNGLCOMPILESHADERPROC glCompileShader{};
PFNGLLINKPROGRAMPROC glLinkProgram{};
PFNGLGETINFOLOGARBPROC glGetInfoLogARB{};
PFNGLATTACHSHADERPROC glAttachShader{};
PFNGLUSEPROGRAMOBJECTARBPROC glUseProgram{};
PFNGLGENERATEMIPMAPPROC glGenerateMipmap{};
PFNGLBINDFRAMEBUFFERPROC glBindFramebuffer{};
PFNGLBLITFRAMEBUFFERPROC glBlitFramebuffer{};
PFNGLBINDVERTEXARRAYPROC glBindVertexArray{};
PFNGLGETUNIFORMLOCATIONPROC glGetUniformLocation{};
PFNGLUNIFORM1IPROC glUniform1i{};
PFNGLUNIFORM1FPROC glUniform1f{};
PFNGLUNIFORM1FVPROC glUniform1fv{};
PFNGLUNIFORM2FPROC glUniform2f{};
PFNGLUNIFORM3FPROC glUniform3f{};
PFNGLUNIFORM4FPROC glUniform4f{};
PFNGLGENFRAMEBUFFERSPROC glGenFramebuffers{};
PFNGLGENBUFFERSPROC glGenBuffers{};
PFNGLGENVERTEXARRAYSPROC glGenVertexArrays{};
PFNGLFRAMEBUFFERTEXTURE2DPROC glFramebufferTexture2D{};
PFNGLGENRENDERBUFFERSPROC glGenRenderbuffers{};
PFNGLBINDRENDERBUFFERPROC glBindRenderbuffer{};
PFNGLBINDBUFFERPROC glBindBuffer{};
PFNGLBUFFERDATAPROC glBufferData{};
PFNGLRENDERBUFFERSTORAGEPROC glRenderbufferStorage{};
PFNGLRENDERBUFFERSTORAGEMULTISAMPLEPROC glRenderbufferStorageMultisample{};
PFNGLFRAMEBUFFERRENDERBUFFERPROC glFramebufferRenderbuffer{};
PFNGLCHECKFRAMEBUFFERSTATUSPROC glCheckFramebufferStatus{};
PFNGLDELETEFRAMEBUFFERSPROC glDeleteFramebuffers{};
PFNGLDELETERENDERBUFFERSPROC glDeleteRenderbuffers{};
PFNGLVERTEXATTRIBPOINTERPROC glVertexAttribPointer{};
PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray{};
PFNGLDISABLEVERTEXATTRIBARRAYPROC glDisableVertexAttribArray{};
PFNGLUNIFORMMATRIX4FVARBPROC glUniformMatrix4fv{};
PFNGLBINDATTRIBLOCATIONPROC glBindAttribLocation{};
PFNGLGETSHADERIVPROC glGetShaderiv{};
PFNGLGETPROGRAMIVPROC glGetProgramiv{};
PFNGLDELETESHADERPROC glDeleteShader{};
PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays{};
PFNGLDELETEBUFFERSPROC glDeleteBuffers{};
PFNGLDELETEPROGRAMPROC glDeleteProgram{};
PFNGLDETACHSHADERPROC glDetachShader{};
PFNGLGETSHADERINFOLOGPROC glGetShaderInfoLog{};
PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog{};
PFNGLGETSTRINGIPROC glGetStringi{};

namespace ballistica::base {

static auto GetGLFunc_(const char* name, bool required) -> void* {
  void* func = SDL_GL_GetProcAddress(name);
  if (!func) {
    func = SDL_GL_GetProcAddress((std::string(name) + "EXT").c_str());
  }
  if (required && func == nullptr) {
    FatalError("OpenGL function '" + std::string(name)
               + "' not found.\nAre your graphics drivers up to date?");
  }
  return func;
}

// Our variable name matches the name we're fetching from the library.
#define GET(PTRTYPE, FUNC, REQUIRED) FUNC = (PTRTYPE)GetGLFunc_(#FUNC, REQUIRED)

// Our variable name equals the library name + BA. (For symbol clashes).
#define GET2(PTRTYPE, FUNC, REQUIRED) \
  FUNC##BA = (PTRTYPE)GetGLFunc_(#FUNC, REQUIRED)

void SysGLInit(RendererGL* renderer) {
  assert(!g_sys_gl_inited);

  SDL_GL_LoadLibrary(nullptr);

  // Check overall GL version here before loading any extended functions.
  // We'd rather die with a 'Your OpenGL is too old' error rather than a
  // 'Could not load function foofDinglePlop2XZ'.
  renderer->CheckGLVersion();

  void* testval{};

  PFNGLGETINTERNALFORMATIVPROC fptr;
  fptr = (PFNGLGETINTERNALFORMATIVPROC)testval;

  // For checking msaa level support. This is only available in GL 4.2+
  // so we can survive without it.
  GET(PFNGLGETINTERNALFORMATIVPROC, glGetInternalformativ, false);

  GET(PFNGLBLENDFUNCSEPARATEPROC, glBlendFuncSeparate, true);
  GET(PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC,
      glGetFramebufferAttachmentParameteriv, true);
  GET(PFNGLGETSTRINGIPROC, glGetStringi, true);
  GET2(PFNGLACTIVETEXTUREPROC, glActiveTexture, true);
  GET(PFNWGLSWAPINTERVALEXTPROC, wglSwapIntervalEXT, true);
  GET(PFNGLPOINTPARAMETERFVARBPROC, glPointParameterfvARB, true);
  GET(PFNGLCREATEPROGRAMPROC, glCreateProgram, true);
  GET(PFNGLCREATESHADERPROC, glCreateShader, true);
  GET(PFNGLSHADERSOURCEPROC, glShaderSource, true);
  GET(PFNGLCOMPILESHADERPROC, glCompileShader, true);
  GET(PFNGLLINKPROGRAMPROC, glLinkProgram, true);
  GET(PFNGLGETINFOLOGARBPROC, glGetInfoLogARB, true);
  GET(PFNGLATTACHSHADERPROC, glAttachShader, true);
  GET(PFNGLUSEPROGRAMOBJECTARBPROC, glUseProgram, true);
  GET(PFNGLGENERATEMIPMAPPROC, glGenerateMipmap, true);
  GET(PFNGLBINDFRAMEBUFFERPROC, glBindFramebuffer, true);
  GET(PFNGLGETUNIFORMLOCATIONPROC, glGetUniformLocation, true);
  GET(PFNGLUNIFORM1IPROC, glUniform1i, true);
  GET(PFNGLUNIFORM1FPROC, glUniform1f, true);
  GET(PFNGLUNIFORM1FVPROC, glUniform1fv, true);
  GET(PFNGLUNIFORM2FPROC, glUniform2f, true);
  GET(PFNGLUNIFORM3FPROC, glUniform3f, true);
  GET(PFNGLUNIFORM4FPROC, glUniform4f, true);
  GET(PFNGLGENFRAMEBUFFERSPROC, glGenFramebuffers, true);
  GET(PFNGLGENBUFFERSPROC, glGenBuffers, true);
  GET(PFNGLFRAMEBUFFERTEXTURE2DPROC, glFramebufferTexture2D, true);
  GET(PFNGLGENRENDERBUFFERSPROC, glGenRenderbuffers, true);
  GET(PFNGLBINDRENDERBUFFERPROC, glBindRenderbuffer, true);
  GET(PFNGLBINDBUFFERPROC, glBindBuffer, true);
  GET(PFNGLBUFFERDATAPROC, glBufferData, true);
  GET(PFNGLRENDERBUFFERSTORAGEPROC, glRenderbufferStorage, true);
  GET(PFNGLFRAMEBUFFERRENDERBUFFERPROC, glFramebufferRenderbuffer, true);
  GET(PFNGLCHECKFRAMEBUFFERSTATUSPROC, glCheckFramebufferStatus, true);
  GET(PFNGLDELETEFRAMEBUFFERSPROC, glDeleteFramebuffers, true);
  GET(PFNGLDELETERENDERBUFFERSPROC, glDeleteRenderbuffers, true);
  GET(PFNGLVERTEXATTRIBPOINTERPROC, glVertexAttribPointer, true);
  GET(PFNGLENABLEVERTEXATTRIBARRAYPROC, glEnableVertexAttribArray, true);
  GET(PFNGLDISABLEVERTEXATTRIBARRAYPROC, glDisableVertexAttribArray, true);
  GET(PFNGLUNIFORMMATRIX4FVARBPROC, glUniformMatrix4fv, true);
  GET(PFNGLBINDATTRIBLOCATIONPROC, glBindAttribLocation, true);
  GET2(PFNGLCOMPRESSEDTEXIMAGE2DPROC, glCompressedTexImage2D, true);
  GET(PFNGLGETSHADERIVPROC, glGetShaderiv, true);
  GET(PFNGLGETPROGRAMIVPROC, glGetProgramiv, true);
  GET(PFNGLDELETESHADERPROC, glDeleteShader, true);
  GET(PFNGLDELETEBUFFERSPROC, glDeleteBuffers, true);
  GET(PFNGLDELETEPROGRAMPROC, glDeleteProgram, true);
  GET(PFNGLDETACHSHADERPROC, glDetachShader, true);
  GET(PFNGLGETSHADERINFOLOGPROC, glGetShaderInfoLog, true);
  GET(PFNGLGETPROGRAMINFOLOGPROC, glGetProgramInfoLog, true);
  GET(PFNGLBINDVERTEXARRAYPROC, glBindVertexArray, true);
  GET(PFNGLGENVERTEXARRAYSPROC, glGenVertexArrays, true);
  GET(PFNGLDELETEVERTEXARRAYSPROC, glDeleteVertexArrays, true);
  GET(PFNGLBLITFRAMEBUFFERPROC, glBlitFramebuffer, true);
  GET(PFNGLRENDERBUFFERSTORAGEMULTISAMPLEPROC, glRenderbufferStorageMultisample,
      true);
}
#undef GET
#undef GET2

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS
