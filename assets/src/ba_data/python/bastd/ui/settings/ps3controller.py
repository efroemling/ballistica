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
"""Settings UI related to PS3 controllers."""

from __future__ import annotations

import _ba
import ba


class PS3ControllerSettingsWindow(ba.Window):
    """UI showing info about using PS3 controllers."""

    def __init__(self) -> None:
        width = 760
        height = 330 if _ba.is_running_on_fire_tv() else 540
        spacing = 40
        self._r = 'ps3ControllersWindow'
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition='in_right',
            scale=(1.35 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0)))

        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(37, height - 73),
                              size=(135, 65),
                              scale=0.85,
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              autoselect=True,
                              on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, height - 46),
                      size=(0, 0),
                      maxwidth=410,
                      text=ba.Lstr(resource=self._r + '.titleText',
                                   subs=[('${APP_NAME}',
                                          ba.Lstr(resource='titleText'))]),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 90
        v -= spacing

        if _ba.is_running_on_fire_tv():
            ba.textwidget(parent=self._root_widget,
                          position=(width * 0.5, height * 0.45),
                          size=(0, 0),
                          color=(0.7, 0.9, 0.7, 1.0),
                          maxwidth=width * 0.95,
                          max_height=height * 0.8,
                          scale=1.0,
                          text=ba.Lstr(resource=self._r +
                                       '.ouyaInstructionsText'),
                          h_align='center',
                          v_align='center')
        else:
            txts = ba.Lstr(resource=self._r +
                           '.macInstructionsText').evaluate().split('\n\n\n')
            ba.textwidget(parent=self._root_widget,
                          position=(width * 0.5, v - 29),
                          size=(0, 0),
                          color=(0.7, 0.9, 0.7, 1.0),
                          maxwidth=width * 0.95,
                          max_height=170,
                          scale=1.0,
                          text=txts[0].strip(),
                          h_align='center',
                          v_align='center')
            if txts:
                ba.textwidget(parent=self._root_widget,
                              position=(width * 0.5, v - 280),
                              size=(0, 0),
                              color=(0.7, 0.9, 0.7, 1.0),
                              maxwidth=width * 0.95,
                              max_height=170,
                              scale=1.0,
                              text=txts[1].strip(),
                              h_align='center',
                              v_align='center')

            ba.buttonwidget(parent=self._root_widget,
                            position=(225, v - 176),
                            size=(300, 40),
                            label=ba.Lstr(resource=self._r +
                                          '.pairingTutorialText'),
                            autoselect=True,
                            on_activate_call=ba.Call(
                                ba.open_url, 'http://www.youtube.com/watch'
                                '?v=IlR_HxeOQpI&feature=related'))

    def _back(self) -> None:
        from bastd.ui.settings import controls
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            controls.ControlsSettingsWindow(
                transition='in_left').get_root_widget())
