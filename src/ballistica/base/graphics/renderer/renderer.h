// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_RENDERER_RENDERER_H_
#define BALLISTICA_BASE_GRAPHICS_RENDERER_RENDERER_H_

#include <string>
#include <unordered_map>
#include <vector>

#include "ballistica/base/assets/mesh_asset.h"
#include "ballistica/base/graphics/mesh/mesh_buffer_base.h"
#include "ballistica/base/graphics/mesh/mesh_data_client_handle.h"
#include "ballistica/base/graphics/renderer/render_pass.h"
#include "ballistica/base/graphics/renderer/render_target.h"
#include "ballistica/base/graphics/renderer/render_view_renderer_data.h"
#include "ballistica/base/graphics/support/frame_def.h"
#include "ballistica/base/graphics/support/render_command_buffer.h"
#include "ballistica/shared/foundation/object.h"
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

  /// Given a distance out in front of a pass's camera, returns the
  /// beauty-pass z-buffer value (0 to 1) that things that far out are
  /// drawn with.
  auto GetZBufferValueForDistance(RenderPass* pass, float dist) -> float;

  // All 3 of these must be called during a render.
  void PreprocessFrameDef(FrameDef* frame_def);
  void RenderFrameDef(FrameDef* frame_def);
  void FinishFrameDef(FrameDef* frame_def);

  /// What we hold for the view being drawn right now: its buffers and
  /// the look it is set to draw with. The accessors below for such
  /// things all go through this, so drawing code gets the right
  /// view's without needing to know which view that is.
  auto view_data() const -> RenderViewRendererData* {
    assert(current_view_data_ != nullptr);
    return current_view_data_;
  }

  // This needs to be generalized.
  void SetLight(float pitch, float heading, float tz);
  void set_shadow_offset(const Vector3f& offset) {
    view_data()->shadow_offset = offset;
  }
  void set_shadow_scale(float x, float z) {
    view_data()->shadow_scale_x = x;
    view_data()->shadow_scale_z = z;
  }
  void set_shadow_ortho(bool ortho) { view_data()->shadow_ortho = ortho; }
  void set_tint(const Vector3f& val) { view_data()->tint = val; }
  void set_ambient_color(const Vector3f& val) {
    view_data()->ambient_color = val;
  }
  void set_vignette_outer(const Vector3f& val) {
    view_data()->vignette_outer = val;
  }
  void set_vignette_inner(const Vector3f& val) {
    view_data()->vignette_inner = val;
  }
  auto tint() const -> const Vector3f& { return view_data()->tint; }
  auto ambient_color() const -> const Vector3f& {
    return view_data()->ambient_color;
  }
  auto vignette_outer() const -> const Vector3f& {
    return view_data()->vignette_outer;
  }
  auto vignette_inner() const -> const Vector3f& {
    return view_data()->vignette_inner;
  }
  auto shadow_ortho() const -> bool { return view_data()->shadow_ortho; }
  auto shadow_offset() const -> const Vector3f& {
    return view_data()->shadow_offset;
  }
  auto shadow_scale_x() const -> float { return view_data()->shadow_scale_x; }
  auto shadow_scale_z() const -> float { return view_data()->shadow_scale_z; }
  auto light_tz() const -> float { return view_data()->light_tz; }
  auto light_pitch() const -> float { return view_data()->light_pitch; }
  auto light_heading() const -> float { return view_data()->light_heading; }
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
    return view_data()->camera_render_target.exists();
  }
  auto has_camera_msaa_render_target() const -> bool {
    return view_data()->camera_msaa_render_target.exists();
  }
  auto camera_render_target() -> RenderTarget* {
    assert(view_data()->camera_render_target.exists());
    return view_data()->camera_render_target.get();
  }
  auto camera_msaa_render_target() -> RenderTarget* {
    assert(view_data()->camera_msaa_render_target.exists());
    return view_data()->camera_msaa_render_target.get();
  }
  auto has_backing_render_target() const -> bool {
    return backing_render_target_.exists();
  }
  auto backing_render_target() -> RenderTarget* {
    assert(backing_render_target_.exists());
    return backing_render_target_.get();
  }
  auto screen_render_target() -> RenderTarget* {
    assert(screen_render_target_.exists());
    return screen_render_target_.get();
  }
  auto light_render_target() -> RenderTarget* {
    assert(view_data()->light_render_target.exists());
    return view_data()->light_render_target.get();
  }
  auto light_shadow_render_target() -> RenderTarget* {
    assert(view_data()->light_shadow_render_target.exists());
    return view_data()->light_shadow_render_target.get();
  }
  auto vr_overlay_flat_render_target() -> RenderTarget* {
    assert(vr_overlay_flat_render_target_.exists());
    return vr_overlay_flat_render_target_.get();
  }
  auto shadow_res() const -> int { return view_data()->shadow_res; }
  auto blur_res_count() const -> int { return view_data()->blur_res_count; }
  auto drawing_reflection() const -> bool { return drawing_reflection_; }
  void set_drawing_reflection(bool val) { drawing_reflection_ = val; }
  auto dof_near_smoothed() const -> float {
    return view_data()->dof_near_smoothed;
  }
  auto dof_far_smoothed() const -> float {
    return view_data()->dof_far_smoothed;
  }
  auto total_frames_rendered() -> int { return frames_rendered_count_; }

  /// Counts of what rendering does, for render profiling
  /// (BA_RENDER_PROFILE). Unlike timings these are exact and repeat
  /// from run to run, so they are what to compare when checking that a
  /// change hasn't made us draw less efficiently.
  struct Stats {
    /// Draws issued.
    int64_t draw_calls{};
    /// Times we started drawing into a render target.
    int64_t target_begins{};
    /// Times we cleared one (color, depth, or both).
    int64_t clears{};
    /// Buffer-to-buffer copies.
    int64_t blits{};
    /// Pixels held by offscreen render targets right now (a running
    /// total, not a per-frame count).
    int64_t target_pixels{};
  };
  auto stats() -> Stats* { return &stats_; }

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

  /// Create the data we'll hold for a view.
  virtual auto NewRenderViewData() -> Object::Ref<RenderViewRendererData> = 0;

  /// Set up anything of our own in the data held for the current
  /// view, newly made. (The main view's gets set up along with
  /// everything else in Load().)
  virtual void LoadCurrentViewData() = 0;

  /// Shadow buffer resolution for a graphics quality. Static and pure
  /// so the logic thread, which needs to know how big passes are as it
  /// builds them, gets the same answer we do.
  static auto ShadowResForQuality(GraphicsQuality quality) -> int;
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
  /// What we hold for a texture view, or nullptr if we hold nothing
  /// for it (it hasn't been drawn yet, or it is gone).
  auto GetTextureViewData(int view_id) const -> RenderViewRendererData* {
    auto i = texture_view_datas_.find(view_id);
    return i == texture_view_datas_.end() ? nullptr : i->second.get();
  }

  /// Set up what we hold for the main view. Particular renderers call
  /// this from their constructors (it can't happen in ours, as it is
  /// they who supply the data).
  void CreateMainViewData();

  /// Let go of everything we hold for views. Particular renderers
  /// call this from their destructors.
  void ReleaseViewData();

  virtual void DrawDebug() = 0;
  virtual void CheckForErrors() = 0;
  virtual void UpdateVignetteTex_(bool force) = 0;
  virtual void GenerateCameraBufferBlurPasses() = 0;
  virtual void UpdateMeshes(
      const std::vector<Object::Ref<MeshDataClientHandle>>& meshes,
      const std::vector<int8_t>& index_sizes,
      const std::vector<uint32_t>& index_draw_counts,
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

  /// A small persistent texture-backed target the screenshot path
  /// downscale-blits the (large) finished frame into, so it can read a
  /// small texture. A large glReadPixels reads back torn on ANGLE's
  /// Metal backend regardless of sync; a small one is reliable.
  /// Subclass-managed; see RendererGL::GetScreenshotReadTarget.
  Object::Ref<RenderTarget> screenshot_blit_target_;

 private:
  void UpdateLightAndShadowBuffers(FrameDef* frame_def);
  void UpdateViewQualityAndLook(FrameDef* frame_def);
  void RenderTextureViews(FrameDef* frame_def);
  void UpdateTextureViewTargets(FrameDef* frame_def);
  void DrawWorldToTexture(FrameDef* frame_def);
  void DrawWorldToTextureThroughCamera_(FrameDef* frame_def);
  void CreateCameraRenderTargets_(GraphicsQuality quality, int w, int h,
                                  int max_res);
  void RenderLightAndShadowPasses(FrameDef* frame_def);
  void UpdateSizesQualitiesAndColors(FrameDef* frame_def);
  void DrawWorldToCameraBuffer(FrameDef* frame_def);
  void UpdatePixelScaleAndBackingBuffer(FrameDef* frame_def);
  void UpdateCameraRenderTargets(FrameDef* frame_def);
  void LoadMedia(FrameDef* frame_def);
  void UpdateDOFParams(FrameDef* frame_def);

#if BA_VR_BUILD
  void VRPreprocess(FrameDef* frame_def);
  void VRUpdateForEyeRender(FrameDef* frame_def);
  void VRDrawOverlayFlatPass(FrameDef* frame_def);
#endif  // BA_VR_BUILD

#if BA_VR_BUILD

  bool vr_use_fov_tangents_{};

  // Raw values from vr system.
  VRHandsState vr_raw_hands_state_{};
  int vr_eye_{};
  int vr_viewport_x_{};
  int vr_viewport_y_{};
  float vr_fov_l_tan_{1.0f};
  float vr_fov_r_tan_{1.0f};
  float vr_fov_b_tan_{1.0f};
  float vr_fov_t_tan_{1.0f};
  float vr_fov_degrees_x_{30.0f};
  float vr_fov_degrees_y_{30.0f};
  float vr_eye_x_{};
  float vr_eye_y_{};
  float vr_eye_z_{};
  float vr_eye_yaw_{};
  float vr_eye_pitch_{};
  float vr_eye_roll_{};
  float vr_raw_head_tx_{};
  float vr_raw_head_ty_{};
  float vr_raw_head_tz_{};
  float vr_raw_head_yaw_{};
  float vr_raw_head_pitch_{};
  float vr_raw_head_roll_{};
  Matrix44f vr_base_transform_{kMatrix44fIdentity};
  Matrix44f vr_transform_right_hand_{kMatrix44fIdentity};
  Matrix44f vr_transform_left_hand_{kMatrix44fIdentity};
  Matrix44f vr_transform_head_{kMatrix44fIdentity};
#endif  // BA_VR_BUILD

  // The *actual* current quality (set based on the currently-rendering
  // frame_def)
  GraphicsQuality last_render_quality_{GraphicsQuality::kLow};
  bool debug_draw_mode_{};
  bool screen_size_dirty_{};
  bool msaa_enabled_dirty_{};
  bool dof_delay_{true};
  bool drawing_reflection_{};

  int last_commands_buffer_size_{};
  int last_f_vals_buffer_size_{};
  int last_i_vals_buffer_size_{};
  int last_meshes_buffer_size_{};
  int last_textures_buffer_size_{};
  int frames_rendered_count_{};

  float screen_gamma_{1.0f};
  float pixel_scale_requested_{1.0f};
  float pixel_scale_{1.0f};
  Stats stats_;

  millisecs_t last_screen_gamma_update_time_{};

  // What we hold for the main game world's view, and for whichever
  // view is being drawn right now.
  Object::Ref<RenderViewRendererData> main_view_data_;
  RenderViewRendererData* current_view_data_{};

  // What we hold for views drawing to textures, by view id.
  std::unordered_map<int, Object::Ref<RenderViewRendererData>>
      texture_view_datas_;

  Object::Ref<RenderTarget> screen_render_target_;
  Object::Ref<RenderTarget> backing_render_target_;
  Object::Ref<RenderTarget> vr_overlay_flat_render_target_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_RENDERER_RENDERER_H_
