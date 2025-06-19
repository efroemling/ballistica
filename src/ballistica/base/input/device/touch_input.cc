// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/touch_input.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/component/simple_component.h"
#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/support/app_config.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/logging/logging_macros.h"

namespace ballistica::base {

const float kButtonSpread = 10.0f;
const float kDrawDepth = -0.07f;

// Given coords within a (-1,-1) to (1,1) box,
// convert them such that their length is never greater than 1.
static void CircleToBoxCoords(float* lr, float* ud) {
  if (std::abs((*lr)) < 0.0001f || std::abs((*ud)) < 0.0001f) {
    return;  // Not worth doing anything.
  }

  // Project them out to hit the border.
  float s;
  if (std::abs((*lr)) > std::abs((*ud))) {
    s = 1.0f / std::abs((*lr));
  } else {
    s = 1.0f / std::abs((*ud));
  }
  float proj_lr = (*lr) * s;
  float proj_ud = (*ud) * s;
  float proj_len = sqrtf(proj_lr * proj_lr + proj_ud * proj_ud);
  (*lr) *= proj_len;
  (*ud) *= proj_len;
}

void TouchInput::HandleTouchEvent(TouchEvent::Type type, void* touch, float x,
                                  float y) {
  // Currently we completely ignore these when in editing mode;
  // In that case we get fed in SDL mouse events
  // (so we can properly mask interaction with widgets, etc).
  if (editing()) {
    return;
  }

  switch (type) {
    case TouchEvent::Type::kDown: {
      HandleTouchDown(touch, x, y);
      return;
    }
    case TouchEvent::Type::kCanceled:
    case TouchEvent::Type::kUp: {
      HandleTouchUp(touch, x, y);
      return;
    }
    case TouchEvent::Type::kMoved: {
      HandleTouchMoved(touch, x, y);
      return;
    }
  }
  BA_LOG_ERROR_NATIVE_TRACE_ONCE("Unhandled touch event type "
                                 + std::to_string(static_cast<int>(type)));
}

TouchInput::TouchInput() {
  switch (g_base->ui->uiscale()) {
    case UIScale::kSmall:
      base_controls_scale_ = 2.0f;
      world_draw_scale_ = 1.2f;
      break;
    case UIScale::kMedium:
      base_controls_scale_ = 1.5f;
      world_draw_scale_ = 1.1f;
      break;
    default:
      base_controls_scale_ = 1.0f;
      world_draw_scale_ = 1.0f;
      break;
  }

  assert(g_base);
  assert(g_base->touch_input == nullptr);
  g_base->touch_input = this;
}

TouchInput::~TouchInput() = default;

void TouchInput::UpdateButtons(bool new_touch) {
  millisecs_t real_time = g_core->AppTimeMillisecs();
  float spread_scaled_actions =
      kButtonSpread * base_controls_scale_ * controls_scale_actions_;
  float width = g_base->graphics->screen_virtual_width();
  float height = g_base->graphics->screen_virtual_height();
  float edge_buffer = spread_scaled_actions;

  if (new_touch && action_control_type_ == ActionControlType::kSwipe) {
    buttons_x_ = buttons_touch_x_;
    buttons_y_ = buttons_touch_y_;
  }

  // See which button we're closest to.
  float bomb_mag = buttons_touch_x_ - buttons_x_;
  float punch_mag = buttons_x_ - buttons_touch_x_;
  float jump_mag = buttons_y_ - buttons_touch_y_;
  float pickup_mag = buttons_touch_y_ - buttons_y_;
  float max_mag =
      std::max(std::max(std::max(bomb_mag, punch_mag), jump_mag), pickup_mag);
  bool closest_to_bomb = false;
  bool closest_to_punch = false;
  bool closest_to_jump = false;
  bool closest_to_pickup = false;
  if (bomb_mag == max_mag) {
    closest_to_bomb = true;
  } else if (punch_mag == max_mag) {
    closest_to_punch = true;
  } else if (jump_mag == max_mag) {
    closest_to_jump = true;
  } else if (pickup_mag == max_mag) {
    closest_to_pickup = true;
  } else {
    char buffer[256];
    snprintf(buffer, sizeof(buffer),
             "TouchInput closest-to logic fail; bomb_mag=%f"
             " punch_mag=%f jump_mag=%f pickup_mag=%f max_mag=%f",
             bomb_mag, punch_mag, jump_mag, pickup_mag, max_mag);
    BA_LOG_ERROR_NATIVE_TRACE_ONCE(buffer);
    closest_to_bomb = true;
  }
  if (buttons_touch_) {
    last_buttons_touch_time_ = g_core->AppTimeMillisecs();
  }

  // Handle swipe mode.
  if (action_control_type_ == ActionControlType::kSwipe) {
    // If we're dragging on one axis, center the other axis.
    if (closest_to_bomb
        // NOLINTNEXTLINE(bugprone-branch-clone)
        && buttons_touch_x_ >= buttons_x_ + spread_scaled_actions) {
      buttons_y_ = buttons_touch_y_;
    } else if (closest_to_punch
               && buttons_touch_x_ <= buttons_x_ - spread_scaled_actions) {
      buttons_y_ = buttons_touch_y_;
    } else if (closest_to_pickup
               // NOLINTNEXTLINE(bugprone-branch-clone)
               && buttons_touch_y_ >= buttons_y_ + spread_scaled_actions) {
      buttons_x_ = buttons_touch_x_;
    } else if (closest_to_jump
               && buttons_touch_y_ <= buttons_y_ - spread_scaled_actions) {
      buttons_x_ = buttons_touch_x_;
    }

    // Drag along the axis we're dragging.
    float spread_scaled_actions_extra = 1.01f * spread_scaled_actions;
    if (closest_to_bomb
        && buttons_touch_x_ >= buttons_x_ + spread_scaled_actions_extra) {
      buttons_x_ = buttons_touch_x_ - spread_scaled_actions_extra;
    } else if (closest_to_punch
               && buttons_touch_x_
                      <= buttons_x_ - spread_scaled_actions_extra) {
      buttons_x_ = buttons_touch_x_ + spread_scaled_actions_extra;
    } else if (closest_to_pickup
               && buttons_touch_y_
                      >= buttons_y_ + spread_scaled_actions_extra) {
      buttons_y_ = buttons_touch_y_ - spread_scaled_actions_extra;
    } else if (closest_to_jump
               && buttons_touch_y_
                      <= buttons_y_ - spread_scaled_actions_extra) {
      buttons_y_ = buttons_touch_y_ + spread_scaled_actions_extra;
    }

    // Keep them away from screen edges.
    if (buttons_x_ > width - edge_buffer) {
      buttons_x_ = width - edge_buffer;
    }
    if (buttons_y_ > height - edge_buffer) {
      buttons_y_ = height - edge_buffer;
    } else if (buttons_y_ < edge_buffer) {
      buttons_y_ = edge_buffer;
    }

    // Handle new presses.
    if (buttons_touch_) {
      if (!bomb_held_
          && buttons_touch_x_ >= buttons_x_ + spread_scaled_actions) {
        bomb_held_ = true;
        last_bomb_press_time_ = real_time;
        InputCommand(InputType::kBombPress);
      }
      if (!punch_held_
          && buttons_touch_x_ <= buttons_x_ - spread_scaled_actions) {
        punch_held_ = true;
        last_punch_press_time_ = real_time;
        InputCommand(InputType::kPunchPress);
      }
      if (!jump_held_
          && buttons_touch_y_ <= buttons_y_ - spread_scaled_actions) {
        jump_held_ = true;
        last_jump_press_time_ = real_time;
        InputCommand(InputType::kJumpPress);
      }
      if (!pickup_held_
          && buttons_touch_y_ >= buttons_y_ + spread_scaled_actions) {
        pickup_held_ = true;
        last_pickup_press_time_ = real_time;
        InputCommand(InputType::kPickUpPress);
      }
    }

    // Handle releases.
    if (bomb_held_
        && (!buttons_touch_
            || buttons_touch_x_ < buttons_x_ + spread_scaled_actions)) {
      bomb_held_ = false;
      last_bomb_held_time_ = real_time;
      InputCommand(InputType::kBombRelease);
    }
    if (punch_held_
        && (!buttons_touch_
            || buttons_touch_x_ > buttons_x_ - spread_scaled_actions)) {
      punch_held_ = false;
      last_punch_held_time_ = real_time;
      InputCommand(InputType::kPunchRelease);
    }
    if (jump_held_
        && (!buttons_touch_
            || buttons_touch_y_ > buttons_y_ - spread_scaled_actions)) {
      jump_held_ = false;
      last_jump_held_time_ = real_time;
      InputCommand(InputType::kJumpRelease);
    }
    if (pickup_held_
        && (!buttons_touch_
            || buttons_touch_y_ < buttons_y_ + spread_scaled_actions)) {
      pickup_held_ = false;
      last_pickup_held_time_ = real_time;
      InputCommand(InputType::kPickUpRelease);
    }
  } else {
    bool was_bomb_held = bomb_held_;
    bool was_jump_held = jump_held_;
    bool was_pickup_held = pickup_held_;
    bool was_punch_held = punch_held_;
    bomb_held_ = jump_held_ = pickup_held_ = punch_held_ = false;
    if (buttons_touch_) {
      if (closest_to_bomb) {
        bomb_held_ = true;
        if (!was_bomb_held) {
          last_bomb_press_time_ = real_time;
          InputCommand(InputType::kBombPress);
        }
      } else if (closest_to_punch) {
        punch_held_ = true;
        if (!was_punch_held) {
          last_punch_press_time_ = real_time;
          InputCommand(InputType::kPunchPress);
        }
      } else if (closest_to_jump) {
        jump_held_ = true;
        if (!was_jump_held) {
          last_jump_press_time_ = real_time;
          // fixme should just send one or the other..
          InputCommand(InputType::kJumpPress);
          InputCommand(InputType::kFlyPress);
        }
      } else if (closest_to_pickup) {
        pickup_held_ = true;
        if (!was_pickup_held) {
          last_pickup_press_time_ = real_time;
          InputCommand(InputType::kPickUpPress);
        }
      }
    }

    // Handle releases.
    if (was_bomb_held && !bomb_held_) {
      last_bomb_held_time_ = real_time;
      InputCommand(InputType::kBombRelease);
    }
    if (was_punch_held && !punch_held_) {
      punch_held_ = false;
      last_punch_held_time_ = real_time;
      InputCommand(InputType::kPunchRelease);
    }
    if (was_jump_held && !jump_held_) {
      jump_held_ = false;
      last_jump_held_time_ = real_time;
      // fixme should just send one or the other..
      InputCommand(InputType::kJumpRelease);
      InputCommand(InputType::kFlyRelease);
    }
    if (was_pickup_held && !pickup_held_) {
      pickup_held_ = false;
      last_pickup_held_time_ = real_time;
      InputCommand(InputType::kPickUpRelease);
    }
  }
}

void TouchInput::UpdateDPad() {
  // Keep our base somewhat close to our drag point.
  float max_dist = 30.0f * base_controls_scale_ * controls_scale_move_;

  // Keep it within a circle of max_dist radius.
  float x = (d_pad_x_ - d_pad_base_x_) / max_dist;
  float y = (d_pad_y_ - d_pad_base_y_) / max_dist;
  float len = sqrtf(x * x + y * y);

  // In swipe mode we move our base around to follow the touch.
  if (movement_control_type_ == MovementControlType::kSwipe) {
    // If this is the first move event, scoot our base towards our current point
    // by a small amount. This is meant to counter the fact that the first
    // touch-moved event is always significantly far from the touch-down and
    // allows us to start out moving slowly.
    if (!did_first_move_ && (x != 0 || y != 0)) {
      if (len != 0.0f) {
        float offs = 0.8f * std::min(len, 0.8f);
        d_pad_base_x_ += x * max_dist * (offs / len);
        d_pad_base_y_ += y * max_dist * (offs / len);
        x = (d_pad_x_ - d_pad_base_x_) / max_dist;
        y = (d_pad_y_ - d_pad_base_y_) / max_dist;
        len = sqrtf(x * x + y * y);
      }
      did_first_move_ = true;
    }

    if (len > 1.0f) {
      float inv_len = 1.0f / len;
      x *= inv_len;
      y *= inv_len;
      d_pad_base_x_ = d_pad_x_ - x * max_dist;
      d_pad_base_y_ = d_pad_y_ - y * max_dist;
    }
  } else {
    // Likewise in joystick mode we keep our touch near the base.
    if (len > 1.0f) {
      float inv_len = 1.0f / len;
      x *= inv_len;
      y *= inv_len;
      d_pad_x_ = d_pad_base_x_ + x * max_dist;
      d_pad_y_ = d_pad_base_y_ + y * max_dist;
    }
  }

  d_pad_draw_x_ = x;
  d_pad_draw_y_ = y;

  // Although its a circle we need to deliver box coords.. (ie: upper-left is
  // -1,1).
  CircleToBoxCoords(&x, &y);

  float remap = 1.0f;
  InputCommand(InputType::kLeftRight, x * remap);
  InputCommand(InputType::kUpDown, y * remap);
}

void TouchInput::Draw(FrameDef* frame_def) {
  assert(g_base->InLogicThread());
  bool active = (!g_base->ui->IsMainUIVisible());
  millisecs_t real_time = frame_def->app_time_millisecs();

  // Update our action center whenever possible in case screen is resized.
  if (!buttons_touch_) {
    float width = g_base->graphics->screen_virtual_width();
    float height = g_base->graphics->screen_virtual_height();
    buttons_x_ = width * buttons_default_frac_x_;
    buttons_y_ = height * buttons_default_frac_y_;
  }
  // Same for dpad.
  if (!d_pad_touch_) {
    float width = g_base->graphics->screen_virtual_width();
    float height = g_base->graphics->screen_virtual_height();
    d_pad_x_ = d_pad_base_x_ = width * d_pad_default_frac_x_;
    d_pad_y_ = d_pad_base_y_ = height * d_pad_default_frac_y_;
  }

  // Update time-dependent stuff to this point.
  if ((real_time - update_time_ > 500) && (real_time - update_time_ < 99999)) {
    update_time_ = real_time - 500;
  }
  while (update_time_ < real_time) {
    update_time_ += 10;

    // Update presence based on whether or not we're active.
    if ((AttachedToPlayer() && active) || editing_) {
      presence_ = std::min(1.0f, presence_ + 0.06f);
    } else {
      presence_ = std::max(0.0f, presence_ - 0.06f);
    }

    if (action_control_type_ == ActionControlType::kSwipe) {
      // Overall backing opacity fades in and out based on whether we have a
      // button touch.
      if (buttons_touch_ || editing_) {
        button_fade_ = std::min(1.0f, button_fade_ + 0.06f);
      } else {
        button_fade_ = std::max(0.0f, button_fade_ - 0.015f);
      }

      // If there's a button touch but its not on a button, slowly move the
      // center towards it (keeps us from slowly sliding onto a button press
      // while trying to run and stuff).
      if (buttons_touch_ && !bomb_held_ && !punch_held_ && !pickup_held_
          && !jump_held_) {
        buttons_x_ += 0.015f * (buttons_touch_x_ - buttons_x_);
        buttons_y_ += 0.015f * (buttons_touch_y_ - buttons_y_);
      }
    } else {
      button_fade_ = 1.0f;
    }
  }

  if (presence_ > 0.0f) {
    float width = g_base->graphics->screen_virtual_width();
    float height = g_base->graphics->screen_virtual_height();
    SimpleComponent c(frame_def->GetOverlayFlatPass());
    c.SetTransparent(true);

    float sc_move = base_controls_scale_ * controls_scale_move_
                    * (200.0f - presence_ * 100.0f);
    float sc_actions = base_controls_scale_ * controls_scale_actions_
                       * (200.0f - presence_ * 100.0f);

    bool do_draw;
    if (movement_control_type_ == MovementControlType::kSwipe) {
      do_draw = (!d_pad_touch_ && !swipe_controls_hidden_);
    } else {
      do_draw = true;  // always draw in joystick mode
    }

    if (do_draw) {
      float sc2 = sc_move;
      if (movement_control_type_ == MovementControlType::kSwipe) sc2 *= 0.6f;

      if (movement_control_type_ == MovementControlType::kSwipe) {
        c.SetTexture(g_base->assets->SysTexture(SysTextureID::kTouchArrows));
        if (editing_) {
          float val = 1.5f + sinf(static_cast<float>(real_time) * 0.02f);
          c.SetColor(val, val, 1.0f, 1.0f);
        }
      } else {
        float val;
        if (editing_) {
          val = 0.35f + 0.15f * sinf(static_cast<float>(real_time) * 0.02f);
        } else {
          val = 0.35f;
        }
        c.SetColor(0.5f, 0.3f, 0.8f, val);
        c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCircle));
      }

      float x_offs =
          width * (-0.1f - d_pad_default_frac_x_) * (1.0f - presence_);
      float y_offs =
          height * (-0.1f - d_pad_default_frac_y_) * (1.0f - presence_);

      {
        auto xf = c.ScopedTransform();
        c.Translate(d_pad_base_x_ + x_offs, d_pad_base_y_ + y_offs, kDrawDepth);
        c.Scale(sc2, sc2);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
      }

      if (movement_control_type_ == MovementControlType::kJoystick) {
        float val;
        if (editing_) {
          val = 0.35f + 0.15f * sinf(static_cast<float>(real_time) * 0.02f);
        } else {
          val = 0.35f;
        }
        c.SetColor(0.0f, 0.0f, 0.0f, val);
        {
          auto xf = c.ScopedTransform();
          c.Translate(d_pad_x_ + x_offs, d_pad_y_ + y_offs, kDrawDepth);
          c.Scale(sc_move * 0.5f, sc_move * 0.5f);
          c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
        }
      }
    }

    if (!buttons_touch_ && action_control_type_ == ActionControlType::kSwipe
        && !swipe_controls_hidden_) {
      float sc2{sc_actions * 0.6f};
      c.SetTexture(
          g_base->assets->SysTexture(SysTextureID::kTouchArrowsActions));
      if (editing_) {
        float val = 1.5f + sinf(static_cast<float>(real_time) * 0.02f);
        c.SetColor(val, val, 1.0f, 1.0f);
      } else {
        c.SetColor(1.0f, 1.0f, 1.0f, 1.0f);
      }
      {
        auto xf = c.ScopedTransform();
        float x_offs =
            width * (1.1f - buttons_default_frac_x_) * (1.0f - presence_);
        float y_offs =
            height * (-0.1f - buttons_default_frac_y_) * (1.0f - presence_);
        c.Translate(buttons_x_ + x_offs, buttons_y_ + y_offs, kDrawDepth);
        c.Scale(sc2, sc2);
        c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
      }
    }
    c.Submit();
  }

  bool have_player_position{false};
  std::vector<float> player_position(3);
  if (AttachedToPlayer()) {
    auto pos = delegate().GetPlayerPosition();
    if (pos) {
      have_player_position = true;
      player_position = pos->AsStdVector();
    }
  }

  SimpleComponent c(frame_def->GetOverlayFlatPass());
  c.SetTransparent(true);

  uint32_t residual_time{130};

  // Draw buttons.
  bool do_draw;
  if (action_control_type_ == ActionControlType::kButtons) {
    do_draw = (presence_ > 0.0f);
  } else {
    do_draw = (active);
  }

  if (do_draw) {
    float base_fade;

    if (action_control_type_ == ActionControlType::kSwipe) {
      base_fade = 0.25f;
    } else {
      base_fade = 0.8f;
      c.SetTexture(g_base->assets->SysTexture(SysTextureID::kActionButtons));
    }

    float x_offs;
    float y_offs;
    if (action_control_type_ == ActionControlType::kSwipe) {
      x_offs = -buttons_x_;
      y_offs = -buttons_y_ - 75;
    } else {
      x_offs = y_offs = 0.0f;

      // Do transition in button mode.
      if (presence_ < 1.0f) {
        float width = g_base->graphics->screen_virtual_width();
        float height = g_base->graphics->screen_virtual_height();
        x_offs = width * (1.1f - buttons_default_frac_x_) * (1.0f - presence_);
        y_offs =
            height * (-0.1f - buttons_default_frac_y_) * (1.0f - presence_);
      }
    }

    float s{0.5f};

    // In buttons mode we draw based on our UI size. Otherwise we draw in the
    // world at a constant scale.
    if (action_control_type_ == ActionControlType::kButtons) {
      s *= 3.0f * base_controls_scale_ * controls_scale_actions_;
    } else {
      // When not drawing under the character we obey ui size.
      if (!have_player_position) {
        s *= 0.5f * 1.5f * base_controls_scale_ * controls_scale_actions_;
      } else {
        s *= world_draw_scale_;
      }
    }

    float b_width{50.0f * s};
    float half_b_width{0.0f};

    float button_spread_s{0.0f * s};

    if (action_control_type_ == ActionControlType::kSwipe) {
      button_spread_s *= 2.0f;
    }

    bool was_held;
    float pop;
    float pop_time{100.0f};

    {
      auto xf = c.ScopedTransform();

      // In swipe mode we draw under our character when possible, and above the
      // touch otherwise.
      if (action_control_type_ == ActionControlType::kSwipe) {
        if (have_player_position) {
          c.TranslateToProjectedPoint(player_position[0], player_position[1],
                                      player_position[2]);
        } else {
          float s2 = base_controls_scale_ * controls_scale_actions_;
          c.Translate(buttons_touch_start_x_ - s2 * 50.0f,
                      buttons_touch_start_y_ + 75.0f + s2 * 50.0f, 0.0f);
        }
      }

      float squash{1.3f};
      float stretch{1.3f};

      float s_extra{1.0f};
      if (editing_)
        s_extra = 0.7f + 0.3f * sinf(static_cast<float>(real_time) * 0.02f);

      // Bomb.
      was_held =
          bomb_held_ || (real_time - last_bomb_press_time_ < residual_time);
      if ((button_fade_ > 0.0f) || bomb_held_ || was_held) {
        pop = std::max(
            0.0f, 1.0f
                      - static_cast<float>(real_time - last_bomb_press_time_)
                            / pop_time);
        if (was_held) {
          c.SetColor(1.5f, 2.0f * pop, 2.0f * pop, 1.0f);
        } else {
          c.SetColor(0.65f * s_extra, 0.0f, 0.0f, base_fade * button_fade_);
        }

        {
          auto xf = c.ScopedTransform();
          c.Translate(buttons_x_ + button_spread_s + half_b_width + x_offs,
                      buttons_y_ + y_offs, kDrawDepth);
          if (bomb_held_) {
            c.Scale(stretch * b_width, squash * b_width);
          } else {
            c.Scale(b_width, b_width);
          }
          c.DrawMeshAsset(
              g_base->assets->SysMesh(SysMeshID::kActionButtonRight));
        }
      }

      // Punch.
      was_held =
          punch_held_ || (real_time - last_punch_press_time_ < residual_time);
      if ((button_fade_ > 0.0f) || punch_held_ || was_held) {
        pop = std::max(
            0.0f, 1.0f
                      - static_cast<float>(real_time - last_punch_press_time_)
                            / pop_time);
        if (was_held) {
          c.SetColor(1.3f + 2.0f * pop, 1.3f + 2.0f * pop, 0.0f + 2.0f * pop,
                     1.0f);
        } else {
          c.SetColor(0.9f * s_extra, 0.9f * s_extra, 0.2f * s_extra,
                     base_fade * button_fade_);
        }
        {
          auto xf = c.ScopedTransform();
          c.Translate(buttons_x_ - button_spread_s - half_b_width + x_offs,
                      buttons_y_ + y_offs, kDrawDepth);
          if (punch_held_) {
            c.Scale(stretch * b_width, squash * b_width);
          } else {
            c.Scale(b_width, b_width);
          }
          c.DrawMeshAsset(
              g_base->assets->SysMesh(SysMeshID::kActionButtonLeft));
        }
      }

      // Jump.
      was_held =
          jump_held_ || (real_time - last_jump_press_time_ < residual_time);
      if ((button_fade_ > 0.0f) || jump_held_ || was_held) {
        pop = std::max(
            0.0f, 1.0f
                      - static_cast<float>(real_time - last_jump_press_time_)
                            / pop_time);
        if (was_held) {
          c.SetColor(1.8f * pop, 1.2f + 0.9f * pop, 2.0f * pop, 1.0f);
        } else {
          c.SetColor(0.0f, 0.8f * s_extra, 0.0f, base_fade * button_fade_);
        }
        {
          auto xf = c.ScopedTransform();
          c.Translate(buttons_x_ + x_offs,
                      buttons_y_ - button_spread_s - half_b_width + y_offs,
                      kDrawDepth);
          if (jump_held_) {
            c.Scale(squash * b_width, stretch * b_width);
          } else {
            c.Scale(b_width, b_width);
          }
          c.DrawMeshAsset(
              g_base->assets->SysMesh(SysMeshID::kActionButtonBottom));
        }
      }

      // Pickup.
      was_held =
          pickup_held_ || (real_time - last_pickup_press_time_ < residual_time);
      if ((button_fade_ > 0.0f) || pickup_held_ || was_held) {
        pop = std::max(
            0.0f, 1.0f
                      - static_cast<float>(real_time - last_pickup_press_time_)
                            / pop_time);
        if (was_held) {
          c.SetColor(0.5f + 1.4f * pop, 0.8f + 2.4f * pop, 2.0f + 0.4f * pop,
                     1.0f);
        } else {
          c.SetColor(0.3f * s_extra, 0.65f * s_extra, 1.0f * s_extra,
                     base_fade * button_fade_);
        }
        {
          auto xf = c.ScopedTransform();
          c.Translate(buttons_x_ + x_offs,
                      buttons_y_ + button_spread_s + half_b_width + y_offs,
                      kDrawDepth);
          if (pickup_held_) {
            c.Scale(squash * b_width, stretch * b_width);
          } else {
            c.Scale(b_width, b_width);
          }
          c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kActionButtonTop));
        }
      }

      // Center point.
      if (buttons_touch_ && action_control_type_ == ActionControlType::kSwipe) {
        c.SetTexture(g_base->assets->SysTexture(SysTextureID::kCircle));
        c.SetColor(1.0f, 1.0f, 0.0f, 0.8f);
        {
          auto xf = c.ScopedTransform();

          // We need to scale this up/down relative to the scale we're drawing
          // at since we're not drawing in screen space.
          float diff_x = buttons_touch_x_ - buttons_x_;
          float diff_y = buttons_touch_y_ - buttons_y_;

          if (have_player_position) {
            c.Translate(
                buttons_x_
                    + 2.3f * world_draw_scale_ * diff_x
                          / (base_controls_scale_ * controls_scale_actions_)
                    + x_offs,
                buttons_y_
                    + 2.3f * world_draw_scale_ * diff_y
                          / (base_controls_scale_ * controls_scale_actions_)
                    + y_offs,
                kDrawDepth);
          } else {
            c.Translate(buttons_x_ + 0.5f * 1.55f * 2.3f * diff_x + x_offs,
                        buttons_y_ + 0.5f * 1.55f * 2.3f * diff_y + y_offs,
                        kDrawDepth);
          }
          c.Scale(b_width * 0.3f, b_width * 0.3f);
          c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kImage1x1));
        }
      }
    }
  }
  c.Submit();

  bool draw_in_world = have_player_position;

  // Always draw when we've got a world-pos.  if not, only draw on screen in
  // swipe mode.
  if (d_pad_touch_
      && (draw_in_world
          || movement_control_type_ == MovementControlType::kSwipe)) {
    // Circle.
    SimpleComponent c2(draw_in_world ? frame_def->overlay_3d_pass()
                                     : frame_def->GetOverlayFlatPass());
    c2.SetTransparent(true);
    if (buttons_touch_) {
      c2.SetColor(1.0f, 0.3f, 0.2f, 0.45f);
    } else {
      c2.SetColor(1.0f, 1.0f, 0.0f, 0.45f);
    }

    bool zero_len;
    if (std::abs(d_pad_draw_x_) > 0.00001f
        || std::abs(d_pad_draw_y_) > 0.00001f) {
      d_pad_draw_dir_ = Vector3f(d_pad_draw_x_, 0.0f, -d_pad_draw_y_);
      zero_len = false;
    } else {
      zero_len = true;
    }

    // Line.
    float dist = sqrtf(d_pad_draw_dir_.x * d_pad_draw_dir_.x
                       + d_pad_draw_dir_.z * d_pad_draw_dir_.z);
    if (zero_len) {
      dist = 0.05f;
    }

    c2.SetTexture(g_base->assets->SysTexture(SysTextureID::kArrow));
    Matrix44f orient =
        Matrix44fOrient(d_pad_draw_dir_, Vector3f(0.0f, 1.0f, 0.0f));
    {
      auto xf = c2.ScopedTransform();

      // Drawing in the 3d world.
      if (draw_in_world) {
        c2.Translate(player_position[0], player_position[1] - 0.5f,
                     player_position[2]);

        // In happy thoughts mode show the arrow on the xy plane instead of xz.
        if (g_base->graphics->camera()->happy_thoughts_mode()) {
          c2.Translate(0.0f, 0.5f, 0.0f);
          c2.Rotate(90.0f, 1.0f, 0.0f, 0.0f);
        }
      } else {
        // Drawing on 2d overlay.
        float s = base_controls_scale_ * controls_scale_move_;
        c2.Translate(d_pad_start_x_ + s * 50.0f, d_pad_start_y_ + s * 50.0f,
                     0.0f);
        c2.ScaleUniform(s * 50.0f);
        c2.Rotate(90.0f, 1.0f, 0.0f, 0.0f);
      }

      c2.MultMatrix(orient.m);
      c2.Rotate(-90.0f, 1.0f, 0.0f, 0.0f);

      c2.ScaleUniform(0.8f);

      {
        auto xf = c2.ScopedTransform();
        c2.Translate(0.0f, dist * -0.5f, 0.0f);
        c2.Scale(0.15f, dist, 0.2f);
        c2.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kArrowBack));
      }

      {
        auto xf = c2.ScopedTransform();
        c2.Translate(0.0f, dist * -1.0f - 0.15f, 0.0f);
        c2.Scale(0.45f, 0.3f, 0.3f);
        c2.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kArrowFront));
      }
    }
    c2.Submit();
  }
}

void TouchInput::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  std::string touch_movement_type = g_base->app_config->Resolve(
      AppConfig::StringID::kTouchMovementControlType);
  if (touch_movement_type == "swipe") {
    movement_control_type_ = TouchInput::MovementControlType::kSwipe;
  } else if (touch_movement_type == "joystick") {
    movement_control_type_ = TouchInput::MovementControlType::kJoystick;
  } else {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "Invalid touch-movement-type: " + touch_movement_type);
    movement_control_type_ = TouchInput::MovementControlType::kSwipe;
  }
  std::string touch_action_type =
      g_base->app_config->Resolve(AppConfig::StringID::kTouchActionControlType);
  if (touch_action_type == "swipe") {
    action_control_type_ = TouchInput::ActionControlType::kSwipe;
  } else if (touch_action_type == "buttons") {
    action_control_type_ = TouchInput::ActionControlType::kButtons;
  } else {
    g_core->logging->Log(LogName::kBaInput, LogLevel::kError,
                         "Invalid touch-action-type: " + touch_action_type);
    action_control_type_ = TouchInput::ActionControlType::kSwipe;
  }

  controls_scale_move_ = g_base->app_config->Resolve(
      AppConfig::FloatID::kTouchControlsScaleMovement);
  controls_scale_actions_ = g_base->app_config->Resolve(
      AppConfig::FloatID::kTouchControlsScaleActions);
  swipe_controls_hidden_ =
      g_base->app_config->Resolve(AppConfig::BoolID::kTouchControlsSwipeHidden);

  // Start with defaults.
  switch (g_base->ui->uiscale()) {
    case UIScale::kSmall:
      buttons_default_frac_x_ = 0.88f;
      buttons_default_frac_y_ = 0.25f;
      d_pad_default_frac_x_ = 0.12f;
      d_pad_default_frac_y_ = 0.25f;
      break;
    case UIScale::kMedium:
      buttons_default_frac_x_ = 0.89f;
      buttons_default_frac_y_ = 0.2f;
      d_pad_default_frac_x_ = 0.11f;
      d_pad_default_frac_y_ = 0.2f;
      break;
    default:
      buttons_default_frac_x_ = 0.9f;
      buttons_default_frac_y_ = 0.3f;
      d_pad_default_frac_x_ = 0.1f;
      d_pad_default_frac_y_ = 0.3f;
      break;
  }

  // Now override with config.
  d_pad_default_frac_x_ =
      g_base->python->GetRawConfigValue("Touch DPad X", d_pad_default_frac_x_);
  d_pad_default_frac_y_ =
      g_base->python->GetRawConfigValue("Touch DPad Y", d_pad_default_frac_y_);
  buttons_default_frac_x_ = g_base->python->GetRawConfigValue(
      "Touch Buttons X", buttons_default_frac_x_);
  buttons_default_frac_y_ = g_base->python->GetRawConfigValue(
      "Touch Buttons Y", buttons_default_frac_y_);
}

auto TouchInput::HandleTouchDown(void* touch, float x, float y) -> bool {
  assert(g_base->InLogicThread());

  float width = g_base->graphics->screen_virtual_width();
  float height = g_base->graphics->screen_virtual_height();

  // If we're in edit mode, see if the touch should become an edit-dpad touch or
  // an edit-button touch.
  if (editing_) {
    float x_diff = x - d_pad_base_x_;
    float y_diff = y - d_pad_base_y_;
    float len = sqrtf(x_diff * x_diff + y_diff * y_diff)
                / (base_controls_scale_ * controls_scale_move_);
    if (len < 40.0f) {
      d_pad_drag_touch_ = touch;
      d_pad_drag_x_offs_ = x_diff;
      d_pad_drag_y_offs_ = y_diff;
      return true;
    }

    x_diff = x - buttons_x_;
    y_diff = y - buttons_y_;
    len = sqrtf(x_diff * x_diff + y_diff * y_diff)
          / (base_controls_scale_ * controls_scale_actions_);
    if (len < 40.0f) {
      buttons_drag_touch_ = touch;
      buttons_drag_x_offs_ = x_diff;
      buttons_drag_y_offs_ = y_diff;
      return true;
    }
    return false;  // We don't claim the event.

  } else {
    // Normal in-game operation:

    // Normal operation is disabled while a UI is up.
    if (g_base->ui->IsMainUIVisible()) {
      return false;
    }

    if (!AttachedToPlayer()) {
      // Ignore touches at the very top (so we don't interfere with the menu).
      if (y < height * 0.8f) {
        RequestPlayer();

        // Joining with the touchscreen can sometimes
        // be accidental if there's a trackpad on the controller.
        // ..so lets issue a warning to that effect if there's already
        // controllers active.. (only if we got a player though).
        if (AttachedToPlayer() && g_base->input->HaveControllerWithPlayer()) {
          g_base->ScreenMessage(
              g_base->assets->GetResourceString("touchScreenJoinWarningText"),
              {1.0f, 1.0f, 0.0f});
        }
      }
    } else {
      // If its on the left side, this is our new dpad touch.
      if (x < width * 0.5f) {
        d_pad_touch_ = touch;
        did_first_move_ = false;
        if (movement_control_type_ == MovementControlType::kSwipe) {
          d_pad_base_x_ = x;
          d_pad_base_y_ = y;
        }
        d_pad_x_ = x;
        d_pad_y_ = y;
        d_pad_start_x_ = x;
        d_pad_start_y_ = y;

        UpdateDPad();
      } else if (y < height * 0.8f) {
        // Its on the right side (and below the menu), handle buttons.
        // Start running if this is a new press.
        if (buttons_touch_ == nullptr) {
          InputCommand(InputType::kRun, 1.0f);
          // in swipe mode we count this as a fly-press
          if (action_control_type_ == ActionControlType::kSwipe) {
            InputCommand(InputType::kFlyPress);
          }
        }
        buttons_touch_ = touch;
        buttons_touch_x_ = buttons_touch_start_x_ = x;
        buttons_touch_y_ = buttons_touch_start_y_ = y;

        UpdateButtons(true);
      }
    }
  }
  return true;
}

auto TouchInput::HandleTouchUp(void* touch, float x, float y) -> bool {
  assert(g_base->InLogicThread());

  // Release dpad drag touch.
  if (touch == d_pad_drag_touch_) {
    d_pad_drag_touch_ = nullptr;

    // Write the current frac to our config.
    g_base->python->SetRawConfigValue("Touch DPad X", d_pad_default_frac_x_);
    g_base->python->SetRawConfigValue("Touch DPad Y", d_pad_default_frac_y_);
  }

  if (touch == buttons_drag_touch_) {
    buttons_drag_touch_ = nullptr;

    // Write the current frac to our config.
    g_base->python->SetRawConfigValue("Touch Buttons X",
                                      buttons_default_frac_x_);
    g_base->python->SetRawConfigValue("Touch Buttons Y",
                                      buttons_default_frac_y_);
  }

  // Release on button touch.
  if (touch == buttons_touch_) {
    InputCommand(InputType::kRun, 0.0f);
    if (action_control_type_ == ActionControlType::kSwipe) {
      InputCommand(InputType::kFlyRelease);
    }
    buttons_touch_x_ = x;
    buttons_touch_y_ = y;
    buttons_touch_ = nullptr;
    UpdateButtons();
  }

  // If it was our dpad touch, stop tracking.
  if (touch == d_pad_touch_) {
    d_pad_x_ = d_pad_base_x_;
    d_pad_y_ = d_pad_base_y_;
    d_pad_touch_ = nullptr;
    UpdateDPad();
  }
  return true;
}

auto TouchInput::HandleTouchMoved(void* touch, float x, float y) -> bool {
  assert(g_base->InLogicThread());
  if (touch == d_pad_drag_touch_) {
    float width = g_base->graphics->screen_virtual_width();
    float height = g_base->graphics->screen_virtual_height();
    float ratio_x =
        std::min(0.45f, std::max(0.0f, (x - d_pad_drag_x_offs_) / width));
    float ratio_y =
        std::min(0.9f, std::max(0.0f, (y - d_pad_drag_y_offs_) / height));
    d_pad_default_frac_x_ = ratio_x;
    d_pad_default_frac_y_ = ratio_y;
  }
  if (touch == buttons_drag_touch_) {
    float width = g_base->graphics->screen_virtual_width();
    float height = g_base->graphics->screen_virtual_height();
    float ratio_x =
        std::min(1.0f, std::max(0.55f, (x - buttons_drag_x_offs_) / width));
    float ratio_y =
        std::min(0.9f, std::max(0.0f, (y - buttons_drag_y_offs_) / height));
    buttons_default_frac_x_ = ratio_x;
    buttons_default_frac_y_ = ratio_y;
  }

  // Ignore button/pad touches while gui is up.
  if (g_base->ui->IsMainUIVisible()) {
    return false;
  }
  if (touch == buttons_touch_) {
    buttons_touch_x_ = x;
    buttons_touch_y_ = y;
    UpdateButtons();
  }

  // If it was our dpad touch, update tracking.
  if (touch == d_pad_touch_) {
    d_pad_x_ = x;
    d_pad_y_ = y;
    UpdateDPad();
  }
  return true;
}

auto TouchInput::DoGetDeviceName() -> std::string { return "TouchScreen"; }

}  // namespace ballistica::base
