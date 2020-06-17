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
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import weakref
from enum import Enum
from typing import TYPE_CHECKING

import ba
from bastd.actor.flag import Flag
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.scoreboard import Scoreboard
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Any, Type, List, Dict, Optional, Sequence, Union


class FlagState(Enum):
    """States our single flag can be in."""
    NEW = 0
    UNCONTESTED = 1
    CONTESTED = 2
    HELD = 3


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.time_at_flag = 0


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self, time_remaining: int) -> None:
        self.time_remaining = time_remaining


# ba_meta export game
class KingOfTheHillGame(ba.TeamGameActivity[Player, Team]):
    """Game where a team wins by holding a 'hill' for a set amount of time."""

    name = 'King of the Hill'
    description = 'Secure the flag for a set length of time.'
    available_settings = [
        ba.IntSetting(
            'Hold Time',
            min_value=10,
            default=30,
            increment=10,
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
    ]
    scoreconfig = ba.ScoreConfig(label='Time Held')

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.MultiTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('king_of_the_hill')

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._swipsound = ba.getsound('swip')
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
        self._flag_state: Optional[FlagState] = None
        self._flag: Optional[Flag] = None
        self._flag_light: Optional[ba.Node] = None
        self._scoring_team: Optional[ReferenceType[Team]] = None
        self._hold_time = int(settings['Hold Time'])
        self._time_limit = float(settings['Time Limit'])
        self._flag_region_material = ba.Material()
        self._flag_region_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 ba.Call(self._handle_player_flag_region_collide, True)),
                ('call', 'at_disconnect',
                 ba.Call(self._handle_player_flag_region_collide, False)),
            ))

        # Base class overrides.
        self.default_music = ba.MusicType.SCARY

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Secure the flag for ${ARG1} seconds.', self._hold_time

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return 'secure the flag for ${ARG1} seconds', self._hold_time

    def create_team(self, sessionteam: ba.SessionTeam) -> Team:
        return Team(time_remaining=self._hold_time)

    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_pos = self.map.get_flag_position(None)
        ba.timer(1.0, self._tick, repeat=True)
        self._flag_state = FlagState.NEW
        Flag.project_stand(self._flag_pos)
        self._flag = Flag(position=self._flag_pos,
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
        flagmats = [self._flag_region_material, shared.region_material]
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
            if player.time_at_flag > 0:
                self.stats.player_scored(player,
                                         3,
                                         screenmessage=False,
                                         display=False)
        if self._scoring_team is None:
            scoring_team = None
        else:
            scoring_team = self._scoring_team()
        if scoring_team:

            if scoring_team.time_remaining > 0:
                ba.playsound(self._tick_sound)

            scoring_team.time_remaining = max(0,
                                              scoring_team.time_remaining - 1)
            self._update_scoreboard()
            if scoring_team.time_remaining > 0:
                assert self._flag is not None
                self._flag.set_score_text(str(scoring_team.time_remaining))

            # Announce numbers we have sounds for.
            numsound = self._countdownsounds.get(scoring_team.time_remaining)
            if numsound is not None:
                ba.playsound(numsound)

            # winner
            if scoring_team.time_remaining <= 0:
                self.end_game()

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, self._hold_time - team.time_remaining)
        self.end(results=results, announce_delay=0)

    def _update_flag_state(self) -> None:
        holding_teams = set(player.team for player in self.players
                            if player.time_at_flag)
        prev_state = self._flag_state
        assert self._flag_light
        assert self._flag is not None
        assert self._flag.node
        if len(holding_teams) > 1:
            self._flag_state = FlagState.CONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.6, 0.6, 0.1)
            self._flag.node.color = (1.0, 1.0, 0.4)
        elif len(holding_teams) == 1:
            holding_team = list(holding_teams)[0]
            self._flag_state = FlagState.HELD
            self._scoring_team = weakref.ref(holding_team)
            self._flag_light.color = ba.normalized_color(holding_team.color)
            self._flag.node.color = holding_team.color
        else:
            self._flag_state = FlagState.UNCONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.2, 0.2, 0.2)
            self._flag.node.color = (1, 1, 1)
        if self._flag_state != prev_state:
            ba.playsound(self._swipsound)

    def _handle_player_flag_region_collide(self, colliding: bool) -> None:
        try:
            player = ba.getcollision().opposingnode.getdelegate(
                PlayerSpaz, True).getplayer(Player, True)
        except ba.NotFoundError:
            return

        # Different parts of us can collide so a single value isn't enough
        # also don't count it if we're dead (flying heads shouldn't be able to
        # win the game :-)
        if colliding and player.is_alive():
            player.time_at_flag += 1
        else:
            player.time_at_flag = max(0, player.time_at_flag - 1)

        self._update_flag_state()

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team,
                                            team.time_remaining,
                                            self._hold_time,
                                            countdown=True)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment default.

            # No longer can count as time_at_flag once dead.
            player = msg.getplayer(Player)
            player.time_at_flag = 0
            self._update_flag_state()
            self.respawn_player(player)
