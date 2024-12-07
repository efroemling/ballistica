# Released under the MIT License. See LICENSE for details.
#
"""Implements Target Practice game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.onscreencountdown import OnScreenCountdown
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.popuptext import PopupText

if TYPE_CHECKING:
    from typing import Any, Sequence

    from bascenev1lib.actor.bomb import Blast


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.streak = 0


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class TargetPracticeGame(bs.TeamGameActivity[Player, Team]):
    """Game where players try to hit targets with bombs."""

    name = 'Target Practice'
    description = 'Bomb as many targets as you can.'
    available_settings = [
        bs.IntSetting('Target Count', min_value=1, default=3),
        bs.BoolSetting('Enable Impact Bombs', default=True),
        bs.BoolSetting('Enable Triple Bombs', default=True),
    ]
    default_music = bs.MusicType.FORWARD_MARCH

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Doom Shroom']

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        # We support any teams or versus sessions.
        return issubclass(sessiontype, bs.CoopSession) or issubclass(
            sessiontype, bs.MultiTeamSession
        )

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._targets: list[Target] = []
        self._update_timer: bs.Timer | None = None
        self._countdown: OnScreenCountdown | None = None
        self._target_count = int(settings['Target Count'])
        self._enable_impact_bombs = bool(settings['Enable Impact Bombs'])
        self._enable_triple_bombs = bool(settings['Enable Triple Bombs'])

    @override
    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self.update_scoreboard()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.update_scoreboard()

        # Number of targets is based on player count.
        for i in range(self._target_count):
            bs.timer(5.0 + i * 1.0, self._spawn_target)

        self._update_timer = bs.Timer(1.0, self._update, repeat=True)
        self._countdown = OnScreenCountdown(60, endcall=self.end_game)
        bs.timer(4.0, self._countdown.start)

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        spawn_center = (0, 3, -5)
        pos = (
            spawn_center[0] + random.uniform(-1.5, 1.5),
            spawn_center[1],
            spawn_center[2] + random.uniform(-1.5, 1.5),
        )

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
            points.append(bs.Vec3(8.0 * xpos, 2.2, -3.5 + 5.0 * ypos))

        def get_min_dist_from_target(pnt: bs.Vec3) -> float:
            return min((t.get_dist_from_point(pnt) for t in self._targets))

        # If we have existing targets, use the point with the highest
        # min-distance-from-targets.
        if self._targets:
            point = max(points, key=get_min_dist_from_target)
        else:
            point = points[0]

        self._targets.append(Target(position=point))

    def _on_spaz_dropped_bomb(self, spaz: bs.Actor, bomb: bs.Actor) -> None:
        del spaz  # Unused.

        # Wire up this bomb to inform us when it blows up.
        assert isinstance(bomb, Bomb)
        bomb.add_explode_callback(self._on_bomb_exploded)

    def _on_bomb_exploded(self, bomb: Bomb, blast: Blast) -> None:
        assert blast.node
        pos = blast.node.position

        # Debugging: throw a locator down where we landed.
        # bs.newnode('locator', attrs={'position':blast.node.position})

        # Feed the explosion point to all our targets and get points in return.
        # Note: we operate on a copy of self._targets since the list may change
        # under us if we hit stuff (don't wanna get points for new targets).
        player = bomb.get_source_player(Player)
        if not player:
            # It's possible the player left after throwing the bomb.
            return

        bullseye = any(
            target.do_hit_at_position(pos, player)
            for target in list(self._targets)
        )
        if bullseye:
            player.streak += 1
        else:
            player.streak = 0

    def _update(self) -> None:
        """Misc. periodic updating."""
        # Clear out targets that have died.
        self._targets = [t for t in self._targets if t]

    @override
    def handlemessage(self, msg: Any) -> Any:
        # When players die, respawn them.
        if isinstance(msg, bs.PlayerDiedMessage):
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

    @override
    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results)


class Target(bs.Actor):
    """A target practice target."""

    class TargetHitMessage:
        """Inform an object a target was hit."""

    def __init__(self, position: Sequence[float]):
        self._r1 = 0.45
        self._r2 = 1.1
        self._r3 = 2.0
        self._rfudge = 0.15
        super().__init__()
        self._position = bs.Vec3(position)
        self._hit = False

        # It can be handy to test with this on to make sure the projection
        # isn't too far off from the actual object.
        show_in_space = False
        loc1 = bs.newnode(
            'locator',
            attrs={
                'shape': 'circle',
                'position': position,
                'color': (0, 1, 0),
                'opacity': 0.5,
                'draw_beauty': show_in_space,
                'additive': True,
            },
        )
        loc2 = bs.newnode(
            'locator',
            attrs={
                'shape': 'circleOutline',
                'position': position,
                'color': (0, 1, 0),
                'opacity': 0.3,
                'draw_beauty': False,
                'additive': True,
            },
        )
        loc3 = bs.newnode(
            'locator',
            attrs={
                'shape': 'circleOutline',
                'position': position,
                'color': (0, 1, 0),
                'opacity': 0.1,
                'draw_beauty': False,
                'additive': True,
            },
        )
        self._nodes = [loc1, loc2, loc3]
        bs.animate_array(loc1, 'size', 1, {0: [0.0], 0.2: [self._r1 * 2.0]})
        bs.animate_array(loc2, 'size', 1, {0.05: [0.0], 0.25: [self._r2 * 2.0]})
        bs.animate_array(loc3, 'size', 1, {0.1: [0.0], 0.3: [self._r3 * 2.0]})
        bs.getsound('laserReverse').play()

    @override
    def exists(self) -> bool:
        return bool(self._nodes)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            for node in self._nodes:
                node.delete()
            self._nodes = []
        else:
            super().handlemessage(msg)

    def get_dist_from_point(self, pos: bs.Vec3) -> float:
        """Given a point, returns distance squared from it."""
        return (pos - self._position).length()

    def do_hit_at_position(self, pos: Sequence[float], player: Player) -> bool:
        """Handle a bomb hit at the given position."""
        # pylint: disable=too-many-statements
        activity = self.activity

        # Ignore hits if the game is over or if we've already been hit
        if activity.has_ended() or self._hit or not self._nodes:
            return False

        diff = bs.Vec3(pos) - self._position

        # Disregard Y difference. Our target point probably isn't exactly
        # on the ground anyway.
        diff[1] = 0.0
        dist = diff.length()

        bullseye = False
        if dist <= self._r3 + self._rfudge:
            # Inform our activity that we were hit
            self._hit = True
            activity.handlemessage(self.TargetHitMessage())
            keys: dict[float, Sequence[float]] = {
                0.0: (1.0, 0.0, 0.0),
                0.049: (1.0, 0.0, 0.0),
                0.05: (1.0, 1.0, 1.0),
                0.1: (0.0, 1.0, 0.0),
            }
            cdull = (0.3, 0.3, 0.3)
            popupcolor: Sequence[float]
            if dist <= self._r1 + self._rfudge:
                bullseye = True
                self._nodes[1].color = cdull
                self._nodes[2].color = cdull
                bs.animate_array(self._nodes[0], 'color', 3, keys, loop=True)
                popupscale = 1.8
                popupcolor = (1, 1, 0, 1)
                streak = player.streak
                points = 10 + min(20, streak * 2)
                bs.getsound('bellHigh').play()
                if streak > 0:
                    bs.getsound(
                        'orchestraHit4'
                        if streak > 3
                        else (
                            'orchestraHit3'
                            if streak > 2
                            else (
                                'orchestraHit2'
                                if streak > 1
                                else 'orchestraHit'
                            )
                        )
                    ).play()
            elif dist <= self._r2 + self._rfudge:
                self._nodes[0].color = cdull
                self._nodes[2].color = cdull
                bs.animate_array(self._nodes[1], 'color', 3, keys, loop=True)
                popupscale = 1.25
                popupcolor = (1, 0.5, 0.2, 1)
                points = 4
                bs.getsound('bellMed').play()
            else:
                self._nodes[0].color = cdull
                self._nodes[1].color = cdull
                bs.animate_array(self._nodes[2], 'color', 3, keys, loop=True)
                popupscale = 1.0
                popupcolor = (0.8, 0.3, 0.3, 1)
                points = 2
                bs.getsound('bellLow').play()

            # Award points/etc.. (technically should probably leave this up
            # to the activity).
            popupstr = '+' + str(points)

            # If there's more than 1 player in the game, include their
            # names and colors so they know who got the hit.
            if len(activity.players) > 1:
                popupcolor = bs.safecolor(player.color, target_intensity=0.75)
                popupstr += ' ' + player.getname()
            PopupText(
                popupstr,
                position=self._position,
                color=popupcolor,
                scale=popupscale,
            ).autoretain()

            # Give this player's team points and update the score-board.
            player.team.score += points
            assert isinstance(activity, TargetPracticeGame)
            activity.update_scoreboard()

            # Also give this individual player points
            # (only applies in teams mode).
            assert activity.stats is not None
            activity.stats.player_scored(
                player, points, showpoints=False, screenmessage=False
            )

            bs.animate_array(
                self._nodes[0],
                'size',
                1,
                {0.8: self._nodes[0].size, 1.0: [0.0]},
            )
            bs.animate_array(
                self._nodes[1],
                'size',
                1,
                {0.85: self._nodes[1].size, 1.05: [0.0]},
            )
            bs.animate_array(
                self._nodes[2],
                'size',
                1,
                {0.9: self._nodes[2].size, 1.1: [0.0]},
            )
            bs.timer(1.1, bs.Call(self.handlemessage, bs.DieMessage()))

        return bullseye
