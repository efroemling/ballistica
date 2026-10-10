// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_NODE_SPAZ_PHYSICS_TUNING_H_
#define BALLISTICA_SCENE_V1_NODE_SPAZ_PHYSICS_TUNING_H_

namespace ballistica::scene_v1 {

// Tuning values for the spaz's main-sim physics: how heavy the
// character is, how it is held up, how it moves and how it meets the
// world. This is the place to experiment with character 'feel'.
//
// A spaz is simulated as three core bodies (head, torso, pelvis)
// riding on an invisible 'roller ball' that stands in for the legs:
//
// - The ball hangs off the torso on a spring (the suspension). Jumps
//   are that spring shoving the ball down against the ground.
// - A motor spins the ball to walk and run; a second motor acts as
//   brakes.
// - A 'stand joint' pulls the torso upright, with a strength that
//   follows the character's balance (zero when knocked out or frozen).
// - The neck and pelvis joints are springs holding head and pelvis to
//   the torso.
//
// There are two sets of values, and each spaz picks one for life when
// it is created (SpazNode::UseBgLimbs_):
//
// - kSpazPhysicsTuningLegacyLimbs: the original physics, where arms
//   and legs are bodies in the main sim. Still used for older servers
//   and by the tutorial. DO NOT CHANGE THESE; recorded input and
//   compatibility depend on them staying exactly as they are.
// - kSpazPhysicsTuningBgLimbs: the current physics, where arms and
//   legs are simulated visually on the bg-dynamics thread and the core
//   carries their mass. THIS IS THE ONE TO TUNE.
//
// Everything here is sim state: a host and its clients must agree on
// it or clients will fight the host's corrections, so shipped changes
// to the bg-limbs values go out under a scene protocol bump.
//
// Units are ODE's (roughly meters, kilograms, seconds). Stiffness and
// damping pairs describe a spring: more stiffness pulls harder toward
// the target, more damping kills oscillation (too little and things
// bounce, too much and they feel sluggish).
struct SpazPhysicsTuning {
  // --- Mass ---------------------------------------------------------------
  // Body mass is density times the volume of a fixed 'mass shape' that
  // is separate from the collision shape, so these change weight and
  // inertia without changing what the character bumps into. Heavier
  // bodies sag more on their springs, respond less to forces and take
  // more damage from area blasts (which scale with mass).

  // Head; mass shape is a 0.28 sphere.
  float head_density;
  // Torso; mass shape is a 0.2 sphere. Carries the arms' mass in
  // bg-limbs mode.
  float torso_density;
  // Pelvis; mass shape is a 0.25 x pelvis_mass_height x 0.16 box.
  float pelvis_density;
  // Height of the pelvis mass box. Taller is heavier and also harder
  // to tip. Carries the legs' mass in bg-limbs mode.
  float pelvis_mass_height;
  // Roller ball; mass shape is a 0.3 sphere whatever size the ball
  // currently is.
  float roller_density;

  // --- Suspension and jumping ---------------------------------------------
  // The spring holding the roller ball under the torso: the
  // character's legs, in effect. Softer or less damped rides bouncier.
  float roller_joint_stiffness;
  float roller_joint_damping;
  // A jump pushes the spring's rest point down by this distance for
  // jump_steps sim steps, launching the character off the ball.
  float jump_push_distance;
  int jump_steps;
  // The suspension spring is scaled by these while the jump is
  // pushing.
  float jump_roller_stiffness_scale;
  float jump_roller_damping_scale;

  // --- Core joints --------------------------------------------------------
  // Pelvis-to-torso spring: 'linear' holds position, 'angular' holds
  // orientation. (Stiffened and locked while frozen.)
  float pelvis_linear_stiffness;
  float pelvis_linear_damping;
  float pelvis_angular_stiffness;
  float pelvis_angular_damping;
  // Head-to-torso spring in normal play. Looser lets the head whip
  // around more, which also feeds whiplash damage.
  float neck_linear_stiffness;
  float neck_linear_damping;
  float neck_angular_stiffness;
  float neck_angular_damping;
  // The same while knocked out (a floppier neck).
  float neck_knockout_linear_stiffness;
  float neck_knockout_linear_damping;
  float neck_knockout_angular_stiffness;
  float neck_knockout_angular_damping;

  // --- Balance ------------------------------------------------------------
  // Angular spring pulling the torso upright and toward the direction
  // being steered. Scaled by balance (0 when knocked out, frozen or
  // long airborne), so this sets how firmly a standing character
  // resists being tipped and how fast it rights itself.
  float stand_angular_stiffness;
  float stand_angular_damping;
  // Extra scale on that spring: normally, and while carrying
  // something (a held object needs a firmer stance).
  float stand_balance_scale;
  float stand_balance_scale_holding;
  // How far the character leans into acceleration and turns. (Further
  // scaled x1.2 outside hockey and x0.5 while carrying something.)
  float lean_amount;

  // --- Locomotion ---------------------------------------------------------
  // (Normal movement only; hockey and demo mode use their own fixed
  // values in spaz_node.cc.)

  // Most force the motor may use to spin the ball toward its target
  // speed: acceleration and hill-climbing power. Blends from the low
  // value at a standstill to the high one at gear_up_speed.
  float roller_motor_max_force_low_gear;
  float roller_motor_max_force_high_gear;
  // The same for the ball's vertical (turning in place) axis, which is
  // simply held still.
  float roller_motor_max_force_vertical;
  // Target ball spin for a full-stick walk, and how much more a full
  // run adds once up to speed. These set top speeds.
  float walk_speed;
  float run_speed_add;
  // Smoothed speed at which the run bonus is fully available. Lower
  // reaches top run speed sooner.
  float gear_up_speed;
  // Per-step smoothing of the speed used for gearing, when speeding up
  // and when slowing down (0-1; closer to 1 changes more slowly). The
  // 'up' value is most of what makes a run take time to build.
  float speed_smoothing_up;
  float speed_smoothing_down;
  // How strongly climbing slows the character and descending speeds it
  // up, per unit of vertical speed.
  float uphill_slow;
  float downhill_boost;
  // Brake motor between torso and ball: full strength when frozen or
  // dead, and brake_idle_scale of it when standing with the stick
  // released. Stops the character drifting and sliding.
  float brake_max_force;
  float brake_idle_scale;

  // --- Contacts -----------------------------------------------------------
  // Spring behind collisions of the head, torso and pelvis with
  // everything else. Softer lets them sink into what they hit.
  float core_contact_stiffness;
  float core_contact_damping;
  // The same for the roller ball on floors: the landing and standing
  // response. Low damping here makes landings bounce.
  float roller_floor_contact_stiffness;
  float roller_floor_contact_damping;
  // And for the roller ball against walls and steep surfaces (always
  // frictionless there).
  float roller_side_contact_stiffness;
  float roller_side_contact_damping;
  // Force pushing the ball away from steep terrain it touches, so
  // characters don't stick to walls.
  float roller_wall_kick_force;
  // Friction scale for every body except the roller ball (1 is the
  // surface's own friction). Sets how a fallen character slides.
  float body_friction_scale;

  // --- Knocked out or frozen (bg-limbs mode only) -------------------------
  // The old physics lets the ball vanish when a character goes down
  // and it lands on its legs; with no main-sim legs the ball stays as
  // a small, soft stand-in for them instead. The legacy set never
  // reads these.

  // Ball size while down, as a fraction of full size (smaller sits the
  // hips lower).
  float down_ball_size;
  // How far above the standing ball's bottom the down ball's bottom is
  // held.
  float down_ball_bottom_lift;
  // The down ball's floor contact spring, in place of
  // roller_floor_contact_*. Soft, so it cushions the drop and then
  // sinks under a lying body instead of propping the hips up.
  float down_ball_contact_stiffness;
  float down_ball_contact_damping;
  // Whether to lock the ball to the torso (full brakes) while knocked
  // out, instead of letting the ragdoll roll on it.
  bool down_ball_brakes;
};

// The original (main-sim limbs) physics. DO NOT CHANGE; see above.
inline constexpr SpazPhysicsTuning kSpazPhysicsTuningLegacyLimbs = {
    .head_density = 1.0f,
    .torso_density = 3.0f,
    .pelvis_density = 5.0f,
    .pelvis_mass_height = 0.16f,
    .roller_density = 0.1f,

    .roller_joint_stiffness = 1000.0f,
    .roller_joint_damping = 0.2f,
    .jump_push_distance = 0.3f,
    .jump_steps = 7,
    .jump_roller_stiffness_scale = 0.6f,
    .jump_roller_damping_scale = 0.2f,

    .pelvis_linear_stiffness = 300.0f,
    .pelvis_linear_damping = 20.0f,
    .pelvis_angular_stiffness = 1.5f,
    .pelvis_angular_damping = 0.06f,
    .neck_linear_stiffness = 500.0f,
    .neck_linear_damping = 1.0f,
    .neck_angular_stiffness = 13.0f,
    .neck_angular_damping = 0.8f,
    .neck_knockout_linear_stiffness = 400.0f,
    .neck_knockout_linear_damping = 1.0f,
    .neck_knockout_angular_stiffness = 5.0f,
    .neck_knockout_angular_damping = 0.3f,

    .stand_angular_stiffness = 180.0f,
    .stand_angular_damping = 3.0f,
    .stand_balance_scale = 0.6f,
    .stand_balance_scale_holding = 0.9f,
    .lean_amount = 0.4f,

    .roller_motor_max_force_low_gear = 15.0f,
    .roller_motor_max_force_high_gear = 15.0f,
    .roller_motor_max_force_vertical = 500.0f,
    .walk_speed = 7.68f,
    .run_speed_add = 15.0f,
    .gear_up_speed = 7.0f,
    .speed_smoothing_up = 0.985f,
    .speed_smoothing_down = 0.94f,
    .uphill_slow = 0.2f,
    .downhill_boost = 0.1f,
    .brake_max_force = 10.0f,
    .brake_idle_scale = 0.4f,

    .core_contact_stiffness = 5000.0f,
    .core_contact_damping = 0.001f,
    .roller_floor_contact_stiffness = 7000.0f,
    .roller_floor_contact_damping = 7.0f,
    .roller_side_contact_stiffness = 800.0f,
    .roller_side_contact_damping = 0.001f,
    .roller_wall_kick_force = 100.0f,
    .body_friction_scale = 0.3f,

    // (Unused: the ball vanishes and the main-sim legs take over.)
    .down_ball_size = 0.0f,
    .down_ball_bottom_lift = 0.0f,
    .down_ball_contact_stiffness = 0.0f,
    .down_ball_contact_damping = 0.0f,
    .down_ball_brakes = false,
};

// The current (bg-dynamics limbs) physics. Tune these. A trailing
// comment gives the legacy value wherever the two differ.
inline constexpr SpazPhysicsTuning kSpazPhysicsTuningBgLimbs = {
    // The core carries the limbs' mass so the character weighs what it
    // used to (1.392 in all): the arms' 0.109 as torso density, the
    // legs' and toes' 0.104 as a taller pelvis mass box.
    .head_density = 1.0f,
    .torso_density = 3.65f,  // Legacy: 3.0.
    .pelvis_density = 5.0f,
    .pelvis_mass_height = 0.264f,  // Legacy: 0.16.
    .roller_density = 0.1f,

    .roller_joint_stiffness = 1000.0f,
    .roller_joint_damping = 0.2f,
    .jump_push_distance = 0.3f,
    .jump_steps = 7,
    .jump_roller_stiffness_scale = 0.6f,
    .jump_roller_damping_scale = 0.2f,

    .pelvis_linear_stiffness = 300.0f,
    .pelvis_linear_damping = 20.0f,
    .pelvis_angular_stiffness = 1.5f,
    .pelvis_angular_damping = 0.06f,
    .neck_linear_stiffness = 500.0f,
    .neck_linear_damping = 1.0f,
    .neck_angular_stiffness = 13.0f,
    .neck_angular_damping = 0.8f,
    .neck_knockout_linear_stiffness = 400.0f,
    .neck_knockout_linear_damping = 1.0f,
    .neck_knockout_angular_stiffness = 5.0f,
    .neck_knockout_angular_damping = 0.3f,

    .stand_angular_stiffness = 180.0f,
    .stand_angular_damping = 3.0f,
    .stand_balance_scale = 0.6f,
    .stand_balance_scale_holding = 0.9f,
    .lean_amount = 0.4f,

    .roller_motor_max_force_low_gear = 15.0f,
    .roller_motor_max_force_high_gear = 15.0f,
    .roller_motor_max_force_vertical = 500.0f,
    .walk_speed = 7.68f,
    .run_speed_add = 15.0f,
    .gear_up_speed = 7.0f,
    .speed_smoothing_up = 0.985f,
    .speed_smoothing_down = 0.94f,
    .uphill_slow = 0.2f,
    .downhill_boost = 0.1f,
    .brake_max_force = 10.0f,
    .brake_idle_scale = 0.4f,

    .core_contact_stiffness = 5000.0f,
    .core_contact_damping = 0.001f,
    .roller_floor_contact_stiffness = 7000.0f,
    .roller_floor_contact_damping = 7.0f,
    .roller_side_contact_stiffness = 800.0f,
    .roller_side_contact_damping = 0.001f,
    .roller_wall_kick_force = 100.0f,
    .body_friction_scale = 0.3f,

    // 0.4 is a ball of radius 0.138; 0.108 is where a 0.6 ball with no
    // offset sat (the first tuning that felt right). Brakes while down
    // were tried and set aside (the free ball read better).
    .down_ball_size = 0.4f,
    .down_ball_bottom_lift = 0.108f,
    .down_ball_contact_stiffness = 400.0f,
    .down_ball_contact_damping = 2.0f,
    .down_ball_brakes = false,
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_NODE_SPAZ_PHYSICS_TUNING_H_
