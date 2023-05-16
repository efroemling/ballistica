// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_fuse.h"

#include "ballistica/base/dynamics/bg/bg_dynamics_fuse_data.h"

namespace ballistica::base {

BGDynamicsFuse::BGDynamicsFuse() {
  assert(g_base->bg_dynamics_server);
  assert(g_base->InLogicThread());

  // Allocate our data. We'll pass this to the BGDynamics thread, and
  // it'll then own it.
  data_ = new BGDynamicsFuseData();
  g_base->bg_dynamics_server->PushAddFuseCall(data_);
}

BGDynamicsFuse::~BGDynamicsFuse() {
  assert(g_base->bg_dynamics_server);
  assert(g_base->InLogicThread());

  // Let the data know the client side is dead
  // so that we're no longer included in step messages.
  // (since by the time the worker gets it the data will be gone).
  data_->client_dead_ = true;
  g_base->bg_dynamics_server->PushRemoveFuseCall(data_);
}

void BGDynamicsFuse::SetTransform(const Matrix44f& t) {
  assert(g_base->InLogicThread());
  data_->transform_client_ = t;
  data_->have_transform_client_ = true;
}

void BGDynamicsFuse::SetLength(float length) {
  assert(g_base->InLogicThread());
  data_->length_client_ = length;
}

}  // namespace ballistica::base
