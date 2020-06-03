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
"""Defines assault minigame."""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.flag import Flag
from bastd.actor.scoreboard import Scoreboard
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Sequence, Union


class Player(ba.Player['Team']):
    """Our player type for this game."""


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self, base_pos: Sequence[float], flag: Flag) -> None:
        self.base_pos = base_pos
        self.flag = flag
        self.score = 0


# ba_meta export game
class AssaultGame(ba.TeamGameActivity[Player, Team]):
    """Game where you score by touching the other team's flag."""

    name = 'Assault'
    description = 'Reach the enemy flag to score.'
    available_settings = [
        ba.IntSetting(
            'Score to Win',
            min_value=1,
            default=3,
        ),
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
        return ba.getmaps('team_flag')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._last_score_time = 0.0
        self._score_sound = ba.getsound('score')
        self._base_region_materials: Dict[int, ba.Material] = {}
        self._epic_mode = bool(settings['Epic Mode'])
        self._score_to_win = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC if self._epic_mode else
                              ba.MusicType.FORWARD_MARCH)

    def get_instance_description(self) -> Union[str, Sequence]:
        if self._score_to_win == 1:
            return 'Touch the enemy flag.'
        return 'Touch the enemy flag ${ARG1} times.', self._score_to_win

    def get_instance_description_short(self) -> Union[str, Sequence]:
        if self._score_to_win == 1:
            return 'touch 1 flag'
        return 'touch ${ARG1} flags', self._score_to_win

    def create_team(self, sessionteam: ba.SessionTeam) -> Team:
        shared = SharedObjects.get()
        base_pos = self.map.get_flag_position(sessionteam.id)
        ba.newnode('light',
                   attrs={
                       'position': base_pos,
                       'intensity': 0.6,
                       'height_attenuated': False,
                       'volume_intensity_scale': 0.1,
                       'radius': 0.1,
                       'color': sessionteam.color
                   })
        Flag.project_stand(base_pos)
        flag = Flag(touchable=False,
                    position=base_pos,
                    color=sessionteam.color)
        team = Team(base_pos=base_pos, flag=flag)

        mat = self._base_region_materials[sessionteam.id] = ba.Material()
        mat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', ba.Call(self._handle_base_collide,
                                               team)),
            ),
        )

        ba.newnode(
            'region',
            owner=flag.node,
            attrs={
                'position': (base_pos[0], base_pos[1] + 0.75, base_pos[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [self._base_region_materials[sessionteam.id]]
            })

        return team

    def on_team_join(self, team: Team) -> None:
        # Can't do this in create_team because the team's color/etc. have
        # not been wired up yet at that point.
        self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard.
            self.respawn_player(msg.getplayer(Player))
        else:
            super().handlemessage(msg)

    def _flash_base(self, team: Team, length: float = 2.0) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': team.base_pos,
                               'height_attenuated': False,
                               'radius': 0.3,
                               'color': team.color
                           })
        ba.animate(light, 'intensity', {0: 0, 0.25: 2.0, 0.5: 0}, loop=True)
        ba.timer(length, light.delete)

    def _handle_base_collide(self, team: Team) -> None:
        try:
            player = ba.getcollision().opposingnode.getdelegate(
                PlayerSpaz, True).getplayer(Player, True)
        except ba.NotFoundError:
            return

        if not player.is_alive():
            return

        # If its another team's player, they scored.
        player_team = player.team
        if player_team is not team:

            # Prevent multiple simultaneous scores.
            if ba.time() != self._last_score_time:
                self._last_score_time = ba.time()
                self.stats.player_scored(player, 50, big_message=True)
                ba.playsound(self._score_sound)
                self._flash_base(team)

                # Move all players on the scoring team back to their start
                # and add flashes of light so its noticeable.
                for player in player_team.players:
                    if player.is_alive():
                        pos = player.node.position
                        light = ba.newnode('light',
                                           attrs={
                                               'position': pos,
                                               'color': player_team.color,
                                               'height_attenuated': False,
                                               'radius': 0.4
                                           })
                        ba.timer(0.5, light.delete)
                        ba.animate(light, 'intensity', {
                            0: 0,
                            0.1: 1.0,
                            0.5: 0
                        })

                        new_pos = (self.map.get_start_position(player_team.id))
                        light = ba.newnode('light',
                                           attrs={
                                               'position': new_pos,
                                               'color': player_team.color,
                                               'radius': 0.4,
                                               'height_attenuated': False
                                           })
                        ba.timer(0.5, light.delete)
                        ba.animate(light, 'intensity', {
                            0: 0,
                            0.1: 1.0,
                            0.5: 0
                        })
                        if player.actor:
                            player.actor.handlemessage(
                                ba.StandMessage(new_pos,
                                                random.uniform(0, 360)))

                # Have teammates celebrate.
                for player in player_team.players:
                    if player.actor:
                        player.actor.handlemessage(ba.CelebrateMessage(2.0))

                player_team.score += 1
                self._update_scoreboard()
                if player_team.score >= self._score_to_win:
                    self.end_game()

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)
