// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/session_stream.h"

#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/scene_v1/connection/connection_to_client.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/dynamics/material/material_component.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/support/host_session.h"
#include "ballistica/scene_v1/support/replay_writer.h"
#include "ballistica/scene_v1/support/scene.h"

namespace ballistica::scene_v1 {

SessionStream::SessionStream(HostSession* host_session, bool save_replay)
    : app_mode_{classic::ClassicAppMode::GetActiveOrThrow()},
      host_session_{host_session} {
  if (save_replay) {
    // Sanity check - we should only ever be writing one replay at once.
    if (g_scene_v1->replay_open) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "g_scene_v1->replay_open true at replay start;"
                           " shouldn't happen.");
    }
    // We always write replays as the max protocol version we support.
    assert(g_base->assets_server);

    replay_writer_ = new ReplayWriter;
    writing_replay_ = true;
    g_scene_v1->replay_open = true;
  }

  // If we're the live output-stream from a host-session,
  // take responsibility for feeding all clients to this device.
  if (host_session_) {
    auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
    appmode->connections()->RegisterClientController(this);
  }
}

SessionStream::~SessionStream() {
  // Ship our last commands (if it matters..)
  Flush();

  if (writing_replay_) {
    // Sanity check: We should only ever be writing one replay at once.
    if (!g_scene_v1->replay_open) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "g_scene_v1->replay_open false at replay close;"
                           " shouldn't happen.");
    }
    g_scene_v1->replay_open = false;
    assert(g_base->assets_server);

    replay_writer_->Finish();
    replay_writer_ = nullptr;

    writing_replay_ = false;
  }

  // If we're wired to the host-session, go ahead and release clients.
  if (host_session_) {
    if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
      appmode->connections()->UnregisterClientController(this);
    }

    // Also, in the host-session case, make sure everything cleaned itself up.
    if (g_buildconfig.debug_build()) {
      size_t count;
      count = GetPointerCount(scenes_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count)
                + " scene graphs in output stream at shutdown");
      }
      count = GetPointerCount(nodes_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " nodes in output stream at shutdown");
      }
      count = GetPointerCount(materials_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " materials in output stream at shutdown");
      }
      count = GetPointerCount(textures_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " textures in output stream at shutdown");
      }
      count = GetPointerCount(meshes_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " meshes in output stream at shutdown");
      }
      count = GetPointerCount(sounds_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " sounds in output stream at shutdown");
      }
      count = GetPointerCount(collision_meshes_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count)
                + " collision_meshes in output stream at shutdown");
      }
    }
  }
}

// Pull the current built-up message.
auto SessionStream::GetOutMessage() const -> std::vector<uint8_t> {
  assert(!host_session_);  // this should only be getting used for
  // standalone temp ones..
  if (!out_command_.empty()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "SceneStream shutting down with non-empty outCommand");
  }
  return out_message_;
}

template <typename T>
auto SessionStream::GetPointerCount(const std::vector<T*>& vec) -> size_t {
  size_t count = 0;

  auto size = vec.size();
  T* const* vals = vec.data();
  for (size_t i = 0; i < size; i++) {
    if (vals[i] != nullptr) {
      count++;
    }
  }
  return count;
}

// Given a vector of pointers, return an index to an available (nullptr) entry,
// expanding the vector if need be.
template <typename T>
auto SessionStream::GetFreeIndex(std::vector<T*>* vec,
                                 std::vector<size_t>* free_indices) -> size_t {
  // If we have any free indices, use one of them.
  if (!free_indices->empty()) {
    size_t val = free_indices->back();
    free_indices->pop_back();
    return val;
  }

  // No free indices; expand the vec and return the new index.
  vec->push_back(nullptr);
  return vec->size() - 1;
}

// Add an entry.
template <typename T>
void SessionStream::Add(T* val, std::vector<T*>* vec,
                        std::vector<size_t>* free_indices) {
  // This should only get used when we're being driven by the host-session.
  assert(host_session_);
  assert(val);
  assert(val->stream_id() == -1);
  size_t index = GetFreeIndex(vec, free_indices);
  (*vec)[index] = val;
  val->set_stream_id(index);
}

// Remove an entry.
template <typename T>
void SessionStream::Remove(T* val, std::vector<T*>* vec,
                           std::vector<size_t>* free_indices) {
  assert(val);
  assert(val->stream_id() >= 0);
  assert(static_cast<int>(vec->size()) > val->stream_id());
  assert((*vec)[val->stream_id()] == val);
  (*vec)[val->stream_id()] = nullptr;

  // Add this to our list of available slots to recycle.
  free_indices->push_back(val->stream_id());
  val->clear_stream_id();
}

void SessionStream::Fail() {
  g_core->logging->Log(LogName::kBa, LogLevel::kError,
                       "Error writing replay file");
  if (writing_replay_) {
    // Sanity check: We should only ever be writing one replay at once.
    if (!g_scene_v1->replay_open) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "g_scene_v1->replay_open false at replay close;"
                           " shouldn't happen.");
    }
    assert(g_base->assets_server);
    replay_writer_->Finish();
    replay_writer_ = nullptr;
    writing_replay_ = false;
    g_scene_v1->replay_open = false;
  }
}

void SessionStream::Flush() {
  if (!out_command_.empty())
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "SceneStream flushing down with non-empty outCommand");
  if (!out_message_.empty()) {
    ShipSessionCommandsMessage();
  }
}

// Writes just a command.
void SessionStream::WriteCommand(SessionCommand cmd) {
  assert(out_command_.empty());

  // For now just use full size values.
  size_t size = 0;
  out_command_.resize(size + 1);
  uint8_t* ptr = &out_command_[size];
  *ptr = static_cast<uint8_t>(cmd);
}

// Writes a command plus an int to the stream, using whatever size is optimal.
void SessionStream::WriteCommandInt32(SessionCommand cmd, int32_t value) {
  assert(out_command_.empty());

  // For now just use full size values.
  size_t size = 0;
  out_command_.resize(size + 5);
  uint8_t* ptr = &out_command_[size];
  *(ptr++) = static_cast<uint8_t>(cmd);
  int32_t vals[] = {value};
  memcpy(ptr, vals, 4);
}

void SessionStream::WriteCommandInt32_2(SessionCommand cmd, int32_t value1,
                                        int32_t value2) {
  assert(out_command_.empty());

  // For now just use full size vals.
  size_t size = 0;
  out_command_.resize(size + 9);
  uint8_t* ptr = &out_command_[size];
  *(ptr++) = static_cast<uint8_t>(cmd);
  int32_t vals[] = {value1, value2};
  memcpy(ptr, vals, 8);
}

void SessionStream::WriteCommandInt32_3(SessionCommand cmd, int32_t value1,
                                        int32_t value2, int32_t value3) {
  assert(out_command_.empty());

  // For now just use full size vals.
  size_t size = 0;
  out_command_.resize(size + 13);
  uint8_t* ptr = &out_command_[size];
  *(ptr++) = static_cast<uint8_t>(cmd);
  int32_t vals[] = {value1, value2, value3};
  memcpy(ptr, vals, 12);
}

void SessionStream::WriteCommandInt32_4(SessionCommand cmd, int32_t value1,
                                        int32_t value2, int32_t value3,
                                        int32_t value4) {
  assert(out_command_.empty());

  // For now just use full size vals.
  size_t size = 0;
  out_command_.resize(size + 17);
  uint8_t* ptr = &out_command_[size];
  *(ptr++) = static_cast<uint8_t>(cmd);
  int32_t vals[] = {value1, value2, value3, value4};
  memcpy(ptr, vals, 16);
}

// FIXME: We don't actually support sending out 64 bit values yet, but
//  adding these placeholders for if/when we do.
//  They will also catch values greater than 32 bits in debug mode.
//  We'll need a protocol update to add support for 64 bit over the wire.
void SessionStream::WriteCommandInt64(SessionCommand cmd, int64_t value) {
  WriteCommandInt32(cmd, static_cast_check_fit<int32_t>(value));
}

void SessionStream::WriteCommandInt64_2(SessionCommand cmd, int64_t value1,
                                        int64_t value2) {
  WriteCommandInt32_2(cmd, static_cast_check_fit<int32_t>(value1),
                      static_cast_check_fit<int32_t>(value2));
}

void SessionStream::WriteCommandInt64_3(SessionCommand cmd, int64_t value1,
                                        int64_t value2, int64_t value3) {
  WriteCommandInt32_3(cmd, static_cast_check_fit<int32_t>(value1),
                      static_cast_check_fit<int32_t>(value2),
                      static_cast_check_fit<int32_t>(value3));
}

void SessionStream::WriteCommandInt64_4(SessionCommand cmd, int64_t value1,
                                        int64_t value2, int64_t value3,
                                        int64_t value4) {
  WriteCommandInt32_4(cmd, static_cast_check_fit<int32_t>(value1),
                      static_cast_check_fit<int32_t>(value2),
                      static_cast_check_fit<int32_t>(value3),
                      static_cast_check_fit<int32_t>(value4));
}

void SessionStream::WriteString(const std::string& s) {
  // Write length int.
  auto string_size = s.size();
  auto size = out_command_.size();
  out_command_.resize(size + 4 + s.size());
  memcpy(&out_command_[size], &string_size, 4);
  if (string_size > 0) {
    memcpy(&out_command_[size + 4], s.c_str(), string_size);
  }
}

void SessionStream::WriteFloat(float val) {
  auto size = static_cast<int>(out_command_.size());
  out_command_.resize(size + sizeof(val));
  memcpy(&out_command_[size], &val, 4);
}

void SessionStream::WriteFloats(size_t count, const float* vals) {
  assert(count > 0);
  auto size = out_command_.size();
  size_t vals_size = sizeof(float) * count;
  out_command_.resize(size + vals_size);
  memcpy(&(out_command_[size]), vals, vals_size);
}

void SessionStream::WriteInts32(size_t count, const int32_t* vals) {
  assert(count > 0);
  auto size = out_command_.size();
  size_t vals_size = sizeof(int32_t) * count;
  out_command_.resize(size + vals_size);
  memcpy(&(out_command_[size]), vals, vals_size);
}

void SessionStream::WriteInts64(size_t count, const int64_t* vals) {
  // FIXME: we don't actually support writing 64 bit values to the wire
  // at the moment; will need a protocol update for that.
  // This is just implemented as a placeholder.
  std::vector<int32_t> vals32(count);
  for (size_t i = 0; i < count; i++) {
    vals32[i] = static_cast_check_fit<int32_t>(vals[i]);
  }
  WriteInts32(count, vals32.data());
}

void SessionStream::WriteChars(size_t count, const char* vals) {
  assert(count > 0);
  auto size = out_command_.size();
  auto vals_size = static_cast<size_t>(count);
  out_command_.resize(size + vals_size);
  memcpy(&(out_command_[size]), vals, vals_size);
}

void SessionStream::ShipSessionCommandsMessage() {
  BA_PRECONDITION(!out_message_.empty());

  // Send this message to all client-connections we're attached to.
  for (auto& connection : connections_to_clients_) {
    (*connection).SendReliableMessage(out_message_);
  }
  if (writing_replay_) {
    AddMessageToReplay(out_message_);
  }
  out_message_.clear();
  last_send_time_ = g_core->AppTimeMillisecs();
}

void SessionStream::AddMessageToReplay(const std::vector<uint8_t>& message) {
  assert(writing_replay_);
  assert(g_base->assets_server);

  assert(!message.empty());
  if (g_buildconfig.debug_build()) {
    switch (message[0]) {
      case BA_MESSAGE_SESSION_RESET:
      case BA_MESSAGE_SESSION_COMMANDS:
      case BA_MESSAGE_SESSION_DYNAMICS_CORRECTION:
        break;
      default:
        throw Exception("unexpected message going to replay: "
                        + std::to_string(static_cast<int>(message[0])));
    }
  }

  assert(replay_writer_);
  replay_writer_->PushAddMessageToReplayCall(message);
}

void SessionStream::SendPhysicsCorrection(bool blend) {
  assert(host_session_);

  std::vector<std::vector<uint8_t> > messages;
  host_session_->GetCorrectionMessages(blend, &messages);

  // FIXME - have to send reliably at the moment since these will most likely be
  //  bigger than our unreliable packet limit. :-(
  for (auto& message : messages) {
    for (auto& connections_to_client : connections_to_clients_) {
      (*connections_to_client).SendReliableMessage(message);
    }
    if (writing_replay_) {
      AddMessageToReplay(message);
    }
  }
}

void SessionStream::EndCommand(bool is_time_set) {
  assert(!out_command_.empty());

  int out_message_size;
  if (out_message_.empty()) {
    // Init the message if we're the first command on it.
    out_message_.resize(1);
    out_message_[0] = BA_MESSAGE_SESSION_COMMANDS;
    out_message_size = 1;
  } else {
    out_message_size = static_cast<int>(out_message_.size());
  }

  out_message_.resize(out_message_size + 2
                      + out_command_.size());  // command length plus data

  auto val = static_cast<uint16_t>(out_command_.size());
  memcpy(&(out_message_[out_message_size]), &val, 2);
  memcpy(&(out_message_[out_message_size + 2]), &(out_command_[0]),
         out_command_.size());

  // When attached to a host-session, send this message to clients if it's been
  // long enough. Also send off occasional correction packets.
  if (host_session_) {
    auto* appmode = classic::ClassicAppMode::GetSingleton();
    // Now if its been long enough *AND* this is a time-step command, send.
    millisecs_t real_time = g_core->AppTimeMillisecs();
    millisecs_t diff = real_time - last_send_time_;
    if (is_time_set && diff >= app_mode_->buffer_time()) {
      ShipSessionCommandsMessage();

      // Also, as long as we're here, fire off a physics-correction packet every
      // now and then.

      // IMPORTANT: We only do this right after shipping off our pending session
      // commands; otherwise the client will get the correction that accounts
      // for commands that they haven't been sent yet.
      diff = real_time - last_physics_correction_time_;
      if (diff >= appmode->dynamics_sync_time()) {
        last_physics_correction_time_ = real_time;
        SendPhysicsCorrection(true);
      }
    }
  }
  out_command_.clear();
}

auto SessionStream::IsValidScene(Scene* s) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (s != nullptr && s->stream_id() >= 0
          && s->stream_id() < static_cast<int64_t>(scenes_.size())
          && scenes_[s->stream_id()] == s);
}

auto SessionStream::IsValidNode(Node* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(nodes_.size())
          && nodes_[n->stream_id()] == n);
}

auto SessionStream::IsValidTexture(SceneTexture* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(textures_.size())
          && textures_[n->stream_id()] == n);
}

auto SessionStream::IsValidMesh(SceneMesh* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(meshes_.size())
          && meshes_[n->stream_id()] == n);
}

auto SessionStream::IsValidSound(SceneSound* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(sounds_.size())
          && sounds_[n->stream_id()] == n);
}

auto SessionStream::IsValidData(SceneDataAsset* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(datas_.size())
          && datas_[n->stream_id()] == n);
}

auto SessionStream::IsValidCollisionMesh(SceneCollisionMesh* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(collision_meshes_.size())
          && collision_meshes_[n->stream_id()] == n);
}

auto SessionStream::IsValidMaterial(Material* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(materials_.size())
          && materials_[n->stream_id()] == n);
}

void SessionStream::SetTime(millisecs_t t) {
  if (time_ == t) {
    return;  // Ignore redundants.
  }
  millisecs_t diff = t - time_;
  if (diff > 255) {
    g_core->logging->Log(LogName::kBa, LogLevel::kError,
                         "SceneStream got time diff > 255; not expected.");
    diff = 255;
  }
  WriteCommandInt64(SessionCommand::kBaseTimeStep, diff);
  time_ = t;
  EndCommand(true);
}

void SessionStream::AddScene(Scene* s) {
  // Host mode.
  if (host_session_) {
    Add(s, &scenes_, &free_indices_scene_graphs_);
    s->SetOutputStream(this);
  } else {
    // Dump mode.
    assert(s->stream_id() != -1);
  }
  WriteCommandInt64_2(SessionCommand::kAddSceneGraph, s->stream_id(),
                      s->time());
  EndCommand();
}

void SessionStream::RemoveScene(Scene* s) {
  WriteCommandInt64(SessionCommand::kRemoveSceneGraph, s->stream_id());
  Remove(s, &scenes_, &free_indices_scene_graphs_);
  EndCommand();
}

void SessionStream::StepScene(Scene* s) {
  assert(IsValidScene(s));
  WriteCommandInt64(SessionCommand::kStepSceneGraph, s->stream_id());
  EndCommand();
}

void SessionStream::AddNode(Node* n) {
  assert(n);
  if (host_session_) {
    Add(n, &nodes_, &free_indices_nodes_);
  } else {
    assert(n && n->stream_id() != -1);
  }

  Scene* sg = n->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_3(SessionCommand::kAddNode, sg->stream_id(),
                      n->type()->id(), n->stream_id());
  EndCommand();
}

void SessionStream::NodeOnCreate(Node* n) {
  assert(IsValidNode(n));
  WriteCommandInt64(SessionCommand::kNodeOnCreate, n->stream_id());
  EndCommand();
}

void SessionStream::SetForegroundScene(Scene* sg) {
  assert(IsValidScene(sg));
  WriteCommandInt64(SessionCommand::kSetForegroundScene, sg->stream_id());
  EndCommand();
}

void SessionStream::RemoveNode(Node* n) {
  assert(IsValidNode(n));
  WriteCommandInt64(SessionCommand::kRemoveNode, n->stream_id());
  Remove(n, &nodes_, &free_indices_nodes_);
  EndCommand();
}

void SessionStream::AddTexture(SceneTexture* t) {
  // Register an ID in host mode.
  if (host_session_) {
    Add(t, &textures_, &free_indices_textures_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddTexture, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void SessionStream::RemoveTexture(SceneTexture* t) {
  assert(IsValidTexture(t));
  WriteCommandInt64(SessionCommand::kRemoveTexture, t->stream_id());
  Remove(t, &textures_, &free_indices_textures_);
  EndCommand();
}

void SessionStream::AddMesh(SceneMesh* t) {
  // Register an ID in host mode.
  if (host_session_) {
    Add(t, &meshes_, &free_indices_meshes_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddMesh, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void SessionStream::RemoveMesh(SceneMesh* t) {
  assert(IsValidMesh(t));
  WriteCommandInt64(SessionCommand::kRemoveMesh, t->stream_id());
  Remove(t, &meshes_, &free_indices_meshes_);
  EndCommand();
}

void SessionStream::AddSound(SceneSound* t) {
  // Register an ID in host mode.
  if (host_session_) {
    Add(t, &sounds_, &free_indices_sounds_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddSound, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void SessionStream::RemoveSound(SceneSound* t) {
  assert(IsValidSound(t));
  WriteCommandInt64(SessionCommand::kRemoveSound, t->stream_id());
  Remove(t, &sounds_, &free_indices_sounds_);
  EndCommand();
}

void SessionStream::AddData(SceneDataAsset* t) {
  // Register an ID in host mode.
  if (host_session_) {
    Add(t, &datas_, &free_indices_datas_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddData, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void SessionStream::RemoveData(SceneDataAsset* t) {
  assert(IsValidData(t));
  WriteCommandInt64(SessionCommand::kRemoveData, t->stream_id());
  Remove(t, &datas_, &free_indices_datas_);
  EndCommand();
}

void SessionStream::AddCollisionMesh(SceneCollisionMesh* t) {
  if (host_session_) {
    Add(t, &collision_meshes_, &free_indices_collision_meshes_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddCollisionMesh, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void SessionStream::RemoveCollisionMesh(SceneCollisionMesh* t) {
  assert(IsValidCollisionMesh(t));
  WriteCommandInt64(SessionCommand::kRemoveCollisionMesh, t->stream_id());
  Remove(t, &collision_meshes_, &free_indices_collision_meshes_);
  EndCommand();
}

void SessionStream::AddMaterial(Material* m) {
  if (host_session_) {
    Add(m, &materials_, &free_indices_materials_);
  } else {
    assert(m && m->stream_id() != -1);
  }
  Scene* sg = m->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddMaterial, sg->stream_id(),
                      m->stream_id());
  EndCommand();
}

void SessionStream::RemoveMaterial(Material* m) {
  assert(IsValidMaterial(m));
  WriteCommandInt64(SessionCommand::kRemoveMaterial, m->stream_id());
  Remove(m, &materials_, &free_indices_materials_);
  EndCommand();
}

void SessionStream::AddMaterialComponent(Material* m, MaterialComponent* c) {
  assert(IsValidMaterial(m));
  auto flattened_size = c->GetFlattenedSize();
  assert(flattened_size > 0 && flattened_size < 10000);
  WriteCommandInt64_2(SessionCommand::kAddMaterialComponent, m->stream_id(),
                      static_cast_check_fit<int64_t>(flattened_size));
  size_t size = out_command_.size();
  out_command_.resize(size + flattened_size);
  char* ptr = reinterpret_cast<char*>(&out_command_[size]);
  char* ptr2 = ptr;
  c->Flatten(&ptr2, this);
  size_t actual_size = ptr2 - ptr;
  if (actual_size != flattened_size) {
    throw Exception("Expected flattened_size " + std::to_string(flattened_size)
                    + " got " + std::to_string(actual_size));
  }
  EndCommand();
}

void SessionStream::ConnectNodeAttribute(Node* src_node,
                                         NodeAttributeUnbound* src_attr,
                                         Node* dst_node,
                                         NodeAttributeUnbound* dst_attr) {
  assert(IsValidNode(src_node));
  assert(IsValidNode(dst_node));
  assert(src_attr->node_type() == src_node->type());
  assert(dst_attr->node_type() == dst_node->type());
  if (src_node->scene() != dst_node->scene()) {
    throw Exception("Nodes are from different scenes");
  }
  assert(src_node->scene() == dst_node->scene());
  WriteCommandInt64_4(SessionCommand::kConnectNodeAttribute,
                      src_node->stream_id(), src_attr->index(),
                      dst_node->stream_id(), dst_attr->index());
  EndCommand();
}

void SessionStream::NodeMessage(Node* node, const char* buffer, size_t size) {
  assert(IsValidNode(node));
  BA_PRECONDITION(size > 0 && size < 10000);
  WriteCommandInt64_2(SessionCommand::kNodeMessage, node->stream_id(),
                      static_cast_check_fit<int64_t>(size));
  WriteChars(size, buffer);
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, float val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_2(SessionCommand::kSetNodeAttrFloat, attr.node->stream_id(),
                      attr.index());
  WriteFloat(val);
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, int64_t val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrInt32, attr.node->stream_id(),
                      attr.index(), val);
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, bool val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrBool, attr.node->stream_id(),
                      attr.index(), val);
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<float>& vals) {
  assert(IsValidNode(attr.node));
  size_t count{vals.size()};
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrFloats,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteFloats(count, vals.data());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<int64_t>& vals) {
  assert(IsValidNode(attr.node));
  size_t count{vals.size()};
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrInt32s,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts64(count, vals.data());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::string& val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_2(SessionCommand::kSetNodeAttrString,
                      attr.node->stream_id(), attr.index());
  WriteString(val);
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, Node* val) {
  assert(IsValidNode(attr.node));
  if (val) {
    assert(IsValidNode(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("nodes are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrNode,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrNodeNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<Node*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    if (g_buildconfig.debug_build()) {
      for (auto val : vals) {
        assert(IsValidNode(val));
      }
    }
  }
  size_t count{vals.size()};
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("nodes are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrNodes, attr.node->stream_id(),
                      attr.index(), static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, vals_out.data());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, Player* val) {
  // cout << "SET PLAYER ATTR " << attr.getIndex() << endl;
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<Material*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidMaterial(val));
    }
  }
  size_t count = vals.size();
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("material/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrMaterials,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, &(vals_out[0]));
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, SceneTexture* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidTexture(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("texture/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrTexture,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrTextureNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<SceneTexture*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidTexture(val));
    }
  }
  size_t count{vals.size()};
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene{attr.node->scene()};
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("texture/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrTextures,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, vals_out.data());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, SceneSound* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidSound(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("sound/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrSound,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrSoundNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<SceneSound*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidSound(val));
    }
  }
  size_t count{vals.size()};
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("sound/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrSounds,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, &(vals_out[0]));
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr, SceneMesh* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidMesh(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("mesh/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrMesh,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrMeshNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<SceneMesh*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidMesh(val));
    }
  }
  size_t count = vals.size();
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("mesh/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrMeshes,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, &(vals_out[0]));
  }
  EndCommand();
}
void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                SceneCollisionMesh* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidCollisionMesh(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("collision_mesh/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrCollisionMesh,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrCollisionMeshNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}
void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<SceneCollisionMesh*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidCollisionMesh(val));
    }
  }
  size_t count = vals.size();
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("collision_mesh/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrCollisionMeshes,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, &(vals_out[0]));
  }
  EndCommand();
}

void SessionStream::PlaySoundAtPosition(SceneSound* sound, float volume,
                                        float x, float y, float z) {
  assert(IsValidSound(sound));
  assert(IsValidScene(sound->scene()));

  // FIXME: We shouldn't need to be passing all these as full floats. :-(
  WriteCommandInt64(SessionCommand::kPlaySoundAtPosition, sound->stream_id());
  WriteFloat(volume);
  WriteFloat(x);
  WriteFloat(y);
  WriteFloat(z);
  EndCommand();
}

void SessionStream::EmitBGDynamics(const base::BGDynamicsEmission& e) {
  WriteCommandInt64_4(SessionCommand::kEmitBGDynamics,
                      static_cast<int64_t>(e.emit_type), e.count,
                      static_cast<int64_t>(e.chunk_type),
                      static_cast<int64_t>(e.tendril_type));
  float fvals[8];
  fvals[0] = e.position.x;
  fvals[1] = e.position.y;
  fvals[2] = e.position.z;
  fvals[3] = e.velocity.x;
  fvals[4] = e.velocity.y;
  fvals[5] = e.velocity.z;
  fvals[6] = e.scale;
  fvals[7] = e.spread;
  WriteFloats(8, fvals);
  EndCommand();
}

void SessionStream::EmitCameraShake(float intensity) {
  WriteCommand(SessionCommand::kCameraShake);
  // FIXME: We shouldn't need to be passing all these as full floats. :-(
  WriteFloat(intensity);
  EndCommand();
}

void SessionStream::PlaySound(SceneSound* sound, float volume) {
  assert(IsValidSound(sound));
  assert(IsValidScene(sound->scene()));

  // FIXME: We shouldn't need to be passing all these as full floats. :-(
  WriteCommandInt64(SessionCommand::kPlaySound, sound->stream_id());
  WriteFloat(volume);
  EndCommand();
}

void SessionStream::ScreenMessageTop(const std::string& val, float r, float g,
                                     float b, SceneTexture* texture,
                                     SceneTexture* tint_texture, float tint_r,
                                     float tint_g, float tint_b, float tint2_r,
                                     float tint2_g, float tint2_b) {
  assert(IsValidTexture(texture));
  assert(IsValidTexture(tint_texture));
  assert(IsValidScene(texture->scene()));
  assert(IsValidScene(tint_texture->scene()));
  WriteCommandInt64_2(SessionCommand::kScreenMessageTop, texture->stream_id(),
                      tint_texture->stream_id());
  WriteString(val);
  float f[9];
  f[0] = r;
  f[1] = g;
  f[2] = b;
  f[3] = tint_r;
  f[4] = tint_g;
  f[5] = tint_b;
  f[6] = tint2_r;
  f[7] = tint2_g;
  f[8] = tint2_b;
  WriteFloats(9, f);
  EndCommand();
}

void SessionStream::ScreenMessageBottom(const std::string& val, float r,
                                        float g, float b) {
  WriteCommand(SessionCommand::kScreenMessageBottom);
  WriteString(val);
  float color[3];
  color[0] = r;
  color[1] = g;
  color[2] = b;
  WriteFloats(3, color);
  EndCommand();
}

auto SessionStream::GetSoundID(SceneSound* s) -> int64_t {
  assert(IsValidSound(s));
  return s->stream_id();
}

auto SessionStream::GetMaterialID(Material* m) -> int64_t {
  assert(IsValidMaterial(m));
  return m->stream_id();
}

void SessionStream::OnClientConnected(ConnectionToClient* c) {
  // Sanity check - abort if its on either of our lists already.
  for (auto& connections_to_client : connections_to_clients_) {
    if (connections_to_client == c) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "SceneStream::OnClientConnected() got duplicate connection.");
      return;
    }
  }
  for (auto& i : connections_to_clients_ignored_) {
    if (i == c) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "SceneStream::OnClientConnected() got duplicate connection.");
      return;
    }
  }

  {
    // First thing, we need to flush all pending session-commands to clients.
    // The host-session's current state is the result of having already run
    // these commands locally, so if we leave them on the list while 'restoring'
    // the new client to our state they'll get essentially double-applied, which
    // is bad. (ie: a delete-node command will get called but the node will
    // already be gone)
    Flush();

    connections_to_clients_.push_back(c);

    // We create a temporary output stream just for the purpose of building
    // a giant session-commands message to reconstruct everything in our
    // host-session in its current form.
    SessionStream out(nullptr, false);

    // Ask the host-session that we came from to dump it's complete state.
    host_session_->DumpFullState(&out);

    // Grab the message that's been built up.
    // If its not empty, send it to the client.
    std::vector<uint8_t> out_message = out.GetOutMessage();
    if (!out_message.empty()) {
      c->SendReliableMessage(out_message);
    }

    // Also send a correction packet to sync up all our dynamics.
    // (technically could do this *just* for the new client)
    SendPhysicsCorrection(false);
  }
}

void SessionStream::OnClientDisconnected(ConnectionToClient* c) {
  // Search for it on either our ignored or regular lists.
  for (auto i = connections_to_clients_.begin();
       i != connections_to_clients_.end(); i++) {
    if (*i == c) {
      connections_to_clients_.erase(i);
      return;
    }
  }
  for (auto i = connections_to_clients_ignored_.begin();
       i != connections_to_clients_ignored_.end(); i++) {
    if (*i == c) {
      connections_to_clients_ignored_.erase(i);
      return;
    }
  }
  g_core->logging->Log(
      LogName::kBaNetworking, LogLevel::kError,
      "SceneStream::OnClientDisconnected() called for connection not on "
      "lists");
}

}  // namespace ballistica::scene_v1
