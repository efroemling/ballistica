// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_COMPONENT_RENDER_COMPONENT_H_
#define BALLISTICA_BASE_GRAPHICS_COMPONENT_RENDER_COMPONENT_H_

#include <vector>

#include "ballistica/base/graphics/renderer/renderer.h"

namespace ballistica::base {

class RenderComponent {
 public:
  class ScopedTransformObj {
   public:
    explicit ScopedTransformObj(RenderComponent* c) : c_{c} {
      c_->PushTransform();
    }
    ~ScopedTransformObj() { c_->PopTransform(); }

   private:
    RenderComponent* c_;
  };

  explicit RenderComponent(RenderPass* pass)
      : state_(State::kConfiguring), pass_(pass), cmd_buffer_(nullptr) {}
  ~RenderComponent() {
    if (state_ != State::kSubmitted) {
      Log(LogLevel::kError,
          "RenderComponent dying without submit() having been called.");
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
  // draw triangles using old-school gl format.. only for debugging
  // and not supported in all configurations
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
  void ScissorPush(const Rect& rIn);
  void ScissorPop() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kScissorPop);
  }
  void PushTransform() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kPushTransform);
  }
  void PopTransform() {
    EnsureDrawing();
    cmd_buffer_->PutCommand(RenderCommandBuffer::Command::kPopTransform);
  }
  auto ScopedTransform() -> ScopedTransformObj {
    return ScopedTransformObj(this);
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
  void Submit() {
    if (state_ != State::kSubmitted) {
      // If we were drawing, make note that we're done.
      if (state_ == State::kDrawing) {
#if BA_DEBUG_BUILD
        assert(pass_->frame_def()->defining_component());
        pass_->frame_def()->set_defining_component(false);
#endif
      }
      state_ = State::kSubmitted;
    }
  }

 protected:
  enum class State { kConfiguring, kDrawing, kSubmitted };
  void EnsureConfiguring() {
    if (state_ != State::kConfiguring) {
      // if we were drawing, make note that we're done
#if BA_DEBUG_BUILD
      if (state_ == State::kDrawing) {
        assert(pass_->frame_def()->defining_component());
        pass_->frame_def()->set_defining_component(false);
      }
#endif  // BA_DEBUG_BUILD
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
    // Debugging: if we've got transparent-only or opaque-only mode flipped on,
    // make sure only those type of components are being submitted.
#if BA_DEBUG_BUILD
    ConfigForShadingDebugChecks(shading_type);
    // Also make sure only transparent stuff is going into the
    // light/shadow/overlay3D passes (we skip rendering the opaque lists there
    // since there shouldn't be anything in them, and we're not using depth
    // for those so it wouldn't be much of an optimization..)
    if ((pass_->type() == RenderPass::Type::kLightPass
         || pass_->type() == RenderPass::Type::kLightShadowPass
         || pass_->type() == RenderPass::Type::kOverlay3DPass)
        && !Graphics::IsShaderTransparent(shading_type)) {
      throw Exception(
          "Opaque component submitted to light/shadow/overlay3d pass;"
          " not cool man.");
    }

    // Likewise the blit pass should consist solely of opaque stuff.
    if (pass_->type() == RenderPass::Type::kBlitPass
        && Graphics::IsShaderTransparent(shading_type)) {
      throw Exception(
          "Transparent component submitted to blit pass;"
          " not cool man.");
    }
#endif  // BA_DEBUG_BUILD
    // Certain passes (overlay, etc) draw objects in the order
    // provided.  Other passes group by shader for efficiency.
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
      // make sure we're the only one drawing until we're submitted
#if BA_DEBUG_BUILD
      assert(!pass_->frame_def()->defining_component());
      pass_->frame_def()->set_defining_component(true);
#endif  // BA_DEBUG_BUILD
    }
  }
  // subclasses should override this to dump
  // their needed data to the stream
  virtual void WriteConfig() = 0;

 protected:
  RenderCommandBuffer* cmd_buffer_;
  State state_;
  RenderPass* pass_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_COMPONENT_RENDER_COMPONENT_H_
