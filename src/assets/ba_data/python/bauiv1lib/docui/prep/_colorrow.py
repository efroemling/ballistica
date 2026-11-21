# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui color rows: a label and a color swatch to pick with."""

import weakref
from functools import partial
from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui._layout import popup_scale
from bauiv1lib.docui.prep._rowtext import control_label_style
from bauiv1lib.docui.prep._types import ColorPrep

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence

    import bacommon.docui.v2 as dui2

    from bauiv1lib.docui._host import DocUIPageHost
    from bauiv1lib.docui.prep._types import NativeLangStrFn, RowPrep

COLOR_HEIGHT = 50.0

# The swatch button in a color row sits at the row's right (a
# clean-layout button, so this is its art's size; as wide as the
# profile editor's 80-unit buttons around it).
_COLOR_SWATCH_SIZE = (80.0, 44.0)

# Space between the label and the swatch (as for a text input's box).
_COLOR_LABEL_GAP = 30.0


def color_row_height(row: dui2.ColorRow) -> float:
    """Full height of a color row.

    :meta private:
    """
    return row.padding_top + row.padding_bottom + COLOR_HEIGHT


def prep_color_row(
    row: dui2.ColorRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    idprefix: str,
    tdelay: float | None,
    native: NativeLangStrFn,
) -> None:
    """Fill out prep for a color row.

    ``left``/``right`` are where our label should start and our swatch
    should end (before any padding the row asks for).

    :meta private:
    """
    left += row.padding_left
    right -= row.padding_right
    bottom += row.padding_bottom
    center_y = bottom + COLOR_HEIGHT * 0.5
    bwidth, bheight = _COLOR_SWATCH_SIZE
    bleft = right - bwidth

    labelcall: Callable[..., bui.Widget] | None = None
    if row.label is not None:
        labelcall = partial(
            bui.textwidget,
            position=(left, center_y),
            size=(0, 0),
            text=native(row.label),
            literal=True,
            maxwidth=max(1.0, bleft - _COLOR_LABEL_GAP - left),
            h_align='left',
            v_align='center',
            **control_label_style(row),
            enabled=not row.disabled,
            transition_delay=tdelay,
            transition_type='scale',
        )

    # See prep_checkbox_row() for why ids look like this.
    widgetid = f'{idprefix}|input.{row.name}'
    rowprep.color = ColorPrep(
        labelcall=labelcall,
        buttoncall=partial(
            bui.buttonwidget,
            id=widgetid,
            position=(bleft, center_y - bheight * 0.5),
            size=(bwidth, bheight),
            button_type='square',
            label='',
            # (A disabled swatch goes grey like any disabled button.)
            enabled=not row.disabled,
            autoselect=True,
            clean_layout=True,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        key=row.name,
        on_change=row.on_change,
        widgetid=widgetid,
        button_center=(bleft + bwidth * 0.5, center_y),
    )


def _as_color(value: Any) -> tuple[float, float, float] | None:
    """A state value as an rgb tuple, if it is one."""
    if (
        isinstance(value, (list, tuple))
        and len(value) == 3
        and all(isinstance(v, (int, float)) for v in value)
    ):
        return (float(value[0]), float(value[1]), float(value[2]))
    return None


class _ColorRowPicker:
    """Delegate for a color row's picker popup.

    Records each color the picker reports into the page's state right
    away (so a press elsewhere sends the latest), but only fires the
    row's on-change action once, when the picker closes with a color
    different from the one it opened on; the exact-color picker streams
    intermediate values that nobody wants a request per.
    """

    def __init__(
        self,
        window: DocUIPageHost,
        prep: ColorPrep,
        button: bui.Widget,
        initial: tuple[float, float, float],
    ) -> None:
        self._window = weakref.ref(window)
        self._prep = prep
        self._button = button
        self._initial = initial
        self._color = initial

    def color_picker_selected_color(
        self, picker: Any, color: Sequence[float]
    ) -> None:
        """Called by the picker for each color it lands on."""
        del picker  # Unused.
        window = self._window()
        if window is None:
            return
        self._color = (color[0], color[1], color[2])
        if self._button:
            bui.buttonwidget(edit=self._button, color=self._color)
        window.set_page_state_values(
            {self._prep.key: list(self._color)}, push=False
        )

    def color_picker_closing(self, picker: Any) -> None:
        """Called by the picker as it goes away."""
        del picker  # Unused.
        window = self._window()
        if window is None:
            return
        # Take the global selection back from the picker *before* firing
        # our change: that may re-request the page, which saves the
        # window's selection first, and main-windows save the global
        # selection (see MainWindow.main_window_save_shared_state()) --
        # otherwise that'd be one of the picker's (id-less) swatches.
        if self._button:
            self._button.global_select()
        if self._color != self._initial:
            window.controller.input_changed(
                window,
                self._prep.widgetid,
                self._prep.key,
                list(self._color),
                self._prep.on_change,
            )


def instantiate_color_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIPageHost
) -> bui.Widget:
    """Create the widgets for a prepped color row.

    Returns the swatch button (the part that can be selected).

    :meta private:
    """
    prep = rowprep.color
    assert prep is not None

    if prep.labelcall is not None:
        prep.labelcall(parent=parent)

    # (See instantiate_checkbox_row() for why values are fetched here.)
    color = _as_color((window.page_state or {}).get(prep.key)) or (
        1.0,
        1.0,
        1.0,
    )

    button = prep.buttoncall(parent=parent, color=color)

    def _pick() -> None:
        from bauiv1lib.colorpicker import ColorPicker

        if not button:
            return
        current = _as_color((window.page_state or {}).get(prep.key)) or color
        ColorPicker(
            parent=parent,
            position=button.get_screen_space_center(),
            initial_color=current,
            delegate=_ColorRowPicker(window, prep, button, current),
            # (In proportion with doc-ui windows, like our other popups.)
            scale=popup_scale(),
        )

    bui.buttonwidget(edit=button, on_activate_call=_pick)

    def _push(newvalue: Any) -> None:
        newcolor = _as_color(newvalue)
        if button and newcolor is not None:
            bui.buttonwidget(edit=button, color=newcolor)

    window.pagestate.register_pusher(prep.key, _push)
    window.register_spinner_position(button, prep.button_center)
    return button
