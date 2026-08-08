// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/ui/ui.h"

#include <Python.h>

#include <exception>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/app_mode/app_mode.h"
#include "ballistica/base/assets/builtin_strings.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/input/device/keyboard_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/dev_console.h"
#include "ballistica/base/ui/simple_dialog.h"
#include "ballistica/base/ui/ui_delegate.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/vector4f.h"

namespace ballistica::base {

static const int kUIOwnerTimeoutSeconds = 15;

/// Flip to true to spin up a placeholder SimpleDialog at boot (with a
/// self-animating progress bar) for iterating on the dialog's looks without a
/// live asset resolve. Must stay false in committed code.
static const bool kSimpleDialogDemo = false;

/// We use this to gather up runnables triggered by UI elements in response
/// to stuff happening (mouse clicks, elements being added or removed,
/// etc.). It's a bad idea to run such runnables immediately because they
/// might modify UI lists we're in the process of traversing. It's also a
/// bad idea to schedule such runnables in the event loop, because a
/// runnable may wish to modify the UI to prevent further runs from
/// happening and that won't work if multiple runnables can be scheduled
/// before the first runs. So our goldilocks approach here is to gather all
/// runnables that get scheduled as part of each operation and then run them
/// explicitly once we are safely out of any UI list traversal.
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
    // If a context was set when we came into existence, it should still be
    // that same context when we go out of existence.
    assert(g_base->ui->operation_context_ == parent_);
    assert(runnables_.empty());
  }

  // Complain if our Finish() call was never run (unless it seems we're
  // being torn down as part of stack-unwinding due to an exception).
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

  // Set touch-mode. In the future we'll update this dynamically depending
  // on whether touch events or mouse events come through/etc.
  touch_mode_ = !g_core->platform->IsRunningOnDesktop();

  // Handy way to test touchscreen interaction from desktop.
  // printf("FORCING TOUCH\n");
  // touch_mode_ = true;
}

void UI::SetTouchMode(bool val) {
  assert(g_base->InLogicThread());
  touch_mode_ = val;
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
  // A modal SimpleDialog swallows input; don't let the party button (which
  // calls here directly, bypassing SendWidgetMessage) toggle the party window
  // out from under it.
  if (HasModalSimpleDialog()) {
    return;
  }
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

  // SimpleDialogs (above the main UI, below the dev console). Give the
  // top-most (highest-id) a first crack.
  if (!handled) {
    for (auto it = simple_dialogs_.rbegin(); it != simple_dialogs_.rend();
         ++it) {
      if (it->second->HandleMouseDown(button, x, y)) {
        handled = true;
        break;
      }
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

  // A release in-bounds on a SimpleDialog's button fires it. Collect ids
  // first so we don't dispatch into Python (which may mutate the map) while
  // iterating it.
  std::vector<int> fired_dialog_ids;
  for (auto&& entry : simple_dialogs_) {
    if (entry.second->HandleMouseUp(button, x, y)) {
      fired_dialog_ids.push_back(entry.first);
    }
  }
  for (int id : fired_dialog_ids) {
    DispatchSimpleDialogButton_(id, "mouse/touch");
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

  for (auto&& entry : simple_dialogs_) {
    entry.second->HandleMouseCancel(button, x, y);
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

  // Any switch here resets mousing-in-main-ui mode. (otherwise sometimes
  // highlighting doesn't start showing until second key press).
  mousing_in_main_ui_ = false;

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
  // Show selection highlights only when a main ui is up and we're
  // getting inputs from something besides a mouse or touchscreen.
  return IsMainUIVisible() && !mousing_in_main_ui_;
}

auto UI::SendWidgetMessage(const WidgetMessage& m) -> bool {
  // A SimpleDialog is modal while it's up: consume EVERY message here so
  // nothing leaks to the widget tree / game underneath. Confirm-family
  // messages (kStart/kActivate -- keyboard return, controller/remote OK
  // buttons, etc.) fire the dialog's button if it has one; everything else
  // (cancel, navigation, stray mouse events that missed the dialog) is
  // swallowed with no effect. This is the funnel for both keyboard/controller
  // widget messages and the mouse-event fall-through from HandleMouse*.
  if (!simple_dialogs_.empty()) {
    if (m.type == WidgetMessage::Type::kStart
        || m.type == WidgetMessage::Type::kActivate) {
      HandleSimpleDialogActivate_();
    }
    return true;
  }

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
      g_base->audio->SafePlayBuiltinSound(BuiltinSoundID::kAudioError);
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
      if (timeout > 0 && timeout < (kUIOwnerTimeoutSeconds - 3)) {
        time_out_str = " "
                       + BuiltinStrings::Ui::MenuControlTimeOut(
                             static_cast<int64_t>(timeout))
                             ->Evaluate();
      } else {
        time_out_str =
            " " + BuiltinStrings::Ui::MenuControlWillTimeOut()->Evaluate();
      }

      std::string name{input->GetDeviceNamePretty()};

      g_base->ScreenMessage(
          BuiltinStrings::Ui::HasMenuControl(name)->Evaluate() + time_out_str,
          {0.45f, 0.4f, 0.5f});
    }
  }
  return ret_val;
}

void UI::Draw(FrameDef* frame_def) {
  if (auto* ui_delegate = delegate()) {
    ui_delegate->Draw(frame_def);
  }
}

void UI::DrawSimpleDialogs(FrameDef* frame_def) {
  // Drawn in id order, so a newer dialog layers over an older one.
  for (auto&& entry : simple_dialogs_) {
    entry.second->Draw(frame_def);
  }
}

auto UI::CreateSimpleDialog() -> int {
  assert(g_base->InLogicThread());
  int id = next_simple_dialog_id_++;
  simple_dialogs_[id] = std::make_unique<SimpleDialog>(id);
  return id;
}

void UI::SetSimpleDialogState(int id, const std::string& title,
                              const std::string& message, float progress,
                              const std::string& button_label) {
  assert(g_base->InLogicThread());
  auto it = simple_dialogs_.find(id);
  if (it != simple_dialogs_.end()) {
    it->second->SetState(title, message, progress, button_label);
  }
}

void UI::DismissSimpleDialog(int id) {
  assert(g_base->InLogicThread());
  simple_dialogs_.erase(id);
}

auto UI::HandleSimpleDialogActivate_() -> bool {
  // Fire the top-most (highest-id) button-bearing dialog.
  for (auto it = simple_dialogs_.rbegin(); it != simple_dialogs_.rend(); ++it) {
    if (it->second->Activate()) {
      DispatchSimpleDialogButton_(it->first, "key/controller OK");
      return true;
    }
  }
  return false;
}

void UI::DispatchSimpleDialogButton_(int id, const char* source) {
  assert(g_base->InLogicThread());
  // Click-sound feedback + a DEBUG trace on every activation, regardless of
  // input device (mouse/touch, keyboard return, controller/remote OK buttons
  // all funnel through here). The real action is the Python on_button.
  g_core->logging->Log(LogName::kBa, LogLevel::kDebug,
                       "SimpleDialog: button activated (dialog "
                           + std::to_string(id) + ", via " + source + ").");
  g_base->audio->SafePlayBuiltinSound(BuiltinSoundID::kAudioClick01);
  PythonRef args(Py_BuildValue("(i)", id), PythonRef::kSteal);
  g_base->python->objs()
      .Get(BasePython::ObjID::kSimpleDialogButtonPressCall)
      .Call(args);
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
  auto* button_tex =
      g_base->assets->BuiltinTexture(BuiltinTextureID::kTexturesCircleShadow);
  c.SetTexture(button_tex);
  // Premultiply rgb by alpha for the premultiplied texture so the faded
  // (alpha 0.8) button composites 'over' correctly (see
  // docs/design/premultiplied-alpha.md).
  float cmul = button_tex->premultiplied() ? 0.8f : 1.0f;
  if (dev_console_button_pressed_) {
    c.SetColor(cmul, cmul, cmul, 0.8f);
  } else {
    c.SetColor(0.5f * cmul, 0.5f * cmul, 0.5f * cmul, 0.8f);
  }
  {
    auto xf = c.ScopedTransform();
    c.Translate(vwidth - bsz * 0.5f, vheight * 0.5f, kDevConsoleZDepth + 0.01f);
    c.Scale(bsz, bsz, 1.0f);
    c.DrawMeshAsset(
        g_base->assets->BuiltinMesh(BuiltinMeshID::kMeshesImage1x1));
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

void UI::PushDevConsolePrintCall(
    std::vector<core::DevConsolePrintEntry> entries) {
  // Completely ignore this stuff in headless mode.
  if (g_core->HeadlessMode()) {
    return;
  }
  // If our event loop AND console are up and running, ship the whole batch
  // off to be printed in a SINGLE logic-thread call. Doing one PushCall per
  // log line instead let a logging burst (e.g. a verbose-logging boot)
  // flood the logic thread's message queue -- see the >1000/>10000
  // ThreadMessage guards in EventLoop. Otherwise store the lines for the
  // console to grab once it's ready.
  if (auto* event_loop = g_base->logic->event_loop()) {
    if (dev_console_ != nullptr) {
      event_loop->PushCall([this, entries = std::move(entries)] {
        for (auto& entry : entries) {
          dev_console_->Print(entry.msg.c_str(), entry.scale, entry.color);
        }
      });
      return;
    }
  }
  // Console not ready yet; buffer the lines for later.
  for (auto& entry : entries) {
    dev_console_startup_messages_.emplace_back(entry.msg, entry.scale,
                                               entry.color);
  }
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
        dev_console_->Print(std::get<0>(entry).c_str(), std::get<1>(entry),
                            std::get<2>(entry));
      }
      dev_console_startup_messages_.clear();
    }

    // Look-iteration aid: when enabled, spin up a demo SimpleDialog with
    // placeholder content (self-animating progress bar) so we can tune the
    // dialog's appearance without a live asset resolve. Off in normal use --
    // real dialogs are created on demand via CreateSimpleDialog (needs builtin
    // assets, same as the dev console).
    if (kSimpleDialogDemo) {
      int id = CreateSimpleDialog();
      auto it = simple_dialogs_.find(id);
      assert(it != simple_dialogs_.end());
      it->second->SetState("UPDATING ASSETS",
                           "Downloading assets (37 remaining)…\n"
                           "Verifying downloaded data…\n"
                           "Unpacking and installing…\n"
                           "Finishing up…",
                           -1.0f, "Retry");
      it->second->set_demo_animate(true);
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

void UI::OnClickOrTap() {
  assert(g_base->InLogicThread());

  // Note that the user seems to be tapping/clicking their way around.
  if (IsMainUIVisible()) {
    if (!mousing_in_main_ui_) {
      mousing_in_main_ui_ = true;
    }
  }
}

void UI::OnInputDeviceActive(InputDevice* device) {
  assert(g_base->InLogicThread());

  // Any input associated with a device is *not* touch/mouse input.
  // Note that the user seems to be navigating UI in that manner.
  if (GetMainUIInputDevice() == device && IsMainUIVisible()) {
    if (mousing_in_main_ui_) {
      mousing_in_main_ui_ = false;
    }
  }
}

}  // namespace ballistica::base
