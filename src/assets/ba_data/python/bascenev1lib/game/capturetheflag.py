# Released under the MIT License. See LICENSE for details.
#
"""Defines a capture-the-flag game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import weakref
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.flag import (
    FlagFactory,
    Flag,
    FlagPickedUpMessage,
    FlagDroppedMessage,
    FlagDiedMessage,
)

if TYPE_CHECKING:
    from typing import Any, Sequence


class CTFFlag(Flag):
    """Special flag type for CTF games."""

    activity: CaptureTheFlagGame

    def __init__(self, team: Team):

        assert team.flagmaterial is not None
        super().__init__(
            materials=[team.flagmaterial],
            position=team.base_pos,
            color=team.color,
        )
        self._team = weakref.ref(team)  # Avoid ref cycles.
        self.held_count = 0
        self.counter = bs.newnode(
            'text',
            owner=self.node,
            attrs={'in_world': True, 'scale': 0.02, 'h_align': 'center'},
        )
        self.reset_return_times()
        self.last_player_to_hold: Player | None = None
        self.time_out_respawn_time: int | None = None
        self.touch_return_time: float | None = None

    def reset_return_times(self) -> None:
        """Clear flag related times in the activity."""
        self.time_out_respawn_time = int(self.activity.flag_idle_return_time)
        self.touch_return_time = float(self.activity.flag_touch_return_time)

    @property
    def team(self) -> Team:
        """The flag's team."""
        team = self._team()
        if team is None:
            raise RuntimeError('Team no longer exists.')
        return team


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.touching_own_flag = 0


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(
        self,
        *,
        base_pos: Sequence[float],
        base_region_material: bs.Material,
        base_region: bs.Node,
        spaz_material_no_flag_physical: bs.Material,
        spaz_material_no_flag_collide: bs.Material,
        flagmaterial: bs.Material,
    ):
        self.base_pos = base_pos
        self.base_region_material = base_region_material
        self.base_region = base_region
        self.spaz_material_no_flag_physical = spaz_material_no_flag_physical
        self.spaz_material_no_flag_collide = spaz_material_no_flag_collide
        self.flagmaterial = flagmaterial
        self.score = 0
        self.flag_return_touches = 0
        self.home_flag_at_base = True
        self.touch_return_timer: bs.Timer | None = None
        self.enemy_flag_at_base = False
        self.flag: CTFFlag | None = None
        self.last_flag_leave_time: float | None = None
        self.touch_return_timer_ticking: bs.NodeActor | None = None


# ba_meta export bascenev1.GameActivity
class CaptureTheFlagGame(bs.TeamGameActivity[Player, Team]):
    """Game of stealing other team's flag and returning it to your base."""

    name = 'Capture the Flag'
    description = 'Return the enemy flag to score.'
    available_settings = [
        bs.IntSetting('Score to Win', min_value=1, default=3),
        bs.IntSetting(
            'Flag Touch Return Time',
            min_value=0,
            default=0,
            increment=1,
        ),
        bs.IntSetting(
            'Flag Idle Return Time',
            min_value=5,
            default=30,
            increment=5,
        ),
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
        return bs.app.classic.getmaps('team_flag')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._alarmsound = bs.getsound('alarm')
        self._ticking_sound = bs.getsound('ticking')
        self._score_sound = bs.getsound('score')
        self._swipsound = bs.getsound('swip')
        self._last_score_time = 0
        self._all_bases_material = bs.Material()
        self._last_home_flag_notice_print_time = 0.0
        self._score_to_win = int(settings['Score to Win'])
        self._epic_mode = bool(settings['Epic Mode'])
        self._time_limit = float(settings['Time Limit'])

        self.flag_touch_return_time = float(settings['Flag Touch Return Time'])
        self.flag_idle_return_time = float(settings['Flag Idle Return Time'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.FLAG_CATCHER
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if self._score_to_win == 1:
            return 'Steal the enemy flag.'
        return 'Steal the enemy flag ${ARG1} times.', self._score_to_win

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if self._score_to_win == 1:
            return 'return 1 flag'
        return 'return ${ARG1} flags', self._score_to_win

    @override
    def create_team(self, sessionteam: bs.SessionTeam) -> Team:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        # Create our team instance and its initial values.

        base_pos = self.map.get_flag_position(sessionteam.id)
        Flag.project_stand(base_pos)

        bs.newnode(
            'light',
            attrs={
                'position': base_pos,
                'intensity': 0.6,
                'height_attenuated': False,
                'volume_intensity_scale': 0.1,
                'radius': 0.1,
                'color': sessionteam.color,
            },
        )

        base_region_mat = bs.Material()
        pos = base_pos
        base_region = bs.newnode(
            'region',
            attrs={
                'position': (pos[0], pos[1] + 0.75, pos[2]),
                'scale': (0.5, 0.5, 0.5),
                'type': 'sphere',
                'materials': [base_region_mat, self._all_bases_material],
            },
        )

        spaz_mat_no_flag_physical = bs.Material()
        spaz_mat_no_flag_collide = bs.Material()
        flagmat = bs.Material()

        team = Team(
            base_pos=base_pos,
            base_region_material=base_region_mat,
            base_region=base_region,
            spaz_material_no_flag_physical=spaz_mat_no_flag_physical,
            spaz_material_no_flag_collide=spaz_mat_no_flag_collide,
            flagmaterial=flagmat,
        )

        # Some parts of our spazzes don't collide physically with our
        # flags but generate callbacks.
        spaz_mat_no_flag_physical.add_actions(
            conditions=('they_have_material', flagmat),
            actions=(
                ('modify_part_collision', 'physical', False),
                (
                    'call',
                    'at_connect',
                    lambda: self._handle_touching_own_flag(team, True),
                ),
                (
                    'call',
                    'at_disconnect',
                    lambda: self._handle_touching_own_flag(team, False),
                ),
            ),
        )

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
                (
                    'call',
                    'at_connect',
                    lambda: self._handle_flag_entered_base(team),
                ),
                (
                    'call',
                    'at_disconnect',
                    lambda: self._handle_flag_left_base(team),
                ),
            ),
        )

        return team

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        # Can't do this in create_team because the team's color/etc. have
        # not been wired up yet at that point.
        self._spawn_flag_for_team(team)
        self._update_scoreboard()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        bs.timer(1.0, call=self._tick, repeat=True)

    def _spawn_flag_for_team(self, team: Team) -> None:
        team.flag = CTFFlag(team)
        team.flag_return_touches = 0
        self._flash_base(team, length=1.0)
        assert team.flag.node
        self._swipsound.play(position=team.flag.node.position)

    def _handle_flag_entered_base(self, team: Team) -> None:
        try:
            flag = bs.getcollision().opposingnode.getdelegate(CTFFlag, True)
        except bs.NotFoundError:
            # Don't think this should logically ever happen.
            print('Error getting CTFFlag in entering-base callback.')
            return

        if flag.team is team:
            team.home_flag_at_base = True

            # If the enemy flag is already here, score!
            if team.enemy_flag_at_base:
                # And show team name which scored (but actually we could
                # show here player who returned enemy flag).
                self.show_zoom_message(
                    bs.Lstr(
                        resource='nameScoresText', subs=[('${NAME}', team.name)]
                    ),
                    color=team.color,
                )
                self._score(team)
        else:
            team.enemy_flag_at_base = True
            if team.home_flag_at_base:
                # Award points to whoever was carrying the enemy flag.
                player = flag.last_player_to_hold
                if player and player.team is team:
                    self.stats.player_scored(player, 50, big_message=True)

                # Update score and reset flags.
                self._score(team)

            # If the home-team flag isn't here, print a message to that effect.
            else:
                # Don't want slo-mo affecting this
                curtime = bs.basetime()
                if curtime - self._last_home_flag_notice_print_time > 5.0:
                    self._last_home_flag_notice_print_time = curtime
                    bpos = team.base_pos
                    tval = bs.Lstr(resource='ownFlagAtYourBaseWarning')
                    tnode = bs.newnode(
                        'text',
                        attrs={
                            'text': tval,
                            'in_world': True,
                            'scale': 0.013,
                            'color': (1, 1, 0, 1),
                            'h_align': 'center',
                            'position': (bpos[0], bpos[1] + 3.2, bpos[2]),
                        },
                    )
                    bs.timer(5.1, tnode.delete)
                    bs.animate(
                        tnode, 'scale', {0.0: 0, 0.2: 0.013, 4.8: 0.013, 5.0: 0}
                    )

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
                    flag.handlemessage(bs.DieMessage())
            else:
                time_out_counting_down = False

            if flag.node and flag.counter:
                pos = flag.node.position
                flag.counter.position = (pos[0], pos[1] + 1.3, pos[2])

                # If there's no self-touches on this flag, set its text
                # to show its auto-return counter.  (if there's self-touches
                # its showing that time).
                if team.flag_return_touches == 0:
                    flag.counter.text = (
                        str(flag.time_out_respawn_time)
                        if (
                            time_out_counting_down
                            and flag.time_out_respawn_time is not None
                            and flag.time_out_respawn_time <= 10
                        )
                        else ''
                    )
                    flag.counter.color = (1, 1, 1, 0.5)
                    flag.counter.scale = 0.014

    def _score(self, team: Team) -> None:
        team.score += 1
        self._score_sound.play()
        self._flash_base(team)
        self._update_scoreboard()

        # Have teammates celebrate.
        for player in team.players:
            if player.actor:
                player.actor.handlemessage(bs.CelebrateMessage(2.0))

        # Reset all flags/state.
        for reset_team in self.teams:
            if not reset_team.home_flag_at_base:
                assert reset_team.flag is not None
                reset_team.flag.handlemessage(bs.DieMessage())
            reset_team.enemy_flag_at_base = False
        if team.score >= self._score_to_win:
            self.end_game()

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results, announce_delay=0.8)

    def _handle_flag_left_base(self, team: Team) -> None:
        cur_time = bs.time()
        try:
            flag = bs.getcollision().opposingnode.getdelegate(CTFFlag, True)
        except bs.NotFoundError:
            # This can happen if the flag stops touching us due to being
            # deleted; that's ok.
            return

        if flag.team is team:
            # Check times here to prevent too much flashing.
            if (
                team.last_flag_leave_time is None
                or cur_time - team.last_flag_leave_time > 3.0
            ):
                self._alarmsound.play(position=team.base_pos)
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
            team.touch_return_timer_ticking = bs.NodeActor(
                bs.newnode(
                    'sound',
                    attrs={
                        'sound': self._ticking_sound,
                        'positional': False,
                        'loop': True,
                    },
                )
            )
        flag = team.flag
        if flag.touch_return_time is not None:
            flag.touch_return_time -= 0.1
            if flag.counter:
                flag.counter.text = f'{flag.touch_return_time:.1f}'
                flag.counter.color = (1, 1, 0, 1)
                flag.counter.scale = 0.02

            if flag.touch_return_time <= 0.0:
                self._award_players_touching_own_flag(team)
                flag.handlemessage(bs.DieMessage())

    def _award_players_touching_own_flag(self, team: Team) -> None:
        for player in team.players:
            if player.touching_own_flag > 0:
                return_score = 10 + 5 * int(self.flag_touch_return_time)
                self.stats.player_scored(
                    player, return_score, screenmessage=False
                )

    def _handle_touching_own_flag(self, team: Team, connecting: bool) -> None:
        """Called when a player touches or stops touching their own team flag.

        We keep track of when each player is touching their own flag so we
        can award points when returned.
        """
        player: Player | None
        try:
            spaz = bs.getcollision().sourcenode.getdelegate(PlayerSpaz, True)
        except bs.NotFoundError:
            return

        player = spaz.getplayer(Player, True)

        if player:
            player.touching_own_flag += 1 if connecting else -1

        # If return-time is zero, just kill it immediately.. otherwise keep
        # track of touches and count down.
        if float(self.flag_touch_return_time) <= 0.0:
            assert team.flag is not None
            if (
                connecting
                and not team.home_flag_at_base
                and team.flag.held_count == 0
            ):
                self._award_players_touching_own_flag(team)
                bs.getcollision().opposingnode.handlemessage(bs.DieMessage())

        # Takes a non-zero amount of time to return.
        else:
            if connecting:
                team.flag_return_touches += 1
                if team.flag_return_touches == 1:
                    team.touch_return_timer = bs.Timer(
                        0.1,
                        call=bs.Call(self._touch_return_update, team),
                        repeat=True,
                    )
                    team.touch_return_timer_ticking = None
            else:
                team.flag_return_touches -= 1
                if team.flag_return_touches == 0:
                    team.touch_return_timer = None
                    team.touch_return_timer_ticking = None
            if team.flag_return_touches < 0:
                logging.error('CTF flag_return_touches < 0', stack_info=True)

    def _handle_death_flag_capture(self, player: Player) -> None:
        """Handles flag values when a player dies or leaves the game."""
        # Don't do anything if the player hasn't touched the flag at all.
        if not player.touching_own_flag:
            return

        team = player.team

        # For each "point" our player has touched theflag (Could be
        # multiple), deduct one from both our player and the flag's
        # return touches variable.
        for _ in range(player.touching_own_flag):
            # Deduct
            player.touching_own_flag -= 1

            # (This was only incremented if we have non-zero
            # return-times).
            if float(self.flag_touch_return_time) > 0.0:
                team.flag_return_touches -= 1
                # Update our flag's timer accordingly
                # (Prevents immediate resets in case
                # there might be more people touching it).
                if team.flag_return_touches == 0:
                    team.touch_return_timer = None
                    team.touch_return_timer_ticking = None
                # Safety check, just to be sure!
                if team.flag_return_touches < 0:
                    logging.error(
                        'CTF flag_return_touches < 0', stack_info=True
                    )

    def _flash_base(self, team: Team, length: float = 2.0) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': team.base_pos,
                'height_attenuated': False,
                'radius': 0.3,
                'color': team.color,
            },
        )
        bs.animate(light, 'intensity', {0.0: 0, 0.25: 2.0, 0.5: 0}, loop=True)
        bs.timer(length, light.delete)

    @override
    def spawn_player_spaz(
        self,
        player: Player,
        position: Sequence[float] | None = None,
        angle: float | None = None,
    ) -> PlayerSpaz:
        """Intercept new spazzes and add our team material for them."""
        spaz = super().spawn_player_spaz(player, position, angle)
        player = spaz.getplayer(Player, True)
        team: Team = player.team
        player.touching_own_flag = 0
        no_physical_mats: list[bs.Material] = [
            team.spaz_material_no_flag_physical
        ]
        no_collide_mats: list[bs.Material] = [
            team.spaz_material_no_flag_collide
        ]

        # Our normal parts should still collide; just not physically
        # (so we can calc restores).
        assert spaz.node
        spaz.node.materials = list(spaz.node.materials) + no_physical_mats
        spaz.node.roller_materials = (
            list(spaz.node.roller_materials) + no_physical_mats
        )

        # Pickups and punches shouldn't hit at all though.
        spaz.node.punch_materials = (
            list(spaz.node.punch_materials) + no_collide_mats
        )
        spaz.node.pickup_materials = (
            list(spaz.node.pickup_materials) + no_collide_mats
        )
        spaz.node.extras_material = (
            list(spaz.node.extras_material) + no_collide_mats
        )
        return spaz

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.score, self._score_to_win
            )

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self._handle_death_flag_capture(msg.getplayer(Player))
            self.respawn_player(msg.getplayer(Player))

        elif isinstance(msg, FlagDiedMessage):
            assert isinstance(msg.flag, CTFFlag)
            bs.timer(0.1, bs.Call(self._spawn_flag_for_team, msg.flag.team))

        elif isinstance(msg, FlagPickedUpMessage):
            # Store the last player to hold the flag for scoring purposes.
            assert isinstance(msg.flag, CTFFlag)
            try:
                msg.flag.last_player_to_hold = msg.node.getdelegate(
                    PlayerSpaz, True
                ).getplayer(Player, True)
            except bs.NotFoundError:
                pass

            msg.flag.held_count += 1
            msg.flag.reset_return_times()

        elif isinstance(msg, FlagDroppedMessage):
            # Store the last player to hold the flag for scoring purposes.
            assert isinstance(msg.flag, CTFFlag)
            msg.flag.held_count -= 1

        else:
            super().handlemessage(msg)

    @override
    def on_player_leave(self, player: Player) -> None:
        """Prevents leaving players from capturing their flag."""
        self._handle_death_flag_capture(player)
