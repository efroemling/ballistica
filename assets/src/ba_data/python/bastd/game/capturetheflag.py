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
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor import flag as stdflag
from bastd.actor import playerspaz

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Tuple, Sequence, Union, Optional


class CTFFlag(stdflag.Flag):
    """Special flag type for ctf games."""

    def __init__(self, team: ba.Team):
        super().__init__(materials=[team.gamedata['flagmaterial']],
                         position=team.gamedata['base_pos'],
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
        self.last_player_to_hold: Optional[ba.Player] = None
        self.time_out_respawn_time: Optional[int] = None
        self.touch_return_time: Optional[float] = None

    def reset_return_times(self) -> None:
        """Clear flag related times in the activity."""
        self.time_out_respawn_time = int(
            self.activity.settings['Flag Idle Return Time'])
        self.touch_return_time = float(
            self.activity.settings['Flag Touch Return Time'])

    def get_team(self) -> ba.Team:
        """return the flag's team."""
        return self._team


# ba_meta export game
class CaptureTheFlagGame(ba.TeamGameActivity):
    """Game of stealing other team's flag and returning it to your base."""

    @classmethod
    def get_name(cls) -> str:
        return 'Capture the Flag'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Return the enemy flag to score.'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return issubclass(sessiontype, ba.TeamsSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('team_flag')

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        return [
            ('Score to Win', {'min_value': 1, 'default': 3}),
            ('Flag Touch Return Time', {
                'min_value': 0, 'default': 0, 'increment': 1}),
            ('Flag Idle Return Time', {
                'min_value': 5, 'default': 30, 'increment': 5}),
            ('Time Limit', {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0}),
            ('Respawn Times', {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                            ('Long', 2.0), ('Longer', 4.0)],
                'default': 1.0}),
            ('Epic Mode', {'default': False})]  # yapf: disable

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        if self.settings['Epic Mode']:
            self.slow_motion = True
        self._alarmsound = ba.getsound('alarm')
        self._ticking_sound = ba.getsound('ticking')
        self._last_score_time = 0
        self._score_sound = ba.getsound('score')
        self._swipsound = ba.getsound('swip')
        self._all_bases_material = ba.Material()
        self._last_home_flag_notice_print_time = 0.0

    def get_instance_description(self) -> Union[str, Sequence]:
        if self.settings['Score to Win'] == 1:
            return 'Steal the enemy flag.'
        return ('Steal the enemy flag ${ARG1} times.',
                self.settings['Score to Win'])

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        if self.settings['Score to Win'] == 1:
            return 'return 1 flag'
        return 'return ${ARG1} flags', self.settings['Score to Win']

    def on_transition_in(self) -> None:
        self.default_music = (ba.MusicType.EPIC if self.settings['Epic Mode']
                              else ba.MusicType.FLAG_CATCHER)
        super().on_transition_in()

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['score'] = 0
        team.gamedata['flag_return_touches'] = 0
        team.gamedata['home_flag_at_base'] = True
        team.gamedata['touch_return_timer'] = None
        team.gamedata['enemy_flag_at_base'] = False
        team.gamedata['base_pos'] = (self.map.get_flag_position(team.get_id()))

        self.project_flag_stand(team.gamedata['base_pos'])

        ba.newnode('light',
                   attrs={
                       'position': team.gamedata['base_pos'],
                       'intensity': 0.6,
                       'height_attenuated': False,
                       'volume_intensity_scale': 0.1,
                       'radius': 0.1,
                       'color': team.color
                   })

        base_region_mat = team.gamedata['base_region_material'] = ba.Material()
        pos = team.gamedata['base_pos']
        team.gamedata['base_region'] = ba.newnode(
            "region",
            attrs={
                'position': (pos[0], pos[1] + 0.75, pos[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [base_region_mat, self._all_bases_material]
            })

        # create some materials for this team
        spaz_mat_no_flag_physical = team.gamedata[
            'spaz_material_no_flag_physical'] = ba.Material()
        spaz_mat_no_flag_collide = team.gamedata[
            'spaz_material_no_flag_collide'] = ba.Material()
        flagmat = team.gamedata['flagmaterial'] = ba.Material()

        # Some parts of our spazzes don't collide physically with our
        # flags but generate callbacks.
        spaz_mat_no_flag_physical.add_actions(
            conditions=('they_have_material', flagmat),
            actions=(('modify_part_collision', 'physical',
                      False), ('call', 'at_connect',
                               lambda: self._handle_hit_own_flag(team, 1)),
                     ('call', 'at_disconnect',
                      lambda: self._handle_hit_own_flag(team, 0))))

        # Other parts of our spazzes don't collide with our flags at all.
        spaz_mat_no_flag_collide.add_actions(conditions=('they_have_material',
                                                         flagmat),
                                             actions=('modify_part_collision',
                                                      'collide', False))

        # We wanna know when *any* flag enters/leaves our base.
        base_region_mat.add_actions(
            conditions=('they_have_material',
                        stdflag.get_factory().flagmaterial),
            actions=(('modify_part_collision', 'collide',
                      True), ('modify_part_collision', 'physical', False),
                     ('call', 'at_connect',
                      lambda: self._handle_flag_entered_base(team)),
                     ('call', 'at_disconnect',
                      lambda: self._handle_flag_left_base(team))))

        self._spawn_flag_for_team(team)
        self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()
        ba.timer(1.0, call=self._tick, repeat=True)

    def _spawn_flag_for_team(self, team: ba.Team) -> None:
        flag = team.gamedata['flag'] = CTFFlag(team)
        team.gamedata['flag_return_touches'] = 0
        self._flash_base(team, length=1.0)
        assert flag.node
        ba.playsound(self._swipsound, position=flag.node.position)

    def _handle_flag_entered_base(self, team: ba.Team) -> None:
        flag = ba.get_collision_info("opposing_node").getdelegate()
        assert isinstance(flag, CTFFlag)

        if flag.get_team() is team:
            team.gamedata['home_flag_at_base'] = True

            # If the enemy flag is already here, score!
            if team.gamedata['enemy_flag_at_base']:
                self._score(team)
        else:
            team.gamedata['enemy_flag_at_base'] = True
            if team.gamedata['home_flag_at_base']:
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
                    bpos = team.gamedata['base_pos']
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
            flag = team.gamedata['flag']

            if (not team.gamedata['home_flag_at_base']
                    and flag.held_count == 0):
                time_out_counting_down = True
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
                if team.gamedata['flag_return_touches'] == 0:
                    flag.counter.text = (str(flag.time_out_respawn_time) if
                                         (time_out_counting_down
                                          and flag.time_out_respawn_time <= 10)
                                         else '')
                    flag.counter.color = (1, 1, 1, 0.5)
                    flag.counter.scale = 0.014

    def _score(self, team: ba.Team) -> None:
        team.gamedata['score'] += 1
        ba.playsound(self._score_sound)
        self._flash_base(team)
        self._update_scoreboard()

        # Have teammates celebrate
        for player in team.players:
            if player.actor is not None and player.actor.node:
                # Note: celebrate message is milliseconds
                # for historical reasons.
                player.actor.node.handlemessage('celebrate', 2000)

        # Reset all flags/state.
        for reset_team in self.teams:
            if not reset_team.gamedata['home_flag_at_base']:
                reset_team.gamedata['flag'].handlemessage(ba.DieMessage())
            reset_team.gamedata['enemy_flag_at_base'] = False
        if team.gamedata['score'] >= self.settings['Score to Win']:
            self.end_game()

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(team, team.gamedata['score'])
        self.end(results=results, announce_delay=0.8)

    def _handle_flag_left_base(self, team: ba.Team) -> None:
        cur_time = ba.time()
        op_node = ba.get_collision_info("opposing_node")
        try:
            flag = op_node.getdelegate()
        except Exception:
            return  # Can happen when we kill a flag.

        if flag.get_team() is team:

            # Check times here to prevent too much flashing.
            if ('last_flag_leave_time' not in team.gamedata
                    or cur_time - team.gamedata['last_flag_leave_time'] > 3.0):
                ba.playsound(self._alarmsound,
                             position=team.gamedata['base_pos'])
                self._flash_base(team)
            team.gamedata['last_flag_leave_time'] = cur_time
            team.gamedata['home_flag_at_base'] = False
        else:
            team.gamedata['enemy_flag_at_base'] = False

    def _touch_return_update(self, team: ba.Team) -> None:

        # Count down only while its away from base and not being held.
        if (team.gamedata['home_flag_at_base']
                or team.gamedata['flag'].held_count > 0):
            team.gamedata['touch_return_timer_ticking'] = None
            return  # No need to return when its at home.
        if team.gamedata['touch_return_timer_ticking'] is None:
            team.gamedata['touch_return_timer_ticking'] = ba.Actor(
                ba.newnode('sound',
                           attrs={
                               'sound': self._ticking_sound,
                               'positional': False,
                               'loop': True
                           }))
        flag = team.gamedata['flag']
        flag.touch_return_time -= 0.1
        if flag.counter:
            flag.counter.text = "%.1f" % flag.touch_return_time
            flag.counter.color = (1, 1, 0, 1)
            flag.counter.scale = 0.02

        if flag.touch_return_time <= 0.0:
            self._award_players_touching_own_flag(team)
            flag.handlemessage(ba.DieMessage())

    def _award_players_touching_own_flag(self, team: ba.Team) -> None:
        for player in team.players:
            if player.gamedata['touching_own_flag'] > 0:
                return_score = 10 + 5 * int(
                    self.settings['Flag Touch Return Time'])
                self.stats.player_scored(player,
                                         return_score,
                                         screenmessage=False)

    def _handle_hit_own_flag(self, team: ba.Team, val: int) -> None:
        """
        keep track of when each player is touching their
        own flag so we can award points when returned
        """
        # I wear the cone of shame.
        # pylint: disable=too-many-branches
        srcnode = ba.get_collision_info('source_node')
        try:
            player = srcnode.getdelegate().getplayer()
        except Exception:
            player = None
        if player:
            if val:
                player.gamedata['touching_own_flag'] += 1
            else:
                player.gamedata['touching_own_flag'] -= 1

        # If return-time is zero, just kill it immediately.. otherwise keep
        # track of touches and count down.
        if float(self.settings['Flag Touch Return Time']) <= 0.0:
            if (not team.gamedata['home_flag_at_base']
                    and team.gamedata['flag'].held_count == 0):

                # Use a node message to kill the flag instead of just killing
                # our team's. (avoids redundantly killing new flags if
                # multiple body parts generate callbacks in one step).
                node = ba.get_collision_info("opposing_node")
                if node:
                    self._award_players_touching_own_flag(team)
                    node.handlemessage(ba.DieMessage())

        # Takes a non-zero amount of time to return.
        else:
            if val:
                team.gamedata['flag_return_touches'] += 1
                if team.gamedata['flag_return_touches'] == 1:
                    team.gamedata['touch_return_timer'] = ba.Timer(
                        0.1,
                        call=ba.Call(self._touch_return_update, team),
                        repeat=True)
                    team.gamedata['touch_return_timer_ticking'] = None
            else:
                team.gamedata['flag_return_touches'] -= 1
                if team.gamedata['flag_return_touches'] == 0:
                    team.gamedata['touch_return_timer'] = None
                    team.gamedata['touch_return_timer_ticking'] = None
            if team.gamedata['flag_return_touches'] < 0:
                ba.print_error(
                    "CTF: flag_return_touches < 0; this shouldn't happen.")

    def _flash_base(self, team: ba.Team, length: float = 2.0) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': team.gamedata['base_pos'],
                               'height_attenuated': False,
                               'radius': 0.3,
                               'color': team.color
                           })
        ba.animate(light, 'intensity', {0.0: 0, 0.25: 2.0, 0.5: 0}, loop=True)
        ba.timer(length, light.delete)

    def spawn_player_spaz(self, *args: Any, **keywds: Any) -> Any:
        """Intercept new spazzes and add our team material for them."""
        # (chill pylint; we're passing our exact args to parent call)
        # pylint: disable=arguments-differ
        spaz = ba.TeamGameActivity.spawn_player_spaz(self, *args, **keywds)
        player = spaz.player
        player.gamedata['touching_own_flag'] = 0

        # Ignore false alarm for gamedata member.
        no_physical_mats = [
            player.team.gamedata['spaz_material_no_flag_physical']
        ]
        no_collide_mats = [
            player.team.gamedata['spaz_material_no_flag_collide']
        ]
        # pylint: enable=arguments-differ

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
            self._scoreboard.set_team_value(team, team.gamedata['score'],
                                            self.settings['Score to Win'])

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.respawn_player(msg.spaz.player)
        elif isinstance(msg, stdflag.FlagDeathMessage):
            assert isinstance(msg.flag, CTFFlag)
            ba.timer(0.1,
                     ba.Call(self._spawn_flag_for_team, msg.flag.get_team()))
        elif isinstance(msg, stdflag.FlagPickedUpMessage):
            # Store the last player to hold the flag for scoring purposes.
            assert isinstance(msg.flag, CTFFlag)
            msg.flag.last_player_to_hold = msg.node.getdelegate().getplayer()
            msg.flag.held_count += 1
            msg.flag.reset_return_times()
        elif isinstance(msg, stdflag.FlagDroppedMessage):
            # Store the last player to hold the flag for scoring purposes.
            assert isinstance(msg.flag, CTFFlag)
            msg.flag.held_count -= 1
        else:
            super().handlemessage(msg)
