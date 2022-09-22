// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_COLLISION_CACHE_H_
#define BALLISTICA_DYNAMICS_COLLISION_CACHE_H_

#include <vector>

#include "ballistica/ballistica.h"
#include "ode/ode.h"

namespace ballistica {

// Given geoms, creates/samples a height map on the fly
// which can be used for very fast AABB tests against the geometry.
class CollisionCache {
 public:
  CollisionCache();
  ~CollisionCache();

  // If returns true, the provided AABB *may* intersect the geoms.
  auto SetGeoms(const std::vector<dGeomID>& geoms) -> void;
  auto Draw(FrameDef* f) -> void;  // For debugging.
  auto CollideAgainstSpace(dSpaceID space, void* data, dNearCallback* callback)
      -> void;
  auto CollideAgainstGeom(dGeomID geom, void* data, dNearCallback* callback)
      -> void;

  // Call this periodically (once per cycle or so) to slowly fill in
  // the cache so there's less to do during spurts of activity;
  auto Precalc() -> void;

 private:
  auto TestCell(size_t cell_index, int x, int z) -> void;
  auto Update() -> void;
  uint32_t precalc_index_{};
  std::vector<dGeomID> geoms_;
  struct Cell {
    float height_confirmed_empty_;
    float height_confirmed_collide_;
  };
  std::vector<Cell> cells_;
  std::vector<uint8_t> glow_;
  bool dirty_{true};
  dGeomID shadow_ray_{};
  dGeomID test_box_{};
  int grid_width_{1};
  int grid_height_{1};
  float cell_width_{};
  float cell_height_{};
  float x_min_{-1.0f};
  float x_max_{1.0f};
  float y_min_{-1.0f};
  float y_max_{1.0f};
  float z_min_{-1.0f};
  float z_max_{1.0f};
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_COLLISION_CACHE_H_
