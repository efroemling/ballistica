// Released under the MIT License. See LICENSE for details.

#include "ballistica/logic/session/session.h"

#include "ballistica/app/app.h"
#include "ballistica/logic/logic.h"

namespace ballistica {

Session::Session() {
  g_app->session_count++;

  // New sessions immediately become foreground.
  g_logic->SetForegroundSession(this);
}

Session::~Session() { g_app->session_count--; }

void Session::Update(int time_advance) {}

auto Session::GetForegroundContext() -> Context { return Context(); }

void Session::Draw(FrameDef*) {}

void Session::ScreenSizeChanged() {}

void Session::LanguageChanged() {}

void Session::GraphicsQualityChanged(GraphicsQuality q) {}

void Session::DebugSpeedMultChanged() {}

void Session::DumpFullState(SceneStream* out) {
  Log("Session::DumpFullState() being called; shouldn't happen.");
}

}  // namespace ballistica
