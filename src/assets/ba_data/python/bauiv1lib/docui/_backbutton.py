# Released under the MIT License. See LICENSE for details.
#
"""Where a doc-ui window's back button goes."""

from typing import assert_never

import bacommon.docui.v2 as dui2

from bauiv1lib.docui._layout import CONTENT_INDENT


def back_button_nudge_x(
    layout: dui2.WindowLayout, scroll_edge_style: dui2.ScrollEdgeStyle
) -> float:
    """How far right of a window's visible left edge its back button sits.

    (Medium/large ui-scale; small uses the system back button.) The
    viewer layout's window is squat enough to get the rounder backing,
    whose top-left corner curves in further than the button's usual
    spot. Small layouts, whose scroll area matches their visible area,
    line it up with their content's indentation once no outline marks
    the scroll area's edge for it to line up with instead.
    """
    match layout:
        case dui2.WindowLayout.VIEWER | dui2.WindowLayout.VIEWER_NARROW:
            return _VIEWER_BACK_NUDGE_X
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
        ):
            match scroll_edge_style:
                case dui2.ScrollEdgeStyle.FADE:
                    return CONTENT_INDENT
                case dui2.ScrollEdgeStyle.OUTLINE:
                    return 0.0
                case _:
                    assert_never(scroll_edge_style)
        case (
            dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.LARGE
        ):
            return 0.0
        case _:
            assert_never(layout)


#: See back_button_nudge_x().
_VIEWER_BACK_NUDGE_X = 45.0

#: The back button's base geometry (medium/large ui-scale): scale,
#: size (close style, back style), and its bottom-left's offset from
#: the window's visible top-left. These placed it; it read a little
#: small, so back_button_geometry() grows it about its center.
_BACK_BASE_SCALE = 0.8
_BACK_CLOSE_SIZE = (50.0, 50.0)
_BACK_BACK_SIZE = (60.0, 55.0)
_BACK_BASE_OFFSET = (2.0, -33.0)
_BACK_GROW = 1.1


def back_button_geometry(
    layout: dui2.WindowLayout,
    scroll_edge_style: dui2.ScrollEdgeStyle,
    close_style: bool,
) -> tuple[float, tuple[float, float], tuple[float, float]]:
    """A window's back button: (scale, size, bottom-left offset).

    The offset is from the window's visible top-left corner (its
    layout's nudge included), at medium/large ui-scale. ``close_style``
    is whether it is a close (auxiliary window) rather than back button.
    """
    size = _BACK_CLOSE_SIZE if close_style else _BACK_BACK_SIZE
    # Grown about its center: the bottom-left moves back by half the
    # growth in each axis.
    shift = tuple(
        0.5 * dim * _BACK_BASE_SCALE * (_BACK_GROW - 1.0) for dim in size
    )
    return (
        _BACK_BASE_SCALE * _BACK_GROW,
        size,
        (
            _BACK_BASE_OFFSET[0]
            + back_button_nudge_x(layout, scroll_edge_style)
            - shift[0],
            _BACK_BASE_OFFSET[1] - shift[1],
        ),
    )
