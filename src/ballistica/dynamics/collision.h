// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_COLLISION_H_
#define BALLISTICA_DYNAMICS_COLLISION_H_

#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/core/object.h"
#include "ballistica/dynamics/material/material_context.h"
#include "ode/ode.h"

namespace ballistica {

// Stores info about an occurring collision.
// Note than just because a collision exists between two parts doesn't mean
// they're physically colliding in the simulation. It is just a shortcut to
// determine what behavior, if any, exists between two parts which are currently
// overlapping in the simulation.
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

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_COLLISION_H_
