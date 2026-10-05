// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_volume_light.h"

#include "ballistica/base/dynamics/bg/bg_dynamics_kinds.h"

namespace ballistica::base {

BGDynamicsVolumeLight::BGDynamicsVolumeLight(BGDynamicsWorld* world)
    : world_(world) {
  assert(g_base->InLogicThread());
  slot_ = world_->channel<BGDynamicsVolumeLightKind>().Create(
      BGDynamicsVolumeLightKind::Config{});
}

BGDynamicsVolumeLight::~BGDynamicsVolumeLight() {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsVolumeLightKind>().Destroy(slot_);
}

void BGDynamicsVolumeLight::SetPosition(const Vector3f& pos) {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsVolumeLightKind>().input(slot_).position = pos;
}

void BGDynamicsVolumeLight::SetRadius(float radius) {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsVolumeLightKind>().input(slot_).radius = radius;
}

void BGDynamicsVolumeLight::SetColor(float r, float g, float b) {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsVolumeLightKind>().input(slot_);
  input.r = r;
  input.g = g;
  input.b = b;
}

}  // namespace ballistica::base
