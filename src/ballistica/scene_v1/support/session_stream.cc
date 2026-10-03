// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/session_stream.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_name_compat.h"
#include "ballistica/base/assets/asset_package_registry.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
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
#include "ballistica/scene_v1/support/scene_depiction.h"
#include "ballistica/scene_v1/support/spaz_def.h"
#include "ballistica/shared/foundation/exception.h"

namespace ballistica::scene_v1 {

SessionStream::SessionStream(HostSession* host_session, bool save_replay)
    : app_mode_{classic::ClassicAppMode::GetActiveOrThrow()},
      host_session_{host_session} {
  compact_ =
      app_mode_->host_protocol_version() >= kProtocolVersionCompactStream;
  reliable_corrections_ = getenv("BA_RELIABLE_CORRECTIONS") != nullptr;
  merge_steps_ =
      app_mode_->host_protocol_version() >= kProtocolVersionMergedStep;
  fold_anim_curves_ =
      app_mode_->host_protocol_version() >= kProtocolVersionAnimCurveCommand;
  pack_node_creates_ =
      app_mode_->host_protocol_version() >= kProtocolVersionPackedCommands;
  if (save_replay) {
    // Sanity check - we should only ever be writing one replay at once.
    if (g_scene_v1->replay_open) {
      g_core->logging->Log(LogName::kBa, LogLevel::kError,
                           "g_scene_v1->replay_open true at replay start;"
                           " shouldn't happen.");
    }
    // We're recording our own host-session's stream, so the replay's
    // protocol is our hosted protocol.
    assert(g_base->assets_server);

    replay_writer_ = new ReplayWriter(app_mode_->host_protocol_version());
    writing_replay_ = true;
    g_scene_v1->replay_open = true;
  }

  // If we're the live output-stream from a host-session,
  // take responsibility for feeding all clients to this device.
  if (host_session_) {
    stats_enabled_ = getenv("BA_STREAM_STATS") != nullptr;
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
      count = GetPointerCount(spaz_defs_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " spaz defs in output stream at shutdown");
      }
      count = GetPointerCount(depictions_);
      if (count != 0) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            std::to_string(count) + " depictions in output stream at shutdown");
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

// Out of line so the template above stays private to this file (an
// inline caller in the header left other TUs needing an instantiation
// only debug builds happened to emit).
auto SessionStream::live_spaz_def_count() -> size_t {
  return GetPointerCount(spaz_defs_);
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

// LEB128 varint for the compact framing (protocol 44+); declared in the
// header since compact corrections (Scene) use it too.
void AppendVarint(std::vector<uint8_t>* out, uint32_t value) {
  while (value >= 0x80) {
    out->push_back(static_cast<uint8_t>((value & 0x7f) | 0x80));
    value >>= 7;
  }
  out->push_back(static_cast<uint8_t>(value));
}

namespace {

auto ZigZag(int32_t value) -> uint32_t {
  return (static_cast<uint32_t>(value) << 1)
         ^ static_cast<uint32_t>(value >> 31);
}

// Decode one varint at *pos (bounded by end); returns false if truncated.
auto ReadVarintAt(const uint8_t* end, const uint8_t** pos, uint32_t* value)
    -> bool {
  uint32_t result = 0;
  int shift = 0;
  while (*pos < end && shift <= 28) {
    uint8_t b = *((*pos)++);
    result |= static_cast<uint32_t>(b & 0x7f) << shift;
    if (!(b & 0x80)) {
      *value = result;
      return true;
    }
    shift += 7;
  }
  return false;
}

auto UnZigZag(uint32_t value) -> int32_t {
  return static_cast<int32_t>(value >> 1) ^ -static_cast<int32_t>(value & 1);
}

auto SessionCommandName(uint8_t cmd) -> const char* {
  switch (static_cast<SessionCommand>(cmd)) {
    case SessionCommand::kBaseTimeStep:
      return "BaseTimeStep";
    case SessionCommand::kStepSceneGraph:
      return "StepSceneGraph";
    case SessionCommand::kStepSceneGraphAndTime:
      return "StepSceneGraphAndTime";
    case SessionCommand::kAddAnimCurve:
      return "AddAnimCurve";
    case SessionCommand::kTimeStepSceneGraphAndTime:
      return "TimeStepSceneGraphAndTime";
    case SessionCommand::kAddNodeWithAttrs:
      return "AddNodeWithAttrs";
    case SessionCommand::kAddSceneGraph:
      return "AddSceneGraph";
    case SessionCommand::kRemoveSceneGraph:
      return "RemoveSceneGraph";
    case SessionCommand::kAddNode:
      return "AddNode";
    case SessionCommand::kNodeOnCreate:
      return "NodeOnCreate";
    case SessionCommand::kSetForegroundScene:
      return "SetForegroundScene";
    case SessionCommand::kRemoveNode:
      return "RemoveNode";
    case SessionCommand::kAddMaterial:
      return "AddMaterial";
    case SessionCommand::kRemoveMaterial:
      return "RemoveMaterial";
    case SessionCommand::kAddMaterialComponent:
      return "AddMaterialComponent";
    case SessionCommand::kAddTexture:
      return "AddTexture";
    case SessionCommand::kRemoveTexture:
      return "RemoveTexture";
    case SessionCommand::kAddMesh:
      return "AddMesh";
    case SessionCommand::kRemoveMesh:
      return "RemoveMesh";
    case SessionCommand::kAddSound:
      return "AddSound";
    case SessionCommand::kRemoveSound:
      return "RemoveSound";
    case SessionCommand::kAddCollisionMesh:
      return "AddCollisionMesh";
    case SessionCommand::kRemoveCollisionMesh:
      return "RemoveCollisionMesh";
    case SessionCommand::kConnectNodeAttribute:
      return "ConnectNodeAttribute";
    case SessionCommand::kNodeMessage:
      return "NodeMessage";
    case SessionCommand::kSetNodeAttrFloat:
      return "SetNodeAttrFloat";
    case SessionCommand::kSetNodeAttrInt32:
      return "SetNodeAttrInt32";
    case SessionCommand::kSetNodeAttrBool:
      return "SetNodeAttrBool";
    case SessionCommand::kSetNodeAttrFloats:
      return "SetNodeAttrFloats";
    case SessionCommand::kSetNodeAttrInt32s:
      return "SetNodeAttrInt32s";
    case SessionCommand::kSetNodeAttrString:
      return "SetNodeAttrString";
    case SessionCommand::kSetNodeAttrNode:
      return "SetNodeAttrNode";
    case SessionCommand::kSetNodeAttrNodeNull:
      return "SetNodeAttrNodeNull";
    case SessionCommand::kSetNodeAttrNodes:
      return "SetNodeAttrNodes";
    case SessionCommand::kSetNodeAttrPlayer:
      return "SetNodeAttrPlayer";
    case SessionCommand::kSetNodeAttrPlayerNull:
      return "SetNodeAttrPlayerNull";
    case SessionCommand::kSetNodeAttrMaterials:
      return "SetNodeAttrMaterials";
    case SessionCommand::kSetNodeAttrTexture:
      return "SetNodeAttrTexture";
    case SessionCommand::kSetNodeAttrTextureNull:
      return "SetNodeAttrTextureNull";
    case SessionCommand::kSetNodeAttrTextures:
      return "SetNodeAttrTextures";
    case SessionCommand::kSetNodeAttrSound:
      return "SetNodeAttrSound";
    case SessionCommand::kSetNodeAttrSoundNull:
      return "SetNodeAttrSoundNull";
    case SessionCommand::kSetNodeAttrSounds:
      return "SetNodeAttrSounds";
    case SessionCommand::kSetNodeAttrMesh:
      return "SetNodeAttrMesh";
    case SessionCommand::kSetNodeAttrMeshNull:
      return "SetNodeAttrMeshNull";
    case SessionCommand::kSetNodeAttrMeshes:
      return "SetNodeAttrMeshes";
    case SessionCommand::kSetNodeAttrCollisionMesh:
      return "SetNodeAttrCollisionMesh";
    case SessionCommand::kSetNodeAttrCollisionMeshNull:
      return "SetNodeAttrCollisionMeshNull";
    case SessionCommand::kSetNodeAttrCollisionMeshes:
      return "SetNodeAttrCollisionMeshes";
    case SessionCommand::kPlaySoundAtPosition:
      return "PlaySoundAtPosition";
    case SessionCommand::kPlaySound:
      return "PlaySound";
    case SessionCommand::kEmitBGDynamics:
      return "EmitBGDynamics";
    case SessionCommand::kEndOfFile:
      return "EndOfFile";
    case SessionCommand::kDynamicsCorrection:
      return "DynamicsCorrection";
    case SessionCommand::kScreenMessageBottom:
      return "ScreenMessageBottom";
    case SessionCommand::kScreenMessageTop:
      return "ScreenMessageTop";
    case SessionCommand::kAddData:
      return "AddData";
    case SessionCommand::kRemoveData:
      return "RemoveData";
    case SessionCommand::kCameraShake:
      return "CameraShake";
    case SessionCommand::kDeclareAssetPackage:
      return "DeclareAssetPackage";
    case SessionCommand::kAddTextureIndexed:
      return "AddTextureIndexed";
    case SessionCommand::kAddMeshIndexed:
      return "AddMeshIndexed";
    case SessionCommand::kAddSoundIndexed:
      return "AddSoundIndexed";
    case SessionCommand::kAddCollisionMeshIndexed:
      return "AddCollisionMeshIndexed";
    case SessionCommand::kInputDeviceFeedback:
      return "InputDeviceFeedback";
    case SessionCommand::kAddSpazDef:
      return "AddSpazDef";
    case SessionCommand::kRemoveSpazDef:
      return "RemoveSpazDef";
    case SessionCommand::kSetNodeAttrSpazDef:
      return "SetNodeAttrSpazDef";
    case SessionCommand::kSetNodeAttrSpazDefNull:
      return "SetNodeAttrSpazDefNull";
    case SessionCommand::kAddDepiction:
      return "AddDepiction";
    case SessionCommand::kRemoveDepiction:
      return "RemoveDepiction";
    case SessionCommand::kSetNodeAttrDepiction:
      return "SetNodeAttrDepiction";
    case SessionCommand::kSetNodeAttrDepictionNull:
      return "SetNodeAttrDepictionNull";
    case SessionCommand::kScreenMessageTopDepiction:
      return "ScreenMessageTopDepiction";
    default:
      return "?";
  }
}

auto KBPerSec(int64_t bytes, millisecs_t millis) -> std::string {
  char buf[32];
  snprintf(
      buf, sizeof(buf), "%.1f",
      static_cast<double>(bytes) / 1024.0
          / (static_cast<double>(std::max<millisecs_t>(millis, 1)) / 1000.0));
  return buf;
}

}  // namespace

void SessionStream::StatsNoteCommand_() {
  // Called from EndCommand with the finished command in out_command_
  // (its first byte is the command id; it ships with a 2-byte length).
  uint8_t cmd = out_command_[0];
  int64_t size = static_cast<int64_t>(out_command_.size()) + 2;
  stats_cmd_bytes_[cmd] += size;
  stats_cmd_counts_[cmd]++;
  stats_last_cmd_size_ = size;
  {
    auto ts = static_cast<int>(SessionCommand::kBaseTimeStep);
    auto st = static_cast<int>(SessionCommand::kStepSceneGraph);
    if (stats_prev_cmd_ == ts && cmd == ts) stats_adj_ts_ts_++;
    if (stats_prev_cmd_ == ts && cmd == st) stats_adj_ts_step_++;
    if (stats_prev_cmd_ == st && cmd == ts) stats_adj_step_ts_++;
    stats_prev_cmd_ = cmd;
  }
  // Per-node-type breakdown for the node-addressed commands: every
  // kSetNodeAttr* and kNodeMessage lead with the node's stream id as
  // an int32 right after the command byte.
  auto c = static_cast<SessionCommand>(cmd);
  bool node_addressed = c == SessionCommand::kNodeMessage
                        || (c >= SessionCommand::kSetNodeAttrFloat
                            && c <= SessionCommand::kSetNodeAttrCollisionMeshes)
                        || c == SessionCommand::kSetNodeAttrSpazDef
                        || c == SessionCommand::kSetNodeAttrSpazDefNull
                        || c == SessionCommand::kSetNodeAttrDepiction
                        || c == SessionCommand::kSetNodeAttrDepictionNull;
  if (node_addressed && out_command_.size() >= 2) {
    // The node id and (for set-attr) attr index are the first two ints
    // after the command byte, in whichever int encoding we're using.
    int32_t node_id = -1;
    int32_t attr_index = -1;
    bool have_attr = false;
    if (compact_) {
      const uint8_t* pos = &out_command_[1];
      const uint8_t* end = &out_command_[0] + out_command_.size();
      uint32_t v;
      if (ReadVarintAt(end, &pos, &v)) {
        node_id = UnZigZag(v);
        if (ReadVarintAt(end, &pos, &v)) {
          attr_index = UnZigZag(v);
          have_attr = true;
        }
      }
    } else if (out_command_.size() >= 5) {
      memcpy(&node_id, &out_command_[1], 4);
      if (out_command_.size() >= 9) {
        memcpy(&attr_index, &out_command_[5], 4);
        have_attr = true;
      }
    }
    if (node_id >= 0 && node_id < static_cast<int32_t>(nodes_.size())
        && nodes_[node_id]) {
      NodeType* type = nodes_[node_id]->type();
      stats_node_type_bytes_[type->name()] += size;
      if (c != SessionCommand::kNodeMessage && have_attr && attr_index >= 0
          && attr_index
                 < static_cast<int32_t>(type->attributes_by_index().size())) {
        if (NodeAttributeUnbound* attr = type->GetAttribute(attr_index)) {
          auto& entry = stats_attr_bytes_[type->name() + "." + attr->name()];
          entry.first += size;
          entry.second++;
        }
      }
    }
  }
}

void SessionStream::StatsMaybeLog_(millisecs_t real_time) {
  const millisecs_t kInterval = 5000;
  if (stats_last_log_time_ == 0) {
    stats_last_log_time_ = real_time;
    return;
  }
  millisecs_t elapsed = real_time - stats_last_log_time_;
  if (elapsed < kInterval) {
    return;
  }
  std::string out = "stream stats (" + std::to_string(elapsed) + "ms): shipped "
                    + std::to_string(stats_shipped_bytes_) + " B in "
                    + std::to_string(stats_shipped_messages_) + " msgs ("
                    + KBPerSec(stats_shipped_bytes_, elapsed)
                    + " KB/s raw); corrections "
                    + std::to_string(stats_correction_bytes_) + " B in "
                    + std::to_string(stats_correction_messages_) + " msgs ("
                    + KBPerSec(stats_correction_bytes_, elapsed) + " KB/s)";
  // Top command types by bytes.
  std::vector<int> cmds;
  int64_t cmd_total = 0;
  for (int i = 0; i < 256; ++i) {
    if (stats_cmd_bytes_[i] > 0) {
      cmds.push_back(i);
      cmd_total += stats_cmd_bytes_[i];
    }
  }
  std::sort(cmds.begin(), cmds.end(), [this](int a, int b) {
    return stats_cmd_bytes_[a] > stats_cmd_bytes_[b];
  });
  out += "; commands by type:";
  int shown = 0;
  for (int i : cmds) {
    if (shown++ >= 10) {
      break;
    }
    out += std::string(" ") + SessionCommandName(static_cast<uint8_t>(i)) + " "
           + KBPerSec(stats_cmd_bytes_[i], elapsed) + "KB/s ("
           + std::to_string(stats_cmd_bytes_[i] * 100
                            / std::max<int64_t>(cmd_total, 1))
           + "%, " + std::to_string(stats_cmd_counts_[i]) + ")";
  }
  // Node-addressed bytes by node type.
  std::vector<std::pair<std::string, int64_t>> types(
      stats_node_type_bytes_.begin(), stats_node_type_bytes_.end());
  std::sort(types.begin(), types.end(),
            [](auto& a, auto& b) { return a.second > b.second; });
  out += "; attrs/messages by node type:";
  shown = 0;
  for (auto& [name, bytes] : types) {
    if (shown++ >= 8) {
      break;
    }
    out += " " + name + " " + KBPerSec(bytes, elapsed) + "KB/s";
  }
  // And the individual attrs behind that.
  std::vector<std::pair<std::string, std::pair<int64_t, int64_t>>> attrs(
      stats_attr_bytes_.begin(), stats_attr_bytes_.end());
  std::sort(attrs.begin(), attrs.end(),
            [](auto& a, auto& b) { return a.second.first > b.second.first; });
  out += "; top attrs:";
  shown = 0;
  for (auto& [name, entry] : attrs) {
    if (shown++ >= 12) {
      break;
    }
    out += " " + name + " " + KBPerSec(entry.first, elapsed) + "KB/s("
           + std::to_string(entry.second) + "x, "
           + std::to_string(entry.first / std::max<int64_t>(entry.second, 1))
           + "B)";
  }
  out += "; framing adjacency: ts>ts " + std::to_string(stats_adj_ts_ts_)
         + ", ts>step " + std::to_string(stats_adj_ts_step_) + ", step>ts "
         + std::to_string(stats_adj_step_ts_);
  stats_adj_ts_ts_ = stats_adj_ts_step_ = stats_adj_step_ts_ = 0;
  // What each client connection actually put on the wire (all packet
  // types, resends included), raw and huffman-compressed.
  out += "; clients:";
  if (connections_to_clients_.empty()) {
    out += " none";
  }
  for (auto* conn : connections_to_clients_) {
    out += " [" + std::to_string(conn->id()) + "] "
           + KBPerSec(conn->TakeStatsBytesOutCompressed(), elapsed)
           + " KB/s wire (" + KBPerSec(conn->TakeStatsBytesOut(), elapsed)
           + " KB/s raw, " + std::to_string(conn->TakeStatsPacketsOut())
           + " pkts, resent " + std::to_string(conn->TakeStatsResendBytesOut())
           + " B;";
    if (int64_t dropped = conn->TakeStatsPacketsDropped()) {
      out += " dropped " + std::to_string(dropped) + " (injected loss);";
    }
    int64_t same_ms = conn->TakeStatsPacketsSameMs();
    auto types = conn->TakeStatsPacketTypes();
    std::vector<std::pair<int, Connection::PacketTypeStats>> tv(types.begin(),
                                                                types.end());
    std::sort(tv.begin(), tv.end(),
              [](auto& a, auto& b) { return a.second.count > b.second.count; });
    for (auto& [type, st] : tv) {
      const char* name =
          type == BA_SCENEPACKET_MESSAGE                   ? "msg"
          : type == BA_SCENEPACKET_MESSAGE_UNRELIABLE      ? "unreliable"
          : type == BA_SCENEPACKET_MESSAGE_UNRELIABLE_PART ? "unreliable-part"
          : type == BA_SCENEPACKET_KEEPALIVE               ? "keepalive"
                                                           : "other";
      out += std::string(" ") + name + " " + std::to_string(st.count) + "x avg "
             + std::to_string(st.bytes / std::max<int64_t>(st.count, 1)) + "B";
    }
    out += "; " + std::to_string(same_ms)
           + " pkts shared a ms with the previous; messages by type:";
    auto mtypes = conn->TakeStatsMessageTypes();
    std::vector<std::pair<int, Connection::PacketTypeStats>> mv(mtypes.begin(),
                                                                mtypes.end());
    std::sort(mv.begin(), mv.end(),
              [](auto& a, auto& b) { return a.second.count > b.second.count; });
    for (auto& [type, st] : mv) {
      out += " m" + std::to_string(type) + " " + std::to_string(st.count)
             + "x avg "
             + std::to_string(st.bytes / std::max<int64_t>(st.count, 1)) + "B";
    }
    out += ")";
  }
  g_core->logging->Log(LogName::kBaNetworking, LogLevel::kInfo, out);
  stats_last_log_time_ = real_time;
  memset(stats_cmd_bytes_, 0, sizeof(stats_cmd_bytes_));
  memset(stats_cmd_counts_, 0, sizeof(stats_cmd_counts_));
  stats_node_type_bytes_.clear();
  stats_attr_bytes_.clear();
  stats_correction_bytes_ = stats_correction_messages_ = 0;
  stats_shipped_bytes_ = stats_shipped_messages_ = 0;
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
// One integer field: a zigzag varint under the compact framing,
// otherwise a full int32.
void SessionStream::WriteInt_(int32_t value) {
  if (compact_) {
    AppendVarint(&out_command_, ZigZag(value));
  } else {
    auto size = out_command_.size();
    out_command_.resize(size + 4);
    memcpy(&out_command_[size], &value, 4);
  }
}

void SessionStream::WriteCommandInt32(SessionCommand cmd, int32_t value) {
  assert(out_command_.empty());
  out_command_.push_back(static_cast<uint8_t>(cmd));
  WriteInt_(value);
}

void SessionStream::WriteCommandInt32_2(SessionCommand cmd, int32_t value1,
                                        int32_t value2) {
  assert(out_command_.empty());
  out_command_.push_back(static_cast<uint8_t>(cmd));
  WriteInt_(value1);
  WriteInt_(value2);
}

void SessionStream::WriteCommandInt32_3(SessionCommand cmd, int32_t value1,
                                        int32_t value2, int32_t value3) {
  assert(out_command_.empty());
  out_command_.push_back(static_cast<uint8_t>(cmd));
  WriteInt_(value1);
  WriteInt_(value2);
  WriteInt_(value3);
}

void SessionStream::WriteCommandInt32_4(SessionCommand cmd, int32_t value1,
                                        int32_t value2, int32_t value3,
                                        int32_t value4) {
  assert(out_command_.empty());
  out_command_.push_back(static_cast<uint8_t>(cmd));
  WriteInt_(value1);
  WriteInt_(value2);
  WriteInt_(value3);
  WriteInt_(value4);
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
  // Length int, then the chars.
  WriteInt_(static_cast_check_fit<int32_t>(s.size()));
  if (!s.empty()) {
    out_command_.insert(out_command_.end(), s.begin(), s.end());
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
  for (size_t i = 0; i < count; ++i) {
    WriteInt_(vals[i]);
  }
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

  if (stats_enabled_) {
    stats_shipped_bytes_ += static_cast<int64_t>(out_message_.size());
    stats_shipped_messages_++;
  }
  // Send this message to all client-connections we're attached to.
  for (auto& connection : connections_to_clients_) {
    (*connection).SendReliableMessage(out_message_);
  }
  if (writing_replay_) {
    AddMessageToReplay(out_message_);
  }
  out_message_.clear();
  stats_prev_cmd_ = -1;
  last_cmd_offset_ = -1;
  last_cmd_id_ = -1;
  prev_cmd_offset_ = -1;
  prev_cmd_id_ = -1;
  last_time_step_delta_ = -1;
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

  std::vector<std::vector<uint8_t>> messages;
  host_session_->GetCorrectionMessages(blend, &messages);

  // Corrections go unreliable to peers that speak unreliable parts
  // (split as needed; the client reassembles and applies all-or-nothing
  // and only once it has processed the commands this accounts for). A
  // lost one is superseded by the next correction instead of stalling
  // the in-order reliable stream for a resend round trip. Older peers,
  // and BA_RELIABLE_CORRECTIONS (the A/B switch), keep reliable.
  for (auto& message : messages) {
    if (stats_enabled_) {
      stats_correction_bytes_ += static_cast<int64_t>(message.size());
      stats_correction_messages_++;
    }
    for (auto& connections_to_client : connections_to_clients_) {
      if (!reliable_corrections_
          && (*connections_to_client).PeerSupportsUnreliableParts()) {
        (*connections_to_client).SendUnreliableMessage(message);
      } else {
        (*connections_to_client).SendReliableMessage(message);
      }
    }
    if (writing_replay_) {
      AddMessageToReplay(message);
    }
  }
}

void SessionStream::BeginFold() {
  assert(!folding_);
  folding_ = true;
  fold_cmds_.clear();
}

void SessionStream::AbortFold() {
  assert(folding_);
  folding_ = false;
  std::vector<std::vector<uint8_t>> cmds;
  cmds.swap(fold_cmds_);
  for (auto& cmd : cmds) {
    out_command_ = cmd;
    EndCommand();
  }
}

void SessionStream::CommitFoldAnimCurve(
    Scene* scene, Node* curve, Node* globals, NodeAttributeUnbound* time_attr,
    NodeAttributeUnbound* in_attr, NodeAttributeUnbound* out_attr, Node* target,
    NodeAttributeUnbound* target_attr, int64_t offset, bool loop,
    const std::vector<int64_t>& times, const std::vector<float>& values) {
  assert(folding_);
  assert(times.size() == values.size());
  folding_ = false;
  fold_cmds_.clear();
  WriteCommand(SessionCommand::kAddAnimCurve);
  int32_t hdr[12] = {static_cast_check_fit<int32_t>(scene->stream_id()),
                     static_cast_check_fit<int32_t>(curve->type()->id()),
                     static_cast_check_fit<int32_t>(curve->stream_id()),
                     static_cast_check_fit<int32_t>(globals->stream_id()),
                     static_cast_check_fit<int32_t>(time_attr->index()),
                     static_cast_check_fit<int32_t>(in_attr->index()),
                     static_cast_check_fit<int32_t>(out_attr->index()),
                     static_cast_check_fit<int32_t>(target->stream_id()),
                     static_cast_check_fit<int32_t>(target_attr->index()),
                     static_cast_check_fit<int32_t>(offset),
                     loop ? 1 : 0,
                     static_cast_check_fit<int32_t>(times.size())};
  WriteInts32(12, hdr);
  if (!times.empty()) {
    std::vector<int32_t> t32(times.size());
    for (size_t i = 0; i < times.size(); ++i) {
      t32[i] = static_cast_check_fit<int32_t>(times[i]);
    }
    WriteInts32(t32.size(), t32.data());
    WriteFloats(values.size(), values.data());
  }
  EndCommand();
}

namespace {

// Read a zigzag varint from a finished command body.
auto ReadZigzag(const std::vector<uint8_t>& b, size_t* pos) -> int64_t {
  uint32_t v = 0;
  int shift = 0;
  while (true) {
    if (*pos >= b.size() || shift > 28) {
      throw Exception("corrupt command body");
    }
    uint8_t byte = b[(*pos)++];
    v |= static_cast<uint32_t>(byte & 0x7f) << shift;
    if (!(byte & 0x80)) {
      break;
    }
    shift += 7;
  }
  return static_cast<int32_t>(v >> 1) ^ -static_cast<int32_t>(v & 1);
}

}  // namespace

// Attr-set commands kAddNodeWithAttrs may carry: the client re-splits
// their bodies from a value-layout table (ClientSession's
// SkipPackedAttrValue_), so both lists must agree exactly.
auto IsPackableAttrCommand(uint8_t cmd) -> bool {
  switch (static_cast<SessionCommand>(cmd)) {
    case SessionCommand::kSetNodeAttrFloat:
    case SessionCommand::kSetNodeAttrInt32:
    case SessionCommand::kSetNodeAttrBool:
    case SessionCommand::kSetNodeAttrFloats:
    case SessionCommand::kSetNodeAttrInt32s:
    case SessionCommand::kSetNodeAttrString:
    case SessionCommand::kSetNodeAttrNode:
    case SessionCommand::kSetNodeAttrNodeNull:
    case SessionCommand::kSetNodeAttrNodes:
    case SessionCommand::kSetNodeAttrMaterials:
    case SessionCommand::kSetNodeAttrTexture:
    case SessionCommand::kSetNodeAttrTextureNull:
    case SessionCommand::kSetNodeAttrTextures:
    case SessionCommand::kSetNodeAttrSound:
    case SessionCommand::kSetNodeAttrSoundNull:
    case SessionCommand::kSetNodeAttrSounds:
    case SessionCommand::kSetNodeAttrMesh:
    case SessionCommand::kSetNodeAttrMeshNull:
    case SessionCommand::kSetNodeAttrMeshes:
    case SessionCommand::kSetNodeAttrCollisionMesh:
    case SessionCommand::kSetNodeAttrCollisionMeshNull:
    case SessionCommand::kSetNodeAttrCollisionMeshes:
    case SessionCommand::kSetNodeAttrSpazDef:
    case SessionCommand::kSetNodeAttrSpazDefNull:
    case SessionCommand::kSetNodeAttrDepiction:
    case SessionCommand::kSetNodeAttrDepictionNull:
      return true;
    default:
      return false;
  }
}

void SessionStream::CommitFoldAddNode(Node* node) {
  assert(folding_);
  // Expect exactly [AddNode(scene, type, id)][packable attr sets on
  // id...][NodeOnCreate(id)]; anything else goes out as it was.
  bool ok = fold_cmds_.size() >= 2;
  int64_t scene_id = -1;
  int64_t type_id = -1;
  int64_t id = node->stream_id();
  std::vector<size_t> body_starts;  // Per attr cmd: offset after node id.
  try {
    if (ok) {
      auto& first = fold_cmds_.front();
      auto& last = fold_cmds_.back();
      size_t pos = 1;
      ok = first[0] == static_cast<uint8_t>(SessionCommand::kAddNode);
      if (ok) {
        scene_id = ReadZigzag(first, &pos);
        type_id = ReadZigzag(first, &pos);
        ok = ReadZigzag(first, &pos) == id && pos == first.size();
      }
      if (ok) {
        pos = 1;
        ok = last[0] == static_cast<uint8_t>(SessionCommand::kNodeOnCreate)
             && ReadZigzag(last, &pos) == id && pos == last.size();
      }
      for (size_t i = 1; ok && i + 1 < fold_cmds_.size(); ++i) {
        auto& cmd = fold_cmds_[i];
        pos = 1;
        ok = IsPackableAttrCommand(cmd[0]) && ReadZigzag(cmd, &pos) == id;
        body_starts.push_back(pos);
      }
    }
  } catch (const std::exception&) {
    ok = false;
  }
  if (!ok) {
    AbortFold();
    return;
  }
  std::vector<std::vector<uint8_t>> cmds;
  cmds.swap(fold_cmds_);
  folding_ = false;
  WriteCommand(SessionCommand::kAddNodeWithAttrs);
  int32_t hdr[4] = {static_cast_check_fit<int32_t>(scene_id),
                    static_cast_check_fit<int32_t>(type_id),
                    static_cast_check_fit<int32_t>(id),
                    static_cast_check_fit<int32_t>(cmds.size() - 2)};
  WriteInts32(4, hdr);
  for (size_t i = 1; i + 1 < cmds.size(); ++i) {
    auto& cmd = cmds[i];
    out_command_.push_back(cmd[0]);
    out_command_.insert(out_command_.end(), cmd.begin() + body_starts[i - 1],
                        cmd.end());
  }
  EndCommand();
}

void SessionStream::EndCommand(bool is_time_set) {
  assert(!out_command_.empty());
  if (folding_) {
    // Held aside for CommitFoldAnimCurve / AbortFold.
    fold_cmds_.push_back(out_command_);
    out_command_.clear();
    return;
  }
  if (stats_enabled_) {
    StatsNoteCommand_();
  }

  int out_message_size;
  if (out_message_.empty()) {
    // Init the message if we're the first command on it.
    out_message_.resize(1);
    out_message_[0] = BA_MESSAGE_SESSION_COMMANDS;
    out_message_size = 1;
  } else {
    out_message_size = static_cast<int>(out_message_.size());
  }
  prev_cmd_offset_ = last_cmd_offset_;
  prev_cmd_id_ = last_cmd_id_;
  prev_cmd_stats_size_ = last_cmd_stats_size_;
  last_cmd_offset_ = out_message_size;
  last_cmd_id_ = out_command_[0];
  last_cmd_stats_size_ = stats_last_cmd_size_;

  if (compact_) {
    // Varint length, then the command.
    AppendVarint(&out_message_, static_cast<uint32_t>(out_command_.size()));
    out_message_.insert(out_message_.end(), out_command_.begin(),
                        out_command_.end());
  } else {
    out_message_.resize(out_message_size + 2
                        + out_command_.size());  // command length plus data

    auto val = static_cast<uint16_t>(out_command_.size());
    memcpy(&(out_message_[out_message_size]), &val, 2);
    memcpy(&(out_message_[out_message_size + 2]), &(out_command_[0]),
           out_command_.size());
  }

  // When attached to a host-session, send this message to clients if it's been
  // long enough. Also send off occasional correction packets.
  if (host_session_) {
    auto* appmode = classic::ClassicAppMode::GetSingleton();
    // Ship on a time-step command, but only once the foreground scene
    // has stepped since the last ship. The host advances base time on
    // every event-loop update (a few ms apart, irregular) as well as
    // at each 8ms sim step, and shipping on every time-set sent ~330
    // tiny packets/s per client, most carrying a 2-3ms time step and
    // nothing a client could act on (2026-09-07 measurement; UDP/IP
    // headers were half the wire cost). The time-set that follows the
    // step timers lands in the same update, so the gameplay scene's
    // commands still go out the moment its step is done; other scenes
    // (the session scene: UI, mostly idle) step on their own timers
    // whose phase may not match, and their commands ride with the next
    // foreground ship rather than forcing one of their own -- unless
    // nothing has shipped for a couple of steps (paused activity, no
    // activity), in which case they go out on their own.
    millisecs_t real_time = g_core->AppTimeMillisecs();
    millisecs_t diff = real_time - last_send_time_;
    bool due =
        foreground_step_pending_
        || (other_step_pending_
            && time_ - last_ship_base_time_ >= 2 * kGameStepMilliseconds);
    if (is_time_set && due && diff >= app_mode_->buffer_time()) {
      foreground_step_pending_ = other_step_pending_ = false;
      last_ship_base_time_ = time_;
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
      if (stats_enabled_) {
        StatsMaybeLog_(real_time);
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

auto SessionStream::IsValidSpazDef(SpazDef* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(spaz_defs_.size())
          && spaz_defs_[n->stream_id()] == n);
}

auto SessionStream::IsValidDepiction(SceneDepiction* n) -> bool {
  if (!host_session_) {
    return true;  // We don't build lists in this mode so can't verify this.
  }
  return (n != nullptr && n->stream_id() >= 0
          && n->stream_id() < static_cast<int64_t>(depictions_.size())
          && depictions_[n->stream_id()] == n);
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
  if (merge_steps_ && prev_cmd_offset_ > 0 && last_time_step_delta_ >= 0
      && last_cmd_id_ == static_cast<int>(SessionCommand::kStepSceneGraph)
      && prev_cmd_id_ == static_cast<int>(SessionCommand::kBaseTimeStep)) {
    // [time step][scene step] then this time step: one command carrying
    // all three (kTimeStepSceneGraphAndTime). Wire-only: the client
    // expands it back into the two commands on receipt.
    out_message_.resize(static_cast<size_t>(prev_cmd_offset_));
    if (stats_enabled_) {
      auto st = static_cast<int>(SessionCommand::kStepSceneGraph);
      auto ts = static_cast<int>(SessionCommand::kBaseTimeStep);
      stats_cmd_bytes_[st] -= last_cmd_stats_size_;
      stats_cmd_counts_[st]--;
      stats_cmd_bytes_[ts] -= prev_cmd_stats_size_;
      stats_cmd_counts_[ts]--;
      stats_prev_cmd_ = -1;
    }
    WriteCommandInt64_3(SessionCommand::kTimeStepSceneGraphAndTime,
                        last_time_step_delta_, last_step_scene_id_, diff);
    last_time_step_delta_ = -1;
    time_ = t;
    EndCommand(true);
    return;
  }
  if (merge_steps_ && last_cmd_offset_ > 0
      && last_cmd_id_ == static_cast<int>(SessionCommand::kStepSceneGraph)) {
    // The last thing in the unshipped message is a scene step: fold it
    // and this time step into one command (kStepSceneGraphAndTime). The
    // client performs the same two operations in the same order, so
    // this is purely 2 bytes less framing per sim step.
    out_message_.resize(static_cast<size_t>(last_cmd_offset_));
    if (stats_enabled_) {
      auto st = static_cast<int>(SessionCommand::kStepSceneGraph);
      stats_cmd_bytes_[st] -= stats_last_cmd_size_;
      stats_cmd_counts_[st]--;
      stats_prev_cmd_ = -1;
    }
    WriteCommandInt64_2(SessionCommand::kStepSceneGraphAndTime,
                        last_step_scene_id_, diff);
    last_time_step_delta_ = -1;
    time_ = t;
    EndCommand(true);
    return;
  }
  WriteCommandInt64(SessionCommand::kBaseTimeStep, diff);
  last_time_step_delta_ = diff;
  time_ = t;
  EndCommand(true);
}

void SessionStream::AddScene(Scene* s) {
  // Host mode.
  if (host_session_) {
    Add(s, &scenes_, &free_indices_scene_graphs_);
    s->SetOutputStream(this);
    // Host scenes run under the protocol we host.
    s->set_protocol_version(app_mode_->host_protocol_version());
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
  last_step_scene_id_ = s->stream_id();
  if (s == classic::ClassicAppMode::GetActiveOrFatal()->GetForegroundScene()) {
    foreground_step_pending_ = true;
  } else {
    other_step_pending_ = true;
  }
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
  // Package-housed assets go as compact indexed refs (protocol 39+;
  // everything we host is); local non-package assets keep the legacy
  // string form.
  if (TryAddAssetIndexed_(SessionCommand::kAddTextureIndexed, sg->stream_id(),
                          t->stream_id(), t->name(), "textures",
                          AssetBucketKind::kTextures)) {
    return;
  }
  WriteCommandInt64_2(SessionCommand::kAddTexture, sg->stream_id(),
                      t->stream_id());
  WriteString(base::AssetNameCompat::ToLegacy(t->name()));
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
  // See AddTexture: indexed for package-housed, legacy string otherwise.
  if (TryAddAssetIndexed_(SessionCommand::kAddMeshIndexed, sg->stream_id(),
                          t->stream_id(), t->name(), "meshes",
                          AssetBucketKind::kMeshes)) {
    return;
  }
  WriteCommandInt64_2(SessionCommand::kAddMesh, sg->stream_id(),
                      t->stream_id());
  WriteString(base::AssetNameCompat::ToLegacy(t->name()));
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
  // See AddTexture: indexed for package-housed, legacy string otherwise.
  if (TryAddAssetIndexed_(SessionCommand::kAddSoundIndexed, sg->stream_id(),
                          t->stream_id(), t->name(), "audio",
                          AssetBucketKind::kAudio)) {
    return;
  }
  WriteCommandInt64_2(SessionCommand::kAddSound, sg->stream_id(),
                      t->stream_id());
  WriteString(base::AssetNameCompat::ToLegacy(t->name()));
  EndCommand();
}

void SessionStream::RemoveSound(SceneSound* t) {
  assert(IsValidSound(t));
  WriteCommandInt64(SessionCommand::kRemoveSound, t->stream_id());
  Remove(t, &sounds_, &free_indices_sounds_);
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
  // See AddTexture: indexed for package-housed, legacy string
  // otherwise. Collision meshes index against the constant bucket
  // (their package home; asset-packages #26) though their
  // legacy-name mapping is kind 'meshes'.
  if (TryAddAssetIndexed_(SessionCommand::kAddCollisionMeshIndexed,
                          sg->stream_id(), t->stream_id(), t->name(), "meshes",
                          AssetBucketKind::kConstant)) {
    return;
  }
  WriteCommandInt64_2(SessionCommand::kAddCollisionMesh, sg->stream_id(),
                      t->stream_id());
  WriteString(base::AssetNameCompat::ToLegacy(t->name()));
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

// Live spaz defs (or depictions) on a hosted stream past which their
// Add warns (once); a game normally needs one per distinct appearance
// (or name/icon) in play.
const size_t kLiveSpazDefsWarnThreshold = 64;
const size_t kLiveDepictionsWarnThreshold = 256;

void SessionStream::AddSpazDef(SpazDef* d) {
  if (host_session_) {
    Add(d, &spaz_defs_, &free_indices_spaz_defs_);
    // Every live definition costs its json on the stream and in every
    // late joiner's baseline; game code is expected to reuse one per
    // look (the session player's cloud_spaz_def), so a pile-up means
    // something is minting them per spawn.
    size_t live = spaz_defs_.size() - free_indices_spaz_defs_.size();
    if (live > kLiveSpazDefsWarnThreshold) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                  "Session stream has " + std::to_string(live)
                      + " live spaz defs; are they being minted per"
                        " spawn instead of reused per look?");
    }
  } else {
    assert(d && d->stream_id() != -1);
  }
  Scene* sg = d->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddSpazDef, sg->stream_id(),
                      d->stream_id());
  WriteString(d->json());
  EndCommand();
}

void SessionStream::RemoveSpazDef(SpazDef* d) {
  assert(IsValidSpazDef(d));
  WriteCommandInt64(SessionCommand::kRemoveSpazDef, d->stream_id());
  Remove(d, &spaz_defs_, &free_indices_spaz_defs_);
  EndCommand();
}

void SessionStream::AddDepiction(SceneDepiction* d) {
  if (host_session_) {
    Add(d, &depictions_, &free_indices_depictions_);
    // As with spaz defs: one per distinct name/icon in play, reused.
    size_t live = depictions_.size() - free_indices_depictions_.size();
    if (live > kLiveDepictionsWarnThreshold) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                  "Session stream has " + std::to_string(live)
                      + " live depictions; are they being reused rather"
                        " than made per use?");
    }
  } else {
    assert(d && d->stream_id() != -1);
  }
  Scene* sg = d->scene();
  assert(IsValidScene(sg));
  WriteCommandInt64_2(SessionCommand::kAddDepiction, sg->stream_id(),
                      d->stream_id());
  WriteString(d->json());
  EndCommand();
}

void SessionStream::RemoveDepiction(SceneDepiction* d) {
  assert(IsValidDepiction(d));
  WriteCommandInt64(SessionCommand::kRemoveDepiction, d->stream_id());
  Remove(d, &depictions_, &free_indices_depictions_);
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
      for ([[maybe_unused]] auto val : vals) {
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
    for ([[maybe_unused]] auto val : vals) {
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

void SessionStream::SetNodeAttr(const NodeAttribute& attr, SpazDef* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidSpazDef(val));
    // A definition built in the session scene (a player's cloud
    // profile look, made by the lobby before any activity has them) is
    // usable from every scene in the session: it outlives every
    // activity and HostSession::DumpFullState adds it before any
    // activity's nodes. Activity-scene ones stay confined to their own
    // scene since their stream id is recycled at activity teardown
    // while a foreign node could still reference them.
    bool session_scene =
        host_session_ != nullptr && val->scene() == host_session_->scene();
    if (attr.node->scene() != val->scene() && !session_scene) {
      throw Exception("spaz-def/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrSpazDef,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrSpazDefNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                SceneDepiction* val) {
  if (val) {
    assert(IsValidNode(attr.node));
    assert(IsValidDepiction(val));
    // Scoping as for spaz defs (session-scene ones work everywhere).
    bool session_scene =
        host_session_ != nullptr && val->scene() == host_session_->scene();
    if (attr.node->scene() != val->scene() && !session_scene) {
      throw Exception("depiction/node are from different scenes");
    }
    WriteCommandInt64_3(SessionCommand::kSetNodeAttrDepiction,
                        attr.node->stream_id(), attr.index(), val->stream_id());
  } else {
    WriteCommandInt64_2(SessionCommand::kSetNodeAttrDepictionNull,
                        attr.node->stream_id(), attr.index());
  }
  EndCommand();
}

void SessionStream::SetNodeAttr(const NodeAttribute& attr,
                                const std::vector<SceneTexture*>& vals) {
  assert(IsValidNode(attr.node));
  if (g_buildconfig.debug_build()) {
    for ([[maybe_unused]] auto val : vals) {
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
    for ([[maybe_unused]] auto val : vals) {
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
    for ([[maybe_unused]] auto val : vals) {
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
    for ([[maybe_unused]] auto val : vals) {
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

void SessionStream::EmitInputDeviceFeedback(int player_id,
                                            const std::string& json_payload) {
  WriteCommandInt32(SessionCommand::kInputDeviceFeedback, player_id);
  WriteString(json_payload);
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
                                     float tint2_g, float tint2_b,
                                     float tint3_r, float tint3_g,
                                     float tint3_b) {
  assert(IsValidTexture(texture));
  assert(IsValidTexture(tint_texture));
  assert(IsValidScene(texture->scene()));
  assert(IsValidScene(tint_texture->scene()));
  WriteCommandInt64_2(SessionCommand::kScreenMessageTop, texture->stream_id(),
                      tint_texture->stream_id());
  WriteString(val);
  // (We only ever write at kProtocolVersionMax, which carries tint3;
  // see kProtocolVersionTint3.)
  float f[12];
  f[0] = r;
  f[1] = g;
  f[2] = b;
  f[3] = tint_r;
  f[4] = tint_g;
  f[5] = tint_b;
  f[6] = tint2_r;
  f[7] = tint2_g;
  f[8] = tint2_b;
  f[9] = tint3_r;
  f[10] = tint3_g;
  f[11] = tint3_b;
  WriteFloats(12, f);
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

void SessionStream::ScreenMessageTopDepiction(const std::string& val, float r,
                                              float g, float b,
                                              SceneDepiction* depiction) {
  assert(IsValidDepiction(depiction));
  WriteCommandInt64(SessionCommand::kScreenMessageTopDepiction,
                    depiction->stream_id());
  WriteString(val);
  float color[3];
  color[0] = r;
  color[1] = g;
  color[2] = b;
  WriteFloats(3, color);
  EndCommand();
}

void SessionStream::DeclareAssetPackages(
    const std::vector<std::string>& table) {
  // One tiny command per entry (the command framing has a uint16 size
  // cap, so a single monolithic table command would bound universe
  // size). The explicit (index, total) pair lets readers detect a fresh
  // table start and know when the declaration is complete.
  auto total = static_cast<int32_t>(table.size());
  for (int32_t i = 0; i < total; ++i) {
    WriteCommandInt32_2(SessionCommand::kDeclareAssetPackage, i, total);
    WriteString(table[i]);
    EndCommand();
  }
  // Retain: subsequent asset adds index against this.
  declared_packages_ = table;

  // Host recordings know their universe here (this is the live output
  // stream); hand it to the replay writer for the file header. (Client
  // recordings feed the writer from ClientSession instead, since their
  // table is only known once the incoming baseline finishes parsing.)
  if (writing_replay_ && replay_writer_) {
    replay_writer_->SetAssetPackageTable(table);
  }
}

auto SessionStream::TryAddAssetIndexed_(SessionCommand cmd, int64_t scene_id,
                                        int64_t stream_id,
                                        const std::string& name,
                                        const char* legacy_kind,
                                        AssetBucketKind bucket_kind) -> bool {
  // Streams with no declared package table don't carry indexed refs at
  // all (e.g. the temp stream a replay builds for its seek-state
  // snapshot) -- fall straight back to the legacy string form. This
  // also keeps the out-of-universe warning below meaningful (it fires
  // only for a real table-bearing stream).
  if (declared_packages_.empty()) {
    return false;
  }

  // Map possibly-legacy bare names into package space the same way the
  // load path does; genuinely local names come back unqualified and
  // stay on the legacy string form.
  std::string qualified = base::AssetNameCompat::FromLegacy(name, legacy_kind);
  auto colon_pos = qualified.find(':');
  if (colon_pos == std::string::npos) {
    return false;
  }
  std::string apverid = qualified.substr(0, colon_pos);
  std::string logical_path = qualified.substr(colon_pos + 1);

  // Package must be in our declared table (the session universe).
  auto pkg_it =
      std::find(declared_packages_.begin(), declared_packages_.end(), apverid);
  if (pkg_it == declared_packages_.end()) {
    // Out-of-universe package refs are host-side bugs per the fixed-
    // universe design (asset-packages #36); make noise but keep the
    // stream functional via the self-describing legacy form.
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                "Asset '" + qualified
                    + "' is outside the session's package universe;"
                      " emitting non-indexed. This indicates a host-side"
                      " bug (see asset-packages decision #36).");
    return false;
  }
  auto pkg_idx = static_cast<int32_t>(pkg_it - declared_packages_.begin());

  auto* registry = g_base->assets->package_registry();
  std::string bucket_id;
  switch (bucket_kind) {
    case AssetBucketKind::kTextures:
      bucket_id = registry->LookupTextureBucketId(apverid);
      break;
    case AssetBucketKind::kAudio:
      bucket_id = registry->LookupAudioBucketId(apverid);
      break;
    case AssetBucketKind::kMeshes:
      bucket_id = registry->LookupMeshBucketId(apverid);
      break;
    case AssetBucketKind::kConstant:
      bucket_id = registry->LookupConstantBucketId(apverid);
      break;
  }
  if (bucket_id.empty()) {
    return false;
  }

  auto cache_key = apverid + '\n' + bucket_id;
  auto cache_it = asset_index_keys_cache_.find(cache_key);
  if (cache_it == asset_index_keys_cache_.end()) {
    cache_it = asset_index_keys_cache_
                   .emplace(cache_key, registry->BucketLogicalPathsSorted(
                                           apverid, bucket_id))
                   .first;
  }
  auto& keys = cache_it->second;
  auto key_it = std::lower_bound(keys.begin(), keys.end(), logical_path);
  if (key_it == keys.end() || *key_it != logical_path) {
    return false;
  }

  WriteCommandInt32_4(cmd, static_cast_check_fit<int32_t>(scene_id),
                      static_cast_check_fit<int32_t>(stream_id), pkg_idx,
                      static_cast<int32_t>(key_it - keys.begin()));
  EndCommand();
  return true;
}

auto SessionStream::GetSoundID(SceneSound* s) -> int64_t {
  assert(IsValidSound(s));
  return s->stream_id();
}

auto SessionStream::GetMaterialID(Material* m) -> int64_t {
  assert(IsValidMaterial(m));
  return m->stream_id();
}

auto SessionStream::GetSpazDefID(SpazDef* d) -> int64_t {
  assert(IsValidSpazDef(d));
  return d->stream_id();
}

auto SessionStream::GetDepictionID(SceneDepiction* d) -> int64_t {
  assert(IsValidDepiction(d));
  return d->stream_id();
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
