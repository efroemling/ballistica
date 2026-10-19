# Released under the MIT License. See LICENSE for details.
#
"""A viewer showing a few meshes, turning."""

from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Self


class MeshViewer(bui.Viewer):
    """Shows what a mesh-viewer depiction describes.

    The native viewer does the work (framing, turning, fetching its
    meshes); we hand it the depiction as is and pass drags along so it
    can be swung around.

    Use :meth:`get` to get the one kept under an id (made if need be)
    and hand its :attr:`source` to whatever shows viewers.

    :meta private:
    """

    def __init__(self) -> None:
        from bauiv1lib.docui._windowparts import VIEWER_BLANK_COLOR

        # Size gets set by whatever shows us.
        self._viewer = bui.MeshViewer(256, 256)

        # Depictions not saying otherwise blend into the viewer pane
        # around us.
        self._viewer.set_default_background(VIEWER_BLANK_COLOR)
        self._drag_from: tuple[float, float] | None = None

    @classmethod
    def for_depiction(cls, key: str, depiction_json: str) -> Self:
        """Return the viewer showing a mesh-viewer depiction.

        Registered as the live-depiction maker for that kind (see
        ``bauiv1.UIV1AppSubsystem.live_depictions``); carries on with
        the viewer kept under ``key`` so changed meshes reframe in
        place.
        """
        viewer = cls.get(key)
        viewer.set_depiction(depiction_json)
        return viewer

    def set_depiction(self, depiction_json: str) -> None:
        """Show what a mesh-viewer depiction's json describes.

        One it can't use isn't an error here: our source reports it
        broken, and whatever shows us draws the broken-depiction
        placeholder (and logs why).
        """
        self._viewer.set_depiction(depiction_json)

    @classmethod
    def get(cls, viewer_id: str) -> Self:
        """Return the viewer kept under an id, making it if need be."""
        viewers = bui.app.ui_v1.viewers
        viewer = viewers.get(viewer_id, cls)
        if viewer is None:
            viewer = cls()
            viewers.add(viewer_id, viewer)
        return viewer

    @override
    @property
    def source(self) -> bui.ViewerSource:
        return self._viewer.source

    @override
    def shutdown(self) -> None:
        self._viewer.shutdown()

    @override
    def wants_presses(self) -> bool:
        return True

    @override
    def handle_press(self, x: float, y: float) -> None:
        self._drag_from = (x, y)

    @override
    def handle_drag(self, x: float, y: float) -> None:
        if self._drag_from is None:
            return
        self._viewer.orbit(x - self._drag_from[0], y - self._drag_from[1])
        self._drag_from = (x, y)

    @override
    def handle_release(self) -> None:
        self._drag_from = None
