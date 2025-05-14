# Released under the MIT License. See LICENSE for details.
#
"""Defines the King of the Hill game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import weakref
from enum import Enum
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.flag import Flag
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


class FlagState(Enum):
    """States our single flag can be in."""

    NEW = 0
    UNCONTESTED = 1
    CONTESTED = 2
    HELD = 3


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.time_at_flag = 0


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self, time_remaining: int) -> None:
        self.time_remaining = time_remaining


# ba_meta export bascenev1.GameActivity
class KingOfTheHillGame(bs.TeamGameActivity[Player, Team]):
    """Game where a team wins by holding a 'hill' for a set amount of time."""

    name = 'King of the Hill'
    description = 'Secure the flag for a set length of time.'
    available_settings = [
        bs.IntSetting(
            'Hold Time',
            min_value=10,
            default=30,
            increment=10,
        ),
        bs.IntChoiceSetting(
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
        bs.FloatChoiceSetting(
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
        bs.BoolSetting('Epic Mode', default=False),
    ]
    scoreconfig = bs.ScoreConfig(label='Time Held')

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.MultiTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        assert bs.app.classic is not None
        return bs.app.classic.getmaps('king_of_the_hill')

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._swipsound = bs.getsound('swip')
        self._tick_sound = bs.getsound('tick')
        self._countdownsounds = {
            10: bs.getsound('announceTen'),
            9: bs.getsound('announceNine'),
            8: bs.getsound('announceEight'),
            7: bs.getsound('announceSeven'),
            6: bs.getsound('announceSix'),
            5: bs.getsound('announceFive'),
            4: bs.getsound('announceFour'),
            3: bs.getsound('announceThree'),
            2: bs.getsound('announceTwo'),
            1: bs.getsound('announceOne'),
        }
        self._flag_pos: Sequence[float] | None = None
        self._flag_state: FlagState | None = None
        self._flag: Flag | None = None
        self._flag_light: bs.Node | None = None
        self._scoring_team: weakref.ref[Team] | None = None
        self._hold_time = int(settings['Hold Time'])
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])
        self._flag_region_material = bs.Material()
        self._flag_region_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                (
                    'call',
                    'at_connect',
                    bs.Call(self._handle_player_flag_region_collide, True),
                ),
                (
                    'call',
                    'at_disconnect',
                    bs.Call(self._handle_player_flag_region_collide, False),
                ),
            ),
        )

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SCARY
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'Secure the flag for ${ARG1} seconds.', self._hold_time

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'secure the flag for ${ARG1} seconds', self._hold_time

    @override
    def create_team(self, sessionteam: bs.SessionTeam) -> Team:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return Team(time_remaining=self._hold_time)

    @override
    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_pos = self.map.get_flag_position(None)
        bs.timer(1.0, self._tick, repeat=True)
        self._flag_state = FlagState.NEW
        Flag.project_stand(self._flag_pos)
        self._flag = Flag(
            position=self._flag_pos, touchable=False, color=(1, 1, 1)
        )
        self._flag_light = bs.newnode(
            'light',
            attrs={
                'position': self._flag_pos,
                'intensity': 0.2,
                'height_attenuated': False,
                'radius': 0.4,
                'color': (0.2, 0.2, 0.2),
            },
        )
        # Flag region.
        flagmats = [self._flag_region_material, shared.region_material]
        bs.newnode(
            'region',
            attrs={
                'position': self._flag_pos,
                'scale': (1.8, 1.8, 1.8),
                'type': 'sphere',
                'materials': flagmats,
            },
        )
        self._update_scoreboard()
        self._update_flag_state()

    def _tick(self) -> None:
        self._update_flag_state()

        # Give holding players points.
        for player in self.players:
            if player.time_at_flag > 0:
                self.stats.player_scored(
                    player, 3, screenmessage=False, display=False
                )
        if self._scoring_team is None:
            scoring_team = None
        else:
            scoring_team = self._scoring_team()
        if scoring_team:
            if scoring_team.time_remaining > 0:
                self._tick_sound.play()

            scoring_team.time_remaining = max(
                0, scoring_team.time_remaining - 1
            )
            self._update_scoreboard()
            if scoring_team.time_remaining > 0:
                assert self._flag is not None
                self._flag.set_score_text(str(scoring_team.time_remaining))

            # Announce numbers we have sounds for.
            numsound = self._countdownsounds.get(scoring_team.time_remaining)
            if numsound is not None:
                numsound.play()

            # winner
            if scoring_team.time_remaining <= 0:
                self.end_game()

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, self._hold_time - team.time_remaining)
        self.end(results=results, announce_delay=0)

    def _update_flag_state(self) -> None:
        holding_teams = set(
            player.team for player in self.players if player.time_at_flag
        )
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
            self._flag_light.color = bs.normalized_color(holding_team.color)
            self._flag.node.color = holding_team.color
        else:
            self._flag_state = FlagState.UNCONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.2, 0.2, 0.2)
            self._flag.node.color = (1, 1, 1)
        if self._flag_state != prev_state:
            self._swipsound.play()

    def _handle_player_flag_region_collide(self, colliding: bool) -> None:
        try:
            spaz = bs.getcollision().opposingnode.getdelegate(PlayerSpaz, True)
        except bs.NotFoundError:
            return

        if not spaz.is_alive():
            return

        player = spaz.getplayer(Player, True)

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
            self._scoreboard.set_team_value(
                team, team.time_remaining, self._hold_time, countdown=True
            )

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment default.

            # No longer can count as time_at_flag once dead.
            player = msg.getplayer(Player)
            player.time_at_flag = 0
            self._update_flag_state()
            self.respawn_player(player)
