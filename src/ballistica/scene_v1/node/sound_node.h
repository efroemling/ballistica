// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_SOUND_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_SOUND_NODE_H_

#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class SoundNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit SoundNode(Scene* scene);
  ~SoundNode() override;
  void Step() override;
  auto position() const -> const std::vector<float>& { return position_; }
  void SetPosition(const std::vector<float>& vals);
  auto volume() const -> float { return volume_; }
  void SetVolume(float val);
  auto positional() const -> bool { return positional_; }
  void SetPositional(bool val);
  auto music() const -> bool { return music_; }
  void SetMusic(bool val);
  auto loop() const -> bool { return loop_; }
  void SetLoop(bool val);
  auto sound() const -> SceneSound* { return sound_.Get(); }
  void SetSound(SceneSound* s);

 private:
  Object::Ref<SceneSound> sound_;
  millisecs_t last_position_update_time_{};
  std::vector<float> position_{0.0f, 0.0f, 0.0f};
  float volume_{1.0f};
  bool positional_{true};
  bool position_dirty_{true};
  bool music_{};
  bool loop_{true};
  uint32_t play_id_{};
  bool playing_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_SOUND_NODE_H_
