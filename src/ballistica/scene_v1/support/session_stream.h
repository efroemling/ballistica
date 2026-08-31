// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SESSION_STREAM_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SESSION_STREAM_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/classic/classic.h"
#include "ballistica/scene_v1/support/client_controller_interface.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

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
  void AddTexture(SceneTexture* t);
  void RemoveTexture(SceneTexture* t);
  void AddMesh(SceneMesh* t);
  void RemoveMesh(SceneMesh* t);
  void AddSound(SceneSound* t);
  void RemoveSound(SceneSound* t);
  void AddData(SceneDataAsset* d);
  void RemoveData(SceneDataAsset* d);
  void AddCollisionMesh(SceneCollisionMesh* t);
  void RemoveCollisionMesh(SceneCollisionMesh* t);
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
  void ScreenMessageBottom(const std::string& val, float r, float g, float b);
  void ScreenMessageTop(const std::string& val, float r, float g, float b,
                        SceneTexture* texture, SceneTexture* tint_texture,
                        float tint_r, float tint_g, float tint_b, float tint2_r,
                        float tint2_g, float tint2_b);
  void OnClientConnected(ConnectionToClient* c) override;
  void OnClientDisconnected(ConnectionToClient* c) override;
  auto GetOutMessage() const -> std::vector<uint8_t>;

  /// Same as GetOutMessage but hands over the buffer rather than
  /// copying it. Only valid on a temp dump stream that is about to be
  /// discarded; a keyframe is large enough that the copy is worth
  /// avoiding.
  auto TakeOutMessage() -> std::vector<uint8_t>;

  /// Declare the session's full asset-package table (index -> apverid)
  /// up front. Emitted at the start of the live stream (so replays open
  /// with it) and at the top of baseline dumps (so every joining client
  /// receives it before any other session state). Also retained on this
  /// stream: subsequent asset adds emit compact indexed refs against it
  /// (kAdd*Indexed) for package-housed assets.
  void DeclareAssetPackages(const std::vector<std::string>& table);

  /// Build a keyframe: a complete snapshot of our host-session's current
  /// state, as the same messages a joining client would be sent. Returns
  /// the baseline (a BA_MESSAGE_SESSION_COMMANDS blob); any dynamics
  /// corrections that go with it are appended to `corrections` (pass
  /// nullptr to skip gathering those). Flushes pending commands first,
  /// since our state already reflects them and re-sending them on top of
  /// the snapshot would double-apply them.
  auto BuildKeyframe(std::vector<std::vector<uint8_t>>* corrections)
      -> std::vector<uint8_t>;

  /// Our rolling instant-replay window, or nullptr if we're not keeping
  /// one (disabled by config, or we're not a live host stream).
  auto instant_replay_recorder() const -> InstantReplayRecorder* {
    return instant_replay_recorder_;
  }

 private:
  // Make sure various components are part of our stream.
  auto IsValidScene(Scene* val) -> bool;
  auto IsValidNode(Node* val) -> bool;
  auto IsValidTexture(SceneTexture* val) -> bool;
  auto IsValidMesh(SceneMesh* val) -> bool;
  auto IsValidSound(SceneSound* val) -> bool;
  auto IsValidData(SceneDataAsset* val) -> bool;
  auto IsValidCollisionMesh(SceneCollisionMesh* val) -> bool;
  auto IsValidMaterial(Material* val) -> bool;

  void Flush();
  void AddMessageToReplay(const std::vector<uint8_t>& message);
  void Fail();

  /// Cut a keyframe if enough stream time has passed since the last one.
  /// Driven from SetTime, so the cadence follows game time rather than
  /// wall time and a paused or slow session doesn't accumulate them.
  void MaybeEmitKeyframe_();

  /// Wrap a baseline + its corrections into a BA_MESSAGE_SESSION_KEYFRAME
  /// record (see base/networking/networking.h for the layout).
  static auto PackKeyframeRecord_(
      millisecs_t base_time, const std::vector<uint8_t>& baseline,
      const std::vector<std::vector<uint8_t>>& corrections)
      -> std::vector<uint8_t>;

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
  millisecs_t last_instant_replay_keyframe_time_{};
  millisecs_t last_replay_keyframe_time_{};
  InstantReplayRecorder* instant_replay_recorder_{};
  millisecs_t last_physics_correction_time_{};
  millisecs_t last_send_time_{};
  millisecs_t time_{};
  std::vector<Scene*> scenes_;
  std::vector<size_t> free_indices_scene_graphs_;
  std::vector<Node*> nodes_;
  std::vector<size_t> free_indices_nodes_;
  std::vector<Material*> materials_;
  std::vector<size_t> free_indices_materials_;
  std::vector<SceneTexture*> textures_;
  std::vector<size_t> free_indices_textures_;
  std::vector<SceneMesh*> meshes_;
  std::vector<size_t> free_indices_meshes_;
  std::vector<SceneSound*> sounds_;
  std::vector<size_t> free_indices_sounds_;
  std::vector<SceneDataAsset*> datas_;
  std::vector<size_t> free_indices_datas_;
  std::vector<SceneCollisionMesh*> collision_meshes_;
  std::vector<size_t> free_indices_collision_meshes_;
  ReplayWriter* replay_writer_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SESSION_STREAM_H_
