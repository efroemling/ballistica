# Released under the MIT License. See LICENSE for details.
#
"""Useful bits to use with UIs."""

import bauiv1 as bui

#: How far in from the top/bottom of a full-screen (small ui-scale)
#: scroll area :func:`apply_toolbar_scroll_fades` fades content, in the
#: scroll area's local units. Calibrated against the toolbars, so it
#: assumes the scroll area's top and bottom sit at the virtual rect's.
TOOLBAR_SCROLL_FADE = 85.0


def get_screen_margins(root_scale: float) -> tuple[float, float, float, float]:
    """Return visible-screen margins outside the virtual rect.

    Returns ``(left, right, bottom, top)`` distances between the
    virtual rect edges and the virtual outer rect (true visible area)
    edges, converted into a window's local coordinate space via its
    root container's ``root_scale``. All values are zero unless the
    virtual bounds are inset (camera cutouts and such).

    Windows that fill the screen at small ui-scale should extend
    backing elements such as scroll areas outward by these amounts
    (insetting their content by the same amounts so it stays put) so
    the backing reaches the true screen edges instead of stopping at
    the virtual rect. A scroll area using
    :func:`apply_toolbar_scroll_fades` should only do so at its sides,
    keeping its top and bottom at the virtual rect's.
    """
    outer = bui.get_virtual_outer_rect()
    vsize = bui.get_virtual_screen_size()
    return (
        max(0.0, 0.0 - outer[0]) / root_scale,
        max(0.0, outer[2] - vsize[0]) / root_scale,
        max(0.0, 0.0 - outer[1]) / root_scale,
        max(0.0, outer[3] - vsize[1]) / root_scale,
    )


def apply_toolbar_scroll_fades(
    scrollwidget: bui.Widget,
    *,
    top_fade: float = TOOLBAR_SCROLL_FADE,
    bottom_fade: float = TOOLBAR_SCROLL_FADE,
    left_fade: float = 0.0,
    right_fade: float = 0.0,
) -> None:
    """Fade a full-screen scroll area's content out toward the toolbars.

    For scroll areas filling the screen at small ui-scale. Content fades
    into the window backing over ``top_fade``/``bottom_fade`` units in
    from the top/bottom (zero for none). The sides get nothing by
    default, as content just scrolls off the screen there; a scroll
    area with a side edge on screen instead (beside a viewer pane,
    say) can fade that one over ``left_fade``/``right_fade``. The
    scroll area must be
    a direct child of a window with a backing, with its top and bottom
    at the virtual rect's (not extended into screen margins), which the
    default :data:`TOOLBAR_SCROLL_FADE` is calibrated against.
    """
    bui.scrollwidget(
        edit=scrollwidget,
        edge_style='fade',
        edge_fade=(left_fade, bottom_fade, right_fade, top_fade),
    )
