// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_RENDER_VIEW_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_RENDER_VIEW_H_

#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/graphics/support/shadow_range.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector2f.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// Everything that defines how one world gets drawn: its camera, its
/// look (tint, ambient color, vignette, shadow setup), and the light
/// and shadow blotches cast in it today, with its buffers to follow.
/// (Its passes for a given frame are that frame's FrameDefView.)
///
/// The main game world draws through the one owned by Graphics
/// (Graphics::main_view()); small standalone scenes such as ui viewers
/// get their own, so nothing about how they are drawn touches the main
/// world's. Whatever is drawing a world (a scene, generally) holds the
/// view it draws into and sets these values on it.
///
/// Logic thread only. Design: docs/initiatives/render-views.md.
class RenderView : public Object {
 public:
  /// Where what a view draws ends up.
  enum class Output : uint8_t {
    /// The screen (the main game world's view).
    kScreen,
    /// A texture of the view's own, to be drawn wherever wanted (ui
    /// viewers and such).
    kTexture
  };

  /// Create a view drawing to the screen.
  explicit RenderView(Camera* camera);

  /// Create a view drawing to a texture of a given size in pixels.
  RenderView(Camera* camera, int width, int height);

  ~RenderView() override;

  /// A number identifying us for as long as the app runs. This is how
  /// the renderer, which lives on another thread and never touches us
  /// directly, knows one view's buffers from another's.
  auto id() const -> int { return id_; }

  auto output() const -> Output { return output_; }

  /// Size in pixels of the texture we draw to (texture views only).
  auto width() const -> int {
    assert(output_ == Output::kTexture);
    return width_;
  }
  auto height() const -> int {
    assert(output_ == Output::kTexture);
    return height_;
  }

  /// Change the size of the texture we draw to (texture views only).
  /// The renderer rebuilds our buffers when this changes, so it is not
  /// something to do every frame.
  void SetSize(int width, int height);

  /// The highest graphics quality we will draw at; we draw at this or
  /// the app's current quality, whichever is lower. Buffers a view
  /// needs grow with quality (above medium brings a camera buffer with
  /// depth and blurred copies of it), so this is how a small view
  /// keeps itself cheap.
  auto max_quality() const -> GraphicsQuality { return max_quality_; }
  void set_max_quality(GraphicsQuality val) { max_quality_ = val; }

  /// The quality we draw at when the app's is a given one. Everything
  /// that goes by quality in a world drawn through us (its frames, its
  /// bg-dynamics) should go by this.
  auto GetQuality(GraphicsQuality app_quality) const -> GraphicsQuality;

  /// What our texture is cleared to before our world is drawn
  /// (texture views only).
  auto clear_color() const -> const Vector3f& { return clear_color_; }
  void set_clear_color(const Vector3f& val) { clear_color_ = val; }

  /// The texture we draw to (texture views only). Draw this anywhere
  /// a texture can be drawn; its being drawn in a frame is what gets
  /// our world drawn for that frame, so a view nothing is showing
  /// costs nothing to draw.
  auto texture() -> TextureAsset*;

  /// Whether our texture was drawn in the last frame built, which is
  /// to say whether anyone is looking. Whatever runs our world can
  /// use this to let it rest while no one is.
  auto wanted() const -> bool;

  /// Called as our world gets drawn into a frame.
  void set_last_drawn_frame_number(int64_t val) {
    last_drawn_frame_number_ = val;
  }

  /// Draw our world into the current view of a frame being built.
  /// Called for texture views that something has drawn the texture of
  /// this frame; whatever owns such a view overrides this to draw what
  /// is in it. (The main game world is drawn by the app-mode instead.)
  virtual void DrawWorld(FrameDef* frame_def);

  /// What we see our world through. Things drawing the world register
  /// areas of interest with it and so on; what it does with them is up
  /// to the particular camera.
  auto camera() const -> Camera* {
    assert(camera_.exists());
    return camera_.get();
  }

  auto floor_reflection() const {
    assert(g_base->InLogicThread());
    return floor_reflection_;
  }
  void set_floor_reflection(bool val) {
    assert(g_base->InLogicThread());
    floor_reflection_ = val;
  }
  auto shadow_offset() const -> const Vector3f& {
    assert(g_base->InLogicThread());
    return shadow_offset_;
  }
  void set_shadow_offset(const Vector3f& val) {
    assert(g_base->InLogicThread());
    shadow_offset_ = val;
  }
  auto shadow_scale() const -> const Vector2f& {
    assert(g_base->InLogicThread());
    return shadow_scale_;
  }
  void set_shadow_scale(float x, float y) {
    assert(g_base->InLogicThread());
    shadow_scale_.x = x;
    shadow_scale_.y = y;
  }
  auto shadow_ortho() const {
    assert(g_base->InLogicThread());
    return shadow_ortho_;
  }
  void set_shadow_ortho(bool val) {
    assert(g_base->InLogicThread());
    shadow_ortho_ = val;
  }
  auto tint() const -> const Vector3f& { return tint_; }
  void set_tint(const Vector3f& val) {
    assert(g_base->InLogicThread());
    tint_ = val;
  }
  auto ambient_color() const -> const Vector3f& {
    assert(g_base->InLogicThread());
    return ambient_color_;
  }
  void set_ambient_color(const Vector3f& val) {
    assert(g_base->InLogicThread());
    ambient_color_ = val;
  }
  auto vignette_outer() const -> const Vector3f& {
    assert(g_base->InLogicThread());
    return vignette_outer_;
  }
  void set_vignette_outer(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vignette_outer_ = val;
  }
  auto vignette_inner() const -> const Vector3f& {
    assert(g_base->InLogicThread());
    return vignette_inner_;
  }
  void set_vignette_inner(const Vector3f& val) {
    assert(g_base->InLogicThread());
    vignette_inner_ = val;
  }

  /// Set the heights between which shadows show: they fade in from
  /// lower_bottom to lower_top and back out from upper_bottom to
  /// upper_top.
  void SetShadowRange(float lower_bottom, float lower_top, float upper_bottom,
                      float upper_top);

  auto shadow_range() const -> const ShadowRange& {
    assert(g_base->InLogicThread());
    return shadow_range_;
  }

  /// Given a point in space, returns the shadow density that should be
  /// drawn into the shadow pass.
  auto GetShadowDensity(float x, float y, float z) const -> float {
    return shadow_range().GetDensity(y);
  }

  // Ways to add a few simple light/shadow shapes quickly; they get
  // batched up and drawn together by DrawBlotches().

  /// Draw a blotch of light or shadow on everything.
  void DrawBlotch(const Vector3f& pos, float size, float r, float g, float b,
                  float a) {
    DoDrawBlotch_(&blotch_indices_, &blotch_verts_, pos, size, r, g, b, a);
  }

  /// Draw a soft blotch on everything.
  void DrawBlotchSoft(const Vector3f& pos, float size, float r, float g,
                      float b, float a) {
    DoDrawBlotch_(&blotch_soft_indices_, &blotch_soft_verts_, pos, size, r, g,
                  b, a);
  }

  /// Draw a soft blotch on objects; not terrain.
  void DrawBlotchSoftObj(const Vector3f& pos, float size, float r, float g,
                         float b, float a) {
    DoDrawBlotch_(&blotch_soft_obj_indices_, &blotch_soft_obj_verts_, pos, size,
                  r, g, b, a);
  }

  /// Draw the blotches that have built up into our passes of a frame.
  /// Call once everything in our world has drawn.
  void DrawBlotches(FrameDef* frame_def);

  /// Drop any blotches that have built up. Call at the end of each
  /// frame, whether or not they got drawn.
  void ClearBlotches();

 private:
  void DoDrawBlotch_(std::vector<uint16_t>* indices,
                     std::vector<VertexSprite>* verts, const Vector3f& pos,
                     float size, float r, float g, float b, float a);

  int id_;
  Output output_;
  int width_{};
  int height_{};
  GraphicsQuality max_quality_{GraphicsQuality::kHigher};
  Vector3f clear_color_{0.0f, 0.0f, 0.0f};
  int64_t last_drawn_frame_number_{-1};
  Object::Ref<TextureAsset> texture_;
  Object::Ref<Camera> camera_;
  bool floor_reflection_{};
  bool shadow_ortho_{};
  Vector3f shadow_offset_{0.0f, 0.0f, 0.0f};
  Vector2f shadow_scale_{1.0f, 1.0f};
  Vector3f tint_{1.0f, 1.0f, 1.0f};
  Vector3f ambient_color_{1.0f, 1.0f, 1.0f};
  Vector3f vignette_outer_{0.0f, 0.0f, 0.0f};
  Vector3f vignette_inner_{1.0f, 1.0f, 1.0f};
  ShadowRange shadow_range_;
  std::vector<uint16_t> blotch_indices_;
  std::vector<VertexSprite> blotch_verts_;
  std::vector<uint16_t> blotch_soft_indices_;
  std::vector<VertexSprite> blotch_soft_verts_;
  std::vector<uint16_t> blotch_soft_obj_indices_;
  std::vector<VertexSprite> blotch_soft_obj_verts_;
  Object::Ref<SpriteMesh> shadow_blotch_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_mesh_;
  Object::Ref<SpriteMesh> shadow_blotch_soft_obj_mesh_;
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_RENDER_VIEW_H_
