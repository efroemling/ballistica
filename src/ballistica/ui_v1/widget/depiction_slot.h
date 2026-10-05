// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_DEPICTION_SLOT_H_
#define BALLISTICA_UI_V1_WIDGET_DEPICTION_SLOT_H_

#include <optional>
#include <string>

#include "ballistica/base/depiction/depiction.h"
#include "ballistica/ui_v1/widget/widget.h"

namespace ballistica::ui_v1 {

/// A depiction (bacommon.depiction) shown by a ui widget: the ui side
/// of base::Depiction, carried by widgets that can show one in place of
/// their usual art (ImageWidget, ButtonWidget). The widget supplies the
/// box and host state each draw; the depiction decides what is drawn
/// there. Kinds this build can't draw show the placeholder (see
/// base::DepictionRegistry).
///
/// A depiction with a shape of its own is fitted inside the box by our
/// alignment. Input reaches the depiction only if the widget routes it
/// here (HandleMessage) and take_input is set, and then only for
/// depictions taking some (a live viewer's poke-to-jump, say): a
/// depiction on a button must never swallow the button's press.
///
/// Optional pane styling -- a backing color (drawn beneath the
/// depiction, and all that shows while it has nothing) and a frame
/// color for the green channel of the widget's mask -- is what lets a
/// doc-ui viewer pane be a plain depiction host. Design:
/// docs/initiatives/depictions.md.
class DepictionSlot {
 public:
  /// Host state and placement for one draw.
  struct DrawArgs {
    Widget* owner{};
    base::RenderPass* pass{};
    bool transparent{};
    float width{};
    float height{};

    /// Drawn offset (tilt, slide-in transitions) and scale about the
    /// box's center (scale-in transitions); these don't affect
    /// pixels-per-unit, which follows the settled box.
    float offset_x{};
    float offset_y{};
    float scale{1.0f};
    float brightness{1.0f};
    float opacity{1.0f};
    bool disabled{};

    /// Cuts the edges of the depiction and backing (see
    /// base::DepictionDrawContext::mask_texture). Null for none.
    base::TextureAsset* mask_texture{};
  };

  DepictionSlot();
  ~DepictionSlot();

  /// Show a depiction from its json (empty for none). Unchanged json
  /// keeps the depiction we have. Logic thread only.
  void SetDepiction(const std::string& json);

  /// Whether we have a depiction set (or a backing to draw); widgets
  /// draw us in place of their own art when so.
  auto active() const -> bool { return !json_.empty() || has_backing_; }

  /// What we're showing, for kinds with something long-lived behind
  /// them (see base::DepictionRegistry::Create). Unique to us unless
  /// set; applies to depictions set afterward.
  void set_key(const std::string& val) { key_ = val; }

  void set_h_align(base::DepictionHAlign val) { h_align_ = val; }
  void set_v_align(base::DepictionVAlign val) { v_align_ = val; }
  void set_take_input(bool val) { take_input_ = val; }

  /// Tint the box our depiction reports covering (its content box; see
  /// GetContentBox), for checking that what it draws matches what it
  /// reports -- and so where a hit-tested host takes presses.
  void set_debug(bool val) { debug_ = val; }
  void set_frame_color(float r, float g, float b) {
    frame_color_[0] = r;
    frame_color_[1] = g;
    frame_color_[2] = b;
  }
  void set_backing_color(float r, float g, float b) {
    has_backing_ = true;
    backing_color_[0] = r;
    backing_color_[1] = g;
    backing_color_[2] = b;
  }

  void Draw(const DrawArgs& args);

  /// Route a message to the depiction (if take_input is set and it
  /// takes input). Coords are in the owner's space; returns whether
  /// it was claimed.
  auto HandleMessage(const base::WidgetMessage& m, float width, float height)
      -> bool;

  /// What our depiction covers of a box of this size at its origin
  /// (fitted by our alignment; see base::Depiction::GetContentBox),
  /// or none if we have no depiction. Ignores draw-time offsets
  /// (tilt, transitions), as hit-testing should.
  auto GetContentBox(float width, float height) const
      -> std::optional<base::DepictionBox>;

  /// The depiction's Python control object, if it offers one (see
  /// base::Depiction::GetPythonControl). Borrowed.
  auto GetPythonControl() -> PyObject*;

  /// The depiction's flat-color override, if it offers one (see
  /// base::Depiction::GetTintControl). Borrowed; don't hold it.
  auto GetTintControl() -> base::DepictionTintControl*;

 private:
  void DrawBacking_(const DrawArgs& args, const base::DepictionBox& box);
  void DrawDebugBox_(const DrawArgs& args, const base::DepictionBox& box);
  void Release_();

  std::string json_;
  std::string key_;
  Object::Ref<base::Depiction> depiction_;
  base::DepictionHAlign h_align_{base::DepictionHAlign::kCenter};
  base::DepictionVAlign v_align_{base::DepictionVAlign::kCenter};
  bool take_input_{};
  bool pressed_{};
  bool debug_{};
  float frame_color_[3]{1.0f, 1.0f, 1.0f};
  bool has_backing_{};
  float backing_color_[3]{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_DEPICTION_SLOT_H_
