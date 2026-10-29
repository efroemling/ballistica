// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/support/viewer_depiction.h"

#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <unordered_set>
#include <utility>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/depiction/depiction.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/shared/python/python_ref.h"
#include "ballistica/ui_v1/python/class/python_class_viewer_source.h"
#include "ballistica/ui_v1/python/ui_v1_python.h"
#include "ballistica/ui_v1/support/viewer_source.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

namespace {

// Wire type ids of the live-viewer kinds (bacommon.depiction
// .DepictionTypeID.CHARACTER_VIEWER and .MESH_VIEWER). Each is shown
// the same way: by the viewer the app mode's maker for it hands back.
const char* const kTypeCharacterViewer = "cv";
const char* const kTypeMeshViewer = "mv";

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
    // Once we know we can never show it, we just show that.
    if (!failure_.empty()) {
      return;
    }
    // Get our viewer the first time we're shown, and again (not too
    // often) if the registry retired it while we still show it -- say
    // another viewer bumped it out while ours was briefly unseen. (Even
    // before it ever showed us a picture: a pane on a window that's on
    // its way out can bump ours right as we're made.)
    bool lost =
        source_.exists()
        && (source_->retired()
            || (had_picture_ && source_->GetViewerTexture() == nullptr));
    if ((!viewer_.exists() || lost)
        && (last_acquire_ms_ < 0
            || now - last_acquire_ms_ > kReacquireIntervalMs)) {
      last_acquire_ms_ = now;
      Acquire_();
    }
    if (source_.exists()) {
      // Our viewer finding what it was given unusable (now or once its
      // media turns out to be missing) is final.
      std::string failure = source_->GetViewerFailure();
      if (!failure.empty()) {
        Fail_(failure);
        return;
      }
      source_->MarkShown();
    }
    CheckBlank_(now);
  }

  void Draw(const base::DepictionDrawContext& context) override {
    if (!failure_.empty()) {
      // (Our host decides its size; a doc-ui viewer pane asks for
      // small ones.)
      placeholder_.Draw(context);
      return;
    }
    if (!source_.exists()) {
      return;
    }
    DrawPicture_(context);
    // Still fetching what it's to show: say so over it, as images do.
    // (Our picture keeps being drawn meanwhile; that's what keeps the
    // viewer running and so loading.) Half the usual size: a viewer's
    // box is a whole pane, where the usual third of it looms.
    if (source_.exists() && source_->IsViewerLoading()) {
      base::DrawDepictionLoading(context, 1.0f / 6.0f);
    }
  }

  void DrawPicture_(const base::DepictionDrawContext& context) {
    const base::DepictionBox& b = context.box;

    // Once per frame (the opaque pass always runs): tell our source
    // how big we show it, in pixels, so it can make its picture land
    // one to one.
    if (!context.transparent) {
      // Through a layered mask we draw over our host's backing
      // ourselves, so keeping transparency costs nothing and lets a
      // translucent backing show through.
      source_->SetViewerOverlay(context.overlay || context.layered_mask);
      source_->SetViewerPixelSize(
          std::max(1, static_cast<int>(
                          std::round(b.width * context.pixels_per_unit))),
          std::max(1, static_cast<int>(
                          std::round(b.height * context.pixels_per_unit))));
    }

    base::TextureAsset* picture = ReadyPicture_();
    if (picture == nullptr) {
      return;
    }
    had_picture_ = true;
    ever_had_picture_ = true;
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
    // Masked, not fully opaque, or an overlay (whose picture may keep
    // its own alpha) needs the transparent pass.
    bool transparent = masked || alpha < 1.0f || context.overlay;
    if (context.transparent != transparent) {
      return;
    }
    // A render view's texture is premultiplied, so our modulate color
    // must be too (see docs/design/premultiplied-alpha.md).
    float cmul = picture->premultiplied() ? alpha : 1.0f;
    float mult[3];
    context.StandardMultiplier(mult);
    base::SimpleComponent c(context.pass);
    c.SetTransparent(transparent);
    c.SetTexture(picture);
    if (masked && context.layered_mask) {
      // All of it in one go: our picture over the host's backing, its
      // layers painted over that. Host opacity applies to the whole;
      // our fade-in just to the picture (fading in over the backing).
      float pmul = picture->premultiplied() ? fade : 1.0f;
      c.SetColor(pmul * mult[0], pmul * mult[1], pmul * mult[2], fade);
      float underlay[4];
      float layer1[4];
      float layer2[4];
      context.StandardLayerColors(underlay, layer1, layer2);
      c.SetLayeredMask(context.mask_texture, underlay, layer1, layer2,
                       context.StandardOpacity());
    } else if (masked) {
      c.SetColor(cmul * mult[0], cmul * mult[1], cmul * mult[2], alpha);
      float frame[3]{context.frame_color[0], context.frame_color[1],
                     context.frame_color[2]};
      context.StandardColor(frame);
      c.SetMaskTexture(context.mask_texture);
      // (The host's frame is drawn as the mask's addition; it follows
      // brightness and color_multiply like the picture does.)
      c.SetMaskAddMult(mult[0], mult[1], mult[2]);
      c.SetColorizeColor(frame[0], frame[1], frame[2]);
    } else {
      c.SetColor(cmul * mult[0], cmul * mult[1], cmul * mult[2], alpha);
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

  auto DrawsHostBacking() const -> bool override {
    return ReadyPicture_() != nullptr;
  }

  /// Our viewer's picture, if we're to draw it.
  auto ReadyPicture_() const -> base::TextureAsset* {
    if (!failure_.empty() || !source_.exists()) {
      return nullptr;
    }
    base::TextureAsset* picture = source_->GetViewerTexture();
    if (picture == nullptr || !picture->loaded()) {
      return nullptr;
    }
    return picture;
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
    // Nothing may throw out of here: we run while a frame is being
    // built, and an exception escaping that leaves drawing wedged. A
    // viewer we can't use however it misbehaves is just one more that
    // can't show us.
    try {
      TryAcquire_();
    } catch (const std::exception& exc) {
      Fail_(std::string("Its viewer is unusable: ") + exc.what());
    }
  }

  void TryAcquire_() {
    auto& objs = g_ui_v1->python->objs();
    PythonRef args = PythonRef::Stolen(
        Py_BuildValue("(sss)", type_id().c_str(), key_.c_str(), json_.c_str()));
    PythonRef viewer =
        objs.Get(UIV1Python::ObjID::kGetLiveDepictionCall).Call(args);
    // Not getting a viewer is final too: its maker choked on what it
    // was given (its exception is logged above), or nothing here makes
    // this kind. Asking again would only fail the same way.
    if (!viewer.exists()) {
      Fail_("Its viewer could not be made from it (see the error above).");
      return;
    }
    if (viewer.get() == Py_None) {
      Fail_("Nothing here makes viewers of this kind.");
      return;
    }
    PythonRef source_obj = viewer.GetAttr("source");
    if (!PythonClassViewerSource::Check(source_obj.get())) {
      Fail_("Its viewer has no usable source.");
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
    acquire_count_++;
    wants_presses_ = viewer.GetAttr("wants_presses").Call().ValueAsBool();
    press_call_ =
        Object::New<base::PythonContextCall>(viewer.GetAttr("handle_press"));
    drag_call_ =
        Object::New<base::PythonContextCall>(viewer.GetAttr("handle_drag"));
    release_call_ =
        Object::New<base::PythonContextCall>(viewer.GetAttr("handle_release"));
  }

  /// Give up for good: draw the placeholder from here on. Let go of our
  /// viewer (unshown, the registry retires it) and say why, once per
  /// distinct broken depiction -- user content can send plenty, and
  /// each should be findable without one bad one repeating.
  void Fail_(const std::string& reason) {
    failure_ = reason;
    source_.Clear();
    viewer_.Release();
    press_call_.Clear();
    drag_call_.Clear();
    release_call_.Clear();
    wants_presses_ = false;
    static std::unordered_set<size_t> warned;
    if (warned.size() < kMaxWarnedFailures
        && warned.insert(std::hash<std::string>{}(json_)).second) {
      g_core->logging->Log(
          LogName::kBaUI, LogLevel::kWarning,
          "Drawing a placeholder for a '" + type_id()
              + "' depiction that can't be shown: " + reason
              + " Depiction json (start): " + json_.substr(0, 200));
    }
  }

  /// Warn (once) if we've been shown a good while and our viewer
  /// never once gave us a picture, without saying it's loading or
  /// broken: the pane just sits blank, which looks the same as
  /// "nothing there yet", so it's otherwise easy to miss. (A viewer
  /// retired before it got going, a renderer never drawing into its
  /// texture, a maker handing back a viewer that never starts, ...)
  void CheckBlank_(millisecs_t now) {
    if (warned_blank_ || ever_had_picture_) {
      return;
    }
    // Only time we're actually shown and not knowingly waiting on
    // something counts: restart the clock after a gap in being shown
    // (we're updated each frame we are) or while loading.
    bool waiting = source_.exists() && source_->IsViewerLoading();
    if (blank_since_ms_ < 0 || waiting || now - last_update_ms_ > kBlankGapMs) {
      blank_since_ms_ = now;
    }
    last_update_ms_ = now;
    if (now - blank_since_ms_ < kBlankWarnMs) {
      return;
    }
    warned_blank_ = true;
    std::string state =
        !source_.exists()
            ? "it has no viewer"
            : (source_->retired()
                   ? "its viewer ('" + source_->GetName() + "') was retired"
                   : "its viewer is '" + source_->GetName() + "'");
    g_core->logging->Log(
        LogName::kBaUI, LogLevel::kWarning,
        "A '" + type_id() + "' viewer depiction (key '" + key_
            + "') has been shown for "
            + std::to_string(kBlankWarnMs / 1000)
            + "s without its viewer ever giving it a picture (not loading,"
              " not failed); "
            + state + "; viewers asked for: "
            + std::to_string(acquire_count_) + ".");
  }

  // Past this many we stop noting which broken depictions we've warned
  // about (and so stop warning); a flood of junk shouldn't grow memory.
  static constexpr size_t kMaxWarnedFailures{256};

  std::string failure_;
  base::DepictionPlaceholder placeholder_;
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
  static constexpr millisecs_t kBlankWarnMs{5000};
  static constexpr millisecs_t kBlankGapMs{500};
  bool ever_had_picture_{};
  bool warned_blank_{};
  millisecs_t blank_since_ms_{-1};
  millisecs_t last_update_ms_{-1};
  int acquire_count_{};
};

}  // namespace

void RegisterViewerDepictionKinds() {
  for (const char* type_id : {kTypeCharacterViewer, kTypeMeshViewer}) {
    base::DepictionRegistry::RegisterKind(
        type_id,
        [type_id](const base::DepictionRegistry::Source& src)
            -> Object::Ref<base::Depiction> {
          // The viewer's maker parses the depiction whole, so we hand
          // along the json we were made from.
          return Object::New<base::Depiction, LiveViewerDepiction>(
              type_id, src.json, src.key);
        });
  }
}

}  // namespace ballistica::ui_v1
