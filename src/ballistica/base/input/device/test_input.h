// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_TEST_INPUT_H_
#define BALLISTICA_BASE_INPUT_DEVICE_TEST_INPUT_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

/// A fake joystick that mashes random directions and buttons, for
/// stress tests and attract mode. It is deliberately dumb; anything
/// that needs to survive random input (the lobby's ready state, for
/// instance) handles test-input devices on its own side.
class TestInput {
 public:
  TestInput();
  virtual ~TestInput();
  void Process(millisecs_t time);

  /// Return to neutral (no direction, nothing held).
  void Reset();

 private:
  int lr_{};
  int ud_{};
  bool jump_pressed_{};
  bool bomb_pressed_{};
  bool pickup_pressed_{};
  bool punch_pressed_{};
  bool reset_{true};
  millisecs_t next_event_time_{};
  JoystickInput* joystick_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_TEST_INPUT_H_
