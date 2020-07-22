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
"""Dialog window controlled by the master server."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Dict, Optional


class ServerDialogWindow(ba.Window):
    """A dialog window driven by the master-server."""

    def __init__(self, data: Dict[str, Any]):
        self._dialog_id = data['dialogID']
        txt = ba.Lstr(translate=('serverResponses', data['text']),
                      subs=data.get('subs', [])).evaluate()
        txt = txt.strip()
        txt_scale = 1.5
        txt_height = (_ba.get_string_height(txt, suppress_warning=True) *
                      txt_scale)
        self._width = 500
        self._height = 130 + min(200, txt_height)
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            scale=(1.8 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        self._starttime = ba.time(ba.TimeType.REAL, ba.TimeFormat.MILLISECONDS)

        ba.playsound(ba.getsound('swish'))
        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5,
                                70 + (self._height - 70) * 0.5),
                      size=(0, 0),
                      color=(1.0, 3.0, 1.0),
                      scale=txt_scale,
                      h_align='center',
                      v_align='center',
                      text=txt,
                      maxwidth=self._width * 0.85,
                      max_height=(self._height - 110))
        show_cancel = data.get('showCancel', True)
        self._cancel_button: Optional[ba.Widget]
        if show_cancel:
            self._cancel_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(30, 30),
                size=(160, 60),
                autoselect=True,
                label=ba.Lstr(resource='cancelText'),
                on_activate_call=self._cancel_press)
        else:
            self._cancel_button = None
        self._ok_button = ba.buttonwidget(
            parent=self._root_widget,
            position=((self._width - 182) if show_cancel else
                      (self._width * 0.5 - 80), 30),
            size=(160, 60),
            autoselect=True,
            label=ba.Lstr(resource='okText'),
            on_activate_call=self._ok_press)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button,
                           start_button=self._ok_button,
                           selected_child=self._ok_button)

    def _ok_press(self) -> None:
        if ba.time(ba.TimeType.REAL,
                   ba.TimeFormat.MILLISECONDS) - self._starttime < 1000:
            ba.playsound(ba.getsound('error'))
            return
        _ba.add_transaction({
            'type': 'DIALOG_RESPONSE',
            'dialogID': self._dialog_id,
            'response': 1
        })
        ba.containerwidget(edit=self._root_widget, transition='out_scale')

    def _cancel_press(self) -> None:
        if ba.time(ba.TimeType.REAL,
                   ba.TimeFormat.MILLISECONDS) - self._starttime < 1000:
            ba.playsound(ba.getsound('error'))
            return
        _ba.add_transaction({
            'type': 'DIALOG_RESPONSE',
            'dialogID': self._dialog_id,
            'response': 0
        })
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
