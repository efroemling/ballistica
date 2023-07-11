// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_DELEGATE_H_
#define BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_DELEGATE_H_

#include <optional>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

class InputDeviceDelegate : public Object {
 public:
  InputDeviceDelegate();
  ~InputDeviceDelegate() override;

  /// Called when the device is pressing a button/etc. which should
  /// 'join the game' in some way.
  virtual void RequestPlayer();

  /// Does the device currently have something in the game it is controlling?
  virtual auto AttachedToPlayer() const -> bool;

  /// For debugging; should return something like 'remote-player'
  /// 'local-player'.
  virtual auto DescribeAttachedTo() const -> std::string;

  /// Does the device have a position for something in the game that it is
  /// controlling? (for drawing guides such as touch-screen direction
  /// arrows/etc.)
  virtual auto GetPlayerPosition() -> std::optional<Vector3f>;

  /// Called when the device is passing input to its player.
  virtual void InputCommand(InputType type, float value);

  /// Called when the device wants to stop controlling any player in the
  /// game it is controlling.
  virtual void DetachFromPlayer();

  /// Called once per update cycle (generally corresponds with frame draws).
  virtual void Update();

  /// An input-device-delegate should never outlive its input_device;
  /// our accessor returns a reference to show this does not need
  /// to be checked.
  auto input_device() const -> InputDevice& {
    BA_PRECONDITION_FATAL(input_device_.Exists());
    return *input_device_;
  }
  void set_input_device(InputDevice* device);
  auto InputDeviceExists() const -> bool { return input_device_.Exists(); }

 private:
  Object::WeakRef<InputDevice> input_device_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_INPUT_DEVICE_DELEGATE_H_
