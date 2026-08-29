# Released under the MIT License. See LICENSE for details.
#
"""Provides a factory object from creating Spazzes."""

from typing import TYPE_CHECKING

import bascenev1 as bs

from bascenev1 import _classicassets
from bascenev1 import _builtinassets

from bascenev1lib.actor import spazappearance
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


class SpazFactory:
    """Wraps up media and other resources used by bs.Spaz instances.

    Generally one of these is created per bascenev1.Activity and shared
    between all spaz instances. Use bs.Spaz.get_factory() to return
    the shared factory for the current activity.
    """

    impact_sounds_medium: Sequence[bs.Sound]
    """A tuple of bs.Sound-s for when a bs.Spaz hits something kinda hard."""

    impact_sounds_hard: Sequence[bs.Sound]
    """A tuple of bs.Sound-s for when a bs.Spaz hits something really hard."""

    impact_sounds_harder: Sequence[bs.Sound]
    """A tuple of bs.Sound-s for when a bs.Spaz hits something really
       really hard."""

    single_player_death_sound: bs.Sound
    """The sound that plays for an 'important' spaz death such as in
       co-op games."""

    punch_sound_weak: bs.Sound
    """A weak punch bs.Sound."""

    punch_sound: bs.Sound
    """A standard punch bs.Sound."""

    punch_sound_strong: Sequence[bs.Sound]
    """A tuple of stronger sounding punch bs.Sounds."""

    punch_sound_stronger: bs.Sound
    """A really really strong sounding punch bs.Sound."""

    swish_sound: bs.Sound
    """A punch swish bs.Sound."""

    block_sound: bs.Sound
    """A bs.Sound for when an attack is blocked by invincibility."""

    shatter_sound: bs.Sound
    """A bs.Sound for when a frozen bs.Spaz shatters."""

    splatter_sound: bs.Sound
    """A bs.Sound for when a bs.Spaz blows up via curse."""

    spaz_material: bs.Material
    """A bs.Material applied to all of parts of a bs.Spaz."""

    roller_material: bs.Material
    """A bs.Material applied to the invisible roller ball body that
       a bs.Spaz uses for locomotion."""

    punch_material: bs.Material
    """A bs.Material applied to the 'fist' of a bs.Spaz."""

    pickup_material: bs.Material
    """A bs.Material applied to the 'grabber' body of a bs.Spaz."""

    curse_material: bs.Material
    """A bs.Material applied to a cursed bs.Spaz that triggers an explosion."""

    _STORENAME = bs.storagename()

    def _preload(self, character: str) -> None:
        """Preload media needed for a given character."""
        self.get_media(character)

    def __init__(self) -> None:
        """Instantiate a factory object."""
        # pylint: disable=cyclic-import

        plus = bs.app.plus
        assert plus is not None

        # FIXME: should probably put these somewhere common so we don't
        # have to import them from a module that imports us.
        from bascenev1lib.actor.spaz import (
            PickupMessage,
            PunchHitMessage,
            CurseExplodeMessage,
        )

        shared = SharedObjects.get()
        self.impact_sounds_medium = (
            _classicassets.audio.impact_medium.get(),
            _classicassets.audio.impact_medium2.get(),
        )
        self.impact_sounds_hard = (
            _classicassets.audio.impact_hard.get(),
            _classicassets.audio.impact_hard2.get(),
            _classicassets.audio.impact_hard3.get(),
        )
        self.impact_sounds_harder = (
            _classicassets.audio.big_impact.get(),
            _classicassets.audio.big_impact2.get(),
        )
        self.single_player_death_sound = _classicassets.audio.player_death.get()
        self.punch_sound_weak = _classicassets.audio.punch_weak01.get()
        self.punch_sound = _builtinassets.audio.punch01.get()
        self.punch_sound_strong = (
            _classicassets.audio.punch_strong01.get(),
            _classicassets.audio.punch_strong02.get(),
        )
        self.punch_sound_stronger = _classicassets.audio.super_punch.get()
        self.swish_sound = _classicassets.audio.punch_swish.get()
        self.block_sound = _classicassets.audio.block.get()
        self.shatter_sound = _classicassets.audio.shatter.get()
        self.splatter_sound = _classicassets.audio.splatter.get()
        self.spaz_material = bs.Material()
        self.roller_material = bs.Material()
        self.punch_material = bs.Material()
        self.pickup_material = bs.Material()
        self.curse_material = bs.Material()

        footing_material = shared.footing_material
        object_material = shared.object_material
        player_material = shared.player_material
        region_material = shared.region_material

        # Send footing messages to spazzes so they know when they're on
        # solid ground.
        # Eww; this probably should just be built into the spaz node.
        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )

        # Punches.
        self.punch_material.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', PunchHitMessage()),
            ),
        )

        # Pickups.
        self.pickup_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', object_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', PickupMessage()),
            ),
        )

        # Curse.
        self.curse_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', player_material),
            ),
            actions=(
                'message',
                'our_node',
                'at_connect',
                CurseExplodeMessage(),
            ),
        )

        self.foot_impact_sounds = (
            _classicassets.audio.foot_impact01.get(),
            _classicassets.audio.foot_impact02.get(),
            _classicassets.audio.foot_impact03.get(),
        )

        self.foot_skid_sound = _classicassets.audio.skid01.get()
        self.foot_roll_sound = _classicassets.audio.scamper01.get()

        self.roller_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('impact_sound', self.foot_impact_sounds, 1, 0.2),
                ('skid_sound', self.foot_skid_sound, 20, 0.3),
                ('roll_sound', self.foot_roll_sound, 20, 3.0),
            ),
        )

        self.skid_sound = _classicassets.audio.gravel_skid.get()

        self.spaz_material.add_actions(
            conditions=('they_have_material', footing_material),
            actions=(
                ('impact_sound', self.foot_impact_sounds, 20, 6),
                ('skid_sound', self.skid_sound, 2.0, 1),
                ('roll_sound', self.skid_sound, 2.0, 1),
            ),
        )

        self.shield_up_sound = _classicassets.audio.shield_up.get()
        self.shield_down_sound = _classicassets.audio.shield_down.get()
        self.shield_hit_sound = _classicassets.audio.shield_hit.get()

        # We don't want to collide with stuff we're initially overlapping
        # (unless its marked with a special region material).
        self.spaz_material.add_actions(
            conditions=(
                (
                    ('we_are_younger_than', 51),
                    'and',
                    ('they_are_different_node_than_us',),
                ),
                'and',
                ('they_dont_have_material', region_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )

        self.spaz_media: dict[str, Any] = {}

        # Lets load some basic rules.
        # (allows them to be tweaked from the master server)
        self.shield_decay_rate = plus.get_v1_account_misc_read_val('rsdr', 10.0)
        self.punch_cooldown = plus.get_v1_account_misc_read_val('rpc', 400)
        self.punch_cooldown_gloves = plus.get_v1_account_misc_read_val(
            'rpcg', 300
        )
        self.punch_power_scale = plus.get_v1_account_misc_read_val('rpp', 1.2)
        self.punch_power_scale_gloves = plus.get_v1_account_misc_read_val(
            'rppg', 1.4
        )
        self.max_shield_spillover_damage = plus.get_v1_account_misc_read_val(
            'rsms', 500
        )

    def get_style(self, character: str) -> str:
        """Return the named style for this character.

        (this influences subtle aspects of their appearance, etc)
        """
        assert bs.app.classic is not None
        return bs.app.classic.spaz_appearances[character].style

    def get_media(self, character: str) -> dict[str, Any]:
        """Return the set of media used by this variant of spaz."""
        assert bs.app.classic is not None
        char = bs.app.classic.spaz_appearances[character]
        if character not in self.spaz_media:
            media = self.spaz_media[character] = {
                'jump_sounds': [
                    spazappearance.scene_sound(s) for s in char.jump_sounds
                ],
                'attack_sounds': [
                    spazappearance.scene_sound(s) for s in char.attack_sounds
                ],
                'impact_sounds': [
                    spazappearance.scene_sound(s) for s in char.impact_sounds
                ],
                'death_sounds': [
                    spazappearance.scene_sound(s) for s in char.death_sounds
                ],
                'pickup_sounds': [
                    spazappearance.scene_sound(s) for s in char.pickup_sounds
                ],
                'fall_sounds': [
                    spazappearance.scene_sound(s) for s in char.fall_sounds
                ],
                'color_texture': spazappearance.scene_texture(
                    char.color_texture
                ),
                'color_mask_texture': spazappearance.scene_texture(
                    char.color_mask_texture
                ),
                'head_mesh': spazappearance.scene_mesh(char.head_mesh),
                'torso_mesh': spazappearance.scene_mesh(char.torso_mesh),
                'pelvis_mesh': spazappearance.scene_mesh(char.pelvis_mesh),
                'upper_arm_mesh': spazappearance.scene_mesh(
                    char.upper_arm_mesh
                ),
                'forearm_mesh': spazappearance.scene_mesh(char.forearm_mesh),
                'hand_mesh': spazappearance.scene_mesh(char.hand_mesh),
                'upper_leg_mesh': spazappearance.scene_mesh(
                    char.upper_leg_mesh
                ),
                'lower_leg_mesh': spazappearance.scene_mesh(
                    char.lower_leg_mesh
                ),
                'toes_mesh': spazappearance.scene_mesh(char.toes_mesh),
            }
        else:
            media = self.spaz_media[character]
        return media

    @classmethod
    def get(cls) -> SpazFactory:
        """Return the shared bs.SpazFactory, creating it if necessary."""
        # pylint: disable=cyclic-import
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = activity.customdata[cls._STORENAME] = SpazFactory()
        assert isinstance(factory, SpazFactory)
        return factory
