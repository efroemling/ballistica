// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/ui.h"

#include <exception>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui_delegate.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/native_stack_trace.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

static const int kUIOwnerTimeoutSeconds = 30;

/// We use this to gather up runnables triggered by UI elements in response
/// to stuff happening (mouse clicks, elements being added or removed,
/// etc.). It's a bad idea to run such runnables immediately because they
/// might modify UI lists we're in the process of traversing. It's also a
/// bad idea to schedule such runnables in the event loop, because a
/// runnable may wish to modify the UI to prevent further runs from
/// happening and that won't work if multiple runnables can be scheduled
/// before the first runs. So our goldilocks approach here is to gather
/// all runnables that get scheduled as part of each operation and then
/// run them explicitly once we are safely out of any UI list traversal.
UI::OperationContext::OperationContext() {
  assert(g_base->InLogicThread());

  // Register ourself as current only if there is none.
  parent_ = g_base->ui->operation_context_;
  if (parent_ == nullptr) {
    g_base->ui->operation_context_ = this;
  }
}

UI::OperationContext::~OperationContext() {
  assert(g_base->InLogicThread());

  // If we registered ourself as the top level context, unregister.
  if (parent_ == nullptr) {
    assert(g_base->ui->operation_context_ == this);
    g_base->ui->operation_context_ = nullptr;
  } else {
    // If a context was set when we came into existence, it should
    // still be that same context when we go out of existence.
    assert(g_base->ui->operation_context_ == parent_);
    assert(runnables_.empty());
  }

  // Complain if our Finish() call was never run (unless we're being torn
  // down due to an exception).
  if (!ran_finish_ && !std::current_exception()) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE(
        "UI::InteractionContext_ being torn down without Complete called.");
  }

  // Our runnables are raw unmanaged pointers; need to explicitly kill them.
  // Finish generally clears these out as it goes, but there might be some
  // left in the case of exceptions or infinite loop breakouts.
  for (auto* ptr : runnables_) {
    delete ptr;
  }
}

void UI::OperationContext::AddRunnable(Runnable* runnable) {
  // This should only be getting called when we installed ourself as top
  // level context.
  assert(parent_ == nullptr);
  assert(Object::IsValidUnmanagedObject(runnable));
  runnables_.push_back(runnable);
}

/// Should be explicitly called at the end of the operation.
void UI::OperationContext::Finish() {
  assert(g_base->InLogicThread());
  assert(!ran_finish_);
  ran_finish_ = true;

  // Run pent up runnaables. It's possible that the payload of something
  // scheduled here will itself schedule something here, so we need to do
  // this in a loop (and watch for infinite ones).
  int cycle_count{};
  while (!runnables_.empty()) {
    std::vector<Runnable*> runnables;
    runnables.swap(runnables_);
    for (auto* runnable : runnables) {
      runnable->RunAndLogErrors();
      // Our runnables are raw unmanaged pointers; need to explicitly kill
      // them.
      delete runnable;
    }
    cycle_count += 1;
    if (cycle_count >= 10) {
      BA_LOG_ERROR_NATIVE_TRACE(
          "UIOperationCount cycle-count hit max; you probably have an infinite "
          "loop.");
      break;
    }
  }
}

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
    if (g_core->vr_mode() || g_core->platform->IsRunningOnTV()) {
      // VR and TV modes always use medium.
      scale_ = UIScale::kMedium;
    } else {
      scale_ = g_core->platform->GetDefaultUIScale();
    }
  }
}

void UI::StepDisplayTime() {
  assert(g_base->InLogicThread());
  if (dev_console_) {
    dev_console_->StepDisplayTime();
  }
}

void UI::OnAppStart() {
  assert(g_base->InLogicThread());

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

void UI::OnAppSuspend() { assert(g_base->InLogicThread()); }

void UI::OnAppUnsuspend() {
  assert(g_base->InLogicThread());
  SetUIInputDevice(nullptr);
}

void UI::OnAppShutdown() { assert(g_base->InLogicThread()); }
void UI::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }

void UI::DoApplyAppConfig() {
  assert(g_base->InLogicThread());
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->DoApplyAppConfig();
  }
  show_dev_console_button_ =
      g_base->app_config->Resolve(AppConfig::BoolID::kShowDevConsoleButton);
}

auto UI::MainMenuVisible() const -> bool {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    return ui_delegate->MainMenuVisible();
  }
  return false;
}

auto UI::PartyIconVisible() -> bool {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    return ui_delegate->PartyIconVisible();
  }
  return false;
}

void UI::ActivatePartyIcon() {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->ActivatePartyIcon();
  }
}

auto UI::PartyWindowOpen() -> bool {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    return ui_delegate->PartyWindowOpen();
  }
  return false;
}

auto UI::HandleMouseDown(int button, float x, float y, bool double_click)
    -> bool {
  assert(g_base->InLogicThread());

  bool handled{};

  // Dev console button.
  if (show_dev_console_button_) {
    if (InDevConsoleButton_(x, y)) {
      if (button == 1) {
        dev_console_button_pressed_ = true;
      }
      handled = true;
    }
  }

  // Dev console itself.
  if (!handled && dev_console_ && dev_console_->IsActive()) {
    handled = dev_console_->HandleMouseDown(button, x, y);
  }

  if (!handled) {
    if (auto* ui_delegate = g_base->ui->delegate()) {
      handled = ui_delegate->HandleLegacyRootUIMouseDown(x, y);
    }
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

  if (dev_console_) {
    dev_console_->HandleMouseUp(button, x, y);
  }

  if (dev_console_button_pressed_ && button == 1) {
    dev_console_button_pressed_ = false;
    if (InDevConsoleButton_(x, y)) {
      if (dev_console_) {
        dev_console_->ToggleState();
      }
    }
  }

  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->HandleLegacyRootUIMouseUp(x, y);
  }
}

auto UI::UIHasDirectKeyboardInput() const -> bool {
  // As a first gate, ask the app-adapter if it is providing keyboard
  // events at all.
  if (g_base->app_adapter->HasDirectKeyboardInput()) {
    // Ok, direct keyboard input is a thing.
    // Now let's also require the keyboard (or nothing) to be currently
    // driving the UI. If something like a game-controller is driving,
    // we'll probably want to pop up a controller-centric on-screen-keyboard
    // thingie instead.
    auto* ui_input_device = g_base->ui->GetUIInputDevice();
    if (auto* keyboard = g_base->input->keyboard_input()) {
      if (ui_input_device == keyboard || ui_input_device == nullptr) {
        return true;
      }
    }
  }
  return false;
}

void UI::HandleMouseMotion(float x, float y) {
  SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseMove, nullptr, x, y));

  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->HandleLegacyRootUIMouseMotion(x, y);
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
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->DoHandleDeviceMenuPress(device);
  }
}

void UI::SetUIInputDevice(InputDevice* input_device) {
  assert(g_base->InLogicThread());

  ui_input_device_ = input_device;

  // So they dont get stolen from immediately.
  last_input_device_use_time_ = g_core->GetAppTimeMillisecs();
}

void UI::Reset() {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->Reset();
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

auto UI::SendWidgetMessage(const WidgetMessage& m) -> bool {
  OperationContext operation_context;

  bool result;
  if (auto* ui_delegate = g_base->ui->delegate()) {
    result = ui_delegate->SendWidgetMessage(m);
  } else {
    result = false;
  }

  // Run anything we triggered.
  operation_context.Finish();

  return result;
}

void UI::OnScreenSizeChange() {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->OnScreenSizeChange();
  }
}

void UI::LanguageChanged() {
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->OnLanguageChange();
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

  auto* ui_delegate = g_base->ui->delegate();

  if (!ui_delegate) {
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
    ret_val = ui_delegate->GetRootWidget();
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
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->Draw(frame_def);
  }
}

void UI::DrawDev(FrameDef* frame_def) {
  // Draw dev console.
  if (dev_console_) {
    dev_console_->Draw(frame_def);
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
  return 60.0f;
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
    dev_console_button_txt_->SetText("dev");
  }
  auto& grp(*dev_console_button_txt_);
  float vwidth = g_base->graphics->screen_virtual_width();
  float vheight = g_base->graphics->screen_virtual_height();
  float bsz = DevConsoleButtonSize_();

  SimpleComponent c(frame_def->overlay_front_pass());
  c.SetTransparent(true);
  c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCircleShadow));
  if (dev_console_button_pressed_) {
    c.SetColor(1.0f, 1.0f, 1.0f, 0.8f);
  } else {
    c.SetColor(0.5f, 0.5f, 0.5f, 0.8f);
  }
  {
    auto xf = c.ScopedTransform();
    c.Translate(vwidth - bsz * 0.5f, vheight * 0.5f, kDevConsoleZDepth + 0.01f);
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
  if (auto* ui_delegate = g_base->ui->delegate()) {
    ui_delegate->DoShowURL(url);
  } else {
    Log(LogLevel::kWarning, "UI::ShowURL called without ui_delegate present.");
  }
}

void UI::set_ui_delegate(base::UIDelegateInterface* delegate) {
  assert(g_base->InLogicThread());

  if (delegate == delegate_) {
    return;
  }

  try {
    auto* old_delegate = delegate_;
    delegate_ = nullptr;
    if (old_delegate) {
      old_delegate->OnDeactivate();
    }
    delegate_ = delegate;
    if (delegate_) {
      delegate_->OnActivate();

      // Inform them that a few things changed, since they might have since
      // the last time they were active (these callbacks only go to the *active*
      // ui delegate).
      delegate_->DoApplyAppConfig();
      delegate_->OnScreenSizeChange();
      delegate_->OnLanguageChange();
    }
  } catch (const Exception& exc) {
    // Switching UI delegates is a big deal; don't try to continue if
    // something goes wrong.
    FatalError(std::string("Error setting native layer ui-delegate: ")
               + exc.what());
  }
}

void UI::PushDevConsolePrintCall(const std::string& msg) {
  // Completely ignore this stuff in headless mode.
  if (g_core->HeadlessMode()) {
    return;
  }
  // If our event loop AND console are up and running, ship it off to
  // be printed. Otherwise store it for the console to grab when it's ready.
  if (auto* event_loop = g_base->logic->event_loop()) {
    if (dev_console_ != nullptr) {
      event_loop->PushCall([this, msg] { dev_console_->Print(msg); });
      return;
    }
  }
  // Didn't send a print; store for later.
  dev_console_startup_messages_ += msg;
}

void UI::OnAssetsAvailable() {
  assert(g_base->InLogicThread());

  // Spin up the dev console.
  if (!g_core->HeadlessMode() && !g_buildconfig.demo_build()) {
    assert(dev_console_ == nullptr);
    dev_console_ = new DevConsole();

    // Print any messages that have built up.
    if (!dev_console_startup_messages_.empty()) {
      dev_console_->Print(dev_console_startup_messages_);
      dev_console_startup_messages_.clear();
    }
  }
}

void UI::PushUIOperationRunnable(Runnable* runnable) {
  assert(g_base->InLogicThread());

  if (operation_context_ != nullptr) {
    operation_context_->AddRunnable(runnable);
    return;
  }

  // For now, gracefully fall back to pushing an event if there's no current
  // operation. Once we've got any bugs cleared out, can leave this as just
  // an error log.

  auto trace = g_core->platform->GetNativeStackTrace();
  BA_LOG_ERROR_NATIVE_TRACE_ONCE(
      "UI::PushUIOperationRunnable() called outside of UI operation.");

  g_base->logic->event_loop()->PushRunnable(runnable);
}

auto UI::InUIOperation() -> bool {
  assert(g_base->InLogicThread());
  return operation_context_ != nullptr;
}

}  // namespace ballistica::base
