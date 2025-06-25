// Released under the MIT License. See LICENSE for details.

#if BA_ENABLE_OPENGL
#include "ballistica/base/graphics/gl/renderer_gl.h"

#include <algorithm>
#include <cstdio>
#include <iterator>
#include <list>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "ballistica/base/graphics/component/special_component.h"
#include "ballistica/base/graphics/gl/mesh/mesh_asset_data_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_dual_texture_full_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_object_split_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_simple_full_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_simple_split_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_smoke_full_gl.h"
#include "ballistica/base/graphics/gl/mesh/mesh_data_sprite_gl.h"
#include "ballistica/base/graphics/gl/program/program_blur_gl.h"
#include "ballistica/base/graphics/gl/program/program_gl.h"
#include "ballistica/base/graphics/gl/program/program_object_gl.h"
#include "ballistica/base/graphics/gl/program/program_post_process_gl.h"
#include "ballistica/base/graphics/gl/program/program_shield_gl.h"
#include "ballistica/base/graphics/gl/program/program_simple_gl.h"
#include "ballistica/base/graphics/gl/program/program_smoke_gl.h"
#include "ballistica/base/graphics/gl/program/program_sprite_gl.h"
#include "ballistica/base/graphics/gl/render_target_gl.h"
#include "ballistica/base/graphics/gl/texture_data_gl.h"
#include "ballistica/shared/math/rect.h"

// Turn this off to see how much blend overdraw is occurring.
#define BA_GL_ENABLE_BLEND 1

// Support legacy drawing purely for debugging (should migrate this to
// post-fixed pipeline).
#define BA_GL_ENABLE_DEBUG_DRAW_COMMANDS 0

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

namespace ballistica::base {

bool RendererGL::funky_depth_issue_set_{};
bool RendererGL::funky_depth_issue_{};

RendererGL::RendererGL() {
  assert(g_base->app_adapter->InGraphicsContext());

  if (explicit_bool(BA_FORCE_CHECK_GL_ERRORS)) {
    g_base->ScreenMessage("GL ERROR CHECKS ENABLED");
  }

  // Run any one-time setup the platform might need to do
  // (grabbing function pointers, etc.)
  if (!g_sys_gl_inited) {
    SysGLInit(this);
    g_sys_gl_inited = true;
  }

  CheckGLCapabilities_();
  SyncGLState_();
}

void RendererGL::CheckGLError(const char* file, int line) {
  GLenum err = glGetError();
  if (err != GL_NO_ERROR) {
    const char* version = (const char*)glGetString(GL_VERSION);
    BA_PRECONDITION_FATAL(version);
    const char* vendor = (const char*)glGetString(GL_VENDOR);
    BA_PRECONDITION_FATAL(vendor);
    const char* renderer = (const char*)glGetString(GL_RENDERER);
    BA_PRECONDITION_FATAL(renderer);
    g_core->logging->Log(
        LogName::kBaGraphics, LogLevel::kError,
        "OpenGL Error at " + std::string(file) + " line " + std::to_string(line)
            + ": " + GLErrorToString(err) + "\nrenderer: " + renderer
            + "\nvendor: " + vendor + "\nversion: " + version
            + "\ntime: " + std::to_string(g_core->AppTimeMillisecs()));
  }
}

auto RendererGL::GLErrorToString(GLenum err) -> std::string {
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

// Look for a gl extension prefixed by "GL_ARB", "GL_EXT", etc. Returns true
// if found.
static auto CheckGLExtension(const std::vector<std::string>& exts,
                             const char* ext) -> bool {
  assert(strlen(ext) < 100);
  const int variant_count{10};
  char variants[variant_count][128];
  int i = 0;
  snprintf(variants[i], sizeof(variants[i]), "OES_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_OES_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_KHR_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_ARB_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_APPLE_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_EXT_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_NV_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_ATI_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_SGIS_%s", ext);
  i++;
  snprintf(variants[i], sizeof(variants[i]), "GL_IMG_%s", ext);
  i++;
  assert(i == variant_count);

  for (auto&& ext : exts) {
    for (int i = 0; i < variant_count; ++i) {
      if (variants[i] == ext) {
        return true;
      }
    }
  }
  return false;
}

// This is split into its own call because systems that load GL calls
// dynamically may want to run the check before trying to load said GL
// calls. It's better to die with a 'Your OpenGL is too old' error rather
// than a 'Could not load function foofDinglePlop2XZ'.
void RendererGL::CheckGLVersion() {
  if (checked_gl_version_) {
    return;
  }
  const char* version_str = (const char*)glGetString(GL_VERSION);
  BA_PRECONDITION_FATAL(version_str);
  std::string version_str_s{version_str};

  // Do a rough check to make sure we're running 3 or newer of GL/GLES. This
  // query should be available even on older versions which is why we do it
  // before the GL_MAJOR_VERSION/GL_MINOR_VERSION business which is not.
  if (gl_is_es()) {
    // GL ES version strings start with 'OpenGL ES X' with X being version.
    const char* prefix = "OpenGL ES ";
    auto prefixlen = strlen(prefix);
    BA_PRECONDITION_FATAL(!strncmp(version_str, prefix, prefixlen));
    if (version_str[prefixlen] != '3') {
      FatalError(
          std::string("Your OpenGL ES version is too old (") + version_str
          + "). We require 3.0 or later. Try updating your graphics drivers.");
    }
  } else {
    // Regular GL version strings start with numeric version.
    if (version_str_s.starts_with("4.") || version_str_s.starts_with("3.2")
        || version_str_s.starts_with("3.3")) {
      // We're Good.
    } else {
      FatalError(
          std::string("Your OpenGL version is too old (") + version_str
          + "). We require 3.2 or later. Try updating your graphics drivers.");
    }
  }
  checked_gl_version_ = true;
}

void RendererGL::CheckGLCapabilities_() {
  BA_DEBUG_CHECK_GL_ERROR;
  assert(g_base->app_adapter->InGraphicsContext());

  // Die if our overall GL version is too old.
  CheckGLVersion();

  const char* renderer = (const char*)glGetString(GL_RENDERER);
  BA_PRECONDITION_FATAL(renderer);
  const char* vendor = (const char*)glGetString(GL_VENDOR);
  BA_PRECONDITION_FATAL(vendor);
  const char* version_str = (const char*)glGetString(GL_VERSION);
  BA_PRECONDITION_FATAL(version_str);

  // Now fetch exact major/minor versions. This query requires version 3.0
  // or newer which is why we checked overall version in CheckGLVersion()
  // above.
  glGetError();  // Clear any existing error so we don't die on it here.
  glGetIntegerv(GL_MAJOR_VERSION, &gl_version_major_);
  BA_PRECONDITION_FATAL(glGetError() == GL_NO_ERROR);
  glGetIntegerv(GL_MINOR_VERSION, &gl_version_minor_);
  BA_PRECONDITION_FATAL(glGetError() == GL_NO_ERROR);

  const char* basestr;
  if (gl_is_es()) {
    basestr = "OpenGL ES";
  } else {
    basestr = "OpenGL";
  }

  g_core->logging->Log(LogName::kBaGraphics, LogLevel::kInfo,
                       std::string("Using ") + basestr + " (vendor: " + vendor
                           + ", renderer: " + renderer
                           + ", version: " + version_str + ").");

  // Build a vector of extensions. Newer GLs give us extensions as lists
  // already, but on older ones we may need to break a single string apart
  // ourself.
  std::vector<std::string> extensions;
  bool used_num_extensions{};

  // Do the modern gl thing of looking through a list of extensions; not a
  // single string.
  if (auto num_extensions = GLGetIntOptional(GL_NUM_EXTENSIONS)) {
    used_num_extensions = true;
    extensions.reserve(*num_extensions);
    for (int i = 0; i < num_extensions; ++i) {
      const char* extension = (const char*)glGetStringi(GL_EXTENSIONS, i);
      BA_PRECONDITION(extension);
      extensions.push_back(extension);
    }
  } else {
    g_core->logging->Log(LogName::kBaGraphics, LogLevel::kWarning,
                         "Falling back on legacy GL_EXTENSIONS parsing.");
    // Fall back on parsing the single giant string if need be.
    // (Can probably kill this).
    auto* ex = reinterpret_cast<const char*>(glGetString(GL_EXTENSIONS));
    BA_DEBUG_CHECK_GL_ERROR;
    BA_PRECONDITION_FATAL(ex);
    std::istringstream iss(ex);
    extensions = {std::istream_iterator<std::string>(iss),
                  std::istream_iterator<std::string>()};
  }

  // On Android, look at the GL version and try to get gl3 funcs to
  // determine if we're running ES3 or not.
#if BA_PLATFORM_ANDROID

  BA_DEBUG_CHECK_GL_ERROR;

  // Flag certain devices as 'speedy' - we use this to enable high/higher
  // quality and whatnot (even in cases where ES3 isnt available).

  // Let just consider ES 3.2 stuff speedy.
  assert(gl_version_major() == 3);
  is_speedy_android_device_ = gl_version_minor() >= 2;

  is_adreno_ = (strstr(renderer, "Adreno") != nullptr);

#endif  // BA_PLATFORM_ANDROID

  std::list<TextureCompressionType> c_types;
  assert(g_base->graphics);
  if (CheckGLExtension(extensions, "texture_compression_s3tc")) {
    c_types.push_back(TextureCompressionType::kS3TC);
  }

  // Limiting pvr support to iOS for the moment.
  if (!g_buildconfig.platform_android()) {
    if (CheckGLExtension(extensions, "texture_compression_pvrtc")) {
      c_types.push_back(TextureCompressionType::kPVR);
    }
  }

  // Pretty much all Android devices should support ETC1.
  if (CheckGLExtension(extensions, "compressed_ETC1_RGB8_texture")) {
    c_types.push_back(TextureCompressionType::kETC1);
  } else {
    if (g_buildconfig.platform_android()) {
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                           "Android device missing ETC1 support.");
    }
  }

  // ETC2 is required for ES3 support (and OpenGL 4.4 or something once we
  // eventually get there).
  if (gl_is_es()) {
    c_types.push_back(TextureCompressionType::kETC2);
  }

  // ASTC is generally available on newer mobile hardware.
  if (CheckGLExtension(extensions, "texture_compression_astc_ldr")) {
    c_types.push_back(TextureCompressionType::kASTC);
  }

  g_base->graphics_server->SetTextureCompressionTypes(c_types);

  // Store the tex-compression type we support.
  BA_DEBUG_CHECK_GL_ERROR;

  // Anisotropic sampling is still an extension as of both GL 3 and ES 3, so
  // we need to test for it.
  anisotropic_support_ =
      CheckGLExtension(extensions, "texture_filter_anisotropic");
  if (anisotropic_support_) {
    glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, &max_anisotropy_);
  }

  BA_DEBUG_CHECK_GL_ERROR;

  if (gl_is_es()) {
    // GL ES 3 has glInvalidateFramebuffer as part of the standard.
    invalidate_framebuffer_support_ = true;
  } else {
    // It seems it's standard as of desktop GL 4.3 so we could probably
    // use it selectively if we wanted.
    invalidate_framebuffer_support_ = false;
  }

  combined_texture_image_unit_count_ =
      GLGetInt(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS);

  // If we're running ES3, ask about our max multisample counts and whether
  // we can enable MSAA.
  msaa_max_samples_rgb565_ = msaa_max_samples_rgb8_ = 0;  // start pessimistic

  bool have_gl_get_internal_format_iv{};
  if (gl_is_es()) {
    // This is available on ES 3.
    have_gl_get_internal_format_iv = true;
  } else {
    // This is available on GL 4.2 or newer.
    if (gl_version_major() == 4 && gl_version_minor() >= 2) {
      have_gl_get_internal_format_iv = true;
    }
  }

  if (have_gl_get_internal_format_iv) {
    GLint count;
    glGetInternalformativ(GL_RENDERBUFFER, GL_RGB565, GL_NUM_SAMPLE_COUNTS, 1,
                          &count);
    if (count > 0) {
      std::vector<GLint> samples;
      samples.resize(static_cast<size_t>(static_cast<size_t>(count)));
      glGetInternalformativ(GL_RENDERBUFFER, GL_RGB565, GL_SAMPLES, count,
                            &samples[0]);
      msaa_max_samples_rgb565_ = samples[0];
    } else {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                  "Got 0 samplecounts for RGB565");
      msaa_max_samples_rgb565_ = 0;
    }

    // RGB8 max multisamples.
    glGetInternalformativ(GL_RENDERBUFFER, GL_RGB8, GL_NUM_SAMPLE_COUNTS, 1,
                          &count);
    if (count > 0) {
      std::vector<GLint> samples;
      samples.resize(static_cast<size_t>(count));
      glGetInternalformativ(GL_RENDERBUFFER, GL_RGB8, GL_SAMPLES, count,
                            &samples[0]);
      msaa_max_samples_rgb8_ = samples[0];
    } else {
      BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                  "Got 0 samplecounts for RGB8");
      msaa_max_samples_rgb8_ = 0;
    }
  } else {
    // For older GL (which includes all Macs) it sounds like this is the way
    // to query max samples?.. but I don't know for sure if this applies to
    // renderbuffer targets or just the default drawable. Will it ever be
    // different?
    auto max_samples = GLGetIntOptional(GL_MAX_SAMPLES);
    if (max_samples.has_value()) {
      msaa_max_samples_rgb565_ = msaa_max_samples_rgb8_ = *max_samples;
    }
  }

  BA_DEBUG_CHECK_GL_ERROR;

  first_extension_check_ = false;
}

auto RendererGL::GetMSAASamplesForFramebuffer_(int width, int height) -> int {
  if (g_buildconfig.platform_android()) {
    // We currently aim for 4 up to 800 height and 2 beyond that.
    if (height > 800) {
      return 2;
    } else {
      return 4;
    }
  } else {
    return 4;
  }
}

void RendererGL::UpdateMSAAEnabled_() {
  if (g_buildconfig.platform_macos()) {
    // Let's go ahead and flip this on for Apple Silicon Macs.
#if __aarch64__
    enable_msaa_ = true;
#else
    enable_msaa_ = false;
#endif
  } else if (g_buildconfig.rift_build()) {
    if (msaa_max_samples_rgb8_ > 0) {
      enable_msaa_ = true;
    } else {
      enable_msaa_ = false;
    }
  } else if (g_buildconfig.platform_android()) {
    // lets allow full 1080p msaa with newer stuff..
    int max_msaa_res = is_tegra_k1_ ? 1200 : 800;

    // To start, see if it looks like we support msaa on paper.
    enable_msaa_ =
        ((screen_render_target()->physical_height()
          <= static_cast<float>(max_msaa_res))
         && (msaa_max_samples_rgb8_ > 0) && (msaa_max_samples_rgb565_ > 0));

    // Ok, lets be careful here; msaa blitting/etc seems to be particular in
    // terms of supported formats/etc so let's only enable it on
    // explicitly-tested hardware for now.
    if (!is_tegra_4_ && !is_tegra_k1_ && !is_recent_adreno_) {
      enable_msaa_ = false;
    }
  } else {
    enable_msaa_ = false;
  }
}

auto RendererGL::IsMSAAEnabled() const -> bool { return enable_msaa_; }

auto RendererGL::GetGLTextureFormat(TextureFormat f) -> GLenum {
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

void RendererGL::SetViewport_(GLint x, GLint y, GLsizei width, GLsizei height) {
  if (x != viewport_x_ || y != viewport_y_ || width != viewport_width_
      || height != viewport_height_) {
    viewport_x_ = x;
    viewport_y_ = y;
    viewport_width_ = width;
    viewport_height_ = height;
    glViewport(viewport_x_, viewport_y_, viewport_width_, viewport_height_);
  }
}

void RendererGL::BindTextureUnit(uint32_t tex_unit) {
  assert(tex_unit >= 0 && tex_unit < kMaxGLTexUnitsUsed);
  if (active_tex_unit_ != -1) {
    // Make sure our internal state stays correct.
    assert(GLGetInt(GL_ACTIVE_TEXTURE) == GL_TEXTURE0 + active_tex_unit_);
  }
  if (active_tex_unit_ != tex_unit) {
    active_tex_unit_ = tex_unit;
    glActiveTexture(GL_TEXTURE0 + active_tex_unit_);
    BA_DEBUG_CHECK_GL_ERROR;
  } else {
  }
}

auto RendererGL::GLGetInt(GLenum name) -> int {
  assert(g_base->app_adapter->InGraphicsContext());

  // Clear any error coming in; don't want to fail for something that's not
  // our problem.
  if (g_buildconfig.debug_build()) {
    BA_DEBUG_CHECK_GL_ERROR;
  } else {
    glGetError();
  }
  GLint val;
  glGetIntegerv(name, &val);
  if (glGetError() != GL_NO_ERROR) {
    FatalError("Unable to fetch GL int " + std::to_string(name));
  }
  return val;
}

auto RendererGL::GLGetIntOptional(GLenum name) -> std::optional<int> {
  assert(g_base->app_adapter->InGraphicsContext());

  // Clear any error coming in; don't want to fail for something that's not
  // our problem.
  if (g_buildconfig.debug_build()) {
    BA_DEBUG_CHECK_GL_ERROR;
  } else {
    glGetError();
  }
  GLint val;
  glGetIntegerv(name, &val);
  if (glGetError() != GL_NO_ERROR) {
    return {};
  }
  return val;
}

void RendererGL::BindFramebuffer(GLuint fb) {
  if (active_framebuffer_ != fb) {
    glBindFramebuffer(GL_FRAMEBUFFER, fb);
    active_framebuffer_ = fb;
  } else {
    assert(GLGetInt(GL_FRAMEBUFFER_BINDING) == fb);
  }
}

void RendererGL::BindArrayBuffer(GLuint b) {
  if (active_array_buffer_ != -1) {
    // Make sure our internal state stays correct.
    assert(GLGetInt(GL_ARRAY_BUFFER_BINDING) == active_array_buffer_);
  }
  if (active_array_buffer_ != b) {
    glBindBuffer(GL_ARRAY_BUFFER, b);
    active_array_buffer_ = b;
  }
}

void RendererGL::BindTexture_(GLuint type, const TextureAsset* t,
                              GLuint tex_unit) {
  if (t) {
    auto data = static_cast_check_type<TextureDataGL*>(t->renderer_data());
    BindTexture_(type, data->GetTexture(), tex_unit);
  } else {
    // Fallback to noise.
    BindTexture_(type, random_tex_, tex_unit);
  }
}

void RendererGL::BindTexture_(GLuint type, GLuint tex, GLuint tex_unit) {
  switch (type) {
    case GL_TEXTURE_2D: {
      // Make sure our internal state stays correct.
      if (g_buildconfig.debug_build()) {
        if (bound_textures_2d_[tex_unit] != -1) {
          BindTextureUnit(tex_unit);
          assert(GLGetInt(GL_TEXTURE_BINDING_2D)
                 == bound_textures_2d_[tex_unit]);
        }
      }
      if (tex != bound_textures_2d_[tex_unit]) {
        BindTextureUnit(tex_unit);
        glBindTexture(type, tex);
        bound_textures_2d_[tex_unit] = tex;
      }
      break;
    }
    case GL_TEXTURE_CUBE_MAP: {
      // Make sure our internal state stays correct.
      if (g_buildconfig.debug_build()) {
        if (bound_textures_cube_map_[tex_unit] != -1) {
          BindTextureUnit(tex_unit);
          assert(GLGetInt(GL_TEXTURE_BINDING_CUBE_MAP)
                 == bound_textures_cube_map_[tex_unit]);
        }
      }
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

void RendererGL::CheckFunkyDepthIssue_() {
  if (funky_depth_issue_set_) {
    return;
  }

  // Note: this test fails for some reason on some Broadcom VideoCore and
  // older NVidia chips (tegra 2?) ...so lets limit testing to adreno chips
  // since that's the only place the problem is known to happen.
  if (!is_adreno_) {
    // if (!is_adreno_ || !supports_depth_textures_) {
    funky_depth_issue_set_ = true;
    funky_depth_issue_ = false;
    return;
  }

  // On some adreno chips, depth buffer values are always returned
  // in a 0-1 range in shaders even if a depth range is set; everywhere
  // else they return that depth range.
  // To test for this, we can create a temp buffer, clear it, set a depth range,

  Object::Ref<RenderTargetGL> test_rt1;
  Object::Ref<RenderTargetGL> test_rt2;

  test_rt1 = Object::New<RenderTargetGL>(this, 32, 32, true, true, true, true,
                                         false, false, false);
  BA_DEBUG_CHECK_GL_ERROR;
  test_rt2 = Object::New<RenderTargetGL>(this, 32, 32, true, false, true, false,
                                         false, false, false);
  BA_DEBUG_CHECK_GL_ERROR;

  // This screws up some qualcomm chips.
  SetDepthRange(0.0f, 0.5f);

  // Draw a flat color plane into our first render target.
  SetDepthWriting(true);
  SetDepthTesting(true);
  SetBlend(false);
  SetDoubleSided_(false);
  test_rt1->DrawBegin(true, 1.0f, 1.0f, 1.0f, 1.0f);
  ProgramSimpleGL* p = simple_color_prog_;
  p->Bind();
  p->SetColor(1, 0, 1);
  g_base->graphics_server->ModelViewReset();
  g_base->graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);
  GetActiveProgram_()->PrepareToDraw();
  screen_mesh_->Bind();
  screen_mesh_->Draw(DrawType::kTriangles);
  BA_DEBUG_CHECK_GL_ERROR;

  // Now draw into a second buffer the difference between the depth tex
  // lookup and the gl frag depth.
  SetDepthWriting(false);
  SetDepthTesting(false);
  SetBlend(false);
  SetDoubleSided_(false);
  test_rt2->DrawBegin(false, 1.0f, 1.0f, 1.0f, 1.0f);
  p = simple_tex_dtest_prog_;
  p->Bind();
  g_base->graphics_server->ModelViewReset();
  g_base->graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);
  p->SetColorTexture(test_rt1->framebuffer()->depth_texture());
  GetActiveProgram_()->PrepareToDraw();
  screen_mesh_->Bind();
  screen_mesh_->Draw(DrawType::kTriangles);
  BA_DEBUG_CHECK_GL_ERROR;

  // Now sample a pixel from our render-target. If the depths matched, the
  // value will be 0; otherwise it'll be 30 or so (allow a bit of leeway to
  // account for dithering/etc.).
  uint8_t buffer[16] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  glReadPixels(0, 0, 2, 2, GL_RGBA, GL_UNSIGNED_BYTE, buffer);

  // Sample 4 pixels to reduce effects of dithering.
  funky_depth_issue_ =
      ((buffer[0] + buffer[4] + buffer[8] + buffer[12]) / 4 >= 15);
  funky_depth_issue_set_ = true;

  BA_DEBUG_CHECK_GL_ERROR;
}

void RendererGL::PushGroupMarker(const char* label) {
  BA_GL_PUSH_GROUP_MARKER(label);
}
void RendererGL::PopGroupMarker() { BA_GL_POP_GROUP_MARKER(); }

void RendererGL::InvalidateFramebuffer(bool color, bool depth,
                                       bool target_read_framebuffer) {
  BA_DEBUG_CHECK_GL_ERROR;

  // Currently this is ES only for us.
#if BA_OPENGL_IS_ES

  if (invalidate_framebuffer_support()) {
    GLenum attachments[5];
    // Need to use different flags for the main framebuffer.
    int count = 0;
    if (active_framebuffer_ == 0 && !target_read_framebuffer) {
      if (color) {
        attachments[count++] = GL_COLOR;
      }
      if (depth) {
        attachments[count++] = GL_DEPTH;
      }
    } else {
      if (color) {
        attachments[count++] = GL_COLOR_ATTACHMENT0;
      }
      if (depth) {
        attachments[count++] = GL_DEPTH_ATTACHMENT;
      }

      glInvalidateFramebuffer(
          target_read_framebuffer ? GL_READ_FRAMEBUFFER : GL_FRAMEBUFFER, count,
          attachments);
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }
#else
  // Make noise if we should be doing this here too at some point.
  assert(!invalidate_framebuffer_support());
#endif  // BA_OPENGL_IS_ES
}

RendererGL::~RendererGL() {
  assert(g_base->app_adapter->InGraphicsContext());
  printf("FIXME: need to unload renderer on destroy.\n");
  // Unload();
  BA_DEBUG_CHECK_GL_ERROR;
}

void RendererGL::UseProgram_(ProgramGL* p) {
  if (p != current_program_) {
    glUseProgram(p->program());
    current_program_ = p;
  }
}

void RendererGL::SyncGLState_() {
  BA_DEBUG_CHECK_GL_ERROR;

#if BA_RIFT_BUILD
  if (g_core->vr_mode()) {
    glFrontFace(GL_CCW);
  }
  BA_DEBUG_CHECK_GL_ERROR;
#endif  // BA_RIFT_BUILD

  active_tex_unit_ = -1;      // force a set next time
  active_framebuffer_ = -1;   // ditto
  active_array_buffer_ = -1;  // ditto
  for (int i = 0; i < kMaxGLTexUnitsUsed; i++) {
    bound_textures_2d_[i] = -1;        // ditto
    bound_textures_cube_map_[i] = -1;  // ditto
  }
  glUseProgram(0);
  BA_DEBUG_CHECK_GL_ERROR;
  current_program_ = nullptr;
  current_vertex_array_ = 0;

  glBindVertexArray(0);
  BA_DEBUG_CHECK_GL_ERROR;

  // Wack these out so the next call will definitely call glViewport.
  viewport_x_ = -9999;
  viewport_y_ = -9999;
  viewport_width_ = -9999;
  viewport_height_ = -9999;

  glDisable(GL_BLEND);
  blend_ = false;

  // Currently we only ever write to an alpha buffer for our vr flat overlay
  // texture, and in that case we need alpha to accumulate; not get
  // overwritten. could probably enable this everywhere but I don't know if
  // it's supported on all hardware or slower.
  if (g_core->vr_mode()) {
#if BA_PLATFORM_WINDOWS
    if (glBlendFuncSeparate == nullptr) {
      FatalError(
          "VR mode is not supported by your GPU (no glBlendFuncSeparate); Try "
          "updating your drivers?...");
    }
#endif
    glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE,
                        GL_ONE_MINUS_SRC_ALPHA);
    BA_DEBUG_CHECK_GL_ERROR;
  } else {
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    BA_DEBUG_CHECK_GL_ERROR;
  }
  blend_premult_ = false;
  glEnable(GL_CULL_FACE);
  glCullFace(GL_BACK);
  BA_DEBUG_CHECK_GL_ERROR;
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
  BA_DEBUG_CHECK_GL_ERROR;
}

#define GET_MESH_DATA(TYPE, VAR)                              \
  auto* VAR = static_cast<TYPE*>(mesh_data->renderer_data()); \
  assert(VAR&& VAR == dynamic_cast<TYPE*>(mesh_data->renderer_data()))

#define GET_INDEX_BUFFER()                                                   \
  assert(buffer != buffers.end());                                           \
  assert(index_size != index_sizes.end());                                   \
  MeshIndexBuffer16* indices16{nullptr};                                     \
  MeshIndexBuffer32* indices32{nullptr};                                     \
  assert(*index_size == 4 || *index_size == 2);                              \
  bool use_indices32 = (*index_size == 4);                                   \
  if (use_indices32) {                                                       \
    indices32 = static_cast<MeshIndexBuffer32*>(buffer->get());              \
    assert(indices32                                                         \
           && indices32 == dynamic_cast<MeshIndexBuffer32*>(buffer->get())); \
  } else {                                                                   \
    indices16 = static_cast<MeshIndexBuffer16*>(buffer->get());              \
    assert(indices16                                                         \
           && indices16 == dynamic_cast<MeshIndexBuffer16*>(buffer->get())); \
  }                                                                          \
  index_size++;                                                              \
  buffer++

#define GET_BUFFER(TYPE, VAR)                              \
  assert(buffer != buffers.end());                         \
  auto* VAR = static_cast<TYPE*>(buffer->get());           \
  assert(VAR&& VAR == dynamic_cast<TYPE*>(buffer->get())); \
  buffer++

// Takes all latest mesh data from the client side and applies it to our gl
// implementations.
void RendererGL::UpdateMeshes(
    const std::vector<Object::Ref<MeshDataClientHandle> >& meshes,
    const std::vector<int8_t>& index_sizes,
    const std::vector<Object::Ref<MeshBufferBase> >& buffers) {
  auto index_size = index_sizes.begin();
  auto buffer = buffers.begin();
  for (auto&& mesh : meshes) {
    // For each mesh, plug in the latest and greatest buffers it should be
    // using.
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
  // We should have gone through all lists exactly.
  assert(index_size == index_sizes.end());
  assert(buffer == buffers.end());
}
#undef GET_MESH_DATA
#undef GET_BUFFER
#undef GET_INDEX_BUFFER

void RendererGL::StandardPostProcessSetup_(ProgramPostProcessGL* p,
                                           const RenderPass& pass) {
  auto* cam_target = static_cast<RenderTargetGL*>(camera_render_target());
  assert(cam_target
         && dynamic_cast<RenderTargetGL*>(camera_render_target())
                == cam_target);
  RenderPass* beauty_pass = pass.frame_def()->beauty_pass();
  assert(beauty_pass);
  SetDoubleSided_(false);
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

  // FIXME: These sort of fudge-factors don't belong here in the renderer.
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
            SetDoubleSided_(false);
            SetBlend(false);
            ProgramSimpleGL* p = simple_color_prog_;
            p->Bind();
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            p->SetColor(r, g, b);
            break;
          }
          case ShadingType::kSimpleColorTransparent: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            ProgramSimpleGL* p = simple_color_prog_;
            p->Bind();
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            p->SetColor(r, g, b, a);
            break;
          }
          case ShadingType::kSimpleColorTransparentDoubleSided: {
            SetDoubleSided_(true);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            ProgramSimpleGL* p = simple_color_prog_;
            p->Bind();
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            p->SetColor(r, g, b, a);
            break;
          }
          case ShadingType::kSimpleTexture: {
            SetDoubleSided_(false);
            SetBlend(false);
            ProgramSimpleGL* p = simple_tex_prog_;
            p->Bind();
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparent: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ProgramSimpleGL* p = simple_tex_mod_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransFlatness: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, flatness;
            buffer->GetFloats(&r, &g, &b, &a, &flatness);
            ProgramSimpleGL* p = simple_tex_mod_flatness_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetFlatness(flatness);
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentShadow: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, shadow_offset_x, shadow_offset_y, shadow_blur,
                shadow_opacity;
            buffer->GetFloats(&r, &g, &b, &a, &shadow_offset_x,
                              &shadow_offset_y, &shadow_blur, &shadow_opacity);
            ProgramSimpleGL* p = simple_tex_mod_shadow_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureAsset* t = buffer->GetTexture();
            const TextureAsset* t_mask = buffer->GetTexture();
            p->SetColorTexture(t);
            // If this isn't a full-res texture, ramp down the blurring we
            // do.
            p->SetShadow(shadow_offset_x, shadow_offset_y,
                         std::max(0.0f, shadow_blur), shadow_opacity);
            p->SetMaskUV2Texture(t_mask);
            break;
          }
          case ShadingType::kSimpleTexModulatedTransShadowFlatness: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, shadow_offset_x, shadow_offset_y, shadow_blur,
                shadow_opacity, flatness;
            buffer->GetFloats(&r, &g, &b, &a, &shadow_offset_x,
                              &shadow_offset_y, &shadow_blur, &shadow_opacity,
                              &flatness);
            ProgramSimpleGL* p = simple_tex_mod_shadow_flatness_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureAsset* t = buffer->GetTexture();
            const TextureAsset* t_mask = buffer->GetTexture();
            p->SetColorTexture(t);
            // If this isn't a full-res texture, ramp down the blurring we
            // do.
            p->SetShadow(shadow_offset_x, shadow_offset_y,
                         std::max(0.0f, shadow_blur), shadow_opacity);
            p->SetMaskUV2Texture(t_mask);
            p->SetFlatness(flatness);
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentGlow: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, glow_amount, glow_blur;
            buffer->GetFloats(&r, &g, &b, &a, &glow_amount, &glow_blur);
            ProgramSimpleGL* p = simple_tex_mod_glow_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureAsset* t = buffer->GetTexture();
            p->SetColorTexture(t);

            // Glow.
            p->SetGlow(glow_amount, std::max(0.0f, glow_blur));
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentGlowMaskUV2: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, glow_amount, glow_blur;
            buffer->GetFloats(&r, &g, &b, &a, &glow_amount, &glow_blur);
            ProgramSimpleGL* p = simple_tex_mod_glow_maskuv2_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            const TextureAsset* t = buffer->GetTexture();
            p->SetColorTexture(t);
            const TextureAsset* t_mask = buffer->GetTexture();
            p->SetMaskUV2Texture(t_mask);
            // Glow.
            p->SetGlow(glow_amount, std::max(0.0f, glow_blur));
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentDoubleSided: {
            SetDoubleSided_(true);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ProgramSimpleGL* p = simple_tex_mod_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulated: {
            SetDoubleSided_(false);
            SetBlend(false);
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            ProgramSimpleGL* p = simple_tex_mod_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedColorized: {
            SetDoubleSided_(false);
            SetBlend(false);
            float r, g, b, colorize_r, colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &colorize_r, &colorize_g,
                              &colorize_b);
            ProgramSimpleGL* p = simple_tex_mod_colorized_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorizeTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedColorized2: {
            SetDoubleSided_(false);
            SetBlend(false);
            float r, g, b, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &colorize_r, &colorize_g, &colorize_b,
                              &colorize2_r, &colorize2_g, &colorize2_b);
            ProgramSimpleGL* p = simple_tex_mod_colorized2_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorize2Color(colorize2_r, colorize2_g, colorize2_b);
            break;
          }
          case ShadingType::kSimpleTextureModulatedColorized2Masked: {
            SetDoubleSided_(false);
            SetBlend(false);
            float r, g, b, a, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            ProgramSimpleGL* p = simple_tex_mod_colorized2_masked_prog_;
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
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, colorize_r, colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b);
            ProgramSimpleGL* p = simple_tex_mod_colorized_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetColorizeColor(colorize_r, colorize_g, colorize_b);
            p->SetColorizeTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSimpleTextureModulatedTransparentColorized2: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            ProgramSimpleGL* p = simple_tex_mod_colorized2_prog_;
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
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, colorize_r, colorize_g, colorize_b, colorize2_r,
                colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &a, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            ProgramSimpleGL* p = simple_tex_mod_colorized2_masked_prog_;
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
            SetDoubleSided_(false);
            SetBlend(false);
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            ProgramObjectGL* p = obj_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetVignetteTexture(vignette_tex_);
            break;
          }
          case ShadingType::kSmoke: {
            SetDoubleSided_(true);
            SetBlend(true);
            SetBlendPremult(true);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ProgramSmokeGL* p = smoke_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            break;
          }
          case ShadingType::kSmokeOverlay: {
            SetDoubleSided_(true);
            SetBlend(true);
            SetBlendPremult(true);
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ProgramSmokeGL* p = smoke_overlay_prog_;
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
            ProgramPostProcessGL* p = postprocess_distort_prog_;
            StandardPostProcessSetup_(p, pass);
            p->SetDistort(distort);
            break;
          }
          case ShadingType::kPostProcess: {
            ProgramPostProcessGL* p = postprocess_prog_;
            StandardPostProcessSetup_(p, pass);
            break;
          }
          case ShadingType::kPostProcessEyes: {
            assert(postprocess_eyes_prog_);
            ProgramPostProcessGL* p = postprocess_eyes_prog_;
            StandardPostProcessSetup_(p, pass);
            break;
          }
          case ShadingType::kSprite: {
            SetDoubleSided_(false);
            SetBlend(true);
            SetBlendPremult(true);

            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            bool overlay = static_cast<bool>(buffer->GetInt());
            bool cam_aligned = static_cast<bool>(buffer->GetInt());

            ProgramSpriteGL* p;
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
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());

            SetBlend(true);
            SetBlendPremult(premult);

            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ProgramObjectGL* p = obj_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetVignetteTexture(vignette_tex_);
            break;
          }
          case ShadingType::kObjectLightShadow: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            int world_space = buffer->GetInt();
            float r, g, b;
            buffer->GetFloats(&r, &g, &b);
            ProgramObjectGL* p = world_space ? obj_lightshad_worldspace_prog_
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectLightShadowTransparent: {
            SetDoubleSided_(false);
            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            float r, g, b, a;
            buffer->GetFloats(&r, &g, &b, &a);
            ProgramObjectGL* p = obj_lightshad_transparent_prog_;
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);

            break;
          }
          case ShadingType::kObjectReflectLightShadow: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            int world_space = buffer->GetInt();
            float r, g, b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b);
            ProgramObjectGL* p = world_space
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowDoubleSided: {
            // FIXME: This shader isn't actually flipping the normal for the
            //  back side of the face.. for now we don't care though.
            SetDoubleSided_(true);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            int world_space = buffer->GetInt();

            // Verified.
            float r, g, b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b);
            ProgramObjectGL* p;

            // Testing why reflection is wonky.
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowColorized: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            float r, g, b, reflect_r, reflect_g, reflect_b, colorize_r,
                colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b,
                              &colorize_r, &colorize_g, &colorize_b);
            ProgramObjectGL* p = obj_refl_lightshad_colorize_prog_;
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowColorized2: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());

            float r, g, b, reflect_r, reflect_g, reflect_b, colorize_r,
                colorize_g, colorize_b, colorize2_r, colorize2_g, colorize2_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b,
                              &colorize_r, &colorize_g, &colorize_b,
                              &colorize2_r, &colorize2_g, &colorize2_b);
            ProgramObjectGL* p = obj_refl_lightshad_colorize2_prog_;
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowAdd: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());
            float r, g, b, add_r, add_g, add_b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &add_r, &add_g, &add_b, &reflect_r,
                              &reflect_g, &reflect_b);
            ProgramObjectGL* p = obj_refl_lightshad_add_prog_;
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowAddColorized: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());

            float r, g, b, add_r, add_g, add_b, reflect_r, reflect_g, reflect_b,
                colorize_r, colorize_g, colorize_b;
            buffer->GetFloats(&r, &g, &b, &add_r, &add_g, &add_b, &reflect_r,
                              &reflect_g, &reflect_b, &colorize_r, &colorize_g,
                              &colorize_b);
            ProgramObjectGL* p = obj_refl_lightshad_add_colorize_prog_;
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflectLightShadowAddColorized2: {
            SetDoubleSided_(false);
            SetBlend(false);
            auto light_shadow = static_cast<LightShadowType>(buffer->GetInt());

            float r, g, b, add_r, add_g, add_b, reflect_r, reflect_g, reflect_b,
                colorize_r, colorize_g, colorize_b, colorize2_r, colorize2_g,
                colorize2_b;
            buffer->GetFloats(&r, &g, &b, &add_r, &add_g, &add_b, &reflect_r,
                              &reflect_g, &reflect_b, &colorize_r, &colorize_g,
                              &colorize_b, &colorize2_r, &colorize2_g,
                              &colorize2_b);
            ProgramObjectGL* p = obj_refl_lightshad_add_colorize2_prog_;
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
                light_shadow_tex = 0;
                FatalError("Unhandled LightShadowType.");
            }
            p->SetLightShadowTexture(light_shadow_tex);
            break;
          }
          case ShadingType::kObjectReflect: {
            SetDoubleSided_(false);
            SetBlend(false);
            int world_space = buffer->GetInt();
            // verified
            float r, g, b, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &reflect_r, &reflect_g, &reflect_b);
            ProgramObjectGL* p =
                world_space ? obj_refl_worldspace_prog_ : obj_refl_prog_;
            p->Bind();
            p->SetColor(r, g, b);
            p->SetColorTexture(buffer->GetTexture());
            p->SetReflectionTexture(buffer->GetTexture());  // reflection
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            break;
          }
          case ShadingType::kObjectReflectTransparent: {
            SetDoubleSided_(false);

            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, reflect_r, reflect_g, reflect_b;
            buffer->GetFloats(&r, &g, &b, &a, &reflect_r, &reflect_g,
                              &reflect_b);
            ProgramObjectGL* p = obj_refl_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetReflectionTexture(buffer->GetTexture());  // reflection
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            break;
          }
          case ShadingType::kObjectReflectAddTransparent: {
            SetDoubleSided_(false);

            bool premult = static_cast<bool>(buffer->GetInt());
            SetBlend(true);
            SetBlendPremult(premult);
            float r, g, b, a, add_r, add_g, add_b, reflect_r, reflect_g,
                reflect_b;
            buffer->GetFloats(&r, &g, &b, &a, &add_r, &add_g, &add_b,
                              &reflect_r, &reflect_g, &reflect_b);
            ProgramObjectGL* p = obj_refl_add_transparent_prog_;
            p->Bind();
            p->SetColor(r, g, b, a);
            p->SetColorTexture(buffer->GetTexture());
            p->SetAddColor(add_r, add_g, add_b);
            p->SetReflectionTexture(buffer->GetTexture());  // reflection
            p->SetReflectionMult(reflect_r, reflect_g, reflect_b);
            break;
          }
          case ShadingType::kShield: {
            SetDoubleSided_(true);
            SetBlend(true);
            SetBlendPremult(true);
            ProgramShieldGL* p = shield_prog_;
            p->Bind();
            p->SetDepthTexture(
                static_cast<RenderTargetGL*>(camera_render_target())
                    ->framebuffer()
                    ->depth_texture());
            break;
          }
          case ShadingType::kSpecial: {
            SetDoubleSided_(false);

            // If we ever need to use non-blend version of this in real
            // renders, we should split off a non-blend version.
            SetBlend(true);
            SetBlendPremult(true);
            auto source = (SpecialComponent::Source)buffer->GetInt();
            ProgramSimpleGL* p = simple_tex_mod_prog_;
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
                FatalError("Unhandled SpecialComponent type.");
            }
            break;
          }
          default:
            FatalError("Unhandled Shader Type.");
        }
        break;
      }
      case RenderCommandBuffer::Command::kSimpleComponentInlineColor: {
        float r, g, b, a;
        buffer->GetFloats(&r, &g, &b, &a);
        auto* p = static_cast<ProgramSimpleGL*>(GetActiveProgram_());
        assert(p != nullptr
               && p == dynamic_cast<ProgramSimpleGL*>(GetActiveProgram_()));
        p->SetColor(r, g, b, a);
        break;
      }
      case RenderCommandBuffer::Command::kObjectComponentInlineColor: {
        float r, g, b, a;
        buffer->GetFloats(&r, &g, &b, &a);
        auto* p = static_cast<ProgramObjectGL*>(GetActiveProgram_());
        assert(p != nullptr
               && p == dynamic_cast<ProgramObjectGL*>(GetActiveProgram_()));
        p->SetColor(r, g, b, a);
        break;
      }
      case RenderCommandBuffer::Command::kObjectComponentInlineAddColor: {
        float r, g, b;
        buffer->GetFloats(&r, &g, &b);
        auto* p = static_cast<ProgramObjectGL*>(GetActiveProgram_());
        assert(p != nullptr
               && p == dynamic_cast<ProgramObjectGL*>(GetActiveProgram_()));
        p->SetAddColor(r, g, b);
        break;
      }
      case RenderCommandBuffer::Command::kDrawMeshAsset: {
        int flags = buffer->GetInt();
        const MeshAsset* m = buffer->GetMesh();
        assert(m);
        auto mesh =
            static_cast_check_type<MeshAssetDataGL*>(m->renderer_data());
        assert(mesh);

        // if they don't wanna draw in reflections...
        if ((flags & kMeshDrawFlagNoReflection) && drawing_reflection()) {
          break;
        }
        GetActiveProgram_()->PrepareToDraw();
        mesh->Bind();
        mesh->Draw();
        break;
      }
      case RenderCommandBuffer::Command::kDrawMeshAssetInstanced: {
        int flags = buffer->GetInt();
        const MeshAsset* m = buffer->GetMesh();
        assert(m);
        auto mesh =
            static_cast_check_type<MeshAssetDataGL*>(m->renderer_data());
        assert(mesh);
        Matrix44f* mats;
        int count;
        mats = buffer->GetMatrices(&count);
        // if they don't wanna draw in reflections...
        if ((flags & kMeshDrawFlagNoReflection) && drawing_reflection()) {
          break;
        }
        mesh->Bind();
        for (int i = 0; i < count; i++) {
          g_base->graphics_server->PushTransform();
          g_base->graphics_server->MultMatrix(mats[i]);
          GetActiveProgram_()->PrepareToDraw();
          mesh->Draw();
          g_base->graphics_server->PopTransform();
        }
        break;
      }
        // NOLINTNEXTLINE(bugprone-branch-clone)
      case RenderCommandBuffer::Command::kBeginDebugDrawTriangles: {
        GetActiveProgram_()->PrepareToDraw();
#if BA_GL_ENABLE_DEBUG_DRAW_COMMANDS
        glBegin(GL_TRIANGLES);
#endif
        break;
      }
      case RenderCommandBuffer::Command::kBeginDebugDrawLines: {
        GetActiveProgram_()->PrepareToDraw();
#if BA_GL_ENABLE_DEBUG_DRAW_COMMANDS
        glBegin(GL_LINES);
#endif
        break;
      }
      case RenderCommandBuffer::Command::kEndDebugDraw: {
#if BA_GL_ENABLE_DEBUG_DRAW_COMMANDS
        glEnd();
#endif
        break;
      }
      case RenderCommandBuffer::Command::kDebugDrawVertex3: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
#if BA_GL_ENABLE_DEBUG_DRAW_COMMANDS
        glVertex3f(x, y, z);
#endif
        break;
      }
      case RenderCommandBuffer::Command::kDrawMesh: {
        int flags = buffer->GetInt();
        auto* mesh = buffer->GetMeshRendererData<MeshDataGL>();
        assert(mesh);
        if ((flags & kMeshDrawFlagNoReflection) && drawing_reflection()) {
          break;
        }
        GetActiveProgram_()->PrepareToDraw();
        mesh->Bind();
        mesh->Draw(DrawType::kTriangles);
        break;
      }
      case RenderCommandBuffer::Command::kDrawScreenQuad: {
        // Save proj/mv matrices, set up to draw a simple screen quad at the
        // back of our depth range, draw, and restore.
        Matrix44f old_model_view_matrix =
            g_base->graphics_server->model_view_matrix();
        Matrix44f old_projection_matrix =
            g_base->graphics_server->projection_matrix();
        g_base->graphics_server->SetModelViewMatrix(kMatrix44fIdentity);
        g_base->graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 0.01f);
        GetActiveProgram_()->PrepareToDraw();
        screen_mesh_->Bind();
        screen_mesh_->Draw(DrawType::kTriangles);
        g_base->graphics_server->SetModelViewMatrix(old_model_view_matrix);
        g_base->graphics_server->SetProjectionMatrix(old_projection_matrix);
        break;
      }
      case RenderCommandBuffer::Command::kScissorPush: {
        Rect r;
        buffer->GetFloats(&r.l, &r.b, &r.r, &r.t);

        // Convert scissor-values from model space to view space.
        // this of course assumes there's no rotations and whatnot.
        Vector3f bot_left_pt = g_base->graphics_server->model_view_matrix()
                               * Vector3f(r.l, r.b, 0);
        Vector3f top_right_pt = g_base->graphics_server->model_view_matrix()
                                * Vector3f(r.r, r.t, 0);
        r.l = bot_left_pt.x;
        r.b = bot_left_pt.y;
        r.r = top_right_pt.x;
        r.t = top_right_pt.y;
        ScissorPush_(r, render_target);
        break;
      }
      case RenderCommandBuffer::Command::kScissorPop: {
        ScissorPop_(render_target);
        break;
      }
      case RenderCommandBuffer::Command::kPushTransform: {
        g_base->graphics_server->PushTransform();
        break;
      }
      case RenderCommandBuffer::Command::kTranslate2: {
        float x, y;
        buffer->GetFloats(&x, &y);
        g_base->graphics_server->Translate(Vector3f(x, y, 0));
        break;
      }
      case RenderCommandBuffer::Command::kTranslate3: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
        g_base->graphics_server->Translate(Vector3f(x, y, z));
        break;
      }
      case RenderCommandBuffer::Command::kCursorTranslate: {
        float x, y;
        g_base->app_adapter->CursorPositionForDraw(&x, &y);
        g_base->graphics_server->Translate(Vector3f(x, y, 0));
        break;
      }
      case RenderCommandBuffer::Command::kScale2: {
        float x, y;
        buffer->GetFloats(&x, &y);
        g_base->graphics_server->scale(Vector3f(x, y, 1.0f));
        break;
      }
      case RenderCommandBuffer::Command::kScale3: {
        float x, y, z;
        buffer->GetFloats(&x, &y, &z);
        g_base->graphics_server->scale(Vector3f(x, y, z));
        break;
      }
      case RenderCommandBuffer::Command::kScaleUniform: {
        float s = buffer->GetFloat();
        g_base->graphics_server->scale(Vector3f(s, s, s));
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
        g_base->graphics_server->Translate(Vector3f(
            t.x * g_base->graphics_server->screen_virtual_width(),
            t.y * g_base->graphics_server->screen_virtual_height(), 0));
        break;
      }
      case RenderCommandBuffer::Command::kRotate: {
        float angle, x, y, z;
        buffer->GetFloats(&angle, &x, &y, &z);
        g_base->graphics_server->Rotate(angle, Vector3f(x, y, z));
        break;
      }
      case RenderCommandBuffer::Command::kMultMatrix: {
        g_base->graphics_server->MultMatrix(*(buffer->GetMatrix()));
        break;
      }
      case RenderCommandBuffer::Command::kPopTransform: {
        g_base->graphics_server->PopTransform();
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
  BA_DEBUG_CHECK_GL_ERROR;
  auto* src = static_cast<RenderTargetGL*>(src_in);
  assert(src && src == dynamic_cast<RenderTargetGL*>(src_in));
  auto* dst = static_cast<RenderTargetGL*>(dst_in);
  assert(dst && dst == dynamic_cast<RenderTargetGL*>(dst_in));

  bool do_shader_blit{true};

  // If they want depth we *MUST* use glBlitFramebuffer and can't have
  // linear interp.
  if (depth) {
    assert(!force_shader_mode);
    linear_interpolation = false;
  }
  // Use glBlitFramebuffer when its available.
  // FIXME: This should be available in ES3.
  // #if !BA_PLATFORM_IOS_TVOS
  if (!force_shader_mode) {
    do_shader_blit = false;
    BA_DEBUG_CHECK_GL_ERROR;
    glBindFramebuffer(GL_READ_FRAMEBUFFER, src->GetFramebufferID());
    BA_DEBUG_CHECK_GL_ERROR;
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst->GetFramebufferID());
    BA_DEBUG_CHECK_GL_ERROR;

    glBlitFramebuffer(0, 0, static_cast<GLint>(src->physical_width()),
                      static_cast<GLint>(src->physical_height()), 0, 0,
                      static_cast<GLint>(dst->physical_width()),
                      static_cast<GLint>(dst->physical_height()),
                      depth ? (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                            : GL_COLOR_BUFFER_BIT,
                      linear_interpolation ? GL_LINEAR : GL_NEAREST);
    BA_DEBUG_CHECK_GL_ERROR;
    if (invalidate_source) {
      InvalidateFramebuffer(true, depth, true);
    }
  } else {
    do_shader_blit = true;
  }
  // #endif
  if (do_shader_blit) {
    SetDepthWriting(false);
    SetDepthTesting(false);
    dst_in->DrawBegin(false);
    g_base->graphics_server->ModelViewReset();
    g_base->graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);

    // Copied from ShadingType::kSimpleColor.
    SetDoubleSided_(false);
    SetBlend(false);
    ProgramSimpleGL* p = simple_tex_prog_;
    p->Bind();
    p->SetColorTexture(src->framebuffer()->texture());
    GetActiveProgram_()->PrepareToDraw();
    screen_mesh_->Bind();
    screen_mesh_->Draw(DrawType::kTriangles);
    BA_DEBUG_CHECK_GL_ERROR;
  }
}

void RendererGL::ScissorPush_(const Rect& r_in, RenderTarget* render_target) {
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
  if (clip.l > clip.r) {
    clip.l = clip.r;
  }
  if (clip.b > clip.t) {
    clip.b = clip.t;
  }
  auto* glt = static_cast<RenderTargetGL*>(render_target);
  float scissor_scale_x =
      static_cast<RenderTargetGL*>(render_target)->GetScissorScaleX();
  float scissor_scale_y =
      static_cast<RenderTargetGL*>(render_target)->GetScissorScaleY();
  glScissor(static_cast<GLint>(glt->GetScissorX(clip.l)),
            static_cast<GLint>(glt->GetScissorY(clip.b)),
            static_cast<GLsizei>(scissor_scale_x * (clip.r - clip.l)),
            static_cast<GLsizei>(scissor_scale_y * (clip.t - clip.b)));
  BA_DEBUG_CHECK_GL_ERROR;
}

void RendererGL::ScissorPop_(RenderTarget* render_target) {
  BA_PRECONDITION(!scissor_rects_.empty());
  scissor_rects_.pop_back();
  if (scissor_rects_.empty()) {
    glDisable(GL_SCISSOR_TEST);
  } else {
    Rect clip = scissor_rects_.back();
    if (clip.l > clip.r) {
      clip.l = clip.r;
    }
    if (clip.b > clip.t) {
      clip.b = clip.t;
    }
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
  BA_DEBUG_CHECK_GL_ERROR;
}

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

// FIXME FIXME FIXME FIXME:
//
// Turning off GL_DEPTH_TEST also disables depth writing which we may not
// want. It sounds like the proper thing to do in that case is leave
// GL_DEPTH_TEST on and set glDepthFunc(GL_ALWAYS).

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
#if !BA_GL_ENABLE_BLEND
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
      if (g_core->vr_mode()) {
        glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE,
                            GL_ONE_MINUS_SRC_ALPHA);
      } else {
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
      }
    }
  }
}

void RendererGL::BindVertexArray_(GLuint v) {
  if (v != current_vertex_array_) {
    glBindVertexArray(v);
    BA_DEBUG_CHECK_GL_ERROR;
    current_vertex_array_ = v;
  }
}

void RendererGL::SetDoubleSided_(bool d) {
  if (double_sided_ != d) {
    double_sided_ = d;
    if (double_sided_) {
      glDisable(GL_CULL_FACE);
    } else {
      glEnable(GL_CULL_FACE);
    }
  }
}

void RendererGL::UpdateVignetteTex_(bool force) {
  if (force || vignette_quality_ != g_base->graphics_server->quality()
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
    vignette_quality_ = g_base->graphics_server->quality();

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

    glGetError();  // Clear any error.
    BindTexture_(GL_TEXTURE_2D, vignette_tex_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
                 GL_UNSIGNED_BYTE, data);

    // If 32 bit failed for some reason, attempt 16.
    GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
      static bool reported = false;
      if (!reported) {
        g_core->logging->Log(
            LogName::kBaGraphics, LogLevel::kError,
            "32-bit vignette creation failed; falling back to 16.");
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
      BindTexture_(GL_TEXTURE_2D, vignette_tex_);
      glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB,
                   GL_UNSIGNED_SHORT_5_6_5, data2);
      BA_DEBUG_CHECK_GL_ERROR;
    }
    if (force) {
      BA_GL_LABEL_OBJECT(GL_TEXTURE, vignette_tex_, "vignetteTex");
    }
  }
}

auto RendererGL::GetFunkyDepthIssue_() -> bool {
  if (!funky_depth_issue_set_) {
    BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kError,
                "fetching funky depth issue but not set");
  }
  return funky_depth_issue_;
}

#if BA_PLATFORM_ANDROID
std::string RendererGL::GetAutoAndroidRes() {
  assert(g_base->app_adapter->InGraphicsContext());

  // Simplifying this to just 1080p for anything we label 'speedy' and 720p
  // for everything else.
  if (is_speedy_android_device_) {
    return "1080p";
  }
  return "720p";
}
#endif  // BA_PLATFORM_ANDROID

auto RendererGL::GetAutoTextureQuality() -> TextureQuality {
  assert(g_base->app_adapter->InGraphicsContext());

  TextureQuality qual{TextureQuality::kHigh};

#if BA_PLATFORM_ANDROID
  {
    // Lets be cheaper in VR mode since we have to draw twice.
    if (g_core->vr_mode()) {
      qual = TextureQuality::kHigh;
    } else {
      qual = TextureQuality::kHigh;
    }
  }
#else  // BA_PLATFORM_ANDROID

  // On other platforms (iOS, mac, pc, etc) just default to high.
  qual = TextureQuality::kHigh;

#endif  // BA_PLATFORM_ANDROID

  return qual;
}

auto RendererGL::GetAutoGraphicsQuality() -> GraphicsQuality {
  assert(g_base->app_adapter->InGraphicsContext());
  GraphicsQuality q{GraphicsQuality::kMedium};
#if BA_PLATFORM_ANDROID
  // lets be cheaper in VR mode since we draw twice..
  if (g_core->vr_mode()) {
    q = GraphicsQuality::kMedium;
  } else {
    if (is_speedy_android_device_) {
      q = GraphicsQuality::kHigher;
    } else {
      q = GraphicsQuality::kHigh;
    }
  }
#else
  // Elsewhere just assume we're working with something speedy.
  q = GraphicsQuality::kHigher;
#endif
  return q;
}

void RendererGL::RetainShader_(ProgramGL* p) { shaders_.emplace_back(p); }

void RendererGL::Load() {
  assert(g_base->app_adapter->InGraphicsContext());
  assert(!data_loaded_);
  assert(g_base->graphics_server->graphics_quality()
         != GraphicsQuality::kUnset);
  BA_DEBUG_CHECK_GL_ERROR;
  if (!got_screen_framebuffer_) {
    got_screen_framebuffer_ = true;

    // Grab the current framebuffer and consider that to be our 'screen'
    // framebuffer. This can be 0 for the main framebuffer or can be
    // something else.
    screen_framebuffer_ = GLGetInt(GL_FRAMEBUFFER_BINDING);
  }
  Renderer::Load();
  int high_qual_pp_flag =
      g_base->graphics_server->quality() >= GraphicsQuality::kHigher
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
  BA_DEBUG_CHECK_GL_ERROR;
  ProgramGL* p;
  p = simple_color_prog_ = new ProgramSimpleGL(this, SHD_MODULATE);
  RetainShader_(p);
  p = simple_tex_prog_ = new ProgramSimpleGL(this, SHD_TEXTURE);
  RetainShader_(p);
  p = simple_tex_dtest_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_DEPTH_BUG_TEST);
  RetainShader_(p);

  // Have to run this after we've created the shader to be able to test it.
  CheckFunkyDepthIssue_();
  p = simple_tex_mod_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_MODULATE);
  RetainShader_(p);
  p = simple_tex_mod_flatness_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_FLATNESS);
  RetainShader_(p);
  p = simple_tex_mod_shadow_prog_ = new ProgramSimpleGL(
      this, SHD_TEXTURE | SHD_MODULATE | SHD_SHADOW | SHD_MASK_UV2);
  RetainShader_(p);
  p = simple_tex_mod_shadow_flatness_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_SHADOW
                                    | SHD_MASK_UV2 | SHD_FLATNESS);
  RetainShader_(p);
  p = simple_tex_mod_glow_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_GLOW);
  RetainShader_(p);
  p = simple_tex_mod_glow_maskuv2_prog_ = new ProgramSimpleGL(
      this, SHD_TEXTURE | SHD_MODULATE | SHD_GLOW | SHD_MASK_UV2);
  RetainShader_(p);
  p = simple_tex_mod_colorized_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_COLORIZE);
  RetainShader_(p);
  p = simple_tex_mod_colorized2_prog_ = new ProgramSimpleGL(
      this, SHD_TEXTURE | SHD_MODULATE | SHD_COLORIZE | SHD_COLORIZE2);
  RetainShader_(p);
  p = simple_tex_mod_colorized2_masked_prog_ =
      new ProgramSimpleGL(this, SHD_TEXTURE | SHD_MODULATE | SHD_COLORIZE
                                    | SHD_COLORIZE2 | SHD_MASKED);
  RetainShader_(p);
  p = obj_prog_ = new ProgramObjectGL(this, 0);
  RetainShader_(p);
  p = obj_transparent_prog_ = new ProgramObjectGL(this, SHD_OBJ_TRANSPARENT);
  RetainShader_(p);
  p = obj_lightshad_transparent_prog_ =
      new ProgramObjectGL(this, SHD_OBJ_TRANSPARENT | SHD_LIGHT_SHADOW);
  RetainShader_(p);
  p = obj_refl_prog_ = new ProgramObjectGL(this, SHD_REFLECTION);
  RetainShader_(p);
  p = obj_refl_worldspace_prog_ =
      new ProgramObjectGL(this, SHD_REFLECTION | SHD_WORLD_SPACE_PTS);
  RetainShader_(p);
  p = obj_refl_transparent_prog_ =
      new ProgramObjectGL(this, SHD_REFLECTION | SHD_OBJ_TRANSPARENT);
  RetainShader_(p);
  p = obj_refl_add_transparent_prog_ =
      new ProgramObjectGL(this, SHD_REFLECTION | SHD_ADD | SHD_OBJ_TRANSPARENT);
  RetainShader_(p);
  p = obj_lightshad_prog_ = new ProgramObjectGL(this, SHD_LIGHT_SHADOW);
  RetainShader_(p);
  p = obj_lightshad_worldspace_prog_ =
      new ProgramObjectGL(this, SHD_LIGHT_SHADOW | SHD_WORLD_SPACE_PTS);
  RetainShader_(p);
  p = obj_refl_lightshad_prog_ =
      new ProgramObjectGL(this, SHD_LIGHT_SHADOW | SHD_REFLECTION);
  RetainShader_(p);
  p = obj_refl_lightshad_worldspace_prog_ = new ProgramObjectGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_WORLD_SPACE_PTS);
  RetainShader_(p);
  p = obj_refl_lightshad_colorize_prog_ = new ProgramObjectGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_COLORIZE);
  RetainShader_(p);
  p = obj_refl_lightshad_colorize2_prog_ = new ProgramObjectGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_COLORIZE | SHD_COLORIZE2);
  RetainShader_(p);
  p = obj_refl_lightshad_add_prog_ =
      new ProgramObjectGL(this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_ADD);
  RetainShader_(p);
  p = obj_refl_lightshad_add_colorize_prog_ = new ProgramObjectGL(
      this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_ADD | SHD_COLORIZE);
  RetainShader_(p);
  p = obj_refl_lightshad_add_colorize2_prog_ =
      new ProgramObjectGL(this, SHD_LIGHT_SHADOW | SHD_REFLECTION | SHD_ADD
                                    | SHD_COLORIZE | SHD_COLORIZE2);
  RetainShader_(p);
  p = smoke_prog_ =
      new ProgramSmokeGL(this, SHD_OBJ_TRANSPARENT | SHD_WORLD_SPACE_PTS);
  RetainShader_(p);
  p = smoke_overlay_prog_ = new ProgramSmokeGL(
      this, SHD_OBJ_TRANSPARENT | SHD_WORLD_SPACE_PTS | SHD_OVERLAY);
  RetainShader_(p);
  p = sprite_prog_ = new ProgramSpriteGL(this, SHD_COLOR);
  RetainShader_(p);
  p = sprite_camalign_prog_ =
      new ProgramSpriteGL(this, SHD_CAMERA_ALIGNED | SHD_COLOR);
  RetainShader_(p);
  p = sprite_camalign_overlay_prog_ =
      new ProgramSpriteGL(this, SHD_CAMERA_ALIGNED | SHD_OVERLAY | SHD_COLOR);
  RetainShader_(p);
  p = blur_prog_ = new ProgramBlurGL(this, 0);
  RetainShader_(p);
  p = shield_prog_ = new ProgramShieldGL(this, 0);
  RetainShader_(p);

  // Conditional seems to be a *very* slight win on some architectures (A7),
  // a loss on some (A5) and a wash on some (Adreno 320). Gonna wait before
  // a clean win before turning it on.
  p = postprocess_prog_ = new ProgramPostProcessGL(this, high_qual_pp_flag);
  RetainShader_(p);
  if (g_base->graphics_server->quality() >= GraphicsQuality::kHigher) {
    p = postprocess_eyes_prog_ = new ProgramPostProcessGL(this, SHD_EYES);
    RetainShader_(p);
  } else {
    postprocess_eyes_prog_ = nullptr;
  }
  p = postprocess_distort_prog_ =
      new ProgramPostProcessGL(this, SHD_DISTORT | high_qual_pp_flag);
  RetainShader_(p);

  // Generate our random value texture.
  // TODO(ericf): move this to assets.
  {
    glGenTextures(1, &random_tex_);
    BindTexture_(GL_TEXTURE_2D, random_tex_);
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
    BA_GL_LABEL_OBJECT(GL_TEXTURE, random_tex_, "randomTex");
  }

  // Generate our vignette tex.
  // TODO(ericf): move this to assets.
  {
    glGenTextures(1, &vignette_tex_);
    BindTexture_(GL_TEXTURE_2D, vignette_tex_);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    UpdateVignetteTex_(true);
  }

  // Let's pre-fill our recyclable mesh-datas list to reduce the need to
  // make more which could cause hitches.
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

  // Re-sync with the GL state since we might be dealing with a new
  // context/etc.
  SyncGLState_();
  BA_DEBUG_CHECK_GL_ERROR;
  data_loaded_ = true;
}

void RendererGL::PostLoad() {
  Renderer::PostLoad();
  // Control may pass back to cardboard after we've finished loading but
  // before we render, (in cases such as graphics settings switches) ...and
  // it seems they can screw up our VAOs if we leave them bound. So lets be
  // defensive.
#if BA_VARIANT_CARDBOARD
  SyncGLState_();
#endif
}

void RendererGL::Unload() {
  assert(g_base->app_adapter->InGraphicsContext());
  BA_DEBUG_CHECK_GL_ERROR;
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
  if (!g_base->graphics_server->renderer_context_lost()) {
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
  BA_DEBUG_CHECK_GL_ERROR;
}

auto RendererGL::NewMeshAssetData(const MeshAsset& model)
    -> Object::Ref<MeshAssetRendererData> {
  return Object::New<MeshAssetRendererData, MeshAssetDataGL>(model, this);
}

auto RendererGL::NewTextureData(const TextureAsset& texture)
    -> Object::Ref<TextureAssetRendererData> {
  return Object::New<TextureAssetRendererData, TextureDataGL>(texture, this);
}

auto RendererGL::NewScreenRenderTarget() -> RenderTarget* {
  return Object::NewDeferred<RenderTargetGL>(this);
}

auto RendererGL::NewFramebufferRenderTarget(int width, int height,
                                            bool linear_interp, bool depth,
                                            bool texture, bool depth_texture,
                                            bool high_quality, bool msaa,
                                            bool alpha)
    -> Object::Ref<RenderTarget> {
  return Object::New<RenderTarget, RenderTargetGL>(
      this, width, height, linear_interp, depth, texture, depth_texture,
      high_quality, msaa, alpha);
}

auto RendererGL::NewMeshData(MeshDataType mesh_type, MeshDrawType draw_type)
    -> MeshRendererData* {
  switch (mesh_type) {
    case MeshDataType::kIndexedSimpleSplit: {
      MeshDataSimpleSplitGL* data;
      // Use a recycled one if we've got one; otherwise create a new one.
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
      // Use a recycled one if we've got one; otherwise create a new one.
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
      // Use a recycled one if we've got one; otherwise create a new one.
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
      // Use a recycled one if we've got one; otherwise create a new one.
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
      // Use a recycled one if we've got one; otherwise create a new one.
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
      // Use a recycled one if we've got one; otherwise create a new one.
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
  // When we're done with mesh-data we keep it around for recycling. It
  // seems that killing off VAO/VBOs can be hitchy (on mac at least). Hmmm
  // should we have some sort of threshold at which point we kill off some?

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
  // Lets only check periodically. I doubt it hurts to run this all the time
  // but just in case.
  error_check_counter_++;
  if (error_check_counter_ > 120) {
    error_check_counter_ = 0;
    BA_CHECK_GL_ERROR;
  }
}

void RendererGL::DrawDebug() {
  if (explicit_bool(false)) {
    // Draw our cam buffer if we have it.
    if (has_camera_render_target()) {
      SetDepthWriting(false);
      SetDepthTesting(false);
      SetDoubleSided_(false);
      SetBlend(false);
      ProgramSimpleGL* p = simple_tex_prog_;
      p->Bind();

      g_base->graphics_server->ModelViewReset();
      g_base->graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);

      float tx = -0.6f;
      float ty = 0.6f;

      g_base->graphics_server->PushTransform();
      g_base->graphics_server->scale(Vector3f(0.4f, 0.4f, 0.4f));
      g_base->graphics_server->Translate(Vector3f(-1.3f, -0.7f, 0));

      // Draw cam buffer.
      g_base->graphics_server->PushTransform();
      g_base->graphics_server->Translate(Vector3f(tx, ty, 0));
      tx += 0.2f;
      ty -= 0.25f;
      g_base->graphics_server->scale(Vector3f(0.5f, 0.5f, 1.0f));
      p->SetColorTexture(static_cast<RenderTargetGL*>(camera_render_target())
                             ->framebuffer()
                             ->texture());
      GetActiveProgram_()->PrepareToDraw();
      screen_mesh_->Bind();
      screen_mesh_->Draw(DrawType::kTriangles);
      g_base->graphics_server->PopTransform();

      // Draw blur buffers.
      if (explicit_bool(false)) {
        for (auto&& i : blur_buffers_) {
          g_base->graphics_server->PushTransform();
          g_base->graphics_server->Translate(Vector3f(tx, ty, 0));
          tx += 0.2f;
          ty -= 0.25f;
          g_base->graphics_server->scale(Vector3f(0.5f, 0.5f, 1.0f));
          p->SetColorTexture(i->texture());
          GetActiveProgram_()->PrepareToDraw();
          screen_mesh_->Bind();
          screen_mesh_->Draw(DrawType::kTriangles);
          g_base->graphics_server->PopTransform();
        }
      }
      g_base->graphics_server->PopTransform();
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
        (g_base->graphics_server->quality() >= GraphicsQuality::kHigher);
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
          false,              // depth_tex
          high_quality_fbos,  // high_quality
          false,              // msaa
          false               // alpha
          ));                 // NOLINT(whitespace/parens)
    }

    // Final redundant one (we run an extra blur without down-rezing).
    if (g_base->graphics_server->quality() >= GraphicsQuality::kHigher)
      blur_buffers_.push_back(Object::New<FramebufferObjectGL>(
          this, w, h,
          true,   // linear_interp
          false,  // depth
          true,   // tex
          false,  // depth_tex
          false,  // high_quality
          false,  // msaa
          false   // alpha
          ));     // NOLINT(whitespace/parens)
  }

  // Ok now go through and do the blurring.
  SetDepthWriting(false);
  SetDepthTesting(false);
  g_base->graphics_server->ModelViewReset();
  g_base->graphics_server->SetOrthoProjection(-1, 1, -1, 1, -1, 1);
  SetDoubleSided_(false);
  SetBlend(false);

  ProgramBlurGL* p = blur_prog_;
  p->Bind();

  FramebufferObjectGL* src_fb =
      static_cast<RenderTargetGL*>(camera_render_target())->framebuffer();
  for (auto&& i : blur_buffers_) {
    FramebufferObjectGL* fb = i.get();
    assert(fb);
    fb->Bind();
    SetViewport_(0, 0, fb->width(), fb->height());
    InvalidateFramebuffer(true, false, false);
    p->SetColorTexture(src_fb->texture());
    if (fb->width() == src_fb->width()) {  // Our last one is equal res.
      p->SetPixelSize(2.0f / static_cast<float>(fb->width()),
                      2.0f / static_cast<float>(fb->height()));
    } else {
      p->SetPixelSize(1.0f / static_cast<float>(fb->width()),
                      1.0f / static_cast<float>(fb->height()));
    }
    GetActiveProgram_()->PrepareToDraw();
    screen_mesh_->Bind();
    screen_mesh_->Draw(DrawType::kTriangles);
    src_fb = fb;
  }
}

void RendererGL::CardboardDisableScissor() { glDisable(GL_SCISSOR_TEST); }

void RendererGL::CardboardEnableScissor() { glEnable(GL_SCISSOR_TEST); }

void RendererGL::VREyeRenderBegin() {
  assert(g_core->vr_mode());

  // On rift we need to turn off srgb conversion for each eye render so we
  // can dump our linear data into oculus' srgb buffer as-is. (we really
  // should add proper srgb support to the engine at some point).
#if BA_RIFT_BUILD
  glDisable(GL_FRAMEBUFFER_SRGB);
#endif  // BA_RIFT_BUILD

  screen_framebuffer_ = GLGetInt(GL_FRAMEBUFFER_BINDING);
}

#if BA_VR_BUILD
void RendererGL::VRSyncRenderStates() {
  // GL state has been mucked with outside of our code; let's resync stuff.
  SyncGLState_();
}
#endif  // BA_VR_BUILD

void RendererGL::RenderFrameDefEnd() {
  // Need to set some states to keep cardboard happy.
#if BA_VARIANT_CARDBOARD
  if (g_core->vr_mode()) {
    SyncGLState_();
    glEnable(GL_SCISSOR_TEST);
  }
#endif  // BA_VARIANT_CARDBOARD
}

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL
