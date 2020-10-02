// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_GAME_STREAM_H_
#define BALLISTICA_GAME_GAME_STREAM_H_

#include <string>
#include <vector>

#include "ballistica/core/object.h"
#include "ballistica/game/client_controller_interface.h"

namespace ballistica {

// A mechanism for dumping a live session or session-creation-commands to a
// stream of messages that can be saved to file or sent over the network.
class GameStream : public Object, public ClientControllerInterface {
 public:
  GameStream(HostSession* host_session, bool saveReplay);
  ~GameStream() override;
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
  void AddTexture(Texture* t);
  void RemoveTexture(Texture* t);
  void AddModel(Model* t);
  void RemoveModel(Model* t);
  void AddSound(Sound* t);
  void RemoveSound(Sound* t);
  void AddData(Data* d);
  void RemoveData(Data* d);
  void AddCollideModel(CollideModel* t);
  void RemoveCollideModel(CollideModel* t);
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
  void SetNodeAttr(const NodeAttribute& attr, Texture* n);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<Texture*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, Sound* n);
  void SetNodeAttr(const NodeAttribute& attr, const std::vector<Sound*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, Model* n);
  void SetNodeAttr(const NodeAttribute& attr, const std::vector<Model*>& vals);
  void SetNodeAttr(const NodeAttribute& attr, CollideModel* n);
  void SetNodeAttr(const NodeAttribute& attr,
                   const std::vector<CollideModel*>& vals);
  void PlaySoundAtPosition(Sound* sound, float volume, float x, float y,
                           float z);
  void PlaySound(Sound* sound, float volume);
  void EmitBGDynamics(const BGDynamicsEmission& e);
  auto GetSoundID(Sound* s) -> int64_t;
  auto GetMaterialID(Material* m) -> int64_t;
  void ScreenMessageBottom(const std::string& val, float r, float g, float b);
  void ScreenMessageTop(const std::string& val, float r, float g, float b,
                        Texture* texture, Texture* tint_texture, float tint_r,
                        float tint_g, float tint_b, float tint2_r,
                        float tint2_g, float tint2_b);
  void OnClientConnected(ConnectionToClient* c) override;
  void OnClientDisconnected(ConnectionToClient* c) override;
  auto GetOutMessage() const -> std::vector<uint8_t>;

 private:
  HostSession* host_session_;

  // Make sure the scene is in our stream.
  auto IsValidScene(Scene* val) -> bool;
  auto IsValidNode(Node* val) -> bool;
  auto IsValidTexture(Texture* val) -> bool;
  auto IsValidModel(Model* val) -> bool;
  auto IsValidSound(Sound* val) -> bool;
  auto IsValidData(Data* val) -> bool;
  auto IsValidCollideModel(CollideModel* val) -> bool;
  auto IsValidMaterial(Material* val) -> bool;
  millisecs_t next_flush_time_;
  void Flush();
  void AddMessageToReplay(const std::vector<uint8_t>& message);

  // Individual command going into the commands-messages.
  std::vector<uint8_t> out_command_;

  // The complete message full of commands.
  std::vector<uint8_t> out_message_;
  std::vector<ConnectionToClient*> connections_to_clients_;
  std::vector<ConnectionToClient*> connections_to_clients_ignored_;
  bool writing_replay_;
  void Fail();
  millisecs_t last_physics_correction_time_;
  millisecs_t last_send_time_;
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

#endif  // BALLISTICA_GAME_GAME_STREAM_H_
