# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Provides a window to customize team names and colors."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import ba
from bastd.ui import popup

if TYPE_CHECKING:
    from typing import Tuple, List, Sequence
    from bastd.ui.colorpicker import ColorPicker


class TeamNamesColorsWindow(popup.PopupWindow):
    """A popup window for customizing team names and colors."""

    def __init__(self, scale_origin: Tuple[float, float]):
        from ba.internal import DEFAULT_TEAM_COLORS, DEFAULT_TEAM_NAMES
        self._width = 500
        self._height = 330
        self._transitioning_out = False
        self._max_name_length = 16

        # Creates our _root_widget.
        uiscale = ba.app.ui.uiscale
        scale = (1.69 if uiscale is ba.UIScale.SMALL else
                 1.1 if uiscale is ba.UIScale.MEDIUM else 0.85)
        super().__init__(position=scale_origin,
                         size=(self._width, self._height),
                         scale=scale)

        appconfig = ba.app.config
        self._names = list(
            appconfig.get('Custom Team Names', DEFAULT_TEAM_NAMES))
        # We need to flatten the translation since it will be an
        # editable string.
        self._names = [
            ba.Lstr(translate=('teamNames', n)).evaluate() for n in self._names
        ]
        self._colors = list(
            appconfig.get('Custom Team Colors', DEFAULT_TEAM_COLORS))

        self._color_buttons: List[ba.Widget] = []
        self._color_text_fields: List[ba.Widget] = []

        ba.buttonwidget(
            parent=self.root_widget,
            label=ba.Lstr(resource='settingsWindowAdvanced.resetText'),
            autoselect=True,
            scale=0.7,
            on_activate_call=self._reset,
            size=(120, 50),
            position=(self._width * 0.5 - 60 * 0.7, self._height - 60))

        for i in range(2):
            self._color_buttons.append(
                ba.buttonwidget(parent=self.root_widget,
                                autoselect=True,
                                position=(50, 0 + 195 - 90 * i),
                                on_activate_call=ba.Call(self._color_click, i),
                                size=(70, 70),
                                color=self._colors[i],
                                label='',
                                button_type='square'))
            self._color_text_fields.append(
                ba.textwidget(parent=self.root_widget,
                              position=(135, 0 + 201 - 90 * i),
                              size=(280, 46),
                              text=self._names[i],
                              h_align='left',
                              v_align='center',
                              max_chars=self._max_name_length,
                              color=self._colors[i],
                              description=ba.Lstr(resource='nameText'),
                              editable=True,
                              padding=4))
        ba.buttonwidget(parent=self.root_widget,
                        label=ba.Lstr(resource='cancelText'),
                        autoselect=True,
                        on_activate_call=self._on_cancel_press,
                        size=(150, 50),
                        position=(self._width * 0.5 - 200, 20))
        ba.buttonwidget(parent=self.root_widget,
                        label=ba.Lstr(resource='saveText'),
                        autoselect=True,
                        on_activate_call=self._save,
                        size=(150, 50),
                        position=(self._width * 0.5 + 50, 20))
        ba.containerwidget(edit=self.root_widget,
                           selected_child=self._color_buttons[0])
        self._update()

    def _color_click(self, i: int) -> None:
        from bastd.ui.colorpicker import ColorPicker
        ColorPicker(parent=self.root_widget,
                    position=self._color_buttons[i].get_screen_space_center(),
                    offset=(270.0, 0),
                    initial_color=self._colors[i],
                    delegate=self,
                    tag=i)

    def color_picker_closing(self, picker: ColorPicker) -> None:
        """Called when the color picker is closing."""

    def color_picker_selected_color(self, picker: ColorPicker,
                                    color: Sequence[float]) -> None:
        """Called when a color is selected in the color picker."""
        self._colors[picker.get_tag()] = color
        self._update()

    def _reset(self) -> None:
        from ba.internal import DEFAULT_TEAM_NAMES, DEFAULT_TEAM_COLORS
        for i in range(2):
            self._colors[i] = DEFAULT_TEAM_COLORS[i]
            name = ba.Lstr(translate=('teamNames',
                                      DEFAULT_TEAM_NAMES[i])).evaluate()
            if len(name) > self._max_name_length:
                print('GOT DEFAULT TEAM NAME LONGER THAN MAX LENGTH')
            ba.textwidget(edit=self._color_text_fields[i], text=name)
        self._update()

    def _update(self) -> None:
        for i in range(2):
            ba.buttonwidget(edit=self._color_buttons[i], color=self._colors[i])
            ba.textwidget(edit=self._color_text_fields[i],
                          color=self._colors[i])

    def _save(self) -> None:
        from ba.internal import DEFAULT_TEAM_COLORS, DEFAULT_TEAM_NAMES
        cfg = ba.app.config

        # First, determine whether the values here are defaults, in which case
        # we can clear any values from prefs.  Currently if the string matches
        # either the default raw value or its translation we consider it
        # default. (the fact that team names get translated makes this
        # situation a bit sloppy)
        new_names: List[str] = []
        is_default = True
        for i in range(2):
            name = cast(str, ba.textwidget(query=self._color_text_fields[i]))
            if not name:
                ba.screenmessage(ba.Lstr(resource='nameNotEmptyText'),
                                 color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return
            new_names.append(name)

        for i in range(2):
            if self._colors[i] != DEFAULT_TEAM_COLORS[i]:
                is_default = False
            default_team_name = DEFAULT_TEAM_NAMES[i]
            default_team_name_translated = ba.Lstr(
                translate=('teamNames', default_team_name)).evaluate()
            if ((new_names[i] != default_team_name
                 and new_names[i] != default_team_name_translated)):
                is_default = False

        if is_default:
            for key in ('Custom Team Names', 'Custom Team Colors'):
                if key in cfg:
                    del cfg[key]
        else:
            cfg['Custom Team Names'] = tuple(new_names)
            cfg['Custom Team Colors'] = tuple(self._colors)

        cfg.commit()
        ba.playsound(ba.getsound('gunCocking'))
        self._transition_out()

    def _transition_out(self, transition: str = 'out_scale') -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition=transition)

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()

    def _on_cancel_press(self) -> None:
        self._transition_out()
