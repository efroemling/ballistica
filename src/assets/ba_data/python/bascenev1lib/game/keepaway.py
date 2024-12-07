# Released under the MIT License. See LICENSE for details.
#
"""Defines a keep-away game type."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.flag import (
    Flag,
    FlagDroppedMessage,
    FlagDiedMessage,
    FlagPickedUpMessage,
)

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


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self, timeremaining: int) -> None:
        self.timeremaining = timeremaining
        self.holdingflag = False


# ba_meta export bascenev1.GameActivity
class KeepAwayGame(bs.TeamGameActivity[Player, Team]):
    """Game where you try to keep the flag away from your enemies."""

    name = 'Keep Away'
    description = 'Carry the flag for a set length of time.'
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
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('keep_away')

    def __init__(self, settings: dict):
        super().__init__(settings)
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
        self._flag_spawn_pos: Sequence[float] | None = None
        self._update_timer: bs.Timer | None = None
        self._holding_players: list[Player] = []
        self._flag_state: FlagState | None = None
        self._flag_light: bs.Node | None = None
        self._scoring_team: Team | None = None
        self._flag: Flag | None = None
        self._hold_time = int(settings['Hold Time'])
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.KEEP_AWAY
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        return 'Carry the flag for ${ARG1} seconds.', self._hold_time

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'carry the flag for ${ARG1} seconds', self._hold_time

    @override
    def create_team(self, sessionteam: bs.SessionTeam) -> Team:
        return Team(timeremaining=self._hold_time)

    @override
    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        self._spawn_flag()
        self._update_timer = bs.Timer(1.0, call=self._tick, repeat=True)
        self._update_flag_state()
        Flag.project_stand(self._flag_spawn_pos)

    def _tick(self) -> None:
        self._update_flag_state()

        # Award points to all living players holding the flag.
        for player in self._holding_players:
            if player:
                self.stats.player_scored(
                    player, 3, screenmessage=False, display=False
                )

        scoreteam = self._scoring_team

        if scoreteam is not None:
            if scoreteam.timeremaining > 0:
                self._tick_sound.play()

            scoreteam.timeremaining = max(0, scoreteam.timeremaining - 1)
            self._update_scoreboard()
            if scoreteam.timeremaining > 0:
                assert self._flag is not None
                self._flag.set_score_text(str(scoreteam.timeremaining))

            # Announce numbers we have sounds for.
            if scoreteam.timeremaining in self._countdownsounds:
                self._countdownsounds[scoreteam.timeremaining].play()

            # Winner.
            if scoreteam.timeremaining <= 0:
                self.end_game()

    @override
    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, self._hold_time - team.timeremaining)
        self.end(results=results, announce_delay=0)

    def _update_flag_state(self) -> None:
        for team in self.teams:
            team.holdingflag = False
        self._holding_players = []
        for player in self.players:
            holdingflag = False
            try:
                assert isinstance(player.actor, (PlayerSpaz, type(None)))
                if (
                    player.actor
                    and player.actor.node
                    and player.actor.node.hold_node
                ):
                    holdingflag = (
                        player.actor.node.hold_node.getnodetype() == 'flag'
                    )
            except Exception:
                logging.exception('Error checking hold flag.')
            if holdingflag:
                self._holding_players.append(player)
                player.team.holdingflag = True

        holdingteams = set(t for t in self.teams if t.holdingflag)
        prevstate = self._flag_state
        assert self._flag is not None
        assert self._flag_light
        assert self._flag.node
        if len(holdingteams) > 1:
            self._flag_state = FlagState.CONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.6, 0.6, 0.1)
            self._flag.node.color = (1.0, 1.0, 0.4)
        elif len(holdingteams) == 1:
            holdingteam = list(holdingteams)[0]
            self._flag_state = FlagState.HELD
            self._scoring_team = holdingteam
            self._flag_light.color = bs.normalized_color(holdingteam.color)
            self._flag.node.color = holdingteam.color
        else:
            self._flag_state = FlagState.UNCONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.2, 0.2, 0.2)
            self._flag.node.color = (1, 1, 1)

        if self._flag_state != prevstate:
            self._swipsound.play()

    def _spawn_flag(self) -> None:
        self._swipsound.play()
        self._flash_flag_spawn()
        assert self._flag_spawn_pos is not None
        self._flag = Flag(dropped_timeout=20, position=self._flag_spawn_pos)
        self._flag_state = FlagState.NEW
        self._flag_light = bs.newnode(
            'light',
            owner=self._flag.node,
            attrs={'intensity': 0.2, 'radius': 0.3, 'color': (0.2, 0.2, 0.2)},
        )
        assert self._flag.node
        self._flag.node.connectattr('position', self._flag_light, 'position')
        self._update_flag_state()

    def _flash_flag_spawn(self) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': self._flag_spawn_pos,
                'color': (1, 1, 1),
                'radius': 0.3,
                'height_attenuated': False,
            },
        )
        bs.animate(light, 'intensity', {0.0: 0, 0.25: 0.5, 0.5: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.timeremaining, self._hold_time, countdown=True
            )

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))
        elif isinstance(msg, FlagDiedMessage):
            self._spawn_flag()
        elif isinstance(msg, (FlagDroppedMessage, FlagPickedUpMessage)):
            self._update_flag_state()
        else:
            super().handlemessage(msg)
