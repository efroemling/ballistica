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
"""Functionality related to player-controlled Spazzes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

import ba
from bastd.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any, Sequence, Tuple, Optional

PlayerType = TypeVar('PlayerType', bound=ba.Player)
TeamType = TypeVar('TeamType', bound=ba.Team)


class PlayerSpazDeathMessage:
    """A message saying a ba.PlayerSpaz has died.

    category: Message Classes

    Attributes:

       killed
          If True, the spaz was killed;
          If False, they left the game or the round ended.

       killerplayer
          The ba.Player that did the killing, or None.

       how
          The particular type of death.
    """

    def __init__(self, spaz: PlayerSpaz, was_killed: bool,
                 killerplayer: Optional[ba.Player], how: ba.DeathType):
        """Instantiate a message with the given values."""
        self._spaz = spaz
        self.killed = was_killed
        self.killerplayer = killerplayer
        self.how = how

    def playerspaz(
            self, activity: ba.Activity[PlayerType,
                                        TeamType]) -> PlayerSpaz[PlayerType]:
        """Return the spaz that died.

        The current activity is required as an argument so the exact type of
        PlayerSpaz can be determined by the type checker.
        """
        del activity  # Unused
        return self._spaz


class PlayerSpazHurtMessage:
    """A message saying a ba.PlayerSpaz was hurt.

    category: Message Classes

    Attributes:

       spaz
          The ba.PlayerSpaz that was hurt
    """

    def __init__(self, spaz: PlayerSpaz):
        """Instantiate with the given ba.Spaz value."""
        self.spaz = spaz


class PlayerSpaz(Spaz, Generic[PlayerType]):
    """A ba.Spaz subclass meant to be controlled by a ba.Player.

    category: Gameplay Classes

    When a PlayerSpaz dies, it delivers a ba.PlayerSpazDeathMessage
    to the current ba.Activity. (unless the death was the result of the
    player leaving the game, in which case no message is sent)

    When a PlayerSpaz is hurt, it delivers a ba.PlayerSpazHurtMessage
    to the current ba.Activity.
    """

    def __init__(self,
                 player: PlayerType,
                 color: Sequence[float] = (1.0, 1.0, 1.0),
                 highlight: Sequence[float] = (0.5, 0.5, 0.5),
                 character: str = 'Spaz',
                 powerups_expire: bool = True):
        """Create a spaz for the provided ba.Player.

        Note: this does not wire up any controls;
        you must call connect_controls_to_player() to do so.
        """

        super().__init__(color=color,
                         highlight=highlight,
                         character=character,
                         source_player=player,
                         start_invincible=True,
                         powerups_expire=powerups_expire)
        self.last_player_attacked_by: Optional[PlayerType] = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: Optional[Tuple[str, str]] = None
        self.held_count = 0
        self.last_player_held_by: Optional[PlayerType] = None
        self._player = player
        self.playertype = type(player)

        # Grab the node for this player and wire it to follow our spaz
        # (so players' controllers know where to draw their guides, etc).
        if player:
            assert self.node
            assert player.node
            self.node.connectattr('torso_position', player.node, 'position')

    @property
    def player(self) -> PlayerType:
        """The ba.Player associated with this Spaz.

        If the player no longer exists, raises an ba.PlayerNotFoundError.
        """
        if not self._player:
            raise ba.PlayerNotFoundError()
        return self._player

    def getplayer(self) -> Optional[PlayerType]:
        """Get the ba.Player associated with this Spaz.

        Note that this may return None if the player has left.
        """
        # Return None in the case of a no-longer-valid reference.
        return self._player if self._player else None

    def connect_controls_to_player(self,
                                   enable_jump: bool = True,
                                   enable_punch: bool = True,
                                   enable_pickup: bool = True,
                                   enable_bomb: bool = True,
                                   enable_run: bool = True,
                                   enable_fly: bool = True) -> None:
        """Wire this spaz up to the provided ba.Player.

        Full control of the character is given by default
        but can be selectively limited by passing False
        to specific arguments.
        """
        player = self.getplayer()
        assert player

        # Reset any currently connected player and/or the player we're
        # wiring up.
        if self._connected_to_player:
            if player != self._connected_to_player:
                player.reset_input()
            self.disconnect_controls_from_player()
        else:
            player.reset_input()

        player.assign_input_call('upDown', self.on_move_up_down)
        player.assign_input_call('leftRight', self.on_move_left_right)
        player.assign_input_call('holdPositionPress',
                                 self._on_hold_position_press)
        player.assign_input_call('holdPositionRelease',
                                 self._on_hold_position_release)
        if enable_jump:
            player.assign_input_call('jumpPress', self.on_jump_press)
            player.assign_input_call('jumpRelease', self.on_jump_release)
        if enable_pickup:
            player.assign_input_call('pickUpPress', self.on_pickup_press)
            player.assign_input_call('pickUpRelease', self.on_pickup_release)
        if enable_punch:
            player.assign_input_call('punchPress', self.on_punch_press)
            player.assign_input_call('punchRelease', self.on_punch_release)
        if enable_bomb:
            player.assign_input_call('bombPress', self.on_bomb_press)
            player.assign_input_call('bombRelease', self.on_bomb_release)
        if enable_run:
            player.assign_input_call('run', self.on_run)
        if enable_fly:
            player.assign_input_call('flyPress', self.on_fly_press)
            player.assign_input_call('flyRelease', self.on_fly_release)

        self._connected_to_player = player

    def disconnect_controls_from_player(self) -> None:
        """
        Completely sever any previously connected
        ba.Player from control of this spaz.
        """
        if self._connected_to_player:
            self._connected_to_player.reset_input()
            self._connected_to_player = None

            # Send releases for anything in case its held.
            self.on_move_up_down(0)
            self.on_move_left_right(0)
            self._on_hold_position_release()
            self.on_jump_release()
            self.on_pickup_release()
            self.on_punch_release()
            self.on_bomb_release()
            self.on_run(0.0)
            self.on_fly_release()
        else:
            print('WARNING: disconnect_controls_from_player() called for'
                  ' non-connected player')

    def handlemessage(self, msg: Any) -> Any:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks
        if __debug__:
            self._handlemessage_sanity_check()

        # Keep track of if we're being held and by who most recently.
        if isinstance(msg, ba.PickedUpMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.held_count += 1
            picked_up_by = ba.playercast_o(self.playertype,
                                           msg.node.source_player)
            if picked_up_by:
                self.last_player_held_by = picked_up_by
        elif isinstance(msg, ba.DroppedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.held_count -= 1
            if self.held_count < 0:
                print('ERROR: spaz held_count < 0')

            # Let's count someone dropping us as an attack.
            try:
                picked_up_by_2 = ba.playercast_o(self.playertype,
                                                 msg.node.source_player)
            except Exception:
                picked_up_by_2 = None
            if picked_up_by_2:
                self.last_player_attacked_by = picked_up_by_2
                self.last_attacked_time = ba.time()
                self.last_attacked_type = ('picked_up', 'default')
        elif isinstance(msg, ba.DieMessage):

            # Report player deaths to the game.
            if not self._dead:

                # Immediate-mode or left-game deaths don't count as 'kills'.
                killed = (not msg.immediate
                          and msg.how is not ba.DeathType.LEFT_GAME)

                activity = self._activity()

                if not killed:
                    killerplayer = None
                else:
                    # If this player was being held at the time of death,
                    # the holder is the killer.
                    if self.held_count > 0 and self.last_player_held_by:
                        killerplayer = self.last_player_held_by
                    else:
                        # Otherwise, if they were attacked by someone in the
                        # last few seconds, that person is the killer.
                        # Otherwise it was a suicide.
                        # FIXME: Currently disabling suicides in Co-Op since
                        #  all bot kills would register as suicides; need to
                        #  change this from last_player_attacked_by to
                        #  something like last_actor_attacked_by to fix that.
                        if (self.last_player_attacked_by
                                and ba.time() - self.last_attacked_time < 4.0):
                            killerplayer = self.last_player_attacked_by
                        else:
                            # ok, call it a suicide unless we're in co-op
                            if (activity is not None and not isinstance(
                                    activity.session, ba.CoopSession)):
                                killerplayer = self.getplayer()
                            else:
                                killerplayer = None

                # We should never wind up with a dead-reference here;
                # we want to use None in that case.
                assert killerplayer is None or killerplayer

                # Only report if both the player and the activity still exist.
                if killed and activity is not None and self.getplayer():
                    activity.handlemessage(
                        PlayerSpazDeathMessage(self, killed, killerplayer,
                                               msg.how))

            super().handlemessage(msg)  # Augment standard behavior.

        # Keep track of the player who last hit us for point rewarding.
        elif isinstance(msg, ba.HitMessage):
            if msg.source_player:
                srcplayer = ba.playercast_o(self.playertype, msg.source_player)
                self.last_player_attacked_by = srcplayer
                self.last_attacked_time = ba.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            super().handlemessage(msg)  # Augment standard behavior.
            activity = self._activity()
            if activity is not None:
                activity.handlemessage(PlayerSpazHurtMessage(self))
        else:
            super().handlemessage(msg)
