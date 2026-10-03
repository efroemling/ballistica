// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/test_input.h"

#include <algorithm>

#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/shared/foundation/input_types.h"
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

void TestInput::Process(millisecs_t time) {
  assert(g_base->InLogicThread());

  if (reset_) {
    reset_ = false;
    lr_ = ud_ = 0;
    jump_pressed_ = bomb_pressed_ = pickup_pressed_ = punch_pressed_ = false;
  }

  if (time <= next_event_time_) {
    return;
  }
  next_event_time_ = time + static_cast<int>(RandomFloat() * 300.0f);

  // Do nothing while any UI is up.
  if (g_base->ui->IsMainUIVisible()) {
    return;
  }

  float r = RandomFloat();

  BAEvent e;
  if (r < 0.5f) {
    // Movement change.
    r = RandomFloat();
    if (r < 0.3f) {
      lr_ = ud_ = 0;
    } else {
      lr_ = std::max(
          -32767, std::min(32767, static_cast<int>(
                                      -50000.0f + 100000.0f * RandomFloat())));
      ud_ = std::max(
          -32767, std::min(32767, static_cast<int>(
                                      -50000.0f + 100000.0f * RandomFloat())));
    }
    e.type = BA_JOYAXISMOTION;
    e.jaxis.axis = 0;
    e.jaxis.value = static_cast_check_fit<int16_t>(ud_);
    g_base->input->PushJoystickEvent(e, joystick_);
    e.jaxis.axis = 1;
    e.jaxis.value = static_cast_check_fit<int16_t>(lr_);
    g_base->input->PushJoystickEvent(e, joystick_);
    return;
  }

  // Button change: toggle one of jump/punch/bomb/grab.
  r = RandomFloat();
  bool* pressed;
  int button;
  if (r > 0.75f) {
    pressed = &jump_pressed_;
    button = 0;
  } else if (r > 0.5f) {
    pressed = &bomb_pressed_;
    button = 2;
  } else if (r > 0.25f) {
    pressed = &pickup_pressed_;
    button = 3;
  } else {
    pressed = &punch_pressed_;
    button = 1;
  }
  *pressed = !*pressed;
  e.type = *pressed ? BA_JOYBUTTONDOWN : BA_JOYBUTTONUP;
  e.jbutton.button = button;
  g_base->input->PushJoystickEvent(e, joystick_);
}

}  // namespace ballistica::base
