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
"""Defines the runaround co-op game."""

# We wear the cone of shame.
# pylint: disable=too-many-lines

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import ba
from bastd.actor.popuptext import PopupText
from bastd.actor.bomb import TNTSpawner
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.respawnicon import RespawnIcon
from bastd.actor.powerupbox import PowerupBox, PowerupBoxFactory
from bastd.gameutils import SharedObjects
from bastd.actor.spazbot import (
    SpazBotSet, SpazBot, SpazBotDiedMessage, BomberBot, BrawlerBot, TriggerBot,
    TriggerBotPro, BomberBotProShielded, TriggerBotProShielded, ChargerBot,
    ChargerBotProShielded, StickyBot, ExplodeyBot, BrawlerBotProShielded,
    BomberBotPro, BrawlerBotPro)

if TYPE_CHECKING:
    from typing import Type, Any, List, Dict, Tuple, Sequence, Optional, Union


class Preset(Enum):
    """Play presets."""
    ENDLESS = 'endless'
    ENDLESS_TOURNAMENT = 'endless_tournament'
    PRO = 'pro'
    PRO_EASY = 'pro_easy'
    UBER = 'uber'
    UBER_EASY = 'uber_easy'
    TOURNAMENT = 'tournament'
    TOURNAMENT_UBER = 'tournament_uber'


class Point(Enum):
    """Where we can spawn stuff and the corresponding map attr name."""
    BOTTOM_LEFT = 'bot_spawn_bottom_left'
    BOTTOM_RIGHT = 'bot_spawn_bottom_right'
    START = 'bot_spawn_start'


@dataclass
class Spawn:
    """Defines a bot spawn event."""
    type: Type[SpazBot]
    path: int = 0
    point: Optional[Point] = None


@dataclass
class Spacing:
    """Defines spacing between spawns."""
    duration: float


@dataclass
class Wave:
    """Defines a wave of enemies."""
    entries: List[Union[Spawn, Spacing, None]]


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.respawn_timer: Optional[ba.Timer] = None
        self.respawn_icon: Optional[RespawnIcon] = None


class Team(ba.Team[Player]):
    """Our team type for this game."""


class RunaroundGame(ba.CoopGameActivity[Player, Team]):
    """Game involving trying to bomb bots as they walk through the map."""

    name = 'Runaround'
    description = 'Prevent enemies from reaching the exit.'
    tips = [
        'Jump just as you\'re throwing to get bombs up to the highest levels.',
        'No, you can\'t get up on the ledge. You have to throw bombs.',
        'Whip back and forth to get more distance on your throws..'
    ]
    default_music = ba.MusicType.MARCHING

    # How fast our various bot types walk.
    _bot_speed_map: Dict[Type[SpazBot], float] = {
        BomberBot: 0.48,
        BomberBotPro: 0.48,
        BomberBotProShielded: 0.48,
        BrawlerBot: 0.57,
        BrawlerBotPro: 0.57,
        BrawlerBotProShielded: 0.57,
        TriggerBot: 0.73,
        TriggerBotPro: 0.78,
        TriggerBotProShielded: 0.78,
        ChargerBot: 1.0,
        ChargerBotProShielded: 1.0,
        ExplodeyBot: 1.0,
        StickyBot: 0.5
    }

    def __init__(self, settings: dict):
        settings['map'] = 'Tower D'
        super().__init__(settings)
        shared = SharedObjects.get()
        self._preset = Preset(settings.get('preset', 'pro'))

        self._player_death_sound = ba.getsound('playerDeath')
        self._new_wave_sound = ba.getsound('scoreHit01')
        self._winsound = ba.getsound('score')
        self._cashregistersound = ba.getsound('cashRegister')
        self._bad_guy_score_sound = ba.getsound('shieldDown')
        self._heart_tex = ba.gettexture('heart')
        self._heart_model_opaque = ba.getmodel('heartOpaque')
        self._heart_model_transparent = ba.getmodel('heartTransparent')

        self._a_player_has_been_killed = False
        self._spawn_center = self._map_type.defs.points['spawn1'][0:3]
        self._tntspawnpos = self._map_type.defs.points['tnt_loc'][0:3]
        self._powerup_center = self._map_type.defs.boxes['powerup_region'][0:3]
        self._powerup_spread = (
            self._map_type.defs.boxes['powerup_region'][6] * 0.5,
            self._map_type.defs.boxes['powerup_region'][8] * 0.5)

        self._score_region_material = ba.Material()
        self._score_region_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._handle_reached_end),
            ))

        self._last_wave_end_time = ba.time()
        self._player_has_picked_up_powerup = False
        self._scoreboard: Optional[Scoreboard] = None
        self._game_over = False
        self._wavenum = 0
        self._can_end_wave = True
        self._score = 0
        self._time_bonus = 0
        self._score_region: Optional[ba.Actor] = None
        self._dingsound = ba.getsound('dingSmall')
        self._dingsoundhigh = ba.getsound('dingSmallHigh')
        self._exclude_powerups: Optional[List[str]] = None
        self._have_tnt: Optional[bool] = None
        self._waves: Optional[List[Wave]] = None
        self._bots = SpazBotSet()
        self._tntspawner: Optional[TNTSpawner] = None
        self._lives_bg: Optional[ba.NodeActor] = None
        self._start_lives = 10
        self._lives = self._start_lives
        self._lives_text: Optional[ba.NodeActor] = None
        self._flawless = True
        self._time_bonus_timer: Optional[ba.Timer] = None
        self._time_bonus_text: Optional[ba.NodeActor] = None
        self._time_bonus_mult: Optional[float] = None
        self._wave_text: Optional[ba.NodeActor] = None
        self._flawless_bonus: Optional[int] = None
        self._wave_update_timer: Optional[ba.Timer] = None

    def on_transition_in(self) -> None:
        super().on_transition_in()
        self._scoreboard = Scoreboard(label=ba.Lstr(resource='scoreText'),
                                      score_split=0.5)
        self._score_region = ba.NodeActor(
            ba.newnode(
                'region',
                attrs={
                    'position': self.map.defs.boxes['score_region'][0:3],
                    'scale': self.map.defs.boxes['score_region'][6:9],
                    'type': 'box',
                    'materials': [self._score_region_material]
                }))

    def on_begin(self) -> None:
        super().on_begin()
        player_count = len(self.players)
        hard = self._preset not in {Preset.PRO_EASY, Preset.UBER_EASY}

        if self._preset in {Preset.PRO, Preset.PRO_EASY, Preset.TOURNAMENT}:
            self._exclude_powerups = ['curse']
            self._have_tnt = True
            self._waves = [
                Wave(entries=[
                    Spawn(BomberBot, path=3 if hard else 2),
                    Spawn(BomberBot, path=2),
                    Spawn(BomberBot, path=2) if hard else None,
                    Spawn(BomberBot, path=2) if player_count > 1 else None,
                    Spawn(BomberBot, path=1) if hard else None,
                    Spawn(BomberBot, path=1) if player_count > 2 else None,
                    Spawn(BomberBot, path=1) if player_count > 3 else None,
                ]),
                Wave(entries=[
                    Spawn(BomberBot, path=1) if hard else None,
                    Spawn(BomberBot, path=2) if hard else None,
                    Spawn(BomberBot, path=2),
                    Spawn(BomberBot, path=2),
                    Spawn(BomberBot, path=2) if player_count > 3 else None,
                    Spawn(BrawlerBot, path=3),
                    Spawn(BrawlerBot, path=3),
                    Spawn(BrawlerBot, path=3) if hard else None,
                    Spawn(BrawlerBot, path=3) if player_count > 1 else None,
                    Spawn(BrawlerBot, path=3) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(ChargerBot, path=2) if hard else None,
                    Spawn(ChargerBot, path=2) if player_count > 2 else None,
                    Spawn(TriggerBot, path=2),
                    Spawn(TriggerBot, path=2) if player_count > 1 else None,
                    Spacing(duration=3.0),
                    Spawn(BomberBot, path=2) if hard else None,
                    Spawn(BomberBot, path=2) if hard else None,
                    Spawn(BomberBot, path=2),
                    Spawn(BomberBot, path=3) if hard else None,
                    Spawn(BomberBot, path=3),
                    Spawn(BomberBot, path=3),
                    Spawn(BomberBot, path=3) if player_count > 3 else None,
                ]),
                Wave(entries=[
                    Spawn(TriggerBot, path=1) if hard else None,
                    Spacing(duration=1.0) if hard else None,
                    Spawn(TriggerBot, path=2),
                    Spacing(duration=1.0),
                    Spawn(TriggerBot, path=3),
                    Spacing(duration=1.0),
                    Spawn(TriggerBot, path=1) if hard else None,
                    Spacing(duration=1.0) if hard else None,
                    Spawn(TriggerBot, path=2),
                    Spacing(duration=1.0),
                    Spawn(TriggerBot, path=3),
                    Spacing(duration=1.0),
                    Spawn(TriggerBot, path=1) if (
                        player_count > 1 and hard) else None,
                    Spacing(duration=1.0),
                    Spawn(TriggerBot, path=2) if player_count > 2 else None,
                    Spacing(duration=1.0),
                    Spawn(TriggerBot, path=3) if player_count > 3 else None,
                    Spacing(duration=1.0),
                ]),
                Wave(entries=[
                    Spawn(ChargerBotProShielded if hard else ChargerBot,
                          path=1),
                    Spawn(BrawlerBot, path=2) if hard else None,
                    Spawn(BrawlerBot, path=2),
                    Spawn(BrawlerBot, path=2),
                    Spawn(BrawlerBot, path=3) if hard else None,
                    Spawn(BrawlerBot, path=3),
                    Spawn(BrawlerBot, path=3),
                    Spawn(BrawlerBot, path=3) if player_count > 1 else None,
                    Spawn(BrawlerBot, path=3) if player_count > 2 else None,
                    Spawn(BrawlerBot, path=3) if player_count > 3 else None,
                ]),
                Wave(entries=[
                    Spawn(BomberBotProShielded, path=3),
                    Spacing(duration=1.5),
                    Spawn(BomberBotProShielded, path=2),
                    Spacing(duration=1.5),
                    Spawn(BomberBotProShielded, path=1) if hard else None,
                    Spacing(duration=1.0) if hard else None,
                    Spawn(BomberBotProShielded, path=3),
                    Spacing(duration=1.5),
                    Spawn(BomberBotProShielded, path=2),
                    Spacing(duration=1.5),
                    Spawn(BomberBotProShielded, path=1) if hard else None,
                    Spacing(duration=1.5) if hard else None,
                    Spawn(BomberBotProShielded, path=3
                          ) if player_count > 1 else None,
                    Spacing(duration=1.5),
                    Spawn(BomberBotProShielded, path=2
                          ) if player_count > 2 else None,
                    Spacing(duration=1.5),
                    Spawn(BomberBotProShielded, path=1
                          ) if player_count > 3 else None,
                ]),
            ]
        elif self._preset in {
                Preset.UBER_EASY, Preset.UBER, Preset.TOURNAMENT_UBER
        }:
            self._exclude_powerups = []
            self._have_tnt = True
            self._waves = [
                Wave(entries=[
                    Spawn(TriggerBot, path=1) if hard else None,
                    Spawn(TriggerBot, path=2),
                    Spawn(TriggerBot, path=2),
                    Spawn(TriggerBot, path=3),
                    Spawn(BrawlerBotPro if hard else BrawlerBot,
                          point=Point.BOTTOM_LEFT),
                    Spawn(BrawlerBotPro, point=Point.BOTTOM_RIGHT
                          ) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(ChargerBot, path=2),
                    Spawn(ChargerBot, path=3),
                    Spawn(ChargerBot, path=1) if hard else None,
                    Spawn(ChargerBot, path=2),
                    Spawn(ChargerBot, path=3),
                    Spawn(ChargerBot, path=1) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(BomberBotProShielded, path=1) if hard else None,
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(BomberBotProShielded, path=3),
                    Spawn(BomberBotProShielded, path=3),
                    Spawn(ChargerBot, point=Point.BOTTOM_RIGHT),
                    Spawn(ChargerBot, point=Point.BOTTOM_LEFT
                          ) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(TriggerBotPro, path=1) if hard else None,
                    Spawn(TriggerBotPro, path=1 if hard else 2),
                    Spawn(TriggerBotPro, path=1 if hard else 2),
                    Spawn(TriggerBotPro, path=1 if hard else 2),
                    Spawn(TriggerBotPro, path=1 if hard else 2),
                    Spawn(TriggerBotPro, path=1 if hard else 2),
                    Spawn(TriggerBotPro, path=1 if hard else 2
                          ) if player_count > 1 else None,
                    Spawn(TriggerBotPro, path=1 if hard else 2
                          ) if player_count > 3 else None,
                ]),
                Wave(entries=[
                    Spawn(TriggerBotProShielded if hard else TriggerBotPro,
                          point=Point.BOTTOM_LEFT),
                    Spawn(TriggerBotProShielded, point=Point.BOTTOM_RIGHT
                          ) if hard else None,
                    Spawn(TriggerBotProShielded, point=Point.BOTTOM_RIGHT
                          ) if player_count > 2 else None,
                    Spawn(BomberBot, path=3),
                    Spawn(BomberBot, path=3),
                    Spacing(duration=5.0),
                    Spawn(BrawlerBot, path=2),
                    Spawn(BrawlerBot, path=2),
                    Spacing(duration=5.0),
                    Spawn(TriggerBot, path=1) if hard else None,
                    Spawn(TriggerBot, path=1) if hard else None,
                ]),
                Wave(entries=[
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(BomberBotProShielded, path=2) if hard else None,
                    Spawn(StickyBot, point=Point.BOTTOM_RIGHT),
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(StickyBot, point=Point.BOTTOM_RIGHT
                          ) if player_count > 2 else None,
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(ExplodeyBot, point=Point.BOTTOM_LEFT),
                    Spawn(BomberBotProShielded, path=2),
                    Spawn(BomberBotProShielded, path=2
                          ) if player_count > 1 else None,
                    Spacing(duration=5.0),
                    Spawn(StickyBot, point=Point.BOTTOM_LEFT),
                    Spacing(duration=2.0),
                    Spawn(ExplodeyBot, point=Point.BOTTOM_RIGHT),
                ]),
            ]
        elif self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            self._exclude_powerups = []
            self._have_tnt = True

        # Spit out a few powerups and start dropping more shortly.
        self._drop_powerups(standard_points=True)
        ba.timer(4.0, self._start_powerup_drops)
        self.setup_low_life_warning_sound()
        self._update_scores()

        # Our TNT spawner (if applicable).
        if self._have_tnt:
            self._tntspawner = TNTSpawner(position=self._tntspawnpos)

        # Make sure to stay out of the way of menu/party buttons in the corner.
        uiscale = ba.app.ui.uiscale
        l_offs = (-80 if uiscale is ba.UIScale.SMALL else
                  -40 if uiscale is ba.UIScale.MEDIUM else 0)

        self._lives_bg = ba.NodeActor(
            ba.newnode('image',
                       attrs={
                           'texture': self._heart_tex,
                           'model_opaque': self._heart_model_opaque,
                           'model_transparent': self._heart_model_transparent,
                           'attach': 'topRight',
                           'scale': (90, 90),
                           'position': (-110 + l_offs, -50),
                           'color': (1, 0.2, 0.2)
                       }))
        # FIXME; should not set things based on vr mode.
        #  (won't look right to non-vr connected clients, etc)
        vrmode = ba.app.vr_mode
        self._lives_text = ba.NodeActor(
            ba.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'right',
                    'h_align': 'center',
                    'color': (1, 1, 1, 1) if vrmode else (0.8, 0.8, 0.8, 1.0),
                    'flatness': 1.0 if vrmode else 0.5,
                    'shadow': 1.0 if vrmode else 0.5,
                    'vr_depth': 10,
                    'position': (-113 + l_offs, -69),
                    'scale': 1.3,
                    'text': str(self._lives)
                }))

        ba.timer(2.0, self._start_updating_waves)

    def _handle_reached_end(self) -> None:
        spaz = ba.getcollision().opposingnode.getdelegate(SpazBot, True)
        if not spaz.is_alive():
            return  # Ignore bodies flying in.

        self._flawless = False
        pos = spaz.node.position
        ba.playsound(self._bad_guy_score_sound, position=pos)
        light = ba.newnode('light',
                           attrs={
                               'position': pos,
                               'radius': 0.5,
                               'color': (1, 0, 0)
                           })
        ba.animate(light, 'intensity', {0.0: 0, 0.1: 1, 0.5: 0}, loop=False)
        ba.timer(1.0, light.delete)
        spaz.handlemessage(
            ba.DieMessage(immediate=True, how=ba.DeathType.REACHED_GOAL))

        if self._lives > 0:
            self._lives -= 1
            if self._lives == 0:
                self._bots.stop_moving()
                self.continue_or_end_game()
            assert self._lives_text is not None
            assert self._lives_text.node
            self._lives_text.node.text = str(self._lives)
            delay = 0.0

            def _safesetattr(node: ba.Node, attr: str, value: Any) -> None:
                if node:
                    setattr(node, attr, value)

            for _i in range(4):
                ba.timer(
                    delay,
                    ba.Call(_safesetattr, self._lives_text.node, 'color',
                            (1, 0, 0, 1.0)))
                assert self._lives_bg is not None
                assert self._lives_bg.node
                ba.timer(
                    delay,
                    ba.Call(_safesetattr, self._lives_bg.node, 'opacity', 0.5))
                delay += 0.125
                ba.timer(
                    delay,
                    ba.Call(_safesetattr, self._lives_text.node, 'color',
                            (1.0, 1.0, 0.0, 1.0)))
                ba.timer(
                    delay,
                    ba.Call(_safesetattr, self._lives_bg.node, 'opacity', 1.0))
                delay += 0.125
            ba.timer(
                delay,
                ba.Call(_safesetattr, self._lives_text.node, 'color',
                        (0.8, 0.8, 0.8, 1.0)))

    def on_continue(self) -> None:
        self._lives = 3
        assert self._lives_text is not None
        assert self._lives_text.node
        self._lives_text.node.text = str(self._lives)
        self._bots.start_moving()

    def spawn_player(self, player: Player) -> ba.Actor:
        pos = (self._spawn_center[0] + random.uniform(-1.5, 1.5),
               self._spawn_center[1],
               self._spawn_center[2] + random.uniform(-1.5, 1.5))
        spaz = self.spawn_player_spaz(player, position=pos)
        if self._preset in {Preset.PRO_EASY, Preset.UBER_EASY}:
            spaz.impact_scale = 0.25

        # Add the material that causes us to hit the player-wall.
        spaz.pick_up_powerup_callback = self._on_player_picked_up_powerup
        return spaz

    def _on_player_picked_up_powerup(self, player: ba.Actor) -> None:
        del player  # Unused.
        self._player_has_picked_up_powerup = True

    def _drop_powerup(self, index: int, poweruptype: str = None) -> None:
        if poweruptype is None:
            poweruptype = (PowerupBoxFactory.get().get_random_powerup_type(
                excludetypes=self._exclude_powerups))
        PowerupBox(position=self.map.powerup_spawn_points[index],
                   poweruptype=poweruptype).autoretain()

    def _start_powerup_drops(self) -> None:
        ba.timer(3.0, self._drop_powerups, repeat=True)

    def _drop_powerups(self,
                       standard_points: bool = False,
                       force_first: str = None) -> None:
        """Generic powerup drop."""

        # If its been a minute since our last wave finished emerging, stop
        # giving out land-mine powerups. (prevents players from waiting
        # around for them on purpose and filling the map up)
        if ba.time() - self._last_wave_end_time > 60.0:
            extra_excludes = ['land_mines']
        else:
            extra_excludes = []

        if standard_points:
            points = self.map.powerup_spawn_points
            for i in range(len(points)):
                ba.timer(
                    1.0 + i * 0.5,
                    ba.Call(self._drop_powerup, i,
                            force_first if i == 0 else None))
        else:
            pos = (self._powerup_center[0] + random.uniform(
                -1.0 * self._powerup_spread[0], 1.0 * self._powerup_spread[0]),
                   self._powerup_center[1],
                   self._powerup_center[2] + random.uniform(
                       -self._powerup_spread[1], self._powerup_spread[1]))

            # drop one random one somewhere..
            assert self._exclude_powerups is not None
            PowerupBox(
                position=pos,
                poweruptype=PowerupBoxFactory.get().get_random_powerup_type(
                    excludetypes=self._exclude_powerups +
                    extra_excludes)).autoretain()

    def end_game(self) -> None:
        ba.pushcall(ba.Call(self.do_end, 'defeat'))
        ba.setmusic(None)
        ba.playsound(self._player_death_sound)

    def do_end(self, outcome: str) -> None:
        """End the game now with the provided outcome."""

        if outcome == 'defeat':
            delay = 2.0
            self.fade_to_red()
        else:
            delay = 0

        score: Optional[int]
        if self._wavenum >= 2:
            score = self._score
            fail_message = None
        else:
            score = None
            fail_message = 'Reach wave 2 to rank.'

        self.end(delay=delay,
                 results={
                     'outcome': outcome,
                     'score': score,
                     'fail_message': fail_message,
                     'playerinfos': self.initialplayerinfos
                 })

    def _on_got_scores_to_beat(self, scores: List[Dict[str, Any]]) -> None:
        self._show_standard_scores_to_beat_ui(scores)

    def _update_waves(self) -> None:
        # pylint: disable=too-many-branches

        # If we have no living bots, go to the next wave.
        if (self._can_end_wave and not self._bots.have_living_bots()
                and not self._game_over and self._lives > 0):

            self._can_end_wave = False
            self._time_bonus_timer = None
            self._time_bonus_text = None

            if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
                won = False
            else:
                assert self._waves is not None
                won = (self._wavenum == len(self._waves))

            # Reward time bonus.
            base_delay = 4.0 if won else 0
            if self._time_bonus > 0:
                ba.timer(0, ba.Call(ba.playsound, self._cashregistersound))
                ba.timer(base_delay,
                         ba.Call(self._award_time_bonus, self._time_bonus))
                base_delay += 1.0

            # Reward flawless bonus.
            if self._wavenum > 0 and self._flawless:
                ba.timer(base_delay, self._award_flawless_bonus)
                base_delay += 1.0

            self._flawless = True  # reset

            if won:

                # Completion achievements:
                if self._preset in {Preset.PRO, Preset.PRO_EASY}:
                    self._award_achievement('Pro Runaround Victory',
                                            sound=False)
                    if self._lives == self._start_lives:
                        self._award_achievement('The Wall', sound=False)
                    if not self._player_has_picked_up_powerup:
                        self._award_achievement('Precision Bombing',
                                                sound=False)
                elif self._preset in {Preset.UBER, Preset.UBER_EASY}:
                    self._award_achievement('Uber Runaround Victory',
                                            sound=False)
                    if self._lives == self._start_lives:
                        self._award_achievement('The Great Wall', sound=False)
                    if not self._a_player_has_been_killed:
                        self._award_achievement('Stayin\' Alive', sound=False)

                # Give remaining players some points and have them celebrate.
                self.show_zoom_message(ba.Lstr(resource='victoryText'),
                                       scale=1.0,
                                       duration=4.0)

                self.celebrate(10.0)
                ba.timer(base_delay, self._award_lives_bonus)
                base_delay += 1.0
                ba.timer(base_delay, self._award_completion_bonus)
                base_delay += 0.85
                ba.playsound(self._winsound)
                ba.cameraflash()
                ba.setmusic(ba.MusicType.VICTORY)
                self._game_over = True
                ba.timer(base_delay, ba.Call(self.do_end, 'victory'))
                return

            self._wavenum += 1

            # Short celebration after waves.
            if self._wavenum > 1:
                self.celebrate(0.5)

            ba.timer(base_delay, self._start_next_wave)

    def _award_completion_bonus(self) -> None:
        bonus = 200
        ba.playsound(self._cashregistersound)
        PopupText(ba.Lstr(value='+${A} ${B}',
                          subs=[('${A}', str(bonus)),
                                ('${B}',
                                 ba.Lstr(resource='completionBonusText'))]),
                  color=(0.7, 0.7, 1.0, 1),
                  scale=1.6,
                  position=(0, 1.5, -1)).autoretain()
        self._score += bonus
        self._update_scores()

    def _award_lives_bonus(self) -> None:
        bonus = self._lives * 30
        ba.playsound(self._cashregistersound)
        PopupText(ba.Lstr(value='+${A} ${B}',
                          subs=[('${A}', str(bonus)),
                                ('${B}', ba.Lstr(resource='livesBonusText'))]),
                  color=(0.7, 1.0, 0.3, 1),
                  scale=1.3,
                  position=(0, 1, -1)).autoretain()
        self._score += bonus
        self._update_scores()

    def _award_time_bonus(self, bonus: int) -> None:
        ba.playsound(self._cashregistersound)
        PopupText(ba.Lstr(value='+${A} ${B}',
                          subs=[('${A}', str(bonus)),
                                ('${B}', ba.Lstr(resource='timeBonusText'))]),
                  color=(1, 1, 0.5, 1),
                  scale=1.0,
                  position=(0, 3, -1)).autoretain()

        self._score += self._time_bonus
        self._update_scores()

    def _award_flawless_bonus(self) -> None:
        ba.playsound(self._cashregistersound)
        PopupText(ba.Lstr(value='+${A} ${B}',
                          subs=[('${A}', str(self._flawless_bonus)),
                                ('${B}', ba.Lstr(resource='perfectWaveText'))
                                ]),
                  color=(1, 1, 0.2, 1),
                  scale=1.2,
                  position=(0, 2, -1)).autoretain()

        assert self._flawless_bonus is not None
        self._score += self._flawless_bonus
        self._update_scores()

    def _start_time_bonus_timer(self) -> None:
        self._time_bonus_timer = ba.Timer(1.0,
                                          self._update_time_bonus,
                                          repeat=True)

    def _start_next_wave(self) -> None:
        # FIXME: Need to split this up.
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        self.show_zoom_message(ba.Lstr(value='${A} ${B}',
                                       subs=[('${A}',
                                              ba.Lstr(resource='waveText')),
                                             ('${B}', str(self._wavenum))]),
                               scale=1.0,
                               duration=1.0,
                               trail=True)
        ba.timer(0.4, ba.Call(ba.playsound, self._new_wave_sound))
        t_sec = 0.0
        base_delay = 0.5
        delay = 0.0
        bot_types: List[Union[Spawn, Spacing, None]] = []

        if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            level = self._wavenum
            target_points = (level + 1) * 8.0
            group_count = random.randint(1, 3)
            entries: List[Union[Spawn, Spacing, None]] = []
            spaz_types: List[Tuple[Type[SpazBot], float]] = []
            if level < 6:
                spaz_types += [(BomberBot, 5.0)]
            if level < 10:
                spaz_types += [(BrawlerBot, 5.0)]
            if level < 15:
                spaz_types += [(TriggerBot, 6.0)]
            if level > 5:
                spaz_types += [(TriggerBotPro, 7.5)] * (1 + (level - 5) // 7)
            if level > 2:
                spaz_types += [(BomberBotProShielded, 8.0)
                               ] * (1 + (level - 2) // 6)
            if level > 6:
                spaz_types += [(TriggerBotProShielded, 12.0)
                               ] * (1 + (level - 6) // 5)
            if level > 1:
                spaz_types += ([(ChargerBot, 10.0)] * (1 + (level - 1) // 4))
            if level > 7:
                spaz_types += [(ChargerBotProShielded, 15.0)
                               ] * (1 + (level - 7) // 3)

            # Bot type, their effect on target points.
            defender_types: List[Tuple[Type[SpazBot], float]] = [
                (BomberBot, 0.9),
                (BrawlerBot, 0.9),
                (TriggerBot, 0.85),
            ]
            if level > 2:
                defender_types += [(ChargerBot, 0.75)]
            if level > 4:
                defender_types += ([(StickyBot, 0.7)] * (1 + (level - 5) // 6))
            if level > 6:
                defender_types += ([(ExplodeyBot, 0.7)] * (1 +
                                                           (level - 5) // 5))
            if level > 8:
                defender_types += ([(BrawlerBotProShielded, 0.65)] *
                                   (1 + (level - 5) // 4))
            if level > 10:
                defender_types += ([(TriggerBotProShielded, 0.6)] *
                                   (1 + (level - 6) // 3))

            for group in range(group_count):
                this_target_point_s = target_points / group_count

                # Adding spacing makes things slightly harder.
                rval = random.random()
                if rval < 0.07:
                    spacing = 1.5
                    this_target_point_s *= 0.85
                elif rval < 0.15:
                    spacing = 1.0
                    this_target_point_s *= 0.9
                else:
                    spacing = 0.0

                path = random.randint(1, 3)

                # Don't allow hard paths on early levels.
                if level < 3:
                    if path == 1:
                        path = 3

                # Easy path.
                if path == 3:
                    pass

                # Harder path.
                elif path == 2:
                    this_target_point_s *= 0.8

                # Even harder path.
                elif path == 1:
                    this_target_point_s *= 0.7

                # Looping forward.
                elif path == 4:
                    this_target_point_s *= 0.7

                # Looping backward.
                elif path == 5:
                    this_target_point_s *= 0.7

                # Random.
                elif path == 6:
                    this_target_point_s *= 0.7

                def _add_defender(defender_type: Tuple[Type[SpazBot], float],
                                  pnt: Point) -> Tuple[float, Spawn]:
                    # This is ok because we call it immediately.
                    # pylint: disable=cell-var-from-loop
                    return this_target_point_s * defender_type[1], Spawn(
                        defender_type[0], point=pnt)

                # Add defenders.
                defender_type1 = defender_types[random.randrange(
                    len(defender_types))]
                defender_type2 = defender_types[random.randrange(
                    len(defender_types))]
                defender1 = defender2 = None
                if ((group == 0) or (group == 1 and level > 3)
                        or (group == 2 and level > 5)):
                    if random.random() < min(0.75, (level - 1) * 0.11):
                        this_target_point_s, defender1 = _add_defender(
                            defender_type1, Point.BOTTOM_LEFT)
                    if random.random() < min(0.75, (level - 1) * 0.04):
                        this_target_point_s, defender2 = _add_defender(
                            defender_type2, Point.BOTTOM_RIGHT)

                spaz_type = spaz_types[random.randrange(len(spaz_types))]
                member_count = max(
                    1, int(round(this_target_point_s / spaz_type[1])))
                for i, _member in enumerate(range(member_count)):
                    if path == 4:
                        this_path = i % 3  # Looping forward.
                    elif path == 5:
                        this_path = 3 - (i % 3)  # Looping backward.
                    elif path == 6:
                        this_path = random.randint(1, 3)  # Random.
                    else:
                        this_path = path
                    entries.append(Spawn(spaz_type[0], path=this_path))
                    if spacing != 0.0:
                        entries.append(Spacing(duration=spacing))

                if defender1 is not None:
                    entries.append(defender1)
                if defender2 is not None:
                    entries.append(defender2)

                # Some spacing between groups.
                rval = random.random()
                if rval < 0.1:
                    spacing = 5.0
                elif rval < 0.5:
                    spacing = 1.0
                else:
                    spacing = 1.0
                entries.append(Spacing(duration=spacing))

            wave = Wave(entries=entries)

        else:
            assert self._waves is not None
            wave = self._waves[self._wavenum - 1]

        bot_types += wave.entries
        self._time_bonus_mult = 1.0
        this_flawless_bonus = 0
        non_runner_spawn_time = 1.0

        for info in bot_types:
            if info is None:
                continue
            if isinstance(info, Spacing):
                t_sec += info.duration
                continue
            bot_type = info.type
            path = info.path
            self._time_bonus_mult += bot_type.points_mult * 0.02
            this_flawless_bonus += bot_type.points_mult * 5

            # If its got a position, use that.
            if info.point is not None:
                point = info.point
            else:
                point = Point.START

            # Space our our slower bots.
            delay = base_delay
            delay /= self._get_bot_speed(bot_type)
            t_sec += delay * 0.5
            tcall = ba.Call(
                self.add_bot_at_point, point, bot_type, path,
                0.1 if point is Point.START else non_runner_spawn_time)
            ba.timer(t_sec, tcall)
            t_sec += delay * 0.5

        # We can end the wave after all the spawning happens.
        ba.timer(t_sec - delay * 0.5 + non_runner_spawn_time + 0.01,
                 self._set_can_end_wave)

        # Reset our time bonus.
        # In this game we use a constant time bonus so it erodes away in
        # roughly the same time (since the time limit a wave can take is
        # relatively constant) ..we then post-multiply a modifier to adjust
        # points.
        self._time_bonus = 150
        self._flawless_bonus = this_flawless_bonus
        assert self._time_bonus_mult is not None
        txtval = ba.Lstr(
            value='${A}: ${B}',
            subs=[('${A}', ba.Lstr(resource='timeBonusText')),
                  ('${B}', str(int(self._time_bonus * self._time_bonus_mult)))
                  ])
        self._time_bonus_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'center',
                           'h_align': 'center',
                           'color': (1, 1, 0.0, 1),
                           'shadow': 1.0,
                           'vr_depth': -30,
                           'flatness': 1.0,
                           'position': (0, -60),
                           'scale': 0.8,
                           'text': txtval
                       }))

        ba.timer(t_sec, self._start_time_bonus_timer)

        # Keep track of when this wave finishes emerging. We wanna stop
        # dropping land-mines powerups at some point (otherwise a crafty
        # player could fill the whole map with them)
        self._last_wave_end_time = ba.time() + t_sec
        totalwaves = str(len(self._waves)) if self._waves is not None else '??'
        txtval = ba.Lstr(value='${A} ${B}',
                         subs=[('${A}', ba.Lstr(resource='waveText')),
                               ('${B}',
                                str(self._wavenum) + ('' if self._preset in {
                                    Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT
                                } else f'/{totalwaves}'))])
        self._wave_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'center',
                           'h_align': 'center',
                           'vr_depth': -10,
                           'color': (1, 1, 1, 1),
                           'shadow': 1.0,
                           'flatness': 1.0,
                           'position': (0, -40),
                           'scale': 1.3,
                           'text': txtval
                       }))

    def _on_bot_spawn(self, path: int, spaz: SpazBot) -> None:

        # Add our custom update callback and set some info for this bot.
        spaz_type = type(spaz)
        assert spaz is not None
        spaz.update_callback = self._update_bot

        # Tack some custom attrs onto the spaz.
        setattr(spaz, 'r_walk_row', path)
        setattr(spaz, 'r_walk_speed', self._get_bot_speed(spaz_type))

    def add_bot_at_point(self,
                         point: Point,
                         spaztype: Type[SpazBot],
                         path: int,
                         spawn_time: float = 0.1) -> None:
        """Add the given type bot with the given delay (in seconds)."""

        # Don't add if the game has ended.
        if self._game_over:
            return
        pos = self.map.defs.points[point.value][:3]
        self._bots.spawn_bot(spaztype,
                             pos=pos,
                             spawn_time=spawn_time,
                             on_spawn_call=ba.Call(self._on_bot_spawn, path))

    def _update_time_bonus(self) -> None:
        self._time_bonus = int(self._time_bonus * 0.91)
        if self._time_bonus > 0 and self._time_bonus_text is not None:
            assert self._time_bonus_text.node
            assert self._time_bonus_mult
            self._time_bonus_text.node.text = ba.Lstr(
                value='${A}: ${B}',
                subs=[('${A}', ba.Lstr(resource='timeBonusText')),
                      ('${B}',
                       str(int(self._time_bonus * self._time_bonus_mult)))])
        else:
            self._time_bonus_text = None

    def _start_updating_waves(self) -> None:
        self._wave_update_timer = ba.Timer(2.0,
                                           self._update_waves,
                                           repeat=True)

    def _update_scores(self) -> None:
        score = self._score
        if self._preset is Preset.ENDLESS:
            if score >= 500:
                self._award_achievement('Runaround Master')
            if score >= 1000:
                self._award_achievement('Runaround Wizard')
            if score >= 2000:
                self._award_achievement('Runaround God')

        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)

    def _update_bot(self, bot: SpazBot) -> bool:
        # Yup; that's a lot of return statements right there.
        # pylint: disable=too-many-return-statements

        if not bool(bot):
            return True

        assert bot.node

        # FIXME: Do this in a type safe way.
        r_walk_speed: float = getattr(bot, 'r_walk_speed')
        r_walk_row: int = getattr(bot, 'r_walk_row')

        speed = r_walk_speed
        pos = bot.node.position
        boxes = self.map.defs.boxes

        # Bots in row 1 attempt the high road..
        if r_walk_row == 1:
            if ba.is_point_in_box(pos, boxes['b4']):
                bot.node.move_up_down = speed
                bot.node.move_left_right = 0
                bot.node.run = 0.0
                return True

        # Row 1 and 2 bots attempt the middle road..
        if r_walk_row in [1, 2]:
            if ba.is_point_in_box(pos, boxes['b1']):
                bot.node.move_up_down = speed
                bot.node.move_left_right = 0
                bot.node.run = 0.0
                return True

        # All bots settle for the third row.
        if ba.is_point_in_box(pos, boxes['b7']):
            bot.node.move_up_down = speed
            bot.node.move_left_right = 0
            bot.node.run = 0.0
            return True
        if ba.is_point_in_box(pos, boxes['b2']):
            bot.node.move_up_down = -speed
            bot.node.move_left_right = 0
            bot.node.run = 0.0
            return True
        if ba.is_point_in_box(pos, boxes['b3']):
            bot.node.move_up_down = -speed
            bot.node.move_left_right = 0
            bot.node.run = 0.0
            return True
        if ba.is_point_in_box(pos, boxes['b5']):
            bot.node.move_up_down = -speed
            bot.node.move_left_right = 0
            bot.node.run = 0.0
            return True
        if ba.is_point_in_box(pos, boxes['b6']):
            bot.node.move_up_down = speed
            bot.node.move_left_right = 0
            bot.node.run = 0.0
            return True
        if ((ba.is_point_in_box(pos, boxes['b8'])
             and not ba.is_point_in_box(pos, boxes['b9']))
                or pos == (0.0, 0.0, 0.0)):

            # Default to walking right if we're still in the walking area.
            bot.node.move_left_right = speed
            bot.node.move_up_down = 0
            bot.node.run = 0.0
            return True

        # Revert to normal bot behavior otherwise..
        return False

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()

        elif isinstance(msg, ba.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            self._a_player_has_been_killed = True

            # Respawn them shortly.
            player = msg.getplayer(Player)
            assert self.initialplayerinfos is not None
            respawn_time = 2.0 + len(self.initialplayerinfos) * 1.0
            player.respawn_timer = ba.Timer(
                respawn_time, ba.Call(self.spawn_player_if_exists, player))
            player.respawn_icon = RespawnIcon(player, respawn_time)

        elif isinstance(msg, SpazBotDiedMessage):
            if msg.how is ba.DeathType.REACHED_GOAL:
                return None
            pts, importance = msg.spazbot.get_death_points(msg.how)
            if msg.killerplayer is not None:
                target: Optional[Sequence[float]]
                try:
                    assert msg.spazbot is not None
                    assert msg.spazbot.node
                    target = msg.spazbot.node.position
                except Exception:
                    ba.print_exception()
                    target = None
                try:
                    if msg.killerplayer:
                        self.stats.player_scored(msg.killerplayer,
                                                 pts,
                                                 target=target,
                                                 kill=True,
                                                 screenmessage=False,
                                                 importance=importance)
                        ba.playsound(self._dingsound if importance == 1 else
                                     self._dingsoundhigh,
                                     volume=0.6)
                except Exception:
                    ba.print_exception('Error on SpazBotDiedMessage.')

            # Normally we pull scores from the score-set, but if there's no
            # player lets be explicit.
            else:
                self._score += pts
            self._update_scores()

        else:
            return super().handlemessage(msg)
        return None

    def _get_bot_speed(self, bot_type: Type[SpazBot]) -> float:
        speed = self._bot_speed_map.get(bot_type)
        if speed is None:
            raise TypeError('Invalid bot type to _get_bot_speed(): ' +
                            str(bot_type))
        return speed

    def _set_can_end_wave(self) -> None:
        self._can_end_wave = True
