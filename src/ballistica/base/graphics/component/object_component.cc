// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/component/object_component.h"

#include "ballistica/base/assets/assets.h"

namespace ballistica::base {

void ObjectComponent::WriteConfig() {
  // If they didn't give us a texture, just use a blank white texture.
  // This is not a common case and easier than forking all our shaders to
  // create non-textured versions.
  if (!texture_.exists()) {
    texture_ = g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesWhite);
  }
  // A premultiplied-alpha texture (KTX2 DFD flag; decision #23) forces
  // premult-blend, OR'd with the caller's manual flag (which still
  // independently forces it for additive effects). The default white
  // builtin above is straight, so unprovided-texture draws are unaffected.
  bool premult_blend = premultiplied_ || texture_->premultiplied();

  // For a premultiplied texture drawn with a *straight* modulate color, the
  // caller's rgb must be premultiplied by alpha here so faded objects (e.g.
  // mesh fades on death/spawn) composite 'over' correctly under premult blend
  // (which adds rgb directly rather than weighting it by alpha). Only the
  // transparent shadings carry/use alpha; the opaque ones send rgb only. A
  // caller-managed premult (premultiplied_, e.g. additive glows) is left alone.
  // Mirrors the image_widget convention; see
  // docs/design/premultiplied-alpha.md.
  float cmul = (transparent_ && !premultiplied_ && texture_->premultiplied())
                   ? color_a_
                   : 1.0f;
  if (reflection_ == ReflectionType::kNone) {
    assert(!double_sided_);               // Unsupported combo.
    assert(!colorize_texture_.exists());  // Unsupported combo.
    assert(!have_color_add_);             // Unsupported combo.
    if (light_shadow_ == LightShadowType::kNone) {
      if (transparent_) {
        ConfigForShading(ShadingType::kObjectTransparent);
        cmd_buffer_->PutInt(premult_blend);
        cmd_buffer_->PutFloats(color_r_ * cmul, color_g_ * cmul,
                               color_b_ * cmul, color_a_);
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
        cmd_buffer_->PutInt(premult_blend);
        cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
        cmd_buffer_->PutFloats(color_r_ * cmul, color_g_ * cmul,
                               color_b_ * cmul, color_a_);
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
          cmd_buffer_->PutInt(premult_blend);
          cmd_buffer_->PutFloats(
              color_r_ * cmul, color_g_ * cmul, color_b_ * cmul, color_a_,
              color_add_r_, color_add_g_, color_add_b_, reflection_scale_r_,
              reflection_scale_g_, reflection_scale_b_);
          cmd_buffer_->PutTexture(texture_);
          BuiltinCubeMapTextureID r =
              Graphics::CubeMapFromReflectionType(reflection_);
          cmd_buffer_->PutCubeMapTexture(
              g_base->assets->BuiltinCubeMapTexture(r));
        } else {
          ConfigForShading(ShadingType::kObjectReflectTransparent);
          cmd_buffer_->PutInt(premult_blend);
          cmd_buffer_->PutFloats(color_r_ * cmul, color_g_ * cmul,
                                 color_b_ * cmul, color_a_, reflection_scale_r_,
                                 reflection_scale_g_, reflection_scale_b_);
          cmd_buffer_->PutTexture(texture_);
          BuiltinCubeMapTextureID r =
              Graphics::CubeMapFromReflectionType(reflection_);
          cmd_buffer_->PutCubeMapTexture(
              g_base->assets->BuiltinCubeMapTexture(r));
        }
      } else {
        ConfigForShading(ShadingType::kObjectReflect);
        cmd_buffer_->PutInt(world_space_);
        cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                               reflection_scale_r_, reflection_scale_g_,
                               reflection_scale_b_);
        cmd_buffer_->PutTexture(texture_);
        BuiltinCubeMapTextureID r =
            Graphics::CubeMapFromReflectionType(reflection_);
        cmd_buffer_->PutCubeMapTexture(
            g_base->assets->BuiltinCubeMapTexture(r));
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
            BuiltinCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(
                g_base->assets->BuiltinCubeMapTexture(r));
          } else {
            ConfigForShading(ShadingType::kObjectReflectLightShadowColorized);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                                   reflection_scale_r_, reflection_scale_g_,
                                   reflection_scale_b_, colorize_color_r_,
                                   colorize_color_g_, colorize_color_b_);
            cmd_buffer_->PutTexture(texture_);
            cmd_buffer_->PutTexture(colorize_texture_);
            BuiltinCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(
                g_base->assets->BuiltinCubeMapTexture(r));
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
            BuiltinCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(
                g_base->assets->BuiltinCubeMapTexture(r));
          } else {
            ConfigForShading(ShadingType::kObjectReflectLightShadow);
            cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
            cmd_buffer_->PutInt(world_space_);
            cmd_buffer_->PutFloats(color_r_, color_g_, color_b_,
                                   reflection_scale_r_, reflection_scale_g_,
                                   reflection_scale_b_);
            cmd_buffer_->PutTexture(texture_);
            BuiltinCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(
                g_base->assets->BuiltinCubeMapTexture(r));
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
            BuiltinCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(
                g_base->assets->BuiltinCubeMapTexture(r));
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
            BuiltinCubeMapTextureID r =
                Graphics::CubeMapFromReflectionType(reflection_);
            cmd_buffer_->PutCubeMapTexture(
                g_base->assets->BuiltinCubeMapTexture(r));
          }
        } else {
          ConfigForShading(ShadingType::kObjectReflectLightShadowAdd);
          cmd_buffer_->PutInt(static_cast<int>(light_shadow_));
          cmd_buffer_->PutFloats(color_r_, color_g_, color_b_, color_add_r_,
                                 color_add_g_, color_add_b_,
                                 reflection_scale_r_, reflection_scale_g_,
                                 reflection_scale_b_);
          cmd_buffer_->PutTexture(texture_);
          BuiltinCubeMapTextureID r =
              Graphics::CubeMapFromReflectionType(reflection_);
          cmd_buffer_->PutCubeMapTexture(
              g_base->assets->BuiltinCubeMapTexture(r));
        }
      }
    }
  }
}

}  // namespace ballistica::base
