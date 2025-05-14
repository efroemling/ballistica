# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to player-controlled Spazzes."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload, override

import bascenev1 as bs

from bascenev1lib.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any, Sequence, Literal


class PlayerSpazHurtMessage:
    """A message saying a PlayerSpaz was hurt."""

    spaz: PlayerSpaz
    """The PlayerSpaz that was hurt"""

    def __init__(self, spaz: PlayerSpaz):
        """Instantiate with the given bascenev1.Spaz value."""
        self.spaz = spaz


class PlayerSpaz(Spaz):
    """A Spaz subclass meant to be controlled by a bascenev1.Player.

    When a PlayerSpaz dies, it delivers a bascenev1.PlayerDiedMessage
    to the current bascenev1.Activity. (unless the death was the result
    of the player leaving the game, in which case no message is sent)

    When a PlayerSpaz is hurt, it delivers a PlayerSpazHurtMessage
    to the current bascenev1.Activity.
    """

    def __init__(
        self,
        player: bs.Player,
        *,
        color: Sequence[float] = (1.0, 1.0, 1.0),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        character: str = 'Spaz',
        powerups_expire: bool = True,
    ):
        """Create a spaz for the provided bascenev1.Player.

        Note: this does not wire up any controls;
        you must call connect_controls_to_player() to do so.
        """

        super().__init__(
            color=color,
            highlight=highlight,
            character=character,
            source_player=player,
            start_invincible=True,
            powerups_expire=powerups_expire,
        )
        self.last_player_attacked_by: bs.Player | None = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: tuple[str, str] | None = None
        self.held_count = 0
        self.last_player_held_by: bs.Player | None = None
        self._player = player
        self._drive_player_position()

    # Overloads to tell the type system our return type based on doraise val.

    @overload
    def getplayer[PlayerT: bs.Player](
        self, playertype: type[PlayerT], doraise: Literal[False] = False
    ) -> PlayerT | None: ...

    @overload
    def getplayer[PlayerT: bs.Player](
        self, playertype: type[PlayerT], doraise: Literal[True]
    ) -> PlayerT: ...

    def getplayer[PlayerT: bs.Player](
        self, playertype: type[PlayerT], doraise: bool = False
    ) -> PlayerT | None:
        """Get the bascenev1.Player associated with this Spaz.

        By default this will return None if the Player no longer exists.
        If you are logically certain that the Player still exists, pass
        doraise=False to get a non-optional return type.
        """
        player: Any = self._player
        assert isinstance(player, playertype)
        if not player.exists() and doraise:
            raise bs.PlayerNotFoundError()
        return player if player.exists() else None

    def connect_controls_to_player(
        self,
        *,
        enable_jump: bool = True,
        enable_punch: bool = True,
        enable_pickup: bool = True,
        enable_bomb: bool = True,
        enable_run: bool = True,
        enable_fly: bool = True,
    ) -> None:
        """Wire this spaz up to the provided bascenev1.Player.

        Full control of the character is given by default
        but can be selectively limited by passing False
        to specific arguments.
        """
        player = self.getplayer(bs.Player)
        assert player

        # Reset any currently connected player and/or the player we're
        # wiring up.
        if self._connected_to_player:
            if player != self._connected_to_player:
                player.resetinput()
            self.disconnect_controls_from_player()
        else:
            player.resetinput()

        player.assigninput(bs.InputType.UP_DOWN, self.on_move_up_down)
        player.assigninput(bs.InputType.LEFT_RIGHT, self.on_move_left_right)
        player.assigninput(
            bs.InputType.HOLD_POSITION_PRESS, self.on_hold_position_press
        )
        player.assigninput(
            bs.InputType.HOLD_POSITION_RELEASE,
            self.on_hold_position_release,
        )
        intp = bs.InputType
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
        bascenev1.Player from control of this spaz.
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
            print(
                'WARNING: disconnect_controls_from_player() called for'
                ' non-connected player'
            )

    @override
    def handlemessage(self, msg: Any) -> Any:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks
        assert not self.expired

        # Keep track of if we're being held and by who most recently.
        if isinstance(msg, bs.PickedUpMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.held_count += 1
            picked_up_by = msg.node.source_player
            if picked_up_by:
                self.last_player_held_by = picked_up_by
        elif isinstance(msg, bs.DroppedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.held_count -= 1
            if self.held_count < 0:
                print('ERROR: spaz held_count < 0')

            # Let's count someone dropping us as an attack.
            picked_up_by = msg.node.source_player
            if picked_up_by:
                self.last_player_attacked_by = picked_up_by
                self.last_attacked_time = bs.time()
                self.last_attacked_type = ('picked_up', 'default')
        elif isinstance(msg, bs.StandMessage):
            super().handlemessage(msg)  # Augment standard behavior.

            # Our Spaz was just moved somewhere. Explicitly update
            # our associated player's position in case it is being used
            # for logic (otherwise it will be out of date until next step)
            self._drive_player_position()

        elif isinstance(msg, bs.DieMessage):
            # Report player deaths to the game.
            if not self._dead:
                # Was this player killed while being held?
                was_held = self.held_count > 0 and self.last_player_held_by
                # Was this player attacked before death?
                was_attacked_recently = (
                    self.last_player_attacked_by
                    and bs.time() - self.last_attacked_time < 4.0
                )
                # Leaving the game doesn't count as a kill *unless*
                # someone does it intentionally while being attacked.
                left_game_cleanly = msg.how is bs.DeathType.LEFT_GAME and not (
                    was_held or was_attacked_recently
                )

                killed = not (msg.immediate or left_game_cleanly)

                activity = self._activity()

                player = self.getplayer(bs.Player, False)
                if not killed:
                    killerplayer = None
                else:
                    # If this player was being held at the time of death,
                    # the holder is the killer.
                    if was_held:
                        killerplayer = self.last_player_held_by
                    else:
                        # Otherwise, if they were attacked by someone in the
                        # last few seconds, that person is the killer.
                        # Otherwise it was a suicide.
                        # FIXME: Currently disabling suicides in Co-Op since
                        #  all bot kills would register as suicides; need to
                        #  change this from last_player_attacked_by to
                        #  something like last_actor_attacked_by to fix that.
                        if was_attacked_recently:
                            killerplayer = self.last_player_attacked_by
                        else:
                            # ok, call it a suicide unless we're in co-op
                            if activity is not None and not isinstance(
                                activity.session, bs.CoopSession
                            ):
                                killerplayer = player
                            else:
                                killerplayer = None

                # We should never wind up with a dead-reference here;
                # we want to use None in that case.
                assert killerplayer is None or killerplayer

                # Only report if both the player and the activity still exist.
                if killed and activity is not None and player:
                    activity.handlemessage(
                        bs.PlayerDiedMessage(
                            player, killed, killerplayer, msg.how
                        )
                    )

            super().handlemessage(msg)  # Augment standard behavior.

        # Keep track of the player who last hit us for point rewarding.
        elif isinstance(msg, bs.HitMessage):
            source_player = msg.get_source_player(type(self._player))
            if source_player:
                self.last_player_attacked_by = source_player
                self.last_attacked_time = bs.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            super().handlemessage(msg)  # Augment standard behavior.
            activity = self._activity()
            if activity is not None and self._player.exists():
                activity.handlemessage(PlayerSpazHurtMessage(self))
        else:
            return super().handlemessage(msg)
        return None

    def _drive_player_position(self) -> None:
        """Drive our bascenev1.Player's official position

        If our position is changed explicitly, this should be called again
        to instantly update the player position (otherwise it would be out
        of date until the next sim step)
        """
        player = self._player
        if player:
            assert self.node
            assert player.node
            self.node.connectattr('torso_position', player.node, 'position')
