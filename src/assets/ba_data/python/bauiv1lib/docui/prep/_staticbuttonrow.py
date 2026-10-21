# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui button rows that don't scroll sideways.

That's ``FIXED`` rows (buttons at their own sizes, shrinking together
if they don't fit), ``FILL`` rows (buttons sharing the width control
rows' contents span) and ``GRID`` rows (equal cells wrapping onto as
many lines as it takes, across that same width). Their buttons sit
straight on the page, laid out in the column the way control rows'
contents are, so unlike a scrolling row's nothing about them is
clipped.
"""

import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2

from bauiv1lib.docui._layout import BUTTON_ROW_EDGE_INSET
from bauiv1lib.docui.prep._button import (
    button_size,
    button_padded_size,
    prep_button,
    instantiate_button,
)

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum
    import bauiv1 as bui

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import (
        ButtonPrep,
        NativeLangStrFn,
        RowPrep,
    )


def row_content_align(row: dui2.ButtonRow) -> dui2.HAlign:
    """A button row's content alignment.

    Explicit alignment wins over the older center flag.

    :meta private:
    """
    if row.content_align is not None:
        return row.content_align
    return dui2.HAlign.CENTER if row.center_content else dui2.HAlign.LEFT


def column_row_edges(
    row: dui2.Row,
    *,
    control: tuple[float, float],
    column: tuple[float, float],
) -> tuple[float, float]:
    """The (left, right) a control row lays out between.

    Most span control rows' contents (``control``); a fixed button
    row's padding is from where a scrolling row's starts instead, inset
    from the ``column`` (so switching between the two leaves its
    buttons where they were). A row's height and its layout must both
    use these, since a row shrunk to fit is shorter.

    :meta private:
    """
    if (
        isinstance(row, dui2.ButtonRow)
        and row.layout is dui2.ButtonRowLayout.FIXED
    ):
        return (
            column[0] + BUTTON_ROW_EDGE_INSET,
            column[1] - BUTTON_ROW_EDGE_INSET,
        )
    return control


def is_static_button_row(row: dui2.Row) -> bool:
    """Is this a button row that doesn't scroll sideways?

    :meta private:
    """
    return (
        isinstance(row, dui2.ButtonRow)
        and row.layout is not dui2.ButtonRowLayout.SCROLL
    )


@dataclass
class _GridMetrics:
    """How a grid row's cells come out at a given width."""

    columns: int
    lines: int
    #: Cell size and gaps, as laid out (shrunk if the grid had to be).
    cell_width: float
    cell_height: float
    column_gap: float
    line_gap: float
    #: How much the whole grid shrank to fit (1.0 for not at all).
    factor: float
    #: Cell size before any shrinking.
    natural_cell: tuple[float, float]

    @property
    def width(self) -> float:
        """The grid's full width."""
        return (
            self.columns * self.cell_width
            + max(0, self.columns - 1) * self.column_gap
        )

    @property
    def height(self) -> float:
        """The grid's full height."""
        return (
            self.lines * self.cell_height
            + max(0, self.lines - 1) * self.line_gap
        )


def _grid_metrics(row: dui2.ButtonRow, *, avail: float) -> _GridMetrics:
    """Lay out a grid row's cells in ``avail`` width (padding excluded)."""
    count = len(row.buttons)
    padded = [button_padded_size(b) for b in row.buttons]
    cell_w = (
        max((p[0] for p in padded), default=0.0)
        if row.grid_cell_width is None
        else row.grid_cell_width
    )
    cell_h = (
        max((p[1] for p in padded), default=0.0)
        if row.grid_cell_height is None
        else row.grid_cell_height
    )
    cell_w, cell_h = max(1.0, cell_w), max(1.0, cell_h)
    col_gap = max(0.0, row.button_spacing)
    line_gap = max(
        0.0,
        (
            row.button_spacing
            if row.grid_line_spacing is None
            else row.grid_line_spacing
        ),
    )
    avail = max(1.0, avail)
    if row.grid_columns is not None:
        columns = max(1, row.grid_columns)
    else:
        columns = max(1, math.floor((avail + col_gap) / (cell_w + col_gap)))
    # (No wider than it has buttons for; a short grid aligns as a
    # narrower block.)
    columns = max(1, min(columns, count))
    natural_width = columns * cell_w + (columns - 1) * col_gap
    factor = min(1.0, avail / natural_width)
    # Widen the gaps between columns toward spanning the width, by at
    # most the row's max spread each: the outer columns land on its
    # edges when that's enough, and fall short by the rest otherwise.
    # (Capping each gap rather than switching all-or-nothing keeps
    # spacing changing smoothly with the width. A shrunk grid already
    # spans it; a single column has no gaps.)
    widen = 0.0
    if row.grid_max_spread > 0.0 and factor == 1.0 and columns > 1:
        slack = avail - natural_width
        widen = min(max(0.0, slack) / (columns - 1), row.grid_max_spread)
    return _GridMetrics(
        columns=columns,
        lines=math.ceil(count / columns) if count else 0,
        cell_width=cell_w * factor,
        cell_height=cell_h * factor,
        column_gap=col_gap * factor + widen,
        line_gap=line_gap * factor,
        factor=factor,
        natural_cell=(cell_w, cell_h),
    )


def _padded_avail(row: dui2.ButtonRow, *, left: float, right: float) -> float:
    """The width a static row lays out in, given its unpadded edges."""
    padleft, padright, _padtop, _padbottom = row.get_padding()
    return (right - padright) - (left + padleft)


def _buttons_height(row: dui2.ButtonRow, *, left: float, right: float) -> float:
    """Height of the row's button area.

    Its tallest button's (padded, and shrunk as a fixed row's are to
    fit); a grid's is all its lines. ``left``/``right`` are as for
    :func:`prep_static_button_row`.
    """
    avail = _padded_avail(row, left=left, right=right)
    if row.layout is dui2.ButtonRowLayout.GRID:
        return _grid_metrics(row, avail=avail).height
    tallest = max((button_padded_size(b)[1] for b in row.buttons), default=0.0)
    if row.layout is dui2.ButtonRowLayout.FIXED:
        tallest *= _fixed_factor(row, avail=avail)
    return tallest


def _fixed_natural_width(row: dui2.ButtonRow) -> float:
    """A fixed row's buttons' full width, unshrunk."""
    natural = sum(button_padded_size(b)[0] for b in row.buttons)
    return natural + row.button_spacing * max(0, len(row.buttons) - 1)


def _fixed_factor(row: dui2.ButtonRow, *, avail: float) -> float:
    """How much a fixed row's buttons shrink to fit ``avail`` width."""
    return min(1.0, max(1.0, avail) / max(1.0, _fixed_natural_width(row)))


def static_button_row_height(
    row: dui2.ButtonRow, *, left: float, right: float
) -> float:
    """Full height of a static button row.

    ``left``/``right`` are as for :func:`prep_static_button_row` (a
    grid's height depends on how many columns fit).

    :meta private:
    """
    _left, _right, top, bottom = row.get_padding()
    return top + bottom + _buttons_height(row, left=left, right=right)


def _fixed_layout(
    row: dui2.ButtonRow, *, left: float, right: float, center_x: float
) -> list[tuple[dui2.Button, float]]:
    """A fixed row's buttons, as shown, with each one's left x.

    Buttons keep their own sizes, aligned in the row as its content
    alignment says (centered ones on ``center_x``, as centered titles
    are); if they don't fit, they (and the spacing between) all shrink
    together until they do. The row's ``content_offset`` then shifts
    them as a group, short of the row's edges.
    """
    avail = max(1.0, right - left)
    natural = _fixed_natural_width(row)
    factor = _fixed_factor(row, avail=avail)
    buttons = (
        row.buttons
        if factor == 1.0
        else [replace(b, scale=b.scale * factor) for b in row.buttons]
    )
    spacing = row.button_spacing * factor
    x = _group_left(
        row, used=natural * factor, left=left, avail=avail, center_x=center_x
    )
    out: list[tuple[dui2.Button, float]] = []
    for button in buttons:
        out.append((button, x + button.padding_left * button.scale))
        x += button_padded_size(button)[0] + spacing
    return out


def _group_left(
    row: dui2.ButtonRow,
    *,
    used: float,
    left: float,
    avail: float,
    center_x: float,
) -> float:
    """Left edge of a ``used``-wide group of buttons in a row.

    Aligned as the row's content alignment says (centered ones on
    ``center_x``, as centered titles are), then shifted by its
    ``content_offset``, never past the row's edges.
    """
    align = row_content_align(row)
    x: float
    match align:
        case dui2.HAlign.LEFT:
            x = left
        case dui2.HAlign.CENTER:
            x = max(left, min(center_x - used * 0.5, left + avail - used))
        case dui2.HAlign.RIGHT:
            x = left + avail - used
        case _:
            assert_never(align)
    # Shift the group as a whole, keeping it within the row.
    if row.content_offset:
        x = max(left, min(x + row.content_offset, left + avail - used))
    return x


def _grid_layout(
    row: dui2.ButtonRow,
    metrics: _GridMetrics,
    *,
    left: float,
    right: float,
    area_bottom: float,
    center_x: float,
) -> list[tuple[dui2.Button, float, float]]:
    """A grid row's buttons, as shown, with each one's (x, y).

    Buttons fill the grid line by line, left to right. Each sits
    centered in its cell, shrunk (keeping its shape) if it's bigger
    than the cell.
    """
    avail = max(1.0, right - left)
    x0 = _group_left(
        row, used=metrics.width, left=left, avail=avail, center_x=center_x
    )
    area_top = area_bottom + metrics.height
    natural_w, natural_h = metrics.natural_cell
    out: list[tuple[dui2.Button, float, float]] = []
    for i, button in enumerate(row.buttons):
        line, col = divmod(i, metrics.columns)
        cell_left = x0 + col * (metrics.cell_width + metrics.column_gap)
        cell_bottom = (
            area_top
            - metrics.cell_height
            - line * (metrics.cell_height + metrics.line_gap)
        )
        padw, padh = button_padded_size(button)
        fit = min(1.0, natural_w / max(1.0, padw), natural_h / max(1.0, padh))
        scale = fit * metrics.factor
        if scale != 1.0:
            button = replace(button, scale=button.scale * scale)
        padw, padh = padw * scale, padh * scale
        out.append(
            (
                button,
                cell_left
                + (metrics.cell_width - padw) * 0.5
                + button.padding_left * button.scale,
                cell_bottom
                + (metrics.cell_height - padh) * 0.5
                + button.padding_bottom * button.scale,
            )
        )
    return out


def _fill_layout(
    row: dui2.ButtonRow, *, left: float, right: float
) -> list[tuple[dui2.Button, float]]:
    """A fill row's buttons, as shown, with each one's left x.

    The buttons span the whole width, each taking a share in
    proportion to its own width (scaled).
    """
    weights = [max(0.0, button_size(b)[0] * b.scale) for b in row.buttons]
    total = sum(weights)
    count = len(row.buttons)
    if total <= 0.0:
        # (Zero-width buttons all round; just split evenly.)
        weights, total = [1.0] * count, float(count)
    room = max(0.0, right - left - row.button_spacing * max(0, count - 1))
    out: list[tuple[dui2.Button, float]] = []
    x = left
    for button, weight in zip(row.buttons, weights, strict=True):
        each = room * weight / total
        # Our width replaces the button's own (in its own units, so its
        # scale still applies to everything else about it).
        out.append(
            (
                replace(
                    button,
                    size=(
                        max(1.0, each / button.scale),
                        button_size(button)[1],
                    ),
                ),
                x,
            )
        )
        x += each + row.button_spacing
    return out


def prep_static_button_row(
    row: dui2.ButtonRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    center_x: float,
    widgetids: list[str],
    tdelay: float | None,
    packages: list[ApverNum],
    native: NativeLangStrFn,
) -> None:
    """Fill out prep for a static button row.

    ``left``/``right`` are the edges the row's padding is measured
    from: where a scrolling row's padding starts for a fixed row, where
    control rows' contents start/end for a fill row. ``center_x`` is
    where a centered fixed row's buttons center. ``widgetids`` gives
    each button's widget id, in order.

    :meta private:
    """
    assert len(widgetids) == len(row.buttons)
    area_height = _buttons_height(row, left=left, right=right)
    padleft, padright, _padtop, padbottom = row.get_padding()
    left += padleft
    right -= padright
    area_bottom = bottom + padbottom

    placed: list[tuple[dui2.Button, float, float]]
    match row.layout:
        case dui2.ButtonRowLayout.FIXED | dui2.ButtonRowLayout.FILL:
            # One line, each button centered vertically in it (a
            # shorter button beside a taller one sits midway), its
            # padding below it.
            placed = [
                (
                    button,
                    bx,
                    area_bottom
                    + (area_height - button_padded_size(button)[1]) * 0.5
                    + button.padding_bottom * button.scale,
                )
                for button, bx in (
                    _fixed_layout(
                        row, left=left, right=right, center_x=center_x
                    )
                    if row.layout is dui2.ButtonRowLayout.FIXED
                    else _fill_layout(row, left=left, right=right)
                )
            ]
        case dui2.ButtonRowLayout.GRID:
            metrics = _grid_metrics(row, avail=right - left)
            placed = _grid_layout(
                row,
                metrics,
                left=left,
                right=right,
                area_bottom=area_bottom,
                center_x=center_x,
            )
            rowprep.grid_columns = metrics.columns
            rowprep.grid_cell_height = metrics.cell_height
            rowprep.grid_line_gap = metrics.line_gap
        case dui2.ButtonRowLayout.SCROLL:
            raise RuntimeError('Expected a static button row.')
        case _:
            assert_never(row.layout)

    preps: list[ButtonPrep] = []
    for (button, bx, by), widgetid in zip(placed, widgetids, strict=True):
        preps.append(
            prep_button(
                button,
                position=(bx, by),
                widgetid=widgetid,
                tdelay=tdelay,
                packages=packages,
                native=native,
                # (We don't scroll sideways.)
                show_buffers_h=None,
                disabled=button.disabled,
            )
        )
    rowprep.staticbuttons = preps


def instantiate_static_button_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> list[bui.Widget]:
    """Create the widgets for a prepped static button row.

    Returns its buttons, left to right.

    :meta private:
    """
    assert rowprep.staticbuttons is not None
    return [
        instantiate_button(prep, parent=parent, window=window)
        for prep in rowprep.staticbuttons
    ]
