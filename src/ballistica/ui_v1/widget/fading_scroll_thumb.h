// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_WIDGET_FADING_SCROLL_THUMB_H_
#define BALLISTICA_UI_V1_WIDGET_FADING_SCROLL_THUMB_H_

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/math/rect.h"

namespace ballistica::ui_v1 {

/// A scroll widget's thin, rounded, translucent thumb that fades in while
/// wanted (scrolling, hovered, dragged) and back out a moment after, drawn
/// over the widget's content rather than in a trough of its own. Shared by
/// ScrollWidget (in its fading-scrollbar mode) and HScrollWidget (always).
///
/// The owning widget decides each frame whether the bar is wanted (see
/// Show()) and where its thumb goes; this handles the fade and the
/// drawing.
class FadingScrollThumb {
 public:
  // (Out of line: our mesh ref needs NinePatchMesh complete to destroy.)
  FadingScrollThumb();
  ~FadingScrollThumb();

  /// Note the bar is wanted as of this time; it stays fully in until a
  /// moment after the last such call.
  void Show(seconds_t now) { last_show_time_ = now; }

  /// Advance the fade by a frame.
  void Update(seconds_t now, seconds_t elapsed);

  /// Draw the thumb (if faded in at all) at the given rect in the owner's
  /// local space, clipped to ``clip``. ``emphasis`` firms it up (mouse
  /// hover, dragging). Draws only in the transparent pass.
  void Draw(base::RenderPass* pass, bool transparent, float left, float bottom,
            float width, float height, float emphasis, const Rect& clip);

 private:
  /// Rebuild mesh_ if the thumb's size has changed. Ninepatch corners must
  /// not be scaled (it would distort them), so the mesh is built at exact
  /// size and only translated when drawn.
  void EnsureMesh_(float width, float height);

  Object::Ref<base::NinePatchMesh> mesh_;
  float mesh_width_{-1.0f};
  float mesh_height_{-1.0f};
  seconds_t last_show_time_{-999.0};
  float fade_{};
};

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_WIDGET_FADING_SCROLL_THUMB_H_
