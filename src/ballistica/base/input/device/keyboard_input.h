// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_KEYBOARD_INPUT_H_
#define BALLISTICA_BASE_INPUT_DEVICE_KEYBOARD_INPUT_H_

#include <set>
#include <string>

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/shared/foundation/input_types.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

class KeyboardInput : public InputDevice {
 public:
  explicit KeyboardInput(KeyboardInput* parent);
  ~KeyboardInput() override;
  auto HandleKey(const BAKeysym* keysym, bool down) -> bool;
  void ApplyAppConfig() override;
  auto DoGetDeviceName() -> std::string override;
  void ResetHeldStates() override;
  auto left_key_assigned() const { return left_key_assigned_; }
  auto right_key_assigned() const { return right_key_assigned_; }
  auto up_key_assigned() const { return up_key_assigned_; }
  auto down_key_assigned() const { return down_key_assigned_; }
  auto GetPartyButtonName() const -> std::string override;
  auto IsKeyboard() -> bool override { return true; }
  auto HasMeaningfulButtonNames() -> bool override;
  auto GetButtonName(int index) -> std::string override;

 private:
  void UpdateArrowKeys_(BAKeycode key);
  void UpdateRun_(BAKeycode key, bool down);
  bool down_held_{};
  bool up_held_{};
  bool left_held_{};
  bool right_held_{};
  bool enable_child_{};
  bool left_key_assigned_{};
  bool right_key_assigned_{};
  bool up_key_assigned_{};
  bool down_key_assigned_{};
  BAKeycode up_key_{};
  BAKeycode down_key_{};
  BAKeycode left_key_{};
  BAKeycode right_key_{};
  BAKeycode jump_key_{};
  BAKeycode punch_key_{};
  BAKeycode bomb_key_{};
  BAKeycode pick_up_key_{};
  BAKeycode hold_position_key_{};
  BAKeycode start_key_{};
  KeyboardInput* parent_keyboard_input_{};
  KeyboardInput* child_keyboard_input_{};
  std::set<int> keys_held_;
  Object::Ref<Repeater> ui_repeater_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_KEYBOARD_INPUT_H_
