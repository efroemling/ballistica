// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/input/device/keyboard_input.h"

#include <string>

#include "ballistica/base/app_adapter/app_adapter.h"
#include "ballistica/base/support/classic_soft.h"
#include "ballistica/base/support/repeater.h"
#include "ballistica/base/ui/ui.h"

namespace ballistica::base {

KeyboardInput::KeyboardInput(KeyboardInput* parent_keyboard_input_in) {
  if (parent_keyboard_input_in) {
    parent_keyboard_input_ = parent_keyboard_input_in;
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

auto KeyboardInput::HandleKey(const SDL_Keysym* keysym, bool down) -> bool {
  // Only allow the *main* keyboard to talk to the UI
  if (parent_keyboard_input_ == nullptr) {
    // Any new event coming in cancels repeats.
    ui_repeater_.Clear();

    if (g_base->ui->RequestMainUIControl(this)) {
      bool pass = false;
      auto c = WidgetMessage::Type::kEmptyMessage;
      if (down) {
        switch (keysym->sym) {
          case SDLK_TAB:
            // if (keysym->mod & KMOD_SHIFT) {  // NOLINT (signed bitwise)
            //   c = WidgetMessage::Type::kTabPrev;
            // } else {
            //   c = WidgetMessage::Type::kTabNext;
            // }
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
            c = WidgetMessage::Type::kActivate;
            pass = true;
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
        // For movement and key press widget events, set up repeats.
        // Otherwise run a single time immediately.
        switch (c) {
          case WidgetMessage::Type::kMoveUp:
          case WidgetMessage::Type::kMoveDown:
          case WidgetMessage::Type::kMoveLeft:
          case WidgetMessage::Type::kMoveRight:
          case WidgetMessage::Type::kKey:
            // Note: Need to pass keysym along as a value; not a pointer.
            ui_repeater_ = Repeater::New(
                g_base->app_adapter->GetKeyRepeatDelay(),
                g_base->app_adapter->GetKeyRepeatInterval(),
                [c, keysym = *keysym] {
                  g_base->ui->SendWidgetMessage(WidgetMessage(c, &keysym));
                });
            break;
          default:
            g_base->ui->SendWidgetMessage(WidgetMessage(c, keysym));
            break;
        }
      }
      return (pass);
    }
  }

  // Bring up menu if start is pressed.
  if (keysym->sym == start_key_ && !g_base->ui->IsMainUIVisible()) {
    g_base->ui->RequestMainUI(this);
    return true;
  }

  // At this point, if we have a child input, let it try to handle things.
  if (child_keyboard_input_ && enable_child_) {
    if (child_keyboard_input_->HandleKey(keysym, down)) {
      return true;
    }
  }

  if (!AttachedToPlayer()) {
    if (down
        && ((keysym->sym == jump_key_) || (keysym->sym == punch_key_)
            || (keysym->sym == bomb_key_)
            || (keysym->sym == pick_up_key_)
            // Main keyboard accepts enter/return as join-request.
            || (number() == 1 && (keysym->sym == SDLK_KP_ENTER))
            || (number() == 1 && (keysym->sym == SDLK_RETURN)))) {
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
  //  explicit_bool(input_type
  //                == (explicit_bool(false) ? input_type_2 :
  //                InputType::kLast));

  // Keyboard 1 supports assigned keys plus arrow keys if they're unused.
  if (keysym->sym == left_key_
      || (number() == 1 && keysym->sym == SDLK_LEFT && !left_key_assigned())) {
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
             || (number() == 1 && keysym->sym == SDLK_RIGHT
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
             || (number() == 1 && keysym->sym == SDLK_UP
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
             || (number() == 1 && keysym->sym == SDLK_DOWN
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
    UpdateRun_(keysym->sym, down);
    if (down) {
      input_type = InputType::kPunchPress;
    } else {
      input_type = InputType::kPunchRelease;
    }
  } else if (keysym->sym == bomb_key_) {
    player_input = true;
    UpdateRun_(keysym->sym, down);
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
    UpdateRun_(keysym->sym, down);
    if (down) {
      input_type = InputType::kPickUpPress;
    } else {
      input_type = InputType::kPickUpRelease;
    }
  } else if ((number() == 1 && keysym->sym == SDLK_RETURN)
             || (number() == 1 && keysym->sym == SDLK_KP_ENTER)
             || keysym->sym == jump_key_) {
    // Keyboard 1 claims certain keys if they are otherwise unclaimed
    // (arrow keys, enter/return, etc).
    player_input = true;
    UpdateRun_(keysym->sym, down);
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
        if (number() == 2) {
          UpdateRun_(keysym->sym, down);
          return true;
        }
        break;
      default:
        if (number() == 1) {
          UpdateRun_(keysym->sym, down);
          return true;
        }
        break;
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

void KeyboardInput::UpdateRun_(SDL_Keycode key, bool down) {
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

void KeyboardInput::ApplyAppConfig() {
  assert(g_base->InLogicThread());

  auto* cl{g_base->HaveClassic() ? g_base->classic() : nullptr};

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

  int val = cl ? cl->GetControllerValue(this, "buttonJump") : -1;
  jump_key_ = (val == -1) ? jump_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(jump_key_);

  val = cl ? cl->GetControllerValue(this, "buttonPunch") : -1;
  punch_key_ = (val == -1) ? punch_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(punch_key_);

  val = cl ? cl->GetControllerValue(this, "buttonBomb") : -1;
  bomb_key_ = (val == -1) ? bomb_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(bomb_key_);

  val = cl ? cl->GetControllerValue(this, "buttonPickUp") : -1;
  pick_up_key_ = (val == -1) ? pick_up_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(pick_up_key_);

  val = cl ? cl->GetControllerValue(this, "buttonHoldPosition") : -1;
  hold_position_key_ =
      (val == -1) ? hold_position_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(hold_position_key_);

  val = cl ? cl->GetControllerValue(this, "buttonStart") : -1;
  start_key_ = (val == -1) ? start_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(start_key_);

  val = cl ? cl->GetControllerValue(this, "buttonUp") : -1;
  up_key_ = (val == -1) ? up_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(up_key_);

  val = cl ? cl->GetControllerValue(this, "buttonDown") : -1;
  down_key_ = (val == -1) ? down_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(down_key_);

  val = cl ? cl->GetControllerValue(this, "buttonLeft") : -1;
  left_key_ = (val == -1) ? left_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(left_key_);

  val = cl ? cl->GetControllerValue(this, "buttonRight") : -1;
  right_key_ = (val == -1) ? right_key_default : (SDL_Keycode)val;
  UpdateArrowKeys_(right_key_);

  enable_child_ = true;

  up_held_ = down_held_ = left_held_ = right_held_ = false;
}

void KeyboardInput::UpdateArrowKeys_(SDL_Keycode key) {
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
  return g_base->app_adapter->GetKeyName(index);
}

auto KeyboardInput::DoGetDeviceName() -> std::string { return "Keyboard"; }
auto KeyboardInput::GetPartyButtonName() const -> std::string { return "F5"; }
auto KeyboardInput::HasMeaningfulButtonNames() -> bool { return true; }

}  // namespace ballistica::base
