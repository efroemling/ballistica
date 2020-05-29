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
"""Provides tip related Actor(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any


class TipsText(ba.Actor):
    """A bit of text showing various helpful game tips."""

    def __init__(self, offs_y: float = 100.0):
        super().__init__()
        self._tip_scale = 0.8
        self._tip_title_scale = 1.1
        self._offs_y = offs_y
        self.node = ba.newnode('text',
                               delegate=self,
                               attrs={
                                   'text': '',
                                   'scale': self._tip_scale,
                                   'h_align': 'left',
                                   'maxwidth': 800,
                                   'vr_depth': -20,
                                   'v_align': 'center',
                                   'v_attach': 'bottom'
                               })
        tval = ba.Lstr(value='${A}:',
                       subs=[('${A}', ba.Lstr(resource='tipText'))])
        self.title_node = ba.newnode('text',
                                     delegate=self,
                                     attrs={
                                         'text': tval,
                                         'scale': self._tip_title_scale,
                                         'maxwidth': 122,
                                         'h_align': 'right',
                                         'vr_depth': -20,
                                         'v_align': 'center',
                                         'v_attach': 'bottom'
                                     })
        self._message_duration = 10000
        self._message_spacing = 3000
        self._change_timer = ba.Timer(
            0.001 * (self._message_duration + self._message_spacing),
            ba.WeakCall(self.change_phrase),
            repeat=True)
        self._combine = ba.newnode('combine',
                                   owner=self.node,
                                   attrs={
                                       'input0': 1.0,
                                       'input1': 0.8,
                                       'input2': 1.0,
                                       'size': 4
                                   })
        self._combine.connectattr('output', self.node, 'color')
        self._combine.connectattr('output', self.title_node, 'color')
        self.change_phrase()

    def change_phrase(self) -> None:
        """Switch the visible tip phrase."""
        from ba.internal import get_remote_app_name, get_next_tip
        next_tip = ba.Lstr(translate=('tips', get_next_tip()),
                           subs=[('${REMOTE_APP_NAME}', get_remote_app_name())
                                 ])
        spc = self._message_spacing
        assert self.node
        self.node.position = (-200, self._offs_y)
        self.title_node.position = (-220, self._offs_y + 3)
        keys = {
            spc: 0,
            spc + 1000: 1.0,
            spc + self._message_duration - 1000: 1.0,
            spc + self._message_duration: 0.0
        }
        ba.animate(self._combine,
                   'input3', {k: v * 0.5
                              for k, v in list(keys.items())},
                   timeformat=ba.TimeFormat.MILLISECONDS)
        self.node.text = next_tip

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
            self.title_node.delete()
            return None
        return super().handlemessage(msg)
