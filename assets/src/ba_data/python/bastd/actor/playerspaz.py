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

from typing import TYPE_CHECKING, TypeVar, overload

import ba
from bastd.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any, Sequence, Tuple, Optional, Type
    from typing_extensions import Literal

PlayerType = TypeVar('PlayerType', bound=ba.Player)
TeamType = TypeVar('TeamType', bound=ba.Team)


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


class PlayerSpaz(Spaz):
    """A ba.Spaz subclass meant to be controlled by a ba.Player.

    category: Gameplay Classes

    When a PlayerSpaz dies, it delivers a ba.PlayerDiedMessage
    to the current ba.Activity. (unless the death was the result of the
    player leaving the game, in which case no message is sent)

    When a PlayerSpaz is hurt, it delivers a ba.PlayerSpazHurtMessage
    to the current ba.Activity.
    """

    def __init__(self,
                 player: ba.Player,
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
        self.last_player_attacked_by: Optional[ba.Player] = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: Optional[Tuple[str, str]] = None
        self.held_count = 0
        self.last_player_held_by: Optional[ba.Player] = None
        self._player = player
        self._drive_player_position()

    # Overloads to tell the type system our return type based on doraise val.

    @overload
    def getplayer(self,
                  playertype: Type[PlayerType],
                  doraise: Literal[False] = False) -> Optional[PlayerType]:
        ...

    @overload
    def getplayer(self, playertype: Type[PlayerType],
                  doraise: Literal[True]) -> PlayerType:
        ...

    def getplayer(self,
                  playertype: Type[PlayerType],
                  doraise: bool = False) -> Optional[PlayerType]:
        """Get the ba.Player associated with this Spaz.

        By default this will return None if the Player no longer exists.
        If you are logically certain that the Player still exists, pass
        doraise=False to get a non-optional return type.
        """
        player: Any = self._player
        assert isinstance(player, playertype)
        if not player.exists() and doraise:
            raise ba.PlayerNotFoundError()
        return player if player.exists() else None

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
        player = self.getplayer(ba.Player)
        assert player

        # Reset any currently connected player and/or the player we're
        # wiring up.
        if self._connected_to_player:
            if player != self._connected_to_player:
                player.resetinput()
            self.disconnect_controls_from_player()
        else:
            player.resetinput()

        player.assigninput(ba.InputType.UP_DOWN, self.on_move_up_down)
        player.assigninput(ba.InputType.LEFT_RIGHT, self.on_move_left_right)
        player.assigninput(ba.InputType.HOLD_POSITION_PRESS,
                           self.on_hold_position_press)
        player.assigninput(ba.InputType.HOLD_POSITION_RELEASE,
                           self.on_hold_position_release)
        intp = ba.InputType
        if enable_jump:
            player.assigninput(intp.JUMP_PRESS, self.on_jump_press)
            player.assigninput(intp.JUMP_RELEASE, self.on_jump_release)
        if enable_pickup:
            player.assigninput(intp.PICK_UP_PRESS, self.on_pickup_press)
            player.assigninput(intp.PICK_UP_RELEASE, self.on_pickup_release)
        if enable_punch:
            player.assigninput(intp.PUNCH_PRESS, self.on_punch_press)
            player.assigninput(intp.PUNCH_RELEASE, self.on_punch_release)
        if enable_bomb:
            player.assigninput(intp.BOMB_PRESS, self.on_bomb_press)
            player.assigninput(intp.BOMB_RELEASE, self.on_bomb_release)
        if enable_run:
            player.assigninput(intp.RUN, self.on_run)
        if enable_fly:
            player.assigninput(intp.FLY_PRESS, self.on_fly_press)
            player.assigninput(intp.FLY_RELEASE, self.on_fly_release)

        self._connected_to_player = player

    def disconnect_controls_from_player(self) -> None:
        """
        Completely sever any previously connected
        ba.Player from control of this spaz.
        """
        if self._connected_to_player:
            self._connected_to_player.resetinput()
            self._connected_to_player = None

            # Send releases for anything in case its held.
            self.on_move_up_down(0)
            self.on_move_left_right(0)
            self.on_hold_position_release()
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
        assert not self.expired

        # Keep track of if we're being held and by who most recently.
        if isinstance(msg, ba.PickedUpMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.held_count += 1
            picked_up_by = msg.node.source_player
            if picked_up_by:
                self.last_player_held_by = picked_up_by
        elif isinstance(msg, ba.DroppedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.held_count -= 1
            if self.held_count < 0:
                print('ERROR: spaz held_count < 0')

            # Let's count someone dropping us as an attack.
            picked_up_by = msg.node.source_player
            if picked_up_by:
                self.last_player_attacked_by = picked_up_by
                self.last_attacked_time = ba.time()
                self.last_attacked_type = ('picked_up', 'default')
        elif isinstance(msg, ba.StandMessage):
            super().handlemessage(msg)  # Augment standard behavior.

            # Our Spaz was just moved somewhere. Explicitly update
            # our associated player's position in case it is being used
            # for logic (otherwise it will be out of date until next step)
            self._drive_player_position()

        elif isinstance(msg, ba.DieMessage):

            # Report player deaths to the game.
            if not self._dead:

                # Immediate-mode or left-game deaths don't count as 'kills'.
                killed = (not msg.immediate
                          and msg.how is not ba.DeathType.LEFT_GAME)

                activity = self._activity()

                player = self.getplayer(ba.Player, False)
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
                                killerplayer = player
                            else:
                                killerplayer = None

                # We should never wind up with a dead-reference here;
                # we want to use None in that case.
                assert killerplayer is None or killerplayer

                # Only report if both the player and the activity still exist.
                if killed and activity is not None and player:
                    activity.handlemessage(
                        ba.PlayerDiedMessage(player, killed, killerplayer,
                                             msg.how))

            super().handlemessage(msg)  # Augment standard behavior.

        # Keep track of the player who last hit us for point rewarding.
        elif isinstance(msg, ba.HitMessage):
            source_player = msg.get_source_player(type(self._player))
            if source_player:
                self.last_player_attacked_by = source_player
                self.last_attacked_time = ba.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            super().handlemessage(msg)  # Augment standard behavior.
            activity = self._activity()
            if activity is not None and self._player.exists():
                activity.handlemessage(PlayerSpazHurtMessage(self))
        else:
            return super().handlemessage(msg)
        return None

    def _drive_player_position(self) -> None:
        """Drive our ba.Player's official position

        If our position is changed explicitly, this should be called again
        to instantly update the player position (otherwise it would be out
        of date until the next sim step)
        """
        player = self._player
        if player:
            assert self.node
            assert player.node
            self.node.connectattr('torso_position', player.node, 'position')
