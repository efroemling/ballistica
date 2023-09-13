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

/// A server that runs in the graphics thread and renders frame_defs shipped
/// to it by the logic thread.
class GraphicsServer {
 public:
  GraphicsServer();

  void OnMainThreadStartApp();

  /// Should be called to inform ballistica of screen size changes; this
  /// will be applied to the server and then sent to the logic thread to
  /// apply to various app systems (ui, etc.).
  void SetScreenResolution(float h, float v);

  void PushSetScreenGammaCall(float gamma);
  void PushSetScreenPixelScaleCall(float pixel_scale);
  void PushSetVSyncCall(bool sync, bool auto_sync);
  void PushSetScreenCall(bool fullscreen, int width, int height,
                         TextureQualityRequest texture_quality_request,
                         GraphicsQualityRequest graphics_quality_request,
                         const std::string& android_res);
  void PushReloadMediaCall();
  void PushRemoveRenderHoldCall();
  void PushComponentUnloadCall(
      const std::vector<Object::Ref<Asset>*>& components);
  void SetRenderHold();

  /// Used by the logic thread to pass frame-defs to the graphics server for
  /// rendering.
  void EnqueueFrameDef(FrameDef* framedef);

  // Returns the next frame_def to be rendered, waiting for it to arrive if
  // necessary. this can return nullptr if no frame_defs come in within a
  // reasonable amount of time. a frame_def here *must* be rendered and
  // disposed of using the RenderFrameDef* calls.
  auto GetRenderFrameDef() -> FrameDef*;

  void ApplyFrameDefSettings(FrameDef* frame_def);

  void RunFrameDefMeshUpdates(FrameDef* frame_def);

  // renders shadow passes and other common parts of a frame_def
  void PreprocessRenderFrameDef(FrameDef* frame_def);

  // Does the default drawing to the screen, either from the left or right
  // stereo eye or in mono.
  void DrawRenderFrameDef(FrameDef* frame_def, int eye = -1);

  // Clean up the frame_def once done drawing it.
  void FinishRenderFrameDef(FrameDef* frame_def);

  // Equivalent to calling GetRenderFrameDef() and then preprocess, draw (in
  // mono), and finish.
  void TryRender();

  // init the modelview matrix to look here
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

  // Returns the modelview * projection matrix.
  auto GetModelViewProjectionMatrix() -> const Matrix44f& {
    UpdateModelViewProjectionMatrix();
    return model_view_projection_matrix_;
  }

  auto GetModelViewProjectionMatrixState() -> uint32_t {
    UpdateModelViewProjectionMatrix();
    return model_view_projection_matrix_state_;
  }

  auto GetModelWorldMatrix() -> const Matrix44f& {
    UpdateModelWorldMatrix();
    return model_world_matrix_;
  }

  auto GetModelWorldMatrixState() -> uint32_t {
    UpdateModelWorldMatrix();
    return model_world_matrix_state_;
  }

  auto cam_pos() -> const Vector3f& { return cam_pos_; }
  auto cam_pos_state() -> uint32_t { return cam_pos_state_; }
  auto GetCamOrientMatrix() -> const Matrix44f& {
    UpdateCamOrientMatrix();
    return cam_orient_matrix_;
  }

  auto GetCamOrientMatrixState() -> uint32_t {
    UpdateCamOrientMatrix();
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

  void RebuildLostContext();
  ~GraphicsServer();

  auto renderer() { return renderer_; }
  auto quality() const -> GraphicsQuality {
    assert(graphics_quality_set_);
    return graphics_quality_;
  }

  auto texture_quality() const -> TextureQuality {
    assert(texture_quality_set_);
    return texture_quality_;
  }

  auto screen_pixel_width() const -> float {
    assert(g_base->InGraphicsThread());
    return res_x_;
  }
  auto screen_pixel_height() const -> float {
    assert(g_base->InGraphicsThread());
    return res_y_;
  }

  auto screen_virtual_width() const -> float {
    assert(g_base->InGraphicsThread());
    return res_x_virtual_;
  }
  auto screen_virtual_height() const -> float {
    assert(g_base->InGraphicsThread());
    return res_y_virtual_;
  }
  auto tv_border() const {
    assert(g_base->InGraphicsThread());
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
  auto set_renderer_context_lost(bool lost) { renderer_context_lost_ = lost; }
  auto renderer_context_lost() const { return renderer_context_lost_; }
  auto fullscreen_enabled() const { return fullscreen_enabled_; }

  // This doesn't actually toggle fullscreen. It is used to inform the game
  // when fullscreen changes under it.
  auto set_fullscreen_enabled(bool fs) { fullscreen_enabled_ = fs; }

#if BA_ENABLE_OPENGL
  auto gl_context() const -> GLContext* { return gl_context_.get(); }
#endif

  auto graphics_quality_requested() const {
    return graphics_quality_requested_;
  }
  auto graphics_quality() const { return graphics_quality_; }
  auto texture_quality_requested() const { return texture_quality_requested_; }
  auto renderer() const { return renderer_; }
  auto initial_screen_created() const { return initial_screen_created_; }
  auto event_loop() const -> EventLoop* { return event_loop_; }

 private:
  void HandleFullscreenToggling(bool do_set_existing_fs, bool do_toggle_fs,
                                bool fullscreen);
  void HandlePushAndroidRes(const std::string& android_res);
  void HandleFullContextScreenRebuild(
      bool need_full_context_rebuild, bool fullscreen, int width, int height,
      GraphicsQualityRequest graphics_quality_requested,
      TextureQualityRequest texture_quality_requested);

  // Update virtual screen dimensions based on the current physical ones.
  static void CalcVirtualRes(float* x, float* y);

  void UpdateVirtualScreenRes();
  void UpdateCamOrientMatrix();
  void ReloadMedia();
  void UpdateModelViewProjectionMatrix() {
    if (model_view_projection_matrix_dirty_) {
      model_view_projection_matrix_ = model_view_matrix_ * projection_matrix_;
      model_view_projection_matrix_state_++;
      model_view_projection_matrix_dirty_ = false;
    }
  }
  void UpdateModelWorldMatrix() {
    if (model_world_matrix_dirty_) {
      model_world_matrix_ = model_view_matrix_ * view_world_matrix_;
      model_world_matrix_state_++;
      model_world_matrix_dirty_ = false;
    }
  }
  void SetScreen(bool fullscreen, int width, int height,
                 TextureQualityRequest texture_quality_request,
                 GraphicsQualityRequest graphics_quality_request,
                 const std::string& android_res);

#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  void FullscreenCheck();
#endif
#if BA_ENABLE_OPENGL
  std::unique_ptr<GLContext> gl_context_;
#endif
  EventLoop* event_loop_{};
  float res_x_{};
  float res_y_{};
  float res_x_virtual_{};
  float res_y_virtual_{};
  bool tv_border_{};
  bool renderer_context_lost_{};
  uint32_t texture_compression_types_{};
  bool texture_compression_types_set_{};
  TextureQualityRequest texture_quality_requested_{
      TextureQualityRequest::kUnset};
  TextureQuality texture_quality_{TextureQuality::kLow};
  GraphicsQualityRequest graphics_quality_requested_{
      GraphicsQualityRequest::kUnset};
  GraphicsQuality graphics_quality_{GraphicsQuality::kUnset};
  bool graphics_quality_set_{};
  bool texture_quality_set_{};
  bool fullscreen_enabled_{};
  float target_res_x_{800.0f};
  float target_res_y_{600.0f};
  Matrix44f model_view_matrix_{kMatrix44fIdentity};
  Matrix44f view_world_matrix_{kMatrix44fIdentity};
  Matrix44f projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_world_matrix_{kMatrix44fIdentity};
  std::vector<Matrix44f> model_view_stack_;
  uint32_t projection_matrix_state_{1};
  uint32_t model_view_projection_matrix_state_{1};
  uint32_t model_world_matrix_state_{1};
  bool model_view_projection_matrix_dirty_{true};
  bool model_world_matrix_dirty_{true};
  Matrix44f light_shadow_projection_matrix_{kMatrix44fIdentity};
  uint32_t light_shadow_projection_matrix_state_{1};
  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  Vector3f cam_target_{0.0f, 0.0f, 0.0f};
  uint32_t cam_pos_state_{1};
  Matrix44f cam_orient_matrix_ = kMatrix44fIdentity;
  uint32_t cam_orient_matrix_state_{1};
  bool cam_orient_matrix_dirty_{true};
  std::list<MeshData*> mesh_datas_;
  bool v_sync_{};
  bool auto_vsync_{};
  Timer* render_timer_{};
  Renderer* renderer_{};
  FrameDef* frame_def_{};
  bool initial_screen_created_{};
  int render_hold_{};
  std::mutex frame_def_mutex_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_GRAPHICS_SERVER_H_
