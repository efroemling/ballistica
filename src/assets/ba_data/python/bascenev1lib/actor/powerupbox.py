# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence

DEFAULT_POWERUP_INTERVAL = 8.0


class _TouchedMessage:
    pass


class PowerupBoxFactory:
    """A collection of media and other resources used by bs.Powerups.

    Category: **Gameplay Classes**

    A single instance of this is shared between all powerups
    and can be retrieved via bs.Powerup.get_factory().
    """

    mesh: bs.Mesh
    """The bs.Mesh of the powerup box."""

    mesh_simple: bs.Mesh
    """A simpler bs.Mesh of the powerup box, for use in shadows, etc."""

    tex_bomb: bs.Texture
    """Triple-bomb powerup bs.Texture."""

    tex_punch: bs.Texture
    """Punch powerup bs.Texture."""

    tex_ice_bombs: bs.Texture
    """Ice bomb powerup bs.Texture."""

    tex_sticky_bombs: bs.Texture
    """Sticky bomb powerup bs.Texture."""

    tex_shield: bs.Texture
    """Shield powerup bs.Texture."""

    tex_impact_bombs: bs.Texture
    """Impact-bomb powerup bs.Texture."""

    tex_health: bs.Texture
    """Health powerup bs.Texture."""

    tex_land_mines: bs.Texture
    """Land-mine powerup bs.Texture."""

    tex_curse: bs.Texture
    """Curse powerup bs.Texture."""

    health_powerup_sound: bs.Sound
    """bs.Sound played when a health powerup is accepted."""

    powerup_sound: bs.Sound
    """bs.Sound played when a powerup is accepted."""

    powerdown_sound: bs.Sound
    """bs.Sound that can be used when powerups wear off."""

    powerup_material: bs.Material
    """bs.Material applied to powerup boxes."""

    powerup_accept_material: bs.Material
    """Powerups will send a bs.PowerupMessage to anything they touch
       that has this bs.Material applied."""

    _STORENAME = bs.storagename()

    def __init__(self) -> None:
        """Instantiate a PowerupBoxFactory.

        You shouldn't need to do this; call Powerup.get_factory()
        to get a shared instance.
        """
        from bascenev1 import get_default_powerup_distribution

        shared = SharedObjects.get()
        self._lastpoweruptype: str | None = None
        self.mesh = bs.getmesh('powerup')
        self.mesh_simple = bs.getmesh('powerupSimple')
        self.tex_bomb = bs.gettexture('powerupBomb')
        self.tex_punch = bs.gettexture('powerupPunch')
        self.tex_ice_bombs = bs.gettexture('powerupIceBombs')
        self.tex_sticky_bombs = bs.gettexture('powerupStickyBombs')
        self.tex_shield = bs.gettexture('powerupShield')
        self.tex_impact_bombs = bs.gettexture('powerupImpactBombs')
        self.tex_health = bs.gettexture('powerupHealth')
        self.tex_land_mines = bs.gettexture('powerupLandMines')
        self.tex_curse = bs.gettexture('powerupCurse')
        self.health_powerup_sound = bs.getsound('healthPowerup')
        self.powerup_sound = bs.getsound('powerup01')
        self.powerdown_sound = bs.getsound('powerdown01')
        self.drop_sound = bs.getsound('boxDrop')

        # Material for powerups.
        self.powerup_material = bs.Material()

        # Material for anyone wanting to accept powerups.
        self.powerup_accept_material = bs.Material()

        # Pass a powerup-touched message to applicable stuff.
        self.powerup_material.add_actions(
            conditions=('they_have_material', self.powerup_accept_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _TouchedMessage()),
            ),
        )

        # We don't wanna be picked up.
        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )

        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=('impact_sound', self.drop_sound, 0.5, 0.1),
        )

        self._powerupdist: list[str] = []
        for powerup, freq in get_default_powerup_distribution():
            for _i in range(int(freq)):
                self._powerupdist.append(powerup)

    def get_random_powerup_type(
        self,
        forcetype: str | None = None,
        excludetypes: list[str] | None = None,
    ) -> str:
        """Returns a random powerup type (string).

        See bs.Powerup.poweruptype for available type values.

        There are certain non-random aspects to this; a 'curse' powerup,
        for instance, is always followed by a 'health' powerup (to keep things
        interesting). Passing 'forcetype' forces a given returned type while
        still properly interacting with the non-random aspects of the system
        (ie: forcing a 'curse' powerup will result
        in the next powerup being health).
        """
        if excludetypes is None:
            excludetypes = []
        if forcetype:
            ptype = forcetype
        else:
            # If the last one was a curse, make this one a health to
            # provide some hope.
            if self._lastpoweruptype == 'curse':
                ptype = 'health'
            else:
                while True:
                    ptype = self._powerupdist[
                        random.randint(0, len(self._powerupdist) - 1)
                    ]
                    if ptype not in excludetypes:
                        break
        self._lastpoweruptype = ptype
        return ptype

    @classmethod
    def get(cls) -> PowerupBoxFactory:
        """Return a shared bs.PowerupBoxFactory object, creating if needed."""
        activity = bs.getactivity()
        if activity is None:
            raise bs.ContextError('No current activity.')
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = PowerupBoxFactory()
        assert isinstance(factory, PowerupBoxFactory)
        return factory


class PowerupBox(bs.Actor):
    """A box that grants a powerup.

    category: Gameplay Classes

    This will deliver a bs.PowerupMessage to anything that touches it
    which has the bs.PowerupBoxFactory.powerup_accept_material applied.
    """

    poweruptype: str
    """The string powerup type.  This can be 'triple_bombs', 'punch',
       'ice_bombs', 'impact_bombs', 'land_mines', 'sticky_bombs', 'shield',
       'health', or 'curse'."""

    node: bs.Node
    """The 'prop' bs.Node representing this box."""

    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        poweruptype: str = 'triple_bombs',
        expire: bool = True,
    ):
        """Create a powerup-box of the requested type at the given position.

        see bs.Powerup.poweruptype for valid type strings.
        """

        super().__init__()
        shared = SharedObjects.get()
        factory = PowerupBoxFactory.get()
        self.poweruptype = poweruptype
        self._powersgiven = False

        if poweruptype == 'triple_bombs':
            tex = factory.tex_bomb
        elif poweruptype == 'punch':
            tex = factory.tex_punch
        elif poweruptype == 'ice_bombs':
            tex = factory.tex_ice_bombs
        elif poweruptype == 'impact_bombs':
            tex = factory.tex_impact_bombs
        elif poweruptype == 'land_mines':
            tex = factory.tex_land_mines
        elif poweruptype == 'sticky_bombs':
            tex = factory.tex_sticky_bombs
        elif poweruptype == 'shield':
            tex = factory.tex_shield
        elif poweruptype == 'health':
            tex = factory.tex_health
        elif poweruptype == 'curse':
            tex = factory.tex_curse
        else:
            raise ValueError('invalid poweruptype: ' + str(poweruptype))

        if len(position) != 3:
            raise ValueError('expected 3 floats for position')

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'mesh': factory.mesh,
                'light_mesh': factory.mesh_simple,
                'shadow_size': 0.5,
                'color_texture': tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (factory.powerup_material, shared.object_material),
            },
        )

        # Animate in.
        curve = bs.animate(self.node, 'mesh_scale', {0: 0, 0.14: 1.6, 0.2: 1})
        bs.timer(0.2, curve.delete)

        if expire:
            bs.timer(
                DEFAULT_POWERUP_INTERVAL - 2.5,
                bs.WeakCall(self._start_flashing),
            )
            bs.timer(
                DEFAULT_POWERUP_INTERVAL - 1.0,
                bs.WeakCall(self.handlemessage, bs.DieMessage()),
            )

    def _start_flashing(self) -> None:
        if self.node:
            self.node.flashing = True

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired

        if isinstance(msg, bs.PowerupAcceptMessage):
            factory = PowerupBoxFactory.get()
            assert self.node
            if self.poweruptype == 'health':
                factory.health_powerup_sound.play(
                    3, position=self.node.position
                )

            factory.powerup_sound.play(3, position=self.node.position)
            self._powersgiven = True
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, _TouchedMessage):
            if not self._powersgiven:
                node = bs.getcollision().opposingnode
                node.handlemessage(
                    bs.PowerupMessage(self.poweruptype, sourcenode=self.node)
                )

        elif isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    bs.animate(self.node, 'mesh_scale', {0: 1, 0.1: 0})
                    bs.timer(0.1, self.node.delete)

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):
            # Don't die on punches (that's annoying).
            if msg.hit_type != 'punch':
                self.handlemessage(bs.DieMessage())
        else:
            return super().handlemessage(msg)
        return None
