// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/ui_v1.h"

#include "ballistica/base/app/app_mode.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/support/root_ui.h"
#include "ballistica/ui_v1/widget/container_widget.h"

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

  g_core->LifecycleLog("_bauiv1 exec begin");

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

  // Let base know we exist.
  // (save it the trouble of trying to load us if it uses us passively).
  g_base->set_ui_v1(g_ui_v1);

  g_core->LifecycleLog("_bauiv1 exec end");
}

auto UIV1FeatureSet::Import() -> UIV1FeatureSet* {
  // Since we provide a native Python module, we piggyback our C++ front-end
  // on top of that. This way our C++ and Python dependencies are resolved
  // consistently no matter which side we are imported from.
  return ImportThroughPythonModule<UIV1FeatureSet>("_bauiv1");
}

void UIV1FeatureSet::DoHandleDeviceMenuPress(base::InputDevice* device) {
  python->HandleDeviceMenuPress(device);
}

void UIV1FeatureSet::DoShowURL(const std::string& url) { python->ShowURL(url); }

void UIV1FeatureSet::DoQuitWindow() {
  g_ui_v1->python->objs().Get(ui_v1::UIV1Python::ObjID::kQuitWindowCall).Call();
}

RootUI* UIV1FeatureSet::NewRootUI() { return new RootUI(); }

bool UIV1FeatureSet::MainMenuVisible() {
  auto* screen_root = g_base->ui->screen_root_widget();
  auto* overlay_root = g_base->ui->overlay_root_widget();
  return ((screen_root && screen_root->HasChildren())
          || (overlay_root && overlay_root->HasChildren()));
}

bool UIV1FeatureSet::PartyIconVisible() {
  int party_size = g_base->app_mode()->GetPartySize();
  if (party_size > 1 || g_base->app_mode()->HasConnectionToHost()
      || g_base->ui->root_ui()->always_draw_party_icon()) {
    return true;
  }
  return false;
}

void UIV1FeatureSet::ActivatePartyIcon() {
  if (auto* root_ui = g_base->ui->root_ui()) {
    root_ui->ActivatePartyIcon();
  }
}

void UIV1FeatureSet::HandleLegacyRootUIMouseMotion(float x, float y) {
  if (auto* root_ui = g_base->ui->root_ui()) {
    root_ui->HandleMouseMotion(x, y);
  }
}

auto UIV1FeatureSet::HandleLegacyRootUIMouseDown(float x, float y) -> bool {
  if (auto* root_ui = g_base->ui->root_ui()) {
    return root_ui->HandleMouseButtonDown(x, y);
  }
  return false;
}

void UIV1FeatureSet::HandleLegacyRootUIMouseUp(float x, float y) {
  if (auto* root_ui = g_base->ui->root_ui()) {
    root_ui->HandleMouseButtonUp(x, y);
  }
}

}  // namespace ballistica::ui_v1
