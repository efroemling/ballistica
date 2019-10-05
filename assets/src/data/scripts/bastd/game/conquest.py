"""Provides the Conquest game."""

# bs_meta require api 6
# (see bombsquadgame.com/apichanges)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor.flag import Flag
from bastd.actor.playerspaz import PlayerSpazDeathMessage

if TYPE_CHECKING:
    from typing import (Any, Optional, Type, List, Tuple, Dict, Sequence,
                        Union)


class ConquestFlag(Flag):
    """A custom flag for use with Conquest games."""

    def __init__(self, *args: Any, **keywds: Any):
        super().__init__(*args, **keywds)
        self._team: Optional[ba.Team] = None
        self.light: Optional[ba.Node] = None

    def set_team(self, team: ba.Team) -> None:
        """Set the team that owns this flag."""
        self._team = None if team is None else team

    @property
    def team(self) -> ba.Team:
        """The team that owns this flag."""
        assert self._team is not None
        return self._team


# bs_meta export game
class ConquestGame(ba.TeamGameActivity):
    """A game where teams try to claim all flags on the map."""

    @classmethod
    def get_name(cls) -> str:
        return 'Conquest'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Secure all flags on the map to win.'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.TeamsSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps("conquest")

    @classmethod
    def get_settings(cls, sessiontype: Type[ba.Session]
                     ) -> List[Tuple[str, Dict[str, Any]]]:
        return [
            ("Time Limit", {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120),
                            ('5 Minutes', 300),
                            ('10 Minutes', 600),
                            ('20 Minutes', 1200)],
                'default': 0
            }),
            ('Respawn Times', {
                'choices': [('Shorter', 0.25),
                            ('Short', 0.5),
                            ('Normal', 1.0),
                            ('Long', 2.0),
                            ('Longer', 4.0)],
                'default': 1.0
            }),
            ('Epic Mode', {'default': False})]  # yapf: disable

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        if self.settings['Epic Mode']:
            self.slow_motion = True
        self._scoreboard = Scoreboard()
        self._score_sound = ba.getsound('score')
        self._swipsound = ba.getsound('swip')
        self._extraflagmat = ba.Material()
        self._flags: List[ConquestFlag] = []

        # We want flags to tell us they've been hit but not react physically.
        self._extraflagmat.add_actions(
            conditions=('they_have_material', ba.sharedobj('player_material')),
            actions=(('modify_part_collision', 'collide', True),
                     ('call', 'at_connect', self._handle_flag_player_collide)))

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Secure all ${ARG1} flags.', len(self.map.flag_points)

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        return 'secure all ${ARG1} flags', len(self.map.flag_points)

    # noinspection PyMethodOverriding
    def on_transition_in(self) -> None:  # type: ignore
        # FIXME unify these args
        # pylint: disable=arguments-differ
        ba.TeamGameActivity.on_transition_in(
            self, music='Epic' if self.settings['Epic Mode'] else 'GrandRomp')

    def on_team_join(self, team: ba.Team) -> None:
        if self.has_begun():
            self._update_scores()
        team.gamedata['flags_held'] = 0

    def on_player_join(self, player: ba.Player) -> None:
        player.gamedata['respawn_timer'] = None

        # Only spawn if this player's team has a flag currently.
        if player.team.gamedata['flags_held'] > 0:
            self.spawn_player(player)

    def on_begin(self) -> None:
        ba.TeamGameActivity.on_begin(self)
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()

        # Set up flags with marker lights.
        for i in range(len(self.map.flag_points)):
            point = self.map.flag_points[i]
            flag = ConquestFlag(position=point,
                                touchable=False,
                                materials=[self._extraflagmat])
            self._flags.append(flag)
            # FIXME: Move next few lines to the flag class.
            self.project_flag_stand(point)
            flag.light = ba.newnode('light',
                                    owner=flag.node,
                                    attrs={
                                        'position': point,
                                        'intensity': 0.25,
                                        'height_attenuated': False,
                                        'radius': 0.3,
                                        'color': (1, 1, 1)
                                    })

        # Give teams a flag to start with.
        for i in range(len(self.teams)):
            self._flags[i].set_team(self.teams[i])
            light = self._flags[i].light
            assert light
            node = self._flags[i].node
            assert node
            light.color = self.teams[i].color
            node.color = self.teams[i].color

        self._update_scores()

        # Initial joiners didn't spawn due to no flags being owned yet;
        # spawn them now.
        for player in self.players:
            self.spawn_player(player)

    def _update_scores(self) -> None:
        for team in self.teams:
            team.gamedata['flags_held'] = 0
        for flag in self._flags:
            try:
                flag.team.gamedata['flags_held'] += 1
            except Exception:
                pass
        for team in self.teams:

            # If a team finds themselves with no flags, cancel all
            # outstanding spawn-timers.
            if team.gamedata['flags_held'] == 0:
                for player in team.players:
                    player.gamedata['respawn_timer'] = None
                    player.gamedata['respawn_icon'] = None
            if team.gamedata['flags_held'] == len(self._flags):
                self.end_game()
            self._scoreboard.set_team_value(team, team.gamedata['flags_held'],
                                            len(self._flags))

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(team, team.gamedata['flags_held'])
        self.end(results=results)

    def _flash_flag(self, flag: ConquestFlag, length: float = 1.0) -> None:
        assert flag.node
        assert flag.light
        light = ba.newnode('light',
                           attrs={
                               'position': flag.node.position,
                               'height_attenuated': False,
                               'color': flag.light.color
                           })
        ba.animate(light, "intensity", {0: 0, 0.25: 1, 0.5: 0}, loop=True)
        ba.timer(length, light.delete)

    def _handle_flag_player_collide(self) -> None:
        flagnode, playernode = ba.get_collision_info("source_node",
                                                     "opposing_node")
        try:
            player = playernode.getdelegate().getplayer()
            flag = flagnode.getdelegate()
        except Exception:
            return  # Player may have left and his body hit the flag.

        if flag.get_team() is not player.get_team():
            flag.set_team(player.get_team())
            flag.light.color = player.get_team().color
            flag.node.color = player.get_team().color
            self.stats.player_scored(player, 10, screenmessage=False)
            ba.playsound(self._swipsound)
            self._flash_flag(flag)
            self._update_scores()

            # Respawn any players on this team that were in limbo due to the
            # lack of a flag for their team.
            for otherplayer in self.players:
                if (otherplayer.team is flag.team
                        and otherplayer.actor is not None
                        and not otherplayer.is_alive()
                        and otherplayer.gamedata['respawn_timer'] is None):
                    self.spawn_player(otherplayer)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, PlayerSpazDeathMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            # Respawn only if this team has a flag.
            player = msg.spaz.player
            if player.team.gamedata['flags_held'] > 0:
                self.respawn_player(player)
            else:
                player.gamedata['respawn_timer'] = None

        else:
            super().handlemessage(msg)

    def spawn_player(self, player: ba.Player) -> ba.Actor:
        # We spawn players at different places based on what flags are held.
        return self.spawn_player_spaz(player,
                                      self._get_player_spawn_position(player))

    def _get_player_spawn_position(self, player: ba.Player) -> Sequence[float]:

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
            our_pt = ba.Vec3(spt[0], spt[1], spt[2])
            for otherspawn in [
                    i for i in range(spawn_count)
                    if self._flags[i].team is not player.team
            ]:
                spt = self.map.spawn_by_flag_points[otherspawn]
                their_pt = ba.Vec3(spt[0], spt[1], spt[2])
                dist = (their_pt - our_pt).length()
                if dist < closest_distance:
                    closest_distance = dist
                    closest_spawn = spawn

        pos = self.map.spawn_by_flag_points[closest_spawn]
        x_range = (-0.5, 0.5) if pos[3] == 0.0 else (-pos[3], pos[3])
        z_range = (-0.5, 0.5) if pos[5] == 0.0 else (-pos[5], pos[5])
        pos = (pos[0] + random.uniform(*x_range), pos[1],
               pos[2] + random.uniform(*z_range))
        return pos
