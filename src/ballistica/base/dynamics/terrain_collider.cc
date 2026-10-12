// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/terrain_collider.h"

#include <chrono>
#include <vector>

#include "ode/ode_collision_kernel.h"
#include "ode/ode_collision_space_internal.h"

namespace ballistica::base {

namespace {
using Clock = std::chrono::steady_clock;
double MillisecsBetween(Clock::time_point a, Clock::time_point b) {
  return std::chrono::duration<double, std::milli>(b - a).count();
}
}  // namespace

void TerrainCollider::SetTerrainGeoms(const std::vector<dGeomID>& geoms) {
  dirty_ = true;
  geoms_ = geoms;
}

TerrainCollider::Stats TerrainCollider::TakeStats() {
  Stats out = stats_;
  stats_ = Stats{};
  return out;
}

void TerrainCollider::CollideGeom(dGeomID g1, void* data,
                                  dNearCallback* callback) {
  g1->recomputeAABB();

  if (dirty_) Update();
  stats_.queries++;

  // Quick out if it's not within our overall terrain bounds at all
  // (this also catches everything above the terrain's top).
  dReal* bounds1 = g1->aabb;
  if (bounds1[0] > x_max_ || bounds1[1] < x_min_ || bounds1[2] > y_max_
      || bounds1[3] < y_min_ || bounds1[4] > z_max_ || bounds1[5] < z_min_) {
    stats_.bounds_outs++;
    return;
  }

  stats_.full_tests++;
  auto t0 = Clock::now();
  for (dxGeom* g2 : geoms_) {
    collideAABBs(g1, g2, data, callback);
  }
  stats_.full_ms += MillisecsBetween(t0, Clock::now());
}

void TerrainCollider::CollideSpace(dSpaceID space, void* data,
                                   dNearCallback* callback) {
  // We handle our own testing against trimeshes rather than putting
  // them in the space.
  if (!geoms_.empty()) {
    for (dxGeom* g1 = space->first; g1; g1 = g1->next) {
      CollideGeom(g1, data, callback);
    }
  }
}

void TerrainCollider::Update() {
  if (!dirty_) {
    return;
  }

  // Calc our full dimensions.
  if (geoms_.empty()) {
    x_min_ = -1;
    x_max_ = 1;
    y_min_ = -1;
    y_max_ = 1;
    z_min_ = -1;
    z_max_ = 1;
  } else {
    auto i = geoms_.begin();
    dReal aabb[6];
    dGeomGetAABB(*i, aabb);
    float x = aabb[0];
    float X = aabb[1];
    float y = aabb[2];
    float Y = aabb[3];
    float z = aabb[4];
    float Z = aabb[5];
    for (i++; i != geoms_.end(); i++) {
      dGeomGetAABB(*i, aabb);
      if (aabb[0] < x) x = aabb[0];
      if (aabb[1] > X) X = aabb[1];
      if (aabb[2] < y) y = aabb[2];
      if (aabb[3] > Y) Y = aabb[3];
      if (aabb[4] < z) z = aabb[4];
      if (aabb[5] > Z) Z = aabb[5];
    }
    float buffer = 0.3f;
    x_min_ = x - buffer;
    x_max_ = X + buffer;
    y_min_ = y - buffer;
    y_max_ = Y + buffer;
    z_min_ = z - buffer;
    z_max_ = Z + buffer;
  }
  dirty_ = false;
}

}  // namespace ballistica::base
