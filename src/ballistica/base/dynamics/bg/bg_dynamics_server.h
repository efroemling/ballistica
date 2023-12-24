// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_

#include <list>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"
#include "ode/ode.h"

namespace ballistica::base {

class BGDynamicsServer {
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
    auto GetDefaultOwnerThread() const -> EventLoopID override {
      return EventLoopID::kBGDynamics;
    }
    GraphicsQuality graphics_quality{};
    int step_millisecs{};
    Vector3f cam_pos{0.0f, 0.0f, 0.0f};

    // Basically a bit list of pointers to the current set of
    // shadows/volumes/fuses and client values for them.
    std::vector<std::pair<BGDynamicsShadowData*, ShadowStepData> >
        shadow_step_data_;
    std::vector<std::pair<BGDynamicsVolumeLightData*, VolumeLightStepData> >
        volume_light_step_data_;
    std::vector<std::pair<BGDynamicsFuseData*, FuseStepData> > fuse_step_data_;
  };

  BGDynamicsServer();
  void OnMainThreadStartApp();

  auto time_ms() const { return time_ms_; }
  auto graphics_quality() const -> GraphicsQuality { return graphics_quality_; }

  void PushAddVolumeLightCall(BGDynamicsVolumeLightData* volume_light_data);
  void PushRemoveVolumeLightCall(BGDynamicsVolumeLightData* volume_light_data);
  void PushAddFuseCall(BGDynamicsFuseData* fuse_data);
  void PushRemoveFuseCall(BGDynamicsFuseData* fuse_data);
  void PushAddShadowCall(BGDynamicsShadowData* shadow_data);
  void PushRemoveShadowCall(BGDynamicsShadowData* shadow_data);
  void PushAddTerrainCall(Object::Ref<CollisionMeshAsset>* collision_mesh);
  void PushRemoveTerrainCall(CollisionMeshAsset* collision_mesh);
  void PushEmitCall(const BGDynamicsEmission& def);
  auto spark_particles() const -> ParticleSet* {
    return spark_particles_.get();
  }
  auto step_count() const -> int { return step_count_; }
  auto event_loop() const -> EventLoop* { return event_loop_; }

  auto& shadow_list_mutex() { return shadow_list_mutex_; }
  auto& volume_light_list_mutex() { return volume_light_list_mutex_; }
  auto& fuse_list_mutex() { return fuse_list_mutex_; }
  auto& step_count_mutex() { return step_count_mutex_; }

  const auto& terrains() const { return terrains_; }
  const auto& shadows() const { return shadows_; }
  const auto& volume_lights() const { return volume_lights_; }
  const auto& fuses() const { return fuses_; }
  void PushStep(StepData* data);
  void PushTooSlowCall();
  void PushSetDebrisFrictionCall(float friction);
  void PushSetDebrisKillHeightCall(float height);

  auto step_seconds() const { return step_seconds_; }
  auto step_milliseconds() const { return step_milliseconds_; }

 private:
  class Terrain;
  class Chunk;
  class Field;
  class Tendril;
  class TendrilController;

  static void TerrainCollideCallback(void* data, dGeomID o1, dGeomID o2);

  void Emit(const BGDynamicsEmission& def);
  void Step(StepData* data);
  void Clear();
  void UpdateFields();
  void UpdateChunks();
  void UpdateTendrils();
  void UpdateFuses();
  void UpdateShadows();
  auto CreateDrawSnapshot() -> BGDynamicsDrawSnapshot*;
  void CalcERPCFM(dReal stiffness, dReal damping, dReal* erp, dReal* cfm);

  EventLoop* event_loop_{};
  BGDynamicsChunkType cb_type_ = BGDynamicsChunkType::kRock;
  dBodyID cb_body_{};
  float cb_cfm_{};
  float cb_erp_{};

  // FIXME: We're assuming at the moment
  //  that collision-meshes passed to this thread never get deallocated. ew.
  MeshIndexedSmokeFull* tendrils_smoke_mesh_{};
  MeshIndexedSimpleFull* fuses_mesh_{};
  SpriteMesh* shadows_mesh_{};
  SpriteMesh* lights_mesh_{};
  SpriteMesh* sparks_mesh_{};
  int miss_count_{};
  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  std::vector<Terrain*> terrains_;
  std::vector<BGDynamicsShadowData*> shadows_;
  std::vector<BGDynamicsVolumeLightData*> volume_lights_;
  std::vector<BGDynamicsFuseData*> fuses_;
  dWorldID ode_world_{};
  dJointGroupID ode_contact_group_{};

  // Held by the dynamics module when changing any of these lists.
  // Should be grabbed by a client if they need to access the list safely.
  std::mutex shadow_list_mutex_;
  std::mutex volume_light_list_mutex_;
  std::mutex fuse_list_mutex_;
  int step_count_{};
  std::mutex step_count_mutex_;
  std::unique_ptr<ParticleSet> spark_particles_{};
  std::list<Chunk*> chunks_;
  std::list<Field*> fields_;
  std::list<Tendril*> tendrils_;
  int tendril_count_thick_{};
  int tendril_count_thin_{};
  int chunk_count_{};
  std::unique_ptr<BGDynamicsHeightCache> height_cache_;
  std::unique_ptr<CollisionCache> collision_cache_;
  float time_ms_{};  // Internal time step.
  float debris_friction_{1.0f};
  float debris_kill_height_{-50.0f};
  float step_seconds_{};
  float step_milliseconds_{};
  GraphicsQuality graphics_quality_{GraphicsQuality::kLow};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_SERVER_H_
