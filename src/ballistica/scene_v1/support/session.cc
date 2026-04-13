// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/session.h"

#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::scene_v1 {

Session::Session() {
  g_scene_v1->session_count++;

  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // New sessions immediately become foreground.
  appmode->SetForegroundSession(this);
}

Session::~Session() { g_scene_v1->session_count--; }

void Session::Update(int time_advance_millisecs, double time_advance) {}

auto Session::TimeToNextEvent() -> std::optional<microsecs_t> {
  BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
              "Session::TimeToNextEvent() being called; should not happen.");
  return 5000000;
}

auto Session::GetForegroundContext() -> base::ContextRef { return {}; }

void Session::Draw(base::FrameDef*) {}

void Session::OnScreenSizeChange() {}

void Session::LanguageChanged() {}

void Session::DebugSpeedMultChanged() {}

void Session::DumpFullState(SessionStream* out) {
  g_core->logging->Log(
      LogName::kBa, LogLevel::kError,
      "Session::DumpFullState() being called; shouldn't happen.");
}

}  // namespace ballistica::scene_v1
