# Released under the MIT License. See LICENSE for details.
#
"""Defines some standard message objects for use with handlemessage() calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from enum import Enum

import babase

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from typing import Sequence, Any

    # from _bascenev1 import Node
    # from bascenev1._player import Player

    import bascenev1


class _UnhandledType:
    pass


# A special value that should be returned from handlemessage()
# functions for unhandled message types.  This may result
# in fallback message types being attempted/etc.
UNHANDLED = _UnhandledType()


@dataclass
class OutOfBoundsMessage:
    """A message telling an object that it is out of bounds."""


class DeathType(Enum):
    """A reason for a death."""

    GENERIC = 'generic'
    OUT_OF_BOUNDS = 'out_of_bounds'
    IMPACT = 'impact'
    FALL = 'fall'
    REACHED_GOAL = 'reached_goal'
    LEFT_GAME = 'left_game'


@dataclass
class DieMessage:
    """A message telling an object to die.

    Most bascenev1.Actor-s respond to this.
    """

    #: If this is set to True, the actor should disappear immediately.
    #: This is for 'removing' stuff from the game more so than 'killing'
    #: it. If False, the actor should die a 'normal' death and can take
    #: its time with lingering corpses, sound effects, etc.
    immediate: bool = False

    #: The particular reason for death.
    how: DeathType = DeathType.GENERIC


class PlayerDiedMessage:
    """A message saying a bascenev1.Player has died."""

    killed: bool
    """If True, the player was killed;
       If False, they left the game or the round ended."""

    how: DeathType
    """The particular type of death."""

    def __init__(
        self,
        player: bascenev1.Player,
        was_killed: bool,
        killerplayer: bascenev1.Player | None,
        how: DeathType,
    ):
        """Instantiate a message with the given values."""

        # Invalid refs should never be passed as args.
        assert player.exists()
        self._player = player

        # Invalid refs should never be passed as args.
        assert killerplayer is None or killerplayer.exists()
        self._killerplayer = killerplayer
        self.killed = was_killed
        self.how = how

    def getkillerplayer[PlayerT: bascenev1.Player](
        self, playertype: type[PlayerT]
    ) -> PlayerT | None:
        """Return the bascenev1.Player responsible for the killing, if any.

        Pass the Player type being used by the current game.
        """
        assert isinstance(self._killerplayer, (playertype, type(None)))
        return self._killerplayer

    def getplayer[PlayerT: bascenev1.Player](
        self, playertype: type[PlayerT]
    ) -> PlayerT:
        """Return the bascenev1.Player that died.

        The type of player for the current activity should be passed so that
        the type-checker properly identifies the returned value as one.
        """
        player: Any = self._player
        assert isinstance(player, playertype)

        # We should never be delivering invalid refs.
        # (could theoretically happen if someone holds on to us)
        assert player.exists()
        return player


@dataclass
class StandMessage:
    """A message telling an object to move to a position in space.

    Used when teleporting players to home base, etc.
    """

    position: Sequence[float] = (0.0, 0.0, 0.0)
    """Where to move to."""

    angle: float = 0.0
    """The angle to face (in degrees)"""


@dataclass
class PickUpMessage:
    """Tells an object that it has picked something up."""

    node: bascenev1.Node
    """The bascenev1.Node that is getting picked up."""


@dataclass
class DropMessage:
    """Tells an object that it has dropped what it was holding."""


@dataclass
class PickedUpMessage:
    """Tells an object that it has been picked up by something."""

    node: bascenev1.Node
    """The bascenev1.Node doing the picking up."""


@dataclass
class DroppedMessage:
    """Tells an object that it has been dropped."""

    node: bascenev1.Node
    """The bascenev1.Node doing the dropping."""


@dataclass
class ShouldShatterMessage:
    """Tells an object that it should shatter."""


@dataclass
class ImpactDamageMessage:
    """Tells an object that it has been jarred violently."""

    intensity: float
    """The intensity of the impact."""


@dataclass
class FreezeMessage:
    """Tells an object to become frozen.

    As seen in the effects of an ice bascenev1.Bomb.
    """

    time: float = 5.0
    """The amount of time the object will be frozen."""


@dataclass
class ThawMessage:
    """Tells an object to stop being frozen."""


@dataclass
class CelebrateMessage:
    """Tells an object to celebrate."""

    duration: float = 10.0
    """Amount of time to celebrate in seconds."""


class HitMessage:
    """Tells an object it has been hit in some way.

    This is used by punches, explosions, etc to convey their effect to a
    target.
    """

    def __init__(
        self,
        *,
        srcnode: bascenev1.Node | None = None,
        pos: Sequence[float] | None = None,
        velocity: Sequence[float] | None = None,
        magnitude: float = 1.0,
        velocity_magnitude: float = 0.0,
        radius: float = 1.0,
        source_player: bascenev1.Player | None = None,
        kick_back: float = 1.0,
        flat_damage: float | None = None,
        hit_type: str = 'generic',
        force_direction: Sequence[float] | None = None,
        hit_subtype: str = 'default',
    ):
        """Instantiate a message with given values."""

        self.srcnode = srcnode
        self.pos = pos if pos is not None else babase.Vec3()
        self.velocity = velocity if velocity is not None else babase.Vec3()
        self.magnitude = magnitude
        self.velocity_magnitude = velocity_magnitude
        self.radius = radius

        # We should not be getting passed an invalid ref.
        assert source_player is None or source_player.exists()
        self._source_player = source_player
        self.kick_back = kick_back
        self.flat_damage = flat_damage
        self.hit_type = hit_type
        self.hit_subtype = hit_subtype
        self.force_direction = (
            force_direction if force_direction is not None else velocity
        )

    def get_source_player[PlayerT: bascenev1.Player](
        self, playertype: type[PlayerT]
    ) -> PlayerT | None:
        """Return the source-player if one exists and is the provided type."""
        player: Any = self._source_player

        # We should not be delivering invalid refs.
        # (we could translate to None here but technically we are changing
        # the message delivered which seems wrong)
        assert player is None or player.exists()

        # Return the player *only* if they're the type given.
        return player if isinstance(player, playertype) else None


@dataclass
class PlayerProfilesChangedMessage:
    """Signals player profiles may have changed and should be reloaded."""
