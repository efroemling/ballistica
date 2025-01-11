// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_SCROLL_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_SCROLL_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// A scroll-box container widget.
class ScrollWidget : public ContainerWidget {
 public:
  ScrollWidget();
  ~ScrollWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto GetWidgetTypeName() -> std::string override { return "scroll"; }
  auto set_capture_arrows(bool val) { capture_arrows_ = val; }
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
  auto set_center_small_content(bool val) {
    center_small_content_ = val;
    MarkForUpdate();
  }
  auto set_center_small_content_horizontally(bool val) {
    center_small_content_horizontally_ = val;
    MarkForUpdate();
  }
  void OnTouchDelayTimerExpired();
  auto set_color(float r, float g, float b) {
    color_red_ = r;
    color_green_ = g;
    color_blue_ = b;
  }
  auto set_highlight(bool val) { highlight_ = val; }
  auto highlight() const -> bool { return highlight_; }
  auto set_border_opacity(float val) { border_opacity_ = val; }
  auto border_opacity() const -> float { return border_opacity_; }

 protected:
  void UpdateLayout() override;

 private:
  void ClampThumb_(bool velocity_clamp, bool position_clamp);

  Object::Ref<base::AppTimer> touch_delay_timer_;
  millisecs_t last_sub_widget_h_scroll_claim_time_{};
  millisecs_t last_velocity_event_time_millisecs_{};
  millisecs_t inertia_scroll_update_time_{};
  int touch_held_click_count_{};
  float color_red_{0.55f};
  float color_green_{0.47f};
  float color_blue_{0.67f};
  float avg_scroll_speed_h_{};
  float avg_scroll_speed_v_{};
  float center_offset_y_{};
  float touch_down_y_{};
  float touch_x_{};
  float touch_y_{};
  float touch_start_x_{};
  float touch_start_y_{};
  float trough_width_{};
  float trough_height_{};
  float trough_center_x_{};
  float trough_center_y_{};
  float thumb_width_{};
  float thumb_height_{};
  float thumb_center_x_{};
  float thumb_center_y_{};
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
  float thumb_click_start_v_{};
  float thumb_click_start_child_offset_v_{};
  float scroll_bar_width_{10.0f};
  float border_width_{2.0f};
  float border_height_{2.0f};
  float child_offset_v_{};
  float child_offset_v_smoothed_{};
  float child_max_offset_{};
  float amount_visible_{};
  float inertia_scroll_rate_{};
  bool mouse_held_page_down_{};
  bool mouse_held_page_up_{};
  bool mouse_over_thumb_{};
  bool touch_is_scrolling_{};
  bool touch_down_sent_{};
  bool touch_up_sent_{};
  bool touch_mode_{};
  bool has_momentum_{true};
  bool trough_dirty_{true};
  bool shadow_dirty_{true};
  bool glow_dirty_{true};
  bool thumb_dirty_{true};
  bool center_small_content_{};
  bool center_small_content_horizontally_{};
  bool touch_held_{};
  bool highlight_{true};
  bool capture_arrows_{false};
  bool mouse_held_scroll_down_{};
  bool mouse_held_scroll_up_{};
  bool mouse_held_thumb_{};
  bool have_drawn_{};
  bool touch_down_passed_{};
  bool child_is_scrolling_{};
  bool child_disowned_scroll_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_SCROLL_WIDGET_H_
