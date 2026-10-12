// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/support/viewer_depiction.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/depiction/depiction.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/python/python_ref.h"
#include "ballistica/ui_v1/python/class/python_class_viewer_source.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/support/viewer_source.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

namespace {

// Wire type id (bacommon.depiction.DepictionTypeID.CHARACTER_VIEWER).
const char* const kTypeCharacterViewer = "cv";

// How long a newly appearing picture takes to fade in.
const seconds_t kPictureFadeInSeconds = 0.2;

// How often (at most) to ask for our viewer again after losing it.
const millisecs_t kReacquireIntervalMs = 1000;

class LiveViewerDepiction : public base::Depiction,
                            public base::DepictionInput {
 public:
  LiveViewerDepiction(std::string type_id, std::string json, std::string key)
      : base::Depiction(type_id),
        json_{std::move(json)},
        key_{std::move(key)} {}

  auto SupportsHost(base::DepictionHost host) const -> bool override {
    // A live picture renders a scene of its own to a texture; that's
    // for ui, not for in-game overlays.
    return host == base::DepictionHost::kUI;
  }

  void Update(millisecs_t now) override {
    // Get our viewer the first time we're shown, and again (not too
    // often) if the registry retired it while we still show it -- say
    // another viewer bumped it out while ours was briefly unseen.
    bool lost = source_.exists() && had_picture_
                && source_->GetViewerTexture() == nullptr;
    if ((!viewer_.exists() || lost)
        && (last_acquire_ms_ < 0
            || now - last_acquire_ms_ > kReacquireIntervalMs)) {
      last_acquire_ms_ = now;
      Acquire_();
    }
    if (source_.exists()) {
      source_->MarkShown();
    }
  }

  void Draw(const base::DepictionDrawContext& context) override {
    if (!source_.exists()) {
      return;
    }
    const base::DepictionBox& b = context.box;

    // Once per frame (the opaque pass always runs): tell our source
    // how big we show it, in pixels, so it can make its picture land
    // one to one.
    if (!context.transparent) {
      source_->SetViewerPixelSize(
          std::max(1, static_cast<int>(
                          std::round(b.width * context.pixels_per_unit))),
          std::max(1, static_cast<int>(
                          std::round(b.height * context.pixels_per_unit))));
    }

    base::TextureAsset* picture = source_->GetViewerTexture();
    if (picture == nullptr || !picture->loaded()) {
      return;
    }
    had_picture_ = true;
    seconds_t now = g_base->logic->display_time();
    if (picture_start_time_ < 0.0) {
      picture_start_time_ = now;
    }
    float fade = fade_picture_in_
                     ? static_cast<float>(std::clamp(
                           (now - picture_start_time_) / kPictureFadeInSeconds,
                           0.0, 1.0))
                     : 1.0f;
    bool masked = context.mask_texture != nullptr;
    if (masked && !context.mask_texture->loaded()) {
      return;
    }
    float alpha = fade * context.StandardOpacity();
    // Masked or not fully opaque needs the transparent pass.
    bool transparent = masked || alpha < 1.0f;
    if (context.transparent != transparent) {
      return;
    }
    // A render view's texture is premultiplied, so our modulate color
    // must be too (see docs/design/premultiplied-alpha.md).
    float cmul = (picture->premultiplied() ? alpha : 1.0f)
                 * context.StandardBrightness();
    base::SimpleComponent c(context.pass);
    c.SetTransparent(transparent);
    c.SetColor(cmul, cmul, cmul, alpha);
    c.SetTexture(picture);
    if (masked) {
      float frame[3]{context.frame_color[0], context.frame_color[1],
                     context.frame_color[2]};
      context.StandardColor(frame);
      c.SetMaskTexture(context.mask_texture);
      c.SetColorizeColor(frame[0], frame[1], frame[2]);
    }
    {
      auto xf = c.ScopedTransform();
      c.Translate(b.x + b.width * 0.5f, b.y + b.height * 0.5f, context.z);
      c.Scale(b.width, b.height, 1.0f);
      c.DrawMeshAsset(
          g_base->assets->BuiltinMesh(base::BuiltinMeshID::kMeshesImage1x1));
    }
    c.Submit();
  }

  auto GetInput() -> base::DepictionInput* override {
    return wants_presses_ ? this : nullptr;
  }

  auto GetPythonControl() -> PyObject* override {
    return viewer_.exists() ? viewer_.get() : nullptr;
  }

  // DepictionInput: straight through to our viewer, scheduled like any
  // other ui callback.
  auto HandlePress(float x, float y) -> bool override {
    if (!press_call_.exists()) {
      return false;
    }
    press_call_->ScheduleInUIOperation(
        PythonRef::Stolen(Py_BuildValue("(ff)", x, y)));
    return true;
  }

  void HandleDrag(float x, float y) override {
    if (drag_call_.exists()) {
      drag_call_->ScheduleInUIOperation(
          PythonRef::Stolen(Py_BuildValue("(ff)", x, y)));
    }
  }

  void HandleRelease() override {
    if (release_call_.exists()) {
      release_call_->ScheduleInUIOperation();
    }
  }

 private:
  void Acquire_() {
    auto& objs = g_ui_v1->python->objs();
    PythonRef args = PythonRef::Stolen(
        Py_BuildValue("(sss)", type_id().c_str(), key_.c_str(), json_.c_str()));
    PythonRef viewer =
        objs.Get(UIV1Python::ObjID::kGetLiveDepictionCall).Call(args);
    if (!viewer.exists() || viewer.get() == Py_None) {
      return;
    }
    PythonRef source_obj = viewer.GetAttr("source");
    if (!PythonClassViewerSource::Check(source_obj.get())) {
      g_core->logging->Log(LogName::kBaUI, LogLevel::kError,
                           "Live depiction viewer has no usable source.");
      return;
    }
    ViewerSource* source =
        PythonClassViewerSource::FromPyObj(source_obj.get()).GetAsset();
    // A viewer someone was showing a moment ago (a rebuilt window's)
    // just carries on; a new one fades in.
    fade_picture_in_ = !source->WasJustShown();
    picture_start_time_ = -1.0;
    had_picture_ = false;
    source_ = source;
    viewer_ = viewer;
    wants_presses_ = viewer.GetAttr("wants_presses").Call().ValueAsBool();
    press_call_ =
        Object::New<base::PythonContextCall>(viewer.GetAttr("handle_press"));
    drag_call_ =
        Object::New<base::PythonContextCall>(viewer.GetAttr("handle_drag"));
    release_call_ =
        Object::New<base::PythonContextCall>(viewer.GetAttr("handle_release"));
  }

  std::string json_;
  std::string key_;
  PythonRef viewer_;
  Object::Ref<ViewerSource> source_;
  Object::Ref<base::PythonContextCall> press_call_;
  Object::Ref<base::PythonContextCall> drag_call_;
  Object::Ref<base::PythonContextCall> release_call_;
  bool wants_presses_{};
  bool fade_picture_in_{true};
  bool had_picture_{};
  seconds_t picture_start_time_{-1.0};
  millisecs_t last_acquire_ms_{-1};
};

}  // namespace

void RegisterViewerDepictionKinds() {
  base::DepictionRegistry::RegisterKind(
      kTypeCharacterViewer,
      [](const base::DepictionRegistry::Source& src)
          -> Object::Ref<base::Depiction> {
        // The viewer's maker parses the depiction whole, so we hand
        // along the json we were made from.
        return Object::New<base::Depiction, LiveViewerDepiction>(
            kTypeCharacterViewer, src.json, src.key);
      });
}

}  // namespace ballistica::ui_v1
