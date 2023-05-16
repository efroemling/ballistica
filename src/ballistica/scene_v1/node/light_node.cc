// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/node/light_node.h"

#include "ballistica/base/dynamics/bg/bg_dynamics_volume_light.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/scene_v1/node/node_attribute.h"
#include "ballistica/scene_v1/node/node_type.h"

namespace ballistica::scene_v1 {

class LightNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS LightNode
  BA_NODE_CREATE_CALL(CreateLight);
  BA_FLOAT_ARRAY_ATTR(position, position, SetPosition);
  BA_FLOAT_ATTR(intensity, intensity, SetIntensity);
  BA_FLOAT_ATTR(volume_intensity_scale, volume_intensity_scale,
                SetVolumeIntensityScale);
  BA_FLOAT_ARRAY_ATTR(color, color, SetColor);
  BA_FLOAT_ATTR(radius, radius, SetRadius);
  BA_BOOL_ATTR(lights_volumes, lights_volumes, set_lights_volumes);
  BA_BOOL_ATTR(height_attenuated, height_attenuated, set_height_attenuated);
#undef BA_NODE_TYPE_CLASS
  LightNodeType()
      : NodeType("light", CreateLight),
        position(this),
        intensity(this),
        volume_intensity_scale(this),
        color(this),
        radius(this),
        lights_volumes(this),
        height_attenuated(this) {}
};
static NodeType* node_type{};

auto LightNode::InitType() -> NodeType* {
  node_type = new LightNodeType();
  return node_type;
}

LightNode::LightNode(Scene* scene) : Node(scene, node_type) {}

auto LightNode::GetVolumeLightIntensity() -> float {
  return intensity_ * volume_intensity_scale_ * 0.02f;
}

void LightNode::Step() {
#if !BA_HEADLESS_BUILD
  // create or destroy our light-volume as needed
  // (minimize redundant create/destroy/sets this way)
  if (lights_volumes_ && !volume_light_.Exists()) {
    volume_light_ = Object::New<base::BGDynamicsVolumeLight>();
    float i = GetVolumeLightIntensity();
    volume_light_->SetColor(color_[0] * i, color_[1] * i, color_[2] * i);
    volume_light_->SetPosition(
        Vector3f(position_[0], position_[1], position_[2]));
  } else if (!lights_volumes_ && volume_light_.Exists()) {
    volume_light_.Clear();
  }
#endif  // BA_HEADLESS_BUILD
}

void LightNode::SetRadius(float val) {
  radius_ = std::max(0.0f, val);
#if !BA_HEADLESS_BUILD
  if (volume_light_.Exists()) {
    volume_light_->SetRadius(radius_);
  }
#endif  // BA_HEADLESS_BUILD
}

void LightNode::SetColor(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("expected float array of size 3 for color");
  }
  color_ = vals;
#if !BA_HEADLESS_BUILD
  if (volume_light_.Exists()) {
    float i = GetVolumeLightIntensity();
    volume_light_->SetColor(color_[0] * i, color_[1] * i, color_[2] * i);
  }
#endif  // BA_HEADLESS_BUILD
}

void LightNode::SetPosition(const std::vector<float>& vals) {
  if (vals.size() != 3) {
    throw Exception("expected float array of size 3 for position");
  }
  position_ = vals;

#if !BA_HEADLESS_BUILD
  shadow_.SetPosition(Vector3f(position_[0], position_[1], position_[2]));
  if (volume_light_.Exists()) {
    volume_light_->SetPosition(
        Vector3f(position_[0], position_[1], position_[2]));
  }
#endif  // BA_HEADLESS_BUILD
}

void LightNode::SetIntensity(float val) {
  intensity_ = std::max(0.0f, val);
#if !BA_HEADLESS_BUILD
  if (volume_light_.Exists()) {
    float i = GetVolumeLightIntensity();
    volume_light_->SetColor(color_[0] * i, color_[1] * i, color_[2] * i);
  }
#endif  // BA_HEADLESS_BUILD
}

void LightNode::SetVolumeIntensityScale(float val) {
  volume_intensity_scale_ = std::max(0.0f, val);

#if !BA_HEADLESS_BUILD
  if (volume_light_.Exists()) {
    float i = GetVolumeLightIntensity();
    volume_light_->SetColor(color_[0] * i, color_[1] * i, color_[2] * i);
  }
#endif  // BA_HEADLESS_BUILD
}

void LightNode::Draw(base::FrameDef* frame_def) {
#if !BA_HEADLESS_BUILD
  // if we haven't gotten our initial attributes, dont draw
  assert(position_.size() == 3);
  // if (position_.size() == 0) return;

  float s_density, s_scale;

  if (height_attenuated_) {
    shadow_.GetValues(&s_scale, &s_density);
  } else {
    s_density = 1.0f;
    s_scale = 1.0f;
  }

  float brightness = s_density * 0.65f * intensity_;

  // draw our light on both terrain and objects
  g_base->graphics->DrawBlotchSoft(
      Vector3f(&position_[0]), 20.0f * radius_ * s_scale,
      color_[0] * brightness, color_[1] * brightness, color_[2] * brightness,
      0.0f);

  g_base->graphics->DrawBlotchSoftObj(
      Vector3f(&position_[0]), 20.0f * radius_ * s_scale,
      color_[0] * brightness, color_[1] * brightness, color_[2] * brightness,
      0.0f);
#endif  // BA_HEADLESS_BUILD
}

}  // namespace ballistica::scene_v1
