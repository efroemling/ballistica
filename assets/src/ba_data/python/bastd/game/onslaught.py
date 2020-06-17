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
"""Provides Onslaught Co-op game."""

# Yes this is a long one..
# pylint: disable=too-many-lines

from __future__ import annotations

import math
import random
from enum import Enum, unique
from dataclasses import dataclass
from typing import TYPE_CHECKING

import ba
from bastd.actor.popuptext import PopupText
from bastd.actor.bomb import TNTSpawner
from bastd.actor.playerspaz import PlayerSpazHurtMessage
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.controlsguide import ControlsGuide
from bastd.actor.powerupbox import PowerupBox, PowerupBoxFactory
from bastd.actor.spazbot import (
    SpazBotDiedMessage, SpazBotSet, ChargerBot, StickyBot, BomberBot,
    BomberBotLite, BrawlerBot, BrawlerBotLite, TriggerBot, BomberBotStaticLite,
    TriggerBotStatic, BomberBotProStatic, TriggerBotPro, ExplodeyBot,
    BrawlerBotProShielded, ChargerBotProShielded, BomberBotPro,
    TriggerBotProShielded, BrawlerBotPro, BomberBotProShielded)

if TYPE_CHECKING:
    from typing import Any, Type, Dict, Optional, List, Tuple, Union, Sequence
    from bastd.actor.spazbot import SpazBot


@dataclass
class Wave:
    """A wave of enemies."""
    entries: List[Union[Spawn, Spacing, Delay, None]]
    base_angle: float = 0.0


@dataclass
class Spawn:
    """A bot spawn event in a wave."""
    bottype: Union[Type[SpazBot], str]
    point: Optional[Point] = None
    spacing: float = 5.0


@dataclass
class Spacing:
    """Empty space in a wave."""
    spacing: float = 5.0


@dataclass
class Delay:
    """A delay between events in a wave."""
    duration: float


class Preset(Enum):
    """Game presets we support."""
    TRAINING = 'training'
    TRAINING_EASY = 'training_easy'
    ROOKIE = 'rookie'
    ROOKIE_EASY = 'rookie_easy'
    PRO = 'pro'
    PRO_EASY = 'pro_easy'
    UBER = 'uber'
    UBER_EASY = 'uber_easy'
    ENDLESS = 'endless'
    ENDLESS_TOURNAMENT = 'endless_tournament'


@unique
class Point(Enum):
    """Points on the map we can spawn at."""
    LEFT_UPPER_MORE = 'bot_spawn_left_upper_more'
    LEFT_UPPER = 'bot_spawn_left_upper'
    TURRET_TOP_RIGHT = 'bot_spawn_turret_top_right'
    RIGHT_UPPER = 'bot_spawn_right_upper'
    TURRET_TOP_MIDDLE_LEFT = 'bot_spawn_turret_top_middle_left'
    TURRET_TOP_MIDDLE_RIGHT = 'bot_spawn_turret_top_middle_right'
    TURRET_TOP_LEFT = 'bot_spawn_turret_top_left'
    TOP_RIGHT = 'bot_spawn_top_right'
    TOP_LEFT = 'bot_spawn_top_left'
    TOP = 'bot_spawn_top'
    BOTTOM = 'bot_spawn_bottom'
    LEFT = 'bot_spawn_left'
    RIGHT = 'bot_spawn_right'
    RIGHT_UPPER_MORE = 'bot_spawn_right_upper_more'
    RIGHT_LOWER = 'bot_spawn_right_lower'
    RIGHT_LOWER_MORE = 'bot_spawn_right_lower_more'
    BOTTOM_RIGHT = 'bot_spawn_bottom_right'
    BOTTOM_LEFT = 'bot_spawn_bottom_left'
    TURRET_BOTTOM_RIGHT = 'bot_spawn_turret_bottom_right'
    TURRET_BOTTOM_LEFT = 'bot_spawn_turret_bottom_left'
    LEFT_LOWER = 'bot_spawn_left_lower'
    LEFT_LOWER_MORE = 'bot_spawn_left_lower_more'
    TURRET_TOP_MIDDLE = 'bot_spawn_turret_top_middle'
    BOTTOM_HALF_RIGHT = 'bot_spawn_bottom_half_right'
    BOTTOM_HALF_LEFT = 'bot_spawn_bottom_half_left'
    TOP_HALF_RIGHT = 'bot_spawn_top_half_right'
    TOP_HALF_LEFT = 'bot_spawn_top_half_left'


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.has_been_hurt = False
        self.respawn_wave = 0


class Team(ba.Team[Player]):
    """Our team type for this game."""


class OnslaughtGame(ba.CoopGameActivity[Player, Team]):
    """Co-op game where players try to survive attacking waves of enemies."""

    name = 'Onslaught'
    description = 'Defeat all enemies.'

    tips: List[Union[str, ba.GameTip]] = [
        'Hold any button to run.'
        '  (Trigger buttons work well if you have them)',
        'Try tricking enemies into killing eachother or running off cliffs.',
        'Try \'Cooking off\' bombs for a second or two before throwing them.',
        'It\'s easier to win with a friend or two helping.',
        'If you stay in one place, you\'re toast. Run and dodge to survive..',
        'Practice using your momentum to throw bombs more accurately.',
        'Your punches do much more damage if you are running or spinning.'
    ]

    # Show messages when players die since it matters here.
    announce_player_deaths = True

    def __init__(self, settings: dict):

        self._preset = Preset(settings.get('preset', 'training'))
        if self._preset in {
                Preset.TRAINING, Preset.TRAINING_EASY, Preset.PRO,
                Preset.PRO_EASY, Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT
        }:
            settings['map'] = 'Doom Shroom'
        else:
            settings['map'] = 'Courtyard'

        super().__init__(settings)

        self._new_wave_sound = ba.getsound('scoreHit01')
        self._winsound = ba.getsound('score')
        self._cashregistersound = ba.getsound('cashRegister')
        self._a_player_has_been_hurt = False
        self._player_has_dropped_bomb = False

        # FIXME: should use standard map defs.
        if settings['map'] == 'Doom Shroom':
            self._spawn_center = (0, 3, -5)
            self._tntspawnpos = (0.0, 3.0, -5.0)
            self._powerup_center = (0, 5, -3.6)
            self._powerup_spread = (6.0, 4.0)
        elif settings['map'] == 'Courtyard':
            self._spawn_center = (0, 3, -2)
            self._tntspawnpos = (0.0, 3.0, 2.1)
            self._powerup_center = (0, 5, -1.6)
            self._powerup_spread = (4.6, 2.7)
        else:
            raise Exception('Unsupported map: ' + str(settings['map']))
        self._scoreboard: Optional[Scoreboard] = None
        self._game_over = False
        self._wavenum = 0
        self._can_end_wave = True
        self._score = 0
        self._time_bonus = 0
        self._spawn_info_text: Optional[ba.NodeActor] = None
        self._dingsound = ba.getsound('dingSmall')
        self._dingsoundhigh = ba.getsound('dingSmallHigh')
        self._have_tnt = False
        self._excluded_powerups: Optional[List[str]] = None
        self._waves: List[Wave] = []
        self._tntspawner: Optional[TNTSpawner] = None
        self._bots: Optional[SpazBotSet] = None
        self._powerup_drop_timer: Optional[ba.Timer] = None
        self._time_bonus_timer: Optional[ba.Timer] = None
        self._time_bonus_text: Optional[ba.NodeActor] = None
        self._flawless_bonus: Optional[int] = None
        self._wave_text: Optional[ba.NodeActor] = None
        self._wave_update_timer: Optional[ba.Timer] = None
        self._throw_off_kills = 0
        self._land_mine_kills = 0
        self._tnt_kills = 0

    def on_transition_in(self) -> None:
        super().on_transition_in()
        customdata = ba.getsession().customdata

        # Show special landmine tip on rookie preset.
        if self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            # Show once per session only (then we revert to regular tips).
            if not customdata.get('_showed_onslaught_landmine_tip', False):
                customdata['_showed_onslaught_landmine_tip'] = True
                self.tips = [
                    ba.GameTip(
                        'Land-mines are a good way to stop speedy enemies.',
                        icon=ba.gettexture('powerupLandMines'),
                        sound=ba.getsound('ding'))
                ]

        # Show special tnt tip on pro preset.
        if self._preset in {Preset.PRO, Preset.PRO_EASY}:
            # Show once per session only (then we revert to regular tips).
            if not customdata.get('_showed_onslaught_tnt_tip', False):
                customdata['_showed_onslaught_tnt_tip'] = True
                self.tips = [
                    ba.GameTip(
                        'Take out a group of enemies by\n'
                        'setting off a bomb near a TNT box.',
                        icon=ba.gettexture('tnt'),
                        sound=ba.getsound('ding'))
                ]

        # Show special curse tip on uber preset.
        if self._preset in {Preset.UBER, Preset.UBER_EASY}:
            # Show once per session only (then we revert to regular tips).
            if not customdata.get('_showed_onslaught_curse_tip', False):
                customdata['_showed_onslaught_curse_tip'] = True
                self.tips = [
                    ba.GameTip(
                        'Curse boxes turn you into a ticking time bomb.\n'
                        'The only cure is to quickly grab a health-pack.',
                        icon=ba.gettexture('powerupCurse'),
                        sound=ba.getsound('ding'))
                ]

        self._spawn_info_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'position': (15, -130),
                           'h_attach': 'left',
                           'v_attach': 'top',
                           'scale': 0.55,
                           'color': (0.3, 0.8, 0.3, 1.0),
                           'text': ''
                       }))
        ba.setmusic(ba.MusicType.ONSLAUGHT)

        self._scoreboard = Scoreboard(label=ba.Lstr(resource='scoreText'),
                                      score_split=0.5)

    def on_begin(self) -> None:
        super().on_begin()
        player_count = len(self.players)
        hard = self._preset not in {
            Preset.TRAINING_EASY, Preset.ROOKIE_EASY, Preset.PRO_EASY,
            Preset.UBER_EASY
        }
        if self._preset in {Preset.TRAINING, Preset.TRAINING_EASY}:
            ControlsGuide(delay=3.0, lifespan=10.0, bright=True).autoretain()

            self._have_tnt = False
            self._excluded_powerups = ['curse', 'land_mines']
            self._waves = [
                Wave(base_angle=195,
                     entries=[
                         Spawn(BomberBotLite, spacing=5),
                     ] * player_count),
                Wave(base_angle=130,
                     entries=[
                         Spawn(BrawlerBotLite, spacing=5),
                     ] * player_count),
                Wave(base_angle=195,
                     entries=[Spawn(BomberBotLite, spacing=10)] *
                     (player_count + 1)),
                Wave(base_angle=130,
                     entries=[
                         Spawn(BrawlerBotLite, spacing=10),
                     ] * (player_count + 1)),
                Wave(base_angle=130,
                     entries=[
                         Spawn(BrawlerBotLite, spacing=5)
                         if player_count > 1 else None,
                         Spawn(BrawlerBotLite, spacing=5),
                         Spacing(30),
                         Spawn(BomberBotLite, spacing=5)
                         if player_count > 3 else None,
                         Spawn(BomberBotLite, spacing=5),
                         Spacing(30),
                         Spawn(BrawlerBotLite, spacing=5),
                         Spawn(BrawlerBotLite, spacing=5)
                         if player_count > 2 else None,
                     ]),
                Wave(base_angle=195,
                     entries=[
                         Spawn(TriggerBot, spacing=90),
                         Spawn(TriggerBot, spacing=90)
                         if player_count > 1 else None,
                     ]),
            ]

        elif self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            self._have_tnt = False
            self._excluded_powerups = ['curse']
            self._waves = [
                Wave(entries=[
                    Spawn(ChargerBot, Point.LEFT_UPPER_MORE
                          ) if player_count > 2 else None,
                    Spawn(ChargerBot, Point.LEFT_UPPER),
                ]),
                Wave(entries=[
                    Spawn(BomberBotStaticLite, Point.TURRET_TOP_RIGHT),
                    Spawn(BrawlerBotLite, Point.RIGHT_UPPER),
                    Spawn(BrawlerBotLite, Point.RIGHT_LOWER
                          ) if player_count > 1 else None,
                    Spawn(BomberBotStaticLite, Point.TURRET_BOTTOM_RIGHT
                          ) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(BomberBotStaticLite, Point.TURRET_BOTTOM_LEFT),
                    Spawn(TriggerBot, Point.LEFT),
                    Spawn(TriggerBot, Point.LEFT_LOWER
                          ) if player_count > 1 else None,
                    Spawn(TriggerBot, Point.LEFT_UPPER
                          ) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(BrawlerBotLite, Point.TOP_RIGHT),
                    Spawn(BrawlerBot, Point.TOP_HALF_RIGHT
                          ) if player_count > 1 else None,
                    Spawn(BrawlerBotLite, Point.TOP_LEFT),
                    Spawn(BrawlerBotLite, Point.TOP_HALF_LEFT
                          ) if player_count > 2 else None,
                    Spawn(BrawlerBot, Point.TOP),
                    Spawn(BomberBotStaticLite, Point.TURRET_TOP_MIDDLE),
                ]),
                Wave(entries=[
                    Spawn(TriggerBotStatic, Point.TURRET_BOTTOM_LEFT),
                    Spawn(TriggerBotStatic, Point.TURRET_BOTTOM_RIGHT),
                    Spawn(TriggerBot, Point.BOTTOM),
                    Spawn(TriggerBot, Point.BOTTOM_HALF_RIGHT
                          ) if player_count > 1 else None,
                    Spawn(TriggerBot, Point.BOTTOM_HALF_LEFT
                          ) if player_count > 2 else None,
                ]),
                Wave(entries=[
                    Spawn(BomberBotStaticLite, Point.TURRET_TOP_LEFT),
                    Spawn(BomberBotStaticLite, Point.TURRET_TOP_RIGHT),
                    Spawn(ChargerBot, Point.BOTTOM),
                    Spawn(ChargerBot, Point.BOTTOM_HALF_LEFT
                          ) if player_count > 1 else None,
                    Spawn(ChargerBot, Point.BOTTOM_HALF_RIGHT
                          ) if player_count > 2 else None,
                ]),
            ]

        elif self._preset in {Preset.PRO, Preset.PRO_EASY}:
            self._excluded_powerups = ['curse']
            self._have_tnt = True
            self._waves = [
                Wave(base_angle=-50,
                     entries=[
                         Spawn(BrawlerBot, spacing=12)
                         if player_count > 3 else None,
                         Spawn(BrawlerBot, spacing=12),
                         Spawn(BomberBot, spacing=6),
                         Spawn(BomberBot, spacing=6)
                         if self._preset is Preset.PRO else None,
                         Spawn(BomberBot, spacing=6)
                         if player_count > 1 else None,
                         Spawn(BrawlerBot, spacing=12),
                         Spawn(BrawlerBot, spacing=12)
                         if player_count > 2 else None,
                     ]),
                Wave(base_angle=180,
                     entries=[
                         Spawn(BrawlerBot, spacing=6)
                         if player_count > 3 else None,
                         Spawn(BrawlerBot, spacing=6)
                         if self._preset is Preset.PRO else None,
                         Spawn(BrawlerBot, spacing=6),
                         Spawn(ChargerBot, spacing=45),
                         Spawn(ChargerBot, spacing=45)
                         if player_count > 1 else None,
                         Spawn(BrawlerBot, spacing=6),
                         Spawn(BrawlerBot, spacing=6)
                         if self._preset is Preset.PRO else None,
                         Spawn(BrawlerBot, spacing=6)
                         if player_count > 2 else None,
                     ]),
                Wave(base_angle=0,
                     entries=[
                         Spawn(ChargerBot, spacing=30),
                         Spawn(TriggerBot, spacing=30),
                         Spawn(TriggerBot, spacing=30),
                         Spawn(TriggerBot, spacing=30)
                         if self._preset is Preset.PRO else None,
                         Spawn(TriggerBot, spacing=30)
                         if player_count > 1 else None,
                         Spawn(TriggerBot, spacing=30)
                         if player_count > 3 else None,
                         Spawn(ChargerBot, spacing=30),
                     ]),
                Wave(base_angle=90,
                     entries=[
                         Spawn(StickyBot, spacing=50),
                         Spawn(StickyBot, spacing=50)
                         if self._preset is Preset.PRO else None,
                         Spawn(StickyBot, spacing=50),
                         Spawn(StickyBot, spacing=50)
                         if player_count > 1 else None,
                         Spawn(StickyBot, spacing=50)
                         if player_count > 3 else None,
                     ]),
                Wave(base_angle=0,
                     entries=[
                         Spawn(TriggerBot, spacing=72),
                         Spawn(TriggerBot, spacing=72),
                         Spawn(TriggerBot, spacing=72)
                         if self._preset is Preset.PRO else None,
                         Spawn(TriggerBot, spacing=72),
                         Spawn(TriggerBot, spacing=72),
                         Spawn(TriggerBot, spacing=36)
                         if player_count > 2 else None,
                     ]),
                Wave(base_angle=30,
                     entries=[
                         Spawn(ChargerBotProShielded, spacing=50),
                         Spawn(ChargerBotProShielded, spacing=50),
                         Spawn(ChargerBotProShielded, spacing=50)
                         if self._preset is Preset.PRO else None,
                         Spawn(ChargerBotProShielded, spacing=50)
                         if player_count > 1 else None,
                         Spawn(ChargerBotProShielded, spacing=50)
                         if player_count > 2 else None,
                     ])
            ]

        elif self._preset in {Preset.UBER, Preset.UBER_EASY}:

            # Show controls help in kiosk mode.
            if ba.app.kiosk_mode:
                ControlsGuide(delay=3.0, lifespan=10.0,
                              bright=True).autoretain()

            self._have_tnt = True
            self._excluded_powerups = []
            self._waves = [
                Wave(entries=[
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_MIDDLE_LEFT
                          ) if hard else None,
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_MIDDLE_RIGHT),
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_LEFT
                          ) if player_count > 2 else None,
                    Spawn(ExplodeyBot, Point.TOP_RIGHT),
                    Delay(4.0),
                    Spawn(ExplodeyBot, Point.TOP_LEFT),
                ]),
                Wave(entries=[
                    Spawn(ChargerBot, Point.LEFT),
                    Spawn(ChargerBot, Point.RIGHT),
                    Spawn(ChargerBot, Point.RIGHT_UPPER_MORE
                          ) if player_count > 2 else None,
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_LEFT),
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_RIGHT),
                ]),
                Wave(entries=[
                    Spawn(TriggerBotPro, Point.TOP_RIGHT),
                    Spawn(TriggerBotPro, Point.RIGHT_UPPER_MORE
                          ) if player_count > 1 else None,
                    Spawn(TriggerBotPro, Point.RIGHT_UPPER),
                    Spawn(TriggerBotPro, Point.RIGHT_LOWER) if hard else None,
                    Spawn(TriggerBotPro, Point.RIGHT_LOWER_MORE
                          ) if player_count > 2 else None,
                    Spawn(TriggerBotPro, Point.BOTTOM_RIGHT),
                ]),
                Wave(entries=[
                    Spawn(ChargerBotProShielded, Point.BOTTOM_RIGHT),
                    Spawn(ChargerBotProShielded, Point.BOTTOM
                          ) if player_count > 2 else None,
                    Spawn(ChargerBotProShielded, Point.BOTTOM_LEFT),
                    Spawn(ChargerBotProShielded, Point.TOP) if hard else None,
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_MIDDLE),
                ]),
                Wave(entries=[
                    Spawn(ExplodeyBot, Point.LEFT_UPPER),
                    Delay(1.0),
                    Spawn(BrawlerBotProShielded, Point.LEFT_LOWER),
                    Spawn(BrawlerBotProShielded, Point.LEFT_LOWER_MORE),
                    Delay(4.0),
                    Spawn(ExplodeyBot, Point.RIGHT_UPPER),
                    Delay(1.0),
                    Spawn(BrawlerBotProShielded, Point.RIGHT_LOWER),
                    Spawn(BrawlerBotProShielded, Point.RIGHT_UPPER_MORE),
                    Delay(4.0),
                    Spawn(ExplodeyBot, Point.LEFT),
                    Delay(5.0),
                    Spawn(ExplodeyBot, Point.RIGHT),
                ]),
                Wave(entries=[
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_LEFT),
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_RIGHT),
                    Spawn(BomberBotProStatic, Point.TURRET_BOTTOM_LEFT),
                    Spawn(BomberBotProStatic, Point.TURRET_BOTTOM_RIGHT),
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_MIDDLE_LEFT
                          ) if hard else None,
                    Spawn(BomberBotProStatic, Point.TURRET_TOP_MIDDLE_RIGHT
                          ) if hard else None,
                ])
            ]

        # We generate these on the fly in endless.
        elif self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            self._have_tnt = True
            self._excluded_powerups = []
            self._waves = []

        else:
            raise RuntimeError(f'Invalid preset: {self._preset}')

        # FIXME: Should migrate to use setup_standard_powerup_drops().

        # Spit out a few powerups and start dropping more shortly.
        self._drop_powerups(standard_points=True,
                            poweruptype='curse' if self._preset
                            in [Preset.UBER, Preset.UBER_EASY] else
                            ('land_mines' if self._preset
                             in [Preset.ROOKIE, Preset.ROOKIE_EASY] else None))
        ba.timer(4.0, self._start_powerup_drops)

        # Our TNT spawner (if applicable).
        if self._have_tnt:
            self._tntspawner = TNTSpawner(position=self._tntspawnpos)

        self.setup_low_life_warning_sound()
        self._update_scores()
        self._bots = SpazBotSet()
        ba.timer(4.0, self._start_updating_waves)

    def _on_got_scores_to_beat(self, scores: List[Dict[str, Any]]) -> None:
        self._show_standard_scores_to_beat_ui(scores)

    def _get_dist_grp_totals(self, grps: List[Any]) -> Tuple[int, int]:
        totalpts = 0
        totaldudes = 0
        for grp in grps:
            for grpentry in grp:
                dudes = grpentry[1]
                totalpts += grpentry[0] * dudes
                totaldudes += dudes
        return totalpts, totaldudes

    def _get_distribution(self, target_points: int, min_dudes: int,
                          max_dudes: int, group_count: int,
                          max_level: int) -> List[List[Tuple[int, int]]]:
        """Calculate a distribution of bad guys given some params."""
        max_iterations = 10 + max_dudes * 2

        groups: List[List[Tuple[int, int]]] = []
        for _g in range(group_count):
            groups.append([])
        types = [1]
        if max_level > 1:
            types.append(2)
        if max_level > 2:
            types.append(3)
        if max_level > 3:
            types.append(4)
        for iteration in range(max_iterations):
            diff = self._add_dist_entry_if_possible(groups, max_dudes,
                                                    target_points, types)

            total_points, total_dudes = self._get_dist_grp_totals(groups)
            full = (total_points >= target_points)

            if full:
                # Every so often, delete a random entry just to
                # shake up our distribution.
                if random.random() < 0.2 and iteration != max_iterations - 1:
                    self._delete_random_dist_entry(groups)

                # If we don't have enough dudes, kill the group with
                # the biggest point value.
                elif (total_dudes < min_dudes
                      and iteration != max_iterations - 1):
                    self._delete_biggest_dist_entry(groups)

                # If we've got too many dudes, kill the group with the
                # smallest point value.
                elif (total_dudes > max_dudes
                      and iteration != max_iterations - 1):
                    self._delete_smallest_dist_entry(groups)

                # Close enough.. we're done.
                else:
                    if diff == 0:
                        break

        return groups

    def _add_dist_entry_if_possible(self, groups: List[List[Tuple[int, int]]],
                                    max_dudes: int, target_points: int,
                                    types: List[int]) -> int:
        # See how much we're off our target by.
        total_points, total_dudes = self._get_dist_grp_totals(groups)
        diff = target_points - total_points
        dudes_diff = max_dudes - total_dudes

        # Add an entry if one will fit.
        value = types[random.randrange(len(types))]
        group = groups[random.randrange(len(groups))]
        if not group:
            max_count = random.randint(1, 6)
        else:
            max_count = 2 * random.randint(1, 3)
        max_count = min(max_count, dudes_diff)
        count = min(max_count, diff // value)
        if count > 0:
            group.append((value, count))
            total_points += value * count
            total_dudes += count
            diff = target_points - total_points
        return diff

    def _delete_smallest_dist_entry(
            self, groups: List[List[Tuple[int, int]]]) -> None:
        smallest_value = 9999
        smallest_entry = None
        smallest_entry_group = None
        for group in groups:
            for entry in group:
                if entry[0] < smallest_value or smallest_entry is None:
                    smallest_value = entry[0]
                    smallest_entry = entry
                    smallest_entry_group = group
        assert smallest_entry is not None
        assert smallest_entry_group is not None
        smallest_entry_group.remove(smallest_entry)

    def _delete_biggest_dist_entry(
            self, groups: List[List[Tuple[int, int]]]) -> None:
        biggest_value = 9999
        biggest_entry = None
        biggest_entry_group = None
        for group in groups:
            for entry in group:
                if entry[0] > biggest_value or biggest_entry is None:
                    biggest_value = entry[0]
                    biggest_entry = entry
                    biggest_entry_group = group
        if biggest_entry is not None:
            assert biggest_entry_group is not None
            biggest_entry_group.remove(biggest_entry)

    def _delete_random_dist_entry(self,
                                  groups: List[List[Tuple[int, int]]]) -> None:
        entry_count = 0
        for group in groups:
            for _ in group:
                entry_count += 1
        if entry_count > 1:
            del_entry = random.randrange(entry_count)
            entry_count = 0
            for group in groups:
                for entry in group:
                    if entry_count == del_entry:
                        group.remove(entry)
                        break
                    entry_count += 1

    def spawn_player(self, player: Player) -> ba.Actor:

        # We keep track of who got hurt each wave for score purposes.
        player.has_been_hurt = False
        pos = (self._spawn_center[0] + random.uniform(-1.5, 1.5),
               self._spawn_center[1],
               self._spawn_center[2] + random.uniform(-1.5, 1.5))
        spaz = self.spawn_player_spaz(player, position=pos)
        if self._preset in {
                Preset.TRAINING_EASY, Preset.ROOKIE_EASY, Preset.PRO_EASY,
                Preset.UBER_EASY
        }:
            spaz.impact_scale = 0.25
        spaz.add_dropped_bomb_callback(self._handle_player_dropped_bomb)
        return spaz

    def _handle_player_dropped_bomb(self, player: ba.Actor,
                                    bomb: ba.Actor) -> None:
        del player, bomb  # Unused.
        self._player_has_dropped_bomb = True

    def _drop_powerup(self, index: int, poweruptype: str = None) -> None:
        poweruptype = (PowerupBoxFactory.get().get_random_powerup_type(
            forcetype=poweruptype, excludetypes=self._excluded_powerups))
        PowerupBox(position=self.map.powerup_spawn_points[index],
                   poweruptype=poweruptype).autoretain()

    def _start_powerup_drops(self) -> None:
        self._powerup_drop_timer = ba.Timer(3.0,
                                            ba.WeakCall(self._drop_powerups),
                                            repeat=True)

    def _drop_powerups(self,
                       standard_points: bool = False,
                       poweruptype: str = None) -> None:
        """Generic powerup drop."""
        if standard_points:
            points = self.map.powerup_spawn_points
            for i in range(len(points)):
                ba.timer(
                    1.0 + i * 0.5,
                    ba.WeakCall(self._drop_powerup, i,
                                poweruptype if i == 0 else None))
        else:
            point = (self._powerup_center[0] + random.uniform(
                -1.0 * self._powerup_spread[0], 1.0 * self._powerup_spread[0]),
                     self._powerup_center[1],
                     self._powerup_center[2] + random.uniform(
                         -self._powerup_spread[1], self._powerup_spread[1]))

            # Drop one random one somewhere.
            PowerupBox(
                position=point,
                poweruptype=PowerupBoxFactory.get().get_random_powerup_type(
                    excludetypes=self._excluded_powerups)).autoretain()

    def do_end(self, outcome: str, delay: float = 0.0) -> None:
        """End the game with the specified outcome."""
        if outcome == 'defeat':
            self.fade_to_red()
        score: Optional[int]
        if self._wavenum >= 2:
            score = self._score
            fail_message = None
        else:
            score = None
            fail_message = ba.Lstr(resource='reachWave2Text')
        self.end(
            {
                'outcome': outcome,
                'score': score,
                'fail_message': fail_message,
                'playerinfos': self.initialplayerinfos
            },
            delay=delay)

    def _award_completion_achievements(self) -> None:
        if self._preset in {Preset.TRAINING, Preset.TRAINING_EASY}:
            self._award_achievement('Onslaught Training Victory', sound=False)
            if not self._player_has_dropped_bomb:
                self._award_achievement('Boxer', sound=False)
        elif self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            self._award_achievement('Rookie Onslaught Victory', sound=False)
            if not self._a_player_has_been_hurt:
                self._award_achievement('Flawless Victory', sound=False)
        elif self._preset in {Preset.PRO, Preset.PRO_EASY}:
            self._award_achievement('Pro Onslaught Victory', sound=False)
            if not self._player_has_dropped_bomb:
                self._award_achievement('Pro Boxer', sound=False)
        elif self._preset in {Preset.UBER, Preset.UBER_EASY}:
            self._award_achievement('Uber Onslaught Victory', sound=False)

    def _update_waves(self) -> None:

        # If we have no living bots, go to the next wave.
        assert self._bots is not None
        if (self._can_end_wave and not self._bots.have_living_bots()
                and not self._game_over):
            self._can_end_wave = False
            self._time_bonus_timer = None
            self._time_bonus_text = None
            if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
                won = False
            else:
                won = (self._wavenum == len(self._waves))

            base_delay = 4.0 if won else 0.0

            # Reward time bonus.
            if self._time_bonus > 0:
                ba.timer(0, lambda: ba.playsound(self._cashregistersound))
                ba.timer(base_delay,
                         ba.WeakCall(self._award_time_bonus, self._time_bonus))
                base_delay += 1.0

            # Reward flawless bonus.
            if self._wavenum > 0:
                have_flawless = False
                for player in self.players:
                    if player.is_alive() and not player.has_been_hurt:
                        have_flawless = True
                        ba.timer(
                            base_delay,
                            ba.WeakCall(self._award_flawless_bonus, player))
                    player.has_been_hurt = False  # reset
                if have_flawless:
                    base_delay += 1.0

            if won:
                self.show_zoom_message(ba.Lstr(resource='victoryText'),
                                       scale=1.0,
                                       duration=4.0)
                self.celebrate(20.0)
                self._award_completion_achievements()
                ba.timer(base_delay, ba.WeakCall(self._award_completion_bonus))
                base_delay += 0.85
                ba.playsound(self._winsound)
                ba.cameraflash()
                ba.setmusic(ba.MusicType.VICTORY)
                self._game_over = True

                # Can't just pass delay to do_end because our extra bonuses
                # haven't been added yet (once we call do_end the score
                # gets locked in).
                ba.timer(base_delay, ba.WeakCall(self.do_end, 'victory'))
                return

            self._wavenum += 1

            # Short celebration after waves.
            if self._wavenum > 1:
                self.celebrate(0.5)
            ba.timer(base_delay, ba.WeakCall(self._start_next_wave))

    def _award_completion_bonus(self) -> None:
        ba.playsound(self._cashregistersound)
        for player in self.players:
            try:
                if player.is_alive():
                    assert self.initialplayerinfos is not None
                    self.stats.player_scored(
                        player,
                        int(100 / len(self.initialplayerinfos)),
                        scale=1.4,
                        color=(0.6, 0.6, 1.0, 1.0),
                        title=ba.Lstr(resource='completionBonusText'),
                        screenmessage=False)
            except Exception:
                ba.print_exception()

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

    def _award_flawless_bonus(self, player: Player) -> None:
        ba.playsound(self._cashregistersound)
        try:
            if player.is_alive():
                assert self._flawless_bonus is not None
                self.stats.player_scored(
                    player,
                    self._flawless_bonus,
                    scale=1.2,
                    color=(0.6, 1.0, 0.6, 1.0),
                    title=ba.Lstr(resource='flawlessWaveText'),
                    screenmessage=False)
        except Exception:
            ba.print_exception()

    def _start_time_bonus_timer(self) -> None:
        self._time_bonus_timer = ba.Timer(1.0,
                                          ba.WeakCall(self._update_time_bonus),
                                          repeat=True)

    def _update_player_spawn_info(self) -> None:

        # If we have no living players lets just blank this.
        assert self._spawn_info_text is not None
        assert self._spawn_info_text.node
        if not any(player.is_alive() for player in self.teams[0].players):
            self._spawn_info_text.node.text = ''
        else:
            text: Union[str, ba.Lstr] = ''
            for player in self.players:
                if (not player.is_alive()
                        and (self._preset
                             in [Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT] or
                             (player.respawn_wave <= len(self._waves)))):
                    rtxt = ba.Lstr(resource='onslaughtRespawnText',
                                   subs=[('${PLAYER}', player.getname()),
                                         ('${WAVE}', str(player.respawn_wave))
                                         ])
                    text = ba.Lstr(value='${A}${B}\n',
                                   subs=[
                                       ('${A}', text),
                                       ('${B}', rtxt),
                                   ])
            self._spawn_info_text.node.text = text

    def _respawn_players_for_wave(self) -> None:
        # Respawn applicable players.
        if self._wavenum > 1 and not self.is_waiting_for_continue():
            for player in self.players:
                if (not player.is_alive()
                        and player.respawn_wave == self._wavenum):
                    self.spawn_player(player)
        self._update_player_spawn_info()

    def _setup_wave_spawns(self, wave: Wave) -> None:
        tval = 0.0
        dtime = 0.2
        if self._wavenum == 1:
            spawn_time = 3.973
            tval += 0.5
        else:
            spawn_time = 2.648

        bot_angle = wave.base_angle
        self._time_bonus = 0
        self._flawless_bonus = 0
        for info in wave.entries:
            if info is None:
                continue
            if isinstance(info, Delay):
                spawn_time += info.duration
                continue
            if isinstance(info, Spacing):
                bot_angle += info.spacing
                continue
            bot_type_2 = info.bottype
            if bot_type_2 is not None:
                assert not isinstance(bot_type_2, str)
                self._time_bonus += bot_type_2.points_mult * 20
                self._flawless_bonus += bot_type_2.points_mult * 5

            # If its got a position, use that.
            point = info.point
            if point is not None:
                assert bot_type_2 is not None
                spcall = ba.WeakCall(self.add_bot_at_point, point, bot_type_2,
                                     spawn_time)
                ba.timer(tval, spcall)
                tval += dtime
            else:
                spacing = info.spacing
                bot_angle += spacing * 0.5
                if bot_type_2 is not None:
                    tcall = ba.WeakCall(self.add_bot_at_angle, bot_angle,
                                        bot_type_2, spawn_time)
                    ba.timer(tval, tcall)
                    tval += dtime
                bot_angle += spacing * 0.5

        # We can end the wave after all the spawning happens.
        ba.timer(tval + spawn_time - dtime + 0.01,
                 ba.WeakCall(self._set_can_end_wave))

    def _start_next_wave(self) -> None:

        # This can happen if we beat a wave as we die.
        # We don't wanna respawn players and whatnot if this happens.
        if self._game_over:
            return

        self._respawn_players_for_wave()
        if self._preset in {Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT}:
            wave = self._generate_random_wave()
        else:
            wave = self._waves[self._wavenum - 1]
        self._setup_wave_spawns(wave)
        self._update_wave_ui_and_bonuses()
        ba.timer(0.4, ba.Call(ba.playsound, self._new_wave_sound))

    def _update_wave_ui_and_bonuses(self) -> None:

        self.show_zoom_message(ba.Lstr(value='${A} ${B}',
                                       subs=[('${A}',
                                              ba.Lstr(resource='waveText')),
                                             ('${B}', str(self._wavenum))]),
                               scale=1.0,
                               duration=1.0,
                               trail=True)

        # Reset our time bonus.
        tbtcolor = (1, 1, 0, 1)
        tbttxt = ba.Lstr(value='${A}: ${B}',
                         subs=[
                             ('${A}', ba.Lstr(resource='timeBonusText')),
                             ('${B}', str(self._time_bonus)),
                         ])
        self._time_bonus_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'center',
                           'h_align': 'center',
                           'vr_depth': -30,
                           'color': tbtcolor,
                           'shadow': 1.0,
                           'flatness': 1.0,
                           'position': (0, -60),
                           'scale': 0.8,
                           'text': tbttxt
                       }))

        ba.timer(5.0, ba.WeakCall(self._start_time_bonus_timer))
        wtcolor = (1, 1, 1, 1)
        wttxt = ba.Lstr(
            value='${A} ${B}',
            subs=[('${A}', ba.Lstr(resource='waveText')),
                  ('${B}', str(self._wavenum) +
                   ('' if self._preset
                    in [Preset.ENDLESS, Preset.ENDLESS_TOURNAMENT] else
                    ('/' + str(len(self._waves)))))])
        self._wave_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'center',
                           'h_align': 'center',
                           'vr_depth': -10,
                           'color': wtcolor,
                           'shadow': 1.0,
                           'flatness': 1.0,
                           'position': (0, -40),
                           'scale': 1.3,
                           'text': wttxt
                       }))

    def _bot_levels_for_wave(self) -> List[List[Type[SpazBot]]]:
        level = self._wavenum
        bot_types = [
            BomberBot, BrawlerBot, TriggerBot, ChargerBot, BomberBotPro,
            BrawlerBotPro, TriggerBotPro, BomberBotProShielded, ExplodeyBot,
            ChargerBotProShielded, StickyBot, BrawlerBotProShielded,
            TriggerBotProShielded
        ]
        if level > 5:
            bot_types += [
                ExplodeyBot,
                TriggerBotProShielded,
                BrawlerBotProShielded,
                ChargerBotProShielded,
            ]
        if level > 7:
            bot_types += [
                ExplodeyBot,
                TriggerBotProShielded,
                BrawlerBotProShielded,
                ChargerBotProShielded,
            ]
        if level > 10:
            bot_types += [
                TriggerBotProShielded, TriggerBotProShielded,
                TriggerBotProShielded, TriggerBotProShielded
            ]
        if level > 13:
            bot_types += [
                TriggerBotProShielded, TriggerBotProShielded,
                TriggerBotProShielded, TriggerBotProShielded
            ]
        bot_levels = [[b for b in bot_types if b.points_mult == 1],
                      [b for b in bot_types if b.points_mult == 2],
                      [b for b in bot_types if b.points_mult == 3],
                      [b for b in bot_types if b.points_mult == 4]]

        # Make sure all lists have something in them
        if not all(bot_levels):
            raise RuntimeError('Got empty bot level')
        return bot_levels

    def _add_entries_for_distribution_group(
            self, group: List[Tuple[int, int]],
            bot_levels: List[List[Type[SpazBot]]],
            all_entries: List[Union[Spawn, Spacing, Delay, None]]) -> None:
        entries: List[Union[Spawn, Spacing, Delay, None]] = []
        for entry in group:
            bot_level = bot_levels[entry[0] - 1]
            bot_type = bot_level[random.randrange(len(bot_level))]
            rval = random.random()
            if rval < 0.5:
                spacing = 10.0
            elif rval < 0.9:
                spacing = 20.0
            else:
                spacing = 40.0
            split = random.random() > 0.3
            for i in range(entry[1]):
                if split and i % 2 == 0:
                    entries.insert(0, Spawn(bot_type, spacing=spacing))
                else:
                    entries.append(Spawn(bot_type, spacing=spacing))
        if entries:
            all_entries += entries
            all_entries.append(
                Spacing(40.0 if random.random() < 0.5 else 80.0))

    def _generate_random_wave(self) -> Wave:
        level = self._wavenum
        bot_levels = self._bot_levels_for_wave()

        target_points = level * 3 - 2
        min_dudes = min(1 + level // 3, 10)
        max_dudes = min(10, level + 1)
        max_level = 4 if level > 6 else (3 if level > 3 else
                                         (2 if level > 2 else 1))
        group_count = 3
        distribution = self._get_distribution(target_points, min_dudes,
                                              max_dudes, group_count,
                                              max_level)
        all_entries: List[Union[Spawn, Spacing, Delay, None]] = []
        for group in distribution:
            self._add_entries_for_distribution_group(group, bot_levels,
                                                     all_entries)
        angle_rand = random.random()
        if angle_rand > 0.75:
            base_angle = 130.0
        elif angle_rand > 0.5:
            base_angle = 210.0
        elif angle_rand > 0.25:
            base_angle = 20.0
        else:
            base_angle = -30.0
        base_angle += (0.5 - random.random()) * 20.0
        wave = Wave(base_angle=base_angle, entries=all_entries)
        return wave

    def add_bot_at_point(self,
                         point: Point,
                         spaz_type: Type[SpazBot],
                         spawn_time: float = 1.0) -> None:
        """Add a new bot at a specified named point."""
        if self._game_over:
            return
        assert isinstance(point.value, str)
        pointpos = self.map.defs.points[point.value]
        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=pointpos, spawn_time=spawn_time)

    def add_bot_at_angle(self,
                         angle: float,
                         spaz_type: Type[SpazBot],
                         spawn_time: float = 1.0) -> None:
        """Add a new bot at a specified angle (for circular maps)."""
        if self._game_over:
            return
        angle_radians = angle / 57.2957795
        xval = math.sin(angle_radians) * 1.06
        zval = math.cos(angle_radians) * 1.06
        point = (xval / 0.125, 2.3, (zval / 0.2) - 3.7)
        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=point, spawn_time=spawn_time)

    def _update_time_bonus(self) -> None:
        self._time_bonus = int(self._time_bonus * 0.93)
        if self._time_bonus > 0 and self._time_bonus_text is not None:
            assert self._time_bonus_text.node
            self._time_bonus_text.node.text = ba.Lstr(
                value='${A}: ${B}',
                subs=[('${A}', ba.Lstr(resource='timeBonusText')),
                      ('${B}', str(self._time_bonus))])
        else:
            self._time_bonus_text = None

    def _start_updating_waves(self) -> None:
        self._wave_update_timer = ba.Timer(2.0,
                                           ba.WeakCall(self._update_waves),
                                           repeat=True)

    def _update_scores(self) -> None:
        score = self._score
        if self._preset is Preset.ENDLESS:
            if score >= 500:
                self._award_achievement('Onslaught Master')
            if score >= 1000:
                self._award_achievement('Onslaught Wizard')
            if score >= 5000:
                self._award_achievement('Onslaught God')
        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, PlayerSpazHurtMessage):
            msg.spaz.getplayer(Player, True).has_been_hurt = True
            self._a_player_has_been_hurt = True

        elif isinstance(msg, ba.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()

        elif isinstance(msg, ba.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            player = msg.getplayer(Player)
            self._a_player_has_been_hurt = True

            # Make note with the player when they can respawn:
            if self._wavenum < 10:
                player.respawn_wave = max(2, self._wavenum + 1)
            elif self._wavenum < 15:
                player.respawn_wave = max(2, self._wavenum + 2)
            else:
                player.respawn_wave = max(2, self._wavenum + 3)
            ba.timer(0.1, self._update_player_spawn_info)
            ba.timer(0.1, self._checkroundover)

        elif isinstance(msg, SpazBotDiedMessage):
            pts, importance = msg.spazbot.get_death_points(msg.how)
            if msg.killerplayer is not None:
                self._handle_kill_achievements(msg)
                target: Optional[Sequence[float]]
                if msg.spazbot.node:
                    target = msg.spazbot.node.position
                else:
                    target = None

                killerplayer = msg.killerplayer
                self.stats.player_scored(killerplayer,
                                         pts,
                                         target=target,
                                         kill=True,
                                         screenmessage=False,
                                         importance=importance)
                ba.playsound(self._dingsound
                             if importance == 1 else self._dingsoundhigh,
                             volume=0.6)

            # Normally we pull scores from the score-set, but if there's
            # no player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
        else:
            super().handlemessage(msg)

    def _handle_kill_achievements(self, msg: SpazBotDiedMessage) -> None:
        if self._preset in {Preset.TRAINING, Preset.TRAINING_EASY}:
            self._handle_training_kill_achievements(msg)
        elif self._preset in {Preset.ROOKIE, Preset.ROOKIE_EASY}:
            self._handle_rookie_kill_achievements(msg)
        elif self._preset in {Preset.PRO, Preset.PRO_EASY}:
            self._handle_pro_kill_achievements(msg)
        elif self._preset in {Preset.UBER, Preset.UBER_EASY}:
            self._handle_uber_kill_achievements(msg)

    def _handle_uber_kill_achievements(self, msg: SpazBotDiedMessage) -> None:

        # Uber mine achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'land_mine'):
            self._land_mine_kills += 1
            if self._land_mine_kills >= 6:
                self._award_achievement('Gold Miner')

        # Uber tnt achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'tnt'):
            self._tnt_kills += 1
            if self._tnt_kills >= 6:
                ba.timer(0.5, ba.WeakCall(self._award_achievement,
                                          'TNT Terror'))

    def _handle_pro_kill_achievements(self, msg: SpazBotDiedMessage) -> None:

        # TNT achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'tnt'):
            self._tnt_kills += 1
            if self._tnt_kills >= 3:
                ba.timer(
                    0.5,
                    ba.WeakCall(self._award_achievement,
                                'Boom Goes the Dynamite'))

    def _handle_rookie_kill_achievements(self,
                                         msg: SpazBotDiedMessage) -> None:
        # Land-mine achievement:
        if msg.spazbot.last_attacked_type == ('explosion', 'land_mine'):
            self._land_mine_kills += 1
            if self._land_mine_kills >= 3:
                self._award_achievement('Mine Games')

    def _handle_training_kill_achievements(self,
                                           msg: SpazBotDiedMessage) -> None:
        # Toss-off-map achievement:
        if msg.spazbot.last_attacked_type == ('picked_up', 'default'):
            self._throw_off_kills += 1
            if self._throw_off_kills >= 3:
                self._award_achievement('Off You Go Then')

    def _set_can_end_wave(self) -> None:
        self._can_end_wave = True

    def end_game(self) -> None:
        # Tell our bots to celebrate just to rub it in.
        assert self._bots is not None
        self._bots.final_celebrate()
        self._game_over = True
        self.do_end('defeat', delay=2.0)
        ba.setmusic(None)

    def on_continue(self) -> None:
        for player in self.players:
            if not player.is_alive():
                self.spawn_player(player)

    def _checkroundover(self) -> None:
        """Potentially end the round based on the state of the game."""
        if self.has_ended():
            return
        if not any(player.is_alive() for player in self.teams[0].players):
            # Allow continuing after wave 1.
            if self._wavenum > 1:
                self.continue_or_end_game()
            else:
                self.end_game()
