# Released under the MIT License. See LICENSE for details.
#
"""Provides Ninja Fight mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.spazbot import (
    SpazBotSet,
    ChargerBot,
    SpazBotDiedMessage,
)
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class NinjaFightGame(bs.TeamGameActivity[Player, Team]):
    """
    A co-op game where you try to defeat a group
    of Ninjas as fast as possible
    """

    name = 'Ninja Fight'
    description = 'How fast can you defeat the ninjas?'
    scoreconfig = bs.ScoreConfig(
        label='Time', scoretype=bs.ScoreType.MILLISECONDS, lower_is_better=True
    )
    default_music = bs.MusicType.TO_THE_DEATH

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # For now we're hard-coding spawn positions and whatnot
        # so we need to be sure to specify that we only support
        # a specific map.
        return ['Courtyard']

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        # We currently support Co-Op only.
        return issubclass(sessiontype, bs.CoopSession)

    # In the constructor we should load any media we need/etc.
    # ...but not actually create anything yet.
    def __init__(self, settings: dict):
        super().__init__(settings)
        self._winsound = bs.getsound('score')
        self._won = False
        self._timer: OnScreenTimer | None = None
        self._bots = SpazBotSet()
        self._preset = str(settings['preset'])

    # Called when our game actually begins.
    @override
    def on_begin(self) -> None:
        super().on_begin()
        is_pro = self._preset == 'pro'

        # In pro mode there's no powerups.
        if not is_pro:
            self.setup_standard_powerup_drops()

        # Make our on-screen timer and start it roughly when our bots appear.
        self._timer = OnScreenTimer()
        bs.timer(4.0, self._timer.start)

        # Spawn some baddies.
        bs.timer(
            1.0,
            lambda: self._bots.spawn_bot(
                ChargerBot, pos=(3, 3, -2), spawn_time=3.0
            ),
        )
        bs.timer(
            2.0,
            lambda: self._bots.spawn_bot(
                ChargerBot, pos=(-3, 3, -2), spawn_time=3.0
            ),
        )
        bs.timer(
            3.0,
            lambda: self._bots.spawn_bot(
                ChargerBot, pos=(5, 3, -2), spawn_time=3.0
            ),
        )
        bs.timer(
            4.0,
            lambda: self._bots.spawn_bot(
                ChargerBot, pos=(-5, 3, -2), spawn_time=3.0
            ),
        )

        # Add some extras for multiplayer or pro mode.
        assert self.initialplayerinfos is not None
        if len(self.initialplayerinfos) > 2 or is_pro:
            bs.timer(
                5.0,
                lambda: self._bots.spawn_bot(
                    ChargerBot, pos=(0, 3, -5), spawn_time=3.0
                ),
            )
        if len(self.initialplayerinfos) > 3 or is_pro:
            bs.timer(
                6.0,
                lambda: self._bots.spawn_bot(
                    ChargerBot, pos=(0, 3, 1), spawn_time=3.0
                ),
            )

    # Called for each spawning player.
    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        # Let's spawn close to the center.
        spawn_center = (0, 3, -2)
        pos = (
            spawn_center[0] + random.uniform(-1.5, 1.5),
            spawn_center[1],
            spawn_center[2] + random.uniform(-1.5, 1.5),
        )
        return self.spawn_player_spaz(player, position=pos)

    def _check_if_won(self) -> None:
        # Simply end the game if there's no living bots.
        # FIXME: Should also make sure all bots have been spawned;
        #  if spawning is spread out enough that we're able to kill
        #  all living bots before the next spawns, it would incorrectly
        #  count as a win.
        if not self._bots.have_living_bots():
            self._won = True
            self.end_game()

    # Called for miscellaneous messages.
    @override
    def handlemessage(self, msg: Any) -> Any:
        # A player has died.
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.respawn_player(msg.getplayer(Player))

        # A spaz-bot has died.
        elif isinstance(msg, SpazBotDiedMessage):
            # Unfortunately the bot-set will always tell us there are living
            # bots if we ask here (the currently-dying bot isn't officially
            # marked dead yet) ..so lets push a call into the event loop to
            # check once this guy has finished dying.
            bs.pushcall(self._check_if_won)

        # Let the base class handle anything we don't.
        else:
            return super().handlemessage(msg)
        return None

    # When this is called, we should fill out results and end the game
    # *regardless* of whether is has been won. (this may be called due
    # to a tournament ending or other external reason).
    @override
    def end_game(self) -> None:
        # Stop our on-screen timer so players can see what they got.
        assert self._timer is not None
        self._timer.stop()

        results = bs.GameResults()

        # If we won, set our score to the elapsed time in milliseconds.
        # (there should just be 1 team here since this is co-op).
        # ..if we didn't win, leave scores as default (None) which means
        # we lost.
        if self._won:
            elapsed_time_ms = int((bs.time() - self._timer.starttime) * 1000.0)
            bs.cameraflash()
            self._winsound.play()
            for team in self.teams:
                for player in team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage())
                results.set_team_score(team, elapsed_time_ms)

        # Ends the activity.
        self.end(results)
