# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui viewer panes: which one a page gets, and the room around it."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.docui._layout import (
    SMALL_UI_VIEWER_EDGE_FADE,
    SIDE_EDGE_FADE,
    fade_scroll_extents,
)
from bauiv1lib.utils import TOOLBAR_SCROLL_FADE, apply_toolbar_scroll_fades

if TYPE_CHECKING:
    from bauiv1lib.docui._frame import WindowFrame


def viewer_insets_v(uiscale: bui.UIScale) -> tuple[float, float]:
    """How far a viewer pane's bottom and top edges sit in from the
    scroll area's (negative: out past it).

    At small ui-scale it clears the toolbars it runs under (by less than
    page content's clearance, as the pane's own frame and rounded
    corners already read as spacing). All tuned by eye.
    """
    match uiscale:
        case bui.UIScale.SMALL:
            return (55.0, 55.0)
        case bui.UIScale.MEDIUM | bui.UIScale.LARGE:
            # The whole pane a touch lower.
            return (-5.0, 5.0)
        case _:
            assert_never(uiscale)


def fade_scroll_lengths() -> tuple[float, float, float, float]:
    """How far a fade-style scroll area's fades reach in from its edges.

    Returns (left, right, bottom, top), at medium/large ui-scale. Free to
    differ from ``fade_scroll_extents()`` (a longer fade reaches past
    where an outline would clip, into content's space): the top one
    runs long, as content passing up behind the title otherwise muddles
    it. The sides reach out not at all, but sideways-scrolling rows
    still pass under them; those fade within the empty strip before
    content instead of cutting off hard.
    """
    _left, _right, bottom, top = fade_scroll_extents()
    return SIDE_EDGE_FADE, SIDE_EDGE_FADE, bottom, 2.0 * top


def layout_has_viewer_pane(layout: dui2.WindowLayout) -> bool:
    """Whether a layout makes room for a viewer pane (if a page has one)."""
    match layout:
        case dui2.WindowLayout.VIEWER | dui2.WindowLayout.VIEWER_NARROW:
            return True
        case (
            dui2.WindowLayout.LARGE
            | dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
        ):
            return False
        case _:
            assert_never(layout)


@dataclass(frozen=True)
class PaneMode:
    """The viewer pane a page gets: which side it sits on, whether it's
    framed.

    (Its background isn't part of this; a pane takes a new one in place.)
    """

    side: dui2.ViewerSide
    frame_style: dui2.ViewerFrameStyle


def page_pane_mode(
    layout: dui2.WindowLayout, page: dui2.Page | None
) -> PaneMode | None:
    """The viewer pane a page gets in a window at a layout, if any.

    Only pages with a viewer get one, and only at layouts with room for
    it (see :attr:`bacommon.docui.v2.Page.viewer`).
    """
    if page is None or page.viewer is None:
        return None
    if not layout_has_viewer_pane(layout):
        return None
    return PaneMode(side=page.viewer_side, frame_style=page.viewer_frame_style)


@dataclass(frozen=True)
class ScrollGeometry:
    """The scroll area a page is laid out against (see page prep)."""

    scroll_width: float
    scroll_height: float
    margins: tuple[float, float, float, float]
    column_insets: tuple[float, float]

    @classmethod
    def from_frame(cls, frame: WindowFrame) -> ScrollGeometry:
        """A window frame's scroll area."""
        return cls(
            scroll_width=frame.scroll_width,
            scroll_height=frame.scroll_height,
            margins=frame.margins,
            column_insets=frame.column_insets,
        )


@dataclass(frozen=True)
class PageGeometries:
    """A window's scroll areas for each pane its pages may ask for.

    Built in the logic thread and handed to background page prep, which
    picks the one for the page it gets (see :meth:`for_page`); the
    window then lays itself out the same way when the page arrives.
    """

    layout: dui2.WindowLayout
    no_pane: ScrollGeometry
    left_pane: ScrollGeometry
    right_pane: ScrollGeometry

    def for_pane(self, pane: PaneMode | None) -> ScrollGeometry:
        """The scroll area beside a pane (or with none)."""
        if pane is None:
            return self.no_pane
        match pane.side:
            case dui2.ViewerSide.LEFT:
                return self.left_pane
            case dui2.ViewerSide.RIGHT:
                return self.right_pane
            case _:
                assert_never(pane.side)

    def pane_for_page(self, page: dui2.Page) -> PaneMode | None:
        """The pane a page gets (see :func:`page_pane_mode`)."""
        return page_pane_mode(self.layout, page)


def page_geometries(
    layout: dui2.WindowLayout,
    frames: dict[dui2.ViewerSide | None, WindowFrame],
) -> PageGeometries:
    """A window's page geometries, from its frame for each pane side."""
    return PageGeometries(
        layout=layout,
        no_pane=ScrollGeometry.from_frame(frames[None]),
        left_pane=ScrollGeometry.from_frame(frames[dui2.ViewerSide.LEFT]),
        right_pane=ScrollGeometry.from_frame(frames[dui2.ViewerSide.RIGHT]),
    )


def scroll_widget_rect(
    frame: WindowFrame,
) -> tuple[float, float, float, float]:
    """Where a window's scroll widget goes (x, y, width, height).

    Its frame's scroll area, reaching out by its margins.
    """
    mleft, mright, mbottom, mtop = frame.margins
    return (
        frame.scroll_left - mleft,
        frame.scroll_bottom - mbottom,
        frame.scroll_width + mleft + mright,
        frame.scroll_height + mbottom + mtop,
    )


def style_scroll_edges(
    scrollwidget: bui.Widget,
    frame: WindowFrame,
    *,
    uiscale: bui.UIScale,
    scroll_edge_style: dui2.ScrollEdgeStyle,
    toolbar_visibility: str,
) -> None:
    """Set up a window's scroll-area edge fades for its frame."""
    pane_side = frame.pane_side
    if uiscale is bui.UIScale.SMALL:
        # (A minimal toolbar has nothing at the bottom to fade toward.
        # Beside a viewer pane that edge is on screen, where
        # sideways-scrolling rows would otherwise cut off hard -- over
        # the pane's edge, even, which overlaps the scroll area here.)
        apply_toolbar_scroll_fades(
            scrollwidget,
            bottom_fade=(
                0.0
                if toolbar_visibility == 'menu_minimal'
                else TOOLBAR_SCROLL_FADE
            ),
            left_fade=(
                SMALL_UI_VIEWER_EDGE_FADE
                if pane_side is dui2.ViewerSide.LEFT
                else 0.0
            ),
            right_fade=(
                SMALL_UI_VIEWER_EDGE_FADE
                if pane_side is dui2.ViewerSide.RIGHT
                else 0.0
            ),
        )
    elif scroll_edge_style is dui2.ScrollEdgeStyle.FADE:
        # Fades over the stretch it reaches out past an outline one (see
        # fade_scroll_extents()), and a bit more at the top.
        fleft, fright, fbottom, ftop = fade_scroll_lengths()
        bui.scrollwidget(
            edit=scrollwidget,
            edge_style='fade',
            edge_fade=(fleft, fbottom, fright, ftop),
        )
