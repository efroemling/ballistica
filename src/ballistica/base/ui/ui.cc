// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/ui.h"

#include <exception>
#include <string>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/ui_delegate.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/vector4f.h"

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

  // Complain if our Finish() call was never run (unless it seems we're being
  // torn down as part of stack-unwinding due to an exception).
  if (!ran_finish_ && !std::uncaught_exceptions()) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE(
        "UI::InteractionContext_ being torn down without Finish() called.");
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

  // Run pent up runnables. It's possible that the payload of something
  // scheduled here will itself schedule something here, so we need to do
  // this in a loop (and watch for infinite ones).
  int cycle_count{};
  auto initial_runnable_count(runnables_.size());
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
    auto max_count = 10;
    if (cycle_count >= max_count) {
      auto current_runnable_count(runnables_.size());
      BA_LOG_ERROR_NATIVE_TRACE(
          "UIOperationCount cycle-count hit max " + std::to_string(max_count)
          + " (initial " + std::to_string(initial_runnable_count) + ", current "
          + std::to_string(current_runnable_count) + ");"
          + " you probably have an infinite loop.");
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
      uiscale_ = UIScale::kSmall;
      force_scale_ = true;
    } else if (ui_override == std::string("medium")) {
      uiscale_ = UIScale::kMedium;
      force_scale_ = true;
    } else if (ui_override == std::string("large")) {
      uiscale_ = UIScale::kLarge;
      force_scale_ = true;
    }
  }
  if (!force_scale_) {
    // Use automatic val.
    if (g_core->vr_mode() || g_core->platform->IsRunningOnTV()) {
      // VR and TV modes always use medium.
      uiscale_ = UIScale::kMedium;
    } else {
      uiscale_ = g_core->platform->GetDefaultUIScale();
    }
  }
}
void UI::SetUIScale(UIScale val) {
  BA_PRECONDITION(g_base->InLogicThread());
  uiscale_ = val;
  if (dev_console_ != nullptr) {
    dev_console_->OnUIScaleChanged();
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
    if (uiscale_ == UIScale::kSmall) {
      g_base->ScreenMessage("FORCING SMALL UI FOR TESTING", Vector3f(1, 0, 0));
      g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                           "FORCING SMALL UI FOR TESTING");
    } else if (uiscale_ == UIScale::kMedium) {
      g_base->ScreenMessage("FORCING MEDIUM UI FOR TESTING", Vector3f(1, 0, 0));
      g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                           "FORCING MEDIUM UI FOR TESTING");
    } else if (uiscale_ == UIScale::kLarge) {
      g_base->ScreenMessage("FORCING LARGE UI FOR TESTING", Vector3f(1, 0, 0));
      g_core->logging->Log(LogName::kBa, LogLevel::kInfo,
                           "FORCING LARGE UI FOR TESTING");
    } else {
      FatalError("Unhandled scale.");
    }
  }
}

void UI::OnAppSuspend() { assert(g_base->InLogicThread()); }

void UI::OnAppUnsuspend() {
  assert(g_base->InLogicThread());
  SetMainUIInputDevice(nullptr);
}

void UI::OnAppShutdown() { assert(g_base->InLogicThread()); }
void UI::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }

void UI::ApplyAppConfig() {
  assert(g_base->InLogicThread());
  if (auto* ui_delegate = delegate()) {
    ui_delegate->ApplyAppConfig();
  }
  show_dev_console_button_ =
      g_base->app_config->Resolve(AppConfig::BoolID::kShowDevConsoleButton);

  if (dev_console_) {
    dev_console_->ApplyAppConfig();
  }
}

auto UI::IsMainUIVisible() const -> bool {
  assert(g_base->InLogicThread());
  if (auto* ui_delegate = delegate()) {
    return ui_delegate->IsMainUIVisible();
  }
  return false;
}

auto UI::IsPartyIconVisible() -> bool {
  assert(g_base->InLogicThread());
  if (auto* ui_delegate = delegate()) {
    return ui_delegate->IsPartyIconVisible();
  }
  return false;
}

void UI::ActivatePartyIcon() {
  assert(g_base->InLogicThread());
  if (auto* ui_delegate = delegate()) {
    ui_delegate->ActivatePartyIcon();
  }
}

void UI::SetSquadSizeLabel(int val) {
  assert(g_base->InLogicThread());

  // No-op if this exactly matches what we already have.
  if (val == squad_size_label_) {
    return;
  }

  // Store the val so we'll have it for future delegates.
  squad_size_label_ = val;

  // Pass it to any current delegate.
  if (auto* ui_delegate = delegate()) {
    ui_delegate->SetSquadSizeLabel(squad_size_label_);
  }
}

void UI::SetAccountSignInState(bool signed_in, const std::string& name) {
  assert(g_base->InLogicThread());

  // No-op if this exactly matches what we already have.
  if (account_state_signed_in_ == signed_in && account_state_name_ == name) {
    return;
  }

  // Store the val so we'll have it for future delegates.
  account_state_signed_in_ = signed_in;
  account_state_name_ = name;

  // Pass it to any current delegate.
  if (auto* ui_delegate = delegate()) {
    ui_delegate->SetAccountSignInState(account_state_signed_in_,
                                       account_state_name_);
  }
}

auto UI::IsPartyWindowOpen() -> bool {
  if (auto* ui_delegate = delegate()) {
    return ui_delegate->IsPartyWindowOpen();
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
        dev_console_->CycleState();
      }
    }
  }
}

void UI::HandleMouseCancel(int button, float x, float y) {
  assert(g_base->InLogicThread());

  SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseCancel, nullptr, x, y));

  if (dev_console_) {
    dev_console_->HandleMouseUp(button, x, y);
  }

  if (dev_console_button_pressed_ && button == 1) {
    dev_console_button_pressed_ = false;
  }
}

auto UI::UIHasDirectKeyboardInput() const -> bool {
  // As a first gate, ask the app-adapter if it is providing keyboard events
  // at all.
  if (g_base->app_adapter->HasDirectKeyboardInput()) {
    // Ok, direct keyboard input is a thing. Let's also require the keyboard
    // (or nothing) to be currently driving the UI. If something like a
    // game-controller is driving, we'll probably want to pop up a
    // controller-centric on-screen-keyboard thingie instead.
    auto* main_ui_input_device = GetMainUIInputDevice();
    if (KeyboardInput* keyboard = g_base->input->keyboard_input()) {
      if (main_ui_input_device == keyboard || main_ui_input_device == nullptr) {
        return true;
      }
    }
  }
  return false;
}

void UI::HandleMouseMotion(float x, float y) {
  SendWidgetMessage(
      WidgetMessage(WidgetMessage::Type::kMouseMove, nullptr, x, y));
}

void UI::SetMainUIInputDevice(InputDevice* device) {
  assert(g_base->InLogicThread());

  if (device != main_ui_input_device_.get()) {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kDebug, [device] {
      return "Main UI InputDevice is now "
             + (device ? device->GetDeviceNameUnique() : "None") + ".";
    });
  }

  main_ui_input_device_ = device;

  // So they dont get stolen from immediately.
  last_main_ui_input_device_use_time_ = g_core->AppTimeMillisecs();
}

void UI::OnInputDeviceRemoved(InputDevice* input_device) {
  assert(input_device);
  assert(g_base->InLogicThread());

  // If this is the current ui input device, deregister it. This isn't
  // technically necessary but gives us a clean logging message that the
  // main ui input device is now None.
  if (main_ui_input_device_.get() == input_device) {
    SetMainUIInputDevice(nullptr);
  }
}

void UI::Reset() {
  assert(g_base->InLogicThread());
  // Deactivate any current delegate.
  if (auto* ui_delegate = delegate()) {
    SetUIDelegate(nullptr);
  }
}

auto UI::ShouldHighlightWidgets() const -> bool {
  // Show selection highlights only if we've got controllers connected and
  // only when the main UI is visible (dont want a selection highlight for
  // toolbar buttons during a game).
  return g_base->input->have_non_touch_inputs() && IsMainUIVisible();
}

auto UI::SendWidgetMessage(const WidgetMessage& m) -> bool {
  OperationContext operation_context;

  bool result;
  if (auto* ui_delegate = delegate()) {
    result = ui_delegate->SendWidgetMessage(m);
  } else {
    result = false;
  }

  // Run anything we triggered.
  operation_context.Finish();

  return result;
}

void UI::OnScreenSizeChange() {
  if (auto* ui_delegate = delegate()) {
    ui_delegate->OnScreenSizeChange();
  }
}

void UI::LanguageChanged() {
  if (auto* ui_delegate = delegate()) {
    ui_delegate->OnLanguageChange();
  }
}

auto UI::GetMainUIInputDevice() const -> InputDevice* {
  assert(g_base->InLogicThread());
  return main_ui_input_device_.get();
}

auto UI::RequestMainUIControl(InputDevice* input_device) -> bool {
  assert(input_device);
  assert(g_base->InLogicThread());

  // Only allow device control of the UI when main-ui is visible.
  if (!IsMainUIVisible()) {
    return false;
  }

  millisecs_t time = g_core->AppTimeMillisecs();

  bool print_ui_owner{};
  bool ret_val;

  // Ok here's the plan:
  //
  // Because having 10 controllers attached to the UI is pure chaos, we only
  // allow one input device at a time to control the main ui. However, if no
  // events are received by that device for a long time, it is up for grabs
  // to the next device that requests it.
  //
  // We also allow freely switching ui ownership if there's only a few
  // active input-devices (someone with a keyboard and game-controller
  // should be able to freely switch between the two, etc.)

  auto* ui_delegate = delegate();

  if (!ui_delegate) {
    ret_val = false;
  } else if ((GetMainUIInputDevice() == nullptr)
             || (input_device == GetMainUIInputDevice())
             || (time - last_main_ui_input_device_use_time_
                 > (1000 * kUIOwnerTimeoutSeconds))
             || !g_base->input->HaveManyLocalActiveInputDevices()) {
    SetMainUIInputDevice(input_device);
    ret_val = true;
  } else {
    // For rejected input devices, play error sounds sometimes so they know
    // they're not the chosen one.
    if (time - last_widget_input_reject_err_sound_time_ > 5000) {
      last_widget_input_reject_err_sound_time_ = time;
      g_base->audio->SafePlaySysSound(SysSoundID::kErrorBeep);
      print_ui_owner = true;
    }
    ret_val = false;  // Rejected!
  }

  if (print_ui_owner) {
    if (InputDevice* input = GetMainUIInputDevice()) {
      millisecs_t timeout =
          kUIOwnerTimeoutSeconds
          - (time - last_main_ui_input_device_use_time_) / 1000;
      std::string time_out_str;
      if (timeout > 0 && timeout < (kUIOwnerTimeoutSeconds - 10)) {
        time_out_str = " " + g_base->assets->GetResourceString("timeOutText");
        Utils::StringReplaceOne(&time_out_str, "${TIME}",
                                std::to_string(timeout));
      } else {
        time_out_str =
            " " + g_base->assets->GetResourceString("willTimeOutText");
      }

      std::string name{input->GetDeviceNamePretty()};

      std::string b = g_base->assets->GetResourceString("hasMenuControlText");
      Utils::StringReplaceOne(&b, "${NAME}", name);
      g_base->ScreenMessage(b + time_out_str, {0.45f, 0.4f, 0.5f});
    }
  }
  return ret_val;
}

void UI::Draw(FrameDef* frame_def) {
  if (auto* ui_delegate = delegate()) {
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

void UI::MenuPress(InputDevice* input_device) {
  BA_PRECONDITION_FATAL(g_base->InLogicThread());

  // Need to wrap passed pointer in a ref; otherwise it could die before
  // our pushed call runs.
  Object::Ref<InputDevice> input_device_ref;
  if (input_device) {
    input_device_ref = input_device;
  }

  g_base->logic->event_loop()->PushCall([this, input_device_ref] {
    // If there's a UI up, send along a cancel message.
    if (IsMainUIVisible()) {
      // Hmm; do we want to set UI ownership in this case?
      SendWidgetMessage(WidgetMessage(WidgetMessage::Type::kCancel));
    } else {
      // If there's no main screen or overlay windows, ask for a menu owned
      // by this device.
      RequestMainUI_(input_device_ref.get());
    }
  });
}

void UI::RequestMainUI(InputDevice* input_device) {
  BA_PRECONDITION_FATAL(g_base->InLogicThread());

  // Need to wrap passed pointer in a ref; otherwise it could die before our
  // pushed call runs.
  Object::Ref<InputDevice> input_device_ref;
  if (input_device) {
    input_device_ref = input_device;
  }

  g_base->logic->event_loop()->PushCall(
      [this, input_device_ref] { RequestMainUI_(input_device_ref.get()); });
}

void UI::RequestMainUI_(InputDevice* input_device) {
  assert(g_base->InLogicThread());

  // We're a no-op if a main ui is already up.
  if (IsMainUIVisible()) {
    return;
  }

  // Ok; we're (tentatively) bringing up a ui. First, register this device
  // as owning whatever ui may come up.
  SetMainUIInputDevice(input_device);

  // Ask the app-mode to give us whatever it considers a main ui to be.
  if (auto* app_mode = g_base->app_mode()) {
    app_mode->RequestMainUI();
  }
}

auto UI::DevConsoleButtonSize_() const -> float {
  switch (uiscale_) {
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
  if (!dev_console_button_txt_.exists()) {
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
  // We can be called from any thread but DoShowURL expects to be run in
  // the logic thread.
  g_base->logic->event_loop()->PushCall([this, url] {
    if (auto* ui_delegate = delegate()) {
      ui_delegate->DoShowURL(url);
    } else {
      g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                           "UI::ShowURL called without ui_delegate present.");
    }
  });
}

void UI::SetUIDelegate(base::UIDelegateInterface* delegate) {
  assert(g_base->InLogicThread());

  // We should always be either setting or clearing delegate; never setting
  // redundantly.
  if (delegate_) {
    if (delegate) {
      FatalError(
          "Can\'t set UI Delegate when one is already set. Reset base first.");
    }
  } else {
    if (!delegate) {
      FatalError("Can\'t clear UI Delegate when already cleared.");
    }
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

      // Push values to them and trigger various 'changed' callbacks so they
      // pick up the latest state of the world.
      delegate_->ApplyAppConfig();
      delegate_->OnScreenSizeChange();
      delegate_->OnLanguageChange();
      delegate_->SetSquadSizeLabel(squad_size_label_);
      delegate_->SetAccountSignInState(account_state_signed_in_,
                                       account_state_name_);
    }
  } catch (const Exception& exc) {
    // Switching UI delegates is a big deal; don't try to continue if
    // something goes wrong.
    FatalError(std::string("Error setting native layer ui-delegate: ")
               + exc.what());
  }
}

void UI::PushDevConsolePrintCall(const std::string& msg, float scale,
                                 Vector4f color) {
  // Completely ignore this stuff in headless mode.
  if (g_core->HeadlessMode()) {
    return;
  }
  // If our event loop AND console are up and running, ship it off to be
  // printed. Otherwise store it for the console to grab when it's ready.
  if (auto* event_loop = g_base->logic->event_loop()) {
    if (dev_console_ != nullptr) {
      event_loop->PushCall([this, msg, scale, color] {
        dev_console_->Print(msg, scale, color);
      });
      return;
    }
  }
  // Didn't send a print; store for later.
  dev_console_startup_messages_.emplace_back(msg, scale, color);
}

void UI::OnAssetsAvailable() {
  assert(g_base->InLogicThread());

  // Spin up the dev console.
  if (!g_core->HeadlessMode() && !g_buildconfig.variant_demo()) {
    assert(dev_console_ == nullptr);
    dev_console_ = new DevConsole();

    // If the app-config has been applied at this point, apply it.
    if (g_base->logic->applied_app_config()) {
      dev_console_->ApplyAppConfig();
    }

    // Print any messages that have built up.
    if (!dev_console_startup_messages_.empty()) {
      for (auto&& entry : dev_console_startup_messages_) {
        dev_console_->Print(std::get<0>(entry), std::get<1>(entry),
                            std::get<2>(entry));
      }
      dev_console_startup_messages_.clear();
    }
  }
}

void UI::PushUIOperationRunnable(Runnable* runnable) {
  assert(g_base->InLogicThread());

  if (operation_context_ != nullptr) {
    // Once we're finishing the context, nothing else should be adding calls
    // to it.
    //
    // UPDATE - this is actually ok. Things like widget-select commands can
    // happen as part of user callbacks which themselves add additional
    // callbacks to the current ui-operation.
    //
    // if (operation_context_->ran_finish()) {
    //   auto trace = g_core->platform->GetNativeStackTrace();
    //   BA_LOG_ERROR_NATIVE_TRACE(
    //       "UI::PushUIOperationRunnable() called during UI operation
    //       finish.");
    //   return;
    // }

    operation_context_->AddRunnable(runnable);
    return;
  } else {
    BA_LOG_ERROR_NATIVE_TRACE(
        "UI::PushUIOperationRunnable() called outside of UI operation.");
  }
}

auto UI::InUIOperation() -> bool {
  assert(g_base->InLogicThread());
  return operation_context_ != nullptr;
}

}  // namespace ballistica::base
