// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GRAPHICS_H_
#define BALLISTICA_BASE_GRAPHICS_GRAPHICS_H_

#include <list>
#include <map>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/support/graphics_client_context.h"
#include "ballistica/base/graphics/support/graphics_settings.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/generic/snapshot.h"
#include "ballistica/shared/math/vector2f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

const float kTVBorder = 0.075f;
const float kVRBorder = 0.085f;

// Light/shadow res is divided by this to get pure light res.
const int kLightResDiv{4};

// How we divide up our z depth spectrum:
const float kBackingDepth5{1.0f};

// Background
// blit-shapes (with cam buffer)
const float kBackingDepth4{0.9f};

// World (without cam buffer) or overlay-3d (with cam buffer)
const float kBackingDepth3C{0.65f};
const float kBackingDepth3B{0.4f};
const float kBackingDepth3{0.15f};

// Overlay-3d (without cam buffer) / overlay(vr)
const float kBackingDepth2C{0.147f};
const float kBackingDepth2B{0.143f};
const float kBackingDepth2{0.14f};

// Overlay(non-vr) // cover (vr)
const float kBackingDepth1B{0.01f};
const float kBackingDepth1{0.0f};

const float kShadowNeutral{0.5f};

// Cursor depth within the front-overlay (not related to above depths).
const float kCursorZDepth{1.0f};

// Client class for graphics operations (used from the logic thread).
class Graphics {
 public:
  Graphics();

  void OnAppStart();
  void OnAppSuspend();
  void OnAppUnsuspend();
  void OnAppShutdown();
  void OnAppShutdownComplete();
  void OnScreenSizeChange();
  void ApplyAppConfig();

  /// Should be called by the app-adapter to keep the engine informed on the
  /// drawable area it has to work with (in pixels).
  void SetScreenResolution(float x, float y);

  /// Should be called when UIScale changes.
  void OnUIScaleChange();

  void StepDisplayTime();

  auto TextureQualityFromAppConfig() -> TextureQualityRequest;
  auto GraphicsQualityFromAppConfig() -> GraphicsQualityRequest;
  auto VSyncFromAppConfig() -> VSyncRequest;

  static auto IsShaderTransparent(ShadingType c) -> bool;
  static auto CubeMapFromReflectionType(ReflectionType reflection_type)
      -> SysCubeMapTextureID;

  // Given a string, return a reflection type.
  static auto ReflectionTypeFromString(const std::string& s) -> ReflectionType;

  // ..and the opposite.
  static auto StringFromReflectionType(ReflectionType reflectionType)
      -> std::string;

  void Reset();
  void BuildAndPushFrameDef();

  virtual void ApplyCamera(FrameDef* frame_def);

  /// Called when the language changes.
  void LanguageChanged();

  void AddCleanFrameCommand(const Object::Ref<PythonContextCall>& c);
  void RunCleanFrameCommands();

  // Called when the GraphicsServer has sent us a frame-def for deletion.
  void ReturnCompletedFrameDef(FrameDef* frame_def);

  auto screen_pixel_width() const {
    assert(g_base->InLogicThread());
    return res_x_;
  }
  auto screen_pixel_height() const {
    assert(g_base->InLogicThread());
    return res_y_;
  }

  // Return the current size of the virtual screen. This value should always
  // be used for interface positioning, etc.
  auto screen_virtual_width() const {
    assert(g_base->InLogicThread());
    return res_x_virtual_;
  }
  auto screen_virtual_height() const {
    assert(g_base->InLogicThread());
    return res_y_virtual_;
  }

  // Given a point in space, returns the shadow density that should be drawn
  // into the shadow pass. Does this belong somewhere else?
  auto GetShadowDensity(float x, float y, float z) -> float;

  static void GetSafeColor(float* r, float* g, float* b,
                           float target_intensity = 0.6f);

  // Fade the local screen in or out over the given time period.
  void FadeScreen(bool to, millisecs_t time, PyObject* endcall);

  static void DrawRadialMeter(MeshIndexedSimpleFull* m, float amt);

  // Ways to add a few simple component types quickly (uses particle
  // rendering for efficient batches).
  void DrawBlotch(const Vector3f& pos, float size, float r, float g, float b,
                  float a) {
    DoDrawBlotch(&blotch_indices_, &blotch_verts_, pos, size, r, g, b, a);
  }

  void DrawBlotchSoft(const Vector3f& pos, float size, float r, float g,
                      float b, float a) {
    DoDrawBlotch(&blotch_soft_indices_, &blotch_soft_verts_, pos, size, r, g, b,
                 a);
  }

  // Draw a soft blotch on objects; not terrain.
  void DrawBlotchSoftObj(const Vector3f& pos, float size, float r, float g,
                         float b, float a) {
    DoDrawBlotch(&blotch_soft_obj_indices_, &blotch_soft_obj_verts_, pos, size,
                 r, g, b, a);
  }

  void DrawVirtualSafeAreaBounds(RenderPass* pass);
  static void GetBaseVirtualRes(float* x, float* y);

  // Enable progress bar drawing locally.
  void EnableProgressBar(bool fade_in);

  auto* camera() { return camera_.get(); }
  void ToggleManualCamera();
  void LocalCameraShake(float intensity);
  void ToggleDebugDraw();
  auto network_debug_info_display_enabled() const {
    return network_debug_display_enabled_;
  }
  void ToggleNetworkDebugDisplay();
  void SetGyroEnabled(bool enable);
  auto floor_reflection() const {
    assert(g_base->InLogicThread());
    return floor_reflection_;
  }
  void set_floor_reflection(bool val) {
    assert(g_base->InLogicThread());
    floor_reflection_ = val;
  }
  void set_shadow_offset(const Vector3f& val) {
    assert(g_base->InLogicThread());
    shadow_offset_ = val;
  }
  void set_shadow_scale(float x, float y) {
    assert(g_base->InLogicThread());
    shadow_scale_.x = x;
    shadow_scale_.y = y;
  }
  void set_shadow_ortho(bool o) {
    assert(g_base->InLogicThread());
    shadow_ortho_ = o;
  }
  auto tint() const { return tint_; }
  void set_tint(const Vector3f& val) {
    assert(g_base->InLogicThread());
    tint_ = val;
  }

  void set_ambient_color(const Vector3f& val) {
    assert(g_base->InLogicThread());
    ambient_color_ = val;
  }
  void set_vignette_outer(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vignette_outer_ = val;
  }
  void set_vignette_inner(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vignette_inner_ = val;
  }
  auto shadow_offset() const {
    assert(g_base->InLogicThread());
    return shadow_offset_;
  }
  auto shadow_scale() const {
    assert(g_base->InLogicThread());
    return shadow_scale_;
  }
  auto ambient_color() {
    assert(g_base->InLogicThread());
    return ambient_color_;
  }
  auto vignette_outer() const {
    assert(g_base->InLogicThread());
    return vignette_outer_;
  }
  auto vignette_inner() const {
    assert(g_base->InLogicThread());
    return vignette_inner_;
  }
  auto shadow_ortho() const {
    assert(g_base->InLogicThread());
    return shadow_ortho_;
  }
  void SetShadowRange(float lower_bottom, float lower_top, float upper_bottom,
                      float upper_top);
  void ReleaseFadeEndCommand();

  // Nodes that draw flat stuff into the overlay pass should query this z
  // value for where to draw in z.
  auto overlay_node_z_depth() {
    fetched_overlay_node_z_depth_ = true;
    return overlay_node_z_depth_;
  }

  // This should be called before/after drawing each node to keep the value
  // incrementing.
  void PreNodeDraw() { fetched_overlay_node_z_depth_ = false; }
  void PostNodeDraw() {
    if (fetched_overlay_node_z_depth_) {
      overlay_node_z_depth_ *= 0.99f;
    }
  }

  auto accel() const { return accel_pos_; }
  auto tilt() const { return tilt_pos_; }

  auto PixelToVirtualX(float x) const -> float {
    if (tv_border_) {
      // In this case, 0 to 1 in physical coords maps to -0.05f to 1.05f in
      // virtual.
      return (-0.5f * kTVBorder) * res_x_virtual_
             + (1.0f + kTVBorder) * res_x_virtual_ * (x / res_x_);
    }
    return x * (res_x_virtual_ / res_x_);
  }

  auto PixelToVirtualY(float y) const -> float {
    if (tv_border_) {
      // In this case, 0 to 1 in physical coords maps to -0.05f to 1.05f in
      // virtual.
      return (-0.5f * kTVBorder) * res_y_virtual_
             + (1.0f + kTVBorder) * res_y_virtual_ * (y / res_y_);
    }
    return y * (res_y_virtual_ / res_y_);
  }

  void set_internal_components_inited(bool val) {
    internal_components_inited_ = val;
  }
  void set_gyro_vals(const Vector3f& vals) { gyro_vals_ = vals; }
  auto show_net_info() const { return show_net_info_; }
  void set_show_net_info(bool val) { show_net_info_ = val; }
  auto GetDebugGraph(const std::string& name, bool smoothed) -> NetGraph*;

  // Used by meshes.
  void AddMeshDataCreate(MeshData* d);
  void AddMeshDataDestroy(MeshData* d);

  // For debugging: ensures that only transparent or opaque components are
  // submitted while enabled.
  auto drawing_transparent_only() const { return drawing_transparent_only_; }
  void set_drawing_transparent_only(bool val) {
    drawing_transparent_only_ = val;
  }

  /// Draw regular UI.
  virtual void DrawUI(FrameDef* frame_def);

  /// Draw dev console or whatever else on top of normal stuff.
  virtual void DrawDevUI(FrameDef* frame_def);

  auto drawing_opaque_only() const { return drawing_opaque_only_; }
  void set_drawing_opaque_only(bool val) { drawing_opaque_only_ = val; }

  // Handle testing values from _baclassic.value_test()
  virtual auto ValueTest(const std::string& arg, double* absval,
                         double* deltaval, double* outval) -> bool;
  virtual void DrawWorld(FrameDef* frame_def);

  void set_camera_shake_disabled(bool disabled) {
    camera_shake_disabled_ = disabled;
  }
  auto camera_shake_disabled() const { return camera_shake_disabled_; }
  void set_camera_gyro_explicitly_disabled(bool disabled) {
    camera_gyro_explicitly_disabled_ = disabled;
  }

  auto* settings() const {
    assert(g_base->InLogicThread());
    assert(settings_snapshot_.exists());
    return settings_snapshot_.get()->get();
  }

  auto GetGraphicsSettingsSnapshot() -> Snapshot<GraphicsSettings>*;

  /// Called by the graphics-server when a new client context is ready.
  void set_client_context(Snapshot<GraphicsClientContext>* context);

  void UpdatePlaceholderSettings();

  auto has_client_context() -> bool {
    return client_context_snapshot_.exists();
  }

  auto client_context() const -> const GraphicsClientContext* {
    assert(g_base->InLogicThread());
    assert(client_context_snapshot_.exists());
    return client_context_snapshot_.get()->get();
  }

  static auto GraphicsQualityFromRequest(GraphicsQualityRequest request,
                                         GraphicsQuality auto_val)
      -> GraphicsQuality;
  static auto TextureQualityFromRequest(TextureQualityRequest request,
                                        TextureQuality auto_val)
      -> TextureQuality;

  /// For temporary use from arbitrary threads. This should be removed when
  /// possible and replaced with proper safe thread-specific access patterns
  /// (so we can support switching renderers/etc.).
  auto placeholder_texture_quality() const {
    assert(client_context_snapshot_.exists());
    return texture_quality_placeholder_;
  }

  /// For temporary use in arbitrary threads. This should be removed when
  /// possible and replaced with proper safe thread-specific access patterns
  /// (so we can support switching renderers/etc.).
  auto placeholder_client_context() const -> const GraphicsClientContext* {
    // Using this from arbitrary threads is currently ok currently since
    // context never changes once set. Will need to kill this call once that
    // can happen though.
    assert(client_context_snapshot_.exists());
    return client_context_snapshot_.get()->get();
  }
  auto draw_virtual_safe_area_bounds() const {
    return draw_virtual_safe_area_bounds_;
  }
  void set_draw_virtual_safe_area_bounds(bool val) {
    draw_virtual_safe_area_bounds_ = val;
  }

  ScreenMessages* const screenmessages;

 protected:
  void UpdateScreen_();
  virtual ~Graphics();
  virtual void DoDrawFade(FrameDef* frame_def, float amt);
  static void CalcVirtualRes_(float* x, float* y);
  void DrawBoxingGlovesTest(FrameDef* frame_def);
  void DrawBlotches(FrameDef* frame_def);
  void DrawCursor(FrameDef* frame_def);
  void DrawFades(FrameDef* frame_def);
  void DrawDebugBuffers(RenderPass* pass);
  void UpdateAndDrawOnlyProgressBar(FrameDef* frame_def);
  void DoDrawBlotch(std::vector<uint16_t>* indices,
                    std::vector<VertexSprite>* verts, const Vector3f& pos,
                    float size, float r, float g, float b, float a);
  auto GetEmptyFrameDef() -> FrameDef*;
  void InitInternalComponents(FrameDef* frame_def);
  void DrawMiscOverlays(FrameDef* frame_def);
  void DrawLoadDot(RenderPass* pass);
  void ClearFrameDefDeleteList();
  void DrawProgressBar(RenderPass* pass, float opacity);
  void UpdateProgressBarProgress(float target);
  void UpdateGyro(microsecs_t time, microsecs_t elapsed);
  void UpdateInitialGraphicsSettingsSend_();

  int last_total_frames_rendered_{};
  int last_fps_{};
  int progress_bar_loads_{};
  int frame_def_count_{};
  int frame_def_count_filtered_{};
  int next_settings_index_{};
  TextureQuality texture_quality_placeholder_{};
  bool drawing_transparent_only_{};
  bool drawing_opaque_only_{};
  bool internal_components_inited_{};
  bool fade_out_{true};
  bool progress_bar_{};
  bool progress_bar_fade_in_{};
  bool debug_draw_{};
  bool network_debug_display_enabled_{};
  bool hardware_cursor_visible_{};
  bool camera_shake_disabled_{};
  bool camera_gyro_explicitly_disabled_{};
  bool gyro_enabled_{true};
  bool show_fps_{};
  bool show_ping_{};
  bool show_net_info_{};
  bool tv_border_{};
  bool floor_reflection_{};
  bool building_frame_def_{};
  bool shadow_ortho_{};
  bool fetched_overlay_node_z_depth_{};
  bool gyro_broken_{};
  bool set_fade_start_on_next_draw_{};
  bool graphics_settings_dirty_{true};
  bool applied_app_config_{};
  bool sent_initial_graphics_settings_{};
  bool got_screen_resolution_{};
  bool draw_virtual_safe_area_bounds_{};
  Vector3f shadow_offset_{0.0f, 0.0f, 0.0f};
  Vector2f shadow_scale_{1.0f, 1.0f};
  Vector3f tint_{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer_{0.0f, 0.0f, 0.0f};
  Vector3f vignette_inner_{1.0f, 1.0f, 1.0f};
  Vector3f jitter_{0.0f, 0.0f, 0.0f};
  Vector3f accel_smoothed_{0.0f, 0.0f, 0.0f};
  Vector3f accel_smoothed2_{0.0f, 0.0f, 0.0f};
  Vector3f accel_hi_pass_{0.0f, 0.0f, 0.0f};
  Vector3f accel_vel_{0.0f, 0.0f, 0.0f};
  Vector3f accel_pos_{0.0f, 0.0f, 0.0f};
  Vector3f tilt_smoothed_{0.0f, 0.0f, 0.0f};
  Vector3f tilt_vel_{0.0f, 0.0f, 0.0f};
  Vector3f tilt_pos_{0.0f, 0.0f, 0.0f};
  Vector3f gyro_vals_{0.0f, 0.0, 0.0f};
  std::string fps_string_;
  std::string ping_string_;
  std::string net_info_string_;
  std::map<std::string, Object::Ref<NetGraph>> debug_graphs_;
  std::mutex frame_def_delete_list_mutex_;
  std::list<Object::Ref<PythonContextCall>> clean_frame_commands_;
  std::vector<FrameDef*> recycle_frame_defs_;
  std::vector<uint16_t> blotch_indices_;
  std::vector<VertexSprite> blotch_verts_;
  std::vector<uint16_t> blotch_soft_indices_;
  std::vector<VertexSprite> blotch_soft_verts_;
  std::vector<uint16_t> blotch_soft_obj_indices_;
  std::vector<VertexSprite> blotch_soft_obj_verts_;
  std::vector<FrameDef*> frame_def_delete_list_;
  std::vector<MeshData*> mesh_data_creates_;
  std::vector<MeshData*> mesh_data_destroys_;
  float fade_{};
  float res_x_{256.0f};
  float res_y_{256.0f};
  float res_x_virtual_{256.0f};
  float res_y_virtual_{256.0f};
  float gyro_mag_test_{};
  float overlay_node_z_depth_{};
  float progress_bar_progress_{};
  float shadow_lower_bottom_{-4.0f};
  float shadow_lower_top_{4.0f};
  float shadow_upper_bottom_{30.0f};
  float shadow_upper_top_{40.0f};
  seconds_t last_cursor_visibility_event_time_{};
  millisecs_t fade_start_{};
  millisecs_t fade_cancel_start_{};
  millisecs_t fade_cancel_last_real_ms_{};
  millisecs_t fade_time_{};
  millisecs_t next_stat_update_time_{};
  millisecs_t progress_bar_end_time_{-9999};
  millisecs_t last_progress_bar_draw_time_{};
  millisecs_t last_progress_bar_start_time_{};
  millisecs_t last_create_frame_def_time_millisecs_{};
  millisecs_t last_jitter_update_time_{};
  microsecs_t last_suppress_gyro_time_{};
  microsecs_t next_frame_number_filtered_increment_time_{};
  microsecs_t last_create_frame_def_time_microsecs_{};
  Object::Ref<ImageMesh> screen_mesh_;
  Object::Ref<ImageMesh> progress_bar_bottom_mesh_;
  Object::Ref<ImageMesh> progress_bar_top_mesh_;
  Object::Ref<ImageMesh> load_dot_mesh_;
  Object::Ref<TextGroup> fps_text_group_;
  Object::Ref<TextGroup> ping_text_group_;
  Object::Ref<TextGroup> net_info_text_group_;
  Object::Ref<SpriteMesh> shadow_blotch_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_obj_mesh_;
  Object::Ref<Camera> camera_;
  Object::Ref<PythonContextCall> fade_end_call_;
  Object::Ref<Snapshot<GraphicsSettings>> settings_snapshot_;
  Object::Ref<Snapshot<GraphicsClientContext>> client_context_snapshot_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_GRAPHICS_H_
