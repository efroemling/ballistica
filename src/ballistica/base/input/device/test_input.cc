// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/test_input.h"

#include <algorithm>

#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::base {

TestInput::TestInput() {
  // In attract-mode (pretty demos) we want this to look more like
  // real people connecting to the game, so just say 'Controller'.
  const char* device_name =
      g_base->input->attract_mode() ? "Controller" : "TestInput";

  joystick_ = Object::NewDeferred<JoystickInput>(-1,  // not an sdl joystick
                                                 device_name,  // device name
                                                 false,   // allow configuring?
                                                 false);  // calibrate?;
  joystick_->set_allow_input_in_attract_mode(true);
  joystick_->set_is_test_input(true);
  g_base->input->PushAddInputDeviceCall(joystick_, true);
}

TestInput::~TestInput() {
  g_base->input->PushRemoveInputDeviceCall(joystick_, true);
}

void TestInput::Reset() {
  assert(g_base->InLogicThread());
  reset_ = true;
}

void TestInput::HandleAlreadyPressedTwice() {
  if (print_already_did2_) {
    print_already_did2_ = false;
  }
}

void TestInput::Process(millisecs_t time) {
  assert(g_base->InLogicThread());

  if (reset_) {
    reset_ = false;
    join_end_time_ = time + 7000;  // do joining for the next few seconds
    join_start_time_ = time + 1000;
    join_press_count_ = 0;
    print_non_join_ = true;
    print_already_did2_ = true;
  }

  if (print_non_join_ && time >= join_end_time_) {
    print_non_join_ = false;
  }

  if (time > next_event_time_) {
    next_event_time_ = time + static_cast<int>(RandomFloat() * 300.0f);

    // Do absolutely nothing before join start time.
    if (time < join_start_time_) {
      return;
    }

    // Do nothing while any UI is up.
    if (g_base->ui->IsMainUIVisible()) {
      return;
    }

    float r = RandomFloat();

    SDL_Event e;
    if (r < 0.5f) {
      // Movement change.
      r = RandomFloat();
      if (r < 0.3f) {
        lr_ = ud_ = 0;
      } else {
        lr_ = std::max(
            -32767,
            std::min(32767,
                     static_cast<int>(-50000.0f + 100000.0f * RandomFloat())));
        ud_ = std::max(
            -32767,
            std::min(32767,
                     static_cast<int>(-50000.0f + 100000.0f * RandomFloat())));
      }
      e.type = SDL_JOYAXISMOTION;
      e.jaxis.axis = 0;
      e.jaxis.value = static_cast_check_fit<int16_t>(ud_);
      g_base->input->PushJoystickEvent(e, joystick_);
      e.jaxis.axis = 1;
      e.jaxis.value = static_cast_check_fit<int16_t>(lr_);
      g_base->input->PushJoystickEvent(e, joystick_);
    } else {
      // Button change.
      r = RandomFloat();
      if (r > 0.75f) {
        // Jump:
        // Don't do more than 2 presses while joining.
        if (!jump_pressed_ && time < join_end_time_ && join_press_count_ > 1) {
          HandleAlreadyPressedTwice();
        } else {
          jump_pressed_ = !jump_pressed_;
          if (jump_pressed_) {
            join_press_count_++;
          }
          e.type = jump_pressed_ ? SDL_JOYBUTTONDOWN : SDL_JOYBUTTONUP;
          e.jbutton.button = 0;
          g_base->input->PushJoystickEvent(e, joystick_);
        }
      } else if (r > 0.5f) {
        // Bomb:
        // Don't do more than 2 presses while joining.
        if (!bomb_pressed_ && time < join_end_time_ && join_press_count_ > 1) {
          HandleAlreadyPressedTwice();
        } else {
          bomb_pressed_ = !bomb_pressed_;

          // This counts as a join press *only* if its the first.
          // (presses after that simply change our character)
          if (join_press_count_ == 0 && bomb_pressed_) {
            // cout << "GOT BOMB AS FIRST PRESS " << this << endl;
            join_press_count_++;
          }
          e.type = bomb_pressed_ ? SDL_JOYBUTTONDOWN : SDL_JOYBUTTONUP;
          e.jbutton.button = 2;
          g_base->input->PushJoystickEvent(e, joystick_);
        }

      } else if (r > 0.25f) {
        // Grab:
        // Don't do more than 2 presses while joining.
        if (!pickup_pressed_ && time < join_end_time_
            && join_press_count_ > 1) {
          HandleAlreadyPressedTwice();
        } else {
          pickup_pressed_ = !pickup_pressed_;
          if (pickup_pressed_) {
            join_press_count_++;
          }
          e.type = pickup_pressed_ ? SDL_JOYBUTTONDOWN : SDL_JOYBUTTONUP;
          e.jbutton.button = 3;
          g_base->input->PushJoystickEvent(e, joystick_);
        }
      } else {
        // Punch:
        // Don't do more than 2 presses while joining.
        if (!punch_pressed_ && time < join_end_time_ && join_press_count_ > 1) {
          HandleAlreadyPressedTwice();
        } else {
          punch_pressed_ = !punch_pressed_;
          if (punch_pressed_) {
            join_press_count_++;
          }
          e.type = punch_pressed_ ? SDL_JOYBUTTONDOWN : SDL_JOYBUTTONUP;
          e.jbutton.button = 1;
          g_base->input->PushJoystickEvent(e, joystick_);
        }
      }
    }
  }
}

}  // namespace ballistica::base
