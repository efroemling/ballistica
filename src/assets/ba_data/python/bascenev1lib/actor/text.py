# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Sequence


class Text(bs.Actor):
    """Text with some tricks."""

    class Transition(Enum):
        """Transition types for text."""

        FADE_IN = 'fade_in'
        IN_RIGHT = 'in_right'
        IN_LEFT = 'in_left'
        IN_BOTTOM = 'in_bottom'
        IN_BOTTOM_SLOW = 'in_bottom_slow'
        IN_TOP_SLOW = 'in_top_slow'

    class HAlign(Enum):
        """Horizontal alignment type."""

        LEFT = 'left'
        CENTER = 'center'
        RIGHT = 'right'

    class VAlign(Enum):
        """Vertical alignment type."""

        NONE = 'none'
        CENTER = 'center'

    class HAttach(Enum):
        """Horizontal attach type."""

        LEFT = 'left'
        CENTER = 'center'
        RIGHT = 'right'

    class VAttach(Enum):
        """Vertical attach type."""

        BOTTOM = 'bottom'
        CENTER = 'center'
        TOP = 'top'

    def __init__(
        self,
        text: str | bs.Lstr,
        *,
        position: tuple[float, float] = (0.0, 0.0),
        h_align: HAlign = HAlign.LEFT,
        v_align: VAlign = VAlign.NONE,
        color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
        transition: Transition | None = None,
        transition_delay: float = 0.0,
        flash: bool = False,
        v_attach: VAttach = VAttach.CENTER,
        h_attach: HAttach = HAttach.CENTER,
        scale: float = 1.0,
        transition_out_delay: float | None = None,
        maxwidth: float | None = None,
        shadow: float = 0.5,
        flatness: float = 0.0,
        vr_depth: float = 0.0,
        host_only: bool = False,
        front: bool = False,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        super().__init__()
        self.node = bs.newnode(
            'text',
            delegate=self,
            attrs={
                'text': text,
                'color': color,
                'position': position,
                'h_align': h_align.value,
                'vr_depth': vr_depth,
                'v_align': v_align.value,
                'h_attach': h_attach.value,
                'v_attach': v_attach.value,
                'shadow': shadow,
                'flatness': flatness,
                'maxwidth': 0.0 if maxwidth is None else maxwidth,
                'host_only': host_only,
                'front': front,
                'scale': scale,
            },
        )

        if transition is self.Transition.FADE_IN:
            if flash:
                raise RuntimeError(
                    'fixme: flash and fade-in currently cant both be on'
                )
            cmb = bs.newnode(
                'combine',
                owner=self.node,
                attrs={
                    'input0': color[0],
                    'input1': color[1],
                    'input2': color[2],
                    'size': 4,
                },
            )
            keys = {transition_delay: 0.0, transition_delay + 0.5: color[3]}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = color[3]
                keys[transition_delay + transition_out_delay + 0.5] = 0.0
            bs.animate(cmb, 'input3', keys)
            cmb.connectattr('output', self.node, 'color')

        if flash:
            mult = 2.0
            tm1 = 0.15
            tm2 = 0.3
            cmb = bs.newnode('combine', owner=self.node, attrs={'size': 4})
            bs.animate(
                cmb,
                'input0',
                {0.0: color[0] * mult, tm1: color[0], tm2: color[0] * mult},
                loop=True,
            )
            bs.animate(
                cmb,
                'input1',
                {0.0: color[1] * mult, tm1: color[1], tm2: color[1] * mult},
                loop=True,
            )
            bs.animate(
                cmb,
                'input2',
                {0.0: color[2] * mult, tm1: color[2], tm2: color[2] * mult},
                loop=True,
            )
            cmb.input3 = color[3]
            cmb.connectattr('output', self.node, 'color')

        cmb = self.position_combine = bs.newnode(
            'combine', owner=self.node, attrs={'size': 2}
        )

        if transition is self.Transition.IN_RIGHT:
            keys = {
                transition_delay: position[0] + 1300,
                transition_delay + 0.2: position[0],
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            bs.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_LEFT:
            keys = {
                transition_delay: position[0] - 1300,
                transition_delay + 0.2: position[0],
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[0]
                keys[transition_delay + transition_out_delay + 0.2] = (
                    position[0] - 1300.0
                )
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            bs.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_BOTTOM_SLOW:
            keys = {
                transition_delay: -100.0,
                transition_delay + 1.0: position[1],
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.2: 1.0}
            cmb.input0 = position[0]
            bs.animate(cmb, 'input1', keys)
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_BOTTOM:
            keys = {
                transition_delay: -100.0,
                transition_delay + 0.2: position[1],
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[1]
                keys[transition_delay + transition_out_delay + 0.2] = -100.0
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            cmb.input0 = position[0]
            bs.animate(cmb, 'input1', keys)
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_TOP_SLOW:
            keys = {
                transition_delay: 400.0,
                transition_delay + 3.5: position[1],
            }
            o_keys = {transition_delay: 0, transition_delay + 1.0: 1.0}
            cmb.input0 = position[0]
            bs.animate(cmb, 'input1', keys)
            bs.animate(self.node, 'opacity', o_keys)
        else:
            assert transition is self.Transition.FADE_IN or transition is None
            cmb.input0 = position[0]
            cmb.input1 = position[1]
        cmb.connectattr('output', self.node, 'position')

        # If we're transitioning out, die at the end of it.
        if transition_out_delay is not None:
            bs.timer(
                transition_delay + transition_out_delay + 1.0,
                bs.WeakCall(self.handlemessage, bs.DieMessage()),
            )

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            return None
        return super().handlemessage(msg)
