// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_RENDER_VIEW_DATA_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_RENDER_VIEW_DATA_GL_H_

#if BA_ENABLE_OPENGL

#include <vector>

#include "ballistica/base/graphics/gl/framebuffer_object_gl.h"
#include "ballistica/base/graphics/graphics_server.h"
#include "ballistica/base/graphics/renderer/render_view_renderer_data.h"

namespace ballistica::base {

/// What the GL renderer adds to the data held for each view: blurred
/// copies of the view's camera buffer and its vignette texture. Plain
/// state for the renderer's use, like the rest, aside from cleaning up
/// after itself.
struct RendererGL::RenderViewDataGL : public RenderViewRendererData {
  explicit RenderViewDataGL(RendererGL* renderer_in) : renderer(renderer_in) {}

  ~RenderViewDataGL() override { Unload(); }

  /// Let go of our GL objects. We can be set up again afterward (see
  /// RendererGL::LoadCurrentViewData()).
  void Unload() {
    assert(g_base->app_adapter->InGraphicsContext());
    blur_buffers.clear();
    if (vignette_tex != 0) {
      // If our texture is currently bound as anything, clear that out
      // (otherwise a new texture with that same id won't be bindable).
      for (int& i : renderer->bound_textures_2d_) {
        if (i == vignette_tex) {
          i = -1;
        }
      }
      if (!g_base->graphics_server->renderer_context_lost()) {
        glDeleteTextures(1, &vignette_tex);
      }
      vignette_tex = 0;
    }
  }

  RendererGL* renderer;

  // Progressively blurrier copies of the camera buffer, remade when
  // that buffer's size or the number of levels wanted changes.
  std::vector<Object::Ref<FramebufferObjectGL> > blur_buffers;
  int last_blur_res_count{};
  float last_cam_buffer_width{};
  float last_cam_buffer_height{};

  // The vignette texture, along with what it was last generated from
  // so we can tell when it needs redoing.
  GLuint vignette_tex{};
  GraphicsQuality vignette_tex_quality{};
  float vignette_tex_outer_r{};
  float vignette_tex_outer_g{};
  float vignette_tex_outer_b{};
  float vignette_tex_inner_r{};
  float vignette_tex_inner_g{};
  float vignette_tex_inner_b{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_RENDER_VIEW_DATA_GL_H_
