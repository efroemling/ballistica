// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GRAPHICS_SERVER_H_
#define BALLISTICA_BASE_GRAPHICS_GRAPHICS_SERVER_H_

#include <list>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/matrix44f.h"

namespace ballistica::base {

/// A mechanism used by the AppAdapter to render frame-defs shipped from the
/// logic thread. This may happen in the main thread or in other dedicated
/// thread(s) depending on the AppAdapter and environment.
class GraphicsServer {
 public:
  GraphicsServer();
  ~GraphicsServer();

  void OnMainThreadStartApp();

  /// The current renderer.
  auto renderer() const { return renderer_; }

  /// Assign a renderer.
  void set_renderer(Renderer* renderer);

  /// Load the current renderer. This will lock in various things such as
  /// quality settings and will allow renderer-specific forms of assets and
  /// other components to be created.
  void LoadRenderer();

  /// Unload the current renderer. Destroys all renderer-specific forms of
  /// assets and other components.
  void UnloadRenderer();

  /// Call this if a renderer's context has been lost. This is basically
  /// an UnloadRenderer() followed by a LoadRenderer() except that the
  /// renderer is not asked to delete components during the unload.
  void ReloadLostRenderer();

  /// Return whether the current renderer is loaded.
  auto renderer_loaded() const {
    assert(renderer_);
    return renderer_loaded_;
  }

  /// The AppAdapter should call this to inform the engine of screen size
  /// changes. Changes will be applied to the server and then sent to the
  /// logic thread to apply to various app systems (ui, etc.).
  void SetScreenResolution(float h, float v);

  /// Used by headless builds to init the graphics-server into a
  /// non-functional state.
  void SetNullGraphics();

  void PushSetScreenPixelScaleCall(float pixel_scale);
  void PushReloadMediaCall();
  void PushRemoveRenderHoldCall();
  void PushComponentUnloadCall(
      const std::vector<Object::Ref<Asset>*>& components);
  void SetRenderHold();

  /// Used by the logic thread to pass frame-defs to the graphics server for
  /// rendering.
  void EnqueueFrameDef(FrameDef* framedef);

  void ApplyFrameDefSettings(FrameDef* frame_def);

  void RunFrameDefMeshUpdates(FrameDef* frame_def);

  // Renders shadow passes and other common parts of a frame_def.
  void PreprocessRenderFrameDef(FrameDef* frame_def);

  // Does the default drawing to the screen, either from the left or right
  // stereo eye or in mono.
  void DrawRenderFrameDef(FrameDef* frame_def, int eye = -1);

  // Clean up the frame_def once done drawing it.
  void FinishRenderFrameDef(FrameDef* frame_def);

  // Attempts to wait for a frame-def to come in and render it.
  // Returns true if a frame was rendered.
  auto TryRender() -> bool;

  // Init the modelview matrix to look here.
  void SetCamera(const Vector3f& eye, const Vector3f& target,
                 const Vector3f& up);

  void SetOrthoProjection(float left, float right, float bottom, float top,
                          float near, float far);

  void ModelViewReset() {
    model_view_matrix_ = kMatrix44fIdentity;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
    model_view_stack_.clear();
  }

  void SetProjectionMatrix(const Matrix44f& p) {
    projection_matrix_ = p;
    model_view_projection_matrix_dirty_ = true;
    projection_matrix_state_++;
  }

  auto projection_matrix_state() -> uint32_t {
    return projection_matrix_state_;
  }

  void SetLightShadowProjectionMatrix(const Matrix44f& p) {
    // This will generally get repeatedly set to the same value
    // so we can do nothing most of the time.
    if (p != light_shadow_projection_matrix_) {
      light_shadow_projection_matrix_ = p;
      light_shadow_projection_matrix_state_++;
    }
  }

  auto light_shadow_projection_matrix_state() const -> uint32_t {
    return light_shadow_projection_matrix_state_;
  }

  auto light_shadow_projection_matrix() const -> const Matrix44f& {
    return light_shadow_projection_matrix_;
  }

  // Return the modelview * projection matrix.
  auto GetModelViewProjectionMatrix() -> const Matrix44f& {
    UpdateModelViewProjectionMatrix_();
    return model_view_projection_matrix_;
  }

  auto GetModelViewProjectionMatrixState() -> uint32_t {
    UpdateModelViewProjectionMatrix_();
    return model_view_projection_matrix_state_;
  }

  auto GetModelWorldMatrix() -> const Matrix44f& {
    UpdateModelWorldMatrix_();
    return model_world_matrix_;
  }

  auto GetModelWorldMatrixState() -> uint32_t {
    UpdateModelWorldMatrix_();
    return model_world_matrix_state_;
  }

  auto cam_pos() -> const Vector3f& { return cam_pos_; }

  auto cam_pos_state() -> uint32_t { return cam_pos_state_; }

  auto GetCamOrientMatrix() -> const Matrix44f& {
    UpdateCamOrientMatrix_();
    return cam_orient_matrix_;
  }

  auto GetCamOrientMatrixState() -> uint32_t {
    UpdateCamOrientMatrix_();
    return cam_orient_matrix_state_;
  }

  auto model_view_matrix() const -> const Matrix44f& {
    return model_view_matrix_;
  }

  void SetModelViewMatrix(const Matrix44f& m) {
    model_view_matrix_ = m;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto projection_matrix() const -> const Matrix44f& {
    return projection_matrix_;
  }

  void PushTransform() {
    model_view_stack_.push_back(model_view_matrix_);
    assert(model_view_stack_.size() < 20);
  }

  void PopTransform() {
    assert(!model_view_stack_.empty());
    model_view_matrix_ = model_view_stack_.back();
    model_view_stack_.pop_back();
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  void Translate(const Vector3f& t) {
    model_view_matrix_ = Matrix44fTranslate(t) * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  void Rotate(float angle, const Vector3f& axis) {
    model_view_matrix_ = Matrix44fRotate(axis, angle) * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  void MultMatrix(const Matrix44f& m) {
    model_view_matrix_ = m * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  void scale(const Vector3f& s) {
    model_view_matrix_ = Matrix44fScale(s) * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto quality() const -> GraphicsQuality {
    assert(graphics_quality_set_);
    return graphics_quality_;
  }

  auto texture_quality() const -> TextureQuality {
    assert(texture_quality_set_);
    return texture_quality_;
  }

  auto screen_pixel_width() const -> float {
    assert(InGraphicsContext_());
    return res_x_;
  }

  auto screen_pixel_height() const -> float {
    assert(InGraphicsContext_());
    return res_y_;
  }

  auto screen_virtual_width() const -> float {
    assert(InGraphicsContext_());
    return res_x_virtual_;
  }

  auto screen_virtual_height() const -> float {
    assert(InGraphicsContext_());
    return res_y_virtual_;
  }

  auto tv_border() const {
    assert(InGraphicsContext_());
    return tv_border_;
  }

  auto graphics_quality_set() const { return graphics_quality_set_; }

  auto texture_quality_set() const { return texture_quality_set_; }

  auto SupportsTextureCompressionType(TextureCompressionType t) const -> bool {
    assert(texture_compression_types_set_);
    return ((texture_compression_types_ & (0x01u << static_cast<uint32_t>(t)))
            != 0u);
  }
  void SetTextureCompressionTypes(
      const std::list<TextureCompressionType>& types);

  auto texture_compression_types_are_set() const {
    return texture_compression_types_set_;
  }

  void set_renderer_context_lost(bool lost) { renderer_context_lost_ = lost; }

  auto renderer_context_lost() const { return renderer_context_lost_; }

  // auto fullscreen_enabled() const { return fullscreen_enabled_; }

  // This doesn't actually toggle fullscreen. It is used to inform the game
  // when fullscreen changes under it.
  // auto set_fullscreen_enabled(bool fs) { fullscreen_enabled_ = fs; }

  // #if BA_ENABLE_OPENGL
  //   auto gl_context() const -> GLContext* { return gl_context_.get(); }
  // #endif

  auto graphics_quality_requested() const {
    return graphics_quality_requested_;
  }

  void set_graphics_quality_requested(GraphicsQualityRequest val) {
    graphics_quality_requested_ = val;
  }

  void set_texture_quality_requested(TextureQualityRequest val) {
    texture_quality_requested_ = val;
  }

  auto graphics_quality() const { return graphics_quality_; }

  auto texture_quality_requested() const { return texture_quality_requested_; }

  // auto initial_screen_created() const { return initial_screen_created_; }

  void HandlePushAndroidRes(const std::string& android_res);

  // void HandleFullContextScreenRebuild(
  //     bool need_full_context_rebuild, bool fullscreen,
  //     GraphicsQualityRequest graphics_quality_requested,
  //     TextureQualityRequest texture_quality_requested);
  // void HandleFullscreenToggling(bool do_set_existing_fs, bool do_toggle_fs,
  //                               bool fullscreen);

 private:
  // So we don't have to include app_adapter.h here for asserts.
  auto InGraphicsContext_() const -> bool;

  // Return the next frame_def to be rendered, waiting for it to arrive if
  // necessary. this can return nullptr if no frame_defs come in within a
  // reasonable amount of time. a frame_def here *must* be rendered and
  // disposed of using the RenderFrameDef* calls.
  auto WaitForRenderFrameDef_() -> FrameDef*;

  // Update virtual screen dimensions based on the current physical ones.
  static void CalcVirtualRes_(float* x, float* y);
  void UpdateVirtualScreenRes_();
  void UpdateCamOrientMatrix_();
  void ReloadMedia_();
  void UpdateModelViewProjectionMatrix_() {
    if (model_view_projection_matrix_dirty_) {
      model_view_projection_matrix_ = model_view_matrix_ * projection_matrix_;
      model_view_projection_matrix_state_++;
      model_view_projection_matrix_dirty_ = false;
    }
  }

  void UpdateModelWorldMatrix_() {
    if (model_world_matrix_dirty_) {
      model_world_matrix_ = model_view_matrix_ * view_world_matrix_;
      model_world_matrix_state_++;
      model_world_matrix_dirty_ = false;
    }
  }

  float res_x_{};
  float res_y_{};
  float res_x_virtual_{};
  float res_y_virtual_{};
  uint32_t texture_compression_types_{};
  TextureQualityRequest texture_quality_requested_{
      TextureQualityRequest::kUnset};
  TextureQuality texture_quality_{TextureQuality::kLow};
  GraphicsQualityRequest graphics_quality_requested_{
      GraphicsQualityRequest::kUnset};
  GraphicsQuality graphics_quality_{GraphicsQuality::kUnset};
  // bool fullscreen_enabled_{};
  // float target_res_x_{800.0f};
  // float target_res_y_{600.0f};
  Matrix44f model_view_matrix_{kMatrix44fIdentity};
  Matrix44f view_world_matrix_{kMatrix44fIdentity};
  Matrix44f projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_world_matrix_{kMatrix44fIdentity};
  std::vector<Matrix44f> model_view_stack_;
  uint32_t projection_matrix_state_{1};
  uint32_t model_view_projection_matrix_state_{1};
  uint32_t model_world_matrix_state_{1};
  Matrix44f light_shadow_projection_matrix_{kMatrix44fIdentity};
  uint32_t light_shadow_projection_matrix_state_{1};
  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  Vector3f cam_target_{0.0f, 0.0f, 0.0f};
  uint32_t cam_pos_state_{1};
  Matrix44f cam_orient_matrix_ = kMatrix44fIdentity;
  uint32_t cam_orient_matrix_state_{1};
  std::list<MeshData*> mesh_datas_;
  Timer* render_timer_{};
  Renderer* renderer_{};
  FrameDef* frame_def_{};
  // bool initial_screen_created_{};
  bool renderer_loaded_{};
  bool v_sync_{};
  bool auto_vsync_{};
  bool model_view_projection_matrix_dirty_{true};
  bool model_world_matrix_dirty_{true};
  bool graphics_quality_set_{};
  bool texture_quality_set_{};
  bool tv_border_{};
  bool renderer_context_lost_{};
  bool texture_compression_types_set_{};
  bool cam_orient_matrix_dirty_{true};
  int render_hold_{};
  std::mutex frame_def_mutex_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_GRAPHICS_SERVER_H_
