// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_WIDGET_H_

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/ui/widget_message.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

// Base class for interface widgets.
class Widget : public Object {
 public:
  /// Only relevant for direct children of the main stack widget. Note that
  /// these are bitmask values so that internal root elements can specific
  /// the entire set of visibilities they apply to.
  enum class ToolbarVisibility : uint16_t {
    kInherit = 0,             // For popups and whatnot - leave toolbar as-is.
    kMenuMinimal = 1,         // Menu, squad, back.
    kMenuMinimalNoBack = 2,   // Menu, squad.
    kMenuStore = 4,           // Menu, squad, level, and soft currency.
    kMenuStoreNoBack = 8,     // Menu, squad, level, and soft currency.
    kMenuReduced = 16,        // Menu, squad, account, inbox, settings, back.
    kMenuReducedNoBack = 32,  // Menu, squad, account, inbox, settings.
    kMenuFull = 64,           // Everything.
    kMenuFullNoBack = 128,    // Everything minus back.
    kMenuFullRoot = 256,      // Obsolete.
    kInGame = 512,            // Menu, squad.
    kGetTokens = 1024,        // Squad, tokens without plus.
    kMenuInGame = 2048,       // Squad, settings.
    kMenuTokens = 4096,       // Squad, tokens.
    kNoMenuMinimal = 8192,    // Squad.
  };

  Widget();
  ~Widget() override;

  /// Activate the widget.
  virtual void Activate();

  /// Draw the widget.
  ///
  /// Widgets are drawn in 2 passes. The first is a front-to-back pass where
  /// opaque parts should be drawn and the second is back-to-front where
  /// transparent stuff should be drawn.
  virtual void Draw(base::RenderPass* pass, bool transparent);

  /// Send a message to the widget; returns whether it was handled.
  virtual auto HandleMessage(const base::WidgetMessage& m) -> bool;

  /// Whether the widget (or its children) is selectable in any way.
  virtual auto IsSelectable() -> bool;

  /// Whether the widget can be selected by default with direction/tab
  /// presses.
  virtual auto IsSelectableViaKeys() -> bool;

  /// Is the widget currently accepting input?
  /// (containers transitioning out may return false here, etc).
  virtual auto IsAcceptingInput() const -> bool;

  void SetOnSelectCall(PyObject* call_obj);

  void AddOnDeleteCall(PyObject* call_obj);

  /// Globally select this widget.
  void GlobalSelect();

  /// Show this widget if possible (by scrolling to it, etc).
  void Show();

  /// Returns true if the widget is the currently selected child of its
  /// parent. Note that this does not mean that the parent is selected,
  /// however.
  auto selected() const -> bool { return selected_; }

  /// Returns true if the widget hierarchy is selected (all of its parents).
  auto IsHierarchySelected() const -> bool;

  /// Only really applicable to container widgets.
  void SetToolbarVisibility(ToolbarVisibility v);
  auto toolbar_visibility() const -> ToolbarVisibility {
    return toolbar_visibility_;
  }

  // FIXME: Replace this with GetBounds so we can do different alignments/etc.
  virtual auto GetWidth() -> float { return 0.0f; }
  virtual auto GetHeight() -> float { return 0.0f; }

  /// If this widget is in a container, return it.
  auto parent_widget() const -> ContainerWidget* { return parent_widget_; }

  /// Return the container_widget containing this widget, or the
  /// owner-widget if there is no parent.
  auto GetOwnerWidget() const -> Widget*;

  auto down_widget() const -> Widget* { return down_widget_.get(); }
  void SetDownWidget(Widget* w);
  auto up_widget() const -> Widget* { return up_widget_.get(); }
  void SetUpWidget(Widget* w);
  auto left_widget() const -> Widget* { return left_widget_.get(); }
  void SetLeftWidget(Widget* w);
  auto right_widget() const -> Widget* { return right_widget_.get(); }
  void SetRightWidget(Widget* w);

  void set_auto_select(bool enable) { auto_select_ = enable; }
  auto auto_select() const -> bool { return auto_select_; }

  // If neighbors are locked, calls to set the up/down/left/right widget
  // will fail. (useful for global toolbar widgets where we don't want users
  // redirecting them to transient per-window stuff).
  void set_neighbors_locked(bool locked) { neighbors_locked_ = locked; }

  // Widgets normally draw with a local depth range of 0-1. It can be useful
  // to limit drawing to a subsection of that region however (for manually
  // resolving overlap issues with widgets at the same depth, etc).
  void set_depth_range(float min_depth, float max_depth) {
    assert(min_depth >= 0.0f && min_depth <= 1.0f);
    assert(max_depth >= min_depth && max_depth <= 1.0f);
    depth_range_min_ = min_depth;
    depth_range_max_ = max_depth;
  }

  auto depth_range_min() const -> float { return depth_range_min_; }
  auto depth_range_max() const -> float { return depth_range_max_; }

  // For use by ContainerWidgets (we probably should just add this
  // functionality to all widgets).
  void set_parent_widget(ContainerWidget* c) { parent_widget_ = c; }

  auto IsInMainStack() const -> bool;
  auto IsInOverlayStack() const -> bool;

  // For use when embedding widgets inside others manually. This will allow
  // proper selection states/etc to trickle down to the lowest-level child.
  void set_owner_widget(Widget* o) { owner_widget_ = o; }
  virtual auto GetWidgetTypeName() -> std::string { return "widget"; }
  virtual auto HasChildren() const -> bool { return false; }

  enum class SelectionCause : uint8_t { kNextSelected, kPrevSelected, kNone };

  void set_translate(float x, float y) {
    tx_ = x;
    ty_ = y;
  }
  void set_stack_offset(float x, float y) {
    stack_offset_x_ = x;
    stack_offset_y_ = y;
  }
  auto tx() const { return tx_; }
  auto ty() const { return ty_; }

  // Positional offset used when this widget is part of a stack.
  auto stack_offset_x() const { return stack_offset_x_; }
  auto stack_offset_y() const { return stack_offset_y_; }

  // Overall scale of the widget.
  auto scale() const { return scale_; }
  void set_scale(float s) { scale_ = s; }

  // Return the widget's center in its parent's space.
  virtual void GetCenter(float* x, float* y);

  // Translates a point from screen space to widget space.
  void ScreenPointToWidget(float* x, float* y) const;
  void WidgetPointToScreen(float* x, float* y) const;

  // Draw-control parents are used to give one widget some basic visual
  // control over others, allowing them to inherit things like
  // draw-brightness and tilt shift (for cases such as images drawn over
  // buttons). Ideally we'd probably want to extend the parent mechanism for
  // this, but this works for now.
  auto draw_control_parent() const -> Widget* {
    return draw_control_parent_.get();
  }
  void set_draw_control_parent(Widget* w) { draw_control_parent_ = w; }

  // Can be used to ask link-parents how bright to draw. Note: make sure the
  // value returned here does not get changed when draw() is run, since
  // parts of draw-controlled children may query this before draw() and
  // parts after. (and they need to line up visually)
  virtual auto GetDrawBrightness(millisecs_t current_time) const -> float;

  /// Is this widget in the process of transitioning out before dying?
  virtual auto IsTransitioningOut() const -> bool;

  // Extra buffer added around widgets when they are centered-on.
  void set_show_buffer_top(float b) { show_buffer_top_ = b; }
  void set_show_buffer_bottom(float b) { show_buffer_bottom_ = b; }
  void set_show_buffer_left(float b) { show_buffer_left_ = b; }
  void set_show_buffer_right(float b) { show_buffer_right_ = b; }

  auto show_buffer_top() const -> float { return show_buffer_top_; }
  auto show_buffer_bottom() const -> float { return show_buffer_bottom_; }
  auto show_buffer_left() const -> float { return show_buffer_left_; }
  auto show_buffer_right() const -> float { return show_buffer_right_; }

  auto NewPyRef() -> PyObject* { return GetPyWidget_(true); }
  auto BorrowPyRef() -> PyObject* { return GetPyWidget_(false); }

  auto HasPyRef() -> bool { return (py_ref_ != nullptr); }

  // For use by containers to flag widgets as invisible (for drawing
  // efficiency).
  void set_visible_in_container(bool val) { visible_in_container_ = val; }
  auto visible_in_container() const -> bool { return visible_in_container_; }

  virtual void OnLanguageChange() {}

  // Primitive janktastic child culling for use by containers (should really
  // implement something more proper).
  auto simple_culling_v() const -> float { return simple_culling_v_; }
  auto simple_culling_h() const -> float { return simple_culling_h_; }
  auto simple_culling_bottom() const -> float { return simple_culling_bottom_; }
  auto simple_culling_top() const -> float { return simple_culling_top_; }
  auto simple_culling_left() const -> float { return simple_culling_left_; }
  auto simple_culling_right() const -> float { return simple_culling_right_; }
  void set_simple_culling_h(float val) { simple_culling_h_ = val; }
  void set_simple_culling_v(float val) { simple_culling_v_ = val; }
  void set_simple_culling_left(float val) { simple_culling_left_ = val; }
  void set_simple_culling_right(float val) { simple_culling_right_ = val; }
  void set_simple_culling_bottom(float val) { simple_culling_bottom_ = val; }
  void set_simple_culling_top(float val) { simple_culling_top_ = val; }

  /// Should only be called by a widget's parent container.
  virtual void SetSelected(bool s, SelectionCause cause);

  /// Set widget ID; can be used to lookup particular widgets.
  void set_id(const std::string& id) {
    // It is caller's responsibility to only call us once before we are
    // added to a parent widget.
    assert(!id_.has_value());
    assert(parent_widget_ == nullptr);

    id_ = id;
  }
  auto id() const { return id_; }

 private:
  auto GetPyWidget_(bool new_ref) -> PyObject*;

  std::optional<std::string> id_;
  Object::Ref<base::PythonContextCall> on_select_call_;
  std::vector<Object::Ref<base::PythonContextCall> > on_delete_calls_;
  Object::WeakRef<Widget> draw_control_parent_;
  Object::WeakRef<Widget> down_widget_;
  Object::WeakRef<Widget> up_widget_;
  Object::WeakRef<Widget> left_widget_;
  Object::WeakRef<Widget> right_widget_;
  ContainerWidget* parent_widget_{};
  PyObject* py_ref_{};
  Widget* owner_widget_{};
  ToolbarVisibility toolbar_visibility_{ToolbarVisibility::kMenuMinimalNoBack};
  float simple_culling_h_{-1.0f};
  float simple_culling_v_{-1.0f};
  float simple_culling_left_{};
  float simple_culling_right_{};
  float simple_culling_bottom_{};
  float simple_culling_top_{};
  float show_buffer_top_{20.0f};
  float show_buffer_bottom_{20.0f};
  float show_buffer_left_{20.0f};
  float show_buffer_right_{20.0f};
  float tx_{};
  float ty_{};
  float stack_offset_x_{};
  float stack_offset_y_{};
  float scale_{1.0f};
  float depth_range_min_{};
  float depth_range_max_{1.0f};
  bool selected_{};
  bool visible_in_container_{true};
  bool neighbors_locked_{};
  bool auto_select_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_WIDGET_H_
