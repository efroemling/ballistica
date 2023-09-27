// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/collision_cache.h"

#include "ballistica/base/graphics/component/simple_component.h"
#include "ode/ode_collision_kernel.h"
#include "ode/ode_collision_space_internal.h"

namespace ballistica::base {

CollisionCache::CollisionCache() : test_box_{dCreateBox(nullptr, 1, 1, 1)} {}

CollisionCache::~CollisionCache() {
  if (shadow_ray_) {
    dGeomDestroy(shadow_ray_);
  }
  dGeomDestroy(test_box_);
}

void CollisionCache::SetGeoms(const std::vector<dGeomID>& geoms) {
  dirty_ = true;
  geoms_ = geoms;
}

void CollisionCache::Draw(FrameDef* frame_def) {
  if (cells_.empty()) {
    return;
  }
  SimpleComponent c(frame_def->beauty_pass());
  c.SetTransparent(true);
  c.SetColor(0, 1, 0, 0.1f);
  float cell_width = (1.0f / static_cast<float>(grid_width_));
  float cell_height = (1.0f / static_cast<float>(grid_height_));
  {
    auto xf = c.ScopedTransform();
    c.Translate((x_min_ + x_max_) * 0.5f, 0, (z_min_ + z_max_) * 0.5f);
    c.Scale(x_max_ - x_min_, 1, z_max_ - z_min_);
    {
      auto xf = c.ScopedTransform();
      c.Scale(1, 0.01f, 1);
      c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBox));
    }
    c.Translate(-0.5f + 0.5f * cell_width, 0, -0.5f + 0.5f * cell_height);
    for (int x = 0; x < grid_width_; x++) {
      for (int z = 0; z < grid_height_; z++) {
        int cell_index = z * grid_width_ + x;
        assert(cell_index >= 0 && cell_index < static_cast<int>(glow_.size()));
        if (glow_[cell_index]) {
          c.SetColor(1, 1, 1, 0.2f);
        } else {
          c.SetColor(0, 0, 1, 0.2f);
        }
        {
          auto xf = c.ScopedTransform();
          c.Translate(static_cast<float>(x) / static_cast<float>(grid_width_),
                      cells_[cell_index].height_confirmed_collide_,
                      static_cast<float>(z) / static_cast<float>(grid_height_));
          c.Scale(0.95f * cell_width, 0.01f, 0.95f * cell_height);
          c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBox));
        }
        if (glow_[cell_index]) {
          c.SetColor(1, 1, 1, 0.2f);
        } else {
          c.SetColor(1, 0, 0, 0.2f);
        }
        {
          auto xf = c.ScopedTransform();
          c.Translate(static_cast<float>(x) / static_cast<float>(grid_width_),
                      cells_[cell_index].height_confirmed_empty_,
                      static_cast<float>(z) / static_cast<float>(grid_height_));
          c.Scale(0.95f * cell_width, 0.01f, 0.95f * cell_height);
          c.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBox));
        }
        glow_[cell_index] = 0;
      }
    }
  }
  c.Submit();

  if (explicit_bool(false)) {
    SimpleComponent c2(frame_def->overlay_3d_pass());
    c2.SetTransparent(true);
    c2.SetColor(1, 0, 0, 1.0f);
    float cell_width2 = (1.0f / static_cast<float>(grid_width_));
    float cell_height2 = (1.0f / static_cast<float>(grid_height_));
    {
      auto xf = c2.ScopedTransform();

      c2.Translate((x_min_ + x_max_) * 0.5f, 0, (z_min_ + z_max_) * 0.5f);
      c2.Scale(x_max_ - x_min_, 1, z_max_ - z_min_);
      {
        auto xf = c2.ScopedTransform();
        c2.Scale(1, 0.01f, 1);
        c2.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBox));
      }
      c2.Translate(-0.5f + 0.5f * cell_width2, 0, -0.5f + 0.5f * cell_height2);
      for (int x = 0; x < grid_width_; x++) {
        for (int z = 0; z < grid_height_; z++) {
          int cell_index = z * grid_width_ + x;
          assert(cell_index >= 0
                 && cell_index < static_cast<int>(glow_.size()));
          if (glow_[cell_index]) {
            c2.SetColor(1, 1, 1, 0.2f);
          } else {
            c2.SetColor(1, 0, 0, 0.2f);
          }
          {
            auto xf = c2.ScopedTransform();
            c2.Translate(
                static_cast<float>(x) / static_cast<float>(grid_width_),
                cells_[cell_index].height_confirmed_empty_,
                static_cast<float>(z) / static_cast<float>(grid_height_));
            c2.Scale(0.95f * cell_width2, 0.01f, 0.95f * cell_height2);
            c2.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBox));
          }
          if (glow_[cell_index]) {
            c2.SetColor(1, 1, 1, 0.2f);
          } else {
            c2.SetColor(0, 0, 1, 0.2f);
          }
          {
            auto xf = c2.ScopedTransform();
            c2.Translate(
                static_cast<float>(x) / static_cast<float>(grid_width_),
                cells_[cell_index].height_confirmed_collide_,
                static_cast<float>(z) / static_cast<float>(grid_height_));
            c2.Scale(0.95f * cell_width2, 0.01f, 0.95f * cell_height2);
            c2.DrawMeshAsset(g_base->assets->SysMesh(SysMeshID::kBox));
          }
          glow_[cell_index] = 0;
        }
      }
    }
    c2.Submit();
  }
}

void CollisionCache::Precalc() {
  Update();

  if (precalc_index_ >= cells_.size()) {
    precalc_index_ = 0;  // Loop.
  }

  auto x = static_cast<int>(precalc_index_ % grid_width_);
  auto z = static_cast<int>(precalc_index_ / grid_width_);
  assert(x >= 0 && x < grid_width_);
  assert(z >= 0 && z < grid_height_);
  TestCell(precalc_index_++, x, z);
}

void CollisionCache::CollideAgainstGeom(dGeomID g1, void* data,
                                        dNearCallback* callback) {
  // Update bounds, test for quick out against our height map,
  // and proceed to a full test on a positive result.
  g1->recomputeAABB();

  if (dirty_) Update();

  // Do a quick out if it's not within our cache bounds at all.
  dReal* bounds1 = g1->aabb;
  if (bounds1[0] > x_max_ || bounds1[1] < x_min_ || bounds1[2] > y_max_
      || bounds1[3] < y_min_ || bounds1[4] > z_max_ || bounds1[5] < z_min_) {
    return;
  }

  int x_min = static_cast<int>(static_cast<float>(grid_width_)
                               * ((g1->aabb[0] - x_min_) / (x_max_ - x_min_)));
  x_min = std::max(0, std::min(grid_width_ - 1, x_min));
  int z_min = static_cast<int>(static_cast<float>(grid_height_)
                               * ((g1->aabb[4] - z_min_) / (z_max_ - z_min_)));
  z_min = std::max(0, std::min(grid_height_ - 1, z_min));

  int x_max = static_cast<int>(static_cast<float>(grid_width_)
                               * ((g1->aabb[1] - x_min_) / (x_max_ - x_min_)));
  x_max = std::max(0, std::min(grid_width_ - 1, x_max));
  int z_max = static_cast<int>(static_cast<float>(grid_height_)
                               * ((g1->aabb[5] - z_min_) / (z_max_ - z_min_)));
  z_max = std::max(0, std::min(grid_height_ - 1, z_max));

  // If all cells are confirmed empty to the bottom of our AABB, we're done.
  bool possible_hit = false;
  for (int z = z_min; z <= z_max; z++) {
    auto cell_index = static_cast<uint32_t>(z * grid_width_);
    for (int x = x_min; x <= x_max; x++) {
      if (bounds1[2] <= cells_[cell_index + x].height_confirmed_empty_) {
        possible_hit = true;
        break;
      }
    }
    if (possible_hit) {
      break;
    }
  }
  if (!possible_hit) {
    return;
  }

  // Ok looks like we need to run collisions.
  int t_count = static_cast<int>(geoms_.size());
  for (int i = 0; i < t_count; i++) {
    dxGeom* g2 = geoms_[i];
    collideAABBs(g1, g2, data, callback);
  }

  // While we're here, lets run one pass of tests on these cells to zero in
  // on the actual collide/empty cutoff.
  for (int z = z_min; z <= z_max; z++) {
    int base_index = z * grid_width_;
    for (int x = x_min; x <= x_max; x++) {
      int cell_index = base_index + x;
      assert(cell_index >= 0);
      TestCell(static_cast<uint32_t>(cell_index), x, z);
    }
  }
}

void CollisionCache::TestCell(size_t cell_index, int x, int z) {
  int t_count = static_cast<int>(geoms_.size());
  float top = cells_[cell_index].height_confirmed_empty_;

  // Midway point.
  float bottom = (cells_[cell_index].height_confirmed_collide_ + top) * 0.5f;
  float height = top - bottom;

  // Don't want to test with too thin a box... may miss stuff.
  float box_height = std::max(1.0f, height);
  if (height > 0.01f) {
    glow_[cell_index] = 1;

    dGeomSetPosition(test_box_,
                     x_min_ + cell_width_ * (0.5f + static_cast<float>(x)),
                     bottom + box_height * 0.5f,
                     z_min_ + cell_height_ * (0.5f + static_cast<float>(z)));
    dGeomBoxSetLengths(test_box_, cell_width_, box_height, cell_height_);

    dContact contact[1];
    bool collided = false;

    // See if we collide with *any* terrain.
    for (int i = 0; i < t_count; i++) {
      if (dCollide(test_box_, geoms_[i], 1, &contact[0].geom,
                   sizeof(dContact))) {
        collided = true;
        break;
      }
    }

    // Ok, we collided. We can move our confirmed collide floor up to
    // our bottom.
    if (collided) {
      cells_[cell_index].height_confirmed_collide_ =
          std::max(cells_[cell_index].height_confirmed_collide_, bottom);
    } else {
      // Didn't collide. Move confirmed empty region to our bottom.
      cells_[cell_index].height_confirmed_empty_ =
          std::min(cells_[cell_index].height_confirmed_empty_, bottom);
    }
    // This shouldn't happen but just in case.
    cells_[cell_index].height_confirmed_empty_ =
        std::max(cells_[cell_index].height_confirmed_empty_,
                 cells_[cell_index].height_confirmed_collide_);
  }
}

void CollisionCache::CollideAgainstSpace(dSpaceID space, void* data,
                                         dNearCallback* callback) {
  // We handle our own testing against trimeshes, so we can bring our fancy
  // caching into play.
  if (!geoms_.empty()) {
    // Intersect all geoms in the space against all terrains.
    for (dxGeom* g1 = space->first; g1; g1 = g1->next) {
      CollideAgainstGeom(g1, data, callback);
    }
  }
}

void CollisionCache::Update() {
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

  // (Re)create our shadow ray with the new dimensions.
  if (shadow_ray_) {
    dGeomDestroy(shadow_ray_);
  }
  shadow_ray_ = dCreateRay(nullptr, y_max_ - y_min_);
  dGeomRaySet(shadow_ray_, 0, 0, 0, 0, -1, 0);  // aim straight down
  dGeomRaySetClosestHit(shadow_ray_, true);

  // Update/clear our cell grid based on our dimensions.
  grid_width_ =
      std::max(1, std::min(256, static_cast<int>((x_max_ - x_min_) * 1.3f)));
  grid_height_ =
      std::max(1, std::min(256, static_cast<int>((z_max_ - z_min_) * 1.3f)));

  assert(grid_width_ >= 0 && grid_height_ >= 0);
  auto cell_count = static_cast<uint32_t>(grid_width_ * grid_height_);
  cells_.clear();
  cells_.resize(cell_count);
  for (uint32_t i = 0; i < cell_count; i++) {
    cells_[i].height_confirmed_empty_ = y_max_;
    cells_[i].height_confirmed_collide_ = y_min_;
  }
  cell_width_ = (x_max_ - x_min_) / static_cast<float>(grid_width_);
  cell_height_ = (z_max_ - z_min_) / static_cast<float>(grid_height_);
  glow_.clear();
  glow_.resize(cell_count);
  memset(&glow_[0], 0, cell_count);
  precalc_index_ = 0;
  dirty_ = false;
}

}  // namespace ballistica::base
