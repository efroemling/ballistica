// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_H_
#define BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_H_

// A single header to include system GL headers along with custom
// per-platform defines/function-pointers/etc.

#if BA_ENABLE_OPENGL

// On most platforms we directly link against GL and want all the functions
// defined in the header for us. On Windows we have to define/load newer
// stuff manually though, so we don't want that.
#if !BA_PLATFORM_WINDOWS
#define GL_GLEXT_PROTOTYPES
#endif

// ----------------------------- BASE GL INCLUDES ------------------------------

// On SDL builds, let SDL handle this for us.
#if BA_SDL_BUILD
#include <SDL_opengl.h>
#endif

// For XCode builds, grab Apple's framework-y headers.
#if BA_XCODE_BUILD
#if BA_OPENGL_IS_ES
#include <OpenGLES/ES3/gl.h>
#include <OpenGLES/ES3/glext.h>
#else
#include <OpenGL/gl3.h>
#include <OpenGL/gl3ext.h>
#endif
#endif

// On Android, we're currently supporting Android API 21 and newer, which
// means we can count on GL ES 3.1 libs/headers always being available. Note
// that hardware may still be limited to older versions so we need to check
// for that and set a limit in our manifest.
#if BA_PLATFORM_ANDROID
#include <GLES3/gl31.h>
#include <GLES3/gl3ext.h>
#endif

// -----------------------------------------------------------------------------

// Now mix in a bit of magic of our own...

// We may use S3TC types even on ES (Android Nvidia hardware supports them)
// but they're not currently in ES's glext.h. Define here if needed.
#ifndef GL_EXT_texture_compression_s3tc
#define GL_EXT_texture_compression_s3tc 1
#define GL_COMPRESSED_RGB_S3TC_DXT1_EXT 0x83F0
#define GL_COMPRESSED_RGBA_S3TC_DXT1_EXT 0x83F1
#define GL_COMPRESSED_RGBA_S3TC_DXT3_EXT 0x83F2
#define GL_COMPRESSED_RGBA_S3TC_DXT5_EXT 0x83F3
#endif /* GL_EXT_texture_compression_s3tc */

// Anisotropic texturing is still an extension in GL 3 and ES 3.2, so
// define its values if need be (they seem to exist in desktop glext.h
// but not es)
#ifndef GL_EXT_texture_filter_anisotropic
#define GL_EXT_texture_filter_anisotropic 1
#define GL_TEXTURE_MAX_ANISOTROPY_EXT 0x84FE
#define GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT 0x84FF
#endif /* GL_EXT_texture_filter_anisotropic */

// Desktop GL has glDepthRange() which takes a double. GL ES has
// glDepthRangef() which takes a float. Let's always accept doubles and
// down-convert where needed.
#if BA_OPENGL_IS_ES
inline void glDepthRange(double min, double max) {
  return glDepthRangef(min, max);
}
#endif

// #if BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID

// #if BA_USE_ES3_INCLUDES
// #include <GLES3/gl3.h>
// #include <GLES3/gl3ext.h>
// #elif BA_PLATFORM_IOS_TVOS
// #include <OpenGLES/ES2/gl.h>
// #include <OpenGLES/ES2/glext.h>
// #else
// #if BA_SDL_BUILD
// #include <SDL/SDL.h>  // needed for ios?...
// #include <SDL/SDL_opengles2.h>
// #else
// // FIXME: According to https://developer.android.com/ndk/guides/stable_apis
// //  we can always link against ES3.1 now that we're API 21+, so we shouldn't
// //  need our funky stubs and function lookups anymore.
// //  (though we'll still need to check for availability of 3.x features)
// #include <GLES2/gl2.h>
// #include <GLES2/gl2ext.h>
// #endif  // BA_SDL_BUILD
// #endif  // BA_USE_ES3_INCLUDES

// Looks like these few defines are currently missing on android (s3tc works
// on some nvidia hardware).
// #ifndef GL_COMPRESSED_RGB_S3TC_DXT1_EXT
// #define GL_COMPRESSED_RGB_S3TC_DXT1_EXT 0x83F0
// #endif
// #ifndef GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
// #define GL_COMPRESSED_RGBA_S3TC_DXT1_EXT 0x83F1
// #endif
// #ifndef GL_COMPRESSED_RGBA_S3TC_DXT3_EXT
// #define GL_COMPRESSED_RGBA_S3TC_DXT3_EXT 0x83F2
// #endif
// #ifndef GL_COMPRESSED_RGBA_S3TC_DXT5_EXT
// #define GL_COMPRESSED_RGBA_S3TC_DXT5_EXT 0x83F3
// #endif

// #if BA_PLATFORM_IOS_TVOS
// extern void (*glInvalidateFramebuffer)(GLenum target, GLsizei
// num_attachments,
//                                        const GLenum* attachments);
// #define glDepthRange glDepthRangef
// #define glGenVertexArrays glGenVertexArraysOES
// #define glDeleteVertexArrays glDeleteVertexArraysOES
// #define glBindVertexArray glBindVertexArrayOES
// #define glClearDepth glClearDepthf
// #endif  // BA_PLATFORM_IOS_TVOS

// #else  // BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID

// SDL Desktop builds.
// #if BA_SDL2_BUILD
// #include <SDL_opengl.h>
// #elif BA_SDL_BUILD  // BA_SDL2_BUILD
// #define NO_SDL_GLEXT
// #include <SDL_opengl.h>
// #endif  // BA_SDL2_BUILD

// #if BA_PLATFORM_MACOS
// #include <OpenGL/CGLContext.h>
// (NO LONGER APPLIES IN CORE PROFILE)
// #define glGenVertexArrays glGenVertexArraysAPPLE
// #define glDeleteVertexArrays glDeleteVertexArraysAPPLE
// #define glBindVertexArray glBindVertexArrayAPPLE
// #endif  // BA_PLATFORM_MACOS

// #endif  // BA_PLATFORM_IOS_TVOS || BA_PLATFORM_ANDROID

// #if BA_PLATFORM_ANDROID
// #include <EGL/egl.h>
// #include <android/log.h>
// #if !BA_USE_ES3_INCLUDES
// #include "ballistica/core/platform/android/android_gl3.h"
// #endif
// #define glDepthRange glDepthRangef
// #define glDiscardFramebufferEXT _glDiscardFramebufferEXT
// #ifndef GL_RGB565_OES
// #define GL_RGB565_OES 0x8D62
// #endif  // GL_RGB565_OES
// #define GL_READ_FRAMEBUFFER 0x8CA8
// #define GL_DRAW_FRAMEBUFFER 0x8CA9
// #define GL_READ_FRAMEBUFFER_BINDING 0x8CAA
// #define glClearDepth glClearDepthf
// #endif  // BA_PLATFORM_ANDROID

// #if BA_PLATFORM_ANDROID
// extern PFNGLDISCARDFRAMEBUFFEREXTPROC _glDiscardFramebufferEXT;
// #endif

#if BA_PLATFORM_WINDOWS
#include "ballistica/base/graphics/gl/gl_sys_windows.h"
#endif

// #ifndef GL_NV_texture_rectangle
// #define GL_TEXTURE_RECTANGLE_NV 0x84F5
// #define GL_TEXTURE_BINDING_RECTANGLE_NV 0x84F6
// #define GL_PROXY_TEXTURE_RECTANGLE_NV 0x84F7
// #define GL_MAX_RECTANGLE_TEXTURE_SIZE_NV 0x84F8
// #endif
// #ifndef GL_NV_texture_rectangle
// #define GL_NV_texture_rectangle 1
// #endif

// Support for GL object debug labeling.
#if BA_PLATFORM_IOS_TVOS
#define BA_GL_LABEL_OBJECT(type, obj, label) \
  glLabelObjectEXT(type, obj, 0, label)
#define BA_GL_PUSH_GROUP_MARKER(label) glPushGroupMarkerEXT(0, label)
#define BA_GL_POP_GROUP_MARKER() glPopGroupMarkerEXT()
#else
#define BA_GL_LABEL_OBJECT(type, obj, label) ((void)0)
#define BA_GL_PUSH_GROUP_MARKER(label) ((void)0)
#define BA_GL_POP_GROUP_MARKER() ((void)0)
#endif

// OpenGL ES uses precision; regular GL doesn't.
#if BA_OPENGL_IS_ES
#define BA_GLSL_LOWP "lowp "
#define BA_GLSL_MEDIUMP "mediump "
#define BA_GLSL_HIGHP "highp "
#else
#define BA_GLSL_LOWP
#define BA_GLSL_MEDIUMP
#define BA_GLSL_HIGHP
#endif  // BA_OPENGL_IS_ES

// Note: these are the same these days for GLSL regular and ES, so can get
// rid of these defines.
#if BA_OPENGL_IS_ES
#define BA_GLSL_VERTEX_IN "in"
#define BA_GLSL_VERTEX_OUT "out"
#define BA_GLSL_FRAG_IN "in"
#define BA_GLSL_FRAGCOLOR "fragColor"
#define BA_GLSL_TEXTURE2D "texture"
#define BA_GLSL_TEXTURE2DPROJ "textureProj"
#define BA_GLSL_TEXTURECUBE "texture"
#else
#define BA_GLSL_VERTEX_IN "in"
#define BA_GLSL_VERTEX_OUT "out"
#define BA_GLSL_FRAG_IN "in"
#define BA_GLSL_FRAGCOLOR "fragColor"
#define BA_GLSL_TEXTURE2D "texture"
#define BA_GLSL_TEXTURE2DPROJ "textureProj"
#define BA_GLSL_TEXTURECUBE "texture"
#endif

namespace ballistica::base {
class RendererGL;

extern bool g_sys_gl_inited;

// Called when a GL renderer is spinning up. Allows fetching/assigning any
// global function pointers or data needed for GL to function. Will be
// called only once and then g_sys_gl_inited set. A platform that defines
// this should define BA_HAS_SYS_GL_INIT; otherwise a default empty
// implementation will be defined.
void SysGLInit(RendererGL* renderer);

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_GL_SYS_H_
