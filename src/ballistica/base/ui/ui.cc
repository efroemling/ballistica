// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/ui.h"

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/support/ui_v1_soft.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/inline.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

static const int kUIOwnerTimeoutSeconds = 30;

UI::UI() {
  assert(g_core);

  // Figure out our interface scale.

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
    if (g_core->IsVRMode() || g_core->platform->IsRunningOnTV()) {
      // VR and TV modes always use medium.
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

void UI::DoApplyAppConfig() {
  assert(g_base->InLogicThread());
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->DoApplyAppConfig();
  }
  show_dev_console_button_ =
      g_base->app_config->Resolve(AppConfig::BoolID::kShowDevConsoleButton);
}

auto UI::MainMenuVisible() const -> bool {
  if (g_base->HaveUIV1()) {
    return g_base->ui_v1()->MainMenuVisible();
  }
  return false;
}

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
    return g_base->ui_v1()->PartyWindowOpen();
  }
  return false;
}

auto UI::HandleMouseDown(int button, float x, float y, bool double_click)
    -> bool {
  bool handled{};

  if (show_dev_console_button_ && button == 1) {
    float vx = g_base->graphics->screen_virtual_width();
    float vy = g_base->graphics->screen_virtual_height();
    if (InDevConsoleButton_(x, y)) {
      dev_console_button_pressed_ = true;
    }
  }

  if (!handled && g_base->HaveUIV1()) {
    handled = g_base->ui_v1()->HandleLegacyRootUIMouseDown(x, y);
  }

  if (!handled) {
    handled = SendWidgetMessage(WidgetMessage(
        WidgetMessage::Type::kMouseDown, nullptr, x, y, double_click ? 2 : 1));
  }

  return handled;
}

void UI::HandleMouseUp(int button, float x, float y) {
  assert(g_base->InLogicThread());

  SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseUp, nullptr, x, y));

  if (dev_console_button_pressed_) {
    if (InDevConsoleButton_(x, y)) {
      if (auto* console = g_base->console()) {
        console->ToggleState();
      }
    }
    dev_console_button_pressed_ = false;
  }

  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->HandleLegacyRootUIMouseUp(x, y);
  }
}

void UI::HandleMouseMotion(float x, float y) {
  SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseMove, nullptr, x, y));

  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->HandleLegacyRootUIMouseMotion(x, y);
  }
}

void UI::PushBackButtonCall(InputDevice* input_device) {
  g_base->logic->event_loop()->PushCall([this, input_device] {
    assert(g_base->InLogicThread());

    // If there's a UI up, send along a cancel message.
    if (MainMenuVisible()) {
      SendWidgetMessage(WidgetMessage(WidgetMessage::Type::kCancel));
    } else {
      // If there's no main screen or overlay windows, ask for a menu owned
      // by this device.
      MainMenuPress_(input_device);
    }
  });
}

void UI::PushMainMenuPressCall(InputDevice* device) {
  g_base->logic->event_loop()->PushCall(
      [this, device] { MainMenuPress_(device); });
}

void UI::MainMenuPress_(InputDevice* device) {
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

void UI::Reset() {
  if (g_base->HaveUIV1()) {
    g_base->ui_v1()->Reset();
  }
}

auto UI::ShouldHighlightWidgets() const -> bool {
  // Show selection highlights only if we've got controllers connected and
  // only when the main UI is visible (dont want a selection highlight for
  // toolbar buttons during a game).
  return g_base->input->have_non_touch_inputs() && MainMenuVisible();
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

  // We only allow input-devices to control the UI when there's a
  // window/dialog on the screen (even though our top/bottom bars still
  // exist).
  if (!MainMenuVisible()) {
    return nullptr;
  }

  millisecs_t time = g_core->GetAppTimeMillisecs();

  bool print_menu_owner{};
  ui_v1::Widget* ret_val;

  // Ok here's the deal:
  //
  // Because having 10 controllers attached to the UI is pure chaos, we only
  // allow one input device at a time to control the menu. However, if no
  // events are received by that device for a long time, it is up for grabs
  // to the next device that requests it.

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
        // We used to use player names here, but that's kinda sloppy and
        // random; lets just go with device names/numbers.
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

void UI::DrawDev(FrameDef* frame_def) {
  // Draw dev console.
  if (g_base->console()) {
    g_base->console()->Draw(frame_def->overlay_pass());
  }

  // Draw dev console button.
  if (show_dev_console_button_) {
    DrawDevConsoleButton_(frame_def);
  }
}

auto UI::DevConsoleButtonSize_() const -> float {
  switch (scale_) {
    case UIScale::kLarge:
      return 25.0f;
    case UIScale::kMedium:
      return 40.0f;
    case UIScale::kSmall:
    case UIScale::kLast:
      return 60.0f;
  }
}

auto UI::InDevConsoleButton_(float x, float y) const -> bool {
  float vwidth = g_base->graphics->screen_virtual_width();
  float vheight = g_base->graphics->screen_virtual_height();
  float bsz = DevConsoleButtonSize_();
  float bszh = bsz * 0.5f;
  float centerx = vwidth - bsz * 0.5f;
  float centery = vheight * 0.5f;
  float diffx = ::std::abs(centerx - x);
  float diffy = ::std::abs(centery - y);
  return diffx <= bszh && diffy <= bszh;
}

void UI::DrawDevConsoleButton_(FrameDef* frame_def) {
  if (!dev_console_button_txt_.Exists()) {
    dev_console_button_txt_ = Object::New<TextGroup>();
    dev_console_button_txt_->set_text("dev");
  }
  auto& grp(*dev_console_button_txt_);
  float vwidth = g_base->graphics->screen_virtual_width();
  float vheight = g_base->graphics->screen_virtual_height();
  float bsz = DevConsoleButtonSize_();

  SimpleComponent c(frame_def->overlay_pass());
  c.SetTransparent(true);
  c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCircleShadow));
  if (dev_console_button_pressed_) {
    c.SetColor(1.0f, 1.0f, 1.0f, 0.8f);
  } else {
    c.SetColor(0.5f, 0.5f, 0.5f, 0.8f);
  }
  {
    auto xf = c.ScopedTransform();
    c.Translate(vwidth - bsz * 0.5f, vheight * 0.5f, kCursorZDepth - 0.01f);
    c.Scale(bsz, bsz, 1.0f);
    c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
    {
      auto xf = c.ScopedTransform();
      c.Scale(0.017f, 0.017f, 1.0f);
      c.Translate(-20.0f, -15.0f, 0.0f);
      int text_elem_count = grp.GetElementCount();
      if (dev_console_button_pressed_) {
        c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
      } else {
        c.SetColor(0.15f, 0.15f, 0.15f, 1.0f);
      }
      for (int e = 0; e < text_elem_count; e++) {
        c.SetTexture(grp.GetElementTexture(e));
        c.SetFlatness(0.0f);
        c.DrawMesh(grp.GetElementMesh(e));
      }
    }
  }
  c.Submit();
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
    // If the in-app console is active, dismiss it.
    if (g_base->console() != nullptr && g_base->console()->IsActive()) {
      g_base->console()->Dismiss();
    }

    assert(g_base->InLogicThread());
    // If we're headless or we don't have ui-v1, just quit immediately; a
    // confirm screen wouldn't work anyway.
    if (g_core->HeadlessMode() || g_base->input->IsInputLocked()
        || !g_base->HaveUIV1()) {
      g_base->QuitApp();
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
  });
}

}  // namespace ballistica::base
