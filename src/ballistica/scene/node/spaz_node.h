// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_NODE_SPAZ_NODE_H_
#define BALLISTICA_SCENE_NODE_SPAZ_NODE_H_

#include <string>
#include <vector>

#include "ballistica/dynamics/part.h"
#include "ballistica/graphics/renderer.h"
#include "ballistica/logic/player.h"
#include "ballistica/scene/node/node.h"

namespace ballistica {

// Current player character spaz node.
class SpazNode : public Node {
 public:
  static auto InitType() -> NodeType*;
  explicit SpazNode(Scene* scene);
  ~SpazNode() override;
  void Step() override;
  void HandleMessage(const char* data) override;
  void Draw(FrameDef* frame_def) override;
  auto GetRigidBody(int id) -> RigidBody* override;
  void GetRigidBodyPickupLocations(int id, float* obj, float* character,
                                   float* hand1, float* hand2) override;
  auto GetResyncDataSize() -> int override;
  auto GetResyncData() -> std::vector<uint8_t> override;
  void ApplyResyncData(const std::vector<uint8_t>& data) override;
  auto can_fly() const -> bool { return can_fly_; }
  void set_can_fly(bool val) { can_fly_ = val; }
  auto hockey() const -> bool { return hockey_; }
  void set_hockey(bool val) { hockey_ = val; }
  auto GetRollerMaterials() const -> std::vector<Material*>;
  void SetRollerMaterials(const std::vector<Material*>& vals);
  auto GetExtrasMaterials() const -> std::vector<Material*>;
  void SetExtrasMaterials(const std::vector<Material*>& vals);
  auto GetPunchMaterials() const -> std::vector<Material*>;
  void SetPunchMaterials(const std::vector<Material*>& vals);
  auto GetPickupMaterials() const -> std::vector<Material*>;
  void SetPickupMaterials(const std::vector<Material*>& vals);
  auto GetMaterials() const -> std::vector<Material*>;
  void SetMaterials(const std::vector<Material*>& vals);
  auto area_of_interest_radius() const -> float {
    return area_of_interest_radius_;
  }
  void set_area_of_interest_radius(float val) {
    area_of_interest_radius_ = val;
  }
  auto name() const -> std::string { return name_; }
  void set_name(const std::string& val) { name_ = val; }
  auto counter_text() const -> std::string { return counter_text_; }
  void set_counter_text(const std::string& val) { counter_text_ = val; }
  auto mini_billboard_1_texture() const -> Texture* {
    return mini_billboard_1_texture_.get();
  }
  void set_mini_billboard_1_texture(Texture* val) {
    mini_billboard_1_texture_ = val;
  }
  auto mini_billboard_2_texture() const -> Texture* {
    return mini_billboard_2_texture_.get();
  }
  void set_mini_billboard_2_texture(Texture* val) {
    mini_billboard_2_texture_ = val;
  }
  auto mini_billboard_3_texture() const -> Texture* {
    return mini_billboard_3_texture_.get();
  }
  void set_mini_billboard_3_texture(Texture* val) {
    mini_billboard_3_texture_ = val;
  }
  auto mini_billboard_1_start_time() const -> millisecs_t {
    return mini_billboard_1_start_time_;
  }
  void set_mini_billboard_1_start_time(millisecs_t val) {
    mini_billboard_1_start_time_ = val;
  }
  auto mini_billboard_1_end_time() const -> millisecs_t {
    return mini_billboard_1_end_time_;
  }
  void set_mini_billboard_1_end_time(millisecs_t val) {
    mini_billboard_1_end_time_ = val;
  }
  auto mini_billboard_2_start_time() const -> millisecs_t {
    return mini_billboard_2_start_time_;
  }
  void set_mini_billboard_2_start_time(millisecs_t val) {
    mini_billboard_2_start_time_ = val;
  }
  auto mini_billboard_2_end_time() const -> millisecs_t {
    return mini_billboard_2_end_time_;
  }
  void set_mini_billboard_2_end_time(millisecs_t val) {
    mini_billboard_2_end_time_ = val;
  }
  auto mini_billboard_3_start_time() const -> millisecs_t {
    return mini_billboard_3_start_time_;
  }
  void set_mini_billboard_3_start_time(millisecs_t val) {
    mini_billboard_3_start_time_ = val;
  }
  auto mini_billboard_3_end_time() const -> millisecs_t {
    return mini_billboard_3_end_time_;
  }
  void set_mini_billboard_3_end_time(millisecs_t val) {
    mini_billboard_3_end_time_ = val;
  }
  auto billboard_texture() const -> Texture* {
    return billboard_texture_.get();
  }
  void set_billboard_texture(Texture* val) { billboard_texture_ = val; }
  auto billboard_opacity() const -> float { return billboard_opacity_; }
  void set_billboard_opacity(float val) { billboard_opacity_ = val; }
  auto counter_texture() const -> Texture* { return counter_texture_.get(); }
  void set_counter_texture(Texture* val) { counter_texture_ = val; }
  auto invincible() const -> bool { return invincible_; }
  void set_invincible(bool val) { invincible_ = val; }
  auto name_color() const -> std::vector<float> { return name_color_; }
  void SetNameColor(const std::vector<float>& vals);
  auto highlight() const -> std::vector<float> { return highlight_; }
  void set_highlight(const std::vector<float>& vals);
  auto color() const -> std::vector<float> { return color_; }
  void SetColor(const std::vector<float>& vals);
  auto hurt() const -> float { return hurt_; }
  void SetHurt(float val);
  auto boxing_gloves_flashing() const -> bool {
    return boxing_gloves_flashing_;
  }
  void set_boxing_gloves_flashing(bool val) { boxing_gloves_flashing_ = val; }
  auto source_player() const -> Player* { return source_player_.get(); }
  void set_source_player(Player* val) { source_player_ = val; }
  auto frozen() const -> bool { return frozen_; }
  void SetFrozen(bool val);
  auto have_boxing_gloves() const -> bool { return have_boxing_gloves_; }
  void SetHaveBoxingGloves(bool val);
  auto is_area_of_interest() const -> bool {
    return (area_of_interest_ != nullptr);
  }
  void SetIsAreaOfInterest(bool val);
  auto curse_death_time() const -> millisecs_t { return curse_death_time_; }
  void SetCurseDeathTime(millisecs_t val);
  auto shattered() const -> int { return shattered_; }
  void SetShattered(int val);
  auto dead() const -> bool { return dead_; }
  void SetDead(bool val);
  auto style() const -> std::string { return style_; }
  void SetStyle(const std::string& val);
  auto GetKnockout() const -> float {
    return static_cast<float>(knockout_) / 255.0f;
  }
  auto punch_power() const -> float { return punch_power_; }
  auto GetPunchMomentumAngular() const -> float {
    return 0.2f + punch_momentum_angular_;
  }
  auto GetPunchMomentumLinear() const -> std::vector<float>;
  auto damage_out() const -> float { return damage_out_; }
  auto damage_smoothed() const -> float { return damage_smoothed_; }
  auto GetPunchVelocity() const -> std::vector<float>;
  auto GetVelocity() const -> std::vector<float>;
  auto GetPositionForward() const -> std::vector<float>;
  auto GetPositionCenter() const -> std::vector<float>;
  auto GetPunchPosition() const -> std::vector<float>;
  auto GetTorsoPosition() const -> std::vector<float>;
  auto GetPosition() const -> std::vector<float>;
  auto hold_body() const -> int { return hold_body_; }
  void set_hold_body(int val) { hold_body_ = val; }
  auto hold_node() const -> Node* { return hold_node_.get(); }
  void SetHoldNode(Node* val);
  auto GetJumpSounds() const -> std::vector<Sound*>;
  void SetJumpSounds(const std::vector<Sound*>& vals);
  auto GetAttackSounds() const -> std::vector<Sound*>;
  void SetAttackSounds(const std::vector<Sound*>& vals);
  auto GetImpactSounds() const -> std::vector<Sound*>;
  void SetImpactSounds(const std::vector<Sound*>& vals);
  auto GetDeathSounds() const -> std::vector<Sound*>;
  void SetDeathSounds(const std::vector<Sound*>& vals);
  auto GetPickupSounds() const -> std::vector<Sound*>;
  void SetPickupSounds(const std::vector<Sound*>& vals);
  auto GetFallSounds() const -> std::vector<Sound*> {
    return RefsToPointers(fall_sounds_);
  }
  void SetFallSounds(const std::vector<Sound*>& vals);
  auto color_texture() const -> Texture* { return color_texture_.get(); }
  void set_color_texture(Texture* val) { color_texture_ = val; }
  auto color_mask_texture() const -> Texture* {
    return color_mask_texture_.get();
  }
  void set_color_mask_texture(Texture* val) { color_mask_texture_ = val; }
  auto head_model() const -> Model* { return head_model_.get(); }
  void set_head_model(Model* val) { head_model_ = val; }
  auto torso_model() const -> Model* { return torso_model_.get(); }
  void set_torso_model(Model* val) { torso_model_ = val; }
  auto pelvis_model() const -> Model* { return pelvis_model_.get(); }
  void set_pelvis_model(Model* val) { pelvis_model_ = val; }
  auto upper_arm_model() const -> Model* { return upper_arm_model_.get(); }
  void set_upper_arm_model(Model* val) { upper_arm_model_ = val; }
  auto forearm_model() const -> Model* { return forearm_model_.get(); }
  void set_forearm_model(Model* val) { forearm_model_ = val; }
  auto hand_model() const -> Model* { return hand_model_.get(); }
  void set_hand_model(Model* val) { hand_model_ = val; }
  auto upper_leg_model() const -> Model* { return upper_leg_model_.get(); }
  void set_upper_leg_model(Model* val) { upper_leg_model_ = val; }
  auto lower_leg_model() const -> Model* { return lower_leg_model_.get(); }
  void set_lower_leg_model(Model* val) { lower_leg_model_ = val; }
  auto toes_model() const -> Model* { return toes_model_.get(); }
  void set_toes_model(Model* val) { toes_model_ = val; }
  auto billboard_cross_out() const -> bool { return billboard_cross_out_; }
  void set_billboard_cross_out(bool val) { billboard_cross_out_ = val; }
  auto jump_pressed() const -> bool { return jump_pressed_; }
  void SetJumpPressed(bool val);
  auto punch_pressed() const -> bool { return punch_pressed_; }
  void SetPunchPressed(bool val);
  auto bomb_pressed() const -> bool { return bomb_pressed_; }
  void SetBombPressed(bool val);
  auto run() const -> float { return run_; }
  void SetRun(float val);
  auto fly_pressed() const -> bool { return fly_pressed_; }
  void SetFlyPressed(bool val);
  auto behavior_version() const -> int { return behavior_version_; }
  void set_behavior_version(int val) {
    behavior_version_ = static_cast_check_fit<uint8_t>(val);
  }
  auto pickup_pressed() const -> bool { return pickup_pressed_; }
  void SetPickupPressed(bool val);
  auto hold_position_pressed() const -> bool { return hold_position_pressed_; }
  void SetHoldPositionPressed(bool val);
  auto move_left_right() const -> float { return move_left_right_; }
  void SetMoveLeftRight(float val);
  auto move_up_down() const -> float { return move_up_down_; }
  void SetMoveUpDown(float val);

  // Preserve some old behavior so we dont have to re-code the demo.
  auto demo_mode() const -> bool { return demo_mode_; }
  void set_demo_mode(bool val) { demo_mode_ = val; }

 private:
  enum ShatterDamage {
    kNeckJointBroken = 1u << 0u,
    kPelvisJointBroken = 1u << 1u,
    kUpperLeftLegJointBroken = 1u << 2u,
    kUpperRightLegJointBroken = 1u << 3u,
    kLowerLeftLegJointBroken = 1u << 4u,
    kLowerRightLegJointBroken = 1u << 5u,
    kUpperLeftArmJointBroken = 1u << 6u,
    kUpperRightArmJointBroken = 1u << 7u,
    kLowerLeftArmJointBroken = 1u << 8u,
    kLowerRightArmJointBroken = 1u << 9u
  };
  void PlayHurtSound();
  void DrawBodyParts(ObjectComponent* c, bool shading, float death_fade,
                     float death_scale, float* add_color);
  void SetupEyeLidShading(ObjectComponent* c, float death_fade,
                          float* add_color);
  void DrawEyeLids(RenderComponent* c, float death_fade, float death_scale);
  void DrawEyeBalls(RenderComponent* c, ObjectComponent* oc, bool shading,
                    float death_fade, float death_scale, float* add_color);
  void DoFlyPress();

  // Create a fixed joint between two bodies.
  // The anchor is by default at the center of the first body.
  auto CreateFixedJoint(RigidBody* b1, RigidBody* b2, float ls, float ld,
                        float as, float ad) -> JointFixedEF*;

  // Same but more explicit; provide anchor offsets for the two bodies.
  // This also moves the second body based on those values so the anchor
  // points line up.
  auto CreateFixedJoint(RigidBody* b1, RigidBody* b2, float ls, float ld,
                        float as, float ad, float a1x, float a1y, float a1z,
                        float a2x, float a2y, float a2z, bool reposition = true)
      -> JointFixedEF*;
  void Throw(bool withBombButton);

  // Reset to a standing, non-moving state at the given point.
  void Stand(float x, float y, float z, float angle);
  void OnGraphicsQualityChanged(GraphicsQuality q) override;
  void UpdateForGraphicsQuality(GraphicsQuality q);
  void UpdateAreaOfInterest();
  auto CollideCallback(dContact* c, int count, RigidBody* colliding_body,
                       RigidBody* opposingbody) -> bool;
  auto PreFilterCollision(RigidBody* r1, RigidBody* r2) -> bool override;
  auto IsBrokenBodyPart(int id) -> bool;
  static auto StaticCollideCallback(dContact* c, int count,
                                    RigidBody* colliding_body,
                                    RigidBody* opposingbody, void* data)
      -> bool {
    auto* a = static_cast<SpazNode*>(data);
    return a->CollideCallback(c, count, colliding_body, opposingbody);
  }
  void DropHeldObject();
  void ApplyTorque(float x, float y, float z);
  void CreateHair();
  void DestroyHair();
  void UpdateBodiesForStyle();
  void UpdateJoints();
#if !BA_HEADLESS_BUILD
  class FullShadowSet;
  class SimpleShadowSet;
  Object::Ref<FullShadowSet> full_shadow_set_;
  Object::Ref<SimpleShadowSet> simple_shadow_set_;
#endif  // !BA_HEADLESS_BUILD
  float pickup_pos_1_[3]{0.0f, 0.0f, 0.0f};
  float pickup_pos_2_[3]{0.0f, 0.0f, 0.0f};
  float pickup_q1_[4]{0.0f, 0.0f, 0.0f, 0.0f};
  float pickup_q2_[4]{0.0f, 0.0f, 0.0f, 0.0f};
  uint32_t step_count_{};
  millisecs_t birth_time_{};
  Object::Ref<Texture> color_texture_;
  Object::Ref<Texture> color_mask_texture_;
  Object::Ref<Model> head_model_;
  Object::Ref<Model> torso_model_;
  Object::Ref<Model> pelvis_model_;
  Object::Ref<Model> upper_arm_model_;
  Object::Ref<Model> forearm_model_;
  Object::Ref<Model> hand_model_;
  Object::Ref<Model> upper_leg_model_;
  Object::Ref<Model> lower_leg_model_;
  Object::Ref<Model> toes_model_;
  std::vector<Object::Ref<Sound> > jump_sounds_;
  std::vector<Object::Ref<Sound> > attack_sounds_;
  std::vector<Object::Ref<Sound> > impact_sounds_;
  std::vector<Object::Ref<Sound> > death_sounds_;
  std::vector<Object::Ref<Sound> > pickup_sounds_;
  std::vector<Object::Ref<Sound> > fall_sounds_;
  Object::WeakRef<Node> hold_node_;
  std::string style_{"spaz"};
  Object::WeakRef<Player> source_player_;
  bool clamp_move_values_to_circle_{true};
  bool demo_mode_{};
  std::string curse_timer_txt_;
  TextGroup curse_timer_text_group_;
  std::string counter_mesh_text_;
  TextGroup counter_text_group_;
  std::string counter_text_;
  std::vector<float> name_color_{1.0f, 1.0f, 1.0f};
  std::string name_;
  std::string name_mesh_txt_;
  TextGroup name_text_group_;
  MeshIndexedSimpleFull billboard_1_mesh_;
  MeshIndexedSimpleFull billboard_2_mesh_;
  MeshIndexedSimpleFull billboard_3_mesh_;
  float punch_power_{};
  float impact_damage_accum_{};
  Part spaz_part_;
  Part hair_part_;
  Part punch_part_;
  Part pickup_part_;
  Part roller_part_;
  Part extras_part_;
  Part limbs_part_upper_;
  Part limbs_part_lower_;
  bool dead_{};
  // 1 for partially-shattered, 2 for completely.
  int shattered_{};
  bool invincible_{};
  bool trying_to_fly_{};
  bool throwing_with_bomb_button_{};
  bool can_fly_{};
  bool hockey_{};
  bool have_boxing_gloves_{};
  bool boxing_gloves_flashing_{};
  bool frozen_{};
  uint8_t flashing_{};
  float throw_power_{};
  millisecs_t throw_start_{};
  bool have_thrown_{};
  int hold_body_{};
  millisecs_t last_head_collide_time_{};
  millisecs_t last_external_impulse_time_{};
  millisecs_t last_impact_damage_dispatch_time_{};
  Object::Ref<Texture> billboard_texture_;
  float billboard_opacity_{};
  float area_of_interest_radius_{5.0f};
  Object::Ref<Texture> counter_texture_;
  Object::Ref<Texture> mini_billboard_1_texture_;
  millisecs_t mini_billboard_1_start_time_{};
  millisecs_t mini_billboard_1_end_time_{};
  Object::Ref<Texture> mini_billboard_2_texture_;
  millisecs_t mini_billboard_2_start_time_{};
  millisecs_t mini_billboard_2_end_time_{};
  Object::Ref<Texture> mini_billboard_3_texture_;
  millisecs_t mini_billboard_3_start_time_{};
  millisecs_t mini_billboard_3_end_time_{};
  millisecs_t curse_death_time_{};
  millisecs_t last_out_of_bounds_time_{};
  float base_pelvis_roller_anchor_offset_{};
  std::vector<float> color_{1.0f, 1.0f, 1.0f};
  std::vector<float> highlight_{0.5f, 0.5f, 0.5f};
  std::vector<float> shadow_color_{0.5f, 0.5f, 0.5f};
  bool wings_{};
  Vector3f wing_pos_left_{0.0f, 0.0f, 0.0f};
  Vector3f wing_vel_left_{0.0f, 0.0f, 0.0f};
  Vector3f wing_pos_right_{0.0f, 0.0f, 0.0f};
  Vector3f wing_vel_right_{0.0f, 0.0f, 0.0f};
  uint32_t voice_play_id_{0xFFFFFFFF};
  uint32_t tick_play_id_{0xFFFFFFFF};
  millisecs_t last_fall_time_{};
  uint32_t fall_play_id_{};
  AreaOfInterest* area_of_interest_{};
  millisecs_t celebrate_until_time_left_{};
  millisecs_t celebrate_until_time_right_{};
  millisecs_t last_fly_time_{};
  int footing_{};
  int8_t lr_{};
  int8_t ud_{};
  float lr_norm_{};
  float raw_ud_norm_{};
  float raw_lr_norm_{};
  float ud_norm_{};
  float ud_smooth_{};
  float lr_smooth_{};
  float ud_diff_smooth_{};
  float lr_diff_smooth_{};
  float ud_diff_smoother_{};
  float lr_diff_smoother_{};
  float prev_vel_[3]{0.0f, 0.0f, 0.0f};
  float accel_[3]{0.0f, 0.0f, 0.0f};
  float throw_ud_{};
  float throw_lr_{};
  uint8_t behavior_version_{};
  uint8_t balance_{};
  uint8_t dizzy_{};
  uint8_t knockout_{};
  uint8_t jump_{};
  uint8_t punch_{};
  uint8_t pickup_{};
  float fly_power_{};
  float ball_size_{1.0f};
  float run_{};
  float move_left_right_{};
  float move_up_down_{};
  bool jump_pressed_{};
  bool punch_pressed_{};
  bool bomb_pressed_{};
  bool fly_pressed_{};
  bool pickup_pressed_{};
  bool hold_position_pressed_{};
  millisecs_t last_jump_time_{};
  RigidBody::Joint pickup_joint_;
  float eyes_lr_{};
  float eyes_ud_{};
  float eyes_lr_smooth_{};
  float eyes_ud_smooth_{};
  float eyelid_left_ud_{};
  float eyelid_left_ud_smooth_{};
  float eyelid_right_ud_{};
  float eyelid_right_ud_smooth_{};
  float blink_{};
  float blink_smooth_{};
  bool flap_{};
  bool flapping_{};
  bool holding_something_{};
  millisecs_t last_pickup_time_{};
  millisecs_t last_punch_time_{};
  bool throwing_{};
  bool head_back_{};
  millisecs_t last_force_scream_time_{};
  bool force_scream_{};
  Object::Ref<RigidBody> body_head_;
  Object::Ref<RigidBody> body_torso_;
  Object::Ref<RigidBody> body_pelvis_;
  Object::Ref<RigidBody> body_roller_;
  Object::Ref<RigidBody> body_punch_;
  Object::Ref<RigidBody> body_pickup_;
  Object::Ref<RigidBody> stand_body_;
  Object::Ref<RigidBody> upper_right_arm_body_;
  Object::Ref<RigidBody> lower_right_arm_body_;
  Object::Ref<RigidBody> upper_left_arm_body_;
  Object::Ref<RigidBody> lower_left_arm_body_;
  Object::Ref<RigidBody> upper_right_leg_body_;
  Object::Ref<RigidBody> lower_right_leg_body_;
  Object::Ref<RigidBody> upper_left_leg_body_;
  Object::Ref<RigidBody> lower_left_leg_body_;
  Object::Ref<RigidBody> left_toes_body_;
  Object::Ref<RigidBody> right_toes_body_;
  JointFixedEF* upper_right_arm_joint_{};
  JointFixedEF* lower_right_arm_joint_{};
  JointFixedEF* upper_left_arm_joint_{};
  JointFixedEF* lower_left_arm_joint_{};
  JointFixedEF* upper_right_leg_joint_{};
  JointFixedEF* lower_right_leg_joint_{};
  JointFixedEF* upper_left_leg_joint_{};
  JointFixedEF* lower_left_leg_joint_{};
  JointFixedEF* left_toes_joint_{};
  JointFixedEF* left_toes_joint_2_{};
  JointFixedEF* right_toes_joint_{};
  JointFixedEF* right_toes_joint_2_{};
  JointFixedEF* right_leg_ik_joint_{};
  JointFixedEF* left_leg_ik_joint_{};
  JointFixedEF* right_arm_ik_joint_{};
  JointFixedEF* left_arm_ik_joint_{};
  float last_stand_body_orient_x_{};
  float last_stand_body_orient_z_{};
  JointFixedEF* neck_joint_{};
  JointFixedEF* pelvis_joint_{};
  JointFixedEF* roller_ball_joint_{};
  dJointID a_motor_brakes_{};
  JointFixedEF* stand_joint_{};
  dJointID a_motor_roller_{};
  bool female_{};
  bool female_hair_{};
  bool eyeless_{};
  bool fat_{};
  bool pirate_{};
  bool flippers_{};
  bool frosty_{};
  bool dull_reflection_{};
  bool ninja_{};
  bool punch_right_{};
  Object::Ref<RigidBody> hair_front_right_body_;
  JointFixedEF* hair_front_right_joint_{};
  Object::Ref<RigidBody> hair_front_left_body_;
  JointFixedEF* hair_front_left_joint_{};
  Object::Ref<RigidBody> hair_ponytail_top_body_;
  JointFixedEF* hair_ponytail_top_joint_{};
  Object::Ref<RigidBody> hair_ponytail_bottom_body_;
  JointFixedEF* hair_ponytail_bottom_joint_{};
  float hold_hand_offset_left_[3]{};
  float hold_hand_offset_right_[3]{};
  float jolt_head_vel_[3]{0.0f, 0.0f, 0.0f};
  millisecs_t last_shatter_test_time_{};
  float roll_amt_{};
  float damage_smoothed_{};
  float damage_out_{};
  float punch_dir_x_{1.0f};
  float punch_dir_z_{};
  float punch_momentum_angular_{};
  float punch_momentum_angular_d_{};
  float punch_momentum_linear_{};
  float punch_momentum_linear_d_{};
  float a_vel_y_smoothed_{};
  float a_vel_y_smoothed_more_{};
  float eye_lid_angle_{};
  bool last_hit_was_punch_{};
  int fly_time_{};
  float eye_ball_color_red_{0.5f};
  float eye_ball_color_green_{0.5f};
  float eye_ball_color_blue_{0.5f};
  float eye_lid_color_red_{0.5f};
  float eye_lid_color_green_{0.3f};
  float eye_lid_color_blue_{0.2f};
  float eye_color_red_{0.5f};
  float eye_color_green_{0.5f};
  float eye_color_blue_{1.2f};
  float torso_radius_{0.15f};
  float shoulder_offset_x_{};
  float shoulder_offset_y_{};
  float shoulder_offset_z_{};
  bool has_eyelids_{true};
  float eye_scale_{1.0f};
  float reflection_scale_{0.1f};
  float default_eye_lid_angle_{};
  float eye_offset_x_{};
  float eye_offset_y_{};
  float eye_offset_z_{};
  millisecs_t last_got_boxing_gloves_time_{};
  uint32_t shatter_damage_{};
  bool running_{};
  float speed_smoothed_{};
  float run_gas_{};
  float hurt_{};
  float hurt_smoothed_{};
  millisecs_t last_hurt_change_time_{};
  bool billboard_cross_out_{};
  millisecs_t death_time_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_SCENE_NODE_SPAZ_NODE_H_
