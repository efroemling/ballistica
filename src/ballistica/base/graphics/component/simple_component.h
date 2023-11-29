// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

/// Used for UI and overlays and things; no world tinting/etc is applied.
class SimpleComponent : public RenderComponent {
 public:
  explicit SimpleComponent(RenderPass* pass) : RenderComponent(pass) {}

  void SetPremultiplied(bool val) {
    EnsureConfiguring();
    premultiplied_ = val;
  }

  void SetTransparent(bool val) {
    EnsureConfiguring();
    transparent_ = val;
  }

  void SetTexture(TextureAsset* t) {
    EnsureConfiguring();
    texture_ = t;
  }

  void SetTexture(const Object::Ref<TextureAsset>& t) {
    EnsureConfiguring();
    texture_ = t;
  }

  /// Used with colorize color 1 and 2. Red areas of the texture will get
  /// multiplied by colorize-color1 and green areas by colorize-color2.
  void SetColorizeTexture(TextureAsset* t) {
    EnsureConfiguring();
    colorize_texture_ = t;
  }

  /// Red multiplies source color, green adds colorize1-color, and blue adds
  /// white (currently requires colorize1 and colorize 2 to be set).
  void SetMaskTexture(TextureAsset* t) {
    EnsureConfiguring();
    mask_texture_ = t;
  }

  void SetMaskUV2Texture(TextureAsset* t) {
    EnsureConfiguring();
    mask_uv2_texture_ = t;
  }

  void ClearMaskUV2Texture() {
    EnsureConfiguring();
    mask_uv2_texture_.Clear();
  }

  void SetDoubleSided(bool enable) {
    EnsureConfiguring();
    double_sided_ = enable;
  }

  void SetColor(float r, float g, float b, float a = 1.0f) {
    // We support fast inline color changes with drawing streams (avoids
    // having to re-send a whole configure for every color change).

    // Make sure to only allow this if we have a color already; otherwise we
    // need to config since we might be implicitly switch shaders by setting
    // color.
    if (state_ == State::kDrawing && have_color_) {
      cmd_buffer_->PutCommand(
          RenderCommandBuffer::Command::kSimpleComponentInlineColor);
      cmd_buffer_->PutFloats(r, g, b, a);
    } else {
      EnsureConfiguring();
      have_color_ = true;
    }
    color_r_ = r;
    color_g_ = g;
    color_b_ = b;
    color_a_ = a;
  }

  void SetColorizeColor(float r, float g, float b, float a = 1.0f) {
    EnsureConfiguring();
    colorize_color_r_ = r;
    colorize_color_g_ = g;
    colorize_color_b_ = b;
    colorize_color_a_ = a;
  }

  void SetColorizeColor2(float r, float g, float b, float a = 1.0f) {
    EnsureConfiguring();
    colorize_color2_r_ = r;
    colorize_color2_g_ = g;
    colorize_color2_b_ = b;
    colorize_color2_a_ = a;
    do_colorize_2_ = true;
  }

  void SetShadow(float offset_x, float offset_y, float blur, float opacity) {
    EnsureConfiguring();
    shadow_offset_x_ = offset_x;
    shadow_offset_y_ = offset_y;
    shadow_blur_ = blur;
    shadow_opacity_ = opacity;
  }

  void SetGlow(float amount, float blur) {
    EnsureConfiguring();
    glow_amount_ = amount;
    glow_blur_ = blur;
  }

  void SetFlatness(float flatness) {
    EnsureConfiguring();
    flatness_ = flatness;
  }

 protected:
  void WriteConfig() override;

 protected:
  bool do_colorize_2_{};
  bool transparent_{};
  bool premultiplied_{};
  bool have_color_{};
  bool double_sided_{};
  float color_r_{1.0f};
  float color_g_{1.0f};
  float color_b_{1.0f};
  float color_a_{1.0f};
  float colorize_color_r_{1.0f};
  float colorize_color_g_{1.0f};
  float colorize_color_b_{1.0f};
  float colorize_color_a_{1.0f};
  float colorize_color2_r_{1.0f};
  float colorize_color2_g_{1.0f};
  float colorize_color2_b_{1.0f};
  float colorize_color2_a_{1.0f};
  float shadow_offset_x_{};
  float shadow_offset_y_{};
  float shadow_blur_{};
  float shadow_opacity_{};
  float glow_amount_{};
  float glow_blur_{};
  float flatness_{};
  Object::Ref<TextureAsset> texture_;
  Object::Ref<TextureAsset> colorize_texture_;
  Object::Ref<TextureAsset> mask_texture_;
  Object::Ref<TextureAsset> mask_uv2_texture_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_
