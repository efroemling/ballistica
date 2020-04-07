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
"""Provides an easter egg hunt game."""

# ba_meta require api 6
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor import bomb
from bastd.actor import playerspaz
from bastd.actor import spazbot
from bastd.actor.onscreencountdown import OnScreenCountdown

if TYPE_CHECKING:
    from typing import Any, Type, Dict, List, Tuple, Optional


# ba_meta export game
class EasterEggHuntGame(ba.TeamGameActivity):
    """A game where score is based on collecting eggs."""

    @classmethod
    def get_name(cls) -> str:
        return 'Easter Egg Hunt'

    @classmethod
    def get_score_info(cls) -> Dict[str, Any]:
        return {'score_name': 'Score', 'score_type': 'points'}

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Gather eggs!'

    # We're currently hard-coded for one map.
    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Tower D']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.CoopSession)
                or issubclass(sessiontype, ba.TeamsSession)
                or issubclass(sessiontype, ba.FreeForAllSession))

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        return [("Pro Mode", {'default': False})]

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        self._last_player_death_time = None
        self._scoreboard = Scoreboard()
        self.egg_model = ba.getmodel('egg')
        self.egg_tex_1 = ba.gettexture('eggTex1')
        self.egg_tex_2 = ba.gettexture('eggTex2')
        self.egg_tex_3 = ba.gettexture('eggTex3')
        self._collect_sound = ba.getsound('powerup01')
        self._pro_mode = settings.get('Pro Mode', False)
        self._max_eggs = 1.0
        self.egg_material = ba.Material()
        self.egg_material.add_actions(
            conditions=("they_have_material", ba.sharedobj('player_material')),
            actions=(("call", "at_connect", self._on_egg_player_collide), ))
        self._eggs: List[Egg] = []
        self._update_timer: Optional[ba.Timer] = None
        self._countdown: Optional[OnScreenCountdown] = None
        self._bots: Optional[spazbot.BotSet] = None

    # Called when our game is transitioning in but not ready to start.
    # ..we can go ahead and set our music and whatnot.

    def on_transition_in(self) -> None:
        self.default_music = ba.MusicType.FORWARD_MARCH
        super().on_transition_in()

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['score'] = 0
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
        self._bots = spazbot.BotSet()

        # Spawn evil bunny in co-op only.
        if isinstance(self.session, ba.CoopSession) and self._pro_mode:
            self._spawn_evil_bunny()

    # Overriding the default character spawning.
    def spawn_player(self, player: ba.Player) -> ba.Actor:
        spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player()
        return spaz

    def _spawn_evil_bunny(self) -> None:
        assert self._bots is not None
        self._bots.spawn_bot(spazbot.BouncyBot,
                             pos=(6, 4, -7.8),
                             spawn_time=10.0)

    def _on_egg_player_collide(self) -> None:
        if not self.has_ended():
            egg_node, playernode = ba.get_collision_info(
                'source_node', 'opposing_node')
            if egg_node is not None and playernode is not None:
                egg = egg_node.getdelegate()
                spaz = playernode.getdelegate()
                player = (spaz.getplayer()
                          if hasattr(spaz, 'getplayer') else None)
                if player and egg:
                    player.team.gamedata['score'] += 1

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
                    ba.playsound(self._collect_sound,
                                 0.5,
                                 position=egg.node.position)

                    # Create a flash.
                    light = ba.newnode('light',
                                       attrs={
                                           'position': egg_node.position,
                                           'height_attenuated': False,
                                           'radius': 0.1,
                                           'color': (1, 1, 0)
                                       })
                    ba.animate(light,
                               'intensity', {
                                   0: 0,
                                   0.1: 1.0,
                                   0.2: 0
                               },
                               loop=False)
                    ba.timer(0.200, light.delete)
                    egg.handlemessage(ba.DieMessage())

    def _update(self) -> None:
        # Misc. periodic updating.
        xpos = random.uniform(-7.1, 6.0)
        ypos = random.uniform(3.5, 3.5)
        zpos = random.uniform(-8.2, 3.7)
        def _is_exists(egg):
            if egg.node is None: 
                return False
            return egg.node.exists()

        # Prune dead eggs from our list.
        self._eggs = [e for e in self._eggs if _is_exists(e)]

        # Spawn more eggs if we've got space.
        if len(self._eggs) < int(self._max_eggs):

            # Occasionally spawn a land-mine in addition.
            if self._pro_mode and random.random() < 0.25:
                mine = bomb.Bomb(position=(xpos, ypos, zpos),
                                 bomb_type='land_mine').autoretain()
                mine.arm()
            else:
                self._eggs.append(Egg(position=(xpos, ypos, zpos)))

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:

        # Respawn dead players.
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            from bastd.actor import respawnicon

            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.spaz.getplayer()
            if not player:
                return
            self.stats.player_was_killed(player)

            # Respawn them shortly.
            assert self.initial_player_info is not None
            respawn_time = 2.0 + len(self.initial_player_info) * 1.0
            player.gamedata['respawn_timer'] = ba.Timer(
                respawn_time, ba.Call(self.spawn_player_if_exists, player))
            player.gamedata['respawn_icon'] = respawnicon.RespawnIcon(
                player, respawn_time)

        # Whenever our evil bunny dies, respawn him and spew some eggs.
        elif isinstance(msg, spazbot.SpazBotDeathMessage):
            self._spawn_evil_bunny()
            assert msg.badguy.node
            pos = msg.badguy.node.position
            for _i in range(6):
                spread = 0.4
                self._eggs.append(
                    Egg(position=(pos[0] + random.uniform(-spread, spread),
                                  pos[1] + random.uniform(-spread, spread),
                                  pos[2] + random.uniform(-spread, spread))))
        else:
            # Default handler.
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.gamedata['score'])

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(team, team.gamedata['score'])
        self.end(results)


class Egg(ba.Actor):
    """A lovely egg that can be picked up for points."""

    def __init__(self, position: Tuple[float, float, float] = (0.0, 1.0, 0.0)):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, EasterEggHuntGame)

        # Spawn just above the provided point.
        self._spawn_pos = (position[0], position[1] + 1.0, position[2])
        ctex = (activity.egg_tex_1, activity.egg_tex_2,
                activity.egg_tex_3)[random.randrange(3)]
        mats = [ba.sharedobj('object_material'), activity.egg_material]
        self.node = ba.newnode("prop",
                               delegate=self,
                               attrs={
                                   'model': activity.egg_model,
                                   'color_texture': ctex,
                                   'body': 'capsule',
                                   'reflection': 'soft',
                                   'model_scale': 0.5,
                                   'bodyScale': 0.6,
                                   'density': 4.0,
                                   'reflection_scale': [0.15],
                                   'shadow_size': 0.6,
                                   'position': self._spawn_pos,
                                   'materials': mats
                               })

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, ba.OutOfBoundsMessage):
            self.handlemessage(ba.DieMessage())
        elif isinstance(msg, ba.HitMessage):
            if self.node:
                assert msg.force_direction is not None
                self.node.handlemessage(
                    "impulse", msg.pos[0], msg.pos[1], msg.pos[2],
                    msg.velocity[0], msg.velocity[1], msg.velocity[2],
                    1.0 * msg.magnitude, 1.0 * msg.velocity_magnitude,
                    msg.radius, 0, msg.force_direction[0],
                    msg.force_direction[1], msg.force_direction[2])
        else:
            super().handlemessage(msg)
