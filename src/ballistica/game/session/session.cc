// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/game/session/session.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/game/game.h"

namespace ballistica {

Session::Session() {
  g_app_globals->session_count++;
  // new sessions immediately become foreground
  g_game->SetForegroundSession(this);
}

Session::~Session() { g_app_globals->session_count--; }

void Session::Update(int time_advance) {}

auto Session::GetForegroundContext() -> Context { return Context(); }

void Session::Draw(FrameDef*) {}

void Session::ScreenSizeChanged() {}

void Session::LanguageChanged() {}

void Session::GraphicsQualityChanged(GraphicsQuality q) {}

void Session::DebugSpeedMultChanged() {}

void Session::DumpFullState(GameStream* out) {
  Log("Session::DumpFullState() being called; shouldn't happen.");
}

}  // namespace ballistica
