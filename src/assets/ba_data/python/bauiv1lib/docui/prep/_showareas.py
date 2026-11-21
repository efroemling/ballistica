# Released under the MIT License. See LICENSE for details.
#
"""What selecting a doc-ui row brings into view, and its debug rects.

Each selectable row keeps show-buffers above and below its selectable
part; selecting it scrolls that part plus those into view. They are
built from what the row must keep in view (its titles and footnote,
plus any section heading or note attached to it), the page's own
buffers (out to the inset rect, so the selection lands clear of
toolbars and fades) and a nudge toward the middle. While a row is
selected it shows the first: its must-show area. With selection
centering off (see
:func:`bauiv1lib.docui._debugdraw.selection_centering_disabled`), a
selection that has to scroll leaves that area exactly at the inset
rect's edge.
"""

import math
from functools import partial
from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui._debugdraw import (
    DebugDrawKind,
    selection_centering_disabled,
    wants_debug_draw,
)
from bauiv1lib.docui.prep._sections import MARKER_ENTRY_TYPES

if TYPE_CHECKING:
    from typing import Callable

    from bauiv1lib.docui.prep._sections import LayoutEntry
    from bauiv1lib.docui.prep._types import RowPrep

_COLOR = (0.2, 1.0, 0.45)


def _num(val: float) -> str:
    return f'{val:.4g}'


def _call_span(call: Callable[..., bui.Widget] | dict) -> tuple[float, float]:
    """The (bottom, top) a prepped widget call's widget will occupy.

    From its ``position``, ``size`` (or a popup menu's
    ``button_size``) and ``scale``; a dict is a call's kwargs.
    """
    if isinstance(call, dict):
        kwargs = call
    else:
        assert isinstance(call, partial)
        kwargs = call.keywords
    bottom = kwargs['position'][1]
    height = kwargs['size' if 'size' in kwargs else 'button_size'][1]
    return bottom, bottom + height * kwargs.get('scale', 1.0)


def control_spans(rowprep: RowPrep) -> list[tuple[float, float]]:
    """A prepped control row's selectable widgets' (bottom, top).

    In the order instantiation returns them (see
    ``RowPrep.control_spans``).

    :meta private:
    """
    # pylint: disable=too-many-return-statements
    if rowprep.number is not None:
        return [
            _call_span(rowprep.number.minuscall),
            _call_span(rowprep.number.pluscall),
        ]
    if rowprep.staticbuttons is not None:
        return [_call_span(b.buttoncall) for b in rowprep.staticbuttons]
    if rowprep.checkbox is not None:
        return [_call_span(rowprep.checkbox.call)]
    if rowprep.textinput is not None:
        return [_call_span(rowprep.textinput.boxcall)]
    if rowprep.choice is not None:
        return [_call_span(rowprep.choice.menu_kwargs)]
    if rowprep.color is not None:
        return [_call_span(rowprep.color.buttoncall)]
    if rowprep.buttoncontrol is not None:
        return [_call_span(rowprep.buttoncontrol.button.buttoncall)]
    assert rowprep.slider is not None
    return [_call_span(rowprep.slider.slidercall)]


def widget_show_buffers(
    part: tuple[float, float],
    span: tuple[float, float],
    buffers: tuple[float, float],
) -> tuple[float, float]:
    """A widget's (top, bottom) show-buffers, given its part's.

    ``buffers`` are figured from ``part`` (its (bottom, top)); the
    engine applies a widget's to its own bounds, ``span``, so they grow
    by however far it sits inside the part.

    :meta private:
    """
    return buffers[0] + part[1] - span[1], buffers[1] + span[0] - part[0]


def grid_line_part(rowprep: RowPrep, line: int) -> tuple[float, float]:
    """A grid row's line's (bottom, top): its cells' extent.

    :meta private:
    """
    cell, gap = rowprep.grid_cell_height, rowprep.grid_line_gap
    top = rowprep.grid_top - line * (cell + gap)
    return top - cell, top


def _nudged(
    content_height: float, top: float, bottom: float, scroll_height: float
) -> tuple[float, float]:
    """A selectable part's final (top, bottom) show-buffers.

    Nudges what gets kept on screen when it is selected toward the
    scroll area's full visible height, so navigating to a row also
    reveals some of what comes before and after it.
    """
    total_show_height = content_height + top + bottom

    # How much to push show-height towards full available space. 1.0
    # should lead to always perfect centering (but that might feel too
    # aggressive). (None at all with centering off, a debugging aid.)
    amt = 0.0 if selection_centering_disabled() else 0.5
    extra = max(0.0, (scroll_height - total_show_height) * 0.5 * amt)
    return top + extra, bottom + extra


def finalize_show_buffers(
    entries: list[LayoutEntry],
    rows: list[RowPrep],
    *,
    scroll_height: float,
    page: tuple[float, float],
    scrollbar_strip: float,
) -> None:
    """Finalize each selectable row's show-buffers, once all are known.

    Nudges each toward the scroll area's full visible height (see
    :func:`_nudged`; that height includes any margins, as the buffers
    do, so how far selections scroll doesn't depend on them), and
    hands button rows' to their h-scrolls (control rows' go straight
    onto their controls at instantiation). ``page`` is the page's
    (top, bottom) buffers, and ``scrollbar_strip`` how far a scrolling
    row's h-scroll reaches below it.

    :meta private:
    """
    for entry, rowprep in zip(entries, rows, strict=True):
        if rowprep.is_section:
            continue
        base = (rowprep.show_buffer_top, rowprep.show_buffer_bottom)
        if rowprep.grid_columns:
            # A grid's lines navigate like rows of their own: the top
            # line keeps what's above the row in view and the bottom
            # line what's below; lines between keep their gaps. (All
            # get the page's buffers, as every row does.)
            assert rowprep.staticbuttons is not None
            lines = math.ceil(len(rowprep.staticbuttons) / rowprep.grid_columns)
            gap = rowprep.grid_line_gap
            rowprep.grid_show_buffers = [
                _nudged(
                    rowprep.grid_cell_height,
                    base[0] if line == 0 else gap + page[0],
                    base[1] if line == lines - 1 else gap + page[1],
                    scroll_height,
                )
                for line in range(lines)
            ]
        rowprep.show_buffer_top, rowprep.show_buffer_bottom = _nudged(
            # (A scrolling row's h-scroll includes its bar's strip.)
            rowprep.height
            + (0.0 if rowprep.hscrollcall is None else scrollbar_strip),
            base[0],
            base[1],
            scroll_height,
        )
        assert not isinstance(entry, MARKER_ENTRY_TYPES)
        if wants_debug_draw(entry.debug, DebugDrawKind.SHOW_AREAS):
            prep_show_areas(rowprep, base=base, page=page)
        if not rowprep.is_control_row():
            rowprep.hscrolleditcall = partial(
                bui.widget,
                show_buffer_top=rowprep.show_buffer_top,
                show_buffer_bottom=rowprep.show_buffer_bottom,
            )


def prep_show_areas(
    rowprep: RowPrep,
    *,
    base: tuple[float, float],
    page: tuple[float, float],
) -> None:
    """Prep a selectable row's show-area debug rects.

    Once its show-buffers are final. ``base`` is its (top, bottom)
    buffers before the nudge, and ``page`` the page's (top, bottom)
    buffers, which they include. The rects are made at instantiation,
    one per selectable widget, each drawing only while its widget is
    selected (see ``RowPrep.show_area_calls``).

    :meta private:
    """
    left, right = rowprep.show_x

    def _rect(
        part: tuple[float, float],
        must: tuple[float, float],
        label: str,
    ) -> list[Callable[..., bui.Widget]]:
        """A selected widget's rect.

        ``part`` is the (bottom, top) its buffers extend from, and
        ``must`` how far (top, bottom) it must show beyond that.
        """
        must_bottom, must_top = part[0] - must[1], part[1] + must[0]
        return [
            partial(
                bui.debugrectwidget,
                position=(left, must_bottom),
                size=(right - left, must_top - must_bottom),
                color=_COLOR,
                opacity=0.8,
                edge_width=2.0,
                fill_opacity=0.08,
                info=label,
                info_anchor='top_right',
            )
        ]

    # (The page's buffers aside: every row has those.)
    must = (base[0] - page[0], base[1] - page[1])
    if not rowprep.grid_columns:
        bottom, top = rowprep.show_part
        # Labeled with how far it reaches past the row's own bounds (a
        # section heading or note attached to it, say).
        beyond_top = top + must[0] - rowprep.bounds_top
        beyond_bottom = rowprep.bounds_bottom - (bottom - must[1])
        label = (
            'show = row'
            if abs(beyond_top) < 0.05 and abs(beyond_bottom) < 0.05
            else f'show = row +t{_num(beyond_top)} +b{_num(beyond_bottom)}'
        )
        rowprep.show_area_calls = [_rect((bottom, top), must, label)]
        return

    # A grid's lines navigate (and scroll) like rows of their own: the
    # top line keeps what's above the row in view, the bottom line
    # what's below, and lines between their gaps.
    gap = rowprep.grid_line_gap
    lines = len(rowprep.grid_show_buffers)
    calls: list[list[Callable[..., bui.Widget]]] = []
    for line in range(lines):
        line_must = (
            must[0] if line == 0 else gap,
            must[1] if line == lines - 1 else gap,
        )
        calls.append(
            _rect(
                grid_line_part(rowprep, line),
                line_must,
                f'show = line {line + 1} +t{_num(line_must[0])}'
                f' +b{_num(line_must[1])}',
            )
        )
    rowprep.show_area_calls = calls
