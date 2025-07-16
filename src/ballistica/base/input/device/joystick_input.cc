// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/joystick_input.h"

#include <algorithm>
#include <cstdio>
#include <string>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/classic_soft.h"
#include "ballistica/base/support/repeater.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica::base {

// Joy values below this are candidates for calibration.
const float kJoystickCalibrationThreshold{6000.0f};

// Joy events with at least this much movement break calibration.
const float kJoystickCalibrationBreakThreshold{300.0f};

// How long we gotta remain motionless for calibration to kick in.
const int kJoystickCalibrationTimeThreshold{1000};

// How fast calibration occurs.
const float kJoystickCalibrationSpeed = 0.7f;

JoystickInput::JoystickInput(int sdl_joystick_id,
                             const std::string& custom_device_name,
                             bool can_configure, bool calibrate)
    : calibration_threshold_(kJoystickCalibrationThreshold),
      calibration_break_threshold_(kJoystickCalibrationBreakThreshold),
      custom_device_name_(custom_device_name),
      can_configure_(can_configure),
      creation_time_(g_core->AppTimeMillisecs()),
      calibrate_(calibrate) {
  // This is the default calibration for 'non-full' analog calibration.
  for (float& analog_calibration_val : analog_calibration_vals_) {
    analog_calibration_val = 0.6f;
  }

  sdl_joystick_id_ = sdl_joystick_id;

  // Non-negative values here mean its an SDL joystick.
  if (sdl_joystick_id != -1) {
#if BA_ENABLE_SDL_JOYSTICKS
    // Standard SDL joysticks should be getting created in the main thread.
    // Custom joysticks can come from anywhere.
    assert(g_core->InMainThread());

    sdl_joystick_ = SDL_JoystickOpen(sdl_joystick_id);
    if (sdl_joystick_ == nullptr) {
      auto* err = SDL_GetError();
      if (!err) {
        err = "Unknown SDL error.";
      }
      throw Exception(std::string("Error in SDL_JoystickOpen: ") + err + ".");
    }

    // In SDL2 we're passed a device-id but that's only used to open the
    // joystick; events and most everything else use an instance ID, so we store
    // that instead.
    // #if BA_SDL2_BUILD
    sdl_joystick_id_ = SDL_JoystickInstanceID(sdl_joystick_);
    if (auto* name = SDL_JoystickName(sdl_joystick_)) {
      raw_sdl_joystick_name_ = name;
    } else {
      // This can return nullptr if SDL can't find a name.
      raw_sdl_joystick_name_ = "Unknown Controller";
    }

    // Special case: on windows, xinput stuff comes in with unique names
    // "XInput Controller #3", etc.  Let's replace these with simply "XInput
    // Controller" so configuring/etc is sane.
    if (strstr(raw_sdl_joystick_name_.c_str(), "XInput Controller")
        && raw_sdl_joystick_name_.size() >= 20
        && raw_sdl_joystick_name_.size() <= 22) {
      raw_sdl_joystick_name_ = "XInput Controller";
    }

#else   // BA_ENABLE_SDL_JOYSTICKS
    throw Exception();  // Shouldn't happen.
#endif  // BA_ENABLE_SDL_JOYSTICKS

  } else {
    // Its a manual joystick.
    sdl_joystick_ = nullptr;

    // Hard code a few remote controls.
    // The newer way to do this is just set 'UI-Only' on the device config
    is_remote_control_ = ((custom_device_name_ == "Amazon Remote")
                          || (custom_device_name_ == "Amazon Bluetooth Dev")
                          || (custom_device_name_ == "Amazon Fire TV Remote")
                          || (custom_device_name_ == "Nexus Remote"));
  }
}

auto JoystickInput::GetAxisName(int index) -> std::string {
  // On android, lets return some popular axis names.

  if (g_buildconfig.platform_android()) {
    // Due to our stupid 1-based values we have to subtract 1 from our value to
    // get the android motion-event constant.
    // FIXME: should just make a call to android to get these values..
    switch (index) {
      case 1:
        return "Analog X";
      case 2:
        return "Analog Y";
      case 12:
        return "Analog Z";
      case 13:
        return "Right Analog X";
      case 14:
        return "Right Analog Y";
      case 15:
        return "Right Analog Z";
      case 23:
        return "Gas";
      case 24:
        return "Brake";
      case 16:
        return "Hat X";
      case 17:
        return "Hat Y";
      case 18:
        return "Left Trigger";
      case 19:
        return "Right Trigger";
      default:
        break;
    }
  }

  // Fall back to default implementation if we didn't cover it.
  return InputDevice::GetAxisName(index);
}

auto JoystickInput::HasMeaningfulButtonNames() -> bool {
  // Only return true in cases where we know we have proper names
  // for stuff.
  if (is_mfi_controller_) {
    return true;
  }
  return g_buildconfig.platform_android();
}

void JoystickInput::SetButtonName(int button, const std::string& name) {
  button_names_[button] = name;
}

auto JoystickInput::GetButtonName(int index) -> std::string {
  // First check any explicit ones we were passed.
  auto i = button_names_.find(index);
  if (i != button_names_.end()) {
    return i->second;
  }

  // FIXME: Should get fancier here now that PS4 and XBone
  // controllers are supported through this.
  if (is_mfi_controller_) {
    switch (index) {
      case 1:
        return "A";
      case 2:
        return "X";
      case 3:
        return "B";
      case 4:
        return "Y";
      default:
        break;
    }
  }

  if (g_buildconfig.platform_android()) {
    // Some standard android button names:
    switch (index) {
      case 20:
        return "Dpad Up";
      case 22:
        return "Dpad Left";
      case 23:
        return "Dpad Right";
      case 21:
        return "Dpad Down";
      case 102:
        return "Z";
      case 101:
        return "Y";
      case 100:
        return "X";
      case 99:
        return "C";
      case 98:
        return "B";
      case 97:
        return "A";
      case 83:
        return "Menu";
      case 110:
        return "Select";
      case 111:
        return "Mode";
      case 109:
        return "Start";
      case 107:
        return "Thumb-L";
      case 108:
        return "Thumb-R";
      case 103:
        return "L1";
      case 104:
        return "R1";
      case 105:
        return "L2";
      case 106:
        return "R2";
      case 126:
        return "Forward";
      case 189:
        return "B1";
      case 190:
        return "B2";
      case 191:
        return "B3";
      case 192:
        return "B4";
      case 193:
        return "B5";
      case 194:
        return "B6";
      case 195:
        return "B7";
      case 196:
        return "B8";
      case 197:
        return "B9";
      case 198:
        return "B10";
      case 199:
        return "B11";
      case 200:
        return "B12";
      case 201:
        return "B13";
      case 202:
        return "B14";
      case 203:
        return "B15";
      case 204:
        return "B16";
      case 90:
        return g_base->assets->CharStr(SpecialChar::kRewindButton);
      case 91:
        return g_base->assets->CharStr(SpecialChar::kFastForwardButton);
      case 24:
        return g_base->assets->CharStr(SpecialChar::kDpadCenterButton);
      case 86:
        return g_base->assets->CharStr(SpecialChar::kPlayPauseButton);
      default:
        break;
    }
  }
  return InputDevice::GetButtonName(index);
}

JoystickInput::~JoystickInput() {
  if (!g_base->InLogicThread()) {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "Joystick dying in wrong thread.");
  }

  // Kill our child if need be.
  if (child_joy_stick_) {
    g_base->input->RemoveInputDevice(child_joy_stick_, true);
    child_joy_stick_ = nullptr;
  }

  // Have SDL actually close the joystick in the main thread.
  // Send a message back to the main thread to close this SDL Joystick.
  // HMMM - can we just have the main thread close the joystick immediately
  // before informing us its dead?.. i don't think we actually use it at all
  // here in the logic thread..
  if (sdl_joystick_) {
#if BA_ENABLE_SDL_JOYSTICKS
    assert(g_base->app_adapter);
    auto joystick = sdl_joystick_;
    g_base->app_adapter->PushMainThreadCall(
        [joystick] { SDL_JoystickClose(joystick); });
    sdl_joystick_ = nullptr;
#else
    g_core->logging->Log(
        LogName::kBaInput, LogLevel::kError,
        "sdl_joystick_ set in non-sdl-joystick build destructor.");
#endif  // BA_ENABLE_SDL_JOYSTICKS
  }
}

void JoystickInput::OnAdded() { assert(g_base->InLogicThread()); }

auto JoystickInput::ShouldBeHiddenFromUser() -> bool {
  std::string d_name = GetDeviceName();

  // To lowercase.
  int sz = static_cast<int>(d_name.size());
  for (int i = 0; i < sz; i++) {
    if (d_name[i] <= 'Z' && d_name[i] >= 'A') d_name[i] -= ('Z' - 'z');
  }

  const char* n = d_name.c_str();
  if (strstr(n, "mouse") || strstr(n, "keyboard")
      || strstr(n, "athome_remote")) {
    return true;
  } else {
    return InputDevice::ShouldBeHiddenFromUser();
  }
}

auto JoystickInput::GetCalibratedValue(float raw, float neutral) const
    -> int32_t {
  int32_t val;
  float dead_zone = 0.5f;
  float mag, target;
  if (raw > neutral) {
    mag = ((raw - neutral) / (calibration_threshold_ - neutral));
    target = calibration_threshold_;
  } else {
    mag = ((raw - neutral) / (-calibration_threshold_ - neutral));
    target = -calibration_threshold_;
  }
  if (mag < dead_zone) {
    val = 0;
  } else {
    val = static_cast<int32_t>((1.0f - dead_zone) * mag * target);
  }
  return val;
}

void JoystickInput::Update() {
  InputDevice::Update();

  assert(g_base->InLogicThread());

  // We seem to get a fair amount of bogus direction-pressed events from newly
  // plugged in joysticks.. this leads to continuous scrolling in menus and such
  // ...so lets reset our state once early after we're created.
  if (!did_initial_reset_) {
    ResetHeldStates();
    did_initial_reset_ = true;
  }

  // Let's take this opportunity to update our calibration
  // (should probably have a specific place to do that but this works)
  if (calibrate_) {
    millisecs_t time = g_core->AppTimeMillisecs();

    // If we're doing 'aggressive' auto-recalibration we expand extents outward
    // but suck them inward a tiny bit too to account for jitter or random fluke
    // points.
    if (auto_recalibrate_analog_stick_) {
      int cell = static_cast<int>(
          (atan2(static_cast<float>(jaxis_y_), static_cast<float>(jaxis_x_))
           + kPi)
          * ((kJoystickAnalogCalibrationDivisions) / (2.0f * kPi)));
      cell =
          std::min(kJoystickAnalogCalibrationDivisions - 1, std::max(0, cell));
      auto x{static_cast<float>(jaxis_x_) / 32767.0f};
      float y{static_cast<float>(jaxis_y_) / 32767.0f};
      float mag = sqrtf(x * x + y * y);
      if (mag > analog_calibration_vals_[cell]) {
        analog_calibration_vals_[cell] = std::min(1.0f, mag);

        // Push the cell value up towards us a bit and also have it fall by a
        // constant amount.
        analog_calibration_vals_[cell] = std::min(
            1.0f,
            std::max(0.25f,
                     0.9f
                         * (analog_calibration_vals_[cell]
                            + (mag - analog_calibration_vals_[cell]) * 0.15f)));
      }
    }

    // Calibration: if we've been below our calibration thresholds for more than
    // calibration-time, start averaging our current value into our calibrated
    // neutral.
    if (time - calibration_start_time_x_ > kJoystickCalibrationTimeThreshold
        && (static_cast<float>(std::abs(jaxis_raw_x_))
            < calibration_threshold_)) {
      calibrated_neutral_x_ =
          kJoystickCalibrationSpeed * static_cast<float>(jaxis_raw_x_)
          + (1.0f - kJoystickCalibrationSpeed) * calibrated_neutral_x_;

      // Grab our new calibrated x value.. if it differs from the current, ship
      // an event.
      if (static_cast<float>(std::abs(jaxis_raw_x_)) < calibration_threshold_) {
        int32_t x = GetCalibratedValue(static_cast<float>(jaxis_raw_x_),
                                       calibrated_neutral_x_);
        if (x != jaxis_x_) {
          jaxis_x_ = x;
          InputCommand(InputType::kLeftRight,
                       static_cast<float>(jaxis_x_) / 32767.0f);
        }
      }
    }

    if (time - calibration_start_time_y_ > kJoystickCalibrationTimeThreshold
        && (static_cast<float>(std::abs(jaxis_raw_y_))
            < calibration_threshold_)) {
      calibrated_neutral_y_ =
          kJoystickCalibrationSpeed * static_cast<float>(jaxis_raw_y_)
          + (1.0f - kJoystickCalibrationSpeed) * calibrated_neutral_y_;

      // Grab our new calibrated x value.. if it differs from the current, ship
      // an event.
      if (fabs(static_cast<float>(jaxis_raw_y_)) < calibration_threshold_) {
        int32_t y = GetCalibratedValue(static_cast<float>(jaxis_raw_y_),
                                       calibrated_neutral_y_);
        if (y != jaxis_y_) {
          jaxis_y_ = y;
          InputCommand(InputType::kUpDown,
                       static_cast<float>(jaxis_y_) / 32767.0f);
        }
      }
    }
  }
}

void JoystickInput::SetStandardExtendedButtons() {
  // Assign some non-zero dpad values so we can drive them in custom joysticks.
  up_button_ = 20;
  down_button_ = 21;
  left_button_ = 22;
  right_button_ = 23;
  run_trigger1_ = 10;
  run_trigger2_ = 11;
  back_button_ = 12;
  remote_enter_button_ = 13;
}

void JoystickInput::ResetHeldStates() {
  // So we push events through even if there's a dialog in the way.
  resetting_ = true;

  // Send ourself neutral joystick events.
  SDL_Event e;

  dpad_right_held_ = dpad_left_held_ = dpad_up_held_ = dpad_down_held_ = false;
  ui_repeater_.Clear();

  run_buttons_held_.clear();
  run_trigger1_value_ = run_trigger2_value_ = 0.0f;
  UpdateRunningState();

  if (hat_held_) {
    e.type = SDL_JOYHATMOTION;
    e.jhat.hat = static_cast_check_fit<uint8_t>(hat_);
    e.jhat.value = SDL_HAT_CENTERED;
    HandleSDLEvent(&e);
  }

  e.type = SDL_JOYAXISMOTION;
  e.jaxis.axis = static_cast_check_fit<uint8_t>(analog_lr_);
  e.jaxis.value = static_cast<int16_t>(calibrated_neutral_x_);
  HandleSDLEvent(&e);

  e.type = SDL_JOYAXISMOTION;
  e.jaxis.axis = static_cast_check_fit<uint8_t>(analog_ud_);
  e.jaxis.value = static_cast<int16_t>(calibrated_neutral_y_);
  HandleSDLEvent(&e);

  resetting_ = false;
}

void JoystickInput::HandleSDLEvent(const SDL_Event* e) {
  assert(g_base->InLogicThread());

  // If we've got a child joystick, send them any events they're set to handle.
  if (child_joy_stick_) {
    assert(g_base->logic);

    bool send = false;
    switch (e->type) {
      case SDL_JOYAXISMOTION: {
        // If its their analog stick or one of their run-triggers, send.
        if (e->jaxis.axis == child_joy_stick_->analog_lr_
            || e->jaxis.axis == child_joy_stick_->analog_ud_
            || e->jaxis.axis == child_joy_stick_->run_trigger1_
            || e->jaxis.axis == child_joy_stick_->run_trigger2_)
          send = true;
        break;
      }
      case SDL_JOYHATMOTION: {
        // If its their dpad hat, send.
        if (e->jhat.hat == child_joy_stick_->hat_) send = true;
        break;
      }
      case SDL_JOYBUTTONDOWN:
      case SDL_JOYBUTTONUP: {
        // If its one of their 4 action buttons, 2 run buttons, or start, send.
        if (e->jbutton.button == child_joy_stick_->jump_button_
            || e->jbutton.button == child_joy_stick_->punch_button_
            || e->jbutton.button == child_joy_stick_->bomb_button_
            || e->jbutton.button == child_joy_stick_->pickup_button_
            || e->jbutton.button == child_joy_stick_->start_button_
            || e->jbutton.button == child_joy_stick_->start_button_2_
            || e->jbutton.button == child_joy_stick_->run_button1_
            || e->jbutton.button == child_joy_stick_->run_button2_)
          send = true;
        break;
      }
      default:
        break;
    }
    if (send) {
      g_base->input->PushJoystickEvent(*e, child_joy_stick_);
      return;
    }
  }

  // If we're set to ignore events completely, do so.
  if (ignore_completely_) {
    return;
  }

  millisecs_t time = g_core->AppTimeMillisecs();
  SDL_Event e2;

  // Ignore analog-stick input while we're holding a hat switch or d-pad
  // buttons.
  if ((e->type == SDL_JOYAXISMOTION
       && (e->jaxis.axis == analog_lr_ || e->jaxis.axis == analog_ud_))
      && (hat_held_ || dpad_right_held_ || dpad_left_held_ || dpad_up_held_
          || dpad_down_held_))
    return;

  bool is_hold_position_event = false;

  // Keep track of whether hold-position is being held. If so, we don't send
  // window events (some joysticks always give us significant axis values but
  // rely on hold position to keep from doing stuff usually).
  if (e->type == SDL_JOYBUTTONDOWN
      && e->jbutton.button == hold_position_button_) {
    need_to_send_held_state_ = true;
    hold_position_held_ = true;
    is_hold_position_event = true;
  }
  if (e->type == SDL_JOYBUTTONUP
      && e->jbutton.button == hold_position_button_) {
    need_to_send_held_state_ = true;
    hold_position_held_ = false;
    is_hold_position_event = true;
  }

  // Let's ignore events for just a moment after we're created.
  // (some joysticks seem to spit out erroneous button-pressed events when
  // first plugged in ).
  if (time - creation_time_ < 250 && !is_hold_position_event) {
    return;
  }

  // If we're using dpad-buttons, let's convert those events into joystick
  // events.
  // FIXME: should we do the same for hat buttons just to keep things
  //  consistent?
  if (up_button_ >= 0 || left_button_ >= 0 || right_button_ >= 0
      || down_button_ >= 0 || up_button2_ >= 0 || left_button2_ >= 0
      || right_button2_ >= 0 || down_button2_ >= 0) {
    switch (e->type) {
      case SDL_JOYBUTTONDOWN:
      case SDL_JOYBUTTONUP:
        if (e->jbutton.button == right_button_
            || e->jbutton.button == right_button2_) {  // D-pad right.
          e2.type = SDL_JOYAXISMOTION;
          e2.jaxis.axis = static_cast_check_fit<uint8_t>(analog_lr_);
          dpad_right_held_ = (e->type == SDL_JOYBUTTONDOWN);
          e2.jaxis.value = static_cast_check_fit<int16_t>(
              dpad_right_held_  ? (dpad_left_held_ ? 0 : 32767)
              : dpad_left_held_ ? -32767
                                : 0);
          e = &e2;
        } else if (e->jbutton.button == left_button_
                   || e->jbutton.button == left_button2_) {
          e2.type = SDL_JOYAXISMOTION;
          e2.jaxis.axis = static_cast_check_fit<uint8_t>(analog_lr_);
          dpad_left_held_ = (e->type == SDL_JOYBUTTONDOWN);
          e2.jaxis.value = static_cast_check_fit<int16_t>(
              dpad_right_held_  ? (dpad_left_held_ ? 0 : 32767)
              : dpad_left_held_ ? -32767
                                : 0);
          e = &e2;
        } else if (e->jbutton.button == up_button_
                   || e->jbutton.button == up_button2_) {
          e2.type = SDL_JOYAXISMOTION;
          e2.jaxis.axis = static_cast_check_fit<uint8_t>(analog_ud_);
          dpad_up_held_ = (e->type == SDL_JOYBUTTONDOWN);
          e2.jaxis.value = static_cast_check_fit<int16_t>(
              dpad_up_held_     ? (dpad_down_held_ ? 0 : -32767)
              : dpad_down_held_ ? 32767
                                : 0);
          e = &e2;
        } else if (e->jbutton.button == down_button_
                   || e->jbutton.button == down_button2_) {
          e2.type = SDL_JOYAXISMOTION;
          e2.jaxis.axis = static_cast_check_fit<uint8_t>(analog_ud_);
          dpad_down_held_ = (e->type == SDL_JOYBUTTONDOWN);
          e2.jaxis.value = static_cast_check_fit<int16_t>(
              dpad_up_held_     ? (dpad_down_held_ ? 0 : -32767)
              : dpad_down_held_ ? 32767
                                : 0);
          e = &e2;
        }
        break;
      default:
        break;
    }
  }

  // Track our hat-held state independently.
  if (e->type == SDL_JOYHATMOTION && e->jhat.hat == hat_) {
    switch (e->jhat.value) {
      case SDL_HAT_CENTERED:
        hat_held_ = false;
        break;
      case SDL_HAT_UP:
      case SDL_HAT_DOWN:
      case SDL_HAT_LEFT:
      case SDL_HAT_RIGHT:
      case SDL_HAT_LEFTUP:     // NOLINT (signed bitwise)
      case SDL_HAT_RIGHTUP:    // NOLINT (signed bitwise)
      case SDL_HAT_RIGHTDOWN:  // NOLINT (signed bitwise)
      case SDL_HAT_LEFTDOWN:   // NOLINT (signed bitwise)
        hat_held_ = true;
        break;
      default:
        BA_LOG_ONCE(LogName::kBaInput, LogLevel::kError,
                    "Invalid hat value: "
                        + std::to_string(static_cast<int>(e->jhat.value)));
        break;
    }
  }

  // If its an ignored button, ignore it.
  if ((e->type == SDL_JOYBUTTONDOWN || e->type == SDL_JOYBUTTONUP)
      && (e->jbutton.button == ignored_button_
          || e->jbutton.button == ignored_button2_
          || e->jbutton.button == ignored_button3_
          || e->jbutton.button == ignored_button4_)) {
    return;
  }

  // A few high level button press interceptions.
  if (e->type == SDL_JOYBUTTONDOWN) {
    if (e->jbutton.button == start_button_
        || e->jbutton.button == start_button_2_) {
      // If there's no main ui up, request one with us as owner.
      if (!g_base->ui->IsMainUIVisible()) {
        g_base->ui->RequestMainUI(this);
        return;
      }
    }

    // On our Oculus build, select presses reset the orientation.
    if (e->jbutton.button == vr_reorient_button_ && g_core->vr_mode()) {
      g_base->ScreenMessage(
          g_base->assets->GetResourceString("vrOrientationResetText"),
          {0, 1, 0});
      g_core->reset_vr_orientation = true;
      return;
    }
  }

  // Update some calibration parameters.
  if (e->type == SDL_JOYAXISMOTION) {
    if (e->jaxis.axis == analog_lr_) {
      // If we've moved by more than a small amount, break calibration.
      if (static_cast<float>(abs(e->jaxis.value - jaxis_raw_x_))
          > calibration_break_threshold_) {
        calibration_start_time_x_ = time;
      }
      jaxis_raw_x_ = e->jaxis.value;

      // Just take note if we're below our calibration threshold
      // (actual calibration happens in update-repeats).
      if (static_cast<float>(abs(e->jaxis.value)) > calibration_threshold_) {
        calibration_start_time_x_ = time;
      }
    } else if (e->jaxis.axis == analog_ud_) {
      // If we've moved by more than a small amount, break calibration.
      if (static_cast<float>(abs(e->jaxis.value - jaxis_raw_y_))
          > calibration_break_threshold_) {
        calibration_start_time_y_ = time;
      }
      jaxis_raw_y_ = e->jaxis.value;

      // Just take note if we're below our calibration threshold
      // (actual calibration happens in update-repeats).
      if (static_cast<float>(abs(e->jaxis.value)) > calibration_threshold_) {
        calibration_start_time_y_ = time;
      }
    }
  }

  // If we're in the ui, send ui events.
  // We keep track of special x/y values for ui usage.
  // These are formed as combinations of the actual joy value
  // and the hold-position state.
  // Think of hold-position as somewhat of a 'magnitude' to the joy event's
  // direction. They're really one and the same event. (we just need to store
  // their states ourselves since they don't both come through at once).
  // FIXME: Ugh need to rip out this old hold-position stuff.
  bool is_analog_stick_jaxis_event = false;
  if (e->type == SDL_JOYAXISMOTION) {
    if (e->jaxis.axis == analog_lr_) {
      dialog_jaxis_x_ = e->jaxis.value;
      is_analog_stick_jaxis_event = true;
    } else if (e->jaxis.axis == analog_ud_) {
      dialog_jaxis_y_ = e->jaxis.value;
      is_analog_stick_jaxis_event = true;
    }
  }
  int ui_jaxis_x = dialog_jaxis_x_;
  if (hold_position_held_) {
    ui_jaxis_x = 0;  // Throttle is off.
  }
  int ui_jaxis_y = dialog_jaxis_y_;
  if (hold_position_held_) {
    ui_jaxis_y = 0;  // Throttle is off.
  }

  // We might not wanna grab at the UI if we're a axis-motion event
  // below our 'pressed' threshold.. Otherwise fuzzy analog joystick
  // readings would cause rampant UI stealing even if no events are being sent.
  bool would_go_to_ui = false;
  auto wm = WidgetMessage::Type::kEmptyMessage;

  if (is_analog_stick_jaxis_event || is_hold_position_event) {
    // Even when we're not sending, clear out some 'held' states.
    if (left_held_ && ui_jaxis_x >= -kJoystickDiscreteThreshold) {
      left_held_ = false;
      ui_repeater_.Clear();
    }
    if (right_held_ && ui_jaxis_x <= kJoystickDiscreteThreshold) {
      right_held_ = false;
      ui_repeater_.Clear();
    }
    if (up_held_ && ui_jaxis_y >= -kJoystickDiscreteThreshold) {
      up_held_ = false;
      ui_repeater_.Clear();
    }
    if (down_held_ && ui_jaxis_y <= kJoystickDiscreteThreshold) {
      down_held_ = false;
      ui_repeater_.Clear();
    }
    if ((!right_held_) && ui_jaxis_x > kJoystickDiscreteThreshold) {
      would_go_to_ui = true;
    }
    if ((!left_held_) && ui_jaxis_x < -kJoystickDiscreteThreshold) {
      would_go_to_ui = true;
    }
    if ((!up_held_) && ui_jaxis_y < -kJoystickDiscreteThreshold) {
      would_go_to_ui = true;
    }
    if ((!down_held_) && ui_jaxis_y > kJoystickDiscreteThreshold) {
      would_go_to_ui = true;
    }
  } else if ((e->type == SDL_JOYHATMOTION && e->jhat.hat == hat_)
             || (e->type == SDL_JOYBUTTONDOWN
                 && e->jbutton.button != hold_position_button_)) {
    // Other button-downs and hat motions always go.
    would_go_to_ui = true;
  }

  // Resets always circumvent dialogs.
  if (resetting_) {
    would_go_to_ui = false;
  }

  // Anything that would go to ui also counts to mark us as 'recently-used'.
  if (would_go_to_ui) {
    if (!(allow_input_in_attract_mode() && g_base->input->attract_mode())) {
      UpdateLastActiveTime();
    }
  }

  if (would_go_to_ui && g_base->ui->RequestMainUIControl(this)) {
    bool pass{};

    // Special case.. either joy-axis-motion or hold-position events trigger
    // these.
    if (is_analog_stick_jaxis_event || is_hold_position_event) {
      if (ui_jaxis_x > kJoystickDiscreteThreshold) {
        if (!right_held_ && !up_held_ && !down_held_) {
          right_held_ = true;
          pass = true;
          wm = WidgetMessage::Type::kMoveRight;
        }
      } else if (ui_jaxis_x < -kJoystickDiscreteThreshold) {
        if (!left_held_ && !up_held_ && !down_held_) {
          left_held_ = true;
          pass = true;
          wm = WidgetMessage::Type::kMoveLeft;
        }
      }
      if (ui_jaxis_y > kJoystickDiscreteThreshold) {
        if (!down_held_ && !left_held_ && !right_held_) {
          down_held_ = true;
          pass = true;
          wm = WidgetMessage::Type::kMoveDown;
        }
      } else if (ui_jaxis_y < -kJoystickDiscreteThreshold) {
        if (!up_held_ && !left_held_ && !right_held_) {
          up_held_ = true;
          pass = true;
          wm = WidgetMessage::Type::kMoveUp;
        }
      }
    }

    switch (e->type) {
      case SDL_JOYAXISMOTION:
        break;

      case SDL_JOYHATMOTION: {
        if (e->jhat.hat == hat_) {
          switch (e->jhat.value) {
            case SDL_HAT_LEFT: {
              if (!left_held_) {
                wm = WidgetMessage::Type::kMoveLeft;
                pass = true;
                left_held_ = true;
                right_held_ = false;
              }
              break;
            }

            case SDL_HAT_RIGHT: {
              if (!right_held_) {
                wm = WidgetMessage::Type::kMoveRight;
                pass = true;
                right_held_ = true;
                left_held_ = false;
              }
              break;
            }
            case SDL_HAT_UP: {
              if (!up_held_) {
                wm = WidgetMessage::Type::kMoveUp;
                pass = true;
                up_held_ = true;
                down_held_ = false;
              }
              break;
            }
            case SDL_HAT_DOWN: {
              if (!down_held_) {
                wm = WidgetMessage::Type::kMoveDown;
                pass = true;
                down_held_ = true;
                up_held_ = false;
              }
              break;
            }
            case SDL_HAT_CENTERED: {
              up_held_ = false;
              down_held_ = false;
              left_held_ = false;
              right_held_ = false;
              ui_repeater_.Clear();
            }
            default:
              break;
          }
        }
        break;
      }
      case SDL_JOYBUTTONDOWN: {
        if (e->jbutton.button != hold_position_button_) {
          pass = true;
          if (e->jbutton.button == start_button_
              || e->jbutton.button == start_button_2_) {
            if (start_button_activates_default_widget_) {
              wm = WidgetMessage::Type::kStart;
            } else {
              pass = false;
            }
          } else if (e->jbutton.button == bomb_button_
                     || e->jbutton.button == back_button_) {
            wm = WidgetMessage::Type::kCancel;
          } else {
            // Toggle the party UI if we're pressing the party button.
            // (currently don't allow remote to do this.. need to make it
            // customizable)
            if (g_base->ui->IsPartyIconVisible()
                && e->jbutton.button == pickup_button_
                && (!IsRemoteControl())) {
              pass = false;
              g_base->ui->ActivatePartyIcon();
              break;
            }
            wm = WidgetMessage::Type::kActivate;
          }
        }
      } break;
      default:
        break;
    }
    if (pass) {
      switch (wm) {
        case WidgetMessage::Type::kMoveUp:
        case WidgetMessage::Type::kMoveDown:
        case WidgetMessage::Type::kMoveLeft:
        case WidgetMessage::Type::kMoveRight:
          // For UI movement, set up a repeater so we can hold the button.
          ui_repeater_ = Repeater::New(
              kUINavigationRepeatDelay, kUINavigationRepeatInterval,
              [wm] { g_base->ui->SendWidgetMessage(WidgetMessage(wm)); });
          break;
        default:
          // Other messages are just one-shots.
          g_base->ui->SendWidgetMessage(WidgetMessage(wm));
      }
    }
    return;
  }

  // If there's a UI up (even if we didn't get it) lets not pass events along.
  // The only exception is if we're doing a reset.
  if (g_base->ui->IsMainUIVisible() && !resetting_) {
    return;
  }

  if (!AttachedToPlayer()) {
    if (e->type == SDL_JOYBUTTONDOWN
        && (e->jbutton.button != hold_position_button_)
        && (e->jbutton.button != back_button_)) {
      if (ui_only_ || e->jbutton.button == remote_enter_button_) {
        millisecs_t current_time = g_core->AppTimeMillisecs();
        if (current_time - last_ui_only_print_time_ > 5000) {
          g_base->python->objs()
              .Get(BasePython::ObjID::kUIRemotePressCall)
              .Call();
          last_ui_only_print_time_ = current_time;
        }
      } else {
        RequestPlayer();
        // we always want to inform new players of our hold-position-state..
        // make a note to do that.
        need_to_send_held_state_ = true;
      }
    }
    return;
  }

  // Ok we've got a player; just send events along.

  // Held state is a special case; we wanna always send that along first thing
  // if its changed. This is because some joysticks rely on it being on by
  // default.
  if (need_to_send_held_state_) {
    if (hold_position_held_) {
      InputCommand(InputType::kHoldPositionPress);
    } else {
      InputCommand(InputType::kHoldPositionRelease);
    }
    need_to_send_held_state_ = false;
  }

  switch (e->type) {
    case SDL_JOYAXISMOTION: {
      // Handle run-trigger presses.
      if (e->jaxis.axis == run_trigger1_ || e->jaxis.axis == run_trigger2_) {
        if (e->jaxis.axis == run_trigger1_) {
          float value = static_cast<float>(e->jaxis.value) / 32767.0f;

          // If we're calibrating, update calibration bounds and calc a
          // calibrated value.
          if (calibrate_) {
            if (value < run_trigger1_min_) {
              run_trigger1_min_ = value;
            } else if (value > run_trigger1_max_) {
              run_trigger1_max_ = value;
            }
            run_trigger1_value_ = (value - run_trigger1_min_)
                                  / (run_trigger1_max_ - run_trigger1_min_);
          } else {
            run_trigger1_value_ = value;
          }
        } else {
          float value = static_cast<float>(e->jaxis.value) / 32767.0f;

          // If we're calibrating, update calibration bounds and calc a
          // calibrated value.
          if (calibrate_) {
            if (value < run_trigger2_min_) {
              run_trigger2_min_ = value;
            } else if (value > run_trigger2_max_) {
              run_trigger2_max_ = value;
            }
            run_trigger2_value_ = (value - run_trigger2_min_)
                                  / (run_trigger2_max_ - run_trigger2_min_);
          } else {
            run_trigger2_value_ = value;
          }
        }
        UpdateRunningState();
      }
      InputType input_type;
      int32_t input_value;
      if (e->jaxis.axis == analog_lr_) {
        input_type = InputType::kLeftRight;
        input_value = e->jaxis.value;
        if (calibrate_) {
          if (static_cast<float>(abs(jaxis_raw_x_)) < calibration_threshold_
              && static_cast<float>(abs(jaxis_raw_y_))
                     < calibration_threshold_) {
            input_value = GetCalibratedValue(static_cast<float>(input_value),
                                             calibrated_neutral_x_);
          }
        }
        if (input_value > 32767) {
          input_value = 32767;
        } else if (input_value < -32767) {
          input_value = -32767;
        }
        jaxis_x_ = input_value;
      } else if (e->jaxis.axis == analog_ud_) {
        input_type = InputType::kUpDown;
        input_value = e->jaxis.value;
        if (calibrate_) {
          if (static_cast<float>(abs(jaxis_raw_x_)) < calibration_threshold_
              && static_cast<float>(abs(jaxis_raw_y_))
                     < calibration_threshold_) {
            input_value = GetCalibratedValue(static_cast<float>(input_value),
                                             calibrated_neutral_y_);
          }
        }
        input_value = -input_value;
        if (input_value > 32767) {
          input_value = 32767;
        } else if (input_value < -32767) {
          input_value = -32767;
        }
        jaxis_y_ = input_value;
      } else {
        break;
      }

      // Update extent calibration and scale based on that.
      if (calibrate_) {
        // Handle analog stick calibration.. 'full' auto-recalibration.
        if (auto_recalibrate_analog_stick_) {
          int cell = static_cast<int>(
              (atan2f(static_cast<float>(jaxis_y_),
                      static_cast<float>(jaxis_x_))
               + kPi)
              * ((kJoystickAnalogCalibrationDivisions) / (2.0f * kPi)));
          cell = std::min(kJoystickAnalogCalibrationDivisions - 1,
                          std::max(0, cell));
          input_value =
              static_cast<int32_t>(static_cast<float>(input_value)
                                   * (1.0f / analog_calibration_vals_[cell]));
          if (input_value > 32767) {
            input_value = 32767;
          } else if (input_value < -32767) {
            input_value = -32767;
          }
        }
      }
      InputCommand(input_type, static_cast<float>(input_value) / 32767.0f);
      break;
    }
    case SDL_JOYBUTTONDOWN: {
      if (unassigned_buttons_run_ || e->jbutton.button == punch_button_
          || e->jbutton.button == jump_button_
          || e->jbutton.button == bomb_button_
          || e->jbutton.button == pickup_button_
          || e->jbutton.button == run_button1_
          || e->jbutton.button == run_button2_) {
        run_buttons_held_.insert(e->jbutton.button);
      }
      UpdateRunningState();
      if (e->jbutton.button == jump_button_) {
        // FIXME: we should just do one or the other here depending on the game
        //  mode to reduce the number of events sent.
        InputCommand(InputType::kJumpPress);
        InputCommand(InputType::kFlyPress);
      } else if (e->jbutton.button == punch_button_) {
        InputCommand(InputType::kPunchPress);
      } else if (e->jbutton.button == bomb_button_) {
        InputCommand(InputType::kBombPress);
      } else if (e->jbutton.button == pickup_button_) {
        InputCommand(InputType::kPickUpPress);
      }
      break;
    }
    case SDL_JOYBUTTONUP: {
      {
        auto i = run_buttons_held_.find(e->jbutton.button);
        if (i != run_buttons_held_.end()) {
          run_buttons_held_.erase(i);
        }
        UpdateRunningState();
      }
      if (e->jbutton.button == jump_button_) {
        InputCommand(InputType::kJumpRelease);
        InputCommand(InputType::kFlyRelease);
      } else if (e->jbutton.button == punch_button_) {
        InputCommand(InputType::kPunchRelease);
      } else if (e->jbutton.button == bomb_button_) {
        InputCommand(InputType::kBombRelease);
      } else if (e->jbutton.button == pickup_button_) {
        InputCommand(InputType::kPickUpRelease);
      }
      break;
    }
    case SDL_JOYBALLMOTION: {
      break;
    }
    case SDL_JOYHATMOTION: {
      if (e->jhat.hat == hat_) {
        int16_t input_value_lr = 0;
        int16_t input_value_ud = 0;
        switch (e->jhat.value) {
          case SDL_HAT_CENTERED:
            input_value_lr = 0;
            input_value_ud = 0;
            break;
          case SDL_HAT_UP:
            input_value_lr = 0;
            input_value_ud = 32767;
            break;
          case SDL_HAT_DOWN:
            input_value_lr = 0;
            input_value_ud = -32767;
            break;
          case SDL_HAT_LEFT:
            input_value_lr = -32767;
            input_value_ud = 0;
            break;
          case SDL_HAT_RIGHT:
            input_value_lr = 32767;
            input_value_ud = 0;
            break;
          case SDL_HAT_LEFTUP:  // NOLINT (signed bitwise)
            input_value_lr = -32767;
            input_value_ud = 32767;
            break;
          case SDL_HAT_RIGHTUP:  // NOLINT (signed bitwise)
            input_value_lr = 32767;
            input_value_ud = 32767;
            break;
          case SDL_HAT_RIGHTDOWN:  // NOLINT (signed bitwise)
            input_value_lr = 32767;
            input_value_ud = -32767;
            break;
          case SDL_HAT_LEFTDOWN:  // NOLINT (signed bitwise)
            input_value_lr = -32767;
            input_value_ud = -32767;
            break;
          default:
            break;
        }
        InputCommand(InputType::kLeftRight,
                     static_cast<float>(input_value_lr) / 32767.0f);
        InputCommand(InputType::kUpDown,
                     static_cast<float>(input_value_ud) / 32767.0f);
      }
      break;
    }
    default:
      break;
  }
}  // NOLINT(readability/fn_size) Yes I know this is too long.

void JoystickInput::UpdateRunningState() {
  if (!AttachedToPlayer()) {
    return;
  }
  float value;
  float prev_value = run_value_;

  // If there's a button held, our default value is 1.0.
  if (!run_buttons_held_.empty()) {
    value = 1.0f;
  } else {
    value = 0.0f;
  }

  // Now check our analog run triggers.
  value = std::max(value, run_trigger1_value_);
  value = std::max(value, run_trigger2_value_);

  if (value != prev_value) {
    run_value_ = value;
    InputCommand(InputType::kRun, run_value_);
  }
}

void JoystickInput::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  // This doesn't apply to manual ones (except children which are).
  if (!can_configure_ && !parent_joy_stick_) {
    return;
  }

  auto* cl{g_base->HaveClassic() ? g_base->classic() : nullptr};

  if (!cl) {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kWarning,
                         "Classic not present; can't config joystick mapping.");
  }

  // If we're a child, use our parent's id to search for config values and just
  // tack on a '2'.
  JoystickInput* js = parent_joy_stick_ ? parent_joy_stick_ : this;
  std::string ext = parent_joy_stick_ ? "_B" : "";

  // Grab all button values from Python. Traditionally we stored these
  // with the first index 1 so we need to subtract 1 to get the zero-indexed
  // value. (grumble).
  jump_button_ = cl->GetControllerValue(js, "buttonJump" + ext) - 1;
  punch_button_ = cl->GetControllerValue(js, "buttonPunch" + ext) - 1;
  bomb_button_ = cl->GetControllerValue(js, "buttonBomb" + ext) - 1;
  pickup_button_ = cl->GetControllerValue(js, "buttonPickUp" + ext) - 1;
  start_button_ = cl->GetControllerValue(js, "buttonStart" + ext) - 1;
  start_button_2_ = cl->GetControllerValue(js, "buttonStart2" + ext) - 1;
  hold_position_button_ =
      cl->GetControllerValue(js, "buttonHoldPosition" + ext) - 1;
  run_button1_ = cl->GetControllerValue(js, "buttonRun1" + ext) - 1;
  run_button2_ = cl->GetControllerValue(js, "buttonRun2" + ext) - 1;
  vr_reorient_button_ =
      cl->GetControllerValue(js, "buttonVRReorient" + ext) - 1;
  ignored_button_ = cl->GetControllerValue(js, "buttonIgnored" + ext) - 1;
  ignored_button2_ = cl->GetControllerValue(js, "buttonIgnored2" + ext) - 1;
  ignored_button3_ = cl->GetControllerValue(js, "buttonIgnored3" + ext) - 1;
  ignored_button4_ = cl->GetControllerValue(js, "buttonIgnored4" + ext) - 1;
  int old_run_trigger_1 = run_trigger1_;
  run_trigger1_ = cl->GetControllerValue(js, "triggerRun1" + ext) - 1;
  int old_run_trigger_2 = run_trigger2_;
  run_trigger2_ = cl->GetControllerValue(js, "triggerRun2" + ext) - 1;
  up_button_ = cl->GetControllerValue(js, "buttonUp" + ext) - 1;
  left_button_ = cl->GetControllerValue(js, "buttonLeft" + ext) - 1;
  right_button_ = cl->GetControllerValue(js, "buttonRight" + ext) - 1;
  down_button_ = cl->GetControllerValue(js, "buttonDown" + ext) - 1;
  up_button2_ = cl->GetControllerValue(js, "buttonUp2" + ext) - 1;
  left_button2_ = cl->GetControllerValue(js, "buttonLeft2" + ext) - 1;
  right_button2_ = cl->GetControllerValue(js, "buttonRight2" + ext) - 1;
  down_button2_ = cl->GetControllerValue(js, "buttonDown2" + ext) - 1;
  unassigned_buttons_run_ = static_cast<bool>(
      cl->GetControllerValue(js, "unassignedButtonsRun" + ext));

  // If our run trigger has changed, reset its calibration.
  // NOTE: It looks like on Mac we're getting analog trigger values from -1 to 1
  // while on Android we're getting from 0 to 1.. adding this calibration stuff
  // allows us to cover both cases though.
  if (old_run_trigger_1 != run_trigger1_) {
    run_trigger1_min_ = 0.2f;
    run_trigger1_max_ = 0.8f;
  }
  if (old_run_trigger_2 != run_trigger2_) {
    run_trigger2_min_ = 0.2f;
    run_trigger2_max_ = 0.8f;
  }

  int ival = cl->GetControllerValue(js, "uiOnly" + ext);
  if (ival == -1) {
    ui_only_ = false;
  } else {
    ui_only_ = static_cast<bool>(ival);
  }

  ival = cl->GetControllerValue(js, "ignoreCompletely" + ext);
  if (ival == -1) {
    ignore_completely_ = false;
  } else {
    ignore_completely_ = static_cast<bool>(ival);
  }

  ival = cl->GetControllerValue(js, "autoRecalibrateAnalogSticks" + ext);

  {
    bool was_on = auto_recalibrate_analog_stick_;
    if (ival == -1) {
      auto_recalibrate_analog_stick_ = false;
    } else {
      auto_recalibrate_analog_stick_ = static_cast<bool>(ival);
    }
    bool is_on = auto_recalibrate_analog_stick_;

    // If we're flipping on full auto-recalibration, start our extents small.
    if (!was_on && is_on) {
      for (float& analog_calibration_val : analog_calibration_vals_) {
        analog_calibration_val = 0.25f;
      }
    }

    // If we're flipping it off, reset to default calibration values.
    if (was_on && !is_on) {
      for (float& analog_calibration_val : analog_calibration_vals_) {
        analog_calibration_val = 0.6f;
      }
    }
  }

  ival = cl->GetControllerValue(js, "startButtonActivatesDefaultWidget" + ext);

  if (ival == -1) {
    start_button_activates_default_widget_ = true;
  } else {
    start_button_activates_default_widget_ = static_cast<bool>(ival);
  }

  // Update calibration stuff.
  float as = cl->GetControllerFloatValue(js, "analogStickDeadZone" + ext);

  if (as < 0) {
    as = 1.0f;
  }

  // Avoid possibility of divide-by-zero errors.
  if (as < 0.01f) {
    as = 0.01f;
  }

  calibration_threshold_ = kJoystickCalibrationThreshold * as;
  calibration_break_threshold_ = kJoystickCalibrationBreakThreshold * as;

  hat_ = cl->GetControllerValue(js, "dpad" + ext) - 1;

  // If unset, use our default.
  if (hat_ == -2) {
    if (parent_joy_stick_) {
      hat_ = 1;
    } else {
      hat_ = 0;
    }
  }

  // Grab our analog stick.
  analog_lr_ = cl->GetControllerValue(js, "analogStickLR" + ext) - 1;

  // If we got unset, set to our default.
  if (analog_lr_ == -2) {
    if (parent_joy_stick_) {
      analog_lr_ = 4;
    } else {
      analog_lr_ = 0;
    }
  }

  analog_ud_ = cl->GetControllerValue(js, "analogStickUD" + ext) - 1;

  // If we got unset, set to our default.
  if (analog_ud_ == -2) {
    if (parent_joy_stick_) {
      analog_ud_ = 5;
    } else {
      analog_ud_ = 1;
    }
  }

  // See whether we have a child-joystick and create it if need be.
  if (!parent_joy_stick_) {
    int enable = cl->GetControllerValue(js, "enableSecondary");
    if (enable == -1) {
      enable = 0;
    }

    // Create if need be.
    if (enable) {
      char m[256];
      snprintf(m, sizeof(m), "%s B", GetDeviceName().c_str());
      if (!child_joy_stick_) {
        child_joy_stick_ =
            Object::NewDeferred<JoystickInput>(-1,     // Not an sdl joystick.
                                               m,      // Device name.
                                               false,  // Allow configuring.
                                               true);  // Do calibrate.
        child_joy_stick_->parent_joy_stick_ = this;
        assert(g_base->input);
        g_base->input->AddInputDevice(child_joy_stick_, true);
      }
    } else {
      // Kill if need be.
      if (child_joy_stick_) {
        g_base->input->RemoveInputDevice(child_joy_stick_, true);
        child_joy_stick_ = nullptr;
      }
    }
  }
}

auto JoystickInput::DoGetDeviceName() -> std::string {
  if (!custom_device_name_.empty()) {
    return custom_device_name_;
  }

  // For sdl joysticks just return the sdl string.
  if (sdl_joystick_) {
    std::string s = raw_sdl_joystick_name_;
    if (s.empty()) {
      s = "untitled joystick";
    }
    return s;
  } else {
    // The one case we can currently hit this is with android controllers - (if
    // an empty name is passed for the controller type).
    return "Unknown Input Device";
  }
}

auto JoystickInput::GetPartyButtonName() const -> std::string {
  return g_base->assets->CharStr(SpecialChar::kTopButton);
}

}  // namespace ballistica::base
