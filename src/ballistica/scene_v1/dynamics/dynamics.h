// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_DYNAMICS_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_DYNAMICS_H_

#include <memory>
#include <unordered_map>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ode/ode.h"

namespace ballistica::scene_v1 {

class Dynamics : public Object {
 public:
  explicit Dynamics(Scene* scene_in);
  ~Dynamics() override;
  void Draw(base::FrameDef* frame_def);  // Draw any debug stuff, etc.
  auto ode_world() -> dWorldID { return ode_world_; }
  auto getContactGroup() -> dJointGroupID { return ode_contact_group_; }
  auto space() -> dSpaceID { return ode_space_; }

  // Discontinues a collision. Used by parts when changing materials
  // so that new collisions may enter effect.
  void ResetCollision(int64_t node1, int part1, int64_t node2, int part2);

  // Used by collision callbacks - internal.
  auto active_collision() const -> Collision* { return active_collision_; }

  // Used by collision callbacks - internal.
  auto GetActiveCollideSrcNode() -> Node* {
    assert(active_collision_);
    return (collide_message_reverse_order_ ? active_collide_dst_node_
                                           : active_collide_src_node_)
        .Get();
  }
  // Used by collision callbacks - internal.
  auto GetActiveCollideDstNode() -> Node* {
    assert(active_collision_);
    return (collide_message_reverse_order_ ? active_collide_src_node_
                                           : active_collide_dst_node_)
        .Get();
  }
  auto GetCollideMessageReverseOrder() const -> bool {
    return collide_message_reverse_order_;
  }

  // Used by collide message handlers.
  void set_collide_message_state(bool inCollideMessageIn,
                                 bool target_other_in = false) {
    in_collide_message_ = inCollideMessageIn;
    collide_message_reverse_order_ = target_other_in;
  }
  auto in_collide_message() const -> bool { return in_collide_message_; }
  void process();
  void increment_skid_sound_count() { skid_sound_count_++; }
  void decrement_skid_sound_count() { skid_sound_count_--; }
  auto skid_sound_count() const -> int { return skid_sound_count_; }
  void incrementRollSoundCount() { roll_sound_count_++; }
  void decrement_roll_sound_count() { roll_sound_count_--; }
  auto getRollSoundCount() const -> int { return roll_sound_count_; }

  // We do some fancy collision testing stuff for trimeshes instead
  // of going through regular ODE space collision testing.. so we have
  // to keep track of these ourself.
  void AddTrimesh(dGeomID g);
  void RemoveTrimesh(dGeomID g);

  auto collision_count() const -> int { return collision_count_; }
  auto process_real_time() const -> millisecs_t { return real_time_; }
  auto last_impact_sound_time() const -> millisecs_t {
    return last_impact_sound_time_;
  }
  auto in_process() const -> bool { return in_process_; }

 private:
  auto AreColliding(const Part& p1, const Part& p2) -> bool;
  class SrcNodeCollideMap;
  class DstNodeCollideMap;
  class SrcPartCollideMap;
  class CollisionEvent;
  class CollisionReset;
  class Impl;
  std::vector<CollisionReset> collision_resets_;

  // Return a collision object between these two parts,
  // creating a new one if need be.
  auto GetCollision(Part* p1, Part* p2, MaterialContext** cc1,
                    MaterialContext** cc2) -> Collision*;

  std::vector<CollisionEvent> collision_events_;
  void ResetODE();
  void ShutdownODE();
  static void DoCollideCallback(void* data, dGeomID o1, dGeomID o2);
  void CollideCallback(dGeomID o1, dGeomID o2);
  void ProcessCollisions();

  std::unique_ptr<Impl> impl_;
  bool processing_collisions_{};
  dWorldID ode_world_{};
  dJointGroupID ode_contact_group_{};
  dSpaceID ode_space_{};
  millisecs_t real_time_{};
  bool in_process_{};
  std::vector<dGeomID> trimeshes_;
  millisecs_t last_impact_sound_time_{};
  int skid_sound_count_{};
  int roll_sound_count_{};
  int collision_count_{};
  Scene* scene_{};
  bool in_collide_message_{};
  bool collide_message_reverse_order_{};
  Collision* active_collision_{};
  Object::WeakRef<Node> active_collide_src_node_;
  Object::WeakRef<Node> active_collide_dst_node_;
  std::unique_ptr<base::CollisionCache> collision_cache_;
  friend class Impl;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_DYNAMICS_H_
