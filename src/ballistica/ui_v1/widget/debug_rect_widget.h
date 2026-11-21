// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_DEBUG_RECT_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_DEBUG_RECT_WIDGET_H_

#include <string>
#include <vector>

#include "ballistica/shared/math/rect.h"
#include "ballistica/ui_v1/widget/widget.h"

namespace ballistica::ui_v1 {

/// A debugging aid: an outlined (and optionally filled) rect with an
/// optional text label, for showing layout bounds.
///
/// By default it draws in front of everything else in the UI, scroll
/// fades included: while drawing it only records where it sits on
/// screen, and the recorded rects are drawn after the whole widget tree
/// (see DrawFrontQueue()). Clipping by enclosing scroll areas still
/// applies. To know where it sits, containers track a small screen
/// transform as they draw (see PushChildTransform()), but only while
/// some debug rect exists; otherwise the cost is a counter check.
///
/// Only one top-level window's front rects show at a time: the topmost
/// one (the last direct child of a stack widget drawn in a frame -- a
/// popup over a main window, say -- whether or not it has debug rects
/// of its own). Front rects outside any such window always show.
class DebugRectWidget : public Widget {
 public:
  /// Where a label sits in its rect.
  enum class InfoAnchor : uint8_t {
    kTopLeft,
    kTop,
    kTopRight,
    kLeft,
    kCenter,
    kRight,
    kBottomLeft,
    kBottom,
    kBottomRight,
  };

  DebugRectWidget();
  ~DebugRectWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto GetWidth() -> float override { return width_; }
  auto GetHeight() -> float override { return height_; }
  auto GetWidgetTypeName() -> std::string override { return "debugrect"; }

  void set_size(float width, float height) {
    width_ = width;
    height_ = height;
  }
  void set_color(float r, float g, float b) {
    color_r_ = r;
    color_g_ = g;
    color_b_ = b;
  }
  void set_opacity(float val) { opacity_ = val; }
  void set_edge_width(float val) { edge_width_ = val; }
  void set_fill_opacity(float val) { fill_opacity_ = val; }
  void set_info_anchor(InfoAnchor val) { info_anchor_ = val; }
  void set_front(bool val) { front_ = val; }
  void SetInfo(const std::string& info);

  /// Draw only while this widget is selected (it and all its parents);
  /// nullptr to always draw. Once set, we stop drawing if it dies.
  void SetSelectedWidget(Widget* w);

  /// Whether containers should track screen transforms as they draw
  /// (only while some debug rect exists).
  static auto tracking() -> bool { return live_count_ > 0; }

  /// Start a frame's transparent UI draw (root space is screen space,
  /// shifted by the given offset).
  static void BeginFrame(float x_offset, float y_offset);

  /// Containers call these around drawing each child (only while
  /// tracking()). The child's local point p lands at
  /// ``pivot + scale * p`` in its parent's space, and children may be
  /// clipped to ``clip`` (in the parent's space) if ``has_clip``.
  /// ``toplevel`` is whether the child is a top-level window (its
  /// parent is a stack widget).
  static void PushChildTransform(float x, float y, float scale, bool has_clip,
                                 const Rect& clip, const Widget* child,
                                 bool toplevel);
  static void PopChildTransform();

  /// Draw (and clear) the rects recorded this frame, in front of
  /// everything in root space.
  static void DrawFrontQueue(base::RenderPass* pass);

 private:
  /// A screen transform: local point p lands at (x, y) + s * p.
  struct Transform_ {
    float x{};
    float y{};
    float s{1.0f};
    bool has_clip{};
    Rect clip;  // Screen space.
    /// The top-level window we're in, if any (compared only).
    const Widget* toplevel{};
  };

  /// What a debug rect draws, in some space.
  struct Shape_ {
    Rect rect;
    float color_r{};
    float color_g{};
    float color_b{};
    float opacity{};
    float edge_width{};
    float fill_opacity{};
    InfoAnchor info_anchor{};
    Object::Ref<base::TextGroup> info;
    float info_width{};
    bool has_clip{};
    Rect clip;
    /// The top-level window it's in, if any (compared only).
    const Widget* toplevel{};
  };

  static void DrawShape_(base::RenderPass* pass, const Shape_& shape, float z);

  static int live_count_;
  static std::vector<Transform_> transforms_;
  static std::vector<Shape_> front_queue_;
  /// The last top-level window drawn this frame (the topmost).
  static const Widget* topmost_;

  float width_{};
  float height_{};
  float color_r_{1.0f};
  float color_g_{0.2f};
  float color_b_{1.0f};
  float opacity_{1.0f};
  float edge_width_{3.0f};
  float fill_opacity_{};
  InfoAnchor info_anchor_{InfoAnchor::kTopLeft};
  Object::Ref<base::TextGroup> info_;
  float info_width_{};
  bool front_{true};
  Object::WeakRef<Widget> selected_widget_;
  bool has_selected_widget_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_DEBUG_RECT_WIDGET_H_
