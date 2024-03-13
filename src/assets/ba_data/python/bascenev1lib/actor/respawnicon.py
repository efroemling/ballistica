# Released under the MIT License. See LICENSE for details.
#
"""Implements respawn icon actor."""

from __future__ import annotations

import weakref

import bascenev1 as bs


class RespawnIcon:
    """An icon with a countdown that appears alongside the screen.

    category: Gameplay Classes

    This is used to indicate that a bascenev1.Player is waiting to respawn.
    """

    _MASKTEXSTORENAME = bs.storagename('masktex')
    _ICONSSTORENAME = bs.storagename('icons')

    def __init__(self, player: bs.Player, respawn_time: float):
        """Instantiate with a Player and respawn_time (in seconds)."""
        # pylint: disable=too-many-locals
        self._visible = True
        self._dots_epic_only = False

        on_right, offs_extra, respawn_icons = self._get_context(player)

        # Cache our mask tex on the team for easy access.
        mask_tex = player.team.customdata.get(self._MASKTEXSTORENAME)
        if mask_tex is None:
            mask_tex = bs.gettexture('characterIconMask')
            player.team.customdata[self._MASKTEXSTORENAME] = mask_tex
        assert isinstance(mask_tex, bs.Texture)

        # Now find the first unused slot and use that.
        index = 0
        while (
            index in respawn_icons
            and respawn_icons[index]() is not None
            and respawn_icons[index]().visible
        ):
            index += 1
        respawn_icons[index] = weakref.ref(self)

        offs = offs_extra + index * -53
        icon = player.get_icon()
        texture = icon['texture']
        h_offs = -10
        ipos = (-40 - h_offs if on_right else 40 + h_offs, -180 + offs)
        self._image: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'image',
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
                    'attach': 'topRight' if on_right else 'topLeft',
                },
            )
        )

        assert self._image.node
        bs.animate(self._image.node, 'opacity', {0.0: 0, 0.2: 0.7})

        npos = (-40 - h_offs if on_right else 40 + h_offs, -205 + 49 + offs)
        self._name: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'right' if on_right else 'left',
                    'text': bs.Lstr(value=player.getname()),
                    'maxwidth': 100,
                    'h_align': 'center',
                    'v_align': 'center',
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': bs.safecolor(icon['tint_color']),
                    'scale': 0.5,
                    'position': npos,
                },
            )
        )

        assert self._name.node
        bs.animate(self._name.node, 'scale', {0: 0, 0.1: 0.5})

        tpos = (-60 - h_offs if on_right else 60 + h_offs, -193 + offs)
        self._text: bs.NodeActor | None = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'position': tpos,
                    'h_attach': 'right' if on_right else 'left',
                    'h_align': 'right' if on_right else 'left',
                    'scale': 0.9,
                    'shadow': 0.5,
                    'flatness': 0.5,
                    'v_attach': 'top',
                    'color': bs.safecolor(icon['tint_color']),
                    'text': '',
                },
            )
        )
        dpos = [ipos[0] + (7 if on_right else -7), ipos[1] - 16]
        self._dec_text: bs.NodeActor | None = None
        if (
            self._dots_epic_only
            and bs.getactivity().globalsnode.slow_motion
            or not self._dots_epic_only
        ):
            self._dec_text = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'position': dpos,
                        'h_attach': 'right' if on_right else 'left',
                        'h_align': 'right' if on_right else 'left',
                        'scale': 0.65,
                        'shadow': 0.5,
                        'flatness': 0.5,
                        'v_attach': 'top',
                        'color': bs.safecolor(icon['tint_color']),
                        'text': '',
                    },
                )
            )

        assert self._text.node
        bs.animate(self._text.node, 'scale', {0: 0, 0.1: 0.9})
        if self._dec_text:
            bs.animate(self._dec_text.node, 'scale', {0: 0, 0.1: 0.65})

        self._respawn_time = bs.time() + respawn_time
        self._dec_timer: bs.Timer | None = None
        self._update()
        self._timer: bs.Timer | None = bs.Timer(
            1.0, bs.WeakCall(self._update), repeat=True
        )

    @property
    def visible(self) -> bool:
        """Is this icon still visible?"""
        return self._visible

    def _get_context(self, player: bs.Player) -> tuple[bool, float, dict]:
        """Return info on where we should be shown and stored."""
        activity = bs.getactivity()

        if isinstance(activity.session, bs.DualTeamSession):
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

            if isinstance(activity.session, bs.FreeForAllSession):
                offs_extra = -150
            else:
                offs_extra = -20
        return on_right, offs_extra, icons

    def _dec_step(self, display: list) -> None:
        if not self._dec_text:
            self._dec_timer = None
            return
        old_text: bs.Lstr | str = self._dec_text.node.text
        iterate: int
        # Get the following display text using our current one.
        try:
            iterate = display.index(old_text) + 1
        # If we don't match any in the display list, we
        # can assume we've just started iterating.
        except ValueError:
            iterate = 0
        # Kill the timer if we're at the last iteration.
        if iterate >= len(display):
            self._dec_timer = None
            return
        self._dec_text.node.text = display[iterate]

    def _update(self) -> None:
        remaining = int(round(self._respawn_time - bs.time()))

        if remaining > 0:
            assert self._text is not None
            if self._text.node:
                self._text.node.text = str(remaining)
                if self._dec_text:
                    # Display our decimal dots.
                    self._dec_text.node.text = '...'
                    # Start the timer to tick down.
                    self._dec_timer = bs.Timer(
                        0.25,
                        bs.WeakCall(self._dec_step, ['..', '.', '']),
                        repeat=True,
                    )
        else:
            self._visible = False
            self._image = self._text = self._dec_text = self._timer = (
                self._name
            ) = None
