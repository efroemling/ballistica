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
"""Defined Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Union, Tuple, Sequence


class ZoomText(ba.Actor):
    """Big Zooming Text.

    Category: Gameplay Classes

    Used for things such as the 'BOB WINS' victory messages.
    """

    def __init__(self,
                 text: Union[str, ba.Lstr],
                 position: Tuple[float, float] = (0.0, 0.0),
                 shiftposition: Tuple[float, float] = None,
                 shiftdelay: float = None,
                 lifespan: float = None,
                 flash: bool = True,
                 trail: bool = True,
                 h_align: str = 'center',
                 color: Sequence[float] = (0.9, 0.4, 0.0),
                 jitter: float = 0.0,
                 trailcolor: Sequence[float] = (1.0, 0.35, 0.1, 0.0),
                 scale: float = 1.0,
                 project_scale: float = 1.0,
                 tilt_translate: float = 0.0,
                 maxwidth: float = None):
        # pylint: disable=too-many-locals
        super().__init__()
        self._dying = False
        positionadjusted = (position[0], position[1] - 100)
        if shiftdelay is None:
            shiftdelay = 2.500
        if shiftdelay < 0.0:
            ba.print_error('got shiftdelay < 0')
            shiftdelay = 0.0
        self._project_scale = project_scale
        self.node = ba.newnode(
            'text',
            delegate=self,
            attrs={
                'position': positionadjusted,
                'big': True,
                'text': text,
                'trail': trail,
                'vr_depth': 0,
                'shadow': 0.0 if trail else 0.3,
                'scale': scale,
                'maxwidth': maxwidth if maxwidth is not None else 0.0,
                'tilt_translate': tilt_translate,
                'h_align': h_align,
                'v_align': 'center'
            })

        # we never jitter in vr mode..
        if ba.app.vr_mode:
            jitter = 0.0

        # if they want jitter, animate its position slightly...
        if jitter > 0.0:
            self._jitter(positionadjusted, jitter * scale)

        # if they want shifting, move to the shift position and
        # then resume jittering
        if shiftposition is not None:
            positionadjusted2 = (shiftposition[0], shiftposition[1] - 100)
            ba.timer(
                shiftdelay,
                ba.WeakCall(self._shift, positionadjusted, positionadjusted2))
            if jitter > 0.0:
                ba.timer(
                    shiftdelay + 0.25,
                    ba.WeakCall(self._jitter, positionadjusted2,
                                jitter * scale))
        color_combine = ba.newnode('combine',
                                   owner=self.node,
                                   attrs={
                                       'input2': color[2],
                                       'input3': 1.0,
                                       'size': 4
                                   })
        if trail:
            trailcolor_n = ba.newnode('combine',
                                      owner=self.node,
                                      attrs={
                                          'size': 3,
                                          'input0': trailcolor[0],
                                          'input1': trailcolor[1],
                                          'input2': trailcolor[2]
                                      })
            trailcolor_n.connectattr('output', self.node, 'trailcolor')
            basemult = 0.85
            ba.animate(
                self.node, 'trail_project_scale', {
                    0: 0 * project_scale,
                    basemult * 0.201: 0.6 * project_scale,
                    basemult * 0.347: 0.8 * project_scale,
                    basemult * 0.478: 0.9 * project_scale,
                    basemult * 0.595: 0.93 * project_scale,
                    basemult * 0.748: 0.95 * project_scale,
                    basemult * 0.941: 0.95 * project_scale
                })
        if flash:
            mult = 2.0
            tm1 = 0.15
            tm2 = 0.3
            ba.animate(color_combine,
                       'input0', {
                           0: color[0] * mult,
                           tm1: color[0],
                           tm2: color[0] * mult
                       },
                       loop=True)
            ba.animate(color_combine,
                       'input1', {
                           0: color[1] * mult,
                           tm1: color[1],
                           tm2: color[1] * mult
                       },
                       loop=True)
            ba.animate(color_combine,
                       'input2', {
                           0: color[2] * mult,
                           tm1: color[2],
                           tm2: color[2] * mult
                       },
                       loop=True)
        else:
            color_combine.input0 = color[0]
            color_combine.input1 = color[1]
        color_combine.connectattr('output', self.node, 'color')
        ba.animate(self.node, 'project_scale', {
            0: 0,
            0.27: 1.05 * project_scale,
            0.3: 1 * project_scale
        })

        # if they give us a lifespan, kill ourself down the line
        if lifespan is not None:
            ba.timer(lifespan, ba.WeakCall(self.handlemessage,
                                           ba.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, ba.DieMessage):
            if not self._dying and self.node:
                self._dying = True
                if msg.immediate:
                    self.node.delete()
                else:
                    ba.animate(
                        self.node, 'project_scale', {
                            0.0: 1 * self._project_scale,
                            0.6: 1.2 * self._project_scale
                        })
                    ba.animate(self.node, 'opacity', {0.0: 1, 0.3: 0})
                    ba.animate(self.node, 'trail_opacity', {0.0: 1, 0.6: 0})
                    ba.timer(0.7, self.node.delete)
            return None
        return super().handlemessage(msg)

    def _jitter(self, position: Tuple[float, float],
                jitter_amount: float) -> None:
        if not self.node:
            return
        cmb = ba.newnode('combine', owner=self.node, attrs={'size': 2})
        for index, attr in enumerate(['input0', 'input1']):
            keys = {}
            timeval = 0.0
            # gen some random keys for that stop-motion-y look
            for _i in range(10):
                keys[timeval] = (position[index] +
                                 (random.random() - 0.5) * jitter_amount * 1.6)
                timeval += random.random() * 0.1
            ba.animate(cmb, attr, keys, loop=True)
        cmb.connectattr('output', self.node, 'position')

    def _shift(self, position1: Tuple[float, float],
               position2: Tuple[float, float]) -> None:
        if not self.node:
            return
        cmb = ba.newnode('combine', owner=self.node, attrs={'size': 2})
        ba.animate(cmb, 'input0', {0.0: position1[0], 0.25: position2[0]})
        ba.animate(cmb, 'input1', {0.0: position1[1], 0.25: position2[1]})
        cmb.connectattr('output', self.node, 'position')
