// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_GRAPHICS_SUPPORT_DEBUG_TEXTURE_VIEW_H_
#define BALLISTICA_BASE_GRAPHICS_SUPPORT_DEBUG_TEXTURE_VIEW_H_

#include "ballistica/base/graphics/support/render_view.h"

namespace ballistica::base {

/// A view drawing a turning test object to a texture, which Graphics
/// shows in a corner of the screen when asked to (BA_DEBUG_TEXTURE_VIEW;
/// test_game_run --debug-texture-view).
///
/// For checking that views drawing to textures work, using nothing but
/// base: no scene, no ui. If this looks right and a viewer built on the
/// same machinery does not, the trouble is in the viewer.
class DebugTextureView : public RenderView {
 public:
  DebugTextureView();
  ~DebugTextureView() override;

  void DrawWorld(FrameDef* frame_def) override;

  /// Draw our texture (and so get our world drawn).
  void DrawToOverlay(RenderPass* pass);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_GRAPHICS_SUPPORT_DEBUG_TEXTURE_VIEW_H_
