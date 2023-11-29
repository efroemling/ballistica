// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_CAMERA_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_CAMERA_H_

#include <list>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

// Hmm; this shouldn't be here.
const float kHappyThoughtsZPlane = -5.52f;

// Default horizontal camera field of view.
const float kCameraFOVY = 60.0f;
const float kInitialHeading = -1.0f;

// FIXME: looks like this guy gets accessed from a few different threads.
class Camera : public Object {
 public:
  Camera();
  ~Camera() override;
  void Shake(float amount);
  void SetManual(bool enable);
  auto manual() const -> bool { return manual_; }
  void ManualHandleMouseMove(float move_h, float move_v);
  void ManualHandleMouseWheel(float val);

  // Update the camera position values - done once per render
  void UpdatePosition();

  // Update camera velocities/etc. This is done as often as possible.
  void Update(millisecs_t elapsed);
  void SetPosition(float x, float y, float z);
  void SetTarget(float x, float y, float z);
  void SetMode(CameraMode m);
  void set_area_of_interest_bounds(float min_x, float min_y, float min_z,
                                   float max_x, float max_y, float max_z) {
    area_of_interest_bounds_[0] = min_x;
    area_of_interest_bounds_[1] = min_y;
    area_of_interest_bounds_[2] = min_z;
    area_of_interest_bounds_[3] = max_x;
    area_of_interest_bounds_[4] = max_y;
    area_of_interest_bounds_[5] = max_z;
  }
  void area_of_interest_bounds(float* min_x, float* min_y, float* min_z,
                               float* max_x, float* max_y, float* max_z) {
    *min_x = area_of_interest_bounds_[0];
    *min_y = area_of_interest_bounds_[1];
    *min_z = area_of_interest_bounds_[2];
    *max_x = area_of_interest_bounds_[3];
    *max_y = area_of_interest_bounds_[4];
    *max_z = area_of_interest_bounds_[5];
  }
  void UpdateManualMode();

  // Sets up the render in the passes we're associated with.  Call this anytime
  // during a render.
  void ApplyToFrameDef(FrameDef* frame_def);
  auto field_of_view_y() const -> float { return field_of_view_y_; }
  void get_position(float* x, float* y, float* z) const {
    *x = position_.x;
    *y = position_.y;
    *z = position_.z;
  }
  void target_smoothed(float* x, float* y, float* z) const {
    *x = target_smoothed_.x;
    *y = target_smoothed_.y;
    *z = target_smoothed_.z;
  }
  void set_alt_down(bool d) { alt_down_ = d; }
  void set_cmd_down(bool d) { cmd_down_ = d; }
  void set_ctrl_down(bool d) { ctrl_down_ = d; }
  void set_mouse_left_down(bool d) { mouse_left_down_ = d; }
  void set_mouse_right_down(bool d) { mouse_right_down_ = d; }
  void set_mouse_middle_down(bool d) { mouse_middle_down_ = d; }
  void set_happy_thoughts_mode(bool h) { happy_thoughts_mode_ = h; }
  auto happy_thoughts_mode() const -> bool { return happy_thoughts_mode_; }
  auto NewAreaOfInterest(bool inFocus = true) -> AreaOfInterest*;
  void DeleteAreaOfInterest(AreaOfInterest* a);
  auto mode() const -> CameraMode { return mode_; }
  void set_vr_offset(const Vector3f& val) { vr_offset_ = val; }
  void set_vr_extra_offset(const Vector3f& val) { vr_extra_offset_ = val; }
  auto vr_extra_offset() const -> const Vector3f& { return vr_extra_offset_; }
  void set_lock_panning(bool val) { lock_panning_ = val; }
  auto lock_panning() const -> bool { return lock_panning_; }
  auto pan_speed_scale() const -> float { return pan_speed_scale_; }
  void set_pan_speed_scale(float val) { pan_speed_scale_ = val; }

 private:
  CameraMode mode_{CameraMode::kFollow};
  bool manual_{};
  bool smooth_next_frame_{};
  bool have_real_areas_of_interest_{};
  bool lock_panning_{};

  // Manual stuff.
  bool panning_{};
  bool orbiting_{};
  bool rolling_{};
  bool trucking_{};
  bool alt_down_{};
  bool cmd_down_{};
  bool ctrl_down_{};
  bool mouse_left_down_{};
  bool mouse_middle_down_{};
  bool mouse_right_down_{};

  bool happy_thoughts_mode_{};
  bool x_constrained_{true};
  float pan_speed_scale_{1.0f};
  float heading_{kInitialHeading};
  float area_of_interest_bounds_[6]{-9999, -9999, -9999, 9999, 9999, 9999};
  float pan_pos_{};
  float pan_speed_{};
  float pan_target_{};
  float shake_amount_{};
  float target_radius_{2.0f};
  float target_radius_smoothed_{2.0f};
  float field_of_view_x_{5.0f};
  float field_of_view_y_{kCameraFOVY};
  float field_of_view_x_smoothed_{1.0f};
  float field_of_view_y_smoothed_{1.0f};
  float min_target_radius_{5.0f};
  float area_of_interest_near_{1.0f};
  float area_of_interest_far_{2.0f};
  float xy_constrain_blend_{0.5f};
  // millisecs_t last_mode_set_time_{};
  millisecs_t last_listener_update_time_{};
  millisecs_t time_{};
  Vector3f vr_offset_{0.0f, 0.0f, 0.0f};
  Vector3f vr_extra_offset_{0.0f, 0.0f, 0.0f};
  Vector3f vr_offset_smooth_{0.0f, 0.0f, 0.0f};
  Vector3f extra_pos_{0.0f, 0.0f, 0.0f};
  Vector3f extra_pos_2_{0.0f, 0.0f, 0.0f};
  Vector3f shake_pos_{0.0f, 0.0f, 0.0f};
  Vector3f shake_vel_{0.0f, 0.0f, 0.0f};
  Vector3f position_{0.0f, 1.0f, -1.0f};
  Vector3f target_{0.0f, 1.0f, -1.0f};
  Vector3f target_smoothed_{0.0f, 0.0f, 0.0f};
  Vector3f position_offset_smoothed_{0.0f, 0.0f, 0.0f};
  Vector3f smooth_speed_{0.0f, 0.0f, 0.0f};
  Vector3f smooth_speed_2_{0.0f, 0.0f, 0.0f};
  Vector3f up_{0.0f, 1.0f, 0.0f};
  std::list<AreaOfInterest> areas_of_interest_;
  std::vector<Vector3f> area_of_interest_points_{{0.0f, 0.0f, 0.0f}};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_CAMERA_H_
