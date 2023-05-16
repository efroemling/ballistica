// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"

#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_shadow_data.h"
#include "ballistica/base/graphics/graphics.h"

namespace ballistica::base {

BGDynamicsShadow::BGDynamicsShadow(float height_scaling) {
  assert(g_base->InLogicThread());

  // allocate our shadow data... we'll pass this to the BGDynamics thread,
  // which will then own it.
  data_ = new BGDynamicsShadowData(height_scaling);
  assert(g_base->bg_dynamics_server);
  g_base->bg_dynamics_server->PushAddShadowCall(data_);
}

BGDynamicsShadow::~BGDynamicsShadow() {
  assert(g_base->InLogicThread());
  assert(g_base->bg_dynamics_server);

  // let the data know the client side is dead,
  // so we're no longer included in step messages
  // (since by the time the worker gets it the data will be gone)
  data_->client_dead = true;
  g_base->bg_dynamics_server->PushRemoveShadowCall(data_);
}

void BGDynamicsShadow::SetPosition(const Vector3f& pos) {
  assert(g_base->InLogicThread());
  data_->pos_client = pos;
}

auto BGDynamicsShadow::GetPosition() const -> const Vector3f& {
  assert(g_base->InLogicThread());
  return data_->pos_client;
}

void BGDynamicsShadow::GetValues(float* scale, float* density) const {
  assert(g_base->InLogicThread());
  assert(scale);
  assert(density);

  *scale = data_->shadow_scale_client;
  *density = data_->shadow_density_client
             * g_base->graphics->GetShadowDensity(
                 data_->pos_client.x, data_->pos_client.y, data_->pos_client.z);
}

}  // namespace ballistica::base
