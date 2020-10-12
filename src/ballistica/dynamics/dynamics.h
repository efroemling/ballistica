// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_DYNAMICS_DYNAMICS_H_
#define BALLISTICA_DYNAMICS_DYNAMICS_H_

#include <map>
#include <memory>
#include <vector>

#include "ballistica/core/object.h"
#include "ode/ode.h"

namespace ballistica {

class Dynamics : public Object {
 public:
  explicit Dynamics(Scene* scene_in);
  ~Dynamics() override;
  void Draw(FrameDef* frame_def);  // Draw any debug stuff, etc.
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
        .get();
  }
  // Used by collision callbacks - internal.
  auto GetActiveCollideDstNode() -> Node* {
    assert(active_collision_);
    return (collide_message_reverse_order_ ? active_collide_src_node_
                                           : active_collide_dst_node_)
        .get();
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
  std::vector<CollisionReset> collision_resets_;

  // Return a collision object between these two parts,
  // creating a new one if need be.
  auto GetCollision(Part* p1, Part* p2, MaterialContext** cc1,
                    MaterialContext** cc2) -> Collision*;

  // Contains in-progress collisions for current nodes.
  std::map<int64_t, SrcNodeCollideMap> node_collisions_;
  std::vector<CollisionEvent> collision_events_;
  void HandleDisconnect(
      const std::map<int64_t,
                     ballistica::Dynamics::SrcNodeCollideMap>::iterator& i,
      const std::map<int64_t,
                     ballistica::Dynamics::DstNodeCollideMap>::iterator& j,
      const std::map<int, SrcPartCollideMap>::iterator& k,
      const std::map<int, Object::Ref<Collision> >::iterator& l);
  void ResetODE();
  void ShutdownODE();
  static void DoCollideCallback(void* data, dGeomID o1, dGeomID o2);
  void CollideCallback(dGeomID o1, dGeomID o2);
  void ProcessCollisions();
  bool processing_collisions_ = false;
  dWorldID ode_world_ = nullptr;
  dJointGroupID ode_contact_group_ = nullptr;
  dSpaceID ode_space_ = nullptr;
  millisecs_t real_time_ = 0;
  bool in_process_ = false;
  std::vector<dGeomID> trimeshes_;
  millisecs_t last_impact_sound_time_ = 0;
  int skid_sound_count_ = 0;
  int roll_sound_count_ = 0;
  int collision_count_ = 0;
  Scene* scene_;
  bool in_collide_message_ = false;
  bool collide_message_reverse_order_ = false;
  Collision* active_collision_ = nullptr;
  Object::WeakRef<Node> active_collide_src_node_;
  Object::WeakRef<Node> active_collide_dst_node_;
  std::unique_ptr<CollisionCache> collision_cache_;
};

}  // namespace ballistica

#endif  // BALLISTICA_DYNAMICS_DYNAMICS_H_
