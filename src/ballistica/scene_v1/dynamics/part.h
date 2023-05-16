// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_PART_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_PART_H_

#include <vector>

#include "ballistica/scene_v1/dynamics/rigid_body.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

// A categorized "part" of a node which contains collision and other grouping
// information for a set of rigid bodies composing the part.
// Each rigid body is contained in exactly one part.
class Part : public Object {
 public:
  explicit Part(Node* node, bool default_collide = true);
  ~Part() override;
  auto id() const -> int { return our_id_; }

  // Used by RigidBodies when adding themselves to the part.
  void AddBody(RigidBody* rigid_body_in) {
    rigid_bodies_.push_back(rigid_body_in);
  }

  // Used by RigidBodies when removing themselves from the part.
  void RemoveBody(RigidBody* rigid_body_in) {
    for (auto i = rigid_bodies_.begin(); i != rigid_bodies_.end(); ++i) {
      if (*i == rigid_body_in) {
        rigid_bodies_.erase(i);
        return;
      }
    }
    throw Exception();
  }

  // Wakes up all rigid bodies in the part.
  void Wake() {
    for (auto&& i : rigid_bodies_) {
      i->Wake();
    }
  }
  auto node() const -> Node* {
    assert(node_.Exists());
    return node_.Get();
  }

  // Apply a set of materials to the part.
  // Note than anytime a part's material set is changed,
  // All collisions occurring between it and other parts are reset,
  // so the old material set's separation commands will run and then
  // the new material's collide commands will run (if there is still a
  // collision)
  void SetMaterials(const std::vector<Material*>& vals);
  auto GetMaterials() const -> std::vector<Material*>;

  // Apply this part's materials to a context.
  void ApplyMaterials(MaterialContext* s, const Part* src_part,
                      const Part* dst_part);

  // Returns true if the material is directly attached to the part
  // note that having a material that calls the requested material does
  // not count.
  auto ContainsMaterial(const Material* m) const -> bool;

  // Returns whether the part is currently colliding with the specified node.
  auto IsCollidingWith(int64_t node) const -> bool;

  // Returns whether the part is currently colliding with the specified
  // node/part combo.
  auto IsCollidingWith(int64_t node, int part) const -> bool;

  // Used by g_logic to inform us we're now colliding with another part
  // if colliding is false, we've stopped colliding with this part.
  void SetCollidingWith(int64_t node_id, int part, bool colliding,
                        bool physical);

  // Kill constraints for all bodies in the part
  // (useful when teleporting and things like that).
  void KillConstraints();
  auto default_collides() const -> bool { return default_collides_; }
  auto GetAge() const -> millisecs_t;

  // Birthtime can be used to prevent spawning or teleporting parts from
  // colliding with things they are overlapping.
  // Any part with teleporting parts should use this to
  // reset their birth times.  Nodes have a function to do so for all their
  // contained parts as well.
  void UpdateBirthTime();
  auto last_impact_sound_time() const -> millisecs_t {
    return last_impact_sound_time_;
  }
  auto last_skid_sound_time() const -> millisecs_t {
    return last_skid_sound_time_;
  }
  auto last_roll_sound_time() const -> millisecs_t {
    return last_roll_sound_time_;
  }
  void set_last_impact_sound_time(millisecs_t t) {
    last_impact_sound_time_ = t;
  }
  void set_last_skid_sound_time(millisecs_t t) { last_skid_sound_time_ = t; }
  void set_last_roll_sound_time(millisecs_t t) { last_roll_sound_time_ = t; }

  auto rigid_bodies() const -> const std::vector<RigidBody*>& {
    return rigid_bodies_;
  }

  // Debugging: check for NaNs and whatnot.
  void CheckBodies();

 private:
  Dynamics* dynamics_;
  class Collision {
   public:
    int node;
    int part;
    Collision(int node_in, int part_in) : node(node_in), part(part_in) {}
  };

  // Collisions currently affecting us stored for quick access.
  std::vector<Collision> collisions_;
  bool default_collides_;
  millisecs_t birth_time_;
  int our_id_;
  Object::WeakRef<Node> node_;
  std::vector<Object::Ref<Material> > materials_;
  std::vector<RigidBody*> rigid_bodies_;

  // Last time this part played a collide sound (used by the audio system).
  millisecs_t last_impact_sound_time_ = 0;
  millisecs_t last_skid_sound_time_ = 0;
  millisecs_t last_roll_sound_time_ = 0;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_PART_H_
