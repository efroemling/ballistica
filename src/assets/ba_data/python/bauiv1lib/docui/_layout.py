# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui window layout geometry."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
import bauiv1 as bui
from bauiv1lib.utils import get_screen_margins

if TYPE_CHECKING:
    pass

#: Widest the content column gets for a small layout at small ui-scale
#: (window units; the window itself stays full-screen).
SMALL_COLUMN_MAX_WIDTH = 600.0

#: A small layout's insets from backing to visible area at medium/large
#: ui-scale (see window_insets()); tighter than the standard ones, as
#: its rounder backing leaves less dead space at its edges.
_SMALL_SIDE_INSETS = 100.0
_SMALL_VERTICAL_INSETS = 66.0

#: A small layout's backing at medium/large ui-scale: just wide enough
#: that its scroll area is the small-ui column's width (so content lays
#: out exactly as in that column), and a bit under 0.6x that tall --
#: squat enough to get containers' rounder small-window backing.
_SMALL_WIDTH = SMALL_COLUMN_MAX_WIDTH + _SMALL_SIDE_INSETS
_SMALL_HEIGHT = _SMALL_WIDTH * 0.594

#: A small-taller layout's historical backing height at large ui-scale
#: (twice a small layout's height, scaled up a bit); small-tall layouts
#: are sized from it. (Small-taller windows themselves now follow the
#: screen's height; see layout_geometry().)
_SMALL_TALLER_HEIGHT = _SMALL_HEIGHT * 2.0
_SMALL_TALLER_LARGE_SCALE = 1.1

#: A small-tall layout's backing height: midway between a small
#: layout's and a small-taller's at large ui-scale, at every
#: medium/large ui-scale (it fits medium's screen, so like the other
#: layouts it is the same window at both, just scaled differently).
_SMALL_TALL_HEIGHT = 0.5 * (
    _SMALL_HEIGHT + _SMALL_TALLER_HEIGHT * _SMALL_TALLER_LARGE_SCALE
)

#: How much of each extra unit of screen height a small-taller (or
#: wide-taller) window's backing grows by at medium/large ui-scale (its
#: height follows the screen; see _taller_height()).
SMALL_TALLER_SCREEN_HEIGHT_FRACTION = 0.8

#: How much of the screen's height and width a large window's backing
#: takes at medium/large ui-scale (its size follows the screen; see
#: layout_geometry()); on wide screens its height limits its width, so
#: it keeps the standard backing.
LARGE_SCREEN_HEIGHT_FRACTION = 0.89
LARGE_SCREEN_WIDTH_FRACTION = 0.98

#: Every layout's root scale at small ui-scale, where windows fill the
#: screen.
SMALL_UI_ROOT_SCALE = 1.45

#: Popups (menus, popup text) relative to the windows they pop up
#: from, the same at every ui-scale so they stay in proportion with
#: page content. This is what the generic popup-menu scale gives at
#: small ui-scale; that generic scale shrinks relative to doc-ui
#: windows at medium/large, which is why we don't use it.
_POPUP_TO_ROOT_SCALE = 2.3 / SMALL_UI_ROOT_SCALE

#: The shortest the virtual screen gets (16:9 and wider screens; taller
#: ones get more height).
MIN_VIRTUAL_SCREEN_HEIGHT = 720.0

#: The narrowest the virtual screen gets (16:9 and taller screens; wider
#: ones get more width).
MIN_VIRTUAL_SCREEN_WIDTH = 1280.0

#: Height a window's title band takes off the top of its scroll area at
#: medium/large ui-scale (see DocUIWindow).
TITLE_BAND_HEIGHT = 43.0

#: How much taller than the visible area a small-ui scroll area is (it
#: runs full-screen; see DocUIWindow).
SMALL_UI_SCROLL_EXTRA = 1.0

#: Clearance page content gets above and below at small ui-scale, where
#: the scroll area runs under the toolbars (see page prep).
SMALL_UI_TOOLBAR_CLEARANCE = 70.0

#: Viewer layouts' left fades run shorter than the others' (at every
#: ui-scale): their content starts close to that edge, and a full-length
#: fade crept into it.
_VIEWER_LEFT_FADE_SCALE = 0.66

#: How far in from a viewer layout's scroll-area left edge (where its
#: viewer pane meets it) content fades at small ui-scale, so
#: sideways-scrolling rows fade out before reaching the pane rather
#: than cutting off hard; short of where page content starts, so
#: resting content is untouched (tuned by eye).
SMALL_UI_VIEWER_LEFT_FADE = 60.0 * _VIEWER_LEFT_FADE_SCALE

#: How far a viewer pane stays in from the top and bottom of the scroll
#: area at small ui-scale, clearing the toolbars it runs under (less
#: than page content's clearance, as the pane's own frame and rounded
#: corners already read as spacing; tuned by eye).
SMALL_UI_VIEWER_INSET_V = 40.0

#: Page prep's base buffer above and below page content (all ui-scales).
#: (Doc-ui scroll widgets lay out cleanly -- their content spans their
#: full height -- so this is all the room there is.)
PAGE_BASE_BUFFER = 27.0

#: Where a button row's outermost buttons (at its default side padding)
#: sit in from the column's edges, both sides.
BUTTON_INSET = 28.0

#: Where text (titles, labels, footnotes) sits in from the column's
#: edges, both sides; buttons draw a few units inside their own bounds,
#: so this lines text up with their visible edges. Control rows' (and
#: fill rows') contents span from here to here too: labels start where
#: text does, controls end at its mirror.
TEXT_INSET = 33.0

#: Where a button row's side padding starts in from the column's edges;
#: its default padding takes its buttons on to :data:`BUTTON_INSET`.
BUTTON_ROW_EDGE_INSET = 18.0

#: Wide and wider layouts' visible height at medium/large ui-scale:
#: whatever gives their pages exactly the height they get at small
#: ui-scale on the shortest screen, so a page that fits one fits all.
#: (The small-ui one gains the scroll extra but pays toolbar clearance;
#: the medium/large one pays the title band.)
WIDE_VISIBLE_HEIGHT = (
    MIN_VIRTUAL_SCREEN_HEIGHT / SMALL_UI_ROOT_SCALE
    + SMALL_UI_SCROLL_EXTRA
    - 2.0 * SMALL_UI_TOOLBAR_CLEARANCE
    + TITLE_BAND_HEIGHT
)

#: Height wide and wider pages have for their rows (the scroll area's
#: visible extent less page prep's base buffers), at every ui-scale.
WIDE_PAGE_ROWS_HEIGHT = (
    WIDE_VISIBLE_HEIGHT - TITLE_BAND_HEIGHT - 2.0 * PAGE_BASE_BUFFER
)

#: Wide and wider layouts' designed shape at medium/large ui-scale: a
#: shared backing height (loosely after the classic play window, then
#: tuned by eye) and insets (see window_insets()) a bit roomier than a
#: small layout's so content (the back button especially) clears the
#: rounder backing's edges, plus scroll-area side insets well outside
#: the visible area, as their wide content is meant to show no scroll
#: bounds (see window_scroll_overhang()). Both must stay under 0.6
#: height/width for containers' rounder backing. These set the shape
#: (proportions); the actual window units are these times
#: _WIDE_UNIT_SCALE (see below). Widths follow further down.
_WIDE_DESIGN_HEIGHT = 570.0
_WIDE_DESIGN_SIDE_INSETS = 140.0
_WIDE_DESIGN_VERTICAL_INSETS = 86.0
_WIDE_DESIGN_SCROLL_SIDE_INSETS = 60.0

#: Scales the design numbers into window units so the visible height
#: comes out at WIDE_VISIBLE_HEIGHT. Root scale is left at each
#: ui-scale's default, like every other layout, so doc-ui content is
#: the same size on screen in all of them (at large ui-scale, meant for
#: big displays, that makes these windows fairly small; blowing
#: phone-sized UI up to fill a giant screen looks worse).
_WIDE_UNIT_SCALE = WIDE_VISIBLE_HEIGHT / (
    _WIDE_DESIGN_HEIGHT - _WIDE_DESIGN_VERTICAL_INSETS
)

#: Width wide pages have for their content (their scroll area's width),
#: at every ui-scale: small ui-scale's on the narrowest screen. So wide
#: pages can be designed to fill the screen exactly, everywhere.
WIDE_PAGE_WIDTH = MIN_VIRTUAL_SCREEN_WIDTH / SMALL_UI_ROOT_SCALE

#: Wide's backing width comes from WIDE_PAGE_WIDTH; wider's follows the
#: screen (see WIDER_SCREEN_WIDTH_FRACTION), as its content is expected
#: to overflow the screen anyway, so showing more of it at medium/large
#: means less scrolling (at small ui-scale the two are the same, filling
#: the screen).
_WIDE_DESIGN_WIDTH = (
    WIDE_PAGE_WIDTH / _WIDE_UNIT_SCALE + _WIDE_DESIGN_SCROLL_SIDE_INSETS
)

#: Extra backing a wider window gets at medium/large beyond the above,
#: at each side and at the bottom, with its insets grown to match so its
#: visible and scroll areas (and thus its pages) stay exactly as they
#: are: its long scrolling rows read better with more backing around
#: them, and sat a bit low in it without the extra below.
_WIDER_DESIGN_EXTRA_SIDE = 50.0
_WIDER_DESIGN_EXTRA_BOTTOM = 40.0

#: The same for a wide window: about 5% more backing width overall,
#: keeping its content from crowding its edges, and some below, as its
#: content otherwise sat low in its squat backing.
_WIDE_DESIGN_EXTRA_SIDE = _WIDE_DESIGN_WIDTH * 0.025
_WIDE_DESIGN_EXTRA_BOTTOM = 28.0

_WIDE_BASE_HEIGHT = _WIDE_DESIGN_HEIGHT * _WIDE_UNIT_SCALE
_WIDE_EXTRA_SIDE = _WIDE_DESIGN_EXTRA_SIDE * _WIDE_UNIT_SCALE
_WIDE_EXTRA_BOTTOM = _WIDE_DESIGN_EXTRA_BOTTOM * _WIDE_UNIT_SCALE
_WIDE_WIDTH = _WIDE_DESIGN_WIDTH * _WIDE_UNIT_SCALE + 2.0 * _WIDE_EXTRA_SIDE
_WIDE_HEIGHT = _WIDE_BASE_HEIGHT + _WIDE_EXTRA_BOTTOM
_WIDE_SIDE_INSETS = _WIDE_DESIGN_SIDE_INSETS * _WIDE_UNIT_SCALE
_WIDE_VERTICAL_INSETS = _WIDE_DESIGN_VERTICAL_INSETS * _WIDE_UNIT_SCALE
_WIDER_EXTRA_SIDE = _WIDER_DESIGN_EXTRA_SIDE * _WIDE_UNIT_SCALE
_WIDER_EXTRA_BOTTOM = _WIDER_DESIGN_EXTRA_BOTTOM * _WIDE_UNIT_SCALE
_WIDER_HEIGHT = _WIDE_BASE_HEIGHT + _WIDER_EXTRA_BOTTOM

#: A wide-tall window's backing height (medium/large ui-scale): a wide
#: window's, grown so its visible area is as tall as a small-tall
#: window's (its insets and everything else stay wide's).
_WIDE_TALL_HEIGHT = _WIDE_HEIGHT + (
    (_SMALL_TALL_HEIGHT - _SMALL_VERTICAL_INSETS) - WIDE_VISIBLE_HEIGHT
)

#: How much of the screen's width a wider window's backing takes at
#: medium/large ui-scale (its width follows the screen; see
#: layout_geometry()): its long scrolling rows show as much at once as
#: the screen allows. All the extra goes to its visible and scroll
#: areas.
WIDER_SCREEN_WIDTH_FRACTION = 0.85


def window_content_drop(layout: dui2.WindowLayout) -> float:
    """How far below center a window's visible area sits (medium/large).

    Moves the title, back button and scroll area down together; the
    small layout's tight insets otherwise put its back button close to
    the backing's top edge.
    """
    match layout:
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
        ):
            return 3.0
        case (
            dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
        ):
            # Their squat rounder backing otherwise reads top-heavy;
            # less half the extra backing height, which the visible
            # area (centered in the backing) would otherwise split
            # with the top, so all of it lands below (see
            # _WIDE_DESIGN_EXTRA_BOTTOM).
            return 12.0 - 0.5 * _WIDE_EXTRA_BOTTOM
        case dui2.WindowLayout.WIDER:
            # As wide (see _WIDER_DESIGN_EXTRA_BOTTOM).
            return 12.0 - 0.5 * _WIDER_EXTRA_BOTTOM
        case (
            dui2.WindowLayout.LARGE
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
        ):
            return 0.0
        case _:
            assert_never(layout)


def title_lift(layout: dui2.WindowLayout, uiscale: bui.UIScale) -> float:
    """How far above its usual spot a window's title and back button sit.

    (Medium/large ui-scale.) A large window at medium ui-scale otherwise
    reads a bit crowded against its scroll area.
    """
    match layout:
        case dui2.WindowLayout.LARGE:
            return 6.0 if uiscale is bui.UIScale.MEDIUM else 0.0
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
        ):
            return 0.0
        case _:
            assert_never(layout)


def backing_offset_x(
    layout: dui2.WindowLayout, uiscale: bui.UIScale, width: float
) -> float:
    """How far to shift a window's backing art sideways (only the art).

    Containers place their backing art lopsidedly (it runs further past
    their right edge than their left), which on a large window's broad
    shape at medium/large ui-scale reads as sitting right of the window's
    content -- and lets the back button crowd the art's left edge. A
    fraction of the window's ``width``, as the skew grows with it.
    """
    if uiscale is bui.UIScale.SMALL:
        return 0.0
    match layout:
        case dui2.WindowLayout.LARGE:
            return -0.01 * width
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
        ):
            return 0.0
        case _:
            assert_never(layout)


def window_insets(layout: dui2.WindowLayout) -> tuple[float, float]:
    """How much smaller a window's visible area is than its backing.

    Returns (both sides together, top and bottom together) at
    medium/large ui-scale (at small ui-scale the screen limits the
    visible area instead).
    """
    match layout:
        case dui2.WindowLayout.VIEWER | dui2.WindowLayout.VIEWER_NARROW:
            # Its rounder backing wants a bit more room above and
            # below its content (see layout_geometry).
            return 150.0, 80.0 + 2.0 * _VIEWER_EXTRA_PAD_V
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
        ):
            return _SMALL_SIDE_INSETS, _SMALL_VERTICAL_INSETS
        case (
            dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
        ):
            return (
                _WIDE_SIDE_INSETS + 2.0 * _WIDE_EXTRA_SIDE,
                _WIDE_VERTICAL_INSETS + _WIDE_EXTRA_BOTTOM,
            )
        case dui2.WindowLayout.WIDER:
            return (
                _WIDE_SIDE_INSETS + 2.0 * _WIDER_EXTRA_SIDE,
                _WIDE_VERTICAL_INSETS + _WIDER_EXTRA_BOTTOM,
            )
        case dui2.WindowLayout.LARGE:
            return 150.0, 80.0
        case _:
            assert_never(layout)


#: Extra backing shown above and below the viewer layout's content
#: (each), and how much of that comes from making its window taller
#: (the rest comes out of its scroll area and viewer).
_VIEWER_EXTRA_PAD_V = 20.0
_VIEWER_EXTRA_HEIGHT = 20.0

#: A narrow viewer layout's column, as a share of a viewer layout's
#: (a small layout's), and its window's width (medium/large ui-scale)
#: as a share of a viewer layout's.
_VIEWER_NARROW_COLUMN_FRACTION = 2.0 / 3.0
_VIEWER_NARROW_WIDTH_SCALE = 0.9

#: Medium ui-scale's standard window height (the viewer layout uses it
#: at large too).
_MEDIUM_HEIGHT = 729.0


def window_scroll_overhang(layout: dui2.WindowLayout) -> float:
    """How much wider than the visible area the scroll area is.

    Both sides together, at medium/large ui-scale. The title and back
    button stay within the visible area; wide and wider layouts run
    their scroll area out past it, back toward the backing's edges, as
    their wide content is meant to show no scroll bounds anyway. A
    large layout's runs out just far enough that content's standard
    indentation lines up with the back button's left edge.
    """
    match layout:
        case (
            dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
        ):
            return (
                _WIDE_DESIGN_SIDE_INSETS - _WIDE_DESIGN_SCROLL_SIDE_INSETS
            ) * _WIDE_UNIT_SCALE
        case dui2.WindowLayout.LARGE:
            return 2.0 * _LARGE_SCROLL_OVERHANG_SIDE
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
        ):
            return 0.0
        case _:
            assert_never(layout)


#: Content's standard indentation from its scroll area's edge, about
#: (BUTTON_INSET, TEXT_INSET between): what a large layout's scroll area
#: overhangs its visible area by on each side (see
#: window_scroll_overhang()) and a fading small layout's back button is
#: nudged in by (see back_button_nudge_x()), so content and back button
#: line up either way.
_CONTENT_INDENT = 30.0
_LARGE_SCROLL_OVERHANG_SIDE = _CONTENT_INDENT


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
                    return _CONTENT_INDENT
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


def resizes_with_screen(
    layout: dui2.WindowLayout, uiscale: bui.UIScale
) -> bool:
    """Whether a layout's window depends on the screen's size.

    Such windows rebuild themselves when the screen's size changes. At
    small ui-scale every layout fills the screen; at medium/large only
    those whose size follows it (see :func:`layout_geometry`) do.
    """
    if uiscale is bui.UIScale.SMALL:
        return True
    match layout:
        case (
            dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.LARGE
        ):
            return True
        case (
            dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
            | dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
        ):
            return False
        case _:
            assert_never(layout)


def root_scale(uiscale: bui.UIScale) -> float:
    """Every layout's root scale at a ui-scale."""
    match uiscale:
        case bui.UIScale.SMALL:
            return SMALL_UI_ROOT_SCALE
        case bui.UIScale.MEDIUM:
            return 0.9
        case bui.UIScale.LARGE:
            return 0.65
        case _:
            assert_never(uiscale)


def scale_like_windows(
    small_scale: float, uiscale: bui.UIScale | None = None
) -> float:
    """Scale something tuned at small ui-scale as doc-ui windows scale.

    Given the scale that looks right at small ui-scale, returns the
    scale keeping it in the same proportion to doc-ui windows at
    ``uiscale`` (the current ui-scale by default). For non-doc-ui
    windows that should size themselves in step with doc-ui.
    """
    if uiscale is None:
        uiscale = bui.app.ui_v1.uiscale
    return small_scale * root_scale(uiscale) / SMALL_UI_ROOT_SCALE


def popup_scale(uiscale: bui.UIScale | None = None) -> float:
    """Scale for doc-ui popups (menus, popup text) at a ui-scale.

    In proportion with doc-ui windows at every ui-scale. Defaults to
    the current ui-scale.
    """
    if uiscale is None:
        uiscale = bui.app.ui_v1.uiscale
    return root_scale(uiscale) * _POPUP_TO_ROOT_SCALE


def layout_geometry(
    layout: dui2.WindowLayout,
    uiscale: bui.UIScale,
    screen_size: tuple[float, float],
) -> tuple[float, float, float]:
    """A layout's backing (width, height) and root scale at a ui-scale.

    Medium's and large's large widths are as wide as their heights allow
    while keeping the nicer window backing (containers switch to a
    squatter, rounder one once height drops to 0.6x width); small is
    sized to the small-ui column (see _SMALL_WIDTH), deliberately just
    squat enough for that rounder one; wide and wider are fixed shapes
    getting the rounder one too, their window units scaled so their pages
    get the same height at every ui-scale (see WIDE_VISIBLE_HEIGHT). At
    small ui-scale every layout fills the screen (a small layout narrows
    its content instead; see :func:`column_inset`). A small-taller (or
    wide-taller) window's height at medium/large ui-scale grows with the
    screen's (``screen_size``, virtual units), from its '-tall'
    sibling's height on the shortest screen at medium ui-scale (see
    _taller_height()), so it makes use of tall screens; likewise a
    wider window's width as a fixed share of the screen's
    (:data:`WIDER_SCREEN_WIDTH_FRACTION`) and a large window's height
    and width (:data:`LARGE_SCREEN_HEIGHT_FRACTION`,
    :data:`LARGE_SCREEN_WIDTH_FRACTION`).
    """
    scale = root_scale(uiscale)
    match uiscale:
        case bui.UIScale.SMALL:
            return 1400.0, 1200.0, scale
        case bui.UIScale.MEDIUM:
            width, height = 1214.0, _MEDIUM_HEIGHT
        case bui.UIScale.LARGE:
            width, height = 1641.0, 985.0
        case _:
            assert_never(uiscale)
    match layout:
        case dui2.WindowLayout.LARGE:
            # Follows the screen both ways, but never squat enough to
            # switch to the rounder backing (on wide screens its height
            # limits its width).
            height = LARGE_SCREEN_HEIGHT_FRACTION * screen_size[1] / scale
            width = min(
                LARGE_SCREEN_WIDTH_FRACTION * screen_size[0] / scale,
                height / 0.601,
            )
        case dui2.WindowLayout.VIEWER | dui2.WindowLayout.VIEWER_NARROW:
            # The same window at medium and large (just scaled
            # differently, so a viewer never gets blown up big on
            # large screens): medium's standard height plus a bit, and
            # just wide enough for a square viewer pane. The pane runs
            # the scroll area's height (visible height less the title
            # band) and gets whatever width the page column leaves
            # (see viewer_pane_width); the page column keeps its width.
            height = _MEDIUM_HEIGHT + _VIEWER_EXTRA_HEIGHT
            side_insets, vertical_insets = window_insets(layout)
            pane_height = height - vertical_insets - TITLE_BAND_HEIGHT
            width = pane_height + SMALL_COLUMN_MAX_WIDTH + side_insets
            # A narrow viewer's window is narrower too.
            if layout is dui2.WindowLayout.VIEWER_NARROW:
                width *= _VIEWER_NARROW_WIDTH_SCALE
        case dui2.WindowLayout.SMALL:
            width, height = _SMALL_WIDTH, _SMALL_HEIGHT
        case dui2.WindowLayout.SMALL_TALL:
            width, height = _SMALL_WIDTH, _SMALL_TALL_HEIGHT
        case dui2.WindowLayout.SMALL_TALLER:
            width = _SMALL_WIDTH
            height = _taller_height(_SMALL_TALL_HEIGHT, screen_size[1], scale)
        case dui2.WindowLayout.WIDE:
            width, height = _WIDE_WIDTH, _WIDE_HEIGHT
        case dui2.WindowLayout.WIDE_TALL:
            width, height = _WIDE_WIDTH, _WIDE_TALL_HEIGHT
        case dui2.WindowLayout.WIDE_TALLER:
            width = _WIDE_WIDTH
            height = _taller_height(_WIDE_TALL_HEIGHT, screen_size[1], scale)
        case dui2.WindowLayout.WIDER:
            # (Never narrow enough to lose the rounder backing it's
            # designed around.)
            height = _WIDER_HEIGHT
            width = max(
                height / 0.59,
                WIDER_SCREEN_WIDTH_FRACTION * screen_size[0] / scale,
            )
        case _:
            assert_never(layout)
    return width, height, scale


def _taller_height(
    tall_height: float, screen_height: float, scale: float
) -> float:
    """A '-taller' window's backing height (medium/large ui-scale).

    Grows with the screen's height (``screen_height``, virtual units;
    :data:`SMALL_TALLER_SCREEN_HEIGHT_FRACTION` of each extra unit),
    calibrated so the shortest case -- medium ui-scale on the shortest
    screen -- comes out at its '-tall' sibling's ``tall_height``; it is
    never shorter than that, and taller everywhere else.
    """
    shortest = MIN_VIRTUAL_SCREEN_HEIGHT / root_scale(bui.UIScale.MEDIUM)
    return tall_height + SMALL_TALLER_SCREEN_HEIGHT_FRACTION * (
        screen_height / scale - shortest
    )


def column_inset(
    layout: dui2.WindowLayout, uiscale: bui.UIScale, scroll_width: float
) -> float:
    """Inset at each side narrowing content to a column (0 for none).

    A small layout at small ui-scale keeps the full-screen window and
    scroll area but lays content out in a centered column of limited
    width, keeping labels near their values. A wide layout does the
    same with a column of its page width (WIDE_PAGE_WIDTH): it's
    designed to fit the narrowest screen, so on wider ones its content
    (left-aligned content included) sits centered, as it does in its
    medium/large window. Wider content runs the full screen width.
    """
    if uiscale is not bui.UIScale.SMALL:
        return 0.0
    match layout:
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
        ):
            return max(0.0, 0.5 * (scroll_width - SMALL_COLUMN_MAX_WIDTH))
        case (
            dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
        ):
            return max(0.0, 0.5 * (scroll_width - WIDE_PAGE_WIDTH))
        case (
            dui2.WindowLayout.LARGE
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
            | dui2.WindowLayout.WIDER
        ):
            return 0.0
        case _:
            assert_never(layout)


def default_scroll_edge_style(
    layout: dui2.WindowLayout,
) -> dui2.ScrollEdgeStyle:
    """The scroll edge style a layout gets unless a window asks otherwise.

    (Medium/large ui-scale; small ui-scale always fades toward the
    toolbars.)
    """
    match layout:
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.LARGE
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.VIEWER_NARROW
        ):
            return dui2.ScrollEdgeStyle.FADE
        case _:
            assert_never(layout)


def fade_scroll_extents(
    layout: dui2.WindowLayout,
) -> tuple[float, float, float, float]:
    """How far a fade-style scroll area reaches past an outline one's.

    Returns (left, right, bottom, top), at medium/large ui-scale. With no
    outline to look cramped against the window's edges, the scroll area
    reaches out toward them (and up behind the title); content gets
    inset by the same amounts, so it keeps exactly the space and spot it
    would have with an outline, and fades only once scrolled past where
    an outline would have clipped it. A viewer layout's left borders its
    framed viewer pane, so stays put.
    """
    match layout:
        case dui2.WindowLayout.VIEWER | dui2.WindowLayout.VIEWER_NARROW:
            return (0.0, _FADE_EXTENT, _FADE_EXTENT, _FADE_EXTENT)
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.LARGE
        ):
            return (_FADE_EXTENT, _FADE_EXTENT, _FADE_EXTENT, _FADE_EXTENT)
        case _:
            assert_never(layout)


#: See fade_scroll_extents().
_FADE_EXTENT = 40.0


def fit_fade_margins(
    frame: WindowFrame,
    opaque_rect: tuple[float, float, float, float] | None,
) -> tuple[float, float, float, float]:
    """Trim a fading scroll area's margins to keep it on its backing.

    Returns ``frame.margins`` (left, right, bottom, top) cut back so the
    scroll area stays within ``opaque_rect`` (left, bottom, right, top:
    the backing's known-opaque rect, from
    :meth:`bauiv1.Widget.get_backing_opaque_rect`); its corners would
    otherwise poke out past the backing's rounded ones. Margins only
    ever shrink (never below zero), so content stays put. With no
    known rect, no margins.
    """
    if opaque_rect is None:
        return (0.0, 0.0, 0.0, 0.0)
    oleft, obottom, oright, otop = opaque_rect
    mleft, mright, mbottom, mtop = frame.margins
    scroll_right = frame.scroll_left + frame.scroll_width
    scroll_top = frame.scroll_bottom + frame.scroll_height
    return (
        max(0.0, min(mleft, frame.scroll_left - oleft)),
        max(0.0, min(mright, oright - scroll_right)),
        max(0.0, min(mbottom, frame.scroll_bottom - obottom)),
        max(0.0, min(mtop, otop - scroll_top)),
    )


def fade_scroll_lengths(
    layout: dui2.WindowLayout,
) -> tuple[float, float, float, float]:
    """How far a fade-style scroll area's fades reach in from its edges.

    Returns (left, right, bottom, top), at medium/large ui-scale. Free to
    differ from :func:`fade_scroll_extents` (a longer fade reaches past
    where an outline would clip, into content's space): the top one
    runs long, as content passing up behind the title otherwise muddles
    it.
    """
    left, right, bottom, top = fade_scroll_extents(layout)
    # A viewer layout's scroll area doesn't reach left (its viewer pane
    # is there), but sideways-scrolling rows still pass under that edge;
    # fade them within the empty strip before its content instead of
    # cutting them off hard.
    if left == 0.0 and layout in (
        dui2.WindowLayout.VIEWER,
        dui2.WindowLayout.VIEWER_NARROW,
    ):
        left = _FADE_EXTENT * _VIEWER_LEFT_FADE_SCALE
    return left, right, bottom, 2.0 * top


@dataclass
class WindowFrame:
    """Where a doc-ui window's parts sit (see :func:`window_frame`).

    All in window units. The scroll rect is where an outline-style
    scroll area sits; ``margins`` (left, right, bottom, top) is how far
    the actual scroll area reaches past it, with content inset to match
    (screen margins at small ui-scale, fade extents otherwise).
    """

    width: float
    height: float
    root_scale: float
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
    viewer_width: float


def window_frame(
    layout: dui2.WindowLayout,
    uiscale: bui.UIScale,
    scroll_edge_style: dui2.ScrollEdgeStyle,
) -> WindowFrame:
    """Lay out a doc-ui window's backing, visible area and scroll area."""
    small = uiscale is bui.UIScale.SMALL
    screensize = bui.get_virtual_screen_size()
    width, height, rscale = layout_geometry(layout, uiscale, screensize)

    # Our visible area is limited by the screen size in small mode and
    # our backing size otherwise.
    side_insets, vertical_insets = window_insets(layout)
    vis_width = min(width - side_insets, screensize[0] / rscale)
    vis_height = min(height - vertical_insets, screensize[1] / rscale)

    # At medium/large scale, then grow the backing (only) around that,
    # uniformly so its shape -- and thus which backing art it gets --
    # is unchanged; without this our scroll area and buttons (the
    # back button especially) creep out toward its visible edges.
    # Everything else is laid out relative to the visible area, which
    # stays centered. (Small ui-scale windows fill the screen, so
    # there is no edge to keep clear of.)
    backing_pad = 1.0 if small else 1.02
    width *= backing_pad
    height *= backing_pad

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

    # Nudge our vis area up a bit when we can see the full backing
    # (visual fudge factor).
    if not small:
        vis_top += 12.0

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
        mleft, mright, mbottom, mtop = fade_scroll_extents(layout)
    else:
        mleft = mright = mbottom = mtop = 0.0

    # Narrow where content is laid out, if our layout calls for it.
    col_inset = column_inset(layout, uiscale, scroll_width)

    # A viewer pane takes the left of our scroll area (the page
    # scrolls in what remains), so our scroll-widget stops at the
    # pane instead of extending into the screen margin. Unlike
    # scrolling content, the viewer's content doesn't move, so it
    # stays within the virtual bounds (none of it may be cut off by
    # the screen edge) and, in small ui, clear of the toolbars.
    viewer_width = viewer_pane_width(layout, scroll_width)
    if viewer_width > 0.0:
        scroll_left += viewer_width
        scroll_width -= viewer_width
        mleft = 0.0

    return WindowFrame(
        width=width,
        height=height,
        root_scale=rscale,
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
        viewer_width=viewer_width,
    )


def viewer_pane_width(layout: dui2.WindowLayout, scroll_width: float) -> float:
    """Width taken from the left of the scroll area for a viewer pane.

    Zero for layouts without one. A viewer layout keeps a small layout's
    column width for the page itself (at the right) and gives the rest
    to the viewer, which doesn't scroll with the page.
    """
    match layout:
        case dui2.WindowLayout.VIEWER:
            return max(0.0, scroll_width - SMALL_COLUMN_MAX_WIDTH)
        case dui2.WindowLayout.VIEWER_NARROW:
            # A narrower column; the viewer gets the rest.
            return max(
                0.0,
                scroll_width
                - _VIEWER_NARROW_COLUMN_FRACTION * SMALL_COLUMN_MAX_WIDTH,
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
