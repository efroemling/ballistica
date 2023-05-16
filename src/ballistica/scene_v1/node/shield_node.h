// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_SHIELD_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_SHIELD_NODE_H_

#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

class ShieldNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit ShieldNode(Scene* scene);
  ~ShieldNode() override;
  void Draw(base::FrameDef* frame_def) override;
  void Step() override;
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& vals);
  auto radius() const -> float { return radius_; }
  void set_radius(float val) { radius_ = val; }
  auto hurt() const -> float { return hurt_; }
  void SetHurt(float val);
  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& vals);
  auto always_show_health_bar() const -> bool {
    return always_show_health_bar_;
  }
  void set_always_show_health_bar(bool val) { always_show_health_bar_ = val; }

 private:
#if !BA_HEADLESS_BUILD
  base::BGDynamicsShadow shadow_;
#endif  // BA_HEADLESS_BUILD
  bool always_show_health_bar_ = false;
  float hurt_smoothed_ = 1.0f;
  millisecs_t last_hurt_change_time_ = 0;
  float d_r_scale_ = 0.0f;
  float r_scale_ = 0.0f;
  std::vector<float> position_ = {0.0f, 0.0f, 0.0f};
  std::vector<float> color_ = {0.6f, 0.4f, 0.1f};
  float radius_ = 1.0f;
  float hurt_ = 0.0f;
  float flash_ = 0.0f;
  float hurt_rand_ = 0.0f;
  int rot_count_ = 0;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_SHIELD_NODE_H_
