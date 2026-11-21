// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_CONTAINER_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_CONTAINER_WIDGET_H_

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/math/rect.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/ui_v1/widget/widget.h"

namespace ballistica::ui_v1 {

// Base class for widgets that contain other widgets.
class ContainerWidget : public Widget {
 public:
  explicit ContainerWidget(float width = 0.0f, float height = 0.0f);
  ~ContainerWidget() override;

  void Draw(base::RenderPass* pass, bool transparent) override;

  auto HandleMessage(const base::WidgetMessage& m) -> bool override;

  enum class TransitionType {
    kUnset,
    kOutLeft,
    kOutRight,
    kInLeft,
    kInRight,
    kInScale,
    kOutScale
  };

  void SetTransition(TransitionType t);
  /// Make a button our cancel or start button (null for none). The old
  /// one loses the role, and with it the role's colors (see
  /// ButtonWidget::SetRole()).
  void SetCancelButton(ButtonWidget* button);
  void SetStartButton(ButtonWidget* button);

  /// The colors our start and cancel buttons draw in when they have none
  /// of their own. Applies to the current ones right away.
  void SetStartButtonColor(const Vector3f& color);
  void SetCancelButtonColor(const Vector3f& color);
  void SetOnCancelCall(PyObject* call_tuple);

  // Set a widget to selected (must already have been added to dialog). Pass
  // nullptr to deselect widgets.
  void SelectWidget(Widget* w, SelectionCause s = SelectionCause::kNone);
  void ReselectLastSelectedWidget();
  /// Scroll as needed to bring a child into view. Pass animate=false to
  /// snap rather than glide -- see WidgetMessage::animate.
  void ShowWidget(Widget* w, bool animate = true);
  void set_background(bool enable) { background_ = enable; }

  /// Shift where our background art draws, without moving anything else
  /// (children, input, transitions). For working around art whose
  /// placement doesn't suit a particular window shape.
  void set_background_offset(float x, float y) {
    background_offset_x_ = x;
    background_offset_y_ = y;
  }

  /// Scale our background art about its own center (x, y), without
  /// changing anything else; for fine-tuning how the art fits a
  /// particular window shape. Everything that follows the art (its
  /// known-opaque rect, scroll fades blending toward it) follows this.
  void set_background_scale(float x, float y) {
    background_scale_x_ = x;
    background_scale_y_ = y;
  }

  /// Lay our background art out cleanly: our bounds are exactly its
  /// known-opaque area (see GetBackingOpaqueRect()), with the art
  /// hanging out around them, rather than the art being placed around
  /// our bounds by historical fudge factors. Also drops the scale
  /// transition's center fudge, so we zoom about our true center.
  void set_clean_layout(bool val) {
    clean_layout_ = val;
    bg_dirty_ = glow_dirty_ = true;
  }

  /// Which standard window backing art we draw.
  enum class BackingArt : uint8_t {
    /// Picked by our shape.
    kAuto,
    /// window_hsmall_vmed: boxier, for taller windows.
    kTall,
    /// window_hsmall_vsmall: rounder, for squatter windows.
    kSquat,
  };
  void set_backing_art(BackingArt val) {
    backing_art_ = val;
    bg_dirty_ = true;
  }
  void SetRootSelectable(bool enable);
  void set_selectable(bool val) { selectable_ = val; }
  void set_darken_behind(bool val) { darken_behind_ = val; }
  void set_darken_behind_is_permanent(bool val) {
    darken_behind_is_permanent_ = val;
  }

  virtual void SetWidth(float w) {
    bg_dirty_ = glow_dirty_ = true;
    width_ = w;
    MarkForUpdate();
  }

  virtual void SetHeight(float h) {
    bg_dirty_ = glow_dirty_ = true;
    height_ = h;
    MarkForUpdate();
  }

  void SetScaleOriginStackOffset(float x, float y) {
    scale_origin_stack_offset_x_ = x;
    scale_origin_stack_offset_y_ = y;
  }

  // Note: Don't call these on yourself from within your CheckLayout() func.
  // (reason is obvious if you look) - just use your values directly in that
  // case.
  auto GetWidth() -> float override {
    CheckLayout();
    return width_;
  }

  auto GetHeight() -> float override {
    CheckLayout();
    return height_;
  }

  auto IsSelectable() -> bool override { return selectable_; }

  auto HasKeySelectableChild() const -> bool;

  auto is_window_stack() const -> bool { return is_window_stack_; }
  void set_is_window_stack(bool a) { is_window_stack_ = a; }

  auto GetChildCount() const -> int {
    assert(g_base->InLogicThread());
    return static_cast<int>(widgets_.size());
  }
  void Clear();

  void Activate() override;

  /// Add a newly allocated widget to the container. This widget is now
  /// owned by the container and will be disposed by it.
  void AddWidget(Widget* w);

  // Remove a widget from the container.
  void DeleteWidget(Widget* w);

  // Select the next widget in the container's list.
  void SelectNextWidget();

  // Select the previous widget in the container's list.
  void SelectPrevWidget();

  void SelectDownWidget();
  void SelectUpWidget();
  void SelectLeftWidget();
  void SelectRightWidget();

  // Return the currently selected widget, or nullptr if none selected.
  auto selected_widget() -> Widget* { return selected_widget_; }

  auto GetWidgetTypeName() -> std::string override { return "container"; }
  auto HasChildren() const -> bool override { return (!widgets_.empty()); }

  // Whether hitting 'next' at the last widget should loop back to the first.
  // (generally true but list containers may not want)
  auto selection_loops() const -> bool { return selection_loops_; }

  void SetOnActivateCall(PyObject* c);
  void SetOnOutsideClickCall(PyObject* c);

  auto widgets() const -> const std::vector<Object::Ref<Widget> >& {
    return widgets_;
  }

  void set_draggable(bool d) { draggable_ = d; }

  // auto claims_tab() const -> bool { return claims_tab_; }
  // void set_claims_tab(bool c) { claims_tab_ = c; }

  auto claims_left_right() const -> bool { return claims_left_right_; }
  void set_claims_left_right(bool c) { claims_left_right_ = c; }

  auto claims_up_down() const -> bool { return claims_up_down_; }
  void set_claims_up_down(bool c) { claims_up_down_ = c; }

  // If the selection doesn't loop, returns whether a selection loop
  // transfers the message to the parent instead.
  auto selection_loops_to_parent() const -> bool {
    return selection_loops_to_parent_;
  }
  void set_selection_loops_to_parent(bool d) { selection_loops_to_parent_ = d; }

  void set_single_depth(bool s) { single_depth_ = s; }

  // Translate a point in-place into the space of a given child widget.
  void TransformPointToChild(float* x, float* y, const Widget& child) const;
  void TransformPointFromChild(float* x, float* y, const Widget& child) const;

  void set_color(float r, float g, float b, float a) {
    red_ = r;
    green_ = g;
    blue_ = b;
    alpha_ = a;
  }
  auto GetDrawBrightness(millisecs_t time) const -> float override;
  auto IsAcceptingInput() const -> bool override;
  void OnLanguageChange() override;

  void set_selection_loops(bool loops) { selection_loops_ = loops; }
  void set_click_activate(bool enabled) { click_activate_ = enabled; }
  void set_always_highlight(bool enable) { always_highlight_ = enable; }
  void set_claims_outside_clicks(bool val) { claims_outside_clicks_ = val; }
  void set_is_overlay_window_stack(bool val) { is_overlay_window_stack_ = val; }
  void set_is_main_window_stack(bool val) { is_main_window_stack_ = val; }
  void set_should_print_list_exit_instructions(bool v) {
    should_print_list_exit_instructions_ = v;
  }

  // Return the topmost widget that is accepting input. Used for toolbar
  // focusing; may not always equal selected widget if the topmost one is
  // transitioning out, etc.
  auto GetTopmostToolbarInfluencingWidget() -> Widget*;

  auto IsTransitioningOut() const -> bool override;

  /// Color multiplier currently applied to our window backing; > 1 for
  /// the brief glow during a scale-in, otherwise 1. Children that
  /// masquerade as part of the backing can apply it to stay matched.
  auto GetBackingGlowMult() const -> float {
    if (transition_scale_ <= 0.9f && !transitioning_out_) {
      float amt = transition_scale_ / 0.9f;
      return std::min((1.0f - amt) * 4.0f, 2.5f) + amt * 1.0f;
    }
    return 1.0f;
  }

  /// Where and how our window backing draws, for children that redraw
  /// pieces of it over themselves (ScrollWidget's fade edge style).
  struct BackingDrawInfo {
    base::TextureAsset* texture{};
    /// The full backing quad, which the texture spans uniformly
    /// (u left-to-right, v top-down). In the space our children's
    /// positions are in, and before any transition scaling (which
    /// applies to children and backing alike).
    Rect rect;
    /// Ready to pass to SetColor() (already premultiplied as needed).
    float red{}, green{}, blue{}, alpha{};
  };

  /// Fill in our current backing draw info; returns false if we draw
  /// no backing.
  auto GetBackingDrawInfo(BackingDrawInfo* info) const -> bool;

  /// Fill in the rect (in the space our children's positions are in)
  /// known to lie within our backing's fully-opaque pixels; returns
  /// false if we draw no backing or ours isn't calibrated for this.
  auto GetBackingOpaqueRect(Rect* rect) const -> bool;

  auto CoversScreenOpaquely() const -> bool override;

 protected:
  void set_single_depth_root(bool s) { single_depth_root_ = s; }

  // Note that the offsets here are purely for visual transitions and
  // things; the UI itself only knows about the standard widget transform
  // values.
  void DrawChildren(base::RenderPass* pass, bool transparent, float x_offset,
                    float y_offset, float scale);
  void SetSelected(bool s, SelectionCause cause) override;
  void MarkForUpdate();

  // Move/resize the contained widgets.
  virtual void UpdateLayout() {}
  void CheckLayout();

  /// The rect (in our space) our children are clipped to as we draw
  /// them, if any. Only debug rects use this (see DebugRectWidget); the
  /// clipping itself is up to each container's Draw().
  virtual auto GetChildClipRect(Rect* rect) const -> bool { return false; }

  void set_modal_children(bool val) { modal_children_ = val; }

  auto width() const -> float { return width_; }
  auto height() const -> float { return height_; }
  void set_width(float val) { width_ = val; }
  void set_height(float val) { height_ = val; }

 private:
  /// Which standard window backing we draw at our current size, and
  /// where its full quad sits (widget-local, before any background
  /// offset or scale).
  struct BackingLayout {
    bool tall{};  // window_hsmall_vmed; otherwise window_hsmall_vsmall.
    float quad_l{}, quad_b{}, quad_r{}, quad_t{};
    // Legacy layouts fudge these until scaling in/out hits the exact
    // target point; clean ones zoom about their true center.
    float center_fudge_x{}, center_fudge_y{};
  };
  auto CalcBackingLayout_() const -> BackingLayout;

  /// Containers taller than these (height / width) get the taller
  /// backing art unless told otherwise (see CalcBackingLayout_()).
  static constexpr float kLegacyTallAspect{0.6f};
  static constexpr float kCleanLayoutTallAspect{0.59f};

  /// The hand-calibrated known-opaque sub-rect of a standard backing, in
  /// unit coords over its full quad (+-0.5 is the quad's edge).
  static void BackingOpaqueUnitRect_(bool tall, float* l, float* b, float* r,
                                     float* t);

  /// Our backing quad (widget-local), with background offset and scale
  /// applied; what we actually draw.
  void GetPlacedBackingQuad_(const BackingLayout& layout, float* l, float* b,
                             float* r, float* t) const;

  // Calc the widget-local bounds of the hand-calibrated known-opaque
  // sub-rect of our window backing as drawn (offset and scale applied;
  // see CoversScreenOpaquely()); returns false for backing setups with
  // no such calibration.
  auto GetCalibratedOpaqueRegion_(float* l, float* b, float* r, float* t) const
      -> bool;

  // Given a container and a point, returns a selectable widget in the
  // downward direction or nullptr.
  auto GetClosestDownWidget(float x, float y, Widget* ignoreWidget) -> Widget*;
  auto GetClosestUpWidget(float x, float y, Widget* ignoreWidget) -> Widget*;
  auto GetClosestRightWidget(float x, float y, Widget* ignoreWidget) -> Widget*;
  auto GetClosestLeftWidget(float x, float y, Widget* ignoreWidget) -> Widget*;
  auto GetMult(millisecs_t current_time, bool for_glow = false) const -> float;
  void PrintExitListInstructions(millisecs_t old_last_prev_next_time);

  std::vector<Object::Ref<Widget> > widgets_;
  Object::Ref<base::TextureAsset> tex_;
  Object::WeakRef<ButtonWidget> cancel_button_;
  Object::WeakRef<ButtonWidget> start_button_;
  Vector3f start_button_color_{0.2f, 0.8f, 0.55f};
  Vector3f cancel_button_color_{0.7f, 0.4f, 0.34f};
  Widget* selected_widget_{};
  Widget* prev_selected_widget_{};
  Object::Ref<base::MeshAsset> bg_mesh_transparent_;
  Object::Ref<base::MeshAsset> bg_mesh_opaque_;
  TransitionType transition_type_{};
  float width_{};
  float height_{};
  float scale_origin_stack_offset_x_{};
  float scale_origin_stack_offset_y_{};
  float transition_scale_offset_x_{};
  float transition_scale_offset_y_{};
  float red_{0.4f};
  float green_{0.37f};
  float blue_{0.49f};
  float alpha_{1.0f};
  float glow_width_{}, glow_height_{}, glow_center_x_{}, glow_center_y_{};
  float bg_width_{}, bg_height_{}, bg_center_x_{}, bg_center_y_{};
  float transition_target_offset_{};
  float drag_x_{}, drag_y_{};
  float transition_offset_x_{};
  float transition_offset_x_vel_{};
  float transition_offset_x_smoothed_{};
  float transition_offset_y_{};
  float transition_offset_y_vel_{};
  float transition_offset_y_smoothed_{};
  float transition_start_offset_{};
  float transition_scale_{1.0f};
  float d_transition_scale_{};
  float bg_center_fudge_x_{};
  float background_offset_x_{};
  float background_offset_y_{};
  float background_scale_x_{1.0f};
  float background_scale_y_{1.0f};
  float bg_center_fudge_y_{};
  millisecs_t last_activate_time_millisecs_{};
  millisecs_t transition_start_time_{};
  millisecs_t dynamics_update_time_millisecs_{};
  millisecs_t last_prev_next_time_millisecs_{};
  millisecs_t last_list_exit_instructions_print_time_{};
  bool modal_children_{};
  bool selection_loops_{true};
  bool is_main_window_stack_{};
  bool is_overlay_window_stack_{};
  BackingArt backing_art_{BackingArt::kAuto};
  bool bg_dirty_{true};
  bool clean_layout_{};
  bool glow_dirty_{true};
  bool transitioning_{};
  bool pressed_{};
  bool mouse_over_{};
  bool pressed_activate_{};
  bool always_highlight_{};
  bool click_activate_{};
  bool transitioning_out_{};
  bool draggable_{};
  bool dragging_{};
  bool managed_{true};
  bool needs_update_{};
  bool claims_tab_{true};
  bool claims_left_right_{true};
  bool claims_up_down_{true};
  bool selection_loops_to_parent_{};
  bool is_window_stack_{};
  bool background_{true};
  bool darken_behind_{};
  bool darken_behind_is_permanent_{};
  bool root_selectable_{};
  bool selectable_{true};
  bool ignore_input_{};
  bool single_depth_{true};
  bool single_depth_root_{};
  bool should_print_list_exit_instructions_{};
  bool claims_outside_clicks_{};

  // Keep these at the bottom so they're torn down first. ...hmm that seems
  // fragile; should I add explicit code to kill them?
  Object::Ref<base::PythonContextCall> on_activate_call_;
  Object::Ref<base::PythonContextCall> on_outside_click_call_;
  Object::Ref<base::PythonContextCall> on_cancel_call_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_CONTAINER_WIDGET_H_
