// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_HEIGHT_CACHE_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_HEIGHT_CACHE_H_

#include <vector>

#include "ballistica/shared/math/vector3f.h"
#include "ode/ode.h"

namespace ballistica::base {

// given geoms, creates/samples a height map on the fly
// for fast but not-perfectly-accurate height values
class BGDynamicsHeightCache {
 public:
  BGDynamicsHeightCache();
  ~BGDynamicsHeightCache();
  auto Sample(const Vector3f& pos) -> float;
  void SetGeoms(const std::vector<dGeomID>& geoms);

 private:
  auto SampleCell(int x, int y) -> float;
  void Update();
  std::vector<dGeomID> geoms_;
  std::vector<float> heights_;
  std::vector<uint8_t> heights_valid_;
  bool dirty_;
  dGeomID shadow_ray_;
  int grid_width_;
  int grid_height_;
  float x_min_;
  float x_max_;
  float y_min_;
  float y_max_;
  float z_min_;
  float z_max_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_HEIGHT_CACHE_H_
