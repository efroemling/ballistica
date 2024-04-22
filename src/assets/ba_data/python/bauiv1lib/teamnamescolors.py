# Released under the MIT License. See LICENSE for details.
#
"""Provides a window to customize team names and colors."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

from bauiv1lib.popup import PopupWindow
from bauiv1lib.colorpicker import ColorPicker
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Sequence


class TeamNamesColorsWindow(PopupWindow):
    """A popup window for customizing team names and colors."""

    def __init__(self, scale_origin: tuple[float, float]):
        from bascenev1 import DEFAULT_TEAM_COLORS, DEFAULT_TEAM_NAMES

        self._width = 500
        self._height = 330
        self._transitioning_out = False
        self._max_name_length = 16

        # Creates our _root_widget.
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        scale = (
            1.69
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.85
        )
        super().__init__(
            position=scale_origin, size=(self._width, self._height), scale=scale
        )

        appconfig = bui.app.config
        self._names = list(
            appconfig.get('Custom Team Names', DEFAULT_TEAM_NAMES)
        )

        # We need to flatten the translation since it will be an
        # editable string.
        self._names = [
            bui.Lstr(translate=('teamNames', n)).evaluate() for n in self._names
        ]
        self._colors = list(
            appconfig.get('Custom Team Colors', DEFAULT_TEAM_COLORS)
        )

        self._color_buttons: list[bui.Widget] = []
        self._color_text_fields: list[bui.Widget] = []

        resetbtn = bui.buttonwidget(
            parent=self.root_widget,
            label=bui.Lstr(resource='settingsWindowAdvanced.resetText'),
            autoselect=True,
            scale=0.7,
            on_activate_call=self._reset,
            size=(120, 50),
            position=(self._width * 0.5 - 60 * 0.7, self._height - 60),
        )

        for i in range(2):
            self._color_buttons.append(
                bui.buttonwidget(
                    parent=self.root_widget,
                    autoselect=True,
                    position=(50, 0 + 195 - 90 * i),
                    on_activate_call=bui.Call(self._color_click, i),
                    size=(70, 70),
                    color=self._colors[i],
                    label='',
                    button_type='square',
                )
            )
            self._color_text_fields.append(
                bui.textwidget(
                    parent=self.root_widget,
                    position=(135, 0 + 201 - 90 * i),
                    size=(280, 46),
                    text=self._names[i],
                    h_align='left',
                    v_align='center',
                    max_chars=self._max_name_length,
                    color=self._colors[i],
                    description=bui.Lstr(resource='nameText'),
                    editable=True,
                    padding=4,
                )
            )
        bui.widget(
            edit=self._color_text_fields[0],
            down_widget=self._color_text_fields[1],
        )
        bui.widget(
            edit=self._color_text_fields[1],
            up_widget=self._color_text_fields[0],
        )
        bui.widget(edit=self._color_text_fields[0], up_widget=resetbtn)

        cancelbtn = bui.buttonwidget(
            parent=self.root_widget,
            label=bui.Lstr(resource='cancelText'),
            autoselect=True,
            on_activate_call=self._on_cancel_press,
            size=(150, 50),
            position=(self._width * 0.5 - 200, 20),
        )
        okbtn = bui.buttonwidget(
            parent=self.root_widget,
            label=bui.Lstr(resource='okText'),
            autoselect=True,
            on_activate_call=self._ok,
            size=(150, 50),
            position=(self._width * 0.5 + 50, 20),
        )
        bui.containerwidget(
            edit=self.root_widget, selected_child=self._color_buttons[0]
        )
        bui.widget(edit=okbtn, left_widget=cancelbtn)
        self._update()

    def _color_click(self, i: int) -> None:
        ColorPicker(
            parent=self.root_widget,
            position=self._color_buttons[i].get_screen_space_center(),
            offset=(270.0, 0),
            initial_color=self._colors[i],
            delegate=self,
            tag=i,
        )

    def color_picker_closing(self, picker: ColorPicker) -> None:
        """Called when the color picker is closing."""

    def color_picker_selected_color(
        self, picker: ColorPicker, color: Sequence[float]
    ) -> None:
        """Called when a color is selected in the color picker."""
        self._colors[picker.get_tag()] = color
        self._update()

    def _reset(self) -> None:
        from bascenev1 import DEFAULT_TEAM_NAMES, DEFAULT_TEAM_COLORS

        for i in range(2):
            self._colors[i] = DEFAULT_TEAM_COLORS[i]
            name = bui.Lstr(
                translate=('teamNames', DEFAULT_TEAM_NAMES[i])
            ).evaluate()
            if len(name) > self._max_name_length:
                print('GOT DEFAULT TEAM NAME LONGER THAN MAX LENGTH')
            bui.textwidget(edit=self._color_text_fields[i], text=name)
        self._update()

    def _update(self) -> None:
        for i in range(2):
            bui.buttonwidget(edit=self._color_buttons[i], color=self._colors[i])
            bui.textwidget(
                edit=self._color_text_fields[i], color=self._colors[i]
            )

    def _ok(self) -> None:
        from bascenev1 import DEFAULT_TEAM_COLORS, DEFAULT_TEAM_NAMES

        cfg = bui.app.config

        # First, determine whether the values here are defaults, in which case
        # we can clear any values from prefs.  Currently if the string matches
        # either the default raw value or its translation we consider it
        # default. (the fact that team names get translated makes this
        # situation a bit sloppy)
        new_names: list[str] = []
        is_default = True
        for i in range(2):
            name = cast(str, bui.textwidget(query=self._color_text_fields[i]))
            if not name:
                bui.screenmessage(
                    bui.Lstr(resource='nameNotEmptyText'), color=(1, 0, 0)
                )
                bui.getsound('error').play()
                return
            new_names.append(name)

        for i in range(2):
            if self._colors[i] != DEFAULT_TEAM_COLORS[i]:
                is_default = False
            default_team_name = DEFAULT_TEAM_NAMES[i]
            default_team_name_translated = bui.Lstr(
                translate=('teamNames', default_team_name)
            ).evaluate()
            if (
                new_names[i] != default_team_name
                and new_names[i] != default_team_name_translated
            ):
                is_default = False

        if is_default:
            for key in ('Custom Team Names', 'Custom Team Colors'):
                if key in cfg:
                    del cfg[key]
        else:
            cfg['Custom Team Names'] = list(new_names)
            cfg['Custom Team Colors'] = list(self._colors)

        cfg.commit()
        self._transition_out()

    def _transition_out(self, transition: str = 'out_scale') -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition=transition)

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()

    def _on_cancel_press(self) -> None:
        self._transition_out()
