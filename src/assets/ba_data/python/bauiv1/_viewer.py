# Released under the MIT License. See LICENSE for details.
#
"""Viewers: live pictures shown in ui that outlast the ui showing them."""

import logging
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    import bauiv1

#: The most viewers kept at once. One is what we expect to be showing;
#: the second lets one window take over from another without the
#: outgoing one's viewer being pulled out from under it.
MAX_VIEWERS = 2

#: Seconds (of display time) a viewer can go unshown before it is shut
#: down. Enough to carry a viewer through its window being rebuilt or
#: briefly covered; not enough to leave scenes nobody is looking at
#: sitting around.
MAX_IDLE_SECONDS = 5.0


class Viewer:
    """A live picture shown in ui; a little game scene, for instance.

    A viewer is shown by a live depiction (a character viewer
    depiction in a :func:`bauiv1.imagewidget`, say), which draws
    its :attr:`source`, but belongs to no widget. Windows get torn down
    and rebuilt all the time (on screen resizes, when navigating back
    to them, ...) and what they were showing should carry on through
    that instead of starting over, so viewers are kept by id in a
    :class:`ViewerRegistry` and whatever shows one asks there first
    for one to carry on with.

    Subclass this to provide a particular sort of viewer.

    :meta private:
    """

    @property
    def source(self) -> bauiv1.ViewerSource:
        """What gets drawn wherever we're shown."""
        raise NotImplementedError()

    def shutdown(self) -> None:
        """Stop for good and let go of everything we hold.

        Called by the registry when we are retired; a viewer should
        expect nothing further to be asked of it afterward.
        """

    def wants_presses(self) -> bool:
        """Whether widgets showing us should pass along presses.

        If so, they call :meth:`handle_press` and :meth:`handle_release`
        (and take presses on them rather than letting them fall through
        to whatever is beneath).
        """
        return False

    def handle_press(self, x: float, y: float) -> None:
        """A pointer pressed on a widget showing us.

        Where, as fractions (0-1) across its width and up its height.
        """
        del x, y  # Unused.

    def handle_drag(self, x: float, y: float) -> None:
        """A press passed to :meth:`handle_press` moved.

        Where it is now, in the same fractions (and possibly outside
        0-1, once dragged off the widget).
        """
        del x, y  # Unused.

    def handle_release(self) -> None:
        """A press passed to :meth:`handle_press` let go."""


class ViewerRegistry:
    """Keeps viewers by id so they outlast the widgets showing them.

    Viewers here are shut down once they have gone unshown for a short
    while, and the number kept at once is small; asking for more
    retires whichever has gone unshown the longest.

    Access the single shared instance at ``bauiv1.app.ui_v1.viewers``.

    :meta private:
    """

    def __init__(self) -> None:
        self._viewers: dict[str, Viewer] = {}
        self._upkeep_timer: babase.AppTimer | None = None

    def get[T: Viewer](self, viewer_id: str, viewertype: type[T]) -> T | None:
        """Return the viewer kept under an id, if there is one.

        A viewer of some other type than the one asked for is treated
        as not there (and will be replaced by whatever gets added).
        """
        viewer = self._viewers.get(viewer_id)
        if isinstance(viewer, viewertype):
            return viewer
        return None

    def add(self, viewer_id: str, viewer: Viewer) -> None:
        """Keep a viewer under an id.

        Any viewer already kept under that id is shut down, as is
        whichever viewer has gone unshown longest if we would
        otherwise be keeping too many.
        """
        assert babase.in_logic_thread()
        existing = self._viewers.pop(viewer_id, None)
        if existing is not None and existing is not viewer:
            self._shut_down(viewer_id, existing)

        while len(self._viewers) >= MAX_VIEWERS:
            oldest_id = max(self._viewers, key=self._idle_time)
            self._shut_down(oldest_id, self._viewers.pop(oldest_id))

        self._viewers[viewer_id] = viewer
        if self._upkeep_timer is None:
            self._upkeep_timer = babase.AppTimer(
                1.0, babase.WeakCallStrict(self._upkeep), repeat=True
            )

    def remove(self, viewer_id: str) -> None:
        """Shut down the viewer kept under an id, if there is one."""
        assert babase.in_logic_thread()
        viewer = self._viewers.pop(viewer_id, None)
        if viewer is not None:
            self._shut_down(viewer_id, viewer)
        if not self._viewers:
            self._upkeep_timer = None

    def clear(self) -> None:
        """Shut down all viewers."""
        assert babase.in_logic_thread()
        for viewer_id in list(self._viewers):
            self.remove(viewer_id)

    def _idle_time(self, viewer_id: str) -> float:
        try:
            return self._viewers[viewer_id].source.get_idle_time()
        except Exception:
            # A viewer that can't say is one we can do without.
            logging.exception(
                "Error getting idle time for viewer '%s'.", viewer_id
            )
            return 9999.0

    def _upkeep(self) -> None:
        for viewer_id in list(self._viewers):
            if self._idle_time(viewer_id) > MAX_IDLE_SECONDS:
                self.remove(viewer_id)

    @staticmethod
    def _shut_down(viewer_id: str, viewer: Viewer) -> None:
        try:
            viewer.shutdown()
        except Exception:
            logging.exception("Error shutting down viewer '%s'.", viewer_id)
