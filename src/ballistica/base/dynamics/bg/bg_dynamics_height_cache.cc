// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_height_cache.h"

namespace ballistica::base {

const int kBGDynamicsHeightCacheMaxContacts = 20;

BGDynamicsHeightCache::BGDynamicsHeightCache()
    : dirty_(true),
      shadow_ray_(nullptr),
      x_min_(-1.0f),
      x_max_(1.0f),
      y_min_(-1.0f),
      y_max_(1.0f),
      z_min_(-1.0f),
      z_max_(1.0f),
      grid_width_(1),
      grid_height_(1) {}

BGDynamicsHeightCache::~BGDynamicsHeightCache() {
  if (shadow_ray_) {
    dGeomDestroy(shadow_ray_);
  }
}

auto BGDynamicsHeightCache::SampleCell(int x, int z) -> float {
  int index = z * grid_width_ + x;
  assert(index >= 0 && index < static_cast<int>(heights_.size())
         && index < static_cast<int>(heights_valid_.size()));
  if (heights_valid_[index]) {
    return heights_[index];
  } else {
    Vector3f p(
        x_min_
            + ((static_cast<float>(x) + 0.5f) / static_cast<float>(grid_width_))
                  * (x_max_ - x_min_),
        y_max_,
        z_min_
            + ((static_cast<float>(z) + 0.5f)
               / static_cast<float>(grid_height_))
                  * (z_max_ - z_min_));
    assert(shadow_ray_);
    dGeomSetPosition(shadow_ray_, p.x, p.y, p.z);
    float shadow_dist = y_max_ - y_min_;
    for (auto& geom : geoms_) {
      dContact contact[1];
      if (dCollide(shadow_ray_, geom, kBGDynamicsHeightCacheMaxContacts,
                   &contact[0].geom, sizeof(dContact))) {
        float len = p.y - contact[0].geom.pos[1];
        if (len < shadow_dist) {
          shadow_dist = len;
        }
      }
    }
    float height = y_max_ - shadow_dist;
    heights_[index] = height;
    heights_valid_[index] = 1;
    return height;
  }
}

auto BGDynamicsHeightCache::Sample(const Vector3f& pos) -> float {
  if (dirty_) {
    Update();
  }

  // Get sample point in grid coords.
  float x =
      static_cast<float>(grid_width_) * ((pos.x - x_min_) / (x_max_ - x_min_))
      - 0.5f;
  float z =
      static_cast<float>(grid_height_) * ((pos.z - z_min_) / (z_max_ - z_min_))
      - 0.5f;

  // Sample the 4 contributing cells.
  int x_min = static_cast<int>(floor(x));
  x_min = std::max(0, std::min(grid_width_ - 1, x_min));
  int x_max = static_cast<int>(ceil(x));
  x_max = std::max(0, std::min(grid_width_ - 1, x_max));
  float x_blend = fmod(x, 1.0f);
  int z_min = static_cast<int>(floor(z));
  z_min = std::max(0, std::min(grid_height_ - 1, z_min));
  int z_max = static_cast<int>(ceil(z));
  z_max = std::max(0, std::min(grid_height_ - 1, z_max));
  float zBlend = fmod(z, 1.0f);

  float xz = SampleCell(x_min, z_min);
  float xZ = SampleCell(x_min, z_max);
  float Xz = SampleCell(x_max, z_min);
  float XZ = SampleCell(x_max, z_max);

  // Weighted blend per row.
  float zFin = xz * (1.0f - x_blend) + Xz * x_blend;
  float ZFin = xZ * (1.0f - x_blend) + XZ * x_blend;

  // Weighted blend of the two rows.
  return zFin * (1.0f - zBlend) + ZFin * zBlend;
}

void BGDynamicsHeightCache::SetGeoms(const std::vector<dGeomID>& geoms) {
  dirty_ = true;
  geoms_ = geoms;
}

void BGDynamicsHeightCache::Update() {
  // Calc our full dimensions.
  if (geoms_.empty()) {
    x_min_ = -1.0f;
    x_max_ = 1.0f;
    y_min_ = -1.0f;
    y_max_ = 1.0f;
    z_min_ = -1.0f;
    z_max_ = 1.0f;
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

  // (Re)create our shadow ray with the new dimensions.
  if (shadow_ray_) {
    dGeomDestroy(shadow_ray_);
  }
  shadow_ray_ = dCreateRay(nullptr, y_max_ - y_min_);
  dGeomRaySet(shadow_ray_, 0, 0, 0, 0, -1, 0);  // Aim straight down.
  dGeomRaySetClosestHit(shadow_ray_, true);

  // Update/clear our cell grid based on our dimensions.
  grid_width_ =
      std::max(1, std::min(256, static_cast<int>((x_max_ - x_min_) * 8)));
  grid_height_ =
      std::max(1, std::min(256, static_cast<int>((z_max_ - z_min_) * 8)));

  assert(grid_width_ >= 0 && grid_height_ >= 0);
  auto cell_count_u = static_cast<uint32_t>(grid_width_ * grid_height_);
  if (cell_count_u != heights_.size()) {
    heights_.clear();
    heights_.resize(cell_count_u);
    heights_valid_.clear();
    heights_valid_.resize(cell_count_u);
  }
  memset(&heights_valid_[0], 0, cell_count_u);

  dirty_ = false;
}

}  // namespace ballistica::base
