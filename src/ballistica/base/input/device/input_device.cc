// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/input_device.h"

#include <algorithm>
#include <cstdio>
#include <string>

#include "ballistica/base/assets/builtin_strings.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/foundation/input_types.h"

namespace ballistica::base {

InputDevice::InputDevice() = default;

auto InputDevice::GetAllowsConfiguring() -> bool { return true; }
auto InputDevice::IsController() -> bool { return false; }
auto InputDevice::IsSDLController() -> bool { return false; }
auto InputDevice::IsTouchScreen() -> bool { return false; }
auto InputDevice::IsRemoteControl() -> bool { return false; }
auto InputDevice::IsTestInput() -> bool { return false; }
auto InputDevice::IsKeyboard() -> bool { return false; }
auto InputDevice::IsMFiController() -> bool { return false; }
auto InputDevice::IsLocal() -> bool { return true; }
auto InputDevice::IsUIOnly() -> bool { return false; }
auto InputDevice::IsRemoteApp() -> bool { return false; }

void InputDevice::ApplyAppConfig() {}

// Most feedback requests we will hand to hardware in any one-second
// window. Overlap merging (below) already collapses ordinary gameplay
// bursts; this exists purely so a buggy or hostile host cannot drive an
// unbounded number of platform haptic calls.
static const int kMaxFeedbackAppliesPerSecond{40};

auto InputDevice::DoApplyFeedback(const FeedbackEvent& event) -> int {
  // Default: no haptic hardware, nothing to do.
  return 0;
}

void InputDevice::DoStopFeedback() {
  // Default: no haptic hardware, nothing to do.
}

void InputDevice::ApplyFeedback(const FeedbackEvent& event) {
  assert(g_base->InLogicThread());

  auto now = g_core->AppTimeMillisecs();

  // Abuse backstop. Note this is a different concern from the emit-side
  // cooldown in game code: that one exists to keep bandwidth sane, this
  // one assumes the sender may be adversarial.
  if (now - feedback_window_start_ >= 1000) {
    feedback_window_start_ = now;
    feedback_window_count_ = 0;
  }
  if (feedback_window_count_ >= kMaxFeedbackAppliesPerSecond) {
    return;
  }

  const auto& profile = FeedbackEvent::ProfileForType(event.type);

  // Hardware cannot mix, so exactly one event owns the device at a time.
  // A strictly lower-priority event arriving inside that window is
  // dropped -- which is what stops a death being swallowed by the very
  // hit that caused it, since the killing blow's event is still holding
  // when the death arrives.
  //
  // Equal priority preempts rather than being dropped: the most recent
  // event of a given importance is what you should feel, and it keeps a
  // sustained beating alive instead of ending shortly after the first
  // blow.
  if (now < feedback_hold_until_ && profile.priority < feedback_priority_) {
    return;
  }

  feedback_priority_ = profile.priority;
  feedback_window_count_ += 1;

  auto render_millisecs = DoApplyFeedback(event);

  // The window is whichever is longer: how long this event should own
  // the device by design, or how long the backend will actually be busy
  // rendering it.
  //
  // These are two different things and conflating them was a real bug.
  // The design value is shared across platforms, but render lengths are
  // not remotely comparable between them -- an ERM flywheel needs
  // ~150ms to be felt at all, where SDL's direct drive manages in 60.
  // Pinning the window to the design value alone let the next event
  // truncate a render that had not yet become perceptible, so the
  // slowest backend could never finish an event; pinning it to the
  // render length alone would have let one platform's hardware dictate
  // pacing everywhere.
  feedback_hold_until_ =
      now + std::max(profile.hold_millisecs, render_millisecs);
}

void InputDevice::StopFeedback() {
  assert(g_base->InLogicThread());

  // Skip the platform call when nothing can be playing; StopFeedback gets
  // called across every device on events like app-suspend.
  if (feedback_hold_until_ == 0) {
    return;
  }
  feedback_hold_until_ = 0;

  DoStopFeedback();
}

#if BA_SDL_BUILD || BA_MINSDL_BUILD
void InputDevice::HandleSDLEvent(const BAEvent* e) {}
#endif

auto InputDevice::ShouldBeHiddenFromUser() -> bool {
  // Ask the input system whether they want to ignore us..
  return g_base->input->ShouldCompletelyIgnoreInputDevice(this);
}

auto InputDevice::start_button_activates_default_widget() -> bool {
  return false;
}

auto InputDevice::DoGetDeviceName() -> std::string { return "Input Device"; }

void InputDevice::OnAdded() {}

auto InputDevice::GetDeviceName() -> std::string {
  assert(g_base->InLogicThread());
  return DoGetDeviceName();
}

auto InputDevice::GetDeviceNameUnique() -> std::string {
  assert(g_base->InLogicThread());
  return DoGetDeviceName() + " " + GetPersistentIdentifier();
}

auto InputDevice::GetDeviceNamePretty() -> std::string {
  assert(g_base->InLogicThread());

  auto device_name{GetDeviceName()};
  std::string translated_name;

  auto devices_with_name = g_base->input->GetInputDevicesWithName(device_name);

  if (device_name == "Keyboard") {
    translated_name = BuiltinStrings::Input::Keyboard()->Evaluate();
  } else if (GetDeviceName() == "TouchScreen") {
    translated_name = BuiltinStrings::Input::TouchScreen()->Evaluate();
  } else {
    translated_name = device_name;
  }

  // If there's just one, no need to tack on the '#2' or whatever.
  if (devices_with_name.size() == 1) {
    return translated_name;
  }
  return translated_name + " " + GetPersistentIdentifier();
}

auto InputDevice::GetButtonName(int id) -> std::string {
  // By default just say 'button 1' or whatnot.
  // FIXME: should return a LangStr rather than locale-baked text.
  return BuiltinStrings::Input::Button(int64_t{id})->Evaluate();
}

auto InputDevice::GetAxisName(int id) -> std::string {
  // By default just return 'axis 5' or whatnot.
  // FIXME: should return a LangStr rather than locale-baked text.
  return BuiltinStrings::Input::Axis(int64_t{id})->Evaluate();
}

auto InputDevice::HasMeaningfulButtonNames() -> bool { return false; }

auto InputDevice::GetPersistentIdentifier() const -> std::string {
  assert(g_base->InLogicThread());
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "#%d", number_);
  return buffer;
}

InputDevice::~InputDevice() {
  // Once we've been added in the logic thread and given an index we
  // should only be going down in the logic thread. If our constructor
  // throws an exception its possible and valid to go down elsewhere.
  if (index_ != -1) {
    assert(g_base->InLogicThread());
  }
}

// Called to let the current host/client-session know that we'd like to
// control something please.
void InputDevice::RequestPlayer() {
  assert(g_base->InLogicThread());

  // Make note that we're being used in some way.
  UpdateLastActiveTime();

  delegate_->RequestPlayer();
}

// If we're attached to a remote player, ship completed packets every now
// and then.
void InputDevice::Update() { delegate_->Update(); }

auto InputDevice::AttachedToPlayer() const -> bool {
  return delegate_->AttachedToPlayer();
}

void InputDevice::DetachFromPlayer() { delegate_->DetachFromPlayer(); }

void InputDevice::UpdateLastActiveTime() {
  assert(g_base->InLogicThread());

  // Special case: in attract-mode, prevent our virtual test devices from
  // affecting input last-active times otherwise it'll kick us out of
  // attract mode.
  if (allow_input_in_attract_mode_ && g_base->input->attract_mode()) {
    return;
  }

  // Mark active time on this specific device.
  last_active_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  // Mark input in general as active also.
  g_base->input->mark_input_active();

  // Let UI know this particular device is active.
  g_base->ui->OnInputDeviceActive(this);
}

void InputDevice::InputCommand(InputType type, float value) {
  assert(g_base->InLogicThread());

  // Make note that we're being used in some way.
  UpdateLastActiveTime();

  delegate_->InputCommand(type, value);
}

void InputDevice::ResetHeldStates() {}

auto InputDevice::GetPartyButtonName() const -> std::string { return ""; }

}  // namespace ballistica::base
