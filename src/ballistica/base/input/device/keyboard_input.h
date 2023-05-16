// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_KEYBOARD_INPUT_H_
#define BALLISTICA_BASE_INPUT_DEVICE_KEYBOARD_INPUT_H_

#include <set>
#include <string>

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/core/platform/support/min_sdl.h"

namespace ballistica::base {

class KeyboardInput : public InputDevice {
 public:
  explicit KeyboardInput(KeyboardInput* parent);
  ~KeyboardInput() override;
  auto HandleKey(const SDL_Keysym* keysym, bool repeat, bool down) -> bool;
  void UpdateMapping() override;
  auto GetRawDeviceName() -> std::string override;
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
  void UpdateArrowKeys(SDL_Keycode key);
  void UpdateRun(SDL_Keycode key, bool down);
  SDL_Keycode up_key_{};
  SDL_Keycode down_key_{};
  SDL_Keycode left_key_{};
  SDL_Keycode right_key_{};
  SDL_Keycode jump_key_{};
  SDL_Keycode punch_key_{};
  SDL_Keycode bomb_key_{};
  SDL_Keycode pick_up_key_{};
  SDL_Keycode hold_position_key_{};
  SDL_Keycode start_key_{};
  bool down_held_{};
  bool up_held_{};
  bool left_held_{};
  bool right_held_{};
  bool enable_child_{};
  bool left_key_assigned_{};
  bool right_key_assigned_{};
  bool up_key_assigned_{};
  bool down_key_assigned_{};
  KeyboardInput* parent_keyboard_input_{};
  KeyboardInput* child_keyboard_input_{};
  std::set<int> keys_held_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_KEYBOARD_INPUT_H_
