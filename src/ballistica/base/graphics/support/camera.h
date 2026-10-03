// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_CAMERA_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_CAMERA_H_

#include <list>

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/support/area_of_interest.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

// Hmm; this shouldn't be here.
const float kHappyThoughtsZPlane = -5.52f;

/// What a RenderView looks at its world through.
///
/// This is the part of a camera that things drawing a world deal with:
/// they can ask where it is, register areas of interest with it, and
/// pass along what their world would like of it (a mode, bounds to
/// stay within). What a camera makes of those is up to it. The
/// gameplay camera (GameCamera) frames its areas of interest; a camera
/// parked in front of a ui viewer's subject ignores them.
///
/// Logic thread only. Design: docs/initiatives/render-views.md.
class Camera : public Object {
 public:
  Camera();
  ~Camera() override;

  /// Advance by an amount of display time. Called once per frame
  /// drawn, before UpdatePosition().
  virtual void Update(millisecs_t elapsed);

  /// Settle on where we are for the frame about to be drawn.
  virtual void UpdatePosition();

  /// Write our setup into the world passes of a frame being built.
  virtual void ApplyToFrameDef(FrameDef* frame_def) = 0;

  virtual auto GetPosition() const -> Vector3f = 0;
  void get_position(float* x, float* y, float* z) const {
    Vector3f pos = GetPosition();
    *x = pos.x;
    *y = pos.y;
    *z = pos.z;
  }

  /// What our world would like of us. Cameras with their own ideas
  /// ignore these.
  virtual auto mode() const -> CameraMode;
  virtual void SetMode(CameraMode mode);
  virtual void SetAreaOfInterestBounds(float min_x, float min_y, float min_z,
                                       float max_x, float max_y, float max_z);
  virtual void SetVROffset(const Vector3f& val);

  /// Register something in the world worth keeping in frame. The
  /// result stays valid until handed to DeleteAreaOfInterest().
  auto NewAreaOfInterest(bool in_focus = true) -> AreaOfInterest*;
  void DeleteAreaOfInterest(AreaOfInterest* a);

  // This is a property of the world more than of the camera (in this
  // mode things get held to a single plane), but this is where it has
  // always lived.
  void set_happy_thoughts_mode(bool h) { happy_thoughts_mode_ = h; }
  auto happy_thoughts_mode() const -> bool { return happy_thoughts_mode_; }

 protected:
  auto areas_of_interest() const -> const std::list<AreaOfInterest>& {
    return areas_of_interest_;
  }

 private:
  bool happy_thoughts_mode_{};
  std::list<AreaOfInterest> areas_of_interest_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_CAMERA_H_
