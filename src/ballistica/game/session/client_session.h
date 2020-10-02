// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SESSION_CLIENT_SESSION_H_
#define BALLISTICA_GAME_SESSION_CLIENT_SESSION_H_

#include <list>
#include <string>
#include <vector>

#include "ballistica/game/client_controller_interface.h"
#include "ballistica/game/session/session.h"

namespace ballistica {

class ClientSession : public Session {
 public:
  ClientSession();
  ~ClientSession() override;

  // Allows for things like replay speed.
  virtual auto GetActualTimeAdvance(int advance_in) -> int {
    return advance_in;
  }
  void Update(int time_advance) override;
  void Draw(FrameDef* f) override;
  virtual void HandleSessionMessage(const std::vector<uint8_t>& buffer);
  void Reset(bool rewind);
  auto GetForegroundContext() -> Context override;
  auto DoesFillScreen() const -> bool override;
  void ScreenSizeChanged() override;
  void LanguageChanged() override;
  auto shutting_down() const -> bool { return shutting_down_; }
  void GetCorrectionMessages(bool blend,
                             std::vector<std::vector<uint8_t> >* messages);

  // Called when attempting to step without input data available.
  virtual void OnCommandBufferUnderrun() {}

  // Returns existing objects; throws exceptions if not available.
  auto GetScene(int id) const -> Scene*;
  auto GetNode(int id) const -> Node*;
  auto GetTexture(int id) const -> Texture*;
  auto GetModel(int id) const -> Model*;
  auto GetCollideModel(int id) const -> CollideModel*;
  auto GetMaterial(int id) const -> Material*;
  auto GetSound(int id) const -> Sound*;

 protected:
  virtual void OnReset(bool rewind);
  virtual void FetchMessages() {}
  int steps_on_list_;
  std::list<std::vector<uint8_t> > commands_;  // ready-to-go commands
  virtual void Error(const std::string& description);
  void End();
  millisecs_t base_time_;
  double target_base_time_ = 0.0f;
  bool shutting_down_;
  std::vector<int> least_buffered_count_list_;  // move this to net-client?..
  std::vector<int> most_buffered_count_list_;
  int buffer_count_list_index_;
  int adjust_counter_;
  float correction_ = 1.0f;
  float largest_spike_smoothed_ = 0.0f;
  float low_pass_smoothed_ = 0.0f;

 private:
  void ClearSessionObjs();
  void AddCommand(const std::vector<uint8_t>& command);

  // commands being built up for the next time step
  // (we want to be able to run *everything* for a given timestep at once
  // to avoid drawing things in half-changed states, etc)
  std::list<std::vector<uint8_t> > commands_pending_;  // commands for the next
  std::vector<uint8_t> current_cmd_;
  uint8_t* current_cmd_ptr_;
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

 protected:
  std::vector<Object::Ref<Scene> > scenes_;
  std::vector<Object::WeakRef<Node> > nodes_;
  std::vector<Object::Ref<Texture> > textures_;
  std::vector<Object::Ref<Model> > models_;
  std::vector<Object::Ref<Sound> > sounds_;
  std::vector<Object::Ref<CollideModel> > collide_models_;
  std::vector<Object::Ref<Material> > materials_;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SESSION_CLIENT_SESSION_H_
