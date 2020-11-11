// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_RENDER_PASS_H_
#define BALLISTICA_GRAPHICS_RENDER_PASS_H_

#include <memory>
#include <vector>

#include "ballistica/math/matrix44f.h"

namespace ballistica {

// A drawing context for one pass. This can be a render to the screen, a shadow
// pass, a window, etc.
class RenderPass {
 public:
  enum class ReflectionSubPass { kRegular, kMirrored };
  enum class Type {
    kLightShadowPass,
    kLightPass,
    kBeautyPass,
    kBeautyPassBG,
    kBlitPass,
    // Standard 2d overlay stuff. May be drawn in 2d or on a plane in 3d
    // space (in vr).  In VR, each of these elements are drawn individually
    // and can thus have their own depth. also in VR this overlay repositions
    // itself per level; use kOverlayFixedPass for items that shouldn't.
    // this overlay may be obscured by UI. Use OVERLAY_FRONT_PASS if you need
    // things to show up in front of UI.
    kOverlayPass,
    // Just like kOverlayPass but guaranteed to draw in front of UI.
    kOverlayFrontPass,
    // Actually drawn in regular 3d space - for life bars, names, etc that
    // need to overlay regular 3d stuff but exist in the world.
    kOverlay3DPass,
    // Only used in VR - overlay stuff drawn into a flat 2d texture so that
    // scissoring/etc works (the UI uses this).
    kOverlayFlatPass,
    /// Only used in VR - stuff that needs to cover absolutely everything
    /// else (like the 3d wipe fade).
    kVRCoverPass,
    // Only used in VR - overlay elements that should always be fixed in space.
    kOverlayFixedPass
  };

  RenderPass(Type type_in, FrameDef* frame_def);
  virtual ~RenderPass();

  auto type() const -> Type { return type_; }

  // The physical size of the drawing surface.
  auto physical_width() const -> float { return physical_width_; }
  auto physical_height() const -> float { return physical_height_; }

  // The virtual size of the drawing surface.
  // This may or may not have anything to do with the physical size
  // (for instance the overlay pass in VR has its own bounds which
  // is completely independent of the physical surface it gets drawn into).
  auto virtual_width() const -> float { return virtual_width_; }
  auto virtual_height() const -> float { return virtual_height_; }

  // Should objects be rendered 'underground' in this pass?
  auto floor_reflection() const -> bool { return floor_reflection_; }
  void set_floor_reflection(bool val) { floor_reflection_ = val; }
  auto GetPhysicalAspectRatio() const -> float {
    return physical_width() / physical_height();
  }
  void SetCamera(const Vector3f& pos, const Vector3f& target,
                 const Vector3f& up, float near_clip, float far_clip,
                 float fov_x,  // Set to -1 for auto.
                 float fov_y, bool use_fov_tangents, float fov_tan_l,
                 float fov_tan_r, float fov_tan_b, float fov_tan_t,
                 const std::vector<Vector3f>& area_of_interest_points);
  auto frame_def() const -> FrameDef* { return frame_def_; }
  void Render(RenderTarget* t, bool transparent);
  auto tex_project_matrix() const -> const Matrix44f& {
    return tex_project_matrix_;
  }
  auto projection_matrix() const -> const Matrix44f& {
    return projection_matrix_;
  }
  auto model_view_matrix() const -> const Matrix44f& {
    return model_view_matrix_;
  }
  auto model_view_projection_matrix() const -> const Matrix44f& {
    return model_view_projection_matrix_;
  }
  auto HasDrawCommands() const -> bool;
  void Finalize();
  void Reset();

  // Whether this pass draws stuff from the per-shader command lists
  auto UsesWorldLists() const -> bool {
    switch (type()) {
      case Type::kBeautyPass:
      case Type::kBeautyPassBG:
        return true;
      case Type::kOverlayPass:
      case Type::kOverlayFrontPass:
      case Type::kOverlay3DPass:
      case Type::kVRCoverPass:
      case Type::kOverlayFlatPass:
      case Type::kOverlayFixedPass:
      case Type::kBlitPass:
      case Type::kLightPass:
      case Type::kLightShadowPass:
        return false;
      default:
        throw Exception();
    }
  }
  auto commands_flat() const -> RenderCommandBuffer* {
    return commands_flat_.get();
  }
  auto commands_flat_transparent() const -> RenderCommandBuffer* {
    return commands_flat_transparent_.get();
  }
  auto GetCommands(ShadingType type) const -> RenderCommandBuffer* {
    return commands_[static_cast<int>(type)].get();
  }

  auto cam_area_of_interest_points() const -> const std::vector<Vector3f>& {
    return cam_area_of_interest_points_;
  }

 private:
  void SetFrustum(float near_val, float far_val);

  // Our pass holds sets of draw-commands bucketed by section and
  // component-type.
  std::unique_ptr<RenderCommandBuffer>
      commands_[static_cast<int>(ShadingType::kCount)];
  std::unique_ptr<RenderCommandBuffer> commands_flat_;
  std::unique_ptr<RenderCommandBuffer> commands_flat_transparent_;
  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  Vector3f cam_target_{0.0f, 0.0f, 0.0f};
  Vector3f cam_up_{0.0f, 0.0f, 0.0f};
  float cam_near_clip_{};
  float cam_far_clip_{};
  float cam_fov_x_{};
  float cam_fov_y_{};

  // We can now alternately supply left, right, top, bottom frustum tangents.
  bool cam_use_fov_tangents_{};
  float cam_fov_l_tan_{1.0f};
  float cam_fov_r_tan_{1.0f};
  float cam_fov_t_tan_{1.0f};
  float cam_fov_b_tan_{1.0f};
  std::vector<Vector3f> cam_area_of_interest_points_;
  Type type_{};

  // For lights/shadows.
  Matrix44f tex_project_matrix_{kMatrix44fIdentity};
  Matrix44f projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_projection_matrix_{kMatrix44fIdentity};
  bool floor_reflection_{};
  FrameDef* frame_def_{};
  float physical_width_{};
  float physical_height_{};
  float virtual_width_{};
  float virtual_height_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_RENDER_PASS_H_
