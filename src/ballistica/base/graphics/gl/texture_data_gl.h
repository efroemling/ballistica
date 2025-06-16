// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_TEXTURE_DATA_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_TEXTURE_DATA_GL_H_

#if BA_ENABLE_OPENGL

#include <algorithm>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/texture_asset_preload_data.h"
#include "ballistica/base/assets/texture_asset_renderer_data.h"
#include "ballistica/base/graphics/gl/renderer_gl.h"
#include "ballistica/base/graphics/graphics_server.h"

namespace ballistica::base {

class RendererGL::TextureDataGL : public TextureAssetRendererData {
 public:
  TextureDataGL(const TextureAsset& texture_in, RendererGL* renderer_in)
      : tex_media_(&texture_in), texture_(0), renderer_(renderer_in) {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;
    glGenTextures(1, &texture_);
    BA_DEBUG_CHECK_GL_ERROR;
  }

  ~TextureDataGL() override {
    if (!g_base->app_adapter->InGraphicsContext()) {
      g_core->logging->Log(LogName::kBaGraphics, LogLevel::kError,
                           "TextureDataGL dying outside of graphics thread.");
    } else {
      // If we're currently bound as anything, clear that out (otherwise a
      // new texture with that same ID won't be bindable).
      for (int i = 0; i < kMaxGLTexUnitsUsed; i++) {
        if ((renderer_->bound_textures_2d_[i]) == texture_) {
          renderer_->bound_textures_2d_[i] = -1;
        }
        if ((renderer_->bound_textures_cube_map_[i]) == texture_) {
          renderer_->bound_textures_cube_map_[i] = -1;
        }
      }
      if (!g_base->graphics_server->renderer_context_lost()) {
        glDeleteTextures(1, &texture_);
        BA_DEBUG_CHECK_GL_ERROR;
      }
    }
  }

  auto GetTexture() const -> GLuint { return texture_; }

  void Load() override {
    assert(g_base->app_adapter->InGraphicsContext());
    BA_DEBUG_CHECK_GL_ERROR;

    if (tex_media_->texture_type() == TextureType::k2D) {
      renderer_->BindTexture_(GL_TEXTURE_2D, texture_);
      const TextureAssetPreloadData* preload_data =
          &tex_media_->preload_datas()[0];
      int base_src_level = preload_data->base_level;
      assert(preload_data->buffers[base_src_level]);
      GraphicsQuality q = g_base->graphics_server->quality();

      // Determine whether to use anisotropic sampling on this texture:
      // basically all the UI stuff that is only ever seen from straight on
      // doesn't need it.
      bool allow_ani = true;

      // FIXME: filtering based on filename. Once we get this stuff on a
      // server we should include this as metadata instead.
      const char* n = tex_media_->file_name().c_str();

      // The following exceptions should *never* need aniso-sampling.
      {
        if (!strcmp(n, "fontBig")) {
          allow_ani = false;

          // Lets splurge on this for higher but not high (names over
          // characters might benefit, though most text doesnt).
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
        if (strstr(n, "ColorMask")) {
          allow_ani = false;  // character color-masks
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
        if (renderer_->anisotropic_support() && allow_ani) {
          glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT,
                          std::min(16.0f, renderer_->max_anisotropy()));
        }
      } else if (q >= GraphicsQuality::kHigh) {
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR);
        if (renderer_->anisotropic_support() && allow_ani)
          glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT,
                          std::min(16.0f, renderer_->max_anisotropy()));
      } else if (q >= GraphicsQuality::kMedium) {
        // In medium quality we don't do anisotropy but do trilinear.
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR);
      } else {
        // In low quality we do bilinear.
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

            // At the moment we always just let GL generate mipmaps for
            // uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          case TextureFormat::kRGBA_4444: {
            glTexImage2D(
                GL_TEXTURE_2D, level, GL_RGBA, preload_data->widths[src_level],
                preload_data->heights[src_level], 0, GL_RGBA,
                GL_UNSIGNED_SHORT_4_4_4_4, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps for
            // uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          case TextureFormat::kRGB_565: {
            glTexImage2D(
                GL_TEXTURE_2D, level, GL_RGB, preload_data->widths[src_level],
                preload_data->heights[src_level], 0, GL_RGB,
                GL_UNSIGNED_SHORT_5_6_5, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps for
            // uncompressed textures; is there any reason not to?
            glGenerateMipmap(GL_TEXTURE_2D);
            all_levels_handled = true;
            break;
          }
          case TextureFormat::kRGB_888: {
            glTexImage2D(GL_TEXTURE_2D, level, GL_RGB,
                         preload_data->widths[src_level],
                         preload_data->heights[src_level], 0, GL_RGB,
                         GL_UNSIGNED_BYTE, preload_data->buffers[src_level]);

            // At the moment we always just let GL generate mipmaps for
            // uncompressed textures; is there any reason not to?
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
        BA_DEBUG_CHECK_GL_ERROR;
      }
      BA_GL_LABEL_OBJECT(GL_TEXTURE, texture_, tex_media_->GetName().c_str());
    } else if (tex_media_->texture_type() == TextureType::kCubeMap) {
      // Cube map.
      renderer_->BindTexture_(GL_TEXTURE_CUBE_MAP, texture_);

      bool do_generate_mips = false;
      for (uint32_t i = 0; i < 6; i++) {
        const TextureAssetPreloadData* preload_data =
            &tex_media_->preload_datas()[i];
        int base_src_level = preload_data->base_level;
        assert(preload_data->buffers[base_src_level]);

        GraphicsQuality q = g_base->graphics_server->quality();

        // Do trilinear in higher quality; otherwise bilinear is good enough.
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
          BA_DEBUG_CHECK_GL_ERROR;
        }
      }

      // If we're generating remaining mips on the gpu, do so.
      if (do_generate_mips) {
        glGenerateMipmap(GL_TEXTURE_CUBE_MAP);
      }

      BA_GL_LABEL_OBJECT(GL_TEXTURE, texture_, tex_media_->GetName().c_str());
    } else {
      throw Exception();
    }
    BA_DEBUG_CHECK_GL_ERROR;
  }

 private:
  const TextureAsset* tex_media_;
  RendererGL* renderer_;
  GLuint texture_;
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_TEXTURE_DATA_GL_H_
