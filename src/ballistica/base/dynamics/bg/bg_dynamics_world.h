// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_WORLD_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_WORLD_H_

#include <memory>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/dynamics/bg/bg_dynamics.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_kinds.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// One world of bg-dynamics, as the logic thread sees it: the terrain
/// in it, what has been emitted into it, the entities fed to it
/// through channels (shadows, fuses, character rigs, ...), and the
/// latest results handed back for drawing.
///
/// A world goes with a world view: what is in it gets drawn through
/// that view and takes its shadow range from it. The main game world
/// has one (BGDynamics::main_world()); anything drawn through a view of
/// its own makes another, so its debris, smoke, and shadows stay its
/// own. Worlds share nothing but the thread they are simulated on.
///
/// Whoever runs a world's scene steps it (Step()) and draws it
/// (AdoptResults() then Draw()). A world nobody steps just sits.
///
/// Logic thread only. Design: docs/initiatives/render-views.md.
class BGDynamicsWorld : public Object {
 public:
  /// Create a world whose contents get drawn through a given view.
  explicit BGDynamicsWorld(RenderView* view);
  ~BGDynamicsWorld() override;

  /// The view we are drawn through.
  auto view() const -> RenderView* {
    assert(view_.exists());
    return view_.get();
  }

  void Emit(const BGDynamicsEmission& def);
  void Step(const Vector3f& cam_pos, int step_millisecs);

  // can be called to inform the bg dynamics thread to kill off some
  // smoke/chunks/etc. if rendering is chugging or whatnot.
  void TooSlow();

  /// Emergency load-shedding for character rigs, 0-1. Owners add this
  /// to their own base skip when feeding a rig (see
  /// BGDynamicsCharacterKind::Input::skip). Bumped by 0.25 (with a
  /// warning) whenever more than half of a second's feeds had to be
  /// dropped because the bg thread was still busy, at most once a
  /// second; recovers at 0.1/s once fewer than a tenth are dropped.
  ///
  /// Kept per world, from the world's own feeds. The thread behind
  /// them is shared, so when it can't keep up every world being
  /// stepped sees its feeds dropped and sheds load.
  auto load_skip() const -> float { return load_skip_; }

  // Draws the last snapshot the bg-dynamics-server has delivered to us
  void Draw(FrameDef* frame_def);
  void SetDebrisFriction(float val);
  void SetDebrisKillHeight(float val);
  /// Add a terrain to the bg-dynamics world. The transform is baked in at
  /// add time; to move an existing terrain, remove and re-add it.
  void AddTerrain(CollisionMeshAsset* o, const Matrix44f& transform);
  void RemoveTerrain(CollisionMeshAsset* o);

  /// Pull the bg thread's latest finished results (draw snapshot and
  /// channel outputs) into place. Called at each logic step's start
  /// (no waiting) and right before the world draws (waiting briefly
  /// for a step still in flight, so the frame draws the bg results for
  /// the sim step it is drawing whenever the machine keeps up; an
  /// overloaded bg thread just leaves the frame with the last results,
  /// as before).
  void AdoptResults(bool wait_for_pending);

  /// The logic-side channel for an entity kind (see
  /// bg_dynamics_channel.h). Logic thread only.
  template <typename Kind>
  auto channel() -> BGDynamicsChannel<Kind>& {
    assert(g_base->InLogicThread());
    return std::get<BGDynamicsChannel<Kind>>(channels_);
  }

  /// Adopt a step's channel outputs (we take ownership).
  void SetOutputBundle(BGDynamicsOutputBundle* bundle);

 private:
  void SetDrawSnapshot(BGDynamicsDrawSnapshot* s);
  // Draw-time wait accounting (BA_DYNAMICS_PROFILE).
  double wait_profile_micros_{};
  int wait_profile_frames_{};
  int wait_profile_timeouts_{};
  void DrawChunks(FrameDef* frame_def, std::vector<Matrix44f>* instances,
                  BGDynamicsChunkType chunk_type);
  void UpdateLoadSkip_(bool feed_dropped, int step_millisecs);

  Object::Ref<RenderView> view_;
  // Our other half. Ours to have made and unmade, on its thread.
  BGDynamicsWorldServer* server_{};

  float load_skip_{};
  int feed_window_millisecs_{};
  int feed_window_total_{};
  int feed_window_dropped_{};
  int millisecs_since_bump_{1000000};
  int millisecs_since_bump_log_{1000000};
  int unlogged_bumps_{};

  /// Return a cached grow-only index buffer holding the canonical
  /// quad pattern (0,1,2, 1,3,2, 4,5,6, ...) covering at least
  /// quad_count quads for one quad sprite mesh (sparks/lights/
  /// shadows each get their own slot). Meshes set per-frame prefix
  /// draw-counts instead of uploading fresh indices every frame; the
  /// buffer itself changes (and re-uploads) only on growth. One cache
  /// per consuming mesh — NOT shared — because MeshBufferBase::state
  /// dirty-tracking assumes a single owning mesh; sharing one buffer
  /// object across meshes lets their state stamps collide and skip
  /// uploads of grown buffers (which draws garbage indices).
  auto QuadIndices_(int slot, size_t quad_count)
      -> const Object::Ref<MeshIndexBuffer16>&;

  static constexpr int kQuadIndexSlotLights{0};
  static constexpr int kQuadIndexSlotShadows{1};
  static constexpr int kQuadIndexSlotSparks{2};
  Object::Ref<MeshIndexBuffer16> quad_indices_[3];
  Object::Ref<SpriteMesh> lights_mesh_;
  Object::Ref<SpriteMesh> shadows_mesh_;
  Object::Ref<SpriteMesh> sparks_mesh_;
  Object::Ref<MeshIndexedSmokeFull> tendrils_mesh_;
  Object::Ref<MeshIndexedSimpleFull> fuses_mesh_;
  std::unique_ptr<BGDynamicsDrawSnapshot> draw_snapshot_;
  BGDynamicsChannelTuple channels_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_WORLD_H_
