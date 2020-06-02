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
"""Implements respawn icon actor."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Optional, Dict, Tuple


class RespawnIcon:
    """An icon with a countdown that appears alongside the screen.

    category: Gameplay Classes

    This is used to indicate that a ba.Player is waiting to respawn.
    """

    _MASKTEXSTORENAME = ba.storagename('masktex')
    _ICONSSTORENAME = ba.storagename('icons')

    def __init__(self, player: ba.Player, respawn_time: float):
        """Instantiate with a ba.Player and respawn_time (in seconds)."""
        self._visible = True

        on_right, offs_extra, respawn_icons = self._get_context(player)

        # Cache our mask tex on the team for easy access.
        mask_tex = player.team.customdata.get(self._MASKTEXSTORENAME)
        if mask_tex is None:
            mask_tex = ba.gettexture('characterIconMask')
            player.team.customdata[self._MASKTEXSTORENAME] = mask_tex
        assert isinstance(mask_tex, ba.Texture)

        # Now find the first unused slot and use that.
        index = 0
        while (index in respawn_icons and respawn_icons[index]() is not None
               and respawn_icons[index]().visible):
            index += 1
        respawn_icons[index] = weakref.ref(self)

        offs = offs_extra + index * -53
        icon = player.get_icon()
        texture = icon['texture']
        h_offs = -10
        ipos = (-40 - h_offs if on_right else 40 + h_offs, -180 + offs)
        self._image: Optional[ba.NodeActor] = ba.NodeActor(
            ba.newnode('image',
                       attrs={
                           'texture': texture,
                           'tint_texture': icon['tint_texture'],
                           'tint_color': icon['tint_color'],
                           'tint2_color': icon['tint2_color'],
                           'mask_texture': mask_tex,
                           'position': ipos,
                           'scale': (32, 32),
                           'opacity': 1.0,
                           'absolute_scale': True,
                           'attach': 'topRight' if on_right else 'topLeft'
                       }))

        assert self._image.node
        ba.animate(self._image.node, 'opacity', {0.0: 0, 0.2: 0.7})

        npos = (-40 - h_offs if on_right else 40 + h_offs, -205 + 49 + offs)
        self._name: Optional[ba.NodeActor] = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'right' if on_right else 'left',
                           'text': ba.Lstr(value=player.getname()),
                           'maxwidth': 100,
                           'h_align': 'center',
                           'v_align': 'center',
                           'shadow': 1.0,
                           'flatness': 1.0,
                           'color': ba.safecolor(icon['tint_color']),
                           'scale': 0.5,
                           'position': npos
                       }))

        assert self._name.node
        ba.animate(self._name.node, 'scale', {0: 0, 0.1: 0.5})

        tpos = (-60 - h_offs if on_right else 60 + h_offs, -192 + offs)
        self._text: Optional[ba.NodeActor] = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'position': tpos,
                           'h_attach': 'right' if on_right else 'left',
                           'h_align': 'right' if on_right else 'left',
                           'scale': 0.9,
                           'shadow': 0.5,
                           'flatness': 0.5,
                           'v_attach': 'top',
                           'color': ba.safecolor(icon['tint_color']),
                           'text': ''
                       }))

        assert self._text.node
        ba.animate(self._text.node, 'scale', {0: 0, 0.1: 0.9})

        self._respawn_time = ba.time() + respawn_time
        self._update()
        self._timer: Optional[ba.Timer] = ba.Timer(1.0,
                                                   ba.WeakCall(self._update),
                                                   repeat=True)

    @property
    def visible(self) -> bool:
        """Is this icon still visible?"""
        return self._visible

    def _get_context(self, player: ba.Player) -> Tuple[bool, float, Dict]:
        """Return info on where we should be shown and stored."""
        activity = ba.getactivity()

        if isinstance(ba.getsession(), ba.DualTeamSession):
            on_right = player.team.id % 2 == 1

            # Store a list of icons in the team.
            icons = player.team.customdata.get(self._ICONSSTORENAME)
            if icons is None:
                player.team.customdata[self._ICONSSTORENAME] = icons = {}
            assert isinstance(icons, dict)

            offs_extra = -20
        else:
            on_right = False

            # Store a list of icons in the activity.
            icons = activity.customdata.get(self._ICONSSTORENAME)
            if icons is None:
                activity.customdata[self._ICONSSTORENAME] = icons = {}
            assert isinstance(icons, dict)

            if isinstance(activity.session, ba.FreeForAllSession):
                offs_extra = -150
            else:
                offs_extra = -20
        return on_right, offs_extra, icons

    def _update(self) -> None:
        remaining = int(round(self._respawn_time - ba.time()))
        if remaining > 0:
            assert self._text is not None
            if self._text.node:
                self._text.node.text = str(remaining)
        else:
            self._visible = False
            self._image = self._text = self._timer = self._name = None
