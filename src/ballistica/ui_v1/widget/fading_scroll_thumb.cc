// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/fading_scroll_thumb.h"

#include <algorithm>

#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/mesh/nine_patch_mesh.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

FadingScrollThumb::FadingScrollThumb() = default;

FadingScrollThumb::~FadingScrollThumb() = default;

void FadingScrollThumb::Update(seconds_t now, seconds_t elapsed) {
  // Fade in if we want to see the bar. Start fading out a moment after we
  // stop wanting to see it.
  if (now - last_show_time_ < 0.6) {
    fade_ = std::min(1.5f, fade_ + 2.0f * static_cast<float>(elapsed));
  } else {
    fade_ = std::max(0.0f, fade_ - 1.5f * static_cast<float>(elapsed));
  }
}

void FadingScrollThumb::Draw(base::RenderPass* pass, bool transparent,
                             float left, float bottom, float width,
                             float height, float emphasis, const Rect& clip) {
  if (fade_ <= 0.0f || !transparent) {
    return;
  }
  EnsureMesh_(width, height);

  // Rounded rect via a ninepatch over the circle texture. Our color is
  // pure black, so there is no straight-vs-premultiplied rgb adjustment
  // to make here (see docs/design/premultiplied-alpha.md) -- zero
  // premultiplies to zero. Emphasis scales opacity rather than color,
  // since brightening black would wash it out rather than firm it up.
  base::SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(0, 0, 0, std::min(1.0f, 0.3f * emphasis * fade_));
  c.SetTexture(g_ui_v1->assets().circle.get());
  {
    auto scissor = c.ScopedScissor(clip);
    auto xf = c.ScopedTransform();
    // Ninepatch meshes span [0,w] x [0,h], so translate to the bar's
    // lower-left rather than its center, and never scale.
    c.Translate(left, bottom, 0.75f);
    c.DrawMesh(mesh_.get());
    c.Submit();
  }
}

void FadingScrollThumb::EnsureMesh_(float width, float height) {
  if (mesh_.exists() && mesh_width_ == width && mesh_height_ == height) {
    return;
  }
  mesh_width_ = width;
  mesh_height_ = height;

  // A radius of half our thickness makes the ends exact half-circles:
  // the ninepatch's middle row (or column) collapses to nothing and the
  // end caps are pure semicircle.
  float radius{std::min(width, height) * 0.5f};
  mesh_ = Object::New<base::NinePatchMesh>(
      0.0f, 0.0f, 0.0f, width, height,
      base::NinePatchMesh::BorderForRadius(radius, width, height),
      base::NinePatchMesh::BorderForRadius(radius, height, width),
      base::NinePatchMesh::BorderForRadius(radius, width, height),
      base::NinePatchMesh::BorderForRadius(radius, height, width));
}

}  // namespace ballistica::ui_v1
