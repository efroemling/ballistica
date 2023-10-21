// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_COLLISION_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_COLLISION_H_

#include <vector>

#include "ballistica/scene_v1/dynamics/material/material_context.h"
#include "ballistica/shared/ballistica.h"
#include "ballistica/shared/foundation/object.h"
#include "ode/ode.h"

namespace ballistica::scene_v1 {

/// Stores info about an occurring collision.
///
/// Note than just because a collision exists between two parts doesn't mean
/// they're physically colliding in the simulation. It is just a shortcut to
/// determine what behavior, if any, exists between two parts which are
/// currently overlapping in the simulation.
class Collision : public Object {
 public:
  explicit Collision(Scene* scene) : src_context(scene), dst_context(scene) {}
  int claim_count{};  // Used when checking for out-of-date-ness.
  bool collide{true};
  int contact_count{};  // Current number of contacts.
  float depth{};        // Current collision depth.
  float x{};
  float y{};
  float z{};
  float impact{};
  float skid{};
  float roll{};
  Object::WeakRef<Part> src_part;  // Ref to make sure still alive.
  Object::WeakRef<Part> dst_part;  // Ref to make sure still alive.
  int body_id_1{-1};
  int body_id_2{-1};
  std::vector<dJointFeedback> collide_feedback;
  MaterialContext src_context;
  MaterialContext dst_context;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_COLLISION_H_
