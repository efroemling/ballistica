// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/input_device.h"

#include <list>
#include <unordered_map>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"

namespace ballistica::base {

InputDevice::InputDevice() = default;

auto InputDevice::ShouldBeHiddenFromUser() -> bool {
  // Ask the input system whether they want to ignore us..
  return g_base->input->ShouldCompletelyIgnoreInputDevice(this);
}

auto InputDevice::GetDeviceName() -> std::string {
  assert(g_base->InLogicThread());
  return GetRawDeviceName();
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

InputDevice::~InputDevice() { assert(g_base->InLogicThread()); }

// Called to let the current host/client-session know that we'd like to
// control something please.
void InputDevice::RequestPlayer() {
  assert(g_base->InLogicThread());
  // Make note that we're being used in some way.
  last_input_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

  delegate_->RequestPlayer();
}

// If we're attached to a remote player, ship completed packets every now
// and then.
void InputDevice::Update() { delegate_->Update(); }

auto InputDevice::AttachedToPlayer() const -> bool {
  return delegate_->AttachedToPlayer();
}

void InputDevice::DetachFromPlayer() { delegate_->DetachFromPlayer(); }

void InputDevice::UpdateLastInputTime() {
  // Keep our own individual time, and also let the overall input system
  // know something happened.
  last_input_time_millisecs_ =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  g_base->input->MarkInputActive();
}

void InputDevice::InputCommand(InputType type, float value) {
  assert(g_base->InLogicThread());

  // Make note that we're being used in some way.
  UpdateLastInputTime();

  delegate_->InputCommand(type, value);
}

void InputDevice::ResetHeldStates() {}

auto InputDevice::GetPartyButtonName() const -> std::string { return ""; }

}  // namespace ballistica::base
