# Released under the MIT License. See LICENSE for details.
#
"""Provides the Conquest game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.flag import Flag
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.respawnicon import RespawnIcon

if TYPE_CHECKING:
    from typing import Any, Sequence


class ConquestFlag(Flag):
    """A custom flag for use with Conquest games."""

    def __init__(self, *args: Any, **keywds: Any):
        super().__init__(*args, **keywds)
        self._team: Team | None = None
        self.light: bs.Node | None = None

    @property
    def team(self) -> Team | None:
        """The team that owns this flag."""
        return self._team

    @team.setter
    def team(self, team: Team) -> None:
        """Set the team that owns this flag."""
        self._team = team


class Player(bs.Player['Team']):
    """Our player type for this game."""

    # FIXME: We shouldn't be using customdata here
    # (but need to update respawn funcs accordingly first).
    @property
    def respawn_timer(self) -> bs.Timer | None:
        """Type safe access to standard respawn timer."""
        val = self.customdata.get('respawn_timer', None)
        assert isinstance(val, (bs.Timer, type(None)))
        return val

    @respawn_timer.setter
    def respawn_timer(self, value: bs.Timer | None) -> None:
        self.customdata['respawn_timer'] = value

    @property
    def respawn_icon(self) -> RespawnIcon | None:
        """Type safe access to standard respawn icon."""
        val = self.customdata.get('respawn_icon', None)
        assert isinstance(val, (RespawnIcon, type(None)))
        return val

    @respawn_icon.setter
    def respawn_icon(self, value: RespawnIcon | None) -> None:
        self.customdata['respawn_icon'] = value


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.flags_held = 0


# ba_meta export bascenev1.GameActivity
class ConquestGame(bs.TeamGameActivity[Player, Team]):
    """A game where teams try to claim all flags on the map."""

    name = 'Conquest'
    description = 'Secure all flags on the map to win.'
    available_settings = [
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
        return bs.app.classic.getmaps('conquest')

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._score_sound = bs.getsound('score')
        self._swipsound = bs.getsound('swip')
        self._extraflagmat = bs.Material()
        self._flags: list[ConquestFlag] = []
        self._epic_mode = bool(settings['Epic Mode'])
        self._time_limit = float(settings['Time Limit'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.GRAND_ROMP
        )

        # We want flags to tell us they've been hit but not react physically.
        self._extraflagmat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('call', 'at_connect', self._handle_flag_player_collide),
            ),
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'Secure all ${ARG1} flags.', len(self.map.flag_points)

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'secure all ${ARG1} flags', len(self.map.flag_points)

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if self.has_begun():
            self._update_scores()

    @override
    def on_player_join(self, player: Player) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        player.respawn_timer = None

        # Only spawn if this player's team has a flag currently.
        if player.team.flags_held > 0:
            self.spawn_player(player)

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()

        # Set up flags with marker lights.
        for i, flag_point in enumerate(self.map.flag_points):
            point = flag_point
            flag = ConquestFlag(
                position=point, touchable=False, materials=[self._extraflagmat]
            )
            self._flags.append(flag)
            Flag.project_stand(point)
            flag.light = bs.newnode(
                'light',
                owner=flag.node,
                attrs={
                    'position': point,
                    'intensity': 0.25,
                    'height_attenuated': False,
                    'radius': 0.3,
                    'color': (1, 1, 1),
                },
            )

        # Give teams a flag to start with.
        for i, team in enumerate(self.teams):
            self._flags[i].team = team
            light = self._flags[i].light
            assert light
            node = self._flags[i].node
            assert node
            light.color = team.color
            node.color = team.color

        self._update_scores()

        # Initial joiners didn't spawn due to no flags being owned yet;
        # spawn them now.
        for player in self.players:
            self.spawn_player(player)

    def _update_scores(self) -> None:
        for team in self.teams:
            team.flags_held = 0
        for flag in self._flags:
            if flag.team is not None:
                flag.team.flags_held += 1
        for team in self.teams:
            # If a team finds themselves with no flags, cancel all
            # outstanding spawn-timers.
            if team.flags_held == 0:
                for player in team.players:
                    player.respawn_timer = None
                    player.respawn_icon = None
            if team.flags_held == len(self._flags):
                self.end_game()
            self._scoreboard.set_team_value(
                team, team.flags_held, len(self._flags)
            )

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.flags_held)
        self.end(results=results)

    def _flash_flag(self, flag: ConquestFlag, length: float = 1.0) -> None:
        assert flag.node
        assert flag.light
        light = bs.newnode(
            'light',
            attrs={
                'position': flag.node.position,
                'height_attenuated': False,
                'color': flag.light.color,
            },
        )
        bs.animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0}, loop=True)
        bs.timer(length, light.delete)

    def _handle_flag_player_collide(self) -> None:
        collision = bs.getcollision()
        try:
            flag = collision.sourcenode.getdelegate(ConquestFlag, True)
            player = collision.opposingnode.getdelegate(
                PlayerSpaz, True
            ).getplayer(Player, True)
        except bs.NotFoundError:
            return
        assert flag.light

        if flag.team is not player.team:
            flag.team = player.team
            flag.light.color = player.team.color
            flag.node.color = player.team.color
            self.stats.player_scored(player, 10, screenmessage=False)
            self._swipsound.play()
            self._flash_flag(flag)
            self._update_scores()

            # Respawn any players on this team that were in limbo due to the
            # lack of a flag for their team.
            for otherplayer in self.players:
                if (
                    otherplayer.team is flag.team
                    and otherplayer.actor is not None
                    and not otherplayer.is_alive()
                    and otherplayer.respawn_timer is None
                ):
                    self.spawn_player(otherplayer)

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            # Respawn only if this team has a flag.
            player = msg.getplayer(Player)
            if player.team.flags_held > 0:
                self.respawn_player(player)
            else:
                player.respawn_timer = None

        else:
            super().handlemessage(msg)

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        # We spawn players at different places based on what flags are held.
        return self.spawn_player_spaz(
            player, self._get_player_spawn_position(player)
        )

    def _get_player_spawn_position(self, player: Player) -> Sequence[float]:
        # Iterate until we find a spawn owned by this team.
        spawn_count = len(self.map.spawn_by_flag_points)

        # Get all spawns owned by this team.
        spawns = [
            i for i in range(spawn_count) if self._flags[i].team is player.team
        ]

        closest_spawn = 0
        closest_distance = 9999.0

        # Now find the spawn that's closest to a spawn not owned by us;
        # we'll use that one.
        for spawn in spawns:
            spt = self.map.spawn_by_flag_points[spawn]
            our_pt = bs.Vec3(spt[0], spt[1], spt[2])
            for otherspawn in [
                i
                for i in range(spawn_count)
                if self._flags[i].team is not player.team
            ]:
                spt = self.map.spawn_by_flag_points[otherspawn]
                their_pt = bs.Vec3(spt[0], spt[1], spt[2])
                dist = (their_pt - our_pt).length()
                if dist < closest_distance:
                    closest_distance = dist
                    closest_spawn = spawn

        pos = self.map.spawn_by_flag_points[closest_spawn]
        x_range = (-0.5, 0.5) if pos[3] == 0.0 else (-pos[3], pos[3])
        z_range = (-0.5, 0.5) if pos[5] == 0.0 else (-pos[5], pos[5])
        pos = (
            pos[0] + random.uniform(*x_range),
            pos[1],
            pos[2] + random.uniform(*z_range),
        )
        return pos
