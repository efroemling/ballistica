// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_FIXED_CAMERA_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_FIXED_CAMERA_H_

#include "ballistica/base/graphics/support/camera.h"
#include "ballistica/base/graphics/support/depth_of_field.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// A camera that sits where it is put and looks where it is pointed.
///
/// For views whose owner knows what it wants shown, such as a ui
/// viewer framing a character. Areas of interest registered with it
/// affect nothing, nor do mode or bounds requests from the world.
class FixedCamera : public Camera {
 public:
  FixedCamera();
  ~FixedCamera() override;

  void ApplyToFrameDef(FrameDef* frame_def) override;
  auto GetPosition() const -> Vector3f override { return position_; }

  void set_position(const Vector3f& val) { position_ = val; }
  auto target() const -> const Vector3f& { return target_; }
  void set_target(const Vector3f& val) { target_ = val; }

  /// Vertical field of view in degrees; horizontal follows from the
  /// shape of what we're drawing to. So whatever we're pointed at
  /// takes up the same share of the picture's height whatever shape
  /// the picture is.
  auto field_of_view_y() const -> float { return field_of_view_y_; }
  void set_field_of_view_y(float val) { field_of_view_y_ = val; }

  /// The least horizontal field of view we'll go to, in degrees; 0 for
  /// no such limit. When a picture is narrow enough that holding our
  /// vertical field of view would see less across than this, we see
  /// this much across and more up and down instead, so that what we're
  /// pointed at gets smaller rather than cut off at the sides.
  auto min_field_of_view_x() const -> float { return min_field_of_view_x_; }
  void set_min_field_of_view_x(float val) { min_field_of_view_x_ = val; }

  /// Nothing nearer than near-clip or farther than far-clip gets
  /// drawn. Depth precision is spread over the span between them, so
  /// keep it no wider than the scene needs.
  auto near_clip() const -> float { return near_clip_; }
  auto far_clip() const -> float { return far_clip_; }
  void SetClip(float near_clip, float far_clip);

  /// What is in focus (where the view is drawn at a quality that has
  /// depth of field). Everything, unless set otherwise; nothing about
  /// what we show moves on its own, so there is nothing for focus to
  /// follow.
  auto depth_of_field() const -> const DepthOfField& { return depth_of_field_; }
  void set_depth_of_field(const DepthOfField& val) { depth_of_field_ = val; }

  /// Hand-held style shake: we stay where we are but our aim wobbles
  /// on a damped spring (left/right and up/down), poked with a random
  /// kick every so often. Strength is the size of a kick (degrees per
  /// second of spin; 0 for no shake); stiffness and damping shape the
  /// spring; kicks land a random interval apart between the two poke
  /// intervals (seconds). Still while camera shake is disabled.
  void SetShake(float strength, float stiffness, float damping,
                float poke_interval_min, float poke_interval_max);

  /// Swing around our target as the device itself turns (from its gyro;
  /// see Input::tilt()), so that turning the device turns our view of
  /// what we're pointed at with it. Amount scales the turn: 1 turns us
  /// as far as the device turned, 0 (the default) not at all. Like the
  /// ui's tilt, the turn eases back to center over a couple of seconds
  /// once the device holds still, and is nothing on devices without a
  /// gyro or while camera gyro is disabled.
  auto tilt_orbit() const -> float { return tilt_orbit_; }
  void set_tilt_orbit(float val) { tilt_orbit_ = val; }

 private:
  void StepShake_(FrameDef* frame_def);

  /// Our position swung around our target by the device's turn (see
  /// set_tilt_orbit()).
  auto TiltedPosition_() const -> Vector3f;

  float tilt_orbit_{};

  // Shake settings.
  float shake_strength_{};
  float shake_stiffness_{30.0f};
  float shake_damping_{2.0f};
  float shake_poke_interval_min_{0.5f};
  float shake_poke_interval_max_{1.0f};

  // Shake state (angles in degrees; velocities in degrees per second).
  float shake_yaw_{};
  float shake_pitch_{};
  float shake_yaw_vel_{};
  float shake_pitch_vel_{};
  double shake_time_{-1.0};
  double shake_next_poke_time_{};
  double shake_step_accum_{};
  DepthOfField depth_of_field_{.mode = DepthOfField::Mode::kOff};
  float field_of_view_y_{30.0f};
  float min_field_of_view_x_{};
  float near_clip_{1.0f};
  float far_clip_{100.0f};
  Vector3f position_{0.0f, 1.0f, 5.0f};
  Vector3f target_{0.0f, 1.0f, 0.0f};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_FIXED_CAMERA_H_
