// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"

#include <algorithm>
#include <list>
#include <memory>
#include <vector>

#include "ballistica/base/assets/collision_mesh_asset.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_draw_snapshot.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_fuse_data.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_height_cache.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_shadow_data.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_volume_light_data.h"
#include "ballistica/base/dynamics/collision_cache.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/generic/utils.h"

namespace ballistica::base {

// Some triangle-on-box cases generate tons of contacts; lets try limiting it
// this way... If that doesn't work we'll crank this up and add collision
// simplification.
const int kMaxBGDynamicsContacts = 20;

// How far from the shadow will be max size and min density.
const float kMaxShadowGrowDist = 3.0f;

// How far behind something a shadow caster has to be to go transparent.
const float kShadowOccludeDistance = 0.5f;

// How big the shadow gets at its max dist.
const float kMaxShadowScale = 3.0f;

const float kSmokeBaseGlow = 0.0f;
const float kSmokeGlow = 400.0f;

// FIXME: Should get rid of this stuff.
#if BA_DEBUG_BUILD
struct DebugLine {
  DebugLine(const Vector3f& p1_in, const Vector3f& p2_in,
            const Vector3f& color_in)
      : p1(p1_in), p2(p2_in), color(color_in) {}
  Vector3f p1;
  Vector3f p2;
  Vector3f color;
};

// Eww; these aren't thread-safe, but they're just for debugging so whatever.
std::vector<DebugLine> g_debug_lines;
std::vector<Vector3f> g_debug_points;
#endif  // BA_DEBUG_BUILD

// FIXME: Move to a nice math-y place.
inline auto Reflect(const Vector3f& v, const Vector3f& normal) -> Vector3f {
  Vector3f n_projected = normal * (v.Dot(normal.Normalized()));
  return -(n_projected - (v - n_projected));
}

void BGDynamicsServer::CalcERPCFM(dReal stiffness, dReal damping, dReal* erp,
                                  dReal* cfm) {
  if (stiffness <= 0.0f && damping <= 0.0f) {
    *erp = 0.0f;
    // cfm = dInfinity;  // doesn't seem to be happy...
    *cfm = 9999999999.0f;
  } else {
    *erp =
        (step_seconds_ * stiffness) / ((step_seconds_ * stiffness) + damping);
    *cfm = 1.0f / ((step_seconds_ * stiffness) + damping);
  }
}

class BGDynamicsServer::Terrain {
 public:
  Terrain(BGDynamicsServer* t,
          Object::Ref<CollisionMeshAsset>* collision_mesh_in)
      : collision_mesh_(collision_mesh_in) {
    assert((**collision_mesh_).loaded());
    geom_ = dCreateTriMesh(nullptr, (**collision_mesh_).GetBGMeshData(),
                           nullptr, nullptr, nullptr);
  }

  auto GetCollisionMesh() const -> CollisionMeshAsset* {
    return collision_mesh_->get();
  }

  ~Terrain() {
    dGeomDestroy(geom_);
    // We were passed an allocated pointer to a CollisionMeshData strong-ref
    // object to keep it alive while we're using it.  We need to pass that
    // back to the main thread to get freed.
    if (collision_mesh_) {
      Object::Ref<CollisionMeshAsset>* ref = collision_mesh_;
      g_base->logic->event_loop()->PushCall([ref] {
        (**ref).set_last_used_time(g_core->AppTimeMillisecs());
        delete ref;
      });
      collision_mesh_ = nullptr;
    }
  }

  auto geom() const -> dGeomID { return geom_; }

 private:
  Object::Ref<CollisionMeshAsset>* collision_mesh_;
  dGeomID geom_;
};

class BGDynamicsServer::Field {
 public:
  Field(BGDynamicsServer* t, const Vector3f& pos, float mag)
      : pos_(pos),
        rad_(5),
        mag_(mag),
        birth_time_ms_(t->time_ms()),
        lifespan_ms_(500) {}
  ~Field() = default;

  auto rad() const -> dReal { return rad_; }
  auto pos() const -> Vector3f { return pos_; }
  auto amt() const -> dReal { return amt_; }
  void set_amt(dReal val) { amt_ = val; }
  auto birth_time_ms() const { return birth_time_ms_; }
  auto lifespan_ms() const -> dReal { return lifespan_ms_; }
  auto mag() const -> dReal { return mag_; }

 private:
  Vector3f pos_;
  float rad_;
  float mag_;
  float birth_time_ms_;
  float lifespan_ms_;
  float amt_{};
};

class BGDynamicsServer::Tendril {
 public:
  struct Point {
    Vector3f p{0.0f, 0.0f, 0.0f};
    Vector3f v{0.0f, 0.0f, 0.0f};
    Vector3f p_distorted{0.0f, 0.0f, 0.0f};
    float tex_coords[2]{};
    float erode{};
    float erode_rate{};
    float bouyancy{};
    float brightness{};
    float fade{};
    float fade_rate{};
    float age_ms{};
    float glow_r{};
    float glow_g{};
    float glow_b{};
    void Update(BGDynamicsServer* dynamics, const Tendril& t) {
      p += v * dynamics->step_seconds();
      age_ms += dynamics->step_milliseconds();
      v *= 0.992f;
      v.y -= 0.003f * bouyancy;     // Bouyancy.
      v.x += 0.005f * t.wind_amt_;  // Slight side drift.
      erode *= (1.0f - 0.06f * erode_rate);
      if (age_ms > 750 * fade_rate) fade *= 1.0f - 0.0085f * fade_rate;
    }
    void UpdateDistortion(const BGDynamicsServer& d) {
      p_distorted = p;
      for (auto&& fi : d.fields_) {
        const Field& f(*fi);
        float f_rad = f.rad();
        float f_rad_squared = f_rad * f_rad;
        Vector3f diff = p_distorted - f.pos();
        float dist_squared = diff.LengthSquared();
        if (dist_squared <= f_rad_squared) {
          float dist = sqrtf(dist_squared);

          // Shift our point towards or away from the field by its calced mag.
          float mag = f.amt();

          // Points closer than MAG to the field are scaled by their
          // ratio of dist to mag.
          if (dist < -mag) mag *= (dist / -mag);
          float falloff =
              (1.0f - (dist / f_rad));  // falloff with dist from field
          mag *= falloff;
          Vector3f diff_norm = diff.Normalized();
          p_distorted += diff_norm * mag;

          // Also apply a very slight amount of actual outward force to
          // ourselves (only if we're kinda old though - otherwise it screws
          // with our initial shape too much).
          if (age_ms > 400) {
            v += Vector3f(diff_norm.x * 0.03f, diff_norm.y * 0.01f,
                          diff_norm.z * 0.03f)
                 * falloff;
          }
        }
      }
    }

    void UpdateGlow(const BGDynamicsServer& d, float glow_scale) {
      glow_r = glow_g = glow_b = 0.0f;
      for (auto&& li : d.volume_lights_) {
        BGDynamicsVolumeLightData& l(*li);
        Vector3f& pLight(l.pos_worker);
        float light_rad = l.radius_worker * 9.0f;  // Let's grow it a bit.
        float light_rad_squared = light_rad * light_rad;
        float dist_squared = (pLight - p).LengthSquared();
        if (dist_squared <= light_rad_squared) {
          float dist = sqrtf(dist_squared);
          float val = (1.0f - dist / light_rad);
          val = val * val;
          glow_r += val * l.r_worker;
          glow_g += val * l.g_worker;
          glow_b += val * l.b_worker;
        }
      }
      glow_r *= glow_scale;
      glow_g *= glow_scale;
      glow_b *= glow_scale;
    }
  };

  struct Slice {
    Point p1;
    Point p2;
    float emit_rate{};     // What the emit rate was at this slice.
    float start_erode{};   // What the start-erode value was at this slice.
    float start_spread{};  // What the start-erode value was at this slice.
    auto GetCenter() const -> Vector3f { return (p1.p * 0.5f) + (p2.p * 0.5f); }
    auto isFullyTransparent() const -> bool {
      return (p1.fade < 0.01f && p2.fade < 0.01f);
    }
  };

  explicit Tendril(BGDynamicsServer* t)
      : has_updated_{false},
        controller_{nullptr},
        emitting_{true},
        emit_rate_{0.8f + 0.4f * RandomFloat()},
        birth_time_{t->time_ms()},
        radius_{0.1f + RandomFloat() * 0.1f},
        tex_coord_{RandomFloat()},
        start_erode_{0.1f},
        start_spread_{4.0f},
        side_spread_rate_{1.0f},
        point_rand_scale_{1.0f},
        slice_rand_scale_{1.0f},
        tex_change_rate_{1.0f},
        emit_rate_falloff_rate_{1.0f},
        start_brightness_max_{0.9f},
        start_brightness_min_{0.3f},
        brightness_rand_{0.5f},
        start_fade_scale_{1.0f},
        glow_scale_{1.0f} {}
  void SetController(TendrilController* tc) {
    assert((controller_ == nullptr) ^ (tc == nullptr));
    controller_ = tc;
  }
  void UpdateSlices(BGDynamicsServer* t) {
    for (auto&& i : slices_) {
      i.p1.Update(t, *this);
      i.p2.Update(t, *this);

      // Push them together slightly if they're getting too far apart.
      Vector3f diff = i.p1.p - i.p2.p;
      if (diff.LengthSquared() > 2.5f) {
        i.p1.v += diff * -0.1f;
        i.p2.v += diff * 0.1f;
      }
    }

    // No shadows for thin tendrils.
    if (type_ == BGDynamicsTendrilType::kThinSmoke) {
      shadow_density_ = 0.0f;
    } else {
      float blend = 0.995f;

      auto i = slices_.begin();
      if (i == slices_.end()) {
        shadow_density_ = 0.0f;
      }
      int count = 0;
      while (i != slices_.end()) {
        shadow_position_ =
            blend * shadow_position_ + (1.0f - blend) * i->GetCenter();
        shadow_density_ = blend * shadow_density_
                          + (1.0f - blend) * (i->p1.fade + i->p2.fade) * 0.5f;
        count++;
        if (count > 4) break;  // only use first few...
        i++;
      }
    }
  }

  // Clear out old fully transparent slices.
  void PruneSlices() {
    // Clip transparent ones off the front.
    while (true) {
      auto i = slices_.begin();
      if (i == slices_.end()) break;
      auto i_next = i;
      i_next++;
      if (i_next != slices_.end() && i->isFullyTransparent()
          && i_next->isFullyTransparent()) {
        slices_.pop_front();
      } else {
        break;
      }
    }

    // ...and back.
    while (true) {
      auto i = slices_.rbegin();
      if (i == slices_.rend()) break;
      auto i_next = i;
      i_next++;
      if (i_next != slices_.rend() && i->isFullyTransparent()
          && i_next->isFullyTransparent()) {
        slices_.pop_back();
      } else {
        break;
      }
    }
  }

  ~Tendril();

  auto type() const -> BGDynamicsTendrilType { return type_; }

 private:
  TendrilController* controller_;
  Vector3f shadow_position_{0.0f, 0.0f, 0.0f};
  bool shading_flip_{};
  float wind_amt_{};
  float shadow_density_{};
  float emit_rate_{};
  float start_erode_{};
  float start_spread_{};
  float side_spread_rate_{};
  float point_rand_scale_{};
  float slice_rand_scale_{};
  float tex_change_rate_{};
  float emit_rate_falloff_rate_{};
  float start_brightness_max_{};
  float start_brightness_min_{};
  float brightness_rand_{};
  float start_fade_scale_{};
  float glow_scale_{};
  bool emitting_{};
  bool has_updated_{};
  std::list<Slice> slices_{};
  Slice cur_slice_{};
  Vector3f position_{0.0f, 0.0f, 0.0f};
  Vector3f prev_pos_{0.0f, 0.0f, 0.0f};
  Vector3f velocity_{0.0f, 0.0f, 0.0f};
  Vector3f medium_velocity_{0.0f, 0.0f, 0.0f};
  float birth_time_{};
  float tex_coord_{};
  float radius_{};
  BGDynamicsTendrilType type_{};
  friend class BGDynamicsServer;
};

class BGDynamicsServer::TendrilController {
 public:
  explicit TendrilController(Tendril* t) : tendril_{t} {
    tendril_->SetController(this);
  }
  ~TendrilController() {
    // If we have a tendril, tell it we're dying and that it's done emitting.
    if (tendril_) {
      tendril_->SetController(nullptr);
      tendril_->emit_rate_ = 0.0f;
    }
  }
  void update(const Vector3f& pos, const Vector3f& vel) {
    if (tendril_) {
      tendril_->prev_pos_ = tendril_->position_;
      tendril_->position_ = pos;
      tendril_->velocity_ = vel;
    }
  }

 private:
  Tendril* tendril_;
  friend class Tendril;
};

class BGDynamicsServer::Chunk {
 public:
  Chunk(BGDynamicsServer* t, const BGDynamicsEmission& event, bool dynamic,
        bool can_die = true, const Vector3f& d_bias = kVector3f0)
      : shadow_dist_(9999),
        type_(event.chunk_type),
        dynamic_(dynamic),
        can_die_(can_die),
        tendril_controller_(nullptr),
        birth_time_{t->time_ms()},
        flicker_{1.0f},
        flicker_scale_{1.0f} {
    flicker_scale_ = RandomFloat();                             // NOLINT
    flicker_scale_ = 1.0f - (flicker_scale_ * flicker_scale_);  // NOLINT
    if (type_ != BGDynamicsChunkType::kFlagStand) {
      if (type_ == BGDynamicsChunkType::kSplinter) {
        size_[0] = event.scale * 0.15f * (0.4f + 0.6f * RandomFloat());
        size_[1] = event.scale * 0.15f * (0.4f + 0.6f * RandomFloat());
        size_[2] = event.scale * 0.15f * (0.4f + 0.6f * RandomFloat()) * 5.0f;
      } else {
        size_[0] = event.scale * 0.15f * (0.3f + 0.7f * RandomFloat());
        size_[1] = event.scale * 0.15f * (0.3f + 0.7f * RandomFloat());
        size_[2] = event.scale * 0.15f * (0.3f + 0.7f * RandomFloat());
      }
    } else {
      size_[0] = size_[1] = size_[2] = 1.0f;
    }

    lifespan_ = 10000;
    if (type_ == BGDynamicsChunkType::kSpark) {
      lifespan_ = 500 + RandomFloat() * 1500;
      if (RandomFloat() < 0.1f) lifespan_ *= 3.0f;
    } else if (type_ == BGDynamicsChunkType::kSweat) {
      lifespan_ = 200 + RandomFloat() * 400;
      if (RandomFloat() < 0.1f) lifespan_ *= 2.0f;
    } else if (type_ == BGDynamicsChunkType::kFlagStand) {
      lifespan_ = 99999999.0f;
    }

    if (dynamic_) {
      body_ = dBodyCreate(t->ode_world_);
      geom_ = dCreateBox(nullptr, size_[0], size_[1], size_[2]);
      dGeomSetBody(geom_, body_);
      dMass m;
      dMassSetBox(&m, 1.0f, size_[0], size_[1], size_[2]);

      dBodySetMass(body_, &m);

      Vector3f v = event.velocity;
      float spread = event.spread;
      Vector3f v_rand = (Utils::Sphrand() + d_bias).Normalized() * RandomFloat()
                        * 40.0f * spread;

      dBodySetPosition(body_, event.position.x, event.position.y,
                       event.position.z);
      dBodySetLinearVel(body_, v.x + v_rand.x, v.y + v_rand.y, v.z + v_rand.z);
      dBodySetAngularVel(body_, (RandomFloat() - 0.5f) * 5.0f,
                         (RandomFloat() - 0.5f) * 5.0f,
                         (RandomFloat() - 0.5f) * 5.0f);
    } else {
      Vector3f axis{};
      if (type_ == BGDynamicsChunkType::kFlagStand) {
        axis = Vector3f(0, 1, 0);
      } else {
        axis = Utils::Sphrand();
      }
      Matrix44f m = Matrix44fScale(Vector3f(size_[0], size_[1], size_[2]))
                    * Matrix44fRotate(axis, RandomFloat() * 360.0f)
                    * Matrix44fTranslate(event.position);
      for (int i = 0; i < 16; i++) {
        static_transform_[i] = m.m[i];
      }

      // Assume we're sitting on the ground.
      shadow_dist_ = 0.0f;
    }
  }
  auto body() const -> dBodyID { return body_; }

  auto geom() const -> dGeomID { return geom_; }

  auto type() const -> BGDynamicsChunkType { return type_; }

  ~Chunk() {
    delete tendril_controller_;
    if (dynamic_) {
      dBodyDestroy(body_);
      dGeomDestroy(geom_);
    }
  }

  void UpdateTendril() {
    if (tendril_controller_) {
      tendril_controller_->update(Vector3f(dBodyGetPosition(body_)),
                                  Vector3f(dBodyGetLinearVel(body_)));
    }
  }
  auto can_die() const -> bool { return can_die_; }
  auto dynamic() const -> bool { return dynamic_; }
  auto size() const -> const float* { return size_; }
  auto static_transform() const -> const float* { return static_transform_; }

 private:
  TendrilController* tendril_controller_;
  bool dynamic_;
  bool can_die_;
  float lifespan_;
  float flicker_;
  float flicker_scale_;
  float static_transform_[16]{};
  BGDynamicsChunkType type_{};
  float birth_time_{};
  dBodyID body_{};
  dGeomID geom_{};
  float size_[3]{};
  float shadow_dist_;
  friend class BGDynamicsServer;
};  // Chunk

// Contains 2 ping-ponging particle buffers.
void BGDynamicsServer::ParticleSet::Emit(const Vector3f& pos,
                                         const Vector3f& vel, float r, float g,
                                         float b, float a, float dlife,
                                         float size, float d_size,
                                         float flicker) {
  particles[current_set].resize(particles[current_set].size() + 1);
  Particle& p(particles[current_set].back());
  p.x = pos.x;
  p.y = pos.y;
  p.z = pos.z;
  p.vx = vel.x * 1.0f + 0.02f * (RandomFloat() - 0.5f);
  p.vy = vel.y * 1.0f + 0.02f * (RandomFloat() - 0.5f);
  p.vz = vel.z * 1.0f + 0.02f * (RandomFloat() - 0.5f);
  p.r = r;
  p.g = g;
  p.b = b;
  p.a = a;
  p.life = 1.0f;
  assert(dlife < 0.0f);
  p.d_life = dlife;
  p.size = size;
  p.flicker = 1.0f;
  p.flicker_scale = flicker;
  p.d_size = d_size;
}

void BGDynamicsServer::ParticleSet::UpdateAndCreateSnapshot(
    Object::Ref<MeshIndexBuffer16>* index_buffer,
    Object::Ref<MeshBufferVertexSprite>* buffer) {
  assert(g_base->InBGDynamicsThread());

  auto p_count = static_cast<uint32_t>(particles[current_set].size());

  // Quick-out: return empty.
  if (p_count == 0) {
    return;
  }

  Particle* p_src = &particles[current_set][0];

  // Resize target to fit if all particles stay alive.
  particles[!current_set].resize(particles[current_set].size());
  Particle* p_dst = &particles[!current_set][0];

  auto* ibuf = Object::NewDeferred<MeshIndexBuffer16>(p_count * 6);
  // Logic thread is default owner for this type. It needs to be us until
  // we hand it over, so set that up before creating the first ref.
  ibuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
  *index_buffer = Object::CompleteDeferred(ibuf);

  auto* vbuf = Object::NewDeferred<MeshBufferVertexSprite>(p_count * 4);
  // Logic thread is default owner for this type. It needs to be us until
  // we hand it over, so set that up before creating the first ref.
  vbuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
  *buffer = Object::CompleteDeferred(vbuf);

  uint16_t* i_render = &(*index_buffer)->elements[0];
  VertexSprite* p_render = &(*buffer)->elements[0];
  uint32_t p_index = 0;
  uint32_t p_count_remaining = 0;
  uint32_t p_count_rendered = 0;
  for (uint32_t i = 0; i < p_count; i++) {
    float life = p_src->life + p_src->d_life;

    // Our opacity drops rapidly at the end.
    float o = 1.0f - life;
    o = 1.0f - (o * o * o);
    float size = std::max(0.0f, p_src->size + p_src->d_size);

    // Kill the particle if life or size falls to 0.
    if (life > 0.0f && size > 0) {
      p_count_remaining++;
      p_dst->life = life;
      p_dst->size = size;
      p_dst->x = p_src->x + p_src->vx;
      p_dst->y = p_src->y + p_src->vy;
      p_dst->z = p_src->z + p_src->vz;
      p_dst->r = p_src->r;
      p_dst->g = p_src->g;
      p_dst->b = p_src->b;
      p_dst->a = p_src->a;
      p_dst->vx = p_src->vx;
      p_dst->vy = p_src->vy - 0.00001f;
      p_dst->vz = p_src->vz;
      p_dst->d_life = p_src->d_life;
      p_dst->d_size = p_src->d_size;
      p_dst->flicker_scale = p_src->flicker_scale;

      // Every so often update our flicker value if we're flickering.
      if (p_src->flicker_scale != 0.0f) {
        if (RandomFloat() < 0.2f) {
          p_dst->flicker = std::max(
              0.0f, 1.0f + (RandomFloat() - 0.5f) * p_src->flicker_scale);
        } else {
          p_dst->flicker = p_src->flicker;
        }
      } else {
        p_dst->flicker = 1.0f;
      }

      // Render this point if it's got a positive size.
      if (p_dst->flicker > 0.0f && p_dst->size > 0.0f) {
        p_count_rendered++;

        // Add our 6 indices.
        {
          i_render[0] = static_cast<uint16_t>(p_index);
          i_render[1] = static_cast<uint16_t>(p_index + 1);
          i_render[2] = static_cast<uint16_t>(p_index + 2);
          i_render[3] = static_cast<uint16_t>(p_index + 1);
          i_render[4] = static_cast<uint16_t>(p_index + 3);
          i_render[5] = static_cast<uint16_t>(p_index + 2);
        }

        p_render[0].uv[0] = 0;
        p_render[0].uv[1] = 0;
        p_render[1].uv[0] = 0;
        p_render[1].uv[1] = 65535;
        p_render[2].uv[0] = 65535;
        p_render[2].uv[1] = 0;
        p_render[3].uv[0] = 65535;
        p_render[3].uv[1] = 65535;

        p_render[0].position[0] = p_render[1].position[0] =
            p_render[2].position[0] = p_render[3].position[0] = p_dst->x;
        p_render[0].position[1] = p_render[1].position[1] =
            p_render[2].position[1] = p_render[3].position[1] = p_dst->y;
        p_render[0].position[2] = p_render[1].position[2] =
            p_render[2].position[2] = p_render[3].position[2] = p_dst->z;
        p_render[0].size = p_render[1].size = p_render[2].size =
            p_render[3].size = p_dst->size * p_dst->flicker;
        p_render[0].color[0] = p_render[1].color[0] = p_render[2].color[0] =
            p_render[3].color[0] = p_dst->r * o;
        p_render[0].color[1] = p_render[1].color[1] = p_render[2].color[1] =
            p_render[3].color[1] = p_dst->g * o;
        p_render[0].color[2] = p_render[1].color[2] = p_render[2].color[2] =
            p_render[3].color[2] = p_dst->b * o;
        p_render[0].color[3] = p_render[1].color[3] = p_render[2].color[3] =
            p_render[3].color[3] = p_dst->a * o;

        i_render += 6;
        p_render += 4;
        p_index += 4;
      }
      p_dst++;
    }
    p_src++;
  }

  // Clamp dst and render sets to account for deaths.
  if (p_count != p_count_remaining) {
    particles[!current_set].resize(p_count_remaining);
  }

  if (p_count != p_count_rendered) {
    // If we dropped all the way to zero, return empty.
    // Otherwise, return a downsized buffer.
    if (p_count_rendered == 0) {
      *index_buffer = Object::Ref<MeshIndexBuffer16>();
      *buffer = Object::Ref<MeshBufferVertexSprite>();
    } else {
      (*index_buffer)->elements.resize(p_count_rendered * 6);
      (*buffer)->elements.resize(p_count_rendered * 4);
    }
  }
  current_set = !current_set;
}

BGDynamicsServer::BGDynamicsServer()
    : height_cache_(new BGDynamicsHeightCache()),
      collision_cache_(new CollisionCache) {
  // NOLINTNEXTLINE(cppcoreguidelines-prefer-member-initializer)
  ode_world_ = dWorldCreate();
  assert(ode_world_);
  dWorldSetGravity(ode_world_, 0.0f, -20.0f, 0.0f);
  dWorldSetContactSurfaceLayer(ode_world_, 0.001f);
  dWorldSetAutoDisableFlag(ode_world_, true);
  dWorldSetAutoDisableSteps(ode_world_, 5);
  dWorldSetAutoDisableLinearThreshold(ode_world_, 0.6f);
  dWorldSetAutoDisableAngularThreshold(ode_world_, 0.6f);
  dWorldSetAutoDisableSteps(ode_world_, 10);
  dWorldSetAutoDisableTime(ode_world_, 0);
  dWorldSetQuickStepNumIterations(ode_world_, 3);
  ode_contact_group_ = dJointGroupCreate(0);
  assert(ode_contact_group_);
}

void BGDynamicsServer::OnMainThreadStartApp() {
  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kBGDynamics);
  g_core->suspendable_event_loops.push_back(event_loop_);
}

BGDynamicsServer::Tendril::~Tendril() {
  // If we have a controller, tell them not to call us anymore.
  if (controller_) {
    controller_->tendril_ = nullptr;
  }
}

void BGDynamicsServer::UpdateFuses() {
  for (auto&& i : fuses_) {
    i->Update(this);
  }
}

void BGDynamicsServer::UpdateTendrils() {
  int render_slice_count = 0;

  for (auto i = tendrils_.begin(); i != tendrils_.end();) {
    Tendril& t(**i);

    // Kill off fully-dead tendrils.
    if (!t.emitting_ && t.slices_.size() < 2) {
      auto i_next = i;
      i_next++;
      if (t.type_ == BGDynamicsTendrilType::kThinSmoke) {
        tendril_count_thin_--;
      } else {
        tendril_count_thick_--;
      }
      assert(tendril_count_thin_ >= 0 && tendril_count_thick_ >= 0);
      delete *i;
      tendrils_.erase(i);
      i = i_next;
      continue;
    }

    // Clip transparent bits off the ends.
    t.PruneSlices();

    // Step existing tendril points.
    t.UpdateSlices(this);

    // Update the tendrils' physics if it is not being controlled.
    if (t.controller_ == nullptr) {
      t.prev_pos_ = t.position_;
      t.velocity_ += Vector3f(0, -0.1f, 0);  // Gravity.
      t.position_ += t.velocity_ * step_seconds_;
    }

    // If we're still emitting, potentially drop in some new slices.
    if (t.emitting_) {
      // Step from our last slice to our current position,
      // dropping in new slices as we go.
      Vector3f p = {0.0f, 0.0f, 0.0f};
      float tex_coord{};
      float emit_rate{};
      float start_erode{};
      float start_spread{};
      int slice_count = static_cast<int>(t.slices_.size());
      if (slice_count > 0) {
        p = t.slices_.back().GetCenter();
        tex_coord = t.slices_.back().p1.tex_coords[1];
        emit_rate = t.slices_.back().emit_rate;
        start_erode = t.slices_.back().start_erode;
        start_spread = t.slices_.back().start_spread;
      } else {
        p = t.prev_pos_;
        tex_coord = t.tex_coord_;
        emit_rate = t.emit_rate_;
        start_erode = t.start_erode_;
        start_spread = t.start_spread_;
      }
      Vector3f march_dir = t.position_ - p;
      float dist = march_dir.Length();

      // We flip our shading depending on which way the tendril is pointing
      // so that the light side is generally up.
      float start_brightness{};
      float start_brightness_2{};
      if (t.shading_flip_) {
        start_brightness = t.start_brightness_max_;
        start_brightness_2 = t.start_brightness_min_;
      } else {
        start_brightness = t.start_brightness_min_;
        start_brightness_2 = t.start_brightness_max_;
      }

      float start_brightness_rand = t.brightness_rand_;
      float erode_rate_randomness = 0.5f;
      float fade_rate_randomness = 2.0f;

      if (dist > 0.001f) {
        float span = 0.5f;
        march_dir = march_dir.Normalized() * span;
        Vector3f from_cam = cam_pos_ - p;
        Vector3f side_vec = Vector3f::Cross(march_dir, from_cam).Normalized();

        float inherit_velocity = 0.015f;

        // If this is our first step, drop a span immediately.
        if (!t.has_updated_) {
          Vector3f r_uniform = Utils::Sphrand(0.2f * t.slice_rand_scale_);
          float density = emit_rate > 0.1f ? 1.0f : emit_rate / 0.1f;

          t.slices_.emplace_back();
          Tendril::Slice& slice(t.slices_.back());
          slice.emit_rate = emit_rate;
          slice.start_erode = start_erode;
          slice.start_spread = start_spread;
          slice.p1.p = p - t.radius_ * side_vec * start_spread;
          slice.p1.v = t.medium_velocity_ * 0.3f
                       + t.velocity_ * inherit_velocity * 0.1f
                       - side_vec * t.radius_ * t.side_spread_rate_ + r_uniform
                       + Utils::Sphrand(0.13f * t.point_rand_scale_);
          slice.p1.tex_coords[0] = 0.0f;
          slice.p1.tex_coords[1] = tex_coord;
          slice.p1.erode = t.start_erode_;
          slice.p1.erode_rate = std::max(
              0.0f, density + erode_rate_randomness * (RandomFloat() - 0.5f));
          slice.p1.age_ms = 0;
          slice.p1.bouyancy = 0.3f + 0.2f * RandomFloat();
          slice.p1.brightness = std::max(
              0.0f, start_brightness
                        + (RandomFloat() - 0.5f) * start_brightness_rand);
          slice.p1.fade = 0.0f;
          slice.p1.glow_r = slice.p1.glow_g = slice.p1.glow_b = 0.0f;
          slice.p1.fade_rate = 1.0f + fade_rate_randomness * (RandomFloat());

          slice.p2.p = p + t.radius_ * side_vec * start_spread;
          slice.p2.v = t.medium_velocity_ * 0.3f
                       + t.velocity_ * inherit_velocity * 0.1f
                       + side_vec * t.radius_ * t.side_spread_rate_ + r_uniform
                       + Utils::Sphrand(0.13f * t.point_rand_scale_);
          slice.p2.tex_coords[0] = 0.25f;
          slice.p2.tex_coords[1] = tex_coord;
          slice.p2.erode = t.start_erode_;
          slice.p2.erode_rate = std::max(
              0.0f, density + erode_rate_randomness * (RandomFloat() - 0.5f));
          slice.p2.age_ms = 0;
          slice.p2.bouyancy = 0.3f + 0.2f * RandomFloat();
          slice.p2.brightness = std::max(
              0.0f, start_brightness_2
                        + (RandomFloat() - 0.5f) * start_brightness_rand);
          slice.p2.fade = 0.0f;
          slice.p2.glow_r = slice.p2.glow_g = slice.p2.glow_b = 0.0f;
          slice.p2.fade_rate = 1.0f + fade_rate_randomness * (RandomFloat());
        }

        t.has_updated_ = true;
        float tex_change_rate = 0.18f * t.tex_change_rate_;
        float emit_change_rate = -0.4f * t.emit_rate_falloff_rate_;
        float start_erode_change_rate = 1.0f;
        float start_spread_change_rate = -0.35f;

        // Reset our tex coord to that of the last span for marching purposes.
        for (; dist > span; dist -= span) {  // NOLINT
          p += march_dir;
          tex_coord += span * tex_change_rate;
          emit_rate = std::max(0.0f, emit_rate + span * emit_change_rate);
          start_erode =
              std::min(1.0f, start_erode + span * start_erode_change_rate);
          start_spread =
              std::max(1.0f, start_spread + span * start_spread_change_rate);

          // General density stays high until emit rate gets low.
          float density = emit_rate > 0.1f ? 1.0f : emit_rate / 0.1f;

          Vector3f r_uniform = Utils::Sphrand(0.2f * t.slice_rand_scale_);
          t.slices_.emplace_back();
          Tendril::Slice& slice(t.slices_.back());
          slice.emit_rate = emit_rate;
          slice.start_erode = start_erode;
          slice.start_spread = start_spread;
          slice.p1.p = p - t.radius_ * side_vec * start_spread;
          slice.p1.v = t.medium_velocity_ * 0.3f
                       + t.velocity_ * inherit_velocity
                       - side_vec * t.radius_ * t.side_spread_rate_ + r_uniform
                       + Utils::Sphrand(0.2f * t.point_rand_scale_);
          slice.p1.tex_coords[0] = 0.0f;
          slice.p1.tex_coords[1] = tex_coord;
          slice.p1.erode = start_erode;
          slice.p1.erode_rate = std::max(
              0.0f, density + erode_rate_randomness * (RandomFloat() - 0.5f));
          slice.p1.age_ms = 0;
          slice.p1.bouyancy = 0.3f + 0.2f * RandomFloat();
          slice.p1.brightness = std::max(
              0.0f, start_brightness
                        + (RandomFloat() - 0.5f) * start_brightness_rand);
          slice.p1.fade = density * t.start_fade_scale_;
          slice.p1.glow_r = slice.p1.glow_g = slice.p1.glow_b = 0.0f;
          slice.p1.fade_rate = 1.0f + fade_rate_randomness * (RandomFloat());

          slice.p2.p = p + t.radius_ * side_vec * start_spread;
          slice.p2.v = t.medium_velocity_ * 0.3f
                       + t.velocity_ * inherit_velocity
                       + side_vec * t.radius_ * t.side_spread_rate_ + r_uniform
                       + Utils::Sphrand(0.2f * t.point_rand_scale_);
          slice.p2.tex_coords[0] = 0.25f;
          slice.p2.tex_coords[1] = tex_coord;
          slice.p2.erode = start_erode;
          slice.p2.erode_rate = std::max(
              0.0f, density + erode_rate_randomness * (RandomFloat() - 0.5f));
          slice.p2.age_ms = 0;
          slice.p2.bouyancy = 0.3f + 0.2f * RandomFloat();
          slice.p2.brightness = std::max(
              0.0f, start_brightness_2
                        + (RandomFloat() - 0.5f) * start_brightness_rand);
          slice.p2.fade = density * t.start_fade_scale_;
          slice.p2.glow_r = slice.p2.glow_g = slice.p2.glow_b = 0.0f;
          slice.p2.fade_rate = 1.0f + fade_rate_randomness * (RandomFloat());

          // If our emit rate has dropped to zero, this will be our last span.
          if (t.emit_rate_ <= 0.001f) t.emitting_ = false;
        }
        // Add leftover dist to wind up with our current tex-coord/emit-rate.
        t.tex_coord_ = tex_coord + (dist * tex_change_rate);
        t.emit_rate_ = emit_rate + (dist * emit_change_rate);
        t.start_erode_ = start_erode + (dist * start_erode_change_rate);
        t.start_spread_ =
            std::max(1.0f, start_spread + dist * start_spread_change_rate);

        // Update our at-emitter slice.
        float density = t.emit_rate_ > 0.1f ? 1.0f : t.emit_rate_ / 0.1f;

        t.cur_slice_.p1.p =
            t.position_ - t.radius_ * side_vec * t.start_spread_;
        t.cur_slice_.p1.tex_coords[0] = 0.0f;
        t.cur_slice_.p1.tex_coords[1] = t.tex_coord_;
        t.cur_slice_.p1.erode = t.start_erode_;
        t.cur_slice_.p1.erode_rate = std::max(
            0.0f, density + erode_rate_randomness * (RandomFloat() - 0.5f));
        t.cur_slice_.p1.age_ms = 0;
        t.cur_slice_.p1.brightness = start_brightness;
        t.cur_slice_.p1.fade = density * t.start_fade_scale_;
        t.cur_slice_.p1.glow_r = t.cur_slice_.p1.glow_g =
            t.cur_slice_.p1.glow_b = 0.0f;
        t.cur_slice_.p1.fade_rate =
            1.0f + fade_rate_randomness * (RandomFloat());

        t.cur_slice_.p2.p =
            t.position_ + t.radius_ * side_vec * t.start_spread_;
        t.cur_slice_.p2.tex_coords[0] = 0.25f;
        t.cur_slice_.p2.tex_coords[1] = t.tex_coord_;
        t.cur_slice_.p2.erode = t.start_erode_;
        t.cur_slice_.p2.erode_rate = std::max(
            0.0f, density + erode_rate_randomness * (RandomFloat() - 0.5f));
        t.cur_slice_.p2.age_ms = 0;
        t.cur_slice_.p2.brightness = start_brightness_2;
        t.cur_slice_.p2.fade = density * t.start_fade_scale_;
        t.cur_slice_.p2.glow_r = t.cur_slice_.p2.glow_g =
            t.cur_slice_.p2.glow_b = 0.0f;
        t.cur_slice_.p2.fade_rate =
            1.0f + fade_rate_randomness * (RandomFloat());
      }
    }

    // Ok now update lighting and distortion on our tendril points and store
    // them for rendering.
    {
      for (auto&& s : t.slices_) {
        render_slice_count++;
        s.p1.UpdateGlow(*this, t.glow_scale_);
        s.p2.UpdateGlow(*this, t.glow_scale_);
        s.p1.UpdateDistortion(*this);
        s.p2.UpdateDistortion(*this);
      }
      // Also update our in-progress ones.
      render_slice_count++;
      t.cur_slice_.p1.UpdateGlow(*this, t.glow_scale_);
      t.cur_slice_.p2.UpdateGlow(*this, t.glow_scale_);
      t.cur_slice_.p1.UpdateDistortion(*this);
      t.cur_slice_.p2.UpdateDistortion(*this);
    }
    i++;
  }
}

void BGDynamicsServer::Clear() {
  // Clear chunks.
  {
    auto i = chunks_.begin();
    while (i != chunks_.end()) {
      delete *i;
      chunks_.erase(i);
      chunk_count_--;
      i = chunks_.begin();
      assert(chunk_count_ >= 0);
    }
    assert(chunk_count_ == 0);
  }

  // ..and tendrils.
  {
    auto i = tendrils_.begin();
    while (i != tendrils_.end()) {
      if ((**i).type_ == BGDynamicsTendrilType::kThinSmoke) {
        tendril_count_thin_--;
      } else {
        tendril_count_thick_--;
      }
      delete *i;
      tendrils_.erase(i);
      i = tendrils_.begin();
    }
    assert(tendril_count_thin_ == 0 && tendril_count_thick_ == 0);
  }
}

void BGDynamicsServer::PushEmitCall(const BGDynamicsEmission& def) {
  event_loop()->PushCall([this, def] { Emit(def); });
}

void BGDynamicsServer::Emit(const BGDynamicsEmission& def) {
  assert(g_base->InBGDynamicsThread());

  if (def.emit_type == BGDynamicsEmitType::kDistortion) {
    fields_.push_back(new Field(this, def.position, def.spread));
    return;
  }

  // First off, lets ramp down the number of things we're making depending
  // on settings or how many we already have, etc.
  int emit_count = def.count;

  int tendril_thick_max = 20;
  int tendril_thin_max = 14;
  int chunk_max = 200;

  // Scale our counts down based on a few things.
  if (graphics_quality_ <= GraphicsQuality::kLow) {
    emit_count = static_cast<int>(static_cast<float>(emit_count) * 0.35f);
    tendril_thick_max = 0;
    tendril_thin_max = 0;
    chunk_max = static_cast<int>(static_cast<float>(chunk_max) * 0.5f);
  } else if (graphics_quality_ <= GraphicsQuality::kMedium) {
    tendril_thick_max =
        static_cast<int>(static_cast<float>(tendril_thick_max) * 0.5f);
    tendril_thin_max =
        static_cast<int>(static_cast<float>(tendril_thin_max) * 0.5f);
    chunk_max = static_cast<int>(static_cast<float>(chunk_max) * 0.75f);
  } else if (graphics_quality_ == GraphicsQuality::kHigh) {
    emit_count = static_cast<int>(static_cast<float>(emit_count) * 0.8f);
    tendril_thick_max =
        static_cast<int>(static_cast<float>(tendril_thick_max) * 0.6f);
    tendril_thin_max =
        static_cast<int>(static_cast<float>(tendril_thin_max) * 0.6f);
    chunk_max = static_cast<int>(static_cast<float>(chunk_max) * 0.75f);
  } else {
    // (higher-quality)

#if BA_RIFT_BUILD
    // Rift build is gonna be running on beefy hardware; let's go crazy
    // here..
    chunk_max *= 2.5f;
    emit_count *= 2.5f;
    tendril_thin_max *= 2.5f;
#endif

#if BA_VARIANT_DEMO
    // lets beef up our demo kiosk build too.. what the heck.
    chunk_max *= 2.5f;
    emit_count *= 2.5f;
    tendril_thin_max *= 2.5f;
#endif
  }

  if (def.emit_type == BGDynamicsEmitType::kTendrils) {
    if (def.tendril_type == BGDynamicsTendrilType::kThinSmoke) {
      // For thin tendrils, start scaling back once we pass 8 tendrils.
      // Once we're at tendril_thin_max, stop adding completely.
      int scale_count = tendril_thin_max / 3;
      if (tendril_count_thin_ >= tendril_thin_max) {
        emit_count = 0;
      } else if (tendril_count_thin_ > scale_count) {
        emit_count = static_cast<int>(
            static_cast<float>(emit_count)
            * (1.0f
               - static_cast<float>(tendril_count_thin_ - scale_count)
                     / static_cast<float>(tendril_thin_max - scale_count)));
      }
    } else {
      // For thick tendrils, start scaling back once we pass 8 tendrils.
      // Once we're at tendril_thick_max, stop adding completely.
      int scale_count = tendril_thick_max / 3;
      if (tendril_count_thick_ >= tendril_thick_max) {
        emit_count = 0;
      } else if (tendril_count_thick_ > scale_count) {
        emit_count = static_cast<int>(
            static_cast<float>(emit_count)
            * (1.0f
               - static_cast<float>(tendril_count_thick_ - scale_count)
                     / static_cast<float>(tendril_thick_max - scale_count)));
      }
    }
  } else {
    // For debris, start scaling back once we pass 50... at chunk_max lets
    // stop.
    if (chunk_count_ >= chunk_max) {
      emit_count = 0;
    } else if (chunk_count_ > 50) {
      emit_count =
          static_cast<int>(static_cast<float>(emit_count)
                           * (1.0f
                              - static_cast<float>(chunk_count_ - 50)
                                    / static_cast<float>(chunk_max - 50)));
    }
  }

  bool near_surface = false;
  Vector3f surface_normal = {0.0f, 0.0f, 0.0f};
  float surface_closeness = 0.0f;

  // For the chunks/tendrils case, lets throw down a ray in the provided
  // velocity direction. If we hit something nearby, we can use that info
  // to adjust our emission.
  if (def.emit_type == BGDynamicsEmitType::kChunks
      || def.emit_type == BGDynamicsEmitType::kTendrils) {
    dGeomID ray = dCreateRay(nullptr, 2.0f);
    dGeomRaySetClosestHit(ray, true);
    Vector3f dir = def.velocity;
    dir.y -= RandomFloat() * 10.0f;  // bias downward
    dGeomRaySet(ray, def.position.x, def.position.y, def.position.z, dir.x,
                dir.y, dir.z);
    dContact contact[1];
    for (auto&& t : terrains_) {
      dGeomID t_geom = t->geom();
      if (dCollide(ray, t_geom, 1, &contact[0].geom, sizeof(dContact))) {
        near_surface = true;
        surface_normal = contact[0].geom.normal;
        float len = (Vector3f(contact[0].geom.pos) - def.position).Length();
        // At length 0.1, closeness is 1; at 2 its 0.
        surface_closeness =
            1.0f - std::min(1.0f, std::max(0.0f, (len - 0.2f) / (2.0f - 0.2f)));
        break;
      }
    }

    dGeomDestroy(ray);
  }

  Vector3f d_bias = {0.0f, 0.0f, 0.0f};
  if (near_surface)
    d_bias = surface_normal * RandomFloat() * 6.0f * surface_closeness;

  switch (def.emit_type) {
    case BGDynamicsEmitType::kChunks: {
      // Tone down bias on splinters - we always want those flying
      // every which way.
      if (def.chunk_type == BGDynamicsChunkType::kSplinter) {
        d_bias *= 0.3f;
      }

      for (int i = 0; i < emit_count; i++) {
        // Bias *most* of our chunks (looks too empty if *everything* is
        // going one direction).

        auto* chunk = new Chunk(this, def, true, true,
                                RandomFloat() < 0.8f ? d_bias : kVector3f0);

        bool do_tendril = false;
        if (def.chunk_type == BGDynamicsChunkType::kSpark
            && RandomFloat() < 0.13f) {  // NOLINT(bugprone-branch-clone)
          do_tendril = true;
        } else if (def.chunk_type == BGDynamicsChunkType::kSplinter
                   && RandomFloat() < 0.2f) {
          do_tendril = true;
        }

        // If we're emitting sparks, occasionally give one of them a
        // smoke tendril.
        if (do_tendril) {
          // Create a tendril, create a controller for it, and store it
          // with the chunk.
          {
            BGDynamicsTendrilType tendril_type =
                BGDynamicsTendrilType::kThinSmoke;
            auto* t = new Tendril(this);
            t->type_ = tendril_type;
            t->shading_flip_ = false;
            t->wind_amt_ = 0.4f + RandomFloat() * 1.6f;
            t->shadow_density_ = 1.0f;
            {
              t->radius_ *= 0.15f;
              t->side_spread_rate_ = 0.3f;
              t->point_rand_scale_ = 0.5f;
              t->slice_rand_scale_ = 0.5f;
              t->tex_change_rate_ = 1.5f + RandomFloat() * 2.0f;
              t->emit_rate_falloff_rate_ = 0.2f + RandomFloat() * 0.6f;
              t->start_brightness_max_ = 0.92f;
              t->start_brightness_min_ = 0.9f;
              t->brightness_rand_ = 0.1f;
              t->start_fade_scale_ = 0.15f + RandomFloat() * 0.2f;
              t->glow_scale_ = 1.0f;
            }
            tendrils_.push_back(t);
            tendril_count_thin_++;
            auto* c = new TendrilController(t);
            chunk->tendril_controller_ = c;
            chunk->UpdateTendril();
          }
        }
        chunks_.push_back(chunk);
        chunk_count_++;
      }
      break;
    }
    case BGDynamicsEmitType::kStickers: {
      BGDynamicsEmission edef = def;
      dGeomID ray = dCreateRay(nullptr, 4.0f);
      dGeomRaySetClosestHit(ray, true);
      for (int i = 0; i < emit_count; i++) {
        Vector3f dir = Utils::Sphrand(def.spread);
        dir.y -= def.spread * 2.5f * RandomFloat();  // bias downward
        dGeomRaySet(ray, def.position.x, def.position.y + 0.5f, def.position.z,
                    dir.x, dir.y, dir.z);
        dContact contact[1];
        for (auto&& t : terrains_) {
          dGeomID t_geom = t->geom();
          if (dCollide(ray, t_geom, 1, &contact[0].geom, sizeof(dContact))) {
            // Create a static chunk at this hit point.
            edef.position = Vector3f(contact[0].geom.pos);
            chunks_.push_back(new Chunk(this, edef, false));
            chunk_count_++;
          }
        }
      }
      dGeomDestroy(ray);
      break;
    }
    case BGDynamicsEmitType::kTendrils: {
#if BA_DEBUG_BUILD
      g_debug_lines.clear();
      g_debug_points.clear();
      g_debug_points.push_back(def.position);
#endif

      float ray_len = 1.5f;
      float ray_offset = 0.3f;
      dGeomID ray = dCreateRay(nullptr, ray_len);
      dGeomRaySetClosestHit(ray, true);
      for (int i = 0; i < emit_count; i++) {
        Vector3f dir = (Utils::Sphrand() + d_bias * 0.5f).Normalized();
        dGeomRaySet(ray, def.position.x, def.position.y + ray_offset,
                    def.position.z, dir.x, dir.y, dir.z);
        dContact contact[1];
        Vector3f pos = {0.0f, 0.0f, 0.0f};
        Vector3f vel = {0.0f, 0.0f, 0.0f};
        bool hit = false;
        for (auto&& t : terrains_) {
          dGeomID t_geom = t->geom();
          if (dCollide(ray, t_geom, 1, &contact[0].geom, sizeof(dContact))) {
            pos = Vector3f(contact[0].geom.pos);
            vel = Reflect(dir, Vector3f(contact[0].geom.normal));
            // bias direction up a bit... this way it'll hopefully be less
            // likely to point underground when we smash it down on the
            // camera plane
            vel.y += RandomFloat() * def.spread * 1.0f;
            hit = true;
            break;
          }
        }
        if (!hit) {
          // since dbias pushes us all in a direction away from a surface,
          // nudge our start pos in the opposite dir a bit so that we butt up
          // against the surface more
          pos = def.position + d_bias * RandomFloat() * -0.3f;
          vel = dir;
        }
#if BA_DEBUG_BUILD
        g_debug_lines.emplace_back(
            def.position + Vector3f(0, ray_offset, 0),
            def.position + Vector3f(0, ray_offset, 0) + (dir * ray_len),
            hit ? Vector3f(1, 0, 0) : Vector3f(0, 1, 0));
#endif

        Vector3f to_cam = (cam_pos_ - pos).Normalized();

        // Push the velocity towards the camera z plane to minimize
        // artifacts from moving towards/away from cam.
        Vector3f cam_component = to_cam * (vel.Dot(to_cam));
        vel -= 0.8f * cam_component;

        // Let's also push our pos towards the cam a wee bit so less is
        // clipped.
        pos += to_cam * 0.8f;

        // Now that we've got direction, assign random velocity.
        vel = vel.Normalized() * (10.0f + RandomFloat() * 30.0f);

        {
          auto* t = new Tendril(this);
          t->type_ = def.tendril_type;
          t->prev_pos_ = t->position_ = pos;
          t->shadow_position_ = pos;
          t->shading_flip_ = (vel.x > 0.0f);
          t->wind_amt_ = 0.4f + RandomFloat() * 1.6f;
          t->shadow_density_ = 1.0f;
          t->velocity_ = vel;
          if (def.tendril_type == BGDynamicsTendrilType::kThinSmoke) {
            t->radius_ *= 0.2f;
            t->side_spread_rate_ = 0.3f;
            t->point_rand_scale_ = 0.3f;
            t->tex_change_rate_ = 1.0f + RandomFloat() * 2.0f;
            t->emit_rate_falloff_rate_ = 0.45f + RandomFloat() * 0.2f;
            t->start_brightness_max_ = 0.82f;
            t->start_brightness_min_ = 0.8f;
            t->brightness_rand_ = 0.1f;
            t->start_fade_scale_ = 0.1f + RandomFloat() * 0.2f;
            t->glow_scale_ = 0.15f;
          } else {
            t->radius_ *= 0.7f + RandomFloat() * 0.2f;
            t->side_spread_rate_ = 0.2f + 4.0f * RandomFloat();
            t->emit_rate_falloff_rate_ = 0.9f + RandomFloat() * 0.6f;
            t->glow_scale_ = 1.0f;
          }
          tendrils_.push_back(t);
          if (def.tendril_type == BGDynamicsTendrilType::kThinSmoke) {
            tendril_count_thin_++;
          } else {
            tendril_count_thick_++;
          }
        }
      }
      dGeomDestroy(ray);
      break;
    }
    case BGDynamicsEmitType::kFlagStand: {
      float ray_len = 10.0f;
      dGeomID ray = dCreateRay(nullptr, ray_len);
      dGeomRaySetClosestHit(ray, true);
      Vector3f dir(0.0f, -1.0f, 0.0f);
      dGeomRaySet(ray, def.position.x, def.position.y, def.position.z, dir.x,
                  dir.y, dir.z);
      dContact contact[1];
      for (auto&& t : terrains_) {
        dGeomID t_geom = t->geom();
        if (dCollide(ray, t_geom, 1, &contact[0].geom, sizeof(dContact))) {
          BGDynamicsEmission edef = def;
          edef.chunk_type = BGDynamicsChunkType::kFlagStand;
          edef.position = Vector3f(contact[0].geom.pos);
          chunks_.push_back(new Chunk(this, edef, false, false));
          chunk_count_++;
          break;
        }
      }
      dGeomDestroy(ray);
      break;
    }
    case BGDynamicsEmitType::kFairyDust: {
      spark_particles_->Emit(
          Vector3f(def.position.x + 0.9f * (RandomFloat() - 0.5f),
                   def.position.y + 0.9f * (RandomFloat() - 0.5f),
                   def.position.z + 0.9f * (RandomFloat() - 0.5f)),
          0.001f * def.velocity, 0.8f + 3.0f * +RandomFloat(),
          0.8f + 3.0f * RandomFloat(), 0.8f + 3.0f * RandomFloat(), 0,
          -0.01f,                         // dlife
          0.05f + 0.05f * RandomFloat(),  // size
          -0.001f,                        // dsize
          5.0f                            // flicker intensity
      );                                  // NOLINT(whitespace/parens)
      break;
    }
    default: {
      int t = static_cast<int>(def.emit_type);
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "Invalid bg-dynamics emit type: " + std::to_string(t));
      break;
    }
  }
}

void BGDynamicsServer::PushRemoveTerrainCall(
    CollisionMeshAsset* collision_mesh) {
  event_loop()->PushCall([this, collision_mesh] {
    assert(collision_mesh != nullptr);
    bool found = false;
    for (auto i = terrains_.begin(); i != terrains_.end(); ++i) {
      if ((**i).GetCollisionMesh() == collision_mesh) {
        found = true;
        delete *i;
        terrains_.erase(i);
        break;
      }
    }
    if (!found) {
      throw Exception("invalid RemoveTerrainCall");
    }

    // Rebuild geom list from our present terrains.
    std::vector<dGeomID> geoms;
    geoms.reserve(terrains_.size());
    for (auto&& i : terrains_) {
      geoms.push_back(i->geom());
    }
    height_cache_->SetGeoms(geoms);
    collision_cache_->SetGeoms(geoms);

    // Clear existing stuff whenever this changes.
    Clear();
  });
}

void BGDynamicsServer::PushAddShadowCall(BGDynamicsShadowData* shadow_data) {
  event_loop()->PushCall([this, shadow_data] {
    assert(g_base->InBGDynamicsThread());
    std::scoped_lock lock(shadow_list_mutex_);
    shadows_.push_back(shadow_data);
  });
}

void BGDynamicsServer::PushRemoveShadowCall(BGDynamicsShadowData* shadow_data) {
  event_loop()->PushCall([this, shadow_data] {
    assert(g_base->InBGDynamicsThread());
    bool found = false;
    {
      std::scoped_lock lock(shadow_list_mutex_);
      for (auto i = shadows_.begin(); i != shadows_.end(); ++i) {
        if ((*i) == shadow_data) {
          found = true;
          shadows_.erase(i);
          break;
        }
      }
    }
    assert(found);
    delete shadow_data;
  });
}

void BGDynamicsServer::PushAddVolumeLightCall(
    BGDynamicsVolumeLightData* volume_light_data) {
  event_loop()->PushCall([this, volume_light_data] {
    // Add to our internal list.
    std::scoped_lock lock(volume_light_list_mutex_);
    volume_lights_.push_back(volume_light_data);
  });
}

void BGDynamicsServer::PushRemoveVolumeLightCall(
    BGDynamicsVolumeLightData* volume_light_data) {
  event_loop()->PushCall([this, volume_light_data] {
    // Remove from our list and kill.
    bool found = false;
    {
      std::scoped_lock lock(volume_light_list_mutex_);
      for (auto i = volume_lights_.begin(); i != volume_lights_.end(); ++i) {
        if ((*i) == volume_light_data) {
          found = true;
          volume_lights_.erase(i);
          break;
        }
      }
    }
    assert(found);
    delete volume_light_data;
  });
}

void BGDynamicsServer::PushAddFuseCall(BGDynamicsFuseData* fuse_data) {
  event_loop()->PushCall([this, fuse_data] {
    std::scoped_lock lock(fuse_list_mutex_);
    fuses_.push_back(fuse_data);
  });
}

void BGDynamicsServer::PushRemoveFuseCall(BGDynamicsFuseData* fuse_data) {
  event_loop()->PushCall([this, fuse_data] {
    bool found = false;
    {
      std::scoped_lock lock(fuse_list_mutex_);
      for (auto i = fuses_.begin(); i != fuses_.end(); i++) {
        if ((*i) == fuse_data) {
          found = true;
          fuses_.erase(i);
          break;
        }
      }
    }
    assert(found);
    delete fuse_data;
  });
}

void BGDynamicsServer::PushSetDebrisFrictionCall(float friction) {
  event_loop()->PushCall([this, friction] { debris_friction_ = friction; });
}

void BGDynamicsServer::PushSetDebrisKillHeightCall(float height) {
  event_loop()->PushCall([this, height] { debris_kill_height_ = height; });
}

auto BGDynamicsServer::CreateDrawSnapshot() -> BGDynamicsDrawSnapshot* {
  assert(g_base->InBGDynamicsThread());

  auto* ss = new BGDynamicsDrawSnapshot();

  uint32_t rock_count = 0;
  uint32_t ice_count = 0;
  uint32_t slime_count = 0;
  uint32_t metal_count = 0;
  uint32_t spark_count = 0;
  uint32_t splinter_count = 0;
  uint32_t sweat_count = 0;
  uint32_t flag_stand_count = 0;

  uint32_t shadow_max_count = 0;
  uint32_t light_max_count = 0;
  uint32_t shadow_drawn_count = 0;
  uint32_t light_drawn_count = 0;

  for (auto&& i : chunks_) {
    BGDynamicsChunkType t = i->type();
    switch (t) {
      case BGDynamicsChunkType::kRock:
        rock_count++;
        break;
      case BGDynamicsChunkType::kIce:
        ice_count++;
        break;
      case BGDynamicsChunkType::kSlime:
        slime_count++;
        break;
      case BGDynamicsChunkType::kMetal:
        metal_count++;
        break;
      case BGDynamicsChunkType::kSpark:
        spark_count++;
        break;
      case BGDynamicsChunkType::kSplinter:
        splinter_count++;
        break;
      case BGDynamicsChunkType::kSweat:
        sweat_count++;
        break;
      case BGDynamicsChunkType::kFlagStand:
        flag_stand_count++;
        break;
    }
    // tally shadow/lights
    switch (t) {
      case BGDynamicsChunkType::kFlagStand:
      case BGDynamicsChunkType::kSweat:
        break;  //  these have no shadows
      case BGDynamicsChunkType::kIce:
      case BGDynamicsChunkType::kSpark:
        light_max_count++;
        break;
      default:
        shadow_max_count++;
        break;
    }
  }

  Matrix44f* c_rock = nullptr;
  Matrix44f* c_ice = nullptr;
  Matrix44f* c_slime = nullptr;
  Matrix44f* c_metal = nullptr;
  Matrix44f* c_spark = nullptr;
  Matrix44f* c_splinter = nullptr;
  Matrix44f* c_sweat = nullptr;
  Matrix44f* c_flag_stand = nullptr;

  if (rock_count > 0) {
    ss->rocks.resize(rock_count);
    c_rock = ss->rocks.data();
  }
  if (ice_count > 0) {
    ss->ice.resize(ice_count);
    c_ice = ss->ice.data();
  }
  if (slime_count > 0) {
    ss->slime.resize(slime_count);
    c_slime = ss->slime.data();
  }
  if (metal_count > 0) {
    ss->metal.resize(metal_count);
    c_metal = ss->metal.data();
  }
  if (spark_count > 0) {
    ss->sparks.resize(spark_count);
    c_spark = ss->sparks.data();
  }
  if (splinter_count > 0) {
    ss->splinters.resize(splinter_count);
    c_splinter = ss->splinters.data();
  }
  if (sweat_count > 0) {
    ss->sweats.resize(sweat_count);
    c_sweat = ss->sweats.data();
  }
  if (flag_stand_count > 0) {
    ss->flag_stands.resize(flag_stand_count);
    c_flag_stand = ss->flag_stands.data();
  }

  // Allocate buffers as if we're drawing *all* lights/shadows for chunks.
  // We may prune this down.
  uint16_t *s_index = nullptr, *l_index = nullptr;
  VertexSprite *s_vertex = nullptr, *l_vertex = nullptr;
  uint32_t s_vertex_index = 0, l_vertex_index = 0;

  if (shadow_max_count > 0) {
    auto* ibuf = Object::NewDeferred<MeshIndexBuffer16>(shadow_max_count * 6);
    // Logic thread is default owner for this type. It needs to be us until
    // we hand it over, so set that up before creating the first ref.
    ibuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
    ss->shadow_indices = Object::CompleteDeferred(ibuf);
    s_index = &ss->shadow_indices->elements[0];

    auto* vbuf =
        Object::NewDeferred<MeshBufferVertexSprite>(shadow_max_count * 4);
    // Logic thread is default owner for this type. It needs to be us until
    // we hand it over, so set that up before creating the first ref.
    vbuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
    ss->shadow_vertices = Object::CompleteDeferred(vbuf);
    s_vertex = &ss->shadow_vertices->elements[0];
    s_vertex_index = 0;
  }

  if (light_max_count > 0) {
    auto* ibuf = Object::NewDeferred<MeshIndexBuffer16>(light_max_count * 6);
    // Logic thread is default owner for this type. It needs to be us until
    // we hand it over, so set that up before creating the first ref.
    ibuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
    ss->light_indices = Object::CompleteDeferred(ibuf);
    l_index = &ss->light_indices->elements[0];

    auto* vbuf =
        Object::NewDeferred<MeshBufferVertexSprite>(light_max_count * 4);
    // Logic thread is default owner for this type. It needs to be us until
    // we hand it over, so set that up before creating the first ref.
    vbuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
    ss->light_vertices = Object::CompleteDeferred(vbuf);
    l_vertex = &ss->light_vertices->elements[0];
    l_vertex_index = 0;
  }

  Matrix44f* c{};

  for (auto&& i : chunks_) {
    BGDynamicsChunkType type = i->type();
    switch (type) {
      case BGDynamicsChunkType::kRock:
        c = c_rock;
        break;
      case BGDynamicsChunkType::kIce:
        c = c_ice;
        break;
      case BGDynamicsChunkType::kSlime:
        c = c_slime;
        break;
      case BGDynamicsChunkType::kMetal:
        c = c_metal;
        break;
      case BGDynamicsChunkType::kSpark:
        c = c_spark;
        break;
      case BGDynamicsChunkType::kSplinter:
        c = c_splinter;
        break;
      case BGDynamicsChunkType::kSweat:
        c = c_sweat;
        break;
      case BGDynamicsChunkType::kFlagStand:
        c = c_flag_stand;
        break;
    }

    const float* s = i->size();
    if (i->dynamic()) {
      dBodyID b = i->body();
      const dReal* p = dBodyGetPosition(b);
      const dReal* r = dBodyGetRotation(b);
      (*c).m[0] = r[0] * s[0];  // NOLINT: clang-tidy says possible null
      (*c).m[1] = r[4] * s[0];
      (*c).m[2] = r[8] * s[0];
      (*c).m[3] = 0;
      (*c).m[4] = r[1] * s[1];
      (*c).m[5] = r[5] * s[1];
      (*c).m[6] = r[9] * s[1];
      (*c).m[7] = 0;
      (*c).m[8] = r[2] * s[2];
      (*c).m[9] = r[6] * s[2];
      (*c).m[10] = r[10] * s[2];
      (*c).m[11] = 0;
      (*c).m[12] = p[0];
      (*c).m[13] = p[1];
      (*c).m[14] = p[2];
      (*c).m[15] = 1;
    } else {
      // NOLINTNEXTLINE: clang-tidy complaining of possible null here.
      memcpy((*c).m, i->static_transform(), sizeof((*c)));
    }

    // Shadow size is just average of our dimensions.
    float shadow_size = (s[0] + s[1] + s[2]) * 0.3333f;

    // These are elongated so shadows are a bit big by default.
    if (type == BGDynamicsChunkType::kSplinter) shadow_size *= 0.65f;
    float flicker = i->flicker_;
    float shadow_dist = i->shadow_dist_;
    float life = std::min(1.0f, (static_cast<float>(time_ms_)
                                 - static_cast<float>(i->birth_time_))
                                    / i->lifespan_);

    // Shrink our matrix down over time.
    switch (type) {
      case BGDynamicsChunkType::kSpark:
      case BGDynamicsChunkType::kSweat: {
        float shrink_scale = (1.0f - life) * flicker;
        Matrix44f* m = &(*c);
        (*m) = Matrix44fScale(shrink_scale) * (*m);
        break;
      }
      default: {
        // Regular chunks shrink only when on the ground.
        float sd = shadow_dist;
        Matrix44f* m = &(*c);
        if (sd < 1.0f && sd >= 0) {
          float sink = -sd * life;
          (*m) = (*m) * Matrix44fTranslate(0, sink, 0);
        }
        float shrink_scale = 1.0f - life;
        (*m) = Matrix44fScale(shrink_scale) * (*m);
        break;
      }
    }

    // Go ahead and build a buffer for our lights/shadows so when it comes
    // time to draw we just have to upload it.
    float shadow_scale_mult = 1.0f;
    float max_shadow_scale = 2.3f;
    float max_shadow_grow_dist = 2.0f;
    float max_shadow_dist = 1.0f;
    bool draw_shadow{};
    bool draw_light{};
    switch (type) {
      case BGDynamicsChunkType::kIce:
      case BGDynamicsChunkType::kSpark: {
        draw_shadow = false;
        draw_light = true;
        shadow_scale_mult *= 8.0f;
        break;
      }
      case BGDynamicsChunkType::kFlagStand:
      case BGDynamicsChunkType::kSweat:
        draw_shadow = false;
        draw_light = false;
        break;  // These have no shadows.
      default: {
        draw_shadow = true;
        draw_light = false;
      }
    }

    if (draw_shadow || draw_light) {
      // Only draw light/shadow if we're within our max/min distances
      // from the ground.
      if (shadow_dist > -kShadowOccludeDistance
          && shadow_dist < max_shadow_dist) {
        float sd = shadow_dist;

        // Ok we'll draw this fella.
        uint16_t* this_i{};
        VertexSprite* this_v{};
        uint32_t this_v_index{};
        if (draw_shadow) {
          shadow_drawn_count++;
          this_i = s_index;
          this_v = s_vertex;
          this_v_index = s_vertex_index;
          s_index += 6;
          s_vertex += 4;
          s_vertex_index += 4;
        } else {
          light_drawn_count++;
          assert(draw_light);
          this_i = l_index;
          this_v = l_vertex;
          this_v_index = l_vertex_index;
          l_index += 6;
          l_vertex += 4;
          l_vertex_index += 4;
        }

        float* m = c->m;

        // As we get farther from the ground, our shadow gets bigger and
        // softer.
        float shadow_scale{};
        float density{};

        // Negative shadow_dist means some object is in front of our
        // shadow-caster. In this case lets keep our scale the same
        // as it would have been at zero dist but fade our density
        // out gradually as we become more deeply submerged.
        if (sd <= 0.0f) {
          shadow_scale = 1.0f;
          density = 1.0f - std::min(1.0f, -sd / kShadowOccludeDistance);
        } else {
          // Normal non-submerged shadow.
          shadow_scale =
              1.0f
              + std::max(0.0f, std::min(1.0f, (sd / max_shadow_grow_dist))
                                   * (max_shadow_scale - 1.0f));
          density = 0.5f
                    * g_base->graphics->GetShadowDensity(m[12], m[13], m[14])
                    * (1.0f - (sd / max_shadow_dist));
        }

        // Sink down over the course of our lifespan if we
        // know where the ground is.
        float sink = 0.0f;
        if (sd < 1.0f && sd >= 0.0f) {
          sink = -sd * life;
        }
        shadow_scale *= (1.0f - life);
        assert(shadow_scale >= 0.0f);

        // Drop our density as our shadow scale grows.
        // Do this *after* this is used to modulate density.
        shadow_scale *= shadow_scale_mult;

        // Add our 6 indices.
        {
          this_i[0] = static_cast<uint16_t>(this_v_index);
          this_i[1] = static_cast<uint16_t>(this_v_index + 1);
          this_i[2] = static_cast<uint16_t>(this_v_index + 2);
          this_i[3] = static_cast<uint16_t>(this_v_index + 1);
          this_i[4] = static_cast<uint16_t>(this_v_index + 3);
          this_i[5] = static_cast<uint16_t>(this_v_index + 2);
        }

        // Add our 4 verts.
        this_v[0].uv[0] = 0;
        this_v[0].uv[1] = 0;
        this_v[1].uv[0] = 0;
        this_v[1].uv[1] = 65535;
        this_v[2].uv[0] = 65535;
        this_v[2].uv[1] = 0;
        this_v[3].uv[0] = 65535;
        this_v[3].uv[1] = 65535;

        switch (type) {
          case BGDynamicsChunkType::kIce: {
            this_v[0].color[0] = this_v[1].color[0] = this_v[2].color[0] =
                this_v[3].color[0] = 0.1f * density;
            this_v[0].color[1] = this_v[1].color[1] = this_v[2].color[1] =
                this_v[3].color[1] = 0.1f * density;
            this_v[0].color[2] = this_v[1].color[2] = this_v[2].color[2] =
                this_v[3].color[2] = 0.2f * density;
            this_v[0].color[3] = this_v[1].color[3] = this_v[2].color[3] =
                this_v[3].color[3] = 0.2f * density;
            break;
          }
          case BGDynamicsChunkType::kSpark: {
            this_v[0].color[0] = this_v[1].color[0] = this_v[2].color[0] =
                this_v[3].color[0] = 0.3f * density;
            this_v[0].color[1] = this_v[1].color[1] = this_v[2].color[1] =
                this_v[3].color[1] = 0.12f * density;
            this_v[0].color[2] = this_v[1].color[2] = this_v[2].color[2] =
                this_v[3].color[2] = 0.10f * density;
            this_v[0].color[3] = this_v[1].color[3] = this_v[2].color[3] =
                this_v[3].color[3] = 0.1f * density;
            break;
          }
          default: {
            this_v[0].color[0] = this_v[1].color[0] = this_v[2].color[0] =
                this_v[3].color[0] = 0.0f;
            this_v[0].color[1] = this_v[1].color[1] = this_v[2].color[1] =
                this_v[3].color[1] = 0.0f;
            this_v[0].color[2] = this_v[1].color[2] = this_v[2].color[2] =
                this_v[3].color[2] = 0.0f;
            this_v[0].color[3] = this_v[1].color[3] = this_v[2].color[3] =
                this_v[3].color[3] = 0.4f * density;
            break;
          }
        }
        this_v[0].position[0] = this_v[1].position[0] = this_v[2].position[0] =
            this_v[3].position[0] = m[12];
        this_v[0].position[1] = this_v[1].position[1] = this_v[2].position[1] =
            this_v[3].position[1] = m[13] + sink;
        this_v[0].position[2] = this_v[1].position[2] = this_v[2].position[2] =
            this_v[3].position[2] = m[14];
        this_v[0].size = this_v[1].size = this_v[2].size = this_v[3].size =
            2.8f * shadow_size * shadow_scale;
      }
    }
    c++;
    switch (type) {
      case BGDynamicsChunkType::kRock:
        c_rock = c;
        break;
      case BGDynamicsChunkType::kIce:
        c_ice = c;
        break;
      case BGDynamicsChunkType::kSlime:
        c_slime = c;
        break;
      case BGDynamicsChunkType::kMetal:
        c_metal = c;
        break;
      case BGDynamicsChunkType::kSpark:
        c_spark = c;
        break;
      case BGDynamicsChunkType::kSplinter:
        c_splinter = c;
        break;
      case BGDynamicsChunkType::kSweat:
        c_sweat = c;
        break;
      case BGDynamicsChunkType::kFlagStand:
        c_flag_stand = c;
        break;
    }
  }
  if (shadow_max_count > 0) {
    if (shadow_drawn_count == 0) {
      // If we didn't actually draw *any*, completely kill our buffers.
      ss->shadow_indices.Clear();
      ss->shadow_vertices.Clear();
    } else if (shadow_drawn_count != shadow_max_count) {
      // Otherwise, resize our buffers down to what we actually used.
      assert(s_index - (&ss->shadow_indices->elements[0])
             == shadow_drawn_count * 6);
      assert(s_vertex - (&ss->shadow_vertices->elements[0])
             == shadow_drawn_count * 4);
      assert(ss->shadow_indices->elements.size() == shadow_max_count * 6);
      ss->shadow_indices->elements.resize(shadow_drawn_count * 6);
      assert(ss->shadow_vertices->elements.size() == shadow_max_count * 4);
      ss->shadow_vertices->elements.resize(shadow_drawn_count * 4);
    } else {
      assert(s_index - (&ss->shadow_indices->elements[0])
             == shadow_max_count * 6);
      assert(s_vertex - (&ss->shadow_vertices->elements[0])
             == shadow_max_count * 4);
    }
  }
  if (light_max_count > 0) {
    // If we didn't actually draw *any*, clear our buffers.
    if (light_drawn_count == 0) {
      ss->light_indices.Clear();
      ss->light_vertices.Clear();
    } else if (light_drawn_count != light_max_count) {
      // Otherwise, resize our buffers down to what we actually used.
      assert(l_index - (&ss->light_indices->elements[0])
             == light_drawn_count * 6);
      assert(l_vertex - (&ss->light_vertices->elements[0])
             == light_drawn_count * 4);
      assert(ss->light_indices->elements.size() == light_max_count * 6);
      ss->light_indices->elements.resize(light_drawn_count * 6);
      assert(ss->light_vertices->elements.size() == light_max_count * 4);
      ss->light_vertices->elements.resize(light_drawn_count * 4);
    } else {
      assert(l_index - (&ss->light_indices->elements[0])
             == light_max_count * 6);
      assert(l_vertex - (&ss->light_vertices->elements[0])
             == light_max_count * 4);
    }
  }

  // Now add tendrils.
  {
    int smoke_slice_count = 0;
    int smoke_index_count = 0;
    int shadow_count = 0;
    for (auto&& i : tendrils_) {
      const Tendril& t(*i);
      if (!t.has_updated_) continue;
      int slice_count =
          static_cast<int>(t.slices_.size() + (t.emitting_ ? 1 : 0));
      if (slice_count > 1) {
        shadow_count++;
        smoke_index_count += (slice_count - 1) * 6;
        smoke_slice_count += slice_count;
      }
    }
    if (smoke_slice_count > 0) {
      auto* ibuf = Object::NewDeferred<MeshIndexBuffer16>(smoke_index_count);
      // Logic thread is default owner for this type. It needs to be us until
      // we hand it over, so set that up before creating the first ref.
      ibuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
      ss->tendril_indices = Object::CompleteDeferred(ibuf);
      uint16_t* index = &ss->tendril_indices->elements[0];

      auto* vbuf =
          Object::NewDeferred<MeshBufferVertexSmokeFull>(smoke_slice_count * 2);
      // Logic thread is default owner for this type. It needs to be us until
      // we hand it over, so set that up before creating the first ref.
      vbuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
      ss->tendril_vertices = Object::CompleteDeferred(vbuf);
      VertexSmokeFull* v = &ss->tendril_vertices->elements[0];
      ss->tendril_shadows.reserve(static_cast<size_t>(shadow_count));
      int v_num = 0;
      for (auto&& i : tendrils_) {
        const Tendril& t(*i);
        if (!t.has_updated_) {
          continue;
        }
        int slice_count =
            static_cast<int>(t.slices_.size() + (t.emitting_ ? 1 : 0));
        if (slice_count < 2) {
          continue;
        }
        ss->tendril_shadows.emplace_back(t.shadow_position_, t.shadow_density_);
        for (auto&& slc : t.slices_) {
          v->position[0] = slc.p1.p_distorted.x;
          v->position[1] = slc.p1.p_distorted.y;
          v->position[2] = slc.p1.p_distorted.z;
          v->uv[0] = slc.p1.tex_coords[0];
          v->uv[1] = slc.p1.tex_coords[1];
          v->erode = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(255.0f * slc.p1.erode))));
          float fade = std::min(1.0f, slc.p1.fade);
          v->color[0] = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(kSmokeGlow * slc.p1.glow_r))));
          v->color[1] = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(kSmokeGlow * slc.p1.glow_g))));
          v->color[2] = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(kSmokeGlow * slc.p1.glow_b))));
          v->color[3] = static_cast<uint8_t>(
              std::max(0, std::min(255, static_cast<int>(255.0f * fade))));
          v->diffuse = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(255.0f * slc.p1.brightness))));
          v++;
          v->position[0] = slc.p2.p_distorted.x;
          v->position[1] = slc.p2.p_distorted.y;
          v->position[2] = slc.p2.p_distorted.z;
          v->uv[0] = slc.p2.tex_coords[0];
          v->uv[1] = slc.p2.tex_coords[1];
          v->erode = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(255.0f * slc.p2.erode))));
          fade = std::min(1.0f, slc.p2.fade);
          v->color[0] = static_cast<uint8_t>(std::max(
              0,
              std::min(255, static_cast<int>(kSmokeBaseGlow
                                             + kSmokeGlow * slc.p2.glow_r))));
          v->color[1] = static_cast<uint8_t>(std::max(
              0,
              std::min(255, static_cast<int>(kSmokeBaseGlow
                                             + kSmokeGlow * slc.p2.glow_g))));
          v->color[2] = static_cast<uint8_t>(std::max(
              0,
              std::min(255, static_cast<int>(kSmokeBaseGlow
                                             + kSmokeGlow * slc.p2.glow_b))));
          v->color[3] = static_cast<uint8_t>(
              std::max(0, std::min(255, static_cast<int>(255.0f * fade))));
          v->diffuse = static_cast<uint8_t>(std::max(
              0, std::min(255, static_cast<int>(255.0f * slc.p2.brightness))));
          v++;
        }

        // Spit out the in-progress slice if the tendril is still emitting.
        if (t.emitting_) {
          v->position[0] = t.cur_slice_.p1.p_distorted.x;
          v->position[1] = t.cur_slice_.p1.p_distorted.y;
          v->position[2] = t.cur_slice_.p1.p_distorted.z;
          v->uv[0] = t.cur_slice_.p1.tex_coords[0];
          v->uv[1] = t.cur_slice_.p1.tex_coords[1];
          v->erode = std::max(
              0,
              std::min(255, static_cast<int>(255.0f * t.cur_slice_.p1.erode)));
          float fade = std::min(1.0f, t.cur_slice_.p1.fade);
          v->color[0] = std::max(
              0, std::min(255, static_cast<int>(
                                   kSmokeBaseGlow
                                   + kSmokeGlow * t.cur_slice_.p1.glow_r)));
          v->color[1] = std::max(
              0, std::min(255, static_cast<int>(
                                   kSmokeBaseGlow
                                   + kSmokeGlow * t.cur_slice_.p1.glow_g)));
          v->color[2] = std::max(
              0, std::min(255, static_cast<int>(
                                   kSmokeBaseGlow
                                   + kSmokeGlow * t.cur_slice_.p1.glow_b)));
          v->color[3] = static_cast<uint8_t>(
              std::max(0, std::min(255, static_cast<int>(255.0f * fade))));
          v->diffuse = std::max(
              0, std::min(255, static_cast<int>(255.0f
                                                * t.cur_slice_.p1.brightness)));
          v++;
          v->position[0] = t.cur_slice_.p2.p_distorted.x;
          v->position[1] = t.cur_slice_.p2.p_distorted.y;
          v->position[2] = t.cur_slice_.p2.p_distorted.z;
          v->uv[0] = t.cur_slice_.p2.tex_coords[0];
          v->uv[1] = t.cur_slice_.p2.tex_coords[1];
          v->erode = std::max(
              0,
              std::min(255, static_cast<int>(255.0f * t.cur_slice_.p2.erode)));
          fade = std::min(1.0f, t.cur_slice_.p2.fade);
          v->color[0] = std::max(
              0, std::min(255, static_cast<int>(
                                   kSmokeBaseGlow
                                   + kSmokeGlow * t.cur_slice_.p2.glow_r)));
          v->color[1] = std::max(
              0, std::min(255, static_cast<int>(
                                   kSmokeBaseGlow
                                   + kSmokeGlow * t.cur_slice_.p2.glow_g)));
          v->color[2] = std::max(
              0, std::min(255, static_cast<int>(
                                   kSmokeBaseGlow
                                   + kSmokeGlow * t.cur_slice_.p2.glow_b)));
          v->color[3] = static_cast<uint8_t>(
              std::max(0, std::min(255, static_cast<int>(255.0f * fade))));
          v->diffuse = std::max(
              0, std::min(255, static_cast<int>(255.0f
                                                * t.cur_slice_.p2.brightness)));
          v++;
        }

        // Now write the tri indices for this slice.
        for (int j = 0; j < slice_count - 1; j++) {
          *index++ = static_cast<uint16_t>(v_num);
          *index++ = static_cast<uint16_t>(v_num + 1);
          *index++ = static_cast<uint16_t>(v_num + 2);
          *index++ = static_cast<uint16_t>(v_num + 2);
          *index++ = static_cast<uint16_t>(v_num + 1);
          *index++ = static_cast<uint16_t>(v_num + 3);
          v_num += 2;
        }
        v_num += 2;
      }
      assert(ss->tendril_shadows.size() == shadow_count);
      assert(index == (&ss->tendril_indices->elements[0]) + smoke_index_count);
      assert(v
             == (&ss->tendril_vertices->elements[0]) + (smoke_slice_count * 2));
    }
  }

  // Now add fuses.
  {
    int fuse_count = 0;
    for (auto&& i : fuses_) {
      if (i->initial_position_set_) {
        fuse_count++;
      }
    }

    if (fuse_count > 0) {
      auto index_count =
          static_cast<uint32_t>(6 * (kFusePointCount - 1) * fuse_count);
      auto vertex_count =
          static_cast<uint32_t>(2 * kFusePointCount * fuse_count);

      auto* ibuf = Object::NewDeferred<MeshIndexBuffer16>(index_count);
      // Logic thread is default owner for this type. It needs to be us until
      // we hand it over, so set that up before creating the first ref.
      ibuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
      ss->fuse_indices = Object::CompleteDeferred(ibuf);

      auto* vbuf =
          Object::NewDeferred<MeshBufferVertexSimpleFull>(vertex_count);
      // Logic thread is default owner for this type. It needs to be us until
      // we hand it over, so set that up before creating the first ref.
      vbuf->SetThreadOwnership(Object::ThreadOwnership::kNextReferencing);
      ss->fuse_vertices = Object::CompleteDeferred(vbuf);

      uint16_t* index = &ss->fuse_indices->elements[0];
      VertexSimpleFull* v = &ss->fuse_vertices->elements[0];
      int p_num = 0;
      uint16_t uv_inc = 65535 / (kFusePointCount - 1);

      for (auto&& i : fuses_) {
        BGDynamicsFuseData& fuse(*i);
        if (!fuse.initial_position_set_) continue;

        for (int j = 0; j < kFusePointCount - 1; j++) {
          *index++ = static_cast<uint16_t>(p_num);
          *index++ = static_cast<uint16_t>(p_num + 1);
          *index++ = static_cast<uint16_t>(p_num + 2);

          *index++ = static_cast<uint16_t>(p_num + 2);
          *index++ = static_cast<uint16_t>(p_num + 1);
          *index++ = static_cast<uint16_t>(p_num + 3);
          p_num += 2;
        }
        p_num += 2;

        uint16_t uv = 65535;

        Vector3f from_cam = (cam_pos_ - fuse.dyn_pts_[0]).Normalized() * 0.2f;
        Vector3f side{};

        // We push fuse points slightly towards cam, so they're less likely to
        // get occluded by stuff.
        Vector3f cam_offs = {0.0f, 0.0f, 0.0f};

        for (int j = 0; j < kFusePointCount; j++) {
          if (j == 0) {
            side =
                Vector3f::Cross(from_cam, (fuse.dyn_pts_[1] - fuse.dyn_pts_[0]))
                    .Normalized()
                * 0.03f;
          } else {
            side = Vector3f::Cross(from_cam,
                                   (fuse.dyn_pts_[j] - fuse.dyn_pts_[j - 1]))
                       .Normalized()
                   * 0.03f;
          }

          v->position[0] = fuse.dyn_pts_[j].x + side.x + cam_offs.x;
          v->position[1] = fuse.dyn_pts_[j].y + side.y + cam_offs.y;
          v->position[2] = fuse.dyn_pts_[j].z + side.z + cam_offs.z;
          v->uv[0] = 0;
          v->uv[1] = uv;
          v++;
          v->position[0] = fuse.dyn_pts_[j].x - side.x + cam_offs.x;
          v->position[1] = fuse.dyn_pts_[j].y - side.y + cam_offs.y;
          v->position[2] = fuse.dyn_pts_[j].z - side.z + cam_offs.z;
          v->uv[0] = 65535;
          v->uv[1] = uv;
          v++;
          uv -= uv_inc;
        }
      }
      assert(v == &ss->fuse_vertices->elements[0] + vertex_count);
      assert(index == &ss->fuse_indices->elements[0] + index_count);
    }
  }

  // Now sparks.
  if (!spark_particles_) {
    spark_particles_ = std::make_unique<ParticleSet>();
  }
  spark_particles_->UpdateAndCreateSnapshot(&ss->spark_indices,
                                            &ss->spark_vertices);

  return ss;
}  // NOLINT (yes this should be shorter)

void BGDynamicsServer::PushTooSlowCall() {
  event_loop()->PushCall([this] {
    if (chunk_count_ > 0 || tendril_count_thick_ > 0
        || tendril_count_thin_ > 0) {
      // Ok lets kill a small percentage of our oldest chunks.
      int killcount =
          static_cast<int>(0.1f * static_cast<float>(chunks_.size()));
      int killed = 0;
      auto i = chunks_.begin();
      while (i != chunks_.end()) {
        if (killed >= killcount) break;
        auto i_next = i;
        i_next++;

        // Kill it if its killable; otherwise move to next.
        if ((**i).can_die()) {
          delete (*i);
          chunks_.erase(i);
          chunk_count_--;
          killed++;
        }
        i = i_next;
      }
      // ...and tendrils.
      killcount = static_cast<int>(0.2f * static_cast<float>(tendrils_.size()));
      for (int j = 0; j < killcount; j++) {
        Tendril* t = *tendrils_.begin();
        if (t->type_ == BGDynamicsTendrilType::kThinSmoke) {
          tendril_count_thin_--;
        } else {
          tendril_count_thick_--;
        }
        assert(tendril_count_thin_ >= 0 && tendril_count_thick_ >= 0);
        delete t;
        tendrils_.erase(tendrils_.begin());
      }
    }
  });
}

void BGDynamicsServer::Step(StepData* step_data) {
  assert(g_base->InBGDynamicsThread());
  assert(step_data);

  // Grab a ref to the raw StepData pointer we were passed... we now own the
  // data.
  auto ref(Object::CompleteDeferred(step_data));

  // Keep our quality in sync with the graphics thread's.
  graphics_quality_ = step_data->graphics_quality;
  assert(graphics_quality_ != GraphicsQuality::kUnset);

  cam_pos_ = step_data->cam_pos;

  // Apply all step data sent to us for our entities.
  for (auto&& i : step_data->shadow_step_data_) {
    BGDynamicsShadowData* shadow{i.first};
    if (shadow) {
      const ShadowStepData& shadow_step(i.second);
      shadow->pos_worker = shadow_step.position;
    }
  }
  for (auto&& i : step_data->volume_light_step_data_) {
    BGDynamicsVolumeLightData* volume_light{i.first};
    if (volume_light) {
      const VolumeLightStepData& volume_light_step(i.second);
      volume_light->pos_worker = volume_light_step.pos;
      volume_light->radius_worker = volume_light_step.radius;
      volume_light->r_worker = volume_light_step.r;
      volume_light->g_worker = volume_light_step.g;
      volume_light->b_worker = volume_light_step.b;
    }
  }
  for (auto&& i : step_data->fuse_step_data_) {
    BGDynamicsFuseData* fuse{i.first};
    if (fuse) {
      const FuseStepData& fuse_step(i.second);
      fuse->transform_worker_ = fuse_step.transform;
      fuse->have_transform_worker_ = fuse_step.have_transform;
      fuse->length_worker_ = fuse_step.length;
    }
  }

  // Handle shadows first since they need to get back to the client
  // as soon as possible.
  UpdateShadows();

  // Go ahead and run this step for all our existing stuff.
  dJointGroupEmpty(ode_contact_group_);
  UpdateFields();
  UpdateChunks();
  UpdateTendrils();
  UpdateFuses();

  step_milliseconds_ = static_cast<float>(step_data->step_millisecs);
  step_seconds_ = step_milliseconds_ / 1000.0f;

  // Step the world.
  dWorldQuickStep(ode_world_, step_seconds_);

  // Now generate a snapshot of our state and send it to the logic thread so
  // they can draw us.
  BGDynamicsDrawSnapshot* snapshot = CreateDrawSnapshot();
  g_base->logic->event_loop()->PushCall([snapshot] {
    snapshot->SetLogicThreadOwnership();
    g_base->bg_dynamics->SetDrawSnapshot(snapshot);
  });

  time_ms_ += step_milliseconds_;  // milliseconds per step

  // Give our collision cache a bit of processing time here and
  // there to fill itself in slowly.
  collision_cache_->Precalc();

  // Job's done!
  {
    std::scoped_lock lock(step_count_mutex_);
    step_count_--;
  }
  assert(step_count_ >= 0);

  // Math sanity check.
  if (step_count_ < 0) {
    BA_LOG_ONCE(LogName::kBaGraphics, LogLevel::kWarning,
                "BGDynamics step_count too low (" + std::to_string(step_count_)
                    + "); should not happen.");
  }
}

void BGDynamicsServer::PushStep(StepData* data) {
  // Increase our step count and ship it.
  {
    std::scoped_lock lock(step_count_mutex_);
    step_count_++;
  }

  // Client thread should stop feeding us if we get clogged up.
  if (step_count_ > 5) {
    BA_LOG_ONCE(LogName::kBa, LogLevel::kWarning,
                "BGDynamics step_count too high (" + std::to_string(step_count_)
                    + "); should not happen.");
  }

  event_loop()->PushCall([this, data] { Step(data); });
}

void BGDynamicsServer::PushAddTerrainCall(
    Object::Ref<CollisionMeshAsset>* collision_mesh) {
  event_loop()->PushCall([this, collision_mesh] {
    assert(g_base->InBGDynamicsThread());
    assert(collision_mesh != nullptr);

    // Make sure its loaded (might not be when we get it).
    (**collision_mesh).Load();

    // (the terrain now owns the ref pointer passed in)
    terrains_.push_back(new Terrain(this, collision_mesh));

    // Rebuild geom list from our present terrains.
    std::vector<dGeomID> geoms;
    geoms.reserve(terrains_.size());
    for (auto&& i : terrains_) {
      geoms.push_back(i->geom());
    }
    height_cache_->SetGeoms(geoms);
    collision_cache_->SetGeoms(geoms);

    // Reset our chunks whenever anything changes.
    Clear();
  });
}

void BGDynamicsServer::UpdateFields() {
  auto i = fields_.begin();
  while (i != fields_.end()) {
    Field& f(**i);

    // First off, kill this field if its time has come.
    {
      bool kill = false;
      if (static_cast<float>(time_ms_ - f.birth_time_ms()) > f.lifespan_ms()) {
        kill = true;
      }
      if (kill) {
        auto i_next = i;
        i_next++;
        delete *i;
        fields_.erase(i);
        i = i_next;
        continue;
      }
    }

    // Update its distortion amount based on age (get an age in 0-1).
    float age = (time_ms() - f.birth_time_ms()) / f.lifespan_ms();

    float time_scale = 1.3f;
    float start_mag = 0.0f;
    float suck_mag = -0.4f;
    float suck_end_time = 0.05f * time_scale;
    float bulge_mag = 0.7f;
    float bulge_end_time = 0.2f * time_scale;
    float suck_2_mag = -0.05f;
    float suck_2_end_time = 0.4f * time_scale;
    float end_mag = 0.0f;

    // Ramp negative from 0 to 0.3.
    if (age < suck_end_time) {
      f.set_amt(start_mag
                + (suck_mag - start_mag)
                      * Utils::SmoothStep(0.0f, suck_end_time, age));
    } else if (age < bulge_end_time) {
      f.set_amt(suck_mag
                + (bulge_mag - suck_mag)
                      * Utils::SmoothStep(suck_end_time, bulge_end_time, age));
    } else if (age < suck_2_end_time) {
      f.set_amt(
          bulge_mag
          + (suck_2_mag - bulge_mag)
                * Utils::SmoothStep(bulge_end_time, suck_2_end_time, age));
    } else {
      f.set_amt(suck_2_mag
                + (end_mag - suck_2_mag)
                      * Utils::SmoothStep(suck_2_end_time, 1.0f, age));
    }
    f.set_amt(f.amt() * f.mag());
    i++;
  }
}

void BGDynamicsServer::TerrainCollideCallback(void* data, dGeomID geom1,
                                              dGeomID geom2) {
  auto* dyn = static_cast<BGDynamicsServer*>(data);
  dContact contact[kMaxBGDynamicsContacts];  // max contacts per box-box

  if (int numc = dCollide(geom1, geom2, kMaxBGDynamicsContacts,
                          &contact[0].geom, sizeof(dContact))) {
    BGDynamicsChunkType type = dyn->cb_type_;
    dBodyID body = dyn->cb_body_;
    float f_mult = type == BGDynamicsChunkType::kIce ? 0.04f : 1.0f;

    // Slime chunks just slow down on collisions.
    if (type == BGDynamicsChunkType::kSlime) {
      const dReal* vel = dBodyGetLinearVel(body);
      dBodySetLinearVel(body, vel[0] * 0.1f, vel[1] * 0.1f, vel[2] * 0.1f);
      vel = dBodyGetAngularVel(body);
      dBodySetAngularVel(body, vel[0] * 0.8f, vel[1] * 0.8f, vel[2] * 0.8f);
    } else {
      // Only look at some contacts.
      // If we restrict the number of contacts returned we seem to get
      // lopsided contacts and failing collisions, but if we just increment
      // through all contacts at > 1 it seems to work ok.
      int contact_incr = 1;
      if (numc > 4) {
        contact_incr = 2;
        if (numc > 9) {
          contact_incr = 3;
          if (numc > 14) {
            contact_incr = 4;
          }
        }
      }

      for (int i = 0; i < numc; i += contact_incr) {
        // NOLINTNEXTLINE
        contact[i].surface.mode = dContactBounce | dContactSoftCFM
                                  | dContactSoftERP | dContactApprox1;
        contact[i].surface.mu2 = 0;
        contact[i].surface.bounce_vel = 0.1f;
        contact[i].surface.mu = 0.5f * dyn->debris_friction_ * f_mult;
        contact[i].surface.bounce = 0.4f;
        contact[i].surface.soft_cfm = dyn->cb_cfm_;
        contact[i].surface.soft_erp = dyn->cb_erp_;
        dJointID constraint = dJointCreateContact(
            dyn->ode_world_, dyn->ode_contact_group_, contact + i);
        dJointAttach(constraint, body, nullptr);
      }
    }
  }
}

void BGDynamicsServer::UpdateChunks() {
  dReal stiffness = 1000.0f;
  dReal damping = 10.0f;
  dReal erp{}, cfm{};
  CalcERPCFM(stiffness, damping, &erp, &cfm);
  cb_erp_ = erp;
  cb_cfm_ = cfm;

  // We don't use a space since we don't want everything to intercollide;
  // rather we explicitly test everything against our terrain objects;
  // this keeps things simple.

  for (auto i = chunks_.begin(); i != chunks_.end();) {
    Chunk& c(**i);

    // first off, kill this chunk if its time has come
    {
      bool kill = false;
      if (time_ms_ - c.birth_time_ > c.lifespan_) {
        kill = true;
      }

      // If we've fallen off the level.
      if (c.dynamic()) {
        const dReal* pos = dGeomGetPosition(c.geom_);
        if (pos[1] < debris_kill_height_) kill = true;
      }
      if (kill) {
        auto i_next = i;
        i_next++;
        delete *i;
        chunks_.erase(i);
        chunk_count_--;
        assert(chunk_count_ >= 0);
        i = i_next;
        continue;
      }
    }
    BGDynamicsChunkType type = c.type();

    // Some spark-specific stuff.
    if (type == BGDynamicsChunkType::kSpark) {
      if (RandomFloat() < 0.1f) {
        float fs = c.flicker_scale_;
        c.flicker_ = fs * RandomFloat() + (1.0f - fs) * 0.8f;
      }
    } else if (type == BGDynamicsChunkType::kSweat) {
      // Some sweat-specific stuff.
      if (RandomFloat() < 0.25f) {
        c.flicker_ = RandomFloat();
      }
    }

    // Most stuff only applies to dynamic chunks.
    if (c.dynamic()) {
      dGeomID geom = c.geom();
      dBodyID body = c.body();
      if (type == BGDynamicsChunkType::kSlime) {
        // add some drag on slime chunks
        const dReal* vel = dBodyGetLinearVel(body);
        dBodySetLinearVel(body, vel[0] * 0.99f, vel[1] * 0.99f, vel[2] * 0.99f);
      }
      if (type == BGDynamicsChunkType::kSpark) {
        // Add some drag on spark.
        const dReal* vel = dBodyGetLinearVel(body);

        // Also add a bit of upward to counteract gravity.
        float vel_squared = vel[0] * vel[0] + vel[1] * vel[1] + vel[2] * vel[2];

        // Slow down fast if we're going fast.
        // Otherwise, slow down more gradually.
        if (vel_squared > 14) {
          dBodySetLinearVel(body, vel[0] * 0.94f, 0.13f + vel[1] * 0.94f,
                            vel[2] * 0.94f);
        } else {
          dBodySetLinearVel(body, vel[0] * 0.99f, 0.07f + vel[1] * 0.99f,
                            vel[2] * 0.99f);
        }
      } else if (type == BGDynamicsChunkType::kSweat) {
        // Add some drag on sweat.
        const dReal* vel = dBodyGetLinearVel(body);

        // Also add a bit of upward to counteract gravity.
        float vel_squared = vel[0] * vel[0] + vel[1] * vel[1] + vel[2] * vel[2];

        // Slow down fast if we're going fast.
        // Otherwise, slow down more gradually.
        if (vel_squared > 14) {
          dBodySetLinearVel(body, vel[0] * 0.93f, 0.13f + vel[1] * 0.93f,
                            vel[2] * 0.93f);
        } else {
          dBodySetLinearVel(body, vel[0] * 0.97f, 0.11f + vel[1] * 0.97f,
                            vel[2] * 0.97f);
        }
      } else if (type == BGDynamicsChunkType::kSplinter) {
        // Add some drag on slime chunks.
        const dReal* vel = dBodyGetLinearVel(body);
        dBodySetLinearVel(body, vel[0] * 0.995f, vel[1] * 0.995f,
                          vel[2] * 0.995f);
        vel = dBodyGetAngularVel(body);
        dBodySetAngularVel(body, vel[0] * 0.995f, vel[1] * 0.995f,
                           vel[2] * 0.995f);
      } else {
        const dReal* vel = dBodyGetAngularVel(body);
        if (vel[0] * vel[0] + vel[1] * vel[1] + vel[2] * vel[2] > 500) {
          // Drastic slowdown for super-fast stuff.
          dBodySetAngularVel(body, vel[0] * 0.75f, vel[1] * 0.75f,
                             vel[2] * 0.75f);
        } else {
          dBodySetAngularVel(body, vel[0] * 0.995f, vel[1] * 0.995f,
                             vel[2] * 0.995f);
        }
      }

      // If this chunk is disabled, we don't need to do anything
      // (since no terrain ever moves to wake us back up).
      // Also, we skip sweat since that neither casts shadows nor collides.
      if (dBodyIsEnabled(body) && type != BGDynamicsChunkType::kSweat) {
        // Move our shadow ray to where we are and reset our shadow length.
        const dReal* pos = dGeomGetPosition(geom);
        // Update shadow dist.
        c.shadow_dist_ = pos[1] - height_cache_->Sample(Vector3f(pos));
        cb_type_ = type;
        cb_body_ = body;
        collision_cache_->CollideAgainstGeom(geom, this,
                                             TerrainCollideCallback);
        // Tell it to update any tendril it might have.
        c.UpdateTendril();
      }
    }
    i++;
  }
}

void BGDynamicsServer::UpdateShadows() {
  // First go through and calculate distances for all shadows.
  for (auto&& s : shadows_) {
    float shadow_dist = s->pos_worker.y - height_cache_->Sample(s->pos_worker);

    // Update scale/density based on these values.
    // Negative shadow_dist means some object is in front of our
    // shadow-caster. In this case lets keep our scale the same as it would
    // have been at zero dist but fade our density out gradually as we become
    // more deeply submerged.
    if (shadow_dist < 0.0f) {
      s->shadow_scale_worker = 1.0f;
      s->shadow_density_worker =
          1.0f - std::min(1.0f, -shadow_dist / kShadowOccludeDistance);
    } else {
      // Normal non-submerged shadow.
      float max_scale = 1.0f + (kMaxShadowScale - 1.0f) * s->height_scaling;
      float scale =
          1.0f
          + std::max(0.0f, std::min(1.0f, (shadow_dist / kMaxShadowGrowDist))
                               * (max_scale - 1.0f));
      s->shadow_scale_worker = scale;
      s->shadow_density_worker =
          1.0f
          - 0.7f
                * std::max(0.0f,
                           std::min(1.0f, (shadow_dist / kMaxShadowGrowDist)));
    }
  }

  // Now plop this back onto the client side all at once.
  {
    BA_DEBUG_TIME_CHECK_BEGIN(bg_dynamic_shadow_list_lock);
    {
      std::scoped_lock lock(shadow_list_mutex_);
      for (auto&& s : shadows_) {
        s->UpdateClientData();
      }
    }
    BA_DEBUG_TIME_CHECK_END(bg_dynamic_shadow_list_lock, 10);
  }
}

}  // namespace ballistica::base
