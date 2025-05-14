# Released under the MIT License. See LICENSE for details.
#
"""Provides the chosen-one mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.flag import Flag
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.chosen_light: bs.NodeActor | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self, time_remaining: int) -> None:
        self.time_remaining = time_remaining


# ba_meta export bascenev1.GameActivity
class ChosenOneGame(bs.TeamGameActivity[Player, Team]):
    """
    Game involving trying to remain the one 'chosen one'
    for a set length of time while everyone else tries to
    kill you and become the chosen one themselves.
    """

    name = 'Chosen One'
    description = (
        'Be the chosen one for a length of time to win.\n'
        'Kill the chosen one to become it.'
    )
    available_settings = [
        bs.IntSetting(
            'Chosen One Time',
            min_value=10,
            default=30,
            increment=10,
        ),
        bs.BoolSetting('Chosen One Gets Gloves', default=True),
        bs.BoolSetting('Chosen One Gets Shield', default=False),
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
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('keep_away')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._chosen_one_player: Player | None = None
        self._swipsound = bs.getsound('swip')
        self._countdownsounds: dict[int, bs.Sound] = {
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
        self._reset_region_material: bs.Material | None = None
        self._flag: Flag | None = None
        self._reset_region: bs.Node | None = None
        self._epic_mode = bool(settings['Epic Mode'])
        self._chosen_one_time = int(settings['Chosen One Time'])
        self._time_limit = float(settings['Time Limit'])
        self._chosen_one_gets_shield = bool(settings['Chosen One Gets Shield'])
        self._chosen_one_gets_gloves = bool(settings['Chosen One Gets Gloves'])

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.CHOSEN_ONE
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'There can be only one.'

    @override
    def create_team(self, sessionteam: bs.SessionTeam) -> Team:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return Team(time_remaining=self._chosen_one_time)

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        self._update_scoreboard()

    @override
    def on_player_leave(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        super().on_player_leave(player)
        if self._get_chosen_one_player() is player:
            self._set_chosen_one_player(None)

    @override
    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        Flag.project_stand(self._flag_spawn_pos)
        bs.timer(1.0, call=self._tick, repeat=True)

        mat = self._reset_region_material = bs.Material()
        mat.add_actions(
            conditions=(
                'they_have_material',
                shared.player_material,
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', bs.WeakCall(self._handle_reset_collide)),
            ),
        )

        self._set_chosen_one_player(None)

    def _create_reset_region(self) -> None:
        assert self._reset_region_material is not None
        assert self._flag_spawn_pos is not None
        pos = self._flag_spawn_pos
        self._reset_region = bs.newnode(
            'region',
            attrs={
                'position': (pos[0], pos[1] + 0.75, pos[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [self._reset_region_material],
            },
        )

    def _get_chosen_one_player(self) -> Player | None:
        # Should never return invalid references; return None in that case.
        if self._chosen_one_player:
            return self._chosen_one_player
        return None

    def _handle_reset_collide(self) -> None:
        # If we have a chosen one, ignore these.
        if self._get_chosen_one_player() is not None:
            return

        # Attempt to get a Actor that we hit.
        try:
            spaz = bs.getcollision().opposingnode.getdelegate(PlayerSpaz, True)
            player = spaz.getplayer(Player, True)
        except bs.NotFoundError:
            return

        if spaz.is_alive():
            self._set_chosen_one_player(player)

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
        bs.animate(light, 'intensity', {0: 0, 0.25: 0.5, 0.5: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def _tick(self) -> None:
        # Give the chosen one points.
        player = self._get_chosen_one_player()
        if player is not None:
            # This shouldn't happen, but just in case.
            if not player.is_alive():
                logging.error('got dead player as chosen one in _tick')
                self._set_chosen_one_player(None)
            else:
                scoring_team = player.team
                self.stats.player_scored(
                    player, 3, screenmessage=False, display=False
                )

                scoring_team.time_remaining = max(
                    0, scoring_team.time_remaining - 1
                )

                # Show the count over their head
                if scoring_team.time_remaining > 0:
                    if isinstance(player.actor, PlayerSpaz) and player.actor:
                        player.actor.set_score_text(
                            str(scoring_team.time_remaining)
                        )

                self._update_scoreboard()

                # announce numbers we have sounds for
                if scoring_team.time_remaining in self._countdownsounds:
                    self._countdownsounds[scoring_team.time_remaining].play()

                # Winner!
                if scoring_team.time_remaining <= 0:
                    self.end_game()

        else:
            # (player is None)
            # This shouldn't happen, but just in case.
            # (Chosen-one player ceasing to exist should
            # trigger on_player_leave which resets chosen-one)
            if self._chosen_one_player is not None:
                logging.error('got nonexistent player as chosen one in _tick')
                self._set_chosen_one_player(None)

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(
                team, self._chosen_one_time - team.time_remaining
            )
        self.end(results=results, announce_delay=0)

    def _set_chosen_one_player(self, player: Player | None) -> None:
        existing = self._get_chosen_one_player()
        if existing:
            existing.chosen_light = None
        self._swipsound.play()
        if not player:
            assert self._flag_spawn_pos is not None
            self._flag = Flag(
                color=(1, 0.9, 0.2),
                position=self._flag_spawn_pos,
                touchable=False,
            )
            self._chosen_one_player = None

            # Create a light to highlight the flag;
            # this will go away when the flag dies.
            bs.newnode(
                'light',
                owner=self._flag.node,
                attrs={
                    'position': self._flag_spawn_pos,
                    'intensity': 0.6,
                    'height_attenuated': False,
                    'volume_intensity_scale': 0.1,
                    'radius': 0.1,
                    'color': (1.2, 1.2, 0.4),
                },
            )

            # Also an extra momentary flash.
            self._flash_flag_spawn()

            # Re-create our flag region in case if someone is waiting for
            # flag right there:
            self._create_reset_region()
        else:
            if player.actor:
                self._flag = None
                self._chosen_one_player = player

                if self._chosen_one_gets_shield:
                    player.actor.handlemessage(bs.PowerupMessage('shield'))
                if self._chosen_one_gets_gloves:
                    player.actor.handlemessage(bs.PowerupMessage('punch'))

                # Use a color that's partway between their team color
                # and white.
                color = [
                    0.3 + c * 0.7
                    for c in bs.normalized_color(player.team.color)
                ]
                light = player.chosen_light = bs.NodeActor(
                    bs.newnode(
                        'light',
                        attrs={
                            'intensity': 0.6,
                            'height_attenuated': False,
                            'volume_intensity_scale': 0.1,
                            'radius': 0.13,
                            'color': color,
                        },
                    )
                )

                assert light.node
                bs.animate(
                    light.node,
                    'intensity',
                    {0: 1.0, 0.2: 0.4, 0.4: 1.0},
                    loop=True,
                )
                assert isinstance(player.actor, PlayerSpaz)
                player.actor.node.connectattr(
                    'position', light.node, 'position'
                )

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if player is self._get_chosen_one_player():
                killerplayer = msg.getkillerplayer(Player)
                self._set_chosen_one_player(
                    None
                    if (
                        killerplayer is None
                        or killerplayer is player
                        or not killerplayer.is_alive()
                    )
                    else killerplayer
                )
            self.respawn_player(player)
        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.time_remaining, self._chosen_one_time, countdown=True
            )
