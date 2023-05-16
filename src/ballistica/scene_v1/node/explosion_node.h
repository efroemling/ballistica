// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_EXPLOSION_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_EXPLOSION_NODE_H_

#include <vector>

#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class ExplosionNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit ExplosionNode(Scene* scene);
  ~ExplosionNode() override;
  void Draw(base::FrameDef* frame_def) override;
  void Step() override;
  auto position() const -> std::vector<float> { return position_; }
  void set_position(const std::vector<float>& vals);
  auto velocity() const -> std::vector<float> { return velocity_; }
  void set_velocity(const std::vector<float>& vals);
  auto radius() const -> float { return radius_; }
  void set_radius(float val) { radius_ = val; }
  auto color() const -> std::vector<float> { return color_; }
  void set_color(const std::vector<float>& vals);
  auto big() const -> bool { return big_; }
  void set_big(bool val);

 private:
  millisecs_t birth_time_;
  bool check_draw_distortion_{true};
  bool big_{};
  bool draw_distortion_{};
  bool have_distortion_lock_{};
  float radius_{1.0f};
  std::vector<float> position_{0.0f, 0.0f, 0.0f};
  std::vector<float> velocity_{0.0f, 0.0f, 0.0f};
  std::vector<float> color_{0.9f, 0.3f, 0.1f};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_EXPLOSION_NODE_H_
