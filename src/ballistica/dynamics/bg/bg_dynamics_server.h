// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_
#define BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_

#include <list>
#include <memory>
#include <utility>
#include <vector>

#include "ballistica/core/module.h"
#include "ballistica/dynamics/bg/bg_dynamics.h"
#include "ballistica/math/matrix44f.h"
#include "ballistica/math/vector3f.h"
#include "ode/ode.h"

namespace ballistica {

class BGDynamicsServer : public Module {
 public:
  struct Particle {
    float x;
    float y;
    float z;
    // Note that velocities here are in units-per-step (avoids a mult).
    float vx;
    float vy;
    float vz;
    float r;
    float g;
    float b;
    float a;
    float life;
    float d_life;
    float flicker;
    float flicker_scale;
    float size;
    float d_size;
  };

  class ParticleSet {
   public:
    std::vector<Particle> particles[2];
    int current_set;
    ParticleSet() : current_set(0) {}
    void Emit(const Vector3f& pos, const Vector3f& vel, float r, float g,
              float b, float a, float dlife, float size, float d_size,
              float flicker);
    void UpdateAndCreateSnapshot(Object::Ref<MeshIndexBuffer16>* index_buffer,
                                 Object::Ref<MeshBufferVertexSprite>* buffer);
  };
  struct ShadowStepData {
    Vector3f position;
  };
  struct VolumeLightStepData {
    Vector3f pos{};
    float radius{};
    float r{};
    float g{};
    float b{};
  };
  struct FuseStepData {
    Matrix44f transform{};
    bool have_transform{};
    float length{};
  };
  class StepData : public Object {
   public:
    auto GetDefaultOwnerThread() const -> ThreadIdentifier override {
      return ThreadIdentifier::kBGDynamics;
    }
    Vector3f cam_pos{0.0f, 0.0f, 0.0f};

    // Basically a bit list of pointers to the current set of
    // shadows/volumes/fuses and client values for them.
    std::vector<std::pair<BGDynamicsShadowData*, ShadowStepData> >
        shadow_step_data_;
    std::vector<std::pair<BGDynamicsVolumeLightData*, VolumeLightStepData> >
        volume_light_step_data_;
    std::vector<std::pair<BGDynamicsFuseData*, FuseStepData> > fuse_step_data_;
  };

  explicit BGDynamicsServer(Thread* thread);
  ~BGDynamicsServer() override;
  auto time() const -> uint32_t { return time_; }
  auto graphics_quality() const -> GraphicsQuality { return graphics_quality_; }

  void PushAddVolumeLightCall(BGDynamicsVolumeLightData* volume_light_data);
  void PushRemoveVolumeLightCall(BGDynamicsVolumeLightData* volume_light_data);
  void PushAddFuseCall(BGDynamicsFuseData* fuse_data);
  void PushRemoveFuseCall(BGDynamicsFuseData* fuse_data);
  void PushAddShadowCall(BGDynamicsShadowData* shadow_data);
  void PushRemoveShadowCall(BGDynamicsShadowData* shadow_data);
  void PushAddTerrainCall(Object::Ref<CollideModelData>* collide_model);
  void PushRemoveTerrainCall(CollideModelData* collide_model);
  void PushEmitCall(const BGDynamicsEmission& def);
  auto spark_particles() const -> ParticleSet* {
    return spark_particles_.get();
  }
  auto step_count() const -> int { return step_count_; }

 private:
  class Terrain;
  class Chunk;
  class Field;
  class Tendril;
  class TendrilController;

  static void TerrainCollideCallback(void* data, dGeomID o1, dGeomID o2);

  void Emit(const BGDynamicsEmission& def);
  void PushStepCall(StepData* data);
  void Step(StepData* data);
  void PushTooSlowCall();
  void PushSetDebrisFrictionCall(float friction);
  void PushSetDebrisKillHeightCall(float height);
  void Clear();
  void UpdateFields();
  void UpdateChunks();
  void UpdateTendrils();
  void UpdateFuses();
  void UpdateShadows();
  auto CreateDrawSnapshot() -> BGDynamicsDrawSnapshot*;
  BGDynamicsChunkType cb_type_ = BGDynamicsChunkType::kRock;
  dBodyID cb_body_{};
  float cb_cfm_{0.0f};
  float cb_erp_{0.0f};

  // FIXME: We're assuming at the moment
  //  that collide-models passed to this thread never get deallocated. ew.
  MeshIndexedSmokeFull* tendrils_smoke_mesh_{nullptr};
  MeshIndexedSimpleFull* fuses_mesh_{nullptr};
  SpriteMesh* shadows_mesh_{nullptr};
  SpriteMesh* lights_mesh_{nullptr};
  SpriteMesh* sparks_mesh_{nullptr};
  int miss_count_{0};
  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  std::vector<Terrain*> terrains_;
  std::vector<BGDynamicsShadowData*> shadows_;
  std::vector<BGDynamicsVolumeLightData*> volume_lights_;
  std::vector<BGDynamicsFuseData*> fuses_;
  dWorldID ode_world_{nullptr};
  dJointGroupID ode_contact_group_{nullptr};

  // Held by the dynamics module when changing any of these lists.
  // Should be grabbed by a client if they need to access the list safely.
  std::mutex shadow_list_mutex_;
  std::mutex volume_light_list_mutex_;
  std::mutex fuse_list_mutex_;
  int step_count_{0};
  std::mutex step_count_mutex_;
  std::unique_ptr<ParticleSet> spark_particles_{nullptr};
  std::list<Chunk*> chunks_;
  std::list<Field*> fields_;
  std::list<Tendril*> tendrils_;
  int tendril_count_thick_{0};
  int tendril_count_thin_{0};
  int chunk_count_{0};
  std::unique_ptr<BGDynamicsHeightCache> height_cache_;
  std::unique_ptr<CollisionCache> collision_cache_;
  uint32_t time_{0};  // Internal time step.
  float debris_friction_{1.0f};
  float debris_kill_height_{-50.0f};
  GraphicsQuality graphics_quality_{GraphicsQuality::kLow};
  friend class BGDynamics;
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_
