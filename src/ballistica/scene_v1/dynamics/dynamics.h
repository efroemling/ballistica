// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_DYNAMICS_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_DYNAMICS_H_

#include <memory>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ode/ode.h"

namespace ballistica::scene_v1 {

class Dynamics : public Object {
 public:
  explicit Dynamics(Scene* scene);
  ~Dynamics() override;
  void Draw(base::FrameDef* frame_def);  // Draw any debug stuff, etc.
  auto ode_world() -> dWorldID { return ode_world_; }
  auto ode_contact_group() -> dJointGroupID { return ode_contact_group_; }
  auto ode_space() -> dSpaceID { return ode_space_; }

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
  void set_collide_message_state(bool in_collide_message,
                                 bool target_other = false) {
    in_collide_message_ = in_collide_message;
    collide_message_reverse_order_ = target_other;
  }
  auto in_collide_message() const { return in_collide_message_; }
  void Process();
  void IncrementSkidSoundCount() { skid_sound_count_++; }
  void DecrementSkidSoundCount() { skid_sound_count_--; }
  auto skid_sound_count() const { return skid_sound_count_; }
  void IncrementRollSoundCount() { roll_sound_count_++; }
  void DecrementRollSoundCount() { roll_sound_count_--; }
  auto roll_sound_count() const { return roll_sound_count_; }

  // We do some fancy collision testing stuff for trimeshes instead
  // of going through regular ODE space collision testing.. so we have
  // to keep track of these ourself.
  void AddTrimesh(dGeomID g);
  void RemoveTrimesh(dGeomID g);

  auto collision_count() const { return collision_count_; }
  auto process_real_time() const { return real_time_; }
  auto last_impact_sound_time() const { return last_impact_sound_time_; }
  auto in_process() const { return in_process_; }

 private:
  auto AreColliding_(const Part& p1, const Part& p2) -> bool;
  class SrcNodeCollideMap_;
  class DstNodeCollideMap_;
  class SrcPartCollideMap_;
  class CollisionEvent_;
  class CollisionReset_;
  class Impl_;
  std::vector<CollisionReset_> collision_resets_;

  // Return a collision object between these two parts,
  // creating a new one if need be.
  auto GetCollision(Part* p1, Part* p2, MaterialContext** cc1,
                    MaterialContext** cc2) -> Collision*;

  std::vector<CollisionEvent_> collision_events_;
  void ResetODE_();
  void ShutdownODE_();
  static void DoCollideCallback_(void* data, dGeomID o1, dGeomID o2);
  void CollideCallback_(dGeomID o1, dGeomID o2);
  void ProcessCollision_();

  int skid_sound_count_{};
  int roll_sound_count_{};
  int collision_count_{};
  bool in_process_{};
  bool in_collide_message_{};
  bool collide_message_reverse_order_{};
  bool processing_collisions_{};
  dWorldID ode_world_{};
  dJointGroupID ode_contact_group_{};
  dSpaceID ode_space_{};
  millisecs_t real_time_{};
  millisecs_t last_impact_sound_time_{};
  Scene* scene_{};
  Collision* active_collision_{};
  Object::WeakRef<Node> active_collide_src_node_;
  Object::WeakRef<Node> active_collide_dst_node_;
  std::vector<dGeomID> trimeshes_;
  std::unique_ptr<Impl_> impl_;
  std::unique_ptr<base::CollisionCache> collision_cache_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_DYNAMICS_H_
