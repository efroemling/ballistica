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
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor import bomb
from bastd.actor import playerspaz

if TYPE_CHECKING:
    from typing import Any, Tuple, Sequence, Optional, List, Dict, Type
    from bastd.actor.onscreentimer import OnScreenTimer


# ba_meta export game
class MeteorShowerGame(ba.TeamGameActivity):
    """Minigame involving dodging falling bombs."""

    @classmethod
    def get_name(cls) -> str:
        return 'Meteor Shower'

    @classmethod
    def get_score_info(cls) -> Dict[str, Any]:
        return {
            'score_name': 'Survived',
            'score_type': 'milliseconds',
            'score_version': 'B'
        }

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Dodge the falling bombs.'

    # we're currently hard-coded for one map..
    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Rampage']

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        return [("Epic Mode", {'default': False})]

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.TeamsSession)
                or issubclass(sessiontype, ba.FreeForAllSession)
                or issubclass(sessiontype, ba.CoopSession))

    def __init__(self, settings: Dict[str, Any]):
        super().__init__(settings)

        if self.settings['Epic Mode']:
            self.slow_motion = True

        # Print messages when players die (since its meaningful in this game).
        self.announce_player_deaths = True

        self._last_player_death_time: Optional[float] = None
        self._meteor_time = 2.0
        self._timer: Optional[OnScreenTimer] = None

    # Called when our game is transitioning in but not ready to start;
    # ..we can go ahead and set our music and whatnot.
    def on_transition_in(self) -> None:
        self._default_music = (ba.MusicType.EPIC if self.settings['Epic Mode']
                               else ba.MusicType.SURVIVAL)
        super().on_transition_in()

    # Called when our game actually starts.
    def on_begin(self) -> None:
        from bastd.actor.onscreentimer import OnScreenTimer

        ba.TeamGameActivity.on_begin(self)

        # Drop a wave every few seconds.. and every so often drop the time
        # between waves ..lets have things increase faster if we have fewer
        # players.
        delay = 5.0 if len(self.players) > 2 else 2.5
        if self.settings['Epic Mode']:
            delay *= 0.25
        ba.timer(delay, self._decrement_meteor_time, repeat=True)

        # Kick off the first wave in a few seconds.
        delay = 3.0
        if self.settings['Epic Mode']:
            delay *= 0.25
        ba.timer(delay, self._set_meteor_timer)

        self._timer = OnScreenTimer()
        self._timer.start()

        # Check for immediate end (if we've only got 1 player, etc).
        ba.timer(5.0, self._check_end_game)

    def on_player_join(self, player: ba.Player) -> None:
        # Don't allow joining after we start
        # (would enable leave/rejoin tomfoolery).
        if self.has_begun():
            ba.screenmessage(ba.Lstr(resource='playerDelayedJoinText',
                                     subs=[('${PLAYER}',
                                            player.get_name(full=True))]),
                             color=(0, 1, 0))
            # For score purposes, mark them as having died right as the
            # game started.
            assert self._timer is not None
            player.gamedata['death_time'] = self._timer.getstarttime()
            return
        self.spawn_player(player)

    def on_player_leave(self, player: ba.Player) -> None:
        # Augment default behavior.
        ba.TeamGameActivity.on_player_leave(self, player)

        # A departing player may trigger game-over.
        self._check_end_game()

    # overriding the default character spawning..
    def spawn_player(self, player: ba.Player) -> ba.Actor:
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
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            death_time = ba.time()

            # Record the player's moment of death.
            msg.spaz.player.gamedata['death_time'] = death_time

            # In co-op mode, end the game the instant everyone dies
            # (more accurate looking).
            # In teams/ffa, allow a one-second fudge-factor so we can
            # get more draws if players die basically at the same time.
            if isinstance(self.session, ba.CoopSession):
                # Teams will still show up if we check now.. check in
                # the next cycle.
                ba.pushcall(self._check_end_game)

                # Also record this for a final setting of the clock.
                self._last_player_death_time = death_time
            else:
                ba.timer(1.0, self._check_end_game)

        else:
            # Default handler:
            super().handlemessage(msg)

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
        bomb.Bomb(position=position, velocity=velocity).autoretain()

    def _decrement_meteor_time(self) -> None:
        self._meteor_time = max(0.01, self._meteor_time * 0.9)

    def end_game(self) -> None:
        cur_time = ba.time()
        assert self._timer is not None

        # Mark 'death-time' as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:

                # Throw an extra fudge factor in so teams that
                # didn't die come out ahead of teams that did.
                if 'death_time' not in player.gamedata:
                    player.gamedata['death_time'] = cur_time + 0.001

                # Award a per-player score depending on how many seconds
                # they lasted (per-player scores only affect teams mode;
                # everywhere else just looks at the per-team score).
                score = int(player.gamedata['death_time'] -
                            self._timer.getstarttime())
                if 'death_time' not in player.gamedata:
                    score += 50  # a bit extra for survivors
                self.stats.player_scored(player, score, screenmessage=False)

        # Stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endtime=self._last_player_death_time)

        # Ok now calc game results: set a score for each team and then tell
        # the game to end.
        results = ba.TeamGameResults()

        # Remember that 'free-for-all' mode is simply a special form
        # of 'teams' mode where each player gets their own team, so we can
        # just always deal in teams and have all cases covered.
        for team in self.teams:

            # Set the team score to the max time survived by any player on
            # that team.
            longest_life = 0
            for player in team.players:
                longest_life = max(longest_life,
                                   (player.gamedata['death_time'] -
                                    self._timer.getstarttime()))
            results.set_team_score(team, longest_life)

        self.end(results=results)
