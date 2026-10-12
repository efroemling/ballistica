// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_fuse.h"

#include <algorithm>

#include "ballistica/base/dynamics/bg/bg_dynamics_kinds.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world_server.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::base {

// ---- Logic-thread handle. ----

BGDynamicsFuse::BGDynamicsFuse(BGDynamicsWorld* world) : world_(world) {
  assert(g_base->InLogicThread());
  slot_ = world_->channel<BGDynamicsFuseKind>().Create(
      BGDynamicsFuseKind::Config{});
}

BGDynamicsFuse::~BGDynamicsFuse() {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsFuseKind>().Destroy(slot_);
}

void BGDynamicsFuse::SetTransform(const Matrix44f& t) {
  assert(g_base->InLogicThread());
  auto& input = world_->channel<BGDynamicsFuseKind>().input(slot_);
  input.transform = t;
  input.have_transform = true;
}

void BGDynamicsFuse::SetLength(float length) {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsFuseKind>().input(slot_).length = length;
}

// ---- Worker-thread sim. ----

void BGDynamicsFuseKind::Sim::Step(BGDynamicsWorldServer* server) {
  // Do nothing if we haven't received an initial transform.
  if (!input_.have_transform) {
    return;
  }
  const Matrix44f& transform = input_.transform;
  float length = input_.length;
  seg_len_ = 0.2f * std::max(0.01f, length);

  if (!initial_position_set_) {
    // Snap all our stuff into place on the initial transform.
    Vector3f pt = transform.GetTranslate();
    target_pts_[0] = dyn_pts_[0] = pt;
    auto up = Vector3f(&transform.m[4]);
    for (int i = 1; i < kFusePointCount; i++) {
      target_pts_[i] = target_pts_[i - 1] + up * seg_len_;
      dyn_pts_[i] = target_pts_[i];
      up = (target_pts_[i] - target_pts_[i - 1]).Normalized();
    }
    initial_position_set_ = true;
    return;
  }

  // ...otherwise dynamically update it.
  Vector3f pt = transform.GetTranslate();
  target_pts_[0] = dyn_pts_[0] = pt;
  auto up = Vector3f(&transform.m[4]);
  auto back = Vector3f(&transform.m[8]);
  up = (up + -0.03f * back).Normalized();
  float b_amt = 0.0f;
  Vector3f old_tip_pos = dyn_pts_[kFusePointCount - 1];
  for (int i = 1; i < kFusePointCount; i++) {
    target_pts_[i] = dyn_pts_[i - 1] + up * seg_len_;
    float this_follow_amt = (i == 1 ? 0.5f : 0.2f);
    dyn_pts_[i] += this_follow_amt * (target_pts_[i] - dyn_pts_[i]);
    dyn_pts_[i] += Vector3f(0, -0.014f * 0.2f * length, 0);
    up = (dyn_pts_[i] - dyn_pts_[i - 1] - b_amt * back).Normalized();
    dyn_pts_[i] = dyn_pts_[i - 1] + up * seg_len_;
    b_amt += 0.01f * length;
  }

  // Spit out a spark.
  float r, g, b, a;
  if (length > 0.66f) {
    r = 1.6f;
    g = 1.5f;
    b = 0.4f;
    a = 0.5f;
  } else if (length > 0.33f) {
    r = 2.0f;
    g = 0.7f;
    b = 0.3f;
    a = 0.2f;
  } else {
    r = 3.0f;
    g = 0.5f;
    b = 0.4f;
    a = 0.3f;
  }
  int count = 2;
  if (server->graphics_quality() <= GraphicsQuality::kLow) {
    count = 1;
  }
  for (int i = 0; i < count; i++) {
    float rand_f = RandomFloat();
    float d_life = -0.08f;
    float d_size = 0.000f + 0.04f * rand_f * rand_f;
    server->spark_particles()->Emit(dyn_pts_[kFusePointCount - 1],
                                    dyn_pts_[kFusePointCount - 1] - old_tip_pos,
                                    r, g, b, a, d_life, 0.02f, d_size,
                                    0.8f);  // Flicker.
  }
}

}  // namespace ballistica::base
