// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_FRAMEBUFFER_OBJECT_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_FRAMEBUFFER_OBJECT_GL_H_

#if BA_ENABLE_OPENGL

#include <algorithm>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/framebuffer.h"

namespace ballistica::base {

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
    // Desktop stuff is always high-quality.
#if BA_PLATFORM_MACOS || BA_PLATFORM_LINUX || BA_PLATFORM_WINDOWS
    high_quality_ = true;
#endif

    // Things are finally getting to the point where we can default to
    // desktop quality on some mobile stuff.
#if BA_PLATFORM_ANDROID
    if (renderer_->is_tegra_k1_) {
      high_quality_ = true;
    }
#endif

    Load();
  }

  ~FramebufferObjectGL() override { Unload(); }

  void Load(bool force_low_quality = false) {
    if (loaded_) return;
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;
    GLenum status;
    BA_DEBUG_CHECK_GL_ERROR;
    glGenFramebuffers(1, &framebuffer_);
    renderer_->BindFramebuffer(framebuffer_);
    BA_DEBUG_CHECK_GL_ERROR;
    bool do_high_quality = high_quality_;
    if (force_low_quality) do_high_quality = false;
    int samples = 0;
    if (msaa_) {
      // Can't multisample with texture buffers currently.
      assert(!is_texture_ && !depth_is_texture_);

      int target_samples =
          renderer_->GetMSAASamplesForFramebuffer_(width_, height_);

      if (do_high_quality) {
        samples = std::min(target_samples, renderer_->msaa_max_samples_rgb8());
      } else {
        samples =
            std::min(target_samples, renderer_->msaa_max_samples_rgb565());
      }
    }
    if (is_texture_) {
      // Attach a texture for the color target.
      glGenTextures(1, &texture_);
      renderer_->BindTexture_(GL_TEXTURE_2D, texture_);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                      linear_interp_ ? GL_LINEAR : GL_NEAREST);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                      linear_interp_ ? GL_LINEAR : GL_NEAREST);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

      // On android/ios lets go with 16 bit unless they explicitly request
      // high quality.
#if BA_PLATFORM_ANDROID || BA_PLATFORM_IOS_TVOS
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
#if BA_PLATFORM_IOS_TVOS
      GLenum format =
          GL_RGB565;  // FIXME; need to pull ES3 headers in for GL_RGB8
#elif BA_PLATFORM_ANDROID
      GLenum format = do_high_quality ? GL_RGB8 : GL_RGB565;
#else
      GLenum format = GL_RGB8;
#endif
      glGenRenderbuffers(1, &render_buffer_);
      BA_DEBUG_CHECK_GL_ERROR;
      glBindRenderbuffer(GL_RENDERBUFFER, render_buffer_);
      BA_DEBUG_CHECK_GL_ERROR;
      if (samples > 0) {
#if BA_PLATFORM_IOS_TVOS
        throw Exception();
#else
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, samples, format,
                                         width_, height_);
#endif
      } else {
        glRenderbufferStorage(GL_RENDERBUFFER, format, width_, height_);
      }
      BA_DEBUG_CHECK_GL_ERROR;
      glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                                GL_RENDERBUFFER, render_buffer_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
    BA_DEBUG_CHECK_GL_ERROR;
    if (depth_) {
      if (depth_is_texture_) {
        glGenTextures(1, &depth_texture_);
        BA_DEBUG_CHECK_GL_ERROR;
        renderer_->BindTexture_(GL_TEXTURE_2D, depth_texture_);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        BA_DEBUG_CHECK_GL_ERROR;
        // FIXME: need to pull in ES3 stuff for iOS to get GL_DEPTH_COMPONENT24.
        // #if BA_PLATFORM_IOS_TVOS
        //         glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, width_,
        //         height_, 0,
        //                      GL_DEPTH_COMPONENT, GL_UNSIGNED_SHORT, nullptr);
        // #else
        if (do_high_quality) {
          // #if BA_PLATFORM_ANDROID
          //           assert(g_running_es3);
          // #endif  // BA_PLATFORM_ANDROID
          glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, width_, height_,
                       0, GL_DEPTH_COMPONENT, GL_UNSIGNED_INT, nullptr);
        } else {
          glTexImage2D(
              GL_TEXTURE_2D, 0,
              renderer_->gl_is_es() ? GL_DEPTH_COMPONENT16 : GL_DEPTH_COMPONENT,
              width_, height_, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_SHORT,
              nullptr);
        }
        // #endif  // BA_PLATFORM_IOS_TVOS

        BA_DEBUG_CHECK_GL_ERROR;

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                               GL_TEXTURE_2D, depth_texture_, 0);

        BA_DEBUG_CHECK_GL_ERROR;
      } else {
        // Just use a plain old renderbuffer if we don't need it as a texture
        // (this is more widely supported).
        glGenRenderbuffers(1, &depth_render_buffer_);
        BA_DEBUG_CHECK_GL_ERROR;
        glBindRenderbuffer(GL_RENDERBUFFER, depth_render_buffer_);
        BA_DEBUG_CHECK_GL_ERROR;

        if (samples > 0) {
          // #if BA_PLATFORM_IOS_TVOS
          //           throw Exception();
          // #else
          // (GL_DEPTH_COMPONENT24 not available in ES2 it looks like)
          bool do24;
          // #if BA_PLATFORM_ANDROID
          //           do24 = (do_high_quality && g_running_es3);
          // #else
          do24 = do_high_quality;
          // #endif

          glRenderbufferStorageMultisample(
              GL_RENDERBUFFER, samples,
              do24 ? GL_DEPTH_COMPONENT24 : GL_DEPTH_COMPONENT16, width_,
              height_);
          // (do_high_quality &&
          // g_running_es3)?GL_DEPTH_COMPONENT24:GL_DEPTH_COMPONENT16, _width,
          // _height);
          // #endif
        } else {
          // FIXME - need to pull in es3 headers to get GL_DEPTH_COMPONENT24 on
          //  iOS
          // #if BA_PLATFORM_IOS_TVOS
          //           GLenum format = GL_DEPTH_COMPONENT16;
          // #else
          // GL_DEPTH_COMPONENT24 not available in ES2 it looks like.
          GLenum format = (do_high_quality && renderer_->gl_is_es())
                              ? GL_DEPTH_COMPONENT24
                              : GL_DEPTH_COMPONENT16;
          // #endif

          glRenderbufferStorage(GL_RENDERBUFFER, format, width_, height_);
        }

        BA_DEBUG_CHECK_GL_ERROR;
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                  GL_RENDERBUFFER, depth_render_buffer_);
        BA_DEBUG_CHECK_GL_ERROR;
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
    //   Log(LogLevel::kInfo, "GOT SRGB!!!!!!!!!!!");
    // } else if (enc == GL_LINEAR) {
    //   Log(LogLevel::kInfo, "GOT LINEAR...");
    // } else {
    //   Log(LogLevel::kInfo, "GOT OTHER..");
    // }
    loaded_ = true;
  }

  void Unload() {
    assert(g_base->app_adapter->InGraphicsContext());
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

    if (!g_base->graphics_server->renderer_context_lost()) {
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
        BA_DEBUG_CHECK_GL_ERROR;
      }

      // If this one is current, make sure we re-bind next time.
      // (otherwise we might prevent a new framebuffer with a recycled id from
      // binding)
      if (renderer_->active_framebuffer_ == framebuffer_) {
        renderer_->active_framebuffer_ = -1;
      }
      glDeleteFramebuffers(1, &framebuffer_);
      BA_DEBUG_CHECK_GL_ERROR;
    }
    loaded_ = false;
  }

  void Bind() {
    assert(g_base->app_adapter->InGraphicsContext());
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
  GLuint framebuffer_{};
  GLuint texture_{};
  GLuint depth_texture_{};
  GLuint render_buffer_{};
  GLuint depth_render_buffer_{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_FRAMEBUFFER_OBJECT_GL_H_
