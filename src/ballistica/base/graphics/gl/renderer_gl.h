// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_GL_RENDERER_GL_H_
#define BALLISTICA_BASE_GRAPHICS_GL_RENDERER_GL_H_

#include <memory>
#include <string>
#include <vector>

#if BA_ENABLE_OPENGL

#include "ballistica/base/graphics/gl/gl_sys.h"
#include "ballistica/base/graphics/renderer/renderer.h"
#include "ballistica/shared/foundation/object.h"

// Can be handy to check GL errors on opt builds.
#define BA_FORCE_CHECK_GL_ERRORS 0

#define BA_CHECK_GL_ERROR CheckGLError(__FILE__, __LINE__)
#if BA_DEBUG_BUILD || BA_FORCE_CHECK_GL_ERRORS
#define BA_DEBUG_CHECK_GL_ERROR CheckGLError(__FILE__, __LINE__)
#else
#define BA_DEBUG_CHECK_GL_ERROR ((void)0)
#endif

namespace ballistica::base {

// For now lets not go above 8 since that's what the iPhone 3gs has. ...haha
// perhaps can reconsider that since the 3gs was 15 years ago.
constexpr int kMaxGLTexUnitsUsed = 5;

class RendererGL : public Renderer {
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
  class ProgramSimpleGL;
  class ProgramObjectGL;
  class ProgramSmokeGL;
  class ProgramBlurGL;
  class ProgramShieldGL;
  class ProgramPostProcessGL;
  class ProgramSpriteGL;

 public:
  void CheckGLVersion();
  static void CheckGLError(const char* file, int line);
  static auto GLErrorToString(GLenum err) -> std::string;
  static auto GetGLTextureFormat(TextureFormat f) -> GLenum;

  RendererGL();
  ~RendererGL() override;
  void Unload() override;
  void Load() override;
  void PostLoad() override;

  // Flags used internally by shaders.
  enum ShaderPrivateFlags {
    PFLAG_USES_POSITION_ATTR = 1,
    PFLAG_USES_UV_ATTR = 1 << 1,
    PFLAG_USES_NORMAL_ATTR = 1 << 2,
    PFLAG_USES_MODEL_WORLD_MATRIX = 1 << 3,
    PFLAG_USES_CAM_POS = 1 << 4,
    PFLAG_USES_SHADOW_PROJECTION_MATRIX = 1 << 5,
    PFLAG_WORLD_SPACE_PTS = 1 << 6,
    PFLAG_USES_ERODE_ATTR = 1 << 7,
    PFLAG_USES_COLOR_ATTR = 1 << 8,
    PFLAG_USES_SIZE_ATTR = 1 << 9,
    PFLAG_USES_DIFFUSE_ATTR = 1 << 10,
    PFLAG_USES_CAM_ORIENT_MATRIX = 1 << 11,
    PFLAG_USES_MODEL_VIEW_MATRIX = 1 << 12,
    PFLAG_USES_UV2_ATTR = 1 << 13
  };

  // Flags affecting shader creation.
  enum ShaderFlag {
    SHD_REFLECTION = 1,
    SHD_TEXTURE = 1 << 1,
    SHD_MODULATE = 1 << 2,
    SHD_COLORIZE = 1 << 3,
    SHD_LIGHT_SHADOW = 1 << 4,
    SHD_WORLD_SPACE_PTS = 1 << 5,
    SHD_DEBUG_PRINT = 1 << 6,
    SHD_ADD = 1 << 7,
    SHD_OBJ_TRANSPARENT = 1 << 8,
    SHD_COLOR = 1 << 9,
    SHD_EXP2 = 1 << 10,
    SHD_CAMERA_ALIGNED = 1 << 11,
    SHD_DISTORT = 1 << 12,
    SHD_PREMULTIPLY = 1 << 13,
    SHD_OVERLAY = 1 << 14,
    SHD_EYES = 1 << 15,
    SHD_COLORIZE2 = 1 << 16,
    SHD_HIGHER_QUALITY = 1 << 17,
    SHD_SHADOW = 1 << 18,
    SHD_GLOW = 1 << 19,
    SHD_MASKED = 1 << 20,
    SHD_MASK_UV2 = 1 << 21,
    SHD_CONDITIONAL = 1 << 22,
    SHD_FLATNESS = 1 << 23,
    SHD_DEPTH_BUG_TEST = 1 << 24
  };

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

  auto GetAutoGraphicsQuality() -> GraphicsQuality override;
  auto GetAutoTextureQuality() -> TextureQuality override;

#if BA_PLATFORM_ANDROID
  std::string GetAutoAndroidRes() override;
#endif

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
#endif

  auto current_vertex_array() const -> GLuint { return current_vertex_array_; }

  auto anisotropic_support() const { return anisotropic_support_; }
  auto max_anisotropy() const {
    assert(anisotropic_support_);
    return max_anisotropy_;
  }
  auto invalidate_framebuffer_support() const {
    return invalidate_framebuffer_support_;
  }

  auto msaa_max_samples_rgb565() const {
    assert(msaa_max_samples_rgb565_ != -1);
    return msaa_max_samples_rgb565_;
  }

  auto msaa_max_samples_rgb8() const {
    assert(msaa_max_samples_rgb8_ != -1);
    return msaa_max_samples_rgb8_;
  }

  auto gl_is_es() const -> bool {
#if BA_OPENGL_IS_ES
    return true;
#else
    return false;
#endif
  }

  auto gl_version_minor() const { return gl_version_minor_; }
  auto gl_version_major() const { return gl_version_major_; }

  // Wraps glGetIntegerv(). Triggers FatalError if get fails.
  auto GLGetInt(GLenum name) -> int;

  // Wraps glGetIntegerv(); returns empty value if get fails.
  auto GLGetIntOptional(GLenum name) -> std::optional<int>;

 private:
  static auto GetFunkyDepthIssue_() -> bool;
  void CheckFunkyDepthIssue_();
  auto GetMSAASamplesForFramebuffer_(int width, int height) -> int;
  void UpdateMSAAEnabled_() override;
  void CheckGLCapabilities_();
  void UpdateVignetteTex_(bool force) override;
  void StandardPostProcessSetup_(ProgramPostProcessGL* p,
                                 const RenderPass& pass);
  void SyncGLState_();
  void RetainShader_(ProgramGL* p);
  void SetViewport_(GLint x, GLint y, GLsizei width, GLsizei height);
  void UseProgram_(ProgramGL* p);
  auto GetActiveProgram_() const -> ProgramGL* {
    assert(current_program_);
    return current_program_;
  }
  void SetDoubleSided_(bool d);
  void ScissorPush_(const Rect& rIn, RenderTarget* render_target);
  void ScissorPop_(RenderTarget* render_target);
  void BindVertexArray_(GLuint v);

  // Note: This is only for use when VAOs aren't supported. void
  // SetVertexAttributeArrayEnabled_(GLuint i, bool enabled);
  void BindTexture_(GLuint type, const TextureAsset* t, GLuint tex_unit = 0);
  void BindTexture_(GLuint type, GLuint tex, GLuint tex_unit = 0);
  void BindTextureUnit(uint32_t tex_unit);
  void BindFramebuffer(GLuint fb);
  void BindArrayBuffer(GLuint b);
  void SetBlend(bool b);
  void SetBlendPremult(bool b);

  GraphicsQuality vignette_quality_{};
  bool blend_{};
  bool blend_premult_{};
  bool first_extension_check_{true};
  bool is_tegra_4_{};
  bool is_tegra_k1_{};
  bool is_recent_adreno_{};
  bool is_adreno_{};
  bool enable_msaa_{};
  bool draw_at_equal_depth_{};
  bool depth_writing_enabled_{};
  bool depth_testing_enabled_{};
  bool data_loaded_{};
  bool draw_front_{};
  bool got_screen_framebuffer_{};
  bool double_sided_{};
  bool invalidate_framebuffer_support_{};
  bool checked_gl_version_{};
  int last_blur_res_count_{};
  float last_cam_buffer_width_{};
  float last_cam_buffer_height_{};
  float vignette_tex_outer_r_{};
  float vignette_tex_outer_g_{};
  float vignette_tex_outer_b_{};
  float vignette_tex_inner_r_{};
  float vignette_tex_inner_g_{};
  float vignette_tex_inner_b_{};
  float depth_range_min_{};
  float depth_range_max_{};
  GLint gl_version_major_{};
  GLint gl_version_minor_{};
  GLint screen_framebuffer_{};
  GLuint random_tex_{};
  GLint viewport_x_{};
  GLint viewport_y_{};
  GLint viewport_width_{};
  GLint viewport_height_{};
  GLuint vignette_tex_{};
  millisecs_t dof_update_time_{};
  std::vector<Object::Ref<FramebufferObjectGL> > blur_buffers_;
  std::vector<std::unique_ptr<ProgramGL> > shaders_;
  ProgramSimpleGL* simple_color_prog_{};
  ProgramSimpleGL* simple_tex_prog_{};
  ProgramSimpleGL* simple_tex_dtest_prog_{};
  ProgramSimpleGL* simple_tex_mod_prog_{};
  ProgramSimpleGL* simple_tex_mod_flatness_prog_{};
  ProgramSimpleGL* simple_tex_mod_shadow_prog_{};
  ProgramSimpleGL* simple_tex_mod_shadow_flatness_prog_{};
  ProgramSimpleGL* simple_tex_mod_glow_prog_{};
  ProgramSimpleGL* simple_tex_mod_glow_maskuv2_prog_{};
  ProgramSimpleGL* simple_tex_mod_colorized_prog_{};
  ProgramSimpleGL* simple_tex_mod_colorized2_prog_{};
  ProgramSimpleGL* simple_tex_mod_colorized2_masked_prog_{};
  ProgramObjectGL* obj_prog_{};
  ProgramObjectGL* obj_transparent_prog_{};
  ProgramObjectGL* obj_lightshad_transparent_prog_{};
  ProgramObjectGL* obj_refl_prog_{};
  ProgramObjectGL* obj_refl_worldspace_prog_{};
  ProgramObjectGL* obj_refl_transparent_prog_{};
  ProgramObjectGL* obj_refl_add_transparent_prog_{};
  ProgramObjectGL* obj_lightshad_prog_{};
  ProgramObjectGL* obj_lightshad_worldspace_prog_{};
  ProgramObjectGL* obj_refl_lightshad_prog_{};
  ProgramObjectGL* obj_refl_lightshad_worldspace_prog_{};
  ProgramObjectGL* obj_refl_lightshad_colorize_prog_{};
  ProgramObjectGL* obj_refl_lightshad_colorize2_prog_{};
  ProgramObjectGL* obj_refl_lightshad_add_prog_{};
  ProgramObjectGL* obj_refl_lightshad_add_colorize_prog_{};
  ProgramObjectGL* obj_refl_lightshad_add_colorize2_prog_{};
  ProgramSmokeGL* smoke_prog_{};
  ProgramSmokeGL* smoke_overlay_prog_{};
  ProgramSpriteGL* sprite_prog_{};
  ProgramSpriteGL* sprite_camalign_prog_{};
  ProgramSpriteGL* sprite_camalign_overlay_prog_{};
  ProgramBlurGL* blur_prog_{};
  ProgramShieldGL* shield_prog_{};
  ProgramPostProcessGL* postprocess_prog_{};
  ProgramPostProcessGL* postprocess_eyes_prog_{};
  ProgramPostProcessGL* postprocess_distort_prog_{};
  static bool funky_depth_issue_set_;
  static bool funky_depth_issue_;
#if BA_PLATFORM_ANDROID
  bool is_speedy_android_device_{};
#endif
  ProgramGL* current_program_{};
  std::vector<Rect> scissor_rects_;
  GLuint current_vertex_array_{};
  int active_tex_unit_{};
  int active_framebuffer_{};
  int active_array_buffer_{};
  int bound_textures_2d_[kMaxGLTexUnitsUsed]{};
  int bound_textures_cube_map_[kMaxGLTexUnitsUsed]{};
  std::unique_ptr<MeshDataSimpleFullGL> screen_mesh_;
  std::vector<MeshDataSimpleSplitGL*> recycle_mesh_datas_simple_split_;
  std::vector<MeshDataObjectSplitGL*> recycle_mesh_datas_object_split_;
  std::vector<MeshDataSimpleFullGL*> recycle_mesh_datas_simple_full_;
  std::vector<MeshDataDualTextureFullGL*> recycle_mesh_datas_dual_texture_full_;
  std::vector<MeshDataSmokeFullGL*> recycle_mesh_datas_smoke_full_;
  std::vector<MeshDataSpriteGL*> recycle_mesh_datas_sprite_;
  int error_check_counter_{};
  GLint combined_texture_image_unit_count_{};
  GLint anisotropic_support_{};
  GLfloat max_anisotropy_{};
  int msaa_max_samples_rgb565_{-1};
  int msaa_max_samples_rgb8_{-1};
};

}  // namespace ballistica::base

#endif  // BA_ENABLE_OPENGL

#endif  // BALLISTICA_BASE_GRAPHICS_GL_RENDERER_GL_H_
