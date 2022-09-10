// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_SCENE_STREAM_H_
#define BALLISTICA_SCENE_SCENE_STREAM_H_

#include <string>
#include <vector>

#include "ballistica/core/object.h"
#include "ballistica/game/client_controller_interface.h"

namespace ballistica {

// A mechanism for dumping a live session or session-creation-commands to a
// stream of messages that can be saved to file or sent over the network.
class SceneStream : public Object, public ClientControllerInterface {
 public:
  SceneStream(HostSession* host_session, bool save_replay);
  ~SceneStream() override;
  auto SetTime(millisecs_t t) -> void;
  auto AddScene(Scene* s) -> void;
  auto RemoveScene(Scene* s) -> void;
  auto StepScene(Scene* s) -> void;
  auto AddNode(Node* n) -> void;
  auto NodeOnCreate(Node* n) -> void;
  auto RemoveNode(Node* n) -> void;
  auto SetForegroundScene(Scene* sg) -> void;
  auto AddMaterial(Material* m) -> void;
  auto RemoveMaterial(Material* m) -> void;
  auto AddMaterialComponent(Material* m, MaterialComponent* c) -> void;
  auto AddTexture(Texture* t) -> void;
  auto RemoveTexture(Texture* t) -> void;
  auto AddModel(Model* t) -> void;
  auto RemoveModel(Model* t) -> void;
  auto AddSound(Sound* t) -> void;
  auto RemoveSound(Sound* t) -> void;
  auto AddData(Data* d) -> void;
  auto RemoveData(Data* d) -> void;
  auto AddCollideModel(CollideModel* t) -> void;
  auto RemoveCollideModel(CollideModel* t) -> void;
  auto ConnectNodeAttribute(Node* src_node, NodeAttributeUnbound* src_attr,
                            Node* dst_node, NodeAttributeUnbound* dst_attr)
      -> void;
  auto NodeMessage(Node* node, const char* buffer, size_t size) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, float val) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, int64_t val) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, bool val) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::vector<float>& vals)
      -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::vector<int64_t>& vals)
      -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::string& val) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, Node* n) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::vector<Node*>& vals)
      -> void;
  auto SetNodeAttr(const NodeAttribute& attr, Player* n) -> void;
  auto SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<Material*>& vals) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, Texture* n) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::vector<Texture*>& vals)
      -> void;
  auto SetNodeAttr(const NodeAttribute& attr, Sound* n) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::vector<Sound*>& vals)
      -> void;
  auto SetNodeAttr(const NodeAttribute& attr, Model* n) -> void;
  auto SetNodeAttr(const NodeAttribute& attr, const std::vector<Model*>& vals)
      -> void;
  auto SetNodeAttr(const NodeAttribute& attr, CollideModel* n) -> void;
  auto SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<CollideModel*>& vals) -> void;
  auto PlaySoundAtPosition(Sound* sound, float volume, float x, float y,
                           float z) -> void;
  auto PlaySound(Sound* sound, float volume) -> void;
  auto EmitBGDynamics(const BGDynamicsEmission& e) -> void;
  auto GetSoundID(Sound* s) -> int64_t;
  auto GetMaterialID(Material* m) -> int64_t;
  auto ScreenMessageBottom(const std::string& val, float r, float g, float b)
      -> void;
  auto ScreenMessageTop(const std::string& val, float r, float g, float b,
                        Texture* texture, Texture* tint_texture, float tint_r,
                        float tint_g, float tint_b, float tint2_r,
                        float tint2_g, float tint2_b) -> void;
  auto OnClientConnected(ConnectionToClient* c) -> void override;
  auto OnClientDisconnected(ConnectionToClient* c) -> void override;
  auto GetOutMessage() const -> std::vector<uint8_t>;

 private:
  // Make sure various components are part of our stream.
  auto IsValidScene(Scene* val) -> bool;
  auto IsValidNode(Node* val) -> bool;
  auto IsValidTexture(Texture* val) -> bool;
  auto IsValidModel(Model* val) -> bool;
  auto IsValidSound(Sound* val) -> bool;
  auto IsValidData(Data* val) -> bool;
  auto IsValidCollideModel(CollideModel* val) -> bool;
  auto IsValidMaterial(Material* val) -> bool;

  auto Flush() -> void;
  auto AddMessageToReplay(const std::vector<uint8_t>& message) -> void;
  auto Fail() -> void;

  auto ShipSessionCommandsMessage() -> void;
  auto SendPhysicsCorrection(bool blend) -> void;
  auto EndCommand(bool is_time_set = false) -> void;
  auto WriteString(const std::string& s) -> void;
  auto WriteFloat(float val) -> void;
  auto WriteFloats(size_t count, const float* vals) -> void;
  auto WriteInts32(size_t count, const int32_t* vals) -> void;
  auto WriteInts64(size_t count, const int64_t* vals) -> void;
  auto WriteChars(size_t count, const char* vals) -> void;
  auto WriteCommand(SessionCommand cmd) -> void;
  auto WriteCommandInt32(SessionCommand cmd, int32_t value) -> void;
  auto WriteCommandInt64(SessionCommand cmd, int64_t value) -> void;
  auto WriteCommandInt32_2(SessionCommand cmd, int32_t value1, int32_t value2)
      -> void;
  auto WriteCommandInt64_2(SessionCommand cmd, int64_t value1, int64_t value2)
      -> void;
  auto WriteCommandInt32_3(SessionCommand cmd, int32_t value1, int32_t value2,
                           int32_t value3) -> void;
  auto WriteCommandInt64_3(SessionCommand cmd, int64_t value1, int64_t value2,
                           int64_t value3) -> void;
  auto WriteCommandInt32_4(SessionCommand cmd, int32_t value1, int32_t value2,
                           int32_t value3, int32_t value4) -> void;
  auto WriteCommandInt64_4(SessionCommand cmd, int64_t value1, int64_t value2,
                           int64_t value3, int64_t value4) -> void;
  template <typename T>
  auto GetPointerCount(const std::vector<T*>& vec) -> size_t;
  template <typename T>
  auto GetFreeIndex(std::vector<T*>* vec, std::vector<size_t>* free_indices)
      -> size_t;
  template <typename T>
  auto Add(T* val, std::vector<T*>* vec, std::vector<size_t>* free_indices)
      -> void;
  template <typename T>
  auto Remove(T* val, std::vector<T*>* vec, std::vector<size_t>* free_indices)
      -> void;

  HostSession* host_session_;
  millisecs_t next_flush_time_;

  // Individual command going into the commands-messages.
  std::vector<uint8_t> out_command_;

  // The complete message full of commands.
  std::vector<uint8_t> out_message_;
  std::vector<ConnectionToClient*> connections_to_clients_;
  std::vector<ConnectionToClient*> connections_to_clients_ignored_;
  bool writing_replay_;
  millisecs_t last_physics_correction_time_;
  millisecs_t last_send_time_;
  millisecs_t time_;
  std::vector<Scene*> scenes_;
  std::vector<size_t> free_indices_scene_graphs_;
  std::vector<Node*> nodes_;
  std::vector<size_t> free_indices_nodes_;
  std::vector<Material*> materials_;
  std::vector<size_t> free_indices_materials_;
  std::vector<Texture*> textures_;
  std::vector<size_t> free_indices_textures_;
  std::vector<Model*> models_;
  std::vector<size_t> free_indices_models_;
  std::vector<Sound*> sounds_;
  std::vector<size_t> free_indices_sounds_;
  std::vector<Data*> datas_;
  std::vector<size_t> free_indices_datas_;
  std::vector<CollideModel*> collide_models_;
  std::vector<size_t> free_indices_collide_models_;
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_SCENE_STREAM_H_
