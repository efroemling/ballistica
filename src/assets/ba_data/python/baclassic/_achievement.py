# Released under the MIT License. See LICENSE for details.
#
"""Various functionality related to achievements."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import babase
import bascenev1
import bauiv1

if TYPE_CHECKING:
    from typing import Any, Sequence

    import baclassic

# This could use some cleanup.
# We wear the cone of shame.
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches

# FIXME: We should probably point achievements
#  at coop levels instead of hard-coding names.
#  (so level name substitution works right and whatnot).
ACH_LEVEL_NAMES = {
    'Boom Goes the Dynamite': 'Pro Onslaught',
    'Boxer': 'Onslaught Training',
    'Flawless Victory': 'Rookie Onslaught',
    'Gold Miner': 'Uber Onslaught',
    'Got the Moves': 'Uber Football',
    'Last Stand God': 'The Last Stand',
    'Last Stand Master': 'The Last Stand',
    'Last Stand Wizard': 'The Last Stand',
    'Mine Games': 'Rookie Onslaught',
    'Off You Go Then': 'Onslaught Training',
    'Onslaught God': 'Infinite Onslaught',
    'Onslaught Master': 'Infinite Onslaught',
    'Onslaught Training Victory': 'Onslaught Training',
    'Onslaught Wizard': 'Infinite Onslaught',
    'Precision Bombing': 'Pro Runaround',
    'Pro Boxer': 'Pro Onslaught',
    'Pro Football Shutout': 'Pro Football',
    'Pro Football Victory': 'Pro Football',
    'Pro Onslaught Victory': 'Pro Onslaught',
    'Pro Runaround Victory': 'Pro Runaround',
    'Rookie Football Shutout': 'Rookie Football',
    'Rookie Football Victory': 'Rookie Football',
    'Rookie Onslaught Victory': 'Rookie Onslaught',
    'Runaround God': 'Infinite Runaround',
    'Runaround Master': 'Infinite Runaround',
    'Runaround Wizard': 'Infinite Runaround',
    'Stayin\' Alive': 'Uber Runaround',
    'Super Mega Punch': 'Pro Football',
    'Super Punch': 'Rookie Football',
    'TNT Terror': 'Uber Onslaught',
    'The Great Wall': 'Uber Runaround',
    'The Wall': 'Pro Runaround',
    'Uber Football Shutout': 'Uber Football',
    'Uber Football Victory': 'Uber Football',
    'Uber Onslaught Victory': 'Uber Onslaught',
    'Uber Runaround Victory': 'Uber Runaround',
}


class AchievementSubsystem:
    """Subsystem for achievement handling.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.ach'.
    """

    def __init__(self) -> None:
        self.achievements: list[Achievement] = []
        self.achievements_to_display: list[
            tuple[baclassic.Achievement, bool]
        ] = []
        self.achievement_display_timer: bascenev1.BaseTimer | None = None
        self.last_achievement_display_time: float = 0.0
        self.achievement_completion_banner_slots: set[int] = set()
        self._init_achievements()

    def _init_achievements(self) -> None:
        """Fill in available achievements."""

        achs = self.achievements

        # 5
        achs.append(
            Achievement('In Control', 'achievementInControl', (1, 1, 1), '', 5)
        )
        # 15
        achs.append(
            Achievement(
                'Sharing is Caring',
                'achievementSharingIsCaring',
                (1, 1, 1),
                '',
                15,
            )
        )
        # 10
        achs.append(
            Achievement(
                'Dual Wielding', 'achievementDualWielding', (1, 1, 1), '', 10
            )
        )

        # 10
        achs.append(
            Achievement(
                'Free Loader', 'achievementFreeLoader', (1, 1, 1), '', 10
            )
        )
        # 20
        achs.append(
            Achievement(
                'Team Player', 'achievementTeamPlayer', (1, 1, 1), '', 20
            )
        )

        # 5
        achs.append(
            Achievement(
                'Onslaught Training Victory',
                'achievementOnslaught',
                (1, 1, 1),
                'Default:Onslaught Training',
                5,
            )
        )
        # 5
        achs.append(
            Achievement(
                'Off You Go Then',
                'achievementOffYouGo',
                (1, 1.1, 1.3),
                'Default:Onslaught Training',
                5,
            )
        )
        # 10
        achs.append(
            Achievement(
                'Boxer',
                'achievementBoxer',
                (1, 0.6, 0.6),
                'Default:Onslaught Training',
                10,
                hard_mode_only=True,
            )
        )

        # 10
        achs.append(
            Achievement(
                'Rookie Onslaught Victory',
                'achievementOnslaught',
                (0.5, 1.4, 0.6),
                'Default:Rookie Onslaught',
                10,
            )
        )
        # 10
        achs.append(
            Achievement(
                'Mine Games',
                'achievementMine',
                (1, 1, 1.4),
                'Default:Rookie Onslaught',
                10,
            )
        )
        # 15
        achs.append(
            Achievement(
                'Flawless Victory',
                'achievementFlawlessVictory',
                (1, 1, 1),
                'Default:Rookie Onslaught',
                15,
                hard_mode_only=True,
            )
        )

        # 10
        achs.append(
            Achievement(
                'Rookie Football Victory',
                'achievementFootballVictory',
                (1.0, 1, 0.6),
                'Default:Rookie Football',
                10,
            )
        )
        # 10
        achs.append(
            Achievement(
                'Super Punch',
                'achievementSuperPunch',
                (1, 1, 1.8),
                'Default:Rookie Football',
                10,
            )
        )
        # 15
        achs.append(
            Achievement(
                'Rookie Football Shutout',
                'achievementFootballShutout',
                (1, 1, 1),
                'Default:Rookie Football',
                15,
                hard_mode_only=True,
            )
        )

        # 15
        achs.append(
            Achievement(
                'Pro Onslaught Victory',
                'achievementOnslaught',
                (0.3, 1, 2.0),
                'Default:Pro Onslaught',
                15,
            )
        )
        # 15
        achs.append(
            Achievement(
                'Boom Goes the Dynamite',
                'achievementTNT',
                (1.4, 1.2, 0.8),
                'Default:Pro Onslaught',
                15,
            )
        )
        # 20
        achs.append(
            Achievement(
                'Pro Boxer',
                'achievementBoxer',
                (2, 2, 0),
                'Default:Pro Onslaught',
                20,
                hard_mode_only=True,
            )
        )

        # 15
        achs.append(
            Achievement(
                'Pro Football Victory',
                'achievementFootballVictory',
                (1.3, 1.3, 2.0),
                'Default:Pro Football',
                15,
            )
        )
        # 15
        achs.append(
            Achievement(
                'Super Mega Punch',
                'achievementSuperPunch',
                (2, 1, 0.6),
                'Default:Pro Football',
                15,
            )
        )
        # 20
        achs.append(
            Achievement(
                'Pro Football Shutout',
                'achievementFootballShutout',
                (0.7, 0.7, 2.0),
                'Default:Pro Football',
                20,
                hard_mode_only=True,
            )
        )

        # 15
        achs.append(
            Achievement(
                'Pro Runaround Victory',
                'achievementRunaround',
                (1, 1, 1),
                'Default:Pro Runaround',
                15,
            )
        )
        # 20
        achs.append(
            Achievement(
                'Precision Bombing',
                'achievementCrossHair',
                (1, 1, 1.3),
                'Default:Pro Runaround',
                20,
                hard_mode_only=True,
            )
        )
        # 25
        achs.append(
            Achievement(
                'The Wall',
                'achievementWall',
                (1, 0.7, 0.7),
                'Default:Pro Runaround',
                25,
                hard_mode_only=True,
            )
        )

        # 30
        achs.append(
            Achievement(
                'Uber Onslaught Victory',
                'achievementOnslaught',
                (2, 2, 1),
                'Default:Uber Onslaught',
                30,
            )
        )
        # 30
        achs.append(
            Achievement(
                'Gold Miner',
                'achievementMine',
                (2, 1.6, 0.2),
                'Default:Uber Onslaught',
                30,
                hard_mode_only=True,
            )
        )
        # 30
        achs.append(
            Achievement(
                'TNT Terror',
                'achievementTNT',
                (2, 1.8, 0.3),
                'Default:Uber Onslaught',
                30,
                hard_mode_only=True,
            )
        )

        # 30
        achs.append(
            Achievement(
                'Uber Football Victory',
                'achievementFootballVictory',
                (1.8, 1.4, 0.3),
                'Default:Uber Football',
                30,
            )
        )
        # 30
        achs.append(
            Achievement(
                'Got the Moves',
                'achievementGotTheMoves',
                (2, 1, 0),
                'Default:Uber Football',
                30,
                hard_mode_only=True,
            )
        )
        # 40
        achs.append(
            Achievement(
                'Uber Football Shutout',
                'achievementFootballShutout',
                (2, 2, 0),
                'Default:Uber Football',
                40,
                hard_mode_only=True,
            )
        )

        # 30
        achs.append(
            Achievement(
                'Uber Runaround Victory',
                'achievementRunaround',
                (1.5, 1.2, 0.2),
                'Default:Uber Runaround',
                30,
            )
        )
        # 40
        achs.append(
            Achievement(
                'The Great Wall',
                'achievementWall',
                (2, 1.7, 0.4),
                'Default:Uber Runaround',
                40,
                hard_mode_only=True,
            )
        )
        # 40
        achs.append(
            Achievement(
                'Stayin\' Alive',
                'achievementStayinAlive',
                (2, 2, 1),
                'Default:Uber Runaround',
                40,
                hard_mode_only=True,
            )
        )

        # 20
        achs.append(
            Achievement(
                'Last Stand Master',
                'achievementMedalSmall',
                (2, 1.5, 0.3),
                'Default:The Last Stand',
                20,
                hard_mode_only=True,
            )
        )
        # 40
        achs.append(
            Achievement(
                'Last Stand Wizard',
                'achievementMedalMedium',
                (2, 1.5, 0.3),
                'Default:The Last Stand',
                40,
                hard_mode_only=True,
            )
        )
        # 60
        achs.append(
            Achievement(
                'Last Stand God',
                'achievementMedalLarge',
                (2, 1.5, 0.3),
                'Default:The Last Stand',
                60,
                hard_mode_only=True,
            )
        )

        # 5
        achs.append(
            Achievement(
                'Onslaught Master',
                'achievementMedalSmall',
                (0.7, 1, 0.7),
                'Challenges:Infinite Onslaught',
                5,
            )
        )
        # 15
        achs.append(
            Achievement(
                'Onslaught Wizard',
                'achievementMedalMedium',
                (0.7, 1.0, 0.7),
                'Challenges:Infinite Onslaught',
                15,
            )
        )
        # 30
        achs.append(
            Achievement(
                'Onslaught God',
                'achievementMedalLarge',
                (0.7, 1.0, 0.7),
                'Challenges:Infinite Onslaught',
                30,
            )
        )

        # 5
        achs.append(
            Achievement(
                'Runaround Master',
                'achievementMedalSmall',
                (1.0, 1.0, 1.2),
                'Challenges:Infinite Runaround',
                5,
            )
        )
        # 15
        achs.append(
            Achievement(
                'Runaround Wizard',
                'achievementMedalMedium',
                (1.0, 1.0, 1.2),
                'Challenges:Infinite Runaround',
                15,
            )
        )
        # 30
        achs.append(
            Achievement(
                'Runaround God',
                'achievementMedalLarge',
                (1.0, 1.0, 1.2),
                'Challenges:Infinite Runaround',
                30,
            )
        )

    def award_local_achievement(self, achname: str) -> None:
        """For non-game-based achievements such as controller-connection."""
        plus = babase.app.plus
        if plus is None:
            logging.warning('achievements require plus feature-set')
            return
        try:
            ach = self.get_achievement(achname)
            if not ach.complete:
                # Report new achievements to the game-service.
                plus.report_achievement(achname)

                # And to our account.
                plus.add_v1_account_transaction(
                    {'type': 'ACHIEVEMENT', 'name': achname}
                )

                # Now attempt to show a banner.
                self.display_achievement_banner(achname)

        except Exception:
            logging.exception('Error in award_local_achievement.')

    def display_achievement_banner(self, achname: str) -> None:
        """Display a completion banner for an achievement.

        (internal)

        Used for server-driven achievements.
        """
        try:
            # FIXME: Need to get these using the UI context or some other
            #  purely local context somehow instead of trying to inject these
            #  into whatever activity happens to be active
            #  (since that won't work while in client mode).
            activity = bascenev1.get_foreground_host_activity()
            if activity is not None:
                with activity.context:
                    self.get_achievement(achname).announce_completion()
        except Exception:
            logging.exception('Error in display_achievement_banner.')

    def set_completed_achievements(self, achs: Sequence[str]) -> None:
        """Set the current state of completed achievements.

        (internal)

        All achievements not included here will be set incomplete.
        """

        # Note: This gets called whenever game-center/game-circle/etc tells
        # us which achievements we currently have.  We always defer to them,
        # even if that means we have to un-set an achievement we think we have.

        cfg = babase.app.config
        cfg['Achievements'] = {}
        for a_name in achs:
            self.get_achievement(a_name).set_complete(True)
        cfg.commit()

    def get_achievement(self, name: str) -> Achievement:
        """Return an Achievement by name."""
        achs = [a for a in self.achievements if a.name == name]
        assert len(achs) < 2
        if not achs:
            raise ValueError("Invalid achievement name: '" + name + "'")
        return achs[0]

    def achievements_for_coop_level(self, level_name: str) -> list[Achievement]:
        """Given a level name, return achievements available for it."""

        # For the Easy campaign we return achievements for the Default
        # campaign too. (want the user to see what achievements are part of the
        # level even if they can't unlock them all on easy mode).
        return [
            a
            for a in self.achievements
            if a.level_name
            in (level_name, level_name.replace('Easy', 'Default'))
        ]

    def _test(self) -> None:
        """For testing achievement animations."""

        def testcall1() -> None:
            self.achievements[0].announce_completion()
            self.achievements[1].announce_completion()
            self.achievements[2].announce_completion()

        def testcall2() -> None:
            self.achievements[3].announce_completion()
            self.achievements[4].announce_completion()
            self.achievements[5].announce_completion()

        bascenev1.basetimer(3.0, testcall1)
        bascenev1.basetimer(7.0, testcall2)


def _get_ach_mult(include_pro_bonus: bool = False) -> int:
    """Return the multiplier for achievement pts.

    (just for display; changing this here won't affect actual rewards)
    """
    plus = babase.app.plus
    classic = babase.app.classic
    if plus is None or classic is None:
        return 5
    val: int = plus.get_v1_account_misc_read_val('achAwardMult', 5)
    assert isinstance(val, int)
    if include_pro_bonus and classic.accounts.have_pro():
        val *= 2
    return val


def _display_next_achievement() -> None:
    # Pull the first achievement off the list and display it, or kill the
    # display-timer if the list is empty.
    app = babase.app
    assert app.classic is not None
    ach_ss = app.classic.ach
    if app.classic.ach.achievements_to_display:
        try:
            ach, sound = ach_ss.achievements_to_display.pop(0)
            ach.show_completion_banner(sound)
        except Exception:
            logging.exception('Error in _display_next_achievement.')
            ach_ss.achievements_to_display = []
            ach_ss.achievement_display_timer = None
    else:
        ach_ss.achievement_display_timer = None


class Achievement:
    """Represents attributes and state for an individual achievement.

    Category: **App Classes**
    """

    def __init__(
        self,
        name: str,
        icon_name: str,
        icon_color: Sequence[float],
        level_name: str,
        award: int,
        hard_mode_only: bool = False,
    ):
        # pylint: disable=too-many-positional-arguments
        self._name = name
        self._icon_name = icon_name
        self._icon_color: Sequence[float] = list(icon_color) + [1]
        self._level_name = level_name
        self._completion_banner_slot: int | None = None
        self._award = award
        self._hard_mode_only = hard_mode_only

    @property
    def name(self) -> str:
        """The name of this achievement."""
        return self._name

    @property
    def level_name(self) -> str:
        """The name of the level this achievement applies to."""
        return self._level_name

    def get_icon_ui_texture(self, complete: bool) -> bauiv1.Texture:
        """Return the icon texture to display for this achievement"""
        return bauiv1.gettexture(
            self._icon_name if complete else 'achievementEmpty'
        )

    def get_icon_texture(self, complete: bool) -> bascenev1.Texture:
        """Return the icon texture to display for this achievement"""
        return bascenev1.gettexture(
            self._icon_name if complete else 'achievementEmpty'
        )

    def get_icon_color(self, complete: bool) -> Sequence[float]:
        """Return the color tint for this Achievement's icon."""
        if complete:
            return self._icon_color
        return 1.0, 1.0, 1.0, 0.6

    @property
    def hard_mode_only(self) -> bool:
        """Whether this Achievement is only unlockable in hard-mode."""
        return self._hard_mode_only

    @property
    def complete(self) -> bool:
        """Whether this Achievement is currently complete."""
        val: bool = self._getconfig()['Complete']
        assert isinstance(val, bool)
        return val

    def announce_completion(self, sound: bool = True) -> None:
        """Kick off an announcement for this achievement's completion."""

        app = babase.app
        plus = app.plus
        classic = app.classic
        if plus is None or classic is None:
            logging.warning('ach account_completion not available.')
            return

        ach_ss = classic.ach

        # Even though there are technically achievements when we're not
        # signed in, lets not show them (otherwise we tend to get
        # confusing 'controller connected' achievements popping up while
        # waiting to sign in which can be confusing).
        if plus.get_v1_account_state() != 'signed_in':
            return

        # If we're being freshly complete, display/report it and whatnot.
        if (self, sound) not in ach_ss.achievements_to_display:
            ach_ss.achievements_to_display.append((self, sound))

        # If there's no achievement display timer going, kick one off
        # (if one's already running it will pick this up before it dies).

        # Need to check last time too; its possible our timer wasn't able to
        # clear itself if an activity died and took it down with it.
        if (
            ach_ss.achievement_display_timer is None
            or babase.apptime() - ach_ss.last_achievement_display_time > 2.0
        ) and bascenev1.getactivity(doraise=False) is not None:
            ach_ss.achievement_display_timer = bascenev1.BaseTimer(
                1.0, _display_next_achievement, repeat=True
            )

            # Show the first immediately.
            _display_next_achievement()

    def set_complete(self, complete: bool = True) -> None:
        """Set an achievement's completed state.

        note this only sets local state; use a transaction to
        actually award achievements.
        """
        config = self._getconfig()
        if complete != config['Complete']:
            config['Complete'] = complete

    @property
    def display_name(self) -> babase.Lstr:
        """Return a babase.Lstr for this Achievement's name."""
        name: babase.Lstr | str
        try:
            if self._level_name != '':
                campaignname, campaign_level = self._level_name.split(':')
                classic = babase.app.classic
                assert classic is not None
                name = (
                    classic.getcampaign(campaignname)
                    .getlevel(campaign_level)
                    .displayname
                )
            else:
                name = ''
        except Exception:
            name = ''
            logging.exception('Error calcing achievement display-name.')
        return babase.Lstr(
            resource='achievements.' + self._name + '.name',
            subs=[('${LEVEL}', name)],
        )

    @property
    def description(self) -> babase.Lstr:
        """Get a babase.Lstr for the Achievement's brief description."""
        if (
            'description'
            in babase.app.lang.get_resource('achievements')[self._name]
        ):
            return babase.Lstr(
                resource='achievements.' + self._name + '.description'
            )
        return babase.Lstr(
            resource='achievements.' + self._name + '.descriptionFull'
        )

    @property
    def description_complete(self) -> babase.Lstr:
        """Get a babase.Lstr for the Achievement's description when complete."""
        if (
            'descriptionComplete'
            in babase.app.lang.get_resource('achievements')[self._name]
        ):
            return babase.Lstr(
                resource='achievements.' + self._name + '.descriptionComplete'
            )
        return babase.Lstr(
            resource='achievements.' + self._name + '.descriptionFullComplete'
        )

    @property
    def description_full(self) -> babase.Lstr:
        """Get a babase.Lstr for the Achievement's full description."""
        return babase.Lstr(
            resource='achievements.' + self._name + '.descriptionFull',
            subs=[
                (
                    '${LEVEL}',
                    babase.Lstr(
                        translate=(
                            'coopLevelNames',
                            ACH_LEVEL_NAMES.get(self._name, '?'),
                        )
                    ),
                )
            ],
        )

    @property
    def description_full_complete(self) -> babase.Lstr:
        """Get a babase.Lstr for the Achievement's full desc. when completed."""
        return babase.Lstr(
            resource='achievements.' + self._name + '.descriptionFullComplete',
            subs=[
                (
                    '${LEVEL}',
                    babase.Lstr(
                        translate=(
                            'coopLevelNames',
                            ACH_LEVEL_NAMES.get(self._name, '?'),
                        )
                    ),
                )
            ],
        )

    def get_award_ticket_value(self, include_pro_bonus: bool = False) -> int:
        """Get the ticket award value for this achievement."""
        plus = babase.app.plus
        if plus is None:
            return 0
        val: int = plus.get_v1_account_misc_read_val(
            'achAward.' + self._name, self._award
        ) * _get_ach_mult(include_pro_bonus)
        assert isinstance(val, int)
        return val

    @property
    def power_ranking_value(self) -> int:
        """Get the power-ranking award value for this achievement."""
        plus = babase.app.plus
        if plus is None:
            return 0
        val: int = plus.get_v1_account_misc_read_val(
            'achLeaguePoints.' + self._name, self._award
        )
        assert isinstance(val, int)
        return val

    def create_display(
        self,
        x: float,
        y: float,
        delay: float,
        *,
        outdelay: float | None = None,
        color: Sequence[float] | None = None,
        style: str = 'post_game',
    ) -> list[bascenev1.Actor]:
        """Create a display for the Achievement.

        Shows the Achievement icon, name, and description.
        """
        # pylint: disable=cyclic-import
        from bascenev1 import CoopSession
        from bascenev1lib.actor.image import Image
        from bascenev1lib.actor.text import Text

        # Yeah this needs cleaning up.
        if style == 'post_game':
            in_game_colors = False
            in_main_menu = False
            h_attach = Text.HAttach.CENTER
            v_attach = Text.VAttach.CENTER
            attach = Image.Attach.CENTER
        elif style == 'in_game':
            in_game_colors = True
            in_main_menu = False
            h_attach = Text.HAttach.LEFT
            v_attach = Text.VAttach.TOP
            attach = Image.Attach.TOP_LEFT
        elif style == 'news':
            in_game_colors = True
            in_main_menu = True
            h_attach = Text.HAttach.CENTER
            v_attach = Text.VAttach.TOP
            attach = Image.Attach.TOP_CENTER
        else:
            raise ValueError('invalid style "' + style + '"')

        # Attempt to determine what campaign we're in
        # (so we know whether to show "hard mode only").
        if in_main_menu:
            hmo = False
        else:
            try:
                session = bascenev1.getsession()
                if isinstance(session, CoopSession):
                    campaign = session.campaign
                    assert campaign is not None
                    hmo = self._hard_mode_only and campaign.name == 'Easy'
                else:
                    hmo = False
            except Exception:
                logging.exception('Error determining campaign.')
                hmo = False

        objs: list[bascenev1.Actor]

        if in_game_colors:
            objs = []
            out_delay_fin = (delay + outdelay) if outdelay is not None else None
            if color is not None:
                cl1 = (2.0 * color[0], 2.0 * color[1], 2.0 * color[2], color[3])
                cl2 = color
            else:
                cl1 = (1.5, 1.5, 2, 1.0)
                cl2 = (0.8, 0.8, 1.0, 1.0)

            if hmo:
                cl1 = (cl1[0], cl1[1], cl1[2], cl1[3] * 0.6)
                cl2 = (cl2[0], cl2[1], cl2[2], cl2[3] * 0.2)

            objs.append(
                Image(
                    self.get_icon_texture(False),
                    host_only=True,
                    color=cl1,
                    position=(x - 25, y + 5),
                    attach=attach,
                    transition=Image.Transition.FADE_IN,
                    transition_delay=delay,
                    vr_depth=4,
                    transition_out_delay=out_delay_fin,
                    scale=(40, 40),
                ).autoretain()
            )
            txt = self.display_name
            txt_s = 0.85
            txt_max_w = 300
            objs.append(
                Text(
                    txt,
                    host_only=True,
                    maxwidth=txt_max_w,
                    position=(x, y + 2),
                    transition=Text.Transition.FADE_IN,
                    scale=txt_s,
                    flatness=0.6,
                    shadow=0.5,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    color=cl2,
                    transition_delay=delay + 0.05,
                    transition_out_delay=out_delay_fin,
                ).autoretain()
            )
            txt2_s = 0.62
            txt2_max_w = 400
            objs.append(
                Text(
                    self.description_full if in_main_menu else self.description,
                    host_only=True,
                    maxwidth=txt2_max_w,
                    position=(x, y - 14),
                    transition=Text.Transition.FADE_IN,
                    vr_depth=-5,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    scale=txt2_s,
                    flatness=1.0,
                    shadow=0.5,
                    color=cl2,
                    transition_delay=delay + 0.1,
                    transition_out_delay=out_delay_fin,
                ).autoretain()
            )

            if hmo:
                txtactor = Text(
                    babase.Lstr(resource='difficultyHardOnlyText'),
                    host_only=True,
                    maxwidth=txt2_max_w * 0.7,
                    position=(x + 60, y + 5),
                    transition=Text.Transition.FADE_IN,
                    vr_depth=-5,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    h_align=Text.HAlign.CENTER,
                    v_align=Text.VAlign.CENTER,
                    scale=txt_s * 0.8,
                    flatness=1.0,
                    shadow=0.5,
                    color=(1, 1, 0.6, 1),
                    transition_delay=delay + 0.1,
                    transition_out_delay=out_delay_fin,
                ).autoretain()
                txtactor.node.rotate = 10
                objs.append(txtactor)

            # Ticket-award.
            award_x = -100
            objs.append(
                Text(
                    babase.charstr(babase.SpecialChar.TICKET),
                    host_only=True,
                    position=(x + award_x + 33, y + 7),
                    transition=Text.Transition.FADE_IN,
                    scale=1.5,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    h_align=Text.HAlign.CENTER,
                    v_align=Text.VAlign.CENTER,
                    color=(1, 1, 1, 0.2 if hmo else 0.4),
                    transition_delay=delay + 0.05,
                    transition_out_delay=out_delay_fin,
                ).autoretain()
            )
            objs.append(
                Text(
                    '+' + str(self.get_award_ticket_value()),
                    host_only=True,
                    position=(x + award_x + 28, y + 16),
                    transition=Text.Transition.FADE_IN,
                    scale=0.7,
                    flatness=1,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    h_align=Text.HAlign.CENTER,
                    v_align=Text.VAlign.CENTER,
                    color=cl2,
                    transition_delay=delay + 0.05,
                    transition_out_delay=out_delay_fin,
                ).autoretain()
            )

        else:
            complete = self.complete
            objs = []
            c_icon = self.get_icon_color(complete)
            if hmo and not complete:
                c_icon = (c_icon[0], c_icon[1], c_icon[2], c_icon[3] * 0.3)
            objs.append(
                Image(
                    self.get_icon_texture(complete),
                    host_only=True,
                    color=c_icon,
                    position=(x - 25, y + 5),
                    attach=attach,
                    vr_depth=4,
                    transition=Image.Transition.IN_RIGHT,
                    transition_delay=delay,
                    transition_out_delay=None,
                    scale=(40, 40),
                ).autoretain()
            )
            if complete:
                objs.append(
                    Image(
                        bascenev1.gettexture('achievementOutline'),
                        host_only=True,
                        mesh_transparent=bascenev1.getmesh(
                            'achievementOutline'
                        ),
                        color=(2, 1.4, 0.4, 1),
                        vr_depth=8,
                        position=(x - 25, y + 5),
                        attach=attach,
                        transition=Image.Transition.IN_RIGHT,
                        transition_delay=delay,
                        transition_out_delay=None,
                        scale=(40, 40),
                    ).autoretain()
                )
            else:
                if not complete:
                    award_x = -100
                    objs.append(
                        Text(
                            babase.charstr(babase.SpecialChar.TICKET),
                            host_only=True,
                            position=(x + award_x + 33, y + 7),
                            transition=Text.Transition.IN_RIGHT,
                            scale=1.5,
                            h_attach=h_attach,
                            v_attach=v_attach,
                            h_align=Text.HAlign.CENTER,
                            v_align=Text.VAlign.CENTER,
                            color=(1, 1, 1, (0.1 if hmo else 0.2)),
                            transition_delay=delay + 0.05,
                            transition_out_delay=None,
                        ).autoretain()
                    )
                    objs.append(
                        Text(
                            '+' + str(self.get_award_ticket_value()),
                            host_only=True,
                            position=(x + award_x + 28, y + 16),
                            transition=Text.Transition.IN_RIGHT,
                            scale=0.7,
                            flatness=1,
                            h_attach=h_attach,
                            v_attach=v_attach,
                            h_align=Text.HAlign.CENTER,
                            v_align=Text.VAlign.CENTER,
                            color=(0.6, 0.6, 0.6, (0.2 if hmo else 0.4)),
                            transition_delay=delay + 0.05,
                            transition_out_delay=None,
                        ).autoretain()
                    )

                    # Show 'hard-mode-only' only over incomplete achievements
                    # when that's the case.
                    if hmo:
                        txtactor = Text(
                            babase.Lstr(resource='difficultyHardOnlyText'),
                            host_only=True,
                            maxwidth=300 * 0.7,
                            position=(x + 60, y + 5),
                            transition=Text.Transition.FADE_IN,
                            vr_depth=-5,
                            h_attach=h_attach,
                            v_attach=v_attach,
                            h_align=Text.HAlign.CENTER,
                            v_align=Text.VAlign.CENTER,
                            scale=0.85 * 0.8,
                            flatness=1.0,
                            shadow=0.5,
                            color=(1, 1, 0.6, 1),
                            transition_delay=delay + 0.05,
                            transition_out_delay=None,
                        ).autoretain()
                        assert txtactor.node
                        txtactor.node.rotate = 10
                        objs.append(txtactor)

            objs.append(
                Text(
                    self.display_name,
                    host_only=True,
                    maxwidth=300,
                    position=(x, y + 2),
                    transition=Text.Transition.IN_RIGHT,
                    scale=0.85,
                    flatness=0.6,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    color=(
                        (0.8, 0.93, 0.8, 1.0)
                        if complete
                        else (0.6, 0.6, 0.6, (0.2 if hmo else 0.4))
                    ),
                    transition_delay=delay + 0.05,
                    transition_out_delay=None,
                ).autoretain()
            )
            objs.append(
                Text(
                    self.description_complete if complete else self.description,
                    host_only=True,
                    maxwidth=400,
                    position=(x, y - 14),
                    transition=Text.Transition.IN_RIGHT,
                    vr_depth=-5,
                    h_attach=h_attach,
                    v_attach=v_attach,
                    scale=0.62,
                    flatness=1.0,
                    color=(
                        (0.6, 0.6, 0.6, 1.0)
                        if complete
                        else (0.6, 0.6, 0.6, (0.2 if hmo else 0.4))
                    ),
                    transition_delay=delay + 0.1,
                    transition_out_delay=None,
                ).autoretain()
            )
        return objs

    def _getconfig(self) -> dict[str, Any]:
        """
        Return the sub-dict in settings where this achievement's
        state is stored, creating it if need be.
        """
        val: dict[str, Any] = babase.app.config.setdefault(
            'Achievements', {}
        ).setdefault(self._name, {'Complete': False})
        assert isinstance(val, dict)
        return val

    def _remove_banner_slot(self) -> None:
        classic = babase.app.classic
        assert classic is not None
        assert self._completion_banner_slot is not None
        classic.ach.achievement_completion_banner_slots.remove(
            self._completion_banner_slot
        )
        self._completion_banner_slot = None

    def show_completion_banner(self, sound: bool = True) -> None:
        """Create the banner/sound for an acquired achievement announcement."""
        from bascenev1lib.actor.text import Text
        from bascenev1lib.actor.image import Image

        app = babase.app
        assert app.classic is not None
        app.classic.ach.last_achievement_display_time = babase.apptime()

        # Just piggy-back onto any current activity
        # (should we use the session instead?..)
        activity = bascenev1.getactivity(doraise=False)

        # If this gets called while this achievement is occupying a slot
        # already, ignore it. (probably should never happen in real
        # life but whatevs).
        if self._completion_banner_slot is not None:
            return

        if activity is None:
            print('show_completion_banner() called with no current activity!')
            return

        if sound:
            bascenev1.getsound('achievement').play(host_only=True)
        else:
            bascenev1.timer(
                0.5, lambda: bascenev1.getsound('ding').play(host_only=True)
            )

        in_time = 0.300
        out_time = 3.5

        base_vr_depth = 200

        # Find the first free slot.
        i = 0
        while True:
            if i not in app.classic.ach.achievement_completion_banner_slots:
                app.classic.ach.achievement_completion_banner_slots.add(i)
                self._completion_banner_slot = i

                # Remove us from that slot when we close.
                # Use an app-timer in an empty context so the removal
                # runs even if our activity/session dies.
                with babase.ContextRef.empty():
                    babase.apptimer(
                        in_time + out_time, self._remove_banner_slot
                    )
                break
            i += 1
        assert self._completion_banner_slot is not None
        y_offs = 110 * self._completion_banner_slot
        objs: list[bascenev1.Actor] = []
        obj = Image(
            bascenev1.gettexture('shadow'),
            position=(-30, 30 + y_offs),
            front=True,
            attach=Image.Attach.BOTTOM_CENTER,
            transition=Image.Transition.IN_BOTTOM,
            vr_depth=base_vr_depth - 100,
            transition_delay=in_time,
            transition_out_delay=out_time,
            color=(0.0, 0.1, 0, 1),
            scale=(1000, 300),
        ).autoretain()
        objs.append(obj)
        assert obj.node
        obj.node.host_only = True
        obj = Image(
            bascenev1.gettexture('light'),
            position=(-180, 60 + y_offs),
            front=True,
            attach=Image.Attach.BOTTOM_CENTER,
            vr_depth=base_vr_depth,
            transition=Image.Transition.IN_BOTTOM,
            transition_delay=in_time,
            transition_out_delay=out_time,
            color=(1.8, 1.8, 1.0, 0.0),
            scale=(40, 300),
        ).autoretain()
        objs.append(obj)
        assert obj.node
        obj.node.host_only = True
        obj.node.premultiplied = True
        combine = bascenev1.newnode(
            'combine', owner=obj.node, attrs={'size': 2}
        )
        bascenev1.animate(
            combine,
            'input0',
            {
                in_time: 0,
                in_time + 0.4: 30,
                in_time + 0.5: 40,
                in_time + 0.6: 30,
                in_time + 2.0: 0,
            },
        )
        bascenev1.animate(
            combine,
            'input1',
            {
                in_time: 0,
                in_time + 0.4: 200,
                in_time + 0.5: 500,
                in_time + 0.6: 200,
                in_time + 2.0: 0,
            },
        )
        combine.connectattr('output', obj.node, 'scale')
        bascenev1.animate(obj.node, 'rotate', {0: 0.0, 0.35: 360.0}, loop=True)
        obj = Image(
            self.get_icon_texture(True),
            position=(-180, 60 + y_offs),
            attach=Image.Attach.BOTTOM_CENTER,
            front=True,
            vr_depth=base_vr_depth - 10,
            transition=Image.Transition.IN_BOTTOM,
            transition_delay=in_time,
            transition_out_delay=out_time,
            scale=(100, 100),
        ).autoretain()
        objs.append(obj)
        assert obj.node
        obj.node.host_only = True

        # Flash.
        color = self.get_icon_color(True)
        combine = bascenev1.newnode(
            'combine', owner=obj.node, attrs={'size': 3}
        )
        keys = {
            in_time: 1.0 * color[0],
            in_time + 0.4: 1.5 * color[0],
            in_time + 0.5: 6.0 * color[0],
            in_time + 0.6: 1.5 * color[0],
            in_time + 2.0: 1.0 * color[0],
        }
        bascenev1.animate(combine, 'input0', keys)
        keys = {
            in_time: 1.0 * color[1],
            in_time + 0.4: 1.5 * color[1],
            in_time + 0.5: 6.0 * color[1],
            in_time + 0.6: 1.5 * color[1],
            in_time + 2.0: 1.0 * color[1],
        }
        bascenev1.animate(combine, 'input1', keys)
        keys = {
            in_time: 1.0 * color[2],
            in_time + 0.4: 1.5 * color[2],
            in_time + 0.5: 6.0 * color[2],
            in_time + 0.6: 1.5 * color[2],
            in_time + 2.0: 1.0 * color[2],
        }
        bascenev1.animate(combine, 'input2', keys)
        combine.connectattr('output', obj.node, 'color')

        obj = Image(
            bascenev1.gettexture('achievementOutline'),
            mesh_transparent=bascenev1.getmesh('achievementOutline'),
            position=(-180, 60 + y_offs),
            front=True,
            attach=Image.Attach.BOTTOM_CENTER,
            vr_depth=base_vr_depth,
            transition=Image.Transition.IN_BOTTOM,
            transition_delay=in_time,
            transition_out_delay=out_time,
            scale=(100, 100),
        ).autoretain()
        assert obj.node
        obj.node.host_only = True

        # Flash.
        color = (2, 1.4, 0.4, 1)
        combine = bascenev1.newnode(
            'combine', owner=obj.node, attrs={'size': 3}
        )
        keys = {
            in_time: 1.0 * color[0],
            in_time + 0.4: 1.5 * color[0],
            in_time + 0.5: 6.0 * color[0],
            in_time + 0.6: 1.5 * color[0],
            in_time + 2.0: 1.0 * color[0],
        }
        bascenev1.animate(combine, 'input0', keys)
        keys = {
            in_time: 1.0 * color[1],
            in_time + 0.4: 1.5 * color[1],
            in_time + 0.5: 6.0 * color[1],
            in_time + 0.6: 1.5 * color[1],
            in_time + 2.0: 1.0 * color[1],
        }
        bascenev1.animate(combine, 'input1', keys)
        keys = {
            in_time: 1.0 * color[2],
            in_time + 0.4: 1.5 * color[2],
            in_time + 0.5: 6.0 * color[2],
            in_time + 0.6: 1.5 * color[2],
            in_time + 2.0: 1.0 * color[2],
        }
        bascenev1.animate(combine, 'input2', keys)
        combine.connectattr('output', obj.node, 'color')
        objs.append(obj)

        objt = Text(
            babase.Lstr(
                value='${A}:',
                subs=[('${A}', babase.Lstr(resource='achievementText'))],
            ),
            position=(-120, 91 + y_offs),
            front=True,
            v_attach=Text.VAttach.BOTTOM,
            vr_depth=base_vr_depth - 10,
            transition=Text.Transition.IN_BOTTOM,
            flatness=0.5,
            transition_delay=in_time,
            transition_out_delay=out_time,
            color=(1, 1, 1, 0.8),
            scale=0.65,
        ).autoretain()
        objs.append(objt)
        assert objt.node
        objt.node.host_only = True

        objt = Text(
            self.display_name,
            position=(-120, 50 + y_offs),
            front=True,
            v_attach=Text.VAttach.BOTTOM,
            transition=Text.Transition.IN_BOTTOM,
            vr_depth=base_vr_depth,
            flatness=0.5,
            transition_delay=in_time,
            transition_out_delay=out_time,
            flash=True,
            color=(1, 0.8, 0, 1.0),
            scale=1.5,
        ).autoretain()
        objs.append(objt)
        assert objt.node
        objt.node.host_only = True

        objt = Text(
            babase.charstr(babase.SpecialChar.TICKET),
            position=(-120 - 170 + 5, 75 + y_offs - 20),
            front=True,
            v_attach=Text.VAttach.BOTTOM,
            h_align=Text.HAlign.CENTER,
            v_align=Text.VAlign.CENTER,
            transition=Text.Transition.IN_BOTTOM,
            vr_depth=base_vr_depth,
            transition_delay=in_time,
            transition_out_delay=out_time,
            flash=True,
            color=(0.5, 0.5, 0.5, 1),
            scale=3.0,
        ).autoretain()
        objs.append(objt)
        assert objt.node
        objt.node.host_only = True

        objt = Text(
            '+' + str(self.get_award_ticket_value()),
            position=(-120 - 180 + 5, 80 + y_offs - 20),
            v_attach=Text.VAttach.BOTTOM,
            front=True,
            h_align=Text.HAlign.CENTER,
            v_align=Text.VAlign.CENTER,
            transition=Text.Transition.IN_BOTTOM,
            vr_depth=base_vr_depth,
            flatness=0.5,
            shadow=1.0,
            transition_delay=in_time,
            transition_out_delay=out_time,
            flash=True,
            color=(0, 1, 0, 1),
            scale=1.5,
        ).autoretain()
        objs.append(objt)
        assert objt.node
        objt.node.host_only = True

        # Add the 'x 2' if we've got pro.
        if app.classic.accounts.have_pro():
            objt = Text(
                'x 2',
                position=(-120 - 180 + 45, 80 + y_offs - 50),
                v_attach=Text.VAttach.BOTTOM,
                front=True,
                h_align=Text.HAlign.CENTER,
                v_align=Text.VAlign.CENTER,
                transition=Text.Transition.IN_BOTTOM,
                vr_depth=base_vr_depth,
                flatness=0.5,
                shadow=1.0,
                transition_delay=in_time,
                transition_out_delay=out_time,
                flash=True,
                color=(0.4, 0, 1, 1),
                scale=0.9,
            ).autoretain()
            objs.append(objt)
            assert objt.node
            objt.node.host_only = True

        objt = Text(
            self.description_complete,
            position=(-120, 30 + y_offs),
            front=True,
            v_attach=Text.VAttach.BOTTOM,
            transition=Text.Transition.IN_BOTTOM,
            vr_depth=base_vr_depth - 10,
            flatness=0.5,
            transition_delay=in_time,
            transition_out_delay=out_time,
            color=(1.0, 0.7, 0.5, 1.0),
            scale=0.8,
        ).autoretain()
        objs.append(objt)
        assert objt.node
        objt.node.host_only = True

        for actor in objs:
            bascenev1.timer(
                out_time + 1.000,
                babase.WeakCall(actor.handlemessage, bascenev1.DieMessage()),
            )
