// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_UI_H_
#define BALLISTICA_BASE_UI_UI_H_

#include <list>
#include <string>
#include <vector>

#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/ui/widget_message.h"
#include "ballistica/shared/math/vector4f.h"

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
  void ApplyAppConfig();
  void OnScreenSizeChange();
  void StepDisplayTime();

  void OnAssetsAvailable();

  void LanguageChanged();

  /// Reset all UI to a default state. Note that this includes deactivating
  /// any current UI Delegate.
  void Reset();

  void SetUIDelegate(base::UIDelegateInterface* delegate);

  /// Pop up an in-app window to display a URL (NOT to open the URL in a
  /// browser). Can be called from any thread.
  void ShowURL(const std::string& url);

  /// Return whether a 'main ui' is visible. A 'main ui' is one that
  /// consumes full user attention and input focus. Common examples are main
  /// menu screens to get into a game or a menu brought up within a game
  /// allowing exiting or tweaking settings.
  auto IsMainUIVisible() const -> bool;

  /// Request invocation a main ui on the behalf of the provided device (or
  /// nullptr if none). Must be called from the logic thread. May have no
  /// effect depending on conditions such as a main ui already being
  /// present.
  void RequestMainUI(InputDevice* device);

  /// Similar to RequestMainUI(), except that, if there is already a main ui
  /// present, instead sends a cancel event. Appropriate to use for
  /// menu/back/escape buttons/keys.
  void MenuPress(InputDevice* input_device);

  /// Request control of the main ui on behalf of the provided device.
  /// Returns false if there is no main ui or if another device currently
  /// controls it. Devices should only send ui related input after a true
  /// result from this call. This call may result in on-screen messages that
  /// the UI is currently owned by some other device, so only call it when
  /// actively preparing to send some input.
  auto RequestMainUIControl(InputDevice* input_device) -> bool;

  void OnInputDeviceRemoved(InputDevice* input_device);

  /// Set the device controlling the main ui.
  void SetMainUIInputDevice(InputDevice* input_device);

  /// Return the device that currently owns the ui, or nullptr if none does.
  auto GetMainUIInputDevice() const -> InputDevice*;

  auto IsPartyIconVisible() -> bool;
  auto IsPartyWindowOpen() -> bool;
  void ActivatePartyIcon();

  /// Set persistent squad size label; will be provided to current and
  /// future delegates.
  void SetSquadSizeLabel(int val);

  /// Set persistent account state info; will be provided to current and
  /// future delegates.
  void SetAccountSignInState(bool signed_in, const std::string& name);

  auto HandleMouseDown(int button, float x, float y, bool double_click) -> bool;
  void HandleMouseUp(int button, float x, float y);
  void HandleMouseCancel(int button, float x, float y);
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

  /// Send a message to the active widget. This is a high level call that
  /// should only be used by top level event handling/etc.
  auto SendWidgetMessage(const WidgetMessage& msg) -> bool;

  /// Return true if there is a full desktop-style hardware keyboard
  /// attached and no non-keyboard device is currently controlling a main
  /// ui. This may also take language or user preferences into account.
  /// Editable text elements can use this to opt in to accepting key events
  /// directly instead of popping up string edit dialogs.
  auto UIHasDirectKeyboardInput() const -> bool;

  /// Return whether currently selected widgets should flash. This will be
  /// false in some situations such as when only touch screen control is
  /// present.
  auto ShouldHighlightWidgets() const -> bool;

  /// Current overall ui scale for the app.
  auto uiscale() const { return uiscale_; }

  /// Set overall ui scale for the app.
  void SetUIScale(UIScale val);

  auto* dev_console() const { return dev_console_; }

  void PushDevConsolePrintCall(const std::string& msg, float scale,
                               Vector4f color);

  auto* delegate() const { return delegate_; }

  class OperationContext {
   public:
    OperationContext();
    ~OperationContext();
    /// Should be called before returning from the high level event handling
    /// call.
    void Finish();
    void AddRunnable(Runnable* runnable);
    auto ran_finish() const { return ran_finish_; }

   private:
    std::vector<Runnable*> runnables_;
    OperationContext* parent_{};
    bool ran_finish_{};
  };

 private:
  void RequestMainUI_(InputDevice* device);
  auto DevConsoleButtonSize_() const -> float;
  auto InDevConsoleButton_(float x, float y) const -> bool;
  void DrawDevConsoleButton_(FrameDef* frame_def);

  Object::Ref<TextGroup> dev_console_button_txt_;
  Object::WeakRef<InputDevice> main_ui_input_device_;
  std::string account_state_name_;
  OperationContext* operation_context_{};
  base::UIDelegateInterface* delegate_{};
  DevConsole* dev_console_{};
  std::list<std::tuple<std::string, float, Vector4f>>
      dev_console_startup_messages_;
  millisecs_t last_main_ui_input_device_use_time_{};
  millisecs_t last_widget_input_reject_err_sound_time_{};
  UIScale uiscale_{UIScale::kLarge};
  int squad_size_label_{};
  bool account_state_signed_in_{};
  bool force_scale_{};
  bool show_dev_console_button_{};
  bool dev_console_button_pressed_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_UI_H_
