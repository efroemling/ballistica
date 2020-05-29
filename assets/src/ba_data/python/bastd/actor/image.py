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

from enum import Enum
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Tuple, Sequence, Union, Dict, Optional


class Image(ba.Actor):
    """Just a wrapped up image node with a few tricks up its sleeve."""

    class Transition(Enum):
        """Transition types we support."""
        FADE_IN = 'fade_in'
        IN_RIGHT = 'in_right'
        IN_LEFT = 'in_left'
        IN_BOTTOM = 'in_bottom'
        IN_BOTTOM_SLOW = 'in_bottom_slow'
        IN_TOP_SLOW = 'in_top_slow'

    class Attach(Enum):
        """Attach types we support."""
        CENTER = 'center'
        TOP_CENTER = 'topCenter'
        TOP_LEFT = 'topLeft'
        BOTTOM_CENTER = 'bottomCenter'

    def __init__(self,
                 texture: Union[ba.Texture, Dict[str, Any]],
                 position: Tuple[float, float] = (0, 0),
                 transition: Optional[Transition] = None,
                 transition_delay: float = 0.0,
                 attach: Attach = Attach.CENTER,
                 color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
                 scale: Tuple[float, float] = (100.0, 100.0),
                 transition_out_delay: float = None,
                 model_opaque: ba.Model = None,
                 model_transparent: ba.Model = None,
                 vr_depth: float = 0.0,
                 host_only: bool = False,
                 front: bool = False):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        super().__init__()

        # If they provided a dict as texture, assume its an icon.
        # otherwise its just a texture value itself.
        mask_texture: Optional[ba.Texture]
        if isinstance(texture, dict):
            tint_color = texture['tint_color']
            tint2_color = texture['tint2_color']
            tint_texture = texture['tint_texture']
            texture = texture['texture']
            mask_texture = ba.gettexture('characterIconMask')
        else:
            tint_color = (1, 1, 1)
            tint2_color = None
            tint_texture = None
            mask_texture = None

        self.node = ba.newnode('image',
                               attrs={
                                   'texture': texture,
                                   'tint_color': tint_color,
                                   'tint_texture': tint_texture,
                                   'position': position,
                                   'vr_depth': vr_depth,
                                   'scale': scale,
                                   'mask_texture': mask_texture,
                                   'color': color,
                                   'absolute_scale': True,
                                   'host_only': host_only,
                                   'front': front,
                                   'attach': attach.value
                               },
                               delegate=self)

        if model_opaque is not None:
            self.node.model_opaque = model_opaque
        if model_transparent is not None:
            self.node.model_transparent = model_transparent
        if tint2_color is not None:
            self.node.tint2_color = tint2_color
        if transition is self.Transition.FADE_IN:
            keys = {transition_delay: 0, transition_delay + 0.5: color[3]}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = color[3]
                keys[transition_delay + transition_out_delay + 0.5] = 0
            ba.animate(self.node, 'opacity', keys)
        cmb = self.position_combine = ba.newnode('combine',
                                                 owner=self.node,
                                                 attrs={'size': 2})
        if transition is self.Transition.IN_RIGHT:
            keys = {
                transition_delay: position[0] + 1200,
                transition_delay + 0.2: position[0]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            ba.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            ba.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_LEFT:
            keys = {
                transition_delay: position[0] - 1200,
                transition_delay + 0.2: position[0]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[0]
                keys[transition_delay + transition_out_delay +
                     200] = -position[0] - 1200
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            ba.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            ba.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_BOTTOM_SLOW:
            keys = {
                transition_delay: -400,
                transition_delay + 3.5: position[1]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 2.0: 1.0}
            cmb.input0 = position[0]
            ba.animate(cmb, 'input1', keys)
            ba.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_BOTTOM:
            keys = {
                transition_delay: -400,
                transition_delay + 0.2: position[1]
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[1]
                keys[transition_delay + transition_out_delay + 0.2] = -400
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            cmb.input0 = position[0]
            ba.animate(cmb, 'input1', keys)
            ba.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_TOP_SLOW:
            keys = {transition_delay: 400, transition_delay + 3.5: position[1]}
            o_keys = {transition_delay: 0.0, transition_delay + 1.0: 1.0}
            cmb.input0 = position[0]
            ba.animate(cmb, 'input1', keys)
            ba.animate(self.node, 'opacity', o_keys)
        else:
            assert transition is self.Transition.FADE_IN or transition is None
            cmb.input0 = position[0]
            cmb.input1 = position[1]
        cmb.connectattr('output', self.node, 'position')

        # If we're transitioning out, die at the end of it.
        if transition_out_delay is not None:
            ba.timer(transition_delay + transition_out_delay + 1.0,
                     ba.WeakCall(self.handlemessage, ba.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
            return None
        return super().handlemessage(msg)
