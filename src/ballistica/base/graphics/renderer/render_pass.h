// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_PASS_H_
#define BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_PASS_H_

#include <memory>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/math/matrix44f.h"

namespace ballistica::base {

// A drawing context for one pass. This can be a render to the screen, a
// shadow pass, a window, etc.
class RenderPass {
 public:
  enum class ReflectionSubPass : uint8_t { kRegular, kMirrored };
  enum class Type : uint8_t {
    // A pass whose results are projected onto the scene for lighting and
    // shadow effects. Values lighter than kShadowNeutral will show up as
    // light and darker than neutral will show up as shadowing. This version
    // should be used by anything wanting to draw with both shadows and
    // lighting cast on it. Note that there is no z-depth used in shadow
    // calculations, so objects casting shadows should not show shadows or
    // else they will shadow themselves.
    kLightShadowPass,
    // A pass whose results are projected onto the scene for lighting and
    // shadow effects. Values lighter than kShadowNeutral will show up as
    // light and darker than neutral will show up as shadowing. This pass is
    // intended to only contain lights however. Objects that cast shadows
    // generally should use this light texture when drawing themselves; if
    // they use the kLightShadowPass texture, they will shadow themselves.
    kLightPass,
    // The pass where normal foreground scene geometry is drawn into.
    kBeautyPass,
    // Background geometry is drawn into this; it has a separate depth range
    // so that far off mountains can properly occlude each other and whatnot
    // without sacrificing depth fidelity of the regular beauty pass.
    kBeautyPassBG,
    // Geometry used to blit the camera buffer on-screen for final display.
    // This geometry can make use of shaders for effects such as
    // depth-of-field or can distort the texture lookup UVs for distortion
    // shock-waves or other effects.
    kBlitPass,
    // Standard 2d overlay stuff such as UI. May be drawn in 2d or on a
    // plane in 3d space (in vr). In VR, each of these elements are drawn
    // individually and can thus have their own depth. also in VR, this
    // overlay may be repositions based on the camera/map/etc; use
    // kOverlayFixedPass for items that shouldn't do this (for example,
    // elements visible across map transitions). Be aware that things here
    // may be obscured by UI depending on depth/etc. Use OVERLAY_FRONT_PASS
    // if you need things to always show up in front of UI.
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
    // Only used in VR - overlay elements that should always be fixed in
    // space. Use this for stuff that may be visible across map transitions
    // or other events that can cause the regular overlay to move around.
    kOverlayFixedPass
  };

  RenderPass(Type type_in, FrameDef* frame_def);
  virtual ~RenderPass();

  auto type() const -> Type { return type_; }

  // The physical size of the drawing surface (pixels).
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
  void Complete();
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

  bool cam_use_fov_tangents_{};
  bool floor_reflection_{};
  Type type_{};

  float cam_near_clip_{};
  float cam_far_clip_{};
  float cam_fov_x_{};
  float cam_fov_y_{};
  float physical_width_{};
  float physical_height_{};
  float virtual_width_{};
  float virtual_height_{};

  // We can now alternately supply left, right, top, bottom frustum tangents.
  float cam_fov_l_tan_{1.0f};
  float cam_fov_r_tan_{1.0f};
  float cam_fov_t_tan_{1.0f};
  float cam_fov_b_tan_{1.0f};

  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  Vector3f cam_target_{0.0f, 0.0f, 0.0f};
  Vector3f cam_up_{0.0f, 0.0f, 0.0f};

  Matrix44f tex_project_matrix_{kMatrix44fIdentity};
  Matrix44f projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_projection_matrix_{kMatrix44fIdentity};
  FrameDef* frame_def_{};

  std::vector<Vector3f> cam_area_of_interest_points_;

  // Our pass holds sets of draw-commands bucketed by section and
  // component-type.
  std::unique_ptr<RenderCommandBuffer>
      commands_[static_cast<int>(ShadingType::kCount)];
  std::unique_ptr<RenderCommandBuffer> commands_flat_;
  std::unique_ptr<RenderCommandBuffer> commands_flat_transparent_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_RENDERER_RENDER_PASS_H_
