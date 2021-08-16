// Released under the MIT License. See LICENSE for details.

#include "ballistica/dynamics/bg/bg_dynamics_fuse.h"

#include "ballistica/dynamics/bg/bg_dynamics_fuse_data.h"

namespace ballistica {

BGDynamicsFuse::BGDynamicsFuse() {
  assert(g_bg_dynamics_server);
  assert(InGameThread());

  // Allocate our data. We'll pass this to the BGDynamics thread, and
  // it'll then own it.
  data_ = new BGDynamicsFuseData();
  g_bg_dynamics_server->PushAddFuseCall(data_);
}

BGDynamicsFuse::~BGDynamicsFuse() {
  assert(g_bg_dynamics_server);
  assert(InGameThread());

  // Let the data know the client side is dead
  // so that we're no longer included in step messages.
  // (since by the time the worker gets it the data will be gone).
  data_->client_dead_ = true;
  g_bg_dynamics_server->PushRemoveFuseCall(data_);
}

void BGDynamicsFuse::SetTransform(const Matrix44f& t) {
  assert(InGameThread());
  data_->transform_client_ = t;
  data_->have_transform_client_ = true;
}

void BGDynamicsFuse::SetLength(float length) {
  assert(InGameThread());
  data_->length_client_ = length;
}

}  // namespace ballistica
