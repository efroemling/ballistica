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
"""Settings UI functionality related to the remote app."""

from __future__ import annotations

import ba


class RemoteAppSettingsWindow(ba.Window):
    """Window showing info/settings related to the remote app."""

    def __init__(self) -> None:
        from ba.internal import get_remote_app_name
        self._r = 'connectMobileDevicesWindow'
        width = 700
        height = 390
        spacing = 40
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition='in_right',
            scale=(1.85 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(-10, 0) if uiscale is ba.UIScale.SMALL else (0, 0)))
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(40, height - 67),
                              size=(140, 65),
                              scale=0.8,
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              text_scale=1.1,
                              autoselect=True,
                              on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, height - 42),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      maxwidth=370,
                      color=ba.app.ui.title_color,
                      scale=0.8,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 70.0
        v -= spacing * 1.2
        ba.textwidget(parent=self._root_widget,
                      position=(15, v - 26),
                      size=(width - 30, 30),
                      maxwidth=width * 0.95,
                      color=(0.7, 0.9, 0.7, 1.0),
                      scale=0.8,
                      text=ba.Lstr(resource=self._r + '.explanationText',
                                   subs=[('${APP_NAME}',
                                          ba.Lstr(resource='titleText')),
                                         ('${REMOTE_APP_NAME}',
                                          get_remote_app_name())]),
                      max_height=100,
                      h_align='center',
                      v_align='center')
        v -= 90

        # hmm the itms:// version doesnt bounce through safari but is kinda
        # apple-specific-ish

        # Update: now we just show link to the remote webpage.
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, v + 5),
                      size=(0, 0),
                      color=(0.7, 0.9, 0.7, 1.0),
                      scale=1.4,
                      text='bombsquadgame.com/remote',
                      maxwidth=width * 0.95,
                      max_height=60,
                      h_align='center',
                      v_align='center')
        v -= 30

        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, v - 35),
                      size=(0, 0),
                      color=(0.7, 0.9, 0.7, 0.8),
                      scale=0.65,
                      text=ba.Lstr(resource=self._r + '.bestResultsText'),
                      maxwidth=width * 0.95,
                      max_height=height * 0.19,
                      h_align='center',
                      v_align='center')

        ba.checkboxwidget(
            parent=self._root_widget,
            position=(width * 0.5 - 150, v - 116),
            size=(300, 30),
            maxwidth=300,
            scale=0.8,
            value=not ba.app.config.resolve('Enable Remote App'),
            autoselect=True,
            text=ba.Lstr(resource='disableRemoteAppConnectionsText'),
            on_value_change_call=self._on_check_changed)

    def _on_check_changed(self, value: bool) -> None:
        cfg = ba.app.config
        cfg['Enable Remote App'] = not value
        cfg.apply_and_commit()

    def _back(self) -> None:
        from bastd.ui.settings import controls
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            controls.ControlsSettingsWindow(
                transition='in_left').get_root_widget())
