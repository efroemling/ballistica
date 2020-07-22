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
"""UI functionality for importing shared playlists."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui import promocode

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Optional, Tuple


class SharePlaylistImportWindow(promocode.PromoCodeWindow):
    """Window for importing a shared playlist."""

    def __init__(self,
                 origin_widget: ba.Widget = None,
                 on_success_callback: Callable[[], Any] = None):
        promocode.PromoCodeWindow.__init__(self,
                                           modal=True,
                                           origin_widget=origin_widget)
        self._on_success_callback = on_success_callback

    def _on_import_response(self, response: Optional[Dict[str, Any]]) -> None:
        if response is None:
            ba.screenmessage(ba.Lstr(resource='errorText'), color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        if response['playlistType'] == 'Team Tournament':
            playlist_type_name = ba.Lstr(resource='playModes.teamsText')
        elif response['playlistType'] == 'Free-for-All':
            playlist_type_name = ba.Lstr(resource='playModes.freeForAllText')
        else:
            playlist_type_name = ba.Lstr(value=response['playlistType'])

        ba.screenmessage(ba.Lstr(resource='importPlaylistSuccessText',
                                 subs=[('${TYPE}', playlist_type_name),
                                       ('${NAME}', response['playlistName'])]),
                         color=(0, 1, 0))
        ba.playsound(ba.getsound('gunCocking'))
        if self._on_success_callback is not None:
            self._on_success_callback()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)

    def _do_enter(self) -> None:
        _ba.add_transaction(
            {
                'type': 'IMPORT_PLAYLIST',
                'expire_time': time.time() + 5,
                'code': ba.textwidget(query=self._text_field)
            },
            callback=ba.WeakCall(self._on_import_response))
        _ba.run_transactions()
        ba.screenmessage(ba.Lstr(resource='importingText'))


class SharePlaylistResultsWindow(ba.Window):
    """Window for sharing playlists."""

    def __init__(self,
                 name: str,
                 data: str,
                 origin: Tuple[float, float] = (0.0, 0.0)):
        del origin  # unused arg
        self._width = 450
        self._height = 300
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='in_scale',
            scale=(1.8 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        ba.playsound(ba.getsound('cashRegister'))
        ba.playsound(ba.getsound('swish'))

        self._cancel_button = ba.buttonwidget(parent=self._root_widget,
                                              scale=0.7,
                                              position=(40, self._height - 40),
                                              size=(50, 50),
                                              label='',
                                              on_activate_call=self.close,
                                              autoselect=True,
                                              color=(0.45, 0.63, 0.15),
                                              icon=ba.gettexture('crossOut'),
                                              iconscale=1.2)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height * 0.745),
                      size=(0, 0),
                      color=ba.app.ui.infotextcolor,
                      scale=1.0,
                      flatness=1.0,
                      h_align='center',
                      v_align='center',
                      text=ba.Lstr(resource='exportSuccessText',
                                   subs=[('${NAME}', name)]),
                      maxwidth=self._width * 0.85)

        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.645),
            size=(0, 0),
            color=ba.app.ui.infotextcolor,
            scale=0.6,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='importPlaylistCodeInstructionsText'),
            maxwidth=self._width * 0.85)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height * 0.4),
                      size=(0, 0),
                      color=(1.0, 3.0, 1.0),
                      scale=2.3,
                      h_align='center',
                      v_align='center',
                      text=data,
                      maxwidth=self._width * 0.85)

    def close(self) -> None:
        """Close the window."""
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
