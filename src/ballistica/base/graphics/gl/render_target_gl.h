// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_RENDER_TARGET_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_RENDER_TARGET_GL_H_

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/framebuffer_object_gl.h"

namespace ballistica::base {

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
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;

    Bind();

#if BA_VARIANT_CARDBOARD
    int x, y;
    // Viewport offsets only apply to the screen render-target.
    if (type_ == Type::kScreen) {
      x = renderer_->VRGetViewportX();
      y = renderer_->VRGetViewportY();
    } else {
      x = 0;
      y = 0;
    }
    renderer_->SetViewport_(x, y, physical_width_, physical_height_);
#else
    renderer_->SetViewport_(0, 0, static_cast<GLsizei>(physical_width_),
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
              LogName::kBaGraphics, LogLevel::kWarning,
              "RendererGL: depth-writing not enabled when clearing depth");
        }
        clear_mask |= GL_DEPTH_BUFFER_BIT;
      }

      if (clear_mask != 0) {
        if (clear_mask & GL_COLOR_BUFFER_BIT) {
          glClearColor(clear_r, clear_g, clear_b, clear_a);
          BA_DEBUG_CHECK_GL_ERROR;
        }
        glClear(clear_mask);
        BA_DEBUG_CHECK_GL_ERROR;
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

  // Screen constructor.
  explicit RenderTargetGL(RendererGL* renderer)
      : RenderTarget(Type::kScreen), renderer_(renderer) {
    assert(g_base->app_adapter->InGraphicsContext());
    depth_ = true;

    // This will update our width/height values.
    OnScreenSizeChange();
  }

  // Framebuffer constructor.
  RenderTargetGL(RendererGL* renderer, int width, int height,
                 bool linear_interp, bool depth, bool texture,
                 bool depth_texture, bool high_quality, bool msaa, bool alpha)
      : RenderTarget(Type::kFramebuffer), renderer_(renderer) {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;
    framebuffer_ = Object::New<FramebufferObjectGL>(
        renderer, width, height, linear_interp, depth, texture, depth_texture,
        high_quality, msaa, alpha);
    physical_width_ = static_cast<float>(width);
    physical_height_ = static_cast<float>(height);
    depth_ = depth;
    BA_DEBUG_CHECK_GL_ERROR;
  }

 private:
  Object::Ref<FramebufferObjectGL> framebuffer_;
  RendererGL* renderer_{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_RENDER_TARGET_GL_H_
