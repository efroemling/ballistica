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
"""UI functionality related to using xbox360 controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    pass


class XBox360ControllerSettingsWindow(ba.Window):
    """UI showing info about xbox 360 controllers."""

    def __init__(self) -> None:
        self._r = 'xbox360ControllersWindow'
        width = 700
        height = 300 if _ba.is_running_on_fire_tv() else 485
        spacing = 40
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition='in_right',
            scale=(1.4 if uiscale is ba.UIScale.SMALL else
                   1.4 if uiscale is ba.UIScale.MEDIUM else 1.0)))

        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(35, height - 65),
                              size=(120, 60),
                              scale=0.84,
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              autoselect=True,
                              on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, height - 42),
                      size=(0, 0),
                      scale=0.85,
                      text=ba.Lstr(resource=self._r + '.titleText',
                                   subs=[('${APP_NAME}',
                                          ba.Lstr(resource='titleText'))]),
                      color=ba.app.ui.title_color,
                      maxwidth=400,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 70
        v -= spacing

        if _ba.is_running_on_fire_tv():
            ba.textwidget(parent=self._root_widget,
                          position=(width * 0.5, height * 0.47),
                          size=(0, 0),
                          color=(0.7, 0.9, 0.7, 1.0),
                          maxwidth=width * 0.95,
                          max_height=height * 0.75,
                          scale=0.7,
                          text=ba.Lstr(resource=self._r +
                                       '.ouyaInstructionsText'),
                          h_align='center',
                          v_align='center')
        else:
            ba.textwidget(parent=self._root_widget,
                          position=(width * 0.5, v - 1),
                          size=(0, 0),
                          color=(0.7, 0.9, 0.7, 1.0),
                          maxwidth=width * 0.95,
                          max_height=height * 0.22,
                          text=ba.Lstr(resource=self._r +
                                       '.macInstructionsText'),
                          scale=0.7,
                          h_align='center',
                          v_align='center')
            v -= 90
            b_width = 300
            btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - b_width) * 0.5, v - 10),
                size=(b_width, 50),
                label=ba.Lstr(resource=self._r + '.getDriverText'),
                autoselect=True,
                on_activate_call=ba.Call(
                    ba.open_url,
                    'https://github.com/360Controller/360Controller/releases'))
            ba.containerwidget(edit=self._root_widget, start_button=btn)
            v -= 60
            ba.textwidget(parent=self._root_widget,
                          position=(width * 0.5, v - 85),
                          size=(0, 0),
                          color=(0.7, 0.9, 0.7, 1.0),
                          maxwidth=width * 0.95,
                          max_height=height * 0.46,
                          scale=0.7,
                          text=ba.Lstr(resource=self._r +
                                       '.macInstructions2Text'),
                          h_align='center',
                          v_align='center')

    def _back(self) -> None:
        from bastd.ui.settings import controls
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            controls.ControlsSettingsWindow(
                transition='in_left').get_root_widget())
