# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui number rows: a value with '-' and '+' buttons.

Split out of :mod:`bauiv1lib.docui.prep._controlrows` for size; it is
the same kind of thing as the rows there (label at the left, control
at the right, value in the page's state).
"""

import weakref
from functools import partial
from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui.prep._types import NumberPrep

if TYPE_CHECKING:
    from typing import Any, Callable

    import bacommon.docui.v2 as dui2

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import NativeLangStrFn, RowPrep

NUMBER_HEIGHT = 50.0

# A number row's '+' button sits at the row's right with the '-' left
# of it; the value readout sits left of those, and the label (at the
# row's left, like other control rows') gets what is left after a fixed
# gap. The gaps start from ConfigNumberEdit's (14 and 22 around
# 28-unit buttons) scaled to our button size, with the value held a
# little farther off so it reads as clearly its own thing, and the
# buttons pulled a bit closer together.
_NUMBER_BUTTON_SIZE = 40.0
_NUMBER_BUTTON_GAP = 25.0

# Scale of the buttons' '-' and '+' labels.
_NUMBER_BUTTON_TEXT_SCALE = 1.2
_NUMBER_VALUE_GAP = 26.0
_NUMBER_VALUE_WIDTH = 60.0
_NUMBER_LABEL_GAP = 32.0


def number_row_height(row: dui2.NumberRow) -> float:
    """Full height of a number row."""
    return row.padding_top + row.padding_bottom + NUMBER_HEIGHT


def prep_number_row(
    row: dui2.NumberRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    idprefix: str,
    tdelay: float | None,
    native: NativeLangStrFn,
) -> None:
    """Fill out prep for a number row.

    ``left``/``right`` are where our label should start and our '+'
    button should end (before any padding the row asks for).
    """
    left += row.padding_left
    right -= row.padding_right
    bottom += row.padding_bottom
    center_y = bottom + NUMBER_HEIGHT * 0.5

    plusleft = right - _NUMBER_BUTTON_SIZE
    minusleft = plusleft - _NUMBER_BUTTON_GAP - _NUMBER_BUTTON_SIZE
    valueright = minusleft - _NUMBER_VALUE_GAP
    labelright = valueright - _NUMBER_VALUE_WIDTH - _NUMBER_LABEL_GAP
    buttonbottom = center_y - _NUMBER_BUTTON_SIZE * 0.5

    # A disabled row dims its label and readout (their enabled=False is
    # purely a dimming here; they aren't selectable) and disables both
    # buttons (see _NumberRowDriver._update_buttons()).
    enabled = not row.disabled

    labelcall: Callable[..., bui.Widget] | None = None
    if row.label is not None:
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
            enabled=enabled,
            transition_delay=tdelay,
            transition_type='scale',
        )

    # Ids are stable and derived from our state key, so selection
    # survives the page being rebuilt around us (see
    # _controlrows.prep_checkbox_row()); each button gets its own.
    widgetid = f'{idprefix}|input.{row.name}'
    minus_widgetid = f'{widgetid}|minus'
    plus_widgetid = f'{widgetid}|plus'

    def _buttoncall(
        buttonid: str, buttonleft: float, label: str
    ) -> Callable[..., bui.Widget]:
        return partial(
            bui.buttonwidget,
            id=buttonid,
            position=(buttonleft, buttonbottom),
            size=(_NUMBER_BUTTON_SIZE, _NUMBER_BUTTON_SIZE),
            label=label,
            text_scale=_NUMBER_BUTTON_TEXT_SCALE,
            autoselect=True,
            # Holding a button keeps stepping, as ConfigNumberEdit's do.
            repeat=True,
            transition_delay=tdelay,
            transition_type='scale',
        )

    rowprep.number = NumberPrep(
        labelcall=labelcall,
        valuecall=partial(
            bui.textwidget,
            position=(valueright, center_y),
            size=(0, 0),
            editable=False,
            maxwidth=_NUMBER_VALUE_WIDTH,
            h_align='right',
            v_align='center',
            color=(0.3, 1.0, 0.3, 1.0),
            enabled=enabled,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        minuscall=_buttoncall(minus_widgetid, minusleft, '-'),
        pluscall=_buttoncall(plus_widgetid, plusleft, '+'),
        key=row.name,
        on_change=row.on_change,
        as_percent=row.as_percent,
        decimals=row.decimals,
        min_value=row.min_value,
        max_value=row.max_value,
        increment=row.increment,
        minus_widgetid=minus_widgetid,
        plus_widgetid=plus_widgetid,
        disabled=row.disabled,
    )


class _NumberRowDriver:
    """Holds a number row's value and runs its buttons.

    Each press (and each repeat of a held button) steps the value,
    updating the readout and the page's state locally. The row's
    on-change action fires once the press sequence is over (the
    button's actions-complete call), and only if the value moved --
    so a hold is one round trip, not one per step -- attributed to
    the button, so any busy-spinner lands on it.
    """

    def __init__(
        self,
        window: DocUIWindow,
        prep: NumberPrep,
        valuetext: bui.Widget,
        value: float,
    ) -> None:
        self._window = weakref.ref(window)
        self._prep = prep
        self._valuetext = valuetext
        self._minus: bui.Widget | None = None
        self._plus: bui.Widget | None = None
        self._value = value
        #: The value the row's on-change last went out with (or arrived
        #: with); a press sequence ending elsewhere fires it again.
        self._committed = value
        self.show(value)

    def set_buttons(self, minus: bui.Widget, plus: bui.Widget) -> None:
        """Hand us our buttons once they exist (we grey them at the ends)."""
        self._minus = minus
        self._plus = plus
        self._update_buttons()

    def show(self, value: float) -> None:
        """Update the readout (and the buttons' state) for a value."""
        prep = self._prep
        if prep.as_percent:
            text = f'{round(value * 100.0)}%'
        else:
            text = f'{value:.{prep.decimals}f}'
        if self._valuetext:
            bui.textwidget(edit=self._valuetext, text=text)
        self._update_buttons()

    def _update_buttons(self) -> None:
        # A button that can't step any further is disabled: greyed, and
        # a press gets an error sound rather than a no-op step. Disabled
        # buttons stay selectable, so navigation through the row is
        # unaffected, and one held into its limit just ends its press
        # there (see ButtonWidget::SetEnabled()). We compare against the
        # value the grid lands on at each end, so float fuzz can't leave
        # one lit. A disabled row disables both, whatever the value.
        prep = self._prep
        tolerance = prep.increment * 1e-3
        at_min = self._value <= prep.min_value + tolerance
        at_max = self._value >= prep.max_value - tolerance
        for button, disabled in (
            (self._minus, prep.disabled or at_min),
            (self._plus, prep.disabled or at_max),
        ):
            if button:
                bui.buttonwidget(edit=button, enabled=not disabled)

    def set(self, value: float) -> None:
        """Take on a value pushed from the page's state."""
        self._value = value
        self._committed = value
        self.show(value)

    def step(self, direction: int) -> None:
        """Step by one increment (``direction`` -1 or 1); local only."""
        prep = self._prep
        # Land exactly on the grid (and within range) rather than
        # accumulating float drift press after press.
        newvalue = bui.snap_slider_value(
            self._value + direction * prep.increment,
            min_value=prep.min_value,
            max_value=prep.max_value,
            increment=prep.increment,
        )
        if newvalue == self._value:
            return
        self._value = newvalue
        self.show(newvalue)
        window = self._window()
        if window is not None:
            window.set_page_state_values({prep.key: newvalue}, push=False)

    def commit(self, direction: int) -> None:
        """A button's press sequence ended; fire on-change if we moved."""
        if self._value == self._committed:
            return
        window = self._window()
        if window is None:
            return
        prep = self._prep
        self._committed = self._value
        window.controller.input_changed(
            window,
            prep.minus_widgetid if direction < 0 else prep.plus_widgetid,
            prep.key,
            self._value,
            prep.on_change,
        )


def instantiate_number_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> list[bui.Widget]:
    """Create the widgets for a prepped number row.

    Returns the '-' and '+' buttons (the parts that can be selected),
    in that order.
    """
    prep = rowprep.number
    assert prep is not None

    if prep.labelcall is not None:
        prep.labelcall(parent=parent)

    # (See _controlrows.instantiate_checkbox_row() for why values are
    # fetched here.)
    raw = (window.page_state or {}).get(prep.key)
    value = (
        min(prep.max_value, max(prep.min_value, float(raw)))
        if isinstance(raw, (int, float)) and not isinstance(raw, bool)
        else prep.min_value
    )

    valuetext = prep.valuecall(parent=parent, text='')
    driver = _NumberRowDriver(window, prep, valuetext, value)
    # Each activation (press or repeat) steps locally; the on-change
    # request goes out once when the press sequence is over.
    minus = prep.minuscall(
        parent=parent,
        on_activate_call=partial(driver.step, -1),
        on_actions_complete_call=partial(driver.commit, -1),
    )
    plus = prep.pluscall(
        parent=parent,
        on_activate_call=partial(driver.step, 1),
        on_actions_complete_call=partial(driver.commit, 1),
    )
    driver.set_buttons(minus, plus)

    # (State values are arbitrary json, hence the Any.)
    def _push(newvalue: Any) -> None:
        if (
            minus
            and isinstance(newvalue, (int, float))
            and not isinstance(newvalue, bool)
        ):
            driver.set(float(newvalue))

    window.pagestate.register_pusher(prep.key, _push)
    return [minus, plus]
