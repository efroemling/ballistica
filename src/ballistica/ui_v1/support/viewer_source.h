// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_SUPPORT_VIEWER_SOURCE_H_
#define BALLISTICA_UI_V1_SUPPORT_VIEWER_SOURCE_H_

#include <string>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

/// Something that makes a picture for a viewer widget to show.
///
/// We say nothing about what the picture is of or how it gets made;
/// that is up to whoever provides one (scene_v1 provides scenes drawn
/// to a texture, for instance). All a viewer widget needs is a texture
/// to draw and someone to tell how big it is drawing it.
///
/// Sources are made to outlast the widgets showing them: ui gets torn
/// down and rebuilt often, and what is being shown should carry on
/// through that instead of starting over. So nothing here is tied to a
/// widget; a source just keeps track of when it was last shown, and
/// whoever owns it can use that to retire it once nothing has shown it
/// in a while.
///
/// Design: docs/initiatives/render-views.md.
class ViewerSource : public Object {
 public:
  ViewerSource();
  ~ViewerSource() override;

  /// The texture holding our picture, or nullptr if we have nothing to
  /// show (any longer).
  virtual auto GetViewerTexture() -> base::TextureAsset* = 0;

  /// Called by a viewer widget each frame it shows us, with the size
  /// in pixels it shows us at once settled (any transition it may be
  /// playing aside). A source able to should make its picture that
  /// size so its pixels land one to one on screen.
  virtual void SetViewerPixelSize(int width, int height) = 0;

  /// A short name for us, for descriptions and the like.
  virtual auto GetName() const -> std::string;

  /// Called by a viewer widget each frame it shows us.
  void MarkShown();

  /// Display-time seconds since we were last shown (or since we were
  /// created, if we never have been).
  auto GetIdleTime() const -> seconds_t;

  /// Whether some widget was showing us just now (a moment ago, as
  /// when a window is rebuilt and a new widget takes over showing us).
  auto WasJustShown() const -> bool;

 private:
  seconds_t last_shown_time_;
  bool ever_shown_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_SUPPORT_VIEWER_SOURCE_H_
