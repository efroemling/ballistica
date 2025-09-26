// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/ui_v1.h"

#include <string>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/widget/root_widget.h"
#include "ballistica/ui_v1/widget/stack_widget.h"

namespace ballistica::ui_v1 {

core::CoreFeatureSet* g_core{};
base::BaseFeatureSet* g_base{};
UIV1FeatureSet* g_ui_v1{};

UIV1FeatureSet::UIV1FeatureSet() : python(new UIV1Python()) {
  // We're a singleton. If there's already one of us, something's wrong.
  assert(g_ui_v1 == nullptr);
}

void UIV1FeatureSet::OnModuleExec(PyObject* module) {
  // Ok, our feature-set's Python module is getting imported.
  // Like any normal Python module, we take this opportunity to
  // import/create the stuff we use.

  // Importing core should always be the first thing we do.
  // Various ballistica functionality will fail if this has not been done.
  g_core = core::CoreFeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_bauiv1 exec begin");

  // Create our feature-set's C++ front-end.
  assert(g_ui_v1 == nullptr);
  g_ui_v1 = new UIV1FeatureSet();
  g_ui_v1->python->AddPythonClasses(module);

  // Store our C++ front-end with our Python module.
  // This lets anyone get at us by going through the Python
  // import system (keeping things nice and consistent between
  // Python and C++ worlds).
  g_ui_v1->StoreOnPythonModule(module);

  // Import any Python stuff we use into objs_.
  g_ui_v1->python->ImportPythonObjs();

  // Import any other C++ feature-set-front-ends we use.
  assert(g_base == nullptr);  // Should be getting set once here.
  g_base = base::BaseFeatureSet::Import();

  g_core->logging->Log(LogName::kBaLifecycle, LogLevel::kInfo,
                       "_bauiv1 exec end");
}

auto UIV1FeatureSet::Import() -> UIV1FeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<UIV1FeatureSet>("_bauiv1");
}

void UIV1FeatureSet::DoShowURL(const std::string& url) { python->ShowURL(url); }

bool UIV1FeatureSet::IsMainUIVisible() {
  // We consider anything on our screen or overlay stacks to be a 'main ui'.
  auto* screen_root = screen_root_widget();
  auto* overlay_root = overlay_root_widget();
  return ((screen_root && screen_root->HasChildren())
          || (overlay_root && overlay_root->HasChildren()));
}

bool UIV1FeatureSet::IsPartyIconVisible() {
  // Currently this is always visible.
  return true;
}

void UIV1FeatureSet::SetAccountSignInState(bool signed_in,
                                           const std::string& name) {
  assert(root_widget_.exists());
  root_widget_->SetAccountSignInState(signed_in, name);
}

void UIV1FeatureSet::SetSquadSizeLabel(int num) {
  assert(root_widget_.exists());
  root_widget_->SetSquadSizeLabel(num);
}

void UIV1FeatureSet::ActivatePartyIcon() {
  if (auto* r = root_widget()) {
    root_widget_->SquadPress();
  }
}

bool UIV1FeatureSet::IsPartyWindowOpen() { return party_window_open_; }

void UIV1FeatureSet::Draw(base::FrameDef* frame_def) {
  base::RenderPass* overlay_flat_pass = frame_def->GetOverlayFlatPass();

  // Draw interface elements.
  auto* root_widget = root_widget_.get();

  if (root_widget && root_widget->HasChildren()) {
    // Draw our opaque and transparent parts separately. This way we can
    // draw front-to-back for opaque and back-to-front for transparent.

    g_base->graphics->set_drawing_opaque_only(true);

    // Do a wee bit of shifting based on tilt just for fun.
    Vector3f tilt = 0.1f * g_base->graphics->tilt();
    {
      base::EmptyComponent c(overlay_flat_pass);
      c.SetTransparent(false);
      {
        auto xf = c.ScopedTransform();
        c.Translate(-tilt.y, tilt.x, -0.5f);

        // We want our widgets to cover 0.1f in z space.
        c.Scale(1.0f, 1.0f, 0.1f);
        c.Submit();
        root_widget->Draw(overlay_flat_pass, false);
      }
      c.Submit();
    }

    g_base->graphics->set_drawing_opaque_only(false);
    g_base->graphics->set_drawing_transparent_only(true);

    {
      base::EmptyComponent c(overlay_flat_pass);
      c.SetTransparent(true);
      {
        auto xf = c.ScopedTransform();
        c.Translate(-tilt.y, tilt.x, -0.5f);

        // We want our widgets to cover 0.1f in z space.
        c.Scale(1.0f, 1.0f, 0.1f);
        c.Submit();
        root_widget->Draw(overlay_flat_pass, true);
      }
      c.Submit();
    }

    g_base->graphics->set_drawing_transparent_only(false);
  }
}

auto UIV1FeatureSet::GetSelectedWidget() -> Widget* {
  assert(g_base->InLogicThread());
  assert(root_widget_.exists());
  Widget* w{root_widget_.get()};

  while (true) {
    // If this widget has a selected child, recurse down.
    if (auto* cw = dynamic_cast<ContainerWidget*>(w)) {
      if (Widget* selected_widget = cw->selected_widget()) {
        w = selected_widget;
        continue;
      }
    }
    // Ok; no more children. Return the widget itself if its selectable, or
    // nothing otherwise.
    if (w->IsSelectable()) {
      return w;
    }
    return nullptr;
  }
}

void UIV1FeatureSet::OnActivate() {
  assert(g_base->InLogicThread());

  // (Re)create our screen window stack.
  auto sw(Object::New<StackWidget>());
  sw->set_is_main_window_stack(true);
  sw->SetWidth(g_base->graphics->screen_virtual_width());
  sw->SetHeight(g_base->graphics->screen_virtual_height());
  sw->set_translate(0, 0);
  sw->SetID("screen_root");
  screen_root_widget_ = sw;

  // (Re)create our overlay window stack.
  auto ow(Object::New<StackWidget>());
  ow->set_is_overlay_window_stack(true);
  ow->SetWidth(g_base->graphics->screen_virtual_width());
  ow->SetHeight(g_base->graphics->screen_virtual_height());
  ow->set_translate(0, 0);
  ow->SetID("overlay_root");
  overlay_root_widget_ = ow;

  // (Re)create our abs-root widget.
  auto rw(Object::New<RootWidget>());
  root_widget_ = rw;
  rw->SetWidth(g_base->graphics->screen_virtual_width());
  rw->SetHeight(g_base->graphics->screen_virtual_height());
  rw->SetID("root");
  // We don't call AddWidget on this so we need to manually register stuff:
  RegisterWidgetID(*rw->id(), rw.get());
  rw->set_in_hierarchy(true);
  // In order, add the screen stack, root's own ui bits, and then the
  // overlay stack.
  rw->SetScreenWidget(sw.get());
  rw->Setup();
  rw->SetOverlayWidget(ow.get());

  sw->GlobalSelect();
}

void UIV1FeatureSet::OnDeactivate() {
  assert(g_base->InLogicThread());

  root_widget_.Clear();
  screen_root_widget_.Clear();
  overlay_root_widget_.Clear();

  // All widgets should have unregistered their IDs by this point.
  assert(widgets_by_id_.empty());
}

void UIV1FeatureSet::AddWidget(Widget* w, ContainerWidget* parent) {
  assert(g_base->InLogicThread());

  BA_PRECONDITION(parent != nullptr);

  // If they're adding an initial window/dialog to our screen-stack or
  // overlay stack, send a reset-local-input message so that characters who
  // have lost focus will not get stuck running or whatnot. We should come
  // up with a more generalized way to track this sort of focus as this is a
  // bit hacky, but it works for now.
  auto* screen_root_widget = screen_root_widget_.get();
  auto* overlay_root_widget = overlay_root_widget_.get();
  if ((screen_root_widget && !screen_root_widget->HasChildren()
       && parent == screen_root_widget)
      || (overlay_root_widget && !overlay_root_widget->HasChildren()
          && parent == overlay_root_widget)) {
    g_base->input->ResetHoldStates();
  }

  parent->AddWidget(w);
}

void UIV1FeatureSet::OnScreenSizeChange() {
  // This gets called by the native layer as window is resized/etc.
  if (root_widget_.exists()) {
    root_widget_->SetWidth(g_base->graphics->screen_virtual_width());
    root_widget_->SetHeight(g_base->graphics->screen_virtual_height());
  }
}

void UIV1FeatureSet::OnUIScaleChange() {
  // This gets called by the Python layer when UIScale or window size
  // changes.
  assert(g_base->InLogicThread());

  // We allow OnScreenSizeChange() to handle size changes but *do* handle
  // UIScale changes here.
  if (auto* root_widget = root_widget_.get()) {
    root_widget->OnUIScaleChange();
  }
}

void UIV1FeatureSet::OnLanguageChange() {
  // Since switching languages is a bit costly, ignore redundant change
  // notifications. These will tend to happen nowadays since change
  // notifications go out anytime the ui-delegate switches.
  auto asset_language_state = g_base->assets->language_state();
  if (asset_language_state != language_state_) {
    language_state_ = asset_language_state;
    if (auto* r = root_widget()) {
      r->OnLanguageChange();
    }
  }
}

Widget* UIV1FeatureSet::GetRootWidget() { return root_widget(); }

auto UIV1FeatureSet::SendWidgetMessage(const base::WidgetMessage& m) -> int {
  if (!root_widget_.exists()) {
    return false;
  }
  return root_widget_->HandleMessage(m);
}

void UIV1FeatureSet::DeleteWidget(Widget* widget) {
  assert(widget);
  if (widget) {
    ContainerWidget* parent = widget->parent_widget();
    if (parent) {
      parent->DeleteWidget(widget);
    }
  }
}

void UIV1FeatureSet::ApplyAppConfig() {
  always_use_internal_on_screen_keyboard_ = g_base->app_config->Resolve(
      base::AppConfig::BoolID::kAlwaysUseInternalKeyboard);
}

auto UIV1FeatureSet::HasQuitConfirmDialog() -> bool { return true; }
void UIV1FeatureSet::ConfirmQuit(QuitType quit_type) {
  python->InvokeQuitWindow(quit_type);
}

UIV1FeatureSet::UIReadLock::UIReadLock() {
  assert(g_base->InLogicThread());

  // Grabbing a read-lock while writing is happening is an error.
  if (g_ui_v1->ui_write_lock_count_ != 0) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE("Can't read-lock UI: is write-locked");
  }
  g_ui_v1->ui_read_lock_count_++;
}

UIV1FeatureSet::UIReadLock::~UIReadLock() {
  g_ui_v1->ui_read_lock_count_--;
  if (g_ui_v1->ui_read_lock_count_ < 0) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE("ui_read_lock_count_ < 0");
    g_ui_v1->ui_read_lock_count_ = 0;
  }
}

UIV1FeatureSet::UIWriteLock::UIWriteLock() {
  assert(g_base->InLogicThread());

  // Grabbing a write-lock while reads are happening is an error.
  if (g_ui_v1->ui_read_lock_count_ != 0) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE("Can't write-lock UI: is read-locked.");
  }
  g_ui_v1->ui_write_lock_count_++;
}

UIV1FeatureSet::UIWriteLock::~UIWriteLock() {
  g_ui_v1->ui_write_lock_count_--;
  if (g_ui_v1->ui_write_lock_count_ < 0) {
    BA_LOG_ERROR_NATIVE_TRACE_ONCE("ui_write_lock_count_ < 0");
    g_ui_v1->ui_write_lock_count_ = 0;
  }
}
void UIV1FeatureSet::RegisterWidgetID(const std::string& id, Widget* w) {
  assert(g_base->InLogicThread());
  g_core->logging->Log(LogName::kBaUI, LogLevel::kDebug,
                       [&id] { return "Registering widget id '" + id + "'."; });

  // Warn if there is already a widget with this ID.
  auto it = widgets_by_id_.find(id);
  if (it != widgets_by_id_.end()) {
    g_core->logging->Log(LogName::kBaUI, LogLevel::kWarning, [&id] {
      return "Widget id '" + id
             + "' is already in use;"
               " all widgets should have unique IDs.";
    });
  }
  auto& vec = widgets_by_id_[id];
  vec.push_back(w);
}

void UIV1FeatureSet::UnregisterWidgetID(const std::string& id, Widget* w) {
  assert(g_base->InLogicThread());
  g_core->logging->Log(LogName::kBaUI, LogLevel::kDebug, [&id] {
    return "Unregistering widget id '" + id + "'.";
  });

  auto it = widgets_by_id_.find(id);
  if (it == widgets_by_id_.end()) {
    g_core->logging->Log(LogName::kBaUI, LogLevel::kError, [&id] {
      return "Widget id '" + id + "' not found at unregister.";
    });
    return;
  }

  auto& vec = it->second;
  auto vit = std::find(vec.begin(), vec.end(), w);
  if (vit == vec.end()) {
    g_core->logging->Log(LogName::kBaUI, LogLevel::kError, [&id] {
      return "Widget id '" + id
             + "' does not point to provided widget at unregister.";
    });
    return;
  }

  // Remove the widget pointer from the vector.
  vec.erase(vit);

  // Remove the id entirely if its vector is now empty.
  if (vec.empty()) {
    widgets_by_id_.erase(it);
  }
}

}  // namespace ballistica::ui_v1
