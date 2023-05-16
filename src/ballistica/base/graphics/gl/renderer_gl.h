// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_RENDERER_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_RENDERER_GL_H_

#include <memory>
#include <string>
#include <vector>

#include "ballistica/shared/ballistica.h"

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

// for now lets not go above 8 since that's what the iPhone 3gs has..
// ...haha perhaps should revisit this
constexpr int kMaxGLTexUnitsUsed = 5;

class RendererGL : public Renderer {
  class FakeVertexArrayObject;
  class TextureDataGL;
  class MeshAssetDataGL;
  class MeshDataGL;
  class MeshDataSimpleSplitGL;
  class MeshDataObjectSplitGL;
  class MeshDataSimpleFullGL;
  class MeshDataDualTextureFullGL;
  class MeshDataSmokeFullGL;
  class MeshDataSpriteGL;
  class RenderTargetGL;
  class FramebufferObjectGL;
  class ShaderGL;
  class FragmentShaderGL;
  class VertexShaderGL;
  class ProgramGL;
  class SimpleProgramGL;
  class ObjectProgramGL;
  class SmokeProgramGL;
  class BlurProgramGL;
  class ShieldProgramGL;
  class PostProcessProgramGL;
  class SpriteProgramGL;

 public:
  RendererGL();
  ~RendererGL() override;
  void Unload() override;
  void Load() override;
  void PostLoad() override;

  // our vertex attrs
  enum VertexAttr {
    kVertexAttrPosition,
    kVertexAttrUV,
    kVertexAttrNormal,
    kVertexAttrErode,
    kVertexAttrColor,
    kVertexAttrSize,
    kVertexAttrDiffuse,
    kVertexAttrUV2,
    kVertexAttrCount
  };

  void CheckCapabilities() override;
  auto GetAutoGraphicsQuality() -> GraphicsQuality override;
  auto GetAutoTextureQuality() -> TextureQuality override;
#if BA_OSTYPE_ANDROID
  std::string GetAutoAndroidRes() override;
#endif  // BA_OSTYPE_ANDROID

 protected:
  void DrawDebug() override;
  void CheckForErrors() override;
  void GenerateCameraBufferBlurPasses() override;
  void FlipCullFace() override;
  void SetDepthRange(float min, float max) override;
  void SetDepthWriting(bool enable) override;
  void SetDepthTesting(bool enable) override;
  void SetDrawAtEqualDepth(bool enable) override;
  auto NewScreenRenderTarget() -> RenderTarget* override;
  auto NewFramebufferRenderTarget(int width, int height, bool linear_interp,
                                  bool depth, bool texture,
                                  bool depth_is_texture, bool high_quality,
                                  bool msaa, bool alpha)
      -> Object::Ref<RenderTarget> override;
  auto NewMeshAssetData(const MeshAsset& mesh)
      -> Object::Ref<MeshAssetRendererData> override;
  auto NewTextureData(const TextureAsset& texture)
      -> Object::Ref<TextureAssetRendererData> override;

  auto NewMeshData(MeshDataType type, MeshDrawType drawType)
      -> MeshRendererData* override;
  void DeleteMeshData(MeshRendererData* data, MeshDataType type) override;

  void ProcessRenderCommandBuffer(RenderCommandBuffer* buffer,
                                  const RenderPass& pass,
                                  RenderTarget* render_target) override;
  void BlitBuffer(RenderTarget* src, RenderTarget* dst, bool depth,
                  bool linear_interpolation, bool force_shader_mode,
                  bool invalidate_source) override;
  void UpdateMeshes(
      const std::vector<Object::Ref<MeshDataClientHandle> >& meshes,
      const std::vector<int8_t>& index_sizes,
      const std::vector<Object::Ref<MeshBufferBase> >& buffers) override;
  void PushGroupMarker(const char* label) override;
  void PopGroupMarker() override;
  auto IsMSAAEnabled() const -> bool override;
  void InvalidateFramebuffer(bool color, bool depth,
                             bool target_read_framebuffer) override;
  void VREyeRenderBegin() override;
  void CardboardDisableScissor() override;
  void CardboardEnableScissor() override;
  void RenderFrameDefEnd() override;

#if BA_VR_BUILD
  void VRSyncRenderStates() override;
#endif  // BA_VR_BUILD

  // TEMP
  auto current_vertex_array() const -> GLuint { return current_vertex_array_; }

 private:
  void CheckFunkyDepthIssue();
  auto GetMSAASamplesForFramebuffer(int width, int height) -> int;
  void UpdateMSAAEnabled() override;
  void CheckGLExtensions();
  void UpdateVignetteTex(bool force) override;
  void StandardPostProcessSetup(PostProcessProgramGL* p,
                                const RenderPass& pass);
  void SyncGLState();
  void RetainShader(ProgramGL* p);
  void SetViewport(GLint x, GLint y, GLsizei width, GLsizei height);
  void UseProgram(ProgramGL* p);
  auto GetActiveProgram() const -> ProgramGL* {
    assert(current_program_);
    return current_program_;
  }
  void SetDoubleSided(bool d);
  void ScissorPush(const Rect& rIn, RenderTarget* render_target);
  void ScissorPop(RenderTarget* render_target);
  void BindVertexArray(GLuint v);

  // Note: This is only for use when VAOs aren't supported.
  void SetVertexAttribArrayEnabled(GLuint i, bool enabled);
  void BindTexture(GLuint type, const TextureAsset* t, GLuint tex_unit = 0);
  void BindTexture(GLuint type, GLuint tex, GLuint tex_unit = 0);
  void BindTextureUnit(uint32_t tex_unit);
  void BindFramebuffer(GLuint fb);
  void BindArrayBuffer(GLuint b);
  void SetBlend(bool b);
  void SetBlendPremult(bool b);
  millisecs_t dof_update_time_{};
  std::vector<Object::Ref<FramebufferObjectGL> > blur_buffers_;
  bool supports_depth_textures_{};
  bool first_extension_check_{true};
  bool is_tegra_4_{};
  bool is_tegra_k1_{};
  bool is_recent_adreno_{};
  bool is_adreno_{};
  bool enable_msaa_{};
  float last_cam_buffer_width_{};
  float last_cam_buffer_height_{};
  int last_blur_res_count_{};
  float vignette_tex_outer_r_{};
  float vignette_tex_outer_g_{};
  float vignette_tex_outer_b_{};
  float vignette_tex_inner_r_{};
  float vignette_tex_inner_g_{};
  float vignette_tex_inner_b_{};
  float depth_range_min_{};
  float depth_range_max_{};
  bool draw_at_equal_depth_{};
  bool depth_writing_enabled_{};
  bool depth_testing_enabled_{};
  bool data_loaded_{};
  bool draw_front_{};
  GLuint screen_framebuffer_{};
  bool got_screen_framebuffer_{};
  GLuint random_tex_{};
  GLuint vignette_tex_{};
  GraphicsQuality vignette_quality_{};
  std::vector<std::unique_ptr<ProgramGL> > shaders_;
  GLint viewport_x_{};
  GLint viewport_y_{};
  GLint viewport_width_{};
  GLint viewport_height_{};
  SimpleProgramGL* simple_color_prog_{};
  SimpleProgramGL* simple_tex_prog_{};
  SimpleProgramGL* simple_tex_dtest_prog_{};
  SimpleProgramGL* simple_tex_mod_prog_{};
  SimpleProgramGL* simple_tex_mod_flatness_prog_{};
  SimpleProgramGL* simple_tex_mod_shadow_prog_{};
  SimpleProgramGL* simple_tex_mod_shadow_flatness_prog_{};
  SimpleProgramGL* simple_tex_mod_glow_prog_{};
  SimpleProgramGL* simple_tex_mod_glow_maskuv2_prog_{};
  SimpleProgramGL* simple_tex_mod_colorized_prog_{};
  SimpleProgramGL* simple_tex_mod_colorized2_prog_{};
  SimpleProgramGL* simple_tex_mod_colorized2_masked_prog_{};
  ObjectProgramGL* obj_prog_{};
  ObjectProgramGL* obj_transparent_prog_{};
  ObjectProgramGL* obj_lightshad_transparent_prog_{};
  ObjectProgramGL* obj_refl_prog_{};
  ObjectProgramGL* obj_refl_worldspace_prog_{};
  ObjectProgramGL* obj_refl_transparent_prog_{};
  ObjectProgramGL* obj_refl_add_transparent_prog_{};
  ObjectProgramGL* obj_lightshad_prog_{};
  ObjectProgramGL* obj_lightshad_worldspace_prog_{};
  ObjectProgramGL* obj_refl_lightshad_prog_{};
  ObjectProgramGL* obj_refl_lightshad_worldspace_prog_{};
  ObjectProgramGL* obj_refl_lightshad_colorize_prog_{};
  ObjectProgramGL* obj_refl_lightshad_colorize2_prog_{};
  ObjectProgramGL* obj_refl_lightshad_add_prog_{};
  ObjectProgramGL* obj_refl_lightshad_add_colorize_prog_{};
  ObjectProgramGL* obj_refl_lightshad_add_colorize2_prog_{};
  SmokeProgramGL* smoke_prog_{};
  SmokeProgramGL* smoke_overlay_prog_{};
  SpriteProgramGL* sprite_prog_{};
  SpriteProgramGL* sprite_camalign_prog_{};
  SpriteProgramGL* sprite_camalign_overlay_prog_{};
  BlurProgramGL* blur_prog_{};
  ShieldProgramGL* shield_prog_{};
  PostProcessProgramGL* postprocess_prog_{};
  PostProcessProgramGL* postprocess_eyes_prog_{};
  PostProcessProgramGL* postprocess_distort_prog_{};
  static auto GetFunkyDepthIssue() -> bool;
  static auto GetDrawsShieldsFunny() -> bool;
  static bool funky_depth_issue_set_;
  static bool funky_depth_issue_;
  static bool draws_shields_funny_set_;
  static bool draws_shields_funny_;
#if BA_OSTYPE_ANDROID
  static bool is_speedy_android_device_;
  static bool is_extra_speedy_android_device_;
#endif  // BA_OSTYPE_ANDROID
  ProgramGL* current_program_{};
  bool double_sided_{};
  std::vector<Rect> scissor_rects_;
  GLuint current_vertex_array_{};
  bool vertex_attrib_arrays_enabled_[kVertexAttrCount]{};
  int active_tex_unit_{};
  int active_framebuffer_{};
  int active_array_buffer_{};
  int bound_textures_2d_[kMaxGLTexUnitsUsed]{};
  int bound_textures_cube_map_[kMaxGLTexUnitsUsed]{};
  bool blend_{};
  bool blend_premult_{};
  std::unique_ptr<MeshDataSimpleFullGL> screen_mesh_;
  std::vector<MeshDataSimpleSplitGL*> recycle_mesh_datas_simple_split_;
  std::vector<MeshDataObjectSplitGL*> recycle_mesh_datas_object_split_;
  std::vector<MeshDataSimpleFullGL*> recycle_mesh_datas_simple_full_;
  std::vector<MeshDataDualTextureFullGL*> recycle_mesh_datas_dual_texture_full_;
  std::vector<MeshDataSmokeFullGL*> recycle_mesh_datas_smoke_full_;
  std::vector<MeshDataSpriteGL*> recycle_mesh_datas_sprite_;
  int error_check_counter_{};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_RENDERER_GL_H_
