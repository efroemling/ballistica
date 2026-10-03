// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_shadow.h"

#include <algorithm>

#include "ballistica/base/dynamics/bg/bg_dynamics_height_cache.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_kinds.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_world_server.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/support/render_view.h"

namespace ballistica::base {

// ---- Logic-thread handle. ----

BGDynamicsShadow::BGDynamicsShadow(BGDynamicsWorld* world, float height_scaling)
    : world_(world) {
  assert(g_base->InLogicThread());
  BGDynamicsShadowKind::Config config;
  config.height_scaling = height_scaling;
  slot_ = world_->channel<BGDynamicsShadowKind>().Create(config);
}

BGDynamicsShadow::~BGDynamicsShadow() {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsShadowKind>().Destroy(slot_);
}

void BGDynamicsShadow::SetPosition(const Vector3f& pos) {
  assert(g_base->InLogicThread());
  world_->channel<BGDynamicsShadowKind>().input(slot_).position = pos;
}

auto BGDynamicsShadow::GetPosition() const -> const Vector3f& {
  assert(g_base->InLogicThread());
  return world_->channel<BGDynamicsShadowKind>().input(slot_).position;
}

void BGDynamicsShadow::GetValues(float* scale, float* density) const {
  assert(g_base->InLogicThread());
  assert(scale);
  assert(density);
  const auto& channel = world_->channel<BGDynamicsShadowKind>();
  // Until the first result lands, the defaults (full scale, zero
  // density) keep a fresh caster invisible rather than popping.
  BGDynamicsShadowKind::Output out;
  if (const auto* latest = channel.output(slot_)) {
    out = *latest;
  }
  const Vector3f& pos = channel.input(slot_).position;
  *scale = out.scale;
  *density =
      out.density * world_->view()->GetShadowDensity(pos.x, pos.y, pos.z);
}

// ---- Worker-thread sim. ----

BGDynamicsShadowKind::Sim::Sim(const Config& config,
                               BGDynamicsWorldServer* server)
    : height_scaling_(config.height_scaling) {}

void BGDynamicsShadowKind::Sim::SetInput(const Input& input) {
  position_ = input.position;
}

void BGDynamicsShadowKind::Sim::Step(BGDynamicsWorldServer* server) {
  float shadow_dist = position_.y - server->height_cache()->Sample(position_);

  float scale;
  float density;
  if (shadow_dist < 0.0f) {
    // Negative dist means some object is in front of our caster: keep
    // the scale as it would be at zero dist but fade the density out
    // gradually as we become more deeply submerged.
    scale = 1.0f;
    density = 1.0f - std::min(1.0f, -shadow_dist / kOccludeDistance);
  } else {
    // Normal non-submerged shadow.
    float max_scale = 1.0f + (kMaxScale - 1.0f) * height_scaling_;
    float grow = std::max(0.0f, std::min(1.0f, shadow_dist / kMaxGrowDist));
    scale = 1.0f + grow * (max_scale - 1.0f);
    density = 1.0f - 0.7f * grow;
  }

  // A bit of smoothing so our shadow doesn't jump instantly when we
  // go over an edge/etc.
  const float smoothing{0.8f};
  scale_ = smoothing * scale_ + (1.0f - smoothing) * scale;
  density_ = smoothing * density_ + (1.0f - smoothing) * density;
}

void BGDynamicsShadowKind::Sim::GetOutput(Output* out) const {
  out->scale = scale_;
  out->density = density_;
}

}  // namespace ballistica::base
