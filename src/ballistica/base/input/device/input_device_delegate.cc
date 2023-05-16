// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/input_device_delegate.h"

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

InputDeviceDelegate::InputDeviceDelegate() = default;
InputDeviceDelegate::~InputDeviceDelegate() = default;

auto InputDeviceDelegate::AttachedToPlayer() const -> bool { return false; }

auto InputDeviceDelegate::DescribeAttachedTo() const -> std::string {
  return AttachedToPlayer() ? "something" : "nothing";
}

auto InputDeviceDelegate::GetPlayerPosition() -> std::optional<Vector3f> {
  return {};
}

void InputDeviceDelegate::RequestPlayer() {}

void InputDeviceDelegate::InputCommand(InputType type, float value) {}

void InputDeviceDelegate::set_input_device(InputDevice* device) {
  input_device_ = device;
}

void InputDeviceDelegate::DetachFromPlayer() {}

void InputDeviceDelegate::Update() {}

}  // namespace ballistica::base
