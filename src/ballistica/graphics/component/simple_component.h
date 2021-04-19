// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_
#define BALLISTICA_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_

#include "ballistica/graphics/component/render_component.h"

namespace ballistica {

// used for UI and overlays and things - no world tinting/etc is applied
class SimpleComponent : public RenderComponent {
 public:
  explicit SimpleComponent(RenderPass* pass)
      : RenderComponent(pass),
        color_r_(1.0f),
        color_g_(1.0f),
        color_b_(1.0f),
        color_a_(1.0f),
        colorize_color_r_(1.0f),
        colorize_color_g_(1.0f),
        colorize_color_b_(1.0f),
        colorize_color_a_(1.0f),
        colorize_color2_r_(1.0f),
        colorize_color2_g_(1.0f),
        colorize_color2_b_(1.0f),
        colorize_color2_a_(1.0f),
        shadow_offset_x_(0.0f),
        shadow_offset_y_(0.0f),
        shadow_blur_(0.0f),
        shadow_opacity_(0.0f),
        glow_amount_(0.0f),
        glow_blur_(0.0f),
        flatness_(0.0f),
        transparent_(false),
        premultiplied_(false),
        have_color_(false),
        double_sided_(false),
        do_colorize_2_(false) {}
  void SetPremultiplied(bool val) {
    EnsureConfiguring();
    premultiplied_ = val;
  }
  void SetTransparent(bool val) {
    EnsureConfiguring();
    transparent_ = val;
  }
  void SetTexture(TextureData* t) {
    EnsureConfiguring();
    texture_ = t;
  }
  void SetTexture(const Object::Ref<Texture>& t_in) {
    EnsureConfiguring();
    if (t_in.exists()) {
      texture_ = t_in->texture_data();
    } else {
      texture_.Clear();
    }
  }
  // used with colorize color 1 and 2
  // red areas of the texture will get multiplied by colorize-color1
  // and green areas by colorize-color2
  void SetColorizeTexture(const Object::Ref<Texture>& t_in) {
    EnsureConfiguring();
    if (t_in.exists()) {
      colorize_texture_ = t_in->texture_data();
    } else {
      colorize_texture_.Clear();
    }
  }
  void SetColorizeTexture(TextureData* t) {
    EnsureConfiguring();
    colorize_texture_ = t;
  }
  // red multiplies source color, green adds colorize1-color,
  // and blue adds white
  // (currently requires colorize1 and colorize 2 to be set)
  void SetMaskTexture(const Object::Ref<Texture>& t_in) {
    EnsureConfiguring();
    if (t_in.exists()) {
      mask_texture_ = t_in->texture_data();
    } else {
      mask_texture_.Clear();
    }
  }
  void SetMaskTexture(TextureData* t) {
    EnsureConfiguring();
    mask_texture_ = t;
  }
  void SetMaskUV2Texture(const Object::Ref<Texture>& t_in) {
    EnsureConfiguring();
    if (t_in.exists()) {
      mask_uv2_texture_ = t_in->texture_data();
    } else {
      mask_uv2_texture_.Clear();
    }
  }
  void SetMaskUV2Texture(TextureData* t) {
    EnsureConfiguring();
    mask_uv2_texture_ = t;
  }
  void clearMaskUV2Texture() {
    EnsureConfiguring();
    mask_uv2_texture_.Clear();
  }
  void SetDoubleSided(bool enable) {
    EnsureConfiguring();
    double_sided_ = enable;
  }
  void SetColor(float r, float g, float b, float a = 1.0f) {
    // we support fast inline color changes with drawing streams
    // (avoids having to re-send a whole configure for every color change)
    // ..make sure to only allow this if we have a color already; otherwise we
    // need to config since we might be implicitly switch shaders by setting
    // color
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
  void SetShadow(float offsetX, float offsetY, float blur, float opacity) {
    EnsureConfiguring();
    shadow_offset_x_ = offsetX;
    shadow_offset_y_ = offsetY;
    shadow_blur_ = blur;
    shadow_opacity_ = opacity;
  }
  void setGlow(float amount, float blur) {
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
  float color_r_, color_g_, color_b_, color_a_;
  float colorize_color_r_, colorize_color_g_, colorize_color_b_,
      colorize_color_a_;
  float colorize_color2_r_, colorize_color2_g_, colorize_color2_b_,
      colorize_color2_a_;
  float shadow_offset_x_, shadow_offset_y_, shadow_blur_, shadow_opacity_;
  float glow_amount_, glow_blur_;
  float flatness_;
  Object::Ref<TextureData> texture_;
  Object::Ref<TextureData> colorize_texture_;
  Object::Ref<TextureData> mask_texture_;
  Object::Ref<TextureData> mask_uv2_texture_;
  bool do_colorize_2_;
  bool transparent_;
  bool premultiplied_;
  bool have_color_;
  bool double_sided_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_
