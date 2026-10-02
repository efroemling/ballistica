# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui button rows that don't scroll sideways.

That's ``FIXED`` rows (buttons at their own sizes, shrinking together
if they don't fit) and ``FILL`` rows (buttons sharing the width control
rows' contents span). Their buttons sit straight on the page, laid out
in the column the way control rows' contents are, so unlike a
scrolling row's nothing about them is clipped.
"""

from dataclasses import replace
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2

from bauiv1lib.docui.prep._button import (
    button_size,
    button_padded_size,
    prep_button,
    instantiate_button,
)

if TYPE_CHECKING:
    from typing import Callable

    from bacommon.assetpackage import ApverNum
    from bacommon.langstr import LangStrSpec
    import bauiv1 as bui

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import ButtonPrep, RowPrep


def row_content_align(row: dui2.ButtonRow) -> dui2.HAlign:
    """A button row's content alignment.

    Explicit alignment wins over the older center flag.

    :meta private:
    """
    if row.content_align is not None:
        return row.content_align
    return dui2.HAlign.CENTER if row.center_content else dui2.HAlign.LEFT


def is_static_button_row(row: dui2.Row) -> bool:
    """Is this a button row that doesn't scroll sideways?

    :meta private:
    """
    return (
        isinstance(row, dui2.ButtonRow)
        and row.layout is not dui2.ButtonRowLayout.SCROLL
    )


def _buttons_height(row: dui2.ButtonRow) -> float:
    """Height of the row's button area: its tallest button's (padded)."""
    return max((button_padded_size(b)[1] for b in row.buttons), default=0.0)


def static_button_row_height(row: dui2.ButtonRow) -> float:
    """Full height of a static button row.

    :meta private:
    """
    _left, _right, top, bottom = row.get_padding()
    return top + bottom + _buttons_height(row)


def _fixed_layout(
    row: dui2.ButtonRow, *, left: float, right: float, center_x: float
) -> list[tuple[dui2.Button, float]]:
    """A fixed row's buttons, as shown, with each one's left x.

    Buttons keep their own sizes, aligned in the row as its content
    alignment says (centered ones on ``center_x``, as centered titles
    are); if they don't fit, they (and the spacing between) all shrink
    together until they do.
    """
    avail = max(1.0, right - left)
    natural = sum(button_padded_size(b)[0] for b in row.buttons)
    natural += row.button_spacing * max(0, len(row.buttons) - 1)
    factor = min(1.0, avail / max(1.0, natural))
    buttons = (
        row.buttons
        if factor == 1.0
        else [replace(b, scale=b.scale * factor) for b in row.buttons]
    )
    spacing = row.button_spacing * factor
    used = natural * factor
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
    out: list[tuple[dui2.Button, float]] = []
    for button in buttons:
        out.append((button, x + button.padding_left * button.scale))
        x += button_padded_size(button)[0] + spacing
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
    native: Callable[[LangStrSpec | int], bui.LangStr],
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
    padleft, padright, _padtop, padbottom = row.get_padding()
    left += padleft
    right -= padright
    placed: list[tuple[dui2.Button, float]]
    match row.layout:
        case dui2.ButtonRowLayout.FIXED:
            placed = _fixed_layout(
                row, left=left, right=right, center_x=center_x
            )
        case dui2.ButtonRowLayout.FILL:
            placed = _fill_layout(row, left=left, right=right)
        case dui2.ButtonRowLayout.SCROLL:
            raise RuntimeError('Expected a static button row.')
        case _:
            assert_never(row.layout)

    area_bottom = bottom + padbottom
    area_height = _buttons_height(row)
    preps: list[ButtonPrep] = []
    for (button, bx), widgetid in zip(placed, widgetids, strict=True):
        # Centered vertically in the button area (a shorter button
        # beside a taller one sits midway), its padding below it.
        by = (
            area_bottom
            + (area_height - button_padded_size(button)[1]) * 0.5
            + button.padding_bottom * button.scale
        )
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
