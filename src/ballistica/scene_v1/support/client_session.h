// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_H_

#include <list>
#include <string>
#include <vector>

#include "ballistica/scene_v1/support/client_controller_interface.h"
#include "ballistica/scene_v1/support/session.h"

namespace ballistica::scene_v1 {

class ClientSession : public Session {
 public:
  ClientSession();
  ~ClientSession() override;

  // Allows for things like replay speed.
  virtual auto GetActualTimeAdvanceMillisecs(double base_advance_millisecs)
      -> double {
    return base_advance_millisecs;
  }
  void Update(int time_advance_millisecs, double time_advance) override;
  void Draw(base::FrameDef* f) override;
  virtual void HandleSessionMessage(const std::vector<uint8_t>& buffer);
  void Reset(bool rewind);
  auto GetForegroundContext() -> base::ContextRef override;
  auto DoesFillScreen() const -> bool override;
  void OnScreenSizeChange() override;
  void LanguageChanged() override;
  void GetCorrectionMessages(bool blend,
                             std::vector<std::vector<uint8_t> >* messages);

  /// Called when attempting to step without input data available.
  virtual void OnCommandBufferUnderrun() {}

  virtual void OnBaseTimeStepAdded(int step) {}

  // Returns existing objects; throws exceptions if not available.
  auto GetScene(int id) const -> Scene*;
  auto GetNode(int id) const -> Node*;
  auto GetTexture(int id) const -> SceneTexture*;
  auto GetMesh(int id) const -> SceneMesh*;
  auto GetCollisionMesh(int id) const -> SceneCollisionMesh*;
  auto GetMaterial(int id) const -> Material*;
  auto GetSound(int id) const -> SceneSound*;

  auto base_time_buffered() const { return base_time_buffered_; }
  auto consume_rate() const { return consume_rate_; }
  auto set_consume_rate(float val) { consume_rate_ = val; }
  auto target_base_time() const { return target_base_time_millisecs_; }
  auto base_time() const { return base_time_millisecs_; }
  auto shutting_down() const { return shutting_down_; }

  auto scenes() const -> const std::vector<Object::Ref<Scene> >& {
    return scenes_;
  }
  auto nodes() const -> const std::vector<Object::WeakRef<Node> >& {
    return nodes_;
  }
  auto textures() const -> const std::vector<Object::Ref<SceneTexture> >& {
    return textures_;
  }
  auto meshes() const -> const std::vector<Object::Ref<SceneMesh> >& {
    return meshes_;
  }
  auto sounds() const -> const std::vector<Object::Ref<SceneSound> >& {
    return sounds_;
  }
  auto collision_meshes() const
      -> const std::vector<Object::Ref<SceneCollisionMesh> >& {
    return collision_meshes_;
  }
  auto materials() const -> const std::vector<Object::Ref<Material> >& {
    return materials_;
  }
  auto commands() const -> const std::list<std::vector<uint8_t> >& {
    return commands_;
  }
  auto add_end_of_file_command() {
    commands_.emplace_back(1, static_cast<uint8_t>(SessionCommand::kEndOfFile));
  }
  virtual void OnReset(bool rewind);
  virtual void FetchMessages() {}
  virtual void Error(const std::string& description);
  void End();
  void DumpFullState(SessionStream* out) override;

  /// Reset target base time to equal current. This can be used during command
  /// buffer underruns to cause playback to pause momentarily instead of
  /// skipping ahead to catch up. Generally desired for replays but not for
  /// net-play.
  void ResetTargetBaseTime() {
    target_base_time_millisecs_ = base_time_millisecs_;
  }

 private:
  void ClearSessionObjs();
  void AddCommand(const std::vector<uint8_t>& command);

  auto ReadByte() -> uint8_t;
  auto ReadInt32() -> int32_t;
  void ReadInt32_2(int32_t* vals);
  void ReadInt32_3(int32_t* vals);
  void ReadInt32_4(int32_t* vals);
  auto ReadString() -> std::string;
  auto ReadFloat() -> float;
  void ReadFloats(int count, float* vals);
  void ReadInt32s(int count, int32_t* vals);
  void ReadChars(int count, char* vals);

  // Ready-to-go commands.
  std::list<std::vector<uint8_t> > commands_;

  // Commands being built up for the next time step (we need to ship timesteps
  // as a whole).
  std::list<std::vector<uint8_t> > commands_pending_;
  std::vector<uint8_t> current_cmd_;
  uint8_t* current_cmd_ptr_{};
  int base_time_buffered_{};
  bool shutting_down_{};

  millisecs_t base_time_millisecs_{};
  double target_base_time_millisecs_{};
  float consume_rate_{1.0f};

  std::vector<Object::Ref<Scene> > scenes_;
  std::vector<Object::WeakRef<Node> > nodes_;
  std::vector<Object::Ref<SceneTexture> > textures_;
  std::vector<Object::Ref<SceneMesh> > meshes_;
  std::vector<Object::Ref<SceneSound> > sounds_;
  std::vector<Object::Ref<SceneCollisionMesh> > collision_meshes_;
  std::vector<Object::Ref<Material> > materials_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_H_
