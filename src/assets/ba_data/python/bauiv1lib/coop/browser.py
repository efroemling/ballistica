# Released under the MIT License. See LICENSE for details.
#
"""UI for browsing available co-op levels/games/etc."""
# FIXME: Break this up.
# pylint: disable=too-many-lines

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any

    from bauiv1lib.coop.tournamentbutton import TournamentButton

HARD_REQUIRES_PRO = False


class CoopBrowserWindow(bui.MainWindow):
    """Window for browsing co-op levels/games/etc."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import

        plus = bui.app.plus
        assert plus is not None

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        bui.set_analytics_screen('Coop Window')

        app = bui.app
        classic = app.classic
        assert classic is not None
        cfg = app.config

        # Quick note to players that tourneys won't work in ballistica
        # core builds. (need to split the word so it won't get subbed
        # out)
        if 'ballistica' + 'kit' == bui.appname() and bui.do_once():
            bui.apptimer(
                1.0,
                lambda: bui.screenmessage(
                    bui.Lstr(resource='noTournamentsInTestBuildText'),
                    color=(1, 1, 0),
                ),
            )

        # Try to recreate the same number of buttons we had last time so our
        # re-selection code works.
        self._tournament_button_count = app.config.get('Tournament Rows', 0)
        assert isinstance(self._tournament_button_count, int)

        self.star_tex = bui.gettexture('star')
        self.lsbt = bui.getmesh('level_select_button_transparent')
        self.lsbo = bui.getmesh('level_select_button_opaque')
        self.a_outline_tex = bui.gettexture('achievementOutline')
        self.a_outline_mesh = bui.getmesh('achievementOutline')
        self._campaign_sub_container: bui.Widget | None = None
        self._tournament_info_button: bui.Widget | None = None
        self._easy_button: bui.Widget | None = None
        self._hard_button: bui.Widget | None = None
        self._hard_button_lock_image: bui.Widget | None = None
        self._campaign_percent_text: bui.Widget | None = None

        uiscale = app.ui_v1.uiscale
        self._width = 1520 if uiscale is bui.UIScale.SMALL else 1120
        self._x_inset = x_inset = 200 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            585
            if uiscale is bui.UIScale.SMALL
            else 730 if uiscale is bui.UIScale.MEDIUM else 800
        )
        self._r = 'coopSelectWindow'
        top_extra = 0 if uiscale is bui.UIScale.SMALL else 0

        self._tourney_data_up_to_date = False

        self._campaign_difficulty = plus.get_v1_account_misc_val(
            'campaignDifficulty', 'easy'
        )

        if (
            self._campaign_difficulty == 'hard'
            and HARD_REQUIRES_PRO
            and not classic.accounts.have_pro_options()
        ):
            plus.add_v1_account_transaction(
                {
                    'type': 'SET_MISC_VAL',
                    'name': 'campaignDifficulty',
                    'value': 'easy',
                }
            )
            self._campaign_difficulty = 'easy'

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                toolbar_visibility='menu_full',
                stack_offset=(
                    (0, -8)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 0) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
                scale=(
                    1.31
                    if uiscale is bui.UIScale.SMALL
                    else 0.8 if uiscale is bui.UIScale.MEDIUM else 0.75
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
            self._back_button = bui.buttonwidget(
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
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 50),
                position=(
                    75 + x_inset,
                    self._height - 87 + 6,
                ),
                label=bui.charstr(bui.SpecialChar.BACK),
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        # self._league_rank_button: LeagueRankButton | None
        # self._store_button: StoreButton | None
        # self._store_button_widget: bui.Widget | None
        # self._league_rank_button_widget: bui.Widget | None

        # if not app.ui_v1.use_toolbars:
        #     prb = self._league_rank_button = LeagueRankButton(
        #         parent=self._root_widget,
        #         position=(
        #             self._width - (282 + x_inset),
        #             self._height
        #             - 85
        #             - (4 if uiscale is bui.UIScale.SMALL else 0),
        #         ),
        #         size=(100, 60),
        #         color=(0.4, 0.4, 0.9),
        #         textcolor=(0.9, 0.9, 2.0),
        #         scale=1.05,
        #         on_activate_call=bui.WeakCall(
        # self._switch_to_league_rankings),
        #     )
        #     self._league_rank_button_widget = prb.get_button()

        #     sbtn = self._store_button = StoreButton(
        #         parent=self._root_widget,
        #         position=(
        #             self._width - (170 + x_inset),
        #             self._height
        #             - 85
        #             - (4 if uiscale is bui.UIScale.SMALL else 0),
        #         ),
        #         size=(100, 60),
        #         color=(0.6, 0.4, 0.7),
        #         show_tickets=True,
        #         button_type='square',
        #         sale_scale=0.85,
        #         textcolor=(0.9, 0.7, 1.0),
        #         scale=1.05,
        #         on_activate_call=bui.WeakCall(self._switch_to_score, None),
        #     )
        #     self._store_button_widget = sbtn.get_button()
        #     assert self._back_button is not None
        #     bui.widget(
        #         edit=self._back_button,
        #         right_widget=self._league_rank_button_widget,
        #     )
        #     bui.widget(
        #         edit=self._league_rank_button_widget,
        #         left_widget=self._back_button,
        #     )
        # else:
        # self._league_rank_button = None
        # self._store_button = None
        # self._store_button_widget = None
        # self._league_rank_button_widget = None

        # Move our corner buttons dynamically to keep them out of the way of
        # the party icon :-(
        # self._update_corner_button_positions()
        # self._update_corner_button_positions_timer = bui.AppTimer(
        #     1.0, bui.WeakCall(
        # self._update_corner_button_positions), repeat=True
        # )

        self._last_tournament_query_time: float | None = None
        self._last_tournament_query_response_time: float | None = None
        self._doing_tournament_query = False

        self._selected_campaign_level = cfg.get(
            'Selected Coop Campaign Level', None
        )
        self._selected_custom_level = cfg.get(
            'Selected Coop Custom Level', None
        )

        # Don't want initial construction affecting our last-selected.
        self._do_selection_callbacks = False
        v = self._height - 95
        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                v + 40 - (25 if uiscale is bui.UIScale.SMALL else 0),
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource='playModes.singlePlayerCoopText',
                fallback_resource='playModes.coopText',
            ),
            h_align='center',
            color=app.ui_v1.title_color,
            scale=0.85 if uiscale is bui.UIScale.SMALL else 1.5,
            maxwidth=280 if uiscale is bui.UIScale.SMALL else 500,
            v_align='center',
        )

        self._selected_row = cfg.get('Selected Coop Row', None)

        self._scroll_width = self._width - (130 + 2 * x_inset)
        self._scroll_height = self._height - (
            # 219 if uiscale is bui.UIScale.SMALL else 160
            170
            if uiscale is bui.UIScale.SMALL
            else 160
        )

        self._subcontainerwidth = 800.0
        self._subcontainerheight = 1400.0

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(
                # (65 + x_inset, 120)
                (65 + x_inset, 70)
                if uiscale is bui.UIScale.SMALL
                else (65 + x_inset, 70)
            ),
            size=(self._scroll_width, self._scroll_height),
            simple_culling_v=10.0,
            claims_left_right=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )

        if uiscale is bui.UIScale.SMALL:
            bimg = bui.imagewidget(
                parent=self._root_widget,
                texture=bui.gettexture('uiAtlas'),
                mesh_transparent=bui.getmesh('windowBGBlotch'),
                position=(x_inset + 10.0, -20),
                size=(500.0, 200.0),
                color=(0.4, 0.37, 0.49),
                # color=(1, 0, 0),
            )
            bui.widget(edit=bimg, depth_range=(0.9, 1.0))
            bimg = bui.imagewidget(
                parent=self._root_widget,
                texture=bui.gettexture('uiAtlas'),
                mesh_transparent=bui.getmesh('windowBGBlotch'),
                position=(x_inset + self._scroll_width - 270, -20),
                size=(500.0, 200.0),
                color=(0.4, 0.37, 0.49),
                # color=(1, 0, 0),
            )
            bui.widget(edit=bimg, depth_range=(0.9, 1.0))

        self._subcontainer: bui.Widget | None = None

        # Take note of our account state; we'll refresh later if this changes.
        self._account_state_num = plus.get_v1_account_state_num()

        # Same for fg/bg state.
        self._fg_state = app.fg_state

        self._refresh()
        self._restore_state()

        # Even though we might display cached tournament data immediately, we
        # don't consider it valid until we've pinged.
        # the server for an update
        self._tourney_data_up_to_date = False

        # If we've got a cached tournament list for our account and info for
        # each one of those tournaments, go ahead and display it as a
        # starting point.
        if (
            classic.accounts.account_tournament_list is not None
            and classic.accounts.account_tournament_list[0]
            == plus.get_v1_account_state_num()
            and all(
                t_id in classic.accounts.tournament_info
                for t_id in classic.accounts.account_tournament_list[1]
            )
        ):
            tourney_data = [
                classic.accounts.tournament_info[t_id]
                for t_id in classic.accounts.account_tournament_list[1]
            ]
            self._update_for_data(tourney_data)

        # This will pull new data periodically, update timers, etc.
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

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

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use; avoids hitches (called in bg thread)."""
        # pylint: disable=cyclic-import
        import bauiv1lib.purchase as _unused1
        import bauiv1lib.coop.gamebutton as _unused2
        import bauiv1lib.confirm as _unused3
        import bauiv1lib.account as _unused4
        import bauiv1lib.league.rankwindow as _unused5
        import bauiv1lib.store.browser as _unused6
        import bauiv1lib.account.viewer as _unused7
        import bauiv1lib.tournamentscores as _unused8
        import bauiv1lib.tournamententry as _unused9
        import bauiv1lib.play as _unused10
        import bauiv1lib.coop.tournamentbutton as _unused11

    def _update(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # Do nothing if we've somehow outlived our actual UI.
        if not self._root_widget:
            return

        cur_time = bui.apptime()

        # If its been a while since we got a tournament update, consider
        # the data invalid (prevents us from joining tournaments if our
        # internet connection goes down for a while).
        if (
            self._last_tournament_query_response_time is None
            or bui.apptime() - self._last_tournament_query_response_time
            > 60.0 * 2
        ):
            self._tourney_data_up_to_date = False

        # If our account state has changed, do a full request.
        account_state_num = plus.get_v1_account_state_num()
        if account_state_num != self._account_state_num:
            self._account_state_num = account_state_num
            self._save_state()
            self._refresh()

            # Also encourage a new tournament query since this will clear out
            # our current results.
            if not self._doing_tournament_query:
                self._last_tournament_query_time = None

        # If we've been backgrounded/foregrounded, invalidate our
        # tournament entries (they will be refreshed below asap).
        if self._fg_state != bui.app.fg_state:
            self._tourney_data_up_to_date = False

        # Send off a new tournament query if its been long enough or whatnot.
        if not self._doing_tournament_query and (
            self._last_tournament_query_time is None
            or cur_time - self._last_tournament_query_time > 30.0
            or self._fg_state != bui.app.fg_state
        ):
            self._fg_state = bui.app.fg_state
            self._last_tournament_query_time = cur_time
            self._doing_tournament_query = True
            plus.tournament_query(
                args={'source': 'coop window refresh', 'numScores': 1},
                callback=bui.WeakCall(self._on_tournament_query_response),
            )

        # Decrement time on our tournament buttons.
        ads_enabled = plus.have_incentivized_ad()
        for tbtn in self._tournament_buttons:
            tbtn.time_remaining = max(0, tbtn.time_remaining - 1)
            if tbtn.time_remaining_value_text is not None:
                bui.textwidget(
                    edit=tbtn.time_remaining_value_text,
                    text=(
                        bui.timestring(tbtn.time_remaining, centi=False)
                        if (
                            tbtn.has_time_remaining
                            and self._tourney_data_up_to_date
                        )
                        else '-'
                    ),
                )

            # Also adjust the ad icon visibility.
            if tbtn.allow_ads and plus.has_video_ads():
                bui.imagewidget(
                    edit=tbtn.entry_fee_ad_image,
                    opacity=1.0 if ads_enabled else 0.25,
                )
                bui.textwidget(
                    edit=tbtn.entry_fee_text_remaining,
                    color=(0.6, 0.6, 0.6, 1 if ads_enabled else 0.2),
                )

        self._update_hard_mode_lock_image()

    def _update_hard_mode_lock_image(self) -> None:
        assert bui.app.classic is not None
        try:
            bui.imagewidget(
                edit=self._hard_button_lock_image,
                opacity=(
                    0.0
                    if (
                        (not HARD_REQUIRES_PRO)
                        or bui.app.classic.accounts.have_pro_options()
                    )
                    else 1.0
                ),
            )
        except Exception:
            logging.exception('Error updating campaign lock.')

    def _update_for_data(self, data: list[dict[str, Any]] | None) -> None:
        # If the number of tournaments or challenges in the data differs
        # from our current arrangement, refresh with the new number.
        if (data is None and self._tournament_button_count != 0) or (
            data is not None and (len(data) != self._tournament_button_count)
        ):
            self._tournament_button_count = len(data) if data is not None else 0
            bui.app.config['Tournament Rows'] = self._tournament_button_count
            self._refresh()

        # Update all of our tourney buttons based on whats in data.
        for i, tbtn in enumerate(self._tournament_buttons):
            assert data is not None
            tbtn.update_for_data(data[i])

    def _on_tournament_query_response(
        self, data: dict[str, Any] | None
    ) -> None:
        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        accounts = bui.app.classic.accounts
        if data is not None:
            tournament_data = data['t']  # This used to be the whole payload.
            self._last_tournament_query_response_time = bui.apptime()
        else:
            tournament_data = None

        # Keep our cached tourney info up to date.
        if data is not None:
            self._tourney_data_up_to_date = True
            accounts.cache_tournament_info(tournament_data)

            # Also cache the current tourney list/order for this account.
            accounts.account_tournament_list = (
                plus.get_v1_account_state_num(),
                [e['tournamentID'] for e in tournament_data],
            )

        self._doing_tournament_query = False
        self._update_for_data(tournament_data)

    def _set_campaign_difficulty(self, difficulty: str) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        if difficulty != self._campaign_difficulty:
            if (
                difficulty == 'hard'
                and HARD_REQUIRES_PRO
                and not bui.app.classic.accounts.have_pro_options()
            ):
                PurchaseWindow(items=['pro'])
                return
            bui.getsound('gunCocking').play()
            if difficulty not in ('easy', 'hard'):
                print('ERROR: invalid campaign difficulty:', difficulty)
                difficulty = 'easy'
            self._campaign_difficulty = difficulty
            plus.add_v1_account_transaction(
                {
                    'type': 'SET_MISC_VAL',
                    'name': 'campaignDifficulty',
                    'value': difficulty,
                }
            )
            self._refresh_campaign_row()
        else:
            bui.getsound('click01').play()

    def _refresh_campaign_row(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from bauiv1lib.coop.gamebutton import GameButton

        parent_widget = self._campaign_sub_container

        # Clear out anything in the parent widget already.
        assert parent_widget is not None
        for child in parent_widget.get_children():
            child.delete()

        next_widget_down = self._tournament_info_button

        h = 0
        v2 = -2
        sel_color = (0.75, 0.85, 0.5)
        sel_color_hard = (0.4, 0.7, 0.2)
        un_sel_color = (0.5, 0.5, 0.5)
        sel_textcolor = (2, 2, 0.8)
        un_sel_textcolor = (0.6, 0.6, 0.6)
        self._easy_button = bui.buttonwidget(
            parent=parent_widget,
            position=(h + 30, v2 + 105),
            size=(120, 70),
            label=bui.Lstr(resource='difficultyEasyText'),
            button_type='square',
            autoselect=True,
            enable_sound=False,
            on_activate_call=bui.Call(self._set_campaign_difficulty, 'easy'),
            on_select_call=bui.Call(self.sel_change, 'campaign', 'easyButton'),
            color=(
                sel_color
                if self._campaign_difficulty == 'easy'
                else un_sel_color
            ),
            textcolor=(
                sel_textcolor
                if self._campaign_difficulty == 'easy'
                else un_sel_textcolor
            ),
        )
        bui.widget(edit=self._easy_button, show_buffer_left=100)
        if self._selected_campaign_level == 'easyButton':
            bui.containerwidget(
                edit=parent_widget,
                selected_child=self._easy_button,
                visible_child=self._easy_button,
            )
        lock_tex = bui.gettexture('lock')

        self._hard_button = bui.buttonwidget(
            parent=parent_widget,
            position=(h + 30, v2 + 32),
            size=(120, 70),
            label=bui.Lstr(resource='difficultyHardText'),
            button_type='square',
            autoselect=True,
            enable_sound=False,
            on_activate_call=bui.Call(self._set_campaign_difficulty, 'hard'),
            on_select_call=bui.Call(self.sel_change, 'campaign', 'hardButton'),
            color=(
                sel_color_hard
                if self._campaign_difficulty == 'hard'
                else un_sel_color
            ),
            textcolor=(
                sel_textcolor
                if self._campaign_difficulty == 'hard'
                else un_sel_textcolor
            ),
        )
        self._hard_button_lock_image = bui.imagewidget(
            parent=parent_widget,
            size=(30, 30),
            draw_controller=self._hard_button,
            position=(h + 30 - 10, v2 + 32 + 70 - 35),
            texture=lock_tex,
        )
        self._update_hard_mode_lock_image()
        bui.widget(edit=self._hard_button, show_buffer_left=100)
        if self._selected_campaign_level == 'hardButton':
            bui.containerwidget(
                edit=parent_widget,
                selected_child=self._hard_button,
                visible_child=self._hard_button,
            )

        bui.widget(edit=self._hard_button, down_widget=next_widget_down)
        h_spacing = 200
        campaign_buttons = []
        if self._campaign_difficulty == 'easy':
            campaignname = 'Easy'
        else:
            campaignname = 'Default'
        items = [
            campaignname + ':Onslaught Training',
            campaignname + ':Rookie Onslaught',
            campaignname + ':Rookie Football',
            campaignname + ':Pro Onslaught',
            campaignname + ':Pro Football',
            campaignname + ':Pro Runaround',
            campaignname + ':Uber Onslaught',
            campaignname + ':Uber Football',
            campaignname + ':Uber Runaround',
        ]
        items += [campaignname + ':The Last Stand']
        if self._selected_campaign_level is None:
            self._selected_campaign_level = items[0]
        h = 150
        for i in items:
            is_last_sel = i == self._selected_campaign_level
            campaign_buttons.append(
                GameButton(
                    self, parent_widget, i, h, v2, is_last_sel, 'campaign'
                ).get_button()
            )
            h += h_spacing

        bui.widget(edit=campaign_buttons[0], left_widget=self._easy_button)

        # bui.widget(edit=self._easy_button)
        # if self._back_button is not None:
        bui.widget(
            edit=self._easy_button,
            left_widget=self._back_button,
            up_widget=self._back_button,
        )
        bui.widget(edit=self._hard_button, left_widget=self._back_button)
        for btn in campaign_buttons:
            bui.widget(
                edit=btn,
                up_widget=self._back_button,
            )
        for btn in campaign_buttons:
            bui.widget(edit=btn, down_widget=next_widget_down)

        # Update our existing percent-complete text.
        assert bui.app.classic is not None
        campaign = bui.app.classic.getcampaign(campaignname)
        levels = campaign.levels
        levels_complete = sum((1 if l.complete else 0) for l in levels)

        # Last level cant be completed; hence the -1.
        progress = min(1.0, float(levels_complete) / (len(levels) - 1))
        p_str = str(int(progress * 100.0)) + '%'

        self._campaign_percent_text = bui.textwidget(
            edit=self._campaign_percent_text,
            text=bui.Lstr(
                value='${C} (${P})',
                subs=[
                    ('${C}', bui.Lstr(resource=f'{self._r}.campaignText')),
                    ('${P}', p_str),
                ],
            ),
        )

    def _on_tournament_info_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        txt = bui.Lstr(resource=f'{self._r}.tournamentInfoText')
        ConfirmWindow(
            txt,
            cancel_button=False,
            width=550,
            height=260,
            origin_widget=self._tournament_info_button,
        )

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bauiv1lib.coop.gamebutton import GameButton
        from bauiv1lib.coop.tournamentbutton import TournamentButton

        plus = bui.app.plus
        assert plus is not None
        assert bui.app.classic is not None

        # (Re)create the sub-container if need be.
        if self._subcontainer is not None:
            self._subcontainer.delete()

        tourney_row_height = 200
        self._subcontainerheight = (
            700 + self._tournament_button_count * tourney_row_height
        )

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._subcontainerwidth, self._subcontainerheight),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )

        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

        w_parent = self._subcontainer
        h_base = 6

        v = self._subcontainerheight - 90

        self._campaign_percent_text = bui.textwidget(
            parent=w_parent,
            position=(h_base + 27, v + 30),
            size=(0, 0),
            text='',
            h_align='left',
            v_align='center',
            color=bui.app.ui_v1.title_color,
            scale=1.1,
        )

        row_v_show_buffer = 80
        v -= 198

        h_scroll = bui.hscrollwidget(
            parent=w_parent,
            size=(self._scroll_width, 205),
            position=(-5, v),
            simple_culling_h=70,
            highlight=False,
            border_opacity=0.0,
            color=(0.45, 0.4, 0.5),
            on_select_call=lambda: self._on_row_selected('campaign'),
        )
        self._campaign_h_scroll = h_scroll
        bui.widget(
            edit=h_scroll,
            show_buffer_top=row_v_show_buffer,
            show_buffer_bottom=row_v_show_buffer,
            autoselect=True,
        )
        if self._selected_row == 'campaign':
            bui.containerwidget(
                edit=w_parent, selected_child=h_scroll, visible_child=h_scroll
            )
        bui.containerwidget(edit=h_scroll, claims_left_right=True)
        self._campaign_sub_container = bui.containerwidget(
            parent=h_scroll, size=(180 + 200 * 10, 200), background=False
        )

        # Tournaments

        self._tournament_buttons: list[TournamentButton] = []

        v -= 53
        # FIXME shouldn't use hard-coded strings here.
        txt = bui.Lstr(
            resource='tournamentsText', fallback_resource='tournamentText'
        ).evaluate()
        t_width = bui.get_string_width(txt, suppress_warning=True)
        bui.textwidget(
            parent=w_parent,
            position=(h_base + 27, v + 30),
            size=(0, 0),
            text=txt,
            h_align='left',
            v_align='center',
            color=bui.app.ui_v1.title_color,
            scale=1.1,
        )
        self._tournament_info_button = bui.buttonwidget(
            parent=w_parent,
            label='?',
            size=(20, 20),
            text_scale=0.6,
            position=(h_base + 27 + t_width * 1.1 + 15, v + 18),
            button_type='square',
            color=(0.6, 0.5, 0.65),
            textcolor=(0.7, 0.6, 0.75),
            autoselect=True,
            up_widget=self._campaign_h_scroll,
            left_widget=self._back_button,
            on_activate_call=self._on_tournament_info_press,
        )
        bui.widget(
            edit=self._tournament_info_button,
            right_widget=self._tournament_info_button,
        )

        # Say 'unavailable' if there are zero tournaments, and if we're
        # not signed in add that as well (that's probably why we see no
        # tournaments).
        if self._tournament_button_count == 0:
            unavailable_text = bui.Lstr(resource='unavailableText')
            if plus.get_v1_account_state() != 'signed_in':
                unavailable_text = bui.Lstr(
                    value='${A} (${B})',
                    subs=[
                        ('${A}', unavailable_text),
                        ('${B}', bui.Lstr(resource='notSignedInText')),
                    ],
                )
            bui.textwidget(
                parent=w_parent,
                position=(h_base + 47, v),
                size=(0, 0),
                text=unavailable_text,
                h_align='left',
                v_align='center',
                color=bui.app.ui_v1.title_color,
                scale=0.9,
            )
            v -= 40
        v -= 198

        tournament_h_scroll = None
        if self._tournament_button_count > 0:
            for i in range(self._tournament_button_count):
                tournament_h_scroll = h_scroll = bui.hscrollwidget(
                    parent=w_parent,
                    size=(self._scroll_width, 205),
                    position=(-5, v),
                    highlight=False,
                    border_opacity=0.0,
                    color=(0.45, 0.4, 0.5),
                    on_select_call=bui.Call(
                        self._on_row_selected, 'tournament' + str(i + 1)
                    ),
                )
                bui.widget(
                    edit=h_scroll,
                    show_buffer_top=row_v_show_buffer,
                    show_buffer_bottom=row_v_show_buffer,
                    autoselect=True,
                )
                if self._selected_row == 'tournament' + str(i + 1):
                    bui.containerwidget(
                        edit=w_parent,
                        selected_child=h_scroll,
                        visible_child=h_scroll,
                    )
                bui.containerwidget(edit=h_scroll, claims_left_right=True)
                sc2 = bui.containerwidget(
                    parent=h_scroll,
                    size=(self._scroll_width - 24, 200),
                    background=False,
                )
                h = 0
                v2 = -2
                is_last_sel = True
                self._tournament_buttons.append(
                    TournamentButton(
                        sc2,
                        h,
                        v2,
                        is_last_sel,
                        on_pressed=bui.WeakCall(self.run_tournament),
                    )
                )
                v -= 200

        # Custom Games. (called 'Practice' in UI these days).
        v -= 50
        bui.textwidget(
            parent=w_parent,
            position=(h_base + 27, v + 30 + 198),
            size=(0, 0),
            text=bui.Lstr(
                resource='practiceText',
                fallback_resource='coopSelectWindow.customText',
            ),
            h_align='left',
            v_align='center',
            color=bui.app.ui_v1.title_color,
            scale=1.1,
        )

        items = [
            'Challenges:Infinite Onslaught',
            'Challenges:Infinite Runaround',
            'Challenges:Ninja Fight',
            'Challenges:Pro Ninja Fight',
            'Challenges:Meteor Shower',
            'Challenges:Target Practice B',
            'Challenges:Target Practice',
        ]

        # Show easter-egg-hunt either if its easter or we own it.
        if plus.get_v1_account_misc_read_val(
            'easter', False
        ) or plus.get_v1_account_product_purchased('games.easter_egg_hunt'):
            items = [
                'Challenges:Easter Egg Hunt',
                'Challenges:Pro Easter Egg Hunt',
            ] + items

        # If we've defined custom games, put them at the beginning.
        if bui.app.classic.custom_coop_practice_games:
            items = bui.app.classic.custom_coop_practice_games + items

        self._custom_h_scroll = custom_h_scroll = h_scroll = bui.hscrollwidget(
            parent=w_parent,
            size=(self._scroll_width, 205),
            position=(-5, v),
            highlight=False,
            border_opacity=0.0,
            color=(0.45, 0.4, 0.5),
            on_select_call=bui.Call(self._on_row_selected, 'custom'),
        )
        bui.widget(
            edit=h_scroll,
            show_buffer_top=row_v_show_buffer,
            show_buffer_bottom=1.5 * row_v_show_buffer,
            autoselect=True,
        )
        if self._selected_row == 'custom':
            bui.containerwidget(
                edit=w_parent, selected_child=h_scroll, visible_child=h_scroll
            )
        bui.containerwidget(edit=h_scroll, claims_left_right=True)
        sc2 = bui.containerwidget(
            parent=h_scroll,
            size=(max(self._scroll_width - 24, 30 + 200 * len(items)), 200),
            background=False,
        )
        h_spacing = 200
        self._custom_buttons: list[GameButton] = []
        h = 0
        v2 = -2
        for item in items:
            is_last_sel = item == self._selected_custom_level
            self._custom_buttons.append(
                GameButton(self, sc2, item, h, v2, is_last_sel, 'custom')
            )
            h += h_spacing

        # We can't fill in our campaign row until tourney buttons are in place.
        # (for wiring up)
        self._refresh_campaign_row()

        for i, tbutton in enumerate(self._tournament_buttons):
            bui.widget(
                edit=tbutton.button,
                up_widget=(
                    self._tournament_info_button
                    if i == 0
                    else self._tournament_buttons[i - 1].button
                ),
                down_widget=(
                    self._tournament_buttons[(i + 1)].button
                    if i + 1 < len(self._tournament_buttons)
                    else custom_h_scroll
                ),
                left_widget=self._back_button,
            )
            bui.widget(
                edit=tbutton.more_scores_button,
                down_widget=(
                    self._tournament_buttons[(i + 1)].current_leader_name_text
                    if i + 1 < len(self._tournament_buttons)
                    else custom_h_scroll
                ),
            )
            bui.widget(
                edit=tbutton.current_leader_name_text,
                up_widget=(
                    self._tournament_info_button
                    if i == 0
                    else self._tournament_buttons[i - 1].more_scores_button
                ),
            )

        for i, btn in enumerate(self._custom_buttons):
            try:
                bui.widget(
                    edit=btn.get_button(),
                    up_widget=(
                        tournament_h_scroll
                        if self._tournament_buttons
                        else self._tournament_info_button
                    ),
                )
                if i == 0:
                    bui.widget(
                        edit=btn.get_button(), left_widget=self._back_button
                    )

            except Exception:
                logging.exception('Error wiring up custom buttons.')

        # There's probably several 'onSelected' callbacks pushed onto the
        # event queue.. we need to push ours too so we're enabled *after* them.
        bui.pushcall(self._enable_selectable_callback)

    def _on_row_selected(self, row: str) -> None:
        if self._do_selection_callbacks:
            if self._selected_row != row:
                self._selected_row = row

    def _enable_selectable_callback(self) -> None:
        self._do_selection_callbacks = True

    def is_tourney_data_up_to_date(self) -> bool:
        """Return whether our tourney data is up to date."""
        return self._tourney_data_up_to_date

    def run_game(self, game: str) -> None:
        """Run the provided game."""
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow
        from bauiv1lib.purchase import PurchaseWindow
        from bauiv1lib.account.signin import show_sign_in_prompt

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None

        args: dict[str, Any] = {}

        if game == 'Easy:The Last Stand':
            ConfirmWindow(
                bui.Lstr(
                    resource='difficultyHardUnlockOnlyText',
                    fallback_resource='difficultyHardOnlyText',
                ),
                cancel_button=False,
                width=460,
                height=130,
            )
            return

        # Infinite onslaught/runaround require pro; bring up a store link
        # if need be.
        if (
            game
            in (
                'Challenges:Infinite Runaround',
                'Challenges:Infinite Onslaught',
            )
            and not bui.app.classic.accounts.have_pro()
        ):
            if plus.get_v1_account_state() != 'signed_in':
                show_sign_in_prompt()
            else:
                PurchaseWindow(items=['pro'])
            return

        required_purchase: str | None
        if game in ['Challenges:Meteor Shower']:
            required_purchase = 'games.meteor_shower'
        elif game in [
            'Challenges:Target Practice',
            'Challenges:Target Practice B',
        ]:
            required_purchase = 'games.target_practice'
        elif game in ['Challenges:Ninja Fight']:
            required_purchase = 'games.ninja_fight'
        elif game in ['Challenges:Pro Ninja Fight']:
            required_purchase = 'games.ninja_fight'
        elif game in [
            'Challenges:Easter Egg Hunt',
            'Challenges:Pro Easter Egg Hunt',
        ]:
            required_purchase = 'games.easter_egg_hunt'
        else:
            required_purchase = None

        if (
            required_purchase is not None
            and not plus.get_v1_account_product_purchased(required_purchase)
        ):
            if plus.get_v1_account_state() != 'signed_in':
                show_sign_in_prompt()
            else:
                PurchaseWindow(items=[required_purchase])
            return

        self._save_state()

        if bui.app.classic.launch_coop_game(game, args=args):
            bui.containerwidget(edit=self._root_widget, transition='out_left')

    def run_tournament(self, tournament_button: TournamentButton) -> None:
        """Run the provided tournament game."""
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.tournamententry import TournamentEntryWindow

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        if bui.workspaces_in_use():
            bui.screenmessage(
                bui.Lstr(resource='tournamentsDisabledWorkspaceText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        if not self._tourney_data_up_to_date:
            bui.screenmessage(
                bui.Lstr(resource='tournamentCheckingStateText'),
                color=(1, 1, 0),
            )
            bui.getsound('error').play()
            return

        if tournament_button.tournament_id is None:
            bui.screenmessage(
                bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        if tournament_button.required_league is not None:
            bui.screenmessage(
                bui.Lstr(
                    resource='league.tournamentLeagueText',
                    subs=[
                        (
                            '${NAME}',
                            bui.Lstr(
                                translate=(
                                    'leagueNames',
                                    tournament_button.required_league,
                                )
                            ),
                        )
                    ],
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        if tournament_button.time_remaining <= 0:
            bui.screenmessage(
                bui.Lstr(resource='tournamentEndedText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        self._save_state()

        assert tournament_button.tournament_id is not None
        TournamentEntryWindow(
            tournament_id=tournament_button.tournament_id,
            position=tournament_button.button.get_screen_space_center(),
        )

    def _save_state(self) -> None:
        cfg = bui.app.config
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._back_button:
                sel_name = 'Back'
            # elif sel == self._store_button_widget:
            #     sel_name = 'Store'
            # elif sel == self._league_rank_button_widget:
            #     sel_name = 'PowerRanking'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            else:
                raise ValueError('unrecognized selection')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}
        except Exception:
            logging.exception('Error saving state for %s.', self)

        cfg['Selected Coop Row'] = self._selected_row
        cfg['Selected Coop Custom Level'] = self._selected_custom_level
        cfg['Selected Coop Campaign Level'] = self._selected_campaign_level
        cfg.commit()

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            # elif sel_name == 'PowerRanking':
            #     sel = self._league_rank_button_widget
            # elif sel_name == 'Store':
            #     sel = self._store_button_widget
            else:
                sel = self._scrollwidget
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)

    def sel_change(self, row: str, game: str) -> None:
        """(internal)"""
        if self._do_selection_callbacks:
            if row == 'custom':
                self._selected_custom_level = game
            elif row == 'campaign':
                self._selected_campaign_level = game
