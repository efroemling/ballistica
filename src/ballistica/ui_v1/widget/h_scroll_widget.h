// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_H_SCROLL_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_H_SCROLL_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/container_widget.h"

namespace ballistica::ui_v1 {

// A scroll-box container widget.
class HScrollWidget : public ContainerWidget {
 public:
  HScrollWidget();
  ~HScrollWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto GetWidgetTypeName() -> std::string override { return "scroll"; }
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
  void setColor(float r, float g, float b) {
    color_red_ = r;
    color_green_ = g;
    color_blue_ = b;
  }
  void set_highlight(bool val) { highlight_ = val; }
  auto highlight() const -> bool { return highlight_; }
  void setBorderOpacity(float val) { border_opacity_ = val; }
  auto getBorderOpacity() const -> float { return border_opacity_; }

 protected:
  void UpdateLayout() override;

 private:
  void ClampThumb(bool velocity_clamp, bool position_clamp);

  bool touch_mode_{};
  float color_red_{0.55f};
  float color_green_{0.47f};
  float color_blue_{0.67f};
  bool has_momentum_{true};
  bool trough_dirty_{true};
  bool shadow_dirty_{true};
  bool glow_dirty_{true};
  bool thumb_dirty_{true};
  millisecs_t last_velocity_event_time_millisecs_{};
  float touch_fade_{};
  bool center_small_content_{};
  float center_offset_x_{};
  bool touch_held_{};
  int touch_held_click_count_{};
  float touch_down_x_{};
  float touch_x_{};
  float touch_y_{};
  float touch_start_x_{};
  float touch_start_y_{};
  bool touch_is_scrolling_{};
  bool touch_down_sent_{};
  bool touch_up_sent_{};
  bool new_scroll_touch_{};
  float trough_width_{};
  float trough_height_{};
  float trough_center_x_{};
  float trough_center_y_{};
  float thumb_width_{}, thumb_height_{}, thumb_center_x_{}, thumb_center_y_{};
  float smoothing_amount_{1.0f};
  bool highlight_{true};
  float glow_width_{};
  float glow_height_{};
  float glow_center_x_{};
  float glow_center_y_{};
  float outline_width_{};
  float outline_height_{};
  float outline_center_x_{};
  float outline_center_y_{};
  float border_opacity_{1.0f};
  bool capture_arrows_{};
  bool mouse_held_scroll_down_{};
  bool mouse_held_scroll_up_{};
  bool mouse_held_thumb_{};
  float thumb_click_start_h_{};
  float thumb_click_start_child_offset_h_{};
  bool mouse_held_page_down_{};
  bool mouse_held_page_up_{};
  bool mouse_over_thumb_{};
  bool mouse_over_{};
  float scroll_bar_height_{10.0f};
  float border_width_{2.0f};
  float border_height_{2.0f};
  float child_offset_h_{-9999.0f};
  float child_offset_h_smoothed_{};
  float child_max_offset_{};
  float amount_visible_{};
  bool have_drawn_{};
  millisecs_t inertia_scroll_update_time_{};
  float inertia_scroll_rate_{};
  Object::Ref<base::AppTimer> touch_delay_timer_;
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_H_SCROLL_WIDGET_H_
