// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_UI_H_
#define BALLISTICA_UI_UI_H_

#include <string>
#include <unordered_map>

#include "ballistica/core/context.h"
#include "ballistica/generic/timer_list.h"
#include "ballistica/ui/widget/widget.h"

// UI-Locks: make sure widget-lists don't change under you.
// Use a read-lock if you just need to ensure lists remain intact but won't be
// changing anything. Use a write-lock whenever modifying a list.
#if BA_DEBUG_BUILD
#define BA_DEBUG_UI_READ_LOCK UI::UILock ui_lock(false)
#define BA_DEBUG_UI_WRITE_LOCK UI::UILock ui_lock(true)
#else
#define BA_DEBUG_UI_READ_LOCK
#define BA_DEBUG_UI_WRITE_LOCK
#endif
#define BA_UI_READ_LOCK UI::UILock ui_lock(false)
#define BA_UI_WRITE_LOCK UI::UILock ui_lock(true)

namespace ballistica {

// All this stuff must be called from the game module.
class UI : public ContextTarget {
 public:
  UI();
  ~UI() override;
  void Reset();

  // Return the root widget containing all windows & dialogs
  // Whenever this contains children, the UI is considered to be in focus
  auto screen_root_widget() -> ContainerWidget* {
    return screen_root_widget_.get();
  }

  auto overlay_root_widget() -> ContainerWidget* {
    return overlay_root_widget_.get();
  }

  // Returns true if there is UI present in either the main or overlay
  // stacks.  Generally this implies the focus should be on the UI.
  auto IsWindowPresent() const -> bool;

  // Return the absolute root widget; this includes persistent UI
  // bits such as the top/bottom bars
  auto root_widget() -> RootWidget* { return root_widget_.get(); }

  auto Draw(FrameDef* frame_def) -> void;

  // Returns the widget an input should send commands to, if any.
  // Also potentially locks other inputs out of controlling the UI,
  // so only call this if you intend on sending a message to that widget.
  auto GetWidgetForInput(InputDevice* input_device) -> Widget*;

  // Add a widget to a container.
  // If a parent is provided, the widget is added to it; otherwise it is added
  // to the root widget.
  void AddWidget(Widget* w, ContainerWidget* to);

  // Send message to the active widget.
  auto SendWidgetMessage(const WidgetMessage& msg) -> int;

  // Use this to destroy any named widget (even those in containers).
  void DeleteWidget(Widget* widget);

  void ScreenSizeChanged();

  void SetUIInputDevice(InputDevice* input_device);

  // Returns the input-device that currently owns the menu; otherwise nullptr.
  auto GetUIInputDevice() const -> InputDevice*;

  // Returns whether currently selected widgets should flash.
  // This will be false in some situations such as when only touch screen
  // control is active.
  auto ShouldHighlightWidgets() const -> bool;

  // Same except for button shortcuts; these generally only get shown
  // if a joystick of some form is present.
  auto ShouldShowButtonShortcuts() const -> bool;

  void DrawExtras(FrameDef* frame_def);

  // Used to ensure widgets are not created or destroyed at certain times
  // (while traversing widget hierarchy, etc).
  class UILock {
   public:
    explicit UILock(bool write);
    ~UILock();

   private:
    BA_DISALLOW_CLASS_COPIES(UILock);
  };

  auto GetSound(const std::string& name) -> Object::Ref<Sound> override;
  auto GetData(const std::string& name) -> Object::Ref<Data> override;
  auto GetModel(const std::string& name) -> Object::Ref<Model> override;
  auto GetTexture(const std::string& name) -> Object::Ref<Texture> override;
  auto GetAsUIContext() -> UI* override;
  auto scene() -> Scene* {
    assert(scene_.exists());
    return scene_.get();
  }
  void Update(millisecs_t time_advance);
  auto GetMutableScene() -> Scene* override;

  // Context-target timer support.
  auto NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                const Object::Ref<Runnable>& runnable) -> int override;
  void DeleteTimer(TimeType timetype, int timer_id) override;

  RootUI* root_ui() const {
    assert(root_ui_);
    return root_ui_;
  }

 private:
  void StepScene();
  RootUI* root_ui_{};
  millisecs_t next_prune_time_{};
  int node_warning_count_{};
  Timer* step_scene_timer_{};
  millisecs_t base_time_{};
  TimerList sim_timers_;
  TimerList base_timers_;
  Object::Ref<Scene> scene_;
  Object::WeakRef<InputDevice> ui_input_device_;
  millisecs_t last_input_device_use_time_{};
  millisecs_t last_widget_input_reject_err_sound_time_{};
  Object::Ref<ContainerWidget> screen_root_widget_;
  Object::Ref<ContainerWidget> overlay_root_widget_;
  Object::Ref<RootWidget> root_widget_;
  int ui_lock_count_{};

  // Media loaded in the UI context.
  std::unordered_map<std::string, Object::WeakRef<Texture> > textures_;
  std::unordered_map<std::string, Object::WeakRef<Sound> > sounds_;
  std::unordered_map<std::string, Object::WeakRef<Data> > datas_;
  std::unordered_map<std::string, Object::WeakRef<Model> > models_;
};

}  // namespace ballistica

#endif  // BALLISTICA_UI_UI_H_
