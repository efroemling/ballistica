// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui/ui.h"

#include "ballistica/app/app_globals.h"
#include "ballistica/audio/audio.h"
#include "ballistica/generic/lambda_runnable.h"
#include "ballistica/graphics/component/empty_component.h"
#include "ballistica/input/device/input_device.h"
#include "ballistica/input/input.h"
#include "ballistica/media/component/data.h"
#include "ballistica/media/component/sound.h"
#include "ballistica/python/python.h"
#include "ballistica/scene/scene.h"
#include "ballistica/ui/root_ui.h"
#include "ballistica/ui/widget/button_widget.h"
#include "ballistica/ui/widget/root_widget.h"
#include "ballistica/ui/widget/stack_widget.h"

namespace ballistica {

static const int kUIOwnerTimeoutSeconds = 30;

UI::UI() {
  // Figure out our interface type.
  assert(g_platform);

  // Allow overriding via an environment variable.
  auto* ui_override = getenv("BA_UI_SCALE");
  bool force_test_small{};
  bool force_test_medium{};
  bool force_test_large{};
  if (ui_override) {
    if (ui_override == std::string("small")) {
      force_test_small = true;
    } else if (ui_override == std::string("medium")) {
      force_test_medium = true;
    } else if (ui_override == std::string("large")) {
      force_test_large = true;
    }
  }
  if (force_test_small) {
    scale_ = UIScale::kSmall;
  } else if (force_test_medium) {
    scale_ = UIScale::kMedium;
  } else if (force_test_large) {
    scale_ = UIScale::kLarge;
  } else {
    // Use automatic val.
    if (g_buildconfig.iircade_build()) {  // NOLINT(bugprone-branch-clone)
      scale_ = UIScale::kMedium;
    } else if (IsVRMode() || g_platform->IsRunningOnTV()) {
      // VR and tv builds always use medium.
      scale_ = UIScale::kMedium;
    } else {
      scale_ = g_platform->GetUIScale();
    }
  }

  // Make sure we know when forced-ui-scale is enabled.
  if (force_test_small) {
    ScreenMessage("FORCING SMALL UI FOR TESTING", Vector3f(1, 0, 0));
    Log("FORCING SMALL UI FOR TESTING");
  } else if (force_test_medium) {
    ScreenMessage("FORCING MEDIUM UI FOR TESTING", Vector3f(1, 0, 0));
    Log("FORCING MEDIUM UI FOR TESTING");
  } else if (force_test_large) {
    ScreenMessage("FORCING LARGE UI FOR TESTING", Vector3f(1, 0, 0));
    Log("FORCING LARGE UI FOR TESTING");
  }

  step_scene_timer_ =
      base_timers_.NewTimer(base_time_, kGameStepMilliseconds, 0, -1,
                            NewLambdaRunnable([this] { StepScene(); }));
  scene_ = Object::New<Scene>(0);
}

auto UI::PostInit() -> void { root_ui_ = new RootUI(); }

// Currently the UI never dies so we don't bother doing a clean tear-down..
// (verifying scene cleanup, etc)
UI::~UI() {
  assert(root_ui_);
  delete root_ui_;
}

auto UI::IsWindowPresent() const -> bool {
  return ((screen_root_widget_.exists() && screen_root_widget_->HasChildren())
          || (overlay_root_widget_.exists()
              && overlay_root_widget_->HasChildren()));
}

void UI::SetUIInputDevice(InputDevice* input_device) {
  assert(InLogicThread());

  ui_input_device_ = input_device;

  // So they dont get stolen from immediately.
  last_input_device_use_time_ = GetRealTime();
}

UI::UILock::UILock(bool write) {
  assert(g_ui);
  assert(InLogicThread());

  if (write && g_ui->ui_lock_count_ != 0) {
    BA_LOG_ERROR_TRACE_ONCE("Illegal operation: UI is locked");
  }
  g_ui->ui_lock_count_++;
}

UI::UILock::~UILock() {
  g_ui->ui_lock_count_--;
  if (g_ui->ui_lock_count_ < 0) {
    BA_LOG_ERROR_TRACE_ONCE("ui_lock_count_ < 0");
    g_ui->ui_lock_count_ = 0;
  }
}

void UI::StepScene() {
  auto s = scene();
  sim_timers_.Run(s->time());
  s->Step();
}

void UI::Update(millisecs_t time_advance) {
  assert(InLogicThread());

  millisecs_t target_base_time = base_time_ + time_advance;
  while (!base_timers_.empty()
         && (base_time_ + base_timers_.GetTimeToNextExpire(base_time_)
             <= target_base_time)) {
    base_time_ += base_timers_.GetTimeToNextExpire(base_time_);
    base_timers_.Run(base_time_);
  }
  base_time_ = target_base_time;

  // Periodically prune various dead refs.
  if (base_time_ > next_prune_time_) {
    PruneDeadMapRefs(&textures_);
    PruneDeadMapRefs(&sounds_);
    PruneDeadMapRefs(&models_);
    next_prune_time_ = base_time_ + 4920;

    // Since we never clear our scene, we need to watch for leaks.
    // If there's more than a few nodes in existence for an extended period of
    // time, complain.
    if (scene_->nodes().size() > 10) {
      node_warning_count_++;
      if (node_warning_count_ > 3) {
        static bool complained = false;
        if (!complained) {
          Log(">10 nodes in UI context!");
          complained = true;
        }
      }
    } else {
      node_warning_count_ = 0;
    }
  }
}

void UI::Reset() {
  // Hmm; technically we don't need to recreate these each time we reset.
  root_widget_.Clear();

  // Kill our screen-root widget.
  screen_root_widget_.Clear();

  // (Re)create our screen-root widget.
  auto sw(Object::New<StackWidget>());
  sw->set_is_main_window_stack(true);
  sw->SetWidth(g_graphics->screen_virtual_width());
  sw->SetHeight(g_graphics->screen_virtual_height());
  sw->set_translate(0, 0);
  screen_root_widget_ = sw;

  // (Re)create our screen-overlay widget.
  auto ow(Object::New<StackWidget>());
  ow->set_is_overlay_window_stack(true);
  ow->SetWidth(g_graphics->screen_virtual_width());
  ow->SetHeight(g_graphics->screen_virtual_height());
  ow->set_translate(0, 0);
  overlay_root_widget_ = ow;

  // (Re)create our abs-root widget.
  auto rw(Object::New<RootWidget>());
  root_widget_ = rw;
  rw->SetWidth(g_graphics->screen_virtual_width());
  rw->SetHeight(g_graphics->screen_virtual_height());
  rw->SetScreenWidget(sw.get());
  rw->Setup();
  rw->SetOverlayWidget(ow.get());

  sw->GlobalSelect();
}

auto UI::ShouldHighlightWidgets() const -> bool {
  // Show selection highlights only if we've got controllers connected and only
  // when the main UI is visible (dont want a selection highlight for toolbar
  // buttons during a game).
  return (
      g_input->have_non_touch_inputs()
      && ((screen_root_widget_.exists() && screen_root_widget_->HasChildren())
          || (overlay_root_widget_.exists()
              && overlay_root_widget_->HasChildren())));
}

auto UI::ShouldShowButtonShortcuts() const -> bool {
  return g_input->have_non_touch_inputs();
}

void UI::AddWidget(Widget* w, ContainerWidget* parent) {
  assert(InLogicThread());

  BA_PRECONDITION(parent != nullptr);

  // If they're adding an initial window/dialog to our screen-stack,
  // send a reset-local-input message so that characters who have lost focus
  // will not get stuck running or whatnot.
  if (screen_root_widget_.exists() && !screen_root_widget_->HasChildren()
      && parent == &(*screen_root_widget_)) {
    g_game->ResetInput();
  }

  parent->AddWidget(w);
}

auto UI::SendWidgetMessage(const WidgetMessage& m) -> int {
  if (!root_widget_.exists()) {
    return false;
  }
  return root_widget_->HandleMessage(m);
}

void UI::DeleteWidget(Widget* widget) {
  assert(widget);
  if (widget) {
    ContainerWidget* parent = widget->parent_widget();
    if (parent) {
      parent->DeleteWidget(widget);
    }
  }
}

void UI::ScreenSizeChanged() {
  if (root_widget_.exists()) {
    root_widget_->SetWidth(g_graphics->screen_virtual_width());
    root_widget_->SetHeight(g_graphics->screen_virtual_height());
  }
}

auto UI::GetUIInputDevice() const -> InputDevice* {
  assert(InLogicThread());
  return ui_input_device_.get();
}

auto UI::GetWidgetForInput(InputDevice* input_device) -> Widget* {
  assert(input_device);
  assert(InLogicThread());

  // We only allow input-devices to control the UI when there's a window/dialog
  // on the screen (even though our top/bottom bars still exist).
  if ((!screen_root_widget_.exists() || (!screen_root_widget_->HasChildren()))
      && (!overlay_root_widget_.exists()
          || (!overlay_root_widget_->HasChildren()))) {
    return nullptr;
  }

  millisecs_t time = GetRealTime();

  bool print_menu_owner = false;
  Widget* ret_val;

  // Ok here's the deal:
  // Because having 10 controllers attached to the UI is pure chaos,
  // we only allow one input device at a time to control the menu.
  // However, if no events are received by that device for a long time,
  // it is up for grabs to the next device that requests it.

  if ((GetUIInputDevice() == nullptr) || (input_device == GetUIInputDevice())
      || (time - last_input_device_use_time_ > (1000 * kUIOwnerTimeoutSeconds))
      || !g_input->HaveManyLocalActiveInputDevices()) {
    // Don't actually assign yet; only update times and owners if there's a
    // widget to be had (we don't want some guy who moved his character 3
    // seconds ago to automatically own a newly created widget).
    last_input_device_use_time_ = time;
    ui_input_device_ = input_device;
    ret_val = screen_root_widget_.get();
  } else {
    // For rejected input devices, play error sounds sometimes so they know
    // they're not the chosen one.
    if (time - last_widget_input_reject_err_sound_time_ > 5000) {
      last_widget_input_reject_err_sound_time_ = time;
      g_audio->PlaySound(g_media->GetSound(SystemSoundID::kErrorBeep));
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
        time_out_str = " " + g_game->GetResourceString("timeOutText");
        Utils::StringReplaceOne(&time_out_str, "${TIME}",
                                std::to_string(timeout));
      } else {
        time_out_str = " " + g_game->GetResourceString("willTimeOutText");
      }

      std::string name;
      if (input->GetDeviceName() == "Keyboard") {
        name = g_game->GetResourceString("keyboardText");
      } else if (input->GetDeviceName() == "TouchScreen") {
        name = g_game->GetResourceString("touchScreenText");
      } else {
        // We used to use player names here, but that's kinda sloppy and random;
        // lets just go with device names/numbers.
        auto devicesWithName =
            g_input->GetInputDevicesWithName(input->GetDeviceName());
        if (devicesWithName.size() == 1) {
          // If there's just one, no need to tack on the '#2' or whatever.
          name = input->GetDeviceName();
        } else {
          name =
              input->GetDeviceName() + " " + input->GetPersistentIdentifier();
        }
      }

      std::string b = g_game->GetResourceString("hasMenuControlText");
      Utils::StringReplaceOne(&b, "${NAME}", name);
      ScreenMessage(b + time_out_str, {0.45f, 0.4f, 0.5f});
    }
  }
  return ret_val;
}

auto UI::GetModel(const std::string& name) -> Object::Ref<Model> {
  return Media::GetMedia(&models_, name, scene());
}

auto UI::GetTexture(const std::string& name) -> Object::Ref<Texture> {
  return Media::GetMedia(&textures_, name, scene());
}

auto UI::GetSound(const std::string& name) -> Object::Ref<Sound> {
  return Media::GetMedia(&sounds_, name, scene());
}

auto UI::GetData(const std::string& name) -> Object::Ref<Data> {
  return Media::GetMedia(&datas_, name, scene());
}

auto UI::GetAsUIContext() -> UI* { return this; }

auto UI::GetMutableScene() -> Scene* {
  Scene* sg = scene_.get();
  assert(sg);
  return sg;
}

auto UI::NewTimer(TimeType timetype, TimerMedium length, bool repeat,
                  const Object::Ref<Runnable>& runnable) -> int {
  // All of our stuff is just real-time; lets just map all timer options to
  // that.
  switch (timetype) {
    case TimeType::kSim:
    case TimeType::kBase:
    case TimeType::kReal:
      return g_game->NewRealTimer(length, repeat, runnable);
    default:
      // Fall back to default for descriptive error otherwise.
      return ContextTarget::NewTimer(timetype, length, repeat, runnable);
  }
}

void UI::DeleteTimer(TimeType timetype, int timer_id) {
  switch (timetype) {
    case TimeType::kSim:
    case TimeType::kBase:
    case TimeType::kReal:
      g_game->DeleteRealTimer(timer_id);
      break;
    default:
      // Fall back to default for descriptive error otherwise.
      ContextTarget::DeleteTimer(timetype, timer_id);
      break;
  }
}

auto UI::Draw(FrameDef* frame_def) -> void {
  RenderPass* overlay_flat_pass = frame_def->GetOverlayFlatPass();

  // Draw interface elements.
  auto* root_widget = root_widget_.get();

  if (root_widget && root_widget->HasChildren()) {
    // Draw our opaque and transparent parts separately.
    // This way we can draw front-to-back for opaque and back-to-front for
    // transparent.

    g_graphics->set_drawing_opaque_only(true);

    // Do a wee bit of shifting based on tilt just for fun.
    Vector3f tilt = 0.1f * g_graphics->tilt();
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

    g_graphics->set_drawing_opaque_only(false);
    g_graphics->set_drawing_transparent_only(true);

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

    g_graphics->set_drawing_transparent_only(false);
  }
  if (root_ui_) {
    root_ui_->Draw(frame_def);
  }
}

// void UI::DrawExtras(FrameDef* frame_def) {
//   assert(frame_def != nullptr);
//   assert(root_ui_ != nullptr);
//   root_ui_->Draw(frame_def);
// }

}  // namespace ballistica
