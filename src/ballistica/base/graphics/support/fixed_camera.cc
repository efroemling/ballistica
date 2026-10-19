// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/fixed_camera.h"

#include <algorithm>
#include <cmath>
#include <vector>

#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/graphics/support/frame_def_view.h"
#include "ballistica/base/input/input.h"
#include "ballistica/shared/math/random.h"

namespace ballistica::base {

FixedCamera::FixedCamera() = default;
FixedCamera::~FixedCamera() = default;

void FixedCamera::SetClip(float near_clip, float far_clip) {
  assert(near_clip > 0.0f && far_clip > near_clip);
  near_clip_ = near_clip;
  far_clip_ = far_clip;
}

void FixedCamera::ApplyToFrameDef(FrameDef* frame_def) {
  // What we're pointed at is the one thing of interest we know of.
  std::vector<Vector3f> area_of_interest_points{target_};

  frame_def->current_view()->set_depth_of_field(depth_of_field_);

  RenderPass* passes[] = {frame_def->beauty_pass(), frame_def->beauty_pass_bg(),
                          frame_def->overlay_3d_pass(), frame_def->blit_pass()};

  // We hold our vertical field of view, so what we see across follows
  // from the shape of what we draw to; unless that would be less
  // across than our minimum, in which case we hold that and see more
  // up and down instead.
  float field_of_view_y = field_of_view_y_;
  if (min_field_of_view_x_ > 0.0f) {
    const float aspect = passes[0]->GetPhysicalAspectRatio();
    const float kDegToRad = kPi / 180.0f;
    const float tan_half_x_min = tanf(0.5f * min_field_of_view_x_ * kDegToRad);
    const float tan_half_y = tanf(0.5f * field_of_view_y_ * kDegToRad);
    if (aspect > 0.0f && tan_half_y * aspect < tan_half_x_min) {
      field_of_view_y =
          std::min(170.0f, 2.0f * atanf(tan_half_x_min / aspect) / kDegToRad);
    }
  }

  // Swung around our target by however far the device has turned.
  const Vector3f position = TiltedPosition_();

  // Aim at our target, turned by however far our shake has us off it
  // (left/right about world up, then up/down about our right).
  StepShake_(frame_def);
  Vector3f target = target_;
  if (shake_yaw_ != 0.0f || shake_pitch_ != 0.0f) {
    const float kDegToRad = kPi / 180.0f;
    Vector3f dir = target_ - position;
    const float yaw = shake_yaw_ * kDegToRad;
    const float cy = cosf(yaw);
    const float sy = sinf(yaw);
    dir = Vector3f(dir.x * cy + dir.z * sy, dir.y, -dir.x * sy + dir.z * cy);
    Vector3f right = Vector3f::Cross(dir, Vector3f(0.0f, 1.0f, 0.0f));
    if (right.LengthSquared() > 0.000001f) {
      right = right.Normalized();
      const float pitch = shake_pitch_ * kDegToRad;
      const float cp = cosf(pitch);
      const float sp = sinf(pitch);
      // Rodrigues rotation of dir about right (dir is perpendicular to
      // right, so the dot term drops out).
      dir = dir * cp + Vector3f::Cross(right, dir) * sp;
    }
    target = position + dir;
  }

  for (RenderPass* pass : passes) {
    pass->SetCamera(position, target, Vector3f(0.0f, 1.0f, 0.0f), near_clip_,
                    far_clip_,
                    -1.0f,  // Auto x fov.
                    field_of_view_y, false, 0.0f, 0.0f, 0.0f,
                    0.0f,  // Not using tangent fovs.
                    area_of_interest_points);
  }
}

auto FixedCamera::TiltedPosition_() const -> Vector3f {
  if (tilt_orbit_ == 0.0f) {
    return position_;
  }

  // Input's tilt is the gyro's turn rate (radians per second) summed
  // at 3x per 60hz frame, so it runs about 180 per radian the device
  // has turned. Its x is a lean up/down and its y a lean left/right.
  // (It also eases back to zero on its own, which is what recenters
  // us.) A positive x lean wants us lower, so pitch takes its negative
  // (verified on device).
  const Vector3f tilt = g_base->input->tilt();
  constexpr float kTiltToRad{1.0f / 180.0f};
  const float yaw = tilt.y * kTiltToRad * tilt_orbit_;
  const float pitch = -tilt.x * kTiltToRad * tilt_orbit_;
  if (yaw == 0.0f && pitch == 0.0f) {
    return position_;
  }

  Vector3f offset = position_ - target_;
  const float dist = offset.Length();
  if (dist < 0.0001f) {
    return position_;
  }

  // Left/right: around world up through our target.
  const float cy = cosf(yaw);
  const float sy = sinf(yaw);
  offset = Vector3f(offset.x * cy + offset.z * sy, offset.y,
                    -offset.x * sy + offset.z * cy);

  // Up/down: change our elevation over our target, stopping short of
  // straight above or below it (where which way is up would flip).
  const float horizontal = sqrtf(offset.x * offset.x + offset.z * offset.z);
  if (horizontal < 0.0001f) {
    return target_ + offset;
  }
  const float kMaxElevation{80.0f * kPi / 180.0f};
  const float elevation = std::clamp(atan2f(offset.y, horizontal) + pitch,
                                     -kMaxElevation, kMaxElevation);
  const float out = cosf(elevation) * dist / horizontal;
  return target_
         + Vector3f(offset.x * out, sinf(elevation) * dist, offset.z * out);
}

void FixedCamera::SetShake(float strength, float stiffness, float damping,
                           float poke_interval_min, float poke_interval_max) {
  shake_strength_ = strength;
  shake_stiffness_ = stiffness;
  shake_damping_ = damping;
  shake_poke_interval_min_ = poke_interval_min;
  shake_poke_interval_max_ = poke_interval_max;
}

void FixedCamera::StepShake_(FrameDef* frame_def) {
  const double now =
      static_cast<double>(frame_def->display_time_microsecs()) / 1000000.0;

  // Settled and still when off.
  if (shake_strength_ <= 0.0f || g_base->graphics->camera_shake_disabled()) {
    shake_yaw_ = shake_pitch_ = shake_yaw_vel_ = shake_pitch_vel_ = 0.0f;
    shake_time_ = -1.0;
    return;
  }

  // Starting (or resuming after being off or unseen for a while):
  // just note the time.
  if (shake_time_ < 0.0 || now - shake_time_ > 0.25 || now < shake_time_) {
    shake_time_ = now;
    shake_step_accum_ = 0.0;
    shake_next_poke_time_ = now;
    return;
  }

  // Step the spring at a fixed rate so it behaves the same at any
  // frame rate.
  constexpr double kStep{1.0 / 240.0};
  shake_step_accum_ += now - shake_time_;
  shake_time_ = now;
  double step_time = now - shake_step_accum_;
  while (shake_step_accum_ >= kStep) {
    shake_step_accum_ -= kStep;
    step_time += kStep;

    // Every so often, a kick in a random direction.
    if (step_time >= shake_next_poke_time_) {
      const float angle = RandomFloat() * 2.0f * kPi;
      const float amount = shake_strength_ * (0.5f + 0.5f * RandomFloat());
      shake_yaw_vel_ += cosf(angle) * amount;
      shake_pitch_vel_ += sinf(angle) * amount;
      shake_next_poke_time_ =
          step_time + shake_poke_interval_min_
          + RandomFloat()
                * (shake_poke_interval_max_ - shake_poke_interval_min_);
    }

    // Semi-implicit Euler: stable for a stiff spring at this step.
    const auto h = static_cast<float>(kStep);
    shake_yaw_vel_ +=
        (-shake_stiffness_ * shake_yaw_ - shake_damping_ * shake_yaw_vel_) * h;
    shake_pitch_vel_ +=
        (-shake_stiffness_ * shake_pitch_ - shake_damping_ * shake_pitch_vel_)
        * h;
    shake_yaw_ += shake_yaw_vel_ * h;
    shake_pitch_ += shake_pitch_vel_ * h;
  }
}

}  // namespace ballistica::base
