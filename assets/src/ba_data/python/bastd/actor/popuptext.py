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
"""Defines Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Union, Sequence


class PopupText(ba.Actor):
    """Text that pops up above a position to denote something special.

    category: Gameplay Classes
    """

    def __init__(self,
                 text: Union[str, ba.Lstr],
                 position: Sequence[float] = (0.0, 0.0, 0.0),
                 color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
                 random_offset: float = 0.5,
                 offset: Sequence[float] = (0.0, 0.0, 0.0),
                 scale: float = 1.0):
        """Instantiate with given values.

        random_offset is the amount of random offset from the provided position
        that will be applied. This can help multiple achievements from
        overlapping too much.
        """
        super().__init__()
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)
        pos = (position[0] + offset[0] + random_offset *
               (0.5 - random.random()), position[1] + offset[0] +
               random_offset * (0.5 - random.random()), position[2] +
               offset[0] + random_offset * (0.5 - random.random()))

        self.node = ba.newnode('text',
                               attrs={
                                   'text': text,
                                   'in_world': True,
                                   'shadow': 1.0,
                                   'flatness': 1.0,
                                   'h_align': 'center'
                               },
                               delegate=self)

        lifespan = 1.5

        # scale up
        ba.animate(
            self.node, 'scale', {
                0: 0.0,
                lifespan * 0.11: 0.020 * 0.7 * scale,
                lifespan * 0.16: 0.013 * 0.7 * scale,
                lifespan * 0.25: 0.014 * 0.7 * scale
            })

        # translate upward
        self._tcombine = ba.newnode('combine',
                                    owner=self.node,
                                    attrs={
                                        'input0': pos[0],
                                        'input2': pos[2],
                                        'size': 3
                                    })
        ba.animate(self._tcombine, 'input1', {
            0: pos[1] + 1.5,
            lifespan: pos[1] + 2.0
        })
        self._tcombine.connectattr('output', self.node, 'position')

        # fade our opacity in/out
        self._combine = ba.newnode('combine',
                                   owner=self.node,
                                   attrs={
                                       'input0': color[0],
                                       'input1': color[1],
                                       'input2': color[2],
                                       'size': 4
                                   })
        for i in range(4):
            ba.animate(
                self._combine, 'input' + str(i), {
                    0.13 * lifespan: color[i],
                    0.18 * lifespan: 4.0 * color[i],
                    0.22 * lifespan: color[i]
                })
        ba.animate(self._combine, 'input3', {
            0: 0,
            0.1 * lifespan: color[3],
            0.7 * lifespan: color[3],
            lifespan: 0
        })
        self._combine.connectattr('output', self.node, 'color')

        # kill ourself
        self._die_timer = ba.Timer(
            lifespan, ba.WeakCall(self.handlemessage, ba.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
        else:
            super().handlemessage(msg)
