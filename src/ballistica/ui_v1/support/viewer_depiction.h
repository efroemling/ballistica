// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_UI_V1_SUPPORT_VIEWER_DEPICTION_H_
#define BALLISTICA_UI_V1_SUPPORT_VIEWER_DEPICTION_H_

namespace ballistica::ui_v1 {

/// Register the depiction kinds backed by live viewers (the 3d
/// character viewer). Called as ui_v1 loads.
///
/// Such a kind is a thin native bridge: the live thing itself (a little
/// scene with a character in it, and what it does when poked) is a
/// Python bauiv1.Viewer, made by whatever the app mode registered for
/// the kind in ``bauiv1.app.ui_v1.live_depictions`` and kept by the
/// host's key in the viewer registry, so a host handed a changed
/// depiction under the same key carries on with the same viewer. The
/// bridge draws the viewer's picture sized to land one to one on
/// screen, routes input its host opts into to the viewer
/// (press/drag/release), and hands out the viewer object itself as its
/// Python control. Design: docs/initiatives/depictions.md.
void RegisterViewerDepictionKinds();

}  // namespace ballistica::ui_v1

#endif  // BALLISTICA_UI_V1_SUPPORT_VIEWER_DEPICTION_H_
