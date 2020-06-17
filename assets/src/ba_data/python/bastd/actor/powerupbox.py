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

import random
from typing import TYPE_CHECKING

import ba
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import List, Any, Optional, Sequence

DEFAULT_POWERUP_INTERVAL = 8.0


class _TouchedMessage:
    pass


class PowerupBoxFactory:
    """A collection of media and other resources used by ba.Powerups.

    category: Gameplay Classes

    A single instance of this is shared between all powerups
    and can be retrieved via ba.Powerup.get_factory().

    Attributes:

       model
          The ba.Model of the powerup box.

       model_simple
          A simpler ba.Model of the powerup box, for use in shadows, etc.

       tex_bomb
          Triple-bomb powerup ba.Texture.

       tex_punch
          Punch powerup ba.Texture.

       tex_ice_bombs
          Ice bomb powerup ba.Texture.

       tex_sticky_bombs
          Sticky bomb powerup ba.Texture.

       tex_shield
          Shield powerup ba.Texture.

       tex_impact_bombs
          Impact-bomb powerup ba.Texture.

       tex_health
          Health powerup ba.Texture.

       tex_land_mines
          Land-mine powerup ba.Texture.

       tex_curse
          Curse powerup ba.Texture.

       health_powerup_sound
          ba.Sound played when a health powerup is accepted.

       powerup_sound
          ba.Sound played when a powerup is accepted.

       powerdown_sound
          ba.Sound that can be used when powerups wear off.

       powerup_material
          ba.Material applied to powerup boxes.

       powerup_accept_material
          Powerups will send a ba.PowerupMessage to anything they touch
          that has this ba.Material applied.
    """

    _STORENAME = ba.storagename()

    def __init__(self) -> None:
        """Instantiate a PowerupBoxFactory.

        You shouldn't need to do this; call ba.Powerup.get_factory()
        to get a shared instance.
        """
        from ba.internal import get_default_powerup_distribution
        shared = SharedObjects.get()
        self._lastpoweruptype: Optional[str] = None
        self.model = ba.getmodel('powerup')
        self.model_simple = ba.getmodel('powerupSimple')
        self.tex_bomb = ba.gettexture('powerupBomb')
        self.tex_punch = ba.gettexture('powerupPunch')
        self.tex_ice_bombs = ba.gettexture('powerupIceBombs')
        self.tex_sticky_bombs = ba.gettexture('powerupStickyBombs')
        self.tex_shield = ba.gettexture('powerupShield')
        self.tex_impact_bombs = ba.gettexture('powerupImpactBombs')
        self.tex_health = ba.gettexture('powerupHealth')
        self.tex_land_mines = ba.gettexture('powerupLandMines')
        self.tex_curse = ba.gettexture('powerupCurse')
        self.health_powerup_sound = ba.getsound('healthPowerup')
        self.powerup_sound = ba.getsound('powerup01')
        self.powerdown_sound = ba.getsound('powerdown01')
        self.drop_sound = ba.getsound('boxDrop')

        # Material for powerups.
        self.powerup_material = ba.Material()

        # Material for anyone wanting to accept powerups.
        self.powerup_accept_material = ba.Material()

        # Pass a powerup-touched message to applicable stuff.
        self.powerup_material.add_actions(
            conditions=('they_have_material', self.powerup_accept_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _TouchedMessage()),
            ))

        # We don't wanna be picked up.
        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )

        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=('impact_sound', self.drop_sound, 0.5, 0.1),
        )

        self._powerupdist: List[str] = []
        for powerup, freq in get_default_powerup_distribution():
            for _i in range(int(freq)):
                self._powerupdist.append(powerup)

    def get_random_powerup_type(self,
                                forcetype: str = None,
                                excludetypes: List[str] = None) -> str:
        """Returns a random powerup type (string).

        See ba.Powerup.poweruptype for available type values.

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
                    ptype = self._powerupdist[random.randint(
                        0,
                        len(self._powerupdist) - 1)]
                    if ptype not in excludetypes:
                        break
        self._lastpoweruptype = ptype
        return ptype

    @classmethod
    def get(cls) -> PowerupBoxFactory:
        """Return a shared ba.PowerupBoxFactory object, creating if needed."""
        activity = ba.getactivity()
        if activity is None:
            raise ba.ContextError('No current activity.')
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = PowerupBoxFactory()
        assert isinstance(factory, PowerupBoxFactory)
        return factory


class PowerupBox(ba.Actor):
    """A box that grants a powerup.

    category: Gameplay Classes

    This will deliver a ba.PowerupMessage to anything that touches it
    which has the ba.PowerupBoxFactory.powerup_accept_material applied.

    Attributes:

       poweruptype
          The string powerup type.  This can be 'triple_bombs', 'punch',
          'ice_bombs', 'impact_bombs', 'land_mines', 'sticky_bombs', 'shield',
          'health', or 'curse'.

       node
          The 'prop' ba.Node representing this box.
    """

    def __init__(self,
                 position: Sequence[float] = (0.0, 1.0, 0.0),
                 poweruptype: str = 'triple_bombs',
                 expire: bool = True):
        """Create a powerup-box of the requested type at the given position.

        see ba.Powerup.poweruptype for valid type strings.
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

        self.node = ba.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'model': factory.model,
                'light_model': factory.model_simple,
                'shadow_size': 0.5,
                'color_texture': tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (factory.powerup_material,
                              shared.object_material)
            })  # yapf: disable

        # Animate in.
        curve = ba.animate(self.node, 'model_scale', {0: 0, 0.14: 1.6, 0.2: 1})
        ba.timer(0.2, curve.delete)

        if expire:
            ba.timer(DEFAULT_POWERUP_INTERVAL - 2.5,
                     ba.WeakCall(self._start_flashing))
            ba.timer(DEFAULT_POWERUP_INTERVAL - 1.0,
                     ba.WeakCall(self.handlemessage, ba.DieMessage()))

    def _start_flashing(self) -> None:
        if self.node:
            self.node.flashing = True

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired

        if isinstance(msg, ba.PowerupAcceptMessage):
            factory = PowerupBoxFactory.get()
            assert self.node
            if self.poweruptype == 'health':
                ba.playsound(factory.health_powerup_sound,
                             3,
                             position=self.node.position)
            ba.playsound(factory.powerup_sound, 3, position=self.node.position)
            self._powersgiven = True
            self.handlemessage(ba.DieMessage())

        elif isinstance(msg, _TouchedMessage):
            if not self._powersgiven:
                node = ba.getcollision().opposingnode
                node.handlemessage(
                    ba.PowerupMessage(self.poweruptype, sourcenode=self.node))

        elif isinstance(msg, ba.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    ba.animate(self.node, 'model_scale', {0: 1, 0.1: 0})
                    ba.timer(0.1, self.node.delete)

        elif isinstance(msg, ba.OutOfBoundsMessage):
            self.handlemessage(ba.DieMessage())

        elif isinstance(msg, ba.HitMessage):
            # Don't die on punches (that's annoying).
            if msg.hit_type != 'punch':
                self.handlemessage(ba.DieMessage())
        else:
            return super().handlemessage(msg)
        return None
