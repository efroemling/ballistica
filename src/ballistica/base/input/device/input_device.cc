// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/input_device.h"

#include <cstdio>
#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"

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

#if BA_SDL_BUILD || BA_MINSDL_BUILD
void InputDevice::HandleSDLEvent(const SDL_Event* e) {}
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
    translated_name = g_base->assets->GetResourceString("keyboardText");
  } else if (GetDeviceName() == "TouchScreen") {
    translated_name = g_base->assets->GetResourceString("touchScreenText");
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
  // FIXME: should return this in Lstr json form.
  return g_base->assets->GetResourceString("buttonText") + " "
         + std::to_string(id);
}

auto InputDevice::GetAxisName(int id) -> std::string {
  // By default just return 'axis 5' or whatnot.
  // FIXME: should return this in Lstr json form.
  return g_base->assets->GetResourceString("axisText") + " "
         + std::to_string(id);
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
  g_base->input->MarkInputActive();
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
