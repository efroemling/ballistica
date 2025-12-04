// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/widget/scroll_widget.h"

#include <algorithm>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/empty_component.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/support/app_timer.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/math/lerp.h"

namespace ballistica::ui_v1 {

static const float kMarginV{5.0f};

ScrollWidget::ScrollWidget() {
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

      // Make note this is deferred so it doesn't generate delayed clicks
      // itself.
      handling_deferred_click_ = true;

      HandleMessage(base::WidgetMessage(
          base::WidgetMessage::Type::kMouseDown, nullptr, touch_x_, touch_y_,
          static_cast<float>(touch_held_click_count_)));

      touch_down_sent_ = true;
      handling_deferred_click_ = false;

      // Run any calls built up by UI callbacks.
      ui_op_context.Finish();
    }
  }

  // Clean ourself out.
  touch_delay_timer_.Clear();
}

void ScrollWidget::ClampScrolling_(bool velocity_clamp, bool position_clamp,
                                   millisecs_t current_time_millisecs) {
  BA_DEBUG_UI_READ_LOCK;  // Make sure hierarchy doesn't change under us.

  float stiffness = touch_is_scrolling_ ? -0.4f : -0.004f;
  float damping_scaling = 0.89f;
  auto i = widgets().begin();
  if (i == widgets().end()) {
    return;  // No children.
  }
  float child_height = (**i).GetHeight();

  if (velocity_clamp) {
    if (child_offset_v_ < 0.0f) {
      // We've scrolled past the top.
      float diff = child_offset_v_;
      inertia_scroll_rate_ += diff * stiffness;
      inertia_scroll_rate_ *= damping_scaling;

    } else {
      float diff =
          child_offset_v_
          - (child_height
             - std::min(child_height,
                        (height() - 2.0f * (border_height_ + kMarginV))));
      if (diff > 0.0f) {
        // We've scrolled past the bottom.
        inertia_scroll_rate_ += diff * stiffness;
        inertia_scroll_rate_ *= damping_scaling;
      } else {
        // We're in the middle.
        //
        // Hit the brakes a moment after our last non-touch non-momentum
        // scroll event comes through. This kills motion for regular
        // non-momentum scroll wheels and for momentum stuff while the touch
        // is still happening. Also kill it when we're feeding h-scrolls to
        // children.
        if (!last_scroll_was_touch_) {
          if ((!has_momentum_
               && (current_time_millisecs - last_v_scroll_event_time_millisecs_
                   > 1000 / 30))
              || should_pass_h_scroll_to_children_) {
            inertia_scroll_rate_ *= 0.5f;
          }
        }
      }
    }
  }

  // Hard clipping if we're dragging the scrollbar.
  if (position_clamp) {
    if (child_offset_v_smoothed_
        > child_height - (height() - 2.0f * (border_height_ + kMarginV))) {
      child_offset_v_smoothed_ =
          child_height - (height() - 2.0f * (border_height_ + kMarginV));
    }
    if (child_offset_v_smoothed_ < 0.0f) {
      child_offset_v_smoothed_ = 0.0f;
    }
    if (child_offset_v_
        > child_height - (height() - 2.0f * (border_height_ + kMarginV))) {
      child_offset_v_ =
          child_height - (height() - 2.0f * (border_height_ + kMarginV));
    }
    if (child_offset_v_ < 0) {
      child_offset_v_ = 0;
    }
  }
}

auto ScrollWidget::HandleMessage(const base::WidgetMessage& m) -> bool {
  BA_DEBUG_UI_READ_LOCK;  // Make sure hierarchy doesn't change under us.
  bool claimed{false};
  bool pass{true};
  float right_overlap{0.0f};
  float left_overlap{3.0f};

  switch (m.type) {
    case base::WidgetMessage::Type::kMoveUp:
      if (capture_arrows_) {
        smoothing_amount_ = 1.0f;  // So we can see the transition.
        child_offset_v_ -= 60.0f;
        MarkForUpdate();
        ClampScrolling_(false, true, -1);
      }
      break;

    case base::WidgetMessage::Type::kMoveDown:
      if (capture_arrows_) {
        smoothing_amount_ = 1.0f;  // So we can see the transition.
        child_offset_v_ += 60.0f;
        MarkForUpdate();
        ClampScrolling_(false, true, -1);
      }
      break;

    case base::WidgetMessage::Type::kShow: {
      claimed = true;
      pass = false;
      auto i = widgets().begin();
      if (i == widgets().end()) {
        break;
      }
      float scroll_child_height = (**i).GetHeight();

      float target_y{m.fval2};
      float target_height{m.fval4};

      float vis_height{(height() - 2.0f * (border_height_ + kMarginV))};
      bool changing{};

      // See where we'd have to scroll to get target at top and bottom.
      float child_offset_bot = scroll_child_height - target_y - vis_height;
      float child_offset_top = scroll_child_height - target_y - target_height;

      // If the area we're trying to show is bigger than the space we've got
      // available, aim for the middle. Perhaps we should warn when this
      // happens, but passing huge top+bottom show-buffers can also be a
      // decent way to center the selection so maybe we shouldn't.
      if (vis_height < target_height) {
        child_offset_v_ = 0.5f * (child_offset_top + child_offset_bot);
        changing = true;
      } else {
        // If its already fully visible, don't do anything.
        if (child_offset_v_ > child_offset_bot
            && child_offset_v_ < child_offset_top) {
        } else {
          // Do whichever offset is less of a move.
          if (std::abs(child_offset_bot - child_offset_v_)
              < std::abs(child_offset_top - child_offset_v_)) {
            child_offset_v_ = child_offset_bot;
          } else {
            child_offset_v_ = child_offset_top;
          }
          changing = true;
        }
      }

      if (changing) {
        // If we're moving down, stop at the bottom.
        {
          float max_val = scroll_child_height
                          - (height() - 2.0f * (border_height_ + kMarginV));
          if (child_offset_v_ > max_val) {
            child_offset_v_ = max_val;
          }
        }

        // If we're moving up, stop at the top.
        {
          if (child_offset_v_ < 0.0f) {
            child_offset_v_ = 0.0f;
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

    case base::WidgetMessage::Type::kMouseWheelH: {
      // If its out of our bounds, ignore and don't pass to children.
      float x = m.fval1;
      float y = m.fval2;
      if (!(x >= 0.0f && x < width() && y >= 0.0f && y < height())) {
        pass = false;
        break;
      }

      last_scroll_was_touch_ = false;

      // We don't do anything with h-scrolling but we do keep track
      // of the current speed.
      scroll_h_accum_ += m.fval3;

      if (!should_pass_h_scroll_to_children_) {
        pass = false;
        break;
      }

      break;
    }

    case base::WidgetMessage::Type::kMouseWheelVelocityH: {
      // If its out of our bounds, ignore and don't pass to children.
      float x = m.fval1;
      float y = m.fval2;
      if (!(x >= 0.0f && x < width() && y >= 0.0f && y < height())) {
        pass = false;
        break;
      }

      last_scroll_was_touch_ = false;

      // We don't do anything with h-scrolling but we do keep track
      // of the current speed.
      auto event_is_momentum = static_cast<bool>(m.fval4);
      if (!event_is_momentum) {
        scroll_h_accum_ += m.fval3;
      }

      if (!should_pass_h_scroll_to_children_) {
        pass = false;
        break;
      }

      break;
    }

    case base::WidgetMessage::Type::kMouseWheel: {
      // If its out of our bounds, ignore and don't pass to children.
      float x = m.fval1;
      float y = m.fval2;
      if (!(x >= 0.0f && x < width() && y >= 0.0f && y < height())) {
        pass = false;
        break;
      }

      last_scroll_was_touch_ = false;

      // Keep track of whether we're getting actual events or momentum
      // ones.
      has_momentum_ = false;
      last_v_scroll_event_time_millisecs_ =
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

      // Don't do scrolling if everything is visible.
      if (amount_visible_ >= 1.0f) {
        break;
      }

      // Simply add it to our accum val; we'll apply at next update.
      claimed = true;
      pass = false;
      scroll_v_accum_ -= m.fval3;
      break;
    }

    case base::WidgetMessage::Type::kMouseWheelVelocity: {
      // If its out of our bounds, ignore and don't pass to children.
      float x = m.fval1;
      float y = m.fval2;
      if (!(x >= 0.0f && x < width() && y >= 0.0f && y < height())) {
        pass = false;
        break;
      }

      last_scroll_was_touch_ = false;

      // Keep a few things up to date regardless of what we do with the
      // event.
      has_momentum_ = static_cast<bool>(m.fval4);

      // Do nothing with momentum events since we calc our own momentum.
      if (has_momentum_) {
        claimed = true;
        pass = false;
        break;
      }
      last_v_scroll_event_time_millisecs_ =
          static_cast<millisecs_t>(g_base->logic->display_time() * 1000.0);

      // Don't do scrolling if everything is visible.
      if (amount_visible_ >= 1.0f) {
        break;
      }

      // Simply add it to our accum val; we'll apply at next update.
      claimed = true;
      pass = false;
      scroll_v_accum_ += m.fval3;
      break;
    }

    case base::WidgetMessage::Type::kMouseDown: {
      float x = m.fval1;
      float y = m.fval2;
      if (!handling_deferred_click_) {
        // In our scroll box?
        if (x >= 0.0f && x < (width() + right_overlap) && y >= 0.0f
            && y < height()) {
          // On touch devices, touches begin scrolling, (and eventually can
          // count as clicks if they don't move).
          if (g_base->ui->touch_mode()) {
            touch_held_ = true;
            last_touch_held_time_ = g_core->AppTimeMillisecs();

            auto click_count = static_cast<int>(m.fval3);
            touch_held_click_count_ = click_count;
            touch_down_sent_ = false;
            touch_up_sent_ = false;
            touch_start_x_ = x;
            touch_start_y_ = y;
            touch_moved_significantly_ = false;
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
              last_scroll_was_touch_ = true;
            }

            pass = false;
            claimed = true;

            if (!touch_is_scrolling_) {
              // Give children a chance to claim this for their own scrolling
              // before we do so.
              child_is_scrolling_ =
                  ContainerWidget::HandleMessage(base::WidgetMessage(
                      base::WidgetMessage::Type::kScrollMouseDown, nullptr,
                      m.fval1, m.fval2, m.fval3));

              // After a short delay we go ahead and handle this as a regular
              // click if it hasn't turned into a scroll or a child scroll.
              if (!child_is_scrolling_) {
                touch_delay_timer_ = base::AppTimer::New(
                    0.150, false, [this] { OnTouchDelayTimerExpired(); });
              }
            }
          }

          // For mouse type devices, allow clicking on the scrollbar.
          if (!g_base->ui->touch_mode()) {
            if (x >= width() - scroll_bar_width_ - left_overlap) {
              claimed = true;
              pass = false;
              float s_top = height() - border_height_;
              float s_bottom = border_height_;
              float sb_thumb_height =
                  amount_visible_ * (height() - 2.0f * border_height_);
              float sb_thumb_top =
                  s_top
                  - child_offset_v_ / child_max_offset_
                        * (s_top - (s_bottom + sb_thumb_height));
              // Above thumb (page-up).
              if (y >= sb_thumb_top) {
                // So we can see the transition.
                smoothing_amount_ = 1.0f;
                child_offset_v_ -=
                    (height() - 2.0f * (border_height_ + kMarginV));
                MarkForUpdate();
                ClampScrolling_(false, true, -1);
              } else if (y >= sb_thumb_top - sb_thumb_height) {
                // On thumb.
                mouse_held_thumb_ = true;
                thumb_click_start_v_ = y;
                thumb_click_start_child_offset_v_ = child_offset_v_;
              } else if (y >= s_bottom) {
                // Below thumb (page down). So we can see the transition.
                smoothing_amount_ = 1.0f;
                child_offset_v_ +=
                    (height() - 2.0f * (border_height_ + kMarginV));
                MarkForUpdate();
                ClampScrolling_(false, true, -1);
              }
            }
          }
        } else {
          // Not in the scroll box; dont allow children to claim it.
          pass = false;
        }
      }
      break;
    }

    case base::WidgetMessage::Type::kMouseMove: {
      float x = m.fval1;
      float y = m.fval2;
      bool was_claimed = (m.fval3 > 0.0f);

      if (was_claimed) {
        claimed = true;
      }

      // If coords are outside of our bounds we don't want to pass
      // mouse-moved events through the standard container logic.
      // (otherwise, if we mouse down over a button that doesn't overlap the
      // scroll area but overlaps some widget in the scroll area, the widget
      // would claim the move and the button would lose its
      // mouse-over-highlight; ew.) There may be some case where we *would*
      // want to pass this though.
      auto in_bounds = ((x >= 0.0f) && (x < width() + right_overlap)
                        && (y >= 0.0f) && (y < height()));

      auto repeat_out_of_bounds = !last_mouse_move_in_bounds_ && !in_bounds;
      auto just_exited_bounds = last_mouse_move_in_bounds_ && !in_bounds;
      last_mouse_move_in_bounds_ = in_bounds;

      // If we weren't in bounds before and still aren't, don't bother
      // passing to our children (a single already-claimed move should be
      // enough for them to cancel hovers/etc).
      if (repeat_out_of_bounds) {
        pass = false;
      }

      if (was_claimed) {
        // No hovering if someone above us claimed this.
        hovering_thumb_ = false;
      } else {
        if (g_base->ui->touch_mode()) {
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

              // If we're currently scrolling but this touch has moved
              // significantly left or right, cancel our scrolling and pass
              // the touch.
              auto since_held =
                  g_core->AppTimeMillisecs() - last_touch_held_time_;
              auto xdiff = std::abs(touch_x_ - touch_start_x_);
              auto ydiff = std::abs(touch_y_ - touch_start_y_);

              // Stop watching for left/right scrolling once they've moved a
              // short distance (50 virtual pixels). Otherwise they could
              // erroneously trigger us later in a long touch where they're
              // moving around a lot.
              auto touch_had_moved_significantly = touch_moved_significantly_;
              if (!touch_moved_significantly_
                  && xdiff * xdiff + ydiff * ydiff > (50.0f * 50.0f)) {
                touch_moved_significantly_ = true;
              }

              if (!touch_had_moved_significantly && touch_is_scrolling_
                  && xdiff > 3.0f && (ydiff < 0.1f || xdiff / ydiff > 1.25f)) {
                touch_held_ = false;
                touch_is_scrolling_ = false;
                inertia_scroll_rate_ = 0.0f;
                MarkForUpdate();

                ContainerWidget::HandleMessage(base::WidgetMessage(
                    base::WidgetMessage::Type::kMouseDown, nullptr,
                    touch_start_x_, touch_start_y_, false));
                ContainerWidget::HandleMessage(
                    base::WidgetMessage(base::WidgetMessage::Type::kMouseMove,
                                        nullptr, touch_x_, touch_y_, false));

              } else if (!touch_is_scrolling_
                         && ((std::abs(touch_x_ - touch_start_x_) > 10.0f)
                             || (std::abs(touch_y_ - touch_start_y_)
                                 > 10.0f))) {
                // If we move more than a slight amount it means our touch
                // goes to scrolling and isn't a deferred click.
                touch_is_scrolling_ = true;
                last_scroll_was_touch_ = true;

                // Go ahead and send a mouse-up to our sub-widgets; in their
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

        if (g_base->ui->touch_mode()) {
          hovering_thumb_ = false;
        } else {
          float s_top = height() - border_height_;
          float s_bottom = border_height_;
          float sb_thumb_height =
              amount_visible_ * (height() - 2.0f * border_height_);
          float sb_thumb_top = s_top
                               - child_offset_v_ / child_max_offset_
                                     * (s_top - (s_bottom + sb_thumb_height));

          hovering_thumb_ =
              (((x >= width() - scroll_bar_width_ - left_overlap)
                && (x < width() + right_overlap) && y < sb_thumb_top
                && y >= sb_thumb_top - sb_thumb_height));

          if (hovering_thumb_) {
            claimed = true;
          }
        }
      }

      // If we're dragging the thumb.
      if (mouse_held_thumb_) {
        claimed = true;  // We own this; noone below us should highlight.u

        auto i = widgets().begin();
        if (i != widgets().end()) {
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
          ClampScrolling_(false, true, -1);
          MarkForUpdate();
        }
      }

      // If we're hovering over or dragging the thumb or we just exited our
      // bounds, send the event to children but with claimed marked as true
      // so they know to kill hover effects/etc.
      if (mouse_held_thumb_ || hovering_thumb_ || just_exited_bounds) {
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
      if (g_base->ui->touch_mode()) {
        if (touch_held_) {
          // If we moved at all, we mark it as claimed to keep sub-widgets
          // from acting on it (since we used it for scrolling)
          bool claimed2 = touch_is_scrolling_ || child_is_scrolling_;

          // If a child is still scrolling, send them a
          // scroll-mouse-up/cancel.
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

          touch_held_ = false;
          touch_is_scrolling_ = false;
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
  BA_DEBUG_UI_READ_LOCK;  // Make sure hierarchy doesn't change under us.

  // Move everything based on our offset.
  auto i = widgets().begin();
  if (i == widgets().end()) {
    amount_visible_ = 0.0f;
    return;
  }

  float extra_border_x{4.0f};  // Whee arbitrary hard coded values.
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
      child_height - (height() - 2.0f * (border_height_ + kMarginV));
  amount_visible_ =
      (height() - 2.0f * (border_height_ + kMarginV)) / child_height;
  if (amount_visible_ > 1.0f) {
    amount_visible_ = 1.0f;
    if (center_small_content_) {
      center_offset_y_ = child_max_offset_ * 0.5f;
    } else {
      center_offset_y_ = 0.0f;
    }
  } else {
    center_offset_y_ = 0.0f;
  }

  if (mouse_held_thumb_) {
    if (child_offset_v_
        > child_height - (height() - 2.0f * (border_height_ + kMarginV))) {
      child_offset_v_ =
          child_height - (height() - 2.0f * (border_height_ + kMarginV));
      inertia_scroll_rate_ = 0;
    }
    if (child_offset_v_ < 0.0f) {
      child_offset_v_ = 0.0f;
      inertia_scroll_rate_ = 0.0f;
    }
  }
  (**i).set_translate(xoffs, height() - (border_height_ + kMarginV)
                                 + child_offset_v_smoothed_ - child_height
                                 + center_offset_y_);
  thumb_dirty_ = true;
}

void ScrollWidget::UpdateScrolling_(millisecs_t current_time_millisecs) {
  float prev_child_offset_v_smoothed = child_offset_v_smoothed_;

  // Skip huge differences.
  if (current_time_millisecs - inertia_scroll_update_time_millisecs_ > 100) {
    inertia_scroll_update_time_millisecs_ = current_time_millisecs - 100;
  }

  // Step once per 4ms; should give us decent consistency at 60 or 120hz.
  while (current_time_millisecs - inertia_scroll_update_time_millisecs_ > 4) {
    inertia_scroll_update_time_millisecs_ += 4;

    // Keep a smoothed value of how much scrolling we're *trying* to do,
    // in both x and y.
    auto accum_smoothing{0.5f};
    scroll_h_accum_smoothed_ = accum_smoothing * scroll_h_accum_smoothed_
                               + (1.0f - accum_smoothing) * scroll_h_accum_;
    scroll_v_accum_smoothed_ = accum_smoothing * scroll_v_accum_smoothed_
                               + (1.0f - accum_smoothing) * scroll_v_accum_;

    // Update whether we should be passing h-scrolls to children (we
    // suppress our vertical scrolling while we're doing child horizontal
    // scrolling and vice versa).
    {
      auto scroll_h_mag{std::abs(scroll_h_accum_smoothed_)};
      auto scroll_v_mag{std::abs(scroll_v_accum_smoothed_)};
      if (should_pass_h_scroll_to_children_) {
        if (scroll_v_mag > 0.1 && scroll_v_mag > scroll_h_mag * 2.0) {
          should_pass_h_scroll_to_children_ = false;
          // printf("OFF %.3f %.3f\n", scroll_h_mag, scroll_v_mag);
        }
      } else {
        if (scroll_h_mag > 0.1 && scroll_h_mag > scroll_v_mag * 2.0) {
          should_pass_h_scroll_to_children_ = true;
          // printf("ON %.3f %.3f\n", scroll_h_mag, scroll_v_mag);
        }
      }
    }

    // Update our scrolling rate based on our latest accumulated scroll
    // values.
    //
    // TODO(ericf): Ideally we should be tracking scroll actions through to
    // the end and ALWAYS be setting this during the scroll; not only when
    // there are significant values.
    if (std::abs(scroll_v_accum_) > 0.0001f) {
      // Add a bit of smoothing here since what we're doing is not entirely
      // accurate (ie: 3 staggered scroll events with a value of 4 will give
      // us a lower velocity than a single event with value 12 even though
      // they're supposed to represent the same change. Smoothing helps even
      // things out a bit).
      float smoothing{0.5f};
      float scroll_speed = 8.0f;
      inertia_scroll_rate_ =
          smoothing * inertia_scroll_rate_
          + (1.0f - smoothing) * (scroll_speed * scroll_v_accum_);
      scroll_v_accum_ = 0.0f;
    }
    scroll_h_accum_ = 0.0f;

    // Limit how far we can overshoot edges by clamping velocity as we do.
    auto fade_region{200.0f};
    float inertia_scroll_mult{1.0f};
    if (inertia_scroll_rate_ < 0.0f) {
      // If we're scrolling up and have passed the top, slow down.
      if (child_offset_v_ < 0.0f) {
        inertia_scroll_mult =
            inv_lerp_clamped(-fade_region, 0.0f, child_offset_v_);
      }
    } else {
      // If we're scrolling down and have passed the bottom, slow down.
      auto i = widgets().begin();
      if (i != widgets().end()) {
        float child_height = (**i).GetHeight();
        float diff =
            child_offset_v_
            - (child_height
               - std::min(child_height,
                          (height() - 2.0f * (border_height_ + kMarginV))));
        if (diff > 0.0f) {
          inertia_scroll_mult = inv_lerp_clamped(fade_region, 0.0f, diff);
        }
      }
    }

    // If we're using scroll events (not touches) and we're h-scrolling
    // children, freeze vertically.
    if (should_pass_h_scroll_to_children_ && !last_scroll_was_touch_) {
      inertia_scroll_mult = 0.0f;
    }

    // In touch mode, push our scroll rate to match what the touch is doing.
    if (g_base->ui->touch_mode()) {
      if (touch_held_) {
        float diff = (touch_y_ - child_offset_v_) - touch_down_y_;

        // Calibrate springiness here so scrolling stays as close to a
        // cursor as possible without noise or oscillations.
        float aggression{0.3f};
        float smoothing = 0.7f;
        // float damping_scale = 0.6f;
        inertia_scroll_rate_ = smoothing * inertia_scroll_rate_
                               + (1.0f - smoothing) * aggression * diff;

        // float fudge{1.0f};  // Calibrate to visually match.
        // float smoothing = 0.0f;
        // inertia_scroll_rate_ = smoothing * inertia_scroll_rate_
        //                        + (1.0f - smoothing) * fudge * diff;
      } else {
        inertia_scroll_rate_ *= 0.985f;
      }
    } else {
      inertia_scroll_rate_ *= 0.985f;
    }
    ClampScrolling_(true, mouse_held_thumb_, current_time_millisecs);  //

    // Finally update our scroll position.
    child_offset_v_ +=
        inertia_scroll_rate_ * std::pow(inertia_scroll_mult, 2.0f);

    // Lastly we apply smoothing so that if we're snapping to a specific
    // place we don't go instantly there we blend between smoothed and
    // non-smoothed depending on whats driving us (we dont want to add
    // smoothing on top of inertial scrolling for example or it'll feel
    // muddy).
    float diff = child_offset_v_ - child_offset_v_smoothed_;
    if (std::abs(diff) < 1.0f) {
      child_offset_v_smoothed_ = child_offset_v_;
    } else {
      child_offset_v_smoothed_ += (1.0f - smoothing_amount_) * diff;
    }
    smoothing_amount_ = std::max(0.0f, smoothing_amount_ - 0.002f);
  }

  // Only re-layout our widgets if we've moved a significant amount.
  if (std::abs(prev_child_offset_v_smoothed - child_offset_v_smoothed_)
      > 0.01f) {
    MarkForUpdate();
  }
}

void ScrollWidget::Draw(base::RenderPass* pass, bool draw_transparent) {
  have_drawn_ = true;

  auto current_time_millisecs{pass->frame_def()->display_time_millisecs()};

  // Ok, lets update our inertial scrolling during the opaque pass (we
  // really should have some sort of update() function for this but widgets
  // don't have that).
  if (!draw_transparent) {
    UpdateScrolling_(current_time_millisecs);
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
    auto scissor =
        c.ScopedScissor({l + border_width_, b + border_height_ + 1.0f,
                         l + (width() - border_width_),
                         b + (height() - border_height_) - 1.0f});
    c.Submit();  // Get out of the way for children drawing.

    set_simple_culling_bottom(b + border_height_ + 1.0f);
    set_simple_culling_top(b + (height() - border_height_) - 1.0f);

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
          l_border = 3.0f;
          r_border = 0.0f;
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
            - ((height() - (border_height_ * 2.0f) - sb_thumb_height)
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
        } else if (hovering_thumb_) {
          c_scale = 1.25f;
        }

        c.SetColor(color_red_ * c_scale, color_green_ * c_scale,
                   color_blue_ * c_scale, 1.0f);

        c.SetTexture(g_base->assets->SysTexture(base::SysTextureID::kUIAtlas));
        {
          auto scissor =
              c.ScopedScissor({l + border_width_, b + border_height_ + 1.0f,
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
    float m = (0.8f
               + std::abs(sinf(static_cast<float>(current_time_millisecs)
                               * 0.006467f))
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
