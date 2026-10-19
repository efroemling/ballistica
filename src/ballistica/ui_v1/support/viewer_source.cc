// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/support/viewer_source.h"

#include <algorithm>
#include <string>

#include "ballistica/base/logic/logic.h"

namespace ballistica::ui_v1 {

ViewerSource::ViewerSource() : last_shown_time_{g_base->logic->display_time()} {
  assert(g_base->InLogicThread());
}

ViewerSource::~ViewerSource() = default;

auto ViewerSource::GetName() const -> std::string { return "viewer-source"; }

void ViewerSource::MarkShown() {
  assert(g_base->InLogicThread());
  last_shown_time_ = g_base->logic->display_time();
  ever_shown_ = true;
}

auto ViewerSource::WasJustShown() const -> bool {
  // A few frames' worth, even at low frame rates.
  return ever_shown_ && GetIdleTime() < 0.25;
}

auto ViewerSource::GetIdleTime() const -> seconds_t {
  assert(g_base->InLogicThread());
  return std::max(0.0, g_base->logic->display_time() - last_shown_time_);
}

}  // namespace ballistica::ui_v1
