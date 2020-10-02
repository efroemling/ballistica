// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/input/device/input_device.h"

#include <cstring>
#include <list>
#include <map>

#include "ballistica/app/app_globals.h"
#include "ballistica/game/connection/connection_to_host.h"
#include "ballistica/game/player.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/game/session/net_client_session.h"
#include "ballistica/game/session/replay_client_session.h"
#include "ballistica/networking/networking.h"
#include "ballistica/python/class/python_class_input_device.h"
#include "ballistica/python/python.h"

namespace ballistica {

static std::map<std::string, std::string>* g_rand_name_registry = nullptr;
std::list<std::string> g_default_names;

InputDevice::InputDevice() = default;

auto InputDevice::ShouldBeHiddenFromUser() -> bool {
  // Ask the input system whether they want to ignore us..
  return g_input->ShouldCompletelyIgnoreInputDevice(this);
}

auto InputDevice::GetDeviceName() -> std::string {
  assert(InGameThread());
  return GetRawDeviceName();
}

void InputDevice::ResetRandomNames() {
  assert(InGameThread());
  if (g_rand_name_registry == nullptr) return;
  g_rand_name_registry->clear();
}

// Given a full name "SomeJoyStick #3" etc, reserves/returns a persistent random
// name for it.
static auto GetRandomName(const std::string& full_name) -> std::string {
  assert(InGameThread());

  // Hmm; statically allocating this is giving some crashes on shutdown :-(
  if (g_rand_name_registry == nullptr) {
    g_rand_name_registry = new std::map<std::string, std::string>();
  }

  auto i = g_rand_name_registry->find(full_name);
  if (i == g_rand_name_registry->end()) {
    // Doesn't exist. Pull a random one and add it.
    // Refill the global list if its empty.
    if (g_default_names.empty()) {
      const std::list<std::string>& random_name_list =
          Utils::GetRandomNameList();
      for (const auto& i2 : random_name_list) {
        g_default_names.push_back(i2);
      }
    }

    // Ok now pull a random one off the list and assign it to us
    int index = static_cast<int>(rand() % g_default_names.size());  // NOLINT
    auto i3 = g_default_names.begin();
    for (int j = 0; j < index; j++) {
      i3++;
    }
    (*g_rand_name_registry)[full_name] = *i3;
    g_default_names.erase(i3);
  }
  return (*g_rand_name_registry)[full_name];
}

auto InputDevice::GetPlayerProfiles() const -> PyObject* { return nullptr; }

auto InputDevice::GetPublicAccountID() const -> std::string {
  assert(InGameThread());

  // this default implementation assumes the device is local
  // so just returns the locally signed in account's public id..

  // the master-server makes our public account-id available to us
  // through a misc-read-val; look for that..
  std::string pub_id =
      g_python->GetAccountMiscReadVal2String("resolvedAccountID");
  return pub_id;
}

auto InputDevice::GetAccountName(bool full) const -> std::string {
  assert(InGameThread());
  if (full) {
    return PlayerSpec::GetAccountPlayerSpec().GetDisplayString();
  } else {
    return PlayerSpec::GetAccountPlayerSpec().GetShortName();
  }
}

auto InputDevice::IsRemoteClient() const -> bool { return false; }

auto InputDevice::GetClientID() const -> int { return -1; }

auto InputDevice::GetDefaultPlayerName() -> std::string {
  assert(InGameThread());
  char buffer[256];
  snprintf(buffer, sizeof(buffer), "%s %s", GetDeviceName().c_str(),
           GetPersistentIdentifier().c_str());
  std::string default_name = GetRandomName(buffer);
  return default_name;
}

auto InputDevice::GetButtonName(int id) -> std::string {
  // By default just say 'button 1' or whatnot.
  // FIXME: should return this in Lstr json form.
  return g_game->GetResourceString("buttonText") + " " + std::to_string(id);
}

auto InputDevice::GetAxisName(int id) -> std::string {
  // By default just return 'axis 5' or whatnot.
  // FIXME: should return this in Lstr json form.
  return g_game->GetResourceString("axisText") + " " + std::to_string(id);
}

auto InputDevice::HasMeaningfulButtonNames() -> bool { return false; }

auto InputDevice::GetPersistentIdentifier() const -> std::string {
  assert(InGameThread());
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "#%d", number_);
  return buffer;
}

InputDevice::~InputDevice() {
  assert(InGameThread());
  assert(!player_.exists());
  // release our python ref to ourself if we have one
  if (py_ref_) {
    Py_DECREF(py_ref_);
  }
}

// when the host-session tells us to attach to a player
void InputDevice::AttachToLocalPlayer(Player* player) {
  if (player_.exists()) {
    Log("Error: InputDevice::AttachToLocalPlayer() called with already "
        "existing "
        "player");
    return;
  }
  if (remote_player_.exists()) {
    Log("Error: InputDevice::AttachToLocalPlayer() called with already "
        "existing "
        "remote-player");
    return;
  }
  player_ = player;
  player_->SetInputDevice(this);
}

void InputDevice::AttachToRemotePlayer(ConnectionToHost* connection_to_host,
                                       int remote_player_id) {
  assert(connection_to_host);
  if (player_.exists()) {
    Log("Error: InputDevice::AttachToRemotePlayer()"
        " called with already existing "
        "player");
    return;
  }
  if (remote_player_.exists()) {
    Log("Error: InputDevice::AttachToRemotePlayer()"
        " called with already existing "
        "remote-player");
    return;
  }
  remote_player_ = connection_to_host;
  remote_player_id_ = remote_player_id;
}

void InputDevice::RemoveRemotePlayerFromGame() {
  if (ConnectionToHost* connection_to_host = remote_player_.get()) {
    std::vector<uint8_t> data(2);
    data[0] = BA_MESSAGE_REMOVE_REMOTE_PLAYER;
    data[1] = static_cast_check_fit<unsigned char>(index());
    connection_to_host->SendReliableMessage(data);
  } else {
    Log("Error: RemoveRemotePlayerFromGame called without remote player");
  }
}

void InputDevice::DetachFromPlayer() {
  if (player_.exists()) {
    player_->SetInputDevice(nullptr);
    player_.Clear();
  }
  // Hmmm.. DetachFromPlayer() doesn't get called if the remote connection dies,
  // but since its a weak-ref it should be all good since we don't do anything
  // here except clear the weak-ref anyway...
  if (remote_player_.exists()) {
    remote_player_.Clear();
  }
}

auto InputDevice::GetRemotePlayer() const -> ConnectionToHost* {
  return remote_player_.get();
}

// Called to let the current host/client-session know that we'd like to control
// something please.
void InputDevice::RequestPlayer() {
  assert(InGameThread());

  // Make note that we're being used in some way.
  last_input_time_ = g_game->master_time();

  if (player_.exists()) {
    Log("Error: InputDevice::RequestPlayer()"
        " called with already-existing player");
    return;
  }
  if (remote_player_.exists()) {
    Log("Error: InputDevice::RequestPlayer() called with already-existing "
        "remote-player");
    return;
  }

  // If we have a local host-session, ask it for a player.. otherwise if we have
  // a client-session, ask it for a player.
  assert(g_game);
  if (auto* hs = dynamic_cast<HostSession*>(g_game->GetForegroundSession())) {
    {
      Python::ScopedCallLabel label("requestPlayer");
      hs->RequestPlayer(this);
    }
  } else if (auto* client_session = dynamic_cast<NetClientSession*>(
                 g_game->GetForegroundSession())) {
    if (ConnectionToHost* connection_to_host =
            client_session->connection_to_host()) {
      std::vector<uint8_t> data(2);
      data[0] = BA_MESSAGE_REQUEST_REMOTE_PLAYER;
      data[1] = static_cast_check_fit<uint8_t>(index());
      connection_to_host->SendReliableMessage(data);
    }
  }
  // If we're in a replay or the game is still bootstrapping, just ignore..
}

void InputDevice::ShipBufferIfFull() {
  assert(remote_player_.exists());
  ConnectionToHost* hc = remote_player_.get();

  // Ship the buffer once it gets big enough or once enough time has passed.
  millisecs_t real_time = GetRealTime();
  size_t size = remote_input_commands_buffer_.size();
  if (size > 2
      && (static_cast<int>(real_time - last_remote_input_commands_send_time_)
              > g_app_globals->buffer_time
          || size > 400)) {
    last_remote_input_commands_send_time_ = real_time;
    hc->SendReliableMessage(remote_input_commands_buffer_);
    remote_input_commands_buffer_.clear();
  }
}

// If we're attached to a remote player, ship completed packets every now and
// then.
void InputDevice::Update() {
  if (remote_player_.exists()) {
    ShipBufferIfFull();
  }
}

void InputDevice::UpdateLastInputTime() {
  last_input_time_ = g_game->master_time();
}

void InputDevice::InputCommand(InputType type, float value) {
  assert(InGameThread());

  // Make note that we're being used in some way.
  UpdateLastInputTime();

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
            static_cast_check_fit<uint8_t>(index());
      }
      // Now add this command; add 1 byte for type, 4 for value.
      remote_input_commands_buffer_.resize(remote_input_commands_buffer_.size()
                                           + 5);
      remote_input_commands_buffer_[size] = static_cast<uint8_t>(type);
      memcpy(&(remote_input_commands_buffer_[size + 1]), &value, 4);
    }
  }
}

void InputDevice::ResetHeldStates() {}

auto InputDevice::GetPyInputDevice(bool new_ref) -> PyObject* {
  assert(InGameThread());
  if (py_ref_ == nullptr) {
    py_ref_ = PythonClassInputDevice::Create(this);
  }
  if (new_ref) Py_INCREF(py_ref_);
  return py_ref_;
}

auto InputDevice::GetPartyButtonName() const -> std::string { return ""; }

}  // namespace ballistica
