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
"""Defines Race mini-game."""

# ba_meta require api 6
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)

from __future__ import annotations

import random
from typing import TYPE_CHECKING
from dataclasses import dataclass

import ba
from bastd.actor.bomb import Bomb
from bastd.actor.playerspaz import PlayerSpaz, PlayerSpazDeathMessage

if TYPE_CHECKING:
    from typing import (Any, Type, Tuple, List, Sequence, Optional, Dict,
                        Union)
    from bastd.actor.onscreentimer import OnScreenTimer


@dataclass
class RaceMine:
    """Holds info about a mine on the track."""
    point: Sequence[float]
    mine: Optional[Bomb]


class RaceRegion(ba.Actor):
    """Region used to track progress during a race."""

    def __init__(self, pt: Sequence[float], index: int):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, RaceGame)
        self.pos = pt
        self.index = index
        self.node = ba.newnode(
            'region',
            delegate=self,
            attrs={
                'position': pt[:3],
                'scale': (pt[3] * 2.0, pt[4] * 2.0, pt[5] * 2.0),
                'type': 'box',
                'materials': [activity.race_region_material]
            })


# ba_meta export game
class RaceGame(ba.TeamGameActivity):
    """Game of racing around a track."""

    @classmethod
    def get_name(cls) -> str:
        return 'Race'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Run real fast!'

    @classmethod
    def get_score_info(cls) -> ba.ScoreInfo:
        return ba.ScoreInfo(label='Time',
                            lower_is_better=True,
                            scoretype=ba.ScoreType.MILLISECONDS)

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.MultiTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('race')

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        settings: List[Tuple[str, Dict[str, Any]]] = [
            ('Laps', {
                'min_value': 1,
                'default': 3,
                'increment': 1
            }),
            ('Time Limit', {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0
            }),
            ('Mine Spawning', {
                'choices': [('No Mines', 0), ('8 Seconds', 8000),
                            ('4 Seconds', 4000), ('2 Seconds', 2000)],
                'default': 4000
            }),
            ('Bomb Spawning', {
                'choices': [('None', 0), ('8 Seconds', 8000),
                            ('4 Seconds', 4000), ('2 Seconds', 2000),
                            ('1 Second', 1000)],
            'default': 2000
            }),
            ('Epic Mode', {
                'default': False
            })]  # yapf: disable

        if issubclass(sessiontype, ba.DualTeamSession):
            settings.append(('Entire Team Must Finish', {'default': False}))
        return settings

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        self._race_started = False
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        if self.settings_raw['Epic Mode']:
            self.slow_motion = True
        self._score_sound = ba.getsound('score')
        self._swipsound = ba.getsound('swip')
        self._last_team_time: Optional[float] = None
        self._front_race_region: Optional[int] = None
        self._nub_tex = ba.gettexture('nub')
        self._beep_1_sound = ba.getsound('raceBeep1')
        self._beep_2_sound = ba.getsound('raceBeep2')
        self.race_region_material: Optional[ba.Material] = None
        self._regions: List[RaceRegion] = []
        self._team_finish_pts: Optional[int] = None
        self._time_text: Optional[ba.Actor] = None
        self._timer: Optional[OnScreenTimer] = None
        self._race_mines: Optional[List[RaceMine]] = None
        self._race_mine_timer: Optional[ba.Timer] = None
        self._scoreboard_timer: Optional[ba.Timer] = None
        self._player_order_update_timer: Optional[ba.Timer] = None
        self._start_lights: Optional[List[ba.Node]] = None
        self._bomb_spawn_timer: Optional[ba.Timer] = None

    def get_instance_description(self) -> Union[str, Sequence]:
        if (isinstance(self.session, ba.DualTeamSession)
                and self.settings_raw.get('Entire Team Must Finish', False)):
            t_str = ' Your entire team has to finish.'
        else:
            t_str = ''

        if self.settings_raw['Laps'] > 1:
            return 'Run ${ARG1} laps.' + t_str, self.settings_raw['Laps']
        return 'Run 1 lap.' + t_str

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        if self.settings_raw['Laps'] > 1:
            return 'run ${ARG1} laps', self.settings_raw['Laps']
        return 'run 1 lap'

    def on_transition_in(self) -> None:
        self.default_music = (ba.MusicType.EPIC_RACE
                              if self.settings_raw['Epic Mode'] else
                              ba.MusicType.RACE)
        super().on_transition_in()

        pts = self.map.get_def_points('race_point')
        mat = self.race_region_material = ba.Material()
        mat.add_actions(conditions=('they_have_material',
                                    ba.sharedobj('player_material')),
                        actions=(('modify_part_collision', 'collide', True),
                                 ('modify_part_collision', 'physical',
                                  False), ('call', 'at_connect',
                                           self._handle_race_point_collide)))
        for rpt in pts:
            self._regions.append(RaceRegion(rpt, len(self._regions)))

    def _flash_player(self, player: ba.Player, scale: float) -> None:
        assert isinstance(player.actor, PlayerSpaz)
        assert player.actor.node
        pos = player.actor.node.position
        light = ba.newnode('light',
                           attrs={
                               'position': pos,
                               'color': (1, 1, 0),
                               'height_attenuated': False,
                               'radius': 0.4
                           })
        ba.timer(0.5, light.delete)
        ba.animate(light, 'intensity', {0: 0, 0.1: 1.0 * scale, 0.5: 0})

    def _handle_race_point_collide(self) -> None:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-nested-blocks
        region_node, playernode = ba.get_collision_info(
            'source_node', 'opposing_node')
        try:
            player = playernode.getdelegate().getplayer()
        except Exception:
            player = None
        region = region_node.getdelegate()
        if not player or not region:
            return
        assert isinstance(player, ba.Player)
        assert isinstance(region, RaceRegion)

        last_region = player.gamedata['last_region']
        this_region = region.index

        if last_region != this_region:

            # If a player tries to skip regions, smite them.
            # Allow a one region leeway though (its plausible players can get
            # blown over a region, etc).
            if this_region > last_region + 2:
                if player.is_alive():
                    assert player.actor
                    player.actor.handlemessage(ba.DieMessage())
                    ba.screenmessage(ba.Lstr(
                        translate=('statements', 'Killing ${NAME} for'
                                   ' skipping part of the track!'),
                        subs=[('${NAME}', player.get_name(full=True))]),
                                     color=(1, 0, 0))
            else:
                # If this player is in first, note that this is the
                # front-most race-point.
                if player.gamedata['rank'] == 0:
                    self._front_race_region = this_region

                player.gamedata['last_region'] = this_region
                if last_region >= len(self._regions) - 2 and this_region == 0:
                    team = player.team
                    player.gamedata['lap'] = min(self.settings_raw['Laps'],
                                                 player.gamedata['lap'] + 1)

                    # In teams mode with all-must-finish on, the team lap
                    # value is the min of all team players.
                    # Otherwise its the max.
                    if isinstance(
                            self.session, ba.DualTeamSession
                    ) and self.settings_raw.get('Entire Team Must Finish'):
                        team.gamedata['lap'] = min(
                            [p.gamedata['lap'] for p in team.players])
                    else:
                        team.gamedata['lap'] = max(
                            [p.gamedata['lap'] for p in team.players])

                    # A player is finishing.
                    if player.gamedata['lap'] == self.settings_raw['Laps']:

                        # In teams mode, hand out points based on the order
                        # players come in.
                        if isinstance(self.session, ba.DualTeamSession):
                            assert self._team_finish_pts is not None
                            if self._team_finish_pts > 0:
                                self.stats.player_scored(player,
                                                         self._team_finish_pts,
                                                         screenmessage=False)
                            self._team_finish_pts -= 25

                        # Flash where the player is.
                        self._flash_player(player, 1.0)
                        player.gamedata['finished'] = True
                        assert player.actor
                        player.actor.handlemessage(
                            ba.DieMessage(immediate=True))

                        # Makes sure noone behind them passes them in rank
                        # while finishing.
                        player.gamedata['distance'] = 9999.0

                        # If the whole team has finished the race.
                        if team.gamedata['lap'] == self.settings_raw['Laps']:
                            ba.playsound(self._score_sound)
                            player.team.gamedata['finished'] = True
                            assert self._timer is not None
                            cur_time = ba.time(
                                timeformat=ba.TimeFormat.MILLISECONDS)
                            start_time = self._timer.getstarttime(
                                timeformat=ba.TimeFormat.MILLISECONDS)
                            self._last_team_time = (
                                player.team.gamedata['time']) = (cur_time -
                                                                 start_time)
                            self._check_end_game()

                        # Team has yet to finish.
                        else:
                            ba.playsound(self._swipsound)

                    # They've just finished a lap but not the race.
                    else:
                        ba.playsound(self._swipsound)
                        self._flash_player(player, 0.3)

                        # Print their lap number over their head.
                        try:
                            assert isinstance(player.actor, PlayerSpaz)
                            mathnode = ba.newnode('math',
                                                  owner=player.actor.node,
                                                  attrs={
                                                      'input1': (0, 1.9, 0),
                                                      'operation': 'add'
                                                  })
                            player.actor.node.connectattr(
                                'torso_position', mathnode, 'input2')
                            tstr = ba.Lstr(
                                resource='lapNumberText',
                                subs=[('${CURRENT}',
                                       str(player.gamedata['lap'] + 1)),
                                      ('${TOTAL}',
                                       str(self.settings_raw['Laps']))])
                            txtnode = ba.newnode('text',
                                                 owner=mathnode,
                                                 attrs={
                                                     'text': tstr,
                                                     'in_world': True,
                                                     'color': (1, 1, 0, 1),
                                                     'scale': 0.015,
                                                     'h_align': 'center'
                                                 })
                            mathnode.connectattr('output', txtnode, 'position')
                            ba.animate(txtnode, 'scale', {
                                0.0: 0,
                                0.2: 0.019,
                                2.0: 0.019,
                                2.2: 0
                            })
                            ba.timer(2.3, mathnode.delete)
                        except Exception as exc:
                            print('Exception printing lap:', exc)

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['time'] = None
        team.gamedata['lap'] = 0
        team.gamedata['finished'] = False
        self._update_scoreboard()

    def on_player_join(self, player: ba.Player) -> None:
        player.gamedata['last_region'] = 0
        player.gamedata['lap'] = 0
        player.gamedata['distance'] = 0.0
        player.gamedata['finished'] = False
        player.gamedata['rank'] = None
        super().on_player_join(player)

    def on_player_leave(self, player: ba.Player) -> None:
        super().on_player_leave(player)

        # A player leaving disqualifies the team if 'Entire Team Must Finish'
        # is on (otherwise in teams mode everyone could just leave except the
        # leading player to win).
        if (isinstance(self.session, ba.DualTeamSession)
                and self.settings_raw.get('Entire Team Must Finish')):
            ba.screenmessage(ba.Lstr(
                translate=('statements',
                           '${TEAM} is disqualified because ${PLAYER} left'),
                subs=[('${TEAM}', player.team.name),
                      ('${PLAYER}', player.get_name(full=True))]),
                             color=(1, 1, 0))
            player.team.gamedata['finished'] = True
            player.team.gamedata['time'] = None
            player.team.gamedata['lap'] = 0
            ba.playsound(ba.getsound('boo'))
            for otherplayer in player.team.players:
                otherplayer.gamedata['lap'] = 0
                otherplayer.gamedata['finished'] = True
                try:
                    if otherplayer.actor is not None:
                        otherplayer.actor.handlemessage(ba.DieMessage())
                except Exception:
                    ba.print_exception('Error sending diemessages')

        # Defer so team/player lists will be updated.
        ba.pushcall(self._check_end_game)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            distances = [
                player.gamedata['distance'] for player in team.players
            ]
            if not distances:
                teams_dist = 0
            else:
                if (isinstance(self.session, ba.DualTeamSession)
                        and self.settings_raw.get('Entire Team Must Finish')):
                    teams_dist = min(distances)
                else:
                    teams_dist = max(distances)
            self._scoreboard.set_team_value(
                team,
                teams_dist,
                self.settings_raw['Laps'],
                flash=(teams_dist >= float(self.settings_raw['Laps'])),
                show_value=False)

    def on_begin(self) -> None:
        from bastd.actor.onscreentimer import OnScreenTimer
        super().on_begin()
        self.setup_standard_time_limit(self.settings_raw['Time Limit'])
        self.setup_standard_powerup_drops()
        self._team_finish_pts = 100

        # Throw a timer up on-screen.
        self._time_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'v_attach': 'top',
                           'h_attach': 'center',
                           'h_align': 'center',
                           'color': (1, 1, 0.5, 1),
                           'flatness': 0.5,
                           'shadow': 0.5,
                           'position': (0, -50),
                           'scale': 1.4,
                           'text': ''
                       }))
        self._timer = OnScreenTimer()

        if self.settings_raw['Mine Spawning'] != 0:
            self._race_mines = [
                RaceMine(point=p, mine=None)
                for p in self.map.get_def_points('race_mine')
            ]
            if self._race_mines:
                self._race_mine_timer = ba.Timer(
                    0.001 * self.settings_raw['Mine Spawning'],
                    self._update_race_mine,
                    repeat=True)

        self._scoreboard_timer = ba.Timer(0.25,
                                          self._update_scoreboard,
                                          repeat=True)
        self._player_order_update_timer = ba.Timer(0.25,
                                                   self._update_player_order,
                                                   repeat=True)

        if self.slow_motion:
            t_scale = 0.4
            light_y = 50
        else:
            t_scale = 1.0
            light_y = 150
        lstart = 7.1 * t_scale
        inc = 1.25 * t_scale

        ba.timer(lstart, self._do_light_1)
        ba.timer(lstart + inc, self._do_light_2)
        ba.timer(lstart + 2 * inc, self._do_light_3)
        ba.timer(lstart + 3 * inc, self._start_race)

        self._start_lights = []
        for i in range(4):
            lnub = ba.newnode('image',
                              attrs={
                                  'texture': ba.gettexture('nub'),
                                  'opacity': 1.0,
                                  'absolute_scale': True,
                                  'position': (-75 + i * 50, light_y),
                                  'scale': (50, 50),
                                  'attach': 'center'
                              })
            ba.animate(
                lnub, 'opacity', {
                    4.0 * t_scale: 0,
                    5.0 * t_scale: 1.0,
                    12.0 * t_scale: 1.0,
                    12.5 * t_scale: 0.0
                })
            ba.timer(13.0 * t_scale, lnub.delete)
            self._start_lights.append(lnub)

        self._start_lights[0].color = (0.2, 0, 0)
        self._start_lights[1].color = (0.2, 0, 0)
        self._start_lights[2].color = (0.2, 0.05, 0)
        self._start_lights[3].color = (0.0, 0.3, 0)

    def _do_light_1(self) -> None:
        assert self._start_lights is not None
        self._start_lights[0].color = (1.0, 0, 0)
        ba.playsound(self._beep_1_sound)

    def _do_light_2(self) -> None:
        assert self._start_lights is not None
        self._start_lights[1].color = (1.0, 0, 0)
        ba.playsound(self._beep_1_sound)

    def _do_light_3(self) -> None:
        assert self._start_lights is not None
        self._start_lights[2].color = (1.0, 0.3, 0)
        ba.playsound(self._beep_1_sound)

    def _start_race(self) -> None:
        assert self._start_lights is not None
        self._start_lights[3].color = (0.0, 1.0, 0)
        ba.playsound(self._beep_2_sound)
        for player in self.players:
            if player.actor is not None:
                try:
                    assert isinstance(player.actor, PlayerSpaz)
                    player.actor.connect_controls_to_player()
                except Exception as exc:
                    print('Exception in race player connects:', exc)
        assert self._timer is not None
        self._timer.start()

        if self.settings_raw['Bomb Spawning'] != 0:
            self._bomb_spawn_timer = ba.Timer(
                0.001 * self.settings_raw['Bomb Spawning'],
                self._spawn_bomb,
                repeat=True)

        self._race_started = True

    def _update_player_order(self) -> None:
        # FIXME: tidy this up

        # Calc all player distances.
        for player in self.players:
            pos: Optional[ba.Vec3]
            try:
                assert isinstance(player.actor, PlayerSpaz)
                assert player.actor.node
                pos = ba.Vec3(player.actor.node.position)
            except Exception:
                pos = None
            if pos is not None:
                r_index = player.gamedata['last_region']
                rg1 = self._regions[r_index]
                r1pt = ba.Vec3(rg1.pos[:3])
                rg2 = self._regions[0] if r_index == len(
                    self._regions) - 1 else self._regions[r_index + 1]
                r2pt = ba.Vec3(rg2.pos[:3])
                r2dist = (pos - r2pt).length()
                amt = 1.0 - (r2dist / (r2pt - r1pt).length())
                amt = player.gamedata['lap'] + (r_index + amt) * (
                    1.0 / len(self._regions))
                player.gamedata['distance'] = amt

        # Sort players by distance and update their ranks.
        p_list = [[player.gamedata['distance'], player]
                  for player in self.players]

        p_list.sort(reverse=True, key=lambda x: x[0])
        for i, plr in enumerate(p_list):
            try:
                plr[1].gamedata['rank'] = i
                if plr[1].actor is not None:
                    # noinspection PyUnresolvedReferences
                    node = plr[1].actor.distance_txt
                    if node:
                        node.text = str(i + 1) if plr[1].is_alive() else ''
            except Exception:
                ba.print_exception('error updating player orders')

    def _spawn_bomb(self) -> None:
        if self._front_race_region is None:
            return
        region = (self._front_race_region + 3) % len(self._regions)
        pos = self._regions[region].pos

        # Don't use the full region so we're less likely to spawn off a cliff.
        region_scale = 0.8
        x_range = ((-0.5, 0.5) if pos[3] == 0 else
                   (-region_scale * pos[3], region_scale * pos[3]))
        z_range = ((-0.5, 0.5) if pos[5] == 0 else
                   (-region_scale * pos[5], region_scale * pos[5]))
        pos = (pos[0] + random.uniform(*x_range), pos[1] + 1.0,
               pos[2] + random.uniform(*z_range))
        ba.timer(random.uniform(0.0, 2.0),
                 ba.WeakCall(self._spawn_bomb_at_pos, pos))

    def _spawn_bomb_at_pos(self, pos: Sequence[float]) -> None:
        if self.has_ended():
            return
        Bomb(position=pos, bomb_type='normal').autoretain()

    def _make_mine(self, i: int) -> None:
        assert self._race_mines is not None
        rmine = self._race_mines[i]
        rmine.mine = Bomb(position=rmine.point[:3], bomb_type='land_mine')
        rmine.mine.arm()

    def _flash_mine(self, i: int) -> None:
        assert self._race_mines is not None
        rmine = self._race_mines[i]
        light = ba.newnode('light',
                           attrs={
                               'position': rmine.point[:3],
                               'color': (1, 0.2, 0.2),
                               'radius': 0.1,
                               'height_attenuated': False
                           })
        ba.animate(light, 'intensity', {0.0: 0, 0.1: 1.0, 0.2: 0}, loop=True)
        ba.timer(1.0, light.delete)

    def _update_race_mine(self) -> None:
        assert self._race_mines is not None
        m_index = -1
        rmine = None
        for _i in range(3):
            m_index = random.randrange(len(self._race_mines))
            rmine = self._race_mines[m_index]
            if not rmine.mine:
                break
        assert rmine is not None
        if not rmine.mine:
            self._flash_mine(m_index)
            ba.timer(0.95, ba.Call(self._make_mine, m_index))

    def spawn_player(self, player: ba.Player) -> ba.Actor:
        if player.team.gamedata['finished']:
            # FIXME: This is not type-safe
            #  (this call is expected to return an Actor).
            # noinspection PyTypeChecker
            return None  # type: ignore
        pos = self._regions[player.gamedata['last_region']].pos

        # Don't use the full region so we're less likely to spawn off a cliff.
        region_scale = 0.8
        x_range = ((-0.5, 0.5) if pos[3] == 0 else
                   (-region_scale * pos[3], region_scale * pos[3]))
        z_range = ((-0.5, 0.5) if pos[5] == 0 else
                   (-region_scale * pos[5], region_scale * pos[5]))
        pos = (pos[0] + random.uniform(*x_range), pos[1],
               pos[2] + random.uniform(*z_range))
        spaz = self.spawn_player_spaz(
            player, position=pos, angle=90 if not self._race_started else None)
        assert spaz.node

        # Prevent controlling of characters before the start of the race.
        if not self._race_started:
            spaz.disconnect_controls_from_player()

        mathnode = ba.newnode('math',
                              owner=spaz.node,
                              attrs={
                                  'input1': (0, 1.4, 0),
                                  'operation': 'add'
                              })
        spaz.node.connectattr('torso_position', mathnode, 'input2')

        distance_txt = ba.newnode('text',
                                  owner=spaz.node,
                                  attrs={
                                      'text': '',
                                      'in_world': True,
                                      'color': (1, 1, 0.4),
                                      'scale': 0.02,
                                      'h_align': 'center'
                                  })
        # FIXME store this in a type-safe way
        # noinspection PyTypeHints
        spaz.distance_txt = distance_txt  # type: ignore
        mathnode.connectattr('output', distance_txt, 'position')
        return spaz

    def _check_end_game(self) -> None:

        # If there's no teams left racing, finish.
        teams_still_in = len(
            [t for t in self.teams if not t.gamedata['finished']])
        if teams_still_in == 0:
            self.end_game()
            return

        # Count the number of teams that have completed the race.
        teams_completed = len([
            t for t in self.teams
            if t.gamedata['finished'] and t.gamedata['time'] is not None
        ])

        if teams_completed > 0:
            session = self.session

            # In teams mode its over as soon as any team finishes the race

            # FIXME: The get_ffa_point_awards code looks dangerous.
            if isinstance(session, ba.DualTeamSession):
                self.end_game()
            else:
                # In ffa we keep the race going while there's still any points
                # to be handed out. Find out how many points we have to award
                # and how many teams have finished, and once that matches
                # we're done.
                assert isinstance(session, ba.FreeForAllSession)
                points_to_award = len(session.get_ffa_point_awards())
                if teams_completed >= points_to_award - teams_completed:
                    self.end_game()
                    return

    def end_game(self) -> None:

        # Stop updating our time text, and set it to show the exact last
        # finish time if we have one. (so users don't get upset if their
        # final time differs from what they see onscreen by a tiny bit)
        assert self._timer is not None
        if self._timer.has_started():
            cur_time = self._timer.getstarttime(
                timeformat=ba.TimeFormat.MILLISECONDS)
            self._timer.stop(
                endtime=None if self._last_team_time is None else (
                    cur_time + self._last_team_time))

        results = ba.TeamGameResults()

        for team in self.teams:
            results.set_team_score(team, team.gamedata['time'])
            # If game have ended before we
            # get any result, use 'fail' screen

        # We don't announce a winner in ffa mode since its probably been a
        # while since the first place guy crossed the finish line so it seems
        # odd to be announcing that now.
        self.end(results=results,
                 announce_winning_team=isinstance(self.session,
                                                  ba.DualTeamSession))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, PlayerSpazDeathMessage):
            # Augment default behavior.
            super().handlemessage(msg)
            player = msg.spaz.getplayer()
            if not player:
                ba.print_error('got no player in PlayerSpazDeathMessage')
                return
            if not player.gamedata['finished']:
                self.respawn_player(player, respawn_time=1)
        else:
            super().handlemessage(msg)
