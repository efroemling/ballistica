// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_GRAPHICS_H_
#define BALLISTICA_GRAPHICS_GRAPHICS_H_

#include <list>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <vector>

#include "ballistica/core/object.h"
#include "ballistica/math/matrix44f.h"
#include "ballistica/math/rect.h"
#include "ballistica/math/vector2f.h"

namespace ballistica {

// Light/shadow res is divided by this to get pure light res.
const int kLightResDiv = 4;

// How we divide up our z depth spectrum:
const float kBackingDepth5 = 1.0f;

// Background
// blit-shapes (with cam buffer)
const float kBackingDepth4 = 0.9f;

// World (without cam buffer) or overlay-3d (with cam buffer)
const float kBackingDepth3C = 0.65f;
const float kBackingDepth3B = 0.4f;
const float kBackingDepth3 = 0.15f;

// Overlay-3d (without cam buffer) / overlay(vr)
const float kBackingDepth2C = 0.147f;
const float kBackingDepth2B = 0.143f;
const float kBackingDepth2 = 0.14f;

// Overlay(non-vr) // cover (vr)
const float kBackingDepth1B = 0.01f;
const float kBackingDepth1 = 0.0f;

const float kShadowNeutral = 0.5f;

// Client class for graphics operations (used from the game thread).
class Graphics {
 public:
  Graphics();
  virtual ~Graphics();

  static auto IsShaderTransparent(ShadingType c) -> bool;
  static auto CubeMapFromReflectionType(ReflectionType reflection_type)
      -> SystemCubeMapTextureID;

  // Given a string, return a reflection type.
  static auto ReflectionTypeFromString(const std::string& s) -> ReflectionType;

  // ..and the opposite.
  static auto StringFromReflectionType(ReflectionType reflectionType)
      -> std::string;

  auto Reset() -> void;
  auto BuildAndPushFrameDef() -> void;

  virtual auto ApplyCamera(FrameDef* frame_def) -> void;

  // Called when the GraphicsServer's screen configuration changes.
  auto ScreenResize(float virtual_width, float virtual_height,
                    float physical_width, float physical_height) -> void;

  // Called when the GraphicsServer has sent us a frame-def for deletion.
  auto ReturnCompletedFrameDef(FrameDef* frame_def) -> void;

  auto screen_pixel_width() const -> float { return res_x_; }
  auto screen_pixel_height() const -> float { return res_y_; }

  // Return the size of the virtual screen.  This value should always
  // be used for interface positioning, etc.
  auto screen_virtual_width() const -> float { return res_x_virtual_; }
  auto screen_virtual_height() const -> float { return res_y_virtual_; }

  auto ClearScreenMessageTranslations() -> void;

  // Given a point in space, returns the shadow density that should be drawn
  // into the shadow pass. Does this belong somewhere else?
  auto GetShadowDensity(float x, float y, float z) -> float;

  static auto GetSafeColor(float* r, float* g, float* b,
                           float target_intensity = 0.6f) -> void;

  // Print a message to the on-screen list.
  auto AddScreenMessage(const std::string& msg,
                        const Vector3f& color = Vector3f{1, 1, 1},
                        bool top = false, Texture* texture = nullptr,
                        Texture* tint_texture = nullptr,
                        const Vector3f& tint = Vector3f{1, 1, 1},
                        const Vector3f& tint2 = Vector3f{1, 1, 1}) -> void;

  // Fade the local screen in or out over the given time period.
  auto FadeScreen(bool to, millisecs_t time, PyObject* endcall) -> void;

  static auto DrawRadialMeter(MeshIndexedSimpleFull* m, float amt) -> void;

  // Ways to add a few simple component types quickly.
  // (uses particle rendering for efficient batches).
  auto DrawBlotch(const Vector3f& pos, float size, float r, float g, float b,
                  float a) -> void {
    DoDrawBlotch(&blotch_indices_, &blotch_verts_, pos, size, r, g, b, a);
  }

  auto DrawBlotchSoft(const Vector3f& pos, float size, float r, float g,
                      float b, float a) -> void {
    DoDrawBlotch(&blotch_soft_indices_, &blotch_soft_verts_, pos, size, r, g, b,
                 a);
  }

  // Draw a soft blotch on objects; not terrain.
  auto DrawBlotchSoftObj(const Vector3f& pos, float size, float r, float g,
                         float b, float a) -> void {
    DoDrawBlotch(&blotch_soft_obj_indices_, &blotch_soft_obj_verts_, pos, size,
                 r, g, b, a);
  }

  // Enable progress bar drawing locally.
  auto EnableProgressBar(bool fade_in) -> void;

  auto camera() -> Camera* { return camera_.get(); }
  auto ToggleManualCamera() -> void;
  auto LocalCameraShake(float intensity) -> void;
  auto ToggleDebugDraw() -> void;
  auto debug_info_display() const -> bool { return debug_info_display_; }
  auto ToggleDebugInfoDisplay() -> void;
  auto SetGyroEnabled(bool enable) -> void;
  auto floor_reflection() const -> bool {
    assert(InGameThread());
    return floor_reflection_;
  }
  auto set_floor_reflection(bool val) -> void {
    assert(InGameThread());
    floor_reflection_ = val;
  }
  auto set_shadow_offset(const Vector3f& val) -> void {
    assert(InGameThread());
    shadow_offset_ = val;
  }
  auto set_shadow_scale(float x, float y) -> void {
    assert(InGameThread());
    shadow_scale_.x = x;
    shadow_scale_.y = y;
  }
  auto set_shadow_ortho(bool o) -> void {
    assert(InGameThread());
    shadow_ortho_ = o;
  }
  auto tint() -> const Vector3f& { return tint_; }
  auto set_tint(const Vector3f& val) -> void {
    assert(InGameThread());
    tint_ = val;
  }

  auto set_ambient_color(const Vector3f& val) -> void {
    assert(InGameThread());
    ambient_color_ = val;
  }
  auto set_vignette_outer(const Vector3f& val) -> void {
    assert(InGameThread());
    vignette_outer_ = val;
  }
  auto set_vignette_inner(const Vector3f& val) -> void {
    assert(InGameThread());
    vignette_inner_ = val;
  }
  auto shadow_offset() const -> const Vector3f& {
    assert(InGameThread());
    return shadow_offset_;
  }
  auto shadow_scale() const -> const Vector2f& {
    assert(InGameThread());
    return shadow_scale_;
  }
  auto tint() const -> const Vector3f& {
    assert(InGameThread());
    return tint_;
  }
  auto ambient_color() const -> const Vector3f& {
    assert(InGameThread());
    return ambient_color_;
  }
  auto vignette_outer() const -> const Vector3f& {
    assert(InGameThread());
    return vignette_outer_;
  }
  auto vignette_inner() const -> const Vector3f& {
    assert(InGameThread());
    return vignette_inner_;
  }
  auto shadow_ortho() const -> bool {
    assert(InGameThread());
    return shadow_ortho_;
  }
  auto SetShadowRange(float lower_bottom, float lower_top, float upper_bottom,
                      float upper_top) -> void;
  auto ReleaseFadeEndCommand() -> void;
  auto set_show_fps(bool val) -> void { show_fps_ = val; }

  // FIXME - move to graphics_server
  auto set_tv_border(bool val) -> void {
    assert(InGameThread());
    tv_border_ = val;
  }
  auto tv_border() const -> bool {
    assert(InGameThread());
    return tv_border_;
  }

  // Nodes that draw flat stuff into the overlay pass should query this z value
  // for where to draw in z.
  auto overlay_node_z_depth() -> float {
    fetched_overlay_node_z_depth_ = true;
    return overlay_node_z_depth_;
  }

  // This should be called before/after drawing each node to keep the value
  // incrementing.
  auto PreNodeDraw() -> void { fetched_overlay_node_z_depth_ = false; }
  auto PostNodeDraw() -> void {
    if (fetched_overlay_node_z_depth_) {
      overlay_node_z_depth_ *= 0.99f;
    }
  }

  auto accel() const -> const Vector3f& { return accel_pos_; }
  auto tilt() const -> const Vector3f& { return tilt_pos_; }

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
  auto supports_high_quality_graphics() const -> bool {
    assert(has_supports_high_quality_graphics_value_);
    return supports_high_quality_graphics_;
  }
  auto SetSupportsHighQualityGraphics(bool s) -> void;
  auto has_supports_high_quality_graphics_value() const -> bool {
    return has_supports_high_quality_graphics_value_;
  }
  auto set_internal_components_inited(bool val) -> void {
    internal_components_inited_ = val;
  }
  auto set_gyro_vals(const Vector3f& vals) -> void { gyro_vals_ = vals; }
  auto show_net_info() const -> bool { return show_net_info_; }
  auto set_show_net_info(bool val) -> void { show_net_info_ = val; }
  auto debug_graph_1() const -> NetGraph* { return debug_graph_1_.get(); }
  auto debug_graph_2() const -> NetGraph* { return debug_graph_2_.get(); }

  // Used by meshes.
  auto AddMeshDataCreate(MeshData* d) -> void;
  auto AddMeshDataDestroy(MeshData* d) -> void;

  // For debugging: ensures that only transparent or opaque components
  // are submitted while enabled.
  auto drawing_transparent_only() const -> bool {
    return drawing_transparent_only_;
  }
  auto set_drawing_transparent_only(bool val) -> void {
    drawing_transparent_only_ = val;
  }

  auto drawing_opaque_only() const -> bool { return drawing_opaque_only_; }
  auto set_drawing_opaque_only(bool val) -> void { drawing_opaque_only_ = val; }

  // Handle testing values from _ba.value_test()
  virtual auto ValueTest(const std::string& arg, double* absval,
                         double* deltaval, double* outval) -> bool;
  virtual auto DrawUI(FrameDef* frame_def) -> void;
  virtual auto DrawWorld(Session* session, FrameDef* frame_def) -> void;

  auto set_camera_shake_disabled(bool disabled) -> void {
    camera_shake_disabled_ = disabled;
  }
  auto camera_shake_disabled() const { return camera_shake_disabled_; }
  auto set_camera_gyro_explicitly_disabled(bool disabled) -> void {
    camera_gyro_explicitly_disabled_ = disabled;
  }

 private:
  class ScreenMessageEntry;
  auto DrawBoxingGlovesTest(FrameDef* frame_def) -> void;
  auto DrawBlotches(FrameDef* frame_def) -> void;
  auto DrawCursor(RenderPass* pass, millisecs_t real_time) -> void;
  auto DrawFades(FrameDef* frame_def, millisecs_t real_time) -> void;
  auto DrawDebugBuffers(RenderPass* pass) -> void;
  auto WaitForRendererToExist() -> void;

  auto UpdateAndDrawProgressBar(FrameDef* frame_def, millisecs_t real_time)
      -> void;
  auto DoDrawBlotch(std::vector<uint16_t>* indices,
                    std::vector<VertexSprite>* verts, const Vector3f& pos,
                    float size, float r, float g, float b, float a) -> void;
  auto GetEmptyFrameDef() -> FrameDef*;
  auto InitInternalComponents(FrameDef* frame_def) -> void;
  auto DrawMiscOverlays(RenderPass* pass) -> void;
  auto DrawLoadDot(RenderPass* pass) -> void;
  auto ClearFrameDefDeleteList() -> void;
  auto DrawProgressBar(RenderPass* pass, float opacity) -> void;
  auto UpdateProgressBarProgress(float target) -> void;
  auto UpdateGyro(millisecs_t real_time, millisecs_t elapsed) -> void;

  bool drawing_transparent_only_{};
  bool drawing_opaque_only_{};
  std::vector<MeshData*> mesh_data_creates_;
  std::vector<MeshData*> mesh_data_destroys_;
  bool has_supports_high_quality_graphics_value_{};
  bool supports_high_quality_graphics_ = false;
  millisecs_t last_create_frame_def_time_{};
  Vector3f shadow_offset_{0.0f, 0.0f, 0.0f};
  Vector2f shadow_scale_{1.0f, 1.0f};
  bool shadow_ortho_ = false;
  Vector3f tint_{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer_{0.0f, 0.0f, 0.0f};
  Vector3f vignette_inner_{1.0f, 1.0f, 1.0f};
  std::vector<FrameDef*> recycle_frame_defs_;
  millisecs_t last_jitter_update_time_ = 0;
  Vector3f jitter_{0.0f, 0.0f, 0.0f};
  Vector3f accel_smoothed_{0.0f, 0.0f, 0.0f};
  Vector3f accel_smoothed2_{0.0f, 0.0f, 0.0f};
  Vector3f accel_hi_pass_{0.0f, 0.0f, 0.0f};
  Vector3f accel_vel_{0.0f, 0.0f, 0.0f};
  Vector3f accel_pos_{0.0f, 0.0f, 0.0f};
  Vector3f tilt_smoothed_ = {0.0f, 0.0f, 0.0f};
  Vector3f tilt_vel_{0.0f, 0.0f, 0.0f};
  Vector3f tilt_pos_{0.0f, 0.0f, 0.0f};
  bool gyro_broken_{};
  float gyro_mag_test_{};
  bool fetched_overlay_node_z_depth_{};
  float overlay_node_z_depth_{};
  bool internal_components_inited_{};
  Object::Ref<ImageMesh> screen_mesh_;
  Object::Ref<ImageMesh> progress_bar_bottom_mesh_;
  Object::Ref<ImageMesh> progress_bar_top_mesh_;
  Object::Ref<ImageMesh> load_dot_mesh_;
  Object::Ref<TextGroup> fps_text_group_;
  Object::Ref<TextGroup> net_info_text_group_;
  Object::Ref<SpriteMesh> shadow_blotch_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_obj_mesh_;
  std::string fps_string_;
  std::string net_info_string_;
  std::vector<uint16_t> blotch_indices_;
  std::vector<VertexSprite> blotch_verts_;
  std::vector<uint16_t> blotch_soft_indices_;
  std::vector<VertexSprite> blotch_soft_verts_;
  std::vector<uint16_t> blotch_soft_obj_indices_;
  std::vector<VertexSprite> blotch_soft_obj_verts_;
  bool show_fps_{};
  bool show_net_info_{};
  bool tv_border_{};
  bool floor_reflection_{};
  Object::Ref<NetGraph> debug_graph_1_;
  Object::Ref<NetGraph> debug_graph_2_;
  std::mutex frame_def_delete_list_mutex_;
  std::vector<FrameDef*> frame_def_delete_list_;
  bool debug_draw_{};
  bool debug_info_display_{};
  Object::Ref<Camera> camera_;
  millisecs_t next_stat_update_time_{};
  int last_total_frames_rendered_{};
  int last_fps_{};
  std::list<ScreenMessageEntry> screen_messages_;
  std::list<ScreenMessageEntry> screen_messages_top_;
  bool set_fade_start_on_next_draw_{};
  millisecs_t fade_start_{};
  millisecs_t fade_time_{};
  bool fade_out_{true};
  Object::Ref<PythonContextCall> fade_end_call_;
  float fade_{};
  Vector3f gyro_vals_{0.0f, 0.0, 0.0f};
  float res_x_{100};
  float res_y_{100};
  float res_x_virtual_{100};
  float res_y_virtual_{100};
  int progress_bar_loads_{};
  bool progress_bar_{};
  bool progress_bar_fade_in_{};
  millisecs_t progress_bar_end_time_{-9999};
  float progress_bar_progress_{};
  millisecs_t last_progress_bar_draw_time_{};
  millisecs_t last_progress_bar_start_time_{};
  float screen_gamma_{1.0f};
  float shadow_lower_bottom_{-4.0f};
  float shadow_lower_top_{4.0f};
  float shadow_upper_bottom_{30.0f};
  float shadow_upper_top_{40.0f};
  bool hardware_cursor_visible_{};
  bool camera_shake_disabled_{};
  bool camera_gyro_explicitly_disabled_{};
  millisecs_t last_cursor_visibility_event_time_{};
  int64_t frame_def_count_{1};
  bool gyro_enabled_{true};
  millisecs_t last_suppress_gyro_time_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_GRAPHICS_H_
