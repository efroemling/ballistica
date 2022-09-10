// Released under the MIT License. See LICENSE for details.

#if BA_ENABLE_OPENGL
#include "ballistica/graphics/gl/renderer_gl.h"

#include "ballistica/assets/data/texture_preload_data.h"
#include "ballistica/assets/data/texture_renderer_data.h"
#include "ballistica/graphics/component/special_component.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/graphics/mesh/mesh_renderer_data.h"

#if BA_OSTYPE_IOS_TVOS
#include "ballistica/platform/apple/apple_utils.h"
#endif

#define MSAA_ERROR_TEST 0

#if BA_OSTYPE_ANDROID
#include <EGL/egl.h>
#include <android/log.h>
#if !BA_USE_ES3_INCLUDES
#include "ballistica/platform/android/android_gl3.h"
#endif
#include "ballistica/ui/ui.h"
#define glDepthRange glDepthRangef
#define glDiscardFramebufferEXT _glDiscardFramebufferEXT
#ifndef GL_RGB565_OES
#define GL_RGB565_OES 0x8D62
#endif  // GL_RGB565_OES
#define GL_READ_FRAMEBUFFER 0x8CA8
#define GL_DRAW_FRAMEBUFFER 0x8CA9
#define GL_READ_FRAMEBUFFER_BINDING 0x8CAA
#define glClearDepth glClearDepthf
#endif  // BA_OSTYPE_ANDROID

#if BA_OSTYPE_MACOS
#include <OpenGL/CGLContext.h>
#define glGenVertexArrays glGenVertexArraysAPPLE
#define glDeleteVertexArrays glDeleteVertexArraysAPPLE
#define glBindVertexArray glBindVertexArrayAPPLE
#endif  // BA_OSTYPE_MACOS

#if BA_OSTYPE_IOS_TVOS
void (*glInvalidateFramebuffer)(GLenum target, GLsizei num_attachments,
                                const GLenum* attachments) = nullptr;
#define glDepthRange glDepthRangef
#define glGenVertexArrays glGenVertexArraysOES
#define glDeleteVertexArrays glDeleteVertexArraysOES
#define glBindVertexArray glBindVertexArrayOES
#define glClearDepth glClearDepthf
#endif  // BA_OSTYPE_IOS_TVOS

// Turn this off to see how much blend overdraw is occurring.
#define ENABLE_BLEND 1

// Support legacy drawing purely for debugging (should migrate this to
// post-fixed pipeline).
#if BA_OSTYPE_MACOS
#define ENABLE_DEBUG_DRAWING 1
#else
#define ENABLE_DEBUG_DRAWING 0
#endif

#ifndef GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG
#define GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG 0x8C02
#endif
#ifndef GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG
#define GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG 0x8C03
#endif

#ifndef GL_ETC1_RGB8_OES
#define GL_ETC1_RGB8_OES 0x8D64
#endif

#ifndef GL_COMPRESSED_RGB8_ETC2
#define GL_COMPRESSED_RGB8_ETC2 0x9274
#endif
#ifndef GL_COMPRESSED_RGBA8_ETC2_EAC
#define GL_COMPRESSED_RGBA8_ETC2_EAC 0x9278
#endif

#define CHECK_GL_ERROR _check_gl_error(__LINE__)

// Handy to check gl stuff on opt builds.
#define FORCE_CHECK_GL_ERRORS 0

#if BA_DEBUG_BUILD || FORCE_CHECK_GL_ERRORS
#define DEBUG_CHECK_GL_ERROR _check_gl_error(__LINE__)
#else
#define DEBUG_CHECK_GL_ERROR ((void)0)
#endif

// OpenGL ES uses precision.. regular GL doesn't
#if (BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID)
#define LOWP "lowp "
#define MEDIUMP "mediump "
#define HIGHP "highp "
#else
#define LOWP
#define MEDIUMP
#define HIGHP
#endif  // (BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID)

// FIXME: Should make proper blur work in VR (perhaps just pass a uniform?
#if BA_VR_BUILD
#define BLURSCALE "0.3 * "
#else
#define BLURSCALE
#endif

namespace ballistica {

// Lots of signed bitwise stuff happening in there; should tidy it up.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "bugprone-macro-parentheses"

bool RendererGL::funky_depth_issue_set_{};
bool RendererGL::funky_depth_issue_{};
bool RendererGL::draws_shields_funny_{};
bool RendererGL::draws_shields_funny_set_{};

GLint g_combined_texture_image_unit_count{};
bool g_anisotropic_support{};
bool g_vao_support{};
float g_max_anisotropy{};
bool g_discard_framebuffer_support{};
bool g_invalidate_framebuffer_support{};
bool g_blit_framebuffer_support{};
bool g_framebuffer_multisample_support{};
bool g_running_es3{};
bool g_seamless_cube_maps{};
int g_msaa_max_samples_rgb565{};
int g_msaa_max_samples_rgb8{};

#if BA_OSTYPE_ANDROID
bool RendererGL::is_speedy_android_device_{};
bool RendererGL::is_extra_speedy_android_device_{};
#endif  // BA_OSTYPE_ANDROID

static void _check_gl_error(int line) {
  GLenum err = glGetError();
  if (err != GL_NO_ERROR) {
    const char* version = (const char*)glGetString(GL_VERSION);
    const char* vendor = (const char*)glGetString(GL_VENDOR);
    const char* renderer = (const char*)glGetString(GL_RENDERER);
    Log("Error: OpenGL Error at line " + std::to_string(line) + ": "
        + GLErrorToString(err) + "\nrenderer: " + renderer
        + "\nvendor: " + vendor + "\nversion: " + version
        + "\ntime: " + std::to_string(GetRealTime()));
  }
}

// Flags affecting shader creation.
enum ShaderFlag {
  SHD_REFLECTION = 1,
  SHD_TEXTURE = 1 << 1,
  SHD_MODULATE = 1 << 2,
  SHD_COLORIZE = 1 << 3,
  SHD_LIGHT_SHADOW = 1 << 4,
  SHD_WORLD_SPACE_PTS = 1 << 5,
  SHD_DEBUG_PRINT = 1 << 6,
  SHD_ADD = 1 << 7,
  SHD_OBJ_TRANSPARENT = 1 << 8,
  SHD_COLOR = 1 << 9,
  SHD_EXP2 = 1 << 10,
  SHD_CAMERA_ALIGNED = 1 << 11,
  SHD_DISTORT = 1 << 12,
  SHD_PREMULTIPLY = 1 << 13,
  SHD_OVERLAY = 1 << 14,
  SHD_EYES = 1 << 15,
  SHD_COLORIZE2 = 1 << 16,
  SHD_HIGHER_QUALITY = 1 << 17,
  SHD_SHADOW = 1 << 18,
  SHD_GLOW = 1 << 19,
  SHD_MASKED = 1 << 20,
  SHD_MASK_UV2 = 1 << 21,
  SHD_CONDITIONAL = 1 << 22,
  SHD_FLATNESS = 1 << 23,
  SHD_DEPTH_BUG_TEST = 1 << 24
};

// Flags used internally by shaders.
enum ShaderPrivateFlags {
  PFLAG_USES_POSITION_ATTR = 1,
  PFLAG_USES_UV_ATTR = 1 << 1,
  PFLAG_USES_NORMAL_ATTR = 1 << 2,
  PFLAG_USES_MODEL_WORLD_MATRIX = 1 << 3,
  PFLAG_USES_CAM_POS = 1 << 4,
  PFLAG_USES_SHADOW_PROJECTION_MATRIX = 1 << 5,
  PFLAG_WORLD_SPACE_PTS = 1 << 6,
  PFLAG_USES_ERODE_ATTR = 1 << 7,
  PFLAG_USES_COLOR_ATTR = 1 << 8,
  PFLAG_USES_SIZE_ATTR = 1 << 9,
  PFLAG_USES_DIFFUSE_ATTR = 1 << 10,
  PFLAG_USES_CAM_ORIENT_MATRIX = 1 << 11,
  PFLAG_USES_MODEL_VIEW_MATRIX = 1 << 12,
  PFLAG_USES_UV2_ATTR = 1 << 13
};

// Look for a gl extension prefixed by "GL_ARB", "GL_EXT", etc
// returns true if found.
static auto CheckGLExtension(const char* exts, const char* ext) -> bool {
  char b[128];
  snprintf(b, sizeof(b), "OES_%s", ext);
  if (strstr(exts, b)) return true;
  snprintf(b, sizeof(b), "GL_ARB_%s", ext);
  if (strstr(exts, b)) return true;
  snprintf(b, sizeof(b), "GL_APPLE_%s", ext);
  if (strstr(exts, b)) return true;
  snprintf(b, sizeof(b), "GL_EXT_%s", ext);
  if (strstr(exts, b)) return true;
  snprintf(b, sizeof(b), "GL_NV_%s", ext);
  if (strstr(exts, b)) return true;
  snprintf(b, sizeof(b), "GL_SGIS_%s", ext);
  if (strstr(exts, b)) return true;
  snprintf(b, sizeof(b), "GL_IMG_%s", ext);
  return strstr(exts, b) != nullptr;
}

void RendererGL::CheckGLExtensions() {
  DEBUG_CHECK_GL_ERROR;
  assert(InGraphicsThread());
  // const char *version_str = (const char*)glGetString(GL_VERSION);

  const char* ex = (const char*)glGetString(GL_EXTENSIONS);
  assert(ex);
  // Log(ex);

  // Log(string("GL VERSION: ")+version_str);

  draws_shields_funny_set_ = true;

  // const char *renderer = (const char*)glGetString(GL_RENDERER);
  // const char *vendor = (const char*)glGetString(GL_VENDOR);
  // const char *version_str = (const char*)glGetString(GL_VERSION);
  // printf("RENDERER %s\nVENDOR %s\nVERSION %s\n",renderer,vendor,version_str);

  // on android, look at the GL version and try to get gl3 funcs to determine if
  // we're running ES3 or not
#if BA_OSTYPE_ANDROID

  const char* renderer = (const char*)glGetString(GL_RENDERER);
  const char* vendor = (const char*)glGetString(GL_VENDOR);
  const char* version_str = (const char*)glGetString(GL_VERSION);
  // Log(string("VER ")+version_str);

  bool have_es3;

#if BA_USE_ES3_INCLUDES
  have_es3 = true;
#else
  have_es3 = (strstr(version_str, "OpenGL ES 3.") && gl3stubInit());
#endif

  // if we require ES3
  if (have_es3) {
    g_running_es3 = true;
    Log(std::string("Using OpenGL ES 3 (vendor: ") + vendor
            + ", renderer: " + renderer + ", version: " + version_str + ")",
        false, false);

  } else {
#if !BA_USE_ES3_INCLUDES
    g_running_es3 = false;
    Log(std::string("USING OPENGL ES2 (vendor: ") + vendor
            + ", renderer: " + renderer + ", version: " + version_str + ")",
        false, false);

    // Can still support some stuff like framebuffer-blit with es2 extensions.
    assert(glBlitFramebuffer == nullptr || !first_extension_check_);
    glBlitFramebuffer =
        (decltype(glBlitFramebuffer))eglGetProcAddress("glBlitFramebufferNV");
    assert(glRenderbufferStorageMultisample == nullptr
           || !first_extension_check_);
    glRenderbufferStorageMultisample =
        (decltype(glRenderbufferStorageMultisample))eglGetProcAddress(
            "glRenderbufferStorageMultisampleNV");

    assert(glGenVertexArrays == nullptr || !first_extension_check_);
    glGenVertexArrays =
        (decltype(glGenVertexArrays))eglGetProcAddress("glGenVertexArraysOES");
    assert(glDeleteVertexArrays == nullptr || !first_extension_check_);
    glDeleteVertexArrays = (decltype(glDeleteVertexArrays))eglGetProcAddress(
        "glDeleteVertexArraysOES");
    assert(glBindVertexArray == nullptr || !first_extension_check_);
    glBindVertexArray =
        (decltype(glBindVertexArray))eglGetProcAddress("glBindVertexArrayOES");

#endif  // BA_USE_ES3_INCLUDES
  }

  DEBUG_CHECK_GL_ERROR;

  // Flag certain devices as 'speedy' - we use this to enable high/higher
  // quality and whatnot (even in cases where ES3 isnt available).
  is_speedy_android_device_ = false;
  is_extra_speedy_android_device_ = false;
  is_adreno_ = (strstr(renderer, "Adreno") != nullptr);
  draws_shields_funny_ = false;  // start optimistic.

  // ali tv box
  if (!strcmp(renderer, "Mali-450 MP")) {
    is_speedy_android_device_ = true;  // this is borderline speedy/extra-speedy
    draws_shields_funny_ = true;
  }

  // firetv, etc.. lets enable MSAA
  if (!strcmp(renderer, "Adreno (TM) 320")) {
    is_recent_adreno_ = true;
  }

  // this is right on the borderline, but lets go with extra-speedy i guess
  if (!strcmp(renderer, "Adreno (TM) 330")) {
    is_recent_adreno_ = true;
    is_extra_speedy_android_device_ = true;
  }

  // *any* of the 4xx or 5xx series are extra-speedy
  if (strstr(renderer, "Adreno (TM) 4") || strstr(renderer, "Adreno (TM) 5")
      || strstr(renderer, "Adreno (TM) 6")) {
    is_extra_speedy_android_device_ = true;
    is_recent_adreno_ = true;
  }

  // some speedy malis (Galaxy S6 / Galaxy S7-ish)
  if (strstr(renderer, "Mali-T760") || strstr(renderer, "Mali-T860")
      || strstr(renderer, "Mali-T880")) {
    is_extra_speedy_android_device_ = true;
  }
  // Note 8 is speed-tastic
  if (!strcmp(renderer, "Mali-G71") || !strcmp(renderer, "Mali-G72")) {
    is_extra_speedy_android_device_ = true;
  }

  // covers Nexus player
  // HMM Scratch that - this winds up being too slow for phones using this chip.
  if (strstr(renderer, "PowerVR Rogue G6430")) {
    // is_extra_speedy_android_device_ = true;
  }

  // Figure out if we're a Tegra 4/K1/etc since we do some special stuff on
  // those...
  if (!strcmp(renderer, "NVIDIA Tegra")) {
    // tegra 4 won't have ES3 but will have framebuffer_multisample
    if (!g_running_es3 && CheckGLExtension(ex, "framebuffer_multisample")) {
      is_tegra_4_ = true;
      is_speedy_android_device_ = true;
    } else if (g_running_es3) {
      // running ES3 - must be a K1 (for now)
      is_tegra_k1_ = true;
      is_extra_speedy_android_device_ = true;
    } else {
      // looks like Tegra-2 era stuff was just "NVIDIA Tegra" as well...
    }
  }

  // Also store this globally for a few other bits of the app to use..
  g_platform->set_is_tegra_k1(is_tegra_k1_);

  // Extra-speedy implies speedy too..
  if (is_extra_speedy_android_device_) {
    is_speedy_android_device_ = true;
  }

#endif  // BA_OSTYPE_ANDROID

  std::list<TextureCompressionType> c_types;
  assert(g_graphics);
  if (CheckGLExtension(ex, "texture_compression_s3tc"))
    c_types.push_back(TextureCompressionType::kS3TC);

    // Limiting pvr support to iOS for the moment.
#if !BA_OSTYPE_ANDROID
  if (CheckGLExtension(ex, "texture_compression_pvrtc"))
    c_types.push_back(TextureCompressionType::kPVR);
#endif

  // All android devices should support etc1.
  if (CheckGLExtension(ex, "compressed_ETC1_RGB8_texture")) {
    c_types.push_back(TextureCompressionType::kETC1);
  } else {
#if BA_OSTYPE_ANDROID
    Log("Android device missing ETC1 support");
#endif
  }

  // ETC2 is required for ES3 support (and OpenGL 4.4 or something once we
  // eventually get there)
  if (g_running_es3) c_types.push_back(TextureCompressionType::kETC2);

  g_graphics_server->SetTextureCompressionTypes(c_types);

  // Check whether we support high-quality mode (requires a few things like
  // depth textures) For now lets also disallow high-quality in some VR
  // environments.

  if (CheckGLExtension(ex, "depth_texture")) {
    supports_depth_textures_ = true;
#if BA_CARDBOARD_BUILD
    g_graphics->SetSupportsHighQualityGraphics(false);
#else   // BA_CARDBOARD_BUILD
    g_graphics->SetSupportsHighQualityGraphics(true);
#endif  // BA_CARDBOARD_BUILD
  } else {
    supports_depth_textures_ = false;
    g_graphics->SetSupportsHighQualityGraphics(false);
  }

  // Store the tex-compression type we support.
  DEBUG_CHECK_GL_ERROR;

  g_anisotropic_support = CheckGLExtension(ex, "texture_filter_anisotropic");
  if (g_anisotropic_support) {
    glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, &g_max_anisotropy);
  }

  DEBUG_CHECK_GL_ERROR;

  // We can run with our without VAOs but they're nice to have.
  g_vao_support =
      (glGenVertexArrays != nullptr && glDeleteVertexArrays != nullptr
       && glBindVertexArray != nullptr
       && (g_running_es3 || CheckGLExtension(ex, "vertex_array_object")));

#if BA_OSTYPE_IOS_TVOS
  g_blit_framebuffer_support = false;
  g_framebuffer_multisample_support = false;
#elif BA_OSTYPE_MACOS
  g_blit_framebuffer_support = CheckGLExtension(ex, "framebuffer_blit");
  g_framebuffer_multisample_support = false;
#else
  g_blit_framebuffer_support =
      (glBlitFramebuffer != nullptr
       && (g_running_es3 || CheckGLExtension(ex, "framebuffer_blit")));
  g_framebuffer_multisample_support =
      (glRenderbufferStorageMultisample != nullptr
       && (g_running_es3 || (CheckGLExtension(ex, "framebuffer_multisample"))));
#endif

#if BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID

#if BA_OSTYPE_IOS_TVOS
  g_discard_framebuffer_support = CheckGLExtension(ex, "discard_framebuffer");
#else
  g_discard_framebuffer_support =
      (glDiscardFramebufferEXT != nullptr
       && CheckGLExtension(ex, "discard_framebuffer"));
#endif

  g_invalidate_framebuffer_support =
      (g_running_es3 && glInvalidateFramebuffer != nullptr);
#else
  g_discard_framebuffer_support = false;
  g_invalidate_framebuffer_support = false;
#endif

  g_seamless_cube_maps = CheckGLExtension(ex, "seamless_cube_map");

#if BA_OSTYPE_WINDOWS
  // the vmware gl driver breaks horrifically with VAOs turned on
  const char* vendor = (const char*)glGetString(GL_VENDOR);
  if (strstr(vendor, "VMware")) {
    g_vao_support = false;
  }
#endif

#if BA_OSTYPE_ANDROID
  // VAOs currently break my poor kindle fire hd to the point of rebooting it
  if (!g_running_es3 && !is_tegra_4_) {
    g_vao_support = false;
  }

  // also they seem to be problematic on zenfone2's gpu.
  if (strstr(renderer, "PowerVR Rogue G6430")) {
    g_vao_support = false;
  }
#endif

  glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS,
                &g_combined_texture_image_unit_count);

  // If we're running ES3, ask about our max multisample counts and whether we
  // can enable MSAA.
  // enable_msaa_ = false;  // start pessimistic
  g_msaa_max_samples_rgb565 = g_msaa_max_samples_rgb8 = 0;  // start pessimistic

#if BA_OSTYPE_ANDROID || BA_RIFT_BUILD
  bool check_msaa = false;

#if BA_OSTYPE_ANDROID
  if (g_running_es3) {
    check_msaa = true;
  }
#endif  // BA_OSTYPE_ANDROID
#if BA_RIFT_BUILD
  check_msaa = true;
#endif  // BA_RIFT_BUILD

  if (check_msaa) {
    if (glGetInternalformativ != nullptr) {
      GLint count;
      glGetInternalformativ(GL_RENDERBUFFER, GL_RGB565, GL_NUM_SAMPLE_COUNTS, 1,
                            &count);
      if (count > 0) {
        std::vector<GLint> samples;
        samples.resize(static_cast<size_t>(static_cast<size_t>(count)));
        glGetInternalformativ(GL_RENDERBUFFER, GL_RGB565, GL_SAMPLES, count,
                              &samples[0]);
        g_msaa_max_samples_rgb565 = samples[0];
      } else {
        BA_LOG_ONCE("Got 0 samplecounts for RGB565");
        g_msaa_max_samples_rgb565 = 0;
      }
    }
    // RGB8 max multisamples
    if (glGetInternalformativ != nullptr) {
      GLint count;
      glGetInternalformativ(GL_RENDERBUFFER, GL_RGB8, GL_NUM_SAMPLE_COUNTS, 1,
                            &count);
      if (count > 0) {
        std::vector<GLint> samples;
        samples.resize(static_cast<size_t>(count));
        glGetInternalformativ(GL_RENDERBUFFER, GL_RGB8, GL_SAMPLES, count,
                              &samples[0]);
        g_msaa_max_samples_rgb8 = samples[0];
      } else {
        BA_LOG_ONCE("Got 0 samplecounts for RGB8");
        g_msaa_max_samples_rgb8 = 0;
      }
    }
  } else {
    if (is_tegra_4_) {
      // HMM is there a way to query this without ES3?
      g_msaa_max_samples_rgb8 = g_msaa_max_samples_rgb565 = 4;
    }
  }

#if MSAA_ERROR_TEST
  if (enable_msaa_) {
    ScreenMessage("MSAA ENABLED");
    Log("Ballistica MSAA Test: MSAA ENABLED", false, false);
  } else {
    ScreenMessage("MSAA DISABLED");
    Log("Ballistica MSAA Test: MSAA DISABLED", false, false);
  }
#endif  // MSAA_ERROR_TEST

#endif  // BA_OSTYPE_ANDROID

  DEBUG_CHECK_GL_ERROR;

  first_extension_check_ = false;
}

auto RendererGL::GetMSAASamplesForFramebuffer(int width, int height) -> int {
#if BA_RIFT_BUILD
  return 4;
#else
  // we currently aim for 4 up to 800 height and 2 beyond that..
  if (height > 800) {
    return 2;
  } else {
    return 4;
  }
#endif
}

void RendererGL::UpdateMSAAEnabled() {
#if BA_RIFT_BUILD
  if (g_msaa_max_samples_rgb8 > 0) {
    enable_msaa_ = true;
  } else {
    enable_msaa_ = false;
  }
#else

  // lets allow full 1080p msaa with newer stuff..
  int max_msaa_res = is_tegra_k1_ ? 1200 : 800;

  // to start, see if it looks like we support msaa on paper..
  enable_msaa_ =
      ((screen_render_target()->physical_height()
        <= static_cast<float>(max_msaa_res))
       && (g_msaa_max_samples_rgb8 > 0) && (g_msaa_max_samples_rgb565 > 0));

  // ok, lets be careful here.. msaa blitting/etc seems to be particular in
  // terms of supported formats/etc so let's only enable it on explicitly-tested
  // hardware.
  if (!is_tegra_4_ && !is_tegra_k1_ && !is_recent_adreno_) {
    enable_msaa_ = false;
  }

#endif  // BA_RIFT_BUILD
}

auto RendererGL::IsMSAAEnabled() const -> bool { return enable_msaa_; }

static auto GetGLTextureFormat(TextureFormat f) -> GLenum {
  switch (f) {
    case TextureFormat::kDXT1:
      return GL_COMPRESSED_RGBA_S3TC_DXT1_EXT;
      break;
    case TextureFormat::kDXT5:
      return GL_COMPRESSED_RGBA_S3TC_DXT5_EXT;
      break;
    case TextureFormat::kPVR2:
      return GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG;
      break;
    case TextureFormat::kPVR4:
      return GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;
      break;
    case TextureFormat::kETC1:
      return GL_ETC1_RGB8_OES;
      break;
    case TextureFormat::kETC2_RGB:
      return GL_COMPRESSED_RGB8_ETC2;
      break;
    case TextureFormat::kETC2_RGBA:
      return GL_COMPRESSED_RGBA8_ETC2_EAC;
      break;
    default:
      throw Exception("Invalid TextureFormat: "
                      + std::to_string(static_cast<int>(f)));
  }
}

// a stand-in for vertex-array-objects for use on systems that don't support
// them directly
class RendererGL::FakeVertexArrayObject {
 public:
  struct AttrState {
    bool enable;
    GLuint buffer;
    int elem_count;
    GLenum elem_type;
    bool normalized;
    int stride;
    size_t offset;
  };

  explicit FakeVertexArrayObject(RendererGL* renderer)
      : renderer_(renderer), elem_buffer_(0) {
    for (auto& attr : attrs_) {
      attr.enable = false;
    }
  }

  void Bind() {
    DEBUG_CHECK_GL_ERROR;

    // First bind our element buffer.
    assert(elem_buffer_ != 0);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, elem_buffer_);

    // Now bind/enable the buffers we use and disable the ones we don't.
    for (GLuint i = 0; i < kVertexAttrCount; i++) {
      if (attrs_[i].enable) {
        renderer_->BindArrayBuffer(attrs_[i].buffer);
        glVertexAttribPointer(i, attrs_[i].elem_count, attrs_[i].elem_type,
                              static_cast<GLboolean>(attrs_[i].normalized),
                              attrs_[i].stride,
                              reinterpret_cast<void*>(attrs_[i].offset));
      }
      renderer_->SetVertexAttribArrayEnabled(i, attrs_[i].enable);
    }
    DEBUG_CHECK_GL_ERROR;
  }
  void SetElementBuffer(GLuint vbo) { elem_buffer_ = vbo; }
  void SetAttribBuffer(GLuint buffer, VertexAttr attr, int elem_count,
                       GLenum elem_type, bool normalized, int stride,
                       size_t offset) {
    assert(attr < RendererGL::kVertexAttrCount);
    assert(!attrs_[attr].enable);
    attrs_[attr].enable = true;
    attrs_[attr].buffer = buffer;
    attrs_[attr].elem_count = elem_count;
    attrs_[attr].elem_type = elem_type;
    attrs_[attr].normalized = normalized;
    attrs_[attr].stride = stride;
    attrs_[attr].offset = offset;
  }

  AttrState attrs_[RendererGL::kVertexAttrCount]{};
  RendererGL* renderer_{};
  GLuint elem_buffer_{};
};

class RendererGL::FramebufferObjectGL : public Framebuffer {
 public:
  FramebufferObjectGL(RendererGL* renderer_in, int width_in, int height_in,
                      bool linear_interp_in, bool depth_in, bool is_texture_in,
                      bool depth_is_texture_in, bool high_quality_in,
                      bool msaa_in, bool alpha_in)
      : width_(width_in),
        height_(height_in),
        linear_interp_(linear_interp_in),
        depth_(depth_in),
        is_texture_(is_texture_in),
        depth_is_texture_(depth_is_texture_in),
        renderer_(renderer_in),
        high_quality_(high_quality_in),
        msaa_(msaa_in),
        alpha_(alpha_in) {
    // Desktop stuff is always high-quality
#if BA_OSTYPE_MACOS || BA_OSTYPE_LINUX || BA_OSTYPE_WINDOWS
    high_quality_ = true;
#endif

    // Things are finally getting to the point where we can default to
    // desktop quality on some mobile stuff.
#if BA_OSTYPE_ANDROID
    if (renderer_->is_tegra_k1_) {
      high_quality_ = true;
    }
#endif

    Load();
  }

  ~FramebufferObjectGL() override { Unload(); }

  void Load(bool force_low_quality = false) {
    if (loaded_) return;
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;
    GLenum status;
    DEBUG_CHECK_GL_ERROR;
    glGenFramebuffers(1, &framebuffer_);
    renderer_->BindFramebuffer(framebuffer_);
    DEBUG_CHECK_GL_ERROR;
    bool do_high_quality = high_quality_;
    if (force_low_quality) do_high_quality = false;
    int samples = 0;
    if (msaa_) {
      // Can't multisample with texture buffers currently.
      assert(!is_texture_ && !depth_is_texture_);

      int target_samples =
          renderer_->GetMSAASamplesForFramebuffer(width_, height_);

      if (do_high_quality) {
        samples = std::min(target_samples, g_msaa_max_samples_rgb8);
      } else {
        samples = std::min(target_samples, g_msaa_max_samples_rgb565);
      }
    }
    if (is_texture_) {
      // attach a texture for the color target
      glGenTextures(1, &texture_);
      renderer_->BindTexture(GL_TEXTURE_2D, texture_);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                      linear_interp_ ? GL_LINEAR : GL_NEAREST);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                      linear_interp_ ? GL_LINEAR : GL_NEAREST);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

      // On android/ios lets go with 16 bit unless they explicitly request high
      // quality.
#if BA_OSTYPE_ANDROID || BA_OSTYPE_IOS_TVOS
      GLenum format;
      if (alpha_) {
        format = do_high_quality ? GL_UNSIGNED_BYTE : GL_UNSIGNED_SHORT_4_4_4_4;
      } else {
        format = do_high_quality ? GL_UNSIGNED_BYTE : GL_UNSIGNED_SHORT_5_6_5;
      }
#else
      GLenum format = GL_UNSIGNED_BYTE;
#endif
      // if (srgbTest) {
      //   Log("YOOOOOOO");
      //   glTexImage2D(GL_TEXTURE_2D, 0, alpha_?GL_SRGB8_ALPHA8:GL_SRGB8,
      //   _width, _height, 0, alpha_?GL_RGBA:GL_RGB, format, nullptr);
      // } else {
      glTexImage2D(GL_TEXTURE_2D, 0, alpha_ ? GL_RGBA : GL_RGB, width_, height_,
                   0, alpha_ ? GL_RGBA : GL_RGB, format, nullptr);
      // }
      glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                             GL_TEXTURE_2D, texture_, 0);
    } else {
      // Regular renderbuffer.
      assert(!alpha_);  // fixme
#if BA_OSTYPE_IOS_TVOS
      GLenum format =
          GL_RGB565;  // FIXME; need to pull ES3 headers in for GL_RGB8
#elif BA_OSTYPE_ANDROID
      GLenum format = do_high_quality ? GL_RGB8 : GL_RGB565;
#else
      GLenum format = GL_RGB8;
#endif
      glGenRenderbuffers(1, &render_buffer_);
      DEBUG_CHECK_GL_ERROR;
      glBindRenderbuffer(GL_RENDERBUFFER, render_buffer_);
      DEBUG_CHECK_GL_ERROR;
      if (samples > 0) {
#if BA_OSTYPE_IOS_TVOS
        throw Exception();
#else
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples, format,
                                         width_, height_);
#endif
      } else {
        glRenderbufferStorage(GL_RENDERBUFFER, format, width_, height_);
      }
      DEBUG_CHECK_GL_ERROR;
      glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                                GL_RENDERBUFFER, render_buffer_);
      DEBUG_CHECK_GL_ERROR;
    }
    DEBUG_CHECK_GL_ERROR;
    if (depth_) {
      if (depth_is_texture_) {
        glGenTextures(1, &depth_texture_);
        DEBUG_CHECK_GL_ERROR;
        renderer_->BindTexture(GL_TEXTURE_2D, depth_texture_);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        DEBUG_CHECK_GL_ERROR;
        // fixme - need to pull in ES3 stuff for iOS to get GL_DEPTH_COMPONENT24
#if BA_OSTYPE_IOS_TVOS
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, width_, height_, 0,
                     GL_DEPTH_COMPONENT, GL_UNSIGNED_SHORT, nullptr);
#else
        if (do_high_quality) {
#if BA_OSTYPE_ANDROID
          assert(g_running_es3);
#endif  // BA_OSTYPE_ANDROID
          glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, width_, height_,
                       0, GL_DEPTH_COMPONENT, GL_UNSIGNED_INT, nullptr);
        } else {
          glTexImage2D(
              GL_TEXTURE_2D, 0,
              g_running_es3 ? GL_DEPTH_COMPONENT16 : GL_DEPTH_COMPONENT, width_,
              height_, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_SHORT, nullptr);
        }
#endif  // BA_OSTYPE_IOS_TVOS

        DEBUG_CHECK_GL_ERROR;

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                               GL_TEXTURE_2D, depth_texture_, 0);

        DEBUG_CHECK_GL_ERROR;
      } else {
        // Just use a plain old renderbuffer if we don't need it as a texture
        // (this is more widely supported).
        glGenRenderbuffers(1, &depth_render_buffer_);
        DEBUG_CHECK_GL_ERROR;
        glBindRenderbuffer(GL_RENDERBUFFER, depth_render_buffer_);
        DEBUG_CHECK_GL_ERROR;

        if (samples > 0) {
#if BA_OSTYPE_IOS_TVOS
          throw Exception();
#else
          // (GL_DEPTH_COMPONENT24 not available in ES2 it looks like)
          bool do24;
#if BA_OSTYPE_ANDROID
          do24 = (do_high_quality && g_running_es3);
#else
          do24 = do_high_quality;
#endif

          glRenderbufferStorageMultisample(
              GL_RENDERBUFFER, samples,
              do24 ? GL_DEPTH_COMPONENT24 : GL_DEPTH_COMPONENT16, width_,
              height_);
          // (do_high_quality &&
          // g_running_es3)?GL_DEPTH_COMPONENT24:GL_DEPTH_COMPONENT16, _width,
          // _height);
#endif
        } else {
          // FIXME - need to pull in es3 headers to get GL_DEPTH_COMPONENT24 on
          //  iOS
#if BA_OSTYPE_IOS_TVOS
          GLenum format = GL_DEPTH_COMPONENT16;
#else
          // (GL_DEPTH_COMPONENT24 not available in ES2 it looks like)
          GLenum format = (do_high_quality && g_running_es3)
                              ? GL_DEPTH_COMPONENT24
                              : GL_DEPTH_COMPONENT16;
#endif

          glRenderbufferStorage(GL_RENDERBUFFER, format, width_, height_);
        }

        DEBUG_CHECK_GL_ERROR;
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                  GL_RENDERBUFFER, depth_render_buffer_);
        DEBUG_CHECK_GL_ERROR;
      }
    }

    status = glCheckFramebufferStatus(GL_FRAMEBUFFER);

    if (status != GL_FRAMEBUFFER_COMPLETE) {
      const char* version = (const char*)glGetString(GL_VERSION);
      const char* vendor = (const char*)glGetString(GL_VENDOR);
      const char* renderer = (const char*)glGetString(GL_RENDERER);
      throw Exception(
          "Framebuffer setup failed for " + std::to_string(width_) + " by "
          + std::to_string(height_) + " fb with depth " + std::to_string(depth_)
          + " asTex " + std::to_string(depth_is_texture_) + " gl-version "
          + version + " vendor " + vendor + " renderer " + renderer);
    }
    // GLint enc;
    // glGetFramebufferAttachmentParameteriv(GL_FRAMEBUFFER,
    // GL_COLOR_ATTACHMENT0, GL_FRAMEBUFFER_ATTACHMENT_COLOR_ENCODING, &enc); if
    // (enc == GL_SRGB) {
    //   Log("GOT SRGB!!!!!!!!!!!");
    // } else if (enc == GL_LINEAR) {
    //   Log("GOT LINEAR...");
    // } else {
    //   Log("GOT OTHER..");
    // }
    loaded_ = true;
  }

  void Unload() {
    assert(InGraphicsThread());
    if (!loaded_) return;

    // If our textures are currently bound as anything, clear that out.
    // (otherwise a new texture with that same ID won't be bindable)
    for (int& i : renderer_->bound_textures_2d_) {
      if (i == texture_) {  // NOLINT(bugprone-branch-clone)
        i = -1;
      } else if (depth_ && (i == depth_texture_)) {
        i = -1;
      }
    }

    if (!g_graphics_server->renderer_context_lost()) {
      // Tear down the FBO and texture attachment
      if (is_texture_) {
        glDeleteTextures(1, &texture_);
      } else {
        glDeleteRenderbuffers(1, &render_buffer_);
      }
      if (depth_) {
        if (depth_is_texture_) {
          glDeleteTextures(1, &depth_texture_);
        } else {
          glDeleteRenderbuffers(1, &depth_render_buffer_);
        }
        DEBUG_CHECK_GL_ERROR;
      }

      // If this one is current, make sure we re-bind next time.
      // (otherwise we might prevent a new framebuffer with a recycled id from
      // binding)
      if (renderer_->active_framebuffer_ == framebuffer_) {
        renderer_->active_framebuffer_ = -1;
      }
      glDeleteFramebuffers(1, &framebuffer_);
      DEBUG_CHECK_GL_ERROR;
    }
    loaded_ = false;
  }

  void Bind() {
    assert(InGraphicsThread());
    renderer_->BindFramebuffer(framebuffer_);
    // if (time(nullptr)%2 == 0) {
    //   glDisable(GL_FRAMEBUFFER_SRGB);
    // }
  }

  auto texture() const -> GLuint {
    assert(is_texture_);
    return texture_;
  }

  auto depth_texture() const -> GLuint {
    assert(depth_ && depth_is_texture_);
    return depth_texture_;
  }

  auto width() const -> int { return width_; }
  auto height() const -> int { return height_; }
  auto id() const -> GLuint { return framebuffer_; }

 private:
  RendererGL* renderer_{};
  bool depth_{};
  bool is_texture_{};
  bool depth_is_texture_{};
  bool high_quality_{};
  bool msaa_{};
  bool alpha_{};
  bool linear_interp_{};
  bool loaded_{};
  int width_{}, height_{};
  GLuint framebuffer_{}, texture_{}, depth_texture_{}, render_buffer_{},
      depth_render_buffer_{};
};  // FramebufferObject

// Base class for fragment/vertex shaders.
class RendererGL::ShaderGL : public Object {
 public:
  auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
    return ThreadIdentifier::kMain;
  }

  ShaderGL(GLenum type_in, const std::string& src_in) : type_(type_in) {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;
    assert(type_ == GL_FRAGMENT_SHADER || type_ == GL_VERTEX_SHADER);
    shader_ = glCreateShader(type_);
    DEBUG_CHECK_GL_ERROR;
    BA_PRECONDITION(shader_);
    const char* s = src_in.c_str();
    glShaderSource(shader_, 1, &s, nullptr);
    glCompileShader(shader_);
    GLint compile_status;
    glGetShaderiv(shader_, GL_COMPILE_STATUS, &compile_status);
    if (compile_status == GL_FALSE) {
      const char* version = (const char*)glGetString(GL_VERSION);
      const char* vendor = (const char*)glGetString(GL_VENDOR);
      const char* renderer = (const char*)glGetString(GL_RENDERER);
      // Let's not crash here. We have a better chance of calling home this way
      // and theres a chance the game will still be playable.
      Log(std::string("Compile failed for ") + GetTypeName()
          + " shader:\n------------SOURCE BEGIN-------------\n" + src_in
          + "\n-----------SOURCE END-------------\n" + GetInfo()
          + "\nrenderer: " + renderer + "\nvendor: " + vendor
          + "\nversion:" + version);
    } else {
      assert(compile_status == GL_TRUE);
      std::string info = GetInfo();
      if (!info.empty()
          && (strstr(info.c_str(), "error:") || strstr(info.c_str(), "warning:")
              || strstr(info.c_str(), "Error:")
              || strstr(info.c_str(), "Warning:"))) {
        const char* version = (const char*)glGetString(GL_VERSION);
        const char* vendor = (const char*)glGetString(GL_VENDOR);
        const char* renderer = (const char*)glGetString(GL_RENDERER);
        Log(std::string("WARNING: info returned for ") + GetTypeName()
            + " shader:\n------------SOURCE BEGIN-------------\n" + src_in
            + "\n-----------SOURCE END-------------\n" + info + "\nrenderer: "
            + renderer + "\nvendor: " + vendor + "\nversion:" + version);
      }
    }
    DEBUG_CHECK_GL_ERROR;
  }
  ~ShaderGL() override {
    assert(InGraphicsThread());
    if (!g_graphics_server->renderer_context_lost()) {
      glDeleteShader(shader_);
      DEBUG_CHECK_GL_ERROR;
    }
  }
  auto shader() const -> GLuint { return shader_; }

 private:
  auto GetTypeName() const -> const char* {
    if (type_ == GL_VERTEX_SHADER) {
      return "vertex";
    } else {
      return "fragment";
    }
  }
  auto GetInfo() -> std::string {
    static char log[1024];
    GLsizei log_size;
    glGetShaderInfoLog(shader_, sizeof(log), &log_size, log);
    return log;
  }
  std::string name_;
  GLuint shader_{};
  GLenum type_{};
  BA_DISALLOW_CLASS_COPIES(ShaderGL);
};  // ShaderGL

//-----------------------------------------------------------------

class RendererGL::FragmentShaderGL : public RendererGL::ShaderGL {
 public:
  explicit FragmentShaderGL(const std::string& src_in)
      : ShaderGL(GL_FRAGMENT_SHADER, src_in) {}
};

//-------------------------------------------------------------------

class RendererGL::VertexShaderGL : public RendererGL::ShaderGL {
 public:
  explicit VertexShaderGL(const std::string& src_in)
      : ShaderGL(GL_VERTEX_SHADER, src_in) {}
};

//-------------------------------------------------------------------

class RendererGL::ProgramGL {
 public:
  ProgramGL(RendererGL* renderer,
            const Object::Ref<VertexShaderGL>& vertex_shader_in,
            const Object::Ref<FragmentShaderGL>& fragment_shader_in,
            std::string name, int pflags)
      : fragment_shader_(fragment_shader_in),
        vertex_shader_(vertex_shader_in),
        renderer_(renderer),
        pflags_(pflags),
        name_(std::move(name)) {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;
    program_ = glCreateProgram();
    BA_PRECONDITION(program_);
    glAttachShader(program_, fragment_shader_->shader());
    glAttachShader(program_, vertex_shader_->shader());
    assert(pflags_ & PFLAG_USES_POSITION_ATTR);
    if (pflags_ & PFLAG_USES_POSITION_ATTR)
      glBindAttribLocation(program_, kVertexAttrPosition, "position");
    if (pflags_ & PFLAG_USES_UV_ATTR)
      glBindAttribLocation(program_, kVertexAttrUV, "uv");
    if (pflags_ & PFLAG_USES_NORMAL_ATTR)
      glBindAttribLocation(program_, kVertexAttrNormal, "normal");
    if (pflags_ & PFLAG_USES_ERODE_ATTR)
      glBindAttribLocation(program_, kVertexAttrErode, "erode");
    if (pflags_ & PFLAG_USES_COLOR_ATTR)
      glBindAttribLocation(program_, kVertexAttrColor, "color");
    if (pflags_ & PFLAG_USES_SIZE_ATTR)
      glBindAttribLocation(program_, kVertexAttrSize, "size");
    if (pflags_ & PFLAG_USES_DIFFUSE_ATTR)
      glBindAttribLocation(program_, kVertexAttrDiffuse, "diffuse");
    if (pflags_ & PFLAG_USES_UV2_ATTR)
      glBindAttribLocation(program_, kVertexAttrUV2, "uv2");
    glLinkProgram(program_);
    GLint linkStatus;
    glGetProgramiv(program_, GL_LINK_STATUS, &linkStatus);
    if (linkStatus == GL_FALSE) {
      Log("Link failed for program '" + name_ + "':\n" + GetInfo());
    } else {
      assert(linkStatus == GL_TRUE);

      std::string info = GetInfo();
      if (!info.empty()
          && (strstr(info.c_str(), "error:") || strstr(info.c_str(), "warning:")
              || strstr(info.c_str(), "Error:")
              || strstr(info.c_str(), "Warning:"))) {
        Log("WARNING: program using frag shader '" + name_
            + "' returned info:\n" + info);
      }
    }

    // go ahead and bind ourself so child classes can config uniforms and
    // whatnot
    Bind();
    mvp_uniform_ = glGetUniformLocation(program_, "modelViewProjectionMatrix");
    assert(mvp_uniform_ != -1);
    if (pflags_ & PFLAG_USES_MODEL_WORLD_MATRIX) {
      model_world_matrix_uniform_ =
          glGetUniformLocation(program_, "modelWorldMatrix");
      assert(model_world_matrix_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_MODEL_VIEW_MATRIX) {
      model_view_matrix_uniform_ =
          glGetUniformLocation(program_, "modelViewMatrix");
      assert(model_view_matrix_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_CAM_POS) {
      cam_pos_uniform_ = glGetUniformLocation(program_, "camPos");
      assert(cam_pos_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_CAM_ORIENT_MATRIX) {
      cam_orient_matrix_uniform_ =
          glGetUniformLocation(program_, "camOrientMatrix");
      assert(cam_orient_matrix_uniform_ != -1);
    }
    if (pflags_ & PFLAG_USES_SHADOW_PROJECTION_MATRIX) {
      light_shadow_projection_matrix_uniform_ =
          glGetUniformLocation(program_, "lightShadowProjectionMatrix");
      assert(light_shadow_projection_matrix_uniform_ != -1);
    }
  }

  virtual ~ProgramGL() {
    assert(InGraphicsThread());
    if (!g_graphics_server->renderer_context_lost()) {
      glDetachShader(program_, fragment_shader_->shader());
      glDetachShader(program_, vertex_shader_->shader());
      glDeleteProgram(program_);
      DEBUG_CHECK_GL_ERROR;
    }
  }
  auto IsBound() const -> bool {
    return (renderer()->GetActiveProgram() == this);
  }

  auto program() const -> GLuint { return program_; }

  void Bind() { renderer_->UseProgram(this); }

  auto name() const -> const std::string& { return name_; }

  // should grab matrices from the renderer
  // or whatever else it needs in prep for drawing
  void PrepareToDraw() {
    DEBUG_CHECK_GL_ERROR;

    assert(IsBound());

    // update matrices as necessary...

    uint32_t mvpState = g_graphics_server->GetModelViewProjectionMatrixState();
    if (mvpState != mvp_state_) {
      mvp_state_ = mvpState;
      glUniformMatrix4fv(mvp_uniform_, 1, 0,
                         g_graphics_server->GetModelViewProjectionMatrix().m);
    }
    DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_MODEL_WORLD_MATRIX) {
      assert(!(pflags_
               & PFLAG_WORLD_SPACE_PTS));  // with world space points this would
      // be identity; don't waste time.
      uint32_t state = g_graphics_server->GetModelWorldMatrixState();
      if (state != model_world_matrix_state_) {
        model_world_matrix_state_ = state;
        glUniformMatrix4fv(model_world_matrix_uniform_, 1, 0,
                           g_graphics_server->GetModelWorldMatrix().m);
      }
    }
    DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_MODEL_VIEW_MATRIX) {
      assert(!(pflags_
               & PFLAG_WORLD_SPACE_PTS));  // with world space points this would
      // be identity; don't waste time.
      // there's no state for just modelview but this works
      uint32_t state = g_graphics_server->GetModelViewProjectionMatrixState();
      if (state != model_view_matrix_state_) {
        model_view_matrix_state_ = state;
        glUniformMatrix4fv(model_view_matrix_uniform_, 1, 0,
                           g_graphics_server->model_view_matrix().m);
      }
    }
    DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_CAM_POS) {
      uint32_t state = g_graphics_server->cam_pos_state();
      if (state != cam_pos_state_) {
        cam_pos_state_ = state;
        const Vector3f& p(g_graphics_server->cam_pos());
        glUniform4f(cam_pos_uniform_, p.x, p.y, p.z, 1.0f);
      }
    }
    DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_CAM_ORIENT_MATRIX) {
      uint32_t state = g_graphics_server->GetCamOrientMatrixState();
      if (state != cam_orient_matrix_state_) {
        cam_orient_matrix_state_ = state;
        glUniformMatrix4fv(cam_orient_matrix_uniform_, 1, 0,
                           g_graphics_server->GetCamOrientMatrix().m);
      }
    }
    DEBUG_CHECK_GL_ERROR;

    if (pflags_ & PFLAG_USES_SHADOW_PROJECTION_MATRIX) {
      uint32_t state =
          g_graphics_server->light_shadow_projection_matrix_state();
      if (state != light_shadow_projection_matrix_state_) {
        light_shadow_projection_matrix_state_ = state;
        glUniformMatrix4fv(
            light_shadow_projection_matrix_uniform_, 1, 0,
            g_graphics_server->light_shadow_projection_matrix().m);
      }
    }
    DEBUG_CHECK_GL_ERROR;
  }

 protected:
  void SetTextureUnit(const char* tex_name, int unit) {
    assert(IsBound());
    int c = glGetUniformLocation(program_, tex_name);
    if (c == -1) {
#if !MSAA_ERROR_TEST
      Log("Error: ShaderGL: " + name_ + ": Can't set texture unit for texture '"
          + tex_name + "'");
      DEBUG_CHECK_GL_ERROR;
#endif
    } else {
      glUniform1i(c, unit);
    }
  }

  auto GetInfo() -> std::string {
    static char log[1024];
    GLsizei log_size;
    glGetProgramInfoLog(program_, sizeof(log), &log_size, log);
    return log;
  }

  auto renderer() const -> RendererGL* { return renderer_; }

 private:
  RendererGL* renderer_{};
  Object::Ref<FragmentShaderGL> fragment_shader_;
  Object::Ref<VertexShaderGL> vertex_shader_;
  std::string name_;
  GLuint program_{};
  int pflags_{};
  uint32_t mvp_state_{};
  GLint mvp_uniform_{};
  GLint model_world_matrix_uniform_{};
  GLint model_view_matrix_uniform_{};
  GLint light_shadow_projection_matrix_uniform_{};
  uint32_t light_shadow_projection_matrix_state_{};
  uint32_t model_world_matrix_state_{};
  uint32_t model_view_matrix_state_{};
  GLint cam_pos_uniform_{};
  uint32_t cam_pos_state_{};
  GLint cam_orient_matrix_uniform_{};
  GLuint cam_orient_matrix_state_{};
  BA_DISALLOW_CLASS_COPIES(ProgramGL);
};  // ProgramGL

class RendererGL::SimpleProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
    kColorizeTexUnit,
    kMaskTexUnit,
    kMaskUV2TexUnit,
    kBlurTexUnit
  };

  SimpleProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
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
  void SetColorTexture(const TextureData* t) {
    assert(flags_ & SHD_TEXTURE);
    assert(IsBound());
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetColorTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
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
  void setGlow(float glow_amount, float glow_blur) {
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
  void SetColorizeTexture(const TextureData* t) {
    assert(flags_ & SHD_COLORIZE);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorizeTexUnit);
  }
  void SetMaskTexture(const TextureData* t) {
    assert(flags_ & SHD_MASKED);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kMaskTexUnit);
  }
  void SetMaskUV2Texture(const TextureData* t) {
    assert(flags_ & SHD_MASK_UV2);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kMaskUV2TexUnit);
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
           + " flatness:" + std::to_string((flags & SHD_MASK_UV2) != 0);
  }
  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR;
    if (flags & SHD_TEXTURE) pflags |= PFLAG_USES_UV_ATTR;
    if (flags & SHD_MASK_UV2) pflags |= PFLAG_USES_UV2_ATTR;
    return pflags;
  }
  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "attribute vec4 position;\n";
    if ((flags & SHD_TEXTURE) || (flags & SHD_COLORIZE)
        || (flags & SHD_COLORIZE2))
      s += "attribute vec2 uv;\n"
           "varying vec2 vUV;\n";
    if (flags & SHD_MASK_UV2)
      s += "attribute vec2 uv2;\n"
           "varying vec2 vUV2;\n";
    if (flags & SHD_SHADOW)
      s += "varying vec2 vUVShadow;\n"
           "varying vec2 vUVShadow2;\n"
           "varying vec2 vUVShadow3;\n"
           "uniform " LOWP "vec4 shadowParams;\n";
    s += "void main() {\n";
    if (flags & SHD_TEXTURE) s += "   vUV = uv;\n";
    if (flags & SHD_MASK_UV2) s += "   vUV2 = uv2;\n";
    if (flags & SHD_SHADOW)
      s += "   vUVShadow = uv+0.4*vec2(shadowParams.x,shadowParams.y);\n";
    if (flags & SHD_SHADOW)
      s += "   vUVShadow2 = uv+0.8*vec2(shadowParams.x,shadowParams.y);\n";
    if (flags & SHD_SHADOW)
      s += "   vUVShadow3 = uv+1.3*vec2(shadowParams.x,shadowParams.y);\n";
    s += "   gl_Position = modelViewProjectionMatrix*position;\n"
         "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    if (flags & SHD_TEXTURE) s += "uniform " LOWP "sampler2D colorTex;\n";
    if ((flags & SHD_COLORIZE))
      s += "uniform " LOWP
           "sampler2D colorizeTex;\n"
           "uniform " LOWP "vec4 colorizeColor;\n";
    if ((flags & SHD_COLORIZE2)) s += "uniform " LOWP "vec4 colorize2Color;\n";
    if ((flags & SHD_TEXTURE) || (flags & SHD_COLORIZE)
        || (flags & SHD_COLORIZE2))
      s += "varying " LOWP "vec2 vUV;\n";
    if (flags & SHD_MASK_UV2) s += "varying " LOWP "vec2 vUV2;\n";
    if (flags & SHD_FLATNESS) s += "uniform " LOWP "float flatness;\n";
    if (flags & SHD_SHADOW) {
      s += "varying " LOWP
           "vec2 vUVShadow;\n"
           "varying " LOWP
           "vec2 vUVShadow2;\n"
           "varying " LOWP
           "vec2 vUVShadow3;\n"
           "uniform " LOWP "vec4 shadowParams;\n";
    }
    if (flags & SHD_GLOW) {
      s += "uniform " LOWP "vec2 glowParams;\n";
    }
    if ((flags & SHD_MODULATE) || (!(flags & SHD_TEXTURE)))
      s += "uniform " LOWP "vec4 color;\n";
    if (flags & SHD_MASKED) s += "uniform " LOWP "sampler2D maskTex;\n";
    if (flags & SHD_MASK_UV2) s += "uniform " LOWP "sampler2D maskUV2Tex;\n";
    s += "void main() {\n";
    if (!(flags & SHD_TEXTURE)) {
      s += "   gl_FragColor = color;\n";
    } else {
      std::string blurArg;
      if (flags & SHD_GLOW) {
        s += "   " LOWP
             "vec4 cVal = texture2D(colorTex,vUV,glowParams.g);\n"
             "      gl_FragColor = vec4(color.rgb * cVal.rgb * cVal.a * "
             "glowParams.r,0.0)";  // we premultiply this.
        if (flags & SHD_MASK_UV2) s += " * vec4(texture2D(maskUV2Tex,vUV2).a)";
        s += ";\n";
      } else {
        if ((flags & SHD_COLORIZE) || (flags & SHD_COLORIZE2))
          s += "   " LOWP
               "vec4 colorizeVal = texture2D(colorizeTex,vUV);\n";  // TEMP TEST
        if (flags & SHD_COLORIZE)
          s += "   " LOWP "float colorizeA = colorizeVal.r;\n";
        if (flags & SHD_COLORIZE2)
          s += "   " LOWP "float colorizeB = colorizeVal.g;\n";
        if (flags & SHD_MASKED)
          s += "   " MEDIUMP "vec4 mask = texture2D(maskTex,vUV);";

        if (flags & SHD_MODULATE) {
          if (flags & SHD_FLATNESS) {
            s += "   " LOWP
                 "vec4 rawTexColor = texture2D(colorTex,vUV);\n"
                 "   gl_FragColor = color * "
                 "vec4(mix(rawTexColor.rgb,vec3(1.0),flatness),rawTexColor.a)";
          } else {
            s += "   gl_FragColor = color * texture2D(colorTex,vUV)";
          }
        } else {
          s += "   gl_FragColor = texture2D(colorTex,vUV)";
        }

        if (flags & SHD_COLORIZE)
          s += " * (vec4(1.0-colorizeA)+colorizeColor*colorizeA)";
        if (flags & SHD_COLORIZE2)
          s += " * (vec4(1.0-colorizeB)+colorize2Color*colorizeB)";
        if (flags & SHD_MASKED)
          s += " * vec4(vec3(mask.r),mask.a) + "
               "vec4(vec3(mask.g)*colorizeColor.rgb+vec3(mask.b),0.0)";
        s += ";\n";

        if (flags & SHD_SHADOW) {
          s += "   " LOWP
               "float shadowA = (texture2D(colorTex,vUVShadow).a + "
               "texture2D(colorTex,vUVShadow2,1.0).a + "
               "texture2D(colorTex,vUVShadow3,2.0).a) * shadowParams.a";

          if (flags & SHD_MASK_UV2) s += " * texture2D(maskUV2Tex,vUV2).a";
          s += ";\n";
          s += "   gl_FragColor = "
               "vec4(gl_FragColor.rgb*gl_FragColor.a,gl_FragColor.a) + "
               "(1.0-gl_FragColor.a) * vec4(0,0,0,shadowA);\n";
          s += "   gl_FragColor = "
               "vec4(gl_FragColor.rgb/"
               "max(0.001,gl_FragColor.a),gl_FragColor.a);\n";
        }
      }
      if (flags & SHD_DEPTH_BUG_TEST)
        s += "   gl_FragColor = vec4(abs(gl_FragCoord.z-gl_FragColor.r));\n";
      if (flags & SHD_PREMULTIPLY)
        s += "   gl_FragColor = vec4(gl_FragColor.rgb * "
             "gl_FragColor.a,gl_FragColor.a);";
    }
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
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
};  // SimpleProgramGL

class RendererGL::ObjectProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
    kReflectionTexUnit,
    kVignetteTexUnit,
    kLightShadowTexUnit,
    kColorizeTexUnit
  };

  ObjectProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
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
  void SetColorTexture(const TextureData* t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetReflectionTexture(const TextureData* t) {
    assert(flags_ & SHD_REFLECTION);
    renderer()->BindTexture(GL_TEXTURE_CUBE_MAP, t, kReflectionTexUnit);
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
    renderer()->BindTexture(GL_TEXTURE_2D, t, kVignetteTexUnit);
  }
  void SetLightShadowTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kLightShadowTexUnit);
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
  void SetColorizeTexture(const TextureData* t) {
    assert(flags_ & SHD_COLORIZE);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorizeTexUnit);
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("ObjectProgramGL")
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
        "uniform vec4 camPos;\n"
        "attribute vec4 position;\n"
        "attribute " LOWP
        "vec2 uv;\n"
        "varying " LOWP
        "vec2 vUV;\n"
        "varying " MEDIUMP "vec4 vScreenCoord;\n";
    if ((flags & SHD_REFLECTION) || (flags & SHD_LIGHT_SHADOW))
      s += "uniform mat4 modelWorldMatrix;\n";
    if (flags & SHD_REFLECTION)
      s += "attribute " MEDIUMP
           "vec3 normal;\n"
           "varying " MEDIUMP "vec3 vReflect;\n";
    if (flags & SHD_LIGHT_SHADOW)
      s += "uniform mat4 lightShadowProjectionMatrix;\n"
           "varying " MEDIUMP "vec4 vLightShadowUV;\n";
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
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " LOWP
        "sampler2D colorTex;\n"
        "uniform " LOWP
        "sampler2D vignetteTex;\n"
        "uniform " LOWP
        "vec4 color;\n"
        "varying " LOWP
        "vec2 vUV;\n"
        "varying " MEDIUMP "vec4 vScreenCoord;\n";
    if (flags & SHD_ADD) s += "uniform " LOWP "vec4 colorAdd;\n";
    if (flags & SHD_REFLECTION)
      s += "uniform " LOWP
           "samplerCube reflectionTex;\n"
           "varying " MEDIUMP
           "vec3 vReflect;\n"
           "uniform " LOWP "vec4 reflectMult;\n";
    if (flags & SHD_COLORIZE)
      s += "uniform " LOWP
           "sampler2D colorizeTex;\n"
           "uniform " LOWP "vec4 colorizeColor;\n";
    if (flags & SHD_COLORIZE2) s += "uniform " LOWP "vec4 colorize2Color;\n";
    if (flags & SHD_LIGHT_SHADOW)
      s += "uniform " LOWP
           "sampler2D lightShadowTex;\n"
           "varying " MEDIUMP "vec4 vLightShadowUV;\n";
    s += "void main() {\n";
    if (flags & SHD_LIGHT_SHADOW)
      s +=
          "   " LOWP
          "vec4 lightShadVal = texture2DProj(lightShadowTex,vLightShadowUV);\n";
    if ((flags & SHD_COLORIZE) || (flags & SHD_COLORIZE2))
      s += "   " LOWP "vec4 colorizeVal = texture2D(colorizeTex,vUV);\n";
    if (flags & SHD_COLORIZE)
      s += "   " LOWP "float colorizeA = colorizeVal.r;\n";
    if (flags & SHD_COLORIZE2)
      s += "   " LOWP "float colorizeB = colorizeVal.g;\n";
    s += "   gl_FragColor = (color*texture2D(colorTex,vUV)";
    if (flags & SHD_COLORIZE)
      s += " * (vec4(1.0-colorizeA)+colorizeColor*colorizeA)";
    if (flags & SHD_COLORIZE2)
      s += " * (vec4(1.0-colorizeB)+colorize2Color*colorizeB)";
    s += ")";

    // add in lights/shadows
    if (flags & SHD_LIGHT_SHADOW) {
      if (flags & SHD_OBJ_TRANSPARENT)
        s += " * vec4((2.0*lightShadVal).rgb,1) + "
             "vec4((lightShadVal-0.5).rgb,0)";
      else
        s += " * (2.0*lightShadVal) + (lightShadVal-0.5)";
    }

    // add glow and reflection
    if (flags & SHD_REFLECTION)
      s += " + (reflectMult*textureCube(reflectionTex,vReflect))";
    if (flags & SHD_ADD) s += " + colorAdd";

    // subtract vignette
    s += " - vec4(texture2DProj(vignetteTex,vScreenCoord).rgb,0)";

    s += ";\n";
    // s += "gl_FragColor = 0.999 * texture2DProj(vignetteTex,vScreenCoord) +
    // 0.01 * gl_FragColor;";

    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
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
};  // ObjectProgramGL

class RendererGL::SmokeProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit { kColorTexUnit, kDepthTexUnit, kBlurTexUnit };

  SmokeProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
        flags_(flags),
        r_(0),
        g_(0),
        b_(0),
        a_(0) {
    SetTextureUnit("colorTex", kColorTexUnit);
    if (flags & SHD_OVERLAY) {
      SetTextureUnit("depthTex", kDepthTexUnit);
      SetTextureUnit("blurTex", kBlurTexUnit);
    }
    color_location_ = glGetUniformLocation(program(), "colorMult");
    assert(color_location_ != -1);
  }
  void SetColorTexture(const TextureData* t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetDepthTexture(GLuint t) {
    assert(flags_ & SHD_OVERLAY);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kDepthTexUnit);
  }
  void SetBlurTexture(GLuint t) {
    assert(flags_ & SHD_OVERLAY);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kBlurTexUnit);
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

 private:
  auto GetName(int flags) -> std::string {
    return std::string("SmokeProgramGL");
  }
  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_DIFFUSE_ATTR
                 | PFLAG_USES_UV_ATTR | PFLAG_WORLD_SPACE_PTS
                 | PFLAG_USES_ERODE_ATTR | PFLAG_USES_COLOR_ATTR;
    return pflags;
  }
  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "attribute vec4 position;\n"
        "attribute " MEDIUMP
        "vec2 uv;\n"
        "varying " MEDIUMP
        "vec2 vUV;\n"
        "attribute " LOWP
        "float erode;\n"
        "attribute " MEDIUMP
        "float diffuse;\n"
        "varying " LOWP
        "float vErode;\n"
        "attribute " MEDIUMP
        "vec4 color;\n"
        "varying " LOWP
        "vec4 vColor;\n"
        "uniform " MEDIUMP "vec4 colorMult;\n";
    if (flags & SHD_OVERLAY)
      s += "varying " LOWP
           "vec4 cDiffuse;\n"
           "varying " MEDIUMP "vec4 vScreenCoord;\n";
    s += "void main() {\n"
         "   vUV = uv;\n"
         "   gl_Position = modelViewProjectionMatrix*position;\n"
         "   vErode = erode;\n";
    // in overlay mode we pass color/diffuse to the pixel-shader since we
    // combine them there with a blurred bg image to get a soft look.  In the
    // simple version we just use a flat ambient color here.
    if (flags & SHD_OVERLAY)
      s += "   vScreenCoord = "
           "vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
           "   vColor = vec4(vec3(7.0*diffuse),0.7) * color * colorMult;\n"
           "   cDiffuse = colorMult*(0.3+0.8*diffuse);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    else
      s += "   vColor = "
           "(vec4(vec3(7.0),1.0)*color+vec4(vec3(0.4),0))*vec4(vec3(diffuse),0."
           "4) * colorMult;\n";
    s += "   vColor *= vec4(vec3(vColor.a),1.0);\n";  // premultiply
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " LOWP
        "sampler2D colorTex;\n"
        "varying " MEDIUMP
        "vec2 vUV;\n"
        "varying " LOWP
        "float vErode;\n"
        "varying " LOWP "vec4 vColor;\n";
    if (flags & SHD_OVERLAY)
      s += "varying " MEDIUMP
           "vec4 vScreenCoord;\n"
           "uniform " LOWP
           "sampler2D depthTex;\n"
           "uniform " LOWP
           "sampler2D blurTex;\n"
           "varying " LOWP "vec4 cDiffuse;\n";
    s += "void main() {\n";
    s += "   " LOWP
         "float erodeMult = smoothstep(vErode,1.0,texture2D(colorTex,vUV).r);\n"
         "   gl_FragColor = (vColor*vec4(erodeMult));";
    if (flags & SHD_OVERLAY) {
      s += "   gl_FragColor += vec4(vec3(gl_FragColor.a),0) * cDiffuse * "
           "(0.11+0.8*texture2DProj(blurTex,vScreenCoord));\n";
      s += "   " MEDIUMP
           " float depth =texture2DProj(depthTex,vScreenCoord).r;\n";
      // adreno bug where depth is returned as 0..1 instead of glDepthRange()
      if (GetFunkyDepthIssue()) {
        s += "    depth = " + std::to_string(kBackingDepth3) + "+depth*("
             + std::to_string(kBackingDepth4) + "-"
             + std::to_string(kBackingDepth3) + ");\n";
      }
      s += "   gl_FragColor *= "
           "(1.0-smoothstep(0.0,0.002,gl_FragCoord.z-depth));\n";
    }

    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  float r_, g_, b_, a_;
  GLint color_location_;
  int flags_;
};  // SmokeProgramGL

class RendererGL::BlurProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
  };

  BlurProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
        flags_(flags),
        pixel_size_x_(0.0f),
        pixel_size_y_(0.0f) {
    SetTextureUnit("colorTex", kColorTexUnit);
    pixel_size_location_ = glGetUniformLocation(program(), "pixelSize");
    assert(pixel_size_location_ != -1);
  }
  void SetPixelSize(float x, float y) {
    assert(IsBound());
    if (x != pixel_size_x_ || y != pixel_size_y_) {
      pixel_size_x_ = x;
      pixel_size_y_ = y;
      glUniform2f(pixel_size_location_, pixel_size_x_, pixel_size_y_);
    }
  }

  void SetColorTexture(const TextureData* t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetColorTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("BlurProgramGL");
  }
  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_UV_ATTR;
    return pflags;
  }
  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "attribute vec4 position;\n"
        "attribute " MEDIUMP
        "vec2 uv;\n"
        "varying " MEDIUMP
        "vec2 vUV1;\n"
        "varying " MEDIUMP
        "vec2 vUV2;\n"
        "varying " MEDIUMP
        "vec2 vUV3;\n"
        "varying " MEDIUMP
        "vec2 vUV4;\n"
        "varying " MEDIUMP
        "vec2 vUV5;\n"
        "varying " MEDIUMP
        "vec2 vUV6;\n"
        "varying " MEDIUMP
        "vec2 vUV7;\n"
        "varying " MEDIUMP
        "vec2 vUV8;\n"
        "uniform " MEDIUMP
        "vec2 pixelSize;\n"
        "void main() {\n"
        "   gl_Position = modelViewProjectionMatrix*position;\n"
        "   vUV1 = uv+vec2(-0.5,0)*pixelSize;\n"
        "   vUV2 = uv+vec2(-1.5,0)*pixelSize;\n"
        "   vUV3 = uv+vec2(0.5,0)*pixelSize;\n"
        "   vUV4 = uv+vec2(1.5,0)*pixelSize;\n"
        "   vUV5 = uv+vec2(-0.5,1.0)*pixelSize;\n"
        "   vUV6 = uv+vec2(0.5,1.0)*pixelSize;\n"
        "   vUV7 = uv+vec2(-0.5,-1.0)*pixelSize;\n"
        "   vUV8 = uv+vec2(0.5,-1.0)*pixelSize;\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " MEDIUMP
        "sampler2D colorTex;\n"
        "varying " MEDIUMP
        "vec2 vUV1;\n"
        "varying " MEDIUMP
        "vec2 vUV2;\n"
        "varying " MEDIUMP
        "vec2 vUV3;\n"
        "varying " MEDIUMP
        "vec2 vUV4;\n"
        "varying " MEDIUMP
        "vec2 vUV5;\n"
        "varying " MEDIUMP
        "vec2 vUV6;\n"
        "varying " MEDIUMP
        "vec2 vUV7;\n"
        "varying " MEDIUMP
        "vec2 vUV8;\n"
        "void main() {\n"
        "   gl_FragColor = 0.125*(texture2D(colorTex,vUV1)\n"
        "                     + texture2D(colorTex,vUV2)\n"
        "                     + texture2D(colorTex,vUV3)\n"
        "                     + texture2D(colorTex,vUV4)\n"
        "                     + texture2D(colorTex,vUV5)\n"
        "                     + texture2D(colorTex,vUV6)\n"
        "                     + texture2D(colorTex,vUV7)\n"
        "                     + texture2D(colorTex,vUV8));\n"
        "}";
    if (flags & SHD_DEBUG_PRINT) {
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    }
    return s;
  }

  int flags_;
  GLint pixel_size_location_;
  float pixel_size_x_, pixel_size_y_;
};  // BlurProgramGL

class RendererGL::ShieldProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kDepthTexUnit,
  };

  ShieldProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
        flags_(flags) {
    SetTextureUnit("depthTex", kDepthTexUnit);
  }
  void SetDepthTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kDepthTexUnit);
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
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "attribute vec4 position;\n"
        "varying " HIGHP
        "vec4 vScreenCoord;\n"
        "void main() {\n"
        "   gl_Position = modelViewProjectionMatrix*position;\n"
        "   vScreenCoord = vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
        "   vScreenCoord.xy += vec2(1.0);\n"
        "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " HIGHP
        "sampler2D depthTex;\n"
        "varying " HIGHP
        "vec4 vScreenCoord;\n"
        "void main() {\n"
        "    " HIGHP "float depth = texture2DProj(depthTex,vScreenCoord).r;\n";

    // adreno bug where depth is returned as 0..1 instead of glDepthRange()
    if (GetFunkyDepthIssue()) {
      s += "    depth = " + std::to_string(kBackingDepth3) + "+depth*("
           + std::to_string(kBackingDepth4) + "-"
           + std::to_string(kBackingDepth3) + ");\n";
    }
    // s+= "    depth =
    // "+std::to_string(kBackingDepth3)+"0.15+depth*(0.9-0.15);\n"; "    depth
    // *=
    // 0.936;\n" "    depth = 1.0/(65535.0*((1.0/depth)/16777216.0));\n" " depth
    //= 1.0/((1.0/depth)+0.08);\n" "    depth += 0.1f;\n"
    s += "    " HIGHP
         "float d = abs(depth - gl_FragCoord.z);\n"
         "    d = 1.0 - smoothstep(0.0,0.0006,d);\n"
         "    d = 0.2*smoothstep(0.96,1.0,d)+0.2*d+0.4*d*d*d;\n";

    // some mali chips seem to have no high precision and thus this looks
    // terrible..
    // ..in those cases lets done down the intersection effect significantly
    if (GetDrawsShieldsFunny()) {
      s += "    gl_FragColor = vec4(d*0.13,d*0.1,d,0);\n";
    } else {
      s += "    gl_FragColor = vec4(d*0.5,d*0.4,d,0);\n";
    }
    s += "}";

    // this shows msaa depth error on bridgit
    //"    gl_FragColor = vec4(smoothstep(0.73,0.77,depth),0.0,0.0,0.5);\n"

    // "    d = 1.0 - smoothstep(0.0,0.0006,d);\n"
    // "    d = 0.2*smoothstep(0.96,1.0,d)+0.2*d+0.4*d*d*d;\n"
    //"    if (d < 0.01) gl_FragColor = vec4(0.0,1.0,0.0,0.5);\n"

    //"    gl_FragColor = vec4(vec3(10.0*abs(depth-gl_FragCoord.z)),1);\n"
    // "    gl_FragColor = vec4(0,10.0*abs(depth-gl_FragCoord.z),0,0.1);\n"
    // "    if (depth < gl_FragCoord.z) gl_FragColor =
    // vec4(1.0-10.0*(gl_FragCoord.z-depth),0,0,1);\n" "    else gl_FragColor =
    // vec4(0,1.0-10.0*(depth-gl_FragCoord.z),0,1);\n"
    //"    gl_FragColor = vec4(vec3(depth),1);\n"

    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

  int flags_;
};

class RendererGL::PostProcessProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit {
    kColorTexUnit,
    kDepthTexUnit,
    kColorSlightBlurredTexUnit,
    kColorBlurredTexUnit,
    kColorBlurredMoreTexUnit
  };

  PostProcessProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
        flags_(flags),
        dof_near_min_(0),
        dof_near_max_(0),
        dof_far_min_(0),
        dof_far_max_(0),
        distort_(0.0f) {
    SetTextureUnit("colorTex", kColorTexUnit);

    if (UsesSlightBlurredTex())
      SetTextureUnit("colorSlightBlurredTex", kColorSlightBlurredTexUnit);
    if (UsesBlurredTexture())
      SetTextureUnit("colorBlurredTex", kColorBlurredTexUnit);
    SetTextureUnit("colorBlurredMoreTex", kColorBlurredMoreTexUnit);
    SetTextureUnit("depthTex", kDepthTexUnit);

    dof_location_ = glGetUniformLocation(program(), "dofRange");
#if !MSAA_ERROR_TEST
    assert(dof_location_ != -1);
#endif

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
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetColorSlightBlurredTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorSlightBlurredTexUnit);
  }
  void SetColorBlurredMoreTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorBlurredMoreTexUnit);
  }
  void SetColorBlurredTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorBlurredTexUnit);
  }
  void SetDepthTexture(GLuint t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kDepthTexUnit);
  }

  void SetDepthOfFieldRanges(float near_min, float near_max, float far_min,
                             float far_max) {
    assert(IsBound());
    if (near_min != dof_near_min_ || near_max != dof_near_max_
        || far_min != dof_far_min_ || far_max != dof_far_max_) {
      DEBUG_CHECK_GL_ERROR;
      dof_near_min_ = near_min;
      dof_near_max_ = near_max;
      dof_far_min_ = far_min;
      dof_far_max_ = far_max;
      float vals[4] = {dof_near_min_, dof_near_max_, dof_far_min_,
                       dof_far_max_};
      glUniform1fv(dof_location_, 4, vals);
      DEBUG_CHECK_GL_ERROR;
    }
  }
  void SetDistort(float distort) {
    assert(IsBound());
    assert(flags_ & SHD_DISTORT);
    if (distort != distort_) {
      DEBUG_CHECK_GL_ERROR;
      distort_ = distort;
      glUniform1f(distort_location_, distort_);
      DEBUG_CHECK_GL_ERROR;
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

  // testing MSAA BUG
#if MSAA_ERROR_TEST
  string GetVertexCode(int flags) {
    string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "attribute vec4 position;\n";
    if (flags & SHD_DISTORT)
      s += "attribute " LOWP
           "vec3 normal;\n"
           "uniform mat4 modelViewMatrix;\n"
           "uniform float distort;\n";
    if (flags & SHD_EYES) s += "varying " HIGHP "float calcedDepth;\n";

    s += "varying " HIGHP
         "vec4 vScreenCoord;\n"
         "void main() {\n"
         "   gl_Position = modelViewProjectionMatrix*position;\n";
    if (flags & SHD_DISTORT)
      s += "   float eyeDot = "
           "abs(normalize(modelViewMatrix*vec4(normal,0.0))).z;\n"
           "   vec4 posDistorted = "
           "modelViewProjectionMatrix*(position-eyeDot*distort*vec4(normal,0));"
           "\n"
           "   vScreenCoord = "
           "vec4(posDistorted.xy/posDistorted.w,posDistorted.zw);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    else
      s += "   vScreenCoord = "
           "vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    if (flags & SHD_EYES)
      s += "   calcedDepth = " + std::to_string(kBackingDepth3) + "+"
           + std::to_string(kBackingDepth4 - kBackingDepth3)
           + "*(0.5*(gl_Position.z/gl_Position.w)+0.5);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  string GetFragmentCode(int flags) {
    string s;
    s = "uniform " HIGHP
        "sampler2D depthTex;\n"
        "varying " HIGHP "vec4 vScreenCoord;\n";
    s += "void main() {\n"
         "   " HIGHP "float depth = texture2DProj(depthTex,vScreenCoord).r;\n";
    s += "   gl_FragColor = vec4(vec3(14.0*(depth-0.76)),1);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }

#else   // msaa bug test

  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s = "uniform mat4 modelViewProjectionMatrix;\n"
        "attribute vec4 position;\n";
    if (flags & SHD_DISTORT)
      s += "attribute " LOWP
           "vec3 normal;\n"
           "uniform mat4 modelViewMatrix;\n"
           "uniform float distort;\n";
    if (flags & SHD_EYES) {
      s += "varying " HIGHP "float calcedDepth;\n";
    }

    s += "varying " MEDIUMP
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
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;
    s = "uniform " LOWP
        "sampler2D colorTex;\n"
        "uniform " LOWP
        "sampler2D colorBlurredMoreTex;\n"
        "uniform " HIGHP
        "sampler2D depthTex;\n"
        "varying " MEDIUMP
        "vec4 vScreenCoord;\n"
        "uniform " LOWP "float dofRange[4];\n";
    if (flags & (SHD_HIGHER_QUALITY | SHD_EYES)) {
      s += "uniform " LOWP "sampler2D colorBlurredTex;\n";
    }
    if (flags & SHD_EYES)
      s += "uniform " LOWP
           "sampler2D colorSlightBlurredTex;\n"
           "varying " HIGHP "float calcedDepth;\n";

    s +=
        "void main() {\n"
        "   " MEDIUMP "float depth = texture2DProj(depthTex,vScreenCoord).r;\n";

    bool doConditional = ((flags & SHD_CONDITIONAL) && !(flags & (SHD_EYES)));

    if (doConditional) {
      // special-case completely out of focus areas and completely in-focus
      // areas..
      s += "  if (depth > dofRange[1] && depth < dofRange[2]) {\n";
      if (flags & SHD_HIGHER_QUALITY) {
        s +=
            "   " LOWP
            "vec4 color = texture2DProj(colorTex,vScreenCoord);\n"
            "   " LOWP
            "vec4 colorBlurred = texture2DProj(colorBlurredTex,vScreenCoord);\n"
            "   " LOWP
            "vec4 colorBlurredMore = "
            "0.4*texture2DProj(colorBlurredMoreTex,vScreenCoord);\n"
            "   " MEDIUMP
            "vec4 diff = colorBlurred-color;\n"
            "    diff = sign(diff) * max(vec4(0.0),abs(diff)-0.12);\n"
            "   gl_FragColor = (0.55*colorBlurredMore) + "
            "(0.62+colorBlurredMore)*(color-diff);\n\n";
      } else {
        s += "      gl_FragColor = texture2DProj(colorTex,vScreenCoord);\n";
      }
      s += "   }\n"
           "   else if (depth < dofRange[0] || depth > dofRange[3]) {\n";
      if (flags & SHD_HIGHER_QUALITY) {
        s +=
            "   " LOWP
            "vec4 colorBlurred = texture2DProj(colorBlurredTex,vScreenCoord);\n"
            "   " LOWP
            "vec4 colorBlurredMore = "
            "0.4*texture2DProj(colorBlurredMoreTex,vScreenCoord);\n"
            "   gl_FragColor = (0.55*colorBlurredMore) + "
            "(0.62+colorBlurredMore)*colorBlurred;\n\n";
      } else {
        s += "      gl_FragColor = "
             "texture2DProj(colorBlurredMoreTex,vScreenCoord);\n";
      }
      s += "   }\n"
           "   else{\n";
    }

    // transition areas..
    s += "   " LOWP "vec4 color = texture2DProj(colorTex,vScreenCoord);\n";
    if (flags & SHD_EYES)
      s += "   " LOWP
           "vec4 colorSlightBlurred = "
           "texture2DProj(colorSlightBlurredTex,vScreenCoord);\n";

    if (flags & (SHD_HIGHER_QUALITY | SHD_EYES)) {
      s += "   " LOWP
           "vec4 colorBlurred = texture2DProj(colorBlurredTex,vScreenCoord);\n"
           "   " LOWP
           "vec4 colorBlurredMore = "
           "0.4*texture2DProj(colorBlurredMoreTex,vScreenCoord);\n"
           "   " LOWP "float blur = " BLURSCALE
           " (smoothstep(dofRange[2],dofRange[3],depth)\n"
           "                      +  1.0 - "
           "smoothstep(dofRange[0],dofRange[1],depth));\n"
           "   " MEDIUMP
           "vec4 diff = colorBlurred-color;\n"
           "    diff = sign(diff) * max(vec4(0.0),abs(diff)-0.12);\n"
           "   gl_FragColor = (0.55*colorBlurredMore) + "
           "(0.62+colorBlurredMore)*mix(color-diff,colorBlurred,blur);\n\n";
    } else {
      s += "   " LOWP
           "vec4 colorBlurredMore = "
           "texture2DProj(colorBlurredMoreTex,vScreenCoord);\n"
           "   " LOWP "float blur = " BLURSCALE
           " (smoothstep(dofRange[2],dofRange[3],depth)\n"
           "                      +  1.0 - "
           "smoothstep(dofRange[0],dofRange[1],depth));\n"
           "   gl_FragColor = mix(color,colorBlurredMore,blur);\n\n";
    }

    if (flags & SHD_EYES) {
      s += "   " MEDIUMP "vec4 diffEye = colorBlurred-color;\n";
      s += "    diffEye = sign(diffEye) * max(vec4(0.0),abs(diffEye)-0.06);\n";
      s += "   " LOWP
           "vec4 baseColorEye = "
           "mix(color-10.0*(diffEye),colorSlightBlurred,0.83);\n";
      s += "   " LOWP
           "vec4 eyeColor = (0.55*colorBlurredMore) + "
           "(0.62+colorBlurredMore)*mix(baseColorEye,colorBlurred,blur);\n\n";
      s += "   " LOWP
           "float dBlend = smoothstep(-0.0004,-0.0001,depth-calcedDepth);\n"
           "   gl_FragColor = mix(gl_FragColor,eyeColor,dBlend);\n";
    }
    if (doConditional) {
      s += "   }\n";
    }

    // demonstrates MSAA striation issue:
    // s += "   gl_FragColor =
    // mix(gl_FragColor,vec4(vec3(14.0*(depth-0.76)),1),0.999);\n";
    // s += "   gl_FragColor =
    // vec4(vec3(14.0*(texture2DProj(depthTex,vScreenCoord).r-0.76)),1);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
#endif  // msaa bug test

  int flags_;
  float dof_near_min_;
  float dof_near_max_;
  float dof_far_min_;
  float dof_far_max_;
  GLint dof_location_;
  float distort_;
  GLint distort_location_;
};

class RendererGL::SpriteProgramGL : public RendererGL::ProgramGL {
 public:
  enum TextureUnit { kColorTexUnit, kDepthTexUnit };

  SpriteProgramGL(RendererGL* renderer, int flags)
      : RendererGL::ProgramGL(
          renderer, Object::New<VertexShaderGL>(GetVertexCode(flags)),
          Object::New<FragmentShaderGL>(GetFragmentCode(flags)), GetName(flags),
          GetPFlags(flags)),
        flags_(flags),
        r_(0),
        g_(0),
        b_(0),
        a_(0) {
    SetTextureUnit("colorTex", kColorTexUnit);

    if (flags & SHD_OVERLAY) {
      SetTextureUnit("depthTex", kDepthTexUnit);
    }

    if (flags & SHD_COLOR) {
      color_location_ = glGetUniformLocation(program(), "colorU");
      assert(color_location_ != -1);
    }
    DEBUG_CHECK_GL_ERROR;
  }
  void SetColorTexture(const TextureData* t) {
    renderer()->BindTexture(GL_TEXTURE_2D, t, kColorTexUnit);
  }
  void SetDepthTexture(GLuint t) {
    assert(flags_ & SHD_OVERLAY);
    renderer()->BindTexture(GL_TEXTURE_2D, t, kDepthTexUnit);
  }
  void SetColor(float r, float g, float b, float a = 1.0f) {
    assert(flags_ & SHD_COLOR);
    assert(IsBound());
    if (r != r_ || g != g_ || b != b_ || a != a_) {
      r_ = r;
      g_ = g;
      b_ = b;
      a_ = a;
      glUniform4f(color_location_, r_, g_, b_, a_);
    }
  }

 private:
  auto GetName(int flags) -> std::string {
    return std::string("SpriteProgramGL");
  }
  auto GetPFlags(int flags) -> int {
    int pflags = PFLAG_USES_POSITION_ATTR | PFLAG_USES_SIZE_ATTR
                 | PFLAG_USES_COLOR_ATTR | PFLAG_USES_UV_ATTR;
    if (flags & SHD_CAMERA_ALIGNED) pflags |= PFLAG_USES_CAM_ORIENT_MATRIX;
    return pflags;
  }
  auto GetVertexCode(int flags) -> std::string {
    std::string s;
    s += "uniform mat4 modelViewProjectionMatrix;\n"
         "attribute vec4 position;\n"
         "attribute " MEDIUMP
         "vec2 uv;\n"
         "attribute " MEDIUMP
         "float size;\n"
         "varying " MEDIUMP "vec2 vUV;\n";

    if (flags & SHD_COLOR) s += "uniform " LOWP "vec4 colorU;\n";

    if (flags & SHD_CAMERA_ALIGNED) s += "uniform mat4 camOrientMatrix;\n";

    if (flags & SHD_OVERLAY) s += "varying " LOWP "vec4 vScreenCoord;\n";

    s += "attribute " LOWP
         "vec4 color;\n"
         "varying " LOWP
         "vec4 vColor;\n"
         "void main() {\n";

    if (flags & SHD_CAMERA_ALIGNED)
      s += "   " HIGHP
           "vec4 pLocal = "
           "(position+camOrientMatrix*vec4((uv.s-0.5)*size,0,(uv.t-0.5)*size,0)"
           ");\n";
    else
      s += "   " HIGHP
           "vec4 pLocal = "
           "(position+vec4((uv.s-0.5)*size,0,(uv.t-0.5)*size,0));\n";
    s += "   gl_Position = modelViewProjectionMatrix*pLocal;\n"
         "   vUV = uv;\n";
    if (flags & SHD_COLOR)
      s += "   vColor = color*colorU;\n";
    else
      s += "   vColor = color;\n";
    if (flags & SHD_OVERLAY)
      s += "   vScreenCoord = "
           "vec4(gl_Position.xy/gl_Position.w,gl_Position.zw);\n"
           "   vScreenCoord.xy += vec2(1.0);\n"
           "   vScreenCoord.xy *= vec2(0.5*vScreenCoord.w);\n";
    s += "}";

    if (flags & SHD_DEBUG_PRINT)
      Log("\nVertex code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  auto GetFragmentCode(int flags) -> std::string {
    std::string s;

    s += "uniform " LOWP
         "sampler2D colorTex;\n"
         "varying " MEDIUMP
         "vec2 vUV;\n"
         "varying " LOWP "vec4 vColor;\n";
    if (flags & SHD_OVERLAY)
      s += "varying " MEDIUMP
           "vec4 vScreenCoord;\n"
           "uniform " MEDIUMP "sampler2D depthTex;\n";

    s += "void main() {\n"
         "   gl_FragColor = vColor*vec4(texture2D(colorTex,vUV).r);\n";
    if (flags & SHD_EXP2)
      s += "   gl_FragColor = vec4(vUV,0,0) + "
           "vec4(gl_FragColor.rgb*gl_FragColor.rgb,gl_FragColor.a);\n";
    if (flags & SHD_OVERLAY) {
      s += "   " MEDIUMP
           "float depth = texture2DProj(depthTex,vScreenCoord).r;\n";
      // adreno 320 bug where depth is returned as 0..1 instead of
      // glDepthRange()
      if (GetFunkyDepthIssue()) {
        s += "    depth = " + std::to_string(kBackingDepth3) + "+depth*("
             + std::to_string(kBackingDepth4) + "-"
             + std::to_string(kBackingDepth3) + ");\n";
      }
      s += "   gl_FragColor *= "
           "(1.0-smoothstep(0.0,0.001,gl_FragCoord.z-depth));\n";
    }
    s += "}";
    if (flags & SHD_DEBUG_PRINT)
      Log("\nFragment code for shader '" + GetName(flags) + "':\n\n" + s);
    return s;
  }
  float r_, g_, b_, a_;
  GLint color_location_;

  int flags_;
};

class RendererGL::TextureDataGL : public TextureRendererData {
 public:
  TextureDataGL(const TextureData& texture_in, RendererGL* renderer_in)
      : tex_media_(&texture_in), texture_(0), renderer_(renderer_in) {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;
    glGenTextures(1, &texture_);
    DEBUG_CHECK_GL_ERROR;
  }

  ~TextureDataGL() override {
    if (!InGraphicsThread()) {
      Log("Error: TextureDataGL dying outside of graphics thread.");
    } else {
      // if we're currently bound as anything, clear that out
      // (otherwise a new texture with that same ID won't be bindable)
      for (int i = 0; i < kMaxGLTexUnitsUsed; i++) {
        if ((renderer_->bound_textures_2d_[i]) == texture_) {
          renderer_->bound_textures_2d_[i] = -1;
        }
        if ((renderer_->bound_textures_cube_map_[i]) == texture_) {
          renderer_->bound_textures_cube_map_[i] = -1;
        }
      }
      if (!g_graphics_server->renderer_context_lost()) {
        glDeleteTextures(1, &texture_);
        DEBUG_CHECK_GL_ERROR;
      }
    }
  }

  auto GetTexture() const -> GLuint { return texture_; }

  void Load() override {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;

    if (tex_media_->texture_type() == TextureType::k2D) {
      renderer_->BindTexture(GL_TEXTURE_2D, texture_);
      const TexturePreloadData* preload_data = &tex_media_->preload_datas()[0];
      int base_src_level = preload_data->base_level;
      assert(preload_data->buffers[base_src_level]);
      GraphicsQuality q = g_graphics_server->quality();

      // Determine whether to use anisotropic sampling on this texture:
      // basically all the UI stuff that is only ever seen from straight on
      // doesn't need it.
      bool allow_ani = true;

      // FIXME - filtering by filename.. once we get this stuff on a server we
      //  should include this as metadata instead.
      const char* n = tex_media_->file_name().c_str();

      // The following exceptions should *never* need aniso-sampling.
      {
        if (!strcmp(n, "fontBig")) {  // NOLINT(bugprone-branch-clone)
          allow_ani = false;

          // Lets splurge on this for higher but not high.
          // (names over characters might benefit, though most text doesnt)
        } else if (strstr(n, "Icon")) {
          allow_ani = false;
        } else if (strstr(n, "characterIconMask")) {
          allow_ani = false;
        } else if (!strcmp(n, "bg")) {
          allow_ani = false;
        } else if (strstr(n, "light")) {
          allow_ani = false;
        } else if (strstr(n, "shadow")) {
          allow_ani = false;
        } else if (!strcmp(n, "sparks")) {
          allow_ani = false;
        } else if (!strcmp(n, "smoke")) {
          allow_ani = false;
        } else if (!strcmp(n, "scorch")) {
          allow_ani = false;
        } else if (!strcmp(n, "scorchBig")) {
          allow_ani = false;
        } else if (!strcmp(n, "white")) {
          allow_ani = false;
        } else if (!strcmp(n, "buttonBomb")) {
          allow_ani = false;
        } else if (!strcmp(n, "buttonJump")) {
          allow_ani = false;
        } else if (!strcmp(n, "buttonPickUp")) {
          allow_ani = false;
        } else if (!strcmp(n, "buttonPunch")) {
          allow_ani = false;
        } else if (strstr(n, "touchArrows")) {
          allow_ani = false;
        } else if (!strcmp(n, "actionButtons")) {
          allow_ani = false;
        }
      }
      // The following are considered 'nice to have' - we turn aniso. off for
      // them in anything less than 'higher' mode.
      if (allow_ani && (q < GraphicsQuality::kHigher)) {
        if (strstr(n, "ColorMask")) {  // NOLINT(bugprone-branch-clone)
          allow_ani = false;           // character color-masks
        } else if (strstr(n, "softRect")) {
          allow_ani = false;
        } else if (strstr(n, "BG")) {
          allow_ani = false;  // level backgrounds
        } else if (!strcmp(n, "explosion")) {
          allow_ani = false;
        } else if (!strcmp(n, "bar")) {
          allow_ani = false;
        }
      }

      // In higher quality we do anisotropic trilinear mipmap.
      if (q >= GraphicsQuality::kHigher) {
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR);
        if (g_anisotropic_support && allow_ani) {
          glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT,
                          std::min(16.0f, g_max_anisotropy));
        }
      } else if (q >= GraphicsQuality::kHigh) {
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR);
        if (g_anisotropic_support && allow_ani)
          glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT,
                          std::min(16.0f, g_max_anisotropy));
      } else if (q >= GraphicsQuality::kMedium) {
        // In medium quality we don't do anisotropy but do trilinear.
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR);
      } else {
        // in low quality we do bilinear
        assert(q == GraphicsQuality::kLow);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_NEAREST);
      }

      glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

      int src_level = base_src_level;
      int level = 0;
      bool all_levels_handled = false;
      while (preload_data->buffers[src_level] != nullptr
             && !all_levels_handled) {
        switch (preload_data->formats[src_level]) {
          case TextureFormat::kRGBA_8888: {
            glTexImage2D(GL_TEXTURE_2D, level, GL_RGBA,
                         preload_data->widths[src_level],
                         preload_data->heights[src_level], 0, GL_RGBA,
                         GL_UNSIGNED_BYTE, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps
            // for uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          case TextureFormat::kRGBA_4444: {
            glTexImage2D(
                GL_TEXTURE_2D, level, GL_RGBA, preload_data->widths[src_level],
                preload_data->heights[src_level], 0, GL_RGBA,
                GL_UNSIGNED_SHORT_4_4_4_4, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps
            // for uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          case TextureFormat::kRGB_565: {
            glTexImage2D(
                GL_TEXTURE_2D, level, GL_RGB, preload_data->widths[src_level],
                preload_data->heights[src_level], 0, GL_RGB,
                GL_UNSIGNED_SHORT_5_6_5, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps
            // for uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          case TextureFormat::kRGB_888: {
            glTexImage2D(GL_TEXTURE_2D, level, GL_RGB,
                         preload_data->widths[src_level],
                         preload_data->heights[src_level], 0, GL_RGB,
                         GL_UNSIGNED_BYTE, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps
            // for uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          default: {
            glCompressedTexImage2D(
                GL_TEXTURE_2D, level,
                GetGLTextureFormat(preload_data->formats[src_level]),
                preload_data->widths[src_level],
                preload_data->heights[src_level], 0,
                static_cast_check_fit<GLsizei>(preload_data->sizes[src_level]),
                preload_data->buffers[src_level]);
            break;
          }
        }
        src_level++;
        level++;
        DEBUG_CHECK_GL_ERROR;
      }
      GL_LABEL_OBJECT(GL_TEXTURE, texture_, tex_media_->GetName().c_str());
    } else if (tex_media_->texture_type() == TextureType::kCubeMap) {
      // Cube map.
      renderer_->BindTexture(GL_TEXTURE_CUBE_MAP, texture_);

      bool do_generate_mips = false;
      for (uint32_t i = 0; i < 6; i++) {
        const TexturePreloadData* preload_data =
            &tex_media_->preload_datas()[i];
        int base_src_level = preload_data->base_level;
        assert(preload_data->buffers[base_src_level]);

        GraphicsQuality q = g_graphics_server->quality();

        // do trilinear in higher quality; otherwise bilinear is good enough..
        if (q >= GraphicsQuality::kHigher) {
          glTexParameterf(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER,
                          GL_LINEAR_MIPMAP_LINEAR);
        } else {
          glTexParameterf(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER,
                          GL_LINEAR_MIPMAP_NEAREST);
        }

        glTexParameterf(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S,
                        GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T,
                        GL_CLAMP_TO_EDGE);

        int src_level = base_src_level;
        int level = 0;
        bool generating_remaining_mips = false;
        while (preload_data->buffers[src_level] != nullptr
               && !generating_remaining_mips) {
          switch (preload_data->formats[src_level]) {
            case TextureFormat::kRGBA_8888:
              glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, level, GL_RGBA,
                           preload_data->widths[src_level],
                           preload_data->heights[src_level], 0, GL_RGBA,
                           GL_UNSIGNED_BYTE, preload_data->buffers[src_level]);
              generating_remaining_mips = do_generate_mips = true;
              break;
            case TextureFormat::kRGBA_4444:
              glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, level, GL_RGBA,
                           preload_data->widths[src_level],
                           preload_data->heights[src_level], 0, GL_RGBA,
                           GL_UNSIGNED_SHORT_4_4_4_4,
                           preload_data->buffers[src_level]);
              generating_remaining_mips = do_generate_mips = true;
              break;
            case TextureFormat::kRGB_565:
              glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, level, GL_RGB,
                           preload_data->widths[src_level],
                           preload_data->heights[src_level], 0, GL_RGB,
                           GL_UNSIGNED_SHORT_5_6_5,
                           preload_data->buffers[src_level]);
              generating_remaining_mips = do_generate_mips = true;
              break;
            case TextureFormat::kRGB_888:
              glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, level, GL_RGB,
                           preload_data->widths[src_level],
                           preload_data->heights[src_level], 0, GL_RGB,
                           GL_UNSIGNED_BYTE, preload_data->buffers[src_level]);
              generating_remaining_mips = do_generate_mips = true;
              break;
            default:
              glCompressedTexImage2D(
                  GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, level,
                  GetGLTextureFormat(preload_data->formats[src_level]),
                  preload_data->widths[src_level],
                  preload_data->heights[src_level], 0,
                  static_cast_check_fit<GLsizei>(
                      preload_data->sizes[src_level]),
                  preload_data->buffers[src_level]);
              break;
          }
          src_level++;
          level++;
          DEBUG_CHECK_GL_ERROR;
        }
      }

      // If we're generating remaining mips on the gpu, do so.
      if (do_generate_mips) {
        glGenerateMipmap(GL_TEXTURE_CUBE_MAP);
      }

      GL_LABEL_OBJECT(GL_TEXTURE, texture_, tex_media_->GetName().c_str());
    } else {
      throw Exception();
    }
    DEBUG_CHECK_GL_ERROR;
  }

 private:
  const TextureData* tex_media_;
  RendererGL* renderer_;
  GLuint texture_;
};  // TextureDataGL

void RendererGL::SetViewport(GLint x, GLint y, GLsizei width, GLsizei height) {
  if (x != viewport_x_ || y != viewport_y_ || width != viewport_width_
      || height != viewport_height_) {
    viewport_x_ = x;
    viewport_y_ = y;
    viewport_width_ = width;
    viewport_height_ = height;
    glViewport(viewport_x_, viewport_y_, viewport_width_, viewport_height_);
  }
}

void RendererGL::SetVertexAttribArrayEnabled(GLuint i, bool enabled) {
  assert(!g_vao_support);
  assert(i < kVertexAttrCount);
  if (enabled != vertex_attrib_arrays_enabled_[i]) {
    if (enabled) {
      glEnableVertexAttribArray(i);
    } else {
      glDisableVertexAttribArray(i);
    }
    vertex_attrib_arrays_enabled_[i] = enabled;
  }
}

void RendererGL::BindTextureUnit(uint32_t tex_unit) {
  assert(tex_unit >= 0 && tex_unit < kMaxGLTexUnitsUsed);
  if (active_tex_unit_ != tex_unit) {
    glActiveTexture(GL_TEXTURE0 + tex_unit);
    active_tex_unit_ = tex_unit;
  }
}

void RendererGL::BindFramebuffer(GLuint fb) {
  if (active_framebuffer_ != fb) {
    glBindFramebuffer(GL_FRAMEBUFFER, fb);
    active_framebuffer_ = fb;
  }
}

void RendererGL::BindArrayBuffer(GLuint b) {
  if (active_array_buffer_ != b) {
    glBindBuffer(GL_ARRAY_BUFFER, b);
    active_array_buffer_ = b;
  }
}

void RendererGL::BindTexture(GLuint type, const TextureData* t,
                             GLuint tex_unit) {
  if (t) {
    auto data = static_cast_check_type<TextureDataGL*>(t->renderer_data());
    BindTexture(type, data->GetTexture(), tex_unit);
  } else {
    // Fallback to noise.
    BindTexture(type, random_tex_, tex_unit);
  }
}

void RendererGL::BindTexture(GLuint type, GLuint tex, GLuint tex_unit) {
  switch (type) {
    case GL_TEXTURE_2D: {
      if (tex != bound_textures_2d_[tex_unit]) {
        BindTextureUnit(tex_unit);
        glBindTexture(type, tex);
        bound_textures_2d_[tex_unit] = tex;
      }
      break;
    }
    case GL_TEXTURE_CUBE_MAP: {
      if (tex != bound_textures_cube_map_[tex_unit]) {
        BindTextureUnit(tex_unit);
        glBindTexture(type, tex);
        bound_textures_cube_map_[tex_unit] = tex;
      }
      break;
    }
    default:
      throw Exception();
  }
}

class RendererGL::ModelDataGL : public ModelRendererData {
 public:
  enum BufferType { kVertices, kIndices, kBufferCount };

  ModelDataGL(const ModelData& model, RendererGL* renderer)
      : renderer_(renderer), fake_vao_(nullptr) {
#if BA_DEBUG_BUILD
    name_ = model.GetName();
#endif  // BA_DEBUG_BUILD

    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;

    // Create our vertex array to hold all this state (if supported).
    if (g_vao_support) {
      glGenVertexArrays(1, &vao_);
      DEBUG_CHECK_GL_ERROR;
      renderer->BindVertexArray(vao_);
      DEBUG_CHECK_GL_ERROR;
    } else {
      fake_vao_ = new FakeVertexArrayObject(renderer_);
    }

    glGenBuffers(kBufferCount, vbos_);

    DEBUG_CHECK_GL_ERROR;

    // Fill our vertex data buffer.
    renderer_->BindArrayBuffer(vbos_[kVertices]);
    DEBUG_CHECK_GL_ERROR;
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast_check_fit<GLsizeiptr>(model.vertices().size()
                                                   * sizeof(VertexObjectFull)),
                 &(model.vertices()[0]), GL_STATIC_DRAW);
    DEBUG_CHECK_GL_ERROR;

    // ..and point our array at its members.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertices], kVertexAttrPosition, 3,
                                 GL_FLOAT, GL_FALSE, sizeof(VertexObjectFull),
                                 offsetof(VertexObjectFull, position));
      fake_vao_->SetAttribBuffer(
          vbos_[kVertices], kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexObjectFull), offsetof(VertexObjectFull, uv));
      fake_vao_->SetAttribBuffer(vbos_[kVertices], kVertexAttrNormal, 3,
                                 GL_SHORT, GL_TRUE, sizeof(VertexObjectFull),
                                 offsetof(VertexObjectFull, normal));
      DEBUG_CHECK_GL_ERROR;
    } else {
      glVertexAttribPointer(
          kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexObjectFull),
          reinterpret_cast<void*>(offsetof(VertexObjectFull, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexObjectFull),
          reinterpret_cast<void*>(offsetof(VertexObjectFull, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
      glVertexAttribPointer(
          kVertexAttrNormal, 3, GL_SHORT, GL_TRUE, sizeof(VertexObjectFull),
          reinterpret_cast<void*>(offsetof(VertexObjectFull, normal)));
      glEnableVertexAttribArray(kVertexAttrNormal);
      DEBUG_CHECK_GL_ERROR;
    }

    // fill our index data buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbos_[kIndices]);
    if (!g_vao_support) {
      assert(fake_vao_);
      fake_vao_->SetElementBuffer(vbos_[kIndices]);
    }

    const GLvoid* index_data;
    switch (model.GetIndexSize()) {
      case 1: {
        elem_count_ = static_cast<uint32_t>(model.indices8().size());
        index_type_ = GL_UNSIGNED_BYTE;
        index_data = static_cast<const GLvoid*>(model.indices8().data());
        break;
      }
      case 2: {
        elem_count_ = static_cast<uint32_t>(model.indices16().size());
        index_type_ = GL_UNSIGNED_SHORT;
        index_data = static_cast<const GLvoid*>(model.indices16().data());
        break;
      }
      case 4: {
        BA_LOG_ONCE(
            "GL WARNING - USING 32 BIT INDICES WHICH WONT WORK IN ES2!!");
        elem_count_ = static_cast<uint32_t>(model.indices32().size());
        index_type_ = GL_UNSIGNED_INT;
        index_data = static_cast<const GLvoid*>(model.indices32().data());
        break;
      }
      default:
        throw Exception();
    }
    glBufferData(
        GL_ELEMENT_ARRAY_BUFFER,
        static_cast_check_fit<GLsizeiptr>(elem_count_ * model.GetIndexSize()),
        index_data, GL_STATIC_DRAW);

    DEBUG_CHECK_GL_ERROR;
  }  // ModelDataGL

  ~ModelDataGL() override {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;

    // Unbind if we're bound; otherwise if a new vao pops up with our same ID
    // it'd be prevented from binding
    if (g_vao_support) {
      if (vao_ == renderer_->current_vertex_array_) {
        renderer_->BindVertexArray(0);
      }
      if (!g_graphics_server->renderer_context_lost()) {
        glDeleteVertexArrays(1, &vao_);
      }
    } else {
      assert(fake_vao_);
      delete fake_vao_;
      fake_vao_ = nullptr;
    }
    // make sure our dying buffer isn't current..
    // (don't wanna prevent binding to a new buffer with a recycled id)
    for (unsigned int vbo : vbos_) {
      if (vbo == renderer_->active_array_buffer_) {
        renderer_->active_array_buffer_ = -1;
      }
    }
    if (!g_graphics_server->renderer_context_lost()) {
      glDeleteBuffers(kBufferCount, vbos_);
      DEBUG_CHECK_GL_ERROR;
    }
  }

  void Bind() {
    if (g_vao_support) {
      renderer_->BindVertexArray(vao_);
      DEBUG_CHECK_GL_ERROR;
    } else {
      assert(fake_vao_);
      fake_vao_->Bind();
      DEBUG_CHECK_GL_ERROR;
    }
  }
  void Draw() {
    DEBUG_CHECK_GL_ERROR;
    if (elem_count_ > 0) {
      glDrawElements(GL_TRIANGLES, elem_count_, index_type_, nullptr);
    }
    DEBUG_CHECK_GL_ERROR;
  }

#if BA_DEBUG_BUILD
  auto name() const -> const std::string& { return name_; }
#endif

 private:
#if BA_DEBUG_BUILD
  std::string name_;
#endif

  RendererGL* renderer_{};
  uint32_t elem_count_{};
  GLuint index_type_{};
  GLuint vao_{};
  GLuint vbos_[kBufferCount]{};
  FakeVertexArrayObject* fake_vao_{};
};  // ModelDataGL

class RendererGL::MeshDataGL : public MeshRendererData {
 public:
  enum BufferType {
    kVertexBufferPrimary,
    kIndexBuffer,
    kVertexBufferSecondary
  };
  enum Flags {
    kUsesIndexBuffer = 1u,
    kUsesSecondaryBuffer = 1u << 1u,
    kUsesDynamicDraw = 1u << 2u
  };
  MeshDataGL(RendererGL* renderer, uint32_t flags)
      : renderer_(renderer),
        uses_secondary_data_(static_cast<bool>(flags & kUsesSecondaryBuffer)),
        uses_index_data_(static_cast<bool>(flags & kUsesIndexBuffer)) {
    assert(InGraphicsThread());

    // Create our vertex array to hold all this state.
    if (g_vao_support) {
      glGenVertexArrays(1, &vao_);
      renderer->BindVertexArray(vao_);
    } else {
      fake_vao_ = new FakeVertexArrayObject(renderer_);
    }
    glGenBuffers(GetBufferCount(), vbos_);
  }
  auto uses_index_data() const -> bool { return uses_index_data_; }

  // Set us up to be recycled.
  void Reset() {
    index_state_ = primary_state_ = secondary_state_ = 0;
    have_index_data_ = have_secondary_data_ = have_primary_data_ = false;
  }

  void Bind() {
    if (g_vao_support) {
      renderer_->BindVertexArray(vao_);
      DEBUG_CHECK_GL_ERROR;
    } else {
      assert(fake_vao_);
      fake_vao_->Bind();
      DEBUG_CHECK_GL_ERROR;
    }
  }

  void Draw(DrawType draw_type) {
    DEBUG_CHECK_GL_ERROR;
    assert(have_primary_data_);
    assert(have_index_data_ || !uses_index_data_);
    assert(have_secondary_data_ || !uses_secondary_data_);
    GLuint gl_draw_type;
    switch (draw_type) {
      case DrawType::kTriangles:
        gl_draw_type = GL_TRIANGLES;
        break;
      case DrawType::kPoints:
        gl_draw_type = GL_POINTS;
        break;
      default:
        throw Exception();
    }
    if (uses_index_data_) {
      glDrawElements(gl_draw_type, elem_count_, index_type_, nullptr);
    } else {
      glDrawArrays(gl_draw_type, 0, elem_count_);
    }
    DEBUG_CHECK_GL_ERROR;
  }

  ~MeshDataGL() override {
    assert(InGraphicsThread());
    // unbind if we're bound .. otherwise we might prevent a new with our ID
    // from binding
    if (g_vao_support) {
      if (vao_ == renderer_->current_vertex_array_) {
        renderer_->BindVertexArray(0);
      }
      if (!g_graphics_server->renderer_context_lost()) {
        glDeleteVertexArrays(1, &vao_);
      }
    } else {
      assert(fake_vao_);
      delete fake_vao_;
      fake_vao_ = nullptr;
    }
    // make sure our dying buffer isn't current..
    // (don't wanna prevent binding to a new buffer with a recycled id)
    for (int i = 0; i < GetBufferCount(); i++) {
      if (vbos_[i] == renderer_->active_array_buffer_) {
        renderer_->active_array_buffer_ = -1;
      }
    }
    if (!g_graphics_server->renderer_context_lost()) {
      glDeleteBuffers(GetBufferCount(), vbos_);
      DEBUG_CHECK_GL_ERROR;
    }
  }

  void SetIndexData(MeshIndexBuffer32* data) {
    assert(uses_index_data_);
    if (data->state != index_state_) {
      if (g_vao_support) {
        renderer_->BindVertexArray(vao_);
      } else {
        assert(fake_vao_);
        fake_vao_->SetElementBuffer(vbos_[kIndexBuffer]);
      }
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbos_[kIndexBuffer]);
      elem_count_ = static_cast<uint32_t>(data->elements.size());
      assert(elem_count_ > 0);
      glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                   static_cast_check_fit<GLsizeiptr>(
                       data->elements.size() * sizeof(data->elements[0])),
                   &data->elements[0],
                   dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
      index_state_ = data->state;
      have_index_data_ = true;
      BA_LOG_ONCE("GL WARNING - USING 32 BIT INDICES WHICH WONT WORK IN ES2!!");
      index_type_ = GL_UNSIGNED_INT;
    }
  }
  void SetIndexData(MeshIndexBuffer16* data) {
    assert(uses_index_data_);
    if (data->state != index_state_) {
      if (g_vao_support) {
        renderer_->BindVertexArray(vao_);
      } else {
        assert(fake_vao_);
        fake_vao_->SetElementBuffer(vbos_[kIndexBuffer]);
      }
      glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbos_[kIndexBuffer]);
      elem_count_ = static_cast<uint32_t>(data->elements.size());
      assert(elem_count_ > 0);
      glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                   static_cast_check_fit<GLsizeiptr>(
                       data->elements.size() * sizeof(data->elements[0])),
                   &data->elements[0],
                   dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
      index_state_ = data->state;
      have_index_data_ = true;
      index_type_ = GL_UNSIGNED_SHORT;
    }
  }

  // When dynamic-draw is on, it means *all* buffers should be flagged as
  // dynamic.
  void set_dynamic_draw(bool enable) { dynamic_draw_ = enable; }

  auto vao() const -> GLuint { return vao_; }

 protected:
  template <typename T>
  void UpdateBufferData(BufferType buffer_type, MeshBuffer<T>* data,
                        uint32_t* state, bool* have, GLuint draw_type) {
    assert(state && have);
    if (data->state != *state) {
      DEBUG_CHECK_GL_ERROR;

      // Hmmm didnt think we had to have vao bound here but causes problems on
      // qualcomm if not.
#if BA_OSTYPE_ANDROID
      if (g_vao_support && renderer_->is_adreno_) {
        renderer_->BindVertexArray(vao_);
      }
#endif
      renderer_->BindArrayBuffer(vbos_[buffer_type]);
      assert(!data->elements.empty());
      if (!uses_index_data_ && buffer_type == kVertexBufferPrimary) {
        elem_count_ = static_cast<uint32_t>(data->elements.size());
      }
      glBufferData(GL_ARRAY_BUFFER,
                   static_cast<GLsizeiptr>(data->elements.size()
                                           * sizeof(data->elements[0])),
                   &(data->elements[0]), draw_type);
      DEBUG_CHECK_GL_ERROR;
      *state = data->state;
      *have = true;
    } else {
      assert(*have);
    }
  }

  // FIXME - we should do some sort of ring-buffer system.
  GLuint vbos_[3]{};
  GLuint vao_{};
  auto GetBufferCount() const -> int {
    return uses_secondary_data_ ? 3 : (uses_index_data_ ? 2 : 1);
  }
  bool uses_index_data_{};
  bool uses_secondary_data_{};
  uint32_t index_state_{};
  uint32_t primary_state_{};
  uint32_t secondary_state_{};
  bool dynamic_draw_{};
  bool have_index_data_{};
  bool have_primary_data_{};
  bool have_secondary_data_{};
  RendererGL* renderer_{};
  uint32_t elem_count_{};
  GLuint index_type_{GL_UNSIGNED_SHORT};
  FakeVertexArrayObject* fake_vao_{};
};  // MeshDataGL

class RendererGL::MeshDataSimpleSplitGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataSimpleSplitGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesSecondaryBuffer | kUsesIndexBuffer) {
    // Set up our static vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrUV, 2,
                                 GL_UNSIGNED_SHORT, GL_TRUE,
                                 sizeof(VertexSimpleSplitStatic),
                                 offsetof(VertexSimpleSplitStatic, uv));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexSimpleSplitStatic),
          reinterpret_cast<void*>(offsetof(VertexSimpleSplitStatic, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
    }

    // ..and our dynamic vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferSecondary],
                                 kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                                 sizeof(VertexSimpleSplitDynamic),
                                 offsetof(VertexSimpleSplitDynamic, position));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferSecondary]);
      glVertexAttribPointer(kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                            sizeof(VertexSimpleSplitDynamic),
                            reinterpret_cast<void*>(
                                offsetof(VertexSimpleSplitDynamic, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
    }
  }
  void SetStaticData(MeshBuffer<VertexSimpleSplitStatic>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_, GL_STATIC_DRAW);
  }
  void SetDynamicData(MeshBuffer<VertexSimpleSplitDynamic>* data) {
    assert(uses_secondary_data_);
    UpdateBufferData(kVertexBufferSecondary, data, &secondary_state_,
                     &have_secondary_data_,
                     GL_DYNAMIC_DRAW);  // this is *always* dynamic
  }
};

class RendererGL::MeshDataObjectSplitGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataObjectSplitGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesSecondaryBuffer | kUsesIndexBuffer) {
    // Set up our static vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrUV, 2,
                                 GL_UNSIGNED_SHORT, GL_TRUE,
                                 sizeof(VertexObjectSplitStatic),
                                 offsetof(VertexObjectSplitStatic, uv));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexObjectSplitStatic),
          reinterpret_cast<void*>(offsetof(VertexObjectSplitStatic, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
    }

    // ..and our dynamic vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferSecondary],
                                 kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                                 sizeof(VertexObjectSplitDynamic),
                                 offsetof(VertexObjectSplitDynamic, position));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferSecondary],
                                 kVertexAttrNormal, 3, GL_SHORT, GL_TRUE,
                                 sizeof(VertexObjectSplitDynamic),
                                 offsetof(VertexObjectSplitDynamic, normal));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferSecondary]);
      glVertexAttribPointer(kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                            sizeof(VertexObjectSplitDynamic),
                            reinterpret_cast<void*>(
                                offsetof(VertexObjectSplitDynamic, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
      glVertexAttribPointer(
          kVertexAttrNormal, 3, GL_SHORT, GL_TRUE,
          sizeof(VertexObjectSplitDynamic),
          reinterpret_cast<void*>(offsetof(VertexObjectSplitDynamic, normal)));
      glEnableVertexAttribArray(kVertexAttrNormal);
    }
  }
  void SetStaticData(MeshBuffer<VertexObjectSplitStatic>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_, GL_STATIC_DRAW);
  }
  void SetDynamicData(MeshBuffer<VertexObjectSplitDynamic>* data) {
    assert(uses_secondary_data_);
    UpdateBufferData(kVertexBufferSecondary, data, &secondary_state_,
                     &have_secondary_data_,
                     GL_DYNAMIC_DRAW);  // this is *always* dynamic
  }
};

class RendererGL::MeshDataSimpleFullGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataSimpleFullGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(
          vbos_[kVertexBufferPrimary], kVertexAttrUV, 2, GL_UNSIGNED_SHORT,
          GL_TRUE, sizeof(VertexSimpleFull), offsetof(VertexSimpleFull, uv));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary],
                                 kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                                 sizeof(VertexSimpleFull),
                                 offsetof(VertexSimpleFull, position));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexSimpleFull),
          reinterpret_cast<void*>(offsetof(VertexSimpleFull, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
      glVertexAttribPointer(
          kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexSimpleFull),
          reinterpret_cast<void*>(offsetof(VertexSimpleFull, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
    }
  }
  void SetData(MeshBuffer<VertexSimpleFull>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};

class RendererGL::MeshDataDualTextureFullGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataDualTextureFullGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrUV, 2,
                                 GL_UNSIGNED_SHORT, GL_TRUE,
                                 sizeof(VertexDualTextureFull),
                                 offsetof(VertexDualTextureFull, uv));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrUV2, 2,
                                 GL_UNSIGNED_SHORT, GL_TRUE,
                                 sizeof(VertexDualTextureFull),
                                 offsetof(VertexDualTextureFull, uv2));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary],
                                 kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                                 sizeof(VertexDualTextureFull),
                                 offsetof(VertexDualTextureFull, position));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexDualTextureFull),
          reinterpret_cast<void*>(offsetof(VertexDualTextureFull, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
      glVertexAttribPointer(
          kVertexAttrUV2, 2, GL_UNSIGNED_SHORT, GL_TRUE,
          sizeof(VertexDualTextureFull),
          reinterpret_cast<void*>(offsetof(VertexDualTextureFull, uv2)));
      glEnableVertexAttribArray(kVertexAttrUV2);
      glVertexAttribPointer(
          kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
          sizeof(VertexDualTextureFull),
          reinterpret_cast<void*>(offsetof(VertexDualTextureFull, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
    }
  }
  void SetData(MeshBuffer<VertexDualTextureFull>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};

class RendererGL::MeshDataSmokeFullGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataSmokeFullGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrUV, 2,
                                 GL_FLOAT, GL_FALSE, sizeof(VertexSmokeFull),
                                 offsetof(VertexSmokeFull, uv));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary],
                                 kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE,
                                 sizeof(VertexSmokeFull),
                                 offsetof(VertexSmokeFull, position));
      fake_vao_->SetAttribBuffer(
          vbos_[kVertexBufferPrimary], kVertexAttrErode, 1, GL_UNSIGNED_BYTE,
          GL_TRUE, sizeof(VertexSmokeFull), offsetof(VertexSmokeFull, erode));
      fake_vao_->SetAttribBuffer(
          vbos_[kVertexBufferPrimary], kVertexAttrDiffuse, 1, GL_UNSIGNED_BYTE,
          GL_TRUE, sizeof(VertexSmokeFull), offsetof(VertexSmokeFull, diffuse));
      fake_vao_->SetAttribBuffer(
          vbos_[kVertexBufferPrimary], kVertexAttrColor, 4, GL_UNSIGNED_BYTE,
          GL_TRUE, sizeof(VertexSmokeFull), offsetof(VertexSmokeFull, color));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_FLOAT, GL_FALSE, sizeof(VertexSmokeFull),
          reinterpret_cast<void*>(offsetof(VertexSmokeFull, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
      glVertexAttribPointer(
          kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexSmokeFull),
          reinterpret_cast<void*>(offsetof(VertexSmokeFull, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
      glVertexAttribPointer(
          kVertexAttrErode, 1, GL_UNSIGNED_BYTE, GL_TRUE,
          sizeof(VertexSmokeFull),
          reinterpret_cast<void*>(offsetof(VertexSmokeFull, erode)));
      glEnableVertexAttribArray(kVertexAttrErode);
      glVertexAttribPointer(
          kVertexAttrDiffuse, 1, GL_UNSIGNED_BYTE, GL_TRUE,
          sizeof(VertexSmokeFull),
          reinterpret_cast<void*>(offsetof(VertexSmokeFull, diffuse)));
      glEnableVertexAttribArray(kVertexAttrDiffuse);
      glVertexAttribPointer(
          kVertexAttrColor, 4, GL_UNSIGNED_BYTE, GL_TRUE,
          sizeof(VertexSmokeFull),
          reinterpret_cast<void*>(offsetof(VertexSmokeFull, color)));
      glEnableVertexAttribArray(kVertexAttrColor);
    }
  }
  void SetData(MeshBuffer<VertexSmokeFull>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};

class RendererGL::MeshDataSpriteGL : public RendererGL::MeshDataGL {
 public:
  explicit MeshDataSpriteGL(RendererGL* renderer)
      : MeshDataGL(renderer, kUsesIndexBuffer) {
    // Set up our vertex data.
    if (fake_vao_) {
      fake_vao_->SetAttribBuffer(
          vbos_[kVertexBufferPrimary], kVertexAttrPosition, 3, GL_FLOAT,
          GL_FALSE, sizeof(VertexSprite), offsetof(VertexSprite, position));
      fake_vao_->SetAttribBuffer(
          vbos_[kVertexBufferPrimary], kVertexAttrUV, 2, GL_UNSIGNED_SHORT,
          GL_TRUE, sizeof(VertexSprite), offsetof(VertexSprite, uv));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrSize,
                                 1, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
                                 offsetof(VertexSprite, size));
      fake_vao_->SetAttribBuffer(vbos_[kVertexBufferPrimary], kVertexAttrColor,
                                 4, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
                                 offsetof(VertexSprite, color));
    } else {
      renderer_->BindArrayBuffer(vbos_[kVertexBufferPrimary]);
      glVertexAttribPointer(
          kVertexAttrPosition, 3, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
          reinterpret_cast<void*>(offsetof(VertexSprite, position)));
      glEnableVertexAttribArray(kVertexAttrPosition);
      glVertexAttribPointer(
          kVertexAttrUV, 2, GL_UNSIGNED_SHORT, GL_TRUE, sizeof(VertexSprite),
          reinterpret_cast<void*>(offsetof(VertexSprite, uv)));
      glEnableVertexAttribArray(kVertexAttrUV);
      glVertexAttribPointer(
          kVertexAttrSize, 1, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
          reinterpret_cast<void*>(offsetof(VertexSprite, size)));
      glEnableVertexAttribArray(kVertexAttrSize);
      glVertexAttribPointer(
          kVertexAttrColor, 4, GL_FLOAT, GL_FALSE, sizeof(VertexSprite),
          reinterpret_cast<void*>(offsetof(VertexSprite, color)));
      glEnableVertexAttribArray(kVertexAttrColor);
    }
  }
  void SetData(MeshBuffer<VertexSprite>* data) {
    UpdateBufferData(kVertexBufferPrimary, data, &primary_state_,
                     &have_primary_data_,
                     dynamic_draw_ ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW);
  }
};

class RendererGL::RenderTargetGL : public RenderTarget {
 public:
  void Bind() {
    if (type_ == Type::kFramebuffer) {
      assert(framebuffer_.exists());
      framebuffer_->Bind();
    } else {
      assert(type_ == Type::kScreen);
      renderer_->BindFramebuffer(renderer_->screen_framebuffer_);
    }
  }

  void DrawBegin(bool must_clear_color, float clear_r, float clear_g,
                 float clear_b, float clear_a) override {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;

    Bind();

#if BA_CARDBOARD_BUILD
    int x, y;
    // viewport offsets only apply to the screen render-target
    if (type_ == Type::kScreen) {
      x = renderer_->VRGetViewportX();
      y = renderer_->VRGetViewportY();
    } else {
      x = 0;
      y = 0;
    }
    renderer_->SetViewport(x, y, physical_width_, physical_height_);
#else
    renderer_->SetViewport(0, 0, static_cast<GLsizei>(physical_width_),
                           static_cast<GLsizei>(physical_height_));
#endif

    {
      // Clear depth, color, etc.
      GLuint clear_mask = 0;

      // If they *requested* a clear for color, do so. Otherwise invalidate.
      if (must_clear_color) {
        clear_mask |= GL_COLOR_BUFFER_BIT;
      } else {
        renderer_->InvalidateFramebuffer(true, false, false);
      }

      if (depth_) {
        // FIXME make sure depth writing is turned on at this point.
        //  this needs to be on for glClear to work on depth.
        if (!renderer_->depth_writing_enabled_) {
          BA_LOG_ONCE(
              "RendererGL: depth-writing not enabled when clearing depth");
        }
        clear_mask |= GL_DEPTH_BUFFER_BIT;
      }

      if (clear_mask != 0) {
        if (clear_mask & GL_COLOR_BUFFER_BIT) {
          glClearColor(clear_r, clear_g, clear_b, clear_a);
          DEBUG_CHECK_GL_ERROR;
        }
        glClear(clear_mask);
        DEBUG_CHECK_GL_ERROR;
      }
    }
  }

  auto GetFramebufferID() -> GLuint {
    if (type_ == Type::kFramebuffer) {
      assert(framebuffer_.exists());
      return framebuffer_->id();
    } else {
      return 0;  // screen
    }
  }
  auto framebuffer() -> FramebufferObjectGL* {
    assert(type_ == Type::kFramebuffer);
    return framebuffer_.get();
  }
  // Screen.
  explicit RenderTargetGL(RendererGL* renderer)
      : RenderTarget(Type::kScreen), renderer_(renderer) {
    assert(InGraphicsThread());
    depth_ = true;

    // This will update our width/height values.
    ScreenSizeChanged();
  }

  // Framebuffer.
  RenderTargetGL(RendererGL* renderer, int width, int height,
                 bool linear_interp, bool depth, bool texture,
                 bool depth_texture, bool high_quality, bool msaa, bool alpha)
      : RenderTarget(Type::kFramebuffer), renderer_(renderer) {
    assert(InGraphicsThread());
    DEBUG_CHECK_GL_ERROR;
    framebuffer_ = Object::New<FramebufferObjectGL>(
        renderer, width, height, linear_interp, depth, texture, depth_texture,
        high_quality, msaa, alpha);
    physical_width_ = static_cast<float>(width);
    physical_height_ = static_cast<float>(height);
    depth_ = depth;
    DEBUG_CHECK_GL_ERROR;
  }

 private:
  Object::Ref<FramebufferObjectGL> framebuffer_;
  RendererGL* renderer_{};
  friend class RenderPass;
};  // RenderTargetGL

RendererGL::RendererGL() {
  if (explicit_bool(FORCE_CHECK_GL_ERRORS)) {
    ScreenMessage("GL ERROR CHECKS ENABLED");
  }

  // For some reason we're getting an immediately
  // GL_INVALID_FRAMEBUFFER_OPERATION on EL-CAPITAN, though we shouldn't have
  // run any gl code yet. might be worth looking into at some point, but gonna
  // ignore for now.
#if BA_OSTYPE_MACOS
  glGetError();
#endif  // BA_OSTYPE_MACOS

  assert(InGraphicsThread());
  DEBUG_CHECK_GL_ERROR;

  SyncGLState();
  DEBUG_CHECK_GL_ERROR;
}

void RendererGL::CheckFunkyDepthIssue() {
  if (funky_depth_issue_set_) {
    return;
  }

  // Note: this test fails for some reason on some Broadcom VideoCore and older
  // NVidia chips (tegra 2?)
  // ...so lets limit testing to adreno chips since that's the only place the
  // problem is known to happen.
  if (!is_adreno_ || !supports_depth_textures_) {
    funky_depth_issue_set_ = true;
    funky_depth_issue_ = false;
    return;
  }

  // on some adreno chips, depth buffer values are always returned
  // in a 0-1 range in shaders even if a depth range is set; everywhere
  // else they return that depth range.
  // to test for this we can create a temp buffer, clear it, set a depth range,
  // Log("RUNNING DEPTH TEST");

  Object::Ref<RenderTargetGL> test_rt1;
  Object::Ref<RenderTargetGL> test_rt2;

  test_rt1 = Object::New<RenderTargetGL>(this, 32, 32, true, true, true, true,
                                         false, false, false);
  DEBUG_CHECK_GL_ERROR;
  test_rt2 = Object::New<RenderTargetGL>(this, 32, 32, true, false, true, false,
                                         false, false, false);
  DEBUG_CHECK_GL_ERROR;

  // this screws up some qualcomm chips..
  SetDepthRange(0.0f, 0.5f);

  // draw a flat color plane into our first render target
  SetDepthWriting(true);
  SetDepthTesting(true);
  SetBlend(false);
  SetDoubleSided(false);
  test_rt1->DrawBegin(true, 1.0f, 1.0f, 1.0f, 1.0f);
  SimpleProgramGL* p = simple_color_prog_;
  p->Bind();
  p->SetColor(1, 0, 1);
  g_graphics_server->ModelViewReset();
  g_graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);
  GetActiveProgram()->PrepareToDraw();
  screen_mesh_->Bind();
  screen_mesh_->Draw(DrawType::kTriangles);
  DEBUG_CHECK_GL_ERROR;

  // now draw into a second buffer the difference between the
  // depth tex lookup and the gl frag depth.
  SetDepthWriting(false);
  SetDepthTesting(false);
  SetBlend(false);
  SetDoubleSided(false);
  test_rt2->DrawBegin(false, 1.0f, 1.0f, 1.0f, 1.0f);
  p = simple_tex_dtest_prog_;
  p->Bind();
  g_graphics_server->ModelViewReset();
  g_graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);
  p->SetColorTexture(test_rt1->framebuffer()->depth_texture());
  GetActiveProgram()->PrepareToDraw();
  screen_mesh_->Bind();
  screen_mesh_->Draw(DrawType::kTriangles);
  DEBUG_CHECK_GL_ERROR;

  // now sample a pixel from our render-target
  // if the depths matched, the value will be 0; otherwise it'll be 30 or so
  // (allow a bit of leeway to account for dithering/etc..)
  uint8_t buffer[16] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  glReadPixels(0, 0, 2, 2, GL_RGBA, GL_UNSIGNED_BYTE, buffer);

  // sample 4 pixels to reduce effects of dithering..
  funky_depth_issue_ =
      ((buffer[0] + buffer[4] + buffer[8] + buffer[12]) / 4 >= 15);
  funky_depth_issue_set_ = true;

  DEBUG_CHECK_GL_ERROR;
}

void RendererGL::PushGroupMarker(const char* label) {
  GL_PUSH_GROUP_MARKER(label);
}
void RendererGL::PopGroupMarker() { GL_POP_GROUP_MARKER(); }

void RendererGL::InvalidateFramebuffer(bool color, bool depth,
                                       bool target_read_framebuffer) {
  DEBUG_CHECK_GL_ERROR;

  // currently discard is mobile only
#if BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID

  if (g_discard_framebuffer_support || g_invalidate_framebuffer_support) {
    GLenum attachments[5];
    // need to use different flags for the main framebuffer..
    int count = 0;
    if (active_framebuffer_ == 0 && !target_read_framebuffer) {
      if (color) {
        attachments[count++] = GL_COLOR_EXT;
      }
      if (depth) {
        attachments[count++] = GL_DEPTH_EXT;
      }
    } else {
      if (color) {
        attachments[count++] = GL_COLOR_ATTACHMENT0;
      }
      if (depth) {
        attachments[count++] = GL_DEPTH_ATTACHMENT;
      }
    }
    // apparently the oculus docs say glInvalidateFramebuffer errors
    // on a mali es3 implementation so they always use glDiscard when present...
    if (g_invalidate_framebuffer_support) {
#if BA_OSTYPE_IOS_TVOS
      throw Exception();  // shouldnt happen
#else
      glInvalidateFramebuffer(
          target_read_framebuffer ? GL_READ_FRAMEBUFFER : GL_FRAMEBUFFER, count,
          attachments);
#endif
    } else {
      // if we've got a read-framebuffer we should have invalidate too..
      assert(!target_read_framebuffer);
      glDiscardFramebufferEXT(GL_FRAMEBUFFER, count, attachments);
    }
    DEBUG_CHECK_GL_ERROR;
  }
#endif  // BA_OSTYPE_IOS_TVOS || BA_OSTYPE_ANDROID
}

RendererGL::~RendererGL() {
  assert(InGraphicsThread());
  printf("FIXME: need to unload renderer on destroy.\n");
  // Unload();
  DEBUG_CHECK_GL_ERROR;
}

void RendererGL::UseProgram(ProgramGL* p) {
  if (p != current_program_) {
    glUseProgram(p->program());
    current_program_ = p;
  }
}

void RendererGL::SyncGLState() {
#if BA_RIFT_BUILD
  if (IsVRMode()) {
    glFrontFace(GL_CCW);
  }

  // if (time(nullptr)%2 == 0) {
  //   glEnable(GL_FRAMEBUFFER_SRGB);
  // } else {
  //   glDisable(GL_FRAMEBUFFER_SRGB);
  // }
#endif  // BA_RIFT_BUILD

  active_tex_unit_ = -1;      // force a set next time
  active_framebuffer_ = -1;   // ditto
  active_array_buffer_ = -1;  // ditto
  for (int i = 0; i < kMaxGLTexUnitsUsed; i++) {
    bound_textures_2d_[i] = -1;        // ditto
    bound_textures_cube_map_[i] = -1;  // ditto
  }
  glUseProgram(0);
  current_program_ = nullptr;
  current_vertex_array_ = 0;

  if (g_vao_support) {
    glBindVertexArray(0);
  } else {
    for (GLuint i = 0; i < kVertexAttrCount; i++) {
      glDisableVertexAttribArray(i);
      vertex_attrib_arrays_enabled_[i] = false;
    }
  }

  // wack these out so the next call will definitely call glViewport
  viewport_x_ = -9999;
  viewport_y_ = -9999;
  viewport_width_ = -9999;
  viewport_height_ = -9999;

  glDisable(GL_BLEND);
  blend_ = false;

  // currently we only ever write to an alpha buffer for our vr flat overlay
  // texture, and in that case we need alpha to accumulate; not get overwritten.
  // could probably enable this everywhere but I don't know if it's supported on
  // all hardware or slower..
  if (IsVRMode()) {
#if BA_OSTYPE_WINDOWS
    if (glBlendFuncSeparate == nullptr) {
      throw Exception(
          "VR mode is not supported by your GPU (no glBlendFuncSeparate); Try "
          "updating your drivers?...");
    }
#endif  // BA_WINDOWS_BUILD
    glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE,
                        GL_ONE_MINUS_SRC_ALPHA);
  } else {
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
  }
  blend_premult_ = false;
  glEnable(GL_CULL_FACE);
  glCullFace(GL_BACK);
  double_sided_ = false;
  draw_front_ = true;
  glDisable(GL_DEPTH_TEST);
  depth_testing_enabled_ = false;
  glDepthMask(static_cast<GLboolean>(true));
  depth_writing_enabled_ = true;
  draw_at_equal_depth_ = false;
  glDepthFunc(GL_LESS);
  depth_range_min_ = 0.0f;
  depth_range_max_ = 1.0f;
  glDepthRange(depth_range_min_, depth_range_max_);
}

#define GET_MESH_DATA(TYPE, VAR)                              \
  auto* VAR = static_cast<TYPE*>(mesh_data->renderer_data()); \
  assert(VAR&& VAR == dynamic_cast<TYPE*>(mesh_data->renderer_data()))

#define GET_INDEX_BUFFER()                                      \
  assert(buffer != buffers.end());                              \
  assert(index_size != index_sizes.end());                      \
  MeshIndexBuffer16* indices16{nullptr};                        \
  MeshIndexBuffer32* indices32{nullptr};                        \
  assert(*index_size == 4 || *index_size == 2);                 \
  bool use_indices32 = (*index_size == 4);                      \
  if (use_indices32) {                                          \
    indices32 = static_cast<MeshIndexBuffer32*>(buffer->get()); \
    assert(indices32&& indices32                                \
           == dynamic_cast<MeshIndexBuffer32*>(buffer->get())); \
  } else {                                                      \
    indices16 = static_cast<MeshIndexBuffer16*>(buffer->get()); \
    assert(indices16&& indices16                                \
           == dynamic_cast<MeshIndexBuffer16*>(buffer->get())); \
  }                                                             \
  index_size++;                                                 \
  buffer++

#define GET_BUFFER(TYPE, VAR)                              \
  assert(buffer != buffers.end());                         \
  auto* VAR = static_cast<TYPE*>(buffer->get());           \
  assert(VAR&& VAR == dynamic_cast<TYPE*>(buffer->get())); \
  buffer++

// Takes all latest mesh data from the client side and applies it
// to our gl implementations.
void RendererGL::UpdateMeshes(
    const std::vector<Object::Ref<MeshDataClientHandle> >& meshes,
    const std::vector<int8_t>& index_sizes,
    const std::vector<Object::Ref<MeshBufferBase> >& buffers) {
  auto index_size = index_sizes.begin();
  auto buffer = buffers.begin();
  for (auto&& mesh : meshes) {
    // For each mesh, plug in the latest and greatest buffers it
    // should be using.
    MeshData* mesh_data = mesh->mesh_data;
    switch (mesh_data->type()) {
      case MeshDataType::kIndexedSimpleSplit: {
        GET_MESH_DATA(MeshDataSimpleSplitGL, m);
        GET_INDEX_BUFFER();
        GET_BUFFER(MeshBuffer<VertexSimpleSplitStatic>, static_data);
        GET_BUFFER(MeshBuffer<VertexSimpleSplitDynamic>, dynamic_data);
        if (use_indices32) {
          m->SetIndexData(indices32);
        } else {
          m->SetIndexData(indices16);
        }
        m->SetStaticData(static_data);
        m->SetDynamicData(dynamic_data);
        break;
      }
      case MeshDataType::kIndexedObjectSplit: {
        GET_MESH_DATA(MeshDataObjectSplitGL, m);
        GET_INDEX_BUFFER();
        GET_BUFFER(MeshBuffer<VertexObjectSplitStatic>, static_data);
        GET_BUFFER(MeshBuffer<VertexObjectSplitDynamic>, dynamic_data);
        if (use_indices32) {
          m->SetIndexData(indices32);
        } else {
          m->SetIndexData(indices16);
        }
        m->SetStaticData(static_data);
        m->SetDynamicData(dynamic_data);
        break;
      }
      case MeshDataType::kIndexedSimpleFull: {
        GET_MESH_DATA(MeshDataSimpleFullGL, m);
        GET_INDEX_BUFFER();
        GET_BUFFER(MeshBuffer<VertexSimpleFull>, data);
        if (use_indices32) {
          m->SetIndexData(indices32);
        } else {
          m->SetIndexData(indices16);
        }
        m->SetData(data);
        break;
      }
      case MeshDataType::kIndexedDualTextureFull: {
        GET_MESH_DATA(MeshDataDualTextureFullGL, m);
        GET_INDEX_BUFFER();
        GET_BUFFER(MeshBuffer<VertexDualTextureFull>, data);
        if (use_indices32) {
          m->SetIndexData(indices32);
        } else {
          m->SetIndexData(indices16);
        }
        m->SetData(data);
        break;
      }
      case MeshDataType::kIndexedSmokeFull: {
        GET_MESH_DATA(MeshDataSmokeFullGL, m);
        GET_INDEX_BUFFER();
        GET_BUFFER(MeshBuffer<VertexSmokeFull>, data);
        if (use_indices32) {
          m->SetIndexData(indices32);
        } else {
          m->SetIndexData(indices16);
        }
        m->SetData(data);
        break;
      }
      case MeshDataType::kSprite: {
        GET_MESH_DATA(MeshDataSpriteGL, m);
        GET_INDEX_BUFFER();
        GET_BUFFER(MeshBuffer<VertexSprite>, data);
        if (use_indices32) {
          m->SetIndexData(indices32);
        } else {
          m->SetIndexData(indices16);
        }
        m->SetData(data);
        break;
      }
      default:
        throw Exception("Invalid meshdata type: "
                        + std::to_string(static_cast<int>(mesh_data->type())));
    }
  }
  // We should have gone through all lists exactly..
  assert(index_size == index_sizes.end());
  assert(buffer == buffers.end());
}
#undef GET_MESH_DATA
#undef GET_BUFFER
#undef GET_INDEX_BUFFER

void RendererGL::StandardPostProcessSetup(PostProcessProgramGL* p,
                                          const RenderPass& pass) {
  auto* cam_target = static_cast<RenderTargetGL*>(camera_render_target());
  assert(cam_target
         && dynamic_cast<RenderTargetGL*>(camera_render_target())
                == cam_target);
  RenderPass* beauty_pass = pass.frame_def()->beauty_pass();
  assert(beauty_pass);
  SetDoubleSided(false);
  SetBlend(false);
  p->Bind();
  p->SetColorTexture(cam_target->framebuffer()->texture());
  if (p->UsesSlightBlurredTex()) {
    p->SetColorSlightBlurredTexture(blur_buffers_[0]->texture());
  }
  if (blur_buffers_.size() > 1) {
    if (p->UsesBlurredTexture()) {
      p->SetColorBlurredTexture(blur_buffers_[1]->texture());
    }
    p->SetColorBlurredMoreTexture(
        blur_buffers_[blur_buffers_.size() - 1]->texture());
  } else {
    if (p->UsesBlurredTexture()) {
      p->SetColorBlurredTexture(blur_buffers_[0]->texture());
    }
    p->SetColorBlurredMoreTexture(blur_buffers_[0]->texture());
  }
  p->SetDepthTexture(cam_target->framebuffer()->depth_texture());
  float dof_near_smoothed = this->dof_near_smoothed();
  float dof_far_smoothed = this->dof_far_smoothed();
  if (pass.frame_def()->orbiting()) {
    p->SetDepthOfFieldRanges(
        GetZBufferValue(beauty_pass, 0.80f * dof_near_smoothed),
        GetZBufferValue(beauty_pass, 0.91f * dof_near_smoothed),
        GetZBufferValue(beauty_pass, 1.01f * dof_far_smoothed),
        GetZBufferValue(beauty_pass, 1.10f * dof_far_smoothed));
  } else {
    p->SetDepthOfFieldRanges(
        GetZBufferValue(beauty_pass, 0.93f * dof_near_smoothed),
        GetZBufferValue(beauty_pass, 0.99f * dof_near_smoothed),
        GetZBufferValue(beauty_pass, 1.03f * dof_far_smoothed),
        GetZBufferValue(beauty_pass, 1.09f * dof_far_smoothed));
  }
}

void RendererGL::ProcessRenderCommandBuffer(RenderCommandBuffer* buffer,
                                            const RenderPass& pass,
                                            RenderTarget* render_target) {
  buffer->ReadBegin();
  RenderCommandBuffer::Command cmd;
  while ((cmd = buffer->GetCommand()) != RenderCommandBuffer::Command::kEnd) {
    switch (cmd) {
      case RenderCommandBuffer::Command::kEnd:
        break;
      case RenderCommandBuffer::Command::kShader: {
        auto shader = static_cast<ShadingType>(buffer->GetInt());
        switch (shader) {
          case ShadingType::kSimpleColor: {
            SetDoubleSided(false);
            SetBlend(false);
            SimpleProgramGL* p = simple_color_prog_;
            p->Bind();
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            p->SetColor(r, g, b);
            break;
          }
          case ShadingType::kSimpleColorTransparent: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            SimpleProgramGL* p = simple_color_prog_;
            p->Bind();
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            p->SetColor(r, g, b, a);
            break;
          }
          case ShadingType::kSimpleColorTransparentDoubleSided: {
            SetDoubleSided(true);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            SimpleProgramGL* p = simple_color_prog_;
            p->Bind();
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            p->SetColor(r, g, b, a);
            break;
          }
          case ShadingType::kSimpleTexture: {
            SetDoubleSided(false);
            SetBlend(false);
            SimpleProgramGL* p = simple_tex_prog_;
            p->Bind();
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparent: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            SimpleProgramGL* p = simple_tex_mod_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransFlatness: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, flatness;
            buffer->GetFloats(&r, &g, &b, &a, &flatness);
            SimpleProgramGL* p = simple_tex_mod_flatness_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetFlatness(flatness);
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentShadow: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, shadow_offset_x, shadow_offset_y, shadow_blur,
                shadow_opacity;
            buffer->GetFloats(&r, &g, &b, &a, &shadow_offset_x,
                              &shadow_offset_y, &shadow_blur, &shadow_opacity);
            SimpleProgramGL* p = simple_tex_mod_shadow_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureData* t = buffer->GetTexture();
            const TextureData* t_mask = buffer->GetTexture();
            p->SetColorTexture(t);
            // If this isn't a full-res texture, ramp down the blurring we do.
            p->SetShadow(shadow_offset_x, shadow_offset_y,
                         std::max(0.0f, shadow_blur), shadow_opacity);
            p->SetMaskUV2Texture(t_mask);
            break;
          }
          case ShadingType::kSimpleTexModulatedTransShadowFlatness: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, shadow_offset_x, shadow_offset_y, shadow_blur,
                shadow_opacity, flatness;
            buffer->GetFloats(&r, &g, &b, &a, &shadow_offset_x,
                              &shadow_offset_y, &shadow_blur, &shadow_opacity,
                              &flatness);
            SimpleProgramGL* p = simple_tex_mod_shadow_flatness_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureData* t = buffer->GetTexture();
            const TextureData* t_mask = buffer->GetTexture();
            p->SetColorTexture(t);
            // If this isn't a full-res texture, ramp down the blurring we do.
            p->SetShadow(shadow_offset_x, shadow_offset_y,
                         std::max(0.0f, shadow_blur), shadow_opacity);
            p->SetMaskUV2Texture(t_mask);
            p->SetFlatness(flatness);
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentGlow: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, glow_amount, glow_blur;
            buffer->GetFloats(&r, &g, &b, &a, &glow_amount, &glow_blur);
            SimpleProgramGL* p = simple_tex_mod_glow_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureData* t = buffer->GetTexture();
            p->SetColorTexture(t);

            // Glow.
            p->setGlow(glow_amount, std::max(0.0f, glow_blur));
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentGlowMaskUV2: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, glow_amount, glow_blur;
            buffer->GetFloats(&r, &g, &b, &a, &glow_amount, &glow_blur);
            SimpleProgramGL* p = simple_tex_mod_glow_maskuv2_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureData* t = buffer->GetTexture();
            p->SetColorTexture(t);
            const TextureData* t_mask = buffer->GetTexture();
            p->SetMaskUV2Texture(t_mask);
            // Glow.
            p->setGlow(glow_amount, std::max(0.0f, glow_blur));
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentDoubleSided: {
            SetDoubleSided(true);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            SimpleProgramGL* p = simple_tex_mod_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulated: {
            SetDoubleSided(false);
            SetBlend(false);
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            SimpleProgramGL* p = simple_tex_mod_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedColorized: {
            SetDoubleSided(false);
            SetBlend(false);
            float r, g, b, colorize_r, colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &colorize_r, &colorize_g,
                              &colorize_b);
            SimpleProgramGL* p = simple_tex_mod_colorized_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorizeTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedColorized2: {
            SetDoubleSided(false);
            SetBlend(false);
            float r, g, b, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &colorize_r, &colorize_g, &colorize_b,
                              &colorize2_r, &colorize2_g, &colorize2_b);
            SimpleProgramGL* p = simple_tex_mod_colorized2_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);
            break;
          }
          case ShadingType::kSimpleTextureModulatedColorized2Masked: {
            SetDoubleSided(false);
            SetBlend(false);
            float r, g, b, a, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            SimpleProgramGL* p = simple_tex_mod_colorized2_masked_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);
            p->SetColorizeTexture(buffer->GetTexture());
            p->SetMaskTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentColorized: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, colorize_r, colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b);
            SimpleProgramGL* p = simple_tex_mod_colorized_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorizeTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentColorized2: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            SimpleProgramGL* p = simple_tex_mod_colorized2_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);
            p->SetColorizeTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::
              kSimpleTextureModulatedTransparentColorized2Masked: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            SimpleProgramGL* p = simple_tex_mod_colorized2_masked_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);
            p->SetColorizeTexture(buffer->GetTexture());
            p->SetMaskTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kObject: {
            SetDoubleSided(false);
            SetBlend(false);
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            ObjectProgramGL* p = obj_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetVignetteTexture(vignette_tex_);
            break;
          }
          case ShadingType::kSmoke: {
            SetDoubleSided(true);
            SetBlend(true);
            SetBlendPremult(true);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            SmokeProgramGL* p = smoke_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSmokeOverlay: {
            SetDoubleSided(true);
            SetBlend(true);
            SetBlendPremult(true);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            SmokeProgramGL* p = smoke_overlay_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetDepthTexture(
                static_cast<RenderTargetGL*>(camera_render_target())
                    ->framebuffer()
                    ->depth_texture());
            p->SetBlurTexture(
                blur_buffers_[blur_buffers_.size() - 1]->texture());
            break;
          }
          case ShadingType::kPostProcessNormalDistort: {
            float distort = buffer->GetFloat();
            PostProcessProgramGL* p = postprocess_distort_prog_;
            StandardPostProcessSetup(p, pass);
            p->SetDistort(distort);
            break;
          }
          case ShadingType::kPostProcess: {
            PostProcessProgramGL* p = postprocess_prog_;
            StandardPostProcessSetup(p, pass);
            break;
          }
          case ShadingType::kPostProcessEyes: {
            assert(postprocess_eyes_prog_);
            PostProcessProgramGL* p = postprocess_eyes_prog_;
            StandardPostProcessSetup(p, pass);
            break;
          }
          case ShadingType::kSprite: {
            SetDoubleSided(false);
            SetBlend(true);
            SetBlendPremult(true);

            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            bool overlay = static_cast<bool>(buffer->GetInt());
            bool cam_aligned = static_cast<bool>(buffer->GetInt());

            SpriteProgramGL* p;
            if (cam_aligned) {
              if (overlay) {
                p = sprite_camalign_overlay_prog_;
              } else {
                p = sprite_camalign_prog_;
              }
            } else {
              assert(!overlay);  // Unsupported combo.
              p = sprite_prog_;
            }
            p->Bind();
            if (overlay) {
              p->SetDepthTexture(
                  static_cast<RenderTargetGL*>(camera_render_target())
                      ->framebuffer()
                      ->depth_texture());
            }
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kObjectTransparent: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());

            SetBlend(true);
            SetBlendPremult(premult);

            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ObjectProgramGL* p = obj_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetVignetteTexture(vignette_tex_);
            break;
          }
          case ShadingType::kObjectLightShadow: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            int world_space = buffer->GetInt();
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            ObjectProgramGL* p = world_space ? obj_lightshad_worldspace_prog_
                                             : obj_lightshad_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectLightShadowTransparent: {
            SetDoubleSided(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ObjectProgramGL* p = obj_lightshad_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);

            break;
          }
          case ShadingType::kObjectReflectLightShadow: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            int world_space = buffer->GetInt();
            float r, g, b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b);
            ObjectProgramGL* p = world_space
                                     ? obj_refl_lightshad_worldspace_prog_
                                     : obj_refl_lightshad_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetReflectionTexture(buffer->GetTexture());
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowDoubleSided: {
            // FIXME: This shader isn't actually flipping the normal for the
            //  back side of the face.. for now we don't care though.
            SetDoubleSided(true);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            int world_space = buffer->GetInt();

            // Verified.
            float r, g, b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b);
            ObjectProgramGL* p;

            // Testing why reflection is wonky..
            if (explicit_bool(false)) {
              p = world_space ? obj_lightshad_worldspace_prog_
                              : obj_lightshad_prog_;
              p->Bind();
              p->SetColor(r, g, b);
              p->SetColorTexture(buffer->GetTexture());
              buffer->GetTexture();
            } else {
              p = world_space ? obj_refl_lightshad_worldspace_prog_
                              : obj_refl_lightshad_prog_;
              p->Bind();
              p->SetColor(r, g, b);
              p->SetColorTexture(buffer->GetTexture());
              p->SetReflectionTexture(buffer->GetTexture());
              p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            }
            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowColorized: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            float r, g, b, reflect_r, reflect_g, reflect_b, colorize_r,
                colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b,
                              &colorize_r, &colorize_g, &colorize_b);
            ObjectProgramGL* p = obj_refl_lightshad_colorize_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetReflectionTexture(buffer->GetTexture());
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowColorized2: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());

            float r, g, b, reflect_r, reflect_g, reflect_b, colorize_r,
                colorize_g, colorize_b, colorize2_r, colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b,
                              &colorize_r, &colorize_g, &colorize_b,
                              &colorize2_r, &colorize2_g, &colorize2_b);
            ObjectProgramGL* p = obj_refl_lightshad_colorize2_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());

            p->SetColorizeTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);

            p->SetReflectionTexture(buffer->GetTexture());
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);

            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowAdd: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            float r, g, b, add_r, add_g, add_b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &add_r, &add_g, &add_b, &reflect_r,
                              &reflect_g, &reflect_b);
            ObjectProgramGL* p = obj_refl_lightshad_add_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetAddColor(add_r, add_g, add_b);
            p->SetReflectionTexture(buffer->GetTexture());
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);

            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowAddColorized: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());

            float r, g, b, add_r, add_g, add_b, reflect_r, reflect_g, reflect_b,
                colorize_r, colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &add_r, &add_g, &add_b, &reflect_r,
                              &reflect_g, &reflect_b, &colorize_r, &colorize_g,
                              &colorize_b);
            ObjectProgramGL* p = obj_refl_lightshad_add_colorize_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetAddColor(add_r, add_g, add_b);

            p->SetColorizeTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);

            p->SetReflectionTexture(buffer->GetTexture());
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);

            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowAddColorized2: {
            SetDoubleSided(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());

            float r, g, b, add_r, add_g, add_b, reflect_r, reflect_g, reflect_b,
                colorize_r, colorize_g, colorize_b, colorize2_r, colorize2_g,
                colorize2_b;
            buffer->GetFloats(&r, &g, &b, &add_r, &add_g, &add_b, &reflect_r,
                              &reflect_g, &reflect_b, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            ObjectProgramGL* p = obj_refl_lightshad_add_colorize2_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetAddColor(add_r, add_g, add_b);

            p->SetColorizeTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);

            p->SetReflectionTexture(buffer->GetTexture());
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);

            p->SetVignetteTexture(vignette_tex_);
            GLuint light_shadow_tex;
            switch (light_shadow) {
              case LightShadowType::kTerrain:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              case LightShadowType::kObject:
                light_shadow_tex =
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture();
                break;
              default:
                throw Exception();
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflect: {
            SetDoubleSided(false);
            SetBlend(false);
            int world_space = buffer->GetInt();
            // verified
            float r, g, b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b);
            ObjectProgramGL* p =
                world_space ? obj_refl_worldspace_prog_ : obj_refl_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetReflectionTexture(buffer->GetTexture());  // reflection
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            break;
          }
          case ShadingType::kObjectReflectTransparent: {
            SetDoubleSided(false);

            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &a, &reflect_r, &reflect_g,
                              &reflect_b);
            ObjectProgramGL* p = obj_refl_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetReflectionTexture(buffer->GetTexture());  // reflection
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            break;
          }
          case ShadingType::kObjectReflectAddTransparent: {
            SetDoubleSided(false);

            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, add_r, add_g, add_b, reflect_r, reflect_g,
                reflect_b;
            buffer->GetFloats(&r, &g, &b, &a, &add_r, &add_g, &add_b,
                              &reflect_r, &reflect_g, &reflect_b);
            ObjectProgramGL* p = obj_refl_add_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetAddColor(add_r, add_g, add_b);
            p->SetReflectionTexture(buffer->GetTexture());  // reflection
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            break;
          }
          case ShadingType::kShield: {
            SetDoubleSided(true);
            SetBlend(true);
            SetBlendPremult(true);
            ShieldProgramGL* p = shield_prog_;
            p->Bind();
            p->SetDepthTexture(
                static_cast<RenderTargetGL*>(camera_render_target())
                    ->framebuffer()
                    ->depth_texture());
            break;
          }
          case ShadingType::kSpecial: {
            SetDoubleSided(false);

            // if we ever need to use non-blend version
            // of this in real renders, we should split off a non-blend version
            SetBlend(true);
            SetBlendPremult(true);
            auto source = (SpecialComponent::Source)buffer->GetInt();
            SimpleProgramGL* p = simple_tex_mod_prog_;
            p->Bind();
            switch (source) {
              case SpecialComponent::Source::kLightBuffer:
                p->SetColorTexture(
                    static_cast<RenderTargetGL*>(light_render_target())
                        ->framebuffer()
                        ->texture());
                break;
              case SpecialComponent::Source::kLightShadowBuffer:
                p->SetColorTexture(
                    static_cast<RenderTargetGL*>(light_shadow_render_target())
                        ->framebuffer()
                        ->texture());
                break;
              case SpecialComponent::Source::kVROverlayBuffer: {
                p->SetColorTexture(static_cast<RenderTargetGL*>(
                                       vr_overlay_flat_render_target())
                                       ->framebuffer()
                                       ->texture());
                p->SetColor(1, 1, 1, 0.95f);
                break;
              }
              default:
                throw Exception();
                break;
            }
            break;
          }
          default:
            throw Exception();
        }
        break;
      }
      case RenderCommandBuffer::Command::kSimpleComponentInlineColor: {
        float r, g, b, a;
        buffer->GetFloats(&r, &g, &b, &a);
        auto* p = static_cast<SimpleProgramGL*>(GetActiveProgram());
        assert(p != nullptr
               && p == dynamic_cast<SimpleProgramGL*>(GetActiveProgram()));
        p->SetColor(r, g, b, a);
        break;
      }
      case RenderCommandBuffer::Command::kObjectComponentInlineColor: {
        float r, g, b, a;
        buffer->GetFloats(&r, &g, &b, &a);
        auto* p = static_cast<ObjectProgramGL*>(GetActiveProgram());
        assert(p != nullptr
               && p == dynamic_cast<ObjectProgramGL*>(GetActiveProgram()));
        p->SetColor(r, g, b, a);
        break;
      }
      case RenderCommandBuffer::Command::kObjectComponentInlineAddColor: {
        float r, g, b;
        buffer->GetFloats(&r, &g, &b);
        auto* p = static_cast<ObjectProgramGL*>(GetActiveProgram());
        assert(p != nullptr
               && p == dynamic_cast<ObjectProgramGL*>(GetActiveProgram()));
        p->SetAddColor(r, g, b);
        break;
      }
      case RenderCommandBuffer::Command::kDrawModel: {
        int flags = buffer->GetInt();
        const ModelData* m = buffer->GetModel();
        assert(m);
        auto model = static_cast_check_type<ModelDataGL*>(m->renderer_data());
        assert(model);

        // if they don't wanna draw in reflections...
        if ((flags & kModelDrawFlagNoReflection) && drawing_reflection()) {
          break;
        }
        GetActiveProgram()->PrepareToDraw();
        model->Bind();
        model->Draw();
        break;
      }
      case RenderCommandBuffer::Command::kDrawModelInstanced: {
        int flags = buffer->GetInt();
        const ModelData* m = buffer->GetModel();
        assert(m);
        auto model = static_cast_check_type<ModelDataGL*>(m->renderer_data());
        assert(model);
        Matrix44f* mats;
        int count;
        mats = buffer->GetMatrices(&count);
        // if they don't wanna draw in reflections...
        if ((flags & kModelDrawFlagNoReflection) && drawing_reflection()) {
          break;
        }
        model->Bind();
        for (int i = 0; i < count; i++) {
          g_graphics_server->PushTransform();
          g_graphics_server->MultMatrix(mats[i]);
          GetActiveProgram()->PrepareToDraw();
          model->Draw();
          g_graphics_server->PopTransform();
        }
        break;
      }
        // NOLINTNEXTLINE(bugprone-branch-clone)
      case RenderCommandBuffer::Command::kBeginDebugDrawTriangles: {
        GetActiveProgram()->PrepareToDraw();
#if ENABLE_DEBUG_DRAWING
        glBegin(GL_TRIANGLES);
#endif
        break;
      }
      case RenderCommandBuffer::Command::kBeginDebugDrawLines: {
        GetActiveProgram()->PrepareToDraw();
#if ENABLE_DEBUG_DRAWING
        glBegin(GL_LINES);
#endif
        break;
      }
      case RenderCommandBuffer::Command::kEndDebugDraw: {
#if ENABLE_DEBUG_DRAWING
        glEnd();
#endif  // ENABLE_DEBUG_DRAWING
        break;
      }
      case RenderCommandBuffer::Command::kDebugDrawVertex3: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
#if ENABLE_DEBUG_DRAWING
        glVertex3f(x, y, z);
#endif  // ENABLE_DEBUG_DRAWING
        break;
      }
      case RenderCommandBuffer::Command::kDrawMesh: {
        int flags = buffer->GetInt();
        auto* mesh = buffer->GetMeshRendererData<MeshDataGL>();
        assert(mesh);
        if ((flags & kModelDrawFlagNoReflection) && drawing_reflection()) {
          break;
        }
        GetActiveProgram()->PrepareToDraw();
        mesh->Bind();
        mesh->Draw(DrawType::kTriangles);
        break;
      }
      case RenderCommandBuffer::Command::kDrawScreenQuad: {
        // Save proj/mv matrices, set up to draw a simple screen quad at the
        // back of our depth range, draw, and restore
        Matrix44f old_model_view_matrix =
            g_graphics_server->model_view_matrix();
        Matrix44f old_projection_matrix =
            g_graphics_server->projection_matrix();
        g_graphics_server->SetModelViewMatrix(kMatrix44fIdentity);
        g_graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 0.01f);
        GetActiveProgram()->PrepareToDraw();
        screen_mesh_->Bind();
        screen_mesh_->Draw(DrawType::kTriangles);
        g_graphics_server->SetModelViewMatrix(old_model_view_matrix);
        g_graphics_server->SetProjectionMatrix(old_projection_matrix);
        break;
      }
      case RenderCommandBuffer::Command::kScissorPush: {
        Rect r;
        buffer->GetFloats(&r.l, &r.b, &r.r, &r.t);

        // Convert scissor-values from model space to view space.
        // this of course assumes there's no rotations and whatnot..
        Vector3f bot_left_pt =
            g_graphics_server->model_view_matrix() * Vector3f(r.l, r.b, 0);
        Vector3f top_right_pt =
            g_graphics_server->model_view_matrix() * Vector3f(r.r, r.t, 0);
        r.l = bot_left_pt.x;
        r.b = bot_left_pt.y;
        r.r = top_right_pt.x;
        r.t = top_right_pt.y;
        ScissorPush(r, render_target);
        break;
      }
      case RenderCommandBuffer::Command::kScissorPop: {
        ScissorPop(render_target);
        break;
      }
      case RenderCommandBuffer::Command::kPushTransform: {
        g_graphics_server->PushTransform();
        break;
      }
      case RenderCommandBuffer::Command::kTranslate2: {
        float x, y;
        buffer->GetFloats(&x, &y);
        g_graphics_server->Translate(Vector3f(x, y, 0));
        break;
      }
      case RenderCommandBuffer::Command::kTranslate3: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
        g_graphics_server->Translate(Vector3f(x, y, z));
        break;
      }
      case RenderCommandBuffer::Command::kCursorTranslate: {
        float x, y;
        g_platform->GetCursorPosition(&x, &y);
        g_graphics_server->Translate(Vector3f(x, y, 0));
        break;
      }
      case RenderCommandBuffer::Command::kScale2: {
        float x, y;
        buffer->GetFloats(&x, &y);
        g_graphics_server->scale(Vector3f(x, y, 1.0f));
        break;
      }
      case RenderCommandBuffer::Command::kScale3: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
        g_graphics_server->scale(Vector3f(x, y, z));
        break;
      }
      case RenderCommandBuffer::Command::kScaleUniform: {
        float s = buffer->GetFloat();
        g_graphics_server->scale(Vector3f(s, s, s));
        break;
      }
#if BA_VR_BUILD
      case RenderCommandBuffer::Command::kTransformToRightHand: {
        VRTransformToRightHand();
        break;
      }
      case RenderCommandBuffer::Command::kTransformToLeftHand: {
        VRTransformToLeftHand();
        break;
      }
      case RenderCommandBuffer::Command::kTransformToHead: {
        VRTransformToHead();
        break;
      }
#endif  // BA_VR_BUILD
      case RenderCommandBuffer::Command::kTranslateToProjectedPoint: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
        Vector3f t = pass.frame_def()->beauty_pass()->tex_project_matrix()
                     * Vector3f(x, y, z);
        g_graphics_server->Translate(
            Vector3f(t.x * g_graphics_server->screen_virtual_width(),
                     t.y * g_graphics_server->screen_virtual_height(), 0));
        break;
      }
      case RenderCommandBuffer::Command::kRotate: {
        float angle, x, y, z;
        buffer->GetFloats(&angle, &x, &y, &z);
        g_graphics_server->Rotate(angle, Vector3f(x, y, z));
        break;
      }
      case RenderCommandBuffer::Command::kMultMatrix: {
        g_graphics_server->MultMatrix(*(buffer->GetMatrix()));
        break;
      }
      case RenderCommandBuffer::Command::kPopTransform: {
        g_graphics_server->PopTransform();
        break;
      }
      case RenderCommandBuffer::Command::kFlipCullFace: {
        FlipCullFace();
        break;
      }
      default:
        throw Exception("Invalid command in render-command-buffer");
    }
  }
  assert(buffer->IsEmpty());
}  // NOLINT (yes this is too long)

void RendererGL::BlitBuffer(RenderTarget* src_in, RenderTarget* dst_in,
                            bool depth, bool linear_interpolation,
                            bool force_shader_mode, bool invalidate_source) {
  DEBUG_CHECK_GL_ERROR;
  auto* src = static_cast<RenderTargetGL*>(src_in);
  assert(src && src == dynamic_cast<RenderTargetGL*>(src_in));
  auto* dst = static_cast<RenderTargetGL*>(dst_in);
#if BA_DEBUG_BUILD
  assert(dst && dst == dynamic_cast<RenderTargetGL*>(dst_in));
#endif
  bool do_shader_blit{true};

  // If they want depth we *MUST* use glBlitFramebuffer and can't have linear
  // interp..
  if (depth) {
    assert(g_blit_framebuffer_support && !force_shader_mode);
    linear_interpolation = false;
  }
  // Use glBlitFramebuffer when its available.
  // FIXME: This should be available in ES3.
#if !BA_OSTYPE_IOS_TVOS
  if (g_blit_framebuffer_support && !force_shader_mode) {
    do_shader_blit = false;
    DEBUG_CHECK_GL_ERROR;
    glBindFramebuffer(GL_READ_FRAMEBUFFER, src->GetFramebufferID());
    DEBUG_CHECK_GL_ERROR;
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst->GetFramebufferID());
    DEBUG_CHECK_GL_ERROR;

    glBlitFramebuffer(0, 0, static_cast<GLint>(src->physical_width()),
                      static_cast<GLint>(src->physical_height()), 0, 0,
                      static_cast<GLint>(dst->physical_width()),
                      static_cast<GLint>(dst->physical_height()),
                      depth ? (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                            : GL_COLOR_BUFFER_BIT,
                      linear_interpolation ? GL_LINEAR : GL_NEAREST);
    DEBUG_CHECK_GL_ERROR;
    if (invalidate_source) {
      InvalidateFramebuffer(true, depth, true);
    }
  } else {
    do_shader_blit = true;
  }
#endif
  if (do_shader_blit) {
    SetDepthWriting(false);
    SetDepthTesting(false);
    dst_in->DrawBegin(false);
    g_graphics_server->ModelViewReset();
    g_graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);

    // Copied from ShadingType::kSimpleColor
    SetDoubleSided(false);
    SetBlend(false);
    SimpleProgramGL* p = simple_tex_prog_;
    p->Bind();
    p->SetColorTexture(src->framebuffer()->texture());
    GetActiveProgram()->PrepareToDraw();
    screen_mesh_->Bind();
    screen_mesh_->Draw(DrawType::kTriangles);
    DEBUG_CHECK_GL_ERROR;
  }
}

void RendererGL::ScissorPush(const Rect& r_in, RenderTarget* render_target) {
  if (scissor_rects_.empty()) {
    glEnable(GL_SCISSOR_TEST);
    scissor_rects_.push_back(r_in);
  } else {
    Rect r;
    Rect rp = scissor_rects_.back();
    r.l = r_in.l > rp.l ? r_in.l : rp.l;
    r.r = r_in.r < rp.r ? r_in.r : rp.r;
    r.b = r_in.b > rp.b ? r_in.b : rp.b;
    r.t = r_in.t < rp.t ? r_in.t : rp.t;
    scissor_rects_.push_back(r);
  }
  Rect clip = scissor_rects_.back();
  if (clip.l > clip.r) clip.l = clip.r;
  if (clip.b > clip.t) clip.b = clip.t;
  auto* glt = static_cast<RenderTargetGL*>(render_target);
  float scissor_scale_x =
      static_cast<RenderTargetGL*>(render_target)->GetScissorScaleX();
  float scissor_scale_y =
      static_cast<RenderTargetGL*>(render_target)->GetScissorScaleY();
  glScissor(static_cast<GLint>(glt->GetScissorX(clip.l)),
            static_cast<GLint>(glt->GetScissorY(clip.b)),
            static_cast<GLsizei>(scissor_scale_x * (clip.r - clip.l)),
            static_cast<GLsizei>(scissor_scale_y * (clip.t - clip.b)));
  DEBUG_CHECK_GL_ERROR;
}

void RendererGL::ScissorPop(RenderTarget* render_target) {
  BA_PRECONDITION(!scissor_rects_.empty());
  scissor_rects_.pop_back();
  if (scissor_rects_.empty()) {
    glDisable(GL_SCISSOR_TEST);
  } else {
    Rect clip = scissor_rects_.back();
    if (clip.l > clip.r) clip.l = clip.r;
    if (clip.b > clip.t) clip.b = clip.t;
    auto* glt = static_cast<RenderTargetGL*>(render_target);
    float scissor_scale_x =
        static_cast<RenderTargetGL*>(render_target)->GetScissorScaleX();
    float scissor_scale_y =
        static_cast<RenderTargetGL*>(render_target)->GetScissorScaleY();
    glScissor(static_cast<GLint>(glt->GetScissorX(clip.l)),
              static_cast<GLint>(glt->GetScissorY(clip.b)),
              static_cast<GLsizei>(scissor_scale_x * (clip.r - clip.l)),
              static_cast<GLsizei>(scissor_scale_y * (clip.t - clip.b)));
  }
  DEBUG_CHECK_GL_ERROR;
}

// fixme filter our redundant sets..
void RendererGL::SetDepthWriting(bool enable) {
  if (enable != depth_writing_enabled_) {
    depth_writing_enabled_ = enable;
    glDepthMask(static_cast<GLboolean>(enable));
  }
}

void RendererGL::SetDrawAtEqualDepth(bool enable) {
  if (enable != draw_at_equal_depth_) {
    draw_at_equal_depth_ = enable;
    if (enable) {
      glDepthFunc(GL_LEQUAL);
    } else {
      glDepthFunc(GL_LESS);
    }
  }
}

// FIXME FIXME FIXME FIXME
// turning off GL_DEPTH_TEST also disables
// depth writing which we may not want.
// It sounds like the proper thing
// to do in that case is leave GL_DEPTH_TEST on
// and set glDepthFunc(GL_ALWAYS)

void RendererGL::SetDepthTesting(bool enable) {
  if (enable != depth_testing_enabled_) {
    depth_testing_enabled_ = enable;
    if (enable) {
      glEnable(GL_DEPTH_TEST);
    } else {
      glDisable(GL_DEPTH_TEST);
    }
  }
}

void RendererGL::SetDepthRange(float min, float max) {
  if (min != depth_range_min_ || max != depth_range_max_) {
    depth_range_min_ = min;
    depth_range_max_ = max;
    glDepthRange(min, max);
  }
}

void RendererGL::FlipCullFace() {
  draw_front_ = !draw_front_;
  if (draw_front_) {
    glCullFace(GL_BACK);
  } else {
    glCullFace(GL_FRONT);
  }
}

void RendererGL::SetBlend(bool b) {
#if !ENABLE_BLEND
  b = false;
#endif
  if (blend_ != b) {
    blend_ = b;
    if (blend_) {
      glEnable(GL_BLEND);
    } else {
      glDisable(GL_BLEND);
    }
  }
}
void RendererGL::SetBlendPremult(bool b) {
  if (blend_premult_ != b) {
    blend_premult_ = b;
    if (blend_premult_) {
      glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
    } else {
      // currently we only ever write to an alpha buffer for our vr overlay
      // texture, and in that case we need alpha to accumulate; not get
      // overwritten. could probably enable this everywhere but I don't know if
      // it's supported on all hardware or is slower or whatnot..
      if (IsVRMode()) {
        glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE,
                            GL_ONE_MINUS_SRC_ALPHA);
      } else {
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
      }
    }
  }
}

void RendererGL::BindVertexArray(GLuint v) {
  assert(g_vao_support);
  if (v != current_vertex_array_) {
    glBindVertexArray(v);
    current_vertex_array_ = v;
  }
}
void RendererGL::SetDoubleSided(bool d) {
  if (double_sided_ != d) {
    double_sided_ = d;
    if (double_sided_) {
      glDisable(GL_CULL_FACE);
    } else {
      glEnable(GL_CULL_FACE);
    }
  }
}

void RendererGL::UpdateVignetteTex(bool force) {
  if (force || vignette_quality_ != g_graphics_server->quality()
      || vignette_tex_outer_r_ != vignette_outer().x
      || vignette_tex_outer_g_ != vignette_outer().y
      || vignette_tex_outer_b_ != vignette_outer().z
      || vignette_tex_inner_r_ != vignette_inner().x
      || vignette_tex_inner_g_ != vignette_inner().y
      || vignette_tex_inner_b_ != vignette_inner().z) {
    vignette_tex_outer_r_ = vignette_outer().x;
    vignette_tex_outer_g_ = vignette_outer().y;
    vignette_tex_outer_b_ = vignette_outer().z;
    vignette_tex_inner_r_ = vignette_inner().x;
    vignette_tex_inner_g_ = vignette_inner().y;
    vignette_tex_inner_b_ = vignette_inner().z;
    vignette_quality_ = g_graphics_server->quality();

    const int width = 64;
    const int height = 64;
    const size_t tex_buffer_size = width * height * 4;
    std::vector<uint8_t> datavec(tex_buffer_size);
    uint8_t* data{datavec.data()};
    float max_c = 0.5f * 0.5f * 0.5f * 0.5f;
    uint8_t* b = data;

    float out_r = std::min(
        255.0f, std::max(0.0f, 255.0f * (1.0f - vignette_tex_outer_r_)));
    float out_g = std::min(
        255.0f, std::max(0.0f, 255.0f * (1.0f - vignette_tex_outer_g_)));
    float out_b = std::min(
        255.0f, std::max(0.0f, 255.0f * (1.0f - vignette_tex_outer_b_)));
    float in_r = std::min(
        255.0f, std::max(0.0f, 255.0f * (1.0f - vignette_tex_inner_r_)));
    float in_g = std::min(
        255.0f, std::max(0.0f, 255.0f * (1.0f - vignette_tex_inner_g_)));
    float in_b = std::min(
        255.0f, std::max(0.0f, 255.0f * (1.0f - vignette_tex_inner_b_)));

    for (int y = 0; y < height; y++) {
      float d3 = static_cast<float>(y) / (height - 1);
      float d4 = 1.0f - d3;
      for (int x = 0; x < width; x++) {
        float d1 = static_cast<float>(x) / (width - 1);
        float d2 = 1.0f - d1;
        float c = 1.0f * (1.0f - ((d1 * d2 * d3 * d4) / max_c));
        c = 0.5f * (c * c) + 0.5f * c;
        c = std::min(1.0f, std::max(0.0f, c));

        b[0] = static_cast<uint8_t>(c * out_r + (1.0f - c) * in_r);
        b[1] = static_cast<uint8_t>(c * out_g + (1.0f - c) * in_g);
        b[2] = static_cast<uint8_t>(c * out_b + (1.0f - c) * in_b);
        b[3] = 255;  // alpha
        b += 4;
      }
    }

    glGetError();  // clear error
    BindTexture(GL_TEXTURE_2D, vignette_tex_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
                 GL_UNSIGNED_BYTE, data);

    // If 32 bit failed for some reason, attempt 16.
    GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
      static bool reported = false;
      if (!reported) {
        Log("Error: 32-bit vignette creation failed; falling back to 16.");
        reported = true;
      }
      const int kVignetteTexWidth = 64;
      const int kVignetteTexHeight = 32;
      const int kVignetteTexBufferSize = kVignetteTexWidth * kVignetteTexHeight;
      uint16_t data2[kVignetteTexBufferSize];
      float max_c2 = 0.5f * 0.5f * 0.5f * 0.5f;
      uint16_t* b2 = data2;

      float out_r2 = std::min(
          32.0f, std::max(0.0f, 32.0f * (1.0f - vignette_tex_outer_r_)));
      float out_g2 = std::min(
          64.0f, std::max(0.0f, 64.0f * (1.0f - vignette_tex_outer_g_)));
      float out_b2 = std::min(
          32.0f, std::max(0.0f, 32.0f * (1.0f - vignette_tex_outer_b_)));
      float in_r2 = std::min(
          32.0f, std::max(0.0f, 32.0f * (1.0f - vignette_tex_inner_r_)));
      float in_g2 = std::min(
          64.0f, std::max(0.0f, 64.0f * (1.0f - vignette_tex_inner_g_)));
      float in_b2 = std::min(
          32.0f, std::max(0.0f, 32.0f * (1.0f - vignette_tex_inner_b_)));

      // IMPORTANT - if we tweak anything here we need to tweak vertex
      // shaders that calc this on the fly as well..
      for (int y = 0; y < height; y++) {
        float d3 = static_cast<float>(y) / (height - 1);
        float d4 = 1.0f - d3;
        for (int x = 0; x < width; x++) {
          float d1 = static_cast<float>(x) / (width - 1);
          float d2 = 1.0f - d1;
          float c = 1.0f * (1.0f - ((d1 * d2 * d3 * d4) / max_c2));
          c = 0.5f * (c * c) + 0.5f * c;
          c = std::min(1.0f, std::max(0.0f, c));
          int red =
              std::min(31, static_cast<int>(c * out_r2 + (1.0f - c) * in_r2));
          int green =
              std::min(63, static_cast<int>(c * out_g2 + (1.0f - c) * in_g2));
          int blue =
              std::min(31, static_cast<int>(c * out_b2 + (1.0f - c) * in_b2));
          *b2 = static_cast<uint16_t>(red << 11 | green << 5 | blue);
          b2 += 1;
        }
      }
      BindTexture(GL_TEXTURE_2D, vignette_tex_);
      glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB,
                   GL_UNSIGNED_SHORT_5_6_5, data2);
      DEBUG_CHECK_GL_ERROR;
    }
    if (force) {
      GL_LABEL_OBJECT(GL_TEXTURE, vignette_tex_, "vignetteTex");
    }
  }
}

auto RendererGL::GetFunkyDepthIssue() -> bool {
  if (!funky_depth_issue_set_) {
    BA_LOG_ONCE("fetching funky depth issue but not set");
  }
  return funky_depth_issue_;
}

auto RendererGL::GetDrawsShieldsFunny() -> bool {
  if (!draws_shields_funny_set_) {
    BA_LOG_ONCE("fetching draws-shields-funny value but not set");
  }
  return draws_shields_funny_;
}

void RendererGL::CheckCapabilities() { CheckGLExtensions(); }

#if BA_OSTYPE_ANDROID
std::string RendererGL::GetAutoAndroidRes() {
  assert(InMainThread());

  const char* renderer = (const char*)glGetString(GL_RENDERER);

  // On the adreno 4xxx or 5xxx series we should be able to do anything.
  if (strstr(renderer, "Adreno (TM) 4") || strstr(renderer, "Adreno (TM) 5")) {
    // for phones lets go with 1080p (phones most likely have 1920x1080-ish
    // aspect ratios)
    if (g_ui->scale() == UIScale::kSmall) {
      return "1080p";
    } else {
      // tablets are more likely to have 1920x1200 so lets inch a bit higher
      return "1200p";
    }
  }

  // On extra-speedy devices we should be able to do 1920x1200.
  if (is_extra_speedy_android_device_) {
    // for phones lets go with 1080p (phones most likely have 1920x1080-ish
    // aspect ratios)
    if (g_ui->scale() == UIScale::kSmall) {
      return "1080p";
    } else {
      // tablets are more likely to have 1920x1200 so lets inch a bit higher
      return "1200p";
    }
  }

  // Amazon Fire tablet (as of jan '18) needs REAL low res to feel smooth.
  if (g_platform->GetDeviceName() == "Amazon KFAUWI") {
    return "480p";
  }

  // fall back to the old 'Auto' values elsewhere
  // - this is generally 720p (but varies in a few cases)
  return "Auto";
}
#endif  // BA_OSTYPE_ANDROID

auto RendererGL::GetAutoTextureQuality() -> TextureQuality {
  assert(InMainThread());

  TextureQuality qual{TextureQuality::kHigh};

#if BA_OSTYPE_ANDROID
  {
    // lets be cheaper in VR mode since we have to draw twice..
    if (IsVRMode()) {
      qual = TextureQuality::kMedium;
    } else {
      // ouya is a special case since we have dds textures there; default to
      // high
#if BA_OUYA_BUILD
      qual = TextureQuality::kHigh;
#else   // BA_OUYA_BUILD
      // on android we default to high quality mode if we support ETC2;
      // otherwise go with medium
      if (g_graphics_server->SupportsTextureCompressionType(
              TextureCompressionType::kETC2)
          || is_speedy_android_device_) {
        qual = TextureQuality::kHigh;
      } else {
        qual = TextureQuality::kMedium;
      }
#endif  // BA_OUYA_BUILD
    }
  }
#elif BA_OSTYPE_IOS_TVOS
  {
    if (AppleUtils::IsSlowIOSDevice()) {
      qual = TextureQuality::kMedium;
    } else {
      qual = TextureQuality::kHigh;
    }
  }
#else   // BA_OSTYPE_ANDROID
  {
    // On other platforms (mac,pc,etc) just default to high.
    qual = TextureQuality::kHigh;
  }
#endif  // BA_OSTYPE_ANDROID

  return qual;
}

auto RendererGL::GetAutoGraphicsQuality() -> GraphicsQuality {
  assert(InMainThread());
  GraphicsQuality q{GraphicsQuality::kMedium};
#if BA_OSTYPE_ANDROID
  // lets be cheaper in VR mode since we draw twice..
  if (IsVRMode()) {
    q = GraphicsQuality::kMedium;
  } else {
    if (is_extra_speedy_android_device_) {
      q = GraphicsQuality::kHigher;
    } else if (g_running_es3 || is_speedy_android_device_) {
      q = GraphicsQuality::kHigh;
    } else {
      q = GraphicsQuality::kMedium;
    }
  }
#elif BA_OSTYPE_IOS_TVOS
  // on IOS we default to low-quality for slow devices (iphone-4, etc)
  // medium for recent-ish ones (ipad2, iphone4s, etc), high for newer-ish
  // (iPhone5, iPad4), and higher for anything beyond that
  if (AppleUtils::IsSlowIOSDevice()) {
    q = GraphicsQuality::kLow;
  } else if (AppleUtils::IsMediumIOSDevice()) {
    q = GraphicsQuality::kMedium;
  } else if (AppleUtils::IsHighIOSDevice()) {
    q = GraphicsQuality::kHigh;
  } else {
    q = GraphicsQuality::kHigher;
  }
#else
  // Elsewhere (desktops and such) we default to higher.
  q = GraphicsQuality::kHigher;
#endif
  return q;
}

void RendererGL::RetainShader(ProgramGL* p) { shaders_.emplace_back(p); }

void RendererGL::Load() {
  assert(InGraphicsThread());
  assert(!data_loaded_);
  assert(g_graphics_server->graphics_quality_set());
  if (!got_screen_framebuffer_) {
    got_screen_framebuffer_ = true;

    // Grab the current framebuffer and consider that to be our 'screen'
    // framebuffer.
    // This can be 0 for the main framebuffer or something else.
    glGetIntegerv(GL_FRAMEBUFFER_BINDING,
                  reinterpret_cast<GLint*>(&screen_framebuffer_));
  }
  Renderer::Load();
  int high_qual_pp_flag =
      g_graphics_server->quality() >= GraphicsQuality::kHigher
          ? SHD_HIGHER_QUALITY
          : 0;
  screen_mesh_ = std::make_unique<MeshDataSimpleFullGL>(this);
  VertexSimpleFull v[] = {{{-1, -1, 0}, {0, 0}},
                          {{1, -1, 0}, {65535, 0}},
                          {{1, 1, 0}, {65535, 65535}},
                          {{-1, 1, 0}, {0, 65535}}};
  const uint16_t indices[] = {0, 1, 2, 0, 2, 3};
  MeshBuffer<VertexSimpleFull> buffer(4, v);
  buffer.state = 1;  // Necessary for this to set properly.
  MeshIndexBuffer16 i_buffer(6, indices);
  i_buffer.state = 1;  // Necessary for this to set properly.
  screen_mesh_->SetData(&buffer);
  screen_mesh_->SetIndexData(&i_buffer);
  assert(shaders_.empty());
  ProgramGL* p;
  p = simple_color_prog_ = new SimpleProgramGL(this, SHD_MODULATE);
  RetainShader(p);
  p = simple_tex_prog_ = new SimpleProgramGL(this, SHD_TEXTURE);
  RetainShader(p);
  p = simple_tex_dtest_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_DEPTH_BUG_TEST);
  RetainShader(p);

  // Have to run this after we've created the shader to be able to test it.
  CheckFunkyDepthIssue();
  p = simple_tex_mod_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_MODULATE);
  RetainShader(p);
  p = simple_tex_mod_flatness_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_FLATNESS);
  RetainShader(p);
  p = simple_tex_mod_shadow_prog_ = new SimpleProgramGL(
      this, SHD_TEXTURE | SHD_MODULATE | SHD_SHADOW | SHD_MASK_UV2);
  RetainShader(p);
  p = simple_tex_mod_shadow_flatness_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_SHADOW
                                    | SHD_MASK_UV2 | SHD_FLATNESS);
  RetainShader(p);
  p = simple_tex_mod_glow_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_GLOW);
  RetainShader(p);
  p = simple_tex_mod_glow_maskuv2_prog_ = new SimpleProgramGL(
      this, SHD_TEXTURE | SHD_MODULATE | SHD_GLOW | SHD_MASK_UV2);
  RetainShader(p);
  p = simple_tex_mod_colorized_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_COLORIZE);
  RetainShader(p);
  p = simple_tex_mod_colorized2_prog_ = new SimpleProgramGL(
      this, SHD_TEXTURE | SHD_MODULATE | SHD_COLORIZE | SHD_COLORIZE2);
  RetainShader(p);
  p = simple_tex_mod_colorized2_masked_prog_ =
      new SimpleProgramGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_COLORIZE
                                    | SHD_COLORIZE2 | SHD_MASKED);
  RetainShader(p);
  p = obj_prog_ = new ObjectProgramGL(this, 0);
  RetainShader(p);
  p = obj_transparent_prog_ = new ObjectProgramGL(this, SHD_OBJ_TRANSPARENT);
  RetainShader(p);
  p = obj_lightshad_transparent_prog_ =
      new ObjectProgramGL(this, SHD_OBJ_TRANSPARENT | SHD_LIGHT_SHADOW);
  RetainShader(p);
  p = obj_refl_prog_ = new ObjectProgramGL(this, SHD_REFLECTION);
  RetainShader(p);
  p = obj_refl_worldspace_prog_ =
      new ObjectProgramGL(this, SHD_REFLECTION | SHD_WORLD_SPACE_PTS);
  RetainShader(p);
  p = obj_refl_transparent_prog_ =
      new ObjectProgramGL(this, SHD_REFLECTION | SHD_OBJ_TRANSPARENT);
  RetainShader(p);
  p = obj_refl_add_transparent_prog_ =
      new ObjectProgramGL(this, SHD_REFLECTION | SHD_ADD | SHD_OBJ_TRANSPARENT);
  RetainShader(p);
  p = obj_lightshad_prog_ = new ObjectProgramGL(this, SHD_LIGHT_SHADOW);
  RetainShader(p);
  p = obj_lightshad_worldspace_prog_ =
      new ObjectProgramGL(this, SHD_LIGHT_SHADOW | SHD_WORLD_SPACE_PTS);
  RetainShader(p);
  p = obj_refl_lightshad_prog_ =
      new ObjectProgramGL(this, SHD_LIGHT_SHADOW | SHD_REFLECTION);
  RetainShader(p);
  p = obj_refl_lightshad_worldspace_prog_ = new ObjectProgramGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_WORLD_SPACE_PTS);
  RetainShader(p);
  p = obj_refl_lightshad_colorize_prog_ = new ObjectProgramGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_COLORIZE);
  RetainShader(p);
  p = obj_refl_lightshad_colorize2_prog_ = new ObjectProgramGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_COLORIZE | SHD_COLORIZE2);
  RetainShader(p);
  p = obj_refl_lightshad_add_prog_ =
      new ObjectProgramGL(this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_ADD);
  RetainShader(p);
  p = obj_refl_lightshad_add_colorize_prog_ = new ObjectProgramGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_ADD | SHD_COLORIZE);
  RetainShader(p);
  p = obj_refl_lightshad_add_colorize2_prog_ =
      new ObjectProgramGL(this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_ADD
                                    | SHD_COLORIZE | SHD_COLORIZE2);
  RetainShader(p);
  p = smoke_prog_ =
      new SmokeProgramGL(this, SHD_OBJ_TRANSPARENT | SHD_WORLD_SPACE_PTS);
  RetainShader(p);
  p = smoke_overlay_prog_ = new SmokeProgramGL(
      this, SHD_OBJ_TRANSPARENT | SHD_WORLD_SPACE_PTS | SHD_OVERLAY);
  RetainShader(p);
  p = sprite_prog_ = new SpriteProgramGL(this, SHD_COLOR);
  RetainShader(p);
  p = sprite_camalign_prog_ =
      new SpriteProgramGL(this, SHD_CAMERA_ALIGNED | SHD_COLOR);
  RetainShader(p);
  p = sprite_camalign_overlay_prog_ =
      new SpriteProgramGL(this, SHD_CAMERA_ALIGNED | SHD_OVERLAY | SHD_COLOR);
  RetainShader(p);
  p = blur_prog_ = new BlurProgramGL(this, 0);
  RetainShader(p);
  p = shield_prog_ = new ShieldProgramGL(this, 0);
  RetainShader(p);

  // Conditional seems to be a *very* slight win on some architectures (A7), a
  // loss on some (A5) and a wash on some (Adreno 320).
  // Gonna wait before a clean win before turning it on.
  p = postprocess_prog_ = new PostProcessProgramGL(this, high_qual_pp_flag);
  RetainShader(p);
  if (g_graphics_server->quality() >= GraphicsQuality::kHigher) {
    p = postprocess_eyes_prog_ = new PostProcessProgramGL(this, SHD_EYES);
    RetainShader(p);
  } else {
    postprocess_eyes_prog_ = nullptr;
  }
  p = postprocess_distort_prog_ =
      new PostProcessProgramGL(this, SHD_DISTORT | high_qual_pp_flag);
  RetainShader(p);

  // Generate our random value texture.
  {
    glGenTextures(1, &random_tex_);
    BindTexture(GL_TEXTURE_2D, random_tex_);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    const int tex_buffer_size = 128 * 128 * 3;
    unsigned char data[tex_buffer_size];
    for (unsigned char& i : data) {
      i = static_cast<unsigned char>(rand());  // NOLINT
    }
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 128, 128, 0, GL_RGB,
                 GL_UNSIGNED_BYTE, data);
    GL_LABEL_OBJECT(GL_TEXTURE, random_tex_, "randomTex");
  }

  // Generate our vignette tex.
  {
    glGenTextures(1, &vignette_tex_);
    BindTexture(GL_TEXTURE_2D, vignette_tex_);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    UpdateVignetteTex(true);
  }

  // Let's pre-fill our recyclable mesh-datas list to reduce the need to make
  // more which could cause hitches.
  assert(recycle_mesh_datas_simple_split_.empty());
  for (int i = 0; i < 10; i++) {
    recycle_mesh_datas_simple_split_.push_back(new MeshDataSimpleSplitGL(this));
  }
  assert(recycle_mesh_datas_object_split_.empty());
  for (int i = 0; i < 10; i++) {
    recycle_mesh_datas_object_split_.push_back(new MeshDataObjectSplitGL(this));
  }
  assert(recycle_mesh_datas_simple_full_.empty());
  for (int i = 0; i < 10; i++) {
    recycle_mesh_datas_simple_full_.push_back(new MeshDataSimpleFullGL(this));
  }
  assert(recycle_mesh_datas_dual_texture_full_.empty());
  for (int i = 0; i < 10; i++) {
    recycle_mesh_datas_dual_texture_full_.push_back(
        new MeshDataDualTextureFullGL(this));
  }
  assert(recycle_mesh_datas_smoke_full_.empty());
  for (int i = 0; i < 2; i++) {
    recycle_mesh_datas_smoke_full_.push_back(new MeshDataSmokeFullGL(this));
  }
  assert(recycle_mesh_datas_sprite_.empty());
  for (int i = 0; i < 2; i++) {
    recycle_mesh_datas_sprite_.push_back(new MeshDataSpriteGL(this));
  }

  // Re-sync with the GL state since we might be dealing with a new context/etc.
  SyncGLState();
  DEBUG_CHECK_GL_ERROR;
  data_loaded_ = true;
}

// in
void RendererGL::PostLoad() {
  Renderer::PostLoad();
  // control may pass back to cardboard after we've finished loading
  // but before we render, (in cases such as graphics settings switches)
  // ...and it seems they can screw up our VAOs if we leave them bound...
  // so lets be defensive.
#if BA_CARDBOARD_BUILD
  SyncGLState();
#endif
}

void RendererGL::Unload() {
  assert(InGraphicsThread());
  DEBUG_CHECK_GL_ERROR;
  assert(data_loaded_);
  Renderer::Unload();
  // clear out recycle-mesh-datas
  for (auto&& i : recycle_mesh_datas_simple_split_) {
    delete i;
  }
  recycle_mesh_datas_simple_split_.clear();
  for (auto&& i : recycle_mesh_datas_object_split_) {
    delete i;
  }
  recycle_mesh_datas_object_split_.clear();
  for (auto&& i : recycle_mesh_datas_simple_full_) {
    delete i;
  }
  recycle_mesh_datas_simple_full_.clear();
  for (auto&& i : recycle_mesh_datas_dual_texture_full_) {
    delete i;
  }
  recycle_mesh_datas_dual_texture_full_.clear();
  for (auto&& i : recycle_mesh_datas_smoke_full_) {
    delete i;
  }
  recycle_mesh_datas_smoke_full_.clear();
  for (auto&& i : recycle_mesh_datas_sprite_) {
    delete i;
  }
  recycle_mesh_datas_sprite_.clear();
  screen_mesh_.reset();
  if (!g_graphics_server->renderer_context_lost()) {
    glDeleteTextures(1, &random_tex_);
    glDeleteTextures(1, &vignette_tex_);
  }
  blur_buffers_.clear();
  shaders_.clear();
  simple_color_prog_ = nullptr;
  simple_tex_prog_ = nullptr;
  simple_tex_dtest_prog_ = nullptr;
  simple_tex_mod_prog_ = nullptr;
  simple_tex_mod_flatness_prog_ = nullptr;
  simple_tex_mod_shadow_prog_ = nullptr;
  simple_tex_mod_shadow_flatness_prog_ = nullptr;
  simple_tex_mod_glow_prog_ = nullptr;
  simple_tex_mod_glow_maskuv2_prog_ = nullptr;
  simple_tex_mod_colorized_prog_ = nullptr;
  simple_tex_mod_colorized2_prog_ = nullptr;
  simple_tex_mod_colorized2_masked_prog_ = nullptr;
  obj_prog_ = nullptr;
  obj_transparent_prog_ = nullptr;
  obj_refl_prog_ = nullptr;
  obj_refl_worldspace_prog_ = nullptr;
  obj_refl_transparent_prog_ = nullptr;
  obj_refl_add_transparent_prog_ = nullptr;
  obj_lightshad_prog_ = nullptr;
  obj_lightshad_worldspace_prog_ = nullptr;
  obj_refl_lightshad_prog_ = nullptr;
  obj_refl_lightshad_worldspace_prog_ = nullptr;
  obj_refl_lightshad_colorize_prog_ = nullptr;
  obj_refl_lightshad_colorize2_prog_ = nullptr;
  obj_refl_lightshad_add_prog_ = nullptr;
  obj_refl_lightshad_add_colorize_prog_ = nullptr;
  obj_refl_lightshad_add_colorize2_prog_ = nullptr;
  smoke_prog_ = nullptr;
  smoke_overlay_prog_ = nullptr;
  sprite_prog_ = nullptr;
  sprite_camalign_prog_ = nullptr;
  sprite_camalign_overlay_prog_ = nullptr;
  obj_lightshad_transparent_prog_ = nullptr;
  blur_prog_ = nullptr;
  shield_prog_ = nullptr;
  postprocess_prog_ = nullptr;
  postprocess_eyes_prog_ = nullptr;
  postprocess_distort_prog_ = nullptr;
  data_loaded_ = false;
  DEBUG_CHECK_GL_ERROR;
}

auto RendererGL::NewModelData(const ModelData& model) -> ModelRendererData* {
  return Object::NewDeferred<ModelDataGL>(model, this);
}
auto RendererGL::NewTextureData(const TextureData& texture)
    -> TextureRendererData* {
  return Object::NewDeferred<TextureDataGL>(texture, this);
}
auto RendererGL::NewScreenRenderTarget() -> RenderTarget* {
  return Object::NewDeferred<RenderTargetGL>(this);
}
auto RendererGL::NewFramebufferRenderTarget(int width, int height,
                                            bool linear_interp, bool depth,
                                            bool texture, bool depth_texture,
                                            bool high_quality, bool msaa,
                                            bool alpha) -> RenderTarget* {
  return Object::NewDeferred<RenderTargetGL>(this, width, height, linear_interp,
                                             depth, texture, depth_texture,
                                             high_quality, msaa, alpha);
}

auto RendererGL::NewMeshData(MeshDataType mesh_type, MeshDrawType draw_type)
    -> MeshRendererData* {
  switch (mesh_type) {
    case MeshDataType::kIndexedSimpleSplit: {
      MeshDataSimpleSplitGL* data;
      // use a recycled one if we've got one.. otherwise create a new one
      auto i = recycle_mesh_datas_simple_split_.rbegin();
      if (i != recycle_mesh_datas_simple_split_.rend()) {
        data = *i;
        recycle_mesh_datas_simple_split_.pop_back();
      } else {
        data = new MeshDataSimpleSplitGL(this);
      }
      return data;
      break;
    }
    case MeshDataType::kIndexedObjectSplit: {
      MeshDataObjectSplitGL* data;
      // use a recycled one if we've got one.. otherwise create a new one
      auto i = recycle_mesh_datas_object_split_.rbegin();
      if (i != recycle_mesh_datas_object_split_.rend()) {
        data = *i;
        recycle_mesh_datas_object_split_.pop_back();
      } else {
        data = new MeshDataObjectSplitGL(this);
      }
      return data;
      break;
    }
    case MeshDataType::kIndexedSimpleFull: {
      MeshDataSimpleFullGL* data;
      // use a recycled one if we've got one.. otherwise create a new one
      auto i = recycle_mesh_datas_simple_full_.rbegin();
      if (i != recycle_mesh_datas_simple_full_.rend()) {
        data = *i;
        recycle_mesh_datas_simple_full_.pop_back();
      } else {
        data = new MeshDataSimpleFullGL(this);
      }
      data->set_dynamic_draw(draw_type == MeshDrawType::kDynamic);
      return data;
      break;
    }
    case MeshDataType::kIndexedDualTextureFull: {
      MeshDataDualTextureFullGL* data;
      // use a recycled one if we've got one.. otherwise create a new one
      auto i = recycle_mesh_datas_dual_texture_full_.rbegin();
      if (i != recycle_mesh_datas_dual_texture_full_.rend()) {
        data = *i;
        recycle_mesh_datas_dual_texture_full_.pop_back();
      } else {
        data = new MeshDataDualTextureFullGL(this);
      }
      data->set_dynamic_draw(draw_type == MeshDrawType::kDynamic);
      return data;
      break;
    }
    case MeshDataType::kIndexedSmokeFull: {
      MeshDataSmokeFullGL* data;
      // use a recycled one if we've got one.. otherwise create a new one
      auto i = recycle_mesh_datas_smoke_full_.rbegin();
      if (i != recycle_mesh_datas_smoke_full_.rend()) {
        data = *i;
        recycle_mesh_datas_smoke_full_.pop_back();
      } else {
        data = new MeshDataSmokeFullGL(this);
      }
      data->set_dynamic_draw(draw_type == MeshDrawType::kDynamic);
      return data;
      break;
    }
    case MeshDataType::kSprite: {
      MeshDataSpriteGL* data;
      // use a recycled one if we've got one.. otherwise create a new one
      auto i = recycle_mesh_datas_sprite_.rbegin();
      if (i != recycle_mesh_datas_sprite_.rend()) {
        data = *i;
        recycle_mesh_datas_sprite_.pop_back();
      } else {
        data = new MeshDataSpriteGL(this);
      }
      data->set_dynamic_draw(draw_type == MeshDrawType::kDynamic);
      return data;
      break;
    }
    default:
      throw Exception();
      break;
  }
}
void RendererGL::DeleteMeshData(MeshRendererData* source_in,
                                MeshDataType mesh_type) {
  // when we're done with mesh-data we keep it around for recycling...
  // it seems that killing off VAO/VBOs can be hitchy (on mac at least)
  // hmmm should we have some sort of threshold at which point we kill off
  // some?..

  switch (mesh_type) {
    case MeshDataType::kIndexedSimpleSplit: {
      auto source = static_cast<MeshDataSimpleSplitGL*>(source_in);
      assert(source
             && source == dynamic_cast<MeshDataSimpleSplitGL*>(source_in));
      source->Reset();
      recycle_mesh_datas_simple_split_.push_back(source);
      break;
    }
    case MeshDataType::kIndexedObjectSplit: {
      auto source = static_cast<MeshDataObjectSplitGL*>(source_in);
      assert(source
             && source == dynamic_cast<MeshDataObjectSplitGL*>(source_in));
      source->Reset();
      recycle_mesh_datas_object_split_.push_back(source);
      break;
    }
    case MeshDataType::kIndexedSimpleFull: {
      auto source = static_cast<MeshDataSimpleFullGL*>(source_in);
      assert(source
             && source == dynamic_cast<MeshDataSimpleFullGL*>(source_in));
      source->Reset();
      recycle_mesh_datas_simple_full_.push_back(source);
      break;
    }
    case MeshDataType::kIndexedDualTextureFull: {
      auto source = static_cast<MeshDataDualTextureFullGL*>(source_in);
      assert(source
             && source == dynamic_cast<MeshDataDualTextureFullGL*>(source_in));
      source->Reset();
      recycle_mesh_datas_dual_texture_full_.push_back(source);
      break;
    }
    case MeshDataType::kIndexedSmokeFull: {
      auto source = static_cast<MeshDataSmokeFullGL*>(source_in);
      assert(source && source == dynamic_cast<MeshDataSmokeFullGL*>(source_in));
      source->Reset();
      recycle_mesh_datas_smoke_full_.push_back(source);
      break;
    }
    case MeshDataType::kSprite: {
      auto source = static_cast<MeshDataSpriteGL*>(source_in);
      assert(source && source == dynamic_cast<MeshDataSpriteGL*>(source_in));
      source->Reset();
      recycle_mesh_datas_sprite_.push_back(source);
      break;
    }
    default:
      throw Exception();
      break;
  }
}

void RendererGL::CheckForErrors() {
  // lets only check periodically.. i doubt it hurts to run this all the time
  // but just in case...
  error_check_counter_++;
  if (error_check_counter_ > 120) {
    error_check_counter_ = 0;
    CHECK_GL_ERROR;
  }
}

void RendererGL::DrawDebug() {
  if (explicit_bool(false)) {
    // Draw our cam buffer if we have it.
    if (has_camera_render_target()) {
      SetDepthWriting(false);
      SetDepthTesting(false);
      SetDoubleSided(false);
      SetBlend(false);
      SimpleProgramGL* p = simple_tex_prog_;
      p->Bind();

      g_graphics_server->ModelViewReset();
      g_graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);

      float tx = -0.6f;
      float ty = 0.6f;

      g_graphics_server->PushTransform();
      g_graphics_server->scale(Vector3f(0.4f, 0.4f, 0.4f));
      g_graphics_server->Translate(Vector3f(-1.3f, -0.7f, 0));

      // Draw cam buffer.
      g_graphics_server->PushTransform();
      g_graphics_server->Translate(Vector3f(tx, ty, 0));
      tx += 0.2f;
      ty -= 0.25f;
      g_graphics_server->scale(Vector3f(0.5f, 0.5f, 1.0f));
      p->SetColorTexture(static_cast<RenderTargetGL*>(camera_render_target())
                             ->framebuffer()
                             ->texture());
      GetActiveProgram()->PrepareToDraw();
      screen_mesh_->Bind();
      screen_mesh_->Draw(DrawType::kTriangles);
      g_graphics_server->PopTransform();

      // Draw blur buffers.
      if (explicit_bool(false)) {
        for (auto&& i : blur_buffers_) {
          g_graphics_server->PushTransform();
          g_graphics_server->Translate(Vector3f(tx, ty, 0));
          tx += 0.2f;
          ty -= 0.25f;
          g_graphics_server->scale(Vector3f(0.5f, 0.5f, 1.0f));
          p->SetColorTexture(i->texture());
          GetActiveProgram()->PrepareToDraw();
          screen_mesh_->Bind();
          screen_mesh_->Draw(DrawType::kTriangles);
          g_graphics_server->PopTransform();
        }
      }
      g_graphics_server->PopTransform();
    }
  }
}

void RendererGL::GenerateCameraBufferBlurPasses() {
  // If our cam-buffer res has changed since last time, regenerate our blur
  // buffers.
  auto* cam_buffer = static_cast<RenderTargetGL*>(camera_render_target());
  assert(cam_buffer != nullptr
         && dynamic_cast<RenderTargetGL*>(camera_render_target())
                == cam_buffer);

  if (cam_buffer->physical_width() != last_cam_buffer_width_
      || cam_buffer->physical_height() != last_cam_buffer_height_
      || blur_res_count() != last_blur_res_count_ || blur_buffers_.empty()) {
    blur_buffers_.clear();
    last_cam_buffer_width_ = cam_buffer->physical_width();
    last_cam_buffer_height_ = cam_buffer->physical_height();
    last_blur_res_count_ = blur_res_count();
    int w = static_cast<int>(last_cam_buffer_width_);
    int h = static_cast<int>(last_cam_buffer_height_);

    // In higher-quality we do multiple levels and 16-bit dithering is kinda
    // noticeable and ugly then.
    bool high_quality_fbos =
        (g_graphics_server->quality() >= GraphicsQuality::kHigher);
    for (int i = 0; i < blur_res_count(); i++) {
      assert(w % 2 == 0);
      assert(h % 2 == 0);
      w /= 2;
      h /= 2;
      blur_buffers_.push_back(Object::New<FramebufferObjectGL>(
          this, w, h,
          true,               // linear_interp
          false,              // depth
          true,               // tex
          false,              // depthTex
          high_quality_fbos,  // highQuality
          false,              // msaa
          false               // alpha
          ));                 // NOLINT(whitespace/parens)
    }

    // Final redundant one (we run an extra blur without down-rezing).
    if (g_graphics_server->quality() >= GraphicsQuality::kHigher)
      blur_buffers_.push_back(Object::New<FramebufferObjectGL>(
          this, w, h,
          true,   // linear_interp
          false,  // depth
          true,   // tex
          false,  // depthTex
          false,  // highQuality
          false,  // msaa
          false   // alpha
          ));     // NOLINT(whitespace/parens)
  }

  // Ok now go through and do the blurring.
  SetDepthWriting(false);
  SetDepthTesting(false);
  g_graphics_server->ModelViewReset();
  g_graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);
  SetDoubleSided(false);
  SetBlend(false);

  BlurProgramGL* p = blur_prog_;
  p->Bind();

  FramebufferObjectGL* src_fb =
      static_cast<RenderTargetGL*>(camera_render_target())->framebuffer();
  for (auto&& i : blur_buffers_) {
    FramebufferObjectGL* fb = i.get();
    assert(fb);
    fb->Bind();
    SetViewport(0, 0, fb->width(), fb->height());
    InvalidateFramebuffer(true, false, false);
    p->SetColorTexture(src_fb->texture());
    if (fb->width() == src_fb->width()) {  // Our last one is equal res.
      p->SetPixelSize(2.0f / static_cast<float>(fb->width()),
                      2.0f / static_cast<float>(fb->height()));
    } else {
      p->SetPixelSize(1.0f / static_cast<float>(fb->width()),
                      1.0f / static_cast<float>(fb->height()));
    }
    GetActiveProgram()->PrepareToDraw();
    screen_mesh_->Bind();
    screen_mesh_->Draw(DrawType::kTriangles);
    src_fb = fb;
  }
}

void RendererGL::CardboardDisableScissor() { glDisable(GL_SCISSOR_TEST); }

void RendererGL::CardboardEnableScissor() { glEnable(GL_SCISSOR_TEST); }

void RendererGL::VREyeRenderBegin() {
  assert(IsVRMode());

  // On rift we need to turn off srgb conversion for each eye render
  // so we can dump our linear data into oculus' srgb buffer as-is.
  // (we really should add proper srgb support to the engine at some point)
#if BA_RIFT_BUILD
  glDisable(GL_FRAMEBUFFER_SRGB);
#endif  // BA_RIFT_BUILD

  GLuint fb;
  glGetIntegerv(GL_FRAMEBUFFER_BINDING, reinterpret_cast<GLint*>(&fb));
  screen_framebuffer_ = fb;
}

#if BA_VR_BUILD
void RendererGL::VRSyncRenderStates() {
  // GL state has been mucked with outside of our code; let's resync stuff..
  SyncGLState();
}
#endif  // BA_VR_BUILD

void RendererGL::RenderFrameDefEnd() {
  // Need to set some states to keep cardboard happy.
#if BA_CARDBOARD_BUILD
  if (IsVRMode()) {
    SyncGLState();
    glEnable(GL_SCISSOR_TEST);
  }
#endif  // BA_CARDBOARD_BUILD
}

#pragma clang diagnostic pop

}  // namespace ballistica

#endif  // BA_ENABLE_OPENGL
