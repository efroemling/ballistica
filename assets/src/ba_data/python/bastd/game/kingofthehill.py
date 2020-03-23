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
"""Defines the King of the Hill game."""

# ba_meta require api 6
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba
from bastd.actor import flag as stdflag
from bastd.actor import playerspaz

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import (Any, Type, List, Dict, Tuple, Optional, Sequence,
                        Union)


# ba_meta export game
class KingOfTheHillGame(ba.TeamGameActivity):
    """Game where a team wins by holding a 'hill' for a set amount of time."""

    FLAG_NEW = 0
    FLAG_UNCONTESTED = 1
    FLAG_CONTESTED = 2
    FLAG_HELD = 3

    @classmethod
    def get_name(cls) -> str:
        return 'King of the Hill'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Secure the flag for a set length of time.'

    @classmethod
    def get_score_info(cls) -> Dict[str, Any]:
        return {'score_name': 'Time Held'}

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.TeamBaseSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps("king_of_the_hill")

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        return [("Hold Time", {
            'min_value': 10,
            'default': 30,
            'increment': 10
        }),
                ("Time Limit", {
                    'choices': [('None', 0), ('1 Minute', 60),
                                ('2 Minutes', 120), ('5 Minutes', 300),
                                ('10 Minutes', 600), ('20 Minutes', 1200)],
                    'default': 0
                }),
                ("Respawn Times", {
                    'choices': [('Shorter', 0.25), ('Short', 0.5),
                                ('Normal', 1.0), ('Long', 2.0),
                                ('Longer', 4.0)],
                    'default': 1.0
                })]

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._swipsound = ba.getsound("swip")
        self._tick_sound = ba.getsound('tick')
        self._countdownsounds = {
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
        self._flag_pos: Optional[Sequence[float]] = None
        self._flag_state: Optional[int] = None
        self._flag: Optional[stdflag.Flag] = None
        self._flag_light: Optional[ba.Node] = None
        self._scoring_team: Optional[ReferenceType[ba.Team]] = None

        self._flag_region_material = ba.Material()
        self._flag_region_material.add_actions(
            conditions=("they_have_material", ba.sharedobj('player_material')),
            actions=(("modify_part_collision", "collide",
                      True), ("modify_part_collision", "physical", False),
                     ("call", "at_connect",
                      ba.Call(self._handle_player_flag_region_collide, True)),
                     ("call", "at_disconnect",
                      ba.Call(self._handle_player_flag_region_collide,
                              False))))

    def get_instance_description(self) -> Union[str, Sequence]:
        return ('Secure the flag for ${ARG1} seconds.',
                self.settings['Hold Time'])

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        return ('secure the flag for ${ARG1} seconds',
                self.settings['Hold Time'])

    # noinspection PyMethodOverriding
    def on_transition_in(self) -> None:  # type: ignore
        # FIXME: Unify these args.
        # pylint: disable=arguments-differ
        ba.TeamGameActivity.on_transition_in(self, music='Scary')

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['time_remaining'] = self.settings["Hold Time"]
        self._update_scoreboard()

    def on_player_join(self, player: ba.Player) -> None:
        ba.TeamGameActivity.on_player_join(self, player)
        player.gamedata['at_flag'] = 0

    def on_begin(self) -> None:
        ba.TeamGameActivity.on_begin(self)
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()
        self._flag_pos = self.map.get_flag_position(None)
        ba.timer(1.0, self._tick, repeat=True)
        self._flag_state = self.FLAG_NEW
        self.project_flag_stand(self._flag_pos)

        self._flag = stdflag.Flag(position=self._flag_pos,
                                  touchable=False,
                                  color=(1, 1, 1))
        self._flag_light = ba.newnode('light',
                                      attrs={
                                          'position': self._flag_pos,
                                          'intensity': 0.2,
                                          'height_attenuated': False,
                                          'radius': 0.4,
                                          'color': (0.2, 0.2, 0.2)
                                      })

        # Flag region.
        flagmats = [
            self._flag_region_material,
            ba.sharedobj('region_material')
        ]
        ba.newnode('region',
                   attrs={
                       'position': self._flag_pos,
                       'scale': (1.8, 1.8, 1.8),
                       'type': 'sphere',
                       'materials': flagmats
                   })
        self._update_flag_state()

    def _tick(self) -> None:
        self._update_flag_state()

        # Give holding players points.
        for player in self.players:
            if player.gamedata['at_flag'] > 0:
                self.stats.player_scored(player,
                                         3,
                                         screenmessage=False,
                                         display=False)

        if self._scoring_team is None:
            scoring_team = None
        else:
            scoring_team = self._scoring_team()
        if scoring_team:

            if scoring_team.gamedata['time_remaining'] > 0:
                ba.playsound(self._tick_sound)

            scoring_team.gamedata['time_remaining'] = max(
                0, scoring_team.gamedata['time_remaining'] - 1)
            self._update_scoreboard()
            if scoring_team.gamedata['time_remaining'] > 0:
                assert self._flag is not None
                self._flag.set_score_text(
                    str(scoring_team.gamedata['time_remaining']))

            # Announce numbers we have sounds for.
            try:
                ba.playsound(self._countdownsounds[
                    scoring_team.gamedata['time_remaining']])
            except Exception:
                pass

            # winner
            if scoring_team.gamedata['time_remaining'] <= 0:
                self.end_game()

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(
                team,
                self.settings['Hold Time'] - team.gamedata['time_remaining'])
        self.end(results=results, announce_delay=0)

    def _update_flag_state(self) -> None:
        holding_teams = set(player.team for player in self.players
                            if player.gamedata['at_flag'])
        prev_state = self._flag_state
        assert self._flag_light
        assert self._flag is not None
        assert self._flag.node
        if len(holding_teams) > 1:
            self._flag_state = self.FLAG_CONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.6, 0.6, 0.1)
            self._flag.node.color = (1.0, 1.0, 0.4)
        elif len(holding_teams) == 1:
            holding_team = list(holding_teams)[0]
            self._flag_state = self.FLAG_HELD
            self._scoring_team = weakref.ref(holding_team)
            self._flag_light.color = ba.normalized_color(holding_team.color)
            self._flag.node.color = holding_team.color
        else:
            self._flag_state = self.FLAG_UNCONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.2, 0.2, 0.2)
            self._flag.node.color = (1, 1, 1)
        if self._flag_state != prev_state:
            ba.playsound(self._swipsound)

    def _handle_player_flag_region_collide(self, colliding: bool) -> None:
        playernode = ba.get_collision_info("opposing_node")
        try:
            player = playernode.getdelegate().getplayer()
        except Exception:
            return

        # Different parts of us can collide so a single value isn't enough
        # also don't count it if we're dead (flying heads shouldn't be able to
        # win the game :-)
        if colliding and player.is_alive():
            player.gamedata['at_flag'] += 1
        else:
            player.gamedata['at_flag'] = max(0, player.gamedata['at_flag'] - 1)

        self._update_flag_state()

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team,
                                            team.gamedata['time_remaining'],
                                            self.settings['Hold Time'],
                                            countdown=True)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            super().handlemessage(msg)  # Augment default.

            # No longer can count as at_flag once dead.
            player = msg.spaz.player
            player.gamedata['at_flag'] = 0
            self._update_flag_state()
            self.respawn_player(player)
