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
"""Provides the Conquest game."""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor.flag import Flag
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.playerspaz import PlayerSpaz
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Optional, Type, List, Dict, Sequence, Union
    from bastd.actor.respawnicon import RespawnIcon


class ConquestFlag(Flag):
    """A custom flag for use with Conquest games."""

    def __init__(self, *args: Any, **keywds: Any):
        super().__init__(*args, **keywds)
        self._team: Optional[Team] = None
        self.light: Optional[ba.Node] = None

    @property
    def team(self) -> Optional[Team]:
        """The team that owns this flag."""
        return self._team

    @team.setter
    def team(self, team: Team) -> None:
        """Set the team that owns this flag."""
        self._team = team


class Player(ba.Player['Team']):
    """Our player type for this game."""

    # FIXME: We shouldn't be using customdata here
    # (but need to update respawn funcs accordingly first).
    @property
    def respawn_timer(self) -> Optional[ba.Timer]:
        """Type safe access to standard respawn timer."""
        return self.customdata.get('respawn_timer', None)

    @respawn_timer.setter
    def respawn_timer(self, value: Optional[ba.Timer]) -> None:
        self.customdata['respawn_timer'] = value

    @property
    def respawn_icon(self) -> Optional[RespawnIcon]:
        """Type safe access to standard respawn icon."""
        return self.customdata.get('respawn_icon', None)

    @respawn_icon.setter
    def respawn_icon(self, value: Optional[RespawnIcon]) -> None:
        self.customdata['respawn_icon'] = value


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.flags_held = 0


# ba_meta export game
class ConquestGame(ba.TeamGameActivity[Player, Team]):
    """A game where teams try to claim all flags on the map."""

    name = 'Conquest'
    description = 'Secure all flags on the map to win.'
    available_settings = [
        ba.IntChoiceSetting(
            'Time Limit',
            choices=[
                ('None', 0),
                ('1 Minute', 60),
                ('2 Minutes', 120),
                ('5 Minutes', 300),
                ('10 Minutes', 600),
                ('20 Minutes', 1200),
            ],
            default=0,
        ),
        ba.FloatChoiceSetting(
            'Respawn Times',
            choices=[
                ('Shorter', 0.25),
                ('Short', 0.5),
                ('Normal', 1.0),
                ('Long', 2.0),
                ('Longer', 4.0),
            ],
            default=1.0,
        ),
        ba.BoolSetting('Epic Mode', default=False),
    ]

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('conquest')

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._score_sound = ba.getsound('score')
        self._swipsound = ba.getsound('swip')
        self._extraflagmat = ba.Material()
        self._flags: List[ConquestFlag] = []
        self._epic_mode = bool(settings['Epic Mode'])
        self._time_limit = float(settings['Time Limit'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.GRAND_ROMP)

        # We want flags to tell us they've been hit but not react physically.
        self._extraflagmat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('call', 'at_connect', self._handle_flag_player_collide),
            ))

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Secure all ${ARG1} flags.', len(self.map.flag_points)

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return 'secure all ${ARG1} flags', len(self.map.flag_points)

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scores()

    def on_player_join(self, player: Player) -> None:
        player.respawn_timer = None

        # Only spawn if this player's team has a flag currently.
        if player.team.flags_held > 0:
            self.spawn_player(player)

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()

        # Set up flags with marker lights.
        for i in range(len(self.map.flag_points)):
            point = self.map.flag_points[i]
            flag = ConquestFlag(position=point,
                                touchable=False,
                                materials=[self._extraflagmat])
            self._flags.append(flag)
            Flag.project_stand(point)
            flag.light = ba.newnode('light',
                                    owner=flag.node,
                                    attrs={
                                        'position': point,
                                        'intensity': 0.25,
                                        'height_attenuated': False,
                                        'radius': 0.3,
                                        'color': (1, 1, 1)
                                    })

        # Give teams a flag to start with.
        for i in range(len(self.teams)):
            self._flags[i].team = self.teams[i]
            light = self._flags[i].light
            assert light
            node = self._flags[i].node
            assert node
            light.color = self.teams[i].color
            node.color = self.teams[i].color

        self._update_scores()

        # Initial joiners didn't spawn due to no flags being owned yet;
        # spawn them now.
        for player in self.players:
            self.spawn_player(player)

    def _update_scores(self) -> None:
        for team in self.teams:
            team.flags_held = 0
        for flag in self._flags:
            if flag.team is not None:
                flag.team.flags_held += 1
        for team in self.teams:

            # If a team finds themselves with no flags, cancel all
            # outstanding spawn-timers.
            if team.flags_held == 0:
                for player in team.players:
                    player.respawn_timer = None
                    player.respawn_icon = None
            if team.flags_held == len(self._flags):
                self.end_game()
            self._scoreboard.set_team_value(team, team.flags_held,
                                            len(self._flags))

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.flags_held)
        self.end(results=results)

    def _flash_flag(self, flag: ConquestFlag, length: float = 1.0) -> None:
        assert flag.node
        assert flag.light
        light = ba.newnode('light',
                           attrs={
                               'position': flag.node.position,
                               'height_attenuated': False,
                               'color': flag.light.color
                           })
        ba.animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0}, loop=True)
        ba.timer(length, light.delete)

    def _handle_flag_player_collide(self) -> None:
        collision = ba.getcollision()
        try:
            flag = collision.sourcenode.getdelegate(ConquestFlag, True)
            player = collision.opposingnode.getdelegate(PlayerSpaz,
                                                        True).getplayer(
                                                            Player, True)
        except ba.NotFoundError:
            return
        assert flag.light

        if flag.team is not player.team:
            flag.team = player.team
            flag.light.color = player.team.color
            flag.node.color = player.team.color
            self.stats.player_scored(player, 10, screenmessage=False)
            ba.playsound(self._swipsound)
            self._flash_flag(flag)
            self._update_scores()

            # Respawn any players on this team that were in limbo due to the
            # lack of a flag for their team.
            for otherplayer in self.players:
                if (otherplayer.team is flag.team
                        and otherplayer.actor is not None
                        and not otherplayer.is_alive()
                        and otherplayer.respawn_timer is None):
                    self.spawn_player(otherplayer)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            # Respawn only if this team has a flag.
            player = msg.getplayer(Player)
            if player.team.flags_held > 0:
                self.respawn_player(player)
            else:
                player.respawn_timer = None

        else:
            super().handlemessage(msg)

    def spawn_player(self, player: Player) -> ba.Actor:
        # We spawn players at different places based on what flags are held.
        return self.spawn_player_spaz(player,
                                      self._get_player_spawn_position(player))

    def _get_player_spawn_position(self, player: Player) -> Sequence[float]:

        # Iterate until we find a spawn owned by this team.
        spawn_count = len(self.map.spawn_by_flag_points)

        # Get all spawns owned by this team.
        spawns = [
            i for i in range(spawn_count) if self._flags[i].team is player.team
        ]

        closest_spawn = 0
        closest_distance = 9999.0

        # Now find the spawn that's closest to a spawn not owned by us;
        # we'll use that one.
        for spawn in spawns:
            spt = self.map.spawn_by_flag_points[spawn]
            our_pt = ba.Vec3(spt[0], spt[1], spt[2])
            for otherspawn in [
                    i for i in range(spawn_count)
                    if self._flags[i].team is not player.team
            ]:
                spt = self.map.spawn_by_flag_points[otherspawn]
                their_pt = ba.Vec3(spt[0], spt[1], spt[2])
                dist = (their_pt - our_pt).length()
                if dist < closest_distance:
                    closest_distance = dist
                    closest_spawn = spawn

        pos = self.map.spawn_by_flag_points[closest_spawn]
        x_range = (-0.5, 0.5) if pos[3] == 0.0 else (-pos[3], pos[3])
        z_range = (-0.5, 0.5) if pos[5] == 0.0 else (-pos[5], pos[5])
        pos = (pos[0] + random.uniform(*x_range), pos[1],
               pos[2] + random.uniform(*z_range))
        return pos
