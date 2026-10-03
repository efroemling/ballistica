# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui button control rows: a label and a single button.

Split out of :mod:`bauiv1lib.docui.prep._controlrows` for size. These
are laid out like the rows there (label at the left, control at the
right) but hold no value; the control is whatever button the page
asks for, at whatever size.
"""

from functools import partial
from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui.prep._types import ButtonControlPrep
from bauiv1lib.docui.prep._button import (
    button_padded_size,
    prep_button,
    instantiate_button,
)
from bauiv1lib.docui.prep._rowtext import (
    titles_clear_rise,
    footnote_clear_drop,
)

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from typing import Callable

    import bacommon.docui.v2 as dui2
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import RowPrep

# A button control row is never shorter than the other control rows,
# so a small button's row lines up with its neighbors.
_BUTTON_CONTROL_MIN_HEIGHT = 50.0

# Space between the label and the button (plus any padding the button
# asks for on its left).
_BUTTON_CONTROL_LABEL_GAP = 30.0

# How far the button keeps from title, subtitle or footnote text that
# runs over or under it, whatever its height (as a choice row's popup
# button does; see _controlrows._CHOICE_TEXT_CLEARANCE). Text that stops
# short of the button is no obstacle; the button sits beside it.
_BUTTON_CONTROL_TEXT_CLEARANCE = 6.0


def _control_height(row: dui2.ButtonControlRow) -> float:
    """Height of the row's control area: what its button needs."""
    return max(_BUTTON_CONTROL_MIN_HEIGHT, button_padded_size(row.button)[1])


def button_control_row_height(row: dui2.ButtonControlRow) -> float:
    """Full height of a button control row."""
    return row.padding_top + row.padding_bottom + _control_height(row)


def _button_bounds(
    row: dui2.ButtonControlRow, *, right: float, bottom: float
) -> tuple[float, float, float, float]:
    """The button's (left, bottom, right, top) in its row.

    ``right`` is where the row's control should end and ``bottom`` its
    control area's bottom, both before any padding the row asks for.
    The button and its padding sit at the right, centered vertically.
    """
    button = row.button
    bscale = button.scale
    paddedwidth, paddedheight = button_padded_size(button)
    paddedright = right - row.padding_right
    paddedbottom = (
        bottom
        + row.padding_bottom
        + (_control_height(row) - paddedheight) * 0.5
    )
    return (
        paddedright - paddedwidth + button.padding_left * bscale,
        paddedbottom + button.padding_bottom * bscale,
        paddedright - button.padding_right * bscale,
        paddedbottom + paddedheight - button.padding_top * bscale,
    )


def button_control_row_tucks(
    row: dui2.ButtonControlRow,
    titles_tuck: float,
    footnote_tuck: float,
    *,
    left: float,
    right: float,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> tuple[float, float]:
    """Limit a button control row's tucks to what its button allows.

    The tucks passed in bring the row's titles and footnote as close
    to its label as they are in any control row (see
    :func:`~bauiv1lib.docui.prep._controlrows.control_row_tucks`). A
    button taller than the label would then run into them, so they
    are pulled in only as far as leaves the button clear: beside
    whatever text stops short of it and outside of what does not, and
    in any case within the row. ``left``/``right`` are as for
    :func:`prep_button_control_row`. Measures text, so call from a
    background thread (as prep runs).

    :meta private:
    """
    height = button_control_row_height(row)
    bleft, bbottom, _bright, btop = _button_bounds(row, right=right, bottom=0.0)
    titles_limit = (height - btop) + titles_clear_rise(
        row,
        left=left,
        limit=bleft,
        clearance=_BUTTON_CONTROL_TEXT_CLEARANCE,
        native=native,
    )
    footnote_limit = bbottom + footnote_clear_drop(
        row,
        left=left,
        limit=bleft,
        clearance=_BUTTON_CONTROL_TEXT_CLEARANCE,
        native=native,
    )
    return (
        max(0.0, min(titles_tuck, titles_limit)),
        max(0.0, min(footnote_tuck, footnote_limit)),
    )


def prep_button_control_row(
    row: dui2.ButtonControlRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    widgetid: str,
    tdelay: float | None,
    packages: list[ApverNum],
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> None:
    """Fill out prep for a button control row.

    ``left``/``right`` are where our label should start and our button
    should end (before any padding the row asks for).

    :meta private:
    """
    button = row.button
    bleft, bbottom, _bright, _btop = _button_bounds(
        row, right=right, bottom=bottom
    )
    left += row.padding_left
    center_y = bottom + row.padding_bottom + _control_height(row) * 0.5

    labelcall: Callable[..., bui.Widget] | None = None
    if row.label is not None:
        # The label gets whatever the button leaves, squished to fit.
        labelright = (
            bleft
            - button.padding_left * button.scale
            - _BUTTON_CONTROL_LABEL_GAP
        )
        labelcall = partial(
            bui.textwidget,
            position=(left, center_y),
            size=(0, 0),
            text=native(row.label),
            literal=True,
            maxwidth=max(1.0, labelright - left),
            h_align='left',
            v_align='center',
            color=(0.75, 1.0, 0.7, 1.0),
            # (A disabled row dims its label.)
            enabled=not row.disabled,
            transition_delay=tdelay,
            transition_type='scale',
        )

    rowprep.buttoncontrol = ButtonControlPrep(
        labelcall=labelcall,
        button=prep_button(
            button,
            position=(bleft, bbottom),
            widgetid=widgetid,
            tdelay=tdelay,
            packages=packages,
            native=native,
            # (We don't scroll sideways.)
            show_buffers_h=None,
            disabled=row.disabled or button.disabled,
        ),
    )


def instantiate_button_control_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widgets for a prepped button control row.

    Returns the button (the part that can be selected).

    :meta private:
    """
    prep = rowprep.buttoncontrol
    assert prep is not None

    if prep.labelcall is not None:
        prep.labelcall(parent=parent)
    return instantiate_button(prep.button, parent=parent, window=window)
