# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui control rows.

Control rows hold a single control spanning the full row: a label at
the left edge and the control itself at the right. Most are input
rows, whose values live in the page's state (see
:attr:`bacommon.docui.v2.Page.state`); a button control row holds no
value.
"""

import weakref
from functools import partial
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.docui.prep._types import (
    CheckboxPrep,
    TextInputPrep,
    ChoicePrep,
    ColorPrep,
)
from bauiv1lib.docui.prep._rowtext import (
    control_width,
    control_row_footnote_tuck,
    control_row_titles_tuck,
    label_want_width,
    row_text_reaches,
)
from bauiv1lib.docui.prep._buttoncontrolrow import (
    button_control_row_height,
    button_control_row_tucks,
    prep_button_control_row,
    instantiate_button_control_row,
)
from bauiv1lib.docui.prep._staticbuttonrow import (
    is_static_button_row,
    static_button_row_height,
    prep_static_button_row,
    instantiate_static_button_row,
)
from bauiv1lib.docui.prep._numberrow import (
    number_row_height,
    prep_number_row,
    instantiate_number_row,
)
from bauiv1lib.docui.prep._sliderrow import (
    slider_row_height,
    prep_slider_row,
    instantiate_slider_row,
)

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from typing import Any, Callable, Sequence, TypeGuard

    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import RowPrep

CHECKBOX_HEIGHT = 50.0

# How far in from its right edge a 'right' style checkbox centers its
# box (the widget's box padding plus half its box size; see
# CheckBoxWidget).
_CHECKBOX_BOX_CENTER_INSET = 6.0 + 20.0 * 0.5


def checkbox_row_height(row: dui2.CheckboxRow) -> float:
    """Full height of a checkbox row."""
    return row.padding_top + row.padding_bottom + CHECKBOX_HEIGHT


def prep_checkbox_row(
    row: dui2.CheckboxRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    idprefix: str,
    tdelay: float | None,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> None:
    """Fill out prep for a checkbox row.

    ``left``/``right`` are where our label should start and our
    control should end (before any padding the row asks for).
    ``tdelay`` is when our widgets scale in (None to pop in instantly),
    as for every control row.
    """
    # Stable and derived from our state key, so selection survives
    # the page being rebuilt around us (an on-change action replacing
    # the page, say).
    widgetid = f'{idprefix}|input.{row.name}'
    boxright = right - row.padding_right
    boxbottom = bottom + row.padding_bottom
    rowprep.checkbox = CheckboxPrep(
        call=partial(
            bui.checkboxwidget,
            id=widgetid,
            position=(left + row.padding_left, boxbottom),
            size=(
                right - left - row.padding_left - row.padding_right,
                CHECKBOX_HEIGHT,
            ),
            text='' if row.label is None else native(row.label),
            style='right',
            autoselect=True,
            enabled=not row.disabled,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        key=row.name,
        on_change=row.on_change,
        widgetid=widgetid,
        box_center=(
            boxright - _CHECKBOX_BOX_CENTER_INSET,
            boxbottom + CHECKBOX_HEIGHT * 0.5,
        ),
    )


def instantiate_checkbox_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widget for a prepped checkbox row."""
    prep = rowprep.checkbox
    assert prep is not None

    # Values come from the window's live state at the last moment
    # rather than being baked in at prep time; an old page coming back
    # should show whatever edits were made to it.
    value = (window.page_state or {}).get(prep.key, False)
    widget = prep.call(
        parent=parent,
        value=value is True,
        on_value_change_call=partial(
            window.controller.input_changed,
            window,
            prep.widgetid,
            prep.key,
            on_change=prep.on_change,
        ),
    )

    # (State values are arbitrary json, hence the Any.)
    def _push(newvalue: Any) -> None:
        if widget:
            bui.checkboxwidget(edit=widget, value=newvalue is True)

    window.pagestate.register_pusher(prep.key, _push)

    # We span the whole row, so by default the busy-spinner for a
    # request we fire would land mid-row; put it over our box instead.
    window.register_spinner_position(widget, prep.box_center)
    return widget


TEXT_INPUT_HEIGHT = 50.0

# A text-input row's box is anchored at the right and would like this
# share of the row; a long label can take some of that back (see
# control_width()), squished to fit whatever it ends up with.
_TEXT_INPUT_BOX_WANT_FRACTION = 2.0 / 3.0

# Space between a control row's label and its control.
_TEXT_INPUT_LABEL_GAP = 30.0

_TEXT_INPUT_BOX_HEIGHT = 40.0


def text_input_row_height(row: dui2.TextInputRow) -> float:
    """Full height of a text-input row."""
    return row.padding_top + row.padding_bottom + TEXT_INPUT_HEIGHT


def prep_text_input_row(
    row: dui2.TextInputRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    idprefix: str,
    tdelay: float | None,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> None:
    """Fill out prep for a text-input row.

    ``left``/``right`` are where our label should start and our text
    box should end (before any padding the row asks for).
    """
    left += row.padding_left
    right -= row.padding_right
    bottom += row.padding_bottom
    center_y = bottom + TEXT_INPUT_HEIGHT * 0.5

    # Split the row between label and box (see control_width()); the
    # label is squished to fit its share. We are in a background thread
    # here, which is the right place to be measuring text.
    rowwidth = right - left
    label = None if row.label is None else native(row.label)
    gap = 0.0 if label is None else _TEXT_INPUT_LABEL_GAP
    boxwidth = control_width(
        rowwidth - gap,
        label_want=label_want_width(label),
        control_want=rowwidth * _TEXT_INPUT_BOX_WANT_FRACTION,
    )
    boxleft = right - boxwidth

    # A disabled row dims its label and box; the box stays selectable
    # but can't be edited.
    enabled = not row.disabled

    labelcall: Callable[..., bui.Widget] | None = None
    if label is not None:
        labelcall = partial(
            bui.textwidget,
            position=(left, center_y),
            size=(0, 0),
            text=label,
            literal=True,
            maxwidth=max(1.0, boxleft - gap - left),
            h_align='left',
            v_align='center',
            color=(0.75, 1.0, 0.7, 1.0),
            enabled=enabled,
            transition_delay=tdelay,
            transition_type='scale',
        )

    boxbottom = center_y - _TEXT_INPUT_BOX_HEIGHT * 0.5

    # See prep_checkbox_row() for why ids look like this.
    widgetid = f'{idprefix}|input.{row.name}'
    description = row.description if row.description is not None else row.label
    rowprep.textinput = TextInputPrep(
        labelcall=labelcall,
        boxcall=partial(
            bui.textwidget,
            id=widgetid,
            position=(boxleft, boxbottom),
            size=(right - boxleft, _TEXT_INPUT_BOX_HEIGHT),
            editable=True,
            max_chars=row.max_chars,
            description=None if description is None else native(description),
            h_align='left',
            v_align='center',
            padding=4,
            color=(0.9, 0.9, 0.9, 1.0),
            enabled=enabled,
            autoselect=True,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        key=row.name,
        on_change=row.on_change,
        on_submit=row.on_submit,
        widgetid=widgetid,
        box_center=((boxleft + right) * 0.5, center_y),
    )


def instantiate_text_input_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widgets for a prepped text-input row.

    Returns the text box (the part that can be selected).
    """
    prep = rowprep.textinput
    assert prep is not None

    if prep.labelcall is not None:
        prep.labelcall(parent=parent)

    # (See instantiate_checkbox_row() for why values are fetched here.)
    value = (window.page_state or {}).get(prep.key, '')
    widgets: list[bui.Widget] = []

    def _pull() -> str:
        # Falling back to empty if our widget has died; this should
        # only ever get called while our page is up though.
        if not widgets or not widgets[0]:
            return ''
        return str(bui.textwidget(query=widgets[0]))

    def _applied(newvalue: str) -> None:
        # An edit got applied (as opposed to merely being underway; we
        # don't hear about individual characters being typed and
        # wouldn't want to fire requests for them if we did). The value
        # comes bundled since this runs deferred.
        window.controller.input_changed(
            window, prep.widgetid, prep.key, newvalue, prep.on_change
        )

    # Submitting runs after the apply above (both are scheduled in
    # order), and the action's request pulls the box's current text
    # anyway, so it always sees the submitted value.
    submitkwds: dict[str, Any] = {}
    if prep.on_submit is not None:
        submitkwds['on_submit_call'] = partial(
            window.controller.run_action,
            window,
            prep.widgetid,
            prep.on_submit,
        )
    widget = prep.boxcall(
        parent=parent,
        text=value if isinstance(value, str) else '',
        on_apply_call=_applied,
        **submitkwds,
    )
    widgets.append(widget)

    # (State values are arbitrary json, hence the Any.)
    def _push(newvalue: Any) -> None:
        if widget:
            bui.textwidget(
                edit=widget,
                text=newvalue if isinstance(newvalue, str) else '',
            )

    window.pagestate.register_puller(prep.key, _pull)
    window.pagestate.register_pusher(prep.key, _push)
    window.register_spinner_position(widget, prep.box_center)
    return widget


CHOICE_HEIGHT = 50.0

# The popup-menu button in a choice row sits at the row's right and
# would like to fit its longest choice (plus this much padding); see
# control_width() for how it shares the row with a label.
# The padding covers the button's left-aligned label inset (20) plus
# its popup-accessory region (44); see ButtonWidget.
_CHOICE_BUTTON_HEIGHT = 46.0
_CHOICE_BUTTON_TEXT_PADDING = 64.0
_CHOICE_BUTTON_MIN_WIDTH = 120.0

#: Extra room between a choice row's popup button and a title/subtitle
#: above or footnote below it when that text reaches over the button
#: (see control_row_tucks()).
_CHOICE_TEXT_CLEARANCE = 6.0


def choice_row_height(row: dui2.ChoiceRow) -> float:
    """Full height of a choice row."""
    return row.padding_top + row.padding_bottom + CHOICE_HEIGHT


def _choice_button_left(
    row: dui2.ChoiceRow,
    *,
    left: float,
    right: float,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> float:
    """Where a choice row's popup button starts.

    ``left``/``right`` are as for :func:`prep_choice_row`. Measures
    text, so call from a background thread (as prep runs).
    """
    left += row.padding_left
    right -= row.padding_right

    # Size the button to its widest choice, within bounds.
    widest = max(
        (
            bui.get_string_width(
                native(c.label).evaluate(), suppress_warning=True
            )
            for c in row.choices
        ),
        default=0.0,
    )
    # Split the row between label and button (see control_width()).
    label = None if row.label is None else native(row.label)
    gap = 0.0 if label is None else _TEXT_INPUT_LABEL_GAP
    bwidth = max(
        _CHOICE_BUTTON_MIN_WIDTH,
        control_width(
            right - left - gap,
            label_want=label_want_width(label),
            control_want=widest + _CHOICE_BUTTON_TEXT_PADDING,
        ),
    )
    return right - bwidth


def prep_choice_row(
    row: dui2.ChoiceRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    idprefix: str,
    tdelay: float | None,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> None:
    """Fill out prep for a choice row.

    ``left``/``right`` are where our label should start and our button
    should end (before any padding the row asks for).
    """
    # (We are in a background thread here, which is the right place to
    # be measuring text.)
    bleft = _choice_button_left(row, left=left, right=right, native=native)
    left += row.padding_left
    right -= row.padding_right
    bottom += row.padding_bottom
    center_y = bottom + CHOICE_HEIGHT * 0.5
    label = None if row.label is None else native(row.label)
    choice_labels = [native(c.label) for c in row.choices]
    bwidth = right - bleft
    bheight = _CHOICE_BUTTON_HEIGHT

    labelcall: Callable[..., bui.Widget] | None = None
    if label is not None:
        labelcall = partial(
            bui.textwidget,
            position=(left, center_y),
            size=(0, 0),
            text=label,
            literal=True,
            maxwidth=max(1.0, bleft - _TEXT_INPUT_LABEL_GAP - left),
            h_align='left',
            v_align='center',
            color=(0.75, 1.0, 0.7, 1.0),
            # (A disabled row dims its label; see instantiate_choice_row()
            # for its button.)
            enabled=not row.disabled,
            transition_delay=tdelay,
            transition_type='scale',
        )

    # See prep_checkbox_row() for why ids look like this.
    widgetid = f'{idprefix}|input.{row.name}'
    rowprep.choice = ChoicePrep(
        labelcall=labelcall,
        menu_kwargs={
            'position': (bleft, center_y - bheight * 0.5),
            'button_size': (bwidth, bheight),
            'button_id': widgetid,
            'autoselect': True,
            'transition_delay': tdelay,
            'transition_type': 'scale',
            # Backing drawn to our bounds, like doc-ui button rows.
            'better_bg_fit': True,
        },
        choice_labels=choice_labels,
        choice_values=[c.value for c in row.choices],
        choice_disabled=[c.disabled for c in row.choices],
        key=row.name,
        on_change=row.on_change,
        widgetid=widgetid,
        button_center=(bleft + bwidth * 0.5, center_y),
        disabled=row.disabled,
    )


def instantiate_choice_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widgets for a prepped choice row.

    Returns the popup-menu's button (the part that can be selected).
    """
    from bauiv1lib.popup import PopupMenu

    prep = rowprep.choice
    assert prep is not None

    if prep.labelcall is not None:
        prep.labelcall(parent=parent)

    # PopupMenu keys its choices by string, and our values can be None
    # (an optional's 'nothing' choice), so we key the menu by index and
    # map through prep.choice_values in both directions.
    values = prep.choice_values
    keys = [str(i) for i in range(len(values))]

    def _key_for(value: Any) -> str | None:
        """Menu key for a state value, or None if it is not a choice."""
        # (State values are arbitrary json, hence the Any; None is a
        # legitimate value here, so no isinstance shortcut.)
        return keys[values.index(value)] if value in values else None

    # (See instantiate_checkbox_row() for why values are fetched here.)
    key = _key_for((window.page_state or {}).get(prep.key))
    if key is None:
        key = keys[0] if keys else ''

    # The menu holds this callback and our pusher (below) holds the
    # menu, so a strong window ref here would close a cycle through the
    # page state: window -> pagestate -> pusher -> menu -> here.
    windowref = weakref.ref(window)

    def _picked(newkey: str) -> None:
        # PopupMenu only reports user picks, never set_choice() calls,
        # so state pushes can't loop back through here.
        win = windowref()
        if win is None:
            return
        win.controller.input_changed(
            win, prep.widgetid, prep.key, values[int(newkey)], prep.on_change
        )

    menu = PopupMenu(
        parent,
        choices=keys,
        choices_display=prep.choice_labels,
        choices_disabled=[
            k for k, off in zip(keys, prep.choice_disabled, strict=True) if off
        ],
        current_choice=key,
        on_value_change_call=_picked,
        **prep.menu_kwargs,
    )
    button = menu.get_button()

    # A disabled row's button is a disabled button: greyed, still
    # selectable, and a press sounds an error rather than opening the
    # menu.
    if prep.disabled:
        bui.buttonwidget(edit=button, enabled=False)

    def _push(newvalue: Any) -> None:
        newkey = _key_for(newvalue)
        if button and newkey is not None:
            menu.set_choice(newkey)

    window.pagestate.register_pusher(prep.key, _push)
    window.register_spinner_position(button, prep.button_center)
    return button


COLOR_HEIGHT = 50.0

# The swatch button in a color row sits at the row's right.
_COLOR_SWATCH_SIZE = (70.0, 40.0)


def color_row_height(row: dui2.ColorRow) -> float:
    """Full height of a color row."""
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
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> None:
    """Fill out prep for a color row.

    ``left``/``right`` are where our label should start and our swatch
    should end (before any padding the row asks for).
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
            maxwidth=max(1.0, bleft - _TEXT_INPUT_LABEL_GAP - left),
            h_align='left',
            v_align='center',
            color=(0.75, 1.0, 0.7, 1.0),
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
        window: DocUIWindow,
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
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widgets for a prepped color row.

    Returns the swatch button (the part that can be selected).
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
        )

    bui.buttonwidget(edit=button, on_activate_call=_pick)

    def _push(newvalue: Any) -> None:
        newcolor = _as_color(newvalue)
        if button and newcolor is not None:
            bui.buttonwidget(edit=button, color=newcolor)

    window.pagestate.register_pusher(prep.key, _push)
    window.register_spinner_position(button, prep.button_center)
    return button


#: Rows laid out like control rows: the control rows themselves plus
#: button rows that don't scroll sideways (which put buttons where a
#: label and control go). Only those button rows; see
#: :func:`is_column_row`.
type ColumnRow = dui2.AnyControlRow | dui2.ButtonRow


def is_column_row(row: dui2.Row) -> TypeGuard[ColumnRow]:
    """Is this row laid out like a control row (:data:`ColumnRow`)?

    (Not a TypeIs: a button row that isn't one is still a button row.)
    """
    return dui2.is_control_row(row) or is_static_button_row(row)


def control_row_height(row: ColumnRow) -> float:
    """Full height of a control row of whatever sort."""
    height: float
    if isinstance(row, dui2.ButtonRow):
        height = static_button_row_height(row)
    elif isinstance(row, dui2.CheckboxRow):
        height = checkbox_row_height(row)
    elif isinstance(row, dui2.TextInputRow):
        height = text_input_row_height(row)
    elif isinstance(row, dui2.ChoiceRow):
        height = choice_row_height(row)
    elif isinstance(row, dui2.ColorRow):
        height = color_row_height(row)
    elif isinstance(row, dui2.NumberRow):
        height = number_row_height(row)
    elif isinstance(row, dui2.ButtonControlRow):
        height = button_control_row_height(row)
    else:
        height = slider_row_height(row)
    return height


def control_row_tucks(
    row: ColumnRow,
    *,
    left: float,
    right: float,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> tuple[float, float]:
    """How far a control row's control and footnote pull together.

    Returns (control up into the title strips, footnote up toward the
    control); see :func:`control_row_titles_tuck` and
    :func:`control_row_footnote_tuck`. Every control row's label is
    centered in its control area, between its paddings.
    ``left``/``right`` are as for :func:`prep_control_row`. Measures
    text, so call from a background thread (as prep runs).
    """
    # A static button row's buttons can sit anywhere along it, so no
    # text gets to tuck in beside them; its titles and footnote keep
    # their full strips (as a scrolling row's do).
    if isinstance(row, dui2.ButtonRow):
        return 0.0, 0.0
    height = control_row_height(row)
    half = 0.5 * (height - row.padding_top - row.padding_bottom)
    titles_tuck = control_row_titles_tuck(row, row.padding_top + half)
    footnote_tuck = control_row_footnote_tuck(row, row.padding_bottom + half)

    # A popup button fills nearly its whole control area; text reaching
    # over or under it (rather than just the label) gets a bit more
    # room.
    if isinstance(row, dui2.ChoiceRow):
        bleft = _choice_button_left(row, left=left, right=right, native=native)
        # The line nearest the button above is the subtitle's, else the
        # title's.
        above, above_scale = (
            (row.title, 1.0) if row.subtitle is None else (row.subtitle, 0.7)
        )
        if row_text_reaches(
            row, above, above_scale, left=left, limit=bleft, native=native
        ):
            titles_tuck = max(0.0, titles_tuck - _CHOICE_TEXT_CLEARANCE)
        if row_text_reaches(
            row, row.footnote, 0.7, left=left, limit=bleft, native=native
        ):
            footnote_tuck = max(0.0, footnote_tuck - _CHOICE_TEXT_CLEARANCE)

    # A button can be any size, so how far it can pull toward the text
    # around it depends on how big it is and where that text is.
    elif isinstance(row, dui2.ButtonControlRow):
        titles_tuck, footnote_tuck = button_control_row_tucks(
            row,
            titles_tuck,
            footnote_tuck,
            left=left,
            right=right,
            native=native,
        )
    return titles_tuck, footnote_tuck


def prep_control_row(
    row: ColumnRow,
    rowprep: RowPrep,
    *,
    left: float,
    right: float,
    bottom: float,
    center_x: float,
    idprefix: str,
    tdelay: float | None,
    native: Callable[[LangStrSpec | int], bui.LangStr],
    packages: list[ApverNum],
    buttonids: list[str] | None,
) -> None:
    """Fill out prep for a control row of whatever sort.

    ``left``/``right`` are where the row's label should start and its
    control should end (before any padding the row asks for).
    ``tdelay`` is when the row's widgets scale in; None pops them in
    instantly (immediate mode). ``buttonids`` are the widget ids for a
    button control row's button or a static button row's buttons
    (only); such
    ids come from the page, where the rest of its buttons get theirs.
    ``center_x`` is where centered content centers (for a static button
    row's buttons).
    """
    if isinstance(row, dui2.ButtonRow):
        assert buttonids is not None
        prep_static_button_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            center_x=center_x,
            widgetids=buttonids,
            tdelay=tdelay,
            packages=packages,
            native=native,
        )
    elif isinstance(row, dui2.ButtonControlRow):
        assert buttonids is not None and len(buttonids) == 1
        buttonid = buttonids[0]
        prep_button_control_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            widgetid=buttonid,
            tdelay=tdelay,
            packages=packages,
            native=native,
        )
    elif isinstance(row, dui2.CheckboxRow):
        prep_checkbox_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            idprefix=idprefix,
            tdelay=tdelay,
            native=native,
        )
    elif isinstance(row, dui2.TextInputRow):
        prep_text_input_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            idprefix=idprefix,
            tdelay=tdelay,
            native=native,
        )
    elif isinstance(row, dui2.ChoiceRow):
        prep_choice_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            idprefix=idprefix,
            tdelay=tdelay,
            native=native,
        )
    elif isinstance(row, dui2.ColorRow):
        prep_color_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            idprefix=idprefix,
            tdelay=tdelay,
            native=native,
        )
    elif isinstance(row, dui2.NumberRow):
        prep_number_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            idprefix=idprefix,
            tdelay=tdelay,
            native=native,
        )
    else:
        prep_slider_row(
            row,
            rowprep,
            left=left,
            right=right,
            bottom=bottom,
            idprefix=idprefix,
            tdelay=tdelay,
            native=native,
        )


def instantiate_control_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIWindow
) -> list[bui.Widget]:
    """Create widgets for a prepped control row of whatever sort.

    Returns the row's selectable widgets, left to right: its lone
    control for most rows, the '-' and '+' buttons for a number row,
    every button for a static button row.
    """
    # A number row has two selectable widgets and a static button row
    # as many as it has buttons; the rest have one.
    if rowprep.number is not None:
        return instantiate_number_row(rowprep, parent=parent, window=window)
    if rowprep.staticbuttons is not None:
        return instantiate_static_button_row(
            rowprep, parent=parent, window=window
        )

    control: bui.Widget
    if rowprep.checkbox is not None:
        control = instantiate_checkbox_row(
            rowprep, parent=parent, window=window
        )
    elif rowprep.textinput is not None:
        control = instantiate_text_input_row(
            rowprep, parent=parent, window=window
        )
    elif rowprep.choice is not None:
        control = instantiate_choice_row(rowprep, parent=parent, window=window)
    elif rowprep.color is not None:
        control = instantiate_color_row(rowprep, parent=parent, window=window)
    elif rowprep.buttoncontrol is not None:
        control = instantiate_button_control_row(
            rowprep, parent=parent, window=window
        )
    else:
        assert rowprep.slider is not None
        control = instantiate_slider_row(rowprep, parent=parent, window=window)
    return [control]
