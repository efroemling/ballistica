// Released under the MIT License. See LICENSE for details.

#include "ballistica/input/input.h"

#include "ballistica/app/app.h"
#include "ballistica/app/app_config.h"
#include "ballistica/audio/audio.h"
#include "ballistica/core/thread.h"
#include "ballistica/graphics/camera.h"
#include "ballistica/input/device/joystick.h"
#include "ballistica/input/device/keyboard_input.h"
#include "ballistica/input/device/test_input.h"
#include "ballistica/input/device/touch_input.h"
#include "ballistica/logic/player.h"
#include "ballistica/python/python.h"
#include "ballistica/ui/console.h"
#include "ballistica/ui/root_ui.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/root_widget.h"

namespace ballistica {

// Though it seems strange, input is actually owned by the logic thread, not the
// app thread. This keeps things simple for game logic interacting with input
// stuff (controller names, counts, etc) but means we need to be prudent about
// properly passing stuff between the game and app thread as needed.

// The following was pulled from sdl2
#if BA_SDL2_BUILD || BA_MINSDL_BUILD
static const char* const scancode_names[SDL_NUM_SCANCODES] = {
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "0",
    "Return",
    "Escape",
    "Backspace",
    "Tab",
    "Space",
    "-",
    "=",
    "[",
    "]",
    "\\",
    "#",
    ";",
    "'",
    "`",
    ",",
    ".",
    "/",
    "CapsLock",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "PrintScreen",
    "ScrollLock",
    "Pause",
    "Insert",
    "Home",
    "PageUp",
    "Delete",
    "End",
    "PageDown",
    "Right",
    "Left",
    "Down",
    "Up",
    "Numlock",
    "Keypad /",
    "Keypad *",
    "Keypad -",
    "Keypad +",
    "Keypad Enter",
    "Keypad 1",
    "Keypad 2",
    "Keypad 3",
    "Keypad 4",
    "Keypad 5",
    "Keypad 6",
    "Keypad 7",
    "Keypad 8",
    "Keypad 9",
    "Keypad 0",
    "Keypad .",
    nullptr,
    "Application",
    "Power",
    "Keypad =",
    "F13",
    "F14",
    "F15",
    "F16",
    "F17",
    "F18",
    "F19",
    "F20",
    "F21",
    "F22",
    "F23",
    "F24",
    "Execute",
    "Help",
    "Menu",
    "Select",
    "Stop",
    "Again",
    "Undo",
    "Cut",
    "Copy",
    "Paste",
    "Find",
    "Mute",
    "VolumeUp",
    "VolumeDown",
    nullptr,
    nullptr,
    nullptr,
    "Keypad ,",
    "Keypad = (AS400)",
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "AltErase",
    "SysReq",
    "Cancel",
    "Clear",
    "Prior",
    "Return",
    "Separator",
    "Out",
    "Oper",
    "Clear / Again",
    "CrSel",
    "ExSel",
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "Keypad 00",
    "Keypad 000",
    "ThousandsSeparator",
    "DecimalSeparator",
    "CurrencyUnit",
    "CurrencySubUnit",
    "Keypad (",
    "Keypad )",
    "Keypad {",
    "Keypad }",
    "Keypad Tab",
    "Keypad Backspace",
    "Keypad A",
    "Keypad B",
    "Keypad C",
    "Keypad D",
    "Keypad E",
    "Keypad F",
    "Keypad XOR",
    "Keypad ^",
    "Keypad %",
    "Keypad <",
    "Keypad >",
    "Keypad &",
    "Keypad &&",
    "Keypad |",
    "Keypad ||",
    "Keypad :",
    "Keypad #",
    "Keypad Space",
    "Keypad @",
    "Keypad !",
    "Keypad MemStore",
    "Keypad MemRecall",
    "Keypad MemClear",
    "Keypad MemAdd",
    "Keypad MemSubtract",
    "Keypad MemMultiply",
    "Keypad MemDivide",
    "Keypad +/-",
    "Keypad Clear",
    "Keypad ClearEntry",
    "Keypad Binary",
    "Keypad Octal",
    "Keypad Decimal",
    "Keypad Hexadecimal",
    nullptr,
    nullptr,
    "Left Ctrl",
    "Left Shift",
    "Left Alt",
    "Left GUI",
    "Right Ctrl",
    "Right Shift",
    "Right Alt",
    "Right GUI",
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    "ModeSwitch",
    "AudioNext",
    "AudioPrev",
    "AudioStop",
    "AudioPlay",
    "AudioMute",
    "MediaSelect",
    "WWW",
    "Mail",
    "Calculator",
    "Computer",
    "AC Search",
    "AC Home",
    "AC Back",
    "AC Forward",
    "AC Stop",
    "AC Refresh",
    "AC Bookmarks",
    "BrightnessDown",
    "BrightnessUp",
    "DisplaySwitch",
    "KBDIllumToggle",
    "KBDIllumDown",
    "KBDIllumUp",
    "Eject",
    "Sleep",
    "App1",
    "App2",
    "AudioRewind",
    "AudioFastForward",
};
#endif  // BA_SDL2_BUILD || BA_MINSDL_BUILD

Input::Input() {}

void Input::PushCreateKeyboardInputDevices() {
  g_logic->thread()->PushCall([this] { CreateKeyboardInputDevices(); });
}

void Input::CreateKeyboardInputDevices() {
  assert(InLogicThread());
  if (keyboard_input_ != nullptr || keyboard_input_2_ != nullptr) {
    Log(LogLevel::kError,
        "CreateKeyboardInputDevices called with existing kbs.");
    return;
  }
  keyboard_input_ = Object::NewDeferred<KeyboardInput>(nullptr);
  AddInputDevice(keyboard_input_, false);
  keyboard_input_2_ = Object::NewDeferred<KeyboardInput>(keyboard_input_);
  AddInputDevice(keyboard_input_2_, false);
}

void Input::PushDestroyKeyboardInputDevices() {
  g_logic->thread()->PushCall([this] { DestroyKeyboardInputDevices(); });
}

void Input::DestroyKeyboardInputDevices() {
  assert(InLogicThread());
  if (keyboard_input_ == nullptr || keyboard_input_2_ == nullptr) {
    Log(LogLevel::kError,
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
  assert(InLogicThread());
  for (auto&& i : input_devices_) {
    if (i.exists() && (i->GetDeviceName() == name)
        && i->GetPersistentIdentifier() == unique_id) {
      return i.get();
    }
  }
  return nullptr;
}

auto Input::GetNewNumberedIdentifier(const std::string& name,
                                     const std::string& identifier) -> int {
  assert(InLogicThread());

  // Stuff like reserved_identifiers["JoyStickType"]["0x812312314"] = 2;

  // First off, if we came with an identifier, see if we've got a reserved
  // number already.
  if (!identifier.empty()) {
    auto i = reserved_identifiers_.find(name);
    if (i != reserved_identifiers_.end()) {
      auto j = i->second.find(identifier);
      if (j != i->second.end()) {
        return j->second;
      }
    }
  }

  int num = 1;
  int full_id;
  while (true) {
    bool in_use = false;

    // Scan other devices with the same device-name and find the first number
    // suffix that's not taken.
    for (auto&& i : input_devices_) {
      if (i.exists()) {
        if ((i->GetRawDeviceName() == name) && i->number() == num) {
          in_use = true;
          break;
        }
      }
    }
    if (!in_use) {
      // Ok so far its unused.. however input devices that provide non-empty
      // identifiers (serial number, usb-id, etc) reserve their number for the
      // duration of the game, so we need to check against all reserved numbers
      // so we don't steal someones... (so that if they disconnect and reconnect
      // they'll get the same number and thus the same name, etc)
      if (!identifier.empty()) {
        auto i = reserved_identifiers_.find(name);
        if (i != reserved_identifiers_.end()) {
          for (auto&& j : i->second) {
            if (j.second == num) {
              in_use = true;
              break;
            }
          }
        }
      }

      // If its *still* clear lets nab it.
      if (!in_use) {
        full_id = num;

        // If we have an identifier, reserve it.
        if (!identifier.empty()) {
          reserved_identifiers_[name][identifier] = num;
        }
        break;
      }
    }
    num++;
  }
  return full_id;
}

void Input::CreateTouchInput() {
  assert(InMainThread());
  assert(touch_input_ == nullptr);
  touch_input_ = Object::NewDeferred<TouchInput>();
  PushAddInputDeviceCall(touch_input_, false);
}

void Input::AnnounceConnects() {
  static bool first_print = true;

  // For the first announcement just say "X controllers detected" and don't have
  // a sound.
  if (first_print && GetRealTime() < 10000) {
    first_print = false;

    // Disabling this completely for now; being more lenient with devices
    // allowed on android means this will often come back with large numbers.
    bool do_print{false};

    // If there's been several connected, just give a number.
    if (explicit_bool(do_print)) {
      if (newly_connected_controllers_.size() > 1) {
        std::string s = g_logic->GetResourceString("controllersDetectedText");
        Utils::StringReplaceOne(
            &s, "${COUNT}",
            std::to_string(newly_connected_controllers_.size()));
        ScreenMessage(s);
      } else {
        ScreenMessage(g_logic->GetResourceString("controllerDetectedText"));
      }
    }
  } else {
    // If there's been several connected, just give a number.
    if (newly_connected_controllers_.size() > 1) {
      std::string s = g_logic->GetResourceString("controllersConnectedText");
      Utils::StringReplaceOne(
          &s, "${COUNT}", std::to_string(newly_connected_controllers_.size()));
      ScreenMessage(s);
    } else {
      // If its just one, name it.
      std::string s = g_logic->GetResourceString("controllerConnectedText");
      Utils::StringReplaceOne(&s, "${CONTROLLER}",
                              newly_connected_controllers_.front());
      ScreenMessage(s);
    }
    g_audio->PlaySound(g_assets->GetSound(SystemSoundID::kGunCock));
  }

  newly_connected_controllers_.clear();
}

void Input::AnnounceDisconnects() {
  // If there's been several connected, just give a number.
  if (newly_disconnected_controllers_.size() > 1) {
    std::string s = g_logic->GetResourceString("controllersDisconnectedText");
    Utils::StringReplaceOne(
        &s, "${COUNT}", std::to_string(newly_disconnected_controllers_.size()));
    ScreenMessage(s);
  } else {
    // If its just one, name it.
    std::string s = g_logic->GetResourceString("controllerDisconnectedText");
    Utils::StringReplaceOne(&s, "${CONTROLLER}",
                            newly_disconnected_controllers_.front());
    ScreenMessage(s);
  }
  g_audio->PlaySound(g_assets->GetSound(SystemSoundID::kCorkPop));

  newly_disconnected_controllers_.clear();
}

void Input::ShowStandardInputDeviceConnectedMessage(InputDevice* j) {
  assert(InLogicThread());
  std::string suffix;
  suffix += j->GetPersistentIdentifier();
  suffix += j->GetDeviceExtraDescription();
  if (!suffix.empty()) {
    suffix = " " + suffix;
  }
  newly_connected_controllers_.push_back(j->GetDeviceName() + suffix);

  // Set a timer to go off and announce the accumulated additions.
  if (connect_print_timer_id_ != 0) {
    g_logic->DeleteRealTimer(connect_print_timer_id_);
  }
  connect_print_timer_id_ = g_logic->NewRealTimer(
      250, false, NewLambdaRunnable([this] { AnnounceConnects(); }));
}

void Input::ShowStandardInputDeviceDisconnectedMessage(InputDevice* j) {
  assert(InLogicThread());

  newly_disconnected_controllers_.push_back(j->GetDeviceName() + " "
                                            + j->GetPersistentIdentifier()
                                            + j->GetDeviceExtraDescription());

  // Set a timer to go off and announce the accumulated additions.
  if (disconnect_print_timer_id_ != 0) {
    g_logic->DeleteRealTimer(disconnect_print_timer_id_);
  }
  disconnect_print_timer_id_ = g_logic->NewRealTimer(
      250, false, NewLambdaRunnable([this] { AnnounceDisconnects(); }));
}

void Input::PushAddInputDeviceCall(InputDevice* input_device,
                                   bool standard_message) {
  g_logic->thread()->PushCall([this, input_device, standard_message] {
    AddInputDevice(input_device, standard_message);
  });
}

void Input::AddInputDevice(InputDevice* input, bool standard_message) {
  assert(InLogicThread());

  // Lets go through and find the first unused input-device id and use that
  // (might as well keep our list small if we can).
  int index = 0;
  bool found_slot = false;
  for (auto& input_device : input_devices_) {
    if (!input_device.exists()) {
      input_device = Object::MakeRefCounted(input);
      found_slot = true;
      input->set_index(index);
      break;
    }
    index++;
  }
  if (!found_slot) {
    input_devices_.push_back(Object::MakeRefCounted(input));
    input->set_index(static_cast<int>(input_devices_.size() - 1));
  }

  // We also want to give this input-device as unique an identifier as
  // possible. We ask it for its own string which hopefully includes a serial
  // or something, but if it doesn't and thus matches an already-existing one,
  // we tack an index on to it. that way we can at least uniquely address them
  // based off how many are connected.
  input->set_numbered_identifier(GetNewNumberedIdentifier(
      input->GetRawDeviceName(), input->GetDeviceIdentifier()));
  input->ConnectionComplete();  // Let it do any announcing it wants to.

  // Update controls for just this guy.
  input->UpdateMapping();

  // Need to do this after updating controls, as some control settings can
  // affect things we count (such as whether start activates default button).
  UpdateInputDeviceCounts();

  if (g_buildconfig.ostype_macos()) {
    // Special case: on mac, the first time a iOS/Mac controller is connected,
    // let the user know they may want to enable them if they're currently set
    // as ignored. (the default at the moment is to only use classic device
    // support).
    static bool printed_ios_mac_controller_warning = false;
    if (!printed_ios_mac_controller_warning && ignore_mfi_controllers_
        && input->IsMFiController()) {
      ScreenMessage(R"({"r":"macControllerSubsystemMFiNoteText"})", {1, 1, 0});
      printed_ios_mac_controller_warning = true;
    }
  }

  if (standard_message && !input->ShouldBeHiddenFromUser()) {
    ShowStandardInputDeviceConnectedMessage(input);
  }
}

void Input::PushRemoveInputDeviceCall(InputDevice* input_device,
                                      bool standard_message) {
  g_logic->thread()->PushCall([this, input_device, standard_message] {
    RemoveInputDevice(input_device, standard_message);
  });
}

void Input::RemoveInputDevice(InputDevice* input, bool standard_message) {
  assert(InLogicThread());

  if (standard_message && !input->ShouldBeHiddenFromUser()) {
    ShowStandardInputDeviceDisconnectedMessage(input);
  }

  // Just look for it in our list.. if we find it, simply clear the ref
  // (we need to keep the pointer around so our list indices don't change).
  for (auto& input_device : input_devices_) {
    if (input_device.exists() && (input_device.get() == input)) {
      // Pull it off the list before killing it (in case it triggers another
      // kill itself).
      Object::Ref<InputDevice> device = input_device;

      // Ok we cleared its slot in our vector; now we just have
      // the local variable 'device' keeping it alive.
      input_device.Clear();

      // If we're attached to a local or remote player, kill the player.
      if (input->attached_to_player()) {
        if (input->GetPlayer() != nullptr) {
          // NOTE: we now remove the player instantly instead of pushing
          // a call to do it; otherwise its possible that someone tries
          // to access the player's inputdevice before the call goes
          // through which would lead to an exception.
          g_logic->RemovePlayer(input->GetPlayer());
          // g_logic->PushRemovePlayerCall(input->GetPlayer());
        }
        if (input->GetRemotePlayer() != nullptr) {
          input->RemoveRemotePlayerFromGame();
        }
        device->DetachFromPlayer();
      }

      // This should kill the device.
      // FIXME: since many devices get allocated in the main thread,
      // should we not kill it there too?...
      device.Clear();
      UpdateInputDeviceCounts();
      return;
    }
  }
  throw Exception("Input::RemoveInputDevice: invalid device provided");
}

void Input::UpdateInputDeviceCounts() {
  assert(InLogicThread());

  have_button_using_inputs_ = false;
  have_start_activated_default_button_inputs_ = false;
  have_non_touch_inputs_ = false;
  int total = 0;
  int controller_count = 0;
  for (auto& input_device : input_devices_) {
    // Ok, we now limit non-keyboard non-touchscreen devices to ones that have
    // been active recently.. (we're starting to get lots of virtual devices and
    // other cruft on android; don't wanna show controller UIs just due to
    // those)
    if (input_device.exists()
        && ((*input_device).IsTouchScreen() || (*input_device).IsKeyboard()
            || ((*input_device).last_input_time() != 0
                && g_logic->master_time() - (*input_device).last_input_time()
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
      g_python->PushObjCall(Python::ObjID::kAwardInControlAchievementCall);
    } else if (max_controller_count_so_far_ == 2) {
      g_python->PushObjCall(Python::ObjID::kAwardDualWieldingAchievementCall);
    }
  }
}

auto Input::GetLocalActiveInputDeviceCount() -> int {
  assert(InLogicThread());

  // This can get called alot so lets cache the value.
  millisecs_t current_time = g_logic->master_time();
  if (current_time != last_get_local_active_input_device_count_check_time_) {
    last_get_local_active_input_device_count_check_time_ = current_time;

    int count = 0;
    for (auto& input_device : input_devices_) {
      // Tally up local non-keyboard, non-touchscreen devices that have been
      // used in the last minute.
      if (input_device.exists() && !input_device->IsKeyboard()
          && !input_device->IsTouchScreen() && !input_device->IsUIOnly()
          && input_device->IsLocal()
          && (input_device->last_input_time() != 0
              && g_logic->master_time() - input_device->last_input_time()
                     < 60000)) {
        count++;
      }
    }
    local_active_input_device_count_ = count;
  }
  return local_active_input_device_count_;
}

auto Input::HaveControllerWithPlayer() -> bool {
  assert(InLogicThread());
  // NOLINTNEXTLINE(readability-use-anyofallof)
  for (auto& input_device : input_devices_) {
    if (input_device.exists() && (*input_device).IsController()
        && (*input_device).attached_to_player()) {
      return true;
    }
  }
  return false;
}

auto Input::HaveRemoteAppController() -> bool {
  assert(InLogicThread());
  // NOLINTNEXTLINE(readability-use-anyofallof)
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
  if (!HeadlessMode()) {
    for (auto& input_device : input_devices_) {
      if (input_device.exists()) {
        auto* js = dynamic_cast<Joystick*>(input_device.get());
        if (js && js->GetDeviceName() == name) {
          vals.push_back(js);
        }
      }
    }
  }
  return vals;
}

auto Input::GetConfigurableGamePads() -> std::vector<InputDevice*> {
  assert(InLogicThread());
  std::vector<InputDevice*> vals;
  if (!HeadlessMode()) {
    for (auto& input_device : input_devices_) {
      if (input_device.exists()) {
        auto* js = dynamic_cast<Joystick*>(input_device.get());
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
  if (g_buildconfig.ostype_macos()) {
    if (ignore_mfi_controllers_ && input_device->IsMFiController()) {
      return true;
    }
  }
  return ignore_sdl_controllers_ && input_device->IsSDLController();
}

// auto Input::GetIdleTime() const -> millisecs_t {
//   return GetRealTime() - last_input_time_;
// }

void Input::UpdateEnabledControllerSubsystems() {
  assert(IsBootstrapped());

  // First off, on mac, let's update whether we want to completely ignore either
  // the classic or the iOS/Mac controller subsystems.
  if (g_buildconfig.ostype_macos()) {
    std::string sys =
        g_app_config->Resolve(AppConfig::StringID::kMacControllerSubsystem);
    if (sys == "Classic") {
      ignore_mfi_controllers_ = true;
      ignore_sdl_controllers_ = false;
    } else if (sys == "MFi") {
      ignore_mfi_controllers_ = false;
      ignore_sdl_controllers_ = true;
    } else if (sys == "Both") {
      ignore_mfi_controllers_ = false;
      ignore_sdl_controllers_ = false;
    } else {
      BA_LOG_ONCE(LogLevel::kError,
                  "Invalid mac-controller-subsystem value: '" + sys + "'");
    }
  }
}

// Tells all inputs to update their controls based on the app config.
void Input::ApplyAppConfig() {
  assert(InLogicThread());

  UpdateEnabledControllerSubsystems();

  // It's technically possible that updating these controls will add or remove
  // devices, thus changing the input_devices_ list, so lets work with a copy of
  // it.
  std::vector<Object::Ref<InputDevice> > input_devices = input_devices_;
  for (auto& input_device : input_devices) {
    if (input_device.exists()) {
      input_device->UpdateMapping();
    }
  }
}

void Input::Update() {
  assert(InLogicThread());

  millisecs_t real_time = GetRealTime();

  // If input has been locked an excessively long amount of time, unlock it.
  if (input_lock_count_temp_) {
    if (real_time - last_input_temp_lock_time_ > 10000) {
      Log(LogLevel::kError,
          "Input has been temp-locked for 10 seconds; unlocking.");
      input_lock_count_temp_ = 0;
      PrintLockLabels();
      input_lock_temp_labels_.clear();
      input_unlock_temp_labels_.clear();
    }
  }

  // We now need to update our input-device numbers dynamically since they're
  // based on recently-active devices.
  // ..we do this much more often for the first few seconds to keep
  // controller-usage from being as annoying.
  // millisecs_t incr = (real_time > 10000) ? 468 : 98;
  // Update: don't remember why that was annoying; trying a single value for
  // now.
  millisecs_t incr = 249;
  if (real_time - last_input_device_count_update_time_ > incr) {
    UpdateInputDeviceCounts();
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
  assert(InLogicThread());

  // Detach all inputs from players.
  for (auto& input_device : input_devices_) {
    if (input_device.exists()) {
      input_device->DetachFromPlayer();
    }
  }
}

void Input::LockAllInput(bool permanent, const std::string& label) {
  assert(InLogicThread());
  if (permanent) {
    input_lock_count_permanent_++;
    input_lock_permanent_labels_.push_back(label);
  } else {
    input_lock_count_temp_++;
    if (input_lock_count_temp_ == 1) {
      last_input_temp_lock_time_ = GetRealTime();
    }
    input_lock_temp_labels_.push_back(label);

    recent_input_locks_unlocks_.push_back("temp lock: " + label + " time "
                                          + std::to_string(GetRealTime()));
    while (recent_input_locks_unlocks_.size() > 10) {
      recent_input_locks_unlocks_.pop_front();
    }
  }
}

void Input::UnlockAllInput(bool permanent, const std::string& label) {
  assert(InLogicThread());

  recent_input_locks_unlocks_.push_back(
      permanent
          ? "permanent unlock: "
          : "temp unlock: " + label + " time " + std::to_string(GetRealTime()));
  while (recent_input_locks_unlocks_.size() > 10)
    recent_input_locks_unlocks_.pop_front();

  if (permanent) {
    input_lock_count_permanent_--;
    input_unlock_permanent_labels_.push_back(label);
    if (input_lock_count_permanent_ < 0) {
      BA_LOG_PYTHON_TRACE_ONCE("lock-count-permanent < 0");
      PrintLockLabels();
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
      Log(LogLevel::kWarning, "temp input unlock at time "
                                  + std::to_string(GetRealTime())
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

void Input::PrintLockLabels() {
  std::string s =
      "INPUT LOCK REPORT (time=" + std::to_string(GetRealTime()) + "):";
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

  Log(LogLevel::kError, s);
}

void Input::ProcessStressTesting(int player_count) {
  assert(InMainThread());
  assert(player_count >= 0);

  millisecs_t time = GetRealTime();

  // FIXME: If we don't check for stress_test_last_leave_time_ we totally
  //  confuse the game.. need to be able to survive that.

  // Kill some off if we have too many.
  while (static_cast<int>(test_inputs_.size()) > player_count) {
    delete test_inputs_.front();
    test_inputs_.pop_front();
  }

  // If we have less than full test-inputs, add one randomly.
  if (static_cast<int>(test_inputs_.size()) < player_count
      && ((rand() % 1000 < 10))) {  // NOLINT
    test_inputs_.push_back(new TestInput());
  }

  // Every so often lets kill the oldest one off.
  if (explicit_bool(true)) {
    if (test_inputs_.size() > 0 && (rand() % 2000 < 3)) {  // NOLINT
      stress_test_last_leave_time_ = time;

      // Usually do oldest; sometimes newest.
      if (rand() % 5 == 0) {  // NOLINT
        delete test_inputs_.back();
        test_inputs_.pop_back();
      } else {
        delete test_inputs_.front();
        test_inputs_.pop_front();
      }
    }
  }

  if (time - stress_test_time_ > 1000) {
    stress_test_time_ = time;  // reset..
    for (auto& test_input : test_inputs_) {
      (*test_input).Reset();
    }
  }
  while (stress_test_time_ < time) {
    stress_test_time_++;
    for (auto& test_input : test_inputs_) {
      (*test_input).Process(stress_test_time_);
    }
  }
}

void Input::PushTextInputEvent(const std::string& text) {
  g_logic->thread()->PushCall([this, text] {
    mark_input_active();

    // Ignore  if input is locked.
    if (IsInputLocked()) {
      return;
    }
    if (g_app->console != nullptr && g_app->console->HandleTextEditing(text)) {
      return;
    }
    g_ui->SendWidgetMessage(WidgetMessage(WidgetMessage::Type::kTextInput,
                                          nullptr, 0, 0, 0, 0, text.c_str()));
  });
}

auto Input::PushJoystickEvent(const SDL_Event& event, InputDevice* input_device)
    -> void {
  g_logic->thread()->PushCall([this, event, input_device] {
    HandleJoystickEvent(event, input_device);
  });
}

void Input::HandleJoystickEvent(const SDL_Event& event,
                                InputDevice* input_device) {
  assert(InLogicThread());
  assert(input_device);

  if (ShouldCompletelyIgnoreInputDevice(input_device)) {
    return;
  }
  if (IsInputLocked()) {
    return;
  }

  // Make note that we're not idle.
  mark_input_active();

  // And that this particular device isn't idle either.
  input_device->UpdateLastInputTime();

  // Give Python a crack at it for captures, etc.
  if (g_python->HandleJoystickEvent(event, input_device)) {
    return;
  }

  input_device->HandleSDLEvent(&event);
}

void Input::PushKeyPressEvent(const SDL_Keysym& keysym) {
  g_logic->thread()->PushCall([this, keysym] { HandleKeyPress(&keysym); });
}

void Input::PushKeyReleaseEvent(const SDL_Keysym& keysym) {
  g_logic->thread()->PushCall([this, keysym] { HandleKeyRelease(&keysym); });
}

void Input::HandleKeyPress(const SDL_Keysym* keysym) {
  assert(InLogicThread());

  mark_input_active();

  // Ignore all key presses if input is locked.
  if (IsInputLocked()) {
    return;
  }

  // Give Python a crack at it for captures, etc.
  if (g_python->HandleKeyPressEvent(*keysym)) {
    return;
  }

  // Regardless of what else we do, keep track of mod key states.
  // (for things like manual camera moves. For individual key presses
  // ideally we should use the modifiers bundled with the key presses)
  UpdateModKeyStates(keysym, true);

  bool repeat_press;
  if (keys_held_.count(keysym->sym) != 0) {
    repeat_press = true;
  } else {
    repeat_press = false;
    keys_held_.insert(keysym->sym);
  }

  // Mobile-specific stuff.
  if (g_buildconfig.ostype_ios_tvos() || g_buildconfig.ostype_android()) {
    switch (keysym->sym) {
      // FIXME: See if this stuff is still necessary. Was this perhaps
      //  specifically to support the console?
      case SDLK_DELETE:
      case SDLK_RETURN:
      case SDLK_KP_ENTER:
      case SDLK_BACKSPACE: {
        // FIXME: I don't remember what this was put here for, but now that we
        //  have hardware keyboards it crashes text fields by sending them a
        //  TEXT_INPUT message with no string.. I made them resistant to that
        //  case but wondering if we can take this out?...
        g_ui->SendWidgetMessage(
            WidgetMessage(WidgetMessage::Type::kTextInput, keysym));
        break;
      }
      default:
        break;
    }
  }

  // A few things that apply only to non-mobile.
  if (!g_buildconfig.ostype_ios_tvos() && !g_buildconfig.ostype_android()) {
    // Command-F or Control-F toggles full-screen.
    if (!repeat_press && keysym->sym == SDLK_f
        && ((keysym->mod & KMOD_CTRL) || (keysym->mod & KMOD_GUI))) {  // NOLINT
      g_python->obj(Python::ObjID::kToggleFullscreenCall).Call();
      return;
    }

    // Command-Q or Control-Q quits.
    if (!repeat_press && keysym->sym == SDLK_q
        && ((keysym->mod & KMOD_CTRL) || (keysym->mod & KMOD_GUI))) {  // NOLINT
      g_logic->PushConfirmQuitCall();
      return;
    }
  }

  // Let the console intercept stuff if it wants at this point.
  if (g_app->console != nullptr && g_app->console->HandleKeyPress(keysym)) {
    return;
  }

  // Ctrl-V or Cmd-V sends paste commands to any interested text fields.
  // Command-Q or Control-Q quits.
  if (!repeat_press && keysym->sym == SDLK_v
      && ((keysym->mod & KMOD_CTRL) || (keysym->mod & KMOD_GUI))) {  // NOLINT
    g_ui->SendWidgetMessage(WidgetMessage(WidgetMessage::Type::kPaste));
    return;
  }

  bool handled = false;

  // None of the following stuff accepts key repeats.
  if (!repeat_press) {
    switch (keysym->sym) {
      // Menu button on android/etc. pops up the menu.
      case SDLK_MENU: {
        if (g_ui && g_ui->screen_root_widget()) {
          // If there's no dialogs/windows up, ask for a menu (owned by the
          // touch-screen if available).
          if (g_ui->screen_root_widget()->GetChildCount() == 0) {
            g_ui->PushMainMenuPressCall(touch_input_);
          }
        }
        handled = true;
        break;
      }

      case SDLK_EQUALS:
      case SDLK_PLUS:
        g_logic->ChangeGameSpeed(1);
        handled = true;
        break;

      case SDLK_MINUS:
        g_logic->ChangeGameSpeed(-1);
        handled = true;
        break;

      case SDLK_F5: {
        g_ui->root_ui()->TogglePartyWindowKeyPress();
        handled = true;
        break;
      }

      case SDLK_F7:
        g_logic->PushToggleManualCameraCall();
        handled = true;
        break;

      case SDLK_F8:
        g_logic->PushToggleDebugInfoDisplayCall();
        handled = true;
        break;

      case SDLK_F9:
        g_python->PushObjCall(Python::ObjID::kLanguageTestToggleCall);
        handled = true;
        break;

      case SDLK_F10:
        g_logic->PushToggleCollisionGeometryDisplayCall();
        handled = true;
        break;

      case SDLK_ESCAPE:

        if (g_ui && g_ui->screen_root_widget() && g_ui->root_widget()
            && g_ui->overlay_root_widget()) {
          // If there's no dialogs/windows up, ask for a menu owned by the
          // keyboard.
          if (g_ui->screen_root_widget()->GetChildCount() == 0
              && g_ui->overlay_root_widget()->GetChildCount() == 0) {
            if (keyboard_input_) {
              g_ui->PushMainMenuPressCall(keyboard_input_);
            }
          } else {
            // Ok there's a UI up.. send along a cancel message.
            g_ui->root_widget()->HandleMessage(
                WidgetMessage(WidgetMessage::Type::kCancel));
          }
        }
        handled = true;
        break;

      default:
        break;
    }
  }

  // If we haven't claimed it, pass it along as potential player/widget input.
  if (!handled) {
    if (keyboard_input_) {
      keyboard_input_->HandleKey(keysym, repeat_press, true);
    }
  }
}

void Input::HandleKeyRelease(const SDL_Keysym* keysym) {
  assert(InLogicThread());

  // Note: we want to let these through even if input is locked.

  mark_input_active();

  // Give Python a crack at it for captures, etc.
  if (g_python->HandleKeyReleaseEvent(*keysym)) {
    return;
  }

  // Regardless of what else we do, keep track of mod key states.
  // (for things like manual camera moves. For individual key presses
  // ideally we should use the modifiers bundled with the key presses)
  UpdateModKeyStates(keysym, false);

  // In some cases we may receive duplicate key-release events
  // (if a keyboard reset was run it deals out key releases but then the
  // keyboard driver issues them as well)
  if (keys_held_.count(keysym->sym) == 0) {
    return;
  }

  keys_held_.erase(keysym->sym);

  if (IsInputLocked()) {
    return;
  }

  bool handled = false;

  if (g_app->console != nullptr && g_app->console->HandleKeyRelease(keysym)) {
    handled = true;
  }

  // If we haven't claimed it, pass it along as potential player input.
  if (!handled) {
    if (keyboard_input_) {
      keyboard_input_->HandleKey(keysym, false, false);
    }
  }
}

auto Input::UpdateModKeyStates(const SDL_Keysym* keysym, bool press) -> void {
  switch (keysym->sym) {
    case SDLK_LCTRL:
    case SDLK_RCTRL: {
      if (Camera* c = g_graphics->camera()) {
        c->set_ctrl_down(press);
      }
      break;
    }
    case SDLK_LALT:
    case SDLK_RALT: {
      if (Camera* c = g_graphics->camera()) {
        c->set_alt_down(press);
      }
      break;
    }
    case SDLK_LGUI:
    case SDLK_RGUI: {
      if (Camera* c = g_graphics->camera()) {
        c->set_cmd_down(press);
      }
      break;
    }
    default:
      break;
  }
}

auto Input::PushMouseScrollEvent(const Vector2f& amount) -> void {
  g_logic->thread()->PushCall([this, amount] { HandleMouseScroll(amount); });
}

auto Input::HandleMouseScroll(const Vector2f& amount) -> void {
  assert(InLogicThread());
  if (IsInputLocked()) {
    return;
  }
  mark_input_active();

  Widget* root_widget = g_ui->root_widget();
  if (std::abs(amount.y) > 0.0001f && root_widget) {
    root_widget->HandleMessage(WidgetMessage(WidgetMessage::Type::kMouseWheel,
                                             nullptr, cursor_pos_x_,
                                             cursor_pos_y_, amount.y));
  }
  if (std::abs(amount.x) > 0.0001f && root_widget) {
    root_widget->HandleMessage(WidgetMessage(WidgetMessage::Type::kMouseWheelH,
                                             nullptr, cursor_pos_x_,
                                             cursor_pos_y_, amount.x));
  }
  mouse_move_count_++;

  Camera* camera = g_graphics->camera();
  if (camera) {
    if (camera->manual()) {
      camera->ManualHandleMouseWheel(0.005f * amount.y);
    }
  }
}

auto Input::PushSmoothMouseScrollEvent(const Vector2f& velocity, bool momentum)
    -> void {
  g_logic->thread()->PushCall([this, velocity, momentum] {
    HandleSmoothMouseScroll(velocity, momentum);
  });
}

auto Input::HandleSmoothMouseScroll(const Vector2f& velocity, bool momentum)
    -> void {
  assert(InLogicThread());
  if (IsInputLocked()) {
    return;
  }
  mark_input_active();

  bool handled = false;
  Widget* root_widget = g_ui->root_widget();
  if (root_widget) {
    handled = root_widget->HandleMessage(
        WidgetMessage(WidgetMessage::Type::kMouseWheelVelocity, nullptr,
                      cursor_pos_x_, cursor_pos_y_, velocity.y, momentum));
    root_widget->HandleMessage(
        WidgetMessage(WidgetMessage::Type::kMouseWheelVelocityH, nullptr,
                      cursor_pos_x_, cursor_pos_y_, velocity.x, momentum));
  }
  last_mouse_move_time_ = GetRealTime();
  mouse_move_count_++;

  Camera* camera = g_graphics->camera();
  if (!handled && camera) {
    if (camera->manual()) {
      camera->ManualHandleMouseWheel(-0.25f * velocity.y);
    }
  }
}

auto Input::PushMouseMotionEvent(const Vector2f& position) -> void {
  g_logic->thread()->PushCall(
      [this, position] { HandleMouseMotion(position); });
}

auto Input::HandleMouseMotion(const Vector2f& position) -> void {
  assert(g_graphics);
  assert(InLogicThread());
  mark_input_active();

  float old_cursor_pos_x = cursor_pos_x_;
  float old_cursor_pos_y = cursor_pos_y_;

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_graphics->PixelToVirtualX(
      position.x * g_graphics->screen_pixel_width());
  cursor_pos_y_ = g_graphics->PixelToVirtualY(
      position.y * g_graphics->screen_pixel_height());

  last_mouse_move_time_ = GetRealTime();
  mouse_move_count_++;

  bool handled2{};

  // If we have a touch-input in editing mode, pass along events to it.
  // (it usually handles its own events but here we want it to play nice
  // with stuff under it by blocking touches, etc)
  if (touch_input_ && touch_input_->editing()) {
    touch_input_->HandleTouchMoved(reinterpret_cast<void*>(1), cursor_pos_x_,
                                   cursor_pos_y_);
  }

  // UI interaction.
  Widget* root_widget = g_ui->root_widget();
  if (root_widget && !IsInputLocked())
    handled2 = root_widget->HandleMessage(
        WidgetMessage(WidgetMessage::Type::kMouseMove, nullptr, cursor_pos_x_,
                      cursor_pos_y_));

  // Manual camera motion.
  Camera* camera = g_graphics->camera();
  if (!handled2 && camera && camera->manual()) {
    float move_h =
        (cursor_pos_x_ - old_cursor_pos_x) / g_graphics->screen_virtual_width();
    float move_v =
        (cursor_pos_y_ - old_cursor_pos_y) / g_graphics->screen_virtual_width();
    camera->ManualHandleMouseMove(move_h, move_v);
  }

  g_ui->root_ui()->HandleMouseMotion(cursor_pos_x_, cursor_pos_y_);
}

auto Input::PushMouseDownEvent(int button, const Vector2f& position) -> void {
  g_logic->thread()->PushCall(
      [this, button, position] { HandleMouseDown(button, position); });
}

auto Input::HandleMouseDown(int button, const Vector2f& position) -> void {
  assert(g_graphics);
  assert(InLogicThread());

  if (IsInputLocked()) {
    return;
  }

  if (g_ui == nullptr || g_ui->screen_root_widget() == nullptr) {
    return;
  }

  mark_input_active();

  last_mouse_move_time_ = GetRealTime();
  mouse_move_count_++;

  // printf("Mouse down at %f %f\n", position.x, position.y);

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_graphics->PixelToVirtualX(
      position.x * g_graphics->screen_pixel_width());
  cursor_pos_y_ = g_graphics->PixelToVirtualY(
      position.y * g_graphics->screen_pixel_height());

  millisecs_t click_time = GetRealTime();
  bool double_click = (click_time - last_click_time_ <= double_click_time_);
  last_click_time_ = click_time;

  bool handled2 = false;
  Widget* root_widget = g_ui->root_widget();

  // If we have a touch-input in editing mode, pass along events to it.
  // (it usually handles its own events but here we want it to play nice
  // with stuff under it by blocking touches, etc)
  if (touch_input_ && touch_input_->editing()) {
    handled2 = touch_input_->HandleTouchDown(reinterpret_cast<void*>(1),
                                             cursor_pos_x_, cursor_pos_y_);
  }

  if (!handled2) {
    if (g_ui->root_ui()->HandleMouseButtonDown(cursor_pos_x_, cursor_pos_y_)) {
      handled2 = true;
    }
  }

  if (root_widget && !handled2) {
    handled2 = root_widget->HandleMessage(
        WidgetMessage(WidgetMessage::Type::kMouseDown, nullptr, cursor_pos_x_,
                      cursor_pos_y_, double_click ? 2 : 1));
  }

  // Manual camera input.
  Camera* camera = g_graphics->camera();
  if (!handled2 && camera) {
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

auto Input::PushMouseUpEvent(int button, const Vector2f& position) -> void {
  g_logic->thread()->PushCall(
      [this, button, position] { HandleMouseUp(button, position); });
}

auto Input::HandleMouseUp(int button, const Vector2f& position) -> void {
  assert(InLogicThread());
  mark_input_active();

  // Convert normalized view coords to our virtual ones.
  cursor_pos_x_ = g_graphics->PixelToVirtualX(
      position.x * g_graphics->screen_pixel_width());
  cursor_pos_y_ = g_graphics->PixelToVirtualY(
      position.y * g_graphics->screen_pixel_height());

  bool handled2{};

  // If we have a touch-input in editing mode, pass along events to it.
  // (it usually handles its own events but here we want it to play nice
  // with stuff under it by blocking touches, etc)
  if (touch_input_ && touch_input_->editing()) {
    touch_input_->HandleTouchUp(reinterpret_cast<void*>(1), cursor_pos_x_,
                                cursor_pos_y_);
  }

  Widget* root_widget = g_ui->root_widget();
  if (root_widget)
    handled2 = root_widget->HandleMessage(WidgetMessage(
        WidgetMessage::Type::kMouseUp, nullptr, cursor_pos_x_, cursor_pos_y_));
  Camera* camera = g_graphics->camera();
  if (!handled2 && camera) {
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
  g_ui->root_ui()->HandleMouseButtonUp(cursor_pos_x_, cursor_pos_y_);
}

void Input::PushTouchEvent(const TouchEvent& e) {
  g_logic->thread()->PushCall([e, this] { HandleTouchEvent(e); });
}

void Input::HandleTouchEvent(const TouchEvent& e) {
  assert(InLogicThread());
  assert(g_graphics);

  if (IsInputLocked()) {
    return;
  }

  mark_input_active();

  // float x = e.x;
  // float y = e.y;

  if (g_buildconfig.ostype_ios_tvos()) {
    printf("FIXME: update touch handling\n");
  }

  float x = g_graphics->PixelToVirtualX(e.x * g_graphics->screen_pixel_width());
  float y =
      g_graphics->PixelToVirtualY(e.y * g_graphics->screen_pixel_height());

  if (e.overall) {
    // Sanity test: if the OS tells us that this is the beginning of an,
    // overall multitouch gesture, it should always be winding up as our
    // single_touch_.
    if (e.type == TouchEvent::Type::kDown && single_touch_ != nullptr) {
      BA_LOG_ONCE(LogLevel::kError,
                  "Got touch labeled first but will not be our single.");
    }

    // Also: if the OS tells us that this is the end of an overall multi-touch
    // gesture, it should mean that our single_touch_ has ended or will be.
    if ((e.type == TouchEvent::Type::kUp
         || e.type == TouchEvent::Type::kCanceled)
        && single_touch_ != nullptr && single_touch_ != e.touch) {
      BA_LOG_ONCE(LogLevel::kError,
                  "Last touch coming up is not single touch!");
    }
  }

  // We keep track of one 'single' touch which we pass along as
  // mouse events which covers most UI stuff.
  if (e.type == TouchEvent::Type::kDown && single_touch_ == nullptr) {
    single_touch_ = e.touch;
    HandleMouseDown(SDL_BUTTON_LEFT, Vector2f(e.x, e.y));
  }

  if (e.type == TouchEvent::Type::kMoved && e.touch == single_touch_) {
    HandleMouseMotion(Vector2f(e.x, e.y));
  }

  // Currently just applying touch-cancel the same as touch-up here;
  // perhaps should be smarter in the future.
  if ((e.type == TouchEvent::Type::kUp || e.type == TouchEvent::Type::kCanceled)
      && (e.touch == single_touch_ || e.overall)) {
    single_touch_ = nullptr;
    HandleMouseUp(SDL_BUTTON_LEFT, Vector2f(e.x, e.y));
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
  assert(InLogicThread());
  if (!HeadlessMode()) {
    // Synthesize key-ups for all our held keys.
    while (!keys_held_.empty()) {
      SDL_Keysym k;
      memset(&k, 0, sizeof(k));
      k.sym = (SDL_Keycode)(*keys_held_.begin());
      HandleKeyRelease(&k);
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
  assert(InLogicThread());
  if (!g_ui) {
    return false;
  }
  ContainerWidget* screen_root_widget = g_ui->screen_root_widget();

  // Keeps mouse hidden to start with..
  if (mouse_move_count_ < 2) {
    return false;
  }
  bool val;

  // Show our cursor if any dialogs/windows are up or else if its been
  // moved very recently.
  if (screen_root_widget && screen_root_widget->GetChildCount() > 0) {
    val = (GetRealTime() - last_mouse_move_time_ < 5000);
  } else {
    val = (GetRealTime() - last_mouse_move_time_ < 1000);
  }
  return val;
}

// The following was pulled from sdl2
#if BA_SDL2_BUILD || BA_MINSDL_BUILD

#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

static char* UCS4ToUTF8(uint32_t ch, char* dst) {
  auto* p = reinterpret_cast<uint8_t*>(dst);
  if (ch <= 0x7F) {
    *p = static_cast<uint8_t>(ch);
    ++dst;
  } else if (ch <= 0x7FF) {
    p[0] = static_cast<uint8_t>(0xC0 | static_cast<uint8_t>((ch >> 6) & 0x1F));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 2;
  } else if (ch <= 0xFFFF) {
    p[0] = static_cast<uint8_t>(0xE0 | static_cast<uint8_t>((ch >> 12) & 0x0F));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 3;
  } else if (ch <= 0x1FFFFF) {
    p[0] = static_cast<uint8_t>(0xF0 | static_cast<uint8_t>((ch >> 18) & 0x07));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 12) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[3] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 4;
  } else if (ch <= 0x3FFFFFF) {
    p[0] = static_cast<uint8_t>(0xF8 | static_cast<uint8_t>((ch >> 24) & 0x03));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 18) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 12) & 0x3F));
    p[3] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[4] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 5;
  } else {
    p[0] = static_cast<uint8_t>(0xFC | static_cast<uint8_t>((ch >> 30) & 0x01));
    p[1] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 24) & 0x3F));
    p[2] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 18) & 0x3F));
    p[3] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 12) & 0x3F));
    p[4] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>((ch >> 6) & 0x3F));
    p[5] = static_cast<uint8_t>(0x80 | static_cast<uint8_t>(ch & 0x3F));
    dst += 6;
  }
  return dst;
}
#pragma clang diagnostic pop

const char* GetScancodeName(SDL_Scancode scancode) {
  const char* name;
  if (static_cast<int>(scancode) < SDL_SCANCODE_UNKNOWN
      || scancode >= SDL_NUM_SCANCODES) {
    BA_LOG_ONCE(LogLevel::kError,
                "GetScancodeName passed invalid scancode "
                    + std::to_string(static_cast<int>(scancode)));
    return "";
  }

  name = scancode_names[scancode];
  if (name)
    return name;
  else
    return "";
}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
auto Input::GetKeyName(int keycode) -> std::string {
  SDL_Keycode key{keycode};
  static char name[8];
  char* end;

  if (key & SDLK_SCANCODE_MASK) {
    return GetScancodeName((SDL_Scancode)(key & ~SDLK_SCANCODE_MASK));
  }

  switch (key) {
    case SDLK_RETURN:
      return GetScancodeName(SDL_SCANCODE_RETURN);
    case SDLK_ESCAPE:
      return GetScancodeName(SDL_SCANCODE_ESCAPE);
    case SDLK_BACKSPACE:
      return GetScancodeName(SDL_SCANCODE_BACKSPACE);
    case SDLK_TAB:
      return GetScancodeName(SDL_SCANCODE_TAB);
    case SDLK_SPACE:
      return GetScancodeName(SDL_SCANCODE_SPACE);
    case SDLK_DELETE:
      return GetScancodeName(SDL_SCANCODE_DELETE);
    default:
      /* Unaccented letter keys on latin keyboards are normally
         labeled in upper case (and probably on others like Greek or
         Cyrillic too, so if you happen to know for sure, please
         adapt this). */
      if (key >= 'a' && key <= 'z') {
        key -= 32;
      }

      end = UCS4ToUTF8(static_cast<uint32_t>(key), name);
      *end = '\0';
      return name;
  }
}
#pragma clang diagnostic pop
#endif  // BA_SDL2_BUILD || BA_MINSDL_BUILD

}  // namespace ballistica
