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
"""Provides a popup window for viewing trophies."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.ui import popup

if TYPE_CHECKING:
    from typing import Any, Tuple, Dict, List


class TrophiesWindow(popup.PopupWindow):
    """Popup window for viewing trophies."""

    def __init__(self,
                 position: Tuple[float, float],
                 data: Dict[str, Any],
                 scale: float = None):
        from ba.deprecated import get_resource
        self._data = data
        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (2.3 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)
        self._transitioning_out = False
        self._width = 300
        self._height = 300
        bg_color = (0.5, 0.4, 0.6)

        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=bg_color)

        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2)

        self._title_text = ba.textwidget(parent=self.root_widget,
                                         position=(self._width * 0.5,
                                                   self._height - 20),
                                         size=(0, 0),
                                         h_align='center',
                                         v_align='center',
                                         scale=0.6,
                                         text=ba.Lstr(resource='trophiesText'),
                                         maxwidth=200,
                                         color=(1, 1, 1, 0.4))

        self._scrollwidget = ba.scrollwidget(parent=self.root_widget,
                                             size=(self._width - 60,
                                                   self._height - 70),
                                             position=(30, 30),
                                             capture_arrows=True)
        ba.widget(edit=self._scrollwidget, autoselect=True)

        ba.containerwidget(edit=self.root_widget,
                           cancel_button=self._cancel_button)

        incr = 31
        sub_width = self._width - 90

        trophy_types = [['0a'], ['0b'], ['1'], ['2'], ['3'], ['4']]
        sub_height = 40 + len(trophy_types) * incr

        eq_text = get_resource('coopSelectWindow.powerRankingPointsEqualsText')

        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(sub_width, sub_height),
                                                background=False)

        total_pts = 0

        multi_txt = get_resource('coopSelectWindow.powerRankingPointsMultText')

        total_pts += self._create_trophy_type_widgets(eq_text, incr, multi_txt,
                                                      sub_height, sub_width,
                                                      trophy_types)

        ba.textwidget(parent=self._subcontainer,
                      position=(sub_width * 1.0,
                                sub_height - 20 - incr * len(trophy_types)),
                      maxwidth=sub_width * 0.5,
                      scale=0.7,
                      color=(0.7, 0.8, 1.0),
                      flatness=1.0,
                      shadow=0.0,
                      text=get_resource('coopSelectWindow.totalText') + ' ' +
                      eq_text.replace('${NUMBER}', str(total_pts)),
                      size=(0, 0),
                      h_align='right',
                      v_align='center')

    def _create_trophy_type_widgets(self, eq_text: str, incr: int,
                                    multi_txt: str, sub_height: int,
                                    sub_width: int,
                                    trophy_types: List[List[str]]) -> int:
        from ba.internal import get_trophy_string
        pts = 0
        for i, trophy_type in enumerate(trophy_types):
            t_count = self._data['t' + trophy_type[0]]
            t_mult = self._data['t' + trophy_type[0] + 'm']
            ba.textwidget(parent=self._subcontainer,
                          position=(sub_width * 0.15,
                                    sub_height - 20 - incr * i),
                          scale=0.7,
                          flatness=1.0,
                          shadow=0.7,
                          color=(1, 1, 1),
                          text=get_trophy_string(trophy_type[0]),
                          size=(0, 0),
                          h_align='center',
                          v_align='center')

            ba.textwidget(parent=self._subcontainer,
                          position=(sub_width * 0.31,
                                    sub_height - 20 - incr * i),
                          maxwidth=sub_width * 0.2,
                          scale=0.8,
                          flatness=1.0,
                          shadow=0.0,
                          color=(0, 1, 0) if (t_count > 0) else
                          (0.6, 0.6, 0.6, 0.5),
                          text=str(t_count),
                          size=(0, 0),
                          h_align='center',
                          v_align='center')

            txt = multi_txt.replace('${NUMBER}', str(t_mult))
            ba.textwidget(parent=self._subcontainer,
                          position=(sub_width * 0.57,
                                    sub_height - 20 - incr * i),
                          maxwidth=sub_width * 0.3,
                          scale=0.4,
                          flatness=1.0,
                          shadow=0.0,
                          color=(0.63, 0.6, 0.75) if (t_count > 0) else
                          (0.6, 0.6, 0.6, 0.4),
                          text=txt,
                          size=(0, 0),
                          h_align='center',
                          v_align='center')

            pts = t_count * t_mult
            ba.textwidget(parent=self._subcontainer,
                          position=(sub_width * 0.88,
                                    sub_height - 20 - incr * i),
                          maxwidth=sub_width * 0.3,
                          color=(0.7, 0.8, 1.0) if (t_count > 0) else
                          (0.9, 0.9, 1.0, 0.3),
                          flatness=1.0,
                          shadow=0.0,
                          scale=0.5,
                          text=eq_text.replace('${NUMBER}', str(pts)),
                          size=(0, 0),
                          h_align='center',
                          v_align='center')
            pts += pts
        return pts

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()
