// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_PROP_NODE_H_
#define BALLISTICA_SCENE_NODE_PROP_NODE_H_

#include <string>
#include <vector>

#include "ballistica/assets/component/model.h"
#include "ballistica/assets/component/texture.h"
#include "ballistica/dynamics/bg/bg_dynamics_shadow.h"
#include "ballistica/dynamics/part.h"
#include "ballistica/scene/node/node.h"
#include "ballistica/scene/node/node_attribute.h"
#include "ballistica/scene/node/node_type.h"

namespace ballistica {

class PropNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit PropNode(Scene* scene, NodeType* node_type = nullptr);
  ~PropNode() override;
  void HandleMessage(const char* data) override;
  void Draw(FrameDef* frame_def) override;
  void Step() override;
  auto GetRigidBody(int id) -> RigidBody* override;
  auto is_area_of_interest() const -> bool {
    return (area_of_interest_ != nullptr);
  }
  void SetIsAreaOfInterest(bool val);
  auto reflection_scale() const -> std::vector<float> {
    return reflection_scale_;
  }
  void SetReflectionScale(const std::vector<float>& vals);
  auto GetReflection() const -> std::string;
  void SetReflection(const std::string& val);
  auto color_texture() const -> Texture* { return color_texture_.get(); }
  void set_color_texture(Texture* val) { color_texture_ = val; }
  auto GetModel() const -> Model* { return model_.get(); }
  void set_model(Model* val) { model_ = val; }
  auto light_model() const -> Model* { return light_model_.get(); }
  void set_light_model(Model* val) { light_model_ = val; }
  auto sticky() const -> bool { return sticky_; }
  void set_sticky(bool val) { sticky_ = val; }
  auto shadow_size() const -> float { return shadow_size_; }
  void set_shadow_size(float val) { shadow_size_ = val; }
  auto stick_to_owner() const -> bool { return stick_to_owner_; }
  void set_stick_to_owner(bool val) { stick_to_owner_ = val; }
  auto model_scale() const -> float { return model_scale_; }
  void set_model_scale(float val) { model_scale_ = val; }
  auto flashing() const -> bool { return flashing_; }
  void set_flashing(bool val) { flashing_ = val; }
  auto owner() const -> Node* { return owner_.get(); }
  void set_owner(Node* val) { owner_ = val; }
  auto GetMaterials() const -> std::vector<Material*>;
  void SetMaterials(const std::vector<Material*>& materials);
  auto GetVelocity() const -> std::vector<float>;
  void SetVelocity(const std::vector<float>& vals);
  auto GetPosition() const -> std::vector<float>;
  void SetPosition(const std::vector<float>& vals);
  auto extra_acceleration() const -> std::vector<float> {
    return extra_acceleration_;
  }
  void SetExtraAcceleration(const std::vector<float>& vals);
  auto GetBody() const -> std::string;
  void SetBody(const std::string& val);
  auto density() const -> float { return density_; }
  void SetDensity(float val);
  auto body_scale() const -> float { return body_scale_; }
  void SetBodyScale(float val);
  auto damping() const -> float { return damping_; }
  void set_damping(float val) { damping_ = val; }
  auto max_speed() const -> float { return max_speed_; }
  void set_max_speed(float val) { max_speed_ = val; }
  auto gravity_scale() const -> float { return gravity_scale_; }
  void set_gravity_scale(float val) { gravity_scale_ = val; }

 protected:
  // FIXME - need to make all this private and add protected getters/setters
  //  as necessary
  enum class BodyType { UNSET, SPHERE, BOX, LANDMINE, CRATE, CAPSULE, PUCK };
  void UpdateAreaOfInterest();
#if !BA_HEADLESS_BUILD
  BGDynamicsShadow shadow_;
#endif
  Part part_;
  void* area_of_interest_{};
  float model_scale_{1.0f};
  float shadow_size_{1.0f};
  int color_texture_Val{};
  float gravity_scale_{1.0f};
  Object::Ref<RigidBody> body_;
  RigidBody::Shape shape_{RigidBody::Shape::kSphere};
  Object::Ref<Texture> color_texture_;
  Object::Ref<Model> model_;
  Object::Ref<Model> light_model_;
  float density_{1.0f};
  float body_scale_{1.0f};
  float damping_{};
  float max_speed_{20.0f};
  std::vector<float> velocity_{0.0f, 0.0f, 0.0f};
  std::vector<float> position_{0.0f, 0.0f, 0.0f};
  std::vector<float> extra_acceleration_{0.0, 0.0, 0.0};
  float extra_model_scale_{1.0f};  // For use by subclasses.
  bool sticky_{};
  Object::WeakRef<Node> owner_;
  bool flashing_{};
  bool stick_to_owner_{};
  BodyType body_type_{BodyType::UNSET};
  bool reported_unset_body_type_{};
  ReflectionType reflection_{ReflectionType::kNone};
  std::vector<float> reflection_scale_{1.0f, 1.0f, 1.0f};
  float reflection_scale_r_{1.0f};
  float reflection_scale_g_{1.0f};
  float reflection_scale_b_{1.0f};
  static auto DoCollideCallback(dContact* c, int count,
                                RigidBody* colliding_body,
                                RigidBody* opposingbody, void* data) -> bool {
    auto* a = static_cast<PropNode*>(data);
    return a->CollideCallback(c, count, colliding_body, opposingbody);
  }
  auto CollideCallback(dContact* c, int count, RigidBody* colliding_body,
                       RigidBody* opposingbody) -> bool;
  void GetRigidBodyPickupLocations(int id, float* obj, float* character,
                                   float* hand1, float* hand2) override;
};

class PropNodeType : public NodeType {
 public:
#define BA_NODE_TYPE_CLASS PropNode
  BA_NODE_CREATE_CALL(CreateProp);
  BA_BOOL_ATTR(is_area_of_interest, is_area_of_interest, SetIsAreaOfInterest);
  BA_FLOAT_ARRAY_ATTR(reflection_scale, reflection_scale, SetReflectionScale);
  BA_STRING_ATTR(reflection, GetReflection, SetReflection);
  BA_TEXTURE_ATTR(color_texture, color_texture, set_color_texture);
  BA_MODEL_ATTR(model, GetModel, set_model);
  BA_MODEL_ATTR(light_model, light_model, set_light_model);
  BA_BOOL_ATTR(sticky, sticky, set_sticky);
  BA_FLOAT_ATTR(shadow_size, shadow_size, set_shadow_size);
  BA_BOOL_ATTR(stick_to_owner, stick_to_owner, set_stick_to_owner);
  BA_FLOAT_ATTR(model_scale, model_scale, set_model_scale);
  BA_BOOL_ATTR(flashing, flashing, set_flashing);
  BA_NODE_ATTR(owner, owner, set_owner);
  BA_MATERIAL_ARRAY_ATTR(materials, GetMaterials, SetMaterials);
  BA_FLOAT_ARRAY_ATTR(velocity, GetVelocity, SetVelocity);
  BA_FLOAT_ARRAY_ATTR(position, GetPosition, SetPosition);
  BA_FLOAT_ATTR(density, density, SetDensity);
  BA_FLOAT_ATTR(damping, damping, set_damping);
  BA_FLOAT_ATTR(body_scale, body_scale, SetBodyScale);
  BA_FLOAT_ATTR(max_speed, max_speed, set_max_speed);
  BA_FLOAT_ARRAY_ATTR(extra_acceleration, extra_acceleration,
                      SetExtraAcceleration);
  BA_FLOAT_ATTR(gravity_scale, gravity_scale, set_gravity_scale);
  BA_STRING_ATTR(body, GetBody, SetBody);
#undef BA_NODE_TYPE_CLASS

  explicit PropNodeType(const char* sub_type_name = nullptr,
                        NodeCreateFunc* sub_type_create = nullptr)
      : NodeType(sub_type_name ? sub_type_name : "prop",
                 sub_type_create ? sub_type_create : CreateProp),
        is_area_of_interest(this),
        reflection_scale(this),
        reflection(this),
        color_texture(this),
        model(this),
        light_model(this),
        sticky(this),
        shadow_size(this),
        stick_to_owner(this),
        model_scale(this),
        flashing(this),
        owner(this),
        materials(this),
        velocity(this),
        position(this),
        density(this),
        damping(this),
        max_speed(this),
        body_scale(this),
        body(this),
        extra_acceleration(this),
        gravity_scale(this) {}
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_PROP_NODE_H_
