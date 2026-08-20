// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/spinner_widget.h"

#include <algorithm>
#include <cmath>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/base.h"
#include "ballistica/base/graphics/component/simple_component.h"

namespace ballistica::ui_v1 {

SpinnerWidget::SpinnerWidget() {}
SpinnerWidget::~SpinnerWidget() = default;

auto SpinnerWidget::GetWidth() -> float { return size_; }
auto SpinnerWidget::GetHeight() -> float { return size_; }

void SpinnerWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  seconds_t current_time = pass->frame_def()->display_time();

  // We only draw in transparent pass.
  if (!draw_transparent) {
    return;
  }

  // Fade presence in any time we're visible and out any time we're not.
  if (visible_) {
    if (fade_) {
      presence_ = std::min(
          1.0, presence_ + pass->frame_def()->display_time_elapsed() * 1.0);
    } else {
      presence_ = 1.0f;
    }
  } else {
    if (fade_) {
      presence_ = std::max(
          0.0, presence_ - pass->frame_def()->display_time_elapsed() * 2.0);
    } else {
      presence_ = 0.0f;
    }
    // Also don't draw anything in this case.
    return;
  }

  auto alpha{std::max(0.0, std::min(1.0, presence_ * 2.0 - 1.0))};

  // Select our texture up front so we can honor its premultiplied flag below.
  base::BuiltinTextureID tex_id;
  if (style_ == Style::kSimple) {
    tex_id = base::BuiltinTextureID::kTexturesSpinner;
  } else {
    assert(style_ == Style::kBomb);
    // Advance through our 12 frames at 24fps.
    auto frame{
        static_cast<int>(std::floor(std::fmod(current_time * 24.0, 12.0)))};
    switch (frame) {
      case 0:
        tex_id = base::BuiltinTextureID::kTexturesSpinner0;
        break;
      case 1:
        tex_id = base::BuiltinTextureID::kTexturesSpinner1;
        break;
      case 2:
        tex_id = base::BuiltinTextureID::kTexturesSpinner2;
        break;
      case 3:
        tex_id = base::BuiltinTextureID::kTexturesSpinner3;
        break;
      case 4:
        tex_id = base::BuiltinTextureID::kTexturesSpinner4;
        break;
      case 5:
        tex_id = base::BuiltinTextureID::kTexturesSpinner5;
        break;
      case 6:
        tex_id = base::BuiltinTextureID::kTexturesSpinner6;
        break;
      case 7:
        tex_id = base::BuiltinTextureID::kTexturesSpinner7;
        break;
      case 8:
        tex_id = base::BuiltinTextureID::kTexturesSpinner8;
        break;
      case 9:
        tex_id = base::BuiltinTextureID::kTexturesSpinner9;
        break;
      case 10:
        tex_id = base::BuiltinTextureID::kTexturesSpinner10;
        break;
      default:
        tex_id = base::BuiltinTextureID::kTexturesSpinner11;
        break;
    }
  }
  base::TextureAsset* tex = g_base->assets->BuiltinTexture(tex_id);

  // Premultiply rgb by alpha for premultiplied textures so the spinner fades
  // via 'over' compositing under premult blend instead of staying full-
  // brightness (premult blend adds rgb directly rather than weighting it by
  // alpha). Straight-alpha textures keep raw rgb and fade via alpha as before.
  float amul = (tex != nullptr && tex->premultiplied())
                   ? static_cast<float>(alpha)
                   : 1.0f;

  base::SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(amul, amul, amul, alpha);
  c.SetTexture(tex);

  {
    auto xf = c.ScopedTransform();

    // Draw at depth range 0.9-1 (mostly want to cover other things).
    c.Translate(0.0f, 0.0f, 0.9f);
    c.Scale(size_, size_, 0.1f);
    if (style_ == Style::kSimple) {
      c.Rotate(-360.0f * std::fmod(current_time * 2.0, 1.0), 0.0f, 0.0f, 1.0f);
    }
    c.DrawMeshAsset(
        g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesImage1x1));
  }
  c.Submit();
}

auto SpinnerWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  return false;
}

}  // namespace ballistica::ui_v1
