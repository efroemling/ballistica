# Released under the MIT License. See LICENSE for details.
#
"""How a doc-ui window opens: its shape and look, chosen up front."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bacommon.docui.v2
    from bacommon.docui import DocUIRequest
    from bacommon.docui.routes import DocUIRoute


@dataclass(frozen=True)
class WindowOptions:
    """How a doc-ui window opens: its shape and look.

    All of it is chosen by whatever opens the window (a
    :class:`~bacommon.docui.v2.Browse` action's fields, or a route's
    defaults), since the window is built before any page arrives;
    pages replacing each other within a window share it. None for any
    of them means the default (see each). (A viewer pane, if any, is up
    to each page instead; see :attr:`bacommon.docui.v2.Page.viewer`.)

    On the wire these stay separate flat fields of the browse action
    (clients ignore ones they don't know); here they travel together,
    so a new one is added in one place rather than at every hop.
    """

    #: The window's layout, or None for the wide layout.
    layout: bacommon.docui.v2.WindowLayout | None = None

    #: How its scroll area meets the window, or None to let the layout
    #: decide.
    scroll_edge_style: bacommon.docui.v2.ScrollEdgeStyle | None = None

    @classmethod
    def from_browse(cls, action: bacommon.docui.v2.Browse) -> WindowOptions:
        """The options a browse action asks for.

        (Its legacy ``viewer_style`` is ignored; pages pick their own.)
        """
        return cls(
            layout=action.layout,
            scroll_edge_style=action.scroll_edge_style,
        )

    def with_route_defaults(
        self, request: DocUIRequest | DocUIRoute
    ) -> WindowOptions:
        """These, with anything not chosen filled in from a route.

        A route's own defaults (its
        :meth:`~bacommon.docui.routes.DocUIRoute.get_window_layout`)
        apply to whatever wasn't chosen; anything else is left as is.
        """
        from dataclasses import replace

        from bacommon.docui.routes import DocUIRoute

        if not isinstance(request, DocUIRoute):
            return self
        return replace(
            self,
            layout=(
                request.get_window_layout()
                if self.layout is None
                else self.layout
            ),
        )
