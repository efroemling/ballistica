// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_REMOTE_SUPPORT_REMOTE_INPUT_DEVICE_DELEGATE_H_
#define BALLISTICA_REMOTE_SUPPORT_REMOTE_INPUT_DEVICE_DELEGATE_H_

#include <cstdint>
#include <string>

#include "ballistica/base/input/device/input_device_delegate.h"
#include "ballistica/remote/remote.h"

namespace ballistica::remote {

/// Delegate for every input device while RemoteAppMode is active.
///
/// Rather than driving a player in a local game, a device's input becomes
/// controller state the remote client sends to the game it is connected
/// to. Any device works: the touchscreen controls, a keyboard, or a
/// gamepad attached to the phone or tablet.
class RemoteInputDeviceDelegate : public base::InputDeviceDelegate {
 public:
  RemoteInputDeviceDelegate();
  ~RemoteInputDeviceDelegate() override;

  /// We count as 'attached' while connected to a game; this is what makes
  /// the touchscreen controls show up.
  auto AttachedToPlayer() const -> bool override;
  auto DescribeAttachedTo() const -> std::string override;
  void InputCommand(InputType type, float value) override;

  /// Remote-state button bits currently held on this device.
  auto buttons() const -> uint8_t { return buttons_; }

  /// Stick position in the remote protocol's 0-255 axis bytes.
  auto axis_h() const -> uint8_t;
  auto axis_v() const -> uint8_t;

  /// Increments each time this device's stick moves; the most recently
  /// moved device's stick wins when several are in use.
  auto axis_serial() const -> uint64_t { return axis_serial_; }

 private:
  void SetButton_(uint32_t bit, bool held);

  uint8_t buttons_{};
  float left_right_{};
  float up_down_{};
  uint64_t axis_serial_{};
};

}  // namespace ballistica::remote

#endif  // BALLISTICA_REMOTE_SUPPORT_REMOTE_INPUT_DEVICE_DELEGATE_H_
