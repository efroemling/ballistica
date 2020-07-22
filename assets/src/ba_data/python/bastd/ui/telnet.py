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
"""UI functionality for telnet access."""

from __future__ import annotations

import _ba
import ba


class TelnetAccessRequestWindow(ba.Window):
    """Window asking the user whether to allow a telnet connection."""

    def __init__(self) -> None:
        width = 400
        height = 100
        text = ba.Lstr(resource='telnetAccessText')

        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + 40),
            transition='in_right',
            scale=(1.7 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        padding = 20
        ba.textwidget(parent=self._root_widget,
                      position=(padding, padding + 33),
                      size=(width - 2 * padding, height - 2 * padding),
                      h_align='center',
                      v_align='top',
                      text=text)
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(20, 20),
                              size=(140, 50),
                              label=ba.Lstr(resource='denyText'),
                              on_activate_call=self._cancel)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        ba.containerwidget(edit=self._root_widget, selected_child=btn)

        ba.buttonwidget(parent=self._root_widget,
                        position=(width - 155, 20),
                        size=(140, 50),
                        label=ba.Lstr(resource='allowText'),
                        on_activate_call=self._ok)

    def _cancel(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        _ba.set_telnet_access_enabled(False)

    def _ok(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        _ba.set_telnet_access_enabled(True)
        ba.screenmessage(ba.Lstr(resource='telnetAccessGrantedText'))
