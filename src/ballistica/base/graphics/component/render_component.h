// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_RENDER_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_RENDER_COMPONENT_H_

#include <vector>

#include "ballistica/base/graphics/renderer/renderer.h"

namespace ballistica::base {

/// RenderComponents are used to assemble command streams to send to the
/// renderer. These do a lot of extra work in debug builds to make sure
/// valid commands are being constructed, so it is best to iterate on them
/// in debug mode when possible.
///
/// The general workflow with a RenderComponents is to set all 'config'
/// options at the beginning and then to issue one or more draw commands
/// after. Check the source of each call for EnsureConfiguring() or
/// EnsureDrawing() to see which is which. Flipping from configuring to
/// drawing can cause shader binding or other work to be done in the
/// graphics api, so switches back and forth should be minimized.
///
/// RenderComponent output goes to a specific draw list in the renderer.
/// Depending on the type of RenderPass, there may be a single draw-list,
/// transparent and opaque draw-lists, draw-lists for different shaders,
/// etc. RenderComponents currently must be sure to only draw to a single
/// draw list; otherwise things like PushTransform/PopTransforms may affect
/// different draw lists. Stay tuned for this system to evolve into
/// something more foolproof.
class RenderComponent {
 private:
  class ScopedTransformObj_ {
   public:
    explicit ScopedTransformObj_(RenderComponent* c) : c_{c} {
      c_->PushTransform();
    }
    ~ScopedTransformObj_() { c_->PopTransform(); }

   private:
    RenderComponent* c_;
  };

  class ScopedScissorObj_ {
   public:
    explicit ScopedScissorObj_(RenderComponent* c, const Rect& r) : c_{c} {
      c_->ScissorPush(r);
    }
    ~ScopedScissorObj_() { c_->ScissorPop(); }

   private:
    RenderComponent* c_;
  };

 public:
  explicit RenderComponent(RenderPass* pass) : pass_(pass) {
    assert(g_base->InLogicThread());
  }

  ~RenderComponent() {
    assert(g_base->InLogicThread());

    if (state_ != State::kSubmitted) {
      Submit();
    }
  }

  /// End current drawing by this component. This is implicitly done when a
  /// component goes out of scope, but one may choose to do this explicitly
  /// to allow other components to draw while this one still exists (only
  /// one RenderComponent can be actively drawing in a frame-def at a time).
  void Submit() {
    if (state_ != State::kSubmitted) {
#if BA_DEBUG_BUILD
      if (state_ == State::kDrawing) {
        // If we were drawing, let the frame-def know we're done.
        assert(pass_->frame_def()->active_render_component() == this);
        pass_->frame_def()->set_active_render_component(nullptr);
      }
#endif
      state_ = State::kSubmitted;
    }
  }

  void DrawMeshAsset(MeshAsset* mesh, uint32_t flags = 0) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kDrawMeshAsset);
    cmd_buffer_->PutInt(flags);
    cmd_buffer_->PutMeshAsset(mesh);
  }

  void DrawMeshAssetInstanced(MeshAsset* mesh,
                              const std::vector<Matrix44f>& matrices,
                              int flags = 0) {
    assert(!matrices.empty());
    EnsureDrawing();
    cmd_buffer_->PutCommand(
        RenderCommandBuffer::Command::kDrawMeshAssetInstanced);
    cmd_buffer_->PutInt(flags);
    cmd_buffer_->PutMeshAsset(mesh);
    cmd_buffer_->PutMatrices(matrices);
  }

  void DrawMesh(Mesh* m, int flags = 0) {
    EnsureDrawing();
    if (m->IsValid()) {
      cmd_buffer_->frame_def()->AddMesh(m);
      cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kDrawMesh);
      cmd_buffer_->PutInt(flags);
      cmd_buffer_->PutMeshData(m->mesh_data_client_handle()->mesh_data);
    }
  }

  void DrawScreenQuad() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kDrawScreenQuad);
  }

  // Draw triangles using old-school gl format.. only for debugging and not
  // supported in all configurations.
  void BeginDebugDrawTriangles() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(
        RenderCommandBuffer::Command::kBeginDebugDrawTriangles);
  }

  void BeginDebugDrawLines() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kBeginDebugDrawLines);
  }

  void Vertex(float x, float y, float z) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kDebugDrawVertex3);
    cmd_buffer_->PutFloats(x, y, z);
  }

  void End() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kEndDebugDraw);
  }

  void PushTransform() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kPushTransform);
  }

  void PopTransform() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kPopTransform);
  }

  /// Add a transform push/pop to the component. Remember to assign the
  /// result to a variable or the pop will be immediate.
  auto ScopedTransform() -> ScopedTransformObj_ {
    return ScopedTransformObj_(this);
  }

  /// Add a scissor push/pop to the component. Remember to assign the result
  /// to a variable or the pop will be immediate.
  auto ScopedScissor(const Rect& rect) -> ScopedScissorObj_ {
    return ScopedScissorObj_(this, rect);
  }

  void Translate(float x, float y) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kTranslate2);
    cmd_buffer_->PutFloats(x, y);
  }

  void Translate(float x, float y, float z) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kTranslate3);
    cmd_buffer_->PutFloats(x, y, z);
  }

  void CursorTranslate() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kCursorTranslate);
  }

  void Rotate(float angle, float x, float y, float z) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kRotate);
    cmd_buffer_->PutFloats(angle, x, y, z);
  }

  void Scale(float x, float y) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScale2);
    cmd_buffer_->PutFloats(x, y);
  }

  void Scale(float x, float y, float z) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScale3);
    cmd_buffer_->PutFloats(x, y, z);
  }

  void ScaleUniform(float s) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScaleUniform);
    cmd_buffer_->PutFloat(s);
  }

  void MultMatrix(const float* t) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kMultMatrix);
    cmd_buffer_->PutFloatArray16(t);
  }

#if BA_VR_BUILD
  void VRTransformToRightHand() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(
        RenderCommandBuffer::Command::kTransformToRightHand);
  }

  void VRTransformToLeftHand() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kTransformToLeftHand);
  }

  void VRTransformToHead() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kTransformToHead);
  }
#endif  // BA_VR_BUILD

  void TranslateToProjectedPoint(float x, float y, float z) {
    EnsureDrawing();
    cmd_buffer_->PutCommand(
        RenderCommandBuffer::Command::kTranslateToProjectedPoint);
    cmd_buffer_->PutFloats(x, y, z);
  }

  void FlipCullFace() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kFlipCullFace);
  }

 protected:
  enum class State { kConfiguring, kDrawing, kSubmitted };
  void EnsureConfiguring() {
    if (state_ != State::kConfiguring) {
#if BA_DEBUG_BUILD
      // FIXME: currently releasing status as active-render-component here
      // but should perhaps hold on to it for consistency.
      if (state_ == State::kDrawing) {
        assert(pass_->frame_def()->active_render_component() == this);
        pass_->frame_def()->set_active_render_component(nullptr);
      }
#endif
      state_ = State::kConfiguring;
    }
  }
#if BA_DEBUG_BUILD
  void ConfigForEmptyDebugChecks(bool transparent);
  void ConfigForShadingDebugChecks(ShadingType shading_type);
#endif

  // Given a shader type, returns a buffer to write the command stream to.
  void ConfigForEmpty(bool transparent) {
#if BA_DEBUG_BUILD
    ConfigForEmptyDebugChecks(transparent);
#endif

    assert(!pass_->UsesWorldLists());
    if (transparent) {
      cmd_buffer_ = pass_->commands_flat_transparent();
    } else {
      cmd_buffer_ = pass_->commands_flat();
    }
  }

  // Given a shader type, sets up the config target buffer.
  void ConfigForShading(ShadingType shading_type) {
    // Determine which buffer to write to, etc.

#if BA_DEBUG_BUILD
    // Debugging: if we've got transparent-only or opaque-only mode flipped
    // on, make sure only those type of components are being submitted.
    ConfigForShadingDebugChecks(shading_type);
    // Also make sure only transparent stuff is going into the
    // light/shadow/overlay3D passes (we skip rendering the opaque lists
    // there since there shouldn't be anything in them, and we're not using
    // depth for those so it wouldn't be much of an optimization).
    if ((pass_->type() == RenderPass::Type::kLightPass
         || pass_->type() == RenderPass::Type::kLightShadowPass
         || pass_->type() == RenderPass::Type::kOverlay3DPass)
        && !Graphics::IsShaderTransparent(shading_type)) {
      FatalError("Opaque component submitted to light/shadow/overlay3d pass.");
    }

    // Likewise the blit pass should consist solely of opaque stuff.
    if (pass_->type() == RenderPass::Type::kBlitPass
        && Graphics::IsShaderTransparent(shading_type)) {
      FatalError("Transparent component submitted to blit pass.");
    }
#endif  // BA_DEBUG_BUILD

    // Certain passes (overlay, etc) draw objects in the order provided.
    // Other passes group by shader for efficiency.
    if (pass_->UsesWorldLists()) {
      cmd_buffer_ = pass_->GetCommands(shading_type);
    } else {
      if (Graphics::IsShaderTransparent(shading_type)) {
        cmd_buffer_ = pass_->commands_flat_transparent();
      } else {
        cmd_buffer_ = pass_->commands_flat();
      }
    }

    // Go ahead and throw down the shader command.
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kShader);
    cmd_buffer_->PutInt(static_cast<int>(shading_type));
  }

  void EnsureDrawing() {
    if (state_ != State::kDrawing) {
      WriteConfig();
      state_ = State::kDrawing;
#if BA_DEBUG_BUILD
      // Let the frame-def know we're the active component drawing to it now.
      assert(pass_->frame_def()->active_render_component() == nullptr);
      pass_->frame_def()->set_active_render_component(this);
#endif
    }
  }
  // Subclasses should override this to dump their needed data to the
  // stream.
  virtual void WriteConfig() = 0;

  RenderCommandBuffer* cmd_buffer_{};
  State state_{State::kConfiguring};
  RenderPass* pass_;

 public:
  void ScissorPush(const Rect& rect);

  void ScissorPop() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScissorPop);
  }
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_RENDER_COMPONENT_H_
