// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/client_session.h"

#include <algorithm>
#include <functional>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

#include "ballistica/base/assets/asset_package_registry.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/audio/audio.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/screen_messages.h"
#include "ballistica/base/input/device/input_device.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/networking/networking.h"
#include "ballistica/base/support/lang_str.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/dynamics/material/material.h"
#include "ballistica/scene_v1/dynamics/material/material_component.h"
#include "ballistica/scene_v1/dynamics/rigid_body.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/scene_v1/support/scene_depiction.h"
#include "ballistica/scene_v1/support/scene_v1_input_device_delegate.h"
#include "ballistica/scene_v1/support/session_stream.h"
#include "ballistica/scene_v1/support/spaz_def.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::scene_v1 {

// Resolve a lang-str-tagged wire value (see kLangStrWireTag*) to flat
// display text for transient surfaces (screen-messages): the string to
// show plus whether it is literal (bypasses the legacy resource-string
// compile at draw). LangStr refs bind against the stream's declared
// package table.
//
// SPECIAL CASE -- do not copy this parse-and-evaluate shape to new
// ingest points. Binding and evaluating wire refs with no resolve step
// is only valid because stream consumption implies a verified context:
// net sessions sit behind the arrive-ready prep contract (unprepped
// connects to lang-str-era hosts are refused at the handshake) and
// replay playback is gated by its own pre-playback prep. Out-of-context
// refs fail visibly (LANGSTR_ERROR) by design -- they indicate a
// host-side bug -- and untrusted stream data must never be able to
// trigger client-side resolve/download machinery. New consumers of
// wire LangStrs must establish an equivalent verified context (see the
// D28 trust model + D33 in docs/initiatives/strings-asset-migration.md).
static auto EvalLangStrWireValue_(const std::string& val,
                                  const std::vector<std::string>& package_table)
    -> std::pair<std::string, bool> {
  switch (val[0]) {
    case kLangStrWireTagLiteral:
      return {val.substr(1), true};
    case kLangStrWireTagLegacyJson:
      // The legacy compile happens at draw (and stays
      // language-change-responsive there).
      return {val.substr(1), false};
    default: {
      auto parsed = base::LangStr::FromJson(std::string_view(val).substr(1),
                                            &package_table);
      if (!parsed.has_value()) {
        g_core->logging->Log(
            LogName::kBaNetworking, LogLevel::kWarning,
            "Error parsing lang-str wire value: " + parsed.error());
        return {"LANGSTR_ERROR:" + parsed.error(), true};
      }
      return {(*parsed)->Evaluate(), true};
    }
  }
}

// Ceiling on how much of a feedback payload we will attempt to parse.
// Wire data is untrusted and this sits far above any legitimate payload
// (the common one is two bytes: '{}').
constexpr size_t kFeedbackPayloadMaxBytes{512};

// How many distinct unrecognized type codes we remember for once-only
// logging. Bounded on purpose: this set is fed directly by untrusted
// wire data, so an unbounded one is a slow leak a bad host could drive
// at will -- and it grows whether or not anyone is listening at debug
// level.
constexpr size_t kMaxRememberedUnknownTypes{16};

// Longest type code we will even store for logging purposes.
constexpr size_t kMaxTypeCodeLength{16};

// Note an unrecognized feedback type, once per distinct code.
//
// Debug level and nothing more, deliberately. An unknown type here means
// the sender is a newer build (or a replay written by one) that knows an
// event we do not -- entirely expected as the vocabulary grows, and not
// a problem worth shouting about. The case that DOES deserve a fuss is a
// type defined locally that some backend forgot to handle, and that is
// caught at compile time by the static_asserts on the profile and motor
// tables rather than at runtime.
//
// Deliberately not BA_LOG_ONCE: that fires once per *call site*, so the
// first unknown code ever seen would silently swallow every different
// one after it -- the opposite of what is wanted when the whole point is
// learning which unknown types are showing up.
static void ReportUnknownFeedbackType_(std::string_view code) {
  assert(g_base->InLogicThread());
  static std::set<std::string, std::less<>> reported;
  if (reported.size() >= kMaxRememberedUnknownTypes
      || code.size() > kMaxTypeCodeLength || reported.contains(code)) {
    return;
  }
  auto code_str = std::string(code);
  reported.insert(code_str);
  g_core->logging->Log(LogName::kBaInput, LogLevel::kDebug, [&code_str] {
    return "Ignoring input-device feedback with unrecognized type '" + code_str
           + "'.";
  });
}

void ClientSession::HandleInputDeviceFeedback_(int32_t player_id,
                                               const std::string& payload) {
  assert(g_base->InLogicThread());

  // Find whichever of our local devices (if any) currently drive this
  // player. Done *before* parsing: the stream is a broadcast, so most
  // events belong to somebody else's player and should cost a device
  // scan and nothing more.
  //
  // Note this is also what keeps the feature app-mode agnostic. The
  // delegate type is chosen by the active app-mode
  // (Input::AddInputDevice), so under any other app-mode the cast simply
  // fails, nothing matches, and feedback is inert rather than wrong.
  std::vector<base::InputDevice*> targets;
  for (auto* device : g_base->input->GetInputDevices()) {
    auto* delegate =
        dynamic_cast<SceneV1InputDeviceDelegate*>(&device->delegate());

    // Require an actual attachment rather than trusting the id alone.
    // player_id arrives off the wire, so a host sending the detached
    // sentinel (-1) would otherwise match every idle device at once.
    if (delegate != nullptr && delegate->GetRemotePlayer() != nullptr
        && delegate->remote_player_id() == player_id) {
      targets.push_back(device);
    }
  }
  if (targets.empty()) {
    return;
  }

  auto doc = JsonDoc::Parse(payload, {.max_bytes = kFeedbackPayloadMaxBytes});
  if (!doc.has_value()) {
    BA_LOG_ONCE(LogName::kBaInput, LogLevel::kDebug,
                "Ignoring unparsable input-device feedback payload.");
    return;
  }
  JsonRef root = doc->root();

  // Every key is optional and anything absent, malformed, or unknown
  // falls back to its client-side default. That is what lets the payload
  // grow over time without an older build losing the effect entirely --
  // and what lets the feel of a bare '{}' be retuned later without
  // touching already-shipped game code.
  // Absent means the default type, which is why the commonest event
  // ships as a bare '{}'.
  auto type = base::FeedbackEvent::kDefaultType;
  if (auto code = root["e"].as_string()) {
    auto parsed = code->size() == 1
                      ? base::FeedbackEvent::TypeFromCode((*code)[0])
                      : std::nullopt;
    if (!parsed.has_value()) {
      // Unrecognized types are dropped rather than approximated. A newer
      // build introducing a type is expected to be fine with older ones
      // feeling nothing for it (decision D6).
      ReportUnknownFeedbackType_(*code);
      return;
    }
    type = *parsed;
  }

  // Note there is nothing else to read. The payload carries an event
  // type and nothing more -- how strong and how long are each backend's
  // decisions, so a host cannot dictate them. That also means there are
  // no caller-supplied magnitudes to clamp here, which removes a whole
  // class of untrusted-number handling this ingest point used to need.
  auto event = base::FeedbackEvent{type};

  for (auto* device : targets) {
    device->ApplyFeedback(event);
  }
}

ClientSession::ClientSession() { ClearSessionObjs(); }

void ClientSession::Reset(bool rewind) {
  assert(!shutting_down_);
  OnReset(rewind);
}

void ClientSession::OnReset(bool rewind) {
  ClearSessionObjs();
  target_base_time_millisecs_ = 0.0;
  base_time_millisecs_ = 0;
}

void ClientSession::ClearSessionObjs() {
  scenes_.clear();
  nodes_.clear();
  textures_.clear();
  meshes_.clear();
  sounds_.clear();
  collision_meshes_.clear();
  materials_.clear();
  // Spaz defs and depictions live in lists too; a session reset's new
  // baseline re-adds them under the same ids (found by a client
  // crashing on the stress test's round rollover, 2026-09-07).
  spaz_defs_.clear();
  depictions_.clear();
  commands_pending_.clear();
  commands_.clear();
  base_time_buffered_ = 0;
  asset_package_table_.clear();
  asset_index_keys_cache_.clear();
}

auto ClientSession::ResolveIndexedAssetRef_(int32_t pkg_index,
                                            int32_t asset_index,
                                            AssetBucketKind bucket_kind)
    -> std::string {
  if (pkg_index < 0
      || pkg_index >= static_cast<int32_t>(asset_package_table_.size())) {
    throw Exception("indexed asset ref has invalid package index "
                    + std::to_string(pkg_index) + " (table size "
                    + std::to_string(asset_package_table_.size()) + ")");
  }
  const std::string& apverid = asset_package_table_[pkg_index];

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
    // Hitting this means the arrive-ready prep contract was violated
    // somewhere (the package should have been resolved pre-join);
    // assets hard-fail by design, and the session error carries the
    // diagnostics.
    throw Exception("indexed asset ref package '" + apverid
                    + "' has no registered bucket for kind "
                    + std::to_string(static_cast<int>(bucket_kind)) + ". ["
                    + registry->DebugDescribePackage(apverid) + "]");
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
  if (asset_index < 0 || asset_index >= static_cast<int32_t>(keys.size())) {
    throw Exception("indexed asset ref has invalid asset index "
                    + std::to_string(asset_index) + " for " + apverid + " "
                    + bucket_id + " (key count " + std::to_string(keys.size())
                    + ")");
  }
  std::string name = apverid + ':' + keys[asset_index];
  g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug,
                       [&name, pkg_index, asset_index] {
                         return "ClientSession: indexed asset ref ("
                                + std::to_string(pkg_index) + ","
                                + std::to_string(asset_index) + ") -> " + name;
                       });
  return name;
}

auto ClientSession::DoesFillScreen() const -> bool {
  // Look for any scene that has something that covers the background.
  // NOLINTNEXTLINE(readability-use-anyofallof)
  for (const auto& scene : scenes_) {
    if ((scene.exists()) && (*scene).has_bg_cover()) {
      return true;
    }
  }
  return false;
}

void ClientSession::Draw(base::FrameDef* f) {
  // Just go through and draw all of our scenes.
  for (auto&& i : scenes_) {
    // NOTE - here we draw scenes in the order they were created, but
    // in a host-session we draw session first followed by activities
    // (that should be the same order in both cases, but just something to keep
    // in mind...)
    if (i.exists()) {
      i->Draw(f);
    }
  }
}

auto ClientSession::ReadByte() -> uint8_t {
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - 1) {
    throw Exception("state read error");
  }
  return *(current_cmd_ptr_++);
}

auto ClientSession::ReadVarint_() -> uint32_t {
  const uint8_t* end = &(current_cmd_[0]) + current_cmd_.size();
  uint32_t result = 0;
  int shift = 0;
  while (true) {
    if (current_cmd_ptr_ >= end || shift > 28) {
      throw Exception("state read error");
    }
    uint8_t b = *(current_cmd_ptr_++);
    result |= static_cast<uint32_t>(b & 0x7f) << shift;
    if (!(b & 0x80)) {
      return result;
    }
    shift += 7;
  }
}

auto ClientSession::ReadInt32() -> int32_t {
  if (compact_stream()) {
    uint32_t v = ReadVarint_();
    return static_cast<int32_t>(v >> 1) ^ -static_cast<int32_t>(v & 1);
  }
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - 4) {
    throw Exception("state read error");
  }
  int32_t val;
  memcpy(&val, current_cmd_ptr_, sizeof(val));
  current_cmd_ptr_ += 4;
  return val;
}

auto ClientSession::ReadFloat() -> float {
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - 4) {
    throw Exception("state read error");
  }
  float val;
  memcpy(&val, current_cmd_ptr_, 4);
  current_cmd_ptr_ += 4;
  return val;
}

void ClientSession::ReadFloats(int count, float* vals) {
  int size = 4 * count;
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - size) {
    throw Exception("state read error");
  }
  memcpy(vals, current_cmd_ptr_, static_cast<size_t>(size));
  current_cmd_ptr_ += size;
}

void ClientSession::ReadInt32s(int count, int32_t* vals) {
  if (compact_stream()) {
    for (int i = 0; i < count; ++i) {
      vals[i] = ReadInt32();
    }
    return;
  }
  int size = 4 * count;
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - size) {
    throw Exception("state read error");
  }
  memcpy(vals, current_cmd_ptr_, static_cast<size_t>(size));
  current_cmd_ptr_ += size;
}

void ClientSession::ReadChars(int count, char* vals) {
  int size = count;
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - size) {
    throw Exception("state read error");
  }
  memcpy(vals, current_cmd_ptr_, static_cast<size_t>(size));
  current_cmd_ptr_ += size;
}

void ClientSession::ReadInt32_3(int32_t* vals) { ReadInt32s(3, vals); }

void ClientSession::ReadInt32_4(int32_t* vals) { ReadInt32s(4, vals); }

void ClientSession::ReadInt32_2(int32_t* vals) { ReadInt32s(2, vals); }

auto ClientSession::ReadString() -> std::string {
  int32_t size = ReadInt32();
  if (size < 0) {
    throw Exception("state read error");
  }
  std::vector<char> buffer(static_cast<size_t>(size + 1));
  if (current_cmd_ptr_ > &(current_cmd_[0]) + current_cmd_.size() - size) {
    throw Exception("state read error");
  }
  memcpy(&(buffer[0]), current_cmd_ptr_, static_cast<size_t>(size));
  current_cmd_ptr_ += size;
  return &(buffer[0]);
}

void ClientSession::Update(int time_advance_millisecs, double time_advance) {
  if (shutting_down_) {
    return;
  }

  // Allow replays to modulate speed, etc.
  // Also plug in our more exact time-advance here instead of the old int one.
  double actual_advance_millisecs =
      GetActualTimeAdvanceMillisecs(time_advance * 1000.0);

  target_base_time_millisecs_ += actual_advance_millisecs * consume_rate_;

  try {
    // Read and run all events up to our target time.
    while (static_cast<double>(base_time_millisecs_)
           < target_base_time_millisecs_) {
      // If we need to do something explicit to keep messages flowing in.
      // (informing the replay thread to feed us more, etc.).
      FetchMessages();

      // If we've got another command on the list, pull it and run it.
      if (!commands_.empty()) {
        // Debugging: if this was previously pointed at a buffer, make sure we
        // went exactly to the end.
        if (g_buildconfig.debug_build()) {
          if (current_cmd_ptr_ != nullptr) {
            if (current_cmd_ptr_ != &(current_cmd_[0]) + current_cmd_.size()) {
              g_core->logging->Log(
                  LogName::kBaNetworking, LogLevel::kError,
                  "SIZE ERROR FOR CMD "
                      + std::to_string(static_cast<int>(current_cmd_[0]))
                      + " expected " + std::to_string(current_cmd_.size())
                      + " got "
                      + std::to_string(current_cmd_ptr_ - &(current_cmd_[0])));
            }
          }
          assert(current_cmd_ptr_ == current_cmd_.data() + current_cmd_.size());
        }
        current_cmd_ = commands_.front();
        commands_.pop_front();
        current_cmd_ptr_ = &(current_cmd_[0]);
      } else {
        // Let the subclass know this happened. Replays may want to pause
        // playback until more data comes in but things like net-play may want
        // to just soldier on and skip ahead once data comes in.
        OnCommandBufferUnderrun();
        return;
      }

      auto cmd = static_cast<SessionCommand>(ReadByte());

      switch (cmd) {
        case SessionCommand::kBaseTimeStep: {
          int32_t stepsize = ReadInt32();
          BA_PRECONDITION(stepsize > 0);
          if (stepsize > 10000) {
            throw Exception(
                "got abnormally large stepsize; probably a corrupt stream");
          }
          base_time_buffered_ -= stepsize;
          BA_PRECONDITION(base_time_buffered_ >= 0);
          base_time_millisecs_ += stepsize;
          break;
        }
        case SessionCommand::kDynamicsCorrection: {
          bool blend = current_cmd_[1];
          if (compact_stream()) {
            // Compact layout (kProtocolVersionCompactCorrections); see
            // Scene::GetCorrectionMessageCompact_.
            const uint8_t* p = current_cmd_.data() + 2;
            const uint8_t* end = current_cmd_.data() + current_cmd_.size();
            auto read_byte = [&]() -> uint8_t {
              if (p >= end) {
                throw Exception("truncated compact correction");
              }
              return *p++;
            };
            auto read_varint = [&]() -> uint32_t {
              uint32_t result = 0;
              int shift = 0;
              while (true) {
                if (shift > 28) {
                  throw Exception("corrupt compact correction");
                }
                uint8_t b = read_byte();
                result |= static_cast<uint32_t>(b & 0x7f) << shift;
                if (!(b & 0x80)) {
                  return result;
                }
                shift += 7;
              }
            };
            uint32_t node_count = read_varint();
            for (uint32_t i = 0; i < node_count; i++) {
              uint32_t node_id = read_varint();
              int body_count = read_byte();
              Node* n =
                  (node_id < nodes_.size()) ? nodes_[node_id].get() : nullptr;
              for (int j = 0; j < body_count; j++) {
                int bodyid = read_byte();
                RigidBody* b = n ? n->GetRigidBody(bodyid) : nullptr;
                float old_x{}, old_y{}, old_z{};
                if (b) {
                  const dReal* bp = dBodyGetPosition(b->body());
                  old_x = bp[0];
                  old_y = bp[1];
                  old_z = bp[2];
                }
                RigidBody::ExtractCompact(&p, end, b);
                if (b && blend) {
                  const dReal* bp = dBodyGetPosition(b->body());
                  b->AddBlendOffset(old_x - bp[0], old_y - bp[1],
                                    old_z - bp[2]);
                }
              }
              uint32_t custom_data_len = read_varint();
              if (end - p < static_cast<ptrdiff_t>(custom_data_len)) {
                throw Exception("truncated compact correction");
              }
              if (custom_data_len != 0) {
                std::vector<uint8_t> data(p, p + custom_data_len);
                if (n) n->ApplyResyncData(data);
                p += custom_data_len;
              }
            }
            if (p != end) {
              throw Exception("invalid compact correction data");
            }
            current_cmd_ptr_ = current_cmd_.data() + (p - current_cmd_.data());
            break;
          }
          uint32_t offset = 2;
          uint16_t node_count;
          memcpy(&node_count, current_cmd_.data() + offset, sizeof(node_count));
          offset += 2;
          for (int i = 0; i < node_count; i++) {
            uint32_t node_id;
            memcpy(&node_id, current_cmd_.data() + offset, sizeof(node_id));
            offset += 4;
            int body_count = current_cmd_[offset++];
            Node* n =
                (node_id < nodes_.size()) ? nodes_[node_id].get() : nullptr;
            for (int j = 0; j < body_count; j++) {
              int bodyid = current_cmd_[offset++];
              uint16_t body_data_len;
              memcpy(&body_data_len, current_cmd_.data() + offset,
                     sizeof(body_data_len));
              RigidBody* b = n ? n->GetRigidBody(bodyid) : nullptr;
              offset += 2;
              const char* p1 = reinterpret_cast<char*>(&(current_cmd_[offset]));
              const char* p2 = p1;
              if (b) {
                dBodyID body = b->body();
                const dReal* p = dBodyGetPosition(body);
                float old_x = p[0];
                float old_y = p[1];
                float old_z = p[2];
                b->ExtractFull(&p2);
                if (p2 - p1 != body_data_len)
                  throw Exception("Invalid rbd correction data");
                if (blend) {
                  b->AddBlendOffset(old_x - p[0], old_y - p[1], old_z - p[2]);
                }
              }
              offset += body_data_len;
              if (offset > current_cmd_.size()) {
                throw Exception("Invalid rbd correction data");
              }
            }
            if (offset > current_cmd_.size())
              throw Exception("Invalid rbd correction data");

            // Extract custom per-node data.
            uint16_t custom_data_len;
            memcpy(&custom_data_len, current_cmd_.data() + offset,
                   sizeof(custom_data_len));
            offset += 2;
            if (custom_data_len != 0) {
              std::vector<uint8_t> data(custom_data_len);
              memcpy(&(data[0]), &(current_cmd_[offset]), custom_data_len);
              if (n) n->ApplyResyncData(data);
              offset += custom_data_len;
            }
            if (offset > current_cmd_.size()) {
              throw Exception("Invalid rbd correction data");
            }
          }
          if (offset != current_cmd_.size()) {
            throw Exception("invalid rbd correction data");
          }
          current_cmd_ptr_ = &(current_cmd_[0]) + offset;

          break;
        }
        case SessionCommand::kEndOfFile: {
          // EOF can happen anytime if they run out of disk space/etc.
          // We should expect any state.
          Reset(true);
          break;
        }
        case SessionCommand::kAddSceneGraph: {
          int32_t cmdvals[2];
          ReadInt32_2(cmdvals);
          int32_t id = cmdvals[0];
          millisecs_t starttime = cmdvals[1];
          if (id < 0 || id > 100) {
            throw Exception("invalid scene id");
          }
          if (static_cast<int>(scenes_.size()) < (id + 1)) {
            scenes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!scenes_[id].exists());
          scenes_[id] = Object::New<Scene>(starttime);
          scenes_[id]->set_stream_id(id);
          scenes_[id]->set_protocol_version(stream_protocol());
          break;
        }
        case SessionCommand::kRemoveSceneGraph: {
          int32_t id = ReadInt32();
          GetScene(id);  // Make sure it's valid.
          scenes_[id].Clear();
          break;
        }
        case SessionCommand::kStepSceneGraph: {
          int32_t val = ReadInt32();
          Scene* sg = GetScene(val);
          sg->Step();
          break;
        }
        case SessionCommand::kAddAnimCurve: {
          // (kProtocolVersionAnimCurveCommand) One bs.animate(): the
          // same eight operations kAddNode, kNodeOnCreate, four attr
          // sets and two kConnectNodeAttributes would have performed,
          // in that order.
          int32_t h[12];
          ReadInt32s(12, h);
          Scene* scene = GetScene(h[0]);
          if (h[1] < 0
              || h[1] >= static_cast<int>(
                     g_scene_v1->node_types_by_id().size())) {
            throw Exception("invalid node type id");
          }
          NodeType* node_type = g_scene_v1->node_types_by_id().at(h[1]);
          int id = h[2];
          if (id < 0 || id > 10000) {
            throw Exception("invalid node id");
          }
          int count = h[11];
          if (count < 0 || count > 10000) {
            throw Exception("invalid animcurve key count");
          }
          std::vector<int32_t> times32(static_cast<size_t>(count));
          std::vector<float> values(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, times32.data());
            ReadFloats(count, values.data());
          }
          if (static_cast<int>(nodes_.size()) < (id + 1)) {
            nodes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!nodes_[id].exists());
          Node* curve;
          {
            base::ScopedSetContext ssc(this);
            nodes_[id] = scene->NewNode(node_type->name(), "", nullptr);
            nodes_[id]->set_stream_id(id);
            curve = nodes_[id].get();
          }
          curve->OnCreate();
          // Attrs in bs.animate's order.
          curve->GetAttribute("times").Set(
              std::vector<int64_t>(times32.begin(), times32.end()));
          curve->GetAttribute("offset").Set(static_cast<float>(h[9]));
          curve->GetAttribute("values").Set(values);
          curve->GetAttribute("loop").Set(h[10] != 0);
          Node* globals = GetNode(h[3]);
          Node* target = GetNode(h[7]);
          globals->ConnectAttribute(globals->type()->GetAttribute(h[4]), curve,
                                    curve->type()->GetAttribute(h[5]));
          curve->ConnectAttribute(curve->type()->GetAttribute(h[6]), target,
                                  target->type()->GetAttribute(h[8]));
          break;
        }
        case SessionCommand::kStepSceneGraphAndTime: {
          // A scene step and the time step that followed it, folded
          // (kProtocolVersionMergedStep): same two operations, same
          // order.
          int32_t vals[2];  // scene-id, step-ms
          ReadInt32_2(vals);
          Scene* sg = GetScene(vals[0]);
          sg->Step();
          int32_t stepsize = vals[1];
          BA_PRECONDITION(stepsize > 0);
          if (stepsize > 10000) {
            throw Exception(
                "got abnormally large stepsize; probably a corrupt stream");
          }
          base_time_buffered_ -= stepsize;
          BA_PRECONDITION(base_time_buffered_ >= 0);
          base_time_millisecs_ += stepsize;
          break;
        }
        case SessionCommand::kAddNode: {
          int32_t vals[3];  // scene-id, nodetype-id, node-id
          ReadInt32_3(vals);
          Scene* scene = GetScene(vals[0]);
          assert(g_core != nullptr);
          if (vals[1] < 0
              || vals[1] >= static_cast<int>(
                     g_scene_v1->node_types_by_id().size())) {
            throw Exception("invalid node type id");
          }

          NodeType* node_type = g_scene_v1->node_types_by_id().at(vals[1]);

          // Fail if we get a ridiculous number of nodes.
          // FIXME: should enforce this on the server side too.
          int id = vals[2];
          if (id < 0 || id > 10000) {
            throw Exception("invalid node id");
          }
          if (static_cast<int>(nodes_.size()) < (id + 1)) {
            nodes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!nodes_[id].exists());
          {
            base::ScopedSetContext ssc(this);
            nodes_[id] = scene->NewNode(node_type->name(), "", nullptr);
            nodes_[id]->set_stream_id(id);
          }
          break;
        }
        case SessionCommand::kSetForegroundScene: {
          Scene* scene = GetScene(ReadInt32());
          if (auto* appmode = classic::ClassicAppMode::GetActiveOrWarn()) {
            appmode->SetForegroundScene(scene);
          }
          break;
        }
        case SessionCommand::kNodeMessage: {
          int32_t vals[2];
          ReadInt32_2(vals);
          Node* n = GetNode(vals[0]);
          int32_t msg_size = vals[1];
          if (msg_size < 1 || msg_size > 10000) {
            throw Exception("invalid message");
          }
          std::vector<char> buffer(static_cast<size_t>(msg_size));
          ReadChars(msg_size, &buffer[0]);
          n->DispatchNodeMessage(&buffer[0]);
          break;
        }
        case SessionCommand::kConnectNodeAttribute: {
          int32_t vals[4];
          ReadInt32_4(vals);
          Node* src_node = GetNode(vals[0]);
          Node* dst_node = GetNode(vals[2]);
          NodeAttributeUnbound* src_attr =
              src_node->type()->GetAttribute(vals[1]);
          NodeAttributeUnbound* dst_attr =
              dst_node->type()->GetAttribute(vals[3]);
          src_node->ConnectAttribute(src_attr, dst_node, dst_attr);
          break;
        }
        case SessionCommand::kNodeOnCreate: {
          Node* n = GetNode(ReadInt32());
          n->OnCreate();
          break;
        }
        case SessionCommand::kAddMaterial: {
          int32_t vals[2];  // scene-id, material-id
          ReadInt32_2(vals);
          Scene* scene = GetScene(vals[0]);
          // Fail if we get a ridiculous number of materials.
          // FIXME: should enforce this on the server side too.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 1000) {
            throw Exception("invalid material id");
          }
          if (static_cast<int>(materials_.size()) < (id + 1)) {
            materials_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!materials_[id].exists());
          materials_[id] = Object::New<Material>("", scene);
          materials_[id]->stream_id_ = id;
          break;
        }
        case SessionCommand::kRemoveMaterial: {
          int id = ReadInt32();
          GetMaterial(id);  // make sure its valid
          materials_[id].Clear();
          break;
        }
        case SessionCommand::kAddSpazDef: {
          int32_t vals[2];  // scene-id, spaz-def-id
          ReadInt32_2(vals);
          std::string json = ReadString();
          Scene* scene = GetScene(vals[0]);
          // Fail if we get a ridiculous number of definitions.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 1000) {
            throw Exception("invalid spaz-def id");
          }
          if (static_cast<int>(spaz_defs_.size()) < (id + 1)) {
            spaz_defs_.resize(static_cast<size_t>(id) + 1);
          }
          // A stock host can never re-add a live id (its stream frees an
          // id only after sending kRemoveSpazDef), so this means broken
          // id bookkeeping or baseline dump on our end, or a non-stock
          // host. Fail loudly (Error() logs at ERROR and ends the
          // session) rather than silently replacing the ref.
          if (spaz_defs_[id].exists()) {
            throw Exception("duplicate spaz-def id " + std::to_string(id));
          }
          spaz_defs_[id] = Object::New<SpazDef>(json, scene);
          spaz_defs_[id]->stream_id_ = id;
          break;
        }
        case SessionCommand::kRemoveSpazDef: {
          int id = ReadInt32();
          GetSpazDef(id);  // make sure its valid
          spaz_defs_[id].Clear();
          break;
        }
        case SessionCommand::kAddDepiction: {
          int32_t vals[2];  // scene-id, depiction-id
          ReadInt32_2(vals);
          std::string json = ReadString();
          Scene* scene = GetScene(vals[0]);
          // Fail if we get a ridiculous number of depictions.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 10000) {
            throw Exception("invalid depiction id");
          }
          if (static_cast<int>(depictions_.size()) < (id + 1)) {
            depictions_.resize(static_cast<size_t>(id) + 1);
          }
          // As with spaz defs: a live id re-added is a bug; fail loudly.
          if (depictions_[id].exists()) {
            throw Exception("duplicate depiction id " + std::to_string(id));
          }
          depictions_[id] = Object::New<SceneDepiction>(json, scene);
          depictions_[id]->stream_id_ = id;
          break;
        }
        case SessionCommand::kRemoveDepiction: {
          int id = ReadInt32();
          GetDepiction(id);  // make sure its valid
          depictions_[id].Clear();
          break;
        }
        case SessionCommand::kAddMaterialComponent: {
          int32_t cmdvals[2];
          ReadInt32_2(cmdvals);
          Material* m = GetMaterial(cmdvals[0]);
          int component_size = cmdvals[1];
          if (component_size < 1 || component_size > 10000) {
            throw Exception("invalid component");
          }
          std::vector<char> buffer(static_cast<size_t>(component_size));
          ReadChars(component_size, &buffer[0]);
          auto c(Object::New<MaterialComponent>());
          const char* ptr1 = &buffer[0];
          const char* ptr2 = ptr1;
          c->Restore(&ptr2, this);
          BA_PRECONDITION(ptr2 - ptr1 == component_size);
          m->AddComponent(c);
          break;
        }
        case SessionCommand::kAddTexture: {
          int32_t vals[2];  // scene-id, texture-id
          ReadInt32_2(vals);
          std::string name = ReadString();
          Scene* scene = GetScene(vals[0]);
          // Fail if we get a ridiculous number of textures.
          // FIXME: Should enforce this on the server side too.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 1000) {
            throw Exception("invalid texture id");
          }
          if (static_cast<int>(textures_.size()) < (id + 1)) {
            textures_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!textures_[id].exists());
          textures_[id] = Object::New<SceneTexture>(name, scene);
          textures_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kRemoveTexture: {
          int id = ReadInt32();
          GetTexture(id);  // make sure its valid
          textures_[id].Clear();
          break;
        }
        case SessionCommand::kAddMesh: {
          int32_t vals[2];  // scene-id, mesh-id
          ReadInt32_2(vals);
          std::string name = ReadString();
          Scene* scene = GetScene(vals[0]);

          // Fail if we get a ridiculous number of meshes.
          // FIXME: Should enforce this on the server side too.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 1000) {
            throw Exception("invalid mesh id");
          }
          if (static_cast<int>(meshes_.size()) < (id + 1)) {
            meshes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!meshes_[id].exists());
          meshes_[id] = Object::New<SceneMesh>(name, scene);
          meshes_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kRemoveMesh: {
          int id = ReadInt32();
          GetMesh(id);  // make sure its valid
          meshes_[id].Clear();
          break;
        }
        case SessionCommand::kAddSound: {
          int32_t vals[2];  // scene-id, sound-id
          ReadInt32_2(vals);
          std::string name = ReadString();
          Scene* scene = GetScene(vals[0]);
          // Fail if we get a ridiculous number of sounds.
          // FIXME: Should enforce this on the server side too.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 1000) {
            throw Exception("invalid sound id");
          }
          if (static_cast<int>(sounds_.size()) < (id + 1)) {
            sounds_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!sounds_[id].exists());
          sounds_[id] = Object::New<SceneSound>(name, scene);
          sounds_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kRemoveSound: {
          int id = ReadInt32();
          GetSound(id);  // Make sure its valid.
          sounds_[id].Clear();
          break;
        }
        case SessionCommand::kAddCollisionMesh: {
          int32_t vals[2];  // scene-id, collision_mesh-id
          ReadInt32_2(vals);
          std::string name = ReadString();
          Scene* scene = GetScene(vals[0]);

          // Fail if we get a ridiculous number of collision_meshes.
          // FIXME: Should enforce this on the server side too.
          int id = vals[1];
          if (vals[1] < 0 || vals[1] >= 1000) {
            throw Exception("invalid collision_mesh id");
          }
          if (static_cast<int>(collision_meshes_.size()) < (id + 1)) {
            collision_meshes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!collision_meshes_[id].exists());
          collision_meshes_[id] = Object::New<SceneCollisionMesh>(name, scene);
          collision_meshes_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kRemoveCollisionMesh: {
          int id = ReadInt32();
          GetCollisionMesh(id);  // make sure its valid
          collision_meshes_[id].Clear();
          break;
        }
        case SessionCommand::kRemoveNode: {
          int id = ReadInt32();
          Node* n = GetNode(id);
          n->scene()->DeleteNode(n);
          assert(!nodes_[id].exists());
          break;
        }
        case SessionCommand::kSetNodeAttrFloat: {
          int vals[2];
          ReadInt32_2(vals);
          GetNode(vals[0])->GetAttribute(vals[1]).Set(ReadFloat());
          break;
        }
        case SessionCommand::kSetNodeAttrInt32: {
          int32_t vals[3];
          ReadInt32_3(vals);

          // Note; we currently deal in 64 bit ints locally but read/write 32
          // bit over the wire.
          GetNode(vals[0])->GetAttribute(vals[1]).Set(
              static_cast<int64_t>(vals[2]));
          break;
        }
        case SessionCommand::kSetNodeAttrBool: {
          int vals[3];
          ReadInt32_3(vals);
          GetNode(vals[0])->GetAttribute(vals[1]).Set(
              static_cast<bool>(vals[2]));
          break;
        }
        case SessionCommand::kSetNodeAttrFloats: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<float> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadFloats(count, &(vals[0]));
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kSetNodeAttrInt32s: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals[0]));
          }

          // Note: we currently deal in 64 bit ints locally but read/write 32
          // bit over the wire. Convert.
          std::vector<int64_t> vals64(static_cast<size_t>(count));
          for (int i = 0; i < count; i++) {
            vals64[i] = vals[i];
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals64);
          break;
        }
        case SessionCommand::kSetNodeAttrString: {
          int vals[2];
          ReadInt32_2(vals);
          NodeAttribute attr = GetNode(vals[0])->GetAttribute(vals[1]);
          std::string val = ReadString();
          if (stream_protocol() >= kProtocolVersionLangStrWire
              && attr.is_lang_str() && IsLangStrWireTagged(val)) {
            std::shared_ptr<const base::LangStr> parsed;
            if (val[0] == kLangStrWireTagLangStr) {
              // No-resolve bind-and-parse: legal here only per the
              // verified-context rules on EvalLangStrWireValue_ above.
              auto result = base::LangStr::FromJson(
                  std::string_view(val).substr(1), &asset_package_table_);
              if (result.has_value()) {
                parsed = *result;
              } else {
                g_core->logging->Log(LogName::kBaNetworking, LogLevel::kWarning,
                                     "Error parsing lang-str attr wire value: "
                                         + result.error());
              }
            }
            g_core->logging->Log(
                LogName::kBaNetworking, LogLevel::kDebug, [&val, &parsed] {
                  return "ClientSession: lang-str attr set (tag "
                         + std::to_string(static_cast<int>(val[0])) + "): "
                         + (parsed != nullptr ? parsed->Evaluate()
                                              : val.substr(1));
                });
            attr.SetLangStrWire(val, std::move(parsed));
          } else {
            attr.Set(val);
          }
          break;
        }
        case SessionCommand::kSetNodeAttrNode: {
          int vals[3];
          ReadInt32_3(vals);
          GetNode(vals[0])->GetAttribute(vals[1]).Set(GetNode(vals[2]));
          break;
        }
        case SessionCommand::kSetNodeAttrNodeNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          Node* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrTextureNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SceneTexture* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrSpazDef: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          SpazDef* val = GetSpazDef(cmdvals[2]);
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrSpazDefNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SpazDef* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrDepiction: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          SceneDepiction* val = GetDepiction(cmdvals[2]);
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrDepictionNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SceneDepiction* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrSoundNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SceneSound* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrMeshNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SceneMesh* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrCollisionMeshNull: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SceneCollisionMesh* val = nullptr;
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrNodes: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals_in(static_cast<size_t>(count));
          std::vector<Node*> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals_in[0]));
          }
          for (int i = 0; i < count; i++) {
            vals[i] = GetNode(vals_in[i]);
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kSetNodeAttrTexture: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          SceneTexture* val = GetTexture(cmdvals[2]);
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrTextures: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals_in(static_cast<size_t>(count));
          std::vector<SceneTexture*> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals_in[0]));
          }
          for (int i = 0; i < count; i++) {
            vals[i] = GetTexture(vals_in[i]);
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kSetNodeAttrSound: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          SceneSound* val = GetSound(cmdvals[2]);
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrSounds: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals_in(static_cast<size_t>(count));
          std::vector<SceneSound*> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals_in[0]));
          }
          for (int i = 0; i < count; i++) {
            vals[i] = GetSound(vals_in[i]);
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kSetNodeAttrMesh: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          SceneMesh* val = GetMesh(cmdvals[2]);
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrMeshes: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals_in(static_cast<size_t>(count));
          std::vector<SceneMesh*> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals_in[0]));
          }
          for (int i = 0; i < count; i++) {
            vals[i] = GetMesh(vals_in[i]);
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kSetNodeAttrCollisionMesh: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          SceneCollisionMesh* val = GetCollisionMesh(cmdvals[2]);
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(val);
          break;
        }
        case SessionCommand::kSetNodeAttrCollisionMeshes: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals_in(static_cast<size_t>(count));
          std::vector<SceneCollisionMesh*> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals_in[0]));
          }
          for (int i = 0; i < count; i++) {
            vals[i] = GetCollisionMesh(vals_in[i]);
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kSetNodeAttrMaterials: {
          int cmdvals[3];
          ReadInt32_3(cmdvals);
          int count = cmdvals[2];
          if (count < 0 || count > 1000) {
            throw Exception("invalid array size (" + std::to_string(count)
                            + ")");
          }
          std::vector<int32_t> vals_in(static_cast<size_t>(count));
          std::vector<Material*> vals(static_cast<size_t>(count));
          if (count > 0) {
            ReadInt32s(count, &(vals_in[0]));
          }
          for (int i = 0; i < count; i++) {
            vals[i] = GetMaterial(vals_in[i]);
          }
          GetNode(cmdvals[0])->GetAttribute(cmdvals[1]).Set(vals);
          break;
        }
        case SessionCommand::kPlaySound: {
          SceneSound* sound = GetSound(ReadInt32());
          float volume = ReadFloat();
          g_base->audio->PlaySound(sound->GetSoundData(), volume);
          break;
        }
        case SessionCommand::kScreenMessageBottom: {
          std::string val = ReadString();
          Vector3f color{};
          ReadFloats(3, color.v);
          bool literal{};
          if (stream_protocol() >= kProtocolVersionLangStrWire
              && IsLangStrWireTagged(val)) {
            std::tie(val, literal) =
                EvalLangStrWireValue_(val, asset_package_table_);
            g_core->logging->Log(
                LogName::kBaNetworking, LogLevel::kDebug, [&val] {
                  return "ClientSession: lang-str screen-message: " + val;
                });
          }
          g_base->ScreenMessage(val, color, literal);
          break;
        }
        case SessionCommand::kScreenMessageTop: {
          int cmdvals[2];
          ReadInt32_2(cmdvals);
          SceneTexture* texture = GetTexture(cmdvals[0]);
          SceneTexture* tint_texture = GetTexture(cmdvals[1]);
          std::string s = ReadString();
          // Older streams carry no third tint; white is its no-op.
          float f[12]{0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                      0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f};
          ReadFloats(stream_protocol() >= kProtocolVersionTint3 ? 12 : 9, f);
          bool literal{};
          if (stream_protocol() >= kProtocolVersionLangStrWire
              && IsLangStrWireTagged(s)) {
            std::tie(s, literal) =
                EvalLangStrWireValue_(s, asset_package_table_);
          }
          g_base->graphics->screenmessages->AddScreenMessage(
              s, literal, Vector3f(f[0], f[1], f[2]), true,
              texture->texture_data(), tint_texture->texture_data(),
              Vector3f(f[3], f[4], f[5]), Vector3f(f[6], f[7], f[8]),
              Vector3f(f[9], f[10], f[11]));
          break;
        }
        case SessionCommand::kScreenMessageTopDepiction: {
          SceneDepiction* depiction = GetDepiction(ReadInt32());
          std::string s = ReadString();
          float f[3];
          ReadFloats(3, f);
          bool literal{};
          if (IsLangStrWireTagged(s)) {
            std::tie(s, literal) =
                EvalLangStrWireValue_(s, asset_package_table_);
          }
          g_base->graphics->screenmessages->AddTopScreenMessageWithDepiction(
              s, literal, Vector3f(f[0], f[1], f[2]), depiction->json());
          break;
        }
        case SessionCommand::kPlaySoundAtPosition: {
          SceneSound* sound = GetSound(ReadInt32());
          float volume = ReadFloat();
          float x = ReadFloat();
          float y = ReadFloat();
          float z = ReadFloat();
          g_base->audio->PlaySoundAtPosition(sound->GetSoundData(), volume, x,
                                             y, z);
          break;
        }
        case SessionCommand::kCameraShake: {
          auto intensity = ReadFloat();
          g_base->graphics->LocalCameraShake(intensity);
          break;
        }
        case SessionCommand::kInputDeviceFeedback: {
          // Both reads must happen unconditionally to keep the stream in
          // sync, however little we end up doing with them.
          auto player_id = ReadInt32();
          auto payload = ReadString();
          HandleInputDeviceFeedback_(player_id, payload);
          break;
        }
        case SessionCommand::kEmitBGDynamics: {
          int cmdvals[4];
          ReadInt32_4(cmdvals);
          float vals[8];
          ReadFloats(8, vals);
          if (g_base && g_base->bg_dynamics != nullptr) {
            base::BGDynamicsEmission e;
            e.emit_type = (base::BGDynamicsEmitType)cmdvals[0];
            e.count = cmdvals[1];
            e.chunk_type = (base::BGDynamicsChunkType)cmdvals[2];
            e.tendril_type = (base::BGDynamicsTendrilType)cmdvals[3];
            e.position.x = vals[0];
            e.position.y = vals[1];
            e.position.z = vals[2];
            e.velocity.x = vals[3];
            e.velocity.y = vals[4];
            e.velocity.z = vals[5];
            e.scale = vals[6];
            e.spread = vals[7];

            // What we play back always shows in the main world.
            g_base->bg_dynamics->main_world()->Emit(e);
          }
          break;
        }
        case SessionCommand::kAddTextureIndexed: {
          int32_t vals[4];  // scene-id, texture-id, pkg-idx, asset-idx
          ReadInt32_4(vals);
          std::string name = ResolveIndexedAssetRef_(
              vals[2], vals[3], AssetBucketKind::kTextures);
          Scene* scene = GetScene(vals[0]);
          int id = vals[1];
          if (id < 0 || id >= 1000) {
            throw Exception("invalid texture id");
          }
          if (static_cast<int>(textures_.size()) < (id + 1)) {
            textures_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!textures_[id].exists());
          textures_[id] = Object::New<SceneTexture>(name, scene);
          textures_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kAddMeshIndexed: {
          int32_t vals[4];  // scene-id, mesh-id, pkg-idx, asset-idx
          ReadInt32_4(vals);
          std::string name = ResolveIndexedAssetRef_(vals[2], vals[3],
                                                     AssetBucketKind::kMeshes);
          Scene* scene = GetScene(vals[0]);
          int id = vals[1];
          if (id < 0 || id >= 1000) {
            throw Exception("invalid mesh id");
          }
          if (static_cast<int>(meshes_.size()) < (id + 1)) {
            meshes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!meshes_[id].exists());
          meshes_[id] = Object::New<SceneMesh>(name, scene);
          meshes_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kAddSoundIndexed: {
          int32_t vals[4];  // scene-id, sound-id, pkg-idx, asset-idx
          ReadInt32_4(vals);
          std::string name = ResolveIndexedAssetRef_(vals[2], vals[3],
                                                     AssetBucketKind::kAudio);
          Scene* scene = GetScene(vals[0]);
          int id = vals[1];
          if (id < 0 || id >= 1000) {
            throw Exception("invalid sound id");
          }
          if (static_cast<int>(sounds_.size()) < (id + 1)) {
            sounds_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!sounds_[id].exists());
          sounds_[id] = Object::New<SceneSound>(name, scene);
          sounds_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kAddCollisionMeshIndexed: {
          int32_t vals[4];  // scene-id, collision-mesh-id, pkg-idx, asset-idx
          ReadInt32_4(vals);
          std::string name = ResolveIndexedAssetRef_(
              vals[2], vals[3], AssetBucketKind::kConstant);
          Scene* scene = GetScene(vals[0]);
          int id = vals[1];
          if (id < 0 || id >= 1000) {
            throw Exception("invalid collision_mesh id");
          }
          if (static_cast<int>(collision_meshes_.size()) < (id + 1)) {
            collision_meshes_.resize(static_cast<size_t>(id) + 1);
          }
          assert(!collision_meshes_[id].exists());
          collision_meshes_[id] = Object::New<SceneCollisionMesh>(name, scene);
          collision_meshes_[id]->set_stream_id(id);
          break;
        }
        case SessionCommand::kDeclareAssetPackage: {
          int32_t cmdvals[2];
          ReadInt32_2(cmdvals);
          int32_t index = cmdvals[0];
          int32_t total = cmdvals[1];
          std::string apverid = ReadString();

          // A fresh declaration (index 0) replaces any existing table
          // (a new baseline arrives when the host switches sessions).
          if (index == 0) {
            asset_package_table_.clear();
          }
          if (index < 0 || total < 1 || index >= total
              || index != static_cast<int32_t>(asset_package_table_.size())) {
            throw Exception(
                "invalid asset-package table declaration (index "
                + std::to_string(index) + " total " + std::to_string(total)
                + " have " + std::to_string(asset_package_table_.size()) + ")");
          }
          asset_package_table_.push_back(apverid);
          if (index + 1 == total) {
            g_core->logging->Log(
                LogName::kBaNetworking, LogLevel::kDebug, [this, total] {
                  std::string out =
                      "ClientSession: asset-package table declared ("
                      + std::to_string(total) + " entries):";
                  for (const auto& entry : asset_package_table_) {
                    out += " " + entry;
                  }
                  return out;
                });
            OnAssetPackageTableComplete();
          }
          break;
        }
        default:
          throw Exception("unrecognized stream command: "
                          + std::to_string(static_cast<int>(cmd)));
      }
    }
  } catch (const std::exception& e) {
    Error(e.what());
  }
}  // NOLINT  (yes this is too long)

ClientSession::~ClientSession() = default;

void ClientSession::OnScreenSizeChange() {
  // Let all our scenes know.
  for (auto&& i : scenes_) {
    if (Scene* sg = i.get()) {
      sg->OnScreenSizeChange();
    }
  }
}

void ClientSession::LanguageChanged() {
  // Let all our scenes know.
  for (auto&& i : scenes_) {
    if (Scene* sg = i.get()) {
      sg->LanguageChanged();
    }
  }
}

auto ClientSession::GetScene(int id) const -> Scene* {
  if (id < 0 || id >= static_cast<int>(scenes_.size())) {
    throw Exception("Invalid scene id");
  }
  Scene* sg = scenes_[id].get();
  if (!sg) {
    throw Exception("Invalid scene id");
  }
  return sg;
}
auto ClientSession::GetNode(int id) const -> Node* {
  if (id < 0 || id >= static_cast<int>(nodes_.size())) {
    throw Exception("Invalid node (out of range)");
  }
  Node* n = nodes_[id].get();
  if (!n) {
    throw Exception("Invalid node id (empty slot)");
  }
  return n;
}
auto ClientSession::GetMaterial(int id) const -> Material* {
  if (id < 0 || id >= static_cast<int>(materials_.size())) {
    throw Exception("Invalid material (out of range)");
  }
  Material* n = materials_[id].get();
  if (!n) {
    throw Exception("Invalid material id (empty slot)");
  }
  return n;
}
auto ClientSession::GetSpazDef(int id) const -> SpazDef* {
  if (id < 0 || id >= static_cast<int>(spaz_defs_.size())) {
    throw Exception("Invalid spaz-def (out of range)");
  }
  SpazDef* n = spaz_defs_[id].get();
  if (!n) {
    throw Exception("Invalid spaz-def id (empty slot)");
  }
  return n;
}

auto ClientSession::GetDepiction(int id) const -> SceneDepiction* {
  if (id < 0 || id >= static_cast<int>(depictions_.size())) {
    throw Exception("Invalid depiction (out of range)");
  }
  SceneDepiction* n = depictions_[id].get();
  if (!n) {
    throw Exception("Invalid depiction id (empty slot)");
  }
  return n;
}
auto ClientSession::GetTexture(int id) const -> SceneTexture* {
  if (id < 0 || id >= static_cast<int>(textures_.size())) {
    throw Exception("Invalid texture (out of range)");
  }
  SceneTexture* n = textures_[id].get();
  if (!n) {
    throw Exception("Invalid texture id (empty slot)");
  }
  return n;
}
auto ClientSession::GetMesh(int id) const -> SceneMesh* {
  if (id < 0 || id >= static_cast<int>(meshes_.size())) {
    throw Exception("Invalid mesh (out of range)");
  }
  SceneMesh* n = meshes_[id].get();
  if (!n) {
    throw Exception("Invalid mesh id (empty slot)");
  }
  return n;
}
auto ClientSession::GetSound(int id) const -> SceneSound* {
  if (id < 0 || id >= static_cast<int>(sounds_.size())) {
    throw Exception("Invalid sound (out of range)");
  }
  SceneSound* n = sounds_[id].get();
  if (!n) {
    throw Exception("Invalid sound id (empty slot)");
  }
  return n;
}
auto ClientSession::GetCollisionMesh(int id) const -> SceneCollisionMesh* {
  if (id < 0 || id >= static_cast<int>(collision_meshes_.size())) {
    throw Exception("Invalid collision_mesh (out of range)");
  }
  SceneCollisionMesh* n = collision_meshes_[id].get();
  if (!n) {
    throw Exception("Invalid collision_mesh id (empty slot)");
  }
  return n;
}

void ClientSession::Error(const std::string& description) {
  g_core->logging->Log(LogName::kBaNetworking, LogLevel::kError,
                       "Client session error: " + description);
  End();
}

void ClientSession::End() {
  if (shutting_down_) return;
  shutting_down_ = true;
  g_scene_v1->python->objs().PushCall(
      SceneV1Python::ObjID::kLaunchMainMenuSessionCall);
}

void ClientSession::HandleSessionMessage(const std::vector<uint8_t>& buffer) {
  assert(g_base->InLogicThread());

  BA_PRECONDITION(!buffer.empty());

  switch (buffer[0]) {
    case BA_MESSAGE_SESSION_RESET: {
      // Hmmm; been a while since I wrote this, but wondering why reset isn't
      // just a session-command. (Do we not want it added to replay streams?...)
      Reset(false);
      break;
    }

    case BA_MESSAGE_SESSION_COMMANDS: {
      // A run of [length][command] pairs up to the end of the packet
      // (varint lengths under the compact framing, 16-bit before).
      // Break it apart and feed each command to the client session.
      uint32_t offset = 1;
      std::vector<uint8_t> sub_buffer;
      const bool compact = compact_stream();
      while (true) {
        uint32_t size;
        if (compact) {
          size = 0;
          int shift = 0;
          while (true) {
            if (offset >= buffer.size() || shift > 28) {
              Error("invalid state message");
              return;
            }
            uint8_t b = buffer[offset++];
            size |= static_cast<uint32_t>(b & 0x7f) << shift;
            if (!(b & 0x80)) {
              break;
            }
            shift += 7;
          }
        } else {
          if (offset + 2 > buffer.size()) {
            Error("invalid state message");
            return;
          }
          uint16_t size16;
          memcpy(&size16, &(buffer[offset]), 2);
          size = size16;
          offset += 2;
        }
        if (offset + size > buffer.size()) {
          Error("invalid state message");
          return;
        }
        sub_buffer.resize(size);
        memcpy(&(sub_buffer[0]), &(buffer[offset]), sub_buffer.size());
        AddCommand(sub_buffer);
        offset += size;  // move to next command
        if (offset == buffer.size()) {
          // let's also use this opportunity to graph our command-buffer size
          // for network debugging... if (NetGraph *graph =
          // g_graphics->GetClientSessionStepBufferGraph()) {
          //   graph->addSample(AppTimeMillisecs(), steps_on_list_);
          // }

          break;
        }
      }
      break;
    }

    case BA_MESSAGE_SESSION_DYNAMICS_CORRECTION: {
      // Just drop this in the game's command-stream verbatim, except switch its
      // state-ID to a command-ID.
      std::vector<uint8_t> buffer_out = buffer;
      buffer_out[0] = static_cast<uint8_t>(SessionCommand::kDynamicsCorrection);
      AddCommand(buffer_out);
      break;
    }

    default:
      throw Exception("ClientSession::HandleSessionMessage " + ObjToString(this)
                      + "got unrecognized message : "
                      + std::to_string(static_cast<int>(buffer[0]))
                      + " of size " + std::to_string(buffer.size()));
      break;
  }
}

// Add a single command in.
namespace {

auto ReadZz_(const std::vector<uint8_t>& b, size_t* pos) -> int32_t {
  uint32_t v = 0;
  int shift = 0;
  while (true) {
    if (*pos >= b.size() || shift > 28) {
      throw Exception("corrupt packed command");
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

void AppendZz_(std::vector<uint8_t>* out, int32_t value) {
  auto v =
      (static_cast<uint32_t>(value) << 1) ^ static_cast<uint32_t>(value >> 31);
  while (v >= 0x80) {
    out->push_back(static_cast<uint8_t>((v & 0x7f) | 0x80));
    v >>= 7;
  }
  out->push_back(static_cast<uint8_t>(v));
}

// Advance *pos past one packed attr-set body (everything after the cmd
// byte and node id: attr index then value). Must agree with the writer
// layouts in session_stream.cc and with IsPackableAttrCommand.
void SkipPackedAttrValue_(uint8_t cmd, const std::vector<uint8_t>& b,
                          size_t* pos) {
  auto need = [&](size_t n) {
    if (*pos + n > b.size()) {
      throw Exception("corrupt packed command");
    }
    *pos += n;
  };
  ReadZz_(b, pos);  // Attr index.
  switch (static_cast<SessionCommand>(cmd)) {
    case SessionCommand::kSetNodeAttrFloat:
      need(4);
      break;
    case SessionCommand::kSetNodeAttrInt32:
    case SessionCommand::kSetNodeAttrBool:
    case SessionCommand::kSetNodeAttrNode:
    case SessionCommand::kSetNodeAttrTexture:
    case SessionCommand::kSetNodeAttrSound:
    case SessionCommand::kSetNodeAttrMesh:
    case SessionCommand::kSetNodeAttrCollisionMesh:
    case SessionCommand::kSetNodeAttrSpazDef:
    case SessionCommand::kSetNodeAttrDepiction:
      ReadZz_(b, pos);
      break;
    case SessionCommand::kSetNodeAttrNodeNull:
    case SessionCommand::kSetNodeAttrTextureNull:
    case SessionCommand::kSetNodeAttrSoundNull:
    case SessionCommand::kSetNodeAttrMeshNull:
    case SessionCommand::kSetNodeAttrCollisionMeshNull:
    case SessionCommand::kSetNodeAttrSpazDefNull:
    case SessionCommand::kSetNodeAttrDepictionNull:
      break;
    case SessionCommand::kSetNodeAttrFloats: {
      int32_t n = ReadZz_(b, pos);
      if (n < 0) {
        throw Exception("corrupt packed command");
      }
      need(static_cast<size_t>(n) * 4);
      break;
    }
    case SessionCommand::kSetNodeAttrInt32s:
    case SessionCommand::kSetNodeAttrNodes:
    case SessionCommand::kSetNodeAttrMaterials:
    case SessionCommand::kSetNodeAttrTextures:
    case SessionCommand::kSetNodeAttrSounds:
    case SessionCommand::kSetNodeAttrMeshes:
    case SessionCommand::kSetNodeAttrCollisionMeshes: {
      int32_t n = ReadZz_(b, pos);
      if (n < 0) {
        throw Exception("corrupt packed command");
      }
      for (int32_t i = 0; i < n; ++i) {
        ReadZz_(b, pos);
      }
      break;
    }
    case SessionCommand::kSetNodeAttrString: {
      int32_t n = ReadZz_(b, pos);
      if (n < 0) {
        throw Exception("corrupt packed command");
      }
      need(static_cast<size_t>(n));
      break;
    }
    default:
      throw Exception("unpackable attr command in packed node create");
  }
}

}  // namespace

void ClientSession::ExpandPackedCommand_(const std::vector<uint8_t>& command) {
  size_t pos = 1;
  auto c = static_cast<SessionCommand>(command[0]);
  if (c == SessionCommand::kTimeStepSceneGraphAndTime) {
    int32_t pre = ReadZz_(command, &pos);
    int32_t scene = ReadZz_(command, &pos);
    int32_t post = ReadZz_(command, &pos);
    std::vector<uint8_t> ts{
        static_cast<uint8_t>(SessionCommand::kBaseTimeStep)};
    AppendZz_(&ts, pre);
    AddCommand(ts);
    std::vector<uint8_t> step{
        static_cast<uint8_t>(SessionCommand::kStepSceneGraphAndTime)};
    AppendZz_(&step, scene);
    AppendZz_(&step, post);
    AddCommand(step);
    return;
  }
  assert(c == SessionCommand::kAddNodeWithAttrs);
  int32_t scene = ReadZz_(command, &pos);
  int32_t type = ReadZz_(command, &pos);
  int32_t id = ReadZz_(command, &pos);
  int32_t count = ReadZz_(command, &pos);
  if (count < 0 || count > 1000) {
    throw Exception("corrupt packed command");
  }
  std::vector<uint8_t> add{static_cast<uint8_t>(SessionCommand::kAddNode)};
  AppendZz_(&add, scene);
  AppendZz_(&add, type);
  AppendZz_(&add, id);
  AddCommand(add);
  for (int32_t i = 0; i < count; ++i) {
    if (pos >= command.size()) {
      throw Exception("corrupt packed command");
    }
    uint8_t cmd = command[pos++];
    size_t body_start = pos;
    SkipPackedAttrValue_(cmd, command, &pos);
    std::vector<uint8_t> attr{cmd};
    AppendZz_(&attr, id);
    attr.insert(attr.end(),
                command.begin() + static_cast<ptrdiff_t>(body_start),
                command.begin() + static_cast<ptrdiff_t>(pos));
    AddCommand(attr);
  }
  if (pos != command.size()) {
    throw Exception("corrupt packed command");
  }
  std::vector<uint8_t> oncreate{
      static_cast<uint8_t>(SessionCommand::kNodeOnCreate)};
  AppendZz_(&oncreate, id);
  AddCommand(oncreate);
}

void ClientSession::AddCommand(const std::vector<uint8_t>& command) {
  // Wire-only packings (kProtocolVersionPackedCommands): expand back
  // into the original commands so everything downstream, including the
  // time-step pending release and pacing below, sees exactly what the
  // unpacked stream would have carried.
  if (!command.empty() && compact_stream()
      && (command[0]
              == static_cast<uint8_t>(
                  SessionCommand::kTimeStepSceneGraphAndTime)
          || command[0]
                 == static_cast<uint8_t>(SessionCommand::kAddNodeWithAttrs))) {
    ExpandPackedCommand_(command);
    return;
  }
  // If this is a time-step command, we can dump everything we've been building
  // up onto the list to be chewed through by the interpreter (we don't want to
  // add things until we have the *entire* step, so we don't wind up rendering
  // things halfway through some change, etc.).
  commands_pending_.push_back(command);
  if (!command.empty()) {
    bool is_time_step =
        command[0] == static_cast<uint8_t>(SessionCommand::kBaseTimeStep);
    bool is_merged_step =
        command[0]
        == static_cast<uint8_t>(SessionCommand::kStepSceneGraphAndTime);
    if (is_time_step || is_merged_step) {
      // Peek at the step size (the first int, or the second after the
      // scene id for the merged form). Under the compact framing the
      // integer is a zigzag varint (8ms -> 0x10), not a raw byte; a raw
      // read there doubled the tally and fed the net-client's clock
      // projection 2x steps.
      int step;
      size_t i = 1;
      int skip = is_merged_step ? 1 : 0;
      if (compact_stream()) {
        int32_t val = 0;
        for (int n = 0; n <= skip; n++) {
          uint32_t v = 0;
          int shift = 0;
          while (true) {
            if (i >= command.size() || shift > 28) {
              throw Exception("corrupt time-step command");
            }
            uint8_t b = command[i++];
            v |= static_cast<uint32_t>(b & 0x7f) << shift;
            if (!(b & 0x80)) {
              break;
            }
            shift += 7;
          }
          val = static_cast<int32_t>(v >> 1) ^ -static_cast<int32_t>(v & 1);
        }
        step = val;
      } else {
        i += static_cast<size_t>(skip) * 4;
        if (command.size() < i + 4) {
          throw Exception("corrupt time-step command");
        }
        int32_t val;
        memcpy(&val, command.data() + i, sizeof(val));
        step = val;
      }

      // Keep a tally of how much stepped time we've built up.
      base_time_buffered_ += step;

      // Let subclasses know we just received a step in case they'd like
      // to factor it in for rate adjustments/etc.
      OnBaseTimeStepAdded(step);

      for (auto&& i : commands_pending_) {
        commands_.push_back(i);
      }
      commands_pending_.clear();
    }
  }
}

auto ClientSession::GetForegroundContext() -> base::ContextRef {
  return base::ContextRef(this);
}

void ClientSession::GetCorrectionMessages(
    bool blend, std::vector<std::vector<uint8_t>>* messages) {
  std::vector<uint8_t> message;
  for (auto&& i : scenes_) {
    if (Scene* sg = i.get()) {
      message = sg->GetCorrectionMessage(blend);
      // A correction packet of size 4 is empty; ignore it.
      if (message.size() > 4) {
        messages->push_back(message);
      }
    }
  }
}

void ClientSession::DumpFullState(SessionStream* out) {
  // Declare our asset-package table first so everything below can be
  // written as indexed refs (mirroring HostSession::DumpFullState).
  // This matters for replay seeks: the restore path resets the session
  // (clearing the table) and then resumes reading the on-disk stream
  // *past* its start-of-stream declarations, so the snapshot itself
  // must re-establish the table or every indexed ref after a seek
  // fails against an empty table.
  if (!asset_package_table().empty()) {
    out->DeclareAssetPackages(asset_package_table());
  }

  // Add all scenes.
  for (auto&& i : scenes()) {
    if (Scene* sg = i.get()) {
      sg->Dump(out);
    }
  }

  // Before doing any nodes, we need to create all materials.
  // (but *not* their components, which may reference the nodes that we haven't
  // made yet)
  for (auto&& i : materials()) {
    if (Material* m = i.get()) {
      out->AddMaterial(m);
    }
  }

  // Add all media.
  for (auto&& i : textures()) {
    if (SceneTexture* t = i.get()) {
      out->AddTexture(t);
    }
  }
  for (auto&& i : meshes()) {
    if (SceneMesh* s = i.get()) {
      out->AddMesh(s);
    }
  }
  for (auto&& i : sounds()) {
    if (SceneSound* s = i.get()) {
      out->AddSound(s);
    }
  }
  for (auto&& i : collision_meshes()) {
    if (SceneCollisionMesh* s = i.get()) {
      out->AddCollisionMesh(s);
    }
  }

  // Spaz defs and depictions must exist before any node referencing
  // them (as in HostSession::DumpFullState); a snapshot without them
  // fails every node attr pointing at one on restore.
  for (auto&& i : spaz_defs()) {
    if (SpazDef* d = i.get()) {
      out->AddSpazDef(d);
    }
  }
  for (auto&& i : depictions()) {
    if (SceneDepiction* d = i.get()) {
      out->AddDepiction(d);
    }
  }

  // Add all scene nodes.
  for (auto&& i : scenes()) {
    if (Scene* sg = i.get()) {
      sg->DumpNodes(out);
    }
  }

  // Now fill out materials since we know all the nodes/etc. that they
  // refer to exist.
  for (auto&& i : materials()) {
    if (Material* m = i.get()) {
      m->DumpComponents(out);
    }
  }
}

}  // namespace ballistica::scene_v1
