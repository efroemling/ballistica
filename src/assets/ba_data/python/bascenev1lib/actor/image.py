# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Sequence


class Image(bs.Actor):
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

    def __init__(
        self,
        texture: bs.Texture | dict[str, Any],
        *,
        position: tuple[float, float] = (0, 0),
        transition: Transition | None = None,
        transition_delay: float = 0.0,
        attach: Attach = Attach.CENTER,
        color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
        scale: tuple[float, float] = (100.0, 100.0),
        transition_out_delay: float | None = None,
        mesh_opaque: bs.Mesh | None = None,
        mesh_transparent: bs.Mesh | None = None,
        vr_depth: float = 0.0,
        host_only: bool = False,
        front: bool = False,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        super().__init__()

        # If they provided a dict as texture, use it to wire up extended
        # stuff like tints and masks.
        mask_texture: bs.Texture | None
        if isinstance(texture, dict):
            tint_color = texture['tint_color']
            tint2_color = texture['tint2_color']
            tint_texture = texture['tint_texture']

            # Assume we're dealing with a character icon but allow
            # overriding.
            mask_tex_name = texture.get('mask_texture', 'characterIconMask')
            mask_texture = (
                None if mask_tex_name is None else bs.gettexture(mask_tex_name)
            )
            texture = texture['texture']
        else:
            tint_color = (1, 1, 1)
            tint2_color = None
            tint_texture = None
            mask_texture = None

        self.node = bs.newnode(
            'image',
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
                'attach': attach.value,
            },
            delegate=self,
        )

        if mesh_opaque is not None:
            self.node.mesh_opaque = mesh_opaque
        if mesh_transparent is not None:
            self.node.mesh_transparent = mesh_transparent
        if tint2_color is not None:
            self.node.tint2_color = tint2_color
        if transition is self.Transition.FADE_IN:
            keys = {transition_delay: 0, transition_delay + 0.5: color[3]}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = color[3]
                keys[transition_delay + transition_out_delay + 0.5] = 0
            bs.animate(self.node, 'opacity', keys)
        cmb = self.position_combine = bs.newnode(
            'combine', owner=self.node, attrs={'size': 2}
        )
        if transition is self.Transition.IN_RIGHT:
            keys = {
                transition_delay: position[0] + 1200,
                transition_delay + 0.2: position[0],
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            bs.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_LEFT:
            keys = {
                transition_delay: position[0] - 1200,
                transition_delay + 0.2: position[0],
            }
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[0]
                keys[transition_delay + transition_out_delay + 200] = (
                    -position[0] - 1200
                )
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            bs.animate(cmb, 'input0', keys)
            cmb.input1 = position[1]
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_BOTTOM_SLOW:
            keys = {transition_delay: -400, transition_delay + 3.5: position[1]}
            o_keys = {transition_delay: 0.0, transition_delay + 2.0: 1.0}
            cmb.input0 = position[0]
            bs.animate(cmb, 'input1', keys)
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_BOTTOM:
            keys = {transition_delay: -400, transition_delay + 0.2: position[1]}
            o_keys = {transition_delay: 0.0, transition_delay + 0.05: 1.0}
            if transition_out_delay is not None:
                keys[transition_delay + transition_out_delay] = position[1]
                keys[transition_delay + transition_out_delay + 0.2] = -400
                o_keys[transition_delay + transition_out_delay + 0.15] = 1.0
                o_keys[transition_delay + transition_out_delay + 0.2] = 0.0
            cmb.input0 = position[0]
            bs.animate(cmb, 'input1', keys)
            bs.animate(self.node, 'opacity', o_keys)
        elif transition is self.Transition.IN_TOP_SLOW:
            keys = {transition_delay: 400, transition_delay + 3.5: position[1]}
            o_keys = {transition_delay: 0.0, transition_delay + 1.0: 1.0}
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
