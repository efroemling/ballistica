// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SESSION_STREAM_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SESSION_STREAM_H_

#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/classic/classic.h"
#include "ballistica/scene_v1/support/client_controller_interface.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

/// Append an unsigned LEB128 varint (the compact stream framing).
void AppendVarint(std::vector<uint8_t>* out, uint32_t value);

/// Whether kAddNodeWithAttrs may carry this attr-set command (must match
/// ClientSession's value-layout table).
auto IsPackableAttrCommand(uint8_t cmd) -> bool;

// A mechanism for dumping a live session or session-creation-commands to a
// stream of messages that can be saved to file or sent over the network.
class SessionStream : public Object, public ClientControllerInterface {
 public:
  SessionStream(HostSession* host_session, bool save_replay);
  ~SessionStream() override;
  void SetTime(millisecs_t t);
  void AddScene(Scene* s);
  void RemoveScene(Scene* s);
  void StepScene(Scene* s);
  void AddNode(Node* n);
  void NodeOnCreate(Node* n);
  void RemoveNode(Node* n);
  void SetForegroundScene(Scene* sg);
  void AddMaterial(Material* m);
  void RemoveMaterial(Material* m);
  void AddMaterialComponent(Material* m, MaterialComponent* c);
  void AddSpazDef(SpazDef* d);
  void RemoveSpazDef(SpazDef* d);
  void AddDepiction(SceneDepiction* d);
  void RemoveDepiction(SceneDepiction* d);
  void AddTexture(SceneTexture* t);
  void RemoveTexture(SceneTexture* t);
  void AddMesh(SceneMesh* t);
  void RemoveMesh(SceneMesh* t);
  void AddSound(SceneSound* t);
  void RemoveSound(SceneSound* t);
  void AddCollisionMesh(SceneCollisionMesh* t);
  void RemoveCollisionMesh(SceneCollisionMesh* t);
  /// (kProtocolVersionAnimCurveCommand) Fold scope for bs.animate: commands
  /// ended while folding are held aside instead of appended;
  /// CommitFoldAnimCurve drops them and writes one kAddAnimCurve, and
  /// AbortFold replays them as they were (so a throw mid-animate leaves
  /// the stream exactly as the unfolded path would have).
  auto CanFoldAnimCurve() const -> bool {
    return host_session_ != nullptr && fold_anim_curves_;
  }
  void BeginFold();
  void AbortFold();
  /// (kProtocolVersionPackedCommands) Fold scope for newnode(attrs):
  /// commit writes one kAddNodeWithAttrs if the held commands are
  /// exactly [AddNode][packable attr sets...][NodeOnCreate] for node,
  /// else replays them as they were.
  auto CanFoldNodeCreate() const -> bool {
    return host_session_ != nullptr && pack_node_creates_;
  }
  void CommitFoldAddNode(Node* node);
  void CommitFoldAnimCurve(Scene* scene, Node* curve, Node* globals,
                           NodeAttributeUnbound* time_attr,
                           NodeAttributeUnbound* in_attr,
                           NodeAttributeUnbound* out_attr, Node* target,
                           NodeAttributeUnbound* target_attr, int64_t offset,
                           bool loop, const std::vector<int64_t>& times,
                           const std::vector<float>& values);
  void ConnectNodeAttribute(Node* src_node, NodeAttributeUnbound* src_attr,
                            Node* dst_node, NodeAttributeUnbound* dst_attr);
  void NodeMessage(Node* node, const char* buffer, size_t size);
  void SetNodeAttr(const NodeAttribute& attr, float val);
  void SetNodeAttr(const NodeAttribute& attr, int64_t val);
  void SetNodeAttr(const NodeAttribute& attr, bool val);
  void SetNodeAttr(const NodeAttribute& attr, const std::vector<float>& vals);
  void SetNodeAttr(const NodeAttribute& attr, const std::vector<int64_t>& vals);
  void SetNodeAttr(const NodeAttribute& attr, const std::string& val);
  void SetNodeAttr(const NodeAttribute& attr, Node* n);
  void SetNodeAttr(const NodeAttribute& attr, const std::vector<Node*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, Player* n);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<Material*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, SceneTexture* n);
  void SetNodeAttr(const NodeAttribute& attr, SpazDef* d);
  void SetNodeAttr(const NodeAttribute& attr, SceneDepiction* d);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<SceneTexture*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, SceneSound* n);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<SceneSound*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, SceneMesh* n);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<SceneMesh*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, SceneCollisionMesh* n);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<SceneCollisionMesh*>& vals);
  void PlaySoundAtPosition(SceneSound* sound, float volume, float x, float y,
                           float z);
  void PlaySound(SceneSound* sound, float volume);
  void EmitBGDynamics(const base::BGDynamicsEmission& e);
  void EmitCameraShake(float intensity);

  /// Request physical feedback (rumble/haptics) for whoever controls the
  /// given player. ``json_payload`` is an already-serialized dict of
  /// optional overrides; ``{}`` means a default impact. Clients that own
  /// a device on this player render it and everyone else drops it.
  ///
  /// The payload is opaque at this layer by design -- see the framing
  /// contract on SessionCommand::kInputDeviceFeedback before changing
  /// anything about how this is written.
  void EmitInputDeviceFeedback(int player_id, const std::string& json_payload);
  auto GetSoundID(SceneSound* s) -> int64_t;
  auto GetMaterialID(Material* m) -> int64_t;
  auto GetSpazDefID(SpazDef* d) -> int64_t;
  auto GetDepictionID(SceneDepiction* d) -> int64_t;

  /// Live (non-recycled) spaz-def entries in this stream's table.
  /// Debug/test introspection for the spaz-def churn test.
  auto live_spaz_def_count() -> size_t;
  void ScreenMessageBottom(const std::string& val, float r, float g, float b);
  void ScreenMessageTop(const std::string& val, float r, float g, float b,
                        SceneTexture* texture, SceneTexture* tint_texture,
                        float tint_r, float tint_g, float tint_b, float tint2_r,
                        float tint2_g, float tint2_b, float tint3_r,
                        float tint3_g, float tint3_b);
  /// A top message with a depiction for its icon (protocol 48+).
  void ScreenMessageTopDepiction(const std::string& val, float r, float g,
                                 float b, SceneDepiction* depiction);
  void OnClientConnected(ConnectionToClient* c) override;
  void OnClientDisconnected(ConnectionToClient* c) override;
  auto GetOutMessage() const -> std::vector<uint8_t>;

  /// Declare the session's full asset-package table (index -> apverid)
  /// up front. Emitted at the start of the live stream (so replays open
  /// with it) and at the top of baseline dumps (so every joining client
  /// receives it before any other session state). Also retained on this
  /// stream: subsequent asset adds emit compact indexed refs against it
  /// (kAdd*Indexed) for package-housed assets.
  void DeclareAssetPackages(const std::vector<std::string>& table);

 private:
  // Make sure various components are part of our stream.
  auto IsValidScene(Scene* val) -> bool;
  auto IsValidNode(Node* val) -> bool;
  auto IsValidTexture(SceneTexture* val) -> bool;
  auto IsValidMesh(SceneMesh* val) -> bool;
  auto IsValidSound(SceneSound* val) -> bool;
  auto IsValidCollisionMesh(SceneCollisionMesh* val) -> bool;
  auto IsValidMaterial(Material* val) -> bool;
  auto IsValidSpazDef(SpazDef* val) -> bool;
  auto IsValidDepiction(SceneDepiction* val) -> bool;

  void Flush();
  void AddMessageToReplay(const std::vector<uint8_t>& message);
  void Fail();

  /// Try emitting a compact indexed add (kAdd*Indexed) for an asset:
  /// maps possibly-legacy names into package space, then derives
  /// (pkg_idx, asset_idx) against the declared package table and the
  /// package's canonical sorted bucket keys. Returns false (emitting
  /// nothing) for local non-package assets or anything else that can't
  /// index; the caller then falls back to the legacy string form.
  auto TryAddAssetIndexed_(SessionCommand cmd, int64_t scene_id,
                           int64_t stream_id, const std::string& name,
                           const char* legacy_kind, AssetBucketKind bucket_kind)
      -> bool;

  /// Cached canonical sorted bucket keys, keyed by
  /// ``apverid + '\n' + bucket_id`` (immutable for exact apverids, so
  /// stream-lifetime caching is safe).
  std::unordered_map<std::string, std::vector<std::string>>
      asset_index_keys_cache_;
  std::vector<std::string> declared_packages_;

  void ShipSessionCommandsMessage();
  void SendPhysicsCorrection(bool blend);
  void EndCommand(bool is_time_set = false);
  void WriteString(const std::string& s);
  void WriteFloat(float val);
  void WriteFloats(size_t count, const float* vals);
  void WriteInts32(size_t count, const int32_t* vals);
  void WriteInts64(size_t count, const int64_t* vals);
  void WriteChars(size_t count, const char* vals);
  void WriteCommand(SessionCommand cmd);
  void WriteCommandInt32(SessionCommand cmd, int32_t value);
  void WriteCommandInt64(SessionCommand cmd, int64_t value);
  void WriteCommandInt32_2(SessionCommand cmd, int32_t value1, int32_t value2);
  void WriteCommandInt64_2(SessionCommand cmd, int64_t value1, int64_t value2);
  void WriteCommandInt32_3(SessionCommand cmd, int32_t value1, int32_t value2,
                           int32_t value3);
  void WriteCommandInt64_3(SessionCommand cmd, int64_t value1, int64_t value2,
                           int64_t value3);
  void WriteCommandInt32_4(SessionCommand cmd, int32_t value1, int32_t value2,
                           int32_t value3, int32_t value4);
  void WriteCommandInt64_4(SessionCommand cmd, int64_t value1, int64_t value2,
                           int64_t value3, int64_t value4);
  template <typename T>
  auto GetPointerCount(const std::vector<T*>& vec) -> size_t;
  template <typename T>
  auto GetFreeIndex(std::vector<T*>* vec, std::vector<size_t>* free_indices)
      -> size_t;
  template <typename T>
  void Add(T* val, std::vector<T*>* vec, std::vector<size_t>* free_indices);
  template <typename T>
  void Remove(T* val, std::vector<T*>* vec, std::vector<size_t>* free_indices);

  // Outgoing-stream accounting (BA_STREAM_STATS; test_game_run
  // --stream-stats): what we ship, by command type and by node type
  // for attr/message commands, plus corrections and each client
  // connection's wire bytes, logged every few seconds (ba.net INFO).
  void StatsNoteCommand_();
  void StatsMaybeLog_(millisecs_t real_time);
  bool stats_enabled_{};
  millisecs_t stats_last_log_time_{};
  int64_t stats_cmd_bytes_[256]{};
  int64_t stats_cmd_counts_[256]{};
  // Adjacency of the per-step framing commands within a message (what
  // an encoding-only merge could fold): time-step right after
  // time-step, scene-step right after time-step, time-step right after
  // scene-step. -1 = message empty.
  int stats_prev_cmd_{-1};
  int64_t stats_adj_ts_ts_{};
  int64_t stats_adj_ts_step_{};
  int64_t stats_adj_step_ts_{};
  std::unordered_map<std::string, int64_t> stats_node_type_bytes_;
  // "type.attr" -> (bytes, count) for the set-attr commands.
  std::unordered_map<std::string, std::pair<int64_t, int64_t>>
      stats_attr_bytes_;
  int64_t stats_correction_bytes_{};
  int64_t stats_correction_messages_{};
  int64_t stats_shipped_bytes_{};
  int64_t stats_shipped_messages_{};

  // Protocol 45+ framing: varint command lengths and zigzag-varint
  // integers (see kProtocolVersionCompactStream). Fixed at creation
  // from the protocol we host.
  bool compact_{};
  // kProtocolVersionMergedStep: SetTime folds a trailing scene-step
  // command into kStepSceneGraphAndTime. These track the last command
  // appended to the unshipped message (offset, id) and the scene of the
  // last step written; -1 = nothing to fold.
  bool merge_steps_{};
  bool pack_node_creates_{};
  // The command before last_cmd_* (for the three-way time-step fold)
  // and the delta of the last plain kBaseTimeStep written (-1 = none).
  int prev_cmd_offset_{-1};
  int prev_cmd_id_{-1};
  int64_t last_cmd_stats_size_{};
  int64_t prev_cmd_stats_size_{};
  int64_t last_time_step_delta_{-1};
  bool fold_anim_curves_{};
  bool folding_{};
  std::vector<std::vector<uint8_t>> fold_cmds_;
  int last_cmd_offset_{-1};
  int last_cmd_id_{-1};
  int64_t last_step_scene_id_{-1};
  int64_t stats_last_cmd_size_{};
  // BA_RELIABLE_CORRECTIONS (test_game_run --reliable-corrections): keep
  // physics corrections on the reliable stream (the A/B switch).
  bool reliable_corrections_{};
  void WriteInt_(int32_t value);

  HostSession* host_session_;
  millisecs_t next_flush_time_{};

  // Individual command going into the commands-messages.
  std::vector<uint8_t> out_command_;

  // The complete message full of commands.
  std::vector<uint8_t> out_message_;
  std::vector<ConnectionToClient*> connections_to_clients_;
  std::vector<ConnectionToClient*> connections_to_clients_ignored_;
  classic::ClassicAppMode* app_mode_;
  bool writing_replay_{};
  millisecs_t last_physics_correction_time_{};
  millisecs_t last_send_time_{};
  // Ship gating (see EndCommand): the foreground scene has stepped
  // since the last ship (ships at the next time-set), or some other
  // scene has (rides along, or ships on its own after a couple of
  // steps' worth of base time if nothing else is shipping).
  bool foreground_step_pending_{};
  bool other_step_pending_{};
  millisecs_t last_ship_base_time_{};
  millisecs_t time_{};
  std::vector<Scene*> scenes_;
  std::vector<size_t> free_indices_scene_graphs_;
  std::vector<Node*> nodes_;
  std::vector<size_t> free_indices_nodes_;
  std::vector<Material*> materials_;
  std::vector<size_t> free_indices_materials_;
  std::vector<SpazDef*> spaz_defs_;
  std::vector<size_t> free_indices_spaz_defs_;
  std::vector<SceneDepiction*> depictions_;
  std::vector<size_t> free_indices_depictions_;
  std::vector<SceneTexture*> textures_;
  std::vector<size_t> free_indices_textures_;
  std::vector<SceneMesh*> meshes_;
  std::vector<size_t> free_indices_meshes_;
  std::vector<SceneSound*> sounds_;
  std::vector<size_t> free_indices_sounds_;
  std::vector<SceneCollisionMesh*> collision_meshes_;
  std::vector<size_t> free_indices_collision_meshes_;
  ReplayWriter* replay_writer_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SESSION_STREAM_H_
