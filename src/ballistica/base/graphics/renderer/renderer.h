// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_RENDERER_RENDERER_H_
#define BALLISTICA_BASE_GRAPHICS_RENDERER_RENDERER_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/graphics/mesh/image_mesh.h"
#include "ballistica/base/graphics/mesh/mesh.h"
#include "ballistica/base/graphics/mesh/mesh_buffer.h"
#include "ballistica/base/graphics/mesh/mesh_buffer_base.h"
#include "ballistica/base/graphics/mesh/mesh_buffer_vertex_simple_full.h"
#include "ballistica/base/graphics/mesh/mesh_buffer_vertex_smoke_full.h"
#include "ballistica/base/graphics/mesh/mesh_buffer_vertex_sprite.h"
#include "ballistica/base/graphics/mesh/mesh_data.h"
#include "ballistica/base/graphics/mesh/mesh_data_client_handle.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_16.h"
#include "ballistica/base/graphics/mesh/mesh_index_buffer_32.h"
#include "ballistica/base/graphics/mesh/mesh_indexed.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_dual_texture_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_object_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_simple_split.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_smoke_full.h"
#include "ballistica/base/graphics/mesh/mesh_indexed_static_dynamic.h"
#include "ballistica/base/graphics/mesh/mesh_non_indexed.h"
#include "ballistica/base/graphics/mesh/sprite_mesh.h"
#include "ballistica/base/graphics/mesh/text_mesh.h"
#include "ballistica/base/graphics/renderer/framebuffer.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/renderer/render_target.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/graphics/support/render_command_buffer.h"
#include "ballistica/base/graphics/text/text_group.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

// The renderer is responsible for converting a frame_def to onscreen pixels
class Renderer {
 public:
  Renderer();
  virtual ~Renderer();

  // Given a z-distance in world-space, returns a beauty-pass z-buffer
  // value from 0 to 1.
  auto GetZBufferValue(RenderPass* pass, float dist) -> float;

  // All 3 of these must be called during a render.
  void PreprocessFrameDef(FrameDef* frame_def);
  void RenderFrameDef(FrameDef* frame_def);
  void FinishFrameDef(FrameDef* frame_def);

  // This needs to be generalized.
  void SetLight(float pitch, float heading, float tz);
  void set_shadow_offset(const Vector3f& offset) { shadow_offset_ = offset; }
  void set_shadow_scale(float x, float z) {
    shadow_scale_x_ = x;
    shadow_scale_z_ = z;
  }
  void set_shadow_ortho(bool ortho) { shadow_ortho_ = ortho; }
  void set_tint(const Vector3f& val) { tint_ = val; }
  void set_ambient_color(const Vector3f& val) { ambient_color_ = val; }
  void set_vignette_outer(const Vector3f& val) { vignette_outer_ = val; }
  void set_vignette_inner(const Vector3f& val) { vignette_inner_ = val; }
  auto tint() const -> const Vector3f& { return tint_; }
  auto ambient_color() const -> const Vector3f& { return ambient_color_; }
  auto vignette_outer() const -> const Vector3f& { return vignette_outer_; }
  auto vignette_inner() const -> const Vector3f& { return vignette_inner_; }
  auto shadow_ortho() const -> bool { return shadow_ortho_; }
  auto shadow_offset() const -> const Vector3f& { return shadow_offset_; }
  auto shadow_scale_x() const -> float { return shadow_scale_x_; }
  auto shadow_scale_z() const -> float { return shadow_scale_z_; }
  auto light_tz() const -> float { return light_tz_; }
  auto light_pitch() const -> float { return light_pitch_; }
  auto light_heading() const -> float { return light_heading_; }
  void set_pixel_scale(float s) { pixel_scale_requested_ = s; }
  void set_debug_draw_mode(bool debugModeIn) { debug_draw_mode_ = debugModeIn; }
  auto debug_draw_mode() -> bool { return debug_draw_mode_; }

  // Used when recreating contexts.
  virtual void Unload();
  virtual void Load();
  virtual void PostLoad();
  virtual auto GetAutoGraphicsQuality() -> GraphicsQuality = 0;
  virtual auto GetAutoTextureQuality() -> TextureQuality = 0;

  virtual auto GetAutoAndroidRes() -> std::string;

  void OnScreenSizeChange();
  auto has_camera_render_target() const -> bool {
    return camera_render_target_.Exists();
  }
  auto has_camera_msaa_render_target() const -> bool {
    return camera_msaa_render_target_.Exists();
  }
  auto camera_render_target() -> RenderTarget* {
    assert(camera_render_target_.Exists());
    return camera_render_target_.Get();
  }
  auto camera_msaa_render_target() -> RenderTarget* {
    assert(camera_msaa_render_target_.Exists());
    return camera_msaa_render_target_.Get();
  }
  auto backing_render_target() -> RenderTarget* {
    assert(backing_render_target_.Exists());
    return backing_render_target_.Get();
  }
  auto screen_render_target() -> RenderTarget* {
    assert(screen_render_target_.Exists());
    return screen_render_target_.Get();
  }
  auto light_render_target() -> RenderTarget* {
    assert(light_render_target_.Exists());
    return light_render_target_.Get();
  }
  auto light_shadow_render_target() -> RenderTarget* {
    assert(light_shadow_render_target_.Exists());
    return light_shadow_render_target_.Get();
  }
  auto vr_overlay_flat_render_target() -> RenderTarget* {
    assert(vr_overlay_flat_render_target_.Exists());
    return vr_overlay_flat_render_target_.Get();
  }
  auto shadow_res() const -> int { return shadow_res_; }
  auto blur_res_count() const -> int { return blur_res_count_; }
  auto drawing_reflection() const -> bool { return drawing_reflection_; }
  void set_drawing_reflection(bool val) { drawing_reflection_ = val; }
  auto dof_near_smoothed() const -> float { return dof_near_smoothed_; }
  auto dof_far_smoothed() const -> float { return dof_far_smoothed_; }
  auto total_frames_rendered() -> int { return frames_rendered_count_; }

#if BA_VR_BUILD
  void VRSetHead(float tx, float ty, float tz, float yaw, float pitch,
                 float roll);
  void VRSetHands(const VRHandsState& state) { vr_raw_hands_state_ = state; }
  void VRSetEye(int eye, float yaw, float pitch, float roll, float tanL,
                float tanR, float tanB, float tanT, float eyeX, float eyeY,
                float eyeZ, int viewport_x, int viewport_y);
  int VRGetViewportX() const { return vr_viewport_x_; }
  int VRGetViewportY() const { return vr_viewport_y_; }
#endif

  virtual auto NewMeshAssetData(const MeshAsset& mesh)
      -> Object::Ref<MeshAssetRendererData> = 0;
  virtual auto NewTextureData(const TextureAsset& texture)
      -> Object::Ref<TextureAssetRendererData> = 0;
  virtual auto NewMeshData(MeshDataType t, MeshDrawType drawType)
      -> MeshRendererData* = 0;
  virtual void DeleteMeshData(MeshRendererData* data, MeshDataType t) = 0;
  virtual void ProcessRenderCommandBuffer(RenderCommandBuffer* buffer,
                                          const RenderPass& pass,
                                          RenderTarget* render_target) = 0;
  virtual void SetDepthRange(float min, float max) = 0;
  virtual void FlipCullFace() = 0;

 protected:
  virtual void DrawDebug() = 0;
  virtual void CheckForErrors() = 0;
  virtual void UpdateVignetteTex_(bool force) = 0;
  virtual void GenerateCameraBufferBlurPasses() = 0;
  virtual void UpdateMeshes(
      const std::vector<Object::Ref<MeshDataClientHandle>>& meshes,
      const std::vector<int8_t>& index_sizes,
      const std::vector<Object::Ref<MeshBufferBase>>& buffers) = 0;
  virtual void SetDepthWriting(bool enable) = 0;
  virtual void SetDepthTesting(bool enable) = 0;
  virtual void SetDrawAtEqualDepth(bool enable) = 0;
  virtual void InvalidateFramebuffer(bool color, bool depth,
                                     bool target_read_framebuffer) = 0;
  virtual auto NewScreenRenderTarget() -> RenderTarget* = 0;
  virtual auto NewFramebufferRenderTarget(int width, int height,
                                          bool linear_interp, bool depth,
                                          bool texture, bool depth_texture,
                                          bool high_quality, bool msaa,
                                          bool alpha)
      -> Object::Ref<RenderTarget> = 0;
  virtual void PushGroupMarker(const char* label) = 0;
  virtual void PopGroupMarker() = 0;
  virtual void BlitBuffer(RenderTarget* src, RenderTarget* dst, bool depth,
                          bool linear_interpolation, bool force_shader_blit,
                          bool invalidate_source) = 0;
  virtual auto IsMSAAEnabled() const -> bool = 0;
  virtual void UpdateMSAAEnabled_() = 0;
  virtual void VREyeRenderBegin() = 0;
  virtual void RenderFrameDefEnd() = 0;
  virtual void CardboardDisableScissor() = 0;
  virtual void CardboardEnableScissor() = 0;
#if BA_VR_BUILD
  void VRTransformToRightHand();
  void VRTransformToLeftHand();
  void VRTransformToHead();
  virtual void VRSyncRenderStates() = 0;
#endif

 private:
  void UpdateLightAndShadowBuffers(FrameDef* frame_def);
  void RenderLightAndShadowPasses(FrameDef* frame_def);
  void UpdateSizesQualitiesAndColors(FrameDef* frame_def);
  void DrawWorldToCameraBuffer(FrameDef* frame_def);
  void UpdatePixelScaleAndBackingBuffer(FrameDef* frame_def);
  void UpdateCameraRenderTargets(FrameDef* frame_def);
  // #if BA_OSTYPE_MACOS && BA_SDL_BUILD && !BA_SDL2_BUILD
  //   void HandleFunkyMacGammaIssue(FrameDef* frame_def);
  // #endif
  void LoadMedia(FrameDef* frame_def);
  void UpdateDOFParams(FrameDef* frame_def);
#if BA_VR_BUILD
  void VRPreprocess(FrameDef* frame_def);
  void VRUpdateForEyeRender(FrameDef* frame_def);
  void VRDrawOverlayFlatPass(FrameDef* frame_def);
  // Raw values from vr system.
  VRHandsState vr_raw_hands_state_{};
  float vr_raw_head_tx_{};
  float vr_raw_head_ty_{};
  float vr_raw_head_tz_{};
  float vr_raw_head_yaw_{};
  float vr_raw_head_pitch_{};
  float vr_raw_head_roll_{};
  // Final game-space transforms.
  Matrix44f vr_base_transform_{kMatrix44fIdentity};
  Matrix44f vr_transform_right_hand_{kMatrix44fIdentity};
  Matrix44f vr_transform_left_hand_{kMatrix44fIdentity};
  Matrix44f vr_transform_head_{kMatrix44fIdentity};
  // Values for current eye render.
  bool vr_use_fov_tangents_{};
  float vr_fov_l_tan_{1.0f};
  float vr_fov_r_tan_{1.0f};
  float vr_fov_b_tan_{1.0f};
  float vr_fov_t_tan_{1.0f};
  float vr_fov_degrees_x_{30.0f};
  float vr_fov_degrees_y_{30.0f};
  float vr_eye_x_{};
  float vr_eye_y_{};
  float vr_eye_z_{};
  int vr_eye_{};
  float vr_eye_yaw_{};
  float vr_eye_pitch_{};
  float vr_eye_roll_{};
  int vr_viewport_x_{};
  int vr_viewport_y_{};
#endif  // BA_VR_BUILD

  bool screen_size_dirty_{};
  bool msaa_enabled_dirty_{};
  millisecs_t dof_update_time_{};
  bool dof_delay_{true};
  float dof_near_smoothed_{};
  float dof_far_smoothed_{};
  bool drawing_reflection_{};
  int blur_res_count_{};
  float light_pitch_{};
  float light_heading_{};
  float light_tz_{-22.0f};
  Vector3f shadow_offset_{0.0f, 0.0f, 0.0f};
  float shadow_scale_x_{1.0f};
  float shadow_scale_z_{1.0f};
  bool shadow_ortho_{};
  Vector3f tint_{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer_{0.0f, 0.0f, 0.0f};
  Vector3f vignette_inner_{1.0f, 1.0f, 1.0f};
  int shadow_res_{-1};
  float screen_gamma_{1.0f};
  float pixel_scale_requested_{1.0f};
  float pixel_scale_{1.0f};
  Object::Ref<RenderTarget> screen_render_target_;
  Object::Ref<RenderTarget> backing_render_target_;
  Object::Ref<RenderTarget> camera_render_target_;
  Object::Ref<RenderTarget> camera_msaa_render_target_;
  Object::Ref<RenderTarget> light_render_target_;
  Object::Ref<RenderTarget> light_shadow_render_target_;
  Object::Ref<RenderTarget> vr_overlay_flat_render_target_;
  millisecs_t last_screen_gamma_update_time_{};
  int last_commands_buffer_size_{};
  int last_f_vals_buffer_size_{};
  int last_i_vals_buffer_size_{};
  int last_meshes_buffer_size_{};
  int last_textures_buffer_size_{};
  bool debug_draw_mode_{};
  int frames_rendered_count_{};

  // The *actual* current quality (set based on the
  // currently-rendering frame_def)
  GraphicsQuality last_render_quality_{GraphicsQuality::kLow};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_RENDERER_RENDERER_H_
