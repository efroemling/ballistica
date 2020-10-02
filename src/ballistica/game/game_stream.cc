// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/game/game_stream.h"

#include <cstring>

#include "ballistica/app/app_globals.h"
#include "ballistica/dynamics/bg/bg_dynamics.h"
#include "ballistica/dynamics/material/material.h"
#include "ballistica/dynamics/material/material_action.h"
#include "ballistica/dynamics/material/material_component.h"
#include "ballistica/dynamics/material/material_condition_node.h"
#include "ballistica/dynamics/part.h"
#include "ballistica/game/connection/connection_to_client.h"
#include "ballistica/game/session/host_session.h"
#include "ballistica/media/component/collide_model.h"
#include "ballistica/media/component/data.h"
#include "ballistica/media/component/model.h"
#include "ballistica/media/component/texture.h"
#include "ballistica/media/media_server.h"
#include "ballistica/networking/networking.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/scene/node/node_type.h"
#include "ballistica/scene/scene.h"

namespace ballistica {

GameStream::GameStream(HostSession* host_session, bool saveReplay)
    : time_(0),
      host_session_(host_session),
      next_flush_time_(0),
      last_physics_correction_time_(0),
      last_send_time_(0),
      writing_replay_(false) {
  if (saveReplay) {
    // Sanity check - we should only ever be writing one replay at once.
    if (g_app_globals->replay_open) {
      Log("ERROR: g_replay_open true at replay start; shouldn't happen.");
    }
    assert(g_media_server);
    g_media_server->PushBeginWriteReplayCall();
    writing_replay_ = true;
    g_app_globals->replay_open = true;
  }

  // If we're the live output-stream from a host-session,
  // take responsibility for feeding all clients to this device.
  if (host_session_) {
    g_game->RegisterClientController(this);
  }
}

GameStream::~GameStream() {
  // Ship our last commands (if it matters..)
  Flush();

  if (writing_replay_) {
    // Sanity check: We should only ever be writing one replay at once.
    if (!g_app_globals->replay_open) {
      Log("ERROR: g_replay_open false at replay close; shouldn't happen.");
    }
    g_app_globals->replay_open = false;
    assert(g_media_server);
    g_media_server->PushEndWriteReplayCall();
    writing_replay_ = false;
  }

  // If we're wired to the host-session, go ahead and release clients.
  if (host_session_) {
    g_game->UnregisterClientController(this);

    // Also, in the host-session case, make sure everything cleaned itself up.
#if BA_DEBUG_BUILD
    size_t count;
    count = GetPointerCount(scenes_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " scene graphs in output stream at shutdown");
    }
    count = GetPointerCount(nodes_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " nodes in output stream at shutdown");
    }
    count = GetPointerCount(materials_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " materials in output stream at shutdown");
    }
    count = GetPointerCount(textures_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " textures in output stream at shutdown");
    }
    count = GetPointerCount(models_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " models in output stream at shutdown");
    }
    count = GetPointerCount(sounds_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " sounds in output stream at shutdown");
    }
    count = GetPointerCount(collide_models_);
    if (count != 0) {
      Log("ERROR: " + std::to_string(count)
          + " collide_models in output stream at shutdown");
    }
#endif  // BA_DEBUG_BUILD
  }
}

// Pull the current built-up message.
auto GameStream::GetOutMessage() const -> std::vector<uint8_t> {
  assert(!host_session_);  // this should only be getting used for
  // standalone temp ones..
  if (!out_command_.empty()) {
    Log("Error: GameStream shutting down with non-empty outCommand");
  }
  return out_message_;
}

template <typename T>
auto GameStream::GetPointerCount(const std::vector<T*>& vec) -> size_t {
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
auto GameStream::GetFreeIndex(std::vector<T*>* vec,
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
void GameStream::Add(T* val, std::vector<T*>* vec,
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
void GameStream::Remove(T* val, std::vector<T*>* vec,
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

void GameStream::Fail() {
  Log("Error writing replay file");
  if (writing_replay_) {
    // Sanity check: We should only ever be writing one replay at once.
    if (!g_app_globals->replay_open) {
      Log("ERROR: g_replay_open false at replay close; shouldn't happen.");
    }
    assert(g_media_server);
    g_media_server->PushEndWriteReplayCall();
    writing_replay_ = false;
    g_app_globals->replay_open = false;
  }
}

void GameStream::Flush() {
  if (!out_command_.empty())
    Log("Error: GameStream flushing down with non-empty outCommand");
  if (!out_message_.empty()) {
    ShipSessionCommandsMessage();
  }
}

// Writes just a command.
void GameStream::WriteCommand(SessionCommand cmd) {
  assert(out_command_.empty());

  // For now just use full size values.
  size_t size = 0;
  out_command_.resize(size + 1);
  uint8_t* ptr = &out_command_[size];
  *ptr = static_cast<uint8_t>(cmd);
}

// Writes a command plus an int to the stream, using whatever size is optimal.
void GameStream::WriteCommandInt32(SessionCommand cmd, int32_t value) {
  assert(out_command_.empty());

  // For now just use full size values.
  size_t size = 0;
  out_command_.resize(size + 5);
  uint8_t* ptr = &out_command_[size];
  *(ptr++) = static_cast<uint8_t>(cmd);
  int32_t vals[] = {value};
  memcpy(ptr, vals, 4);
}

void GameStream::WriteCommandInt32_2(SessionCommand cmd, int32_t value1,
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

void GameStream::WriteCommandInt32_3(SessionCommand cmd, int32_t value1,
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

void GameStream::WriteCommandInt32_4(SessionCommand cmd, int32_t value1,
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
void GameStream::WriteCommandInt64(SessionCommand cmd, int64_t value) {
  WriteCommandInt32(cmd, static_cast_check_fit<int32_t>(value));
}

void GameStream::WriteCommandInt64_2(SessionCommand cmd, int64_t value1,
                                     int64_t value2) {
  WriteCommandInt32_2(cmd, static_cast_check_fit<int32_t>(value1),
                      static_cast_check_fit<int32_t>(value2));
}

void GameStream::WriteCommandInt64_3(SessionCommand cmd, int64_t value1,
                                     int64_t value2, int64_t value3) {
  WriteCommandInt32_3(cmd, static_cast_check_fit<int32_t>(value1),
                      static_cast_check_fit<int32_t>(value2),
                      static_cast_check_fit<int32_t>(value3));
}

void GameStream::WriteCommandInt64_4(SessionCommand cmd, int64_t value1,
                                     int64_t value2, int64_t value3,
                                     int64_t value4) {
  WriteCommandInt32_4(cmd, static_cast_check_fit<int32_t>(value1),
                      static_cast_check_fit<int32_t>(value2),
                      static_cast_check_fit<int32_t>(value3),
                      static_cast_check_fit<int32_t>(value4));
}

void GameStream::WriteString(const std::string& s) {
  // Write length int.
  auto string_size = s.size();
  auto size = out_command_.size();
  out_command_.resize(size + 4 + s.size());
  memcpy(&out_command_[size], &string_size, 4);
  if (string_size > 0) {
    memcpy(&out_command_[size + 4], s.c_str(), string_size);
  }
}

void GameStream::WriteFloat(float val) {
  auto size = static_cast<int>(out_command_.size());
  out_command_.resize(size + sizeof(val));
  memcpy(&out_command_[size], &val, 4);
}

void GameStream::WriteFloats(size_t count, const float* vals) {
  assert(count > 0);
  auto size = out_command_.size();
  size_t vals_size = sizeof(float) * count;
  out_command_.resize(size + vals_size);
  memcpy(&(out_command_[size]), vals, vals_size);
}

void GameStream::WriteInts32(size_t count, const int32_t* vals) {
  assert(count > 0);
  auto size = out_command_.size();
  size_t vals_size = sizeof(int32_t) * count;
  out_command_.resize(size + vals_size);
  memcpy(&(out_command_[size]), vals, vals_size);
}

void GameStream::WriteInts64(size_t count, const int64_t* vals) {
  // FIXME: we don't actually support writing 64 bit values to the wire
  // at the moment; will need a protocol update for that.
  // This is just implemented as a placeholder.
  std::vector<int32_t> vals32(count);
  for (size_t i = 0; i < count; i++) {
    vals32[i] = static_cast_check_fit<int32_t>(vals[i]);
  }
  WriteInts32(count, vals32.data());
}

void GameStream::WriteChars(size_t count, const char* vals) {
  assert(count > 0);
  auto size = out_command_.size();
  auto vals_size = static_cast<size_t>(count);
  out_command_.resize(size + vals_size);
  memcpy(&(out_command_[size]), vals, vals_size);
}

void GameStream::ShipSessionCommandsMessage() {
  BA_PRECONDITION(!out_message_.empty());

  // Send this message to all client-connections we're attached to.
  for (auto& connection : connections_to_clients_) {
    (*connection).SendReliableMessage(out_message_);
  }
  if (writing_replay_) {
    AddMessageToReplay(out_message_);
  }
  out_message_.clear();
  last_send_time_ = GetRealTime();
}

void GameStream::AddMessageToReplay(const std::vector<uint8_t>& message) {
  assert(writing_replay_);
  assert(g_media_server);

  assert(!message.empty());
#if BA_DEBUG_BUILD
  switch (message[0]) {
    case BA_MESSAGE_SESSION_RESET:
    case BA_MESSAGE_SESSION_COMMANDS:
    case BA_MESSAGE_SESSION_DYNAMICS_CORRECTION:
      break;
    default:
      throw Exception("unexpected message going to replay: "
                      + std::to_string(static_cast<int>(message[0])));
  }
#endif  // BA_DEBUG_BUILD
  g_media_server->PushAddMessageToReplayCall(message);
}

void GameStream::SendPhysicsCorrection(bool blend) {
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

void GameStream::EndCommand(bool is_time_set) {
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
  // long enough.

  // Also send off occasional correction packets.
  if (host_session_) {
    // Now if its been long enough and this is a time-step command, send.
    millisecs_t real_time = GetRealTime();
    millisecs_t diff = real_time - last_send_time_;
    if (is_time_set && diff > g_app_globals->buffer_time) {
      ShipSessionCommandsMessage();

      // Also, as long as we're here, fire off a physics-correction packet every
      // now and then.

      // IMPORTANT: We only do this right after shipping off our pending session
      // commands; otherwise the client will get the correction that accounts
      // for commands that they haven't been sent yet.
      diff = real_time - last_physics_correction_time_;
      if (diff > g_app_globals->dynamics_sync_time) {
        last_physics_correction_time_ = real_time;
        SendPhysicsCorrection(true);
      }
    }
  }
  out_command_.clear();
}

auto GameStream::IsValidScene(Scene* s) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (s != nullptr && s->stream_id() >= 0
          && s->stream_id() < static_cast<int64_t>(scenes_.size())
          && scenes_[s->stream_id()] == s);
}

auto GameStream::IsValidNode(Node* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(nodes_.size())
          && nodes_[n->stream_id()] == n);
}

auto GameStream::IsValidTexture(Texture* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(textures_.size())
          && textures_[n->stream_id()] == n);
}

auto GameStream::IsValidModel(Model* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(models_.size())
          && models_[n->stream_id()] == n);
}

auto GameStream::IsValidSound(Sound* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(sounds_.size())
          && sounds_[n->stream_id()] == n);
}

auto GameStream::IsValidData(Data* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(datas_.size())
          && datas_[n->stream_id()] == n);
}

auto GameStream::IsValidCollideModel(CollideModel* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(collide_models_.size())
          && collide_models_[n->stream_id()] == n);
}

auto GameStream::IsValidMaterial(Material* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(materials_.size())
          && materials_[n->stream_id()] == n);
}

void GameStream::SetTime(millisecs_t t) {
  if (time_ == t) {
    return;  // Ignore redundants.
  }
  millisecs_t diff = t - time_;
  if (diff > 255) {
    Log("Error: GameStream got time diff > 255; not expected.");
    diff = 255;
  }
  WriteCommandInt64(SessionCommand::kBaseTimeStep, diff);
  time_ = t;
  EndCommand(true);
}

void GameStream::AddScene(Scene* s) {
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

void GameStream::RemoveScene(Scene* s) {
  WriteCommandInt64(SessionCommand::kRemoveSceneGraph, s->stream_id());
  Remove(s, &scenes_, &free_indices_scene_graphs_);
  EndCommand();
}

void GameStream::StepScene(Scene* s) {
  assert(IsValidScene(s));
  WriteCommandInt64(SessionCommand::kStepSceneGraph, s->stream_id());
  EndCommand();
}

void GameStream::AddNode(Node* n) {
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

void GameStream::NodeOnCreate(Node* n) {
  assert(IsValidNode(n));
  WriteCommandInt64(SessionCommand::kNodeOnCreate, n->stream_id());
  EndCommand();
}

void GameStream::SetForegroundScene(Scene* sg) {
  assert(IsValidScene(sg));
  WriteCommandInt64(SessionCommand::kSetForegroundSceneGraph, sg->stream_id());
  EndCommand();
}

void GameStream::RemoveNode(Node* n) {
  assert(IsValidNode(n));
  WriteCommandInt64(SessionCommand::kRemoveNode, n->stream_id());
  Remove(n, &nodes_, &free_indices_nodes_);
  EndCommand();
}

void GameStream::AddTexture(Texture* t) {
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

void GameStream::RemoveTexture(Texture* t) {
  assert(IsValidTexture(t));
  WriteCommandInt64(SessionCommand::kRemoveTexture, t->stream_id());
  Remove(t, &textures_, &free_indices_textures_);
  EndCommand();
}

void GameStream::AddModel(Model* t) {
  // Register an ID in host mode.
  if (host_session_) {
    Add(t, &models_, &free_indices_models_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddModel, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void GameStream::RemoveModel(Model* t) {
  assert(IsValidModel(t));
  WriteCommandInt64(SessionCommand::kRemoveModel, t->stream_id());
  Remove(t, &models_, &free_indices_models_);
  EndCommand();
}

void GameStream::AddSound(Sound* t) {
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

void GameStream::RemoveSound(Sound* t) {
  assert(IsValidSound(t));
  WriteCommandInt64(SessionCommand::kRemoveSound, t->stream_id());
  Remove(t, &sounds_, &free_indices_sounds_);
  EndCommand();
}

void GameStream::AddData(Data* t) {
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

void GameStream::RemoveData(Data* t) {
  assert(IsValidData(t));
  WriteCommandInt64(SessionCommand::kRemoveData, t->stream_id());
  Remove(t, &datas_, &free_indices_datas_);
  EndCommand();
}

void GameStream::AddCollideModel(CollideModel* t) {
  if (host_session_) {
    Add(t, &collide_models_, &free_indices_collide_models_);
  } else {
    assert(t && t->stream_id() != -1);
  }
  Scene* sg = t->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddCollideModel, sg->stream_id(),
                      t->stream_id());
  WriteString(t->name());
  EndCommand();
}

void GameStream::RemoveCollideModel(CollideModel* t) {
  assert(IsValidCollideModel(t));
  WriteCommandInt64(SessionCommand::kRemoveCollideModel, t->stream_id());
  Remove(t, &collide_models_, &free_indices_collide_models_);
  EndCommand();
}

void GameStream::AddMaterial(Material* m) {
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

void GameStream::RemoveMaterial(Material* m) {
  assert(IsValidMaterial(m));
  WriteCommandInt64(SessionCommand::kRemoveMaterial, m->stream_id());
  Remove(m, &materials_, &free_indices_materials_);
  EndCommand();
}

void GameStream::AddMaterialComponent(Material* m, MaterialComponent* c) {
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

void GameStream::ConnectNodeAttribute(Node* src_node,
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

void GameStream::NodeMessage(Node* node, const char* buffer, size_t size) {
  assert(IsValidNode(node));
  BA_PRECONDITION(size > 0 && size < 10000);
  WriteCommandInt64_2(SessionCommand::kNodeMessage, node->stream_id(),
                      static_cast_check_fit<int64_t>(size));
  WriteChars(size, buffer);
  EndCommand();
}

void GameStream::SetNodeAttr(const NodeAttribute& attr, float val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_2(SessionCommand::kSetNodeAttrFloat, attr.node->stream_id(),
                      attr.index());
  WriteFloat(val);
  EndCommand();
}

void GameStream::SetNodeAttr(const NodeAttribute& attr, int64_t val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrInt32, attr.node->stream_id(),
                      attr.index(), val);
  EndCommand();
}

void GameStream::SetNodeAttr(const NodeAttribute& attr, bool val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrBool, attr.node->stream_id(),
                      attr.index(), val);
  EndCommand();
}

void GameStream::SetNodeAttr(const NodeAttribute& attr,
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

void GameStream::SetNodeAttr(const NodeAttribute& attr,
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

void GameStream::SetNodeAttr(const NodeAttribute& attr,
                             const std::string& val) {
  assert(IsValidNode(attr.node));
  WriteCommandInt64_2(SessionCommand::kSetNodeAttrString,
                      attr.node->stream_id(), attr.index());
  WriteString(val);
  EndCommand();
}

void GameStream::SetNodeAttr(const NodeAttribute& attr, Node* val) {
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

void GameStream::SetNodeAttr(const NodeAttribute& attr,
                             const std::vector<Node*>& vals) {
  assert(IsValidNode(attr.node));
#if BA_DEBUG_BUILD
  for (auto val : vals) {
    assert(IsValidNode(val));
  }
#endif
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

void GameStream::SetNodeAttr(const NodeAttribute& attr, Player* val) {
  // cout << "SET PLAYER ATTR " << attr.getIndex() << endl;
}

void GameStream::SetNodeAttr(const NodeAttribute& attr,
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

void GameStream::SetNodeAttr(const NodeAttribute& attr, Texture* val) {
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

void GameStream::SetNodeAttr(const NodeAttribute& attr,
                             const std::vector<Texture*>& vals) {
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

void GameStream::SetNodeAttr(const NodeAttribute& attr, Sound* val) {
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

void GameStream::SetNodeAttr(const NodeAttribute& attr,
                             const std::vector<Sound*>& vals) {
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

void GameStream::SetNodeAttr(const NodeAttribute& attr, Model* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidModel(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("model/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrModel,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrModelNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void GameStream::SetNodeAttr(const NodeAttribute& attr,
                             const std::vector<Model*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidModel(val));
    }
  }
  size_t count = vals.size();
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("model/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrModels,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, &(vals_out[0]));
  }
  EndCommand();
}
void GameStream::SetNodeAttr(const NodeAttribute& attr, CollideModel* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidCollideModel(val));
    if (attr.node->scene() != val->scene()) {
      throw Exception("collide_model/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrCollideModel,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrCollideModelNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}
void GameStream::SetNodeAttr(const NodeAttribute& attr,
                             const std::vector<CollideModel*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for (auto val : vals) {
      assert(IsValidCollideModel(val));
    }
  }
  size_t count = vals.size();
  std::vector<int32_t> vals_out;
  if (count > 0) {
    vals_out.resize(count);
    Scene* scene = attr.node->scene();
    for (size_t i = 0; i < count; i++) {
      if (vals[i]->scene() != scene) {
        throw Exception("collide_model/node are from different scenes");
      }
      vals_out[i] = static_cast_check_fit<int32_t>(vals[i]->stream_id());
    }
  }
  WriteCommandInt64_3(SessionCommand::kSetNodeAttrCollideModels,
                      attr.node->stream_id(), attr.index(),
                      static_cast_check_fit<int64_t>(count));
  if (count > 0) {
    WriteInts32(count, &(vals_out[0]));
  }
  EndCommand();
}

void GameStream::PlaySoundAtPosition(Sound* sound, float volume, float x,
                                     float y, float z) {
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

void GameStream::EmitBGDynamics(const BGDynamicsEmission& e) {
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

void GameStream::PlaySound(Sound* sound, float volume) {
  assert(IsValidSound(sound));
  assert(IsValidScene(sound->scene()));

  // FIXME: We shouldn't need to be passing all these as full floats. :-(
  WriteCommandInt64(SessionCommand::kPlaySound, sound->stream_id());
  WriteFloat(volume);
  EndCommand();
}

void GameStream::ScreenMessageTop(const std::string& val, float r, float g,
                                  float b, Texture* texture,
                                  Texture* tint_texture, float tint_r,
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

void GameStream::ScreenMessageBottom(const std::string& val, float r, float g,
                                     float b) {
  WriteCommand(SessionCommand::kScreenMessageBottom);
  WriteString(val);
  float color[3];
  color[0] = r;
  color[1] = g;
  color[2] = b;
  WriteFloats(3, color);
  EndCommand();
}

auto GameStream::GetSoundID(Sound* s) -> int64_t {
  assert(IsValidSound(s));
  return s->stream_id();
}

auto GameStream::GetMaterialID(Material* m) -> int64_t {
  assert(IsValidMaterial(m));
  return m->stream_id();
}

void GameStream::OnClientConnected(ConnectionToClient* c) {
  // Sanity check - abort if its on either of our lists already.
  for (auto& connections_to_client : connections_to_clients_) {
    if (connections_to_client == c) {
      Log("Error: GameStream::OnClientConnected() got duplicate connection.");
      return;
    }
  }
  for (auto& i : connections_to_clients_ignored_) {
    if (i == c) {
      Log("Error: GameStream::OnClientConnected() got duplicate connection.");
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
    GameStream out(nullptr, false);

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

void GameStream::OnClientDisconnected(ConnectionToClient* c) {
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
  Log("Error: GameStream::OnClientDisconnected() called for connection not on "
      "lists");
}

}  // namespace ballistica
