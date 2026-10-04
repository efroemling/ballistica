# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui window layout geometry."""

from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
import bauiv1 as bui

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

#: How much of the screen's height a small-taller window's backing takes
#: at medium/large ui-scale (its height follows the screen; see
#: layout_geometry()). Roughly the share of the screen the window reads
#: as taking, as its art fills nearly all of its backing.
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

#: How far right a viewer pane is nudged at small ui-scale, so its gap
#: to the virtual bounds matches its gap to the page content (tuned by
#: eye; see DocUIWindow).
SMALL_UI_VIEWER_NUDGE_X = 20.0

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
        case dui2.WindowLayout.WIDE:
            # Their squat rounder backing otherwise reads top-heavy;
            # less half the extra backing height, which the visible
            # area (centered in the backing) would otherwise split
            # with the top, so all of it lands below (see
            # _WIDE_DESIGN_EXTRA_BOTTOM).
            return 12.0 - 0.5 * _WIDE_EXTRA_BOTTOM
        case dui2.WindowLayout.WIDER:
            # As wide (see _WIDER_DESIGN_EXTRA_BOTTOM).
            return 12.0 - 0.5 * _WIDER_EXTRA_BOTTOM
        case dui2.WindowLayout.LARGE | dui2.WindowLayout.VIEWER:
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
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.VIEWER
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
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.VIEWER
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
        case dui2.WindowLayout.VIEWER:
            # Its rounder backing wants a bit more room above and
            # below its content (see layout_geometry).
            return 150.0, 80.0 + 2.0 * _VIEWER_EXTRA_PAD_V
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
        ):
            return _SMALL_SIDE_INSETS, _SMALL_VERTICAL_INSETS
        case dui2.WindowLayout.WIDE:
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

#: Medium ui-scale's standard window height (the viewer layout uses it
#: at large too).
_MEDIUM_HEIGHT = 729.0


def window_scroll_overhang(layout: dui2.WindowLayout) -> float:
    """How much wider than the visible area the scroll area is.

    Both sides together, at medium/large ui-scale. The title and back
    button stay within the visible area; wide and wider layouts run
    their scroll area out past it, back toward the backing's edges, as
    their wide content is meant to show no scroll bounds anyway.
    """
    match layout:
        case dui2.WindowLayout.WIDE | dui2.WindowLayout.WIDER:
            return (
                _WIDE_DESIGN_SIDE_INSETS - _WIDE_DESIGN_SCROLL_SIDE_INSETS
            ) * _WIDE_UNIT_SCALE
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.LARGE
            | dui2.WindowLayout.VIEWER
        ):
            return 0.0
        case _:
            assert_never(layout)


def back_button_nudge_x(layout: dui2.WindowLayout) -> float:
    """How far right of a window's visible left edge its back button sits.

    (Medium/large ui-scale; small uses the system back button.) The
    viewer layout's window is squat enough to get the rounder backing,
    whose top-left corner curves in further than the button's usual
    spot.
    """
    match layout:
        case dui2.WindowLayout.VIEWER:
            return _VIEWER_BACK_NUDGE_X
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
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
    layout: dui2.WindowLayout, close_style: bool
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
            _BACK_BASE_OFFSET[0] + back_button_nudge_x(layout) - shift[0],
            _BACK_BASE_OFFSET[1] - shift[1],
        ),
    )


def show_scroll_border(layout: dui2.WindowLayout) -> bool:
    """Whether a layout's scroll area shows its border when scrollable.

    (It never does when its content fits.) The viewer layout never
    shows one: beside its framed viewer pane, a second outline just
    reads as clutter.
    """
    match layout:
        case dui2.WindowLayout.VIEWER:
            return False
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.LARGE
        ):
            return True
        case _:
            assert_never(layout)


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
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.LARGE
        ):
            return True
        case (
            dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.WIDE
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
    its content instead; see :func:`column_inset`). A small-taller
    window's height at medium/large ui-scale follows the screen's
    (``screen_size``, virtual units): a fixed share of it
    (:data:`SMALL_TALLER_SCREEN_HEIGHT_FRACTION`), so it makes use of
    tall screens; likewise a wider window's width
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
        case dui2.WindowLayout.VIEWER:
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
        case dui2.WindowLayout.SMALL:
            width, height = _SMALL_WIDTH, _SMALL_HEIGHT
        case dui2.WindowLayout.SMALL_TALL:
            width, height = _SMALL_WIDTH, _SMALL_TALL_HEIGHT
        case dui2.WindowLayout.SMALL_TALLER:
            # (Never squat enough to switch to the rounder backing.)
            width = _SMALL_WIDTH
            height = max(
                0.6 * width,
                SMALL_TALLER_SCREEN_HEIGHT_FRACTION * screen_size[1] / scale,
            )
        case dui2.WindowLayout.WIDE:
            width, height = _WIDE_WIDTH, _WIDE_HEIGHT
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
        case dui2.WindowLayout.WIDE:
            return max(0.0, 0.5 * (scroll_width - WIDE_PAGE_WIDTH))
        case (
            dui2.WindowLayout.LARGE
            | dui2.WindowLayout.VIEWER
            | dui2.WindowLayout.WIDER
        ):
            return 0.0
        case _:
            assert_never(layout)


def viewer_pane_width(layout: dui2.WindowLayout, scroll_width: float) -> float:
    """Width taken from the left of the scroll area for a viewer pane.

    Zero for layouts without one. A viewer layout keeps a small layout's
    column width for the page itself (at the right) and gives the rest
    to the viewer, which doesn't scroll with the page.
    """
    match layout:
        case dui2.WindowLayout.VIEWER:
            return max(0.0, scroll_width - SMALL_COLUMN_MAX_WIDTH)
        case (
            dui2.WindowLayout.LARGE
            | dui2.WindowLayout.SMALL
            | dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDER
        ):
            return 0.0
        case _:
            assert_never(layout)
