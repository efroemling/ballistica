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
"""Defines a bomb-dodging mini-game."""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor.bomb import Bomb
from bastd.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any, Sequence, Optional, List, Dict, Type, Type


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: Optional[float] = None


class Team(ba.Team[Player]):
    """Our team type for this game."""


# ba_meta export game
class MeteorShowerGame(ba.TeamGameActivity[Player, Team]):
    """Minigame involving dodging falling bombs."""

    name = 'Meteor Shower'
    description = 'Dodge the falling bombs.'
    available_settings = [ba.BoolSetting('Epic Mode', default=False)]
    scoreconfig = ba.ScoreConfig(label='Survived',
                                 scoretype=ba.ScoreType.MILLISECONDS,
                                 version='B')

    # Print messages when players die (since its meaningful in this game).
    announce_player_deaths = True

    # we're currently hard-coded for one map..
    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Rampage']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.DualTeamSession)
                or issubclass(sessiontype, ba.FreeForAllSession)
                or issubclass(sessiontype, ba.CoopSession))

    def __init__(self, settings: dict):
        super().__init__(settings)

        self._epic_mode = settings.get('Epic Mode', False)
        self._last_player_death_time: Optional[float] = None
        self._meteor_time = 2.0
        self._timer: Optional[OnScreenTimer] = None

        # Some base class overrides:
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.SURVIVAL)
        if self._epic_mode:
            self.slow_motion = True

    def on_begin(self) -> None:
        super().on_begin()

        # Drop a wave every few seconds.. and every so often drop the time
        # between waves ..lets have things increase faster if we have fewer
        # players.
        delay = 5.0 if len(self.players) > 2 else 2.5
        if self._epic_mode:
            delay *= 0.25
        ba.timer(delay, self._decrement_meteor_time, repeat=True)

        # Kick off the first wave in a few seconds.
        delay = 3.0
        if self._epic_mode:
            delay *= 0.25
        ba.timer(delay, self._set_meteor_timer)

        self._timer = OnScreenTimer()
        self._timer.start()

        # Check for immediate end (if we've only got 1 player, etc).
        ba.timer(5.0, self._check_end_game)

    def on_player_join(self, player: Player) -> None:
        # Don't allow joining after we start
        # (would enable leave/rejoin tomfoolery).
        if self.has_begun():
            ba.screenmessage(
                ba.Lstr(resource='playerDelayedJoinText',
                        subs=[('${PLAYER}', player.getname(full=True))]),
                color=(0, 1, 0),
            )
            # For score purposes, mark them as having died right as the
            # game started.
            assert self._timer is not None
            player.death_time = self._timer.getstarttime()
            return
        self.spawn_player(player)

    def on_player_leave(self, player: Player) -> None:
        # Augment default behavior.
        super().on_player_leave(player)

        # A departing player may trigger game-over.
        self._check_end_game()

    # overriding the default character spawning..
    def spawn_player(self, player: Player) -> ba.Actor:
        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(enable_punch=False,
                                        enable_bomb=False,
                                        enable_pickup=False)

        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            curtime = ba.time()

            # Record the player's moment of death.
            # assert isinstance(msg.spaz.player
            msg.getplayer(Player).death_time = curtime

            # In co-op mode, end the game the instant everyone dies
            # (more accurate looking).
            # In teams/ffa, allow a one-second fudge-factor so we can
            # get more draws if players die basically at the same time.
            if isinstance(self.session, ba.CoopSession):
                # Teams will still show up if we check now.. check in
                # the next cycle.
                ba.pushcall(self._check_end_game)

                # Also record this for a final setting of the clock.
                self._last_player_death_time = curtime
            else:
                ba.timer(1.0, self._check_end_game)

        else:
            # Default handler:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break

        # In co-op, we go till everyone is dead.. otherwise we go
        # until one team remains.
        if isinstance(self.session, ba.CoopSession):
            if living_team_count <= 0:
                self.end_game()
        else:
            if living_team_count <= 1:
                self.end_game()

    def _set_meteor_timer(self) -> None:
        ba.timer((1.0 + 0.2 * random.random()) * self._meteor_time,
                 self._drop_bomb_cluster)

    def _drop_bomb_cluster(self) -> None:

        # Random note: code like this is a handy way to plot out extents
        # and debug things.
        loc_test = False
        if loc_test:
            ba.newnode('locator', attrs={'position': (8, 6, -5.5)})
            ba.newnode('locator', attrs={'position': (8, 6, -2.3)})
            ba.newnode('locator', attrs={'position': (-7.3, 6, -5.5)})
            ba.newnode('locator', attrs={'position': (-7.3, 6, -2.3)})

        # Drop several bombs in series.
        delay = 0.0
        for _i in range(random.randrange(1, 3)):
            # Drop them somewhere within our bounds with velocity pointing
            # toward the opposite side.
            pos = (-7.3 + 15.3 * random.random(), 11,
                   -5.5 + 2.1 * random.random())
            dropdir = (-1.0 if pos[0] > 0 else 1.0)
            vel = ((-5.0 + random.random() * 30.0) * dropdir, -4.0, 0)
            ba.timer(delay, ba.Call(self._drop_bomb, pos, vel))
            delay += 0.1
        self._set_meteor_timer()

    def _drop_bomb(self, position: Sequence[float],
                   velocity: Sequence[float]) -> None:
        Bomb(position=position, velocity=velocity).autoretain()

    def _decrement_meteor_time(self) -> None:
        self._meteor_time = max(0.01, self._meteor_time * 0.9)

    def end_game(self) -> None:
        cur_time = ba.time()
        assert self._timer is not None
        start_time = self._timer.getstarttime()

        # Mark death-time as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:
                survived = False

                # Throw an extra fudge factor in so teams that
                # didn't die come out ahead of teams that did.
                if player.death_time is None:
                    survived = True
                    player.death_time = cur_time + 1

                # Award a per-player score depending on how many seconds
                # they lasted (per-player scores only affect teams mode;
                # everywhere else just looks at the per-team score).
                score = int(player.death_time - self._timer.getstarttime())
                if survived:
                    score += 50  # A bit extra for survivors.
                self.stats.player_scored(player, score, screenmessage=False)

        # Stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endtime=self._last_player_death_time)

        # Ok now calc game results: set a score for each team and then tell
        # the game to end.
        results = ba.GameResults()

        # Remember that 'free-for-all' mode is simply a special form
        # of 'teams' mode where each player gets their own team, so we can
        # just always deal in teams and have all cases covered.
        for team in self.teams:

            # Set the team score to the max time survived by any player on
            # that team.
            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(longest_life,
                                   player.death_time - start_time)

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(1000.0 * longest_life))

        self.end(results=results)
