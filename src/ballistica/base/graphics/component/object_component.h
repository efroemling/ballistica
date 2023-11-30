// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_OBJECT_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_OBJECT_COMPONENT_H_

#include "ballistica/base/graphics/component/render_component.h"

namespace ballistica::base {

class ObjectComponent : public RenderComponent {
 public:
  explicit ObjectComponent(RenderPass* pass) : RenderComponent(pass) {}

  void SetTexture(TextureAsset* t) {
    EnsureConfiguring();
    texture_ = t;
  }

  void SetColorizeTexture(TextureAsset* t) {
    EnsureConfiguring();
    colorize_texture_ = t;
  }

  void SetDoubleSided(bool enable) {
    EnsureConfiguring();
    double_sided_ = enable;
  }

  void SetReflection(ReflectionType r) {
    EnsureConfiguring();
    reflection_ = r;
  }

  void SetReflectionScale(float r, float g, float b) {
    EnsureConfiguring();
    reflection_scale_r_ = r;
    reflection_scale_g_ = g;
    reflection_scale_b_ = b;
  }

  void SetPremultiplied(bool val) {
    EnsureConfiguring();
    premultiplied_ = val;
  }

  void SetTransparent(bool val) {
    EnsureConfiguring();
    transparent_ = val;
  }

  void SetColor(float r, float g, float b, float a = 1.0f) {
    // We support fast inline color changes with drawing streams.
    // (avoids having to re-send a whole configure for every color change)
    if (state_ == State::kDrawing) {
      cmd_buffer_->PutCommand(
          RenderCommandBuffer::Command::kObjectComponentInlineColor);
      cmd_buffer_->PutFloats(r, g, b, a);
    } else {
      EnsureConfiguring();
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

  void SetAddColor(float r, float g, float b) {
    // We support fast inline add-color changes with drawing streams
    // (avoids having to re-send a whole configure for every change).
    // Make sure to only allow this if we have an add color already;
    // otherwise we need to config since we might be switching shaders.
    if (state_ == State::kDrawing && have_color_add_) {
      cmd_buffer_->PutCommand(
          RenderCommandBuffer::Command::kObjectComponentInlineAddColor);
      cmd_buffer_->PutFloats(r, g, b);
    } else {
      EnsureConfiguring();
    }
    color_add_r_ = r;
    color_add_g_ = g;
    color_add_b_ = b;
    have_color_add_ = true;
  }

  void SetLightShadow(LightShadowType t) {
    EnsureConfiguring();
    light_shadow_ = t;
  }

  void SetWorldSpace(bool w) {
    EnsureConfiguring();
    world_space_ = w;
  }

 protected:
  void WriteConfig() override;

 protected:
  ReflectionType reflection_{ReflectionType::kNone};
  LightShadowType light_shadow_{LightShadowType::kObject};
  bool world_space_{};
  bool transparent_{};
  bool premultiplied_{};
  bool have_color_add_{};
  bool double_sided_{};
  bool do_colorize_2_{};
  float color_r_{1.0f};
  float color_g_{1.0f};
  float color_b_{1.0f};
  float color_a_{1.0f};
  float colorize_color_r_{1.0f};
  float colorize_color_g_{1.0f};
  float colorize_color_b_{1.0f};
  float colorize_color_a_{1.0f};
  float colorize_color2_r_{};
  float colorize_color2_g_{};
  float colorize_color2_b_{};
  float colorize_color2_a_{};
  float color_add_r_{};
  float color_add_g_{};
  float color_add_b_{};
  float reflection_scale_r_{1.0f};
  float reflection_scale_g_{1.0f};
  float reflection_scale_b_{1.0f};
  Object::Ref<TextureAsset> texture_;
  Object::Ref<TextureAsset> colorize_texture_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_OBJECT_COMPONENT_H_
