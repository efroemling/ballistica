# Released under the MIT License. See LICENSE for details.
#
"""Provides tip related Actor(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class TipsText(bs.Actor):
    """A bit of text showing various helpful game tips."""

    def __init__(self, offs_y: float = 100.0):
        super().__init__()
        self._tip_scale = 0.8
        self._tip_title_scale = 1.1
        self._offs_y = offs_y
        self.node = bs.newnode(
            'text',
            delegate=self,
            attrs={
                'text': '',
                'scale': self._tip_scale,
                'h_align': 'left',
                'maxwidth': 800,
                'vr_depth': -20,
                'v_align': 'center',
                'v_attach': 'bottom',
            },
        )
        tval = bs.Lstr(
            value='${A}:', subs=[('${A}', bs.Lstr(resource='tipText'))]
        )
        self.title_node = bs.newnode(
            'text',
            delegate=self,
            attrs={
                'text': tval,
                'scale': self._tip_title_scale,
                'maxwidth': 122,
                'h_align': 'right',
                'vr_depth': -20,
                'v_align': 'center',
                'v_attach': 'bottom',
            },
        )
        self._message_duration = 10000
        self._message_spacing = 3000
        self._change_timer = bs.Timer(
            0.001 * (self._message_duration + self._message_spacing),
            bs.WeakCall(self.change_phrase),
            repeat=True,
        )
        self._combine = bs.newnode(
            'combine',
            owner=self.node,
            attrs={'input0': 1.0, 'input1': 0.8, 'input2': 1.0, 'size': 4},
        )
        self._combine.connectattr('output', self.node, 'color')
        self._combine.connectattr('output', self.title_node, 'color')
        self.change_phrase()

    def change_phrase(self) -> None:
        """Switch the visible tip phrase."""
        from babase import get_remote_app_name

        next_tip = bs.Lstr(
            translate=(
                'tips',
                (
                    bs.app.classic.get_next_tip()
                    if bs.app.classic is not None
                    else ''
                ),
            ),
            subs=[('${REMOTE_APP_NAME}', get_remote_app_name())],
        )
        spc = self._message_spacing
        assert self.node
        self.node.position = (-200, self._offs_y)
        self.title_node.position = (-220, self._offs_y + 3)
        keys = {
            spc: 0,
            spc + 1000: 1.0,
            spc + self._message_duration - 1000: 1.0,
            spc + self._message_duration: 0.0,
        }
        bs.animate(
            self._combine,
            'input3',
            {k / 1000.0: v * 0.5 for k, v in list(keys.items())},
        )
        self.node.text = next_tip

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            self.title_node.delete()
            return None
        return super().handlemessage(msg)
