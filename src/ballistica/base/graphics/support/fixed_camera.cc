// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/fixed_camera.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>
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
  const ViewPose pose = ViewPose_();
  const Vector3f& position = pose.position;
  Vector3f up = pose.up;

  // Aim at our target, turned by however far our shake has us off it
  // (left/right about our own up, then up/down about our own right, so
  // it wobbles the same on screen whichever way we face).
  StepShake_(frame_def);
  Vector3f target = target_;
  if (shake_yaw_ != 0.0f || shake_pitch_ != 0.0f) {
    const float kDegToRad = kPi / 180.0f;
    Vector3f dir = RotateAbout_(target_ - position, up, shake_yaw_ * kDegToRad);
    Vector3f right = Vector3f::Cross(dir, up);
    if (right.LengthSquared() > 1.0e-12f) {
      right = right.Normalized();
      const float pitch = shake_pitch_ * kDegToRad;
      dir = RotateAbout_(dir, right, pitch);
      up = RotateAbout_(up, right, pitch);
    }
    target = position + dir;
  }

  // Clip to just what we're told is there, from exactly where we're
  // looking from and toward. Clip planes go by depth (along our aim),
  // and a sphere spans exactly its center's depth plus or minus its
  // radius.
  float near_clip = near_clip_;
  float far_clip = far_clip_;
  if (!clip_spheres_.empty()) {
    Vector3f aim = target - position;
    aim = aim.LengthSquared() > 1.0e-12f ? aim.Normalized()
                                         : Vector3f(0.0f, 0.0f, -1.0f);
    float nearest{std::numeric_limits<float>::max()};
    float deepest{std::numeric_limits<float>::lowest()};
    for (const ClipSphere& s : clip_spheres_) {
      const float depth = Vector3f::Dot(s.center - position, aim);
      nearest = std::min(nearest, depth - s.radius);
      deepest = std::max(deepest, depth + s.radius);
    }
    // (A hair of slack for rounding: a mesh can touch its bounds.)
    constexpr float kRounding{1.001f};
    far_clip = std::max(deepest * kRounding, 0.001f);
    near_clip = std::max(nearest / kRounding, far_clip * clip_min_near_ratio_);
  }

  for (RenderPass* pass : passes) {
    pass->SetCamera(position, target, up, near_clip, far_clip,
                    -1.0f,  // Auto x fov.
                    field_of_view_y, false, 0.0f, 0.0f, 0.0f,
                    0.0f,  // Not using tangent fovs.
                    area_of_interest_points);
  }
}

auto FixedCamera::RotateAbout_(const Vector3f& v, const Vector3f& axis,
                               float angle) -> Vector3f {
  // Rodrigues' rotation formula (axis must be unit length).
  const float c = cosf(angle);
  const float s = sinf(angle);
  return v * c + Vector3f::Cross(axis, v) * s
         + axis * (Vector3f::Dot(axis, v) * (1.0f - c));
}

auto FixedCamera::ViewPose_() const -> ViewPose {
  // Our unswung pose: up is world up's share across our aim (as a
  // camera given world up as up would be), or, looking straight up or
  // down, whatever's handy.
  const Vector3f world_up{0.0f, 1.0f, 0.0f};
  Vector3f offset = position_ - target_;
  const float dist = offset.Length();
  if (dist < 0.0001f) {
    return {position_, world_up};
  }
  const Vector3f forward = offset * (-1.0f / dist);
  Vector3f right = Vector3f::Cross(forward, world_up);
  right = right.LengthSquared() > 1.0e-12f ? right.Normalized()
                                           : Vector3f(1.0f, 0.0f, 0.0f);
  Vector3f up = Vector3f::Cross(right, forward);
  if (tilt_orbit_ == 0.0f) {
    return {position_, up};
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
    return {position_, up};
  }

  // Swing around our target, up/down first: about our right (which is
  // level), so it changes our elevation over the target. Our up turns
  // with us, so even swinging over the top nothing flips. (Turning
  // about right by a positive angle lowers us, hence the negative.)
  offset = RotateAbout_(offset, right, -pitch);
  up = RotateAbout_(up, right, -pitch);

  // Then left/right about world up, so the world stays upright on
  // screen. Near straight above or below the target that turn would
  // just roll the view, so it fades out with our resulting elevation:
  // full when level, none looking straight up or down.
  const float level = sqrtf(offset.x * offset.x + offset.z * offset.z) / dist;
  const float level_yaw = yaw * level;
  if (level_yaw != 0.0f) {
    offset = RotateAbout_(offset, world_up, level_yaw);
    up = RotateAbout_(up, world_up, level_yaw);
  }
  return {target_ + offset, up};
}

void FixedCamera::SetClipSpheres(std::vector<ClipSphere> spheres,
                                 float min_near_ratio) {
  assert(min_near_ratio > 0.0f && min_near_ratio < 1.0f);
  clip_spheres_ = std::move(spheres);
  clip_min_near_ratio_ = min_near_ratio;
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
