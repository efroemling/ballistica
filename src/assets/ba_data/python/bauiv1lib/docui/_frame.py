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
    DEFAULT_EDGE_FADE,
    SMALL_UI_SCROLL_EXTRA,
    SMALL_UI_TOOLBAR_CLEARANCE,
    TITLE_BAND_HEIGHT,
    POPUP_EDGE_MARGIN,
    POPUP_FADE_REACH,
    POPUP_TITLE_BAND_HEIGHT,
    VIEWER_SCREEN_BUFFER,
    column_inset,
    fade_scroll_extents,
    layout_geometry,
    root_scale,
    title_lift,
    window_content_drop,
    window_insets,
    window_scroll_overhang,
)
from bauiv1lib.docui._panes import scroll_widget_rect, viewer_pane_rect


@dataclass
class WindowFrame:
    """Where a doc-ui window's parts sit (see :func:`window_frames`).

    All in window units, in the space of the window's root container,
    whose size is ``width`` by ``height``. That container lays out
    cleanly: its bounds are the solid part of its backing art (which
    hangs out around them), so they are sized to just what must sit on
    solid art. ``stack_offset`` is where the container sits relative to
    the screen's center (screen units).

    The content rect is the area the layout gives its page: the page
    lays out against it, its own insets placing its content within it
    (selection keeps rows inside it, too). ``extends`` (left, right,
    bottom, top) is how far the scroll area reaches out past it without
    moving content -- under the title band or toolbars, out to the
    screen margins, across a narrow column's sides -- extra room content
    can be seen in (scrolled, or fading) but is never placed in.
    ``page_arrow_insets`` (left, right) is how far in from the scroll
    area's sides sideways-scrolling rows' page arrows sit (clear of the
    screen margins, so on screen).

    ``fade_lengths`` (left, right, bottom, top) is the longest each
    side's scroll-area edge fade may run, in from the extend rect's
    edge (0 for none); None for an outline-style scroll area, which
    doesn't fade. Each page shortens them to end by where its content
    starts (see :func:`~bauiv1lib.docui._panes.edge_fades`).
    """

    width: float
    height: float
    root_scale: float
    stack_offset: tuple[float, float]
    vis_left: float
    vis_top: float
    vis_width: float
    vis_height: float
    content_left: float
    content_bottom: float
    content_width: float
    content_height: float
    extends: tuple[float, float, float, float]
    page_arrow_insets: tuple[float, float]
    fade_lengths: tuple[float, float, float, float] | None

    #: The viewer pane's side, or None for no pane.
    pane_side: dui2.ViewerSide | None
    viewer_width: float

    @property
    def viewer_left(self) -> float:
        """Where the viewer pane (if any) starts: just past the scroll
        area's side (which doesn't extend into a screen margin there)."""
        ext_left, ext_right, _, _ = self.extends
        if self.pane_side is dui2.ViewerSide.RIGHT:
            return self.content_left + self.content_width + ext_right
        return self.content_left - ext_left - self.viewer_width

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
                rects.append(viewer_pane_rect(frame, uiscale))
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
            content_left=frame.content_left - left,
            content_bottom=frame.content_bottom - bottom,
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
    # bounds (these become part of our extends). Our top and bottom
    # stay at the virtual bounds', where our toolbar fades are
    # calibrated. Elsewhere, a fading scroll area reaches out similarly
    # (see fade_scroll_extents()).
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

    # At small ui-scale our scroll area runs full-screen, under the
    # toolbars; content keeps clear of them. Like screen margins and a
    # narrow column's sides, that's extend: room the scroll area reaches
    # into without content moving. (A fixed amount, never reaching on to
    # the screen margins: how much fading shows under the toolbars
    # mustn't depend on a device's margins.)
    clearance = SMALL_UI_TOOLBAR_CLEARANCE if small else 0.0

    return WindowFrame(
        width=width,
        height=height,
        root_scale=rscale,
        stack_offset=(0.0, 0.0),
        vis_left=vis_left,
        vis_top=vis_top,
        vis_width=vis_width,
        vis_height=vis_height,
        content_left=scroll_left + col_inset,
        content_bottom=scroll_bottom + clearance,
        content_width=scroll_width - 2.0 * col_inset,
        content_height=scroll_height - 2.0 * clearance,
        extends=(
            mleft + col_inset,
            mright + col_inset,
            mbottom + clearance,
            mtop + clearance,
        ),
        page_arrow_insets=(mleft, mright),
        fade_lengths=_window_fade_lengths(small, scroll_edge_style, pane_side),
        pane_side=pane_side,
        viewer_width=viewer_width,
    )


def _window_fade_lengths(
    small: bool,
    scroll_edge_style: dui2.ScrollEdgeStyle,
    pane_side: dui2.ViewerSide | None,
) -> tuple[float, float, float, float] | None:
    """A window frame's fade lengths (see :class:`WindowFrame`).

    At small ui-scale our sides run off the screen's edges, where
    content just scrolls away, so they get none; but not a side facing
    a viewer pane, which is on screen. (Sides only: our top and bottom
    run under the toolbars, and fade to keep them readable.) Otherwise,
    all of them if we fade at all.
    """
    fade = DEFAULT_EDGE_FADE
    if small:
        return (
            fade if pane_side is dui2.ViewerSide.LEFT else 0.0,
            fade if pane_side is dui2.ViewerSide.RIGHT else 0.0,
            fade,
            fade,
        )
    if scroll_edge_style is dui2.ScrollEdgeStyle.FADE:
        return (fade, fade, fade, fade)
    return None


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
    layout's content width for the page itself (a narrow viewer layout
    a narrower one) and gives the rest to the viewer, which doesn't
    scroll with the page.
    """
    match layout:
        case dui2.WindowLayout.VIEWER:
            return max(0.0, scroll_width - dui2.SMALL_CONTENT_WIDTH)
        case dui2.WindowLayout.VIEWER_NARROW:
            return max(0.0, scroll_width - dui2.NARROW_CONTENT_WIDTH)
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


def popup_frame(
    size: tuple[float, float],
    uiscale: bui.UIScale,
    virtual_size: tuple[float, float],
    *,
    title_band: bool,
    scroll_edge_style: dui2.ScrollEdgeStyle,
) -> WindowFrame:
    """Lay out a doc-ui popup window around a content area.

    ``size`` is the content area (the popup's page lays out in exactly
    that; see :attr:`bacommon.docui.v2.Popup.size`): raised to
    :data:`bacommon.docui.v2.POPUP_MIN_SIZE`, and shrunk as needed so
    the whole popup fits ``virtual_size`` (the virtual screen), less
    POPUP_EDGE_MARGIN at each edge, at this ui-scale's root scale; its
    page scrolls if it doesn't fit then.
    ``title_band`` is whether a band for the title and close button
    sits above it. As in windows, the popup's bounds are exactly its
    scroll area and that band; a fading scroll area
    (``scroll_edge_style``) reaches out past the content area at top
    and bottom by POPUP_FADE_REACH, and the popup grows to cover it.
    The root scale matches windows', keeping content the same size on
    screen. The popup places itself (``stack_offset`` is left zero;
    see ``DocUIPopupWindow``).
    """
    scale = root_scale(uiscale)
    # Laid out cleanly, as windows are: our bounds are just what must
    # sit on solid backing art (the scroll area, reach-out included,
    # and any title band), the art hanging out around them.
    reach = (
        POPUP_FADE_REACH
        if scroll_edge_style is dui2.ScrollEdgeStyle.FADE
        else 0.0
    )
    band = POPUP_TITLE_BAND_HEIGHT if title_band else 0.0
    lo = dui2.POPUP_MIN_SIZE
    room_w = virtual_size[0] - 2.0 * POPUP_EDGE_MARGIN[0]
    room_h = virtual_size[1] - 2.0 * POPUP_EDGE_MARGIN[1]
    cwidth = max(lo[0], min(room_w / scale, size[0]))
    cheight = max(lo[1], min(room_h / scale - 2.0 * reach - band, size[1]))
    width = cwidth
    height = cheight + 2.0 * reach + band
    return WindowFrame(
        width=width,
        height=height,
        root_scale=scale,
        stack_offset=(0.0, 0.0),
        vis_left=0.0,
        vis_top=height,
        vis_width=width,
        vis_height=height,
        content_left=0.0,
        content_bottom=reach,
        content_width=cwidth,
        content_height=cheight,
        extends=(0.0, 0.0, reach, reach),
        page_arrow_insets=(0.0, 0.0),
        fade_lengths=(
            (DEFAULT_EDGE_FADE,) * 4
            if scroll_edge_style is dui2.ScrollEdgeStyle.FADE
            else None
        ),
        pane_side=None,
        viewer_width=0.0,
    )
