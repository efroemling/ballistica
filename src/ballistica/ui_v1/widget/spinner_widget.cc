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

auto SpinnerWidget::Alpha_() const -> float {
  // Invisible through the delay, then a linear fade over the duration
  // (a zero duration is a hard cut at the delay).
  float into_fade = presence_ - fade_delay_;
  if (into_fade <= 0.0f) {
    return 0.0f;
  }
  if (fade_duration_ <= 0.0f) {
    return 1.0f;
  }
  return std::min(1.0f, into_fade / fade_duration_);
}

void SpinnerWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  seconds_t current_time = pass->frame_def()->display_time();

  // We only draw in transparent pass.
  if (!draw_transparent) {
    return;
  }

  // Presence accumulates while we're visible and drains (faster) while
  // we're not; alpha is derived from it, so a brief hide/show doesn't
  // restart the fade from scratch.
  float fade_end = fade_delay_ + fade_duration_;
  auto elapsed = static_cast<float>(pass->frame_def()->display_time_elapsed());
  if (visible_) {
    if (fade_) {
      presence_ = std::min(fade_end, presence_ + elapsed);
    } else {
      presence_ = fade_end;
    }
  } else {
    if (fade_) {
      presence_ = std::max(0.0f, presence_ - elapsed * 2.0f);
    } else {
      presence_ = 0.0f;
    }
    // Also don't draw anything in this case.
    return;
  }

  float alpha = fade_ ? Alpha_() : 1.0f;

  // Select our texture up front so we can honor its premultiplied flag below.
  base::TextureAsset* tex;
  if (style_ == Style::kSimple) {
    tex = g_ui_v1->assets().spinner.get();
  } else {
    assert(style_ == Style::kBomb);
    // Advance through our 12 frames at 24fps.
    auto frame{
        static_cast<int>(std::floor(std::fmod(current_time * 24.0, 12.0)))};
    switch (frame) {
      case 0:
        tex = g_ui_v1->assets().spinner0.get();
        break;
      case 1:
        tex = g_ui_v1->assets().spinner1.get();
        break;
      case 2:
        tex = g_ui_v1->assets().spinner2.get();
        break;
      case 3:
        tex = g_ui_v1->assets().spinner3.get();
        break;
      case 4:
        tex = g_ui_v1->assets().spinner4.get();
        break;
      case 5:
        tex = g_ui_v1->assets().spinner5.get();
        break;
      case 6:
        tex = g_ui_v1->assets().spinner6.get();
        break;
      case 7:
        tex = g_ui_v1->assets().spinner7.get();
        break;
      case 8:
        tex = g_ui_v1->assets().spinner8.get();
        break;
      case 9:
        tex = g_ui_v1->assets().spinner9.get();
        break;
      case 10:
        tex = g_ui_v1->assets().spinner10.get();
        break;
      default:
        tex = g_ui_v1->assets().spinner11.get();
        break;
    }
  }
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
    c.DrawMeshAsset(g_ui_v1->assets().image1x1.get());
  }
  c.Submit();
}

auto SpinnerWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  return false;
}

}  // namespace ballistica::ui_v1
