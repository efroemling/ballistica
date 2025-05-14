# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Sequence


class PopupText(bs.Actor):
    """Text that pops up above a position to denote something special.

    category: Gameplay Classes
    """

    def __init__(
        self,
        text: str | bs.Lstr,
        *,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
        random_offset: float = 0.5,
        offset: Sequence[float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
    ):
        """Instantiate with given values.

        random_offset is the amount of random offset from the provided position
        that will be applied. This can help multiple achievements from
        overlapping too much.
        """
        super().__init__()
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)
        pos = (
            position[0] + offset[0] + random_offset * (0.5 - random.random()),
            position[1] + offset[1] + random_offset * (0.5 - random.random()),
            position[2] + offset[2] + random_offset * (0.5 - random.random()),
        )

        self.node = bs.newnode(
            'text',
            attrs={
                'text': text,
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'h_align': 'center',
            },
            delegate=self,
        )

        lifespan = 1.5

        # scale up
        bs.animate(
            self.node,
            'scale',
            {
                0: 0.0,
                lifespan * 0.11: 0.020 * 0.7 * scale,
                lifespan * 0.16: 0.013 * 0.7 * scale,
                lifespan * 0.25: 0.014 * 0.7 * scale,
            },
        )

        # translate upward
        self._tcombine = bs.newnode(
            'combine',
            owner=self.node,
            attrs={'input0': pos[0], 'input2': pos[2], 'size': 3},
        )
        bs.animate(
            self._tcombine, 'input1', {0: pos[1] + 1.5, lifespan: pos[1] + 2.0}
        )
        self._tcombine.connectattr('output', self.node, 'position')

        # fade our opacity in/out
        self._combine = bs.newnode(
            'combine',
            owner=self.node,
            attrs={
                'input0': color[0],
                'input1': color[1],
                'input2': color[2],
                'size': 4,
            },
        )
        for i in range(4):
            bs.animate(
                self._combine,
                'input' + str(i),
                {
                    0.13 * lifespan: color[i],
                    0.18 * lifespan: 4.0 * color[i],
                    0.22 * lifespan: color[i],
                },
            )
        bs.animate(
            self._combine,
            'input3',
            {
                0: 0,
                0.1 * lifespan: color[3],
                0.7 * lifespan: color[3],
                lifespan: 0,
            },
        )
        self._combine.connectattr('output', self.node, 'color')

        # kill ourself
        self._die_timer = bs.Timer(
            lifespan, bs.WeakCall(self.handlemessage, bs.DieMessage())
        )

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            super().handlemessage(msg)
