// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/spinner_widget.h"

#include <algorithm>
#include <cmath>

#include "ballistica/base/assets/assets.h"
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
    presence_ = std::min(
        1.0, presence_ + pass->frame_def()->display_time_elapsed() * 1.0);
  } else {
    presence_ = std::max(
        0.0, presence_ - pass->frame_def()->display_time_elapsed() * 2.0);
    // Also don't draw anything in this case.
    return;
  }

  auto alpha{std::max(0.0, std::min(1.0, presence_ * 2.0 - 1.0))};

  base::SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(1.0f, 1.0f, 1.0f, alpha);

  if (style_ == Style::kSimple) {
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kSpinner));
  } else {
    assert(style_ == Style::kBomb);
    // Advance through our 12 frames at 24fps.
    auto frame{
        static_cast<int>(std::floor(std::fmod(current_time * 24.0, 12.0)))};
    base::SysTextureID tex;
    switch (frame) {
      case 0:
        tex = base::SysTextureID::kSpinner0;
        break;
      case 1:
        tex = base::SysTextureID::kSpinner1;
        break;
      case 2:
        tex = base::SysTextureID::kSpinner2;
        break;
      case 3:
        tex = base::SysTextureID::kSpinner3;
        break;
      case 4:
        tex = base::SysTextureID::kSpinner4;
        break;
      case 5:
        tex = base::SysTextureID::kSpinner5;
        break;
      case 6:
        tex = base::SysTextureID::kSpinner6;
        break;
      case 7:
        tex = base::SysTextureID::kSpinner7;
        break;
      case 8:
        tex = base::SysTextureID::kSpinner8;
        break;
      case 9:
        tex = base::SysTextureID::kSpinner9;
        break;
      case 10:
        tex = base::SysTextureID::kSpinner10;
        break;
      default:
        tex = base::SysTextureID::kSpinner11;
        break;
    }
    c.SetTexture(g_base->assets->SysTexture(tex));
  }

  {
    auto xf = c.ScopedTransform();
    c.Scale(size_, size_, 1.0f);
    if (style_ == Style::kSimple) {
      c.Rotate(-360.0f * std::fmod(current_time * 2.0, 1.0), 0.0f, 0.0f, 1.0f);
    }
    c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
  }
  c.Submit();
}

auto SpinnerWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  return false;
}

}  // namespace ballistica::ui_v1
