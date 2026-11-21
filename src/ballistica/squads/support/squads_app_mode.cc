// Released under the MIT License. See LICENSE for details.

#include "ballistica/squads/support/squads_app_mode.h"

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/text/text_group.h"

namespace ballistica::squads {

static SquadsAppMode* g_squads_app_mode{};

SquadsAppMode::SquadsAppMode() = default;

auto SquadsAppMode::GetSingleton() -> SquadsAppMode* {
  assert(g_base->InLogicThread());
  if (g_squads_app_mode == nullptr) {
    g_squads_app_mode = new SquadsAppMode();
  }
  return g_squads_app_mode;
}

void SquadsAppMode::OnActivate() {
  assert(g_base->InLogicThread());

  // Reset the engine to a default state and fade in.
  g_base->Reset();
  g_base->graphics->FadeScreen(true, 250, nullptr);
}

void SquadsAppMode::DrawWorld(base::FrameDef* frame_def) {
  // Placeholder until there's something real to draw.
  if (!text_group_.exists()) {
    text_group_ = Object::New<base::TextGroup>();
    text_group_->SetText("Squads (scaffold)");
  }
  auto& grp(*text_group_);
  auto* pass = frame_def->overlay_pass();

  base::SimpleComponent c(pass);
  c.SetTransparent(true);
  c.SetColor(0.3f, 0.8f, 1.0f, 1.0f);
  {
    auto xf = c.ScopedTransform();

    // Z value -1 will draw us under most everything.
    c.Translate(pass->virtual_width() * 0.5f - 200.0f,
                pass->virtual_height() * 0.5f - 20.0f, -1.0f);
    c.Scale(2.0, 2.0);
    int text_elem_count = grp.GetElementCount();
    for (int e = 0; e < text_elem_count; e++) {
      c.SetTexture(grp.GetElementTexture(e));
      c.SetFlatness(1.0f);
      c.DrawMesh(grp.GetElementMesh(e));
    }
  }
  c.Submit();
}

}  // namespace ballistica::squads
