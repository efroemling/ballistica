// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_JOYSTICK_INPUT_H_
#define BALLISTICA_BASE_INPUT_DEVICE_JOYSTICK_INPUT_H_

#include <map>
#include <set>
#include <string>

#include "ballistica/base/input/device/input_device.h"

namespace ballistica::base {

// iOS controllers feel more natural with a lower threshold here,
// but it throws off cheap controllers elsewhere.
// not sure what's the right answer.. (should revisit)
const int kJoystickDiscreteThreshold{15000};
const float kJoystickDiscreteThresholdFloat{0.46f};
const int kJoystickAnalogCalibrationDivisions{20};
// extern const char* kMFiControllerName;

/// A physical game controller.
class JoystickInput : public InputDevice {
 public:
  // Create from an SDL joystick id.
  // Pass -1 to create a manual joystick from a non-sdl-source.
  // (in which case you are in charge of feeding it SDL events to make it go)
  explicit JoystickInput(int index, const std::string& custom_device_name = "",
                         bool can_configure = true, bool calibrate = true);

  ~JoystickInput() override;

  void HandleSDLEvent(const SDL_Event* e) override;

  void ApplyAppConfig() override;
  void Update() override;
  void ResetHeldStates() override;

  auto sdl_joystick_id() const -> int { return sdl_joystick_id_; }
  auto sdl_joystick() const -> SDL_Joystick* { return sdl_joystick_; }

  auto GetAllowsConfiguring() -> bool override { return can_configure_; }

  // We treat anything marked as 'ui-only' as a remote too.
  // (perhaps should consolidate this with IsUIOnly?..
  // ...except there's some remotes we want to be able to join the game; hmmm)
  auto IsRemoteControl() -> bool override {
    return (is_remote_control_ || ui_only_);
  }

  auto GetPartyButtonName() const -> std::string override;

  auto GetAxisName(int index) -> std::string override;

  auto IsController() -> bool override { return true; }
  auto IsSDLController() -> bool override { return (sdl_joystick_ != nullptr); }

  auto ShouldBeHiddenFromUser() -> bool override;

  auto IsUIOnly() -> bool override { return ui_only_; }

  void set_is_test_input(bool val) { is_test_input_ = val; }

  auto IsTestInput() -> bool override { return is_test_input_; }
  auto IsRemoteApp() -> bool override { return is_remote_app_; }
  auto IsMFiController() -> bool override { return is_mfi_controller_; }

  void set_is_remote_app(bool val) { is_remote_app_ = val; }
  void set_is_mfi_controller(bool val) { is_mfi_controller_ = val; }

  void SetStandardExtendedButtons();
  void SetStartButtonActivatesDefaultWidget(bool value) {
    start_button_activates_default_widget_ = value;
  }

  auto HasMeaningfulButtonNames() -> bool override;

  auto GetButtonName(int index) -> std::string override;

  /// Custom controller types can pass in controller-specific button names.
  void SetButtonName(int button, const std::string& name);

 protected:
  auto DoGetDeviceName() -> std::string override;
  void OnAdded() override;

  auto start_button_activates_default_widget() -> bool override {
    return start_button_activates_default_widget_;
  }

 private:
  void UpdateRunningState();
  auto GetCalibratedValue(float raw, float neutral) const -> int32_t;

  JoystickInput* child_joy_stick_{};
  JoystickInput* parent_joy_stick_{};
  millisecs_t last_ui_only_print_time_{};
  millisecs_t creation_time_{};

  // FIXME - should take this out and replace it with a bool
  //  (we never actually access the sdl joystick directly outside of our
  //  constructor)
  SDL_Joystick* sdl_joystick_{};

  bool ui_only_{};
  bool unassigned_buttons_run_{true};
  bool start_button_activates_default_widget_{true};
  bool auto_recalibrate_analog_stick_{};
  bool did_initial_reset_{};
  bool is_test_input_{};
  bool is_remote_control_{};
  bool is_remote_app_{};
  bool is_mfi_controller_{};

  // For dialogs.
  bool left_held_{};
  bool right_held_{};
  bool up_held_{};
  bool down_held_{};
  bool hold_position_held_{};
  bool need_to_send_held_state_{};

  bool hat_held_{};
  bool dpad_right_held_{};
  bool dpad_left_held_{};
  bool dpad_up_held_{};
  bool dpad_down_held_{};

  bool ignore_completely_{};
  bool resetting_{};
  bool calibrate_{};
  bool can_configure_{};

  int hat_{0};
  int analog_lr_{0};
  int analog_ud_{1};

  // Mappings of ba buttons to SDL buttons.
  int jump_button_{0};
  int punch_button_{1};
  int bomb_button_{2};
  int pickup_button_{3};
  int start_button_{5};
  int start_button_2_{-1};
  int hold_position_button_{25};
  int back_button_{-1};

  // Used on rift build; we have one button which we disallow from joining but
  // the rest we allow. (all devices are treated as one and the same there).
  int remote_enter_button_{-1};
  int ignored_button_{-1};
  int ignored_button2_{-1};
  int ignored_button3_{-1};
  int ignored_button4_{-1};
  int run_button1_{-1};
  int run_button2_{-1};
  int run_trigger1_{-1};
  int run_trigger2_{-1};
  int vr_reorient_button_{-1};
  int left_button_{-1};
  int right_button_{-1};
  int up_button_{-1};
  int down_button_{-1};
  int left_button2_{-1};
  int right_button2_{-1};
  int up_button2_{-1};
  int down_button2_{-1};
  int sdl_joystick_id_{};
  float run_value_{};
  float run_trigger1_min_{};
  float run_trigger1_max_{};
  float run_trigger2_min_{};
  float run_trigger2_max_{};
  float run_trigger1_value_{};
  float run_trigger2_value_{};
  float calibration_threshold_{};
  float calibration_break_threshold_{};
  float analog_calibration_vals_[kJoystickAnalogCalibrationDivisions]{};
  float calibrated_neutral_x_{};
  float calibrated_neutral_y_{};
  int32_t dialog_jaxis_x_{};
  int32_t dialog_jaxis_y_{};
  int32_t jaxis_raw_x_{};
  int32_t jaxis_raw_y_{};
  int32_t jaxis_x_{};
  int32_t jaxis_y_{};
  millisecs_t calibration_start_time_x_{};
  millisecs_t calibration_start_time_y_{};
  std::set<int> run_buttons_held_;
  std::string custom_device_name_;
  std::string raw_sdl_joystick_name_;
  std::map<int, std::string> button_names_;
  Object::Ref<Repeater> ui_repeater_;

  BA_DISALLOW_CLASS_COPIES(JoystickInput);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_JOYSTICK_INPUT_H_
