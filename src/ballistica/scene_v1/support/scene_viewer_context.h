// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SCENE_VIEWER_CONTEXT_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SCENE_VIEWER_CONTEXT_H_

#include <string>
#include <utility>
#include <vector>

#include "ballistica/scene_v1/support/local_scene_context.h"

namespace ballistica::ui_v1 {
class ViewerSource;
}

namespace ballistica::scene_v1 {

/// A self-contained scene drawn to a texture, for showing in ui.
///
/// We are a local scene (see LocalSceneContext) with a view and a
/// camera of our own, so nothing about us touches the main game world
/// or how it is drawn: our own look, light and shadow, and clock. We
/// make no sound. Whatever is wanted in the scene gets built in our
/// context same as it would in an activity's; what we draw ends up in
/// our view's texture (view()->texture()), which can be drawn anywhere
/// a texture can.
///
/// We run only while being looked at: our scene steps (from display
/// time) when our texture was drawn in the last frame and stands still
/// otherwise, picking up where it left off.
///
/// Design: docs/initiatives/render-views.md.
class SceneViewerContext : public LocalSceneContext {
 public:
  /// Create with a texture of a given size in pixels.
  SceneViewerContext(int width, int height);
  ~SceneViewerContext() override;

  auto GetContextDescription() -> std::string override;

  /// The view we draw through; ours alone.
  auto view() const -> base::RenderView*;

  /// The camera we're seen through.
  auto camera() const -> base::FixedCamera* {
    assert(camera_.exists());
    return camera_.get();
  }

  /// Us as something a ui viewer widget can show. Holds no claim on
  /// us; once we are gone it simply has nothing to show.
  auto viewer_source() const -> ui_v1::ViewerSource*;

  /// Set the size of our picture in pixels (scaled down to what we
  /// allow, keeping its shape).
  void SetSize(int width, int height);

  /// Let our scene make sound (we're silent to start). Sounds are
  /// heard as our camera would hear them, not the game camera: placed
  /// relative to it, gain scaled by volume, and how far to the sides
  /// they sit scaled by pan_scale.
  void SetSound(bool enabled, float volume, float pan_scale);

  /// The largest our picture can be on a side. A viewer is a pane in
  /// a window, not a second screen.
  static constexpr int kMaxSize{2048};

  /// Give all existing viewers some display time to run on. The app
  /// mode calls this as display time advances.
  static void StepAllDisplayTime(millisecs_t time_advance);

 private:
  class View;
  class Source;

  /// A size scaled down evenly, if need be, to fit within kMaxSize on
  /// both sides. Clamping each side on its own would change the
  /// picture's shape, and it is shown stretched to its pane's shape,
  /// so it would come out squashed.
  static auto FitSize_(int width, int height) -> std::pair<int, int>;

  void StepDisplayTime_(millisecs_t time_advance);

  /// Point our scene's sounds' listener where our camera is (its
  /// steady aim; shake is left out).
  void UpdateAudioListener_();

  bool sound_enabled_{};
  float sound_volume_{1.0f};
  float sound_pan_scale_{1.0f};

  Object::Ref<base::FixedCamera> camera_;
  Object::Ref<View> view_;
  Object::Ref<Source> source_;
  millisecs_t unstepped_time_{};
  static std::vector<SceneViewerContext*> s_viewers_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SCENE_VIEWER_CONTEXT_H_
