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
#include "ballistica/shared/generic/snapshot.h"
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

  void ApplySettings(const GraphicsSettings* settings);

  void PushReloadMediaCall();
  void PushRemoveRenderHoldCall();
  void PushComponentUnloadCall(
      const std::vector<Object::Ref<Asset>*>& components);
  void SetRenderHold();

  /// Used by the logic thread to pass frame-defs to the graphics server for
  /// rendering.
  void EnqueueFrameDef(FrameDef* framedef);

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

  auto projection_matrix_state() { return projection_matrix_state_; }

  void SetLightShadowProjectionMatrix(const Matrix44f& p) {
    // This will generally get repeatedly set to the same value
    // so we can do nothing most of the time.
    if (p != light_shadow_projection_matrix_) {
      light_shadow_projection_matrix_ = p;
      light_shadow_projection_matrix_state_++;
    }
  }

  auto light_shadow_projection_matrix_state() const {
    return light_shadow_projection_matrix_state_;
  }

  const auto& light_shadow_projection_matrix() const {
    return light_shadow_projection_matrix_;
  }

  // Return the modelview * projection matrix.
  const auto& GetModelViewProjectionMatrix() {
    UpdateModelViewProjectionMatrix_();
    return model_view_projection_matrix_;
  }

  auto GetModelViewProjectionMatrixState() {
    UpdateModelViewProjectionMatrix_();
    return model_view_projection_matrix_state_;
  }

  const auto& GetModelWorldMatrix() {
    UpdateModelWorldMatrix_();
    return model_world_matrix_;
  }

  auto GetModelWorldMatrixState() {
    UpdateModelWorldMatrix_();
    return model_world_matrix_state_;
  }

  const auto& cam_pos() { return cam_pos_; }

  auto cam_pos_state() { return cam_pos_state_; }

  const auto& GetCamOrientMatrix() {
    UpdateCamOrientMatrix_();
    return cam_orient_matrix_;
  }

  auto GetCamOrientMatrixState() {
    UpdateCamOrientMatrix_();
    return cam_orient_matrix_state_;
  }

  const auto& model_view_matrix() const { return model_view_matrix_; }

  void SetModelViewMatrix(const Matrix44f& m) {
    model_view_matrix_ = m;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  const auto& projection_matrix() const { return projection_matrix_; }

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

  auto quality() const {
    assert(InGraphicsContext_());
    assert(graphics_quality_ != GraphicsQuality::kUnset);
    return graphics_quality_;
  }

  auto texture_quality() const {
    assert(InGraphicsContext_());
    assert(texture_quality_ != TextureQuality::kUnset);
    return texture_quality_;
  }

  auto screen_pixel_width() const {
    assert(InGraphicsContext_());
    return res_x_;
  }

  auto screen_pixel_height() const {
    assert(InGraphicsContext_());
    return res_y_;
  }

  auto screen_virtual_width() const {
    assert(InGraphicsContext_());
    return res_x_virtual_;
  }

  auto screen_virtual_height() const {
    assert(InGraphicsContext_());
    return res_y_virtual_;
  }

  auto tv_border() const {
    assert(InGraphicsContext_());
    return tv_border_;
  }

  auto SupportsTextureCompressionType(TextureCompressionType t) const -> bool {
    assert(InGraphicsContext_());
    assert(texture_compression_types_set_);
    return ((texture_compression_types_ & (0x01u << static_cast<uint32_t>(t)))
            != 0u);
  }

  void SetTextureCompressionTypes(
      const std::list<TextureCompressionType>& types);

  void set_renderer_context_lost(bool lost) { renderer_context_lost_ = lost; }

  auto renderer_context_lost() const { return renderer_context_lost_; }

  auto graphics_quality_requested() const {
    assert(InGraphicsContext_());
    return graphics_quality_requested_;
  }

  void set_graphics_quality_requested(GraphicsQualityRequest val) {
    assert(InGraphicsContext_());
    graphics_quality_requested_ = val;
  }

  void set_texture_quality_requested(TextureQualityRequest val) {
    assert(InGraphicsContext_());
    texture_quality_requested_ = val;
  }

  auto graphics_quality() const {
    assert(InGraphicsContext_());
    return graphics_quality_;
  }

  auto texture_quality_requested() const {
    assert(InGraphicsContext_());
    return texture_quality_requested_;
  }

  auto texture_compression_types() const {
    assert(texture_compression_types_set_);
    return texture_compression_types_;
  }

  /// Start spinning down the graphics server/etc.
  void Shutdown();

  auto shutdown_completed() const { return shutdown_completed_; }

 private:
  /// Pass a freshly allocated GraphicsContext instance, which the graphics
  /// system will take ownership of.
  void set_client_context(GraphicsClientContext* context);

  // So we don't have to include app_adapter.h here for asserts.
  auto InGraphicsContext_() const -> bool;

  // Return the next frame_def to be rendered, waiting for it to arrive if
  // necessary. this can return nullptr if no frame_defs come in within a
  // reasonable amount of time. a frame_def here *must* be rendered and
  // disposed of using the RenderFrameDef* calls.
  auto WaitForRenderFrameDef_() -> FrameDef*;

  // Update virtual screen dimensions based on the current physical ones.
  // static void CalcVirtualRes_(float* x, float* y);
  // void UpdateVirtualScreenRes_();
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

  TextureQualityRequest texture_quality_requested_{};
  TextureQuality texture_quality_{};
  GraphicsQualityRequest graphics_quality_requested_{};
  GraphicsQuality graphics_quality_{};
  bool renderer_loaded_{};
  bool model_view_projection_matrix_dirty_{true};
  bool model_world_matrix_dirty_{true};
  bool tv_border_{};
  bool renderer_context_lost_{};
  bool texture_compression_types_set_{};
  bool cam_orient_matrix_dirty_{true};
  bool shutting_down_{};
  bool shutdown_completed_{};
  float res_x_{};
  float res_y_{};
  float res_x_virtual_{};
  float res_y_virtual_{};
  Matrix44f model_view_matrix_{kMatrix44fIdentity};
  Matrix44f view_world_matrix_{kMatrix44fIdentity};
  Matrix44f projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_view_projection_matrix_{kMatrix44fIdentity};
  Matrix44f model_world_matrix_{kMatrix44fIdentity};
  uint32_t texture_compression_types_{};
  int render_hold_{};
  int projection_matrix_state_{};
  int model_view_projection_matrix_state_{};
  int model_world_matrix_state_{};
  int light_shadow_projection_matrix_state_{};
  int cam_pos_state_{};
  int cam_orient_matrix_state_{};
  int settings_index_{-1};
  Vector3f cam_pos_{0.0f, 0.0f, 0.0f};
  Vector3f cam_target_{0.0f, 0.0f, 0.0f};
  Matrix44f light_shadow_projection_matrix_{kMatrix44fIdentity};
  Matrix44f cam_orient_matrix_ = kMatrix44fIdentity;
  Snapshot<GraphicsClientContext>* client_context_{};
  std::vector<Matrix44f> model_view_stack_;
  std::list<MeshData*> mesh_datas_;
  Renderer* renderer_{};
  FrameDef* frame_def_{};
  std::mutex frame_def_mutex_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_GRAPHICS_SERVER_H_
