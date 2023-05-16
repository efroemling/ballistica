// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_DYNAMICS_RIGID_BODY_H_
#define BALLISTICA_SCENE_V1_DYNAMICS_RIGID_BODY_H_

#include <list>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ode/ode.h"
#include "ode/ode_joint.h"

namespace ballistica::scene_v1 {

// Wrapper for ode rigid bodies which implements collision tracking,
// flattening/restoring, and other extras.
class RigidBody : public Object {
 public:
  // Function type for low level collision callbacks.
  // These callbacks are called just before collision constraints
  // are being created between rigid bodies.  These callback
  // should be used only for contact adjustment - things like
  // changing friction depending on what part of the body was hit, etc.
  // Never use these callbacks to run script command or anything high-level.
  // Return false to cancel all constraint creation.
  typedef bool (*CollideCallbackFunc)(dContact* contacts, int count,
                                      RigidBody* collide_body,
                                      RigidBody* opposingbody,
                                      void* custom_data);
  enum class Type {
    // Collidable but not dynamically affected object.
    // Used to generate collisions.
    kGeomOnly,
    // Collidable as well as dynamically affected object.
    kBody
  };

  // Used to determine what kind of surface a body has and what surfaces it will
  // collide against a body defines its own collide type(s) and its mask for
  // what it will collide against collisions will only occur if each body's
  // collide mask includes the opposite body's type(s).
  enum CollideType {
    kCollideNone = 0,
    // Static background objects such as landscapes
    // These never move and generally never need to test for collisions against
    // other landscapes
    kCollideBackground = 0x01u,
    // Regions - these generally only test for collisions with active bodies
    kCollideRegion = 0x01u << 2u,
    // Active bodies - these generally collide against everything
    kCollideActive = 0x01u << 3u,
    // encapsulates all collide types
    kCollideAll = kCollideBackground | kCollideRegion | kCollideActive
  };

  // Different kinds of geometry a body can be.
  enum class Shape {
    // Simple sphere shape
    kSphere,
    // Simple cube shape
    kBox,
    // Capsule
    kCapsule,
    // cylinder made from 4 cubes (8 sides)
    kCylinder,
    // Trimesh
    kTrimesh
  };

  enum Flag {
    // The body is a 'bumper' - something that under-control character bodies
    // might want to collide with but most other stuff won't want to.
    kIsBumper = 1u << 0u,
    kIsRoller = 1u << 1u,
    kIsTerrain = 1u << 2u
  };

  // these are needed for full states
  auto GetEmbeddedSizeFull() -> int;
  void ExtractFull(const char** buffer);
  void EmbedFull(char** buffer);
  RigidBody(int id_in, Part* part_in, Type type_in, Shape shape_in,
            uint32_t collide_type_in, uint32_t collide_mask_in,
            SceneCollisionMesh* collision_mesh_in = nullptr,
            uint32_t flags = 0);
  ~RigidBody() override;
  auto body() const -> dBodyID { return body_; }
  auto geom(int i = 0) const -> dGeomID { return geoms_[i]; }

  // Draw a representation of the rigid body for debugging.
  void Draw(base::RenderPass* pass, bool shaded = true);
  auto part() const -> Part* {
    assert(part_.Exists());
    return part_.Get();
  }
  void Wake() {
    if (body_) {
      dBodyEnable(body_);
    }
  }
  void AddCallback(CollideCallbackFunc callback_in, void* data_in);
  auto CallCollideCallbacks(dContact* contacts, int count,
                            RigidBody* opposingbody) -> bool;
  void SetDimensions(
      float d1, float d2 = 0.0f, float d3 = 0.0f,  // body dimensions
      float m1 = 0.0f, float m2 = 0.0f,
      float m3 = 0.0f,  // Mass dimensions (default to regular if zero).
      float density = 1.0f);

  // If geomWakeOnCollide is true, a GEOM_ONLY object colliding with a sleeping
  // body will wake it up. Generally this should be true if the geom is moving
  // or changing.
  void set_geom_wake_on_collide(bool enable) { geom_wake_on_collide_ = enable; }
  auto geom_wake_on_collide() const -> bool { return geom_wake_on_collide_; }
  auto id() const -> int { return id_; }
  void ApplyGlobalImpulse(float px, float py, float pz, float fx, float fy,
                          float fz);
  auto ApplyImpulse(float px, float py, float pz, float vx, float vy, float vz,
                    float fdirx, float fdiry, float fdirz, float mag,
                    float v_mag, float radiusm, bool calc_only) -> float;
  void KillConstraints();

  // Rigid body joint wrapper.  This takes ownership of joints it is passed
  // all joints should use this mechanism so they are automatically
  // cleaned up when bodies are destroyed.
  class Joint {
   public:
    Joint();
    ~Joint();

    // Attach this wrapper to a new ode joint.
    // If already attached to a joint, that joint is first killed.
    void SetJoint(dxJointFixed* id, Scene* sg);

    // Returns the ode joint id or nullptr if it has been killed
    // (by the other body dying, etc).
    auto joint() const -> dJointID { return id_; }

    // Always use this in place of dJointAttach to attach the joint to rigid
    // bodies.
    void AttachToBodies(RigidBody* b1, RigidBody* b2);
    void Kill();  // Kills the joint if it is valid.
    // Whether joint still exists.
    auto IsAlive() const -> bool { return id_ != nullptr; }

   private:
    millisecs_t creation_time_{};
    dxJointFixed* id_{};
    RigidBody* b1_{};
    RigidBody* b2_{};
  };

  // Used by Joint.
  void AddJoint(Joint* j) { joints_.push_back(j); }
  void RemoveJoint(Joint* j) {
    for (auto i = joints_.begin(); i != joints_.end(); i++) {
      if ((*i) == j) {
        joints_.erase(i);
        return;
      }
    }
  }
  void Check();
  auto type() const -> Type { return type_; }
  auto collide_type() const -> uint32_t { return collide_type_; }
  auto collide_mask() const -> uint32_t { return collide_mask_; }
  auto flags() const -> uint32_t { return flags_; }
  void set_flags(uint32_t flags) { flags_ = flags; }
  auto can_cause_impact_damage() const -> bool {
    return can_cause_impact_damage_;
  }
  void set_can_cause_impact_damage(bool val) { can_cause_impact_damage_ = val; }

  // Applies to spheres.
  auto radius() const -> float { return dimensions_[0]; }
  auto GetTransform() -> Matrix44f;
  void UpdateBlending();
  void AddBlendOffset(float x, float y, float z);
  auto blend_offset() const -> const Vector3f& { return blend_offset_; }

  void ApplyToRenderComponent(base::RenderComponent* c);

 private:
  Vector3f blend_offset_{0.0f, 0.0f, 0.0f};
  millisecs_t blend_time_{};
#if BA_DEBUG_BUILD
  float prev_pos_[3]{};
  float prev_vel_[3]{};
  float prev_a_vel_[3]{};
#endif
  millisecs_t creation_time_{};
  bool can_cause_impact_damage_{};
  Dynamics* dynamics_{};
  uint32_t collide_type_{};
  uint32_t collide_mask_{};
  std::list<Joint*> joints_;
  bool geom_wake_on_collide_{};
  int id_{};
  Object::Ref<SceneCollisionMesh> collision_mesh_;
  float dimensions_[3]{};
  Type type_{};
  Shape shape_{};
  dBodyID body_{};
  std::vector<dGeomID> geoms_;
  millisecs_t birth_time_{};
  Object::WeakRef<Part> part_;
  struct CollideCallback {
    CollideCallbackFunc callback;
    void* data;
  };
  std::vector<CollideCallback> collide_callbacks_;
  uint32_t flags_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_DYNAMICS_RIGID_BODY_H_
