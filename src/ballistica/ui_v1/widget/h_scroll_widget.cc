// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/h_scroll_widget.h"

#include <algorithm>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/ui/ui.h"

namespace ballistica::ui_v1 {

static const float kMarginH{5.0f};

static const float kPageButtonInset{25.0f};
static const float kPageButtonSize{80.0f};

HScrollWidget::HScrollWidget() {
  set_draggable(false);
  set_claims_left_right(false);
}

HScrollWidget::~HScrollWidget() = default;
auto HScrollWidget::CanScrollLeft_() -> bool {
  return child_offset_h_ < child_max_offset_;
}
auto HScrollWidget::CanScrollRight_() -> bool { return child_offset_h_ > 0.0f; }

void HScrollWidget::OnTouchDelayTimerExpired() {
  if (touch_held_) {
    // Pass a mouse-down event if we haven't moved.
    if (!touch_is_scrolling_ && !touch_down_sent_) {
      // Gather up any user code triggered by this stuff and run it at the end
      // before we return.
      base::UI::OperationContext ui_op_context;

      ContainerWidget::HandleMessage(base::WidgetMessage(
          base::WidgetMessage::Type::kMouseDown, nullptr, touch_x_, touch_y_,
          static_cast<float>(touch_held_click_count_)));
      touch_down_sent_ = true;

      // Run any calls built up by UI callbacks.
      ui_op_context.Finish();
    }
  }

  // Clean ourself out.
  touch_delay_timer_.Clear();
}

void HScrollWidget::ClampThumb_(bool velocity_clamp, bool position_clamp) {
  BA_DEBUG_UI_READ_LOCK;  // Make sure hierarchy doesn't change under us.
  bool is_scrolling = (touch_held_ || !has_momentum_);
  float strong_force;
  float weak_force;
  if (g_base->ui->touch_mode()) {
    strong_force = -0.12f;
    weak_force = -0.004f;
  } else {
    strong_force = -0.012f;
    weak_force = -0.004f;
  }
  auto i = widgets().begin();
  if (i != widgets().end()) {
    float child_w = (**i).GetWidth();

    if (velocity_clamp) {
      if (child_offset_h_ < 0.0f) {
        // Even in velocity case do some sane clamping.
        float diff = child_offset_h_;
        inertia_scroll_rate_ +=
            diff * (is_scrolling ? strong_force : weak_force);
        inertia_scroll_rate_ *= 0.9f;

      } else if (child_offset_h_
                 > child_w - (width() - 2.0f * (border_width_ + kMarginH))) {
        float diff =
            child_offset_h_
            - (child_w
               - std::min(child_w,
                          (width() - 2.0f * (border_width_ + kMarginH))));
        inertia_scroll_rate_ +=
            diff * (is_scrolling ? strong_force : weak_force);
        inertia_scroll_rate_ *= 0.9f;
      }
    }

    // Hard clipping if we're dragging the scrollbar.
    if (position_clamp) {
      if (child_offset_h_smoothed_
          > child_w - (width() - 2.0f * (border_width_ + kMarginH))) {
        child_offset_h_smoothed_ =
            child_w - (width() - 2.0f * (border_width_ + kMarginH));
      }
      if (child_offset_h_smoothed_ < 0.0f) {
        child_offset_h_smoothed_ = 0.0f;
      }
      if (child_offset_h_
          > child_w - (width() - 2.0f * (border_width_ + kMarginH))) {
        child_offset_h_ =
            child_w - (width() - 2.0f * (border_width_ + kMarginH));
      }
      if (child_offset_h_ < 0.0f) {
        child_offset_h_ = 0.0f;
      }
    }
  }
}

auto HScrollWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  BA_DEBUG_UI_READ_LOCK;  // Make sure hierarchy doesn't change under us.
  bool claimed = false;
  bool pass = true;
  float bottom_overlap = 3;
  switch (m.type) {
    case base::WidgetMessage::Type::kShow: {
      claimed = true;
      pass = false;
      auto i = widgets().begin();
      if (i == widgets().end()) {
        break;
      }
      float scroll_child_width = (**i).GetWidth();

      float target_x{m.fval1};
      float target_width{m.fval3};

      float vis_width{(width() - 2.0f * (border_width_ + kMarginH))};
      bool changing{};

      // See where we'd have to scroll to get selection at left and right.
      float child_offset_left = scroll_child_width - target_x - vis_width;
      float child_offset_right = scroll_child_width - target_x - target_width;

      // If the area we're trying to show is bigger than the space we've got
      // available, aim for the middle. Perhaps we should warn when this
      // happens, but passing huge top+bottom show-buffers can also be a
      // decent way to center the selection so maybe we shouldn't.
      if (vis_width < target_width) {
        child_offset_h_ = 0.5f * (child_offset_left + child_offset_right);
        changing = true;
      } else {
        // If we're in the middle, dont do anything.
        if (child_offset_h_ > child_offset_left
            && child_offset_h_ < child_offset_right) {
        } else {
          // float prev_child_offset = child_offset_h_;

          // Do whatever offset is less of a move.
          if (std::abs(child_offset_left - child_offset_h_)
              < std::abs(child_offset_right - child_offset_h_)) {
            child_offset_h_ = child_offset_left;
          } else {
            child_offset_h_ = child_offset_right;
          }
          changing = true;
        }
      }

      if (changing) {
        // If we're moving left, stop at the end.
        {
          float max_val = scroll_child_width
                          - (width() - 2.0f * (border_width_ + kMarginH));
          if (child_offset_h_ > max_val) child_offset_h_ = max_val;
        }

        // If we're moving right, stop at the end.
        {
          // if (child_offset_h_ < prev_child_offset) {
          if (child_offset_h_ < 0.0f) {
            child_offset_h_ = 0.0f;
          }
          // }
        }
      }

      // Go into smooth mode momentarily.
      smoothing_amount_ = 1.0f;

      // Snap our smoothed value to this *only* if we haven't drawn yet
      // (keeps new widgets from inexplicably scrolling around).
      if (!have_drawn_) {
        child_offset_h_smoothed_ = child_offset_h_;
      }
      MarkForUpdate();
      break;
    }
    case base::WidgetMessage::Type::kMouseMove: {
      last_mouse_move_time_ = g_base->logic->display_time();
      float x = m.fval1;
      float y = m.fval2;
      bool was_claimed = m.fval3 > 0.0f;

      auto in_bounds = y >= 0.0f && y < height() && x >= 0.0f && x < width();

      auto repeat_out_of_bounds = !last_mouse_move_in_bounds_ && !in_bounds;
      auto just_exited_bounds = last_mouse_move_in_bounds_ && !in_bounds;
      last_mouse_move_in_bounds_ = in_bounds;

      // If we weren't in bounds before and still aren't, don't bother
      // passing to our children (a single already-claimed move should be
      // enough for them to cancel hovers/etc).
      if (repeat_out_of_bounds) {
        pass = false;
      }

      // if (!in_bounds) {
      //   pass = false;
      // }

      if (g_base->ui->touch_mode()) {
        mouse_over_ = false;
      } else {
        mouse_over_ = !was_claimed && in_bounds;
      }

      if (was_claimed) {
        // No hovering if someone above us claimed this.
        hovering_thumb_ = false;
        hovering_page_left_ = false;
        hovering_page_right_ = false;
      } else {
        if (g_base->ui->touch_mode()) {
          if (touch_held_) {
            touch_x_ = x;
            touch_y_ = y;

            // If this is a new scroll-touch, see which direction the drag
            // is happening; if it's primarily vertical lets disown it so it
            // can get handled by the scroll widget above us (presumably a
            // vertical scroll widget).
            if (new_scroll_touch_) {
              float x_diff = std::abs(touch_x_ - touch_start_x_);
              float y_diff = std::abs(touch_y_ - touch_start_y_);

              float dist = x_diff * x_diff + y_diff * y_diff;

              // If they're somehow equal, wait and look at the next one.
              if (x_diff != y_diff && dist > 30.0f) {
                new_scroll_touch_ = false;

                // If they haven't moved far enough yet, ignore it.
                if (x_diff < y_diff) {
                  return false;
                }
              }
            }

            // Handle generating delayed press/releases.
            if (static_cast<int>(m.type)) {  // <- FIXME WHAT IS THIS FOR??
              // If we move more than a slight amount it means our touch
              // isn't a click.
              if (!touch_is_scrolling_
                  && ((std::abs(touch_x_ - touch_start_x_) > 10.0f)
                      || (std::abs(touch_y_ - touch_start_y_) > 10.0f))) {
                touch_is_scrolling_ = true;

                // Cancel the press for sub-widgets.
                if (touch_down_sent_ && !touch_up_sent_) {
                  ContainerWidget::HandleMessage(base::WidgetMessage(
                      base::WidgetMessage::Type::kMouseCancel, nullptr, m.fval1,
                      m.fval2, true));
                  touch_up_sent_ = true;
                }
              }
            }
            return true;
          }
        }

        if (g_base->ui->touch_mode()) {
          // No hovering in touch mode.
          hovering_thumb_ = false;
          hovering_page_left_ = false;
          hovering_page_right_ = false;
        } else {
          float s_right = width() - border_width_;
          float s_left = border_width_;
          float sb_thumb_width =
              amount_visible_ * (width() - 2.0f * border_width_);
          float sb_thumb_right = s_right
                                 - child_offset_h_ / child_max_offset_
                                       * (s_right - (s_left + sb_thumb_width));

          hovering_thumb_ =
              (((y >= 0) && (y < scroll_bar_height_ + bottom_overlap)
                && x < sb_thumb_right && x >= sb_thumb_right - sb_thumb_width));

          hovering_page_left_ =
              (CanScrollLeft_() && y >= height() * 0.5f - kPageButtonSize * 0.5f
               && y <= height() * 0.5f + kPageButtonSize * 0.5f
               && x >= kPageButtonInset
               && x <= kPageButtonInset + kPageButtonSize);

          hovering_page_right_ =
              (CanScrollRight_()
               && y >= height() * 0.5f - kPageButtonSize * 0.5f
               && y <= height() * 0.5f + kPageButtonSize * 0.5f
               && x >= width() - kPageButtonInset - kPageButtonSize
               && x <= width() - kPageButtonInset);
        }
      }

      // If we're dragging the thumb
      if (mouse_held_thumb_) {
        claimed = true;  // We own this; noone below us should highlight.

        auto i = widgets().begin();
        if (i == widgets().end()) {
          break;
        }
        float child_w = (**i).GetWidth();
        float s_right = width() - border_width_;
        float s_left = border_width_;
        // Note: need a max on denominator here or we can get nan due to
        // divide-by-zero.
        float rate = (child_w - (s_right - s_left))
                     / std::max(1.0f, ((1.0f - ((s_right - s_left) / child_w))
                                       * (s_right - s_left)));
        child_offset_h_ = thumb_click_start_child_offset_h_
                          - rate * (x - thumb_click_start_h_);

        ClampThumb_(false, true);
        MarkForUpdate();
      }

      // If we're hovering over or dragging the thumb or a page-left/right
      // button or we just exited our bounds, send the event to children but
      // with claimed marked as true so they know to kill hover effects/etc.
      if (mouse_held_thumb_ || hovering_thumb_ || just_exited_bounds
          || hovering_page_left_ || page_left_pressed_ || hovering_page_right_
          || page_right_pressed_) {
        // Handle passing this to children ourselves so we can mark as
        // claimed.
        pass = false;
        auto m2{m};
        m2.fval3 = 1.0f;  // Mark claimed.
        ContainerWidget::HandleMessage(m2);
      }

      break;
    }
    case base::WidgetMessage::Type::kMouseUp:
    case base::WidgetMessage::Type::kMouseCancel: {
      mouse_held_scroll_down_ = false;
      mouse_held_scroll_up_ = false;
      mouse_held_thumb_ = false;
      mouse_held_page_down_ = false;
      mouse_held_page_up_ = false;

      float x = m.fval1;
      float y = m.fval2;

      // Handle page-left/right buttons.
      auto in_page_left_button =
          (y >= height() * 0.5f - kPageButtonSize * 0.5f
           && y <= height() * 0.5f + kPageButtonSize * 0.5f
           && x >= kPageButtonInset && x <= kPageButtonInset + kPageButtonSize);

      auto in_page_right_button =
          (y >= height() * 0.5f - kPageButtonSize * 0.5f
           && y <= height() * 0.5f + kPageButtonSize * 0.5f
           && x >= width() - kPageButtonInset - kPageButtonSize
           && x <= width() - kPageButtonInset);

      if (page_left_pressed_ && in_page_left_button
          && m.type == base::WidgetMessage::Type::kMouseUp) {
        smoothing_amount_ = 1.0f;  // So we can see the transition.
        child_offset_h_ +=
            0.95f * (width() - 2.0f * (border_width_ + kMarginH));
        ClampThumb_(false, true);
        claimed = true;
      }
      page_left_pressed_ = false;

      if (page_right_pressed_ && in_page_right_button
          && m.type == base::WidgetMessage::Type::kMouseUp) {
        smoothing_amount_ = 1.0f;  // So we can see the transition.
        child_offset_h_ -=
            0.95f * (width() - 2.0f * (border_width_ + kMarginH));
        ClampThumb_(false, true);
        claimed = true;
      }
      page_right_pressed_ = false;

      if (g_base->ui->touch_mode()) {
        if (touch_held_) {
          bool m_claimed = (m.fval3 > 0.0f);

          touch_held_ = false;

          // If we moved at all, we mark it as claimed to keep sub-widgets
          // from acting on it (since we used it for scrolling).
          bool claimed2 = touch_is_scrolling_ || m_claimed;

          // If we're not claiming it and we haven't sent a mouse_down yet
          // due to our delay, send that first.
          if (m.type == base::WidgetMessage::Type::kMouseUp) {
            if (!claimed2 && !touch_down_sent_) {
              ContainerWidget::HandleMessage(base::WidgetMessage(
                  base::WidgetMessage::Type::kMouseDown, nullptr, m.fval1,
                  m.fval2, static_cast<float>(touch_held_click_count_)));
              touch_down_sent_ = true;
            }
          }
          if (touch_down_sent_ && !touch_up_sent_) {
            ContainerWidget::HandleMessage(base::WidgetMessage(
                m.type, nullptr, m.fval1, m.fval2, claimed2));
            touch_up_sent_ = true;
          }
          return true;
        }
      }

      // If coords are outside of our bounds, pass a mouse-cancel along for
      // anyone tracking a drag, but mark it as claimed so it doesn't
      // actually get acted on.
      if (!((y >= 0.0f) && (y < height()) && (x >= 0.0f) && (x < width()))) {
        pass = false;
        ContainerWidget::HandleMessage(
            base::WidgetMessage(base::WidgetMessage::Type::kMouseCancel,
                                nullptr, m.fval1, m.fval2, true));
      }

      break;
    }

    case base::WidgetMessage::Type::kMouseWheelVelocityH: {
      float x = m.fval1;
      float y = m.fval2;
      if ((x >= 0.0f) && (x < width()) && (y >= 0.0f) && (y < height())) {
        claimed = true;
        pass = false;
        has_momentum_ = static_cast<bool>(m.fval4);

        // Don't scroll if everything is visible.
        if (amount_visible_ >= 1.0f) {
          break;
        }

        // We only set velocity from events when not in momentum mode; we
        // handle momentum ourself.
        if (std::abs(m.fval3) > 0.001f && !has_momentum_) {
          float scroll_speed = 2.2f;
          float smoothing = 0.8f;
          float new_val;
          if (m.fval3 < 0.0f) {
            // Apply less if we're past the end.
            if (child_offset_h_ < 0) {
              new_val = scroll_speed * 0.1f * m.fval3;
            } else {
              new_val = scroll_speed * m.fval3;
            }
          } else {
            // Apply less if we're past the end.
            bool past_end = false;

            // Calc our total height.
            auto i = widgets().begin();
            if (i != widgets().end()) {
              float child_h = (**i).GetWidth();
              float diff =
                  child_offset_h_
                  - (child_h
                     - std::min(child_h,
                                (width() - 2.0f * (border_width_ + kMarginH))));
              if (diff > 0.0f) {
                past_end = true;
              }
            }
            if (past_end) {
              new_val = scroll_speed * 0.1f * m.fval3;
            } else {
              new_val = scroll_speed * m.fval3;
            }
          }
          inertia_scroll_rate_ =
              smoothing * inertia_scroll_rate_ + (1.0f - smoothing) * new_val;
        }
        last_velocity_event_time_millisecs_ =
            static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);
        MarkForUpdate();
      } else {
        // Not within our widget; dont allow children to claim.
        pass = false;
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseWheelH: {
      float x = m.fval1;
      float y = m.fval2;
      if (x >= 0.0f && x < width() && y >= 0.0f && y < height()) {
        claimed = true;
        pass = false;

        // Don't scroll if everything is visible.
        if (amount_visible_ >= 1.0f) {
          break;
        }

        inertia_scroll_rate_ -= m.fval3 * 0.003f;
        MarkForUpdate();
      } else {
        // Not within our widget; dont allow children to claim.
        pass = false;
      }
      break;
    }
    case base::WidgetMessage::Type::kScrollMouseDown:
    case base::WidgetMessage::Type::kMouseDown: {
      float x = m.fval1;
      float y = m.fval2;

      // If its in our overall scroll region at all.
      if (y >= 0.0f && y < height() && x >= 0.0f && x < width()) {
        // Handle page-left/right buttons.
        auto in_page_left_button =
            (CanScrollLeft_() && y >= height() * 0.5f - kPageButtonSize * 0.5f
             && y <= height() * 0.5f + kPageButtonSize * 0.5f
             && x >= kPageButtonInset
             && x <= kPageButtonInset + kPageButtonSize);

        auto in_page_right_button =
            (CanScrollRight_() && y >= height() * 0.5f - kPageButtonSize * 0.5f
             && y <= height() * 0.5f + kPageButtonSize * 0.5f
             && x >= width() - kPageButtonInset - kPageButtonSize
             && x <= width() - kPageButtonInset);

        // On touch devices, clicks begin scrolling, (and eventually can
        // count as clicks if they don't move). Only if we're showing less
        // than everything though.
        if (g_base->ui->touch_mode() && amount_visible_ < 1.0f
            && !in_page_left_button && !in_page_right_button) {
          touch_held_ = true;
          auto click_count = static_cast<int>(m.fval3);
          touch_held_click_count_ = click_count;
          touch_down_sent_ = false;
          touch_up_sent_ = false;
          touch_start_x_ = x;
          touch_start_y_ = y;
          touch_x_ = x;
          touch_y_ = y;
          touch_down_x_ = x - child_offset_h_;
          touch_is_scrolling_ = false;

          // If there's significant scrolling happening we never pass
          // touches. they're only used to scroll more/less.
          if (std::abs(inertia_scroll_rate_) > 0.05f) {
            touch_is_scrolling_ = true;
          }

          pass = false;
          claimed = true;

          // Top level touches eventually get passed as mouse-downs if no
          // scrolling has started.
          if (static_cast<int>(m.type)) {
            touch_delay_timer_ = base::AppTimer::New(
                0.150, false, [this] { OnTouchDelayTimerExpired(); });
          }

          // If we're handling a scroll-touch, take note that we need to
          // decide whether to disown the touch or not.
          if (m.type == base::WidgetMessage::Type::kScrollMouseDown) {
            new_scroll_touch_ = true;
          }
        }

        if (in_page_left_button) {
          page_left_pressed_ = true;
          claimed = true;
          pass = false;
        }
        if (in_page_right_button) {
          page_right_pressed_ = true;
          claimed = true;
          pass = false;
        }

        // For mouse type devices, allow clicking on the scrollbar.
        if (!g_base->ui->touch_mode()) {
          if (y <= scroll_bar_height_ + bottom_overlap) {
            claimed = true;
            pass = false;

            float s_right = width() - border_width_;
            float s_left = border_width_;
            float sb_thumb_width =
                amount_visible_ * (width() - 2.0f * border_width_);
            float sb_thumb_right =
                s_right
                - child_offset_h_ / child_max_offset_
                      * (s_right - (s_left + sb_thumb_width));

            // To right of thumb (page-right).
            if (x >= sb_thumb_right) {
              smoothing_amount_ = 1.0f;  // So we can see the transition.
              child_offset_h_ -= (width() - 2.0f * (border_width_ + kMarginH));
              ClampThumb_(false, true);
            } else if (x >= sb_thumb_right - sb_thumb_width) {
              // On thumb.
              mouse_held_thumb_ = true;
              thumb_click_start_h_ = x;
              thumb_click_start_child_offset_h_ = child_offset_h_;
            } else if (x >= s_left) {
              // To left of thumb (page left).
              smoothing_amount_ = 1.0f;  // So we can see the transition.
              child_offset_h_ += (width() - 2.0f * (border_width_ + kMarginH));
              ClampThumb_(false, true);
            }
          }
        }
      } else {
        pass = false;  // Not in the scroll box; dont allow children to claim.
      }
      break;
    }
    default:
      break;
  }

  // Normal container event handling.
  if (pass) {
    if (ContainerWidget::HandleMessage(m)) {
      claimed = true;
    }
  }

  // If it was a mouse-down and we claimed it, set ourself as selected.
  if (m.type == base::WidgetMessage::Type::kMouseDown && claimed) {
    GlobalSelect();
  }
  return claimed;
}

void HScrollWidget::UpdateLayout() {
  BA_DEBUG_UI_READ_LOCK;  // Make sure hierarchy doesn't change under us.

  // Move everything based on our offset.
  auto i = widgets().begin();
  if (i == widgets().end()) {
    amount_visible_ = 0.0f;
    return;
  }
  float child_w = (**i).GetWidth();
  child_max_offset_ = child_w - (width() - 2.0f * (border_width_ + kMarginH));
  amount_visible_ = (width() - 2.0f * (border_width_ + kMarginH)) / child_w;
  if (amount_visible_ > 1.0f) {
    amount_visible_ = 1.0f;
    if (center_small_content_) {
      center_offset_x_ = child_max_offset_ * 0.5f;
    } else {
      center_offset_x_ = 0.0f;
    }
  } else {
    center_offset_x_ = 0.0f;
  }
  if (mouse_held_thumb_) {
    if (child_offset_h_
        > child_w - (width() - 2.0f * (border_width_ + kMarginH))) {
      child_offset_h_ = child_w - (width() - 2.0f * (border_width_ + kMarginH));
      inertia_scroll_rate_ = 0.0f;
    }
    if (child_offset_h_ < 0.0f) {
      child_offset_h_ = 0.0f;
      inertia_scroll_rate_ = 0.0f;
    }
  }
  (**i).set_translate(width() - (border_width_ + kMarginH)
                          + child_offset_h_smoothed_ - child_w
                          + center_offset_x_,
                      4.0f + border_height_);
  thumb_dirty_ = true;
}

void HScrollWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  have_drawn_ = true;
  auto* frame_def{pass->frame_def()};
  millisecs_t current_time_ms = frame_def->display_time_millisecs();
  float prev_child_offset_h_smoothed = child_offset_h_smoothed_;

  // Ok, lets update our inertial scrolling during the opaque pass. (we
  // really should have some sort of update() function for this but widgets
  // don't have that currently)
  if (!draw_transparent) {
    // (skip huge differences)
    if (current_time_ms - inertia_scroll_update_time_ms_ > 1000) {
      inertia_scroll_update_time_ms_ = current_time_ms - 1000;
    }
    while (current_time_ms - inertia_scroll_update_time_ms_ > 5) {
      inertia_scroll_update_time_ms_ += 5;

      if (g_base->ui->touch_mode()) {
        if (touch_held_) {
          float diff = (touch_x_ - child_offset_h_) - touch_down_x_;
          float smoothing = 0.7f;
          inertia_scroll_rate_ = smoothing * inertia_scroll_rate_
                                 + (1.0f - smoothing) * 0.2f * diff;
        } else {
          inertia_scroll_rate_ *= 0.98f;
        }
      } else {
        inertia_scroll_rate_ *= 0.98f;
      }

      ClampThumb_(true, mouse_held_thumb_);
      child_offset_h_ += inertia_scroll_rate_;

      if (!has_momentum_
          && (current_time_ms - last_velocity_event_time_millisecs_
              > 1000 / 30)) {
        inertia_scroll_rate_ = 0.0f;
      }

      // Lastly we apply smoothing so that if we're snapping to a specific
      // place we don't go instantly there we blend between smoothed and
      // non-smoothed depending on whats driving us (we dont want to add
      // smoothing on top of inertial scrolling for example or it'll feel
      // muddy)
      float diff = child_offset_h_ - child_offset_h_smoothed_;
      if (std::abs(diff) < 1.0f) {
        child_offset_h_smoothed_ = child_offset_h_;
      } else {
        child_offset_h_smoothed_ += (1.0f - smoothing_amount_) * diff;
      }
      smoothing_amount_ = std::max(0.0f, smoothing_amount_ - 0.0025f);
    }

    // Only re-layout our widgets if we've moved a significant amount.
    if (std::abs(prev_child_offset_h_smoothed - child_offset_h_smoothed_)
        > 0.01f) {
      MarkForUpdate();
    }
  }

  CheckLayout();

  Vector3f tilt = 0.02f * g_base->graphics->tilt();
  float extra_offs_x = tilt.y;
  float extra_offs_y = -tilt.x;

  float b = 0;
  float t = b + height();
  float l = 0;
  float r = l + width();

  // Begin clipping for children.
  {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    auto scissor =
        c.ScopedScissor({l + border_width_, b + border_height_ + 1.0f,
                         l + (width() - border_width_ - 0.0f),
                         b + (height() - border_height_) - 1.0f});
    c.Submit();  // Get out of the way for child drawing.

    set_simple_culling_left(l + border_width_);
    set_simple_culling_right(l + (width() - border_height_));

    // Draw all our widgets at our z level.
    DrawChildren(pass, draw_transparent, l + extra_offs_x, b + extra_offs_y,
                 1.0f);
  }

  // Scroll trough (depth 0.7f to 0.8f).
  if (explicit_bool(false)) {
    if (draw_transparent && border_opacity_ > 0.0f) {
      if (trough_dirty_) {
        float b2 = b + 4;
        float t2 = b2 + scroll_bar_height_;
        float l2;
        float r2;
        l2 = l + border_width_;
        r2 = r - border_width_;
        float b_border, t_border, l_border, r_border;
        b_border = 3;
        t_border = 0;
        l_border = width() * 0.006f;
        r_border = width() * 0.002f;
        trough_height_ = t2 - b2 + b_border + t_border;
        trough_width_ = r2 - l2 + l_border + r_border;
        trough_center_y_ = b2 - b_border + trough_height_ * 0.5f;
        trough_center_x_ = l2 - l_border + trough_width_ * 0.5f;
        trough_dirty_ = false;
      }

      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, border_opacity_);
      c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kUIAtlas));
      {
        auto xf = c.ScopedTransform();
        c.Translate(trough_center_x_, trough_center_y_, 0.7f);
        c.Scale(trough_width_, trough_height_, 0.1f);
        c.Rotate(-90, 0, 0, 1);
        c.DrawMeshAsset(g_base->assets->SysMesh(
            base::SysMeshID::kScrollBarTroughTransparent));
      }
      c.Submit();
    }
  }

  // Page left/right buttons at depth 0.9-1.0
  if (explicit_bool(true) && draw_transparent) {
    // Left button.
    if (CanScrollLeft_()) {
      float scale_ex{1.0f};
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      float brightness;
      if (page_left_pressed_) {
        scale_ex = 1.05f;
        brightness = 1.4f;
      } else if (hovering_page_left_) {
        brightness = 0.9f;
      } else {
        brightness = 0.7f;
      }
      c.SetColor(brightness, brightness, brightness, 1.0f);
      c.SetTexture(
          g_base->assets->SysTexture(base::SysTextureID::kPageLeftRight));

      {
        auto xf = c.ScopedTransform();
        c.Translate(kPageButtonInset + kPageButtonSize * 0.5f, height() * 0.5,
                    0.9f);
        c.Scale(scale_ex * kPageButtonSize, scale_ex * kPageButtonSize, 0.1f);
        c.Rotate(180.0f, 0.0f, 0.0f, 1.0f);
        if (draw_transparent) {
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
        c.Submit();
      }
    }
    // Right button.
    if (CanScrollRight_()) {
      float scale_ex{1.0f};
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      float brightness;
      if (page_right_pressed_) {
        scale_ex = 1.05f;
        brightness = 1.4f;
      } else if (hovering_page_right_) {
        brightness = 0.9f;
      } else {
        brightness = 0.7f;
      }
      c.SetColor(brightness, brightness, brightness, 1.0f);
      c.SetTexture(
          g_base->assets->SysTexture(base::SysTextureID::kPageLeftRight));
      {
        auto xf = c.ScopedTransform();
        c.Translate(width() - kPageButtonInset - kPageButtonSize * 0.5f,
                    height() * 0.5, 0.9f);
        c.Scale(scale_ex * kPageButtonSize, scale_ex * kPageButtonSize, 0.1f);
        if (draw_transparent) {
          c.DrawMeshAsset(g_base->assets->SysMesh(base::SysMeshID::kImage1x1));
        }
        c.Submit();
      }
    }
  }

  // Scroll bars.
  if (amount_visible_ > 0.0f && amount_visible_ < 1.0f) {
    // Scroll thumb at depth 0.8 - 0.9.
    {
      float sb_thumb_width = amount_visible_ * (width() - 2.0f * border_width_);
      if (thumb_dirty_) {
        float sb_thumb_right =
            r - border_width_
            - ((width() - (border_width_ * 2.0f) - sb_thumb_width)
               * child_offset_h_smoothed_ / child_max_offset_);
        float b2 = 4.0f;
        float t2 = b2 + scroll_bar_height_;
        float r2 = sb_thumb_right;
        float l2 = r2 - sb_thumb_width;
        float b_border, t_border, l_border, r_border;
        b_border = 6.0f;
        t_border = 3.0f;
        if (sb_thumb_width > 100.0f) {
          auto wd = r2 - l2;
          l_border = wd * 0.04f;
          r_border = wd * 0.06f;
        } else {
          auto wd = r2 - l2;
          r_border = wd * 0.12f;
          l_border = wd * 0.08f;
        }
        thumb_height_ = t2 - b2 + b_border + t_border;
        thumb_width_ = r2 - l2 + l_border + r_border;

        thumb_center_y_ = b2 - b_border + thumb_height_ * 0.5f;
        thumb_center_x_ = l2 - l_border + thumb_width_ * 0.5f;
        thumb_dirty_ = false;
      }

      float frame_duration = frame_def->display_time_elapsed();

      bool smooth_diff =
          (std::abs(child_offset_h_smoothed_ - child_offset_h_) > 0.01f);

      if (g_base->ui->touch_mode()) {
        if (smooth_diff || (touch_held_ && touch_is_scrolling_)
            || std::abs(inertia_scroll_rate_) > 1.0f) {
          last_scroll_bar_show_time_ = frame_def->display_time();
        }
      } else {
        // printf("M %d\n", static_cast<int>(mouse_over_));
        if (smooth_diff || mouse_held_thumb_
            || std::abs(inertia_scroll_rate_) > 1.0f
            || (mouse_over_
                && frame_def->display_time() - last_mouse_move_time_ < 0.1f)) {
          last_scroll_bar_show_time_ = frame_def->display_time();
        }
      }

      // Fade in if we want to see the scrollbar. Start fading out a moment
      // after we stop wanting to see it.
      if (frame_def->display_time() - last_scroll_bar_show_time_ < 0.6f) {
        touch_fade_ = std::min(1.5f, touch_fade_ + 2.0f * frame_duration);
      } else {
        touch_fade_ = std::max(0.0f, touch_fade_ - 1.5f * frame_duration);
      }

      if (touch_fade_ > 0.0f && draw_transparent) {
        base::SimpleComponent c(pass);
        c.SetTransparent(draw_transparent);
        c.SetColor(0, 0, 0, std::min(1.0f, 0.3f * touch_fade_));

        {
          auto scissor =
              c.ScopedScissor({l + border_width_, b + border_height_ + 1.0f,
                               l + (width()), b + (height() * 0.995f)});
          auto xf = c.ScopedTransform();
          c.Translate(thumb_center_x_, thumb_center_y_, 0.75f);
          c.Scale(-thumb_width_, thumb_height_, 0.1f);
          c.FlipCullFace();
          c.Rotate(-90.0f, 0.0f, 0.0f, 1.0f);

          if (draw_transparent) {
            c.DrawMeshAsset(g_base->assets->SysMesh(
                sb_thumb_width > 100.0f
                    ? base::SysMeshID::kScrollBarThumbSimple
                    : base::SysMeshID::kScrollBarThumbShortSimple));
          }
          c.FlipCullFace();
          c.Submit();
        }
      }
    }
  }

  // Outline shadow (depth 0.9 to 1.0).
  if (draw_transparent && border_opacity_ > 0.0f) {
    if (shadow_dirty_) {
      float r2 = l + width();
      float l2 = l;
      float b2 = b;
      float t2 = t;
      float l_border, r_border, b_border, t_border;
      l_border = (r2 - l2) * 0.005f;
      r_border = (r2 - l2) * 0.001f;
      b_border = (t2 - b2) * 0.006f;
      t_border = (t2 - b2) * 0.002f;
      outline_width_ = r2 - l2 + l_border + r_border;
      outline_height_ = t2 - b2 + b_border + t_border;
      outline_center_x_ = l2 - l_border + 0.5f * outline_width_;
      outline_center_y_ = b2 - b_border + 0.5f * outline_height_;
      shadow_dirty_ = false;
    }
    base::SimpleComponent c(pass);
    c.SetTransparent(true);
    c.SetColor(1.0f, 1.0f, 1.0f, border_opacity_);
    c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kScrollWidget));
    {
      auto xf = c.ScopedTransform();
      c.Translate(outline_center_x_, outline_center_y_, 0.9f);
      c.Scale(outline_width_, outline_height_, 0.1f);
      c.DrawMeshAsset(
          g_base->assets->SysMesh(base::SysMeshID::kSoftEdgeOutside));
    }
    c.Submit();
  }

  // If selected, do glow at depth 0.9 - 1.0.
  if (draw_transparent && IsHierarchySelected()
      && g_base->ui->ShouldHighlightWidgets() && highlight_
      && border_opacity_ > 0.0f) {
    float m = (0.8f
               + std::abs(sinf(static_cast<float>(current_time_ms) * 0.006467f))
                     * 0.2f)
              * border_opacity_;

    if (glow_dirty_) {
      float r2 = l + width();
      float l2 = l;
      float b2 = b;
      float t2 = t;
      float l_border, r_border, b_border, t_border;
      l_border = (r2 - l2) * 0.02f;
      r_border = (r2 - l2) * 0.02f;
      b_border = (t2 - b2) * 0.015f;
      t_border = (t2 - b2) * 0.01f;
      glow_width_ = r2 - l2 + l_border + r_border;
      glow_height_ = t2 - b2 + b_border + t_border;
      glow_center_x_ = l2 - l_border + 0.5f * glow_width_;
      glow_center_y_ = b2 - b_border + 0.5f * glow_height_;
      glow_dirty_ = false;
    }
    base::SimpleComponent c(pass);
    c.SetTransparent(true);
    c.SetPremultiplied(true);
    c.SetColor(0.4f * m, 0.5f * m, 0.05f * m, 0.0f);
    c.SetTexture(
        g_base->assets->SysTexture(base::SysTextureID::kScrollWidgetGlow));
    {
      auto xf = c.ScopedTransform();
      c.Translate(glow_center_x_, glow_center_y_, 0.9f);
      c.Scale(glow_width_, glow_height_, 0.1f);
      c.DrawMeshAsset(
          g_base->assets->SysMesh(base::SysMeshID::kSoftEdgeOutside));
    }
    c.Submit();
  }
}

}  // namespace ballistica::ui_v1
