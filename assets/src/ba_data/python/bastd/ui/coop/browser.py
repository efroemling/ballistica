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
"""UI for browsing available co-op levels/games/etc."""
# FIXME: Break this up.
# pylint: disable=too-many-lines

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui.store.button import StoreButton
from bastd.ui.league.rankbutton import LeagueRankButton

if TYPE_CHECKING:
    from typing import Any, Optional, Tuple, Dict, List, Union


class CoopBrowserWindow(ba.Window):
    """Window for browsing co-op levels/games/etc."""

    def _update_corner_button_positions(self) -> None:
        uiscale = ba.app.ui.uiscale
        offs = (-55 if uiscale is ba.UIScale.SMALL
                and _ba.is_party_icon_visible() else 0)
        if self._league_rank_button is not None:
            self._league_rank_button.set_position(
                (self._width - 282 + offs - self._x_inset, self._height - 85 -
                 (4 if uiscale is ba.UIScale.SMALL else 0)))
        if self._store_button is not None:
            self._store_button.set_position(
                (self._width - 170 + offs - self._x_inset, self._height - 85 -
                 (4 if uiscale is ba.UIScale.SMALL else 0)))

    def __init__(self,
                 transition: Optional[str] = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        import threading

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        ba.set_analytics_screen('Coop Window')

        app = ba.app
        cfg = app.config

        # Quick note to players that tourneys won't work in ballistica
        # core builds. (need to split the word so it won't get subbed out)
        if 'ballistica' + 'core' == _ba.appname():
            ba.timer(1.0,
                     lambda: ba.screenmessage(
                         ba.Lstr(resource='noTournamentsInTestBuildText'),
                         color=(1, 1, 0),
                     ),
                     timetype=ba.TimeType.REAL)

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        # Try to recreate the same number of buttons we had last time so our
        # re-selection code works.
        self._tournament_button_count = app.config.get('Tournament Rows', 0)
        assert isinstance(self._tournament_button_count, int)

        self._easy_button: Optional[ba.Widget] = None
        self._hard_button: Optional[ba.Widget] = None
        self._hard_button_lock_image: Optional[ba.Widget] = None
        self._campaign_percent_text: Optional[ba.Widget] = None

        uiscale = ba.app.ui.uiscale
        self._width = 1320 if uiscale is ba.UIScale.SMALL else 1120
        self._x_inset = x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (657 if uiscale is ba.UIScale.SMALL else
                        730 if uiscale is ba.UIScale.MEDIUM else 800)
        app.ui.set_main_menu_location('Coop Select')
        self._r = 'coopSelectWindow'
        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0

        self._tourney_data_up_to_date = False

        self._campaign_difficulty = _ba.get_account_misc_val(
            'campaignDifficulty', 'easy')

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            toolbar_visibility='menu_full',
            scale_origin_stack_offset=scale_origin,
            stack_offset=((0, -15) if uiscale is ba.UIScale.SMALL else (
                0, 0) if uiscale is ba.UIScale.MEDIUM else (0, 0)),
            transition=transition,
            scale=(1.2 if uiscale is ba.UIScale.SMALL else
                   0.8 if uiscale is ba.UIScale.MEDIUM else 0.75)))

        if app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            self._back_button = None
        else:
            self._back_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(75 + x_inset, self._height - 87 -
                          (4 if uiscale is ba.UIScale.SMALL else 0)),
                size=(120, 60),
                scale=1.2,
                autoselect=True,
                label=ba.Lstr(resource='backText'),
                button_type='back')

        self._league_rank_button: Optional[LeagueRankButton]
        self._store_button: Optional[StoreButton]
        self._store_button_widget: Optional[ba.Widget]
        self._league_rank_button_widget: Optional[ba.Widget]

        if not app.ui.use_toolbars:
            prb = self._league_rank_button = LeagueRankButton(
                parent=self._root_widget,
                position=(self._width - (282 + x_inset), self._height - 85 -
                          (4 if uiscale is ba.UIScale.SMALL else 0)),
                size=(100, 60),
                color=(0.4, 0.4, 0.9),
                textcolor=(0.9, 0.9, 2.0),
                scale=1.05,
                on_activate_call=ba.WeakCall(self._switch_to_league_rankings))
            self._league_rank_button_widget = prb.get_button()

            sbtn = self._store_button = StoreButton(
                parent=self._root_widget,
                position=(self._width - (170 + x_inset), self._height - 85 -
                          (4 if uiscale is ba.UIScale.SMALL else 0)),
                size=(100, 60),
                color=(0.6, 0.4, 0.7),
                show_tickets=True,
                button_type='square',
                sale_scale=0.85,
                textcolor=(0.9, 0.7, 1.0),
                scale=1.05,
                on_activate_call=ba.WeakCall(self._switch_to_score, None))
            self._store_button_widget = sbtn.get_button()
            ba.widget(edit=self._back_button,
                      right_widget=self._league_rank_button_widget)
            ba.widget(edit=self._league_rank_button_widget,
                      left_widget=self._back_button)
        else:
            self._league_rank_button = None
            self._store_button = None
            self._store_button_widget = None
            self._league_rank_button_widget = None

        # Move our corner buttons dynamically to keep them out of the way of
        # the party icon :-(
        self._update_corner_button_positions()
        self._update_corner_button_positions_timer = ba.Timer(
            1.0,
            ba.WeakCall(self._update_corner_button_positions),
            repeat=True,
            timetype=ba.TimeType.REAL)

        self._last_tournament_query_time: Optional[float] = None
        self._last_tournament_query_response_time: Optional[float] = None
        self._doing_tournament_query = False

        self._selected_campaign_level = (cfg.get(
            'Selected Coop Campaign Level', None))
        self._selected_custom_level = (cfg.get('Selected Coop Custom Level',
                                               None))
        self._selected_challenge_level = (cfg.get(
            'Selected Coop Challenge Level', None))

        # Don't want initial construction affecting our last-selected.
        self._do_selection_callbacks = False
        v = self._height - 95
        txt = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5,
                      v + 40 - (0 if uiscale is ba.UIScale.SMALL else 0)),
            size=(0, 0),
            text=ba.Lstr(resource='playModes.singlePlayerCoopText',
                         fallback_resource='playModes.coopText'),
            h_align='center',
            color=app.ui.title_color,
            scale=1.5,
            maxwidth=500,
            v_align='center')

        if app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            ba.textwidget(edit=txt, text='')

        if self._back_button is not None:
            ba.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 50),
                position=(75 + x_inset, self._height - 87 -
                          (4 if uiscale is ba.UIScale.SMALL else 0) + 6),
                label=ba.charstr(ba.SpecialChar.BACK))

        self._selected_row = cfg.get('Selected Coop Row', None)

        self.star_tex = ba.gettexture('star')
        self.lsbt = ba.getmodel('level_select_button_transparent')
        self.lsbo = ba.getmodel('level_select_button_opaque')
        self.a_outline_tex = ba.gettexture('achievementOutline')
        self.a_outline_model = ba.getmodel('achievementOutline')

        self._scroll_width = self._width - (130 + 2 * x_inset)
        self._scroll_height = (self._height -
                               (190 if uiscale is ba.UIScale.SMALL
                                and app.ui.use_toolbars else 160))

        self._subcontainerwidth = 800.0
        self._subcontainerheight = 1400.0

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(65 + x_inset, 120) if uiscale is ba.UIScale.SMALL
            and app.ui.use_toolbars else (65 + x_inset, 70),
            size=(self._scroll_width, self._scroll_height),
            simple_culling_v=10.0,
            claims_left_right=True,
            claims_tab=True,
            selection_loops_to_parent=True)
        self._subcontainer: Optional[ba.Widget] = None

        # Take note of our account state; we'll refresh later if this changes.
        self._account_state_num = _ba.get_account_state_num()

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
        if (app.account_tournament_list is not None and
                app.account_tournament_list[0] == _ba.get_account_state_num()
                and all([
                    t_id in app.tournament_info
                    for t_id in app.account_tournament_list[1]
                ])):
            tourney_data = [
                app.tournament_info[t_id]
                for t_id in app.account_tournament_list[1]
            ]
            self._update_for_data(tourney_data)

        # This will pull new data periodically, update timers, etc.
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)
        self._update()

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use (called in bg thread)."""
        import bastd.ui.purchase as _unused1
        import bastd.ui.coop.gamebutton as _unused2
        import bastd.ui.confirm as _unused3
        import bastd.ui.account as _unused4
        import bastd.ui.league.rankwindow as _unused5
        import bastd.ui.store.browser as _unused6
        import bastd.ui.account.viewer as _unused7
        import bastd.ui.tournamentscores as _unused8
        import bastd.ui.tournamententry as _unused9
        import bastd.ui.play as _unused10

    def _update(self) -> None:
        cur_time = ba.time(ba.TimeType.REAL)

        # If its been a while since we got a tournament update, consider the
        # data invalid (prevents us from joining tournaments if our internet
        # connection goes down for a while).
        if (self._last_tournament_query_response_time is None
                or ba.time(ba.TimeType.REAL) -
                self._last_tournament_query_response_time > 60.0 * 2):
            self._tourney_data_up_to_date = False

        # If our account state has changed, do a full request.
        account_state_num = _ba.get_account_state_num()
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
        if self._fg_state != ba.app.fg_state:
            self._tourney_data_up_to_date = False

        # Send off a new tournament query if its been long enough or whatnot.
        if not self._doing_tournament_query and (
                self._last_tournament_query_time is None
                or cur_time - self._last_tournament_query_time > 30.0
                or self._fg_state != ba.app.fg_state):
            self._fg_state = ba.app.fg_state
            self._last_tournament_query_time = cur_time
            self._doing_tournament_query = True
            _ba.tournament_query(
                args={
                    'source': 'coop window refresh',
                    'numScores': 1
                },
                callback=ba.WeakCall(self._on_tournament_query_response),
            )

        # Decrement time on our tournament buttons.
        ads_enabled = _ba.have_incentivized_ad()
        for tbtn in self._tournament_buttons:
            tbtn['time_remaining'] = max(0, tbtn['time_remaining'] - 1)
            if tbtn['time_remaining_value_text'] is not None:
                ba.textwidget(
                    edit=tbtn['time_remaining_value_text'],
                    text=ba.timestring(tbtn['time_remaining'],
                                       centi=False,
                                       suppress_format_warning=True) if
                    (tbtn['has_time_remaining']
                     and self._tourney_data_up_to_date) else '-')

            # Also adjust the ad icon visibility.
            if tbtn.get('allow_ads', False) and _ba.has_video_ads():
                ba.imagewidget(edit=tbtn['entry_fee_ad_image'],
                               opacity=1.0 if ads_enabled else 0.25)
                ba.textwidget(edit=tbtn['entry_fee_text_remaining'],
                              color=(0.6, 0.6, 0.6, 1 if ads_enabled else 0.2))

        self._update_hard_mode_lock_image()

    def _update_hard_mode_lock_image(self) -> None:
        from ba.internal import have_pro_options
        try:
            ba.imagewidget(edit=self._hard_button_lock_image,
                           opacity=0.0 if have_pro_options() else 1.0)
        except Exception:
            ba.print_exception('Error updating campaign lock.')

    def _update_for_data(self, data: Optional[List[Dict[str, Any]]]) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        from ba.internal import getcampaign, get_tournament_prize_strings

        # If the number of tournaments or challenges in the data differs from
        # our current arrangement, refresh with the new number.
        if (((data is None and (self._tournament_button_count != 0))
             or (data is not None and
                 (len(data) != self._tournament_button_count)))):
            self._tournament_button_count = len(
                data) if data is not None else 0
            ba.app.config['Tournament Rows'] = self._tournament_button_count
            self._refresh()

        # Update all of our tourney buttons based on whats in data.
        for i, tbtn in enumerate(self._tournament_buttons):
            assert data is not None
            entry: Dict[str, Any] = data[i]
            prize_y_offs = (34 if 'prizeRange3' in entry else
                            20 if 'prizeRange2' in entry else 12)
            x_offs = 90

            # This seems to be a false alarm.
            # pylint: disable=unbalanced-tuple-unpacking
            pr1, pv1, pr2, pv2, pr3, pv3 = (
                get_tournament_prize_strings(entry))
            # pylint: enable=unbalanced-tuple-unpacking
            enabled = 'requiredLeague' not in entry
            ba.buttonwidget(edit=tbtn['button'],
                            color=(0.5, 0.7, 0.2) if enabled else
                            (0.5, 0.5, 0.5))
            ba.imagewidget(edit=tbtn['lock_image'],
                           opacity=0.0 if enabled else 1.0)
            ba.textwidget(edit=tbtn['prize_range_1_text'],
                          text='-' if pr1 == '' else pr1,
                          position=(tbtn['button_x'] + 365 + x_offs,
                                    tbtn['button_y'] + tbtn['button_scale_y'] -
                                    93 + prize_y_offs))

            # We want to draw values containing tickets a bit smaller
            # (scratch that; we now draw medals a bit bigger).
            ticket_char = ba.charstr(ba.SpecialChar.TICKET_BACKING)
            prize_value_scale_large = 1.0
            prize_value_scale_small = 1.0

            ba.textwidget(edit=tbtn['prize_value_1_text'],
                          text='-' if pv1 == '' else pv1,
                          scale=prize_value_scale_large if ticket_char
                          not in pv1 else prize_value_scale_small,
                          position=(tbtn['button_x'] + 380 + x_offs,
                                    tbtn['button_y'] + tbtn['button_scale_y'] -
                                    93 + prize_y_offs))

            ba.textwidget(edit=tbtn['prize_range_2_text'],
                          text=pr2,
                          position=(tbtn['button_x'] + 365 + x_offs,
                                    tbtn['button_y'] + tbtn['button_scale_y'] -
                                    93 - 45 + prize_y_offs))
            ba.textwidget(edit=tbtn['prize_value_2_text'],
                          text=pv2,
                          scale=prize_value_scale_large if ticket_char
                          not in pv2 else prize_value_scale_small,
                          position=(tbtn['button_x'] + 380 + x_offs,
                                    tbtn['button_y'] + tbtn['button_scale_y'] -
                                    93 - 45 + prize_y_offs))

            ba.textwidget(edit=tbtn['prize_range_3_text'],
                          text=pr3,
                          position=(tbtn['button_x'] + 365 + x_offs,
                                    tbtn['button_y'] + tbtn['button_scale_y'] -
                                    93 - 90 + prize_y_offs))
            ba.textwidget(edit=tbtn['prize_value_3_text'],
                          text=pv3,
                          scale=prize_value_scale_large if ticket_char
                          not in pv3 else prize_value_scale_small,
                          position=(tbtn['button_x'] + 380 + x_offs,
                                    tbtn['button_y'] + tbtn['button_scale_y'] -
                                    93 - 90 + prize_y_offs))

            leader_name = '-'
            leader_score: Union[str, ba.Lstr] = '-'
            if entry['scores']:
                score = tbtn['leader'] = copy.deepcopy(entry['scores'][0])
                leader_name = score[1]
                leader_score = (ba.timestring(
                    score[0] * 10,
                    centi=True,
                    timeformat=ba.TimeFormat.MILLISECONDS,
                    suppress_format_warning=True) if entry['scoreType']
                                == 'time' else str(score[0]))
            else:
                tbtn['leader'] = None

            ba.textwidget(edit=tbtn['current_leader_name_text'],
                          text=ba.Lstr(value=leader_name))
            self._tournament_leader_score_type = (entry['scoreType'])
            ba.textwidget(edit=tbtn['current_leader_score_text'],
                          text=leader_score)
            ba.buttonwidget(edit=tbtn['more_scores_button'],
                            label=ba.Lstr(resource=self._r + '.seeMoreText'))
            out_of_time_text: Union[str, ba.Lstr] = (
                '-' if 'totalTime' not in entry else ba.Lstr(
                    resource=self._r + '.ofTotalTimeText',
                    subs=[('${TOTAL}',
                           ba.timestring(entry['totalTime'],
                                         centi=False,
                                         suppress_format_warning=True))]))
            ba.textwidget(edit=tbtn['time_remaining_out_of_text'],
                          text=out_of_time_text)

            tbtn['time_remaining'] = entry['timeRemaining']
            tbtn['has_time_remaining'] = entry is not None
            tbtn['tournament_id'] = entry['tournamentID']
            tbtn['required_league'] = (None if 'requiredLeague' not in entry
                                       else entry['requiredLeague'])

            game = ba.app.tournament_info[tbtn['tournament_id']]['game']

            if game is None:
                ba.textwidget(edit=tbtn['button_text'], text='-')
                ba.imagewidget(edit=tbtn['image'],
                               texture=ba.gettexture('black'),
                               opacity=0.2)
            else:
                campaignname, levelname = game.split(':')
                campaign = getcampaign(campaignname)
                max_players = ba.app.tournament_info[
                    tbtn['tournament_id']]['maxPlayers']
                txt = ba.Lstr(
                    value='${A} ${B}',
                    subs=[('${A}', campaign.getlevel(levelname).displayname),
                          ('${B}',
                           ba.Lstr(resource='playerCountAbbreviatedText',
                                   subs=[('${COUNT}', str(max_players))]))])
                ba.textwidget(edit=tbtn['button_text'], text=txt)
                ba.imagewidget(
                    edit=tbtn['image'],
                    texture=campaign.getlevel(levelname).get_preview_texture(),
                    opacity=1.0 if enabled else 0.5)

            fee = entry['fee']

            if fee is None:
                fee_var = None
            elif fee == 4:
                fee_var = 'price.tournament_entry_4'
            elif fee == 3:
                fee_var = 'price.tournament_entry_3'
            elif fee == 2:
                fee_var = 'price.tournament_entry_2'
            elif fee == 1:
                fee_var = 'price.tournament_entry_1'
            else:
                if fee != 0:
                    print('Unknown fee value:', fee)
                fee_var = 'price.tournament_entry_0'

            tbtn['allow_ads'] = allow_ads = entry['allowAds']

            final_fee: Optional[int] = (None if fee_var is None else
                                        _ba.get_account_misc_read_val(
                                            fee_var, '?'))

            final_fee_str: Union[str, ba.Lstr]
            if fee_var is None:
                final_fee_str = ''
            else:
                if final_fee == 0:
                    final_fee_str = ba.Lstr(
                        resource='getTicketsWindow.freeText')
                else:
                    final_fee_str = (
                        ba.charstr(ba.SpecialChar.TICKET_BACKING) +
                        str(final_fee))

            ad_tries_remaining = ba.app.tournament_info[
                tbtn['tournament_id']]['adTriesRemaining']
            free_tries_remaining = ba.app.tournament_info[
                tbtn['tournament_id']]['freeTriesRemaining']

            # Now, if this fee allows ads and we support video ads, show
            # the 'or ad' version.
            if allow_ads and _ba.has_video_ads():
                ads_enabled = _ba.have_incentivized_ad()
                ba.imagewidget(edit=tbtn['entry_fee_ad_image'],
                               opacity=1.0 if ads_enabled else 0.25)
                or_text = ba.Lstr(resource='orText',
                                  subs=[('${A}', ''),
                                        ('${B}', '')]).evaluate().strip()
                ba.textwidget(edit=tbtn['entry_fee_text_or'], text=or_text)
                ba.textwidget(
                    edit=tbtn['entry_fee_text_top'],
                    position=(tbtn['button_x'] + 360,
                              tbtn['button_y'] + tbtn['button_scale_y'] - 60),
                    scale=1.3,
                    text=final_fee_str)

                # Possibly show number of ad-plays remaining.
                ba.textwidget(
                    edit=tbtn['entry_fee_text_remaining'],
                    position=(tbtn['button_x'] + 360,
                              tbtn['button_y'] + tbtn['button_scale_y'] - 146),
                    text='' if ad_tries_remaining in [None, 0] else
                    ('' + str(ad_tries_remaining)),
                    color=(0.6, 0.6, 0.6, 1 if ads_enabled else 0.2))
            else:
                ba.imagewidget(edit=tbtn['entry_fee_ad_image'], opacity=0.0)
                ba.textwidget(edit=tbtn['entry_fee_text_or'], text='')
                ba.textwidget(
                    edit=tbtn['entry_fee_text_top'],
                    position=(tbtn['button_x'] + 360,
                              tbtn['button_y'] + tbtn['button_scale_y'] - 80),
                    scale=1.3,
                    text=final_fee_str)

                # Possibly show number of free-plays remaining.
                ba.textwidget(
                    edit=tbtn['entry_fee_text_remaining'],
                    position=(tbtn['button_x'] + 360,
                              tbtn['button_y'] + tbtn['button_scale_y'] - 100),
                    text=('' if (free_tries_remaining in [None, 0]
                                 or final_fee != 0) else
                          ('' + str(free_tries_remaining))),
                    color=(0.6, 0.6, 0.6, 1))

    def _on_tournament_query_response(self, data: Optional[Dict[str,
                                                                Any]]) -> None:
        from ba.internal import cache_tournament_info
        app = ba.app
        if data is not None:
            tournament_data = data['t']  # This used to be the whole payload.
            self._last_tournament_query_response_time = ba.time(
                ba.TimeType.REAL)
        else:
            tournament_data = None

        # Keep our cached tourney info up to date.
        if data is not None:
            self._tourney_data_up_to_date = True
            cache_tournament_info(tournament_data)

            # Also cache the current tourney list/order for this account.
            app.account_tournament_list = (_ba.get_account_state_num(), [
                e['tournamentID'] for e in tournament_data
            ])

        self._doing_tournament_query = False
        self._update_for_data(tournament_data)

    def _set_campaign_difficulty(self, difficulty: str) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui.purchase import PurchaseWindow
        if difficulty != self._campaign_difficulty:
            if difficulty == 'hard' and not have_pro_options():
                PurchaseWindow(items=['pro'])
                return
            ba.playsound(ba.getsound('gunCocking'))
            if difficulty not in ('easy', 'hard'):
                print('ERROR: invalid campaign difficulty:', difficulty)
                difficulty = 'easy'
            self._campaign_difficulty = difficulty
            _ba.add_transaction({
                'type': 'SET_MISC_VAL',
                'name': 'campaignDifficulty',
                'value': difficulty
            })
            self._refresh_campaign_row()
        else:
            ba.playsound(ba.getsound('click01'))

    def _refresh_campaign_row(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from ba.internal import getcampaign
        from bastd.ui.coop.gamebutton import GameButton
        parent_widget = self._campaign_sub_container

        # Clear out anything in the parent widget already.
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
        self._easy_button = ba.buttonwidget(
            parent=parent_widget,
            position=(h + 30, v2 + 105),
            size=(120, 70),
            label=ba.Lstr(resource='difficultyEasyText'),
            button_type='square',
            autoselect=True,
            enable_sound=False,
            on_activate_call=ba.Call(self._set_campaign_difficulty, 'easy'),
            on_select_call=ba.Call(self.sel_change, 'campaign', 'easyButton'),
            color=sel_color
            if self._campaign_difficulty == 'easy' else un_sel_color,
            textcolor=sel_textcolor
            if self._campaign_difficulty == 'easy' else un_sel_textcolor)
        ba.widget(edit=self._easy_button, show_buffer_left=100)
        if self._selected_campaign_level == 'easyButton':
            ba.containerwidget(edit=parent_widget,
                               selected_child=self._easy_button,
                               visible_child=self._easy_button)
        lock_tex = ba.gettexture('lock')

        self._hard_button = ba.buttonwidget(
            parent=parent_widget,
            position=(h + 30, v2 + 32),
            size=(120, 70),
            label=ba.Lstr(resource='difficultyHardText'),
            button_type='square',
            autoselect=True,
            enable_sound=False,
            on_activate_call=ba.Call(self._set_campaign_difficulty, 'hard'),
            on_select_call=ba.Call(self.sel_change, 'campaign', 'hardButton'),
            color=sel_color_hard
            if self._campaign_difficulty == 'hard' else un_sel_color,
            textcolor=sel_textcolor
            if self._campaign_difficulty == 'hard' else un_sel_textcolor)
        self._hard_button_lock_image = ba.imagewidget(
            parent=parent_widget,
            size=(30, 30),
            draw_controller=self._hard_button,
            position=(h + 30 - 10, v2 + 32 + 70 - 35),
            texture=lock_tex)
        self._update_hard_mode_lock_image()
        ba.widget(edit=self._hard_button, show_buffer_left=100)
        if self._selected_campaign_level == 'hardButton':
            ba.containerwidget(edit=parent_widget,
                               selected_child=self._hard_button,
                               visible_child=self._hard_button)

        ba.widget(edit=self._hard_button, down_widget=next_widget_down)
        h_spacing = 200
        campaign_buttons = []
        if self._campaign_difficulty == 'easy':
            campaignname = 'Easy'
        else:
            campaignname = 'Default'
        items = [
            campaignname + ':Onslaught Training',
            campaignname + ':Rookie Onslaught',
            campaignname + ':Rookie Football', campaignname + ':Pro Onslaught',
            campaignname + ':Pro Football', campaignname + ':Pro Runaround',
            campaignname + ':Uber Onslaught', campaignname + ':Uber Football',
            campaignname + ':Uber Runaround'
        ]
        items += [campaignname + ':The Last Stand']
        if self._selected_campaign_level is None:
            self._selected_campaign_level = items[0]
        h = 150
        for i in items:
            is_last_sel = (i == self._selected_campaign_level)
            campaign_buttons.append(
                GameButton(self, parent_widget, i, h, v2, is_last_sel,
                           'campaign').get_button())
            h += h_spacing

        ba.widget(edit=campaign_buttons[0], left_widget=self._easy_button)

        if self._back_button is not None:
            ba.widget(edit=self._easy_button, up_widget=self._back_button)
            for btn in campaign_buttons:
                ba.widget(edit=btn,
                          up_widget=self._back_button,
                          down_widget=next_widget_down)

        # Update our existing percent-complete text.
        campaign = getcampaign(campaignname)
        levels = campaign.levels
        levels_complete = sum((1 if l.complete else 0) for l in levels)

        # Last level cant be completed; hence the -1.
        progress = min(1.0, float(levels_complete) / (len(levels) - 1))
        p_str = str(int(progress * 100.0)) + '%'

        self._campaign_percent_text = ba.textwidget(
            edit=self._campaign_percent_text,
            text=ba.Lstr(value='${C} (${P})',
                         subs=[('${C}',
                                ba.Lstr(resource=self._r + '.campaignText')),
                               ('${P}', p_str)]))

    def _on_tournament_info_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.confirm import ConfirmWindow
        txt = ba.Lstr(resource=self._r + '.tournamentInfoText')
        ConfirmWindow(txt,
                      cancel_button=False,
                      width=550,
                      height=260,
                      origin_widget=self._tournament_info_button)

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bastd.ui.coop.gamebutton import GameButton

        # (Re)create the sub-container if need be.
        if self._subcontainer is not None:
            self._subcontainer.delete()

        tourney_row_height = 200
        self._subcontainerheight = (
            620 + self._tournament_button_count * tourney_row_height)

        self._subcontainer = ba.containerwidget(
            parent=self._scrollwidget,
            size=(self._subcontainerwidth, self._subcontainerheight),
            background=False,
            claims_left_right=True,
            claims_tab=True,
            selection_loops_to_parent=True)

        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)
        if self._back_button is not None:
            ba.containerwidget(edit=self._root_widget,
                               cancel_button=self._back_button)

        w_parent = self._subcontainer
        h_base = 6

        v = self._subcontainerheight - 73

        self._campaign_percent_text = ba.textwidget(
            parent=w_parent,
            position=(h_base + 27, v + 30),
            size=(0, 0),
            text='',
            h_align='left',
            v_align='center',
            color=ba.app.ui.title_color,
            scale=1.1)

        row_v_show_buffer = 100
        v -= 198

        h_scroll = ba.hscrollwidget(
            parent=w_parent,
            size=(self._scroll_width - 10, 205),
            position=(-5, v),
            simple_culling_h=70,
            highlight=False,
            border_opacity=0.0,
            color=(0.45, 0.4, 0.5),
            on_select_call=lambda: self._on_row_selected('campaign'))
        self._campaign_h_scroll = h_scroll
        ba.widget(edit=h_scroll,
                  show_buffer_top=row_v_show_buffer,
                  show_buffer_bottom=row_v_show_buffer,
                  autoselect=True)
        if self._selected_row == 'campaign':
            ba.containerwidget(edit=w_parent,
                               selected_child=h_scroll,
                               visible_child=h_scroll)
        ba.containerwidget(edit=h_scroll, claims_left_right=True)
        self._campaign_sub_container = ba.containerwidget(parent=h_scroll,
                                                          size=(180 + 200 * 10,
                                                                200),
                                                          background=False)

        # Tournaments

        self._tournament_buttons: List[Dict[str, Any]] = []

        v -= 53
        # FIXME shouldn't use hard-coded strings here.
        txt = ba.Lstr(resource='tournamentsText',
                      fallback_resource='tournamentText').evaluate()
        t_width = _ba.get_string_width(txt, suppress_warning=True)
        ba.textwidget(parent=w_parent,
                      position=(h_base + 27, v + 30),
                      size=(0, 0),
                      text=txt,
                      h_align='left',
                      v_align='center',
                      color=ba.app.ui.title_color,
                      scale=1.1)
        self._tournament_info_button = ba.buttonwidget(
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
            on_activate_call=self._on_tournament_info_press)
        ba.widget(edit=self._tournament_info_button,
                  left_widget=self._tournament_info_button,
                  right_widget=self._tournament_info_button)

        # Say 'unavailable' if there are zero tournaments, and if we're not
        # signed in add that as well (that's probably why we see
        # no tournaments).
        if self._tournament_button_count == 0:
            unavailable_text = ba.Lstr(resource='unavailableText')
            if _ba.get_account_state() != 'signed_in':
                unavailable_text = ba.Lstr(
                    value='${A} (${B})',
                    subs=[('${A}', unavailable_text),
                          ('${B}', ba.Lstr(resource='notSignedInText'))])
            ba.textwidget(parent=w_parent,
                          position=(h_base + 47, v),
                          size=(0, 0),
                          text=unavailable_text,
                          h_align='left',
                          v_align='center',
                          color=ba.app.ui.title_color,
                          scale=0.9)
            v -= 40
        v -= 198

        tournament_h_scroll = None
        if self._tournament_button_count > 0:
            for i in range(self._tournament_button_count):
                tournament_h_scroll = h_scroll = ba.hscrollwidget(
                    parent=w_parent,
                    size=(self._scroll_width - 10, 205),
                    position=(-5, v),
                    highlight=False,
                    border_opacity=0.0,
                    color=(0.45, 0.4, 0.5),
                    on_select_call=ba.Call(self._on_row_selected,
                                           'tournament' + str(i + 1)))
                ba.widget(edit=h_scroll,
                          show_buffer_top=row_v_show_buffer,
                          show_buffer_bottom=row_v_show_buffer,
                          autoselect=True)
                if self._selected_row == 'tournament' + str(i + 1):
                    ba.containerwidget(edit=w_parent,
                                       selected_child=h_scroll,
                                       visible_child=h_scroll)
                ba.containerwidget(edit=h_scroll, claims_left_right=True)
                sc2 = ba.containerwidget(parent=h_scroll,
                                         size=(self._scroll_width - 24, 200),
                                         background=False)
                h = 0
                v2 = -2
                is_last_sel = True
                self._tournament_buttons.append(
                    self._tournament_button(sc2, h, v2, is_last_sel))
                v -= 200

        # Custom Games.
        v -= 50
        ba.textwidget(parent=w_parent,
                      position=(h_base + 27, v + 30 + 198),
                      size=(0, 0),
                      text=ba.Lstr(
                          resource='practiceText',
                          fallback_resource='coopSelectWindow.customText'),
                      h_align='left',
                      v_align='center',
                      color=ba.app.ui.title_color,
                      scale=1.1)

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
        if _ba.get_account_misc_read_val(
                'easter', False) or _ba.get_purchased('games.easter_egg_hunt'):
            items = [
                'Challenges:Easter Egg Hunt', 'Challenges:Pro Easter Egg Hunt'
            ] + items

        # add all custom user levels here..
        # items += [
        #     'User:' + l.getname()
        #     for l in getcampaign('User').getlevels()
        # ]

        self._custom_h_scroll = custom_h_scroll = h_scroll = ba.hscrollwidget(
            parent=w_parent,
            size=(self._scroll_width - 10, 205),
            position=(-5, v),
            highlight=False,
            border_opacity=0.0,
            color=(0.45, 0.4, 0.5),
            on_select_call=ba.Call(self._on_row_selected, 'custom'))
        ba.widget(edit=h_scroll,
                  show_buffer_top=row_v_show_buffer,
                  show_buffer_bottom=1.5 * row_v_show_buffer,
                  autoselect=True)
        if self._selected_row == 'custom':
            ba.containerwidget(edit=w_parent,
                               selected_child=h_scroll,
                               visible_child=h_scroll)
        ba.containerwidget(edit=h_scroll, claims_left_right=True)
        sc2 = ba.containerwidget(parent=h_scroll,
                                 size=(max(self._scroll_width - 24,
                                           30 + 200 * len(items)), 200),
                                 background=False)
        h_spacing = 200
        self._custom_buttons: List[GameButton] = []
        h = 0
        v2 = -2
        for item in items:
            is_last_sel = (item == self._selected_custom_level)
            self._custom_buttons.append(
                GameButton(self, sc2, item, h, v2, is_last_sel, 'custom'))
            h += h_spacing

        # We can't fill in our campaign row until tourney buttons are in place.
        # (for wiring up)
        self._refresh_campaign_row()

        for i in range(len(self._tournament_buttons)):
            ba.widget(
                edit=self._tournament_buttons[i]['button'],
                up_widget=self._tournament_info_button
                if i == 0 else self._tournament_buttons[i - 1]['button'],
                down_widget=self._tournament_buttons[(i + 1)]['button']
                if i + 1 < len(self._tournament_buttons) else custom_h_scroll)
            ba.widget(
                edit=self._tournament_buttons[i]['more_scores_button'],
                down_widget=self._tournament_buttons[(
                    i + 1)]['current_leader_name_text']
                if i + 1 < len(self._tournament_buttons) else custom_h_scroll)
            ba.widget(
                edit=self._tournament_buttons[i]['current_leader_name_text'],
                up_widget=self._tournament_info_button if i == 0 else
                self._tournament_buttons[i - 1]['more_scores_button'])

        for btn in self._custom_buttons:
            try:
                ba.widget(
                    edit=btn.get_button(),
                    up_widget=tournament_h_scroll if self._tournament_buttons
                    else self._tournament_info_button)
            except Exception:
                ba.print_exception('Error wiring up custom buttons.')

        if self._back_button is not None:
            ba.buttonwidget(edit=self._back_button,
                            on_activate_call=self._back)
        else:
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._back)

        # There's probably several 'onSelected' callbacks pushed onto the
        # event queue.. we need to push ours too so we're enabled *after* them.
        ba.pushcall(self._enable_selectable_callback)

    def _on_row_selected(self, row: str) -> None:
        if self._do_selection_callbacks:
            if self._selected_row != row:
                self._selected_row = row

    def _enable_selectable_callback(self) -> None:
        self._do_selection_callbacks = True

    def _tournament_button(self, parent: ba.Widget, x: float, y: float,
                           select: bool) -> Dict[str, Any]:
        sclx = 300
        scly = 195.0
        data: Dict[str, Any] = {
            'tournament_id': None,
            'time_remaining': 0,
            'has_time_remaining': False,
            'leader': None
        }
        data['button'] = btn = ba.buttonwidget(
            parent=parent,
            position=(x + 23, y + 4),
            size=(sclx, scly),
            label='',
            button_type='square',
            autoselect=True,
            on_activate_call=lambda: self.run(None, tournament_button=data))
        ba.widget(edit=btn,
                  show_buffer_bottom=50,
                  show_buffer_top=50,
                  show_buffer_left=400,
                  show_buffer_right=200)
        if select:
            ba.containerwidget(edit=parent,
                               selected_child=btn,
                               visible_child=btn)
        image_width = sclx * 0.85 * 0.75

        data['image'] = ba.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 21 + sclx * 0.5 - image_width * 0.5, y + scly - 150),
            size=(image_width, image_width * 0.5),
            model_transparent=self.lsbt,
            model_opaque=self.lsbo,
            texture=ba.gettexture('black'),
            opacity=0.2,
            mask_texture=ba.gettexture('mapPreviewMask'))

        data['lock_image'] = ba.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 21 + sclx * 0.5 - image_width * 0.25,
                      y + scly - 150),
            size=(image_width * 0.5, image_width * 0.5),
            texture=ba.gettexture('lock'),
            opacity=0.0)

        data['button_text'] = ba.textwidget(parent=parent,
                                            draw_controller=btn,
                                            position=(x + 20 + sclx * 0.5,
                                                      y + scly - 35),
                                            size=(0, 0),
                                            h_align='center',
                                            text='-',
                                            v_align='center',
                                            maxwidth=sclx * 0.76,
                                            scale=0.85,
                                            color=(0.8, 1.0, 0.8, 1.0))

        header_color = (0.43, 0.4, 0.5, 1)
        value_color = (0.6, 0.6, 0.6, 1)

        x_offs = 0
        ba.textwidget(parent=parent,
                      draw_controller=btn,
                      position=(x + 360, y + scly - 20),
                      size=(0, 0),
                      h_align='center',
                      text=ba.Lstr(resource=self._r + '.entryFeeText'),
                      v_align='center',
                      maxwidth=100,
                      scale=0.9,
                      color=header_color,
                      flatness=1.0)

        data['entry_fee_text_top'] = ba.textwidget(parent=parent,
                                                   draw_controller=btn,
                                                   position=(x + 360,
                                                             y + scly - 60),
                                                   size=(0, 0),
                                                   h_align='center',
                                                   text='-',
                                                   v_align='center',
                                                   maxwidth=60,
                                                   scale=1.3,
                                                   color=value_color,
                                                   flatness=1.0)
        data['entry_fee_text_or'] = ba.textwidget(parent=parent,
                                                  draw_controller=btn,
                                                  position=(x + 360,
                                                            y + scly - 90),
                                                  size=(0, 0),
                                                  h_align='center',
                                                  text='',
                                                  v_align='center',
                                                  maxwidth=60,
                                                  scale=0.5,
                                                  color=value_color,
                                                  flatness=1.0)
        data['entry_fee_text_remaining'] = ba.textwidget(parent=parent,
                                                         draw_controller=btn,
                                                         position=(x + 360, y +
                                                                   scly - 90),
                                                         size=(0, 0),
                                                         h_align='center',
                                                         text='',
                                                         v_align='center',
                                                         maxwidth=60,
                                                         scale=0.5,
                                                         color=value_color,
                                                         flatness=1.0)

        data['entry_fee_ad_image'] = ba.imagewidget(
            parent=parent,
            size=(40, 40),
            draw_controller=btn,
            position=(x + 360 - 20, y + scly - 140),
            opacity=0.0,
            texture=ba.gettexture('tv'))

        x_offs += 50

        ba.textwidget(parent=parent,
                      draw_controller=btn,
                      position=(x + 447 + x_offs, y + scly - 20),
                      size=(0, 0),
                      h_align='center',
                      text=ba.Lstr(resource=self._r + '.prizesText'),
                      v_align='center',
                      maxwidth=130,
                      scale=0.9,
                      color=header_color,
                      flatness=1.0)

        data['button_x'] = x
        data['button_y'] = y
        data['button_scale_y'] = scly

        xo2 = 0
        prize_value_scale = 1.5

        data['prize_range_1_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 355 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='right',
            v_align='center',
            maxwidth=50,
            text='-',
            scale=0.8,
            color=header_color,
            flatness=1.0)
        data['prize_value_1_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 380 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='left',
            text='-',
            v_align='center',
            maxwidth=100,
            scale=prize_value_scale,
            color=value_color,
            flatness=1.0)

        data['prize_range_2_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 355 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='right',
            v_align='center',
            maxwidth=50,
            scale=0.8,
            color=header_color,
            flatness=1.0)
        data['prize_value_2_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 380 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='left',
            text='',
            v_align='center',
            maxwidth=100,
            scale=prize_value_scale,
            color=value_color,
            flatness=1.0)

        data['prize_range_3_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 355 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='right',
            v_align='center',
            maxwidth=50,
            scale=0.8,
            color=header_color,
            flatness=1.0)
        data['prize_value_3_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 380 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='left',
            text='',
            v_align='center',
            maxwidth=100,
            scale=prize_value_scale,
            color=value_color,
            flatness=1.0)

        ba.textwidget(parent=parent,
                      draw_controller=btn,
                      position=(x + 620 + x_offs, y + scly - 20),
                      size=(0, 0),
                      h_align='center',
                      text=ba.Lstr(resource=self._r + '.currentBestText'),
                      v_align='center',
                      maxwidth=180,
                      scale=0.9,
                      color=header_color,
                      flatness=1.0)
        data['current_leader_name_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 620 + x_offs - (170 / 1.4) * 0.5,
                      y + scly - 60 - 40 * 0.5),
            selectable=True,
            click_activate=True,
            autoselect=True,
            on_activate_call=lambda: self._show_leader(tournament_button=data),
            size=(170 / 1.4, 40),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=170,
            scale=1.4,
            color=value_color,
            flatness=1.0)
        data['current_leader_score_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 620 + x_offs, y + scly - 113 + 10),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=170,
            scale=1.8,
            color=value_color,
            flatness=1.0)

        data['more_scores_button'] = ba.buttonwidget(
            parent=parent,
            position=(x + 620 + x_offs - 60, y + scly - 50 - 125),
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
            label='-',
            size=(120, 40),
            autoselect=True,
            up_widget=data['current_leader_name_text'],
            text_scale=0.6,
            on_activate_call=lambda: self._show_scores(tournament_button=data))
        ba.widget(edit=data['current_leader_name_text'],
                  down_widget=data['more_scores_button'])

        ba.textwidget(parent=parent,
                      draw_controller=btn,
                      position=(x + 820 + x_offs, y + scly - 20),
                      size=(0, 0),
                      h_align='center',
                      text=ba.Lstr(resource=self._r + '.timeRemainingText'),
                      v_align='center',
                      maxwidth=180,
                      scale=0.9,
                      color=header_color,
                      flatness=1.0)
        data['time_remaining_value_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 820 + x_offs, y + scly - 68),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=180,
            scale=2.0,
            color=value_color,
            flatness=1.0)
        data['time_remaining_out_of_text'] = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 820 + x_offs, y + scly - 110),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=120,
            scale=0.72,
            color=(0.4, 0.4, 0.5),
            flatness=1.0)
        return data

    def _switch_to_league_rankings(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import show_sign_in_prompt
        from bastd.ui.league.rankwindow import LeagueRankWindow
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        assert self._league_rank_button is not None
        ba.app.ui.set_main_menu_window(
            LeagueRankWindow(origin_widget=self._league_rank_button.get_button(
            )).get_root_widget())

    def _switch_to_score(self, show_tab: Optional[str] = 'extras') -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import show_sign_in_prompt
        from bastd.ui.store.browser import StoreBrowserWindow
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        assert self._store_button is not None
        ba.app.ui.set_main_menu_window(
            StoreBrowserWindow(
                origin_widget=self._store_button.get_button(),
                show_tab=show_tab,
                back_location='CoopBrowserWindow').get_root_widget())

    def _show_leader(self, tournament_button: Dict[str, Any]) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account.viewer import AccountViewerWindow
        tournament_id = tournament_button['tournament_id']

        # FIXME: This assumes a single player entry in leader; should expand
        #  this to work with multiple.
        if tournament_id is None or tournament_button['leader'] is None or len(
                tournament_button['leader'][2]) != 1:
            ba.playsound(ba.getsound('error'))
            return
        ba.playsound(ba.getsound('swish'))
        AccountViewerWindow(
            account_id=tournament_button['leader'][2][0].get('a', None),
            profile_id=tournament_button['leader'][2][0].get('p', None),
            position=tournament_button['current_leader_name_text'].
            get_screen_space_center())

    def _show_scores(self, tournament_button: Dict[str, Any]) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.tournamentscores import TournamentScoresWindow
        tournament_id = tournament_button['tournament_id']
        if tournament_id is None:
            ba.playsound(ba.getsound('error'))
            return

        TournamentScoresWindow(
            tournament_id=tournament_id,
            position=tournament_button['more_scores_button'].
            get_screen_space_center())

    def is_tourney_data_up_to_date(self) -> bool:
        """Return whether our tourney data is up to date."""
        return self._tourney_data_up_to_date

    def run(self,
            game: Optional[str],
            tournament_button: Dict[str, Any] = None) -> None:
        """Run the provided game."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-return-statements
        # pylint: disable=cyclic-import
        from ba.internal import have_pro
        from bastd.ui.confirm import ConfirmWindow
        from bastd.ui.tournamententry import TournamentEntryWindow
        from bastd.ui.purchase import PurchaseWindow
        from bastd.ui.account import show_sign_in_prompt
        args: Dict[str, Any] = {}

        # Do a bit of pre-flight for tournament options.
        if tournament_button is not None:

            if _ba.get_account_state() != 'signed_in':
                show_sign_in_prompt()
                return

            if not self._tourney_data_up_to_date:
                ba.screenmessage(
                    ba.Lstr(resource='tournamentCheckingStateText'),
                    color=(1, 1, 0))
                ba.playsound(ba.getsound('error'))
                return

            if tournament_button['tournament_id'] is None:
                ba.screenmessage(
                    ba.Lstr(resource='internal.unavailableNoConnectionText'),
                    color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return

            if tournament_button['required_league'] is not None:
                ba.screenmessage(ba.Lstr(
                    resource='league.tournamentLeagueText',
                    subs=[
                        ('${NAME}',
                         ba.Lstr(
                             translate=('leagueNames',
                                        tournament_button['required_league'])))
                    ]),
                                 color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return

            if tournament_button['time_remaining'] <= 0:
                ba.screenmessage(ba.Lstr(resource='tournamentEndedText'),
                                 color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return

            # Game is whatever the tournament tells us it is.
            game = ba.app.tournament_info[
                tournament_button['tournament_id']]['game']

        if tournament_button is None and game == 'Easy:The Last Stand':
            ConfirmWindow(ba.Lstr(resource='difficultyHardUnlockOnlyText',
                                  fallback_resource='difficultyHardOnlyText'),
                          cancel_button=False,
                          width=460,
                          height=130)
            return

        # Infinite onslaught/runaround require pro; bring up a store link if
        # need be.
        if tournament_button is None and game in (
                'Challenges:Infinite Runaround',
                'Challenges:Infinite Onslaught') and not have_pro():
            if _ba.get_account_state() != 'signed_in':
                show_sign_in_prompt()
            else:
                PurchaseWindow(items=['pro'])
            return

        required_purchase: Optional[str]
        if game in ['Challenges:Meteor Shower']:
            required_purchase = 'games.meteor_shower'
        elif game in [
                'Challenges:Target Practice', 'Challenges:Target Practice B'
        ]:
            required_purchase = 'games.target_practice'
        elif game in ['Challenges:Ninja Fight']:
            required_purchase = 'games.ninja_fight'
        elif game in ['Challenges:Pro Ninja Fight']:
            required_purchase = 'games.ninja_fight'
        elif game in [
                'Challenges:Easter Egg Hunt', 'Challenges:Pro Easter Egg Hunt'
        ]:
            required_purchase = 'games.easter_egg_hunt'
        else:
            required_purchase = None

        if (tournament_button is None and required_purchase is not None
                and not _ba.get_purchased(required_purchase)):
            if _ba.get_account_state() != 'signed_in':
                show_sign_in_prompt()
            else:
                PurchaseWindow(items=[required_purchase])
            return

        self._save_state()

        # For tournaments, we pop up the entry window.
        if tournament_button is not None:
            TournamentEntryWindow(
                tournament_id=tournament_button['tournament_id'],
                position=tournament_button['button'].get_screen_space_center())
        else:
            # Otherwise just dive right in.
            assert game is not None
            if ba.app.launch_coop_game(game, args=args):
                ba.containerwidget(edit=self._root_widget,
                                   transition='out_left')

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.play import PlayWindow

        # If something is selected, store it.
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            PlayWindow(transition='in_left').get_root_widget())

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__,
                                                   {}).get('sel_name')
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            elif sel_name == 'PowerRanking':
                sel = self._league_rank_button_widget
            elif sel_name == 'Store':
                sel = self._store_button_widget
            else:
                sel = self._scrollwidget
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')

    def _save_state(self) -> None:
        cfg = ba.app.config
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._back_button:
                sel_name = 'Back'
            elif sel == self._store_button_widget:
                sel_name = 'Store'
            elif sel == self._league_rank_button_widget:
                sel_name = 'PowerRanking'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            else:
                raise ValueError('unrecognized selection')
            ba.app.ui.window_states[self.__class__.__name__] = {
                'sel_name': sel_name
            }
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

        cfg['Selected Coop Row'] = self._selected_row
        cfg['Selected Coop Custom Level'] = self._selected_custom_level
        cfg['Selected Coop Challenge Level'] = self._selected_challenge_level
        cfg['Selected Coop Campaign Level'] = self._selected_campaign_level
        cfg.commit()

    def sel_change(self, row: str, game: str) -> None:
        """(internal)"""
        if self._do_selection_callbacks:
            if row == 'custom':
                self._selected_custom_level = game
            if row == 'challenges':
                self._selected_challenge_level = game
            elif row == 'campaign':
                self._selected_campaign_level = game
