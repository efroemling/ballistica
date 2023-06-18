// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_UI_UI_H_
#define BALLISTICA_BASE_UI_UI_H_

#include <string>
#include <unordered_map>

#include "ballistica/base/support/context.h"
#include "ballistica/base/ui/widget_message.h"
#include "ballistica/shared/generic/timer_list.h"

// UI-Locks: make sure widget-lists don't change under you.
// Use a read-lock if you just need to ensure lists remain intact but won't be
// changing anything. Use a write-lock whenever modifying a list.
#if BA_DEBUG_BUILD
#define BA_DEBUG_UI_READ_LOCK ::ballistica::base::UI::UILock ui_lock(false)
#define BA_DEBUG_UI_WRITE_LOCK ::ballistica::base::UI::UILock ui_lock(true)
#else
#define BA_DEBUG_UI_READ_LOCK
#define BA_DEBUG_UI_WRITE_LOCK
#endif
#define BA_UI_READ_LOCK UI::UILock ui_lock(false)
#define BA_UI_WRITE_LOCK UI::UILock ui_lock(true)

// Predeclare a few things from ui_v1.
namespace ballistica::ui_v1 {
class Widget;
}

namespace ballistica::base {

// Our global UI subsystem. This wrangles all app
class UI {
 public:
  UI();

  void OnAppStart();
  void OnAppPause();
  void OnAppResume();
  void OnAppShutdown();
  void DoApplyAppConfig();
  void OnScreenSizeChange();
  void StepDisplayTime();

  void LanguageChanged();

  void Reset();

  /// Pop up an in-game window to show a url (NOT in a browser).
  /// Can be called from any thread.
  void ShowURL(const std::string& url);

  /// High level call to request a quit ui (or in some cases quit immediately).
  /// This can be called from any thread.
  void ConfirmQuit();

  /// Return whether there is UI present in either the main or overlay
  /// stacks. Generally this implies the focus should be on the UI.
  auto MainMenuVisible() const -> bool;
  auto PartyIconVisible() -> bool;
  void ActivatePartyIcon();
  void HandleLegacyRootUIMouseMotion(float x, float y);
  auto HandleLegacyRootUIMouseDown(float x, float y) -> bool;
  void HandleLegacyRootUIMouseUp(float x, float y);
  auto PartyWindowOpen() -> bool;

  void Draw(FrameDef* frame_def);

  // Returns the widget an input should send commands to, if any.
  // Also potentially locks other inputs out of controlling the UI,
  // so only call this if you intend on sending a message to that widget.
  auto GetWidgetForInput(InputDevice* input_device) -> ui_v1::Widget*;

  // Send message to the active widget.
  auto SendWidgetMessage(const WidgetMessage& msg) -> int;

  void SetUIInputDevice(InputDevice* input_device);

  // Returns the input-device that currently owns the menu; otherwise nullptr.
  auto GetUIInputDevice() const -> InputDevice*;

  void PushBackButtonCall(InputDevice* input_device);

  // Returns whether currently selected widgets should flash.
  // This will be false in some situations such as when only touch screen
  // control is active.
  auto ShouldHighlightWidgets() const -> bool;

  // Same except for button shortcuts; these generally only get shown
  // if a joystick of some form is present.
  auto ShouldShowButtonShortcuts() const -> bool;

  // Used to ensure widgets are not created or destroyed at certain times
  // (while traversing widget hierarchy, etc).
  class UILock {
   public:
    explicit UILock(bool write);
    ~UILock();

   private:
    BA_DISALLOW_CLASS_COPIES(UILock);
  };

  auto scale() const { return scale_; }

  /// Push a generic 'menu press' event, optionally associated with an
  /// input device (nullptr to specify none). Note: caller must ensure
  /// a RemoveInputDevice() call does not arrive at the logic thread
  /// before this one.
  void PushMainMenuPressCall(InputDevice* device);

 private:
  void MainMenuPress(InputDevice* device);
  Object::WeakRef<InputDevice> ui_input_device_;
  millisecs_t last_input_device_use_time_{};
  millisecs_t last_widget_input_reject_err_sound_time_{};
  int ui_lock_count_{};
  UIScale scale_{UIScale::kLarge};
  bool force_scale_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_UI_UI_H_
