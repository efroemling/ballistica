// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_H_SCROLL_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_H_SCROLL_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// A horizontal scroll-box container widget.
class HScrollWidget : public ContainerWidget {
 public:
  HScrollWidget();
  ~HScrollWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto GetWidgetTypeName() -> std::string override { return "hscroll"; }
  void set_capture_arrows(bool val) { capture_arrows_ = val; }
  void SetWidth(float w) override {
    trough_dirty_ = shadow_dirty_ = glow_dirty_ = thumb_dirty_ = true;
    set_width(w);
    MarkForUpdate();
  }
  void SetHeight(float h) override {
    trough_dirty_ = shadow_dirty_ = glow_dirty_ = thumb_dirty_ = true;
    set_height(h);
    MarkForUpdate();
  }
  void SetCenterSmallContent(bool val) {
    center_small_content_ = val;
    MarkForUpdate();
  }
  void OnTouchDelayTimerExpired();
  void SetColor(float r, float g, float b) {
    color_red_ = r;
    color_green_ = g;
    color_blue_ = b;
  }
  void set_highlight(bool val) { highlight_ = val; }
  auto highlight() const -> bool { return highlight_; }
  void setBorderOpacity(float val) { border_opacity_ = val; }
  auto getBorderOpacity() const -> float { return border_opacity_; }

  /// Extra inset for the page-left/page-right buttons from our left
  /// and right edges. For scrolls extended across screen margins,
  /// this keeps the buttons anchored to the virtual rect instead of
  /// drifting into the margins with the widget edge.
  void set_button_inset_left(float val) { button_inset_left_ = val; }
  void set_button_inset_right(float val) { button_inset_right_ = val; }

  /// Whether our page-left/page-right buttons animate in when we first
  /// appear. Off by default, so a freshly-made scroll draws them at
  /// their final form immediately; ui that animates its own contents in
  /// can turn this on so the buttons arrive along with everything else.
  /// Only meaningful before our first draw.
  void set_transition_in(bool val) { transition_in_ = val; }

 protected:
  void UpdateLayout() override;

 private:
  void ClampScrolling_(bool velocity_clamp, bool position_clamp,
                       millisecs_t current_time_millisecs);
  void UpdateScrolling_(millisecs_t current_time);
  auto ShouldShowPageLeftButton_() -> bool;
  auto ShouldShowPageRightButton_() -> bool;
  void UpdatePageLeftRightButtons_(seconds_t display_time_elapsed);
  void SnapPageLeftRightButtons_();
  /// Rebuild thumb_round_mesh_ if the thumb's size has changed. Ninepatch
  /// corners must not be scaled (it would distort them), so the mesh is
  /// built at exact size and only translated when drawn.
  void EnsureThumbRoundMesh_(float w, float h);
  /// Left edge x of the page-left/page-right buttons (insets applied).
  auto PageLeftButtonX_() const -> float;
  auto PageRightButtonX_() const -> float;

  Object::Ref<base::AppTimer> touch_delay_timer_;
  /// Rounded-rect thumb mesh, built at exact pixel size (see
  /// EnsureThumbRoundMesh_).
  Object::Ref<base::NinePatchMesh> thumb_round_mesh_;
  float thumb_round_mesh_width_{-1.0f};
  float thumb_round_mesh_height_{-1.0f};
  /// The thumb's rect, in our local space.
  float thumb_rect_left_{};
  float thumb_rect_bottom_{};
  float thumb_rect_width_{};
  float thumb_rect_height_{};
  seconds_t last_scroll_bar_show_time_{};
  seconds_t last_mouse_move_time_{};
  millisecs_t last_h_scroll_event_time_millisecs_{};
  float color_red_{0.55f};
  float color_green_{0.47f};
  float color_blue_{0.67f};
  float touch_fade_{};
  float center_offset_x_{};
  float touch_down_x_{};
  float touch_x_{};
  float touch_y_{};
  float touch_start_x_{};
  float touch_start_y_{};
  float trough_width_{};
  float trough_height_{};
  float trough_center_x_{};
  float trough_center_y_{};
  float smoothing_amount_{1.0f};
  float glow_width_{};
  float glow_height_{};
  float glow_center_x_{};
  float glow_center_y_{};
  float outline_width_{};
  float outline_height_{};
  float outline_center_x_{};
  float outline_center_y_{};
  float border_opacity_{1.0f};
  float thumb_click_start_h_{};
  float thumb_click_start_child_offset_h_{};
  float scroll_bar_height_{12.0f};
  float border_width_{2.0f};
  float border_height_{2.0f};
  float child_offset_h_{-9999.0f};
  float child_offset_h_smoothed_{};
  float child_max_offset_{};
  float amount_visible_{};
  float inertia_scroll_rate_{};
  float page_left_button_presence_{};
  float page_right_button_presence_{};
  float button_inset_left_{};
  float button_inset_right_{};
  float scroll_h_accum_{};
  millisecs_t inertia_scroll_update_time_millisecs_{};
  int touch_held_click_count_{};
  bool handling_deferred_click_{};
  bool touch_is_scrolling_{};
  bool touch_down_sent_{};
  bool touch_up_sent_{};
  bool new_scroll_touch_{};
  bool touch_held_{};
  bool has_momentum_{};
  bool trough_dirty_{true};
  bool shadow_dirty_{true};
  bool glow_dirty_{true};
  bool thumb_dirty_{true};
  bool center_small_content_{};
  bool highlight_{true};
  bool capture_arrows_{};
  bool mouse_held_scroll_down_{};
  bool mouse_held_scroll_up_{};
  bool mouse_held_thumb_{};
  bool mouse_held_page_down_{};
  bool mouse_held_page_up_{};
  bool hovering_thumb_{};
  bool mouse_over_{};
  bool have_drawn_{};
  bool hovering_page_left_{};
  bool page_left_pressed_{};
  bool hovering_page_right_{};
  bool page_right_pressed_{};
  bool last_mouse_move_in_bounds_{};
  bool last_scroll_was_touch_{};
  bool transition_in_{};
  bool page_buttons_initialized_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_H_SCROLL_WIDGET_H_
