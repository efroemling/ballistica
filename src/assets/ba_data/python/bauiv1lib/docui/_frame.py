# Released under the MIT License. See LICENSE for details.
#
"""Where a doc-ui window's parts sit: its frames."""

from dataclasses import dataclass, replace
from typing import assert_never

import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.utils import get_screen_margins
from bauiv1lib.docui._backbutton import back_button_geometry
from bauiv1lib.docui._layout import (
    SMALL_COLUMN_MAX_WIDTH,
    SMALL_UI_SCROLL_EXTRA,
    TITLE_BAND_HEIGHT,
    VIEWER_NARROW_COLUMN_FRACTION,
    VIEWER_SCREEN_BUFFER,
    column_inset,
    fade_scroll_extents,
    layout_geometry,
    title_lift,
    window_content_drop,
    window_insets,
    window_scroll_overhang,
)
from bauiv1lib.docui._panes import scroll_widget_rect, viewer_insets_v


@dataclass
class WindowFrame:
    """Where a doc-ui window's parts sit (see :func:`window_frames`).

    All in window units, in the space of the window's root container,
    whose size is ``width`` by ``height``. That container lays out
    cleanly: its bounds are the solid part of its backing art (which
    hangs out around them), so they are sized to just what must sit on
    solid art. ``stack_offset`` is where the container sits relative to
    the screen's center (screen units).

    The scroll rect is where an outline-style scroll area sits;
    ``margins`` (left, right, bottom, top) is how far the actual scroll
    area reaches past it, with content inset to match (screen margins at
    small ui-scale, fade extents otherwise).
    """

    width: float
    height: float
    root_scale: float
    stack_offset: tuple[float, float]
    vis_left: float
    vis_top: float
    vis_width: float
    vis_height: float
    scroll_left: float
    scroll_bottom: float
    scroll_width: float
    scroll_height: float
    margins: tuple[float, float, float, float]
    column_insets: tuple[float, float]

    #: The viewer pane's side, or None for no pane.
    pane_side: dui2.ViewerSide | None
    viewer_width: float

    @property
    def viewer_left(self) -> float:
        """Where the viewer pane (if any) starts."""
        if self.pane_side is dui2.ViewerSide.RIGHT:
            return self.scroll_left + self.scroll_width
        return self.scroll_left - self.viewer_width

    @property
    def vis_center(self) -> tuple[float, float]:
        """The visible area's center (where the window's title is
        centered horizontally)."""
        return (
            self.vis_left + 0.5 * self.vis_width,
            self.vis_top - 0.5 * self.vis_height,
        )


def window_frames(
    layout: dui2.WindowLayout,
    uiscale: bui.UIScale,
    scroll_edge_style: dui2.ScrollEdgeStyle,
    *,
    close_style: bool,
) -> dict[dui2.ViewerSide | None, WindowFrame]:
    """Lay out a doc-ui window for each viewer pane its pages may ask for.

    One frame with no pane and one with a pane on either side (if the
    layout has room for one; see :func:`viewer_pane_width`; otherwise
    the same as no pane). A window keeps one root container whatever
    its pages ask for, so all share it: it spans everything that must
    sit on solid backing art in any of them. At medium/large ui-scale
    that's each scroll area (reach-out included), viewer pane and the
    back button (``close_style`` if it's a close button); at small
    ui-scale, where the art must cover the whole screen, it's the whole
    window. The window sits where its visible area would on a window of
    its layout's size centered on the screen.
    """
    small = uiscale is bui.UIScale.SMALL
    frames = {
        side: _centered_frame(layout, uiscale, scroll_edge_style, side)
        for side in (None, dui2.ViewerSide.LEFT, dui2.ViewerSide.RIGHT)
    }
    base = frames[None]
    if small:
        left, bottom, right, top = 0.0, 0.0, base.width, base.height
    else:
        rects: list[tuple[float, float, float, float]] = []
        for frame in frames.values():
            rects.append(scroll_widget_rect(frame))
            if frame.pane_side is not None:
                inset_bottom, inset_top = viewer_insets_v(uiscale)
                rects.append(
                    (
                        frame.viewer_left,
                        frame.scroll_bottom + inset_bottom,
                        frame.viewer_width,
                        frame.scroll_height - inset_bottom - inset_top,
                    )
                )
        back_scale, back_size, back_offset = back_button_geometry(
            layout, scroll_edge_style, close_style=close_style
        )
        rects.append(
            (
                base.vis_left + back_offset[0],
                base.vis_top + back_offset[1] + title_lift(layout, uiscale),
                back_size[0] * back_scale,
                back_size[1] * back_scale,
            )
        )
        left = min(r[0] for r in rects)
        bottom = min(r[1] for r in rects)
        right = max(r[0] + r[2] for r in rects)
        top = max(r[1] + r[3] for r in rects)

    # Our container's center, relative to the centered window's.
    rscale = base.root_scale
    stack_offset = (
        (0.5 * (left + right) - 0.5 * base.width) * rscale,
        (0.5 * (bottom + top) - 0.5 * base.height) * rscale,
    )
    return {
        side: replace(
            frame,
            width=right - left,
            height=top - bottom,
            stack_offset=stack_offset,
            vis_left=frame.vis_left - left,
            vis_top=frame.vis_top - bottom,
            scroll_left=frame.scroll_left - left,
            scroll_bottom=frame.scroll_bottom - bottom,
        )
        for side, frame in frames.items()
    }


def _centered_frame(
    layout: dui2.WindowLayout,
    uiscale: bui.UIScale,
    scroll_edge_style: dui2.ScrollEdgeStyle,
    pane_side: dui2.ViewerSide | None,
) -> WindowFrame:
    """A window's frame for one pane side, on a window of its layout's
    size (see :func:`layout_geometry`) centered on the screen.

    With a viewer pane on ``pane_side`` (if the layout has room for
    one; see :func:`viewer_pane_width`), or none; a viewer layout with
    no pane gives its scroll area the whole width.
    """
    small = uiscale is bui.UIScale.SMALL
    screensize = bui.get_virtual_screen_size()
    width, height, rscale = layout_geometry(layout, uiscale, screensize)

    # Our visible area is limited by the screen size in small mode and
    # our layout's size otherwise. Everything else is laid out relative
    # to the visible area, which stays centered.
    insets = window_insets(layout)  # (sides, top and bottom)
    vis_width = min(width - insets[0], screensize[0] / rscale)
    vis_height = min(height - insets[1], screensize[1] / rscale)

    vis_top = 0.5 * height + 0.5 * vis_height
    if not small:
        vis_top -= window_content_drop(layout)
    vis_left = 0.5 * width - 0.5 * vis_width

    scroll_width = vis_width + (
        0.0 if small else window_scroll_overhang(layout)
    )
    scroll_left = vis_left + 0.5 * (vis_width - scroll_width)
    # Go with full-screen scrollable aread in small ui.
    scroll_height = vis_height + (
        SMALL_UI_SCROLL_EXTRA if small else -TITLE_BAND_HEIGHT
    )
    scroll_bottom = vis_top - (-1 if small else 27) - scroll_height

    # Nudge our vis area up a bit when we can see the whole window
    # (visual fudge factor).
    if not small:
        vis_top += 12.0

    # A viewer pane takes one side of our scroll area (the page scrolls
    # in what remains), so our scroll-widget stops at the pane instead
    # of extending into the screen margin. Unlike scrolling content, the
    # viewer's content doesn't move, so it stays within the virtual
    # bounds (none of it may be cut off by the screen edge) and, in
    # small ui, clear of the toolbars.
    viewer_width = (
        0.0 if pane_side is None else viewer_pane_width(layout, scroll_width)
    )
    if viewer_width <= 0.0:
        pane_side = None

    # In small ui we extend our scrollable area out into the side
    # screen margins (space between the virtual bounds and the actual
    # screen edges) while keeping content laid out within the virtual
    # bounds (page prep gets these margins so it can lay things out
    # accordingly). Our top and bottom stay at the virtual bounds',
    # where our toolbar fades are calibrated. Elsewhere, a fading scroll
    # area reaches out similarly (see fade_scroll_extents()).
    if small:
        mleft, mright, _, _ = get_screen_margins(rscale)
        mbottom = mtop = 0.0
    elif scroll_edge_style is dui2.ScrollEdgeStyle.FADE:
        mleft, mright, mbottom, mtop = fade_scroll_extents()
    else:
        mleft = mright = mbottom = mtop = 0.0

    # Narrow where content is laid out, if our layout calls for it.
    col_inset = column_inset(layout, uiscale, scroll_width)

    if pane_side is dui2.ViewerSide.LEFT:
        scroll_left += viewer_width
        scroll_width -= viewer_width
        mleft = 0.0
    elif pane_side is dui2.ViewerSide.RIGHT:
        scroll_width -= viewer_width
        mright = 0.0

    if pane_side is not None and small:
        viewer_width -= _viewer_screen_overlap(
            pane_side,
            inner_edge=(
                scroll_left
                if pane_side is dui2.ViewerSide.LEFT
                else scroll_left + scroll_width
            ),
            viewer_width=viewer_width,
            window_width=width,
            bounds_half_width=0.5 * screensize[0] / rscale,
            rscale=rscale,
        )

    return WindowFrame(
        width=width,
        height=height,
        root_scale=rscale,
        stack_offset=(0.0, 0.0),
        vis_left=vis_left,
        vis_top=vis_top,
        vis_width=vis_width,
        vis_height=vis_height,
        scroll_left=scroll_left,
        scroll_bottom=scroll_bottom,
        scroll_width=scroll_width,
        scroll_height=scroll_height,
        margins=(mleft, mright, mbottom, mtop),
        column_insets=(col_inset, col_inset),
        pane_side=pane_side,
        viewer_width=viewer_width,
    )


def _viewer_screen_overlap(
    pane_side: dui2.ViewerSide,
    *,
    inner_edge: float,
    viewer_width: float,
    window_width: float,
    bounds_half_width: float,
    rscale: float,
) -> float:
    """How much to narrow a viewer pane (from its outer side) to keep
    its outer edge VIEWER_SCREEN_BUFFER in from the virtual bounds.

    (Which it otherwise meets in small ui. Windows sit centered on the
    screen; all in window units.)
    """
    buffer = VIEWER_SCREEN_BUFFER / rscale
    if pane_side is dui2.ViewerSide.LEFT:
        limit = 0.5 * window_width - bounds_half_width + buffer
        return max(0.0, limit - (inner_edge - viewer_width))
    limit = 0.5 * window_width + bounds_half_width - buffer
    return max(0.0, inner_edge + viewer_width - limit)


def viewer_pane_width(layout: dui2.WindowLayout, scroll_width: float) -> float:
    """Width taken from one side of the scroll area for a viewer pane.

    Zero for layouts without room for one. A viewer layout keeps a small
    layout's column width for the page itself and gives the rest to the
    viewer, which doesn't scroll with the page.
    """
    match layout:
        case dui2.WindowLayout.VIEWER:
            return max(0.0, scroll_width - SMALL_COLUMN_MAX_WIDTH)
        case dui2.WindowLayout.VIEWER_NARROW:
            # A narrower column; the viewer gets the rest.
            return max(
                0.0,
                scroll_width
                - VIEWER_NARROW_COLUMN_FRACTION * SMALL_COLUMN_MAX_WIDTH,
            )
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
            return 0.0
        case _:
            assert_never(layout)
