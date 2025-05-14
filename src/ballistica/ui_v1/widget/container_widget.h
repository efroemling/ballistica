// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_CONTAINER_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_CONTAINER_WIDGET_H_

#include <string>
#include <vector>

#include "ballistica/base/base.h"
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
  void SetCancelButton(ButtonWidget* button);
  void SetStartButton(ButtonWidget* button);
  void SetOnCancelCall(PyObject* call_tuple);

  // Set a widget to selected (must already have been added to dialog). Pass
  // nullptr to deselect widgets.
  void SelectWidget(Widget* w, SelectionCause s = SelectionCause::kNone);
  void ReselectLastSelectedWidget();
  void ShowWidget(Widget* w);
  void set_background(bool enable) { background_ = enable; }
  void SetRootSelectable(bool enable);
  void set_selectable(bool val) { selectable_ = val; }

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

  // Add a newly allocated widget to the container.
  // This widget is now owned by the container and will be disposed by it.
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

  void set_modal_children(bool val) { modal_children_ = val; }

  auto width() const -> float { return width_; }
  auto height() const -> float { return height_; }
  void set_width(float val) { width_ = val; }
  void set_height(float val) { height_ = val; }

 private:
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
  Widget* selected_widget_{};
  Widget* prev_selected_widget_{};
  base::SysMeshID bg_mesh_transparent_i_d_{};
  base::SysMeshID bg_mesh_opaque_i_d_{};
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
  millisecs_t last_activate_time_millisecs_{};
  millisecs_t transition_start_time_{};
  millisecs_t dynamics_update_time_millisecs_{};
  millisecs_t last_prev_next_time_millisecs_{};
  millisecs_t last_list_exit_instructions_print_time_{};
  bool modal_children_{};
  bool selection_loops_{true};
  bool is_main_window_stack_{};
  bool is_overlay_window_stack_{};
  bool bg_dirty_{true};
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
