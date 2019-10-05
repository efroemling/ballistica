"""Defines Actor(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Union, Tuple, Sequence


class Text(ba.Actor):
    """ Text with some tricks """

    def __init__(self,
                 text: Union[str, ba.Lstr],
                 position: Tuple[float, float] = (0.0, 0.0),
                 h_align: str = 'left',
                 v_align: str = 'none',
                 color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
                 transition: str = None,
                 transition_delay: float = 0.0,
                 flash: bool = False,
                 v_attach: str = 'center',
                 h_attach: str = 'center',
                 scale: float = 1.0,
                 transition_out_delay: float = None,
                 maxwidth: float = None,
                 shadow: float = 0.5,
                 flatness: float = 0.0,
                 vr_depth: float = 0.0,
                 host_only: bool = False,
                 front: bool = False):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        super().__init__()
        self.node = ba.newnode(
            'text',
            delegate=self,
            attrs={
                'text': text,
                'color': color,
                'position': position,
                'h_align': h_align,
                'vr_depth': vr_depth,
                'v_align': v_align,
                'h_attach': h_attach,
                'v_attach': v_attach,
                'shadow': shadow,
                'flatness': flatness,
                'maxwidth': 0.0 if maxwidth is None else maxwidth,
                'host_only': host_only,
                'front': front,
                'scale': scale
            })

        if transition == 'fade_in':
            if flash:
                raise Exception("fixme: flash and fade-in"
                                " currently cant both be on")
            cmb = ba.newnode('combine',
                             owner=self.node,
                             attrs={
                                 'input0': color[0],
                                 'input1': color[1],
                                 'input2': color[2],
                                 'size': 4
                             })
            keys = {transition_delay: 0.0, transition_delay + 0.5: color[3]}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = color[3]
                keys[transition_delay + transition_out_delay + 0.5] = 0.0
            ba.animate(cmb, "input3", keys)
            cmb.connectattr('output', self.node, 'color')

        if flash:
            mult = 2.0
            tm1 = 0.15
            tm2 = 0.3
            cmb = ba.newnode('combine', owner=self.node, attrs={'size': 4})
            ba.animate(cmb,
                       "input0", {
                           0.0: color[0] * mult,
                           tm1: color[0],
                           tm2: color[0] * mult
                       },
                       loop=True)
            ba.animate(cmb,
                       "input1", {
                           0.0: color[1] * mult,
                           tm1: color[1],
                           tm2: color[1] * mult
                       },
                       loop=True)
            ba.animate(cmb,
                       "input2", {
                           0.0: color[2] * mult,
                           tm1: color[2],
                           tm2: color[2] * mult
                       },
                       loop=True)
            cmb.input3 = color[3]
            cmb.connectattr('output', self.node, 'color')

        cmb = self.position_combine = ba.newnode('combine',
                                                 owner=self.node,
                                                 attrs={'size': 2})
        if transition == 'in_right':
            keys = {
                transition_delay: position[0] + 1.3,
                transition_delay + 0.2: position[0]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            ba.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            ba.animate(self.node, 'opacity', o_keys)
        elif transition == 'in_left':
            keys = {
                transition_delay: position[0] - 1.3,
                transition_delay + 0.2: position[0]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[0]
                keys[transition_delay + transition_out_delay +
                     0.2] = position[0] - 1300.0
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            ba.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            ba.animate(self.node, 'opacity', o_keys)
        elif transition == 'in_bottom_slow':
            keys = {
                transition_delay: -100.0,
                transition_delay + 1.0: position[1]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.2: 1.0}
            cmb.input0 = position[0]
            ba.animate(cmb, 'input1', keys)
            ba.animate(self.node, 'opacity', o_keys)
        elif transition == 'in_bottom':
            keys = {
                transition_delay: -100.0,
                transition_delay + 0.2: position[1]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[1]
                keys[transition_delay + transition_out_delay + 0.2] = -100.0
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            cmb.input0 = position[0]
            ba.animate(cmb, 'input1', keys)
            ba.animate(self.node, 'opacity', o_keys)
        elif transition == 'inTopSlow':
            keys = {transition_delay: 0.4, transition_delay + 3.5: position[1]}
            o_keys = {transition_delay: 0.0, transition_delay + 1.0: 1.0}
            cmb.input0 = position[0]
            ba.animate(cmb, 'input1', keys)
            ba.animate(self.node, 'opacity', o_keys)
        else:
            cmb.input0 = position[0]
            cmb.input1 = position[1]
        cmb.connectattr('output', self.node, 'position')

        # if we're transitioning out, die at the end of it
        if transition_out_delay is not None:
            ba.timer(transition_delay + transition_out_delay + 1.0,
                     ba.WeakCall(self.handlemessage, ba.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        if __debug__ is True:
            self._handlemessage_sanity_check()
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
            return None
        return super().handlemessage(msg)
