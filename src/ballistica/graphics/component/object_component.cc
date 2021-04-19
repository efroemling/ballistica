// Released under the MIT License. See LICENSE for details.

#include "ballistica/graphics/component/object_component.h"

namespace ballistica {

void ObjectComponent::WriteConfig() {
  // If they didn't give us a texture, just use a blank white texture.
  // This is not a common case and easier than forking all our shaders to
  // create non-textured versions.
  if (!texture_.exists()) {
    texture_ = g_media->GetTexture(SystemTextureID::kWhite);
  }
  if (reflection_ == ReflectionType::kNone) {
    assert(!double_sided_);               // Unsupported combo.
    assert(!colorize_texture_.exists());  // Unsupported combo.
    assert(!have_color_add_);             // Unsupported combo.
    if (light_shadow_ == LightShadowType::kNone) {
      if (transparent_) {
        ConfigForShading(ShadingType::kObjectTransparent);
        cmd_buffer_->PutInt(premultiplied_);
        cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
        cmd_buffer_->PutTexture(texture_);
      } else {
        ConfigForShading(ShadingType::kObject);
        cmd_buffer_->PutFloats(color_r_, color_g_, color_b_);
        cmd_buffer_->PutTexture(texture_);
      }
    } else {
      if (transparent_) {
        assert(!world_space_);  // Unsupported combo.
        ConfigForShading(ShadingType::kObjectLightShadowTransparent);
        cmd_buffer_->PutInt(premultiplied_);
        cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
        cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_);
        cmd_buffer_->PutTexture(texture_);
      } else {
        ConfigForShading(ShadingType::kObjectLightShadow);
        cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
        cmd_buffer_->PutInt(world_space_);
        cmd_buffer_->PutFloats(color_r_, color_g_, color_b_);
        cmd_buffer_->PutTexture(texture_);
      }
    }
  } else {
    if (light_shadow_ == LightShadowType::kNone) {
      assert(!double_sided_);               // Unsupported combo.
      assert(!colorize_texture_.exists());  // Unsupported combo.
      if (transparent_) {
        assert(!world_space_);  // Unsupported combo.
        if (have_color_add_) {
          ConfigForShading(ShadingType::kObjectReflectAddTransparent);
          cmd_buffer_->PutInt(premultiplied_);
          cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_,
                                 color_add_r_, color_add_g_, color_add_b_,
                                 reflection_scale_r_, reflection_scale_g_,
                                 reflection_scale_b_);
          cmd_buffer_->PutTexture(texture_);
          SystemCubeMapTextureID r =
              Graphics::CubeMapFromReflectionType(reflection_);
          cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
        } else {
          ConfigForShading(ShadingType::kObjectReflectTransparent);
          cmd_buffer_->PutInt(premultiplied_);
          cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_a_,
                                 reflection_scale_r_, reflection_scale_g_,
                                 reflection_scale_b_);
          cmd_buffer_->PutTexture(texture_);
          SystemCubeMapTextureID r =
              Graphics::CubeMapFromReflectionType(reflection_);
          cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
        }
      } else {
        ConfigForShading(ShadingType::kObjectReflect);
        cmd_buffer_->PutInt(world_space_);
        cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                               reflection_scale_r_, reflection_scale_g_,
                               reflection_scale_b_);
        cmd_buffer_->PutTexture(texture_);
        SystemCubeMapTextureID r =
            Graphics::CubeMapFromReflectionType(reflection_);
        cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
      }
    } else {
      // With add.
      assert(!transparent_);  // Unsupported combo.
      if (!have_color_add_) {
        if (colorize_texture_.exists()) {
          assert(!double_sided_);  // Unsupported combo.
          assert(!world_space_);   // Unsupported combo.
          if (do_colorize_2_) {
            ConfigForShading(ShadingType::kObjectReflectLightShadowColorized2);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutFloats(
                color_r_, color_g_, color_b_, reflection_scale_r_,
                reflection_scale_g_, reflection_scale_b_, colorize_color_r_,
                colorize_color_g_, colorize_color_b_, colorize_color2_r_,
                colorize_color2_g_, colorize_color2_b_);
            cmd_buffer_->PutTexture(texture_);
            cmd_buffer_->PutTexture(colorize_texture_);
            SystemCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
          } else {
            ConfigForShading(ShadingType::kObjectReflectLightShadowColorized);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                                   reflection_scale_r_, reflection_scale_g_,
                                   reflection_scale_b_, colorize_color_r_,
                                   colorize_color_g_, colorize_color_b_);
            cmd_buffer_->PutTexture(texture_);
            cmd_buffer_->PutTexture(colorize_texture_);
            SystemCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
          }
        } else {
          if (double_sided_) {
            ConfigForShading(ShadingType::kObjectReflectLightShadowDoubleSided);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutInt(world_space_);
            cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                                   reflection_scale_r_, reflection_scale_g_,
                                   reflection_scale_b_);
            cmd_buffer_->PutTexture(texture_);
            SystemCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
          } else {
            ConfigForShading(ShadingType::kObjectReflectLightShadow);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutInt(world_space_);
            cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                                   reflection_scale_r_, reflection_scale_g_,
                                   reflection_scale_b_);
            cmd_buffer_->PutTexture(texture_);
            SystemCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
          }
        }
      } else {
        assert(!double_sided_);  // Unsupported combo.
        assert(!world_space_);   // Unsupported config.
        if (colorize_texture_.exists()) {
          if (do_colorize_2_) {
            ConfigForShading(
                ShadingType::kObjectReflectLightShadowAddColorized2);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutFloats(
                color_r_, color_g_, color_b_, color_add_r_, color_add_g_,
                color_add_b_, reflection_scale_r_, reflection_scale_g_,
                reflection_scale_b_, colorize_color_r_, colorize_color_g_,
                colorize_color_b_, colorize_color2_r_, colorize_color2_g_,
                colorize_color2_b_);
            cmd_buffer_->PutTexture(texture_);
            cmd_buffer_->PutTexture(colorize_texture_);
            SystemCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
          } else {
            ConfigForShading(
                ShadingType::kObjectReflectLightShadowAddColorized);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_add_r_,
                                   color_add_g_, color_add_b_,
                                   reflection_scale_r_, reflection_scale_g_,
                                   reflection_scale_b_, colorize_color_r_,
                                   colorize_color_g_, colorize_color_b_);
            cmd_buffer_->PutTexture(texture_);
            cmd_buffer_->PutTexture(colorize_texture_);
            SystemCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
          }
        } else {
          ConfigForShading(ShadingType::kObjectReflectLightShadowAdd);
          cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
          cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_add_r_,
                                 color_add_g_, color_add_b_,
                                 reflection_scale_r_, reflection_scale_g_,
                                 reflection_scale_b_);
          cmd_buffer_->PutTexture(texture_);
          SystemCubeMapTextureID r =
              Graphics::CubeMapFromReflectionType(reflection_);
          cmd_buffer_->PutCubeMapTexture(g_media->GetCubeMapTexture(r));
        }
      }
    }
  }
}

}  // namespace ballistica
