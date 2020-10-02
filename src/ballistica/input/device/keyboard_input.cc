// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/input/device/keyboard_input.h"

#include "ballistica/game/player.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/ui/ui.h"
#include "ballistica/ui/widget/container_widget.h"

namespace ballistica {

KeyboardInput::KeyboardInput(KeyboardInput* parentKeyboardInputIn) {
  if (parentKeyboardInputIn) {
    parent_keyboard_input_ = parentKeyboardInputIn;
    assert(parent_keyboard_input_->child_keyboard_input_ == nullptr);

    // Currently we assume only 2 keyboard inputs.
    assert(parent_keyboard_input_->parent_keyboard_input_ == nullptr);
    parent_keyboard_input_->child_keyboard_input_ = this;
    up_key_ = SDLK_w;
    down_key_ = SDLK_s;
    left_key_ = SDLK_a;
    right_key_ = SDLK_d;
    jump_key_ = SDLK_1;
    punch_key_ = SDLK_2;
    bomb_key_ = SDLK_3;
    pick_up_key_ = SDLK_4;
    hold_position_key_ = SDLK_6;
    start_key_ = SDLK_KP_7;
  } else {
    up_key_ = SDLK_UP;
    down_key_ = SDLK_DOWN;
    left_key_ = SDLK_LEFT;
    right_key_ = SDLK_RIGHT;
    jump_key_ = SDLK_SPACE;
    punch_key_ = SDLK_v;
    bomb_key_ = SDLK_b;
    pick_up_key_ = SDLK_c;
    hold_position_key_ = SDLK_y;
    start_key_ = SDLK_F5;
  }
}

KeyboardInput::~KeyboardInput() = default;

auto KeyboardInput::HandleKey(const SDL_Keysym* keysym, bool repeat, bool down)
    -> bool {
  // Only allow the *main* keyboard to talk to the UI
  if (parent_keyboard_input_ == nullptr) {
    if (g_ui->GetWidgetForInput(this)) {
      bool pass = false;
      WidgetMessage::Type c = WidgetMessage::Type::kEmptyMessage;
      if (down) {
        switch (keysym->sym) {
          case SDLK_TAB:
            if (keysym->mod & KMOD_SHIFT) {  // NOLINT (signed bitwise)
              c = WidgetMessage::Type::kTabPrev;
            } else {
              c = WidgetMessage::Type::kTabNext;
            }
            pass = true;
            break;
          case SDLK_LEFT:
            c = WidgetMessage::Type::kMoveLeft;
            pass = true;
            break;
          case SDLK_RIGHT:
            c = WidgetMessage::Type::kMoveRight;
            pass = true;
            break;
          case SDLK_UP:
            c = WidgetMessage::Type::kMoveUp;
            pass = true;
            break;
          case SDLK_DOWN:
            c = WidgetMessage::Type::kMoveDown;
            pass = true;
            break;
          case SDLK_SPACE:
          case SDLK_KP_ENTER:
          case SDLK_RETURN:
            if (!repeat) {
              c = WidgetMessage::Type::kActivate;
              pass = true;
            }
            break;
          case SDLK_ESCAPE:
            // (limit to kb1 so we don't get double-beeps on failure)
            c = WidgetMessage::Type::kCancel;
            pass = true;
            break;
          default:

            // for remaining keys, lets see if they map to our assigned
            // movement/actions.  If so, we handle them.
            if (keysym->sym == start_key_ || keysym->sym == jump_key_
                || keysym->sym == punch_key_ || keysym->sym == pick_up_key_) {
              c = WidgetMessage::Type::kActivate;
              pass = true;
            } else if (keysym->sym == bomb_key_) {
              c = WidgetMessage::Type::kCancel;
              pass = true;
            } else if (keysym->sym == left_key_) {
              c = WidgetMessage::Type::kMoveLeft;
              pass = true;
            } else if (keysym->sym == right_key_) {
              c = WidgetMessage::Type::kMoveRight;
              pass = true;
            } else if (keysym->sym == up_key_) {
              c = WidgetMessage::Type::kMoveUp;
              pass = true;
            } else if (keysym->sym == down_key_) {
              c = WidgetMessage::Type::kMoveDown;
              pass = true;
            }

            // if we're keyboard 1 we always send at least a key press event
            // along..
            if (!parent_keyboard_input_ && !pass) {
              c = WidgetMessage::Type::kKey;
              pass = true;
            }
            break;
        }
      }
      if (pass) {
        g_ui->SendWidgetMessage(WidgetMessage(c, keysym));
      }
      return (pass);
    }
  }

  // Bring up menu if start is pressed.
  if (keysym->sym == start_key_ && !repeat && g_ui && g_ui->screen_root_widget()
      && g_ui->screen_root_widget()->GetChildCount() == 0) {
    g_game->PushMainMenuPressCall(this);
    return true;
  }

  // At this point, if we have a child input, let it try to handle things.
  if (child_keyboard_input_ && enable_child_) {
    if (child_keyboard_input_->HandleKey(keysym, repeat, down)) {
      return true;
    }
  }

  if (!attached_to_player()) {
    if (down
        && ((keysym->sym == jump_key_) || (keysym->sym == punch_key_)
            || (keysym->sym == bomb_key_)
            || (keysym->sym == pick_up_key_)
            // Main keyboard accepts enter/return as join-request.
            || (device_number() == 1 && (keysym->sym == SDLK_KP_ENTER))
            || (device_number() == 1 && (keysym->sym == SDLK_RETURN)))) {
      RequestPlayer();
      return true;
    }
    return false;
  }
  InputType input_type{};
  bool have_input_2{};
  InputType input_type_2{};
  int16_t input_value{};
  int16_t input_value_2{};
  bool player_input{};

  // Hack to prevent unused-value lint bug.
  // (removing init values from input_type and input_type_2 gives a
  // 'possibly uninited value used' warning but leaving them gives a
  // 'values unused' warning. Grumble.)
  explicit_bool(input_type
                == (explicit_bool(false) ? input_type_2 : InputType::kLast));

  if (!repeat) {
    // Keyboard 1 supports assigned keys plus arrow keys if they're unused.
    if (keysym->sym == left_key_
        || (device_number() == 1 && keysym->sym == SDLK_LEFT
            && !left_key_assigned())) {
      player_input = true;
      input_type = InputType::kLeftRight;
      left_held_ = down;
      if (down) {
        if (right_held_) {
          input_value = 0;
        } else {
          input_value = -32767;
        }
      } else {
        if (right_held_) {
          input_value = 32767;
        }
      }
    } else if (keysym->sym == right_key_
               || (device_number() == 1 && keysym->sym == SDLK_RIGHT
                   && !right_key_assigned())) {
      // Keyboard 1 supports assigned keys plus arrow keys if they're unused.
      player_input = true;
      input_type = InputType::kLeftRight;
      right_held_ = down;
      if (down) {
        if (left_held_) {
          input_value = 0;
        } else {
          input_value = 32767;
        }
      } else {
        if (left_held_) {
          input_value = -32767;
        }
      }
    } else if (keysym->sym == up_key_
               || (device_number() == 1 && keysym->sym == SDLK_UP
                   && !up_key_assigned())) {
      player_input = true;
      input_type = InputType::kUpDown;
      up_held_ = down;
      if (down) {
        if (down_held_) {
          input_value = 0;
        } else {
          input_value = 32767;
        }
      } else {
        if (down_held_) input_value = -32767;
      }
    } else if (keysym->sym == down_key_
               || (device_number() == 1 && keysym->sym == SDLK_DOWN
                   && !down_key_assigned())) {
      player_input = true;
      input_type = InputType::kUpDown;
      down_held_ = down;
      if (down) {
        if (up_held_) {
          input_value = 0;
        } else {
          input_value = -32767;
        }
      } else {
        if (up_held_) input_value = 32767;
      }
    } else if (keysym->sym == punch_key_) {
      player_input = true;
      UpdateRun(keysym->sym, down);
      if (down) {
        input_type = InputType::kPunchPress;
      } else {
        input_type = InputType::kPunchRelease;
      }
    } else if (keysym->sym == bomb_key_) {
      player_input = true;
      UpdateRun(keysym->sym, down);
      if (down)
        input_type = InputType::kBombPress;
      else
        input_type = InputType::kBombRelease;
    } else if (keysym->sym == hold_position_key_) {
      player_input = true;
      if (down) {
        input_type = InputType::kHoldPositionPress;
      } else {
        input_type = InputType::kHoldPositionRelease;
      }
    } else if (keysym->sym == pick_up_key_) {
      player_input = true;
      UpdateRun(keysym->sym, down);
      if (down) {
        input_type = InputType::kPickUpPress;
      } else {
        input_type = InputType::kPickUpRelease;
      }
    } else if ((device_number() == 1 && keysym->sym == SDLK_RETURN)
               || (device_number() == 1 && keysym->sym == SDLK_KP_ENTER)
               || keysym->sym == jump_key_) {
      // Keyboard 1 claims certain keys if they are otherwise unclaimed
      // (arrow keys, enter/return, etc).
      player_input = true;
      UpdateRun(keysym->sym, down);
      if (down) {
        input_type = InputType::kJumpPress;
        have_input_2 = true;
        input_type_2 = InputType::kFlyPress;
      } else {
        input_type = InputType::kJumpRelease;
        have_input_2 = true;
        input_type_2 = InputType::kFlyRelease;
      }
    } else {
      // Any other keys get processed as run keys.
      // keypad keys go to player 2 - anything else to player 1.
      switch (keysym->sym) {
        case SDLK_KP_0:
        case SDLK_KP_1:
        case SDLK_KP_2:
        case SDLK_KP_3:
        case SDLK_KP_4:
        case SDLK_KP_5:
        case SDLK_KP_6:
        case SDLK_KP_7:
        case SDLK_KP_8:
        case SDLK_KP_9:
        case SDLK_KP_PLUS:
        case SDLK_KP_MINUS:
        case SDLK_KP_ENTER:
          if (device_number() == 2) {
            UpdateRun(keysym->sym, down);
            return true;
          }
          break;
        default:
          if (device_number() == 1) {
            UpdateRun(keysym->sym, down);
            return true;
          }
          break;
      }
    }
  }

  if (player_input) {
    InputCommand(input_type, static_cast<float>(input_value) / 32767.0f);
    if (have_input_2) {
      InputCommand(input_type_2, static_cast<float>(input_value_2) / 32767.0f);
    }
    return true;
  } else {
    return false;
  }
}

void KeyboardInput::ResetHeldStates() {
  down_held_ = up_held_ = left_held_ = right_held_ = false;
  bool was_held = false;
  if (!keys_held_.empty()) {
    was_held = true;
  }
  keys_held_.clear();
  if (was_held) {
    InputCommand(InputType::kRun, 0.0f);
  }
}

void KeyboardInput::UpdateRun(SDL_Keycode key, bool down) {
  bool was_held = (!keys_held_.empty());
  if (down) {
    keys_held_.insert(key);
    if (!was_held) {
      InputCommand(InputType::kRun, 1.0f);
    }
  } else {
    // Remove this key if we find it.
    auto iter = keys_held_.find(key);
    if (iter != keys_held_.end()) {
      keys_held_.erase(iter);
    }
    bool is_held = (!keys_held_.empty());
    if (was_held && !is_held) {
      InputCommand(InputType::kRun, 0.0f);
    }
  }
}

void KeyboardInput::UpdateMapping() {
  assert(InGameThread());

  SDL_Keycode up_key_default, down_key_default, left_key_default,
      right_key_default, jump_key_default, punch_key_default, bomb_key_default,
      pick_up_key_default, hold_position_key_default, start_key_default;

  if (parent_keyboard_input_) {
    up_key_default = SDLK_UP;
    down_key_default = SDLK_DOWN;
    left_key_default = SDLK_LEFT;
    right_key_default = SDLK_RIGHT;

    jump_key_default = SDLK_KP_2;
    punch_key_default = SDLK_KP_1;
    bomb_key_default = SDLK_KP_6;
    pick_up_key_default = SDLK_KP_5;
    hold_position_key_default = (SDL_Keycode)-1;
    start_key_default = SDLK_KP_7;

  } else {
    up_key_default = SDLK_w;
    down_key_default = SDLK_s;
    left_key_default = SDLK_a;
    right_key_default = SDLK_d;
    jump_key_default = SDLK_k;
    punch_key_default = SDLK_j;
    bomb_key_default = SDLK_o;
    pick_up_key_default = SDLK_i;

    hold_position_key_default = (SDL_Keycode)-1;
    start_key_default = (SDL_Keycode)-1;
  }

  // We keep track of whether anyone is using arrow keys
  // If not, we allow them to function for movement.
  left_key_assigned_ = right_key_assigned_ = up_key_assigned_ =
      down_key_assigned_ = false;

  int val;

  val = g_python->GetControllerValue(this, "buttonJump");
  jump_key_ = (val == -1) ? jump_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(jump_key_);

  val = g_python->GetControllerValue(this, "buttonPunch");
  punch_key_ = (val == -1) ? punch_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(punch_key_);

  val = g_python->GetControllerValue(this, "buttonBomb");
  bomb_key_ = (val == -1) ? bomb_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(bomb_key_);

  val = g_python->GetControllerValue(this, "buttonPickUp");
  pick_up_key_ = (val == -1) ? pick_up_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(pick_up_key_);

  val = g_python->GetControllerValue(this, "buttonHoldPosition");
  hold_position_key_ =
      (val == -1) ? hold_position_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(hold_position_key_);

  val = g_python->GetControllerValue(this, "buttonStart");
  start_key_ = (val == -1) ? start_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(start_key_);

  val = g_python->GetControllerValue(this, "buttonUp");
  up_key_ = (val == -1) ? up_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(up_key_);

  val = g_python->GetControllerValue(this, "buttonDown");
  down_key_ = (val == -1) ? down_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(down_key_);

  val = g_python->GetControllerValue(this, "buttonLeft");
  left_key_ = (val == -1) ? left_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(left_key_);

  val = g_python->GetControllerValue(this, "buttonRight");
  right_key_ = (val == -1) ? right_key_default : (SDL_Keycode)val;
  UpdateArrowKeys(right_key_);

  enable_child_ = true;

  up_held_ = down_held_ = left_held_ = right_held_ = false;
}

void KeyboardInput::UpdateArrowKeys(SDL_Keycode key) {
  if (key == SDLK_UP) {
    up_key_assigned_ = true;
  } else if (key == SDLK_DOWN) {
    down_key_assigned_ = true;
  } else if (key == SDLK_LEFT) {
    left_key_assigned_ = true;
  } else if (key == SDLK_RIGHT) {
    right_key_assigned_ = true;
  }
}

auto KeyboardInput::GetButtonName(int index) -> std::string {
  return g_platform->GetKeyName(index);
  // return InputDevice::GetButtonName(index);
}

auto KeyboardInput::GetRawDeviceName() -> std::string { return "Keyboard"; }
auto KeyboardInput::GetPartyButtonName() const -> std::string { return "F5"; }
auto KeyboardInput::HasMeaningfulButtonNames() -> bool { return true; }

}  // namespace ballistica
