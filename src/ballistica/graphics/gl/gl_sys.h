// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_GL_GL_SYS_H_
#define BALLISTICA_GRAPHICS_GL_GL_SYS_H_

#if BA_ENABLE_OPENGL

#if !BA_OSTYPE_WINDOWS
#define GL_GLEXT_PROTOTYPES
#endif

#include <string>

#if BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID

#if BA_USE_ES3_INCLUDES
#include <GLES3/gl3.h>
#include <GLES3/gl3ext.h>
#else
#if BA_SDL_BUILD
#include <SDL/SDL.h>  // needed for ios?...
#include <SDL/SDL_opengles2.h>
#else
// FIXME: According to https://developer.android.com/ndk/guides/stable_apis
//  we can always link against ES3.1 now that we're API 21+, so we shouldn't
//  need our funky stubs and function lookups anymore.
//  (though we'll still need to check for availability of 3.x features)
#include <GLES2/gl2.h>
#include <GLES2/gl2ext.h>
#endif  // BA_SDL_BUILD
#endif  // BA_USE_ES3_INCLUDES

// looks like these few defines are currently missing on android
// (s3tc works on some nvidia hardware)
#ifndef GL_COMPRESSED_RGB_S3TC_DXT1_EXT
#define GL_COMPRESSED_RGB_S3TC_DXT1_EXT 0x83F0
#endif
#ifndef GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
#define GL_COMPRESSED_RGBA_S3TC_DXT1_EXT 0x83F1
#endif
#ifndef GL_COMPRESSED_RGBA_S3TC_DXT3_EXT
#define GL_COMPRESSED_RGBA_S3TC_DXT3_EXT 0x83F2
#endif
#ifndef GL_COMPRESSED_RGBA_S3TC_DXT5_EXT
#define GL_COMPRESSED_RGBA_S3TC_DXT5_EXT 0x83F3
#endif

#else  // BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID

#if BA_SDL2_BUILD
#include <SDL_opengl.h>
#elif BA_SDL_BUILD  // BA_SDL2_BUILD
#define NO_SDL_GLEXT
#include <SDL_opengl.h>
#endif  // BA_SDL2_BUILD

#if BA_OSTYPE_MACOS
#include <OpenGL/glext.h>
#endif  // BA_OSTYPE_MACOS

#endif  // BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID

#include "ballistica/core/object.h"
#include "ballistica/platform/min_sdl.h"

#if BA_OSTYPE_ANDROID
extern PFNGLDISCARDFRAMEBUFFEREXTPROC _glDiscardFramebufferEXT;
#endif

#if BA_OSTYPE_WINDOWS
#ifndef WGL_EXT_swap_control
#define WGL_EXT_swap_control 1
typedef BOOL(WINAPI* PFNWGLSWAPINTERVALEXTPROC)(int interval);
typedef int(WINAPI* PFNWGLGETSWAPINTERVALEXTPROC)(VOID);  // NOLINT
#endif  // WGL_EXT_swap_control
extern PFNGLGETINTERNALFORMATIVPROC glGetInternalformativ;
extern PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC
    glGetFramebufferAttachmentParameteriv;
extern PFNGLBLENDFUNCSEPARATEPROC glBlendFuncSeparate;
extern PFNGLACTIVETEXTUREPROC glActiveTexture;
extern PFNGLCLIENTACTIVETEXTUREARBPROC glClientActiveTextureARB;
extern PFNGLPOINTPARAMETERFARBPROC glPointParameterfARB;
extern PFNGLPOINTPARAMETERFVARBPROC glPointParameterfvARB;
extern PFNWGLSWAPINTERVALEXTPROC wglSwapIntervalEXT;
extern PFNGLCREATEPROGRAMPROC glCreateProgram;
extern PFNGLCREATESHADERPROC glCreateShader;
extern PFNGLSHADERSOURCEPROC glShaderSource;
extern PFNGLCOMPILESHADERPROC glCompileShader;
extern PFNGLLINKPROGRAMPROC glLinkProgram;
extern PFNGLGETINFOLOGARBPROC glGetInfoLogARB;
extern PFNGLATTACHSHADERPROC glAttachShader;
extern PFNGLUSEPROGRAMOBJECTARBPROC glUseProgram;
extern PFNGLGENERATEMIPMAPPROC glGenerateMipmap;
extern PFNGLBINDFRAMEBUFFERPROC glBindFramebuffer;
extern PFNGLBLITFRAMEBUFFERPROC glBlitFramebuffer;
extern PFNGLBINDVERTEXARRAYPROC glBindVertexArray;
extern PFNGLGETUNIFORMLOCATIONPROC glGetUniformLocation;
extern PFNGLUNIFORM1IPROC glUniform1i;
extern PFNGLUNIFORM1FPROC glUniform1f;
extern PFNGLUNIFORM1FVPROC glUniform1fv;
extern PFNGLUNIFORM2FPROC glUniform2f;
extern PFNGLUNIFORM3FPROC glUniform3f;
extern PFNGLUNIFORM4FPROC glUniform4f;
extern PFNGLGENFRAMEBUFFERSPROC glGenFramebuffers;
extern PFNGLGENBUFFERSPROC glGenBuffers;
extern PFNGLGENVERTEXARRAYSPROC glGenVertexArrays;
extern PFNGLFRAMEBUFFERTEXTURE2DPROC glFramebufferTexture2D;
extern PFNGLGENRENDERBUFFERSPROC glGenRenderbuffers;
extern PFNGLBINDRENDERBUFFERPROC glBindRenderbuffer;
extern PFNGLBINDBUFFERPROC glBindBuffer;
extern PFNGLBUFFERDATAPROC glBufferData;
extern PFNGLRENDERBUFFERSTORAGEPROC glRenderbufferStorage;
extern PFNGLRENDERBUFFERSTORAGEMULTISAMPLEPROC glRenderbufferStorageMultisample;
extern PFNGLFRAMEBUFFERRENDERBUFFERPROC glFramebufferRenderbuffer;
extern PFNGLCHECKFRAMEBUFFERSTATUSPROC glCheckFramebufferStatus;
extern PFNGLDELETEFRAMEBUFFERSPROC glDeleteFramebuffers;
extern PFNGLDELETERENDERBUFFERSPROC glDeleteRenderbuffers;
extern PFNGLVERTEXATTRIBPOINTERPROC glVertexAttribPointer;
extern PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray;
extern PFNGLDISABLEVERTEXATTRIBARRAYPROC glDisableVertexAttribArray;
extern PFNGLUNIFORMMATRIX4FVARBPROC glUniformMatrix4fv;
extern PFNGLBINDATTRIBLOCATIONPROC glBindAttribLocation;
extern PFNGLCOMPRESSEDTEXIMAGE2DPROC glCompressedTexImage2D;
extern PFNGLGETSHADERIVPROC glGetShaderiv;
extern PFNGLGETPROGRAMIVPROC glGetProgramiv;
extern PFNGLDELETESHADERPROC glDeleteShader;
extern PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays;
extern PFNGLDELETEBUFFERSPROC glDeleteBuffers;
extern PFNGLDELETEPROGRAMPROC glDeleteProgram;
extern PFNGLDETACHSHADERPROC glDetachShader;
extern PFNGLGETSHADERINFOLOGPROC glGetShaderInfoLog;
extern PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog;
#endif  // BA_OSTYPE_WINDOWS

#ifndef GL_NV_texture_rectangle
#define GL_TEXTURE_RECTANGLE_NV 0x84F5
#define GL_TEXTURE_BINDING_RECTANGLE_NV 0x84F6
#define GL_PROXY_TEXTURE_RECTANGLE_NV 0x84F7
#define GL_MAX_RECTANGLE_TEXTURE_SIZE_NV 0x84F8
#endif
#ifndef GL_NV_texture_rectangle
#define GL_NV_texture_rectangle 1
#endif

// Support for gl object debug labeling.
#if BA_OSTYPE_IOS_TVOS
#define GL_LABEL_OBJECT(type, obj, label) glLabelObjectEXT(type, obj, 0, label)
#define GL_PUSH_GROUP_MARKER(label) glPushGroupMarkerEXT(0, label)
#define GL_POP_GROUP_MARKER() glPopGroupMarkerEXT()
#else
#define GL_LABEL_OBJECT(type, obj, label) ((void)0)
#define GL_PUSH_GROUP_MARKER(label) ((void)0)
#define GL_POP_GROUP_MARKER() ((void)0)
#endif

namespace ballistica {

auto GLErrorToString(GLenum err) -> std::string;

// Container for OpenGL rendering context data.
class GLContext {
 public:
  GLContext(int target_res_x, int target_res_y, bool fullScreen);
  ~GLContext();
  auto res_x() const -> int { return res_x_; }
  auto res_y() const -> int { return res_y_; }
  auto pixel_density() const -> float { return pixel_density_; }
  void SetVSync(bool enable);

  // Currently no surface/window in this case.
#if BA_SDL2_BUILD
  auto sdl_window() const -> SDL_Window* {
    assert(sdl_window_);
    return sdl_window_;
  }
#elif BA_SDL_BUILD  // BA_SDL2_BUILD
  SDL_Surface* sdl_screen_surface() const {
    assert(surface_);
    return surface_;
  }
#endif  // BA_SDL2_BUILD

 private:
#if BA_SDL2_BUILD
  SDL_Window* sdl_window_{};
  SDL_GLContext sdl_gl_context_{};
#endif  // BA_SDL2_BUILD
  bool fullscreen_{};
  int res_x_{};
  int res_y_{};
  float pixel_density_{1.0f};
#if BA_SDL_BUILD && !BA_SDL2_BUILD
  SDL_Surface* surface_{};
#endif
};  // GLContext

}  // namespace ballistica

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_GRAPHICS_GL_GL_SYS_H_
