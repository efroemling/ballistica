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
from typing import TYPE_CHECKING

import ba
from bastd.actor import bomb as stdbomb
from bastd.actor import playerspaz, spazbot

if TYPE_CHECKING:
    from typing import Any, Type, Dict, Optional, List, Tuple, Union, Sequence
    from bastd.actor.scoreboard import Scoreboard


class OnslaughtGame(ba.CoopGameActivity):
    """Co-op game where players try to survive attacking waves of enemies."""

    tips: List[Union[str, Dict[str, Any]]] = [
        'Hold any button to run.'
        '  (Trigger buttons work well if you have them)',
        'Try tricking enemies into killing eachother or running off cliffs.',
        'Try \'Cooking off\' bombs for a second or two before throwing them.',
        'It\'s easier to win with a friend or two helping.',
        'If you stay in one place, you\'re toast. Run and dodge to survive..',
        'Practice using your momentum to throw bombs more accurately.',
        'Your punches do much more damage if you are running or spinning.'
    ]

    @classmethod
    def get_name(cls) -> str:
        return 'Onslaught'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return "Defeat all enemies."

    def __init__(self, settings: Dict[str, Any]):

        self._preset = settings.get('preset', 'training')
        if self._preset in [
                'training',
                'training_easy',
                'pro',
                'pro_easy',
                'endless',
                'endless_tournament',
        ]:
            settings['map'] = 'Doom Shroom'
        else:
            settings['map'] = 'Courtyard'

        super().__init__(settings)

        # Show messages when players die since it matters here.
        self.announce_player_deaths = True

        self._new_wave_sound = ba.getsound('scoreHit01')
        self._winsound = ba.getsound("score")
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
            raise Exception("Unsupported map: " + str(settings['map']))
        self._scoreboard: Optional[Scoreboard] = None
        self._game_over = False
        self._wave = 0
        self._can_end_wave = True
        self._score = 0
        self._time_bonus = 0
        self._spawn_info_text: Optional[ba.Actor] = None
        self._dingsound = ba.getsound('dingSmall')
        self._dingsoundhigh = ba.getsound('dingSmallHigh')
        self._have_tnt = False
        self._excludepowerups: Optional[List[str]] = None
        self._waves: Optional[List[Dict[str, Any]]] = None
        self._tntspawner: Optional[stdbomb.TNTSpawner] = None
        self._bots: Optional[spazbot.BotSet] = None
        self._powerup_drop_timer: Optional[ba.Timer] = None
        self._time_bonus_timer: Optional[ba.Timer] = None
        self._time_bonus_text: Optional[ba.Actor] = None
        self._flawless_bonus: Optional[int] = None
        self._wave_text: Optional[ba.Actor] = None
        self._wave_update_timer: Optional[ba.Timer] = None
        self._throw_off_kills = 0
        self._land_mine_kills = 0
        self._tnt_kills = 0

    def on_transition_in(self) -> None:
        from bastd.actor.scoreboard import Scoreboard
        super().on_transition_in()

        # Show special landmine tip on rookie preset.
        if self._preset in ['rookie', 'rookie_easy']:
            # Show once per session only (then we revert to regular tips).
            if not hasattr(ba.getsession(),
                           '_g_showed_onslaught_land_mine_tip'):
                # pylint: disable=protected-access
                ba.getsession(  # type: ignore
                )._g_showed_onslaught_land_mine_tip = True
                self.tips = [{
                    'tip': "Land-mines are a good way"
                           " to stop speedy enemies.",
                    'icon': ba.gettexture('powerupLandMines'),
                    'sound': ba.getsound('ding')
                }]

        # Show special tnt tip on pro preset.
        if self._preset in ['pro', 'pro_easy']:
            # Show once per session only (then we revert to regular tips).
            if not hasattr(ba.getsession(), '_g_showed_onslaught_tnt_tip'):
                # pylint: disable=protected-access
                ba.getsession(  # type: ignore
                )._g_showed_onslaught_tnt_tip = True
                self.tips = [{
                    'tip': "Take out a group of enemies by\n"
                           "setting off a bomb near a TNT box.",
                    'icon': ba.gettexture('tnt'),
                    'sound': ba.getsound('ding')
                }]

        # Show special curse tip on uber preset.
        if self._preset in ['uber', 'uber_easy']:
            # Show once per session only (then we revert to regular tips).
            if not hasattr(ba.getsession(), '_g_showed_onslaught_curse_tip'):
                # pylint: disable=protected-access
                ba.getsession(  # type: ignore
                )._g_showed_onslaught_curse_tip = True
                self.tips = [{
                    'tip': "Curse boxes turn you into a ticking time bomb.\n"
                           "The only cure is to quickly grab a health-pack.",
                    'icon': ba.gettexture('powerupCurse'),
                    'sound': ba.getsound('ding')
                }]

        self._spawn_info_text = ba.Actor(
            ba.newnode("text",
                       attrs={
                           'position': (15, -130),
                           'h_attach': "left",
                           'v_attach': "top",
                           'scale': 0.55,
                           'color': (0.3, 0.8, 0.3, 1.0),
                           'text': ''
                       }))
        ba.setmusic('Onslaught')

        self._scoreboard = Scoreboard(label=ba.Lstr(resource='scoreText'),
                                      score_split=0.5)

    def on_begin(self) -> None:
        from bastd.actor.controlsguide import ControlsGuide
        super().on_begin()
        player_count = len(self.players)
        hard = self._preset not in [
            'training_easy', 'rookie_easy', 'pro_easy', 'uber_easy'
        ]
        if self._preset in ['training', 'training_easy']:
            ControlsGuide(delay=3.0, lifespan=10.0, bright=True).autoretain()

            self._have_tnt = False
            self._excludepowerups = ['curse', 'land_mines']
            self._waves = [
                {'base_angle': 195,
                 'entries': [
                     {'type': spazbot.BomberBotLite, 'spacing': 5},
                 ] * player_count},
                {'base_angle': 130,
                 'entries': [
                     {'type': spazbot.BrawlerBotLite, 'spacing': 5},
                 ] * player_count},
                {'base_angle': 195,
                 'entries': [
                     {'type': spazbot.BomberBotLite, 'spacing': 10},
                 ] * (player_count + 1)},
                {'base_angle': 130,
                 'entries': [
                     {'type': spazbot.BrawlerBotLite, 'spacing': 10},
                 ] * (player_count + 1)},
                {'base_angle': 130,
                 'entries': [
                     {'type': spazbot.BrawlerBotLite, 'spacing': 5}
                         if player_count > 1 else None,
                     {'type': spazbot.BrawlerBotLite, 'spacing': 5},
                     {'type': None, 'spacing': 30},
                     {'type': spazbot.BomberBotLite, 'spacing': 5}
                         if player_count > 3 else None,
                     {'type': spazbot.BomberBotLite, 'spacing': 5},
                     {'type': None, 'spacing': 30},
                     {'type': spazbot.BrawlerBotLite, 'spacing': 5},
                     {'type': spazbot.BrawlerBotLite, 'spacing': 5}
                         if player_count > 2 else None,
                 ]},
                {'base_angle': 195,
                 'entries': [
                     {'type': spazbot.TriggerBot, 'spacing': 90},
                     {'type': spazbot.TriggerBot, 'spacing': 90}
                         if player_count > 1 else None,
                 ]},
            ]  # yapf: disable

        elif self._preset in ['rookie', 'rookie_easy']:
            self._have_tnt = False
            self._excludepowerups = ['curse']
            self._waves = [
                {'entries': [
                    {'type': spazbot.ChargerBot, 'point': 'left_upper_more'}
                        if player_count > 2 else None,
                    {'type': spazbot.ChargerBot, 'point': 'left_upper'},
                ]},
                {'entries': [
                    {'type': spazbot.BomberBotStaticLite,
                     'point': 'turret_top_right'},
                    {'type': spazbot.BrawlerBotLite, 'point': 'right_upper'},
                    {'type': spazbot.BrawlerBotLite, 'point': 'right_lower'}
                        if player_count > 1 else None,
                    {'type': spazbot.BomberBotStaticLite,
                     'point': 'turret_bottom_right'}
                         if player_count > 2 else None,
                ]},
                {'entries': [
                    {'type': spazbot.BomberBotStaticLite,
                     'point': 'turret_bottom_left'},
                    {'type': spazbot.TriggerBot, 'point': 'Left'},
                    {'type': spazbot.TriggerBot, 'point': 'left_lower'}
                        if player_count > 1 else None,
                    {'type': spazbot.TriggerBot, 'point': 'left_upper'}
                        if player_count > 2 else None,
                ]},
                {'entries': [
                    {'type': spazbot.BrawlerBotLite, 'point': 'top_right'},
                    {'type': spazbot.BrawlerBot, 'point': 'top_half_right'}
                        if player_count > 1 else None,
                    {'type': spazbot.BrawlerBotLite, 'point': 'top_left'},
                    {'type': spazbot.BrawlerBotLite, 'point': 'top_half_left'}
                        if player_count > 2 else None,
                    {'type': spazbot.BrawlerBot, 'point': 'top'},
                    {'type': spazbot.BomberBotStaticLite,
                     'point': 'turret_top_middle'},
                ]},
                {'entries': [
                    {'type': spazbot.TriggerBotStatic,
                     'point': 'turret_bottom_left'},
                    {'type': spazbot.TriggerBotStatic,
                     'point': 'turret_bottom_right'},
                    {'type': spazbot.TriggerBot, 'point': 'bottom'},
                    {'type': spazbot.TriggerBot, 'point': 'bottom_half_right'}
                        if player_count > 1 else None,
                    {'type': spazbot.TriggerBot, 'point': 'bottom_half_left'}
                        if player_count > 2 else None,
                ]},
                {'entries': [
                    {'type': spazbot.BomberBotStaticLite,
                     'point': 'turret_top_left'},
                    {'type': spazbot.BomberBotStaticLite,
                     'point': 'turret_top_right'},
                    {'type': spazbot.ChargerBot, 'point': 'bottom'},
                    {'type': spazbot.ChargerBot, 'point': 'bottom_half_left'}
                        if player_count > 1 else None,
                    {'type': spazbot.ChargerBot, 'point': 'bottom_half_right'}
                        if player_count > 2 else None,
                ]},
            ]  # yapf: disable

        elif self._preset in ['pro', 'pro_easy']:
            self._excludepowerups = ['curse']
            self._have_tnt = True
            self._waves = [
                {'base_angle': -50,
                 'entries': [
                     {'type': spazbot.BrawlerBot, 'spacing': 12}
                         if player_count > 3 else None,
                     {'type': spazbot.BrawlerBot, 'spacing': 12},
                     {'type': spazbot.BomberBot, 'spacing': 6},
                     {'type': spazbot.BomberBot, 'spacing': 6}
                         if self._preset == 'pro' else None,
                     {'type': spazbot.BomberBot, 'spacing': 6}
                         if player_count > 1 else None,
                     {'type': spazbot.BrawlerBot, 'spacing': 12},
                     {'type': spazbot.BrawlerBot, 'spacing': 12}
                         if player_count > 2 else None,
                 ]},
                {'base_angle': 180,
                 'entries': [
                     {'type': spazbot.BrawlerBot, 'spacing': 6}
                         if player_count > 3 else None,
                     {'type': spazbot.BrawlerBot, 'spacing': 6}
                         if self._preset == 'pro' else None,
                     {'type': spazbot.BrawlerBot, 'spacing': 6},
                     {'type': spazbot.ChargerBot, 'spacing': 45},
                     {'type': spazbot.ChargerBot, 'spacing': 45}
                         if player_count > 1 else None,
                     {'type': spazbot.BrawlerBot, 'spacing': 6},
                     {'type': spazbot.BrawlerBot, 'spacing': 6}
                         if self._preset == 'pro' else None,
                     {'type': spazbot.BrawlerBot, 'spacing': 6}
                         if player_count > 2 else None,
                 ]},
                {'base_angle': 0,
                 'entries': [
                     {'type': spazbot.ChargerBot, 'spacing': 30},
                     {'type': spazbot.TriggerBot, 'spacing': 30},
                     {'type': spazbot.TriggerBot, 'spacing': 30},
                     {'type': spazbot.TriggerBot, 'spacing': 30}
                         if self._preset == 'pro' else None,
                     {'type': spazbot.TriggerBot, 'spacing': 30}
                         if player_count > 1 else None,
                     {'type': spazbot.TriggerBot, 'spacing': 30}
                         if player_count > 3 else None,
                     {'type': spazbot.ChargerBot, 'spacing': 30},
                 ]},
                {'base_angle': 90,
                'entries': [
                    {'type': spazbot.StickyBot, 'spacing': 50},
                    {'type': spazbot.StickyBot, 'spacing': 50}
                        if self._preset == 'pro' else None,
                    {'type': spazbot.StickyBot, 'spacing': 50},
                    {'type': spazbot.StickyBot, 'spacing': 50}
                        if player_count > 1 else None,
                    {'type': spazbot.StickyBot, 'spacing': 50}
                        if player_count > 3 else None,
                ]},
                {'base_angle': 0,
                'entries': [
                    {'type': spazbot.TriggerBot, 'spacing': 72},
                    {'type': spazbot.TriggerBot, 'spacing': 72},
                    {'type': spazbot.TriggerBot, 'spacing': 72}
                        if self._preset == 'pro' else None,
                    {'type': spazbot.TriggerBot, 'spacing': 72},
                    {'type': spazbot.TriggerBot, 'spacing': 72},
                    {'type': spazbot.TriggerBot, 'spacing': 36}
                        if player_count > 2 else None,
                ]},
                {'base_angle': 30,
                 'entries': [
                     {'type': spazbot.ChargerBotProShielded, 'spacing': 50},
                     {'type': spazbot.ChargerBotProShielded, 'spacing': 50},
                     {'type': spazbot.ChargerBotProShielded, 'spacing': 50}
                         if self._preset == 'pro' else None,
                     {'type': spazbot.ChargerBotProShielded, 'spacing': 50}
                         if player_count > 1 else None,
                     {'type': spazbot.ChargerBotProShielded, 'spacing': 50}
                         if player_count > 2 else None,
                ]}
            ]  # yapf: disable

        elif self._preset in ['uber', 'uber_easy']:

            # Show controls help in kiosk mode.
            if ba.app.kiosk_mode:
                ControlsGuide(delay=3.0, lifespan=10.0,
                              bright=True).autoretain()

            self._have_tnt = True
            self._excludepowerups = []
            self._waves = [
                {'entries': [
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_middle_left'}
                        if hard else None,
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_middle_right'},
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_left'}
                        if player_count > 2 else None,
                    {'type': spazbot.ExplodeyBot, 'point': 'top_right'},
                    {'type': 'delay', 'duration': 4.0},
                    {'type': spazbot.ExplodeyBot, 'point': 'top_left'},
                ]},
                {'entries': [
                    {'type': spazbot.ChargerBot, 'point': 'Left'},
                    {'type': spazbot.ChargerBot, 'point': 'Right'},
                    {'type': spazbot.ChargerBot, 'point': 'right_upper_more'}
                        if player_count > 2 else None,
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_left'},
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_right'},
                ]},
                {'entries': [
                    {'type': spazbot.TriggerBotPro, 'point': 'top_right'},
                    {'type': spazbot.TriggerBotPro,
                     'point': 'right_upper_more'}
                        if player_count > 1 else None,
                    {'type': spazbot.TriggerBotPro, 'point': 'right_upper'},
                    {'type': spazbot.TriggerBotPro, 'point': 'right_lower'}
                        if hard else None,
                    {'type': spazbot.TriggerBotPro,
                     'point': 'right_lower_more'}
                        if player_count > 2 else None,
                    {'type': spazbot.TriggerBotPro, 'point': 'bottom_right'},
                ]},
                {'entries': [
                    {'type': spazbot.ChargerBotProShielded,
                     'point': 'bottom_right'},
                    {'type': spazbot.ChargerBotProShielded, 'point': 'Bottom'}
                        if player_count > 2 else None,
                    {'type': spazbot.ChargerBotProShielded,
                     'point': 'bottom_left'},
                    {'type': spazbot.ChargerBotProShielded, 'point': 'Top'}
                        if hard else None,
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_middle'},
                ]},
                {'entries': [
                    {'type': spazbot.ExplodeyBot, 'point': 'left_upper'},
                    {'type': 'delay', 'duration': 1.0},
                    {'type': spazbot.BrawlerBotProShielded,
                     'point': 'left_lower'},
                    {'type': spazbot.BrawlerBotProShielded,
                     'point': 'left_lower_more'},
                    {'type': 'delay', 'duration': 4.0},
                    {'type': spazbot.ExplodeyBot, 'point': 'right_upper'},
                    {'type': 'delay', 'duration': 1.0},
                    {'type': spazbot.BrawlerBotProShielded,
                     'point': 'right_lower'},
                    {'type': spazbot.BrawlerBotProShielded,
                     'point': 'right_upper_more'},
                    {'type': 'delay', 'duration': 4.0},
                    {'type': spazbot.ExplodeyBot, 'point': 'Left'},
                    {'type': 'delay', 'duration': 5.0},
                    {'type': spazbot.ExplodeyBot, 'point': 'Right'},
                ]},
                {'entries': [
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_left'},
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_right'},
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_bottom_left'},
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_bottom_right'},
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_middle_left'} if hard else None,
                    {'type': spazbot.BomberBotProStatic,
                     'point': 'turret_top_middle_right'} if hard else None,
                ]
            }]  # yapf: disable

        # We generate these on the fly in endless.
        elif self._preset in ['endless', 'endless_tournament']:
            self._have_tnt = True
            self._excludepowerups = []

        else:
            raise Exception("Invalid preset: " + str(self._preset))

        # FIXME: Should migrate to use setup_standard_powerup_drops().

        # Spit out a few powerups and start dropping more shortly.
        self._drop_powerups(
            standard_points=True,
            poweruptype='curse' if self._preset in ['uber', 'uber_easy'] else
            ('land_mines'
             if self._preset in ['rookie', 'rookie_easy'] else None))
        ba.timer(4.0, self._start_powerup_drops)

        # Our TNT spawner (if applicable).
        if self._have_tnt:
            self._tntspawner = stdbomb.TNTSpawner(position=self._tntspawnpos)

        self.setup_low_life_warning_sound()
        self._update_scores()
        self._bots = spazbot.BotSet()
        ba.timer(4.0, self._start_updating_waves)

    def _on_got_scores_to_beat(self, scores: List[Dict[str, Any]]) -> None:
        self._show_standard_scores_to_beat_ui(scores)

    def _get_distribution(self, target_points: int, min_dudes: int,
                          max_dudes: int, group_count: int,
                          max_level: int) -> List[List[Tuple[int, int]]]:
        """ calculate a distribution of bad guys given some params """
        # FIXME; This method wears the cone of shame
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks
        max_iterations = 10 + max_dudes * 2

        def _get_totals(grps: List[Any]) -> Tuple[int, int]:
            totalpts = 0
            totaldudes = 0
            for grp in grps:
                for grpentry in grp:
                    dudes = grpentry[1]
                    totalpts += grpentry[0] * dudes
                    totaldudes += dudes
            return totalpts, totaldudes

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

            # See how much we're off our target by.
            total_points, total_dudes = _get_totals(groups)
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

            total_points, total_dudes = _get_totals(groups)
            full = (total_points >= target_points)

            if full:
                # Every so often, delete a random entry just to
                # shake up our distribution.
                if random.random() < 0.2 and iteration != max_iterations - 1:
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

                # If we don't have enough dudes, kill the group with
                # the biggest point value.
                elif (total_dudes < min_dudes
                      and iteration != max_iterations - 1):
                    biggest_value = 9999
                    biggest_entry = None
                    biggest_entry_group = None
                    for group in groups:
                        for entry in group:
                            if (entry[0] > biggest_value
                                    or biggest_entry is None):
                                biggest_value = entry[0]
                                biggest_entry = entry
                                biggest_entry_group = group
                    if biggest_entry is not None:
                        assert biggest_entry_group is not None
                        biggest_entry_group.remove(biggest_entry)

                # If we've got too many dudes, kill the group with the
                # smallest point value.
                elif (total_dudes > max_dudes
                      and iteration != max_iterations - 1):
                    smallest_value = 9999
                    smallest_entry = None
                    smallest_entry_group = None
                    for group in groups:
                        for entry in group:
                            if (entry[0] < smallest_value
                                    or smallest_entry is None):
                                smallest_value = entry[0]
                                smallest_entry = entry
                                smallest_entry_group = group
                    assert smallest_entry is not None
                    assert smallest_entry_group is not None
                    smallest_entry_group.remove(smallest_entry)

                # Close enough.. we're done.
                else:
                    if diff == 0:
                        break

        return groups

    def spawn_player(self, player: ba.Player) -> ba.Actor:

        # We keep track of who got hurt each wave for score purposes.
        player.gamedata['has_been_hurt'] = False
        pos = (self._spawn_center[0] + random.uniform(-1.5, 1.5),
               self._spawn_center[1],
               self._spawn_center[2] + random.uniform(-1.5, 1.5))
        spaz = self.spawn_player_spaz(player, position=pos)
        if self._preset in [
                'training_easy', 'rookie_easy', 'pro_easy', 'uber_easy'
        ]:
            spaz.impact_scale = 0.25
        spaz.add_dropped_bomb_callback(self._handle_player_dropped_bomb)
        return spaz

    def _handle_player_dropped_bomb(self, player: ba.Actor,
                                    bomb: ba.Actor) -> None:
        del player, bomb  # Unused.
        self._player_has_dropped_bomb = True

    def _drop_powerup(self, index: int, poweruptype: str = None) -> None:
        from bastd.actor import powerupbox
        poweruptype = (powerupbox.get_factory().get_random_powerup_type(
            forcetype=poweruptype, excludetypes=self._excludepowerups))
        powerupbox.PowerupBox(position=self.map.powerup_spawn_points[index],
                              poweruptype=poweruptype).autoretain()

    def _start_powerup_drops(self) -> None:
        self._powerup_drop_timer = ba.Timer(3.0,
                                            ba.WeakCall(self._drop_powerups),
                                            repeat=True)

    def _drop_powerups(self,
                       standard_points: bool = False,
                       poweruptype: str = None) -> None:
        """Generic powerup drop."""
        from bastd.actor import powerupbox
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
            powerupbox.PowerupBox(
                position=point,
                poweruptype=powerupbox.get_factory().get_random_powerup_type(
                    excludetypes=self._excludepowerups)).autoretain()

    def do_end(self, outcome: str, delay: float = 0.0) -> None:
        """End the game with the specified outcome."""
        if outcome == 'defeat':
            self.fade_to_red()
        score: Optional[int]
        if self._wave >= 2:
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
                'player_info': self.initial_player_info
            },
            delay=delay)

    def _update_waves(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        # If we have no living bots, go to the next wave.
        assert self._bots is not None
        if (self._can_end_wave and not self._bots.have_living_bots()
                and not self._game_over):
            self._can_end_wave = False
            self._time_bonus_timer = None
            self._time_bonus_text = None
            if self._preset in ['endless', 'endless_tournament']:
                won = False
            else:
                assert self._waves is not None
                won = (self._wave == len(self._waves))

            # Reward time bonus.
            base_delay = 4.0 if won else 0.0

            if self._time_bonus > 0:
                ba.timer(0, lambda: ba.playsound(self._cashregistersound))
                ba.timer(base_delay,
                         ba.WeakCall(self._award_time_bonus, self._time_bonus))
                base_delay += 1.0

            # Reward flawless bonus.
            if self._wave > 0:
                have_flawless = False
                for player in self.players:
                    if (player.is_alive()
                            and not player.gamedata['has_been_hurt']):
                        have_flawless = True
                        ba.timer(
                            base_delay,
                            ba.WeakCall(self._award_flawless_bonus, player))
                    player.gamedata['has_been_hurt'] = False  # reset
                if have_flawless:
                    base_delay += 1.0

            if won:
                self.show_zoom_message(ba.Lstr(resource='victoryText'),
                                       scale=1.0,
                                       duration=4.0)
                self.celebrate(20.0)

                # Rookie onslaught completion.
                if self._preset in ['training', 'training_easy']:
                    self._award_achievement('Onslaught Training Victory',
                                            sound=False)
                    if not self._player_has_dropped_bomb:
                        self._award_achievement('Boxer', sound=False)
                elif self._preset in ['rookie', 'rookie_easy']:
                    self._award_achievement('Rookie Onslaught Victory',
                                            sound=False)
                    if not self._a_player_has_been_hurt:
                        self._award_achievement('Flawless Victory',
                                                sound=False)
                elif self._preset in ['pro', 'pro_easy']:
                    self._award_achievement('Pro Onslaught Victory',
                                            sound=False)
                    if not self._player_has_dropped_bomb:
                        self._award_achievement('Pro Boxer', sound=False)
                elif self._preset in ['uber', 'uber_easy']:
                    self._award_achievement('Uber Onslaught Victory',
                                            sound=False)

                ba.timer(base_delay, ba.WeakCall(self._award_completion_bonus))
                base_delay += 0.85
                ba.playsound(self._winsound)
                ba.cameraflash()
                ba.setmusic('Victory')
                self._game_over = True

                # Can't just pass delay to do_end because our extra bonuses
                # haven't been added yet (once we call do_end the score
                # gets locked in).
                ba.timer(base_delay, ba.WeakCall(self.do_end, 'victory'))
                return

            self._wave += 1

            # Short celebration after waves.
            if self._wave > 1:
                self.celebrate(0.5)
            ba.timer(base_delay, ba.WeakCall(self._start_next_wave))

    def _award_completion_bonus(self) -> None:
        ba.playsound(self._cashregistersound)
        for player in self.players:
            try:
                if player.is_alive():
                    assert self.initial_player_info is not None
                    self.stats.player_scored(
                        player,
                        int(100 / len(self.initial_player_info)),
                        scale=1.4,
                        color=(0.6, 0.6, 1.0, 1.0),
                        title=ba.Lstr(resource='completionBonusText'),
                        screenmessage=False)
            except Exception:
                ba.print_exception()

    def _award_time_bonus(self, bonus: int) -> None:
        from bastd.actor import popuptext
        ba.playsound(self._cashregistersound)
        popuptext.PopupText(ba.Lstr(value='+${A} ${B}',
                                    subs=[('${A}', str(bonus)),
                                          ('${B}',
                                           ba.Lstr(resource='timeBonusText'))
                                          ]),
                            color=(1, 1, 0.5, 1),
                            scale=1.0,
                            position=(0, 3, -1)).autoretain()
        self._score += self._time_bonus
        self._update_scores()

    def _award_flawless_bonus(self, player: ba.Player) -> None:
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
                assert self._waves is not None
                if (not player.is_alive() and
                    (self._preset in ['endless', 'endless_tournament'] or
                     (player.gamedata['respawn_wave'] <= len(self._waves)))):
                    rtxt = ba.Lstr(resource='onslaughtRespawnText',
                                   subs=[('${PLAYER}', player.get_name()),
                                         ('${WAVE}',
                                          str(player.gamedata['respawn_wave']))
                                         ])
                    text = ba.Lstr(value='${A}${B}\n',
                                   subs=[
                                       ('${A}', text),
                                       ('${B}', rtxt),
                                   ])
            self._spawn_info_text.node.text = text

    def _start_next_wave(self) -> None:

        # FIXME; tidy up
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        # This could happen if we beat a wave as we die.
        # We don't wanna respawn players and whatnot if this happens.
        if self._game_over:
            return

        # respawn applicable players
        if self._wave > 1 and not self.is_waiting_for_continue():
            for player in self.players:
                if (not player.is_alive()
                        and player.gamedata['respawn_wave'] == self._wave):
                    self.spawn_player(player)
        self._update_player_spawn_info()
        self.show_zoom_message(ba.Lstr(value='${A} ${B}',
                                       subs=[('${A}',
                                              ba.Lstr(resource='waveText')),
                                             ('${B}', str(self._wave))]),
                               scale=1.0,
                               duration=1.0,
                               trail=True)
        ba.timer(0.4, ba.Call(ba.playsound, self._new_wave_sound))
        tval = 0.0
        dtime = 0.2
        if self._wave == 1:
            spawn_time = 3.973
            tval += 0.5
        else:
            spawn_time = 2.648

        # Populate waves:

        # Generate random waves in endless mode.
        wave: Dict[str, Any]
        if self._preset in ['endless', 'endless_tournament']:
            level = self._wave
            bot_types2 = [
                spazbot.BomberBot, spazbot.BrawlerBot, spazbot.TriggerBot,
                spazbot.ChargerBot, spazbot.BomberBotPro,
                spazbot.BrawlerBotPro, spazbot.TriggerBotPro,
                spazbot.BomberBotProShielded, spazbot.ExplodeyBot,
                spazbot.ChargerBotProShielded, spazbot.StickyBot,
                spazbot.BrawlerBotProShielded, spazbot.TriggerBotProShielded
            ]
            if level > 5:
                bot_types2 += [
                    spazbot.ExplodeyBot,
                    spazbot.TriggerBotProShielded,
                    spazbot.BrawlerBotProShielded,
                    spazbot.ChargerBotProShielded,
                ]
            if level > 7:
                bot_types2 += [
                    spazbot.ExplodeyBot,
                    spazbot.TriggerBotProShielded,
                    spazbot.BrawlerBotProShielded,
                    spazbot.ChargerBotProShielded,
                ]
            if level > 10:
                bot_types2 += [
                    spazbot.TriggerBotProShielded,
                    spazbot.TriggerBotProShielded,
                    spazbot.TriggerBotProShielded,
                    spazbot.TriggerBotProShielded
                ]
            if level > 13:
                bot_types2 += [
                    spazbot.TriggerBotProShielded,
                    spazbot.TriggerBotProShielded,
                    spazbot.TriggerBotProShielded,
                    spazbot.TriggerBotProShielded
                ]

            bot_levels = [[b for b in bot_types2 if b.points_mult == 1],
                          [b for b in bot_types2 if b.points_mult == 2],
                          [b for b in bot_types2 if b.points_mult == 3],
                          [b for b in bot_types2 if b.points_mult == 4]]

            # Make sure all lists have something in them
            if not all(bot_levels):
                raise Exception()

            target_points = level * 3 - 2
            min_dudes = min(1 + level // 3, 10)
            max_dudes = min(10, level + 1)
            max_level = 4 if level > 6 else (3 if level > 3 else
                                             (2 if level > 2 else 1))
            group_count = 3
            distribution = self._get_distribution(target_points, min_dudes,
                                                  max_dudes, group_count,
                                                  max_level)

            all_entries: List[Dict[str, Any]] = []
            for group in distribution:
                entries: List[Dict[str, Any]] = []
                for entry in group:
                    bot_level = bot_levels[entry[0] - 1]
                    bot_type = bot_level[random.randrange(len(bot_level))]
                    rval = random.random()
                    if rval < 0.5:
                        spacing = 10
                    elif rval < 0.9:
                        spacing = 20
                    else:
                        spacing = 40
                    split = random.random() > 0.3
                    for i in range(entry[1]):
                        if split and i % 2 == 0:
                            entries.insert(0, {
                                "type": bot_type,
                                "spacing": spacing
                            })
                        else:
                            entries.append({
                                "type": bot_type,
                                "spacing": spacing
                            })
                if entries:
                    all_entries += entries
                    all_entries.append({
                        "type": None,
                        "spacing": 40 if random.random() < 0.5 else 80
                    })

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
            wave = {'base_angle': base_angle, 'entries': all_entries}
        else:
            assert self._waves is not None
            wave = self._waves[self._wave - 1]
        entries = []
        bot_angle = wave.get('base_angle', 0.0)
        entries += wave['entries']
        this_time_bonus = 0
        this_flawless_bonus = 0
        for info in entries:
            if info is None:
                continue
            bot_type_2 = info['type']
            if bot_type_2 == 'delay':
                spawn_time += info['duration']
                continue
            if bot_type_2 is not None:
                this_time_bonus += bot_type_2.points_mult * 20
                this_flawless_bonus += bot_type_2.points_mult * 5
            # if its got a position, use that
            point = info.get('point', None)
            if point is not None:
                spcall = ba.WeakCall(self.add_bot_at_point, point, bot_type_2,
                                     spawn_time)
                ba.timer(tval, spcall)
                tval += dtime
            else:
                spacing = info.get('spacing', 5.0)
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

        # Reset our time bonus.
        self._time_bonus = this_time_bonus
        self._flawless_bonus = this_flawless_bonus
        tbtcolor = (1, 1, 0, 1)
        tbttxt = ba.Lstr(value='${A}: ${B}',
                         subs=[
                             ('${A}', ba.Lstr(resource='timeBonusText')),
                             ('${B}', str(self._time_bonus)),
                         ])
        self._time_bonus_text = ba.Actor(
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
        assert self._waves is not None
        wttxt = ba.Lstr(
            value='${A} ${B}',
            subs=[
                ('${A}', ba.Lstr(resource='waveText')),
                ('${B}', str(self._wave) +
                 ('' if self._preset in ['endless', 'endless_tournament'] else
                  ('/' + str(len(self._waves)))))
            ])
        self._wave_text = ba.Actor(
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

    def add_bot_at_point(self,
                         point: str,
                         spaz_type: Type[spazbot.SpazBot],
                         spawn_time: float = 1.0) -> None:
        """Add a new bot at a specified named point."""
        if self._game_over:
            return
        pointpos = self.map.defs.points['bot_spawn_' + point]
        assert self._bots is not None
        self._bots.spawn_bot(spaz_type, pos=pointpos, spawn_time=spawn_time)

    def add_bot_at_angle(self,
                         angle: float,
                         spaz_type: Type[spazbot.SpazBot],
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
        if self._preset == 'endless':
            if score >= 500:
                self._award_achievement('Onslaught Master')
            if score >= 1000:
                self._award_achievement('Onslaught Wizard')
            if score >= 5000:
                self._award_achievement('Onslaught God')
        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)

    def handlemessage(self, msg: Any) -> Any:

        # FIXME; tidy this up
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        if isinstance(msg, playerspaz.PlayerSpazHurtMessage):
            player = msg.spaz.getplayer()
            if not player:
                return
            player.gamedata['has_been_hurt'] = True
            self._a_player_has_been_hurt = True

        elif isinstance(msg, ba.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()

        elif isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            player = msg.spaz.getplayer()
            assert player is not None
            self._a_player_has_been_hurt = True

            # Make note with the player when they can respawn:
            if self._wave < 10:
                player.gamedata['respawn_wave'] = max(2, self._wave + 1)
            elif self._wave < 15:
                player.gamedata['respawn_wave'] = max(2, self._wave + 2)
            else:
                player.gamedata['respawn_wave'] = max(2, self._wave + 3)
            ba.timer(0.1, self._update_player_spawn_info)
            ba.timer(0.1, self._checkroundover)

        elif isinstance(msg, spazbot.SpazBotDeathMessage):
            pts, importance = msg.badguy.get_death_points(msg.how)
            if msg.killerplayer is not None:

                # Toss-off-map achievement:
                if self._preset in ['training', 'training_easy']:
                    if msg.badguy.last_attacked_type == ('picked_up',
                                                         'default'):
                        self._throw_off_kills += 1
                        if self._throw_off_kills >= 3:
                            self._award_achievement('Off You Go Then')

                # Land-mine achievement:
                elif self._preset in ['rookie', 'rookie_easy']:
                    if msg.badguy.last_attacked_type == ('explosion',
                                                         'land_mine'):
                        self._land_mine_kills += 1
                        if self._land_mine_kills >= 3:
                            self._award_achievement('Mine Games')

                # TNT achievement:
                elif self._preset in ['pro', 'pro_easy']:
                    if msg.badguy.last_attacked_type == ('explosion', 'tnt'):
                        self._tnt_kills += 1
                        if self._tnt_kills >= 3:
                            ba.timer(
                                0.5,
                                ba.WeakCall(self._award_achievement,
                                            'Boom Goes the Dynamite'))

                elif self._preset in ['uber', 'uber_easy']:

                    # Uber mine achievement:
                    if msg.badguy.last_attacked_type == ('explosion',
                                                         'land_mine'):
                        if not hasattr(self, '_land_mine_kills'):
                            self._land_mine_kills = 0
                        self._land_mine_kills += 1
                        if self._land_mine_kills >= 6:
                            self._award_achievement('Gold Miner')

                    # Uber tnt achievement:
                    if msg.badguy.last_attacked_type == ('explosion', 'tnt'):
                        self._tnt_kills += 1
                        if self._tnt_kills >= 6:
                            ba.timer(
                                0.5,
                                ba.WeakCall(self._award_achievement,
                                            'TNT Terror'))

                target: Optional[Sequence[float]]
                try:
                    assert msg.badguy.node
                    target = msg.badguy.node.position
                except Exception:
                    ba.print_exception()
                    target = None
                try:
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
                except Exception:
                    pass

            # Normally we pull scores from the score-set, but if there's
            # no player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
        else:
            super().handlemessage(msg)

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
        """
        see if the round is over in response to an event (player died, etc)
        """
        if self.has_ended():
            return
        if not any(player.is_alive() for player in self.teams[0].players):
            # Allow continuing after wave 1.
            if self._wave > 1:
                self.continue_or_end_game()
            else:
                self.end_game()
