// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/scroll_widget.h"

#include <algorithm>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"

namespace ballistica::ui_v1 {

#define V_MARGIN 5

ScrollWidget::ScrollWidget()
    : touch_mode_(!g_core->platform->IsRunningOnDesktop()) {
  set_background(false);  // Influences default event handling.
  set_draggable(false);
  set_claims_left_right(false);
}

ScrollWidget::~ScrollWidget() = default;

void ScrollWidget::OnTouchDelayTimerExpired() {
  if (touch_held_) {
    // Pass a mouse-down event if we haven't moved.
    if (!touch_is_scrolling_ && !touch_down_sent_) {
      // Gather up any user code triggered by this stuff and run it at the
      // end before we return.
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

void ScrollWidget::ClampThumb_(bool velocity_clamp, bool position_clamp) {
  BA_DEBUG_UI_READ_LOCK;

  bool is_scrolling;
  if (touch_mode_) {
    is_scrolling = (touch_held_ || !has_momentum_);
  } else {
    is_scrolling = (!has_momentum_);
  }
  float strong_force;
  float weak_force;
  if (touch_mode_) {
    strong_force = -0.12f;
    weak_force = -0.004f;
  } else {
    strong_force = -0.012f;
    weak_force = -0.004f;
  }
  auto i = widgets().begin();
  if (i != widgets().end()) {
    float child_h = (**i).GetHeight();
    if (velocity_clamp) {
      if (child_offset_v_ < 0) {
        // Even in velocity case do some sane clamping.
        float diff = child_offset_v_;
        inertia_scroll_rate_ +=
            diff * (is_scrolling ? strong_force : weak_force);
        inertia_scroll_rate_ *= 0.9f;

      } else if (child_offset_v_
                 > child_h - (height() - 2 * (border_height_ + V_MARGIN))) {
        float diff =
            child_offset_v_
            - (child_h
               - std::min(child_h,
                          (height() - 2 * (border_height_ + V_MARGIN))));
        inertia_scroll_rate_ +=
            diff * (is_scrolling ? strong_force : weak_force);
        inertia_scroll_rate_ *= 0.9f;
      }
    }

    // Hard clipping if we're dragging the scrollbar.
    if (position_clamp) {
      if (child_offset_v_smoothed_
          > child_h - (height() - 2 * (border_height_ + V_MARGIN))) {
        child_offset_v_smoothed_ =
            child_h - (height() - 2 * (border_height_ + V_MARGIN));
      }
      if (child_offset_v_smoothed_ < 0) {
        child_offset_v_smoothed_ = 0;
      }
      if (child_offset_v_
          > child_h - (height() - 2 * (border_height_ + V_MARGIN))) {
        child_offset_v_ =
            child_h - (height() - 2 * (border_height_ + V_MARGIN));
      }
      if (child_offset_v_ < 0) {
        child_offset_v_ = 0;
      }
    }
  }
}

auto ScrollWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  BA_DEBUG_UI_READ_LOCK;
  bool claimed = false;
  bool pass = true;
  float right_overlap = 0;
  float left_overlap = 3;
  switch (m.type) {
    case base::WidgetMessage::Type::kMoveUp:
      if (capture_arrows_) {
        smoothing_amount_ = 1.0f;  // So we can see the transition.
        child_offset_v_ -= (60);
        MarkForUpdate();
        ClampThumb_(false, true);
      }
      break;

    case base::WidgetMessage::Type::kMoveDown:
      if (capture_arrows_) {
        smoothing_amount_ = 1.0f;  // So we can see the transition.
        child_offset_v_ += (60);
        MarkForUpdate();
        ClampThumb_(false, true);
      }
      break;

    case base::WidgetMessage::Type::kShow: {
      claimed = true;
      pass = false;
      auto i = widgets().begin();
      if (i == widgets().end()) break;
      float child_h = (**i).GetHeight();

      // See where we'd have to scroll to get selection at top and bottom.
      float child_offset_bot =
          child_h - m.fval2 - (height() - 2 * (border_height_ + V_MARGIN));
      float child_offset_top = child_h - m.fval2 - m.fval4;

      // If we're in the middle, dont do anything.
      if (child_offset_v_ > child_offset_bot
          && child_offset_v_ < child_offset_top) {
      } else {
        // Do whatever offset is less of a move.
        if (std::abs(child_offset_bot - child_offset_v_)
            < std::abs(child_offset_top - child_offset_v_)) {
          child_offset_v_ = child_offset_bot;
        } else {
          child_offset_v_ = child_offset_top;
        }

        // If we're moving down, stop at the bottom.
        {
          float max_val =
              child_h - (height() - 2 * (border_height_ + V_MARGIN));
          if (child_offset_v_ > max_val) {
            child_offset_v_ = max_val;
          }
        }

        // If we're moving up, stop at the top.
        {
          if (child_offset_v_ < 0) {
            child_offset_v_ = 0;
          }
        }
      }

      // Go into smooth mode momentarily.
      smoothing_amount_ = 1.0f;

      // Snap our smoothed value to this *only* if we haven't drawn yet.
      // (keeps new widgets from inexplicably scrolling around)
      if (!have_drawn_) {
        child_offset_v_smoothed_ = child_offset_v_;
      }
      MarkForUpdate();
      break;
    }
    case base::WidgetMessage::Type::kMouseWheelVelocityH: {
      if (ContainerWidget::HandleMessage(m)) {
        claimed = true;

        // Keep track of the average scrolling going on. (only update when
        // we get non-momentum events)
        if (std::abs(m.fval3) > 0.001f && !has_momentum_) {
          float smoothing = 0.8f;
          avg_scroll_speed_h_ =
              smoothing * avg_scroll_speed_h_ + (1.0f - smoothing) * m.fval3;

          // Also tamp this down in case we're not getting new events for it.
          avg_scroll_speed_v_ =
              smoothing * avg_scroll_speed_v_ + (1.0f - smoothing) * 0.0f;
        }
        last_sub_widget_h_scroll_claim_time_ = g_core->AppTimeMillisecs();
      }
      pass = false;
      break;
    }
    case base::WidgetMessage::Type::kMouseWheelVelocity: {
      float x = m.fval1;
      float y = m.fval2;

      // Keep track of the average scrolling going on. (only update when we
      // get non-momentum events).
      if (std::abs(m.fval3) > 0.001f && !has_momentum_) {
        float smoothing = 0.8f;
        avg_scroll_speed_v_ =
            smoothing * avg_scroll_speed_v_ + (1.0f - smoothing) * m.fval3;

        // Also tamp this down in case we're not getting new events for it.
        avg_scroll_speed_h_ =
            smoothing * avg_scroll_speed_h_ + (1.0f - smoothing) * 0.0f;
      }

      // If a child appears to be looking at horizontal scroll events and
      // we're scrolling more horizontally than vertically in general,
      // ignore vertical scrolling (should probably make this less fuzzy).
      bool ignore_regular_scrolling = false;
      bool child_claimed_h_scroll_recently =
          (g_core->AppTimeMillisecs() - last_sub_widget_h_scroll_claim_time_
           < 100);
      if (child_claimed_h_scroll_recently
          && std::abs(avg_scroll_speed_h_) > std::abs(avg_scroll_speed_v_))
        ignore_regular_scrolling = true;

      if ((x >= 0.0f) && (x < width()) && (y >= 0.0f) && (y < height())
          && !ignore_regular_scrolling) {
        claimed = true;
        pass = false;
        has_momentum_ = static_cast<bool>(m.fval4);

        // We only set velocity from events when not in momentum mode. We
        // handle momentum ourself.
        if (std::abs(m.fval3) > 0.001f && !has_momentum_) {
          float scroll_speed = 2.2f;
          float smoothing = 0.8f;
          float new_val;
          if (m.fval3 < 0.0f) {
            // Apply less if we're past the end.
            if (child_offset_v_ < 0) {
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
              float child_h = (**i).GetHeight();
              float diff =
                  child_offset_v_
                  - (child_h
                     - std::min(child_h,
                                (height() - 2 * (border_height_ + V_MARGIN))));
              if (diff > 0) past_end = true;
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
        // Not within our widget; don't allow children to claim.
        pass = false;
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseWheel: {
      float x = m.fval1;
      float y = m.fval2;
      if ((x >= 0.0f) && (x < width()) && (y >= 0.0f) && (y < height())) {
        claimed = true;
        pass = false;
        inertia_scroll_rate_ -= m.fval3 * 0.003f;
        MarkForUpdate();
      } else {
        // Not within our widget; dont allow children to claim.
        pass = false;
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseDown: {
      float x = m.fval1;
      float y = m.fval2;
      if ((x >= 0.0f) && (x < width() + right_overlap) && (y >= 0.0f)
          && (y < height())) {
        // On touch devices, touches begin scrolling, (and eventually can
        // count as clicks if they don't move).
        if (touch_mode_) {
          touch_held_ = true;
          auto click_count = static_cast<int>(m.fval3);
          touch_held_click_count_ = click_count;
          touch_down_sent_ = false;
          touch_up_sent_ = false;
          touch_start_x_ = x;
          touch_start_y_ = y;
          touch_x_ = x;
          touch_y_ = y;
          touch_down_y_ = y - child_offset_v_;
          touch_is_scrolling_ = false;
          child_is_scrolling_ = false;
          child_disowned_scroll_ = false;

          // If there's already significant scrolling happening, we handle
          // all these ourself as scroll events.
          if (std::abs(inertia_scroll_rate_) > 0.05f) {
            touch_is_scrolling_ = true;
          }

          pass = false;
          claimed = true;

          if (!touch_is_scrolling_) {
            // Give children a chance to claim this for their own scrolling
            // before we do so.
            child_is_scrolling_ = ContainerWidget::HandleMessage(
                base::WidgetMessage(base::WidgetMessage::Type::kScrollMouseDown,
                                    nullptr, m.fval1, m.fval2, m.fval3));

            // After a short delay we go ahead and handle this as a regular
            // click if it hasn't turned into a scroll or a child scroll.
            if (!child_is_scrolling_) {
              touch_delay_timer_ = base::AppTimer::New(
                  0.150, false, [this] { OnTouchDelayTimerExpired(); });
            }
          }
        }

        // On desktop, allow clicking on the scrollbar.
        if (!touch_mode_) {
          if (x >= width() - scroll_bar_width_ - left_overlap) {
            claimed = true;
            pass = false;
            float s_top = height() - border_height_;
            float s_bottom = border_height_;
            float sb_thumb_height =
                amount_visible_ * (height() - 2 * border_height_);
            float sb_thumb_top = s_top
                                 - child_offset_v_ / child_max_offset_
                                       * (s_top - (s_bottom + sb_thumb_height));
            // Above thumb (page-up).
            if (y >= sb_thumb_top) {
              // So we can see the transition.
              smoothing_amount_ = 1.0f;
              child_offset_v_ -= (height() - 2 * (border_height_ + V_MARGIN));
              MarkForUpdate();
              ClampThumb_(false, true);
            } else if (y >= sb_thumb_top - sb_thumb_height) {
              // On thumb.
              mouse_held_thumb_ = true;
              thumb_click_start_v_ = y;
              thumb_click_start_child_offset_v_ = child_offset_v_;
            } else if (y >= s_bottom) {
              // Below thumb (page down). So we can see the transition.
              smoothing_amount_ = 1.0f;
              child_offset_v_ += (height() - 2 * (border_height_ + V_MARGIN));
              MarkForUpdate();
              ClampThumb_(false, true);
            }
          }
        }
      } else {
        // Not in the scroll box; dont allow children to claim it.
        pass = false;
      }
      break;
    }
    case base::WidgetMessage::Type::kMouseMove: {
      float x = m.fval1;
      float y = m.fval2;
      bool was_claimed = (m.fval3 > 0.0f);

      // If coords are outside of our bounds we don't want to pass
      // mouse-moved events through the standard container logic.
      // (otherwise, if we mouse down over a button that doesn't overlap the
      // scroll area but overlaps some widget in the scroll area, the widget
      // would claim the move and the button would lose its
      // mouse-over-highlight; ew.) There may be some case where we *would*
      // want to pass this though.
      if (!((x >= 0.0f) && (x < width() + right_overlap) && (y >= 0.0f)
            && (y < height()))) {
        pass = false;
      }

      if (was_claimed) {
        mouse_over_thumb_ = false;
      } else {
        if (touch_mode_) {
          if (touch_held_) {
            // If we have a child claiming this scrolling action for
            // themselves, just keep passing them the events as long as they
            // get claimed.
            if (child_is_scrolling_ && !child_disowned_scroll_) {
              bool move_claimed = ContainerWidget::HandleMessage(
                  base::WidgetMessage(base::WidgetMessage::Type::kMouseMove,
                                      nullptr, m.fval1, m.fval2, m.fval3));
              // If they stopped claiming them, send a scroll-mouse-up to
              // tie things up.
              if (!move_claimed) {
                ContainerWidget::HandleMessage(
                    base::WidgetMessage(base::WidgetMessage::Type::kMouseUp,
                                        nullptr, m.fval1, m.fval2, true));
                child_disowned_scroll_ = true;
              }
            } else {
              // If no child is scrolling; this touch motion is ours to
              // handle.
              touch_x_ = x;
              touch_y_ = y;

              // If we move more than a slight amount it means our touch
              // isn't a click.
              if (!touch_is_scrolling_
                  && ((std::abs(touch_x_ - touch_start_x_) > 10.0f)
                      || (std::abs(touch_y_ - touch_start_y_) > 10.0f))) {
                touch_is_scrolling_ = true;

                // Go ahead and send a mouse-up to the sub-widgets; in their
                // eyes the click is canceled.
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

        if (touch_mode_) {
          mouse_over_thumb_ = false;
        } else {
          float s_top = height() - border_height_;
          float s_bottom = border_height_;
          float sb_thumb_height =
              amount_visible_ * (height() - 2.0f * border_height_);
          float sb_thumb_top = s_top
                               - child_offset_v_ / child_max_offset_
                                     * (s_top - (s_bottom + sb_thumb_height));

          mouse_over_thumb_ =
              (((x >= width() - scroll_bar_width_ - left_overlap)
                && (x < width() + right_overlap) && y < sb_thumb_top
                && y >= sb_thumb_top - sb_thumb_height));
        }
      }

      // If we're dragging.
      if (mouse_held_thumb_) {
        auto i = widgets().begin();
        if (i == widgets().end()) {
          break;
        }
        float child_h = (**i).GetHeight();
        float s_top = height() - border_height_;
        float s_bottom = border_height_;
        // Note: need a max on denominator here or we can get nan due to
        // divide-by-zero.
        float rate = (child_h - (s_top - s_bottom))
                     / std::max(1.0f, ((1.0f - ((s_top - s_bottom) / child_h))
                                       * (s_top - s_bottom)));
        child_offset_v_ = thumb_click_start_child_offset_v_
                          - rate * (y - thumb_click_start_v_);
        ClampThumb_(false, true);
        MarkForUpdate();
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
      if (touch_mode_) {
        if (touch_held_) {
          touch_held_ = false;

          // If we moved at all, we mark it as claimed to keep sub-widgets
          // from acting on it (since we used it for scrolling)
          bool claimed2 = touch_is_scrolling_ || child_is_scrolling_;

          // if a child is still scrolling, send them a scroll-mouse-up/cancel
          if (child_is_scrolling_ && !child_disowned_scroll_) {
            ContainerWidget::HandleMessage(
                base::WidgetMessage(m.type, nullptr, m.fval1, m.fval2, false));
          }

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
      float x = m.fval1;
      float y = m.fval2;
      if (!((x >= 0.0f) && (x < width() + right_overlap) && (y >= 0.0f)
            && (y < height()))) {
        pass = false;
        ContainerWidget::HandleMessage(
            base::WidgetMessage(base::WidgetMessage::Type::kMouseCancel,
                                nullptr, m.fval1, m.fval2, true));
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

  // If it was a mouse-down and we claimed it, set ourself as selected
  if (m.type == base::WidgetMessage::Type::kMouseDown && claimed) {
    GlobalSelect();
  }

  return claimed;
}

void ScrollWidget::UpdateLayout() {
  BA_DEBUG_UI_READ_LOCK;

  // Move everything based on our offset.
  auto i = widgets().begin();
  if (i == widgets().end()) {
    amount_visible_ = 0;
    return;
  }

  float extra_border_x{4.0};  // Whee arbitrary hard coded values.
  float xoffs;
  if (center_small_content_horizontally_) {
    float our_width{width()};
    float child_width = (**i).GetWidth();
    xoffs = (our_width - child_width) * 0.5 - border_width_ - extra_border_x;
  } else {
    xoffs = extra_border_x + border_width_;
  }

  float child_height = (**i).GetHeight();
  child_max_offset_ =
      child_height - (height() - 2 * (border_height_ + V_MARGIN));
  amount_visible_ = (height() - 2 * (border_height_ + V_MARGIN)) / child_height;
  if (amount_visible_ > 1) {
    amount_visible_ = 1;
    if (center_small_content_) {
      center_offset_y_ = child_max_offset_ * 0.5f;
    } else {
      center_offset_y_ = 0;
    }
  } else {
    center_offset_y_ = 0;
  }

  if (mouse_held_thumb_) {
    if (child_offset_v_
        > child_height - (height() - 2 * (border_height_ + V_MARGIN))) {
      child_offset_v_ =
          child_height - (height() - 2 * (border_height_ + V_MARGIN));
      inertia_scroll_rate_ = 0;
    }
    if (child_offset_v_ < 0) {
      child_offset_v_ = 0;
      inertia_scroll_rate_ = 0;
    }
  }
  (**i).set_translate(xoffs, height() - (border_height_ + V_MARGIN)
                                 + child_offset_v_smoothed_ - child_height
                                 + center_offset_y_);
  thumb_dirty_ = true;
}

void ScrollWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  have_drawn_ = true;
  millisecs_t current_time = pass->frame_def()->display_time_millisecs();
  float prev_child_offset_v_smoothed = child_offset_v_smoothed_;

  // Ok, lets update our inertial scrolling during the opaque pass (we
  // really should have some sort of update() function for this but widgets
  // don't have that).
  if (!draw_transparent) {
    // Skip huge differences.
    if (current_time - inertia_scroll_update_time_ > 1000) {
      inertia_scroll_update_time_ = current_time - 1000;
    }
    while (current_time - inertia_scroll_update_time_ > 5) {
      inertia_scroll_update_time_ += 5;

      if (touch_mode_) {
        if (touch_held_) {
          float diff = (touch_y_ - child_offset_v_) - touch_down_y_;
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
      child_offset_v_ += inertia_scroll_rate_;
      if (!has_momentum_
          && (current_time - last_velocity_event_time_millisecs_ > 1000 / 30))
        inertia_scroll_rate_ = 0;

      // Lastly we apply smoothing so that if we're snapping to a specific
      // place we don't go instantly there we blend between smoothed and
      // non-smoothed depending on whats driving us (we dont want to add
      // smoothing on top of inertial scrolling for example or it'll feel
      // muddy).
      float diff = child_offset_v_ - child_offset_v_smoothed_;
      if (std::abs(diff) < 1.0f) {
        child_offset_v_smoothed_ = child_offset_v_;
      } else {
        child_offset_v_smoothed_ += (1.0f - 0.95f * smoothing_amount_) * diff;
      }
      smoothing_amount_ = std::max(0.0f, smoothing_amount_ - 0.005f);
    }

    // Only re-layout our widgets if we've moved a significant amount.
    if (std::abs(prev_child_offset_v_smoothed - child_offset_v_smoothed_)
        > 0.01f) {
      MarkForUpdate();
    }
  }

  CheckLayout();

  Vector3f tilt = 0.02f * g_base->graphics->tilt();
  float extra_offs_x = tilt.y;
  float extra_offs_y = -tilt.x;

  float l = 0;
  float b = 0;
  float t = b + height();

  // Begin clipping for children.
  {
    base::EmptyComponent c(pass);
    c.SetTransparent(draw_transparent);
    auto scissor = c.ScopedScissor({l + border_width_, b + border_height_ + 1,
                                    l + (width() - border_width_),
                                    b + (height() - border_height_) - 1});
    c.Submit();  // Get out of the way for children drawing.

    set_simple_culling_bottom(b + border_height_ + 1);
    set_simple_culling_top(b + (height() - border_height_) - 1);

    // Scroll trough (depth 0.05 to 0.15).
    if (explicit_bool(true)) {
      if (draw_transparent) {
        if (trough_dirty_) {
          float r2 = l + width();
          float l2 = r2 - scroll_bar_width_;
          float b2;
          float t2;
          b2 = b + (border_height_);
          t2 = t - (border_height_);
          float l_border, r_border, b_border, t_border;
          l_border = 3;
          r_border = 0;
          b_border = height() * 0.006f;
          t_border = height() * 0.002f;
          trough_width_ = r2 - l2 + l_border + r_border;
          trough_height_ = t2 - b2 + b_border + t_border;
          trough_center_x_ = l2 - l_border + trough_width_ * 0.5f;
          trough_center_y_ = b2 - b_border + trough_height_ * 0.5f;
          trough_dirty_ = false;
        }
        base::SimpleComponent c(pass);
        c.SetTransparent(true);
        c.SetColor(1.0f, 1.0f, 1.0f, border_opacity_);
        c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kUIAtlas));
        {
          auto xf = c.ScopedTransform();
          c.Translate(trough_center_x_, trough_center_y_, 0.05f);
          c.Scale(trough_width_, trough_height_, 0.1f);
          c.DrawMeshAsset(g_base->assets->SysMesh(
              base::SysMeshID::kScrollBarTroughTransparent));
        }
        c.Submit();
      }
    }

    // Draw all our widgets at our z level.
    DrawChildren(pass, draw_transparent, l + extra_offs_x, b + extra_offs_y,
                 1.0f);
  }

  // Scroll bars.
  if (amount_visible_ > 0 && amount_visible_ < 1) {
    // Scroll thumb at depth 0.8 - 0.9.
    {
      float sb_thumb_height = amount_visible_ * (height() - 2 * border_height_);
      if (thumb_dirty_) {
        float sb_thumb_top =
            t - border_height_
            - ((height() - (border_height_ * 2) - sb_thumb_height)
               * child_offset_v_smoothed_ / child_max_offset_);
        float r2 = l + width();
        float l2 = r2 - scroll_bar_width_;
        float t2 = sb_thumb_top;
        float b2 = t2 - sb_thumb_height;
        float l_border, r_border, b_border, t_border;
        l_border = 6;
        r_border = 3;
        if (sb_thumb_height > 100) {
          b_border = (t2 - b2) * 0.06f;
          t_border = b_border * 0.5f;
        } else {
          b_border = (t2 - b2) * 0.12f;
          t_border = b_border * 0.6f;
        }
        thumb_width_ = r2 - l2 + l_border + r_border;
        thumb_height_ = t2 - b2 + b_border + t_border;
        thumb_center_x_ = l2 - l_border + thumb_width_ * 0.5f;
        thumb_center_y_ = b2 - b_border + thumb_height_ * 0.5f;
        thumb_dirty_ = false;
      }

      {
        base::SimpleComponent c(pass);
        c.SetTransparent(draw_transparent);
        float c_scale = 1.0f;
        if (mouse_held_thumb_) {
          c_scale = 1.8f;
        } else if (mouse_over_thumb_) {
          c_scale = 1.25f;
        }

        c.SetColor(color_red_ * c_scale, color_green_ * c_scale,
                   color_blue_ * c_scale, 1.0f);

        c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kUIAtlas));
        {
          auto scissor =
              c.ScopedScissor({l + border_width_, b + border_height_ + 1,
                               l + (width()), b + (height() * 0.995f)});
          auto xf = c.ScopedTransform();
          c.Translate(thumb_center_x_, thumb_center_y_, 0.8f);
          c.Scale(thumb_width_, thumb_height_, 0.1f);
          if (draw_transparent) {
            c.DrawMeshAsset(g_base->assets->SysMesh(
                sb_thumb_height > 100
                    ? base::SysMeshID::kScrollBarThumbTransparent
                    : base::SysMeshID::kScrollBarThumbShortTransparent));
          } else {
            c.DrawMeshAsset(g_base->assets->SysMesh(
                sb_thumb_height > 100
                    ? base::SysMeshID::kScrollBarThumbOpaque
                    : base::SysMeshID::kScrollBarThumbShortOpaque));
          }
        }
      }
    }
  }

  // Outline shadow (depth 0.9 to 1.0).
  if (draw_transparent) {
    if (shadow_dirty_) {
      float r2 = l + width();
      float l2 = l;
      float b2 = b;
      float t2 = t;
      float l_border, r_border, b_border, t_border;
      l_border = (r2 - l2) * 0.01f;
      r_border = (r2 - l2) * 0.01f;
      b_border = (t2 - b2) * 0.003f;
      t_border = (t2 - b2) * 0.002f;
      outline_width_ = r2 - l2 + l_border + r_border;
      outline_height_ = t2 - b2 + b_border + t_border;
      outline_center_x_ = l2 - l_border + 0.5f * outline_width_;
      outline_center_y_ = b2 - b_border + 0.5f * outline_height_;
      shadow_dirty_ = false;
    }
    {
      base::SimpleComponent c(pass);
      c.SetTransparent(true);
      c.SetColor(1, 1, 1, border_opacity_);
      c.SetTexture(
          g_base->assets->SysTexture(base::SysTextureID::kScrollWidget));
      {
        auto xf = c.ScopedTransform();
        c.Translate(outline_center_x_, outline_center_y_, 0.9f);
        c.Scale(outline_width_, outline_height_, 0.1f);
        c.DrawMeshAsset(
            g_base->assets->SysMesh(base::SysMeshID::kSoftEdgeOutside));
      }
    }
  }

  // If selected, do glow at depth 0.9 - 1.0.
  if (draw_transparent && IsHierarchySelected()
      && g_base->ui->ShouldHighlightWidgets() && highlight_) {
    float m =
        (0.8f
         + std::abs(sinf(static_cast<float>(current_time) * 0.006467f)) * 0.2f)
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
