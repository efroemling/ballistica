# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui slider rows: a float value on a slider.

Split out of :mod:`bauiv1lib.docui.prep._controlrows` for size; it is
the same kind of thing as the rows there (label at the left, control
at the right, value in the page's state).
"""

import weakref
from functools import partial
from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui.prep._rowtext import control_width, label_want_width
from bauiv1lib.docui.prep._types import SliderPrep

if TYPE_CHECKING:
    from typing import Any, Callable

    import bacommon.docui.v2 as dui2
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import RowPrep

SLIDER_HEIGHT = 50.0

# A slider row's slider sits at the row's right with its value
# readout just left of it; the label (at the row's left, like other
# control rows') shares the row with those as control_width() decides,
# after a fixed gap. The slider + readout would like this share of the
# row, their slider no wider than _SLIDER_MAX_WANT (so a wide row
# doesn't get a needlessly long slider), and in any case at least
# _SLIDER_MIN_FRACTION of the row for the slider alone.
_SLIDER_CONTROL_FRACTION = 0.6
_SLIDER_MAX_WANT = 320.0
_SLIDER_MIN_FRACTION = 1.0 / 3.0
_SLIDER_WIDGET_HEIGHT = 28.0
_SLIDER_VALUE_GAP = 14.0
_SLIDER_VALUE_WIDTH = 60.0
_SLIDER_LABEL_GAP = 32.0


def slider_row_height(row: dui2.SliderRow) -> float:
    """Full height of a slider row."""
    return row.padding_top + row.padding_bottom + SLIDER_HEIGHT


def prep_slider_row(
    row: dui2.SliderRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    idprefix: str,
    tdelay: float | None,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> None:
    """Fill out prep for a slider row.

    ``left``/``right`` are where our label should start and our slider
    should end (before any padding the row asks for).
    """
    left += row.padding_left
    right -= row.padding_right
    bottom += row.padding_bottom
    center_y = bottom + SLIDER_HEIGHT * 0.5

    # The control is readout + gap + slider.
    readout = _SLIDER_VALUE_WIDTH + _SLIDER_VALUE_GAP
    label = None if row.label is None else native(row.label)
    gap = 0.0 if label is None else _SLIDER_LABEL_GAP
    rowwidth = right - left
    cwidth = control_width(
        rowwidth - gap,
        label_want=label_want_width(label),
        control_want=max(
            readout + rowwidth * _SLIDER_MIN_FRACTION,
            min(
                rowwidth * _SLIDER_CONTROL_FRACTION,
                readout + _SLIDER_MAX_WANT,
            ),
        ),
    )
    swidth = max(1.0, cwidth - readout)
    sleft = right - swidth
    valueright = sleft - _SLIDER_VALUE_GAP
    labelright = valueright - _SLIDER_VALUE_WIDTH - gap

    # A disabled row dims all three of its widgets (the textwidgets'
    # enabled=False is purely a dimming here; they aren't selectable).
    enabled = not row.disabled

    labelcall: Callable[..., bui.Widget] | None = None
    if label is not None:
        labelcall = partial(
            bui.textwidget,
            position=(left, center_y),
            size=(0, 0),
            text=label,
            literal=True,
            maxwidth=max(1.0, labelright - left),
            h_align='left',
            v_align='center',
            color=(0.75, 1.0, 0.7, 1.0),
            enabled=enabled,
            transition_delay=tdelay,
            transition_type='scale',
        )

    # See prep_checkbox_row() for why ids look like this.
    widgetid = f'{idprefix}|input.{row.name}'
    rowprep.slider = SliderPrep(
        labelcall=labelcall,
        valuecall=partial(
            bui.textwidget,
            position=(valueright, center_y),
            size=(0, 0),
            editable=False,
            maxwidth=_SLIDER_VALUE_WIDTH,
            h_align='right',
            v_align='center',
            color=(0.3, 1.0, 0.3, 1.0),
            enabled=enabled,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        slidercall=partial(
            bui.sliderwidget,
            id=widgetid,
            position=(sleft, center_y - _SLIDER_WIDGET_HEIGHT * 0.5),
            size=(swidth, _SLIDER_WIDGET_HEIGHT),
            min_value=row.min_value,
            max_value=row.max_value,
            increment=row.increment,
            enabled=enabled,
            autoselect=True,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        key=row.name,
        on_change=row.on_change,
        on_drag=row.on_drag,
        drag_interval=row.drag_interval,
        drag_delay=row.drag_delay,
        as_percent=row.as_percent,
        decimals=row.decimals,
        min_value=row.min_value,
        max_value=row.max_value,
        increment=row.increment,
        widgetid=widgetid,
        slider_center=(sleft + swidth * 0.5, center_y),
    )


class _SliderRowDriver:
    """Runs a slider row's callbacks with ConfigSlider's cadence.

    Every step updates the readout and the page's state (cheap; keeps
    a press elsewhere sending the latest). ``on_drag`` runs at most
    every ``drag_interval`` seconds and not before ``drag_delay`` into
    a drag, on the trailing edge (a value arriving mid-interval is
    applied when the interval ends rather than dropped), and never
    twice for the same value. A settled value skips the delay, runs a
    last ``on_drag`` if the drag's applies missed it, then fires
    ``on_change``.
    """

    def __init__(
        self,
        window: DocUIWindow,
        prep: SliderPrep,
        valuetext: bui.Widget,
        value: float,
    ) -> None:
        self._window = weakref.ref(window)
        self._prep = prep
        self._valuetext = valuetext
        self._value = value
        self._last_applied = value
        self._next_apply_time = 0.0
        self._apply_timer: bui.AppTimer | None = None
        self._pending: str | None = None
        self.show(value)

    def show(self, value: float) -> None:
        """Update the readout for a value."""
        prep = self._prep
        if prep.as_percent:
            text = f'{round(value * 100.0)}%'
        else:
            text = f'{value:.{prep.decimals}f}'
        if self._valuetext:
            bui.textwidget(edit=self._valuetext, text=text)

    def _snap(self, value: float) -> float:
        """The widget value in the form state holds (bui.snap_slider_value)."""
        prep = self._prep
        return bui.snap_slider_value(
            value,
            min_value=prep.min_value,
            max_value=prep.max_value,
            increment=prep.increment,
        )

    def dragged(self, value: float) -> None:
        """The slider's on_drag_call."""
        self._value = self._snap(value)
        self.show(self._value)
        self._store()
        self._schedule('drag')

    def changed(self, value: float) -> None:
        """The slider's on_change_call (a settled value)."""
        self._value = self._snap(value)
        self.show(self._value)
        self._store()
        self._schedule('settled')

    def _store(self) -> None:
        window = self._window()
        if window is not None:
            window.set_page_state_values(
                {self._prep.key: self._value}, push=False
            )

    def _schedule(self, action: str) -> None:
        # A later action supersedes a pending earlier one.
        self._pending = action
        now = bui.apptime()
        due = self._next_apply_time
        if action == 'drag':
            due = max(due, now + self._prep.drag_delay)
        if now >= due:
            self._run_pending()
        elif self._apply_timer is None:
            self._apply_timer = bui.AppTimer(
                due - now, bui.WeakCallStrict(self._run_pending)
            )

    def _run_pending(self) -> None:
        self._apply_timer = None
        action, self._pending = self._pending, None
        window = self._window()
        if window is None or action is None:
            return
        prep = self._prep
        # Acts on the *current* value; a later drag supersedes an
        # earlier pending one with no bookkeeping.
        if self._value != self._last_applied:
            self._next_apply_time = bui.apptime() + prep.drag_interval
            self._last_applied = self._value
            if prep.on_drag is not None:
                window.controller.run_input_local_action(
                    window, prep.widgetid, prep.key, prep.on_drag
                )
        if action == 'settled':
            window.controller.input_changed(
                window, prep.widgetid, prep.key, self._value, prep.on_change
            )


def instantiate_slider_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widgets for a prepped slider row.

    Returns the slider (the part that can be selected).
    """
    prep = rowprep.slider
    assert prep is not None

    if prep.labelcall is not None:
        prep.labelcall(parent=parent)

    # (See instantiate_checkbox_row() for why values are fetched here.)
    raw = (window.page_state or {}).get(prep.key)
    value = (
        min(prep.max_value, max(prep.min_value, float(raw)))
        if isinstance(raw, (int, float)) and not isinstance(raw, bool)
        else prep.min_value
    )

    valuetext = prep.valuecall(parent=parent, text='')
    driver = _SliderRowDriver(window, prep, valuetext, value)
    slider = prep.slidercall(
        parent=parent,
        value=value,
        on_drag_call=driver.dragged,
        on_change_call=driver.changed,
    )

    def _push(newvalue: Any) -> None:
        if (
            slider
            and isinstance(newvalue, (int, float))
            and not isinstance(newvalue, bool)
        ):
            bui.sliderwidget(edit=slider, value=float(newvalue))
            driver.show(float(newvalue))

    window.pagestate.register_pusher(prep.key, _push)
    window.register_spinner_position(slider, prep.slider_center)
    return slider
