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
"""Implements Target Practice game."""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.onscreencountdown import OnScreenCountdown
from bastd.actor.bomb import Bomb
from bastd.actor.popuptext import PopupText

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Optional, Sequence
    from bastd.actor.bomb import Blast


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.streak = 0


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export game
class TargetPracticeGame(ba.TeamGameActivity[Player, Team]):
    """Game where players try to hit targets with bombs."""

    name = 'Target Practice'
    description = 'Bomb as many targets as you can.'
    available_settings = [
        ba.IntSetting('Target Count', min_value=1, default=3),
        ba.BoolSetting('Enable Impact Bombs', default=True),
        ba.BoolSetting('Enable Triple Bombs', default=True)
    ]
    default_music = ba.MusicType.FORWARD_MARCH

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Doom Shroom']

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        # We support any teams or versus sessions.
        return (issubclass(sessiontype, ba.CoopSession)
                or issubclass(sessiontype, ba.MultiTeamSession))

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._targets: List[Target] = []
        self._update_timer: Optional[ba.Timer] = None
        self._countdown: Optional[OnScreenCountdown] = None
        self._target_count = int(settings['Target Count'])
        self._enable_impact_bombs = bool(settings['Enable Impact Bombs'])
        self._enable_triple_bombs = bool(settings['Enable Triple Bombs'])

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self.update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.update_scoreboard()

        # Number of targets is based on player count.
        for i in range(self._target_count):
            ba.timer(5.0 + i * 1.0, self._spawn_target)

        self._update_timer = ba.Timer(1.0, self._update, repeat=True)
        self._countdown = OnScreenCountdown(60, endcall=self.end_game)
        ba.timer(4.0, self._countdown.start)

    def spawn_player(self, player: Player) -> ba.Actor:
        spawn_center = (0, 3, -5)
        pos = (spawn_center[0] + random.uniform(-1.5, 1.5), spawn_center[1],
               spawn_center[2] + random.uniform(-1.5, 1.5))

        # Reset their streak.
        player.streak = 0
        spaz = self.spawn_player_spaz(player, position=pos)

        # Give players permanent triple impact bombs and wire them up
        # to tell us when they drop a bomb.
        if self._enable_impact_bombs:
            spaz.bomb_type = 'impact'
        if self._enable_triple_bombs:
            spaz.set_bomb_count(3)
        spaz.add_dropped_bomb_callback(self._on_spaz_dropped_bomb)
        return spaz

    def _spawn_target(self) -> None:

        # Generate a few random points; we'll use whichever one is farthest
        # from our existing targets (don't want overlapping targets).
        points = []

        for _i in range(4):
            # Calc a random point within a circle.
            while True:
                xpos = random.uniform(-1.0, 1.0)
                ypos = random.uniform(-1.0, 1.0)
                if xpos * xpos + ypos * ypos < 1.0:
                    break
            points.append(ba.Vec3(8.0 * xpos, 2.2, -3.5 + 5.0 * ypos))

        def get_min_dist_from_target(pnt: ba.Vec3) -> float:
            return min((t.get_dist_from_point(pnt) for t in self._targets))

        # If we have existing targets, use the point with the highest
        # min-distance-from-targets.
        if self._targets:
            point = max(points, key=get_min_dist_from_target)
        else:
            point = points[0]

        self._targets.append(Target(position=point))

    def _on_spaz_dropped_bomb(self, spaz: ba.Actor, bomb: ba.Actor) -> None:
        del spaz  # Unused.

        # Wire up this bomb to inform us when it blows up.
        assert isinstance(bomb, Bomb)
        bomb.add_explode_callback(self._on_bomb_exploded)

    def _on_bomb_exploded(self, bomb: Bomb, blast: Blast) -> None:
        assert blast.node
        pos = blast.node.position

        # Debugging: throw a locator down where we landed.
        # ba.newnode('locator', attrs={'position':blast.node.position})

        # Feed the explosion point to all our targets and get points in return.
        # Note: we operate on a copy of self._targets since the list may change
        # under us if we hit stuff (don't wanna get points for new targets).
        player = bomb.get_source_player(Player)
        if not player:
            # It's possible the player left after throwing the bomb.
            return

        bullseye = any(
            target.do_hit_at_position(pos, player)
            for target in list(self._targets))
        if bullseye:
            player.streak += 1
        else:
            player.streak = 0

    def _update(self) -> None:
        """Misc. periodic updating."""
        # Clear out targets that have died.
        self._targets = [t for t in self._targets if t]

    def handlemessage(self, msg: Any) -> Any:
        # When players die, respawn them.
        if isinstance(msg, ba.PlayerDiedMessage):
            super().handlemessage(msg)  # Do standard stuff.
            player = msg.getplayer(Player)
            assert player is not None
            self.respawn_player(player)  # Kick off a respawn.
        elif isinstance(msg, Target.TargetHitMessage):
            # A target is telling us it was hit and will die soon..
            # ..so make another one.
            self._spawn_target()
        else:
            super().handlemessage(msg)

    def update_scoreboard(self) -> None:
        """Update the game scoreboard with current team values."""
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score)

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results)


class Target(ba.Actor):
    """A target practice target."""

    class TargetHitMessage:
        """Inform an object a target was hit."""

    def __init__(self, position: Sequence[float]):
        self._r1 = 0.45
        self._r2 = 1.1
        self._r3 = 2.0
        self._rfudge = 0.15
        super().__init__()
        self._position = ba.Vec3(position)
        self._hit = False

        # It can be handy to test with this on to make sure the projection
        # isn't too far off from the actual object.
        show_in_space = False
        loc1 = ba.newnode('locator',
                          attrs={
                              'shape': 'circle',
                              'position': position,
                              'color': (0, 1, 0),
                              'opacity': 0.5,
                              'draw_beauty': show_in_space,
                              'additive': True
                          })
        loc2 = ba.newnode('locator',
                          attrs={
                              'shape': 'circleOutline',
                              'position': position,
                              'color': (0, 1, 0),
                              'opacity': 0.3,
                              'draw_beauty': False,
                              'additive': True
                          })
        loc3 = ba.newnode('locator',
                          attrs={
                              'shape': 'circleOutline',
                              'position': position,
                              'color': (0, 1, 0),
                              'opacity': 0.1,
                              'draw_beauty': False,
                              'additive': True
                          })
        self._nodes = [loc1, loc2, loc3]
        ba.animate_array(loc1, 'size', 1, {0: [0.0], 0.2: [self._r1 * 2.0]})
        ba.animate_array(loc2, 'size', 1, {
            0.05: [0.0],
            0.25: [self._r2 * 2.0]
        })
        ba.animate_array(loc3, 'size', 1, {0.1: [0.0], 0.3: [self._r3 * 2.0]})
        ba.playsound(ba.getsound('laserReverse'))

    def exists(self) -> bool:
        return bool(self._nodes)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.DieMessage):
            for node in self._nodes:
                node.delete()
            self._nodes = []
        else:
            super().handlemessage(msg)

    def get_dist_from_point(self, pos: ba.Vec3) -> float:
        """Given a point, returns distance squared from it."""
        return (pos - self._position).length()

    def do_hit_at_position(self, pos: Sequence[float], player: Player) -> bool:
        """Handle a bomb hit at the given position."""
        # pylint: disable=too-many-statements
        activity = self.activity

        # Ignore hits if the game is over or if we've already been hit
        if activity.has_ended() or self._hit or not self._nodes:
            return False

        diff = (ba.Vec3(pos) - self._position)

        # Disregard Y difference. Our target point probably isn't exactly
        # on the ground anyway.
        diff[1] = 0.0
        dist = diff.length()

        bullseye = False
        if dist <= self._r3 + self._rfudge:
            # Inform our activity that we were hit
            self._hit = True
            activity.handlemessage(self.TargetHitMessage())
            keys: Dict[float, Sequence[float]] = {
                0.0: (1.0, 0.0, 0.0),
                0.049: (1.0, 0.0, 0.0),
                0.05: (1.0, 1.0, 1.0),
                0.1: (0.0, 1.0, 0.0)
            }
            cdull = (0.3, 0.3, 0.3)
            popupcolor: Sequence[float]
            if dist <= self._r1 + self._rfudge:
                bullseye = True
                self._nodes[1].color = cdull
                self._nodes[2].color = cdull
                ba.animate_array(self._nodes[0], 'color', 3, keys, loop=True)
                popupscale = 1.8
                popupcolor = (1, 1, 0, 1)
                streak = player.streak
                points = 10 + min(20, streak * 2)
                ba.playsound(ba.getsound('bellHigh'))
                if streak > 0:
                    ba.playsound(
                        ba.getsound(
                            'orchestraHit4' if streak > 3 else
                            'orchestraHit3' if streak > 2 else
                            'orchestraHit2' if streak > 1 else 'orchestraHit'))
            elif dist <= self._r2 + self._rfudge:
                self._nodes[0].color = cdull
                self._nodes[2].color = cdull
                ba.animate_array(self._nodes[1], 'color', 3, keys, loop=True)
                popupscale = 1.25
                popupcolor = (1, 0.5, 0.2, 1)
                points = 4
                ba.playsound(ba.getsound('bellMed'))
            else:
                self._nodes[0].color = cdull
                self._nodes[1].color = cdull
                ba.animate_array(self._nodes[2], 'color', 3, keys, loop=True)
                popupscale = 1.0
                popupcolor = (0.8, 0.3, 0.3, 1)
                points = 2
                ba.playsound(ba.getsound('bellLow'))

            # Award points/etc.. (technically should probably leave this up
            # to the activity).
            popupstr = '+' + str(points)

            # If there's more than 1 player in the game, include their
            # names and colors so they know who got the hit.
            if len(activity.players) > 1:
                popupcolor = ba.safecolor(player.color, target_intensity=0.75)
                popupstr += ' ' + player.getname()
            PopupText(popupstr,
                      position=self._position,
                      color=popupcolor,
                      scale=popupscale).autoretain()

            # Give this player's team points and update the score-board.
            player.team.score += points
            assert isinstance(activity, TargetPracticeGame)
            activity.update_scoreboard()

            # Also give this individual player points
            # (only applies in teams mode).
            assert activity.stats is not None
            activity.stats.player_scored(player,
                                         points,
                                         showpoints=False,
                                         screenmessage=False)

            ba.animate_array(self._nodes[0], 'size', 1, {
                0.8: self._nodes[0].size,
                1.0: [0.0]
            })
            ba.animate_array(self._nodes[1], 'size', 1, {
                0.85: self._nodes[1].size,
                1.05: [0.0]
            })
            ba.animate_array(self._nodes[2], 'size', 1, {
                0.9: self._nodes[2].size,
                1.1: [0.0]
            })
            ba.timer(1.1, ba.Call(self.handlemessage, ba.DieMessage()))

        return bullseye
