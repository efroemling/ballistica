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
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor.flag import Flag
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.scoreboard import Scoreboard
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Optional, Sequence, Union


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.chosen_light: Optional[ba.NodeActor] = None


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self, time_remaining: int) -> None:
        self.time_remaining = time_remaining


# ba_meta export game
class ChosenOneGame(ba.TeamGameActivity[Player, Team]):
    """
    Game involving trying to remain the one 'chosen one'
    for a set length of time while everyone else tries to
    kill you and become the chosen one themselves.
    """

    name = 'Chosen One'
    description = ('Be the chosen one for a length of time to win.\n'
                   'Kill the chosen one to become it.')
    available_settings = [
        ba.IntSetting(
            'Chosen One Time',
            min_value=10,
            default=30,
            increment=10,
        ),
        ba.BoolSetting('Chosen One Gets Gloves', default=True),
        ba.BoolSetting('Chosen One Gets Shield', default=False),
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
    scoreconfig = ba.ScoreConfig(label='Time Held')

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('keep_away')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._chosen_one_player: Optional[Player] = None
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
        self._flag: Optional[Flag] = None
        self._reset_region: Optional[ba.Node] = None
        self._epic_mode = bool(settings['Epic Mode'])
        self._chosen_one_time = int(settings['Chosen One Time'])
        self._time_limit = float(settings['Time Limit'])
        self._chosen_one_gets_shield = bool(settings['Chosen One Gets Shield'])
        self._chosen_one_gets_gloves = bool(settings['Chosen One Gets Gloves'])

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC
                              if self._epic_mode else ba.MusicType.CHOSEN_ONE)

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'There can be only one.'

    def create_team(self, sessionteam: ba.SessionTeam) -> Team:
        return Team(time_remaining=self._chosen_one_time)

    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        if self._get_chosen_one_player() is player:
            self._set_chosen_one_player(None)

    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        Flag.project_stand(self._flag_spawn_pos)
        self._set_chosen_one_player(None)

        pos = self._flag_spawn_pos
        ba.timer(1.0, call=self._tick, repeat=True)

        mat = self._reset_region_material = ba.Material()
        mat.add_actions(
            conditions=(
                'they_have_material',
                shared.player_material,
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 ba.WeakCall(self._handle_reset_collide)),
            ),
        )

        self._reset_region = ba.newnode('region',
                                        attrs={
                                            'position': (pos[0], pos[1] + 0.75,
                                                         pos[2]),
                                            'scale': (0.5, 0.5, 0.5),
                                            'type': 'sphere',
                                            'materials': [mat]
                                        })

    def _get_chosen_one_player(self) -> Optional[Player]:
        if self._chosen_one_player:
            return self._chosen_one_player
        return None

    def _handle_reset_collide(self) -> None:
        # If we have a chosen one, ignore these.
        if self._get_chosen_one_player() is not None:
            return

        # Attempt to get a Player controlling a Spaz that we hit.
        try:
            player = ba.getcollision().opposingnode.getdelegate(
                PlayerSpaz, True).getplayer(Player, True)
        except ba.NotFoundError:
            return

        if player.is_alive():
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

                scoring_team.time_remaining = max(
                    0, scoring_team.time_remaining - 1)

                # Show the count over their head
                if scoring_team.time_remaining > 0:
                    if isinstance(player.actor, PlayerSpaz) and player.actor:
                        player.actor.set_score_text(
                            str(scoring_team.time_remaining))

                self._update_scoreboard()

                # announce numbers we have sounds for
                if scoring_team.time_remaining in self._countdownsounds:
                    ba.playsound(
                        self._countdownsounds[scoring_team.time_remaining])

                # Winner!
                if scoring_team.time_remaining <= 0:
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
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team,
                                   self._chosen_one_time - team.time_remaining)
        self.end(results=results, announce_delay=0)

    def _set_chosen_one_player(self, player: Optional[Player]) -> None:
        for p_other in self.players:
            p_other.chosen_light = None
        ba.playsound(self._swipsound)
        if not player:
            assert self._flag_spawn_pos is not None
            self._flag = Flag(color=(1, 0.9, 0.2),
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
            if player.actor:
                self._flag = None
                self._chosen_one_player = player

                if self._chosen_one_gets_shield:
                    player.actor.handlemessage(ba.PowerupMessage('shield'))
                if self._chosen_one_gets_gloves:
                    player.actor.handlemessage(ba.PowerupMessage('punch'))

                # Use a color that's partway between their team color
                # and white.
                color = [
                    0.3 + c * 0.7
                    for c in ba.normalized_color(player.team.color)
                ]
                light = player.chosen_light = ba.NodeActor(
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
                assert isinstance(player.actor, PlayerSpaz)
                player.actor.node.connectattr('position', light.node,
                                              'position')

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if player is self._get_chosen_one_player():
                killerplayer = msg.getkillerplayer(Player)
                self._set_chosen_one_player(None if (
                    killerplayer is None or killerplayer is player
                    or not killerplayer.is_alive()) else killerplayer)
            self.respawn_player(player)
        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team,
                                            team.time_remaining,
                                            self._chosen_one_time,
                                            countdown=True)
