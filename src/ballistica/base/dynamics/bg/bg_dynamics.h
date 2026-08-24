// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_

#include <memory>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

enum class BGDynamicsEmitType {
  kChunks,
  kStickers,
  kTendrils,
  kDistortion,
  kFlagStand,
  kFairyDust
};

enum class BGDynamicsTendrilType { kSmoke, kThinSmoke, kIce };

enum class BGDynamicsChunkType {
  kRock,
  kIce,
  kSlime,
  kMetal,
  kSpark,
  kSplinter,
  kSweat,
  kFlagStand
};

class BGDynamicsEmission {
 public:
  BGDynamicsEmitType emit_type = BGDynamicsEmitType::kChunks;
  Vector3f position{0.0f, 0.0f, 0.0f};
  Vector3f velocity{0.0f, 0.0f, 0.0f};
  int count{0};
  float scale{1.0f};
  float spread{1.0f};
  BGDynamicsChunkType chunk_type{BGDynamicsChunkType::kRock};
  BGDynamicsTendrilType tendril_type{BGDynamicsTendrilType::kSmoke};
};

// client (logic thread) functionality for bg dynamics
class BGDynamics {
 public:
  BGDynamics();

  void Emit(const BGDynamicsEmission& def);
  void Step(const Vector3f& cam_pos, int step_millisecs);

  // can be called to inform the bg dynamics thread to kill off some
  // smoke/chunks/etc. if rendering is chugging or whatnot.
  void TooSlow();

  // Draws the last snapshot the bg-dynamics-server has delivered to us
  void Draw(FrameDef* frame_def);
  void SetDebrisFriction(float val);
  void SetDebrisKillHeight(float val);
  /// Add a terrain to the bg-dynamics world. The transform is baked in at
  /// add time; to move an existing terrain, remove and re-add it.
  void AddTerrain(CollisionMeshAsset* o, const Matrix44f& transform);
  void RemoveTerrain(CollisionMeshAsset* o);

  // (sent to us by the bg dynamics server)
  void SetDrawSnapshot(BGDynamicsDrawSnapshot* s);

 private:
  void DrawChunks(FrameDef* frame_def, std::vector<Matrix44f>* instances,
                  BGDynamicsChunkType chunk_type);

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
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_
