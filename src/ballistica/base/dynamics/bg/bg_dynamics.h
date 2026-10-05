// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_

#include <memory>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/dynamics/bg/bg_dynamics_kinds.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// Debug-draw tint for anything the bg-dynamics thread simulates
/// (character limbs and attachments, debris chunks): pulls a body's
/// role color firmly toward blue so bg and main-sim bodies tell apart
/// at a glance while the role still shows through a little.
inline void BGDynamicsDebugTint(float* r, float* g, float* b) {
  *r = 0.2f + 0.35f * (*r);
  *g = 0.35f + 0.35f * (*g);
  *b = 1.0f;
}

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

// How long a frame will wait for a bg-dynamics step still in flight
// before drawing with the previous results
// (BGDynamicsWorld::AdoptResults). A step normally takes well under
// this; hitting it means the bg thread is behind, which the feed-drop
// load shedding handles.
const int kBGDynamicsDrawWaitMicros = 3000;

/// The logic thread's way in to bg-dynamics: cosmetic physics (debris,
/// smoke, sparks, character limbs and attachments, shadow heights)
/// simulated on a thread of its own.
///
/// What gets simulated is held in worlds (BGDynamicsWorld), which
/// share nothing with one another. We own the main one, which
/// everything in the main game world lives in; things drawn through a
/// view of their own (ui viewers) make themselves one to match.
class BGDynamics {
 public:
  BGDynamics();

  /// The world the main game world's bg-dynamics happens in. Logic
  /// thread only.
  auto main_world() -> BGDynamicsWorld*;

 private:
  Object::Ref<BGDynamicsWorld> main_world_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_H_
