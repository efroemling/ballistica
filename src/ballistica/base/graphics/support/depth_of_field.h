// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_DEPTH_OF_FIELD_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_DEPTH_OF_FIELD_H_

#include <cstdint>

namespace ballistica::base {

/// What of a world is in focus when it is drawn with depth of field
/// (which takes high graphics quality or better; below that everything
/// is sharp regardless).
///
/// Plain values; a camera decides them for each frame and the renderer
/// reads them from the frame.
struct DepthOfField {
  enum class Mode : uint8_t {
    /// Focus follows the camera's areas of interest, eased over time
    /// (what gameplay does).
    kFollowAreasOfInterest,
    /// Everything is in focus.
    kOff,
    /// What is in focus is given outright; see the distances below.
    kRange,
  };

  Mode mode{Mode::kFollowAreasOfInterest};

  // For kRange, as distances out from the camera along the way it is
  // looking: everything between focus_near and focus_far is sharp, and
  // from those things get blurrier out to blur_near (nearer the
  // camera) and blur_far (farther from it), past which they are as
  // blurry as things get.
  float blur_near{};
  float focus_near{};
  float focus_far{};
  float blur_far{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_DEPTH_OF_FIELD_H_
