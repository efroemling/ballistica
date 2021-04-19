// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/bg/bg_dynamics_shadow.h"

#include "ballistica/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/dynamics/bg/bg_dynamics_shadow_data.h"
#include "ballistica/graphics/graphics.h"

namespace ballistica {

BGDynamicsShadow::BGDynamicsShadow(float height_scaling) {
  assert(InGameThread());

  // allocate our shadow data.. we'll pass this to the BGDynamics thread
  // and it'll then own it
  data_ = new BGDynamicsShadowData(height_scaling);
  assert(g_bg_dynamics_server);
  g_bg_dynamics_server->PushAddShadowCall(data_);
}

BGDynamicsShadow::~BGDynamicsShadow() {
  assert(InGameThread());
  assert(g_bg_dynamics_server);

  // let the data know the client side is dead
  // so we're no longer included in step messages
  // (since by the time the worker gets the the data will be gone)
  data_->client_dead = true;
  g_bg_dynamics_server->PushRemoveShadowCall(data_);
}

void BGDynamicsShadow::SetPosition(const Vector3f& pos) {
  assert(InGameThread());
  data_->pos_client = pos;
}

auto BGDynamicsShadow::GetPosition() const -> const Vector3f& {
  assert(InGameThread());
  return data_->pos_client;
}

void BGDynamicsShadow::GetValues(float* scale, float* density) const {
  assert(InGameThread());
  assert(scale);
  assert(density);

  *scale = data_->shadow_scale_client;
  *density = data_->shadow_density_client
             * g_graphics->GetShadowDensity(
                 data_->pos_client.x, data_->pos_client.y, data_->pos_client.z);
}

}  // namespace ballistica
