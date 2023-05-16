// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_LIGHT_NODE_H_
#define BALLISTICA_SCENE_V1_NODE_LIGHT_NODE_H_

#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"
#include "ballistica/scene_v1/node/node.h"

namespace ballistica::scene_v1 {

// A light source
class LightNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit LightNode(Scene* scene);
  void Draw(base::FrameDef* frame_def) override;
  void Step() override;
  auto position() const -> std::vector<float> { return position_; }
  void SetPosition(const std::vector<float>& val);
  auto intensity() const -> float { return intensity_; }
  void SetIntensity(float val);
  auto volume_intensity_scale() const -> float {
    return volume_intensity_scale_;
  }
  void SetVolumeIntensityScale(float val);
  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& val);
  auto radius() const -> float { return radius_; }
  void SetRadius(float val);
  auto lights_volumes() const -> bool { return lights_volumes_; }
  void set_lights_volumes(bool val) { lights_volumes_ = val; }
  auto height_attenuated() const -> bool { return height_attenuated_; }
  void set_height_attenuated(bool val) { height_attenuated_ = val; }

 private:
  auto GetVolumeLightIntensity() -> float;
#if !BA_HEADLESS_BUILD
  base::BGDynamicsShadow shadow_{0.2f};
  Object::Ref<base::BGDynamicsVolumeLight> volume_light_;
#endif
  std::vector<float> position_ = {0.0f, 0.0f, 0.0f};
  std::vector<float> color_ = {1.0f, 1.0f, 1.0f};
  float intensity_ = 1.0f;
  float volume_intensity_scale_ = 1.0f;
  float radius_ = 0.5f;
  bool height_attenuated_ = true;
  bool lights_volumes_ = true;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_LIGHT_NODE_H_
