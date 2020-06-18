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
"""Provides a factory object from creating Spazzes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.gameutils import SharedObjects
import _ba

if TYPE_CHECKING:
    from typing import Any, Dict


class SpazFactory:
    """Wraps up media and other resources used by ba.Spaz instances.

    Category: Gameplay Classes

    Generally one of these is created per ba.Activity and shared
    between all spaz instances.  Use ba.Spaz.get_factory() to return
    the shared factory for the current activity.

    Attributes:

       impact_sounds_medium
          A tuple of ba.Sounds for when a ba.Spaz hits something kinda hard.

       impact_sounds_hard
          A tuple of ba.Sounds for when a ba.Spaz hits something really hard.

       impact_sounds_harder
          A tuple of ba.Sounds for when a ba.Spaz hits something really
          really hard.

       single_player_death_sound
          The sound that plays for an 'important' spaz death such as in
          co-op games.

       punch_sound
          A standard punch ba.Sound.

       punch_sound_strong
          A tuple of stronger sounding punch ba.Sounds.

       punch_sound_stronger
          A really really strong sounding punch ba.Sound.

       swish_sound
          A punch swish ba.Sound.

       block_sound
          A ba.Sound for when an attack is blocked by invincibility.

       shatter_sound
          A ba.Sound for when a frozen ba.Spaz shatters.

       splatter_sound
          A ba.Sound for when a ba.Spaz blows up via curse.

       spaz_material
          A ba.Material applied to all of parts of a ba.Spaz.

       roller_material
          A ba.Material applied to the invisible roller ball body that
          a ba.Spaz uses for locomotion.

       punch_material
          A ba.Material applied to the 'fist' of a ba.Spaz.

       pickup_material
          A ba.Material applied to the 'grabber' body of a ba.Spaz.

       curse_material
          A ba.Material applied to a cursed ba.Spaz that triggers an explosion.
    """

    _STORENAME = ba.storagename()

    def _preload(self, character: str) -> None:
        """Preload media needed for a given character."""
        self.get_media(character)

    def __init__(self) -> None:
        """Instantiate a factory object."""
        # pylint: disable=cyclic-import
        # FIXME: should probably put these somewhere common so we don't
        # have to import them from a module that imports us.
        from bastd.actor.spaz import (PickupMessage, PunchHitMessage,
                                      CurseExplodeMessage)

        shared = SharedObjects.get()
        self.impact_sounds_medium = (ba.getsound('impactMedium'),
                                     ba.getsound('impactMedium2'))
        self.impact_sounds_hard = (ba.getsound('impactHard'),
                                   ba.getsound('impactHard2'),
                                   ba.getsound('impactHard3'))
        self.impact_sounds_harder = (ba.getsound('bigImpact'),
                                     ba.getsound('bigImpact2'))
        self.single_player_death_sound = ba.getsound('playerDeath')
        self.punch_sound = ba.getsound('punch01')
        self.punch_sound_strong = (ba.getsound('punchStrong01'),
                                   ba.getsound('punchStrong02'))
        self.punch_sound_stronger = ba.getsound('superPunch')
        self.swish_sound = ba.getsound('punchSwish')
        self.block_sound = ba.getsound('block')
        self.shatter_sound = ba.getsound('shatter')
        self.splatter_sound = ba.getsound('splatter')
        self.spaz_material = ba.Material()
        self.roller_material = ba.Material()
        self.punch_material = ba.Material()
        self.pickup_material = ba.Material()
        self.curse_material = ba.Material()

        footing_material = shared.footing_material
        object_material = shared.object_material
        player_material = shared.player_material
        region_material = shared.region_material

        # Send footing messages to spazzes so they know when they're on
        # solid ground.
        # Eww; this probably should just be built into the spaz node.
        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(('message', 'our_node', 'at_connect', 'footing', 1),
                     ('message', 'our_node', 'at_disconnect', 'footing', -1)))

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(('message', 'our_node', 'at_connect', 'footing', 1),
                     ('message', 'our_node', 'at_disconnect', 'footing', -1)))

        # Punches.
        self.punch_material.add_actions(
            conditions=('they_are_different_node_than_us', ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', PunchHitMessage()),
            ))

        # Pickups.
        self.pickup_material.add_actions(
            conditions=(('they_are_different_node_than_us', ), 'and',
                        ('they_have_material', object_material)),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', PickupMessage()),
            ))

        # Curse.
        self.curse_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us', ),
                'and',
                ('they_have_material', player_material),
            ),
            actions=('message', 'our_node', 'at_connect',
                     CurseExplodeMessage()),
        )

        self.foot_impact_sounds = (ba.getsound('footImpact01'),
                                   ba.getsound('footImpact02'),
                                   ba.getsound('footImpact03'))

        self.foot_skid_sound = ba.getsound('skid01')
        self.foot_roll_sound = ba.getsound('scamper01')

        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('impact_sound', self.foot_impact_sounds, 1, 0.2),
                ('skid_sound', self.foot_skid_sound, 20, 0.3),
                ('roll_sound', self.foot_roll_sound, 20, 3.0),
            ))

        self.skid_sound = ba.getsound('gravelSkid')

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('impact_sound', self.foot_impact_sounds, 20, 6),
                ('skid_sound', self.skid_sound, 2.0, 1),
                ('roll_sound', self.skid_sound, 2.0, 1),
            ))

        self.shield_up_sound = ba.getsound('shieldUp')
        self.shield_down_sound = ba.getsound('shieldDown')
        self.shield_hit_sound = ba.getsound('shieldHit')

        # We don't want to collide with stuff we're initially overlapping
        # (unless its marked with a special region material).
        self.spaz_material.add_actions(
            conditions=(
                (
                    ('we_are_younger_than', 51),
                    'and',
                    ('they_are_different_node_than_us', ),
                ),
                'and',
                ('they_dont_have_material', region_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )

        self.spaz_media: Dict[str, Any] = {}

        # Lets load some basic rules.
        # (allows them to be tweaked from the master server)
        self.shield_decay_rate = _ba.get_account_misc_read_val('rsdr', 10.0)
        self.punch_cooldown = _ba.get_account_misc_read_val('rpc', 400)
        self.punch_cooldown_gloves = (_ba.get_account_misc_read_val(
            'rpcg', 300))
        self.punch_power_scale = _ba.get_account_misc_read_val('rpp', 1.2)
        self.punch_power_scale_gloves = (_ba.get_account_misc_read_val(
            'rppg', 1.4))
        self.max_shield_spillover_damage = (_ba.get_account_misc_read_val(
            'rsms', 500))

    def get_style(self, character: str) -> str:
        """Return the named style for this character.

        (this influences subtle aspects of their appearance, etc)
        """
        return ba.app.spaz_appearances[character].style

    def get_media(self, character: str) -> Dict[str, Any]:
        """Return the set of media used by this variant of spaz."""
        char = ba.app.spaz_appearances[character]
        if character not in self.spaz_media:
            media = self.spaz_media[character] = {
                'jump_sounds': [ba.getsound(s) for s in char.jump_sounds],
                'attack_sounds': [ba.getsound(s) for s in char.attack_sounds],
                'impact_sounds': [ba.getsound(s) for s in char.impact_sounds],
                'death_sounds': [ba.getsound(s) for s in char.death_sounds],
                'pickup_sounds': [ba.getsound(s) for s in char.pickup_sounds],
                'fall_sounds': [ba.getsound(s) for s in char.fall_sounds],
                'color_texture': ba.gettexture(char.color_texture),
                'color_mask_texture': ba.gettexture(char.color_mask_texture),
                'head_model': ba.getmodel(char.head_model),
                'torso_model': ba.getmodel(char.torso_model),
                'pelvis_model': ba.getmodel(char.pelvis_model),
                'upper_arm_model': ba.getmodel(char.upper_arm_model),
                'forearm_model': ba.getmodel(char.forearm_model),
                'hand_model': ba.getmodel(char.hand_model),
                'upper_leg_model': ba.getmodel(char.upper_leg_model),
                'lower_leg_model': ba.getmodel(char.lower_leg_model),
                'toes_model': ba.getmodel(char.toes_model)
            }
        else:
            media = self.spaz_media[character]
        return media

    @classmethod
    def get(cls) -> SpazFactory:
        """Return the shared ba.SpazFactory, creating it if necessary."""
        # pylint: disable=cyclic-import
        activity = ba.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = SpazFactory()
        assert isinstance(factory, SpazFactory)
        return factory
