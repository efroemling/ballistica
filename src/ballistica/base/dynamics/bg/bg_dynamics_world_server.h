// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_WORLD_SERVER_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_WORLD_SERVER_H_

#include <atomic>
#include <condition_variable>
#include <list>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_server.h"
#include "ballistica/base/graphics/support/shadow_range.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"
#include "ode/ode.h"

namespace ballistica::base {

/// The bg-dynamics thread's side of one bg world: the far half of a
/// logic-thread BGDynamicsWorld.
///
/// Everything simulated in the world lives here: its ODE world, the
/// terrain it collides with, debris chunks, smoke, sparks, and the
/// worker halves of the entity channels (shadows, fuses, character
/// rigs, ...). Worlds share nothing with each other but the thread
/// they run on (BGDynamicsServer), so what happens in one can't show
/// up in another.
///
/// The logic thread makes one of us and later asks for it to be
/// unmade (Create() / PushDestroy()); in between it feeds us steps and
/// other requests through Push calls, which run here in the order they
/// were pushed, and picks up our results from a mailbox.
class BGDynamicsWorldServer {
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
    void UpdateAndCreateSnapshot(Object::Ref<MeshBufferVertexSprite>* buffer);
  };

  class StepData : public Object {
   public:
    auto GetDefaultOwnerThread() const -> EventLoopID override {
      return EventLoopID::kBGDynamics;
    }
    GraphicsQuality graphics_quality{};
    int step_millisecs{};
    Vector3f cam_pos{0.0f, 0.0f, 0.0f};
    /// Debug-draw mode: chunk draw matrices then carry only the physics
    /// transform (no shrink/sink/flicker display effects).
    bool debug_draw{};
    /// The heights shadows show between in the view the world is
    /// drawn through.
    ShadowRange shadow_range;

    // Per-kind channel payloads (inputs + create/destroy deltas).
    BGDynamicsChannelStepDataTuple channels;
  };

  /// Logic thread: make a world. It sets itself up on the bg-dynamics
  /// thread ahead of anything pushed to it afterward.
  static auto Create() -> BGDynamicsWorldServer*;

  /// Logic thread: have the world unmade, on the bg-dynamics thread,
  /// once everything pushed to it so far has run. The caller must not
  /// touch it again.
  void PushDestroy();

  auto time_ms() const { return time_ms_; }
  auto shadow_range() const -> const ShadowRange& { return shadow_range_; }
  auto graphics_quality() const -> GraphicsQuality { return graphics_quality_; }

  void PushAddTerrainCall(Object::Ref<CollisionMeshAsset>* collision_mesh,
                          const Matrix44f& transform);
  void PushRemoveTerrainCall(CollisionMeshAsset* collision_mesh);
  void PushEmitCall(const BGDynamicsEmission& def);
  auto spark_particles() const -> ParticleSet* {
    return spark_particles_.get();
  }
  /// Steps fed but not yet processed (any thread).
  auto step_count() const -> int { return step_count_.load(); }
  auto event_loop() const -> EventLoop* {
    return g_base->bg_dynamics_server->event_loop();
  }
  auto height_cache() const -> BGDynamicsHeightCache* {
    return height_cache_.get();
  }
  auto ode_world() const -> dWorldID { return ode_world_; }
  auto ode_contact_group() const -> dJointGroupID { return ode_contact_group_; }
  auto terrain_collider() const -> TerrainCollider* {
    return terrain_collider_.get();
  }

  const auto& terrains() const { return terrains_; }
  void PushStep(StepData* data);
  void PushTooSlowCall();
  void PushSetDebrisFrictionCall(float friction);
  void PushSetDebrisKillHeightCall(float height);

  auto step_seconds() const { return step_seconds_; }
  auto step_milliseconds() const { return step_milliseconds_; }

  /// The quickstep iteration hint character rigs put on their bodies
  /// (see BGDynamicsServer::character_solver_iterations).
  auto character_solver_iterations() const -> int {
    return g_base->bg_dynamics_server->character_solver_iterations();
  }

  /// Logic thread: block until no step pushed to us is still waiting
  /// or being simulated, or the timeout passes. Returns whether we are
  /// idle.
  auto WaitForIdle(int timeout_micros) -> bool;

  /// Logic thread: take the latest finished step's results (the draw
  /// snapshot and channel outputs), if any arrived since the last
  /// take. Only the newest is kept; a step nobody looked at is gone.
  void TakeResults(BGDynamicsDrawSnapshot** snapshot,
                   BGDynamicsOutputBundle** bundle);

  /// Logic thread: hand a bundle from TakeResults back once its
  /// outputs have been swapped out (BGDynamicsChannel::Adopt), so the
  /// next step fills its buffers instead of allocating. Three bundles
  /// cycle in steady state: one being built, one in the mailbox, one
  /// adopted.
  void RecycleBundle(BGDynamicsOutputBundle* bundle);

  /// Logic thread: hand back a draw snapshot it is done with (already
  /// Reset on that thread, which releases its mesh buffers) so the
  /// next step reuses its vectors.
  void RecycleSnapshot(BGDynamicsDrawSnapshot* snapshot);

 private:
  class Terrain;
  class Chunk;
  class Field;
  class Tendril;
  class TendrilController;

  BGDynamicsWorldServer();
  ~BGDynamicsWorldServer();
  void Init_();

  static void TerrainCollideCallback(void* data, dGeomID o1, dGeomID o2);

  void Emit(const BGDynamicsEmission& def);
  void Step(StepData* data);
  void Clear();
  void UpdateFields();
  void UpdateChunks();
  void UpdateTendrils();
  auto CreateDrawSnapshot() -> BGDynamicsDrawSnapshot*;
  /// A kind's worker-side channel state (bg-dynamics thread only).
  template <typename Kind>
  auto channel_worker() const -> const BGDynamicsChannelWorker<Kind>& {
    return std::get<BGDynamicsChannelWorker<Kind>>(channel_workers_);
  }
  void CalcERPCFM(dReal stiffness, dReal damping, dReal* erp, dReal* cfm);

  // Which world we are, for telling worlds apart in logs.
  int id_{};
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
  BGDynamicsChannelWorkerTuple channel_workers_;
  dWorldID ode_world_{};
  dJointGroupID ode_contact_group_{};

  std::atomic<int> step_count_{};
  // Results mailbox (see TakeResults) and the idle signal (WaitForIdle).
  std::mutex results_mutex_;
  std::condition_variable results_cv_;
  BGDynamicsDrawSnapshot* mailbox_snapshot_{};
  BGDynamicsOutputBundle* mailbox_bundle_{};
  // Bundles handed back for reuse (under results_mutex_).
  std::vector<BGDynamicsOutputBundle*> recycled_bundles_;
  void RecycleBundleLocked_(BGDynamicsOutputBundle* bundle);
  auto TakeRecycledBundle_() -> BGDynamicsOutputBundle*;
  std::vector<BGDynamicsDrawSnapshot*> recycled_snapshots_;
  void RecycleSnapshotLocked_(BGDynamicsDrawSnapshot* snapshot);
  auto TakeRecycledSnapshot_() -> BGDynamicsDrawSnapshot*;
  // BA_DYNAMICS_PROFILE=1: per-phase step timing, logged every 300 steps.
  double profile_channels_ms_{};
  double profile_chunks_ms_{};
  double profile_tendrils_ms_{};
  double profile_worldstep_ms_{};
  double profile_snapshot_ms_{};
  double profile_publish_ms_{};
  int profile_steps_{};
  int profile_bodies_max_{};
  int profile_joints_max_{};
  std::unique_ptr<ParticleSet> spark_particles_{};
  std::list<Chunk*> chunks_;
  std::list<Field*> fields_;
  std::list<Tendril*> tendrils_;
  int tendril_count_thick_{};
  int tendril_count_thin_{};
  int chunk_count_{};
  std::unique_ptr<BGDynamicsHeightCache> height_cache_;
  std::unique_ptr<TerrainCollider> terrain_collider_;
  float time_ms_{};  // Internal time step.
  float debris_friction_{1.0f};
  float debris_kill_height_{-50.0f};
  float step_seconds_{};
  float step_milliseconds_{};
  GraphicsQuality graphics_quality_{GraphicsQuality::kLow};
  bool debug_draw_{};
  ShadowRange shadow_range_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_WORLD_SERVER_H_
