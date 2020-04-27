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
"""Provides the chosen-one mini-game."""

# ba_meta require api 6
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)
from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor import flag
from bastd.actor import playerspaz
from bastd.actor import spaz

if TYPE_CHECKING:
    from typing import (Any, Type, List, Dict, Tuple, Optional, Sequence,
                        Union)


# ba_meta export game
class ChosenOneGame(ba.TeamGameActivity):
    """
    Game involving trying to remain the one 'chosen one'
    for a set length of time while everyone else tries to
    kill you and become the chosen one themselves.
    """

    @classmethod
    def get_name(cls) -> str:
        return 'Chosen One'

    @classmethod
    def get_score_info(cls) -> Dict[str, Any]:
        return {'score_name': 'Time Held'}

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return ('Be the chosen one for a length of time to win.\n'
                'Kill the chosen one to become it.')

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('keep_away')

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        return [('Chosen One Time', {
            'min_value': 10,
            'default': 30,
            'increment': 10
        }), ('Chosen One Gets Gloves', {
            'default': True
        }), ('Chosen One Gets Shield', {
            'default': False
        }),
                ('Time Limit', {
                    'choices': [('None', 0), ('1 Minute', 60),
                                ('2 Minutes', 120), ('5 Minutes', 300),
                                ('10 Minutes', 600), ('20 Minutes', 1200)],
                    'default': 0
                }),
                ('Respawn Times', {
                    'choices': [('Shorter', 0.25), ('Short', 0.5),
                                ('Normal', 1.0), ('Long', 2.0),
                                ('Longer', 4.0)],
                    'default': 1.0
                }), ('Epic Mode', {
                    'default': False
                })]

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        if self.settings['Epic Mode']:
            self.slow_motion = True
        self._scoreboard = Scoreboard()
        self._chosen_one_player: Optional[ba.Player] = None
        self._swipsound = ba.getsound('swip')
        self._countdownsounds: Dict[int, ba.Sound] = {
            10: ba.getsound('announceTen'),
            9: ba.getsound('announceNine'),
            8: ba.getsound('announceEight'),
            7: ba.getsound('announceSeven'),
            6: ba.getsound('announceSix'),
            5: ba.getsound('announceFive'),
            4: ba.getsound('announceFour'),
            3: ba.getsound('announceThree'),
            2: ba.getsound('announceTwo'),
            1: ba.getsound('announceOne')
        }
        self._flag_spawn_pos: Optional[Sequence[float]] = None
        self._reset_region_material: Optional[ba.Material] = None
        self._flag: Optional[flag.Flag] = None
        self._reset_region: Optional[ba.Node] = None

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'There can be only one.'

    def on_transition_in(self) -> None:
        self.default_music = (ba.MusicType.EPIC if self.settings['Epic Mode']
                              else ba.MusicType.CHOSEN_ONE)
        super().on_transition_in()

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['time_remaining'] = self.settings['Chosen One Time']
        self._update_scoreboard()

    def on_player_leave(self, player: ba.Player) -> None:
        ba.TeamGameActivity.on_player_leave(self, player)
        if self._get_chosen_one_player() is player:
            self._set_chosen_one_player(None)

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        self.project_flag_stand(self._flag_spawn_pos)
        self._set_chosen_one_player(None)

        pos = self._flag_spawn_pos
        ba.timer(1.0, call=self._tick, repeat=True)

        mat = self._reset_region_material = ba.Material()
        mat.add_actions(conditions=('they_have_material',
                                    ba.sharedobj('player_material')),
                        actions=(('modify_part_collision', 'collide', True),
                                 ('modify_part_collision', 'physical', False),
                                 ('call', 'at_connect',
                                  ba.WeakCall(self._handle_reset_collide))))

        self._reset_region = ba.newnode('region',
                                        attrs={
                                            'position': (pos[0], pos[1] + 0.75,
                                                         pos[2]),
                                            'scale': (0.5, 0.5, 0.5),
                                            'type': 'sphere',
                                            'materials': [mat]
                                        })

    def _get_chosen_one_player(self) -> Optional[ba.Player]:
        if self._chosen_one_player:
            return self._chosen_one_player
        return None

    def _handle_reset_collide(self) -> None:
        # If we have a chosen one, ignore these.
        if self._get_chosen_one_player() is not None:
            return
        try:
            player = (ba.get_collision_info(
                'opposing_node').getdelegate().getplayer())
        except Exception:
            return
        if player is not None and player.is_alive():
            self._set_chosen_one_player(player)

    def _flash_flag_spawn(self) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': self._flag_spawn_pos,
                               'color': (1, 1, 1),
                               'radius': 0.3,
                               'height_attenuated': False
                           })
        ba.animate(light, 'intensity', {0: 0, 0.25: 0.5, 0.5: 0}, loop=True)
        ba.timer(1.0, light.delete)

    def _tick(self) -> None:

        # Give the chosen one points.
        player = self._get_chosen_one_player()
        if player is not None:

            # This shouldn't happen, but just in case.
            if not player.is_alive():
                ba.print_error('got dead player as chosen one in _tick')
                self._set_chosen_one_player(None)
            else:
                scoring_team = player.team
                assert self.stats
                self.stats.player_scored(player,
                                         3,
                                         screenmessage=False,
                                         display=False)

                scoring_team.gamedata['time_remaining'] = max(
                    0, scoring_team.gamedata['time_remaining'] - 1)

                # show the count over their head
                try:
                    if scoring_team.gamedata['time_remaining'] > 0:
                        if isinstance(player.actor, spaz.Spaz):
                            player.actor.set_score_text(
                                str(scoring_team.gamedata['time_remaining']))
                except Exception:
                    pass

                self._update_scoreboard()

                # announce numbers we have sounds for
                try:
                    ba.playsound(self._countdownsounds[
                        scoring_team.gamedata['time_remaining']])
                except Exception:
                    pass

                # Winner!
                if scoring_team.gamedata['time_remaining'] <= 0:
                    self.end_game()

        else:
            # (player is None)
            # This shouldn't happen, but just in case.
            # (Chosen-one player ceasing to exist should
            # trigger on_player_leave which resets chosen-one)
            if self._chosen_one_player is not None:
                ba.print_error('got nonexistent player as chosen one in _tick')
                self._set_chosen_one_player(None)

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(
                team, self.settings['Chosen One Time'] -
                team.gamedata['time_remaining'])
        self.end(results=results, announce_delay=0)

    def _set_chosen_one_player(self, player: Optional[ba.Player]) -> None:
        try:
            for p_other in self.players:
                p_other.gamedata['chosen_light'] = None
            ba.playsound(self._swipsound)
            if not player:
                assert self._flag_spawn_pos is not None
                self._flag = flag.Flag(color=(1, 0.9, 0.2),
                                       position=self._flag_spawn_pos,
                                       touchable=False)
                self._chosen_one_player = None

                # Create a light to highlight the flag;
                # this will go away when the flag dies.
                ba.newnode('light',
                           owner=self._flag.node,
                           attrs={
                               'position': self._flag_spawn_pos,
                               'intensity': 0.6,
                               'height_attenuated': False,
                               'volume_intensity_scale': 0.1,
                               'radius': 0.1,
                               'color': (1.2, 1.2, 0.4)
                           })

                # Also an extra momentary flash.
                self._flash_flag_spawn()
            else:
                if player.actor is not None:
                    self._flag = None
                    self._chosen_one_player = player

                    if player.actor:
                        if self.settings['Chosen One Gets Shield']:
                            player.actor.handlemessage(
                                ba.PowerupMessage('shield'))
                        if self.settings['Chosen One Gets Gloves']:
                            player.actor.handlemessage(
                                ba.PowerupMessage('punch'))

                        # Use a color that's partway between their team color
                        # and white.
                        color = [
                            0.3 + c * 0.7
                            for c in ba.normalized_color(player.team.color)
                        ]
                        light = player.gamedata['chosen_light'] = ba.NodeActor(
                            ba.newnode('light',
                                       attrs={
                                           'intensity': 0.6,
                                           'height_attenuated': False,
                                           'volume_intensity_scale': 0.1,
                                           'radius': 0.13,
                                           'color': color
                                       }))

                        assert light.node
                        ba.animate(light.node,
                                   'intensity', {
                                       0: 1.0,
                                       0.2: 0.4,
                                       0.4: 1.0
                                   },
                                   loop=True)
                        assert isinstance(player.actor, playerspaz.PlayerSpaz)
                        player.actor.node.connectattr('position', light.node,
                                                      'position')

        except Exception:
            ba.print_exception('EXC in _set_chosen_one_player')

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.spaz.player
            if player is self._get_chosen_one_player():
                killerplayer = msg.killerplayer
                self._set_chosen_one_player(None if (
                    killerplayer is None or killerplayer is player
                    or not killerplayer.is_alive()) else killerplayer)
            self.respawn_player(player)
        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team,
                                            team.gamedata['time_remaining'],
                                            self.settings['Chosen One Time'],
                                            countdown=True)
