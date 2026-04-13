# Released under the MIT License. See LICENSE for details.
#
"""Hockey game and support classes."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.powerupbox import PowerupBoxFactory
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


class PuckDiedMessage:
    """Inform something that a puck has died."""

    def __init__(self, puck: Puck):
        self.puck = puck


class Puck(bs.Actor):
    """A lovely giant hockey puck."""

    def __init__(self, position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        shared = SharedObjects.get()
        activity = self.getactivity()

        # Spawn just above the provided point.
        self._spawn_pos = (position[0], position[1] + 1.0, position[2])
        self.last_players_to_touch: dict[int, Player] = {}
        self.scored = False
        assert activity is not None
        assert isinstance(activity, HockeyGame)
        pmats = [shared.object_material, activity.puck_material]
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': activity.puck_mesh,
                'color_texture': activity.puck_tex,
                'body': 'puck',
                'reflection': 'soft',
                'reflection_scale': [0.2],
                'shadow_size': 1.0,
                'is_area_of_interest': True,
                'position': self._spawn_pos,
                'materials': pmats,
            },
        )
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: 1.3, 0.26: 1})

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
                activity = self._activity()
                if activity and not msg.immediate:
                    activity.handlemessage(PuckDiedMessage(self))

        # If we go out of bounds, move back to where we started.
        elif isinstance(msg, bs.OutOfBoundsMessage):
            assert self.node
            self.node.position = self._spawn_pos

        elif isinstance(msg, bs.HitMessage):
            assert self.node
            assert msg.force_direction is not None
            self.node.handlemessage(
                'impulse',
                msg.pos[0],
                msg.pos[1],
                msg.pos[2],
                msg.velocity[0],
                msg.velocity[1],
                msg.velocity[2],
                1.0 * msg.magnitude,
                1.0 * msg.velocity_magnitude,
                msg.radius,
                0,
                msg.force_direction[0],
                msg.force_direction[1],
                msg.force_direction[2],
            )

            # If this hit came from a player, log them as the last to touch us.
            s_player = msg.get_source_player(Player)
            if s_player is not None:
                activity = self._activity()
                if activity:
                    if s_player in activity.players:
                        self.last_players_to_touch[s_player.team.id] = s_player
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class HockeyGame(bs.TeamGameActivity[Player, Team]):
    """Ice hockey game."""

    name = 'Hockey'
    description = 'Score some goals.'
    available_settings = [
        bs.IntSetting(
            'Score to Win',
            min_value=1,
            default=1,
            increment=1,
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
        return bs.app.classic.getmaps('hockey')

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._cheer_sound = bs.getsound('cheer')
        self._chant_sound = bs.getsound('crowdChant')
        self._foghorn_sound = bs.getsound('foghorn')
        self._swipsound = bs.getsound('swip')
        self._whistle_sound = bs.getsound('refWhistle')
        self.puck_mesh = bs.getmesh('puck')
        self.puck_tex = bs.gettexture('puckColor')
        self._puck_sound = bs.getsound('metalHit')
        self.puck_material = bs.Material()
        self.puck_material.add_actions(
            actions=('modify_part_collision', 'friction', 0.5)
        )
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )
        self.puck_material.add_actions(
            conditions=(
                ('we_are_younger_than', 100),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=('impact_sound', self._puck_sound, 0.2, 5),
        )

        # Keep track of which player last touched the puck
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect', self._handle_puck_player_collide),),
        )

        # We want the puck to kill powerups; not get stopped by them
        self.puck_material.add_actions(
            conditions=(
                'they_have_material',
                PowerupBoxFactory.get().powerup_material,
            ),
            actions=(
                ('modify_part_collision', 'physical', False),
                ('message', 'their_node', 'at_connect', bs.DieMessage()),
            ),
        )
        self._score_region_material = bs.Material()
        self._score_region_material.add_actions(
            conditions=('they_have_material', self.puck_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._handle_score),
            ),
        )
        self._puck_spawn_pos: Sequence[float] | None = None
        self._score_regions: list[bs.NodeActor] | None = None
        self._puck: Puck | None = None
        self._score_to_win = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.HOCKEY
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        if self._score_to_win == 1:
            return 'Score a goal.'
        return 'Score ${ARG1} goals.', self._score_to_win

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        if self._score_to_win == 1:
            return 'score a goal'
        return 'score ${ARG1} goals', self._score_to_win

    @override
    def on_begin(self) -> None:
        super().on_begin()

        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._puck_spawn_pos = self.map.get_flag_position(None)
        self._spawn_puck()

        # Set up the two score regions.
        defs = self.map.defs
        self._score_regions = []
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': defs.boxes['goal1'][0:3],
                        'scale': defs.boxes['goal1'][6:9],
                        'type': 'box',
                        'materials': [self._score_region_material],
                    },
                )
            )
        )
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': defs.boxes['goal2'][0:3],
                        'scale': defs.boxes['goal2'][6:9],
                        'type': 'box',
                        'materials': [self._score_region_material],
                    },
                )
            )
        )
        self._update_scoreboard()
        self._chant_sound.play()

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        self._update_scoreboard()

    def _handle_puck_player_collide(self) -> None:
        collision = bs.getcollision()
        try:
            puck = collision.sourcenode.getdelegate(Puck, True)
            player = collision.opposingnode.getdelegate(
                PlayerSpaz, True
            ).getplayer(Player, True)
        except bs.NotFoundError:
            return

        puck.last_players_to_touch[player.team.id] = player

    def _kill_puck(self) -> None:
        self._puck = None

    def _handle_score(self) -> None:
        """A point has been scored."""

        assert self._puck is not None
        assert self._score_regions is not None

        # Our puck might stick around for a second or two
        # we don't want it to be able to score again.
        if self._puck.scored:
            return

        region = bs.getcollision().sourcenode
        index = 0
        for index, score_region in enumerate(self._score_regions):
            if region == score_region.node:
                break

        for team in self.teams:
            if team.id == index:
                scoring_team = team
                team.score += 1

                # Tell all players to celebrate.
                for player in team.players:
                    if player.actor:
                        player.actor.handlemessage(bs.CelebrateMessage(2.0))

                # If we've got the player from the scoring team that last
                # touched us, give them points.
                if (
                    scoring_team.id in self._puck.last_players_to_touch
                    and self._puck.last_players_to_touch[scoring_team.id]
                ):
                    self.stats.player_scored(
                        self._puck.last_players_to_touch[scoring_team.id],
                        100,
                        big_message=True,
                    )

                # End game if we won.
                if team.score >= self._score_to_win:
                    self.end_game()

        self._foghorn_sound.play()
        self._cheer_sound.play()

        self._puck.scored = True

        # Kill the puck (it'll respawn itself shortly).
        bs.timer(1.0, self._kill_puck)

        light = bs.newnode(
            'light',
            attrs={
                'position': bs.getcollision().position,
                'height_attenuated': False,
                'color': (1, 0, 0),
            },
        )
        bs.animate(light, 'intensity', {0: 0, 0.5: 1, 1.0: 0}, loop=True)
        bs.timer(1.0, light.delete)

        bs.cameraflash(duration=10.0)
        self._update_scoreboard()

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def _update_scoreboard(self) -> None:
        winscore = self._score_to_win
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score, winscore)

    @override
    def handlemessage(self, msg: Any) -> Any:
        """Handle arbitrary message."""
        # Respawn dead players if they're still in the game.
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior...
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))

        # Respawn dead pucks.
        elif isinstance(msg, PuckDiedMessage):
            if not self.has_ended():
                bs.timer(3.0, self._spawn_puck)
        else:
            super().handlemessage(msg)

    def _flash_puck_spawn(self) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': self._puck_spawn_pos,
                'height_attenuated': False,
                'color': (1, 0, 0),
            },
        )
        bs.animate(light, 'intensity', {0.0: 0, 0.25: 1, 0.5: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def _spawn_puck(self) -> None:
        self._swipsound.play()
        self._whistle_sound.play()
        self._flash_puck_spawn()
        assert self._puck_spawn_pos is not None
        self._puck = Puck(position=self._puck_spawn_pos)
