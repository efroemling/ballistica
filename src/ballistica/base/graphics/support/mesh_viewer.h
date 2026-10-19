// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_MESH_VIEWER_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_MESH_VIEWER_H_

#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/support/media_block.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/vector3f.h"

namespace ballistica::base {

/// A few meshes, drawn turning in a picture of their own.
///
/// What a mesh-viewer depiction shows (bacommon.depiction
/// .MeshViewerDepiction): textured meshes placed relative to one
/// another, framed to fill the picture and slowly turning, which can be
/// swung around by dragging. Nothing but base: no scene, no ui. What we
/// draw ends up in our view's texture (view()->texture()), which can be
/// drawn anywhere a texture can.
///
/// We run only while being looked at; our turning picks up where it
/// left off.
///
/// Logic thread only. Design: docs/initiatives/mesh-viewer.md.
class MeshViewer : public Object {
 public:
  /// Create with a texture of a given size in pixels.
  MeshViewer(int width, int height);
  ~MeshViewer() override;

  /// Show what a mesh-viewer depiction's json describes. Returns false
  /// (and shows nothing; see failure()) if it can't be used. Showing
  /// the same json again does nothing; showing other meshes reframes
  /// to fit them.
  auto SetDepiction(const std::string& json) -> bool;

  /// Why what we were given can never be shown, if so: unusable json,
  /// or media that will never load (see MediaBlock::failed()). Empty
  /// while all is well or still loading.
  auto failure() const -> std::string;

  /// Whether we have meshes to show that aren't here yet (being
  /// fetched or loaded), and so show nothing of them for now.
  auto loading() const -> bool {
    return !entries_.empty() && !block_.ready() && !block_.failed();
  }

  /// What shows behind our meshes when a depiction doesn't say
  /// (whoever shows us knows what blends in where).
  void SetDefaultBackground(const Vector3f& color);

  /// Draw with no background at all: our picture keeps an alpha
  /// channel (premultiplied) and is composited over whatever is behind
  /// it, the background color ignored. For hosts showing us over the
  /// window directly (a doc-ui overlay viewer pane).
  void SetTransparent(bool transparent);

  /// Swing the view around: horizontal and vertical motion as
  /// fractions of the picture's width and height (as dragged; up is
  /// positive). A full width across is half a turn.
  void Orbit(float dx, float dy);

  /// The view we draw through.
  auto view() const -> RenderView*;

  /// Set the size of our picture in pixels (scaled down to what we
  /// allow, keeping its shape).
  void SetSize(int width, int height);

  /// The largest our picture can be on a side.
  static constexpr int kMaxSize{2048};

 private:
  class View;

  struct Entry {
    PackageAssetRef mesh;
    PackageAssetRef texture;
    float color[4]{1.0f, 1.0f, 1.0f, 1.0f};
    bool transparent{};
    PackageAssetRef reflection;  // A cube map.
    float reflection_scale[3]{1.0f, 1.0f, 1.0f};
    PackageAssetRef tint_texture;
    float tint_colors[3][3]{
        {1.0f, 1.0f, 1.0f}, {1.0f, 1.0f, 1.0f}, {1.0f, 1.0f, 1.0f}};
    Vector3f position{0.0f, 0.0f, 0.0f};
    // Degrees, applied about x, then y, then z.
    Vector3f rotation{0.0f, 0.0f, 0.0f};
    Vector3f scale{1.0f, 1.0f, 1.0f};
    Object::Ref<MeshAsset> mesh_asset;
    Object::Ref<TextureAsset> texture_asset;
    Object::Ref<TextureAsset> reflection_asset;
    Object::Ref<TextureAsset> tint_texture_asset;
  };

  /// How what we show is fit into the picture: a center to look at and
  /// a scale bringing everything within the unit sphere.
  struct Fit {
    Vector3f center{0.0f, 0.0f, 0.0f};
    float scale{1.0f};
    // The radius of everything about center, as it is (unscaled, and
    // before any bounds scale).
    float radius{1.0f};
  };

  /// A camera placed by hand (see MeshViewerDepiction.camera), in the
  /// depiction's own space.
  struct ManualCamera {
    Vector3f position{0.0f, 0.0f, 1.0f};
    Vector3f target{0.0f, 0.0f, 0.0f};
    float fov_y{36.0f};
  };

  /// Read a depiction into us; returns what's wrong with it, if
  /// anything.
  auto Parse_(const std::string& json) -> std::string;
  void Draw_(FrameDef* frame_def);
  void DrawEntry_(const Entry& entry, FrameDef* frame_def, const Fit& fit,
                  float turn_degrees);
  void UpdateMedia_();
  static void ApplyEntryTransform_(const Entry& entry, RenderComponent* c);
  auto CalcFit_() const -> Fit;
  void UpdateCamera_();
  static auto FitSize_(int width, int height) -> std::pair<int, int>;

  Object::Ref<FixedCamera> camera_;
  Object::Ref<View> view_;
  std::string json_;
  std::string failure_;
  std::vector<Entry> entries_;
  std::vector<std::string> packages_;
  std::string domain_digest_;
  bool spin_{true};
  // Whether drags turn us (or swing our camera).
  bool draggable_{true};
  // How much bigger than its contents' bounds the framing is.
  float bounds_scale_{1.0f};
  // Where the turntable and camera start (radians); see Parse_.
  float start_yaw_{};
  float start_pitch_{};
  bool have_pose_{};
  // Set when the depiction places the camera itself.
  std::optional<ManualCamera> manual_camera_;
  Vector3f default_background_{0.0f, 0.0f, 0.0f};
  std::optional<Vector3f> background_;
  MediaBlock block_;
  MediaRetryPacer pacer_;
  // Whether we've said that an entry can't both blend and tint.
  bool warned_tint_blend_{};

  // Framing for what we show (once its media is all here).
  bool have_fit_{};
  Fit fit_;

  // Turning: the idle spin plus however far we've been dragged.
  float spin_angle_{};
  float user_yaw_{};
  float pitch_{};
  double last_draw_time_{-1.0};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_MESH_VIEWER_H_
