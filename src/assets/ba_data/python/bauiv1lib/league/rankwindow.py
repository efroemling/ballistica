# Released under the MIT License. See LICENSE for details.
#
"""UI related to league rank."""
# pylint: disable=too-many-lines

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, override

from bauiv1lib.popup import PopupMenu
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class LeagueRankWindow(bui.MainWindow):
    """Window for showing league rank."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        plus = bui.app.plus
        assert plus is not None

        bui.set_analytics_screen('League Rank Window')

        self._league_rank_data: dict[str, Any] | None = None

        self._power_ranking_achievements_button: bui.Widget | None = None
        self._pro_mult_button: bui.Widget | None = None
        self._power_ranking_trophies_button: bui.Widget | None = None
        self._league_title_text: bui.Widget | None = None
        self._league_text: bui.Widget | None = None
        self._league_number_text: bui.Widget | None = None
        self._your_power_ranking_text: bui.Widget | None = None
        self._loading_spinner: bui.Widget | None = None
        self._season_ends_text: bui.Widget | None = None
        self._power_ranking_rank_text: bui.Widget | None = None
        self._to_ranked_text: bui.Widget | None = None
        self._trophy_counts_reset_text: bui.Widget | None = None

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1490 if uiscale is bui.UIScale.SMALL else 1120
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            660
            if uiscale is bui.UIScale.SMALL
            else 710 if uiscale is bui.UIScale.MEDIUM else 800
        )
        self._r = 'coopSelectWindow'
        self._rdict = bui.app.lang.get_resource(self._r)
        top_extra = 20 if uiscale is bui.UIScale.SMALL else 0

        self._xoffs = 80.0 if uiscale is bui.UIScale.SMALL else 0

        self._league_url_arg = ''

        self._is_current_season = False
        self._can_do_more_button = True

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 10) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
                scale=(
                    1.08
                    if uiscale is bui.UIScale.SMALL
                    else 0.93 if uiscale is bui.UIScale.MEDIUM else 0.8
                ),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = bui.get_special_widget('back_button')
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(75 + x_inset, self._height - 87),
                size=(120, 60),
                scale=1.2,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self.main_window_back,
            )
            bui.buttonwidget(
                edit=btn,
                button_type='backSmall',
                position=(75 + x_inset, self._height - 87),
                size=(60, 55),
                label=bui.charstr(bui.SpecialChar.BACK),
            )
            bui.containerwidget(
                edit=self._root_widget,
                cancel_button=self._back_button,
                selected_child=self._back_button,
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                self._height - (66 if uiscale is bui.UIScale.SMALL else 56),
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource='league.leagueRankText',
                fallback_resource='coopSelectWindow.powerRankingText',
            ),
            h_align='center',
            color=bui.app.ui_v1.title_color,
            scale=1.4,
            maxwidth=600,
            v_align='center',
        )

        self._scroll_width = self._width - (130 + 2 * x_inset)
        self._scroll_height = self._height - 160
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(65 + x_inset, 70),
            size=(self._scroll_width, self._scroll_height),
            center_small_content=True,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._last_power_ranking_query_time: float | None = None
        self._doing_power_ranking_query = False

        self._subcontainer: bui.Widget | None = None
        self._subcontainerwidth = max(800, self._scroll_width)
        self._subcontainerheight = 483
        self._power_ranking_score_widgets: list[bui.Widget] = []

        self._season_popup_menu: PopupMenu | None = None
        self._requested_season: str | None = None
        self._season: str | None = None

        # take note of our account state; we'll refresh later if this changes
        self._account_state = plus.get_v1_account_state()

        self._refresh()
        self._restore_state()

        # if we've got cached power-ranking data already, display it
        assert bui.app.classic is not None
        info = bui.app.classic.accounts.get_cached_league_rank_data()
        if info is not None:
            self._update_for_league_rank_data(info)

        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update(show=info is None)

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _on_achievements_press(self) -> None:
        from bauiv1lib.achievements import AchievementsWindow

        # only allow this for all-time or the current season
        # (we currently don't keep specific achievement data for old seasons)
        if self._season == 'a' or self._is_current_season:
            prab = self._power_ranking_achievements_button
            assert prab is not None
            self.main_window_replace(AchievementsWindow(origin_widget=prab))
        else:
            bui.screenmessage(
                bui.Lstr(
                    resource='achievementsUnavailableForOldSeasonsText',
                    fallback_resource='unavailableText',
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()

    def _on_activity_mult_press(self) -> None:
        from bauiv1lib import confirm

        plus = bui.app.plus
        assert plus is not None

        txt = bui.Lstr(
            resource=(
                'coopSelectWindow.activenessAllTimeInfoText'
                if self._season == 'a'
                else 'coopSelectWindow.activenessInfoText'
            ),
            subs=[
                (
                    '${MAX}',
                    str(
                        plus.get_v1_account_misc_read_val('activenessMax', 1.0)
                    ),
                )
            ],
        )
        confirm.ConfirmWindow(
            txt,
            cancel_button=False,
            width=460,
            height=150,
            origin_widget=self._activity_mult_button,
        )

    def _on_pro_mult_press(self) -> None:
        from bauiv1lib import confirm

        plus = bui.app.plus
        assert plus is not None

        txt = bui.Lstr(
            resource='coopSelectWindow.proMultInfoText',
            subs=[
                (
                    '${PERCENT}',
                    str(
                        plus.get_v1_account_misc_read_val(
                            'proPowerRankingBoost', 10
                        )
                    ),
                ),
                (
                    '${PRO}',
                    bui.Lstr(
                        resource='store.bombSquadProNameText',
                        subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
                    ),
                ),
            ],
        )
        confirm.ConfirmWindow(
            txt,
            cancel_button=False,
            width=460,
            height=130,
            origin_widget=self._pro_mult_button,
        )

    def _on_trophies_press(self) -> None:
        from bauiv1lib.trophies import TrophiesWindow

        info = self._league_rank_data
        if info is not None:
            prtb = self._power_ranking_trophies_button
            assert prtb is not None
            TrophiesWindow(
                position=prtb.get_screen_space_center(),
                data=info,
            )
        else:
            bui.getsound('error').play()

    def _on_power_ranking_query_response(
        self, data: dict[str, Any] | None
    ) -> None:
        self._doing_power_ranking_query = False

        # Important: *only* cache this if we requested the current season.
        if data is not None and data.get('s', None) is None:
            assert bui.app.classic is not None
            bui.app.classic.accounts.cache_league_rank_data(data)

        # Always store a copy locally though (even for other seasons).
        self._league_rank_data = copy.deepcopy(data)
        self._update_for_league_rank_data(data)

    def _restore_state(self) -> None:
        pass

    def _update(self, show: bool = False) -> None:
        plus = bui.app.plus
        assert plus is not None

        cur_time = bui.apptime()

        # If our account state has changed, refresh our UI.
        account_state = plus.get_v1_account_state()
        if account_state != self._account_state:
            self._account_state = account_state
            self._save_state()
            self._refresh()

            # And power ranking too.
            if not self._doing_power_ranking_query:
                self._last_power_ranking_query_time = None

        # Send off a new power-ranking query if its been long enough or our
        # requested season has changed or whatnot.
        if not self._doing_power_ranking_query and (
            self._last_power_ranking_query_time is None
            or cur_time - self._last_power_ranking_query_time > 30.0
        ):
            try:
                if show:
                    bui.textwidget(edit=self._league_title_text, text='')
                    bui.textwidget(edit=self._league_text, text='')
                    bui.textwidget(edit=self._league_number_text, text='')
                    bui.textwidget(edit=self._your_power_ranking_text, text='')
                    bui.spinnerwidget(edit=self._loading_spinner, visible=True)
                    bui.textwidget(edit=self._to_ranked_text, text='')
                    bui.textwidget(edit=self._power_ranking_rank_text, text='')
                    bui.textwidget(edit=self._season_ends_text, text='')
                    bui.textwidget(edit=self._trophy_counts_reset_text, text='')
            except Exception:
                logging.exception('Error showing updated rank info.')

            self._last_power_ranking_query_time = cur_time
            self._doing_power_ranking_query = True
            plus.power_ranking_query(
                season=self._requested_season,
                callback=bui.WeakCall(self._on_power_ranking_query_response),
            )

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements

        plus = bui.app.plus
        assert plus is not None

        # (re)create the sub-container if need be..
        if self._subcontainer is not None:
            self._subcontainer.delete()
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._subcontainerwidth, self._subcontainerheight),
            background=False,
        )

        w_parent = self._subcontainer
        v = self._subcontainerheight - 20

        v -= 0

        h2 = 80
        v2 = v - 60
        worth_color = (0.6, 0.6, 0.65)
        tally_color = (0.5, 0.6, 0.8)
        spc = 43

        h_offs_tally = 150
        tally_maxwidth = 120
        v2 -= 70

        bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 - 60, v2 + 106),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text=bui.Lstr(resource='coopSelectWindow.pointsText'),
            h_align='left',
            v_align='center',
            scale=0.8,
            color=(1, 1, 1, 0.3),
            maxwidth=200,
        )

        self._power_ranking_achievements_button = bui.buttonwidget(
            parent=w_parent,
            position=(self._xoffs + h2 - 60, v2 + 10),
            size=(200, 80),
            icon=bui.gettexture('achievementsIcon'),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._on_achievements_press),
            up_widget=self._back_button,
            left_widget=self._back_button,
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
            label='',
        )

        self._power_ranking_achievement_total_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 + h_offs_tally, v2 + 45),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text='-',
            h_align='left',
            v_align='center',
            scale=0.8,
            color=tally_color,
            maxwidth=tally_maxwidth,
        )

        v2 -= 80

        self._power_ranking_trophies_button = bui.buttonwidget(
            parent=w_parent,
            position=(self._xoffs + h2 - 60, v2 + 10),
            size=(200, 80),
            icon=bui.gettexture('medalSilver'),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._on_trophies_press),
            left_widget=self._back_button,
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
            label='',
        )
        self._power_ranking_trophies_total_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 + h_offs_tally, v2 + 45),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text='-',
            h_align='left',
            v_align='center',
            scale=0.8,
            color=tally_color,
            maxwidth=tally_maxwidth,
        )

        v2 -= 100

        bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 - 60, v2 + 86),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text=bui.Lstr(resource='coopSelectWindow.multipliersText'),
            h_align='left',
            v_align='center',
            scale=0.8,
            color=(1, 1, 1, 0.3),
            maxwidth=200,
        )

        self._activity_mult_button: bui.Widget | None
        if plus.get_v1_account_misc_read_val('act', False):
            self._activity_mult_button = bui.buttonwidget(
                parent=w_parent,
                position=(self._xoffs + h2 - 60, v2 + 10),
                size=(200, 60),
                icon=bui.gettexture('heart'),
                icon_color=(0.5, 0, 0.5),
                label=bui.Lstr(resource='coopSelectWindow.activityText'),
                autoselect=True,
                on_activate_call=bui.WeakCall(self._on_activity_mult_press),
                left_widget=self._back_button,
                color=(0.5, 0.5, 0.6),
                textcolor=(0.7, 0.7, 0.8),
            )

            self._activity_mult_text = bui.textwidget(
                parent=w_parent,
                position=(self._xoffs + h2 + h_offs_tally, v2 + 40),
                size=(0, 0),
                flatness=1.0,
                shadow=0.0,
                text='-',
                h_align='left',
                v_align='center',
                scale=0.8,
                color=tally_color,
                maxwidth=tally_maxwidth,
            )
            v2 -= 65
        else:
            self._activity_mult_button = None

        self._pro_mult_button = bui.buttonwidget(
            parent=w_parent,
            position=(self._xoffs + h2 - 60, v2 + 10),
            size=(200, 60),
            icon=bui.gettexture('logo'),
            icon_color=(0.3, 0, 0.3),
            label=bui.Lstr(
                resource='store.bombSquadProNameText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._on_pro_mult_press),
            left_widget=self._back_button,
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
        )

        self._pro_mult_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 + h_offs_tally, v2 + 40),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text='-',
            h_align='left',
            v_align='center',
            scale=0.8,
            color=tally_color,
            maxwidth=tally_maxwidth,
        )
        v2 -= 30

        v2 -= spc
        bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 + h_offs_tally - 10 - 40, v2 + 35),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text=bui.Lstr(resource='finalScoreText'),
            h_align='right',
            v_align='center',
            scale=0.9,
            color=worth_color,
            maxwidth=150,
        )
        self._power_ranking_total_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + h2 + h_offs_tally - 40, v2 + 35),
            size=(0, 0),
            flatness=1.0,
            shadow=0.0,
            text='-',
            h_align='left',
            v_align='center',
            scale=0.9,
            color=tally_color,
            maxwidth=tally_maxwidth,
        )

        self._season_show_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 390 - 15, v - 20),
            size=(0, 0),
            color=(0.6, 0.6, 0.7),
            maxwidth=200,
            text=bui.Lstr(resource='showText'),
            h_align='right',
            v_align='center',
            scale=0.8,
            shadow=0,
            flatness=1.0,
        )

        self._league_title_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 97),
            size=(0, 0),
            color=(0.6, 0.6, 0.7),
            maxwidth=230,
            text='',
            h_align='center',
            v_align='center',
            scale=0.9,
            shadow=0,
            flatness=1.0,
        )

        self._league_text_scale = 1.8
        self._league_text_maxwidth = 210
        self._league_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 140),
            size=(0, 0),
            color=(1, 1, 1),
            maxwidth=self._league_text_maxwidth,
            text='-',
            h_align='center',
            v_align='center',
            scale=self._league_text_scale,
            shadow=1.0,
            flatness=1.0,
        )
        self._league_number_base_pos = (470, v - 140)
        self._league_number_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 140),
            size=(0, 0),
            color=(1, 1, 1),
            maxwidth=100,
            text='',
            h_align='left',
            v_align='center',
            scale=0.8,
            shadow=1.0,
            flatness=1.0,
        )

        self._loading_spinner = bui.spinnerwidget(
            parent=w_parent,
            position=(
                self._subcontainerwidth * 0.5,
                self._subcontainerheight * 0.5,
            ),
            size=64,
        )
        self._your_power_ranking_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 142 - 70),
            size=(0, 0),
            color=(0.6, 0.6, 0.7),
            maxwidth=230,
            text='',
            h_align='center',
            v_align='center',
            scale=0.9,
            shadow=0,
            flatness=1.0,
        )

        self._to_ranked_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 250 - 70),
            size=(0, 0),
            color=(0.6, 0.6, 0.7),
            maxwidth=230,
            text='',
            h_align='center',
            v_align='center',
            scale=0.8,
            shadow=0,
            flatness=1.0,
        )

        self._power_ranking_rank_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 473, v - 210 - 70),
            size=(0, 0),
            big=False,
            text='-',
            h_align='center',
            v_align='center',
            scale=1.0,
        )

        self._season_ends_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 380),
            size=(0, 0),
            color=(0.6, 0.6, 0.6),
            maxwidth=230,
            text='',
            h_align='center',
            v_align='center',
            scale=0.9,
            shadow=0,
            flatness=1.0,
        )
        self._trophy_counts_reset_text = bui.textwidget(
            parent=w_parent,
            position=(self._xoffs + 470, v - 410),
            size=(0, 0),
            color=(0.5, 0.5, 0.5),
            maxwidth=230,
            text='Trophy counts will reset next season.',
            h_align='center',
            v_align='center',
            scale=0.8,
            shadow=0,
            flatness=1.0,
        )

        self._power_ranking_score_widgets = []

        self._power_ranking_score_v = v - 56

        h = 707
        v -= 451

        self._see_more_button = bui.buttonwidget(
            parent=w_parent,
            label=self._rdict.seeMoreText,
            position=(self._xoffs + h, v),
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
            size=(230, 60),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._on_more_press),
        )

    def _on_more_press(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        our_login_id = plus.get_v1_account_public_login_id()
        # our_login_id = _bs.get_account_misc_read_val_2(
        #     'resolvedAccountID', None)
        if not self._can_do_more_button or our_login_id is None:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='unavailableText'), color=(1, 0, 0)
            )
            return
        if self._season is None:
            season_str = ''
        else:
            season_str = '&season=' + (
                'all_time' if self._season == 'a' else self._season
            )
        if self._league_url_arg != '':
            league_str = '&league=' + self._league_url_arg
        else:
            league_str = ''
        bui.open_url(
            plus.get_master_server_address()
            + '/highscores?list=powerRankings&v=2'
            + league_str
            + season_str
            + '&player='
            + our_login_id
        )

    def _update_for_league_rank_data(self, data: dict[str, Any] | None) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        if not self._root_widget:
            return
        plus = bui.app.plus
        uiscale = bui.app.ui_v1.uiscale
        assert plus is not None
        assert bui.app.classic is not None
        accounts = bui.app.classic.accounts
        in_top = data is not None and data['rank'] is not None
        eq_text = self._rdict.powerRankingPointsEqualsText
        pts_txt = self._rdict.powerRankingPointsText
        num_text = bui.Lstr(resource='numberText').evaluate()
        do_percent = False
        finished_season_unranked = False
        self._can_do_more_button = True
        extra_text = ''
        if plus.get_v1_account_state() != 'signed_in':
            status_text = (
                '(' + bui.Lstr(resource='notSignedInText').evaluate() + ')'
            )
        elif in_top:
            assert data is not None
            status_text = num_text.replace('${NUMBER}', str(data['rank']))
        elif data is not None:
            try:
                # handle old seasons where we didn't wind up ranked
                # at the end..
                if not data['scores']:
                    status_text = (
                        self._rdict.powerRankingFinishedSeasonUnrankedText
                    )
                    extra_text = ''
                    finished_season_unranked = True
                    self._can_do_more_button = False
                else:
                    our_points = accounts.get_league_rank_points(data)
                    progress = float(our_points) / max(1, data['scores'][-1][1])
                    status_text = str(int(progress * 100.0)) + '%'
                    extra_text = (
                        '\n'
                        + self._rdict.powerRankingPointsToRankedText.replace(
                            '${CURRENT}', str(our_points)
                        ).replace('${REMAINING}', str(data['scores'][-1][1]))
                    )
                    do_percent = True
            except Exception:
                logging.exception('Error updating power ranking.')
                status_text = self._rdict.powerRankingNotInTopText.replace(
                    '${NUMBER}', str(data['listSize'])
                )
                extra_text = ''
        else:
            status_text = '-'

        self._season = data['s'] if data is not None else None

        v = self._subcontainerheight - 20
        popup_was_selected = False
        if self._season_popup_menu is not None:
            btn = self._season_popup_menu.get_button()
            assert self._subcontainer
            if self._subcontainer.get_selected_child() == btn:
                popup_was_selected = True
            btn.delete()
        season_choices = []
        season_choices_display = []
        did_first = False
        self._is_current_season = False
        if data is not None:
            # build our list of seasons we have available
            for ssn in data['sl']:
                season_choices.append(ssn)
                if ssn != 'a' and not did_first:
                    season_choices_display.append(
                        bui.Lstr(
                            resource='league.currentSeasonText',
                            subs=[('${NUMBER}', ssn)],
                        )
                    )
                    did_first = True
                    # if we either did not specify a season or specified the
                    # first, we're looking at the current..
                    if self._season in [ssn, None]:
                        self._is_current_season = True
                elif ssn == 'a':
                    season_choices_display.append(
                        bui.Lstr(resource='league.allTimeText')
                    )
                else:
                    season_choices_display.append(
                        bui.Lstr(
                            resource='league.seasonText',
                            subs=[('${NUMBER}', ssn)],
                        )
                    )
            assert self._subcontainer
            self._season_popup_menu = PopupMenu(
                parent=self._subcontainer,
                position=(self._xoffs + 390, v - 45),
                width=150,
                button_size=(200, 50),
                choices=season_choices,
                on_value_change_call=bui.WeakCall(self._on_season_change),
                choices_display=season_choices_display,
                current_choice=self._season,
            )
            if popup_was_selected:
                bui.containerwidget(
                    edit=self._subcontainer,
                    selected_child=self._season_popup_menu.get_button(),
                )
            bui.widget(edit=self._see_more_button, show_buffer_bottom=100)
            bui.widget(
                edit=self._season_popup_menu.get_button(),
                up_widget=self._back_button,
            )
            if uiscale is not bui.UIScale.SMALL:
                bui.widget(
                    edit=self._back_button,
                    down_widget=self._power_ranking_achievements_button,
                    right_widget=self._season_popup_menu.get_button(),
                )

        bui.textwidget(
            edit=self._league_title_text,
            text=(
                ''
                if self._season == 'a'
                else bui.Lstr(resource='league.leagueText')
            ),
        )

        if data is None:
            lname = ''
            lnum = ''
            lcolor = (1, 1, 1)
            self._league_url_arg = ''
        elif self._season == 'a':
            lname = bui.Lstr(resource='league.allTimeText').evaluate()
            lnum = ''
            lcolor = (1, 1, 1)
            self._league_url_arg = ''
        else:
            lnum = ('[' + str(data['l']['i']) + ']') if data['l']['i2'] else ''
            lname = bui.Lstr(
                translate=('leagueNames', data['l']['n'])
            ).evaluate()
            lcolor = data['l']['c']
            self._league_url_arg = (
                data['l']['n'] + '_' + str(data['l']['i'])
            ).lower()

        to_end_string: bui.Lstr | str
        if data is None or self._season == 'a' or data['se'] is None:
            to_end_string = ''
            show_season_end = False
        else:
            show_season_end = True
            days_to_end = data['se'][0]
            minutes_to_end = data['se'][1]
            if days_to_end > 0:
                to_end_string = bui.Lstr(
                    resource='league.seasonEndsDaysText',
                    subs=[('${NUMBER}', str(days_to_end))],
                )
            elif days_to_end == 0 and minutes_to_end >= 60:
                to_end_string = bui.Lstr(
                    resource='league.seasonEndsHoursText',
                    subs=[('${NUMBER}', str(minutes_to_end // 60))],
                )
            elif days_to_end == 0 and minutes_to_end >= 0:
                to_end_string = bui.Lstr(
                    resource='league.seasonEndsMinutesText',
                    subs=[('${NUMBER}', str(minutes_to_end))],
                )
            else:
                to_end_string = bui.Lstr(
                    resource='league.seasonEndedDaysAgoText',
                    subs=[('${NUMBER}', str(-(days_to_end + 1)))],
                )

        bui.textwidget(edit=self._season_ends_text, text=to_end_string)
        bui.textwidget(
            edit=self._trophy_counts_reset_text,
            text=(
                bui.Lstr(resource='league.trophyCountsResetText')
                if self._is_current_season and show_season_end
                else ''
            ),
        )

        bui.textwidget(edit=self._league_text, text=lname, color=lcolor)
        l_text_width = min(
            self._league_text_maxwidth,
            bui.get_string_width(lname, suppress_warning=True)
            * self._league_text_scale,
        )
        bui.textwidget(
            edit=self._league_number_text,
            text=lnum,
            color=lcolor,
            position=(
                self._xoffs
                + self._league_number_base_pos[0]
                + l_text_width * 0.5
                + 8,
                self._league_number_base_pos[1] + 10,
            ),
        )
        bui.textwidget(
            edit=self._to_ranked_text,
            text=(
                bui.Lstr(resource='coopSelectWindow.toRankedText').evaluate()
                + ''
                + extra_text
                if do_percent
                else ''
            ),
        )

        bui.textwidget(
            edit=self._your_power_ranking_text,
            text=(
                bui.Lstr(
                    resource='rankText',
                    fallback_resource='coopSelectWindow.yourPowerRankingText',
                )
                if (not do_percent)
                else ''
            ),
        )
        bui.spinnerwidget(edit=self._loading_spinner, visible=False)

        bui.textwidget(
            edit=self._power_ranking_rank_text,
            position=(self._xoffs + 473, v - 70 - (170 if do_percent else 220)),
            text=status_text,
            big=(in_top or do_percent),
            scale=(
                3.0
                if (in_top or do_percent)
                else 0.7 if finished_season_unranked else 1.0
            ),
        )

        if self._activity_mult_button is not None:
            if data is None or data['act'] is None:
                bui.buttonwidget(
                    edit=self._activity_mult_button,
                    textcolor=(0.7, 0.7, 0.8, 0.5),
                    icon_color=(0.5, 0, 0.5, 0.3),
                )
                bui.textwidget(edit=self._activity_mult_text, text='     -')
            else:
                bui.buttonwidget(
                    edit=self._activity_mult_button,
                    textcolor=(0.7, 0.7, 0.8, 1.0),
                    icon_color=(0.5, 0, 0.5, 1.0),
                )
                # pylint: disable=consider-using-f-string
                bui.textwidget(
                    edit=self._activity_mult_text,
                    text='x ' + ('%.2f' % data['act']),
                )

        have_pro = False if data is None else data['p']
        pro_mult = (
            1.0
            + float(
                plus.get_v1_account_misc_read_val('proPowerRankingBoost', 0.0)
            )
            * 0.01
        )
        # pylint: disable=consider-using-f-string
        bui.textwidget(
            edit=self._pro_mult_text,
            text=(
                '     -'
                if (data is None or not have_pro)
                else 'x ' + ('%.2f' % pro_mult)
            ),
        )
        bui.buttonwidget(
            edit=self._pro_mult_button,
            textcolor=(0.7, 0.7, 0.8, (1.0 if have_pro else 0.5)),
            icon_color=(0.5, 0, 0.5) if have_pro else (0.5, 0, 0.5, 0.2),
        )
        bui.buttonwidget(
            edit=self._power_ranking_achievements_button,
            label=('' if data is None else str(data['a']) + ' ')
            + bui.Lstr(resource='achievementsText').evaluate(),
        )

        # for the achievement value, use the number they gave us for
        # non-current seasons; otherwise calc our own
        total_ach_value = 0
        for ach in bui.app.classic.ach.achievements:
            if ach.complete:
                total_ach_value += ach.power_ranking_value
        if self._season != 'a' and not self._is_current_season:
            if data is not None and 'at' in data:
                total_ach_value = data['at']

        bui.textwidget(
            edit=self._power_ranking_achievement_total_text,
            text=(
                '-'
                if data is None
                else ('+ ' + pts_txt.replace('${NUMBER}', str(total_ach_value)))
            ),
        )

        total_trophies_count = accounts.get_league_rank_points(
            data, 'trophyCount'
        )
        total_trophies_value = accounts.get_league_rank_points(data, 'trophies')
        bui.buttonwidget(
            edit=self._power_ranking_trophies_button,
            label=('' if data is None else str(total_trophies_count) + ' ')
            + bui.Lstr(resource='trophiesText').evaluate(),
        )
        bui.textwidget(
            edit=self._power_ranking_trophies_total_text,
            text=(
                '-'
                if data is None
                else (
                    '+ '
                    + pts_txt.replace('${NUMBER}', str(total_trophies_value))
                )
            ),
        )

        bui.textwidget(
            edit=self._power_ranking_total_text,
            text=(
                '-'
                if data is None
                else eq_text.replace(
                    '${NUMBER}', str(accounts.get_league_rank_points(data))
                )
            ),
        )
        for widget in self._power_ranking_score_widgets:
            widget.delete()
        self._power_ranking_score_widgets = []

        scores = data['scores'] if data is not None else []
        tally_color = (0.5, 0.6, 0.8)
        w_parent = self._subcontainer
        v2 = self._power_ranking_score_v

        for score in scores:
            h2 = 680
            is_us = score[3]
            self._power_ranking_score_widgets.append(
                bui.textwidget(
                    parent=w_parent,
                    position=(self._xoffs + h2 - 20, v2),
                    size=(0, 0),
                    color=(1, 1, 1) if is_us else (0.6, 0.6, 0.7),
                    maxwidth=40,
                    flatness=1.0,
                    shadow=0.0,
                    text=num_text.replace('${NUMBER}', str(score[0])),
                    h_align='right',
                    v_align='center',
                    scale=0.5,
                )
            )
            self._power_ranking_score_widgets.append(
                bui.textwidget(
                    parent=w_parent,
                    position=(self._xoffs + h2 + 20, v2),
                    size=(0, 0),
                    color=(1, 1, 1) if is_us else tally_color,
                    maxwidth=60,
                    text=str(score[1]),
                    flatness=1.0,
                    shadow=0.0,
                    h_align='center',
                    v_align='center',
                    scale=0.7,
                )
            )
            txt = bui.textwidget(
                parent=w_parent,
                position=(self._xoffs + h2 + 60, v2 - (28 * 0.5) / 0.9),
                size=(210 / 0.9, 28),
                color=(1, 1, 1) if is_us else (0.6, 0.6, 0.6),
                maxwidth=210,
                flatness=1.0,
                shadow=0.0,
                autoselect=True,
                selectable=True,
                click_activate=True,
                text=score[2],
                h_align='left',
                v_align='center',
                scale=0.9,
            )
            self._power_ranking_score_widgets.append(txt)
            bui.textwidget(
                edit=txt,
                on_activate_call=bui.Call(
                    self._show_account_info, score[4], txt
                ),
            )
            assert self._season_popup_menu is not None
            bui.widget(
                edit=txt, left_widget=self._season_popup_menu.get_button()
            )
            v2 -= 28

    def _show_account_info(
        self, account_id: str, textwidget: bui.Widget
    ) -> None:
        from bauiv1lib.account.viewer import AccountViewerWindow

        bui.getsound('swish').play()
        AccountViewerWindow(
            account_id=account_id, position=textwidget.get_screen_space_center()
        )

    def _on_season_change(self, value: str) -> None:
        self._requested_season = value
        self._last_power_ranking_query_time = None  # make sure we update asap
        self._update(show=True)

    def _save_state(self) -> None:
        pass
