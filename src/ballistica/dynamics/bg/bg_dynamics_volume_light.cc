// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/bg/bg_dynamics_volume_light.h"

#include "ballistica/dynamics/bg/bg_dynamics_volume_light_data.h"

namespace ballistica {

BGDynamicsVolumeLight::BGDynamicsVolumeLight() {
  assert(InGameThread());
  // allocate our light data... we'll pass this to the BGDynamics thread,
  // which will then own it
  data_ = new BGDynamicsVolumeLightData();
  assert(g_bg_dynamics_server);
  g_bg_dynamics_server->PushAddVolumeLightCall(data_);
}

BGDynamicsVolumeLight::~BGDynamicsVolumeLight() {
  assert(InGameThread());

  // let the data know the client side is dead,
  // so we're no longer included in step messages
  // (since by the time the worker gets it the data will be gone)
  data_->client_dead = true;

  assert(g_bg_dynamics_server);
  g_bg_dynamics_server->PushRemoveVolumeLightCall(data_);
}

void BGDynamicsVolumeLight::SetPosition(const Vector3f& pos) {
  assert(InGameThread());
  data_->pos_client = pos;
}

void BGDynamicsVolumeLight::SetRadius(float radius) {
  assert(InGameThread());
  data_->radius_client = radius;
}

void BGDynamicsVolumeLight::SetColor(float r, float g, float b) {
  assert(InGameThread());
  data_->r_client = r;
  data_->g_client = g;
  data_->b_client = b;
}

}  // namespace ballistica
