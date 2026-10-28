// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_

#include <algorithm>

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

  // The texture setters below also note which kind of slot the texture
  // is going into, so a texture built for another kind (a data-role
  // mask drawn as a picture, a picture used as a mask, plain data used
  // as a frame mask) gets a one-time warning. See
  // TextureAsset::ExpectPictureSlot.

  void SetTexture(TextureAsset* t) {
    EnsureConfiguring();
    if (t != nullptr) {
      t->ExpectPictureSlot();
    }
    texture_ = t;
  }

  void SetTexture(const Object::Ref<TextureAsset>& t) {
    EnsureConfiguring();
    if (t.exists()) {
      t->ExpectPictureSlot();
    }
    texture_ = t;
  }

  /// Used with colorize color 1 and 2. Red areas of the texture will get
  /// multiplied by colorize-color1 and green areas by colorize-color2.
  void SetColorizeTexture(TextureAsset* t) {
    EnsureConfiguring();
    if (t != nullptr) {
      t->ExpectDataSlot("colorize");
    }
    colorize_texture_ = t;
  }

  /// Red multiplies source color, green adds colorize1-color, and blue adds
  /// white (currently requires colorize1 and colorize 2 to be set). All
  /// three are scaled by the mask's alpha, which also cuts the shape
  /// out, so this slot wants a 'premultiplied_data' texture.
  void SetMaskTexture(TextureAsset* t) {
    EnsureConfiguring();
    if (t != nullptr) {
      t->ExpectFrameMaskSlot();
    }
    mask_texture_ = t;
  }

  /// Only the alpha of this one is read.
  void SetMaskUV2Texture(TextureAsset* t) {
    EnsureConfiguring();
    if (t != nullptr) {
      t->ExpectAlphaMaskSlot();
    }
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

  /// With a mask texture: an rgb multiplier on what the mask adds (its
  /// frame and highlight), which SetColor's rgb doesn't reach. Defaults
  /// to (1,1,1), the legacy look; hosts that scale a whole drawing
  /// (depictions' brightness and color_multiply) pass their multiplier.
  void SetMaskAddMult(float r, float g, float b) {
    EnsureConfiguring();
    mask_add_mult_[0] = r;
    mask_add_mult_[1] = g;
    mask_add_mult_[2] = b;
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
  }

  /// Tint applied through the colorize texture's blue channel. White
  /// (the default) is an exact no-op, so masks with stray blue data
  /// cost nothing until a caller actually sets this.
  void SetColorizeColor3(float r, float g, float b, float a = 1.0f) {
    EnsureConfiguring();
    colorize_color3_r_ = r;
    colorize_color3_g_ = g;
    colorize_color3_b_ = b;
    colorize_color3_a_ = a;
  }

  /// A soft shadow under the texture's alpha (text drop shadows). Its
  /// color defaults to black; a bright color with no offset makes a
  /// glow, and ``spread`` widens it (extra blur, as mip bias; the
  /// glyph's padding in its atlas bounds how far it can usefully go).
  ///
  /// ``text_glow`` > 0 draws with the text-glow shader variant instead: the
  /// same shadow, under a blurred copy of the glyph in place of the
  /// glyph itself, its interior lifted toward white (a neon look) at
  /// that strength (1 = standard). The blur's width is a fraction of
  /// the shadow's offset, so pass one even at zero opacity. Its own
  /// program, used only when > 0, so plain text never pays for it.
  void SetShadow(float offset_x, float offset_y, float blur, float opacity,
                 float r = 0.0f, float g = 0.0f, float b = 0.0f,
                 float spread = 0.0f, float text_glow = 0.0f) {
    EnsureConfiguring();
    shadow_offset_x_ = offset_x;
    shadow_offset_y_ = offset_y;
    shadow_blur_ = blur;
    shadow_opacity_ = opacity;
    shadow_color_r_ = r;
    shadow_color_g_ = g;
    shadow_color_b_ = b;
    shadow_spread_ = spread;
    shadow_text_glow_ = text_glow;
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

  /// Fade out what we draw using the mesh's second uv set (so this
  /// needs a dual-texture mesh). Each uv2 axis runs from 0, where we
  /// draw fully, to 1, where we've faded away entirely, easing along
  /// the way; the two axes multiply, so a corner where two fades meet
  /// falls off along both. Transparent textured draws only, and not
  /// combined with other effects.
  void SetUV2Fade(bool enable) {
    EnsureConfiguring();
    uv2_fade_ = enable;
  }

  /// Draw our texture through a layered mask: shown over an underlay
  /// color, with two flat colors painted over it, all within the mask's
  /// silhouette. The mask's red channel is how much of the texture
  /// (over the underlay) shows, green and blue how much of layer1 and
  /// layer2 are painted over that (in that order), and alpha how much
  /// of the whole is drawn; opacity scales all of it. Colors are rgba
  /// (straight). Painting, unlike tinting, adds coverage where there's
  /// nothing: a shadow layer over a clear underlay darkens what's
  /// behind. Transparent textured draws only, and not combined with
  /// other effects (our color still modulates the texture).
  void SetLayeredMask(TextureAsset* mask, const float* underlay,
                      const float* layer1, const float* layer2,
                      float opacity = 1.0f) {
    EnsureConfiguring();
    assert(mask);
    layered_mask_texture_ = mask;
    std::copy(underlay, underlay + 4, layer_underlay_);
    std::copy(layer1, layer1 + 4, layer1_color_);
    std::copy(layer2, layer2 + 4, layer2_color_);
    layer_opacity_ = opacity;
  }

 protected:
  void WriteConfig() override;

 protected:
  bool transparent_{};
  bool premultiplied_{};
  bool have_color_{};
  bool double_sided_{};
  bool uv2_fade_{};
  float color_r_{1.0f};
  float color_g_{1.0f};
  float color_b_{1.0f};
  float color_a_{1.0f};
  float mask_add_mult_[3]{1.0f, 1.0f, 1.0f};
  float colorize_color_r_{1.0f};
  float colorize_color_g_{1.0f};
  float colorize_color_b_{1.0f};
  float colorize_color_a_{1.0f};
  float colorize_color2_r_{1.0f};
  float colorize_color2_g_{1.0f};
  float colorize_color2_b_{1.0f};
  float colorize_color2_a_{1.0f};
  float colorize_color3_r_{1.0f};
  float colorize_color3_g_{1.0f};
  float colorize_color3_b_{1.0f};
  float colorize_color3_a_{1.0f};
  float shadow_offset_x_{};
  float shadow_offset_y_{};
  float shadow_blur_{};
  float shadow_opacity_{};
  float shadow_color_r_{};
  float shadow_color_g_{};
  float shadow_color_b_{};
  float shadow_spread_{};
  float shadow_text_glow_{};
  float glow_amount_{};
  float glow_blur_{};
  float flatness_{};
  float layer_underlay_[4]{};
  float layer1_color_[4]{};
  float layer2_color_[4]{};
  float layer_opacity_{1.0f};
  Object::Ref<TextureAsset> layered_mask_texture_;
  Object::Ref<TextureAsset> texture_;
  Object::Ref<TextureAsset> colorize_texture_;
  Object::Ref<TextureAsset> mask_texture_;
  Object::Ref<TextureAsset> mask_uv2_texture_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_SIMPLE_COMPONENT_H_
