# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui window layout geometry."""

from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Literal

# Layouts promise their pages content rects of at least the sizes in
# bacommon (dui2.SMALL_CONTENT_WIDTH and friends); the geometry here is
# built from those, and checked against them where screens decide (see
# WIDE_VISIBLE_HEIGHT).

#: Height a window's title band takes off the top of its scroll area at
#: medium/large ui-scale (see DocUIWindow).
TITLE_BAND_HEIGHT = 43.0

# A note on sizes: a layout's size here (see layout_geometry()) is its
# window's *nominal* size, from which its visible area is inset (see
# window_insets()) and around whose center everything is placed. These
# were once the window backing's own size, and are tuned as such; the
# backing art is now fit to the window's content instead (see
# _frame.window_frames()), so they no longer set where the art goes.

#: A small layout's insets from its nominal size to its visible area at
#: medium/large ui-scale (see window_insets()); tighter than the
#: standard ones.
_SMALL_SIDE_INSETS = 100.0
_SMALL_VERTICAL_INSETS = 66.0

#: A small layout's nominal size at medium/large ui-scale: just what
#: gives its pages their promised content rect (the small-ui column's
#: width, so content lays out exactly as in that column).
_SMALL_WIDTH = dui2.SMALL_CONTENT_WIDTH + _SMALL_SIDE_INSETS
_SMALL_HEIGHT = (
    dui2.SMALL_CONTENT_HEIGHT + _SMALL_VERTICAL_INSETS + TITLE_BAND_HEIGHT
)

#: A small-tall layout's height at every medium/large ui-scale: just
#: what gives its pages their promised content height there (see
#: :data:`bacommon.docui.v2.TALL_CONTENT_HEIGHT`; it fits medium's
#: screen, so like the other layouts it is the same window at both, just
#: scaled differently). (Once tuned as midway between a small layout's
#: height and a small-taller's at large ui-scale.) Taller windows grow
#: from it with the screen's height (see layout_geometry()).
_SMALL_TALL_HEIGHT = (
    dui2.TALL_CONTENT_HEIGHT + _SMALL_VERTICAL_INSETS + TITLE_BAND_HEIGHT
)

#: How much of each extra unit of screen height a small-taller (or
#: wide-taller) window grows by at medium/large ui-scale (its height
#: follows the screen; see _taller_height()).
SMALL_TALLER_SCREEN_HEIGHT_FRACTION = 0.8

#: How much of the screen's height and width a large window takes at
#: medium/large ui-scale (its size follows the screen; see
#: layout_geometry()); on wide screens its height limits its width.
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

#: How far a doc-ui popup window's fading scroll area reaches out past
#: its content area at top and bottom (the popup grows to cover it, as
#: windows do; see fade_scroll_extents()). Shorter than windows', as
#: popups are small.
POPUP_FADE_REACH = 20.0

#: Where a doc-ui popup window's close button sits in from its left
#: edge (its title band's left end).
POPUP_CLOSE_BUTTON_INSET = 4.0

#: Height of a doc-ui popup window's title band (title and close
#: button), above its content area.
POPUP_TITLE_BAND_HEIGHT = 50.0

#: How far (virtual-screen units; horizontal, vertical) a doc-ui
#: popup's bounds always stay in from the virtual screen's edges. A hard
#: limit: popups are sized and placed within it (see ``popup_frame()``
#: and the popup window's placement), so none sits partly off screen
#: and there's always somewhere outside one to press to dismiss it.
POPUP_EDGE_MARGIN = (100.0, 100.0)

#: The longest a doc-ui scroll area's edge fades ever run: what its
#: frame asks for on each side that fades (see ``WindowFrame``'s
#: ``fade_lengths``). Generous on purpose; each is shortened (its whole
#: ramp squeezed, never cut off) to end by the line where the page's
#: resting content starts (see ``edge_fades()``), so in practice the
#: page's insets and the frame's extends decide. Turn it down only if
#: some fade is seen to look too long.
DEFAULT_EDGE_FADE = 120.0

#: A doc-ui popup window's close button: (scale, size), sitting in its
#: title band's left end. A clean-layout button, so this is its art's
#: size; it matches windows' close buttons.
POPUP_CLOSE_BUTTON = (0.88, (64.0, 55.0))

#: How much taller than the visible area a small-ui scroll area is (it
#: runs full-screen; see DocUIWindow).
SMALL_UI_SCROLL_EXTRA = 1.0

#: Clearance page content gets above and below at small ui-scale, where
#: the scroll area runs under the toolbars (see page prep).
SMALL_UI_TOOLBAR_CLEARANCE = 70.0

#: How far (virtual units) a viewer pane's outer edge stays in from
#: the virtual screen bounds at small ui-scale (where it otherwise
#: meets them).
VIEWER_SCREEN_BUFFER = 25.0


#: Where a button row's side padding starts in from the column's edges;
#: its default padding takes its buttons on to the page's h_inset.
#: (The room between is inside its h-scroll, so button art reaching
#: past its bounds isn't clipped.)
BUTTON_ROW_EDGE_INSET = 18.0

#: Content-rect height wide and wider layouts give their pages, at
#: every ui-scale (see :data:`bacommon.docui.v2.WIDE_CONTENT_HEIGHT`).
WIDE_CONTENT_HEIGHT = dui2.WIDE_CONTENT_HEIGHT

#: Content-rect width wide layouts give their pages, at every ui-scale
#: (see :data:`bacommon.docui.v2.WIDE_CONTENT_WIDTH`).
WIDE_CONTENT_WIDTH = dui2.WIDE_CONTENT_WIDTH

# At small ui-scale windows fill the screen, so the wide promises hold
# there only because the narrowest and shortest screens give exactly
# them (the height less toolbar clearance, plus the scroll extra);
# change any of these numbers and the promises must change too.
assert (
    abs(MIN_VIRTUAL_SCREEN_WIDTH / SMALL_UI_ROOT_SCALE - WIDE_CONTENT_WIDTH)
    < 0.001
)
assert (
    abs(
        MIN_VIRTUAL_SCREEN_HEIGHT / SMALL_UI_ROOT_SCALE
        + SMALL_UI_SCROLL_EXTRA
        - 2.0 * SMALL_UI_TOOLBAR_CLEARANCE
        - WIDE_CONTENT_HEIGHT
    )
    < 0.001
)

#: Wide and wider layouts' visible height at medium/large ui-scale:
#: whatever gives their pages exactly the content height they get at
#: small ui-scale on the shortest screen, so a page that fits one fits
#: all. (The medium/large one pays the title band.)
WIDE_VISIBLE_HEIGHT = WIDE_CONTENT_HEIGHT + TITLE_BAND_HEIGHT

#: Wide and wider layouts' designed shape at medium/large ui-scale: a
#: shared nominal height (loosely after the classic play window, then
#: tuned by eye) and insets (see window_insets()) a bit roomier than a
#: small layout's, plus scroll-area side insets well outside the
#: visible area, as their wide content is meant to show no scroll
#: bounds (see window_scroll_overhang()). These set the shape
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

#: Wide's nominal width comes from WIDE_CONTENT_WIDTH; wider's follows the
#: screen (see WIDER_SCREEN_WIDTH_FRACTION), as its content is expected
#: to overflow the screen anyway, so showing more of it at medium/large
#: means less scrolling (at small ui-scale the two are the same, filling
#: the screen).
_WIDE_DESIGN_WIDTH = (
    WIDE_CONTENT_WIDTH / _WIDE_UNIT_SCALE + _WIDE_DESIGN_SCROLL_SIDE_INSETS
)

#: Extra a wider window gets at medium/large beyond the above, at each
#: side and at the bottom, with its insets grown to match. (Back when
#: these sized its backing, they gave its long scrolling rows more
#: around them.) The sides narrow its visible area, as its width follows
#: the screen regardless; the bottom only moves its content down a bit
#: (see window_content_drop()).
_WIDER_DESIGN_EXTRA_SIDE = 50.0
_WIDER_DESIGN_EXTRA_BOTTOM = 40.0

#: The same below a wide window: only moves its content down a bit (see
#: window_content_drop()).
_WIDE_DESIGN_EXTRA_BOTTOM = 28.0

_WIDE_BASE_HEIGHT = _WIDE_DESIGN_HEIGHT * _WIDE_UNIT_SCALE
_WIDE_EXTRA_BOTTOM = _WIDE_DESIGN_EXTRA_BOTTOM * _WIDE_UNIT_SCALE
_WIDE_WIDTH = _WIDE_DESIGN_WIDTH * _WIDE_UNIT_SCALE
_WIDE_HEIGHT = _WIDE_BASE_HEIGHT + _WIDE_EXTRA_BOTTOM
_WIDE_SIDE_INSETS = _WIDE_DESIGN_SIDE_INSETS * _WIDE_UNIT_SCALE
_WIDE_VERTICAL_INSETS = _WIDE_DESIGN_VERTICAL_INSETS * _WIDE_UNIT_SCALE
_WIDER_EXTRA_SIDE = _WIDER_DESIGN_EXTRA_SIDE * _WIDE_UNIT_SCALE
_WIDER_EXTRA_BOTTOM = _WIDER_DESIGN_EXTRA_BOTTOM * _WIDE_UNIT_SCALE
_WIDER_HEIGHT = _WIDE_BASE_HEIGHT + _WIDER_EXTRA_BOTTOM

#: A wide-tall window's nominal height (medium/large ui-scale): a wide
#: window's, grown so its pages get the same promised content height
#: as a small-tall window's (its insets and everything else stay
#: wide's).
_WIDE_TALL_HEIGHT = _WIDE_HEIGHT + (
    dui2.TALL_CONTENT_HEIGHT - WIDE_CONTENT_HEIGHT
)

#: How much of the screen's width a wider window takes at
#: medium/large ui-scale (its width follows the screen; see
#: layout_geometry()): its long scrolling rows show as much at once as
#: the screen allows. All the extra goes to its visible and scroll
#: areas.
WIDER_SCREEN_WIDTH_FRACTION = 0.85


def window_content_drop(layout: dui2.WindowLayout) -> float:
    """How far below center a window's visible area sits (medium/large).

    Moves the title, back button and scroll area down together on
    screen. (Tuned back when it set where content sat in the window's
    backing; the backing now fits content wherever it sits.)
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
            # Less half the extra height below (see
            # _WIDE_DESIGN_EXTRA_BOTTOM), which the visible area
            # (centered) would otherwise split with the top.
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


def window_backing_art(
    layout: dui2.WindowLayout, uiscale: bui.UIScale
) -> Literal['tall', 'squat']:
    """Which window backing art a layout's window draws.

    (See :func:`bauiv1.containerwidget`'s ``background_art``.) Picked
    per layout rather than left to the container: content-sized windows
    can be shaped unlike the art they were designed around. Squat
    layouts get the rounder art; small ui-scale windows fill the screen
    and get the boxier one.
    """
    if uiscale is bui.UIScale.SMALL:
        return 'tall'
    match layout:
        case (
            dui2.WindowLayout.SMALL
            | dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDER
            | dui2.WindowLayout.VIEWER
        ):
            return 'squat'
        case (
            dui2.WindowLayout.SMALL_TALL
            | dui2.WindowLayout.SMALL_TALLER
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
            | dui2.WindowLayout.LARGE
            | dui2.WindowLayout.VIEWER_NARROW
        ):
            return 'tall'
        case _:
            assert_never(layout)


def window_insets(layout: dui2.WindowLayout) -> tuple[float, float]:
    """How much smaller a window's visible area is than its nominal size.

    Returns (both sides together, top and bottom together) at
    medium/large ui-scale (at small ui-scale the screen limits the
    visible area instead).
    """
    match layout:
        case dui2.WindowLayout.VIEWER | dui2.WindowLayout.VIEWER_NARROW:
            # A bit more above and below its content (see
            # layout_geometry).
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
                _WIDE_SIDE_INSETS,
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


#: Extra room above and below the viewer layout's content (each), and
#: how much of that comes from making its window taller (the rest comes
#: out of its scroll area and viewer).
_VIEWER_EXTRA_PAD_V = 20.0
_VIEWER_EXTRA_HEIGHT = 20.0

#: A narrow viewer layout's window width (medium/large ui-scale) as a
#: share of a viewer layout's. (Its column is
#: :data:`bacommon.docui.v2.NARROW_CONTENT_WIDTH`.)
_VIEWER_NARROW_WIDTH_SCALE = 0.9

#: Medium ui-scale's standard window height (the viewer layout uses it
#: at large too).
_MEDIUM_HEIGHT = 729.0


def window_scroll_overhang(layout: dui2.WindowLayout) -> float:
    """How much wider than the visible area the scroll area is.

    Both sides together, at medium/large ui-scale. The title and back
    button stay within the visible area; wide and wider layouts run
    their scroll area out past it, toward the window's edges, as their
    wide content is meant to show no scroll bounds anyway. A
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
#: (near bacommon.docui.v2.DEFAULT_H_INSET): what a large layout's
#: scroll area overhangs its visible area by on each side (see
#: window_scroll_overhang()) and a fading small layout's back button is
#: nudged in by (see _backbutton.back_button_nudge_x()), so content and
#: back button line up either way.
CONTENT_INDENT = 30.0
_LARGE_SCROLL_OVERHANG_SIDE = CONTENT_INDENT


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
    """A layout's nominal (width, height) and root scale at a ui-scale.

    (Nominal: see the note on sizes at the top of this module.) Medium's
    and large's large widths are as wide as their heights allow while
    staying a bit over 0.6x as tall as wide (a shape once tied to which
    backing art containers drew); small is sized to the small-ui column
    (see _SMALL_WIDTH); wide and wider are fixed shapes, their window
    units scaled so their pages get the same height at every ui-scale
    (see WIDE_VISIBLE_HEIGHT). At
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
            # Follows the screen both ways, but never squatter than
            # this (on wide screens its height limits its width).
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
            width = pane_height + dui2.SMALL_CONTENT_WIDTH + side_insets
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
            # (Never narrower than this.)
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
    """A '-taller' window's nominal height (medium/large ui-scale).

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
    same with a column of its content width (WIDE_CONTENT_WIDTH): it's
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
            return max(0.0, 0.5 * (scroll_width - dui2.SMALL_CONTENT_WIDTH))
        case (
            dui2.WindowLayout.WIDE
            | dui2.WindowLayout.WIDE_TALL
            | dui2.WindowLayout.WIDE_TALLER
        ):
            return max(0.0, 0.5 * (scroll_width - WIDE_CONTENT_WIDTH))
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


def fade_scroll_extents() -> tuple[float, float, float, float]:
    """How far a fade-style scroll area reaches past an outline one's.

    Returns (left, right, bottom, top), at medium/large ui-scale. With no
    outline to look cramped against the window's edges, the scroll area
    reaches out toward the top and bottom (up behind the title); content
    gets inset by the same amounts, so it keeps exactly the space and
    spot it would have with an outline, and fades only once scrolled
    past where an outline would have clipped it. The sides don't reach
    out (a viewer pane's edge couldn't, and both sides match): their
    fades stay within the empty strip before content (the page's
    horizontal inset).

    The same in every layout; a window's backing art is fit around the
    result (see ``_frame.window_frames()``).
    """
    return (0.0, 0.0, _FADE_EXTENT, _FADE_EXTENT)


#: See fade_scroll_extents().
_FADE_EXTENT = 40.0
