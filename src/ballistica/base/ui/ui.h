// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_UI_H_
#define BALLISTICA_BASE_UI_UI_H_

#include <string>
#include <unordered_map>

#include "ballistica/base/support/context.h"
#include "ballistica/base/ui/widget_message.h"
#include "ballistica/shared/generic/timer_list.h"

// Predeclare a few things from ui_v1.
namespace ballistica::ui_v1 {
class Widget;
}

namespace ballistica::base {

/// Delay before moving through elements in the UI when a key/button/stick
/// is held
const seconds_t kUINavigationRepeatDelay{0.25};

/// Interval after the initial delay when moving through UI elements when a
/// key/button/stick is held.
const seconds_t kUINavigationRepeatInterval{0.1};

// Our global UI subsystem. This acts as a manager/wrapper for individual UI
// feature-sets that provide specific UI functionality.
class UI {
 public:
  UI();

  void OnAppStart();
  void OnAppSuspend();
  void OnAppUnsuspend();
  void OnAppShutdown();
  void OnAppShutdownComplete();
  void DoApplyAppConfig();
  void OnScreenSizeChange();
  void StepDisplayTime();

  void OnAssetsAvailable();

  void LanguageChanged();

  /// Reset all UI to a default state. Generally should be called when
  /// switching app-modes or when resetting things within an app mode.
  void Reset();

  void set_ui_delegate(base::UIDelegateInterface* delegate);

  /// Pop up an in-app window to display a URL (NOT to open the URL in a
  /// browser). Can be called from any thread.
  void ShowURL(const std::string& url);

  /// High level call to request a quit; ideally with a confirmation ui.
  /// When a UI can't be shown, triggers an immediate shutdown. This can be
  /// called from any thread.
  // void ConfirmQuit();

  /// Return whether there is UI present in either the main or overlay
  /// stacks. Generally this implies the focus should be on the UI.
  auto MainMenuVisible() const -> bool;

  auto PartyIconVisible() -> bool;
  auto PartyWindowOpen() -> bool;
  void ActivatePartyIcon();

  auto HandleMouseDown(int button, float x, float y, bool double_click) -> bool;
  void HandleMouseUp(int button, float x, float y);
  void HandleMouseMotion(float x, float y);

  /// Draw regular UI.
  void Draw(FrameDef* frame_def);

  /// Draw dev UI on top.
  void DrawDev(FrameDef* frame_def);

  /// Add a runnable to be run as part of the currently-being-processed UI
  /// operation. Pass a Runnable that has been allocated with
  /// NewUnmanaged(). It will be owned and disposed of by the UI from this
  /// point. Must be called from the logic thread.
  void PushUIOperationRunnable(Runnable* runnable);

  auto InUIOperation() -> bool;

  /// Return the widget an input-device should send commands to, if any.
  /// Potentially assigns UI control to the provide device, so only call
  /// this if you intend on actually sending a message to that widget.
  auto GetWidgetForInput(InputDevice* input_device) -> ui_v1::Widget*;

  /// Send a message to the active widget. This is a high level call that
  /// should only be used by top level event handling/etc.
  auto SendWidgetMessage(const WidgetMessage& msg) -> bool;

  /// Set the device controlling the UI.
  void SetUIInputDevice(InputDevice* input_device);

  /// Return the input-device that currently owns the UI; otherwise nullptr.
  auto GetUIInputDevice() const -> InputDevice*;

  /// Return true if there is a full desktop-style hardware keyboard
  /// attached and no non-keyboard device is currently controlling the UI. This
  /// also may take language or user preferences into account. Editable text
  /// elements can use this to opt in to accepting key events directly
  /// instead of popping up string edit dialogs.
  auto UIHasDirectKeyboardInput() const -> bool;

  /// Schedule a back button press. Can be called from any thread.
  void PushBackButtonCall(InputDevice* input_device);

  /// Return whether currently selected widgets should flash. This will be
  /// false in some situations such as when only touch screen control is
  /// present.
  auto ShouldHighlightWidgets() const -> bool;

  /// Return whether currently selected widget should show button shortcuts.
  /// These generally only get shown if a joystick of some form is present.
  auto ShouldShowButtonShortcuts() const -> bool;

  /// Overall ui scale for the app.
  auto scale() const { return scale_; }

  /// Push a generic 'menu press' event, optionally associated with an input
  /// device (nullptr to specify none). Can be called from any thread.
  void PushMainMenuPressCall(InputDevice* device);

  auto* dev_console() const { return dev_console_; }

  void PushDevConsolePrintCall(const std::string& msg);

  auto* delegate() const { return delegate_; }

  class OperationContext {
   public:
    OperationContext();
    ~OperationContext();
    /// Should be called before returning from the high level event handling
    /// call.
    void Finish();
    void AddRunnable(Runnable* runnable);

   private:
    bool ran_finish_{};
    OperationContext* parent_{};
    std::vector<Runnable*> runnables_;
  };

 private:
  void MainMenuPress_(InputDevice* device);
  auto DevConsoleButtonSize_() const -> float;
  auto InDevConsoleButton_(float x, float y) const -> bool;
  void DrawDevConsoleButton_(FrameDef* frame_def);

  OperationContext* operation_context_{};
  base::UIDelegateInterface* delegate_{};
  DevConsole* dev_console_{};
  std::string dev_console_startup_messages_;
  Object::WeakRef<InputDevice> ui_input_device_;
  millisecs_t last_input_device_use_time_{};
  millisecs_t last_widget_input_reject_err_sound_time_{};
  UIScale scale_{UIScale::kLarge};
  bool force_scale_{};
  bool show_dev_console_button_{};
  bool dev_console_button_pressed_{};
  Object::Ref<TextGroup> dev_console_button_txt_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_UI_H_
