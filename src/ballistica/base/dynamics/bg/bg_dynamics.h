// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_

#include <memory>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
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
  void AddTerrain(CollisionMeshAsset* o);
  void RemoveTerrain(CollisionMeshAsset* o);

  // (sent to us by the bg dynamics server)
  void SetDrawSnapshot(BGDynamicsDrawSnapshot* s);

 private:
  void DrawChunks(FrameDef* frame_def, std::vector<Matrix44f>* instances,
                  BGDynamicsChunkType chunk_type);
  Object::Ref<SpriteMesh> lights_mesh_;
  Object::Ref<SpriteMesh> shadows_mesh_;
  Object::Ref<SpriteMesh> sparks_mesh_;
  Object::Ref<MeshIndexedSmokeFull> tendrils_mesh_;
  Object::Ref<MeshIndexedSimpleFull> fuses_mesh_;
  std::unique_ptr<BGDynamicsDrawSnapshot> draw_snapshot_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_
