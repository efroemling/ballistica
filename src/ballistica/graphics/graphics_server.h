// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GRAPHICS_GRAPHICS_SERVER_H_
#define BALLISTICA_GRAPHICS_GRAPHICS_SERVER_H_

#include <list>
#include <memory>
#include <string>
#include <vector>

#include "ballistica/ballistica.h"
#include "ballistica/core/module.h"
#include "ballistica/core/object.h"
#include "ballistica/math/matrix44f.h"

namespace ballistica {

// Runs in the main thread and renders frame_defs shipped to it by the
// Graphics
class GraphicsServer : public Module {
 public:
  explicit GraphicsServer(Thread* thread);
  auto PushSetScreenGammaCall(float gamma) -> void;
  auto PushSetScreenPixelScaleCall(float pixel_scale) -> void;
  auto PushSetVSyncCall(bool sync, bool auto_sync) -> void;
  auto PushSetScreenCall(bool fullscreen, int width, int height,
                         TextureQuality texture_quality,
                         GraphicsQuality graphics_quality,
                         const std::string& android_res) -> void;
  auto PushReloadMediaCall() -> void;
  auto PushRemoveRenderHoldCall() -> void;
  auto PushComponentUnloadCall(
      const std::vector<Object::Ref<MediaComponentData>*>& components) -> void;
  auto SetRenderHold() -> void;

  // Used by the game thread to pass frame-defs to the graphics server
  // for rendering.
  auto SetFrameDef(FrameDef* framedef) -> void;

  // returns the next frame_def needing to be rendered, waiting for it to arrive
  // if necessary. this can return nullptr if no frame_defs come in within a
  // reasonable amount of time. a frame_def here *must* be rendered and disposed
  // of using the RenderFrameDef* calls
  auto GetRenderFrameDef() -> FrameDef*;

  auto RunFrameDefMeshUpdates(FrameDef* frame_def) -> void;

  // renders shadow passes and other common parts of a frame_def
  auto PreprocessRenderFrameDef(FrameDef* frame_def) -> void;

  // Does the default drawing to the screen, either from the left or right
  // stereo eye or in mono.
  auto DrawRenderFrameDef(FrameDef* frame_def, int eye = -1) -> void;

  // Clean up the frame_def once done drawing it.
  auto FinishRenderFrameDef(FrameDef* frame_def) -> void;

  // Equivalent to calling GetRenderFrameDef() and then preprocess, draw (in
  // mono), and finish.
  auto TryRender() -> void;

  // init the modelview matrix to look here
  auto SetCamera(const Vector3f& eye, const Vector3f& target,
                 const Vector3f& up) -> void;
  auto SetOrthoProjection(float left, float right, float bottom, float top,
                          float near, float far) -> void;
  auto ModelViewReset() -> void {
    model_view_matrix_ = kMatrix44fIdentity;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
    model_view_stack_.clear();
  }
  auto SetProjectionMatrix(const Matrix44f& p) -> void {
    projection_matrix_ = p;
    model_view_projection_matrix_dirty_ = true;
    projection_matrix_state_++;
  }
  auto projection_matrix_state() -> uint32_t {
    return projection_matrix_state_;
  }

  auto SetLightShadowProjectionMatrix(const Matrix44f& p) -> void {
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
  auto SetModelViewMatrix(const Matrix44f& m) -> void {
    model_view_matrix_ = m;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto projection_matrix() const -> const Matrix44f& {
    return projection_matrix_;
  }
  auto PushTransform() -> void {
    model_view_stack_.push_back(model_view_matrix_);
    assert(model_view_stack_.size() < 20);
  }

  auto PopTransform() -> void {
    assert(!model_view_stack_.empty());
    model_view_matrix_ = model_view_stack_.back();
    model_view_stack_.pop_back();
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto Translate(const Vector3f& t) -> void {
    model_view_matrix_ = Matrix44fTranslate(t) * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto Rotate(float angle, const Vector3f& axis) -> void {
    model_view_matrix_ = Matrix44fRotate(axis, angle) * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto MultMatrix(const Matrix44f& m) -> void {
    model_view_matrix_ = m * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto scale(const Vector3f& s) -> void {
    model_view_matrix_ = Matrix44fScale(s) * model_view_matrix_;
    model_view_projection_matrix_dirty_ = model_world_matrix_dirty_ = true;
  }

  auto RebuildLostContext() -> void;
  ~GraphicsServer() override;

  auto renderer() { return renderer_; }
  auto quality() const -> GraphicsQuality {
    assert(graphics_quality_set_);
    return quality_actual_;
  }

  auto texture_quality() const -> TextureQuality {
    assert(texture_quality_set_);
    return texture_quality_actual_;
  }

  auto screen_pixel_width() const -> float {
    assert(InMainThread());
    return res_x_;
  }
  auto screen_pixel_height() const -> float {
    assert(InMainThread());
    return res_y_;
  }

  auto screen_virtual_width() const -> float {
    assert(InMainThread());
    return res_x_virtual_;
  }
  auto screen_virtual_height() const -> float {
    assert(InMainThread());
    return res_y_virtual_;
  }
  auto set_tv_border(bool val) -> void {
    assert(InMainThread());
    tv_border_ = val;
  }
  auto tv_border() const {
    assert(InMainThread());
    return tv_border_;
  }

  auto graphics_quality_set() const { return graphics_quality_set_; }
  auto texture_quality_set() const { return texture_quality_set_; }

  auto SupportsTextureCompressionType(TextureCompressionType t) const -> bool {
    assert(texture_compression_types_set_);
    return ((texture_compression_types_ & (0x01u << static_cast<uint32_t>(t)))
            != 0u);
  }
  auto SetTextureCompressionTypes(
      const std::list<TextureCompressionType>& types) -> void;

  auto texture_compression_types_are_set() const {
    return texture_compression_types_set_;
  }
  auto set_renderer_context_lost(bool lost) -> auto {
    renderer_context_lost_ = lost;
  }
  auto renderer_context_lost() const { return renderer_context_lost_; }
  auto fullscreen_enabled() const { return fullscreen_enabled_; }

  // This doesn't actually toggle fullscreen. It is used to inform the game
  // when fullscreen changes under it.
  auto set_fullscreen_enabled(bool fs) -> void { fullscreen_enabled_ = fs; }
  auto VideoResize(float h, float v) -> void;

#if BA_ENABLE_OPENGL
  auto gl_context() const -> GLContext* { return gl_context_.get(); }
#endif

  auto graphics_quality_requested() const { return quality_requested_; }
  auto texture_quality_requested() const { return texture_quality_requested_; }
  auto renderer() const { return renderer_; }
  auto initial_screen_created() const { return initial_screen_created_; }

 private:
  auto HandleFullscreenToggling(bool do_set_existing_fs, bool do_toggle_fs,
                                bool fullscreen) -> void;
  auto HandlePushAndroidRes(const std::string& android_res) -> void;
  auto HandleFullContextScreenRebuild(
      bool need_full_context_rebuild, bool fullscreen, int width, int height,
      GraphicsQuality graphics_quality_requested,
      TextureQuality texture_quality_requested) -> void;

  // Update virtual screen dimensions based on the current physical ones.
  static auto CalcVirtualRes(float* x, float* y) -> void;

  auto UpdateVirtualScreenRes() -> void;
  auto UpdateCamOrientMatrix() -> void;
  auto ReloadMedia() -> void;
  auto UpdateModelViewProjectionMatrix() -> void {
    if (model_view_projection_matrix_dirty_) {
      model_view_projection_matrix_ = model_view_matrix_ * projection_matrix_;
      model_view_projection_matrix_state_++;
      model_view_projection_matrix_dirty_ = false;
    }
  }
  auto UpdateModelWorldMatrix() -> void {
    if (model_world_matrix_dirty_) {
      model_world_matrix_ = model_view_matrix_ * view_world_matrix_;
      model_world_matrix_state_++;
      model_world_matrix_dirty_ = false;
    }
  }
#if BA_ENABLE_OPENGL
  std::unique_ptr<GLContext> gl_context_;
#endif
  float res_x_{};
  float res_y_{};
  float res_x_virtual_{0.0f};
  float res_y_virtual_{0.0f};
  bool tv_border_{};
  bool renderer_context_lost_{};
  uint32_t texture_compression_types_{};
  bool texture_compression_types_set_{};
  TextureQuality texture_quality_requested_{TextureQuality::kLow};
  TextureQuality texture_quality_actual_{TextureQuality::kLow};
  GraphicsQuality quality_requested_{GraphicsQuality::kLow};
  GraphicsQuality quality_actual_{GraphicsQuality::kLow};
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
  auto SetScreen(bool fullscreen, int width, int height,
                 TextureQuality texture_quality,
                 GraphicsQuality graphics_quality,
                 const std::string& android_res) -> void;
  Timer* render_timer_{};
  Renderer* renderer_{};
  FrameDef* frame_def_{};
  bool initial_screen_created_{};
  int render_hold_{};
#if BA_OSTYPE_MACOS && BA_XCODE_BUILD
  void FullscreenCheck();
#endif
};

}  // namespace ballistica

#endif  // BALLISTICA_GRAPHICS_GRAPHICS_SERVER_H_
