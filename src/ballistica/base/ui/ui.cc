// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/ui.h"

#include "ballistica/base/app/app_config.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/ui/console.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/support/root_ui.h"
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

  root_ui_ = g_base->ui_v1()->NewRootUI();

  // Make sure we know when forced-ui-scale is enabled.
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

void UI::PushBackButtonCall(InputDevice* input_device) {
  g_base->logic->event_loop()->PushCall([this, input_device] {
    assert(g_base->InLogicThread());

    // Ignore if UI isn't up yet.
    if (!overlay_root_widget() || !screen_root_widget()) {
      return;
    }

    // If there's a UI up, send along a cancel message.
    if (overlay_root_widget()->GetChildCount() != 0
        || screen_root_widget()->GetChildCount() != 0) {
      root_widget()->HandleMessage(WidgetMessage(WidgetMessage::Type::kCancel));
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

auto UI::IsWindowPresent() const -> bool {
  return ((screen_root_widget_.Exists() && screen_root_widget_->HasChildren())
          || (overlay_root_widget_.Exists()
              && overlay_root_widget_->HasChildren()));
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
  // Hmm; technically we don't need to recreate these each time we reset.
  root_widget_.Clear();

  // Kill our screen-root widget.
  screen_root_widget_.Clear();

  // (Re)create our screen-root widget.
  auto sw(Object::New<ui_v1::StackWidget>());
  sw->set_is_main_window_stack(true);
  sw->SetWidth(g_base->graphics->screen_virtual_width());
  sw->SetHeight(g_base->graphics->screen_virtual_height());
  sw->set_translate(0, 0);
  screen_root_widget_ = sw;

  // (Re)create our screen-overlay widget.
  auto ow(Object::New<ui_v1::StackWidget>());
  ow->set_is_overlay_window_stack(true);
  ow->SetWidth(g_base->graphics->screen_virtual_width());
  ow->SetHeight(g_base->graphics->screen_virtual_height());
  ow->set_translate(0, 0);
  overlay_root_widget_ = ow;

  // (Re)create our abs-root widget.
  auto rw(Object::New<ui_v1::RootWidget>());
  root_widget_ = rw;
  rw->SetWidth(g_base->graphics->screen_virtual_width());
  rw->SetHeight(g_base->graphics->screen_virtual_height());
  rw->SetScreenWidget(sw.Get());
  rw->Setup();
  rw->SetOverlayWidget(ow.Get());

  sw->GlobalSelect();
}

auto UI::ShouldHighlightWidgets() const -> bool {
  // Show selection highlights only if we've got controllers connected and only
  // when the main UI is visible (dont want a selection highlight for toolbar
  // buttons during a game).
  return (
      g_base->input->have_non_touch_inputs()
      && ((screen_root_widget_.Exists() && screen_root_widget_->HasChildren())
          || (overlay_root_widget_.Exists()
              && overlay_root_widget_->HasChildren())));
}

auto UI::ShouldShowButtonShortcuts() const -> bool {
  return g_base->input->have_non_touch_inputs();
}

void UI::AddWidget(ui_v1::Widget* w, ui_v1::ContainerWidget* parent) {
  assert(g_base->InLogicThread());

  BA_PRECONDITION(parent != nullptr);

  // If they're adding an initial window/dialog to our screen-stack
  // or overlay stack, send a reset-local-input message so that characters
  // who have lost focus will not get stuck running or whatnot.
  // We should come up with a more generalized way to track this sort of
  // focus as this is a bit hacky, but it works for now.
  auto* screen_root_widget = screen_root_widget_.Get();
  auto* overlay_root_widget = overlay_root_widget_.Get();
  if ((screen_root_widget && !screen_root_widget->HasChildren()
       && parent == screen_root_widget)
      || (overlay_root_widget && !overlay_root_widget->HasChildren()
          && parent == overlay_root_widget)) {
    g_base->input->ResetHoldStates();
  }

  parent->AddWidget(w);
}

auto UI::SendWidgetMessage(const WidgetMessage& m) -> int {
  if (!root_widget_.Exists()) {
    return false;
  }
  return root_widget_->HandleMessage(m);
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
  if (root_widget_.Exists()) {
    root_widget_->SetWidth(g_base->graphics->screen_virtual_width());
    root_widget_->SetHeight(g_base->graphics->screen_virtual_height());
  }
}

void UI::LanguageChanged() {
  // As well as existing UI stuff.
  if (ui_v1::Widget* root_widget = g_base->ui->root_widget()) {
    root_widget->OnLanguageChange();
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
  if ((!screen_root_widget_.Exists() || (!screen_root_widget_->HasChildren()))
      && (!overlay_root_widget_.Exists()
          || (!overlay_root_widget_->HasChildren()))) {
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

  if ((GetUIInputDevice() == nullptr) || (input_device == GetUIInputDevice())
      || (time - last_input_device_use_time_ > (1000 * kUIOwnerTimeoutSeconds))
      || !g_base->input->HaveManyLocalActiveInputDevices()) {
    // Don't actually assign yet; only update times and owners if there's a
    // widget to be had (we don't want some guy who moved his character 3
    // seconds ago to automatically own a newly created widget).
    last_input_device_use_time_ = time;
    ui_input_device_ = input_device;
    ret_val = screen_root_widget_.Get();
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
  RenderPass* overlay_flat_pass = frame_def->GetOverlayFlatPass();

  // Draw interface elements.
  auto* root_widget = root_widget_.Get();

  if (root_widget && root_widget->HasChildren()) {
    // Draw our opaque and transparent parts separately.
    // This way we can draw front-to-back for opaque and back-to-front for
    // transparent.

    g_base->graphics->set_drawing_opaque_only(true);

    // Do a wee bit of shifting based on tilt just for fun.
    Vector3f tilt = 0.1f * g_base->graphics->tilt();
    {
      EmptyComponent c(overlay_flat_pass);
      c.SetTransparent(false);
      c.PushTransform();
      c.Translate(-tilt.y, tilt.x, -0.5f);

      // We want our widgets to cover 0.1f in z space.
      c.Scale(1.0f, 1.0f, 0.1f);
      c.Submit();
      root_widget->Draw(overlay_flat_pass, false);
      c.PopTransform();
      c.Submit();
    }

    g_base->graphics->set_drawing_opaque_only(false);
    g_base->graphics->set_drawing_transparent_only(true);

    {
      EmptyComponent c(overlay_flat_pass);
      c.SetTransparent(true);
      c.PushTransform();
      c.Translate(-tilt.y, tilt.x, -0.5f);

      // We want our widgets to cover 0.1f in z space.
      c.Scale(1.0f, 1.0f, 0.1f);
      c.Submit();
      root_widget->Draw(overlay_flat_pass, true);
      c.PopTransform();
      c.Submit();
    }

    g_base->graphics->set_drawing_transparent_only(false);
  }
  if (root_ui_) {
    root_ui_->Draw(frame_def);
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
