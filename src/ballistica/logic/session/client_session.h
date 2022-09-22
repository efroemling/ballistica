// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_LOGIC_SESSION_CLIENT_SESSION_H_
#define BALLISTICA_LOGIC_SESSION_CLIENT_SESSION_H_

#include <list>
#include <string>
#include <vector>

#include "ballistica/logic/client_controller_interface.h"
#include "ballistica/logic/session/session.h"

namespace ballistica {

class ClientSession : public Session {
 public:
  ClientSession();
  ~ClientSession() override;

  // Allows for things like replay speed.
  virtual auto GetActualTimeAdvance(int advance_in) -> int {
    return advance_in;
  }
  auto Update(int time_advance) -> void override;
  auto Draw(FrameDef* f) -> void override;
  virtual auto HandleSessionMessage(const std::vector<uint8_t>& buffer) -> void;
  auto Reset(bool rewind) -> void;
  auto GetForegroundContext() -> Context override;
  auto DoesFillScreen() const -> bool override;
  auto ScreenSizeChanged() -> void override;
  auto LanguageChanged() -> void override;
  auto GetCorrectionMessages(bool blend,
                             std::vector<std::vector<uint8_t> >* messages)
      -> void;

  /// Called when attempting to step without input data available.
  virtual auto OnCommandBufferUnderrun() -> void {}

  virtual auto OnBaseTimeStepAdded(int step) -> void {}

  // Returns existing objects; throws exceptions if not available.
  auto GetScene(int id) const -> Scene*;
  auto GetNode(int id) const -> Node*;
  auto GetTexture(int id) const -> Texture*;
  auto GetModel(int id) const -> Model*;
  auto GetCollideModel(int id) const -> CollideModel*;
  auto GetMaterial(int id) const -> Material*;
  auto GetSound(int id) const -> Sound*;

  auto base_time_buffered() const { return base_time_buffered_; }
  auto consume_rate() const { return consume_rate_; }
  auto set_consume_rate(float val) { consume_rate_ = val; }
  auto target_base_time() const { return target_base_time_; }
  auto base_time() const { return base_time_; }
  auto shutting_down() const { return shutting_down_; }

  auto scenes() const -> const std::vector<Object::Ref<Scene> >& {
    return scenes_;
  }
  auto nodes() const -> const std::vector<Object::WeakRef<Node> >& {
    return nodes_;
  }
  auto textures() const -> const std::vector<Object::Ref<Texture> >& {
    return textures_;
  }
  auto models() const -> const std::vector<Object::Ref<Model> >& {
    return models_;
  }
  auto sounds() const -> const std::vector<Object::Ref<Sound> >& {
    return sounds_;
  }
  auto collide_models() const
      -> const std::vector<Object::Ref<CollideModel> >& {
    return collide_models_;
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
  virtual auto OnReset(bool rewind) -> void;
  virtual auto FetchMessages() -> void {}
  virtual void Error(const std::string& description);
  auto End() -> void;
  auto DumpFullState(SceneStream* out) -> void override;

  /// Reset target base time to equal current. This can be used during command
  /// buffer underruns to cause playback to pause momentarily instead of
  /// skipping ahead to catch up. Generally desired for replays but not for
  /// net-play.
  auto ResetTargetBaseTime() -> void { target_base_time_ = base_time_; }

 private:
  auto ClearSessionObjs() -> void;
  auto AddCommand(const std::vector<uint8_t>& command) -> void;

  auto ReadByte() -> uint8_t;
  auto ReadInt32() -> int32_t;
  auto ReadInt32_2(int32_t* vals) -> void;
  auto ReadInt32_3(int32_t* vals) -> void;
  auto ReadInt32_4(int32_t* vals) -> void;
  auto ReadString() -> std::string;
  auto ReadFloat() -> float;
  auto ReadFloats(int count, float* vals) -> void;
  auto ReadInt32s(int count, int32_t* vals) -> void;
  auto ReadChars(int count, char* vals) -> void;

  // Ready-to-go commands.
  std::list<std::vector<uint8_t> > commands_;

  // Commands being built up for the next time step (we need to ship timesteps
  // as a whole).
  std::list<std::vector<uint8_t> > commands_pending_;
  std::vector<uint8_t> current_cmd_;
  uint8_t* current_cmd_ptr_{};
  int base_time_buffered_{};
  bool shutting_down_{};

  millisecs_t base_time_{};
  double target_base_time_{};
  float consume_rate_{1.0f};

  std::vector<Object::Ref<Scene> > scenes_;
  std::vector<Object::WeakRef<Node> > nodes_;
  std::vector<Object::Ref<Texture> > textures_;
  std::vector<Object::Ref<Model> > models_;
  std::vector<Object::Ref<Sound> > sounds_;
  std::vector<Object::Ref<CollideModel> > collide_models_;
  std::vector<Object::Ref<Material> > materials_;
};

}  // namespace ballistica

#endif  // BALLISTICA_LOGIC_SESSION_CLIENT_SESSION_H_
