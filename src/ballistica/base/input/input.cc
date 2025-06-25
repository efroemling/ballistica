// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/input.h"

#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/device/touch_input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

Input::Input() = default;

void Input::PushCreateKeyboardInputDevices() {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this] { CreateKeyboardInputDevices_(); });
}

void Input::CreateKeyboardInputDevices_() {
  assert(g_base->InLogicThread());
  if (keyboard_input_ != nullptr || keyboard_input_2_ != nullptr) {
    g_core->logging->Log(
        LogName::kBaInput, LogLevel::kError,
        "CreateKeyboardInputDevices called with existing kbs.");
    return;
  }
  keyboard_input_ = Object::NewDeferred<KeyboardInput>(nullptr);
  AddInputDevice(keyboard_input_, false);
  keyboard_input_2_ = Object::NewDeferred<KeyboardInput>(keyboard_input_);
  AddInputDevice(keyboard_input_2_, false);
}

void Input::PushDestroyKeyboardInputDevices() {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this] { DestroyKeyboardInputDevices_(); });
}

void Input::DestroyKeyboardInputDevices_() {
  assert(g_base->InLogicThread());
  if (keyboard_input_ == nullptr || keyboard_input_2_ == nullptr) {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "DestroyKeyboardInputDevices called with null kb(s).");
    return;
  }
  RemoveInputDevice(keyboard_input_, false);
  keyboard_input_ = nullptr;
  RemoveInputDevice(keyboard_input_2_, false);
  keyboard_input_2_ = nullptr;
}

auto Input::GetInputDevice(int id) -> InputDevice* {
  if (id < 0 || id >= static_cast<int>(input_devices_.size())) {
    return nullptr;
  }
  return input_devices_[id].get();
}

auto Input::GetInputDevice(const std::string& name,
                           const std::string& unique_id) -> InputDevice* {
  assert(g_base->InLogicThread());
  for (auto&& i : input_devices_) {
    if (i.exists() && (i->GetDeviceName() == name)
        && i->GetPersistentIdentifier() == unique_id) {
      return i.get();
    }
  }
  return nullptr;
}

auto Input::GetFuzzyInputDeviceForEscapeKey() -> InputDevice* {
  assert(g_base->InLogicThread());

  auto* pdevice = GetFuzzyInputDevice_();
  if (pdevice) {
    return pdevice;
  }
  return keyboard_input_;
}

auto Input::GetFuzzyInputDeviceForMenuButton() -> InputDevice* {
  assert(g_base->InLogicThread());

  auto* pdevice = GetFuzzyInputDevice_();
  if (pdevice) {
    return pdevice;
  }
  return touch_input_;
}

auto Input::GetNewNumberedIdentifier_(const std::string& name) -> int {
  assert(g_base->InLogicThread());

  int num = 1;
  int full_id;
  while (true) {
    bool in_use = false;

    // Scan other devices with the same device-name and find the first
    // number suffix that's not taken.
    for (auto&& i : input_devices_) {
      if (i.exists()) {
        if ((i->DoGetDeviceName() == name) && i->number() == num) {
          in_use = true;
          break;
        }
      }
    }
    if (!in_use) {
      full_id = num;
      break;
    }
    num++;
  }
  return full_id;
}

void Input::AnnounceConnects_() {
  assert(g_base->InLogicThread());

  static bool first_print = true;

  // For the first announcement just say "X controllers detected" and don't
  // have a sound.
  if (first_print && g_core->AppTimeSeconds() < 3.0) {
    first_print = false;

    // If there's been several connected, just give a number.
    if (newly_connected_controllers_.size() > 1) {
      std::string s =
          g_base->assets->GetResourceString("controllersDetectedText");
      Utils::StringReplaceOne(
          &s, "${COUNT}", std::to_string(newly_connected_controllers_.size()));
      g_base->ScreenMessage(s);
    } else {
      g_base->ScreenMessage(
          g_base->assets->GetResourceString("controllerDetectedText"));
    }

  } else {
    // If there's been several connected, just give a number.
    if (newly_connected_controllers_.size() > 1) {
      std::string s =
          g_base->assets->GetResourceString("controllersConnectedText");
      Utils::StringReplaceOne(
          &s, "${COUNT}", std::to_string(newly_connected_controllers_.size()));
      g_base->ScreenMessage(s);
    } else {
      // If its just one, give its name.
      std::string s =
          g_base->assets->GetResourceString("controllerConnectedText");
      Utils::StringReplaceOne(&s, "${CONTROLLER}",
                              newly_connected_controllers_.front());
      g_base->ScreenMessage(s);
    }
    if (g_base->assets->sys_assets_loaded()) {
      g_base->audio->SafePlaySysSound(SysSoundID::kGunCock);
    }
  }
  newly_connected_controllers_.clear();
}

void Input::AnnounceDisconnects_() {
  // If there's been several connected, just give a number.
  if (newly_disconnected_controllers_.size() > 1) {
    std::string s =
        g_base->assets->GetResourceString("controllersDisconnectedText");
    Utils::StringReplaceOne(
        &s, "${COUNT}", std::to_string(newly_disconnected_controllers_.size()));
    g_base->ScreenMessage(s);
  } else {
    // If its just one, name it.
    std::string s =
        g_base->assets->GetResourceString("controllerDisconnectedText");
    Utils::StringReplaceOne(&s, "${CONTROLLER}",
                            newly_disconnected_controllers_.front());
    g_base->ScreenMessage(s);
  }
  if (g_base->assets->sys_assets_loaded()) {
    g_base->audio->SafePlaySysSound(SysSoundID::kCorkPop);
  }

  newly_disconnected_controllers_.clear();
}

void Input::ShowStandardInputDeviceConnectedMessage_(InputDevice* j) {
  assert(g_base->InLogicThread());

  // On Android we never show messages for initial input-devices; we often
  // get large numbers of strange virtual devices that aren't actually
  // controllers so this is more confusing than helpful.
  if (g_buildconfig.platform_android() && g_core->AppTimeSeconds() < 3.0) {
    return;
  }

  std::string suffix;
  suffix += j->GetPersistentIdentifier();
  if (!suffix.empty()) {
    suffix = " " + suffix;
  }
  newly_connected_controllers_.push_back(j->GetDeviceName() + suffix);

  // Set a timer to go off and announce controller additions. This allows
  // several connecting at (almost) the same time to be announced as a
  // single event.
  if (connect_print_timer_id_ != 0) {
    g_base->logic->DeleteAppTimer(connect_print_timer_id_);
  }
  connect_print_timer_id_ = g_base->logic->NewAppTimer(
      500 * 1000, false,
      NewLambdaRunnable([this] { AnnounceConnects_(); }).get());
}

void Input::ShowStandardInputDeviceDisconnectedMessage_(InputDevice* j) {
  assert(g_base->InLogicThread());

  newly_disconnected_controllers_.push_back(j->GetDeviceName() + " "
                                            + j->GetPersistentIdentifier());

  // Set a timer to go off and announce the accumulated additions.
  if (disconnect_print_timer_id_ != 0) {
    g_base->logic->DeleteAppTimer(disconnect_print_timer_id_);
  }
  disconnect_print_timer_id_ = g_base->logic->NewAppTimer(
      250 * 1000, false,
      NewLambdaRunnable([this] { AnnounceDisconnects_(); }).get());
}

void Input::PushAddInputDeviceCall(InputDevice* input_device,
                                   bool standard_message) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall([this, input_device, standard_message] {
    AddInputDevice(input_device, standard_message);
  });
}

void Input::RebuildInputDeviceDelegates() {
  assert(g_base->InLogicThread());
  for (auto&& device_ref : input_devices_) {
    if (auto* device = device_ref.get()) {
      auto delegate = Object::CompleteDeferred(
          g_base->app_mode()->CreateInputDeviceDelegate(device));
      device->set_delegate(delegate);
      delegate->set_input_device(device);
    }
  }
}

void Input::AddInputDevice(InputDevice* device, bool standard_message) {
  assert(g_base->InLogicThread());

  device->set_number(GetNewNumberedIdentifier_(device->DoGetDeviceName()));

  g_core->logging->Log(LogName::kBaInput, LogLevel::kDebug, [device] {
    return "InputDevice added: " + device->GetDeviceNameUnique() + ".";
  });

  // Let the current app-mode assign it a delegate.
  auto delegate = Object::CompleteDeferred(
      g_base->app_mode()->CreateInputDeviceDelegate(device));
  device->set_delegate(delegate);
  delegate->set_input_device(device);

  // Find the first unused input-device id and use that (might as well keep
  // our list small if we can).
  int index = 0;
  bool found_slot = false;
  for (auto& input_device : input_devices_) {
    if (!input_device.exists()) {
      input_device = Object::CompleteDeferred(device);
      found_slot = true;
      device->set_index(index);
      break;
    }
    index++;
  }
  if (!found_slot) {
    input_devices_.push_back(Object::CompleteDeferred(device));
    device->set_index(static_cast<int>(input_devices_.size() - 1));
  }

  // Let the device know it's been added (for custom announcements, etc.)
  device->OnAdded();

  // Immediately apply app-config if initial app-config has already been
  // applied; otherwise it'll happen as part of that.
  if (g_base->logic->applied_app_config()) {
    // Update controls for just this guy.
    device->ApplyAppConfig();

    // Need to do this after updating controls, as some control settings can
    // affect things we count (such as whether start activates default
    // button).
    UpdateInputDeviceCounts_();
  }

  if (standard_message && !device->ShouldBeHiddenFromUser()) {
    ShowStandardInputDeviceConnectedMessage_(device);
  }
}

void Input::PushRemoveInputDeviceCall(InputDevice* input_device,
                                      bool standard_message) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall([this, input_device, standard_message] {
    RemoveInputDevice(input_device, standard_message);
  });
}

void Input::RemoveInputDevice(InputDevice* device, bool standard_message) {
  assert(g_base->InLogicThread());

  g_base->ui->OnInputDeviceRemoved(device);

  g_core->logging->Log(LogName::kBaInput, LogLevel::kDebug, [device] {
    return "InputDevice removed: " + device->GetDeviceNameUnique() + ".";
  });

  if (standard_message && !device->ShouldBeHiddenFromUser()) {
    ShowStandardInputDeviceDisconnectedMessage_(device);
  }

  // Look for it in our list, and if we find it, simply clear the ref (we
  // need to keep the ref around so our list indices don't change).
  for (auto& input_device : input_devices_) {
    if (input_device.exists() && (input_device.get() == device)) {
      // Pull it off the list before killing it (in case it tries to trigger
      // another kill itself).
      auto device = Object::Ref<InputDevice>(input_device);

      // Ok we cleared its slot in our vector; now we just have the local
      // variable 'device' keeping it alive.
      input_device.Clear();

      // Tell it to detach from anything it is controlling.
      device->DetachFromPlayer();

      // This should kill the device.
      device.Clear();
      UpdateInputDeviceCounts_();
      return;
    }
  }
  throw Exception("Input::RemoveInputDevice: invalid device provided");
}

void Input::UpdateInputDeviceCounts_() {
  assert(g_base->InLogicThread());

  auto current_time_millisecs =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  have_button_using_inputs_ = false;
  have_start_activated_default_button_inputs_ = false;
  have_non_touch_inputs_ = false;
  int total = 0;
  int controller_count = 0;
  for (auto& input_device : input_devices_) {
    // Ok, we now limit non-keyboard non-touchscreen devices to ones that
    // have been active recently.. (we're starting to get lots of virtual
    // devices and other cruft on android; don't wanna show controller UIs
    // just due to those)
    if (input_device.exists()
        && ((*input_device).IsTouchScreen() || (*input_device).IsKeyboard()
            || ((*input_device).last_active_time_millisecs() != 0
                && current_time_millisecs
                           - (*input_device).last_active_time_millisecs()
                       < 60000))) {
      total++;
      if (!(*input_device).IsTouchScreen()) {
        have_non_touch_inputs_ = true;
      }
      if ((*input_device).start_button_activates_default_widget()) {
        have_start_activated_default_button_inputs_ = true;
      }
      if ((*input_device).IsController()) {
        have_button_using_inputs_ = true;
        if (!(*input_device).IsUIOnly() && !(*input_device).IsTestInput()) {
          controller_count++;
        }
      }
    }
  }
  if (controller_count > max_controller_count_so_far_) {
    max_controller_count_so_far_ = controller_count;
    if (max_controller_count_so_far_ == 1) {
      g_base->python->objs().PushCall(
          BasePython::ObjID::kAwardInControlAchievementCall);
    } else if (max_controller_count_so_far_ == 2) {
      g_base->python->objs().PushCall(
          BasePython::ObjID::kAwardDualWieldingAchievementCall);
    }
  }
}

auto Input::HaveManyLocalActiveInputDevices() -> bool {
  return GetLocalActiveInputDeviceCount() > 1;
}

auto Input::GetLocalActiveInputDeviceCount() -> int {
  assert(g_base->InLogicThread());

  // This can get called alot so lets cache the value.
  auto current_time_millisecs =
      static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
  if (current_time_millisecs
      != last_get_local_active_input_device_count_check_time_) {
    last_get_local_active_input_device_count_check_time_ =
        current_time_millisecs;

    int count = 0;
    for (auto& input_device : input_devices_) {
      // Tally up local non-keyboard, non-touchscreen devices that have been
      // used in the last minute.
      if (input_device.exists() && !input_device->IsKeyboard()
          && !input_device->IsTouchScreen() && !input_device->IsUIOnly()
          && input_device->IsLocal()
          && (input_device->last_active_time_millisecs() != 0
              && current_time_millisecs
                         - input_device->last_active_time_millisecs()
                     < 60000)) {
        count++;
      }
    }
    local_active_input_device_count_ = count;
  }
  return local_active_input_device_count_;
}

auto Input::GetFuzzyInputDevice_() -> InputDevice* {
  assert(g_base->InLogicThread());

  InputDevice* pdevice{};
  int pdevicecount{};

  // Never return fuzzy devices if it seems that there's multiple active
  // devices.
  if (HaveManyLocalActiveInputDevices()) {
    return nullptr;
  }

  // Tally up local devices with a player attached. If there is exactly one,
  // that's our guy.
  for (auto& input_device : input_devices_) {
    if (input_device.exists() && input_device->IsLocal()
        && input_device->AttachedToPlayer()) {
      pdevice = input_device.get();
      pdevicecount += 1;
    }
  }
  return pdevicecount == 1 ? pdevice : nullptr;
}

auto Input::HaveControllerWithPlayer() -> bool {
  assert(g_base->InLogicThread());
  for (auto& input_device : input_devices_) {
    if (input_device.exists() && (*input_device).IsController()
        && (*input_device).AttachedToPlayer()) {
      return true;
    }
  }
  return false;
}

auto Input::HaveRemoteAppController() -> bool {
  assert(g_base->InLogicThread());
  for (auto& input_device : input_devices_) {
    if (input_device.exists() && (*input_device).IsRemoteApp()) {
      return true;
    }
  }
  return false;
}

auto Input::GetInputDevicesWithName(const std::string& name)
    -> std::vector<InputDevice*> {
  std::vector<InputDevice*> vals;
  if (!g_core->HeadlessMode()) {
    for (auto& input_device : input_devices_) {
      if (input_device.exists()) {
        auto* js = dynamic_cast<JoystickInput*>(input_device.get());
        if (js && js->GetDeviceName() == name) {
          vals.push_back(js);
        }
      }
    }
  }
  return vals;
}

auto Input::GetConfigurableGameControllers() -> std::vector<InputDevice*> {
  assert(g_base->InLogicThread());
  std::vector<InputDevice*> vals;
  if (!g_core->HeadlessMode()) {
    for (auto& input_device : input_devices_) {
      if (input_device.exists()) {
        auto* js = dynamic_cast<JoystickInput*>(input_device.get());
        if (js && js->GetAllowsConfiguring() && !js->ShouldBeHiddenFromUser()) {
          vals.push_back(js);
        }
      }
    }
  }
  return vals;
}

auto Input::ShouldCompletelyIgnoreInputDevice(InputDevice* input_device)
    -> bool {
  return false;
}

void Input::OnAppStart() {
  assert(g_base->InLogicThread());
  if (g_core->platform->HasTouchScreen()) {
    assert(touch_input_ == nullptr);
    touch_input_ = Object::NewDeferred<TouchInput>();
    PushAddInputDeviceCall(touch_input_, false);
  }
}

void Input::OnAppSuspend() { assert(g_base->InLogicThread()); }

void Input::OnAppUnsuspend() { assert(g_base->InLogicThread()); }

void Input::OnAppShutdown() { assert(g_base->InLogicThread()); }

void Input::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }

// Tells all inputs to update their controls based on the app config.
void Input::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  // It's technically possible that updating these controls will add or
  // remove devices, thus changing the input_devices_ list, so lets work
  // with a copy of it.
  std::vector<Object::Ref<InputDevice> > input_devices = input_devices_;
  for (auto& input_device : input_devices) {
    if (input_device.exists()) {
      input_device->ApplyAppConfig();
    }
  }

  // Some config settings can affect this.
  UpdateInputDeviceCounts_();
}

void Input::OnScreenSizeChange() { assert(g_base->InLogicThread()); }

void Input::StepDisplayTime() {
  assert(g_base->InLogicThread());

  millisecs_t real_time = g_core->AppTimeMillisecs();

  // If input has been locked an excessively long amount of time, unlock it.
  if (input_lock_count_temp_) {
    if (real_time - last_input_temp_lock_time_ > 10000) {
      g_core->logging->Log(
          LogName::kBaInput, LogLevel::kError,
          "Input has been temp-locked for 10 seconds; unlocking.");
      input_lock_count_temp_ = 0;
      PrintLockLabels_();
      input_lock_temp_labels_.clear();
      input_unlock_temp_labels_.clear();
    }
  }

  // We now need to update our input-device numbers dynamically since
  // they're based on recently-active devices. We do this much more often
  // for the first few seconds to keep controller-usage from being as
  // annoying.

  // Update: don't remember why that was annoying; trying a single value for
  // now.
  millisecs_t incr = 249;
  if (real_time - last_input_device_count_update_time_ > incr) {
    UpdateInputDeviceCounts_();
    last_input_device_count_update_time_ = real_time;

    // Keep our idle-time up to date.
    if (input_active_) {
      input_idle_time_ = 0;
    } else {
      input_idle_time_ += incr;
    }
    input_active_ = false;
  }

  for (auto& input_device : input_devices_) {
    if (input_device.exists()) {
      (*input_device).Update();
    }
  }
}

void Input::Reset() {
  assert(g_base->InLogicThread());

  // Detach all inputs from players.
  for (auto& input_device : input_devices_) {
    if (input_device.exists()) {
      input_device->DetachFromPlayer();
    }
  }
}

void Input::ResetHoldStates() {
  assert(g_base->InLogicThread());
  ResetKeyboardHeldKeys();
  ResetJoyStickHeldButtons();
}

void Input::LockAllInput(bool permanent, const std::string& label) {
  assert(g_base->InLogicThread());
  if (permanent) {
    input_lock_count_permanent_++;
    input_lock_permanent_labels_.push_back(label);
  } else {
    input_lock_count_temp_++;
    if (input_lock_count_temp_ == 1) {
      last_input_temp_lock_time_ = g_core->AppTimeMillisecs();
    }
    input_lock_temp_labels_.push_back(label);

    recent_input_locks_unlocks_.push_back(
        "temp lock: " + label + " time "
        + std::to_string(g_core->AppTimeMillisecs()));
    while (recent_input_locks_unlocks_.size() > 10) {
      recent_input_locks_unlocks_.pop_front();
    }
  }
}

void Input::UnlockAllInput(bool permanent, const std::string& label) {
  assert(g_base->InLogicThread());

  recent_input_locks_unlocks_.push_back(
      permanent ? "permanent unlock: "
                : "temp unlock: " + label + " time "
                      + std::to_string(g_core->AppTimeMillisecs()));
  while (recent_input_locks_unlocks_.size() > 10) {
    recent_input_locks_unlocks_.pop_front();
  }

  if (permanent) {
    input_lock_count_permanent_--;
    input_unlock_permanent_labels_.push_back(label);
    if (input_lock_count_permanent_ < 0) {
      BA_LOG_PYTHON_TRACE_ONCE("lock-count-permanent < 0");
      PrintLockLabels_();
      input_lock_count_permanent_ = 0;
    }

    // When lock counts get back down to zero, clear our labels since all is
    // well.
    if (input_lock_count_permanent_ == 0) {
      input_lock_permanent_labels_.clear();
      input_unlock_permanent_labels_.clear();
    }
  } else {
    input_lock_count_temp_--;
    input_unlock_temp_labels_.push_back(label);
    if (input_lock_count_temp_ < 0) {
      g_core->logging->Log(LogName::kBaInput, LogLevel::kWarning,
                           "temp input unlock at time "
                               + std::to_string(g_core->AppTimeMillisecs())
                               + " with no active lock: '" + label + "'");
      // This is to be expected since we can reset this to 0.
      input_lock_count_temp_ = 0;
    }

    // When lock counts get back down to zero, clear our labels since all is
    // well.
    if (input_lock_count_temp_ == 0) {
      input_lock_temp_labels_.clear();
      input_unlock_temp_labels_.clear();
    }
  }
}

void Input::PrintLockLabels_() {
  std::string s = "INPUT LOCK REPORT (time="
                  + std::to_string(g_core->AppTimeMillisecs()) + "):";
  int num;

  s += "\n " + std::to_string(input_lock_temp_labels_.size()) + " TEMP LOCKS:";
  num = 1;
  for (auto& input_lock_temp_label : input_lock_temp_labels_) {
    s += "\n   " + std::to_string(num++) + ": " + input_lock_temp_label;
  }

  s += "\n " + std::to_string(input_unlock_temp_labels_.size())
       + " TEMP UNLOCKS:";
  num = 1;
  for (auto& input_unlock_temp_label : input_unlock_temp_labels_) {
    s += "\n   " + std::to_string(num++) + ": " + input_unlock_temp_label;
  }

  s += "\n " + std::to_string(input_lock_permanent_labels_.size())
       + " PERMANENT LOCKS:";
  num = 1;
  for (auto& input_lock_permanent_label : input_lock_permanent_labels_) {
    s += "\n   " + std::to_string(num++) + ": " + input_lock_permanent_label;
  }

  s += "\n " + std::to_string(input_unlock_permanent_labels_.size())
       + " PERMANENT UNLOCKS:";
  num = 1;
  for (auto& input_unlock_permanent_label : input_unlock_permanent_labels_) {
    s += "\n   " + std::to_string(num++) + ": " + input_unlock_permanent_label;
  }
  s += "\n " + std::to_string(recent_input_locks_unlocks_.size())
       + " MOST RECENT LOCKS:";
  num = 1;
  for (auto& recent_input_locks_unlock : recent_input_locks_unlocks_) {
    s += "\n   " + std::to_string(num++) + ": " + recent_input_locks_unlock;
  }

  g_core->logging->Log(LogName::kBaInput, LogLevel::kError, s);
}

void Input::PushTextInputEvent(const std::string& text) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall([this, text] {
    // Mark as active even if input is locked.
    MarkInputActive();

    if (IsInputLocked()) {
      return;
    }

    // If the app doesn't want direct text input right now, ignore.
    if (!g_base->app_adapter->HasDirectKeyboardInput()) {
      return;
    }

    // Also ignore if there are any mod keys being held. We process some of
    // our own keyboard shortcuts and don't want text input to come through
    // at the same time.
    if (keys_held_.contains(SDLK_LCTRL) || keys_held_.contains(SDLK_RCTRL)
        || keys_held_.contains(SDLK_LALT) || keys_held_.contains(SDLK_RALT)
        || keys_held_.contains(SDLK_LGUI) || keys_held_.contains(SDLK_RGUI)) {
      return;
    }

    // Ignore back-tick and tilde because we use that key to toggle the
    // console. FIXME: Perhaps should allow typing it if some
    // control-character is held?
    if (text == "`" || text == "~") {
      return;
    }

    // We try to handle char filtering here (to keep it consistent across
    // platforms) but make a stink if they sent us something that we can't
    // at least translate to unicode.
    if (!Utils::IsValidUTF8(text)) {
      g_core->logging->Log(LogName::kBaInput, LogLevel::kWarning,
                           "PushTextInputEvent passed invalid utf-8 text.");
      return;
    }

    // Now scan through unicode vals and ignore stuff like tabs and newlines
    // and backspaces. We want to limit this mechanism to direct simple
    // lines of text. Anything needing something fancier should go through a
    // proper OS-managed text input dialog or whatnot.
    auto univals = Utils::UnicodeFromUTF8(text, "80ff83");
    for (auto&& unival : univals) {
      if (unival < 32) {
        return;
      }
    }

    if (g_base && g_base->ui->dev_console() != nullptr
        && g_base->ui->dev_console()->HandleTextEditing(text)) {
      return;
    }

    g_base->ui->SendWidgetMessage(WidgetMessage(
        WidgetMessage::Type::kTextInput, nullptr, 0, 0, 0, 0, text.c_str()));
  });
}

void Input::PushJoystickEvent(const SDL_Event& event,
                              InputDevice* input_device) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall([this, event, input_device] {
    HandleJoystickEvent_(event, input_device);
  });
}

void Input::HandleJoystickEvent_(const SDL_Event& event,
                                 InputDevice* input_device) {
  assert(g_base->InLogicThread());
  assert(input_device);

  if (ShouldCompletelyIgnoreInputDevice(input_device)) {
    return;
  }

  // Mark as active even if input is locked.
  input_device->UpdateLastActiveTime();

  if (IsInputLocked(input_device)) {
    return;
  }

  // If someone is capturing these events, give them a crack at it.
  if (joystick_input_capture_) {
    if (joystick_input_capture_(event, input_device)) {
      return;
    }
  }

  input_device->HandleSDLEvent(&event);
}

void Input::PushKeyPressEventSimple(int key) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, key] { HandleKeyPressSimple_(key); });
}

void Input::PushKeyReleaseEventSimple(int key) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, key] { HandleKeyReleaseSimple_(key); });
}

void Input::PushKeyPressEvent(const SDL_Keysym& keysym) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, keysym] { HandleKeyPress_(keysym); });
}

void Input::PushKeyReleaseEvent(const SDL_Keysym& keysym) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, keysym] { HandleKeyRelease_(keysym); });
}

void Input::CaptureKeyboardInput(HandleKeyPressCall* press_call,
                                 HandleKeyReleaseCall* release_call) {
  assert(g_base->InLogicThread());
  if (keyboard_input_capture_press_ || keyboard_input_capture_release_) {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "Setting key capture redundantly.");
  }
  keyboard_input_capture_press_ = press_call;
  keyboard_input_capture_release_ = release_call;
}

void Input::ReleaseKeyboardInput() {
  assert(g_base->InLogicThread());
  keyboard_input_capture_press_ = nullptr;
  keyboard_input_capture_release_ = nullptr;
}

void Input::CaptureJoystickInput(HandleJoystickEventCall* call) {
  assert(g_base->InLogicThread());
  if (joystick_input_capture_) {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "Setting joystick capture redundantly.");
  }
  joystick_input_capture_ = call;
}

void Input::ReleaseJoystickInput() {
  assert(g_base->InLogicThread());
  joystick_input_capture_ = nullptr;
}

void Input::AddFakeKeyMods_(SDL_Keysym* sym) {
  // In cases where we are only passed simple keycodes, we fill in modifiers
  // ourself by looking at currently held key states. This is less than
  // ideal because modifier key states can fall out of sync in some cases
  // but is generally 'good enough' for our minimal keyboard needs.
  if (keys_held_.contains(SDLK_LCTRL) || keys_held_.contains(SDLK_RCTRL)) {
    sym->mod |= KMOD_CTRL;
  }
  if (keys_held_.contains(SDLK_LSHIFT) || keys_held_.contains(SDLK_RSHIFT)) {
    sym->mod |= KMOD_SHIFT;
  }
  if (keys_held_.contains(SDLK_LALT) || keys_held_.contains(SDLK_RALT)) {
    sym->mod |= KMOD_ALT;
  }
  if (keys_held_.contains(SDLK_LGUI) || keys_held_.contains(SDLK_RGUI)) {
    sym->mod |= KMOD_GUI;
  }
}

void Input::HandleKeyPressSimple_(int keycode) {
  SDL_Keysym keysym{};
  keysym.sym = keycode;
  AddFakeKeyMods_(&keysym);
  HandleKeyPress_(keysym);
}

void Input::HandleKeyReleaseSimple_(int keycode) {
  // See notes above.
  SDL_Keysym keysym{};
  keysym.sym = keycode;
  AddFakeKeyMods_(&keysym);
  HandleKeyRelease_(keysym);
}

void Input::HandleKeyPress_(const SDL_Keysym& keysym) {
  assert(g_base->InLogicThread());

  // Mark as active even if input is locked.
  MarkInputActive();

  if (IsInputLocked()) {
    return;
  }

  // Nowadays we don't want the OS to deliver repeat events to us, so filter
  // out any that we get and make noise that they should stop. We explicitly
  // handle repeats for UI purposes at the InputDevice or Widget level now.
  if (keys_held_.find(keysym.sym) != keys_held_.end()) {
    // Look out for several repeats coming in within the span of a few
    // seconds and complain if it happens. This should allow for the random
    // fluke repeat key press event due to funky OS circumstances.
    static int count{};
    static seconds_t last_count_reset_time{};
    auto now = g_core->AppTimeSeconds();
    if (now - last_count_reset_time > 2.0) {
      count = 0;
      last_count_reset_time = now;
    } else {
      count++;
      if (count > 10) {
        BA_LOG_ONCE(
            LogName::kBaInput, LogLevel::kWarning,
            "Input::HandleKeyPress_ seems to be getting passed repeat key"
            " press events. Only initial press events should be passed.");
      }
    }
    return;
  }

  keys_held_.insert(keysym.sym);

  // If someone is capturing these events, give them a crack at it.
  if (keyboard_input_capture_press_) {
    if (keyboard_input_capture_press_(keysym)) {
      return;
    }
  }

  // Regardless of what else we do, keep track of mod key states. (for
  // things like manual camera moves. For individual key presses ideally we
  // should use the modifiers bundled with the key presses)
  UpdateModKeyStates_(&keysym, true);

  // Explicitly handle fullscreen-toggles in some cases.
  if (g_base->app_adapter->FullscreenControlAvailable()) {
    bool do_toggle{};
    // On our SDL builds we support both F11 and Alt+Enter for toggling
    // fullscreen.
    if (g_buildconfig.sdl_build()) {
      if ((keysym.sym == SDLK_F11
           || (keysym.sym == SDLK_RETURN && ((keysym.mod & KMOD_ALT))))) {
        do_toggle = true;
      }
    }
    if (do_toggle) {
      g_base->python->objs()
          .Get(BasePython::ObjID::kToggleFullscreenCall)
          .Call();
      return;
    }
  }

  // Ctrl-V or Cmd-V sends paste commands to the console or any interested
  // text fields.
  if (keysym.sym == SDLK_v
      && ((keysym.mod & KMOD_CTRL) || (keysym.mod & KMOD_GUI))) {
    if (auto* console = g_base->ui->dev_console()) {
      if (console->PasteFromClipboard()) {
        return;
      }
    }
    g_base->ui->SendWidgetMessage(WidgetMessage(WidgetMessage::Type::kPaste));
    return;
  }

  // Dev Console.
  if (auto* console = g_base->ui->dev_console()) {
    if (keysym.sym == SDLK_BACKQUOTE || keysym.sym == SDLK_F2) {
      // Reset input so characters don't continue walking and stuff.
      g_base->input->ResetHoldStates();
      auto backwards = (keysym.mod & KMOD_SHIFT) != 0;
      console->CycleState(backwards);
      return;
    }
    if (console->HandleKeyPress(&keysym)) {
      return;
    }
  }

  bool handled = false;

  switch (keysym.sym) {
      // Menu button on android/etc. pops up the menu.
    case SDLK_MENU: {
      if (!g_base->ui->IsMainUIVisible()) {
        g_base->ui->RequestMainUI(GetFuzzyInputDeviceForMenuButton());
      }
      handled = true;
      break;
    }

    case SDLK_EQUALS:
    case SDLK_PLUS:
      if (keysym.mod & KMOD_CTRL) {
        g_base->app_mode()->ChangeGameSpeed(1);
        handled = true;
      }
      break;

    case SDLK_MINUS:
      if (keysym.mod & KMOD_CTRL) {
        g_base->app_mode()->ChangeGameSpeed(-1);
        handled = true;
      }
      break;

    case SDLK_F5: {
      if (g_base->ui->IsPartyIconVisible()) {
        g_base->ui->ActivatePartyIcon();
      }
      handled = true;
      break;
    }

    case SDLK_F7:
      assert(g_base->logic->event_loop());
      g_base->logic->event_loop()->PushCall(
          [] { g_base->graphics->ToggleManualCamera(); });
      handled = true;
      break;

    case SDLK_F8:
      assert(g_base->logic->event_loop());
      g_base->logic->event_loop()->PushCall(
          [] { g_base->graphics->ToggleNetworkDebugDisplay(); });
      handled = true;
      break;

    case SDLK_F9:
      g_base->python->objs().PushCall(
          BasePython::ObjID::kLanguageTestToggleCall);
      handled = true;
      break;

    case SDLK_F10:
      assert(g_base->logic->event_loop());
      g_base->logic->event_loop()->PushCall(
          [] { g_base->graphics->ToggleDebugDraw(); });
      handled = true;
      break;

    case SDLK_ESCAPE:
      if (!g_base->ui->IsMainUIVisible()) {
        // There's no main menu up. Ask for one.
        g_base->ui->RequestMainUI(GetFuzzyInputDeviceForEscapeKey());
      } else {
        // Ok there *is* a main ui up. Send it a cancel message.
        g_base->ui->SendWidgetMessage(
            WidgetMessage(WidgetMessage::Type::kCancel));
      }
      handled = true;
      break;

    default:
      break;
  }

  // If we haven't handled this, pass it along as potential player/widget input.
  if (!handled) {
    if (keyboard_input_) {
      keyboard_input_->HandleKey(&keysym, true);
    }
  }
}

void Input::HandleKeyRelease_(const SDL_Keysym& keysym) {
  assert(g_base->InLogicThread());

  // Note: we want to let releases through even if input is locked.

  MarkInputActive();

  // In some cases we may receive duplicate key-release events (if a
  // keyboard reset was run, it deals out key releases, but then the
  // keyboard driver issues them as well).
  if (keys_held_.find(keysym.sym) == keys_held_.end()) {
    return;
  }

  // If someone is capturing these events, give them a crack at it.
  if (keyboard_input_capture_release_) {
    (keyboard_input_capture_release_(keysym));
  }

  // Keep track of mod key states for things like manual camera moves. For
  // individual key presses ideally we should instead use modifiers bundled
  // with the key press events.
  UpdateModKeyStates_(&keysym, false);

  keys_held_.erase(keysym.sym);

  if (g_base->ui->dev_console() != nullptr) {
    g_base->ui->dev_console()->HandleKeyRelease(&keysym);
  }

  if (keyboard_input_) {
    keyboard_input_->HandleKey(&keysym, false);
  }
}

void Input::UpdateModKeyStates_(const SDL_Keysym* keysym, bool press) {
  switch (keysym->sym) {
    case SDLK_LCTRL:
    case SDLK_RCTRL: {
      if (Camera* c = g_base->graphics->camera()) {
        c->set_ctrl_down(press);
      }
      break;
    }
    case SDLK_LALT:
    case SDLK_RALT: {
      if (Camera* c = g_base->graphics->camera()) {
        c->set_alt_down(press);
      }
      break;
    }
    case SDLK_LGUI:
    case SDLK_RGUI: {
      if (Camera* c = g_base->graphics->camera()) {
        c->set_cmd_down(press);
      }
      break;
    }
    default:
      break;
  }
}

void Input::PushMouseScrollEvent(const Vector2f& amount) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, amount] { HandleMouseScroll_(amount); });
}

void Input::HandleMouseScroll_(const Vector2f& amount) {
  assert(g_base->InLogicThread());

  // Mark as active even if input is locked.
  MarkInputActive();

  if (IsInputLocked()) {
    return;
  }

  if (std::abs(amount.y) > 0.0001f) {
    g_base->ui->SendWidgetMessage(
        WidgetMessage(WidgetMessage::Type::kMouseWheel, nullptr, cursor_pos_x_,
                      cursor_pos_y_, amount.y));
  }
  if (std::abs(amount.x) > 0.0001f) {
    g_base->ui->SendWidgetMessage(
        WidgetMessage(WidgetMessage::Type::kMouseWheelH, nullptr, cursor_pos_x_,
                      cursor_pos_y_, amount.x));
  }
  mouse_move_count_++;

  Camera* camera = g_base->graphics->camera();
  if (camera) {
    if (camera->manual()) {
      camera->ManualHandleMouseWheel(0.005f * amount.y);
    }
  }
}

void Input::PushSmoothMouseScrollEvent(const Vector2f& velocity,
                                       bool momentum) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall([this, velocity, momentum] {
    HandleSmoothMouseScroll_(velocity, momentum);
  });
}

void Input::HandleSmoothMouseScroll_(const Vector2f& velocity, bool momentum) {
  assert(g_base->InLogicThread());

  // Mark as active even if input is locked.
  MarkInputActive();

  if (IsInputLocked()) {
    return;
  }

  bool handled = false;
  handled = g_base->ui->SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseWheelVelocity, nullptr,
                    cursor_pos_x_, cursor_pos_y_, velocity.y, momentum));
  g_base->ui->SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseWheelVelocityH, nullptr,
                    cursor_pos_x_, cursor_pos_y_, velocity.x, momentum));

  last_mouse_move_time_ = g_core->AppTimeSeconds();
  mouse_move_count_++;

  Camera* camera = g_base->graphics->camera();
  if (!handled && camera) {
    if (camera->manual()) {
      camera->ManualHandleMouseWheel(-0.25f * velocity.y);
    }
  }
}

void Input::PushMouseMotionEvent(const Vector2f& position) {
  auto* loop = g_base->logic->event_loop();
  assert(loop);

  // Don't overload it with events if it's stuck.
  if (!loop->CheckPushSafety()) {
    return;
  }

  g_base->logic->event_loop()->PushCall(
      [this, position] { HandleMouseMotion_(position); });
}

void Input::HandleMouseMotion_(const Vector2f& position) {
  assert(g_base->InLogicThread());

  // Mark as active even if input is locked.
  MarkInputActive();

  // Just noticed that blocking these events leads to the cursor freezing up
  // on fades and whatnot (when we're drawing the cursor at least). So gonna
  // just let these go through for now. If that ever causes problems we can
  // reconsider.
  //
  // if (IsInputLocked()) {
  //   return;
  // }

  float old_cursor_pos_x = cursor_pos_x_;
  float old_cursor_pos_y = cursor_pos_y_;

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_base->graphics->PixelToVirtualX(
      position.x * g_base->graphics->screen_pixel_width());
  cursor_pos_y_ = g_base->graphics->PixelToVirtualY(
      position.y * g_base->graphics->screen_pixel_height());

  last_mouse_move_time_ = g_core->AppTimeSeconds();
  mouse_move_count_++;

  // If we have a touch-input in editing mode, pass along events to it. (it
  // usually handles its own events but here we want it to play nice with
  // stuff under it by blocking touches, etc)
  if (touch_input_ && touch_input_->editing()) {
    touch_input_->HandleTouchMoved(reinterpret_cast<void*>(1), cursor_pos_x_,
                                   cursor_pos_y_);
  }

  // Let any UI stuff handle it.
  g_base->ui->HandleMouseMotion(cursor_pos_x_, cursor_pos_y_);

  // Manual camera motion.
  Camera* camera = g_base->graphics->camera();
  if (camera && camera->manual()) {
    float move_h = (cursor_pos_x_ - old_cursor_pos_x)
                   / g_base->graphics->screen_virtual_width();
    float move_v = (cursor_pos_y_ - old_cursor_pos_y)
                   / g_base->graphics->screen_virtual_width();
    camera->ManualHandleMouseMove(move_h, move_v);
  }
}

void Input::PushMouseDownEvent(int button, const Vector2f& position) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, button, position] { HandleMouseDown_(button, position); });
}

void Input::HandleMouseDown_(int button, const Vector2f& position) {
  assert(g_base->InLogicThread());

  // Mark as active even if input is locked.
  MarkInputActive();

  if (IsInputLocked()) {
    return;
  }

  last_mouse_move_time_ = g_core->AppTimeSeconds();
  mouse_move_count_++;

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_base->graphics->PixelToVirtualX(
      position.x * g_base->graphics->screen_pixel_width());
  cursor_pos_y_ = g_base->graphics->PixelToVirtualY(
      position.y * g_base->graphics->screen_pixel_height());

  millisecs_t click_time = g_core->AppTimeMillisecs();
  bool double_click = (click_time - last_click_time_ <= double_click_time_);
  last_click_time_ = click_time;

  bool handled{};

  // If we have a touch-input in editing mode, pass along events to it.
  // (it usually handles its own events but here we want it to play nice
  // with stuff under it by blocking touches, etc)
  if (touch_input_ && touch_input_->editing()) {
    handled = touch_input_->HandleTouchDown(reinterpret_cast<void*>(1),
                                            cursor_pos_x_, cursor_pos_y_);
  }

  if (!handled) {
    handled = g_base->ui->HandleMouseDown(button, cursor_pos_x_, cursor_pos_y_,
                                          double_click);
  }

  // Manual camera input.
  Camera* camera = g_base->graphics->camera();
  if (!handled && camera) {
    switch (button) {
      case SDL_BUTTON_LEFT:
        camera->set_mouse_left_down(true);
        break;
      case SDL_BUTTON_RIGHT:
        camera->set_mouse_right_down(true);
        break;
      case SDL_BUTTON_MIDDLE:
        camera->set_mouse_middle_down(true);
        break;
      default:
        break;
    }
    camera->UpdateManualMode();
  }
}

void Input::PushMouseUpEvent(int button, const Vector2f& position) {
  assert(g_base->logic->event_loop());
  g_base->logic->event_loop()->PushCall(
      [this, button, position] { HandleMouseUp_(button, position); });
}

static void ApplyMouseUpCancelToCamera(int button) {
  if (Camera* camera = g_base->graphics->camera()) {
    switch (button) {
      case SDL_BUTTON_LEFT:
        camera->set_mouse_left_down(false);
        break;
      case SDL_BUTTON_RIGHT:
        camera->set_mouse_right_down(false);
        break;
      case SDL_BUTTON_MIDDLE:
        camera->set_mouse_middle_down(false);
        break;
      default:
        break;
    }
    camera->UpdateManualMode();
  }
}

void Input::HandleMouseUp_(int button, const Vector2f& position) {
  assert(g_base->InLogicThread());
  MarkInputActive();

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_base->graphics->PixelToVirtualX(
      position.x * g_base->graphics->screen_pixel_width());
  cursor_pos_y_ = g_base->graphics->PixelToVirtualY(
      position.y * g_base->graphics->screen_pixel_height());

  // If we have a touch-input in editing mode, pass along events to it.
  // It usually handles its own events but here we want it to play nice
  // with stuff under it by blocking touches, etc.
  if (touch_input_ && touch_input_->editing()) {
    touch_input_->HandleTouchUp(reinterpret_cast<void*>(1), cursor_pos_x_,
                                cursor_pos_y_);
  }

  ApplyMouseUpCancelToCamera(button);

  g_base->ui->HandleMouseUp(button, cursor_pos_x_, cursor_pos_y_);
}

void Input::HandleMouseCancel_(int button, const Vector2f& position) {
  assert(g_base->InLogicThread());
  MarkInputActive();

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_base->graphics->PixelToVirtualX(
      position.x * g_base->graphics->screen_pixel_width());
  cursor_pos_y_ = g_base->graphics->PixelToVirtualY(
      position.y * g_base->graphics->screen_pixel_height());

  // If we have a touch-input in editing mode, pass along events to it.
  // It usually handles its own events but here we want it to play nice
  // with stuff under it by blocking touches, etc.
  //
  // FIXME - passing as touch-up.
  if (touch_input_ && touch_input_->editing()) {
    touch_input_->HandleTouchUp(reinterpret_cast<void*>(1), cursor_pos_x_,
                                cursor_pos_y_);
  }

  ApplyMouseUpCancelToCamera(button);

  g_base->ui->HandleMouseCancel(button, cursor_pos_x_, cursor_pos_y_);
}

void Input::PushTouchEvent(const TouchEvent& e) {
  assert(g_base->logic->event_loop());
  auto* loop{g_base->logic->event_loop()};
  if (loop->CheckPushSafety()) {
    loop->PushCall([e, this] { HandleTouchEvent_(e); });
  }
}

void Input::HandleTouchEvent_(const TouchEvent& e) {
  assert(g_base->InLogicThread());
  assert(g_base->graphics);

  // Mark as active even if input is locked.
  MarkInputActive();

  if (IsInputLocked()) {
    return;
  }

  if (g_buildconfig.platform_ios_tvos()) {
    printf("FIXME: update touch handling\n");
  }

  float x = g_base->graphics->PixelToVirtualX(
      e.x * g_base->graphics->screen_pixel_width());
  float y = g_base->graphics->PixelToVirtualY(
      e.y * g_base->graphics->screen_pixel_height());

  if (e.overall) {
    // Sanity test: if the OS tells us that this is the beginning of an,
    // overall multitouch gesture, it should always be winding up as our
    // single_touch_.
    if (e.type == TouchEvent::Type::kDown && single_touch_ != nullptr) {
      BA_LOG_ONCE(LogName::kBaInput, LogLevel::kError,
                  "Got touch labeled first but will not be our single.");
    }

    // Also: if the OS tells us that this is the end of an overall
    // multi-touch gesture, it should mean that our single_touch_ has ended
    // or will be.
    if ((e.type == TouchEvent::Type::kUp
         || e.type == TouchEvent::Type::kCanceled)
        && single_touch_ != nullptr && single_touch_ != e.touch) {
      BA_LOG_ONCE(LogName::kBaInput, LogLevel::kError,
                  "Last touch coming up is not single touch!");
    }
  }

  // We keep track of one 'single' touch which we pass along as mouse events
  // which covers most UI stuff.
  if (e.type == TouchEvent::Type::kDown && single_touch_ == nullptr) {
    single_touch_ = e.touch;
    HandleMouseDown_(SDL_BUTTON_LEFT, Vector2f(e.x, e.y));
  }

  if (e.type == TouchEvent::Type::kMoved && e.touch == single_touch_) {
    HandleMouseMotion_(Vector2f(e.x, e.y));
  }

  if ((e.type == TouchEvent::Type::kUp)
      && (e.touch == single_touch_ || e.overall)) {
    single_touch_ = nullptr;
    HandleMouseUp_(SDL_BUTTON_LEFT, Vector2f(e.x, e.y));
  }

  if ((e.type == TouchEvent::Type::kCanceled)
      && (e.touch == single_touch_ || e.overall)) {
    single_touch_ = nullptr;
    HandleMouseCancel_(SDL_BUTTON_LEFT, Vector2f(e.x, e.y));
  }
  // If we've got a touch input device, forward events along to it.
  if (touch_input_) {
    touch_input_->HandleTouchEvent(e.type, e.touch, x, y);
  }
}

void Input::ResetJoyStickHeldButtons() {
  for (auto&& i : input_devices_) {
    if (i.exists()) {
      i->ResetHeldStates();
    }
  }
}

// Send key-ups for any currently-held keys.
void Input::ResetKeyboardHeldKeys() {
  assert(g_base->InLogicThread());
  if (!g_core->HeadlessMode()) {
    // Synthesize key-ups for all our held keys.
    while (!keys_held_.empty()) {
      SDL_Keysym k;
      memset(&k, 0, sizeof(k));
      k.sym = (SDL_Keycode)(*keys_held_.begin());
      HandleKeyRelease_(k);
    }
  }
}

void Input::Draw(FrameDef* frame_def) {
  // Draw touch input visual guides.
  if (touch_input_) {
    touch_input_->Draw(frame_def);
  }
}

auto Input::IsCursorVisible() const -> bool {
  assert(g_base->InLogicThread());

  // Keeps mouse hidden to start with.
  if (mouse_move_count_ < 2) {
    return false;
  }

  // If cursor has been flagged as outside the window.
  if (!cursor_in_window_) {
    return false;
  }

  // Hide our cursor as soon as we start shutting down (don't want software
  // cursor to be frozen on screen with our last frame).
  if (g_base->logic->shutting_down()) {
    return false;
  }

  // Show our cursor only if its been moved recently.
  return (g_core->AppTimeSeconds() - last_mouse_move_time_ < 2.071);
}

void Input::LsInputDevices() {
  BA_PRECONDITION(g_base->InLogicThread());

  std::string out;

  std::string ind{"  "};
  int index{0};
  for (auto& device : input_devices_) {
    if (index != 0) {
      out += "\n";
    }
    out += std::to_string(index + 1) + ":\n";
    out += ind + "name: " + device->GetDeviceName() + "\n";
    out += ind + "index: " + std::to_string(device->index()) + "\n";
    out += (ind + "is-controller: " + std::to_string(device->IsController())
            + "\n");
    out += (ind + "is-sdl-controller: "
            + std::to_string(device->IsSDLController()) + "\n");
    out += (ind + "is-touch-screen: " + std::to_string(device->IsTouchScreen())
            + "\n");
    out += (ind + "is-remote-control: "
            + std::to_string(device->IsRemoteControl()) + "\n");
    out += (ind + "is-test-input: " + std::to_string(device->IsTestInput())
            + "\n");
    out +=
        (ind + "is-keyboard: " + std::to_string(device->IsKeyboard()) + "\n");
    out += (ind + "is-mfi-controller: "
            + std::to_string(device->IsMFiController()) + "\n");
    out += (ind + "is-local: " + std::to_string(device->IsLocal()) + "\n");
    out += (ind + "is-ui-only: " + std::to_string(device->IsUIOnly()) + "\n");
    out += (ind + "is-remote-app: " + std::to_string(device->IsRemoteApp())
            + "\n");

    out += ind + "attached-to: " + device->delegate().DescribeAttachedTo();

    ++index;
  }

  g_core->logging->Log(LogName::kBaInput, LogLevel::kInfo, out);
}

auto Input::ShouldAllowInputInAttractMode_(InputDevice* device) const -> bool {
  if (device == nullptr) {
    return false;
  }
  return device->allow_input_in_attract_mode();
}

}  // namespace ballistica::base
