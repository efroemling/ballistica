// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_WINDOWS_H_
#define BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_WINDOWS_H_

// System GL bits for windows.

#if BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS

// We don't *actually* need this because gl_sys.h includes it before
// it includes us, but this keeps things from erroring if we look at
// the header by itself.
#include <SDL_opengl.h>

// We run some init code to grab function ptrs/etc.
#define BA_HAS_SYS_GL_INIT

#ifndef WGL_EXT_swap_control
#define WGL_EXT_swap_control 1
typedef BOOL(WINAPI* PFNWGLSWAPINTERVALEXTPROC)(int interval);
typedef int(WINAPI* PFNWGLGETSWAPINTERVALEXTPROC)(VOID);  // NOLINT
#endif

// These seem to be defined by the SDL GL headers even though we asked them
// nicely not to (by not defining GL_GLEXT_PROTOTYPES). So we need to import
// and use it via a custom name.
#define glActiveTexture glActiveTextureBA
#define glCompressedTexImage2D glCompressedTexImage2DBA

extern PFNGLGETINTERNALFORMATIVPROC glGetInternalformativ;
extern PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC
    glGetFramebufferAttachmentParameteriv;
extern PFNGLBLENDFUNCSEPARATEPROC glBlendFuncSeparate;

// Hopefully can switch this back if SDL gets fixed.
extern PFNGLACTIVETEXTUREPROC glActiveTextureBA;
extern PFNGLCOMPRESSEDTEXIMAGE2DPROC glCompressedTexImage2DBA;
// extern PFNGLCLIENTACTIVETEXTUREARBPROC glClientActiveTextureARB;
// extern PFNGLPOINTPARAMETERFARBPROC glPointParameterfARB;

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
extern PFNGLGETSHADERIVPROC glGetShaderiv;
extern PFNGLGETPROGRAMIVPROC glGetProgramiv;
extern PFNGLDELETESHADERPROC glDeleteShader;
extern PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays;
extern PFNGLDELETEBUFFERSPROC glDeleteBuffers;
extern PFNGLDELETEPROGRAMPROC glDeleteProgram;
extern PFNGLDETACHSHADERPROC glDetachShader;
extern PFNGLGETSHADERINFOLOGPROC glGetShaderInfoLog;
extern PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog;
extern PFNGLGETSTRINGIPROC glGetStringi;

#endif  // BA_ENABLE_OPENGL && BA_PLATFORM_WINDOWS

#endif  // BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_WINDOWS_H_
