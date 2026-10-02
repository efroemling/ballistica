// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_SCROLL_WIDGET_H_
#define BALLISTICA_UI_V1_WIDGET_SCROLL_WIDGET_H_

#include <string>

#include "ballistica/ui_v1/widget/container_widget.h"
#include "ballistica/ui_v1/widget/fading_scroll_thumb.h"

namespace ballistica::ui_v1 {

// A scroll-box container widget.
class ScrollWidget : public ContainerWidget {
 public:
  ScrollWidget();
  ~ScrollWidget() override;
  void Draw(base::RenderPass* pass, bool transparent) override;
  auto HandleMessage(const base::WidgetMessage& m) -> bool override;
  auto GetWidgetTypeName() -> std::string override { return "scroll"; }
  auto GetScrollState() -> std::optional<ScrollState> override;
  auto SetScrollOffset(float offset) -> bool override;
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

  /// Hide our border (and selection glow) entirely while all our content
  /// fits, since there is then nothing to scroll.
  void set_hide_border_when_fits(bool val) { hide_border_when_fits_ = val; }

  /// Whether to draw our scroll bar (trough and thumb) and let the mouse
  /// grab it. Scrolling itself (wheel, touch, keys) is unaffected, and
  /// layout is too: the space the bar would occupy stays as it was.
  void set_scrollbar_visible(bool val) { scrollbar_visible_ = val; }

  /// Draw our scroll bar as a thin translucent thumb over our content that
  /// fades in while wanted (scrolling, hovered, dragged) and back out after,
  /// as HScrollWidget's does, instead of a trough and thumb of its own.
  /// With it there is no bar to leave room for. Only the thumb itself is
  /// grabbable (no paging by clicking the track), so content under the
  /// rest of the bar's strip stays clickable.
  void set_fading_scrollbar(bool val) {
    fading_scrollbar_ = val;
    thumb_dirty_ = true;
  }

  /// Lay our content out with none of our historical fudge offsets: it
  /// starts right at our left edge (centered exactly when centering) and
  /// spans our full height (no border/margin inset top and bottom),
  /// clipped exactly to our bounds. Off by default so existing ui keeps
  /// its layout; callers laying out against our exact bounds (doc-ui)
  /// turn it on.
  void set_clean_layout(bool val) {
    clean_layout_ = val;
    MarkForUpdate();
  }

 protected:
  void UpdateLayout() override;

 private:
  void ClampScrolling_(bool velocity_clamp, bool position_clamp,
                       millisecs_t current_time_millisecs);
  void UpdateScrolling_(millisecs_t current_time_millisecs);

  /// Border opacity as drawn: border_opacity_, or zero when hiding it
  /// because everything fits.
  auto DrawnBorderOpacity_() const -> float;

  /// Space our content keeps from our top and bottom edges (the
  /// historical border-plus-margin inset; none with clean layout).
  auto ContentMarginV_() const -> float;

  /// Our fading thumb's rect in our local space for the given scroll
  /// offset; also its track's height via ``track_height``.
  auto FadingThumbRect_(float offset, float* track_height) const -> Rect;

  Object::Ref<base::AppTimer> touch_delay_timer_;
  FadingScrollThumb thumb_;
  seconds_t last_mouse_move_time_{};
  seconds_t create_time_{};
  /// Our scroll offset as of our fading thumb's last update (any change
  /// shows it).
  float thumb_last_offset_{};
  // millisecs_t last_sub_widget_h_scroll_claim_time_{};
  millisecs_t last_v_scroll_event_time_millisecs_{};
  millisecs_t inertia_scroll_update_time_millisecs_{};
  millisecs_t last_touch_held_time_{};
  int touch_held_click_count_{};
  float color_red_{0.55f};
  float color_green_{0.47f};
  float color_blue_{0.67f};
  float scroll_v_accum_{};
  float scroll_v_accum_smoothed_{};
  float scroll_h_accum_{};
  float scroll_h_accum_smoothed_{};
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
  bool hide_border_when_fits_{};
  bool scrollbar_visible_{true};
  bool fading_scrollbar_{};
  bool clean_layout_{};
  bool mouse_over_{};
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
  bool last_scroll_was_touch_{};
  bool handling_deferred_click_{};
  bool mouse_held_page_down_{};
  bool mouse_held_page_up_{};
  bool hovering_thumb_{};
  bool touch_is_scrolling_{};
  bool touch_down_sent_{};
  bool touch_up_sent_{};
  bool has_momentum_{};
  bool trough_dirty_{true};
  bool shadow_dirty_{true};
  bool glow_dirty_{true};
  bool thumb_dirty_{true};
  bool center_small_content_{};
  bool center_small_content_horizontally_{};
  bool touch_held_{};
  bool touch_moved_significantly_{};
  bool highlight_{true};
  bool capture_arrows_{};
  bool mouse_held_scroll_down_{};
  bool mouse_held_scroll_up_{};
  bool mouse_held_thumb_{};
  bool have_drawn_{};
  bool touch_down_passed_{};
  bool child_is_scrolling_{};
  bool child_disowned_scroll_{};
  bool last_mouse_move_in_bounds_{};
  bool should_pass_h_scroll_to_children_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_SCROLL_WIDGET_H_
