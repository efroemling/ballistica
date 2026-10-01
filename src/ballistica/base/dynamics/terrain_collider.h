// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_TERRAIN_COLLIDER_H_
#define BALLISTICA_BASE_DYNAMICS_TERRAIN_COLLIDER_H_

#include <vector>

#include "ballistica/base/base.h"
#include "ode/ode.h"

namespace ballistica::base {

/// The set of static terrain geoms a sim collides against, with one
/// combined AABB for cheap whole-terrain rejection. Anything that
/// passes the AABB goes straight to ODE's trimesh colliders.
///
/// This used to also maintain a per-column height map (bisected in
/// the background with box tests) so airborne bodies could early-out
/// without touching the trimesh. Measured on an 8-player stress test
/// (2026-09-04) it saved ~4us/step on the main sim and cost ~7us/step
/// on the bg thread: Opcode's tree rejects an airborne body in about
/// a quarter microsecond, which is what the height-map lookup itself
/// costs, and the refinement tests ate the rest. Write-up in
/// docs/followups.md ("Terrain collision height map removed").
class TerrainCollider {
 public:
  TerrainCollider() = default;
  ~TerrainCollider() = default;

  void SetTerrainGeoms(const std::vector<dGeomID>& geoms);

  /// Collide every geom in a space against the terrain geoms.
  void CollideSpace(dSpaceID space, void* data, dNearCallback* callback);

  /// Collide one geom against the terrain geoms.
  void CollideGeom(dGeomID geom, void* data, dNearCallback* callback);

  /// Query counters, accumulated until a profiler takes them.
  struct Stats {
    int64_t queries{};      // CollideGeom calls.
    int64_t bounds_outs{};  // Rejected by the whole-terrain AABB.
    int64_t full_tests{};   // Ran real geom-vs-trimesh collides.
    double full_ms{};       // Time in those collides.
  };
  /// Return the stats since the last call and reset them.
  Stats TakeStats();

 private:
  void Update();
  std::vector<dGeomID> geoms_;
  Stats stats_;
  bool dirty_{true};
  float x_min_{-1.0f};
  float x_max_{1.0f};
  float y_min_{-1.0f};
  float y_max_{1.0f};
  float z_min_{-1.0f};
  float z_max_{1.0f};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_TERRAIN_COLLIDER_H_
