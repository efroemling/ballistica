# Released under the MIT License. See LICENSE for details.
#
"""Provides an easter egg hunt game."""

# ba_meta require api 7
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor.bomb import Bomb
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.spazbot import SpazBotSet, BouncyBot, SpazBotDiedMessage
from bastd.actor.onscreencountdown import OnScreenCountdown
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.respawnicon import RespawnIcon
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.respawn_timer: ba.Timer | None = None
        self.respawn_icon: RespawnIcon | None = None


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export game
class EasterEggHuntGame(ba.TeamGameActivity[Player, Team]):
    """A game where score is based on collecting eggs."""

    name = 'Easter Egg Hunt'
    description = 'Gather eggs!'
    available_settings = [
        ba.BoolSetting('Pro Mode', default=False),
        ba.BoolSetting('Epic Mode', default=False),
    ]
    scoreconfig = ba.ScoreConfig(label='Score', scoretype=ba.ScoreType.POINTS)

    # We're currently hard-coded for one map.
    @classmethod
    def get_supported_maps(cls, sessiontype: type[ba.Session]) -> list[str]:
        return ['Tower D']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: type[ba.Session]) -> bool:
        return (
            issubclass(sessiontype, ba.CoopSession)
            or issubclass(sessiontype, ba.DualTeamSession)
            or issubclass(sessiontype, ba.FreeForAllSession)
        )

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._last_player_death_time = None
        self._scoreboard = Scoreboard()
        self.egg_model = ba.getmodel('egg')
        self.egg_tex_1 = ba.gettexture('eggTex1')
        self.egg_tex_2 = ba.gettexture('eggTex2')
        self.egg_tex_3 = ba.gettexture('eggTex3')
        self._collect_sound = ba.getsound('powerup01')
        self._pro_mode = settings.get('Pro Mode', False)
        self._epic_mode = settings.get('Epic Mode', False)
        self._max_eggs = 1.0
        self.egg_material = ba.Material()
        self.egg_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect', self._on_egg_player_collide),),
        )
        self._eggs: list[Egg] = []
        self._update_timer: ba.Timer | None = None
        self._countdown: OnScreenCountdown | None = None
        self._bots: SpazBotSet | None = None

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (
            ba.MusicType.EPIC if self._epic_mode else ba.MusicType.FORWARD_MARCH
        )

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    # Called when our game actually starts.
    def on_begin(self) -> None:
        from bastd.maps import TowerD

        # There's a player-wall on the tower-d level to prevent
        # players from getting up on the stairs.. we wanna kill that.
        gamemap = self.map
        assert isinstance(gamemap, TowerD)
        gamemap.player_wall.delete()
        super().on_begin()
        self._update_scoreboard()
        self._update_timer = ba.Timer(0.25, self._update, repeat=True)
        self._countdown = OnScreenCountdown(60, endcall=self.end_game)
        ba.timer(4.0, self._countdown.start)
        self._bots = SpazBotSet()

        # Spawn evil bunny in co-op only.
        if isinstance(self.session, ba.CoopSession) and self._pro_mode:
            self._spawn_evil_bunny()

    # Overriding the default character spawning.
    def spawn_player(self, player: Player) -> ba.Actor:
        spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player()
        return spaz

    def _spawn_evil_bunny(self) -> None:
        assert self._bots is not None
        self._bots.spawn_bot(BouncyBot, pos=(6, 4, -7.8), spawn_time=10.0)

    def _on_egg_player_collide(self) -> None:
        if self.has_ended():
            return
        collision = ba.getcollision()

        # Be defensive here; we could be hitting the corpse of a player
        # who just left/etc.
        try:
            egg = collision.sourcenode.getdelegate(Egg, True)
            player = collision.opposingnode.getdelegate(
                PlayerSpaz, True
            ).getplayer(Player, True)
        except ba.NotFoundError:
            return

        player.team.score += 1

        # Displays a +1 (and adds to individual player score in
        # teams mode).
        self.stats.player_scored(player, 1, screenmessage=False)
        if self._max_eggs < 5:
            self._max_eggs += 1.0
        elif self._max_eggs < 10:
            self._max_eggs += 0.5
        elif self._max_eggs < 30:
            self._max_eggs += 0.3
        self._update_scoreboard()
        ba.playsound(self._collect_sound, 0.5, position=egg.node.position)

        # Create a flash.
        light = ba.newnode(
            'light',
            attrs={
                'position': egg.node.position,
                'height_attenuated': False,
                'radius': 0.1,
                'color': (1, 1, 0),
            },
        )
        ba.animate(light, 'intensity', {0: 0, 0.1: 1.0, 0.2: 0}, loop=False)
        ba.timer(0.200, light.delete)
        egg.handlemessage(ba.DieMessage())

    def _update(self) -> None:
        # Misc. periodic updating.
        xpos = random.uniform(-7.1, 6.0)
        ypos = random.uniform(3.5, 3.5)
        zpos = random.uniform(-8.2, 3.7)

        # Prune dead eggs from our list.
        self._eggs = [e for e in self._eggs if e]

        # Spawn more eggs if we've got space.
        if len(self._eggs) < int(self._max_eggs):

            # Occasionally spawn a land-mine in addition.
            if self._pro_mode and random.random() < 0.25:
                mine = Bomb(
                    position=(xpos, ypos, zpos), bomb_type='land_mine'
                ).autoretain()
                mine.arm()
            else:
                self._eggs.append(Egg(position=(xpos, ypos, zpos)))

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:

        # Respawn dead players.
        if isinstance(msg, ba.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            # Respawn them shortly.
            player = msg.getplayer(Player)
            assert self.initialplayerinfos is not None
            respawn_time = 2.0 + len(self.initialplayerinfos) * 1.0
            player.respawn_timer = ba.Timer(
                respawn_time, ba.Call(self.spawn_player_if_exists, player)
            )
            player.respawn_icon = RespawnIcon(player, respawn_time)

        # Whenever our evil bunny dies, respawn him and spew some eggs.
        elif isinstance(msg, SpazBotDiedMessage):
            self._spawn_evil_bunny()
            assert msg.spazbot.node
            pos = msg.spazbot.node.position
            for _i in range(6):
                spread = 0.4
                self._eggs.append(
                    Egg(
                        position=(
                            pos[0] + random.uniform(-spread, spread),
                            pos[1] + random.uniform(-spread, spread),
                            pos[2] + random.uniform(-spread, spread),
                        )
                    )
                )
        else:
            # Default handler.
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score)

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results)


class Egg(ba.Actor):
    """A lovely egg that can be picked up for points."""

    def __init__(self, position: tuple[float, float, float] = (0.0, 1.0, 0.0)):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, EasterEggHuntGame)
        shared = SharedObjects.get()

        # Spawn just above the provided point.
        self._spawn_pos = (position[0], position[1] + 1.0, position[2])
        ctex = (activity.egg_tex_1, activity.egg_tex_2, activity.egg_tex_3)[
            random.randrange(3)
        ]
        mats = [shared.object_material, activity.egg_material]
        self.node = ba.newnode(
            'prop',
            delegate=self,
            attrs={
                'model': activity.egg_model,
                'color_texture': ctex,
                'body': 'capsule',
                'reflection': 'soft',
                'model_scale': 0.5,
                'body_scale': 0.6,
                'density': 4.0,
                'reflection_scale': [0.15],
                'shadow_size': 0.6,
                'position': self._spawn_pos,
                'materials': mats,
            },
        )

    def exists(self) -> bool:
        return bool(self.node)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, ba.HitMessage):
            if self.node:
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
        else:
            super().handlemessage(msg)
