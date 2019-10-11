# Copyright (c) 2011-2019 Eric Froemling
"""Implements respawn icon actor."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Optional


class RespawnIcon:
    """An icon with a countdown that appears alongside the screen.

    category: Gameplay Classes

    This is used to indicate that a ba.Player is waiting to respawn.
    """

    def __init__(self, player: ba.Player, respawn_time: float):
        """
        Instantiate with a given ba.Player and respawn_time (in seconds)
        """
        # FIXME; tidy up
        # pylint: disable=too-many-locals
        activity = ba.getactivity()
        self._visible = True
        if isinstance(ba.getsession(), ba.TeamsSession):
            on_right = player.team.get_id() % 2 == 1
            # store a list of icons in the team
            try:
                respawn_icons = (
                    player.team.gamedata['_spaz_respawn_icons_right'])
            except Exception:
                respawn_icons = (
                    player.team.gamedata['_spaz_respawn_icons_right']) = {}
            offs_extra = -20
        else:
            on_right = False
            # Store a list of icons in the activity.
            # FIXME: Need an elegant way to store our
            #  shared stuff with the activity.
            try:
                respawn_icons = activity.spaz_respawn_icons_right
            except Exception:
                respawn_icons = activity.spaz_respawn_icons_right = {}
            if isinstance(activity.session, ba.FreeForAllSession):
                offs_extra = -150
            else:
                offs_extra = -20

        try:
            mask_tex = (player.team.gamedata['_spaz_respawn_icons_mask_tex'])
        except Exception:
            mask_tex = player.team.gamedata['_spaz_respawn_icons_mask_tex'] = (
                ba.gettexture('characterIconMask'))

        # now find the first unused slot and use that
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
        self._image: Optional[ba.Actor] = ba.Actor(
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
        self._name: Optional[ba.Actor] = ba.Actor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'right' if on_right else 'left',
                           'text': ba.Lstr(value=player.get_name()),
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
        self._text: Optional[ba.Actor] = ba.Actor(
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

    def _update(self) -> None:
        remaining = int(
            round(self._respawn_time -
                  ba.time(timeformat=ba.TimeFormat.MILLISECONDS)) / 1000.0)
        if remaining > 0:
            assert self._text is not None
            if self._text.node:
                self._text.node.text = str(remaining)
        else:
            self._clear()

    def _clear(self) -> None:
        self._visible = False
        self._image = self._text = self._timer = self._name = None
