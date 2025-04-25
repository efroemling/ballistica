// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/graphics/support/camera.h"

#include <algorithm>

#include "ballistica/base/audio/audio.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/graphics_vr.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/support/area_of_interest.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/math/random.h"
#include "ode/ode_collision_util.h"

namespace ballistica::base {

const float kCameraOffsetX = 0.0f;
const float kCameraOffsetY = -8.3f;
const float kCameraOffsetZ = -7.4f;
const float kMaxFOV = 150.0f;
const float kPanMax = 9.0f;
const float kPanMin = -9.0f;

Camera::Camera()
    : lock_panning_(g_core->vr_mode()),
      pan_speed_scale_(g_core->vr_mode() ? 0.3f : 1.0f) {}

Camera::~Camera() = default;

#define DEG2RAD(a) (0.0174532925f * (a))

static auto DotProduct(const dVector3 v1, const dVector3 v2) -> float {
  return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
}

static void ProjectPointOnPlane(dVector3 dst, const dVector3 p,
                                const dVector3 normal) {
  float d;
  dVector3 n;
  float inv_denom;
  inv_denom = 1.0F / DotProduct(normal, normal);
  d = DotProduct(normal, p) * inv_denom;
  n[0] = normal[0] * inv_denom;
  n[1] = normal[1] * inv_denom;
  n[2] = normal[2] * inv_denom;
  dst[0] = p[0] - d * n[0];
  dst[1] = p[1] - d * n[1];
  dst[2] = p[2] - d * n[2];
}

void PerpendicularVector(dVector3 dst, const dVector3 src) {
  int pos;
  int i;
  float minelem = 1.0f;
  dVector3 tempvec;

  // Find the smallest magnitude axially aligned vector.
  for (pos = 0, i = 0; i < 3; i++) {
    if (std::abs(src[i]) < minelem) {
      pos = i;
      minelem = std::abs(src[i]);
    }
  }
  tempvec[0] = tempvec[1] = tempvec[2] = 0.0f;
  tempvec[pos] = 1.0f;

  // Project the point onto the plane defined by src.
  ProjectPointOnPlane(dst, tempvec, src);

  // Normalize the result.
  dNormalize3(dst);
}

static void MatrixMultiply(float in1[3][3], float in2[3][3], float out[3][3]) {
  out[0][0] =
      in1[0][0] * in2[0][0] + in1[0][1] * in2[1][0] + in1[0][2] * in2[2][0];
  out[0][1] =
      in1[0][0] * in2[0][1] + in1[0][1] * in2[1][1] + in1[0][2] * in2[2][1];
  out[0][2] =
      in1[0][0] * in2[0][2] + in1[0][1] * in2[1][2] + in1[0][2] * in2[2][2];
  out[1][0] =
      in1[1][0] * in2[0][0] + in1[1][1] * in2[1][0] + in1[1][2] * in2[2][0];
  out[1][1] =
      in1[1][0] * in2[0][1] + in1[1][1] * in2[1][1] + in1[1][2] * in2[2][1];
  out[1][2] =
      in1[1][0] * in2[0][2] + in1[1][1] * in2[1][2] + in1[1][2] * in2[2][2];
  out[2][0] =
      in1[2][0] * in2[0][0] + in1[2][1] * in2[1][0] + in1[2][2] * in2[2][0];
  out[2][1] =
      in1[2][0] * in2[0][1] + in1[2][1] * in2[1][1] + in1[2][2] * in2[2][1];
  out[2][2] =
      in1[2][0] * in2[0][2] + in1[2][1] * in2[1][2] + in1[2][2] * in2[2][2];
}

static void Cross(const dVector3 v1, const dVector3 v2, dVector3 cross) {
  cross[0] = v1[1] * v2[2] - v1[2] * v2[1];
  cross[1] = v1[2] * v2[0] - v1[0] * v2[2];
  cross[2] = v1[0] * v2[1] - v1[1] * v2[0];
}

static void RotatePointAroundVector(dVector3 dst, const dVector3 dir,
                                    const dVector3 point, float degrees) {
  float m[3][3];
  float im[3][3];
  float zrot[3][3];
  float tmpmat[3][3];
  float rot[3][3];
  int i;
  dVector3 vr, vup, vf;
  float rad;

  vf[0] = dir[0];
  vf[1] = dir[1];
  vf[2] = dir[2];

  PerpendicularVector(vr, dir);
  Cross(vr, vf, vup);

  m[0][0] = vr[0];
  m[1][0] = vr[1];
  m[2][0] = vr[2];

  m[0][1] = vup[0];
  m[1][1] = vup[1];
  m[2][1] = vup[2];

  m[0][2] = vf[0];
  m[1][2] = vf[1];
  m[2][2] = vf[2];

  memcpy(im, m, sizeof(im));

  im[0][1] = m[1][0];
  im[0][2] = m[2][0];
  im[1][0] = m[0][1];
  im[1][2] = m[2][1];
  im[2][0] = m[0][2];
  im[2][1] = m[1][2];

  memset(zrot, 0, sizeof(zrot));
  zrot[0][0] = zrot[1][1] = zrot[2][2] = 1.0F;

  rad = DEG2RAD(degrees);
  zrot[0][0] = cosf(rad);
  zrot[0][1] = sinf(rad);
  zrot[1][0] = -sinf(rad);
  zrot[1][1] = cosf(rad);

  MatrixMultiply(m, zrot, tmpmat);
  MatrixMultiply(tmpmat, im, rot);

  for (i = 0; i < 3; i++) {
    dst[i] = rot[i][0] * point[0] + rot[i][1] * point[1] + rot[i][2] * point[2];
  }
}

void Camera::Shake(float amount) { shake_amount_ += 0.12f * amount; }

void Camera::UpdateManualMode() {
  panning_ = orbiting_ = trucking_ = rolling_ = false;
  if (!manual_) {
    return;
  }
  if ((alt_down_ || cmd_down_) && mouse_middle_down_ && mouse_left_down_) {
    trucking_ = true;
  } else if (ctrl_down_ && mouse_left_down_) {
    panning_ = true;
  } else if ((alt_down_ || cmd_down_) && mouse_left_down_) {
    orbiting_ = true;
  } else if ((alt_down_ || cmd_down_) && mouse_right_down_) {
    rolling_ = true;
  }
}

void Camera::UpdatePosition() {
  // We re-calc our area-of-interest-points here.
  area_of_interest_points_.clear();

  // In non-manual modes, update our position and target automatically.
  if (manual_) {
    area_of_interest_points_.emplace_back(target_.x, target_.y, target_.z);
  } else {
    // Non-manual.

    // If we're orbiting, just put a single AOI point in the middle.
    if (mode_ == CameraMode::kOrbit) {
      target_radius_ = 11;
      float dist = 28;
      float dist_v = 4.5f;
      float altitude = 12;
      float world_offset_z = -3;
      SetTarget(0, dist_v, world_offset_z);
      SetPosition(dist * sinf(heading_), altitude,
                  dist * cosf(heading_) + world_offset_z);
      area_of_interest_points_.emplace_back(target_.x, target_.y, target_.z);

      have_real_areas_of_interest_ = false;
    } else {
      // Follow mode.
      if (explicit_bool(true)) {
        float lr_jitter;
        {
          if (g_core->vr_mode()) {
            lr_jitter = 0.0f;
          } else {
            lr_jitter =
                sinf(static_cast<float>(g_core->AppTimeMillisecs()) / 108.0f)
                    * 0.4f
                + sinf(static_cast<float>(g_core->AppTimeMillisecs()) / 268.0f)
                      * 1.0f;
            lr_jitter *= 0.05f;
          }
        }

        if (!smooth_next_frame_ || lock_panning_) {
          pan_pos_ = 0.0f;
          pan_speed_ = 0.0f;
          pan_target_ = 0.0f;
        }

        SetPosition(pan_pos_ + lr_jitter, 20 + 0.5f, 22);
        SetTarget(0, 0, 0);  // Default.

        float x_min, y_min, z_min, x_max, y_max, z_max;

        if (!areas_of_interest_.empty()) {
          float angle_x_min = 0.0f, angle_x_max = 0.0f, angle_y_min = 0.0f,
                angle_y_max = 0.0f;
          float center_x, center_y, center_z;

          x_min = y_min = z_min = 99999;
          x_max = y_max = z_max = -99999;

          // Find the center of all AOI points (clamped to our bounds plus their
          // radius as a buffer)
          for (auto&& i : areas_of_interest_) {
            float x_clamped, y_clamped, z_clamped;
            float diameter = i.radius() * 2.0f;

            if (diameter
                > (area_of_interest_bounds_[3] - area_of_interest_bounds_[0])) {
              x_clamped =
                  0.5f
                  * (area_of_interest_bounds_[3] + area_of_interest_bounds_[0]);
            } else {
              x_clamped =
                  std::min(area_of_interest_bounds_[3] - i.radius(),
                           std::max(area_of_interest_bounds_[0] + i.radius(),
                                    i.position().x));
            }

            if (diameter
                > (area_of_interest_bounds_[4] - area_of_interest_bounds_[1])) {
              y_clamped =
                  0.5f
                  * (area_of_interest_bounds_[4] + area_of_interest_bounds_[1]);
            } else {
              y_clamped =
                  std::min(area_of_interest_bounds_[4] - i.radius(),
                           std::max(area_of_interest_bounds_[1] + i.radius(),
                                    i.position().y));
            }

            if (diameter
                > (area_of_interest_bounds_[5] - area_of_interest_bounds_[2])) {
              z_clamped = 0.5f
                          * ((area_of_interest_bounds_[5]
                              + area_of_interest_bounds_[2]));
            } else {
              z_clamped =
                  std::min(area_of_interest_bounds_[5] - i.radius(),
                           std::max(area_of_interest_bounds_[2] + i.radius(),
                                    i.position().z));
            }

            x_min = std::min(x_min, x_clamped - i.radius());
            y_min = std::min(y_min, y_clamped - i.radius());
            z_min = std::min(z_min, z_clamped - i.radius());
            x_max = std::max(x_max, x_clamped - i.radius());
            y_max = std::max(y_max, y_clamped - i.radius());
            z_max = std::max(z_max, z_clamped - i.radius());

            x_min = std::min(x_min, x_clamped + i.radius());
            y_min = std::min(y_min, y_clamped + i.radius());
            z_min = std::min(z_min, z_clamped + i.radius());
            x_max = std::max(x_max, x_clamped + i.radius());
            y_max = std::max(y_max, y_clamped + i.radius());
            z_max = std::max(z_max, z_clamped + i.radius());
          }

          center_x = 0.5f * (x_min + x_max);
          center_y = 0.5f * (y_min + y_max);
          center_z = 0.5f * (z_min + z_max);

          // As a starting point, aim at the center of these.
          SetTarget(center_x, center_y, center_z);

          // Ok, now have a cam position point and base target point.
          // now for each point, calc its horizontal and vertical angle from the
          // camera's forward vector.
          Vector3f cam_forward(target_.x - position_.x, target_.y - position_.y,
                               target_.z - position_.z);
          cam_forward.Normalize();
          Vector3f cam_side = Vector3f::Cross(cam_forward, Vector3f(0, 1, 0));
          cam_side.Normalize();
          Vector3f cam_up = Vector3f::Cross(cam_side, cam_forward);
          cam_up.Normalize();

          int num = 0;

          for (auto&& i : areas_of_interest_) {
            // If this point is used for focusing, add it to that list.
            if (i.in_focus()) {
              // Get the AOI center point clamped to AOI bounds (not taking
              // radius into account)
              float x_clamped_focus = std::min(
                  area_of_interest_bounds_[3],
                  std::max(area_of_interest_bounds_[0], i.position().x));
              float y_clamped_focus = std::min(
                  area_of_interest_bounds_[4],
                  std::max(area_of_interest_bounds_[1], i.position().y));
              float z_clamped_focus = std::min(
                  area_of_interest_bounds_[5],
                  std::max(area_of_interest_bounds_[2], i.position().z));
              area_of_interest_points_.emplace_back(
                  x_clamped_focus, y_clamped_focus, z_clamped_focus);
            }

            // Now, for camera aiming purposes, add some of their velocity
            // and clamp to the bounds, taking their radius into account. if
            // our AOI sphere is bigger than a given dimension, center it;
            // otherwise clamp to the box inset by our radius.
            float x_clamped, y_clamped, z_clamped, x_mirrored_clamped;
            float diameter = i.radius() * 2.0f;

            if (diameter
                > (area_of_interest_bounds_[3] - area_of_interest_bounds_[0])) {
              x_clamped =
                  0.5f
                  * (area_of_interest_bounds_[3] + area_of_interest_bounds_[0]);
            } else {
              x_clamped =
                  std::min(area_of_interest_bounds_[3] - i.radius(),
                           std::max(area_of_interest_bounds_[0] + i.radius(),
                                    i.position().x));
            }

            if (diameter
                > (area_of_interest_bounds_[4] - area_of_interest_bounds_[1])) {
              y_clamped =
                  0.5f
                  * (area_of_interest_bounds_[4] + area_of_interest_bounds_[1]);
            } else {
              y_clamped =
                  std::min(area_of_interest_bounds_[4] - i.radius(),
                           std::max(area_of_interest_bounds_[1] + i.radius(),
                                    i.position().y));
            }

            if (diameter
                > (area_of_interest_bounds_[5] - area_of_interest_bounds_[2])) {
              z_clamped = 0.5f
                          * ((area_of_interest_bounds_[5]
                              + area_of_interest_bounds_[2]));
            } else {
              z_clamped =
                  std::min(area_of_interest_bounds_[5] - i.radius(),
                           std::max(area_of_interest_bounds_[2] + i.radius(),
                                    i.position().z));
            }

            // Let's also do a version mirrored across the camera's x
            // coordinate (adding this to our tracked point set causes us
            // zoom out instead of rotating generally)
            float x_mirrored = position_.x - (i.position().x - position_.x);
            if (diameter
                > (area_of_interest_bounds_[3] - area_of_interest_bounds_[0])) {
              x_mirrored_clamped =
                  0.5f
                  * (area_of_interest_bounds_[3] + area_of_interest_bounds_[0]);
            } else {
              x_mirrored_clamped =
                  std::min(area_of_interest_bounds_[3] - i.radius(),
                           std::max(area_of_interest_bounds_[0] + i.radius(),
                                    x_mirrored));
            }

            Vector3f corner_offs = (cam_side + cam_up) * i.radius();

            for (int sample = 0; sample < 2; sample++) {
              Vector3f to_point{x_clamped - position_.x,
                                y_clamped - position_.y,
                                z_clamped - position_.z};

              // For sample 0, subtract AOI radius in camera-space x and y.
              // For sample 1, add them. this way we should get the whole
              // sphere.
              if (sample == 0) {
                to_point -= corner_offs;
              } else if (sample == 1) {
                to_point += corner_offs;
              } else if (sample == 2) {
                to_point.v[0] = x_mirrored_clamped - position_.x;
              }

              to_point.Normalize();
              float up_amt = Vector3f::Dot(to_point, cam_up);
              float side_amt = Vector3f::Dot(to_point, cam_side);

              // Get the vector from the cam to this point, subtract out the
              // component parallel to the camera's up vector, and then measure
              // the angle to the camera's forward vector.

              float angle_x, angle_y;

              if (std::abs(up_amt) < 0.001f) {
                angle_y = 0.0f;
              } else {
                angle_y = Vector3f::Angle(to_point - cam_side * side_amt,
                                          cam_forward);
              }
              if (std::abs(side_amt) < 0.001f) {
                angle_x = 0.0f;
              } else {
                angle_x =
                    Vector3f::Angle(to_point - cam_up * up_amt, cam_forward);
              }
              if (side_amt > 0) {
                angle_x *= -1;
              }
              if (up_amt > 0) {
                angle_y *= -1;
              }
              if (num == 0) {
                angle_x_min = angle_x_max = angle_x;
                angle_y_min = angle_y_max = angle_y;
              } else {
                angle_x_min = std::min(angle_x_min, angle_x);
                angle_x_max = std::max(angle_x_max, angle_x);
                angle_y_min = std::min(angle_y_min, angle_y);
                angle_y_max = std::max(angle_y_max, angle_y);
              }
              num++;
            }
          }

          float turn_angle_x = 0.5f * (angle_x_min + angle_x_max);
          float turn_angle_y = 0.5f * (angle_y_min + angle_y_max);

          // Get cam target relative to the camera, rotate it on cam left/right,
          // and set it.
          Vector3f p(target_.x - position_.x, target_.y - position_.y,
                     target_.z - position_.z);
          p = Matrix44fRotate(cam_up, turn_angle_x) * p;
          SetTarget(position_.x + p.v[0], position_.y + p.v[1],
                    position_.z + p.v[2]);

          // Now the same for camera up/down.
          // Note: technically we should recalc angles since we just rotated,
          // but this should be close enough.
          Vector3f p2(target_.x - position_.x, target_.y - position_.y,
                      target_.z - position_.z);
          p2 = Matrix44fRotate(cam_side, -turn_angle_y) * p2;
          SetTarget(position_.x + p2.v[0], position_.y + p2.v[1],
                    position_.z + p2.v[2]);

          field_of_view_x_ = angle_x_max - angle_x_min;
          field_of_view_y_ = angle_y_max - angle_y_min;
        } else {
          // Look at the center of the AOI bounds.
          if (area_of_interest_bounds_[0] != -9999) {
            x_min = x_max =
                0.5f
                * (area_of_interest_bounds_[3] + area_of_interest_bounds_[0]);
            y_min = y_max = area_of_interest_bounds_[4]
                            + 0.5f
                                  * (area_of_interest_bounds_[1]
                                     - area_of_interest_bounds_[4]);
            z_min = z_max =
                0.5f
                * (area_of_interest_bounds_[5] + area_of_interest_bounds_[2]);
          } else {
            // Our default area of interest position is a bit higher
            // in vr since we want to drag our UI up a bit by default.
            x_min = x_max = 0.0f;
            y_min = y_max = 3.0f;
            z_min = z_max = -5.0f;

            // In vr mode we want or default area-of-interest to line up so that
            // our fixed-overlay matrix and our regular overlay matrix come out
            // the same.
            if (g_buildconfig.vr_build()) {
              if (g_core->vr_mode()) {
                // Only apply map's X offset if camera is locked.
                x_min = x_max =
                    position_.x
                    + (kCameraOffsetX
                       + (lock_panning_ ? vr_offset_smooth_.x : 0.0f)
                       + vr_extra_offset_.x);
                y_min = y_max = position_.y
                                + (kCameraOffsetY + vr_offset_smooth_.y
                                   + vr_extra_offset_.y)
                                + kVRFixedOverlayOffsetY;
                z_min = z_max = position_.z
                                + (kCameraOffsetZ + vr_offset_smooth_.z
                                   + vr_extra_offset_.z)
                                + kVRFixedOverlayOffsetZ;
              }
            }
          }
          field_of_view_x_ = 45.0f;
          field_of_view_y_ = 30.0f;
          SetTarget(0.5f * (x_min + x_max), 0.5f * (y_min + y_max),
                    0.5f * (z_min + z_max));
        }

        // If we don't have any focusable points, drop in a default.
        if (area_of_interest_points_.empty()) {
          area_of_interest_points_.emplace_back(0, 0, 0);
          have_real_areas_of_interest_ = false;
        } else {
          have_real_areas_of_interest_ = true;
        }
        pan_target_ = (x_max + x_min) / 2;
        if (pan_target_ > kPanMax) {
          pan_target_ = kPanMax;
        } else if (pan_target_ < kPanMin) {
          pan_target_ = kPanMin;
        }
      }
    }
  }

  // If they're on manual, we don't do smoothing or anything fancy.
  if (manual_) {
    target_.x = target_smoothed_.x = target_.x;
    target_.y = target_smoothed_.y = target_.y;
    target_.z = target_smoothed_.z = target_.z;
    smooth_speed_ = {0.0f, 0.0f, 0.0f};
    smooth_next_frame_ = false;
  } else {
    if (mode_ == CameraMode::kFollow) {
      // Useful to test camera.
      if (explicit_bool(false)) {
        field_of_view_x_smoothed_ = field_of_view_x_;
        field_of_view_y_smoothed_ = field_of_view_y_;
        target_smoothed_.x = target_.x;
        target_smoothed_.y = target_.y;
        target_smoothed_.z = target_.z;
        pan_pos_ = pan_target_;
        xy_constrain_blend_ = x_constrained_ ? 1.0f : 0.0f;
      }
    } else {
      float dx = target_smoothed_.x - position_.x;
      float dy = target_smoothed_.y - position_.y;
      float dz = target_smoothed_.z - position_.z;
      float target_dist = sqrtf(dx * dx + dy * dy + dz * dz);

      // If we're not smoothing this upcoming frame, snap this value.
      if (!smooth_next_frame_) target_radius_smoothed_ = target_radius_;

      float angle = tanf(target_radius_smoothed_ / target_dist);
      field_of_view_x_ = 0.001f;  // Always want y to be the constrained one.
      field_of_view_y_ = (2 * 360 * (angle / (2 * 3.1415f)));
    }
  }

  // Extra cam-space tweakage (via accelerometer if available).
  {
    Vector3f to_cam(target_smoothed_.x - position_.x,
                    target_smoothed_.y - position_.y,
                    target_smoothed_.z - position_.z);
    to_cam.Normalize();
    Vector3f cam_space_lr = Vector3f::Cross(to_cam, Vector3f(0, 1, 0));
    Vector3f cam_space_ud = Vector3f::Cross(cam_space_lr, to_cam);
    Vector3f tilt = 0.1f * g_base->graphics->tilt();
    if (manual_) {
      tilt.x = 0.0f;
      tilt.y = 0.0f;
    }
    extra_pos_ = -0.1f * tilt.y * cam_space_lr + 0.1f * tilt.x * cam_space_ud;
    extra_pos_2_ = extra_pos_;
    extra_pos_2_ += 0.35f * tilt.y * cam_space_lr;
    extra_pos_2_ -= 0.35f * tilt.x * cam_space_ud;
    up_ = cam_space_ud;

    // A tiny bit of random jitter to our camera pos.
    if (!manual_) {
      float mag = 2.0f;
      extra_pos_2_.x += mag * position_offset_smoothed_.x;
      extra_pos_2_.y += mag * position_offset_smoothed_.y;
      extra_pos_2_.z += mag * position_offset_smoothed_.z;
    }
  }
}

void Camera::Update(millisecs_t elapsed) {
  float rand_component = 0.000005f;
  float zoom_speed = 0.001f;
  float fov_speed_out = 0.0025f;
  float fov_speed_in = 0.001f;
  float speed = 0.000012f;
  float speed_2 = 0.00005f;
  float damping = 0.006f;
  float damping2 = 0.006f;
  float xy_blend_speed = 0.0002f;
  time_ += elapsed;

  // Prevent camera "explosions" if we've been unable to update for a while.
  elapsed = std::min(millisecs_t{100}, elapsed);
  auto elapsedf{static_cast<float>(elapsed)};

  // In normal mode we orbit; in vr mode we don't.
  if (g_core->vr_mode()) {
    heading_ = -0.3f;
  } else {
    heading_ += static_cast<float>(elapsed) / 10000.0f;
  }

  int rand_incr_1 = 309;
  int rand_incr_2 = 273;
  int rand_incr_3 = 247;

  if (mode_ == CameraMode::kOrbit) {
    rand_component *= 2.5f;
    rand_incr_1 /= 2;
    rand_incr_2 /= 2;
    rand_incr_3 /= 2;
  }

  target_radius_smoothed_ +=
      elapsedf * (target_radius_ - target_radius_smoothed_) * zoom_speed;

  float diff = field_of_view_x_ - field_of_view_x_smoothed_;
  field_of_view_x_smoothed_ +=
      elapsedf * diff * (diff > 0.0f ? fov_speed_out : fov_speed_in);

  diff = field_of_view_y_ - field_of_view_y_smoothed_;
  field_of_view_y_smoothed_ +=
      elapsedf * diff * (diff > 0.0f ? fov_speed_out : fov_speed_in);

  if (x_constrained_) {
    xy_constrain_blend_ +=
        elapsedf * (1.0f - xy_constrain_blend_) * xy_blend_speed;
    xy_constrain_blend_ = std::min(1.0f, xy_constrain_blend_);
  } else {
    xy_constrain_blend_ +=
        elapsedf * (0.0f - xy_constrain_blend_) * xy_blend_speed * elapsedf;
    xy_constrain_blend_ = std::max(0.0f, xy_constrain_blend_);
  }

  if (!g_core->vr_mode()) {
    smooth_speed_.x +=
        elapsedf * rand_component
        * (-0.5f
           + Utils::precalc_rand_1((time_ / rand_incr_1) % kPrecalcRandsCount));
    smooth_speed_.y +=
        elapsedf * rand_component
        * (-0.5f
           + Utils::precalc_rand_2((time_ / rand_incr_2) % kPrecalcRandsCount));
    smooth_speed_.z +=
        elapsedf * rand_component
        * (-0.5f
           + Utils::precalc_rand_3((time_ / rand_incr_3) % kPrecalcRandsCount));
  }

  if (RandomFloat() < 0.1f && !g_core->vr_mode()) {
    smooth_speed_2_.x +=
        elapsedf * rand_component * 4.0f * (-0.5f + RandomFloat());
    smooth_speed_2_.y +=
        elapsedf * rand_component * 4.0f * (-0.5f + RandomFloat());
    smooth_speed_2_.z +=
        elapsedf * rand_component * 4.0f * (-0.5f + RandomFloat());
  }

  // If we have no important areas of interest, keep our camera from moving
  // too fast.
  if (!have_real_areas_of_interest_) {
    speed *= 0.5f;
  }

  for (millisecs_t i = 0; i < elapsed; i++) {
    {
      float smoothing = 0.8f;
      float inv_smoothing = 1.0f - smoothing;
      vr_offset_smooth_.x =
          smoothing * vr_offset_smooth_.x + inv_smoothing * vr_offset_.x;
      vr_offset_smooth_.y =
          smoothing * vr_offset_smooth_.y + inv_smoothing * vr_offset_.y;
      vr_offset_smooth_.z =
          smoothing * vr_offset_smooth_.z + inv_smoothing * vr_offset_.z;
    }
    smooth_speed_ += (target_ - target_smoothed_) * speed;
    smooth_speed_ *= (1.0f - damping);
    smooth_speed_2_ += (-position_offset_smoothed_) * speed_2;
    smooth_speed_2_ *= (1.0f - damping2);
    target_smoothed_ += smooth_speed_;
    position_offset_smoothed_ += smooth_speed_2_;

    pan_speed_ += 0.00004f * pan_speed_scale_ * (pan_target_ - position_.x);
    pan_speed_ *= 0.97f;
    if (position_.x > kPanMax) pan_speed_ -= (position_.x - kPanMax) * 0.00003f;
    if (position_.x < kPanMin) pan_speed_ -= (position_.x - kPanMin) * 0.00003f;
    pan_pos_ += pan_speed_;

    int iterations = 1;

    // Jostle the camera occasionally if we're shaking.
    if (i % iterations == 0 && shake_amount_ > 0.0001f) {
      shake_amount_ *= 0.97f;
      shake_vel_.x +=
          0.05f * shake_amount_
          * (0.5f
             - Utils::precalc_rand_1(time_ % 122 * i % kPrecalcRandsCount));
      shake_vel_.y +=
          0.05f * shake_amount_
          * (0.5f
             - Utils::precalc_rand_2(time_ % 323 * i % kPrecalcRandsCount));
      shake_vel_.z +=
          0.05f * shake_amount_
          * (0.5f - Utils::precalc_rand_3(time_ % 76 * i % kPrecalcRandsCount));
    }

    for (int j = 0; j < iterations; j++) {
      shake_pos_ += shake_vel_;
      shake_vel_ += -0.001f * shake_pos_;
      shake_vel_ *= 0.99f;
    }

    if (g_base->graphics->camera_shake_disabled()) {
      shake_pos_ = {0, 0, 0};
    }
  }

  // Update audio position more often in vr since we can whip our head around.
  uint32_t interval = g_core->vr_mode() ? 50 : 100;

  // Occasionally, update microphone position for audio.
  if (time_ - last_listener_update_time_ > interval) {
    last_listener_update_time_ = time_;
    bool do_regular_update = true;
    if (g_core->vr_mode()) {
#if BA_VR_MODE
      GraphicsVR* vrgraphics = GraphicsVR::get();
      do_regular_update = false;
      Vector3f listener_pos = vrgraphics->vr_head_translate()
                              + vrgraphics->vr_head_forward() * 5.0f;
      assert(g_audio_server);
      g_audio->SetListenerPosition(listener_pos);
      g_audio->SetListenerOrientation(vrgraphics->vr_head_forward(),
                                      vrgraphics->vr_head_up());
#endif
    }
    if (explicit_bool(do_regular_update)) {
      float to_target = 0.5f;
      Vector3f listener_pos(
          position_.x + to_target * (target_smoothed_.x - position_.x),
          position_.y + to_target * (target_smoothed_.y - position_.y),
          position_.z + to_target * (target_smoothed_.z - position_.z));
      assert(g_base->audio_server);
      g_base->audio->SetListenerPosition(listener_pos);
    }
  }
}

void Camera::SetPosition(float x, float y, float z) {
  position_.x = x;
  position_.y = y;
  position_.z = z;
}

void Camera::SetTarget(float x, float y, float z) {
  target_.x = x;
  target_.y = y;
  target_.z = z;
}

void Camera::ManualHandleMouseWheel(float value) {
  if (!manual_) {
    return;
  }

  // Make this tiny so that Y is always the constraint.
  field_of_view_x_ = 0.1f;
  field_of_view_y_ *= (1.0f - 0.1f * value);
  if (field_of_view_y_ > kMaxFOV) {
    field_of_view_y_ = kMaxFOV;
  } else if (field_of_view_y_ < 1.0f) {
    field_of_view_y_ = 1.0f;
  }
}

void Camera::ManualHandleMouseMove(float move_h, float move_v) {
  if (!manual_) return;

  if (panning_ || trucking_ || orbiting_ || rolling_) {
    // get cam vector
    dVector3 cam_vec = {target_.x - position_.x, target_.y - position_.y,
                        target_.z - position_.z};
    float len = dVector3Length(cam_vec);
    dNormalize3(cam_vec);

    float fov_width =
        2 * (len * tanf(((field_of_view_y_) / 2) * 0.0174532925f));

    // get cam side vector
    dVector3 up = {0, 1, 0};
    dVector3 side_vec;
    dVector3Cross(up, cam_vec, side_vec);
    dNormalize3(side_vec);

    // get cam's up vector
    dVector3 cam_up;
    dVector3Cross(side_vec, cam_vec, cam_up);
    dNormalize3(cam_up);

    if (panning_) {
      move_h *= fov_width;
      move_v *= fov_width;
      side_vec[0] *= move_h;
      side_vec[1] *= move_h;
      side_vec[2] *= move_h;
      cam_up[0] *= move_v;
      cam_up[1] *= move_v;
      cam_up[2] *= move_v;

      position_.x += side_vec[0] + cam_up[0];
      position_.y += side_vec[1] + cam_up[1];
      position_.z += side_vec[2] + cam_up[2];
      target_.x += side_vec[0] + cam_up[0];
      target_.y += side_vec[1] + cam_up[1];
      target_.z += side_vec[2] + cam_up[2];
    } else if (orbiting_) {
      dVector3 cam_pos = {position_.x - target_.x, position_.y - target_.y,
                          position_.z - target_.z};
      RotatePointAroundVector(cam_pos, side_vec, cam_pos, move_v * -100);
      RotatePointAroundVector(cam_pos, up, cam_pos, move_h * -100);
      position_.x = cam_pos[0] + target_.x;
      position_.y = cam_pos[1] + target_.y;
      position_.z = cam_pos[2] + target_.z;

    } else if (rolling_) {
      // _roll += (move_h + move_v) * 100.0f;
    } else if (trucking_) {
      cam_vec[0] *= (move_h + move_v) * len;
      cam_vec[1] *= (move_h + move_v) * len;
      cam_vec[2] *= (move_h + move_v) * len;
      position_.x += cam_vec[0];
      position_.y += cam_vec[1];
      position_.z += cam_vec[2];
    }
  }
}

auto Camera::NewAreaOfInterest(bool in_focus) -> AreaOfInterest* {
  assert(g_base->InLogicThread());
  areas_of_interest_.emplace_back(in_focus);
  return &areas_of_interest_.back();
}

void Camera::DeleteAreaOfInterest(AreaOfInterest* a) {
  assert(g_base->InLogicThread());
  for (auto i = areas_of_interest_.begin(); i != areas_of_interest_.end();
       ++i) {
    if (&(*i) == a) {
      areas_of_interest_.erase(i);
      return;
    }
  }
  throw Exception("Area-of-interest not found");
}

void Camera::SetManual(bool enable) {
  manual_ = enable;
  if (manual_) {
    // Reset our target settings to our current smoothed ones,
    // so we don't see an instant jump to the target.
    target_.x = target_smoothed_.x;
    target_.y = target_smoothed_.y;
    target_.z = target_smoothed_.z;
  } else {
    smooth_next_frame_ = false;
  }
}

void Camera::SetMode(CameraMode m) {
  if (mode_ != m) {
    mode_ = m;
    smooth_next_frame_ = false;
    // last_mode_set_time_ = g_core->AppTimeMillisecs();
    // last_mode_set_time_ = time_;
    heading_ = kInitialHeading;
  }
}

void Camera::ApplyToFrameDef(FrameDef* frame_def) {
  frame_def->set_camera_mode(mode_);

  // FIXME - we should have some sort of support
  //   for multiple cameras each with their own pass.
  //   for now, though, there's just a single beauty pass
  //   which is us.

  RenderPass* passes[] = {frame_def->beauty_pass(),
                          frame_def->beauty_pass_bg(),
#if BA_VR_BUILD
                          frame_def->overlay_pass(),
                          frame_def->GetOverlayFixedPass(),
                          frame_def->vr_cover_pass(),
#endif
                          frame_def->overlay_3d_pass(),
                          frame_def->blit_pass(),
                          nullptr};

  // Currently, our x/y fovs are simply enough to fit everything.
  // Check the aspect ratio of what we're rendering to and fit them.

  // Add a few degrees just to keep things away from the edges a bit
  // since we have various UI elements there.
  float extra = 0.0f;

  // If we don't want to smooth this frame, snap these values.
  if (!smooth_next_frame_) {
    field_of_view_x_smoothed_ = field_of_view_x_;
    field_of_view_y_smoothed_ = field_of_view_y_;
  }

  float final_fov_y = field_of_view_y_smoothed_ + extra;
  if (final_fov_y < 1.0f) {
    final_fov_y = 1.0f;
  } else if (final_fov_y > 120.0f) {
    final_fov_y = 120.0f;
  }
  float final_fov_x = field_of_view_x_smoothed_ + extra;
  if (final_fov_x < 1.0f) {
    final_fov_x = 1.0f;
  } else if (final_fov_x > 120.0f) {
    final_fov_x = 120.0f;
  }
  float ratio = final_fov_x / final_fov_y;

  // Need to look at a pass to know if we're x or y constrained.
  float render_ratio = passes[0]->GetPhysicalAspectRatio();

  // Update whether we're x-constrained or not.
  x_constrained_ = (ratio >= render_ratio);

  // When we're x-constrained, we calc y so that x fits.
  float final_fov_y2 = final_fov_x / render_ratio;

  // If we're not smoothing this frame, snap immediately.
  if (!smooth_next_frame_) {
    xy_constrain_blend_ = x_constrained_ ? 1.0f : 0.0f;
  }

  // We smoothly blend between our x-constrained and non-x-constrained y values
  // so that we don't see a hitch when it switches.
  final_fov_y = xy_constrain_blend_ * final_fov_y2
                + (1.0f - xy_constrain_blend_) * final_fov_y;

  final_fov_y = std::max(5.0f, final_fov_y);

  // Reset some last things if we're non-smoothed.
  if (!smooth_next_frame_) {
    smooth_speed_ = {0.0f, 0.0f, 0.0f};
    shake_amount_ = 0;
    shake_pos_ = {0.0f, 0.0f, 0.0f};
    shake_vel_ = {0.0f, 0.0f, 0.0f};
    target_smoothed_ = target_;
    up_.x = 0.0f;
    up_.y = 1.0f;
    up_.z = 0.0f;
    vr_offset_smooth_ = vr_offset_;
  }

  // Also store original positions with the frame_def in case we want to muck
  // with them later (VR, etc.).
  frame_def->set_cam_original(Vector3f(position_.x + extra_pos_2_.x,
                                       position_.y + extra_pos_2_.y,
                                       position_.z + extra_pos_2_.z));

  // If we're vr, apply current vr offsets.
  // FIXME: should create a VRCamera subclass or whatnot.
  if (g_core->vr_mode()) {
    if (mode_ == CameraMode::kFollow) {
      Vector3f cam_original = frame_def->cam_original();

      // Only apply map's X offset if our camera is locked.
      cam_original.x += kCameraOffsetX
                        + (lock_panning_ ? vr_offset_smooth_.x : 0.0f)
                        + vr_extra_offset_.x;
      cam_original.y +=
          kCameraOffsetY + vr_offset_smooth_.y + vr_extra_offset_.y;
      cam_original.z +=
          kCameraOffsetZ + vr_offset_smooth_.z + vr_extra_offset_.z;
      frame_def->set_cam_original(cam_original);
    } else {
      Vector3f cam_original = frame_def->cam_original();
      cam_original.y += 3.0f;
      frame_def->set_cam_original(cam_original);
    }
  }
  frame_def->set_cam_target_original(target_smoothed_);
  frame_def->set_shake_original(shake_pos_);

  for (RenderPass** p = passes; *p != nullptr; p++) {
    assert(!area_of_interest_points_.empty());
    (**p).SetCamera(
        position_ + extra_pos_2_, target_smoothed_ + shake_pos_ + extra_pos_,
        up_, 4, 1000.0f,
        -1.0f,  // Auto x fov.
        final_fov_y
            * (frame_def->settings()->tv_border ? (1.0f + kTVBorder) : 1.0f),
        false, 0, 0, 0, 0,  // Not using tangent fovs.
        area_of_interest_points_);
  }
  smooth_next_frame_ = true;
}

}  // namespace ballistica::base
