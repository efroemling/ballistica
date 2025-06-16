// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"

#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/support/plus_soft.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/scene_v1/connection/connection_to_host.h"
#include "ballistica/scene_v1/node/player_node.h"
#include "ballistica/scene_v1/python/class/python_class_input_device.h"
#include "ballistica/scene_v1/support/client_session_net.h"
#include "ballistica/scene_v1/support/host_activity.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

SceneV1InputDeviceDelegate::SceneV1InputDeviceDelegate() = default;

SceneV1InputDeviceDelegate::~SceneV1InputDeviceDelegate() {
  assert(g_base->InLogicThread());
  assert(!player_.exists());
  // Release our Python ref to ourself if we have one.
  if (py_ref_) {
    Py_DECREF(py_ref_);
  }
}
std::optional<Vector3f> SceneV1InputDeviceDelegate::GetPlayerPosition() {
  PlayerNode* player_node{};
  // Try to come up with whichever scene is in the foreground, and try
  // to pull a node for the player we're attached to.

  if (HostActivity* host_activity =
          ContextRefSceneV1::FromAppForegroundContext().GetHostActivity()) {
    if (Player* player = GetPlayer()) {
      player_node = host_activity->scene()->GetPlayerNode(player->id());
    }
  } else {
    if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
      if (Scene* scene = appmode->GetForegroundScene()) {
        player_node = scene->GetPlayerNode(remote_player_id());
      }
    }
  }
  if (player_node) {
    auto pos = player_node->position();
    return Vector3f(player_node->position());
  }
  return {};
}

auto SceneV1InputDeviceDelegate::AttachedToPlayer() const -> bool {
  return player_.exists() || remote_player_.exists();
}

void SceneV1InputDeviceDelegate::RequestPlayer() {
  assert(g_base->InLogicThread());

  auto* appmode = classic::ClassicAppMode::GetActive();
  BA_PRECONDITION_FATAL(appmode);

  if (player_.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "InputDevice::RequestPlayer()"
                         " called with already-existing player");
    return;
  }
  if (remote_player_.exists()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "InputDevice::RequestPlayer() called with already-existing "
        "remote-player");
    return;
  }

  // If we have a local host-session, ask it for a player.. otherwise if we
  // have a client-session, ask it for a player.
  assert(g_base->logic);
  if (auto* hs = dynamic_cast<HostSession*>(appmode->GetForegroundSession())) {
    {
      Python::ScopedCallLabel label("requestPlayer");
      hs->RequestPlayer(this);
    }
  } else if (auto* client_session = dynamic_cast<ClientSessionNet*>(
                 appmode->GetForegroundSession())) {
    if (ConnectionToHost* connection_to_host =
            client_session->connection_to_host()) {
      std::vector<uint8_t> data(2);
      data[0] = BA_MESSAGE_REQUEST_REMOTE_PLAYER;
      data[1] = static_cast_check_fit<uint8_t>(input_device().index());
      connection_to_host->SendReliableMessage(data);
    }
  }
  // If we're in a replay or the game is still bootstrapping, just ignore..
}

// When the host-session tells us to attach to a player
void SceneV1InputDeviceDelegate::AttachToLocalPlayer(Player* player) {
  if (player_.exists()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "InputDevice::AttachToLocalPlayer() called with already "
        "existing "
        "player");
    return;
  }
  if (remote_player_.exists()) {
    g_core->logging->Log(
        LogName::kBa, LogLevel::kError,
        "InputDevice::AttachToLocalPlayer() called with already "
        "existing "
        "remote-player");
    return;
  }
  player_ = player;
  player_->set_input_device_delegate(this);
}

void SceneV1InputDeviceDelegate::AttachToRemotePlayer(
    ConnectionToHost* connection_to_host, int remote_player_id) {
  assert(connection_to_host);
  if (player_.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "InputDevice::AttachToRemotePlayer()"
                         " called with already existing "
                         "player");
    return;
  }
  if (remote_player_.exists()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "InputDevice::AttachToRemotePlayer()"
                         " called with already existing "
                         "remote-player");
    return;
  }
  remote_player_ = connection_to_host;
  remote_player_id_ = remote_player_id;
}

void SceneV1InputDeviceDelegate::DetachFromPlayer() {
  // Handle local player.
  if (auto* player = player_.get()) {
    // NOTE: we now remove the player instantly instead of pushing
    // a call to do it; otherwise its possible that someone tries
    // to access the player's inputdevice before the call goes
    // through which would lead to an exception.
    player_->set_input_device_delegate(nullptr);
    player_.Clear();
    if (HostSession* host_session = player->GetHostSession()) {
      host_session->RemovePlayer(player);
    }
  }

  // Handle remote player.
  if (auto* connection_to_host = remote_player_.get()) {
    std::vector<uint8_t> data(2);
    data[0] = BA_MESSAGE_REMOVE_REMOTE_PLAYER;
    data[1] = static_cast_check_fit<unsigned char>(input_device().index());
    connection_to_host->SendReliableMessage(data);
    remote_player_.Clear();
  }
}

std::string SceneV1InputDeviceDelegate::DescribeAttachedTo() const {
  return (GetRemotePlayer() != nullptr ? "remote-player"
          : GetPlayer() != nullptr     ? "local-player"
                                       : "nothing");
}

void SceneV1InputDeviceDelegate::InputCommand(InputType type, float value) {
  if (Player* p = player_.get()) {
    p->InputCommand(type, value);
  } else if (remote_player_.exists()) {
    // Add to existing buffer of input-commands.
    {
      size_t size = remote_input_commands_buffer_.size();
      // Init if empty; we'll fill in count(bytes 2+3) later.
      if (size == 0) {
        size = 2;
        remote_input_commands_buffer_.resize(size);
        remote_input_commands_buffer_[0] =
            BA_MESSAGE_REMOTE_PLAYER_INPUT_COMMANDS;
        remote_input_commands_buffer_[1] =
            static_cast_check_fit<uint8_t>(input_device().index());
      }
      // Now add this command; add 1 byte for type, 4 for value.
      remote_input_commands_buffer_.resize(remote_input_commands_buffer_.size()
                                           + 5);
      remote_input_commands_buffer_[size] = static_cast<uint8_t>(type);
      memcpy(&(remote_input_commands_buffer_[size + 1]), &value, 4);
    }
  }
}

void SceneV1InputDeviceDelegate::ShipBufferIfFull() {
  assert(remote_player_.exists());
  auto* appmode = classic::ClassicAppMode::GetSingleton();

  ConnectionToHost* hc = remote_player_.get();

  // Ship the buffer once it gets big enough or once enough time has passed.
  millisecs_t real_time = g_core->AppTimeMillisecs();

  size_t size = remote_input_commands_buffer_.size();
  if (size > 2
      && (static_cast<int>(real_time - last_remote_input_commands_send_time_)
              >= appmode->buffer_time()
          || size > 400)) {
    last_remote_input_commands_send_time_ = real_time;
    hc->SendReliableMessage(remote_input_commands_buffer_);
    remote_input_commands_buffer_.clear();
  }
}

auto SceneV1InputDeviceDelegate::GetClientID() const -> int { return -1; }

void SceneV1InputDeviceDelegate::Update() {
  if (remote_player_.exists()) {
    ShipBufferIfFull();
  }
}

auto SceneV1InputDeviceDelegate::GetRemotePlayer() const -> ConnectionToHost* {
  return remote_player_.get();
}

auto SceneV1InputDeviceDelegate::GetPyInputDevice(bool new_ref) -> PyObject* {
  assert(g_base->InLogicThread());
  if (py_ref_ == nullptr) {
    py_ref_ = PythonClassInputDevice::Create(this);
  }
  if (new_ref) {
    Py_INCREF(py_ref_);
  }
  return py_ref_;
}

void SceneV1InputDeviceDelegate::InvalidateConnectionToHost() {
  remote_player_.Clear();
}

auto SceneV1InputDeviceDelegate::GetPublicV1AccountID() const -> std::string {
  assert(g_base->InLogicThread());

  // This default implementation assumes the device is local so just returns
  // the locally signed in account's public id.

  return g_base->Plus()->GetPublicV1AccountID();
}

auto SceneV1InputDeviceDelegate::GetPlayerProfiles() const -> PyObject* {
  return nullptr;
}

auto SceneV1InputDeviceDelegate::GetAccountName(bool full) const
    -> std::string {
  assert(g_base->InLogicThread());
  if (full) {
    return PlayerSpec::GetAccountPlayerSpec().GetDisplayString();
  } else {
    return PlayerSpec::GetAccountPlayerSpec().GetShortName();
  }
}

auto SceneV1InputDeviceDelegate::IsRemoteClient() const -> bool {
  return false;
}

void SceneV1InputDeviceDelegate::ResetRandomNames() {
  assert(g_scene_v1);
  g_scene_v1->ResetRandomNames();
}

auto SceneV1InputDeviceDelegate::GetDefaultPlayerName() -> std::string {
  assert(g_base->InLogicThread());
  assert(g_scene_v1);
  auto&& device = input_device();

  // Custom name, if present, trumps default.
  if (!device.custom_default_player_name().empty()) {
    return device.custom_default_player_name();
  }

  char buffer[256];
  snprintf(buffer, sizeof(buffer), "%s %s", device.GetDeviceName().c_str(),
           device.GetPersistentIdentifier().c_str());
  std::string default_name = g_scene_v1->GetRandomName(buffer);
  return default_name;
}

}  // namespace ballistica::scene_v1
