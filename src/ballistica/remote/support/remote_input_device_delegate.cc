// Released under the MIT License. See LICENSE for details.

#include "ballistica/remote/support/remote_input_device_delegate.h"

#include <algorithm>
#include <cmath>
#include <string>

#include "ballistica/base/base.h"
#include "ballistica/base/input/support/remote_app_server.h"
#include "ballistica/remote/support/remote_app_mode.h"

namespace ballistica::remote {

// Shared across all our delegates so the most recently moved stick can
// be found.
static uint64_t g_next_axis_serial{1};

// Map a -1..1 axis value to the remote protocol's 0-255 byte (the game
// maps it back as -1 + 2 * byte / 255).
static auto AxisToByte(float value) -> uint8_t {
  float clamped = std::clamp(value, -1.0f, 1.0f);
  return static_cast<uint8_t>(std::lround((clamped + 1.0f) * 127.5f));
}

RemoteInputDeviceDelegate::RemoteInputDeviceDelegate() = default;

RemoteInputDeviceDelegate::~RemoteInputDeviceDelegate() = default;

auto RemoteInputDeviceDelegate::AttachedToPlayer() const -> bool {
  auto* mode = RemoteAppMode::GetActive();
  return mode != nullptr && mode->connected();
}

auto RemoteInputDeviceDelegate::DescribeAttachedTo() const -> std::string {
  return AttachedToPlayer() ? "remote-game" : "nothing";
}

auto RemoteInputDeviceDelegate::axis_h() const -> uint8_t {
  return AxisToByte(left_right_);
}

auto RemoteInputDeviceDelegate::axis_v() const -> uint8_t {
  // The game flips the vertical axis on the way in (0 = up), as it does
  // for a physical joystick.
  return AxisToByte(-up_down_);
}

void RemoteInputDeviceDelegate::SetButton_(uint32_t bit, bool held) {
  uint32_t buttons = held ? (buttons_ | bit) : (buttons_ & ~bit);
  buttons_ = static_cast<uint8_t>(buttons & 0xFFu);
}

void RemoteInputDeviceDelegate::InputCommand(InputType type, float value) {
  assert(g_base->InLogicThread());
  switch (type) {
    case InputType::kLeftRight:
      left_right_ = value;
      axis_serial_ = g_next_axis_serial++;
      break;
    case InputType::kUpDown:
      up_down_ = value;
      axis_serial_ = g_next_axis_serial++;
      break;
    case InputType::kJumpPress:
      SetButton_(base::kRemoteStateJump, true);
      break;
    case InputType::kJumpRelease:
      SetButton_(base::kRemoteStateJump, false);
      break;
    case InputType::kPunchPress:
      SetButton_(base::kRemoteStatePunch, true);
      break;
    case InputType::kPunchRelease:
      SetButton_(base::kRemoteStatePunch, false);
      break;
    case InputType::kBombPress:
      SetButton_(base::kRemoteStateBomb, true);
      break;
    case InputType::kBombRelease:
      SetButton_(base::kRemoteStateBomb, false);
      break;
    case InputType::kPickUpPress:
      SetButton_(base::kRemoteStateThrow, true);
      break;
    case InputType::kPickUpRelease:
      SetButton_(base::kRemoteStateThrow, false);
      break;
    case InputType::kHoldPositionPress:
      SetButton_(base::kRemoteStateHoldPosition, true);
      break;
    case InputType::kHoldPositionRelease:
      SetButton_(base::kRemoteStateHoldPosition, false);
      break;
    case InputType::kRun:
      SetButton_(base::kRemoteStateRun, value > 0.5f);
      break;
    default:
      // Fly comes along with jump; directional presses and start aren't
      // sent by devices driving players. Nothing else to forward.
      return;
  }
  if (auto* mode = RemoteAppMode::GetActive()) {
    mode->OnInputStateChanged();
  }
}

}  // namespace ballistica::remote
