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

# bs_meta require api 6
# (see bombsquadgame.com/apichanges)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor import playerspaz

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Tuple, Sequence, Union


# bs_meta export game
class AssaultGame(ba.TeamGameActivity):
    """Game where you score by touching the other team's flag."""

    @classmethod
    def get_name(cls) -> str:
        return 'Assault'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Reach the enemy flag to score.'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.TeamsSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('team_flag')

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        return [('Score to Win', {'min_value': 1, 'default': 3}),
                ('Time Limit', {
                    'choices': [('None', 0), ('1 Minute', 60),
                                ('2 Minutes', 120), ('5 Minutes', 300),
                                ('10 Minutes', 600), ('20 Minutes', 1200)],
                    'default': 0}),
                ('Respawn Times', {
                    'choices': [('Shorter', 0.25), ('Short', 0.5),
                                ('Normal', 1.0), ('Long', 2.0),
                                ('Longer', 4.0)],
                    'default': 1.0}),
                ('Epic Mode', {'default': False})]  # yapf: disable

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        if self.settings['Epic Mode']:
            self.slow_motion = True
        self._last_score_time = 0.0
        self._score_sound = ba.getsound("score")
        self._base_region_materials: Dict[int, ba.Material] = {}

    def get_instance_description(self) -> Union[str, Sequence]:
        if self.settings['Score to Win'] == 1:
            return 'Touch the enemy flag.'
        return ('Touch the enemy flag ${ARG1} times.',
                self.settings['Score to Win'])

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        if self.settings['Score to Win'] == 1:
            return 'touch 1 flag'
        return 'touch ${ARG1} flags', self.settings['Score to Win']

    # noinspection PyMethodOverriding
    def on_transition_in(self) -> None:  # type: ignore
        # FIXME: Need to unify these parameters.
        # pylint: disable=arguments-differ
        ba.TeamGameActivity.on_transition_in(
            self,
            music='Epic' if self.settings['Epic Mode'] else 'ForwardMarch')

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['score'] = 0
        self._update_scoreboard()

    def on_begin(self) -> None:
        from bastd.actor.flag import Flag
        ba.TeamGameActivity.on_begin(self)
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()
        for team in self.teams:
            mat = self._base_region_materials[team.get_id()] = ba.Material()
            mat.add_actions(conditions=('they_have_material',
                                        ba.sharedobj('player_material')),
                            actions=(('modify_part_collision', 'collide',
                                      True), ('modify_part_collision',
                                              'physical', False),
                                     ('call', 'at_connect',
                                      ba.Call(self._handle_base_collide,
                                              team))))

        # Create a score region and flag for each team.
        for team in self.teams:
            team.gamedata['base_pos'] = self.map.get_flag_position(
                team.get_id())

            ba.newnode('light',
                       attrs={
                           'position': team.gamedata['base_pos'],
                           'intensity': 0.6,
                           'height_attenuated': False,
                           'volume_intensity_scale': 0.1,
                           'radius': 0.1,
                           'color': team.color
                       })

            self.project_flag_stand(team.gamedata['base_pos'])
            team.gamedata['flag'] = Flag(touchable=False,
                                         position=team.gamedata['base_pos'],
                                         color=team.color)
            basepos = team.gamedata['base_pos']
            ba.newnode(
                'region',
                owner=team.gamedata['flag'].node,
                attrs={
                    'position': (basepos[0], basepos[1] + 0.75, basepos[2]),
                    'scale': (0.5, 0.5, 0.5),
                    'type': 'sphere',
                    'materials': [self._base_region_materials[team.get_id()]]
                })

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            super().handlemessage(msg)  # augment standard
            self.respawn_player(msg.spaz.player)
        else:
            super().handlemessage(msg)

    def _flash_base(self, team: ba.Team, length: float = 2.0) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': team.gamedata['base_pos'],
                               'height_attenuated': False,
                               'radius': 0.3,
                               'color': team.color
                           })
        ba.animate(light, "intensity", {0: 0, 0.25: 2.0, 0.5: 0}, loop=True)
        ba.timer(length, light.delete)

    def _handle_base_collide(self, team: ba.Team) -> None:
        cval = ba.get_collision_info('opposing_node')
        try:
            player = cval.getdelegate().getplayer()
        except Exception:
            return
        if not player or not player.is_alive():
            return

        # If its another team's player, they scored.
        player_team = player.get_team()
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
                        pos = player.actor.node.position
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

                        new_pos = (self.map.get_start_position(
                            player_team.get_id()))
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
                        player.actor.handlemessage(
                            ba.StandMessage(new_pos, random.uniform(0, 360)))

                # Have teammates celebrate.
                for player in player_team.players:
                    try:
                        # Note: celebrate message is milliseconds
                        # for historical reasons.
                        player.actor.node.handlemessage('celebrate', 2000)
                    except Exception:
                        pass

                player_team.gamedata['score'] += 1
                self._update_scoreboard()
                if (player_team.gamedata['score'] >=
                        self.settings['Score to Win']):
                    self.end_game()

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(team, team.gamedata['score'])
        self.end(results=results)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.gamedata['score'],
                                            self.settings['Score to Win'])
