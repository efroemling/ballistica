// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_TEST_INPUT_H_
#define BALLISTICA_BASE_INPUT_DEVICE_TEST_INPUT_H_

#include "ballistica/base/base.h"

namespace ballistica::base {

class TestInput {
 public:
  TestInput();
  virtual ~TestInput();
  void Process(millisecs_t time);
  void Reset();

 private:
  void HandleAlreadyPressedTwice();

  int lr_{};
  int ud_{};
  int join_press_count_{};
  bool jump_pressed_ : 1 {};
  bool bomb_pressed_ : 1 {};
  bool pickup_pressed_ : 1 {};
  bool punch_pressed_ : 1 {};
  bool print_non_join_ : 1 {};
  bool print_already_did2_ : 1 {};
  bool reset_ : 1 {true};
  millisecs_t next_event_time_{};
  millisecs_t join_start_time_{};
  millisecs_t join_end_time_{9999};
  JoystickInput* joystick_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_TEST_INPUT_H_
