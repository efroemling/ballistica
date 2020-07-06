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
"""Defines a capture-the-flag game."""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.flag import (FlagFactory, Flag, FlagPickedUpMessage,
                              FlagDroppedMessage, FlagDiedMessage)

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Sequence, Union, Optional


class CTFFlag(Flag):
    """Special flag type for CTF games."""

    activity: CaptureTheFlagGame

    def __init__(self, team: Team):
        assert team.flagmaterial is not None
        super().__init__(materials=[team.flagmaterial],
                         position=team.base_pos,
                         color=team.color)
        self._team = team
        self.held_count = 0
        self.counter = ba.newnode('text',
                                  owner=self.node,
                                  attrs={
                                      'in_world': True,
                                      'scale': 0.02,
                                      'h_align': 'center'
                                  })
        self.reset_return_times()
        self.last_player_to_hold: Optional[Player] = None
        self.time_out_respawn_time: Optional[int] = None
        self.touch_return_time: Optional[float] = None

    def reset_return_times(self) -> None:
        """Clear flag related times in the activity."""
        self.time_out_respawn_time = int(self.activity.flag_idle_return_time)
        self.touch_return_time = float(self.activity.flag_touch_return_time)

    @property
    def team(self) -> Team:
        """The flag's team."""
        return self._team


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.touching_own_flag = 0


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self, base_pos: Sequence[float],
                 base_region_material: ba.Material, base_region: ba.Node,
                 spaz_material_no_flag_physical: ba.Material,
                 spaz_material_no_flag_collide: ba.Material,
                 flagmaterial: ba.Material):
        self.base_pos = base_pos
        self.base_region_material = base_region_material
        self.base_region = base_region
        self.spaz_material_no_flag_physical = spaz_material_no_flag_physical
        self.spaz_material_no_flag_collide = spaz_material_no_flag_collide
        self.flagmaterial = flagmaterial
        self.score = 0
        self.flag_return_touches = 0
        self.home_flag_at_base = True
        self.touch_return_timer: Optional[ba.Timer] = None
        self.enemy_flag_at_base = False
        self.flag: Optional[CTFFlag] = None
        self.last_flag_leave_time: Optional[float] = None
        self.touch_return_timer_ticking: Optional[ba.NodeActor] = None


# ba_meta export game
class CaptureTheFlagGame(ba.TeamGameActivity[Player, Team]):
    """Game of stealing other team's flag and returning it to your base."""

    name = 'Capture the Flag'
    description = 'Return the enemy flag to score.'
    available_settings = [
        ba.IntSetting('Score to Win', min_value=1, default=3),
        ba.IntSetting(
            'Flag Touch Return Time',
            min_value=0,
            default=0,
            increment=1,
        ),
        ba.IntSetting(
            'Flag Idle Return Time',
            min_value=5,
            default=30,
            increment=5,
        ),
        ba.IntChoiceSetting(
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
        ba.FloatChoiceSetting(
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
        ba.BoolSetting('Epic Mode', default=False),
    ]

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('team_flag')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._alarmsound = ba.getsound('alarm')
        self._ticking_sound = ba.getsound('ticking')
        self._score_sound = ba.getsound('score')
        self._swipsound = ba.getsound('swip')
        self._last_score_time = 0
        self._all_bases_material = ba.Material()
        self._last_home_flag_notice_print_time = 0.0
        self._score_to_win = int(settings['Score to Win'])
        self._epic_mode = bool(settings['Epic Mode'])
        self._time_limit = float(settings['Time Limit'])

        self.flag_touch_return_time = float(settings['Flag Touch Return Time'])
        self.flag_idle_return_time = float(settings['Flag Idle Return Time'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (ba.MusicType.EPIC if self._epic_mode else
                              ba.MusicType.FLAG_CATCHER)

    def get_instance_description(self) -> Union[str, Sequence]:
        if self._score_to_win == 1:
            return 'Steal the enemy flag.'
        return 'Steal the enemy flag ${ARG1} times.', self._score_to_win

    def get_instance_description_short(self) -> Union[str, Sequence]:
        if self._score_to_win == 1:
            return 'return 1 flag'
        return 'return ${ARG1} flags', self._score_to_win

    def create_team(self, sessionteam: ba.SessionTeam) -> Team:

        # Create our team instance and its initial values.

        base_pos = self.map.get_flag_position(sessionteam.id)
        Flag.project_stand(base_pos)

        ba.newnode('light',
                   attrs={
                       'position': base_pos,
                       'intensity': 0.6,
                       'height_attenuated': False,
                       'volume_intensity_scale': 0.1,
                       'radius': 0.1,
                       'color': sessionteam.color
                   })

        base_region_mat = ba.Material()
        pos = base_pos
        base_region = ba.newnode(
            'region',
            attrs={
                'position': (pos[0], pos[1] + 0.75, pos[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [base_region_mat, self._all_bases_material]
            })

        spaz_mat_no_flag_physical = ba.Material()
        spaz_mat_no_flag_collide = ba.Material()
        flagmat = ba.Material()

        team = Team(base_pos=base_pos,
                    base_region_material=base_region_mat,
                    base_region=base_region,
                    spaz_material_no_flag_physical=spaz_mat_no_flag_physical,
                    spaz_material_no_flag_collide=spaz_mat_no_flag_collide,
                    flagmaterial=flagmat)

        # Some parts of our spazzes don't collide physically with our
        # flags but generate callbacks.
        spaz_mat_no_flag_physical.add_actions(
            conditions=('they_have_material', flagmat),
            actions=(
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 lambda: self._handle_touching_own_flag(team, True)),
                ('call', 'at_disconnect',
                 lambda: self._handle_touching_own_flag(team, False)),
            ))

        # Other parts of our spazzes don't collide with our flags at all.
        spaz_mat_no_flag_collide.add_actions(
            conditions=('they_have_material', flagmat),
            actions=('modify_part_collision', 'collide', False),
        )

        # We wanna know when *any* flag enters/leaves our base.
        base_region_mat.add_actions(
            conditions=('they_have_material', FlagFactory.get().flagmaterial),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 lambda: self._handle_flag_entered_base(team)),
                ('call', 'at_disconnect',
                 lambda: self._handle_flag_left_base(team)),
            ))

        return team

    def on_team_join(self, team: Team) -> None:
        # Can't do this in create_team because the team's color/etc. have
        # not been wired up yet at that point.
        self._spawn_flag_for_team(team)
        self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        ba.timer(1.0, call=self._tick, repeat=True)

    def _spawn_flag_for_team(self, team: Team) -> None:
        team.flag = CTFFlag(team)
        team.flag_return_touches = 0
        self._flash_base(team, length=1.0)
        assert team.flag.node
        ba.playsound(self._swipsound, position=team.flag.node.position)

    def _handle_flag_entered_base(self, team: Team) -> None:
        try:
            flag = ba.getcollision().opposingnode.getdelegate(CTFFlag, True)
        except ba.NotFoundError:
            # Don't think this should logically ever happen.
            print('Error getting CTFFlag in entering-base callback.')
            return

        if flag.team is team:
            team.home_flag_at_base = True

            # If the enemy flag is already here, score!
            if team.enemy_flag_at_base:
                self._score(team)
        else:
            team.enemy_flag_at_base = True
            if team.home_flag_at_base:
                # Award points to whoever was carrying the enemy flag.
                player = flag.last_player_to_hold
                if player and player.team is team:
                    assert self.stats
                    self.stats.player_scored(player, 50, big_message=True)

                # Update score and reset flags.
                self._score(team)

            # If the home-team flag isn't here, print a message to that effect.
            else:
                # Don't want slo-mo affecting this
                curtime = ba.time(ba.TimeType.BASE)
                if curtime - self._last_home_flag_notice_print_time > 5.0:
                    self._last_home_flag_notice_print_time = curtime
                    bpos = team.base_pos
                    tval = ba.Lstr(resource='ownFlagAtYourBaseWarning')
                    tnode = ba.newnode(
                        'text',
                        attrs={
                            'text': tval,
                            'in_world': True,
                            'scale': 0.013,
                            'color': (1, 1, 0, 1),
                            'h_align': 'center',
                            'position': (bpos[0], bpos[1] + 3.2, bpos[2])
                        })
                    ba.timer(5.1, tnode.delete)
                    ba.animate(tnode, 'scale', {
                        0.0: 0,
                        0.2: 0.013,
                        4.8: 0.013,
                        5.0: 0
                    })

    def _tick(self) -> None:
        # If either flag is away from base and not being held, tick down its
        # respawn timer.
        for team in self.teams:
            flag = team.flag
            assert flag is not None

            if not team.home_flag_at_base and flag.held_count == 0:
                time_out_counting_down = True
                if flag.time_out_respawn_time is None:
                    flag.reset_return_times()
                assert flag.time_out_respawn_time is not None
                flag.time_out_respawn_time -= 1
                if flag.time_out_respawn_time <= 0:
                    flag.handlemessage(ba.DieMessage())
            else:
                time_out_counting_down = False

            if flag.node and flag.counter:
                pos = flag.node.position
                flag.counter.position = (pos[0], pos[1] + 1.3, pos[2])

                # If there's no self-touches on this flag, set its text
                # to show its auto-return counter.  (if there's self-touches
                # its showing that time).
                if team.flag_return_touches == 0:
                    flag.counter.text = (str(flag.time_out_respawn_time) if (
                        time_out_counting_down
                        and flag.time_out_respawn_time is not None
                        and flag.time_out_respawn_time <= 10) else '')
                    flag.counter.color = (1, 1, 1, 0.5)
                    flag.counter.scale = 0.014

    def _score(self, team: Team) -> None:
        team.score += 1
        ba.playsound(self._score_sound)
        self._flash_base(team)
        self._update_scoreboard()

        # Have teammates celebrate.
        for player in team.players:
            if player.actor:
                player.actor.handlemessage(ba.CelebrateMessage(2.0))

        # Reset all flags/state.
        for reset_team in self.teams:
            if not reset_team.home_flag_at_base:
                assert reset_team.flag is not None
                reset_team.flag.handlemessage(ba.DieMessage())
            reset_team.enemy_flag_at_base = False
        if team.score >= self._score_to_win:
            self.end_game()

    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results, announce_delay=0.8)

    def _handle_flag_left_base(self, team: Team) -> None:
        cur_time = ba.time()
        try:
            flag = ba.getcollision().opposingnode.getdelegate(CTFFlag, True)
        except ba.NotFoundError:
            # This can happen if the flag stops touching us due to being
            # deleted; that's ok.
            return

        if flag.team is team:

            # Check times here to prevent too much flashing.
            if (team.last_flag_leave_time is None
                    or cur_time - team.last_flag_leave_time > 3.0):
                ba.playsound(self._alarmsound, position=team.base_pos)
                self._flash_base(team)
            team.last_flag_leave_time = cur_time
            team.home_flag_at_base = False
        else:
            team.enemy_flag_at_base = False

    def _touch_return_update(self, team: Team) -> None:
        # Count down only while its away from base and not being held.
        assert team.flag is not None
        if team.home_flag_at_base or team.flag.held_count > 0:
            team.touch_return_timer_ticking = None
            return  # No need to return when its at home.
        if team.touch_return_timer_ticking is None:
            team.touch_return_timer_ticking = ba.NodeActor(
                ba.newnode('sound',
                           attrs={
                               'sound': self._ticking_sound,
                               'positional': False,
                               'loop': True
                           }))
        flag = team.flag
        if flag.touch_return_time is not None:
            flag.touch_return_time -= 0.1
            if flag.counter:
                flag.counter.text = f'{flag.touch_return_time:.1f}'
                flag.counter.color = (1, 1, 0, 1)
                flag.counter.scale = 0.02

            if flag.touch_return_time <= 0.0:
                self._award_players_touching_own_flag(team)
                flag.handlemessage(ba.DieMessage())

    def _award_players_touching_own_flag(self, team: Team) -> None:
        for player in team.players:
            if player.touching_own_flag > 0:
                return_score = 10 + 5 * int(self.flag_touch_return_time)
                self.stats.player_scored(player,
                                         return_score,
                                         screenmessage=False)

    def _handle_touching_own_flag(self, team: Team, connecting: bool) -> None:
        """Called when a player touches or stops touching their own team flag.

        We keep track of when each player is touching their own flag so we
        can award points when returned.
        """
        player: Optional[Player]
        try:
            player = ba.getcollision().sourcenode.getdelegate(
                PlayerSpaz, True).getplayer(Player, True)
        except ba.NotFoundError:
            # This can happen if the player leaves but his corpse touches/etc.
            player = None

        if player:
            player.touching_own_flag += (1 if connecting else -1)

        # If return-time is zero, just kill it immediately.. otherwise keep
        # track of touches and count down.
        if float(self.flag_touch_return_time) <= 0.0:
            assert team.flag is not None
            if (connecting and not team.home_flag_at_base
                    and team.flag.held_count == 0):
                self._award_players_touching_own_flag(team)
                ba.getcollision().opposingnode.handlemessage(ba.DieMessage())

        # Takes a non-zero amount of time to return.
        else:
            if connecting:
                team.flag_return_touches += 1
                if team.flag_return_touches == 1:
                    team.touch_return_timer = ba.Timer(
                        0.1,
                        call=ba.Call(self._touch_return_update, team),
                        repeat=True)
                    team.touch_return_timer_ticking = None
            else:
                team.flag_return_touches -= 1
                if team.flag_return_touches == 0:
                    team.touch_return_timer = None
                    team.touch_return_timer_ticking = None
            if team.flag_return_touches < 0:
                ba.print_error('CTF flag_return_touches < 0')

    def _flash_base(self, team: Team, length: float = 2.0) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': team.base_pos,
                               'height_attenuated': False,
                               'radius': 0.3,
                               'color': team.color
                           })
        ba.animate(light, 'intensity', {0.0: 0, 0.25: 2.0, 0.5: 0}, loop=True)
        ba.timer(length, light.delete)

    def spawn_player_spaz(self,
                          player: Player,
                          position: Sequence[float] = None,
                          angle: float = None) -> PlayerSpaz:
        """Intercept new spazzes and add our team material for them."""
        spaz = super().spawn_player_spaz(player, position, angle)
        player = spaz.getplayer(Player, True)
        team: Team = player.team
        player.touching_own_flag = 0
        no_physical_mats: List[ba.Material] = [
            team.spaz_material_no_flag_physical
        ]
        no_collide_mats: List[ba.Material] = [
            team.spaz_material_no_flag_collide
        ]

        # Our normal parts should still collide; just not physically
        # (so we can calc restores).
        assert spaz.node
        spaz.node.materials = list(spaz.node.materials) + no_physical_mats
        spaz.node.roller_materials = list(
            spaz.node.roller_materials) + no_physical_mats

        # Pickups and punches shouldn't hit at all though.
        spaz.node.punch_materials = list(
            spaz.node.punch_materials) + no_collide_mats
        spaz.node.pickup_materials = list(
            spaz.node.pickup_materials) + no_collide_mats
        spaz.node.extras_material = list(
            spaz.node.extras_material) + no_collide_mats
        return spaz

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)

    def handlemessage(self, msg: Any) -> Any:

        if isinstance(msg, ba.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.respawn_player(msg.getplayer(Player))

        elif isinstance(msg, FlagDiedMessage):
            assert isinstance(msg.flag, CTFFlag)
            ba.timer(0.1, ba.Call(self._spawn_flag_for_team, msg.flag.team))

        elif isinstance(msg, FlagPickedUpMessage):

            # Store the last player to hold the flag for scoring purposes.
            assert isinstance(msg.flag, CTFFlag)
            try:
                msg.flag.last_player_to_hold = msg.node.getdelegate(
                    PlayerSpaz, True).getplayer(Player, True)
            except ba.NotFoundError:
                pass

            msg.flag.held_count += 1
            msg.flag.reset_return_times()

        elif isinstance(msg, FlagDroppedMessage):
            # Store the last player to hold the flag for scoring purposes.
            assert isinstance(msg.flag, CTFFlag)
            msg.flag.held_count -= 1

        else:
            super().handlemessage(msg)
