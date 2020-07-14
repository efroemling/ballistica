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
"""Settings UI functionality related to wiimote support."""
from __future__ import annotations

import _ba
import ba


class WiimoteSettingsWindow(ba.Window):
    """Window for setting up Wiimotes."""

    def __init__(self) -> None:
        self._r = 'wiimoteSetupWindow'
        width = 600
        height = 480
        spacing = 40
        super().__init__(root_widget=ba.containerwidget(size=(width, height),
                                                        transition='in_right'))

        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(55, height - 50),
                              size=(120, 60),
                              scale=0.8,
                              autoselect=True,
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              on_activate_call=self._back)

        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, height - 28),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      maxwidth=270,
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 60.0
        v -= spacing
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, v - 80),
                      size=(0, 0),
                      color=(0.7, 0.9, 0.7, 1.0),
                      scale=0.75,
                      text=ba.Lstr(resource=self._r + '.macInstructionsText'),
                      maxwidth=width * 0.95,
                      max_height=height * 0.5,
                      h_align='center',
                      v_align='center')
        v -= 230
        button_width = 200
        v -= 30
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(width / 2 - button_width / 2, v + 1),
                              autoselect=True,
                              size=(button_width, 50),
                              label=ba.Lstr(resource=self._r + '.listenText'),
                              on_activate_call=WiimoteListenWindow)
        ba.containerwidget(edit=self._root_widget, start_button=btn)
        v -= spacing * 1.1
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, v),
                      size=(0, 0),
                      color=(0.7, 0.9, 0.7, 1.0),
                      scale=0.8,
                      maxwidth=width * 0.95,
                      text=ba.Lstr(resource=self._r + '.thanksText'),
                      h_align='center',
                      v_align='center')
        v -= 30
        this_button_width = 200
        ba.buttonwidget(parent=self._root_widget,
                        position=(width / 2 - this_button_width / 2, v - 14),
                        color=(0.45, 0.4, 0.5),
                        autoselect=True,
                        size=(this_button_width, 15),
                        label=ba.Lstr(resource=self._r + '.copyrightText'),
                        textcolor=(0.55, 0.5, 0.6),
                        text_scale=0.6,
                        on_activate_call=WiimoteLicenseWindow)

    def _back(self) -> None:
        from bastd.ui.settings import controls
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            controls.ControlsSettingsWindow(
                transition='in_left').get_root_widget())


class WiimoteListenWindow(ba.Window):
    """Window shown while listening for a wiimote connection."""

    def __init__(self) -> None:
        self._r = 'wiimoteListenWindow'
        width = 650
        height = 210
        super().__init__(root_widget=ba.containerwidget(size=(width, height),
                                                        transition='in_right'))
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(35, height - 60),
                              size=(140, 60),
                              autoselect=True,
                              label=ba.Lstr(resource='cancelText'),
                              scale=0.8,
                              on_activate_call=self._dismiss)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        _ba.start_listening_for_wii_remotes()
        self._wiimote_connect_counter = 15
        ba.app.ui.dismiss_wii_remotes_window_call = ba.WeakCall(self._dismiss)
        ba.textwidget(parent=self._root_widget,
                      position=(15, height - 55),
                      size=(width - 30, 30),
                      text=ba.Lstr(resource=self._r + '.listeningText'),
                      color=ba.app.ui.title_color,
                      maxwidth=320,
                      h_align='center',
                      v_align='center')
        ba.textwidget(parent=self._root_widget,
                      position=(15, height - 110),
                      size=(width - 30, 30),
                      scale=1.0,
                      text=ba.Lstr(resource=self._r + '.pressText'),
                      maxwidth=width * 0.9,
                      color=(0.7, 0.9, 0.7, 1.0),
                      h_align='center',
                      v_align='center')
        ba.textwidget(parent=self._root_widget,
                      position=(15, height - 140),
                      size=(width - 30, 30),
                      color=(0.7, 0.9, 0.7, 1.0),
                      scale=0.55,
                      text=ba.Lstr(resource=self._r + '.pressText2'),
                      maxwidth=width * 0.95,
                      h_align='center',
                      v_align='center')
        self._counter_text = ba.textwidget(parent=self._root_widget,
                                           position=(15, 23),
                                           size=(width - 30, 30),
                                           scale=1.2,
                                           text='15',
                                           h_align='center',
                                           v_align='top')
        for i in range(1, 15):
            ba.timer(1.0 * i,
                     ba.WeakCall(self._decrement),
                     timetype=ba.TimeType.REAL)
        ba.timer(15.0, ba.WeakCall(self._dismiss), timetype=ba.TimeType.REAL)

    def _decrement(self) -> None:
        self._wiimote_connect_counter -= 1
        ba.textwidget(edit=self._counter_text,
                      text=str(self._wiimote_connect_counter))

    def _dismiss(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        _ba.stop_listening_for_wii_remotes()


class WiimoteLicenseWindow(ba.Window):
    """Window displaying the Darwiinremote software license."""

    def __init__(self) -> None:
        self._r = 'wiimoteLicenseWindow'
        width = 750
        height = 550
        super().__init__(root_widget=ba.containerwidget(size=(width, height),
                                                        transition='in_right'))
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(65, height - 50),
                              size=(120, 60),
                              scale=0.8,
                              autoselect=True,
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              on_activate_call=self._close)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        ba.textwidget(parent=self._root_widget,
                      position=(0, height - 48),
                      size=(width, 30),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      h_align='center',
                      color=ba.app.ui.title_color,
                      v_align='center')
        license_text = (
            'Copyright (c) 2007, DarwiinRemote Team\n'
            'All rights reserved.\n'
            '\n'
            '   Redistribution and use in source and binary forms, with or '
            'without modification,\n'
            '   are permitted provided that'
            ' the following conditions are met:\n'
            '\n'
            '1. Redistributions of source code must retain the above copyright'
            ' notice, this\n'
            '     list of conditions and the following disclaimer.\n'
            '2. Redistributions in binary form must reproduce the above'
            ' copyright notice, this\n'
            '     list of conditions and the following disclaimer in the'
            ' documentation and/or other\n'
            '     materials provided with the distribution.\n'
            '3. Neither the name of this project nor the names of its'
            ' contributors may be used to\n'
            '     endorse or promote products derived from this software'
            ' without specific prior\n'
            '     written permission.\n'
            '\n'
            'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND'
            ' CONTRIBUTORS "AS IS"\n'
            'AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT'
            ' LIMITED TO, THE\n'
            'IMPLIED WARRANTIES OF MERCHANTABILITY'
            ' AND FITNESS FOR A PARTICULAR'
            ' PURPOSE\n'
            'ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR'
            ' CONTRIBUTORS BE\n'
            'LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,'
            ' OR\n'
            'CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT'
            ' OF\n'
            ' SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;'
            ' OR BUSINESS\n'
            'INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,'
            ' WHETHER IN\n'
            'CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR'
            ' OTHERWISE)\n'
            'ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF'
            ' ADVISED OF THE\n'
            'POSSIBILITY OF SUCH DAMAGE.\n')
        license_text_scale = 0.62
        ba.textwidget(parent=self._root_widget,
                      position=(100, height * 0.45),
                      size=(0, 0),
                      h_align='left',
                      v_align='center',
                      padding=4,
                      color=(0.7, 0.9, 0.7, 1.0),
                      scale=license_text_scale,
                      maxwidth=width * 0.9 - 100,
                      max_height=height * 0.85,
                      text=license_text)

    def _close(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
