// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/ui.h"

#include "ballistica/base/app/app_config.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/ui/console.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/ui_v1/widget/root_widget.h"
#include "ballistica/ui_v1/widget/stack_widget.h"
#include "ballistica/ui_v1/widget/text_widget.h"

namespace ballistica::base {

static const int kUIOwnerTimeoutSeconds = 30;

UI::UI() {
  // Figure out our interface type.
  assert(g_core);

  // Allow overriding via an environment variable.
  auto* ui_override = getenv("BA_UI_SCALE");
  if (ui_override) {
    if (ui_override == std::string("small")) {
      scale_ = UIScale::kSmall;
      force_scale_ = true;
    } else if (ui_override == std::string("medium")) {
      scale_ = UIScale::kMedium;
      force_scale_ = true;
    } else if (ui_override == std::string("large")) {
      scale_ = UIScale::kLarge;
      force_scale_ = true;
    }
  }
  if (!force_scale_) {
    // Use automatic val.
    if (g_buildconfig.iircade_build()) {  // NOLINT(bugprone-branch-clone)
      scale_ = UIScale::kMedium;
    } else if (g_core->IsVRMode() || g_core->platform->IsRunningOnTV()) {
      // VR and tv builds always use medium.
      scale_ = UIScale::kMedium;
    } else {
      scale_ = g_core->platform->GetUIScale();
    }
  }
}

void UI::StepDisplayTime() { assert(g_base->InLogicThread()); }

void UI::OnAppStart() {
  assert(g_base->InLogicThread());

  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->OnAppStart();
  }

  // Make sure user knows when forced-ui-scale is enabled.
  if (force_scale_) {
    if (scale_ == UIScale::kSmall) {
      ScreenMessage("FORCING SMALL UI FOR TESTING", Vector3f(1, 0, 0));
      Log(LogLevel::kInfo, "FORCING SMALL UI FOR TESTING");
    } else if (scale_ == UIScale::kMedium) {
      ScreenMessage("FORCING MEDIUM UI FOR TESTING", Vector3f(1, 0, 0));
      Log(LogLevel::kInfo, "FORCING MEDIUM UI FOR TESTING");
    } else if (scale_ == UIScale::kLarge) {
      ScreenMessage("FORCING LARGE UI FOR TESTING", Vector3f(1, 0, 0));
      Log(LogLevel::kInfo, "FORCING LARGE UI FOR TESTING");
    } else {
      FatalError("Unhandled scale.");
    }
  }
}

void UI::OnAppPause() { assert(g_base->InLogicThread()); }

void UI::OnAppResume() {
  assert(g_base->InLogicThread());
  SetUIInputDevice(nullptr);
}

void UI::OnAppShutdown() { assert(g_base->InLogicThread()); }

void UI::ApplyAppConfig() {
  assert(g_base->InLogicThread());
  ui_v1::TextWidget::set_always_use_internal_keyboard(
      g_base->app_config->Resolve(
          AppConfig::BoolID::kAlwaysUseInternalKeyboard));
}

auto UI::MainMenuVisible() const -> bool {
  if (g_base->HaveUIV1()) {
    return g_base->ui_v1()->MainMenuVisible();
  }
  return false;
}

// FIXME should be same as MainMenuVisible.
// auto UI::IsWindowPresent() const -> bool {
//  return ((screen_root_widget_.Exists() && screen_root_widget_->HasChildren())
//          || (overlay_root_widget_.Exists()
//              && overlay_root_widget_->HasChildren()));
//}

auto UI::PartyIconVisible() -> bool {
  if (g_base->HaveUIV1()) {
    return g_base->ui_v1()->PartyIconVisible();
  }
  return false;
}

void UI::ActivatePartyIcon() {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->ActivatePartyIcon();
  }
}

auto UI::PartyWindowOpen() -> bool {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->PartyWindowOpen();
  }
  return false;
}

void UI::HandleLegacyRootUIMouseMotion(float x, float y) {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->HandleLegacyRootUIMouseMotion(x, y);
  }
}

auto UI::HandleLegacyRootUIMouseDown(float x, float y) -> bool {
  if (g_base->HaveUIV1()) {
    return g_base->ui_v1()->HandleLegacyRootUIMouseDown(x, y);
  }
  return false;
}

void UI::HandleLegacyRootUIMouseUp(float x, float y) {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->HandleLegacyRootUIMouseUp(x, y);
  }
}

void UI::PushBackButtonCall(InputDevice* input_device) {
  g_base->logic->event_loop()->PushCall([this, input_device] {
    assert(g_base->InLogicThread());

    // If there's a UI up, send along a cancel message.
    if (g_base->ui->MainMenuVisible()) {
      g_base->ui->SendWidgetMessage(
          WidgetMessage(WidgetMessage::Type::kCancel));
    } else {
      // If there's no main screen or overlay windows, ask for a menu owned by
      // this device.
      MainMenuPress(input_device);
    }
  });
}

void UI::PushMainMenuPressCall(InputDevice* device) {
  g_base->logic->event_loop()->PushCall(
      [this, device] { MainMenuPress(device); });
}

void UI::MainMenuPress(InputDevice* device) {
  assert(g_base->InLogicThread());
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->DoHandleDeviceMenuPress(device);
  } else {
    Log(LogLevel::kWarning,
        "UI::MainMenuPress called without ui_v1 present; unexpected.");
  }
}

void UI::SetUIInputDevice(InputDevice* input_device) {
  assert(g_base->InLogicThread());

  ui_input_device_ = input_device;

  // So they dont get stolen from immediately.
  last_input_device_use_time_ = g_core->GetAppTimeMillisecs();
}

UI::UILock::UILock(bool write) {
  assert(g_base->ui);
  assert(g_base->InLogicThread());

  if (write && g_base->ui->ui_lock_count_ != 0) {
    BA_LOG_ERROR_TRACE_ONCE("Illegal operation: UI is locked");
  }
  g_base->ui->ui_lock_count_++;
}

UI::UILock::~UILock() {
  g_base->ui->ui_lock_count_--;
  if (g_base->ui->ui_lock_count_ < 0) {
    BA_LOG_ERROR_TRACE_ONCE("ui_lock_count_ < 0");
    g_base->ui->ui_lock_count_ = 0;
  }
}

void UI::Reset() {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->Reset();
  }
}

auto UI::ShouldHighlightWidgets() const -> bool {
  // Show selection highlights only if we've got controllers connected and only
  // when the main UI is visible (dont want a selection highlight for toolbar
  // buttons during a game).
  return (g_base->input->have_non_touch_inputs() && MainMenuVisible());
}

auto UI::ShouldShowButtonShortcuts() const -> bool {
  return g_base->input->have_non_touch_inputs();
}

auto UI::SendWidgetMessage(const WidgetMessage& m) -> int {
  if (g_base->HaveUIV1()) {
    return g_base->ui_v1()->SendWidgetMessage(m);
  }
  return false;
}

void UI::DeleteWidget(ui_v1::Widget* widget) {
  assert(widget);
  if (widget) {
    ui_v1::ContainerWidget* parent = widget->parent_widget();
    if (parent) {
      parent->DeleteWidget(widget);
    }
  }
}

void UI::OnScreenSizeChange() {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->OnScreenSizeChange();
  }
}

void UI::LanguageChanged() {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->OnLanguageChange();
  }
}

auto UI::GetUIInputDevice() const -> InputDevice* {
  assert(g_base->InLogicThread());
  return ui_input_device_.Get();
}

auto UI::GetWidgetForInput(InputDevice* input_device) -> ui_v1::Widget* {
  assert(input_device);
  assert(g_base->InLogicThread());

  // We only allow input-devices to control the UI when there's a window/dialog
  // on the screen (even though our top/bottom bars still exist).
  if (!MainMenuVisible()) {
    return nullptr;
  }

  millisecs_t time = g_core->GetAppTimeMillisecs();

  bool print_menu_owner = false;
  ui_v1::Widget* ret_val;

  // Ok here's the deal:
  // Because having 10 controllers attached to the UI is pure chaos,
  // we only allow one input device at a time to control the menu.
  // However, if no events are received by that device for a long time,
  // it is up for grabs to the next device that requests it.

  if (!g_base->HaveUIV1()) {
    ret_val = nullptr;
  } else if ((GetUIInputDevice() == nullptr)
             || (input_device == GetUIInputDevice())
             || (time - last_input_device_use_time_
                 > (1000 * kUIOwnerTimeoutSeconds))
             || !g_base->input->HaveManyLocalActiveInputDevices()) {
    // Don't actually assign yet; only update times and owners if there's a
    // widget to be had (we don't want some guy who moved his character 3
    // seconds ago to automatically own a newly created widget).
    last_input_device_use_time_ = time;
    ui_input_device_ = input_device;
    // ret_val = screen_root_widget_.Get();
    ret_val = g_base->ui_v1()->GetRootWidget();
  } else {
    // For rejected input devices, play error sounds sometimes so they know
    // they're not the chosen one.
    if (time - last_widget_input_reject_err_sound_time_ > 5000) {
      last_widget_input_reject_err_sound_time_ = time;
      g_base->audio->PlaySound(
          g_base->assets->SysSound(SysSoundID::kErrorBeep));
      print_menu_owner = true;
    }
    ret_val = nullptr;  // Rejected!
  }

  if (print_menu_owner) {
    InputDevice* input = GetUIInputDevice();

    if (input) {
      millisecs_t timeout =
          kUIOwnerTimeoutSeconds - (time - last_input_device_use_time_) / 1000;
      std::string time_out_str;
      if (timeout > 0 && timeout < (kUIOwnerTimeoutSeconds - 10)) {
        time_out_str = " " + g_base->assets->GetResourceString("timeOutText");
        Utils::StringReplaceOne(&time_out_str, "${TIME}",
                                std::to_string(timeout));
      } else {
        time_out_str =
            " " + g_base->assets->GetResourceString("willTimeOutText");
      }

      std::string name;
      if (input->GetDeviceName() == "Keyboard") {
        name = g_base->assets->GetResourceString("keyboardText");
      } else if (input->GetDeviceName() == "TouchScreen") {
        name = g_base->assets->GetResourceString("touchScreenText");
      } else {
        // We used to use player names here, but that's kinda sloppy and random;
        // lets just go with device names/numbers.
        auto devicesWithName =
            g_base->input->GetInputDevicesWithName(input->GetDeviceName());
        if (devicesWithName.size() == 1) {
          // If there's just one, no need to tack on the '#2' or whatever.
          name = input->GetDeviceName();
        } else {
          name =
              input->GetDeviceName() + " " + input->GetPersistentIdentifier();
        }
      }

      std::string b = g_base->assets->GetResourceString("hasMenuControlText");
      Utils::StringReplaceOne(&b, "${NAME}", name);
      ScreenMessage(b + time_out_str, {0.45f, 0.4f, 0.5f});
    }
  }
  return ret_val;
}

void UI::Draw(FrameDef* frame_def) {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->Draw(frame_def);
  }
}

void UI::ShowURL(const std::string& url) {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->DoShowURL(url);
  } else {
    Log(LogLevel::kWarning,
        "UI::ShowURL called without g_ui_v1_soft present; unexpected.");
  }
}

void UI::ConfirmQuit() {
  g_base->logic->event_loop()->PushCall([] {
    assert(g_base->InLogicThread());
    if (g_core->HeadlessMode()) {
      Log(LogLevel::kError, "UI::ConfirmQuit() unhandled on headless.");
    } else {
      // If input is locked or the in-app-console is up or we don't have ui-v1,
      // just quit immediately; a confirm screen wouldn't work anyway.
      if (g_base->input->IsInputLocked() || !g_base->HaveUIV1()
          || (g_base->console() != nullptr && g_base->console()->active())) {
        // Just go through _babase.quit().
        // FIXME: Shouldn't need to go out to the Python layer here;
        //  once we've got a high level quit call in platform we can use
        //  that directly.
        g_base->python->objs().Get(BasePython::ObjID::kQuitCall).Call();
        return;
      } else {
        ScopedSetContext ssc(nullptr);
        g_base->audio->PlaySound(g_base->assets->SysSound(SysSoundID::kSwish));
        g_base->ui_v1()->DoQuitWindow();

        // If we have a keyboard, give it UI ownership.
        InputDevice* keyboard = g_base->input->keyboard_input();
        if (keyboard) {
          g_base->ui->SetUIInputDevice(keyboard);
        }
      }
    }
  });
}

}  // namespace ballistica::base
