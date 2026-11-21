# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui viewer panes: which one a page gets, and the room around it."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.docui._frame import WindowFrame
    from bauiv1lib.docui._pagelook import PageLook


def viewer_insets_v(uiscale: bui.UIScale) -> tuple[float, float]:
    """How far a viewer pane's bottom and top edges sit in from the
    content rect's (negative: out past it).

    At small ui-scale it reaches out a little past content toward the
    toolbars (still clear of them: the pane's own frame and rounded
    corners already read as spacing). All tuned by eye.
    """
    match uiscale:
        case bui.UIScale.SMALL:
            return (-15.0, -15.0)
        case bui.UIScale.MEDIUM | bui.UIScale.LARGE:
            # The whole pane a touch lower.
            return (-5.0, 5.0)
        case _:
            assert_never(uiscale)


def viewer_pane_rect(
    frame: WindowFrame, uiscale: bui.UIScale
) -> tuple[float, float, float, float]:
    """Where a window frame's viewer pane goes (x, y, width, height).

    Beside its scroll area, spanning its content rect's height with its
    edges nudged per ui-scale (see :func:`viewer_insets_v`).
    (Meaningless for a frame with no pane.)
    """
    inset_bottom, inset_top = viewer_insets_v(uiscale)
    return (
        frame.viewer_left,
        frame.content_bottom + inset_bottom,
        frame.viewer_width,
        frame.content_height - inset_bottom - inset_top,
    )


def edge_fades(
    frame: WindowFrame, look: PageLook
) -> tuple[float, float, float, float] | None:
    """How far a frame's scroll-area edge fades reach in for a page.

    (left, right, bottom, top), in from the extend rect's edges; None
    for no fades. Each is the frame's fade length on that side (see
    :class:`~bauiv1lib.docui._frame.WindowFrame`), shortened to end by
    the page's inset line (the side's extend plus the page's horizontal
    or vertical inset), so content at rest is never faded. A shortened
    fade is squeezed, not cut off: it still runs all the way from clear
    to solid.
    """
    if frame.fade_lengths is None:
        return None
    fleft, fright, fbottom, ftop = frame.fade_lengths
    eleft, eright, ebottom, etop = frame.extends
    h_inset, v_inset = look.h_inset, look.v_inset
    return (
        max(0.0, min(fleft, eleft + h_inset)),
        max(0.0, min(fright, eright + h_inset)),
        max(0.0, min(fbottom, ebottom + v_inset)),
        max(0.0, min(ftop, etop + v_inset)),
    )


def apply_edge_fades(
    scrollwidget: bui.Widget, fades: tuple[float, float, float, float] | None
) -> None:
    """Give a scroll widget edge fades (see :func:`edge_fades`)."""
    if fades is None:
        return
    fleft, fright, fbottom, ftop = fades
    bui.scrollwidget(
        edit=scrollwidget,
        edge_style='fade',
        edge_fade=(fleft, fbottom, fright, ftop),
    )


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
    """What a page is laid out against (see page prep).

    Its frame's content rect size, extends and page-arrow insets (see
    :class:`~bauiv1lib.docui._frame.WindowFrame`).
    """

    content_width: float
    content_height: float
    extends: tuple[float, float, float, float]
    page_arrow_insets: tuple[float, float]

    @classmethod
    def from_frame(cls, frame: WindowFrame) -> ScrollGeometry:
        """A window (or popup) frame's."""
        return cls(
            content_width=frame.content_width,
            content_height=frame.content_height,
            extends=frame.extends,
            page_arrow_insets=frame.page_arrow_insets,
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

    Its frame's content rect, reaching out by its extends (its extend
    rect).
    """
    ext_left, ext_right, ext_bottom, ext_top = frame.extends
    return (
        frame.content_left - ext_left,
        frame.content_bottom - ext_bottom,
        frame.content_width + ext_left + ext_right,
        frame.content_height + ext_bottom + ext_top,
    )


def window_edge_fades(
    frame: WindowFrame,
    *,
    uiscale: bui.UIScale,
    toolbar_visibility: str,
    look: PageLook,
) -> tuple[float, float, float, float] | None:
    """How far a window's scroll-area edge fades reach in (or None).

    Its frame's for its page (see :func:`edge_fades`), less any at the
    bottom at small ui-scale under a minimal toolbar, which has nothing
    there to fade toward.
    """
    fades = edge_fades(frame, look)
    if (
        fades is not None
        and uiscale is bui.UIScale.SMALL
        and toolbar_visibility == 'menu_minimal'
    ):
        fleft, fright, _fbottom, ftop = fades
        return (fleft, fright, 0.0, ftop)
    return fades
