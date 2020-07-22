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
"""UI functionality related to URLs."""

from __future__ import annotations

import _ba
import ba


class ShowURLWindow(ba.Window):
    """A window presenting a URL to the user visually."""

    def __init__(self, address: str):

        # in some cases we might want to show it as a qr code
        # (for long URLs especially)
        app = ba.app
        uiscale = app.ui.uiscale
        if app.platform == 'android' and app.subplatform == 'alibaba':
            self._width = 500
            self._height = 500
            super().__init__(root_widget=ba.containerwidget(
                size=(self._width, self._height),
                transition='in_right',
                scale=(1.25 if uiscale is ba.UIScale.SMALL else
                       1.25 if uiscale is ba.UIScale.MEDIUM else 1.25)))
            self._cancel_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(50, self._height - 30),
                size=(50, 50),
                scale=0.6,
                label='',
                color=(0.6, 0.5, 0.6),
                on_activate_call=self._done,
                autoselect=True,
                icon=ba.gettexture('crossOut'),
                iconscale=1.2)
            qr_size = 400
            ba.imagewidget(parent=self._root_widget,
                           position=(self._width * 0.5 - qr_size * 0.5,
                                     self._height * 0.5 - qr_size * 0.5),
                           size=(qr_size, qr_size),
                           texture=_ba.get_qrcode_texture(address))
            ba.containerwidget(edit=self._root_widget,
                               cancel_button=self._cancel_button)
        else:
            # show it as a simple string...
            self._width = 800
            self._height = 200
            self._root_widget = ba.containerwidget(
                size=(self._width, self._height + 40),
                transition='in_right',
                scale=(1.25 if uiscale is ba.UIScale.SMALL else
                       1.25 if uiscale is ba.UIScale.MEDIUM else 1.25))
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, self._height - 10),
                          size=(0, 0),
                          color=ba.app.ui.title_color,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource='directBrowserToURLText'),
                          maxwidth=self._width * 0.95)
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5,
                                    self._height * 0.5 + 29),
                          size=(0, 0),
                          scale=1.3,
                          color=ba.app.ui.infotextcolor,
                          h_align='center',
                          v_align='center',
                          text=address,
                          maxwidth=self._width * 0.95)
            button_width = 200
            btn = ba.buttonwidget(parent=self._root_widget,
                                  position=(self._width * 0.5 -
                                            button_width * 0.5, 20),
                                  size=(button_width, 65),
                                  label=ba.Lstr(resource='doneText'),
                                  on_activate_call=self._done)
            # we have no 'cancel' button but still want to be able to
            # hit back/escape/etc to leave..
            ba.containerwidget(edit=self._root_widget,
                               selected_child=btn,
                               start_button=btn,
                               on_cancel_call=btn.activate)

    def _done(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_left')
