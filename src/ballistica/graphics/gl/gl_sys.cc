// Released under the MIT License. See LICENSE for details.

#if BA_ENABLE_OPENGL
#include "ballistica/graphics/gl/gl_sys.h"

#include "ballistica/platform/sdl/sdl_app.h"

#if BA_OSTYPE_ANDROID
#include <EGL/egl.h>
#if !BA_USE_ES3_INCLUDES
#include "ballistica/platform/android/android_gl3.h"
#endif
#endif

#if BA_OSTYPE_WINDOWS
#pragma comment(lib, "opengl32.lib")
#pragma comment(lib, "glu32.lib")
#endif

#if BA_OSTYPE_MACOS
#include <OpenGL/CGLContext.h>
#include <OpenGL/CGLTypes.h>
#include <OpenGL/OpenGL.h>
#endif

#if BA_DEBUG_BUILD
#define DEBUG_CHECK_GL_ERROR                                        \
  {                                                                 \
    GLenum err = glGetError();                                      \
    if (err != GL_NO_ERROR)                                         \
      Log("OPENGL ERROR AT LINE " + std::to_string(__LINE__) + ": " \
          + GLErrorToString(err));                                  \
  }
#else
#define DEBUG_CHECK_GL_ERROR
#endif

#if BA_OSTYPE_ANDROID
PFNGLDISCARDFRAMEBUFFEREXTPROC _glDiscardFramebufferEXT = nullptr;
#endif

#if BA_OSTYPE_WINDOWS
PFNGLGETINTERNALFORMATIVPROC glGetInternalformativ = nullptr;
PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC
glGetFramebufferAttachmentParameteriv = nullptr;
PFNGLBLENDFUNCSEPARATEPROC glBlendFuncSeparate = nullptr;
PFNGLACTIVETEXTUREPROC glActiveTexture = nullptr;
PFNGLCLIENTACTIVETEXTUREARBPROC glClientActiveTextureARB = nullptr;
PFNGLPOINTPARAMETERFVARBPROC glPointParameterfvARB = nullptr;
PFNGLPOINTPARAMETERFARBPROC glPointParameterfARB = nullptr;
PFNWGLSWAPINTERVALEXTPROC wglSwapIntervalEXT = nullptr;
PFNGLCREATEPROGRAMPROC glCreateProgram = nullptr;
PFNGLCREATESHADERPROC glCreateShader = nullptr;
PFNGLSHADERSOURCEPROC glShaderSource = nullptr;
PFNGLCOMPILESHADERPROC glCompileShader = nullptr;
PFNGLLINKPROGRAMPROC glLinkProgram = nullptr;
PFNGLGETINFOLOGARBPROC glGetInfoLogARB = nullptr;
PFNGLATTACHSHADERPROC glAttachShader = nullptr;
PFNGLUSEPROGRAMOBJECTARBPROC glUseProgram = nullptr;
PFNGLGENERATEMIPMAPPROC glGenerateMipmap = nullptr;
PFNGLBINDFRAMEBUFFERPROC glBindFramebuffer = nullptr;
PFNGLBLITFRAMEBUFFERPROC glBlitFramebuffer = nullptr;
PFNGLBINDVERTEXARRAYPROC glBindVertexArray = nullptr;
PFNGLGETUNIFORMLOCATIONPROC glGetUniformLocation = nullptr;
PFNGLUNIFORM1IPROC glUniform1i = nullptr;
PFNGLUNIFORM1FPROC glUniform1f = nullptr;
PFNGLUNIFORM1FVPROC glUniform1fv = nullptr;
PFNGLUNIFORM2FPROC glUniform2f = nullptr;
PFNGLUNIFORM3FPROC glUniform3f = nullptr;
PFNGLUNIFORM4FPROC glUniform4f = nullptr;
PFNGLGENFRAMEBUFFERSPROC glGenFramebuffers = nullptr;
PFNGLGENBUFFERSPROC glGenBuffers = nullptr;
PFNGLGENVERTEXARRAYSPROC glGenVertexArrays = nullptr;
PFNGLFRAMEBUFFERTEXTURE2DPROC glFramebufferTexture2D = nullptr;
PFNGLGENRENDERBUFFERSPROC glGenRenderbuffers = nullptr;
PFNGLBINDRENDERBUFFERPROC glBindRenderbuffer = nullptr;
PFNGLBINDBUFFERPROC glBindBuffer = nullptr;
PFNGLBUFFERDATAPROC glBufferData = nullptr;
PFNGLRENDERBUFFERSTORAGEPROC glRenderbufferStorage = nullptr;
PFNGLRENDERBUFFERSTORAGEMULTISAMPLEPROC glRenderbufferStorageMultisample =
    nullptr;
PFNGLFRAMEBUFFERRENDERBUFFERPROC glFramebufferRenderbuffer = nullptr;
PFNGLCHECKFRAMEBUFFERSTATUSPROC glCheckFramebufferStatus = nullptr;
PFNGLDELETEFRAMEBUFFERSPROC glDeleteFramebuffers = nullptr;
PFNGLDELETERENDERBUFFERSPROC glDeleteRenderbuffers = nullptr;
PFNGLVERTEXATTRIBPOINTERPROC glVertexAttribPointer = nullptr;
PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray = nullptr;
PFNGLDISABLEVERTEXATTRIBARRAYPROC glDisableVertexAttribArray = nullptr;
PFNGLUNIFORMMATRIX4FVARBPROC glUniformMatrix4fv = nullptr;
PFNGLBINDATTRIBLOCATIONPROC glBindAttribLocation = nullptr;
PFNGLCOMPRESSEDTEXIMAGE2DPROC glCompressedTexImage2D = nullptr;
PFNGLGETSHADERIVPROC glGetShaderiv = nullptr;
PFNGLGETPROGRAMIVPROC glGetProgramiv = nullptr;
PFNGLDELETESHADERPROC glDeleteShader = nullptr;
PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays = nullptr;
PFNGLDELETEBUFFERSPROC glDeleteBuffers = nullptr;
PFNGLDELETEPROGRAMPROC glDeleteProgram = nullptr;
PFNGLDETACHSHADERPROC glDetachShader = nullptr;
PFNGLGETSHADERINFOLOGPROC glGetShaderInfoLog = nullptr;
PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog = nullptr;
#endif  // BA_OSTYPE_WINDOWS

namespace ballistica {

#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "EmptyDeclOrStmt"

GLContext::GLContext(int target_res_x, int target_res_y, bool fullscreen)
    : fullscreen_(fullscreen) {
  assert(InMainThread());
  bool need_window = true;
#if BA_RIFT_BUILD
  // on the rift build we don't need a window when running in vr mode; we just
  // use the context we're created into...
  if (IsVRMode()) {
    need_window = false;
  }
#endif  // BA_RIFT_BUILD
  if (explicit_bool(need_window)) {
#if BA_SDL2_BUILD
#if BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID
    int flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_BORDERLESS;
#else
    // Things are a bit more varied on desktop..
    uint32_t flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN
                     | SDL_WINDOW_ALLOW_HIGHDPI | SDL_WINDOW_RESIZABLE;
    if (fullscreen_) {
      flags |= SDL_WINDOW_FULLSCREEN_DESKTOP;
    }
#endif
    sdl_window_ = SDL_CreateWindow(nullptr, SDL_WINDOWPOS_UNDEFINED,
                                   SDL_WINDOWPOS_UNDEFINED, target_res_x,
                                   target_res_y, flags);
    if (!sdl_window_) {
      throw Exception("Unable to create SDL Window of size "
                      + std::to_string(target_res_x) + " by "
                      + std::to_string(target_res_y));
    }
    sdl_gl_context_ = SDL_GL_CreateContext(sdl_window_);
    if (!sdl_gl_context_) {
      throw Exception("Unable to create SDL GL Context");
    }
    SDL_SetWindowTitle(sdl_window_, "BallisticaCore");

    // Our actual drawable size could differ from the window size on retina
    // devices.
    int win_size_x, win_size_y;
    SDL_GetWindowSize(sdl_window_, &win_size_x, &win_size_y);
    SDLApp::get()->SetInitialScreenDimensions(Vector2f(
        static_cast<float>(win_size_x), static_cast<float>(win_size_y)));
#if BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID
    res_x_ = win_size_x;
    res_y_ = win_size_y;
#else
    SDL_GL_GetDrawableSize(sdl_window_, &res_x_, &res_y_);
#endif  // BA_OSTYPE_ANDROID

    // This can come through as zero in some cases (on our cardboard build at
    // least).
    if (win_size_x != 0) {
      pixel_density_ =
          static_cast<float>(res_x_) / static_cast<float>(win_size_x);
    }
#elif BA_SDL_BUILD  // BA_SDL2_BUILD

    int v_flags;
    v_flags = SDL_OPENGL;
    if (fullscreen_) {
      v_flags |= SDL_FULLSCREEN;
      // convert to the closest valid fullscreen resolution
      // (our last 1.2 build is mac and it's got hacked-in fullscreen-window
      // support; so we don't need this) getValidResolution(target_res_x,
      // target_res_y);
    } else {
      v_flags |= SDL_RESIZABLE;
    }
    surface_ = SDL_SetVideoMode(target_res_x, target_res_y, 32, v_flags);

    // if we failed, fall back to windowed mode.
    if (surface_ == nullptr) {
      throw Exception("SDL_SetVideoMode() failed for "
                      + std::to_string(target_res_x) + " by "
                      + std::to_string(target_res_y) + " fullscreen="
                      + std::to_string(static_cast<int>(fullscreen_)));
    }
    res_x_ = surface_->w;
    res_y_ = surface_->h;
    SDLApp::get()->SetInitialScreenDimensions(Vector2f(res_x_, res_y_));
    SDL_WM_SetCaption("BallisticaCore", "BallisticaCore");
#elif BA_OSTYPE_ANDROID
    // On Android the Java layer creates a GL setup before even calling us.
    // So we have nothing to do here. Hooray!
#else
    throw Exception("FIXME: Unimplemented");
#endif  // BA_SDL2_BUILD
  }

  // Fetch needed android gl stuff.
#if BA_OSTYPE_ANDROID
#define GET(PTRTYPE, FUNC, REQUIRED)                         \
  FUNC = (PTRTYPE)eglGetProcAddress(#FUNC);                  \
  if (!FUNC) FUNC = (PTRTYPE)eglGetProcAddress(#FUNC "EXT"); \
  if (REQUIRED) {                                            \
    BA_PRECONDITION(FUNC != nullptr);                        \
  }
  GET(PFNGLDISCARDFRAMEBUFFEREXTPROC, _glDiscardFramebufferEXT, false);
#endif  // BA_OSTYPE_ANDROID

  // Fetch needed windows gl stuff.
#if BA_OSTYPE_WINDOWS
#define GET(PTRTYPE, FUNC, REQUIRED)                         \
  FUNC = (PTRTYPE)wglGetProcAddress(#FUNC);                  \
  if (!FUNC) FUNC = (PTRTYPE)wglGetProcAddress(#FUNC "EXT"); \
  if (REQUIRED) {                                            \
    BA_PRECONDITION(FUNC != nullptr);                        \
  }
  GET(PFNGLGETINTERNALFORMATIVPROC, glGetInternalformativ,
      false);  // for checking msaa level support
  GET(PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC,
      glGetFramebufferAttachmentParameteriv, false);  // for checking srgb stuff
  GET(PFNGLBLENDFUNCSEPARATEPROC, glBlendFuncSeparate,
      false);  // needed for VR overlay
  GET(PFNGLACTIVETEXTUREPROC, glActiveTexture, true);
  GET(PFNGLCLIENTACTIVETEXTUREARBPROC, glClientActiveTextureARB, true);
  GET(PFNWGLSWAPINTERVALEXTPROC, wglSwapIntervalEXT, true);
  GET(PFNGLPOINTPARAMETERFVARBPROC, glPointParameterfvARB, true);
  GET(PFNGLPOINTPARAMETERFARBPROC, glPointParameterfARB, true);
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
  GET(PFNGLCOMPRESSEDTEXIMAGE2DPROC, glCompressedTexImage2D, true);
  GET(PFNGLGETSHADERIVPROC, glGetShaderiv, true);
  GET(PFNGLGETPROGRAMIVPROC, glGetProgramiv, true);
  GET(PFNGLDELETESHADERPROC, glDeleteShader, true);
  GET(PFNGLDELETEBUFFERSPROC, glDeleteBuffers, true);
  GET(PFNGLDELETEPROGRAMPROC, glDeleteProgram, true);
  GET(PFNGLDETACHSHADERPROC, glDetachShader, true);
  GET(PFNGLGETSHADERINFOLOGPROC, glGetShaderInfoLog, true);
  GET(PFNGLGETPROGRAMINFOLOGPROC, glGetProgramInfoLog, true);

  // Stuff we can live without:
  GET(PFNGLBINDVERTEXARRAYPROC, glBindVertexArray, false);
  GET(PFNGLGENVERTEXARRAYSPROC, glGenVertexArrays, false);
  GET(PFNGLDELETEVERTEXARRAYSPROC, glDeleteVertexArrays, false);
  GET(PFNGLBLITFRAMEBUFFERPROC, glBlitFramebuffer, false);
  GET(PFNGLRENDERBUFFERSTORAGEMULTISAMPLEPROC, glRenderbufferStorageMultisample,
      false);

#undef GET
#endif  // BA_OSTYPE_WINDOWS

  // So that our window comes up nice and black.
  // FIXME should just make the window's blanking color black.

#if BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID
  // Not needed here.
#else

#if BA_SDL2_BUILD
  // Gonna wait and see if if still need this.
#elif BA_SDL_BUILD
  glClearColor(0, 0, 0, 1);
  glClear(GL_COLOR_BUFFER_BIT);
  SDL_GL_SwapBuffers();
#endif  // BA_SDL2_BUILD

#endif  // IOS/ANDROID
}
#pragma clang diagnostic pop

void GLContext::SetVSync(bool enable) {
  assert(InMainThread());

#if BA_OSTYPE_MACOS
  CGLContextObj context = CGLGetCurrentContext();
  BA_PRECONDITION(context);
  GLint sync = enable;
  CGLSetParameter(context, kCGLCPSwapInterval, &sync);
#else

#endif  // BA_OSTYPE_MACOS
}

GLContext::~GLContext() {
  if (!InMainThread()) {
    Log("Error: GLContext dying in non-graphics thread");
  }
#if BA_SDL2_BUILD

#if BA_RIFT_BUILD
  // (in rift we only have a window in 2d mode)
  if (!IsVRMode()) {
    BA_PRECONDITION_LOG(sdl_window_);
  }
#else   // BA_RIFT_MODE
  BA_PRECONDITION_LOG(sdl_window_);
#endif  // BA_RIFT_BUILD

  if (sdl_window_) {
    SDL_DestroyWindow(sdl_window_);
    sdl_window_ = nullptr;
  }
#elif BA_SDL_BUILD
  BA_PRECONDITION_LOG(surface_);
  if (surface_) {
    SDL_FreeSurface(surface_);
    surface_ = nullptr;
  }
#endif
}

auto GLErrorToString(GLenum err) -> std::string {
  switch (err) {
    case GL_NO_ERROR:
      return "GL_NO_ERROR";
    case GL_INVALID_ENUM:
      return "GL_INVALID_ENUM";
    case GL_INVALID_VALUE:
      return "GL_INVALID_VALUE";
    case GL_INVALID_OPERATION:
      return "GL_INVALID_OPERATION";
    case GL_OUT_OF_MEMORY:
      return "GL_OUT_OF_MEMORY";
    case GL_INVALID_FRAMEBUFFER_OPERATION:
      return "GL_INVALID_FRAMEBUFFER_OPERATION";
    default:
      return std::to_string(err);
  }
}

}  // namespace ballistica

#endif  // BA_ENABLE_OPENGL
