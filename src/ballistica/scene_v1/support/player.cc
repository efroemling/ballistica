// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/player.h"

#include <algorithm>
#include <string>
#include <vector>

#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/python/support/python_context_call.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/python/class/python_class_session_player.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::scene_v1 {

Player::Player(int id_in, HostSession* host_session)
    : id_(id_in),
      creation_time_(g_core->AppTimeMillisecs()),
      host_session_(host_session) {
  assert(host_session);
  assert(g_base->InLogicThread());
}

Player::~Player() {
  assert(g_base->InLogicThread());

  // If we have an input-device driving us, detach it.
  if (auto* delegate = input_device_delegate_.get()) {
    delegate->DetachFromPlayer();
  }

  // Release our ref to ourself if we have one.
  if (py_ref_) {
    Py_DECREF(py_ref_);
  }
}

auto Player::GetAge() const -> millisecs_t {
  return g_core->AppTimeMillisecs() - creation_time_;
}

auto Player::GetName(bool full, bool icon) const -> std::string {
  std::string n = full ? full_name_ : name_;

  // Quasi-hacky: if they ask for no icon, strip the first char off our string
  // if its in the custom-use-range.
  if (!icon) {
    std::vector<uint32_t> uni = Utils::UnicodeFromUTF8(n, "3f94f4f");
    if (!uni.empty() && uni[0] >= 0xE000 && uni[0] <= 0xF8FF) {
      uni.erase(uni.begin());
    }
    return Utils::UTF8FromUnicode(uni);
  } else {
    return n;
  }
}

auto Player::GetHostActivity() const -> HostActivity* {
  return host_activity_.get();
}

void Player::SetHostActivity(HostActivity* a) {
  assert(g_base->InLogicThread());

  // Make sure we get pulled out of one activity before being added to
  // another.
  if (a && in_activity_) {
    std::string old_name =
        host_activity_.exists()
            ? PythonRef::StolenSoft(host_activity_->GetPyActivity()).Str()
            : "<nullptr>";

    // GetPyActivity returns a new ref or nullptr.
    auto py_activity{PythonRef::StolenSoft(a->GetPyActivity())};

    BA_LOG_PYTHON_TRACE_ONCE(
        "Player::SetHostActivity() called when already in an activity (old="
        + old_name + ", new=" + py_activity.Str() + ")");
  } else if (!a && !in_activity_) {
    BA_LOG_PYTHON_TRACE_ONCE(
        "Player::SetHostActivity() called with nullptr when not in an "
        "activity");
  }
  host_activity_ = a;
  in_activity_ = (a != nullptr);
}

void Player::ClearHostSessionForTearDown() { host_session_.Clear(); }

void Player::SetPosition(const Vector3f& position) {
  position_ = position;
  have_position_ = true;
}

void Player::ResetInput() {
  // Hold a ref to ourself while clearing this to make sure
  // we don't die midway as a result of freeing something.
  Object::Ref<Object> ref(this);
  calls_.clear();
  left_held_ = right_held_ = up_held_ = down_held_ = have_position_ = false;
}

void Player::SetPyTeam(PyObject* team) {
  if (team != nullptr && team != Py_None) {
    // We store a weak-ref to this.
    py_team_weak_ref_.Steal(PyWeakref_NewRef(team, nullptr));
  } else {
    py_team_weak_ref_.Release();
  }
}

auto Player::GetPyTeam() -> PyObject* {
  auto* ref_obj{py_team_weak_ref_.get()};
  if (!ref_obj) {
    return nullptr;
  }
  PyObject* obj{};
  int result = PyWeakref_GetRef(ref_obj, &obj);
  // Return new obj ref (result 1) or nullptr for dead objs (result 0).
  if (result == 0 || result == 1) {
    return obj;
  }
  // Something went wrong and an exception is set. We don't expect this to
  // ever happen so currently just providing a simple error msg.
  assert(result == -1);
  PyErr_Clear();
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       "Player::GetPyTeam(): error getting weakref obj.");
  return nullptr;
}

void Player::SetPyCharacter(PyObject* character) {
  if (character != nullptr && character != Py_None) {
    py_character_.Acquire(character);
  } else {
    py_character_.Release();
  }
}

auto Player::GetPyCharacter() -> PyObject* {
  return py_character_.exists() ? py_character_.get() : Py_None;
}

void Player::SetPyColor(PyObject* c) { py_color_.Acquire(c); }
auto Player::GetPyColor() -> PyObject* {
  return py_color_.exists() ? py_color_.get() : Py_None;
}

void Player::SetPyHighlight(PyObject* c) { py_highlight_.Acquire(c); }
auto Player::GetPyHighlight() -> PyObject* {
  return py_highlight_.exists() ? py_highlight_.get() : Py_None;
}

void Player::SetPyActivityPlayer(PyObject* c) { py_activityplayer_.Acquire(c); }
auto Player::GetPyActivityPlayer() -> PyObject* {
  return py_activityplayer_.exists() ? py_activityplayer_.get() : Py_None;
}

auto Player::GetPyRef(bool new_ref) -> PyObject* {
  assert(g_base->InLogicThread());
  if (py_ref_ == nullptr) {
    py_ref_ = PythonClassSessionPlayer::Create(this);
  }
  if (new_ref) {
    Py_INCREF(py_ref_);
  }
  return py_ref_;
}

void Player::AssignInputCall(InputType type, PyObject* call_obj) {
  assert(g_base->InLogicThread());
  assert(static_cast<int>(type) >= 0
         && static_cast<int>(type) < static_cast<int>(InputType::kLast));

  // Special case: if they're assigning hold-position-press or
  // hold-position-release, or any direction events, we add in a hold-position
  // press/release event before we deliver any other events.. that way newly
  // created stuff is informed of the hold state and doesn't wrongly think they
  // should start moving.
  switch (type) {
    case InputType::kHoldPositionPress:
    case InputType::kHoldPositionRelease:
    case InputType::kLeftPress:
    case InputType::kLeftRelease:
    case InputType::kRightPress:
    case InputType::kUpPress:
    case InputType::kUpRelease:
    case InputType::kDownPress:
    case InputType::kDownRelease:
    case InputType::kUpDown:
    case InputType::kLeftRight: {
      send_hold_state_ = true;
      break;
    }
    default:
      break;
  }
  if (call_obj) {
    calls_[static_cast<int>(type)] =
        Object::New<base::PythonContextCall>(call_obj);
  } else {
    calls_[static_cast<int>(type)].Clear();
  }

  // If they assigned l/r, immediately send an update for its current value.
  if (type == InputType::kLeftRight) {
    RunInput(type, lr_state_);
  }

  // Same for up/down.
  if (type == InputType::kUpDown) {
    RunInput(type, ud_state_);
  }

  // Same for run.
  if (type == InputType::kRun) {
    RunInput(type, run_state_);
  }

  // Same for fly.
  if (type == InputType::kFlyPress && fly_held_) {
    RunInput(type);
  }
}

void Player::RunInput(InputType type, float value) {
  assert(g_base->InLogicThread());

  const float threshold = base::kJoystickDiscreteThresholdFloat;

  // Most input commands cause us to reset the player's time-out
  // there are a few exceptions though - very small analog values
  // get ignored since they can come through without user intervention.
  bool reset_time_out = true;
  if (type == InputType::kLeftRight || type == InputType::kUpDown) {
    if (std::abs(value) < 0.3f) {
      reset_time_out = false;
    }
  }
  if (type == InputType::kRun) {
    if (value < 0.3f) {
      reset_time_out = false;
    }
  }

  // Also ignore hold-position stuff since it can come through without user
  // interaction.
  if ((type == InputType::kHoldPositionPress)
      || (type == InputType::kHoldPositionRelease))
    reset_time_out = false;

  if (reset_time_out) {
    time_out_ = BA_PLAYER_TIME_OUT;
  }

  // Keep track of the hold-position state that comes through here.
  // any-time hold position buttons are re-assigned, we subsequently
  // re-send the current hold-state so whatever its driving starts out correctly
  // held if need be.
  if (type == InputType::kHoldPositionPress) {
    hold_position_ = true;
  } else if (type == InputType::kHoldPositionRelease) {
    hold_position_ = false;
  } else if (type == InputType::kFlyPress) {
    fly_held_ = true;
  } else if (type == InputType::kFlyRelease) {
    fly_held_ = false;
  }

  // If we were supposed to deliver hold-state, go ahead and do that first.
  if (send_hold_state_) {
    send_hold_state_ = false;
    if (hold_position_) {
      RunInput(InputType::kHoldPositionPress);
    } else {
      RunInput(InputType::kHoldPositionRelease);
    }
  }

  // Let's make our life simpler by converting held-position-joystick-events..
  {
    // We need to store these since we might look at them during a hold-position
    // event when we don't have their originating events available.
    if (type == InputType::kLeftRight) {
      lr_state_ = value;
    }
    if (type == InputType::kUpDown) {
      ud_state_ = value;
    }
    if (type == InputType::kRun) {
      run_state_ = value;
    }

    // Special input commands - keep track of left/right and up/down positions
    // so we can deliver simple "leftUp", "leftDown", etc type of events
    // in addition to the standard absolute leftRight positions, etc.
    if (type == InputType::kLeftRight || type == InputType::kHoldPositionPress
        || type == InputType::kHoldPositionRelease) {
      float arg = lr_state_;
      if (hold_position_) {
        arg = 0.0f;  // Throttle is off.
      }
      if (left_held_) {
        if (arg > -threshold) {
          left_held_ = false;
          RunInput(InputType::kLeftRelease);
        }
      } else if (right_held_) {
        if (arg < threshold) {
          right_held_ = false;
          RunInput(InputType::kRightRelease);
        }
      } else {
        if (arg >= threshold) {
          if (!up_held_ && !down_held_) {
            right_held_ = true;
            RunInput(InputType::kRightPress);
          }
        } else if (arg <= -threshold) {
          if (!up_held_ && !down_held_) {
            left_held_ = true;
            RunInput(InputType::kLeftPress);
          }
        }
      }
    }
    if (type == InputType::kUpDown || type == InputType::kHoldPositionPress
        || type == InputType::kHoldPositionRelease) {
      float arg = ud_state_;
      if (hold_position_) arg = 0.0f;  // throttle is off;
      if (up_held_) {
        if (arg < threshold) {
          up_held_ = false;
          RunInput(InputType::kUpRelease);
        }
      } else if (down_held_) {
        if (arg > -threshold) {
          down_held_ = false;
          RunInput(InputType::kDownRelease);
        }
      } else {
        if (arg <= -threshold) {
          if (!left_held_ && !right_held_) {
            down_held_ = true;
            RunInput(InputType::kDownPress);
          }
        } else if (arg >= threshold) {
          if (!left_held_ && !right_held_) {
            up_held_ = true;
            RunInput(InputType::kUpPress);
          }
        }
      }
    }
  }

  auto j = calls_.find(static_cast<int>(type));
  if (j != calls_.end() && j->second.exists()) {
    if (type == InputType::kRun) {
      PythonRef args(
          Py_BuildValue("(f)", std::min(1.0f, std::max(0.0f, value))),
          PythonRef::kSteal);
      j->second->Run(args.get());
    } else if (type == InputType::kLeftRight || type == InputType::kUpDown) {
      PythonRef args(
          Py_BuildValue("(f)", std::min(1.0f, std::max(-1.0f, value))),
          PythonRef::kSteal);
      j->second->Run(args.get());
    } else {
      j->second->Run();
    }
  }
}

auto Player::GetHostSession() const -> HostSession* {
  return host_session_.get();
}

void Player::SetName(const std::string& name, const std::string& full_name,
                     bool is_real) {
  assert(g_base->InLogicThread());
  HostSession* host_session = GetHostSession();
  BA_PRECONDITION(host_session);
  name_is_real_ = is_real;
  name_ = host_session->GetUnusedPlayerName(this, name);
  full_name_ = full_name;

  // If we're already in the game and our name is changing, we need to update
  // the roster.
  if (accepted_) {
    if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
      appmode->UpdateGameRoster();
    }
  }
}

void Player::InputCommand(InputType type, float value) {
  assert(g_base->InLogicThread());
  switch (type) {
    case InputType::kUpDown:
    case InputType::kLeftRight:
    case InputType::kRun:
      RunInput(type, value);
      break;
    // case InputType::kReset:
    //   Log(LogLevel::kError, "FIXME: player-input-reset command
    //   unimplemented"); break;
    default:
      RunInput(type);
      break;
  }
}

void Player::set_input_device_delegate(
    SceneV1InputDeviceDelegate* input_device) {
  input_device_delegate_ = input_device;
}

auto Player::GetPublicV1AccountID() const -> std::string {
  assert(g_base->InLogicThread());
  if (input_device_delegate_.exists()) {
    return input_device_delegate_->GetPublicV1AccountID();
  }
  return "";
}

void Player::SetIcon(const std::string& tex_name,
                     const std::string& tint_tex_name,
                     const std::vector<float>& tint_color,
                     const std::vector<float>& tint2_color) {
  assert(tint_color.size() == 3);
  assert(tint2_color.size() == 3);
  icon_tex_name_ = tex_name;
  icon_tint_tex_name_ = tint_tex_name;
  icon_tint_color_ = tint_color;
  icon_tint2_color_ = tint2_color;
  icon_set_ = true;
}

}  // namespace ballistica::scene_v1
