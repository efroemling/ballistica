# Released under the MIT License. See LICENSE for details.
#
"""Defines assault minigame."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.flag import Flag
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self, base_pos: Sequence[float], flag: Flag) -> None:

        #: Where our base is.
        self.base_pos = base_pos

        #: Flag for this team.
        self.flag = flag

        #: Current score.
        self.score = 0


# ba_meta export bascenev1.GameActivity
class AssaultGame(bs.TeamGameActivity[Player, Team]):
    """Game where you score by touching the other team's flag."""

    name = 'Assault'
    description = 'Reach the enemy flag to score.'
    available_settings = [
        bs.IntSetting(
            'Score to Win',
            min_value=1,
            default=3,
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

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('team_flag')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._last_score_time = 0.0
        self._score_sound = bs.getsound('score')
        self._base_region_materials: dict[int, bs.Material] = {}
        self._epic_mode = bool(settings['Epic Mode'])
        self._score_to_win = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.FORWARD_MARCH
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        if self._score_to_win == 1:
            return 'Touch the enemy flag.'
        return 'Touch the enemy flag ${ARG1} times.', self._score_to_win

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        if self._score_to_win == 1:
            return 'touch 1 flag'
        return 'touch ${ARG1} flags', self._score_to_win

    @override
    def create_team(self, sessionteam: bs.SessionTeam) -> Team:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        shared = SharedObjects.get()
        base_pos = self.map.get_flag_position(sessionteam.id)
        bs.newnode(
            'light',
            attrs={
                'position': base_pos,
                'intensity': 0.6,
                'height_attenuated': False,
                'volume_intensity_scale': 0.1,
                'radius': 0.1,
                'color': sessionteam.color,
            },
        )
        Flag.project_stand(base_pos)
        flag = Flag(touchable=False, position=base_pos, color=sessionteam.color)
        team = Team(base_pos=base_pos, flag=flag)

        mat = self._base_region_materials[sessionteam.id] = bs.Material()
        mat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                (
                    'call',
                    'at_connect',
                    bs.Call(self._handle_base_collide, team),
                ),
            ),
        )

        bs.newnode(
            'region',
            owner=flag.node,
            attrs={
                'position': (base_pos[0], base_pos[1] + 0.75, base_pos[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [self._base_region_materials[sessionteam.id]],
            },
        )

        return team

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        # Can't do this in create_team because the team's color/etc. have
        # not been wired up yet at that point.
        self._update_scoreboard()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard.
            self.respawn_player(msg.getplayer(Player))
        else:
            super().handlemessage(msg)

    def _flash_base(self, team: Team, length: float = 2.0) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': team.base_pos,
                'height_attenuated': False,
                'radius': 0.3,
                'color': team.color,
            },
        )
        bs.animate(light, 'intensity', {0: 0, 0.25: 2.0, 0.5: 0}, loop=True)
        bs.timer(length, light.delete)

    def _handle_base_collide(self, team: Team) -> None:
        try:
            spaz = bs.getcollision().opposingnode.getdelegate(PlayerSpaz, True)
        except bs.NotFoundError:
            return

        if not spaz.is_alive():
            return

        try:
            player = spaz.getplayer(Player, True)
        except bs.NotFoundError:
            return

        # If its another team's player, they scored.
        player_team = player.team
        if player_team is not team:
            # Prevent multiple simultaneous scores.
            if bs.time() != self._last_score_time:
                self._last_score_time = bs.time()
                self.stats.player_scored(player, 50, big_message=True)
                self._score_sound.play()
                self._flash_base(team)

                # Move all players on the scoring team back to their start
                # and add flashes of light so its noticeable.
                for player in player_team.players:
                    if player.is_alive():
                        pos = player.node.position
                        light = bs.newnode(
                            'light',
                            attrs={
                                'position': pos,
                                'color': player_team.color,
                                'height_attenuated': False,
                                'radius': 0.4,
                            },
                        )
                        bs.timer(0.5, light.delete)
                        bs.animate(light, 'intensity', {0: 0, 0.1: 1.0, 0.5: 0})

                        new_pos = self.map.get_start_position(player_team.id)
                        light = bs.newnode(
                            'light',
                            attrs={
                                'position': new_pos,
                                'color': player_team.color,
                                'radius': 0.4,
                                'height_attenuated': False,
                            },
                        )
                        bs.timer(0.5, light.delete)
                        bs.animate(light, 'intensity', {0: 0, 0.1: 1.0, 0.5: 0})
                        if player.actor:
                            random_num = random.uniform(0, 360)

                            # Slightly hacky workaround: normally,
                            # teleporting back to base with a sticky
                            # bomb stuck to you gives a crazy whiplash
                            # rubber-band effect. Running the teleport
                            # twice in a row seems to suppress that
                            # though. Would be better to fix this at a
                            # lower level, but this works for now.
                            self._teleport(player, new_pos, random_num)
                            bs.timer(
                                0.01,
                                bs.Call(
                                    self._teleport, player, new_pos, random_num
                                ),
                            )

                # Have teammates celebrate.
                for player in player_team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage(2.0))

                player_team.score += 1
                self._update_scoreboard()
                if player_team.score >= self._score_to_win:
                    self.end_game()

    def _teleport(
        self, client: Player, pos: Sequence[float], num: float
    ) -> None:
        if client.actor:
            client.actor.handlemessage(bs.StandMessage(pos, num))

    @override
    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.score, self._score_to_win
            )
