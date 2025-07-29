# Released under the MIT License. See LICENSE for details.
#
"""Defines a popup window for entering tournaments."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable
    import bascenev1 as bs


class TournamentEntryWindow(PopupWindow):
    """Popup window for entering tournaments."""

    def __init__(
        self,
        tournament_id: str,
        tournament_activity: bs.Activity | None = None,
        position: tuple[float, float] = (0.0, 0.0),
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        on_close_call: Callable[[], Any] | None = None,
    ):
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        from bauiv1lib.coop.tournamentbutton import USE_ENTRY_FEES

        assert bui.app.classic is not None
        assert bui.app.plus
        bui.set_analytics_screen('Tournament Entry Window')

        self._tournament_id = tournament_id
        self._tournament_info = bui.app.classic.accounts.tournament_info[
            self._tournament_id
        ]

        self._purchase_name: str | None
        self._purchase_price_name: str | None

        # Set a few vars depending on the tourney fee.
        self._fee = self._tournament_info['fee']
        assert isinstance(self._fee, int | None)
        self._allow_ads = (
            self._tournament_info['allowAds'] if USE_ENTRY_FEES else False
        )
        if self._fee == 4:
            self._purchase_name = 'tournament_entry_4'
            self._purchase_price_name = 'price.tournament_entry_4'
        elif self._fee == 3:
            self._purchase_name = 'tournament_entry_3'
            self._purchase_price_name = 'price.tournament_entry_3'
        elif self._fee == 2:
            self._purchase_name = 'tournament_entry_2'
            self._purchase_price_name = 'price.tournament_entry_2'
        elif self._fee == 1:
            self._purchase_name = 'tournament_entry_1'
            self._purchase_price_name = 'price.tournament_entry_1'
        elif self._fee is None or self._fee == -1:
            self._purchase_name = None
            self._purchase_price_name = 'FREE-WOOT'
        else:
            if self._fee != 0:
                raise ValueError('invalid fee: ' + str(self._fee))
            self._purchase_name = 'tournament_entry_0'
            self._purchase_price_name = 'price.tournament_entry_0'

        self._purchase_price: int | None = None

        self._on_close_call = on_close_call
        if scale is None:
            uiscale = bui.app.ui_v1.uiscale
            scale = (
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )
        self._delegate = delegate
        self._transitioning_out = False

        self._tournament_activity = tournament_activity

        self._width: float = 340.0
        self._height: float = 225.0

        bg_color = (0.5, 0.4, 0.6)

        # Show the practice button as long as we're not
        # restarting while on a paid tournament run.
        self._do_practice = (
            self._tournament_activity is None
            and bui.app.config.get('tournament_practice_enabled', False)
        )

        off_p = 0 if not self._do_practice else 48
        self._height += off_p * 0.933

        # Creates our root_widget.
        super().__init__(
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=bg_color,
            offset=offset,
            toolbar_visibility='menu_store_no_back',
        )

        self._last_ad_press_time = -9999.0
        self._last_ticket_press_time = -9999.0
        self._entering = False
        self._launched = False

        # Show the ad button only if we support ads *and* it has a level 1 fee.
        self._do_ad_btn = bui.app.plus.ads.has_video_ads() and self._allow_ads

        x_offs = 0 if self._do_ad_btn else 85

        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(40, self._height - 34),
            size=(60, 60),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        self._title_text = bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text=bui.Lstr(resource='tournamentEntryText'),
            maxwidth=180,
            # color=(1, 1, 1, 0.4),
            color=bui.app.ui_v1.title_color,
        )

        btn = self._pay_with_tickets_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(30 + x_offs, 60 + off_p),
            autoselect=True,
            button_type='square',
            size=(120, 120),
            label='',
            on_activate_call=self._on_pay_with_tickets_press,
        )
        self._ticket_img_pos = (50 + x_offs, 94 + off_p)
        self._ticket_img_pos_free = (50 + x_offs, 80 + off_p)
        self._ticket_img = bui.imagewidget(
            parent=self.root_widget,
            draw_controller=btn,
            size=(80, 80),
            position=self._ticket_img_pos,
            texture=bui.gettexture('tickets'),
        )
        self._ticket_cost_text_position = (87 + x_offs, 88 + off_p)
        self._ticket_cost_text_position_free = (87 + x_offs, 120 + off_p)
        self._ticket_cost_text = bui.textwidget(
            parent=self.root_widget,
            draw_controller=btn,
            position=self._ticket_cost_text_position,
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text='',
            maxwidth=95,
            color=(0, 1, 0),
        )
        self._free_plays_remaining_text = bui.textwidget(
            parent=self.root_widget,
            draw_controller=btn,
            position=(87 + x_offs, 78 + off_p),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.33,
            text='',
            maxwidth=95,
            color=(0, 0.8, 0),
        )
        self._pay_with_ad_btn: bui.Widget | None
        if self._do_ad_btn:
            btn = self._pay_with_ad_btn = bui.buttonwidget(
                parent=self.root_widget,
                position=(190, 60 + off_p),
                autoselect=True,
                button_type='square',
                size=(120, 120),
                label='',
                on_activate_call=self._on_pay_with_ad_press,
            )
            self._pay_with_ad_img = bui.imagewidget(
                parent=self.root_widget,
                draw_controller=btn,
                size=(80, 80),
                position=(210, 94 + off_p),
                texture=bui.gettexture('tv'),
            )

            self._ad_text_position = (251, 88 + off_p)
            self._ad_text_position_remaining = (251, 92 + off_p)
            have_ad_tries_remaining = (
                self._tournament_info['adTriesRemaining'] is not None
            )
            self._ad_text = bui.textwidget(
                parent=self.root_widget,
                draw_controller=btn,
                position=(
                    self._ad_text_position_remaining
                    if have_ad_tries_remaining
                    else self._ad_text_position
                ),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.6,
                # Note to self: AdMob requires rewarded ad usage
                # specifically says 'Ad' in it.
                text=bui.Lstr(resource='watchAnAdText'),
                maxwidth=95,
                color=(0, 1, 0),
            )
            ad_plays_remaining_text = (
                ''
                if not have_ad_tries_remaining
                else '' + str(self._tournament_info['adTriesRemaining'])
            )
            self._ad_plays_remaining_text = bui.textwidget(
                parent=self.root_widget,
                draw_controller=btn,
                position=(251, 78 + off_p),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.33,
                text=ad_plays_remaining_text,
                maxwidth=95,
                color=(0, 0.8, 0),
            )

            bui.textwidget(
                parent=self.root_widget,
                position=(self._width * 0.5, 120 + off_p),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.6,
                text=bui.Lstr(
                    resource='orText', subs=[('${A}', ''), ('${B}', '')]
                ),
                maxwidth=35,
                color=(1, 1, 1, 0.5),
            )
        else:
            self._pay_with_ad_btn = None

        btn_size = (150, 45)
        btn_pos = (self._width / 2 - btn_size[0] / 2, self._width / 2 - 110)
        self._practice_button = None
        if self._do_practice:
            self._practice_button = bui.buttonwidget(
                parent=self.root_widget,
                position=btn_pos,
                autoselect=True,
                size=btn_size,
                label=bui.Lstr(resource='practiceText'),
                on_activate_call=self._on_practice_press,
            )

        self._get_tickets_button: bui.Widget | None = None
        self._ticket_count_text: bui.Widget | None = None

        self._seconds_remaining = None

        bui.containerwidget(
            edit=self.root_widget, cancel_button=self._cancel_button
        )

        # Let's also ask the server for info about this tournament
        # (time remaining, etc) so we can show the user time remaining,
        # disallow entry if time has run out, etc.
        # xoffs = 104 if bui.app.ui.use_toolbars else 0
        self._time_remaining_text = bui.textwidget(
            parent=self.root_widget,
            position=(self._width / 2, 28),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='-',
            scale=0.65,
            maxwidth=100,
            flatness=1.0,
            color=(0.7, 0.7, 0.7),
        )
        self._time_remaining_label_text = bui.textwidget(
            parent=self.root_widget,
            position=(self._width / 2, 45),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='coopSelectWindow.timeRemainingText'),
            scale=0.45,
            flatness=1.0,
            maxwidth=100,
            color=(0.7, 0.7, 0.7),
        )

        self._last_query_time: float | None = None

        # If there seems to be a relatively-recent valid cached info for this
        # tournament, use it. Otherwise we'll kick off a query ourselves.
        if (
            self._tournament_id in bui.app.classic.accounts.tournament_info
            and bui.app.classic.accounts.tournament_info[self._tournament_id][
                'valid'
            ]
            and (
                bui.apptime()
                - bui.app.classic.accounts.tournament_info[self._tournament_id][
                    'timeReceived'
                ]
                < 60 * 5
            )
        ):
            try:
                info = bui.app.classic.accounts.tournament_info[
                    self._tournament_id
                ]
                self._seconds_remaining = max(
                    0,
                    info['timeRemaining']
                    - int((bui.apptime() - info['timeReceived'])),
                )
                self._have_valid_data = True
                self._last_query_time = bui.apptime()
            except Exception:
                logging.exception('Error using valid tourney data.')
                self._have_valid_data = False
        else:
            self._have_valid_data = False

        self._fg_state = bui.app.fg_state
        self._running_query = False
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()
        self._restore_state()

    def _on_tournament_query_response(
        self, data: dict[str, Any] | None
    ) -> None:
        assert bui.app.classic is not None
        accounts = bui.app.classic.accounts
        self._running_query = False
        if data is not None:
            data = data['t']  # This used to be the whole payload.
            accounts.cache_tournament_info(data)
            self._seconds_remaining = accounts.tournament_info[
                self._tournament_id
            ]['timeRemaining']
            self._have_valid_data = True

    def _save_state(self) -> None:
        if not self.root_widget:
            return
        sel = self.root_widget.get_selected_child()
        if sel == self._pay_with_ad_btn:
            sel_name = 'Ad'
        elif sel == self._practice_button:
            sel_name = 'Practice'
        else:
            sel_name = 'Tickets'
        cfg = bui.app.config
        cfg['Tournament Pay Selection'] = sel_name
        cfg.commit()

    def _restore_state(self) -> None:
        sel_name = bui.app.config.get('Tournament Pay Selection', 'Tickets')
        if sel_name == 'Ad' and self._pay_with_ad_btn is not None:
            sel = self._pay_with_ad_btn
        elif sel_name == 'Practice' and self._practice_button is not None:
            sel = self._practice_button
        else:
            sel = self._pay_with_tickets_button
        bui.containerwidget(edit=self.root_widget, selected_child=sel)

    def _update(self) -> None:
        plus = bui.app.plus
        assert plus is not None
        classic = bui.app.classic
        assert classic is not None

        # We may outlive our widgets.
        if not self.root_widget:
            return

        # If we've been foregrounded/backgrounded we need to re-grab data.
        if self._fg_state != bui.app.fg_state:
            self._fg_state = bui.app.fg_state
            self._have_valid_data = False

        # If we need to run another tournament query, do so.
        if not self._running_query and (
            (self._last_query_time is None)
            or (not self._have_valid_data)
            or (bui.apptime() - self._last_query_time > 30.0)
        ):
            plus.tournament_query(
                args={
                    'source': (
                        'entry window'
                        if self._tournament_activity is None
                        else 'retry entry window'
                    )
                },
                callback=bui.WeakCall(self._on_tournament_query_response),
            )
            self._last_query_time = bui.apptime()
            self._running_query = True

        # Grab the latest info on our tourney.
        assert bui.app.classic is not None
        self._tournament_info = bui.app.classic.accounts.tournament_info[
            self._tournament_id
        ]

        # If we don't have valid data always show a '-' for time.
        if not self._have_valid_data:
            bui.textwidget(edit=self._time_remaining_text, text='-')
        else:
            if self._seconds_remaining is not None:
                self._seconds_remaining = max(0, self._seconds_remaining - 1)
                bui.textwidget(
                    edit=self._time_remaining_text,
                    text=bui.timestring(self._seconds_remaining, centi=False),
                )

        # Keep price up-to-date and update the button with it.
        if self._purchase_price_name is not None:
            self._purchase_price = (
                0
                if self._purchase_price_name == 'FREE-WOOT'
                else plus.get_v1_account_misc_read_val(
                    self._purchase_price_name, None
                )
            )

        # HACK - this is always free now, so just have this say 'PLAY'
        bui.textwidget(
            edit=self._ticket_cost_text,
            text=(
                bui.Lstr(resource='playText')
                # if self._purchase_price == 0
                # else bui.Lstr(
                #     resource='getTicketsWindow.ticketsText',
                #     subs=[
                #         (
                #             '${COUNT}',
                #             (
                #                 str(self._purchase_price)
                #                 if self._purchase_price is not None
                #                 else '?'
                #             ),
                #         )
                #     ],
                # )
            ),
            # text=(
            #     bui.Lstr(resource='getTicketsWindow.freeText')
            #     if self._purchase_price == 0
            #     else bui.Lstr(
            #         resource='getTicketsWindow.ticketsText',
            #         subs=[
            #             (
            #                 '${COUNT}',
            #                 (
            #                     str(self._purchase_price)
            #                     if self._purchase_price is not None
            #                     else '?'
            #                 ),
            #             )
            #         ],
            #     )
            # ),
            position=(
                self._ticket_cost_text_position_free
                if self._purchase_price == 0
                else self._ticket_cost_text_position
            ),
            scale=1.0 if self._purchase_price == 0 else 0.6,
        )

        bui.textwidget(
            edit=self._free_plays_remaining_text,
            # text=(
            #     ''
            #     if (
            #         self._tournament_info['freeTriesRemaining'] in [None, 0]
            #         or self._purchase_price != 0
            #     )
            #     else '' + str(self._tournament_info['freeTriesRemaining'])
            # ),
            text='',  # No longer relevant.
        )

        bui.imagewidget(
            edit=self._ticket_img,
            opacity=0.0 if self._purchase_price == 0 else 1.0,
            position=(
                self._ticket_img_pos_free
                if self._purchase_price == 0
                else self._ticket_img_pos
            ),
        )

        if self._do_ad_btn:
            enabled = plus.ads.have_incentivized_ad()
            have_ad_tries_remaining = (
                self._tournament_info['adTriesRemaining'] is not None
                and self._tournament_info['adTriesRemaining'] > 0
            )
            bui.textwidget(
                edit=self._ad_text,
                position=(
                    self._ad_text_position_remaining
                    if have_ad_tries_remaining
                    else self._ad_text_position
                ),
                color=(0, 1, 0) if enabled else (0.5, 0.5, 0.5),
            )
            bui.imagewidget(
                edit=self._pay_with_ad_img, opacity=1.0 if enabled else 0.2
            )
            bui.buttonwidget(
                edit=self._pay_with_ad_btn,
                color=(0.5, 0.7, 0.2) if enabled else (0.5, 0.5, 0.5),
            )
            ad_plays_remaining_text = (
                ''
                if not have_ad_tries_remaining
                else '' + str(self._tournament_info['adTriesRemaining'])
            )
            bui.textwidget(
                edit=self._ad_plays_remaining_text,
                text=ad_plays_remaining_text,
                color=(0, 0.8, 0) if enabled else (0.4, 0.4, 0.4),
            )

        try:
            t_str = str(classic.tickets)
        except Exception:
            t_str = '?'
        if self._get_tickets_button:
            bui.buttonwidget(
                edit=self._get_tickets_button,
                label=bui.charstr(bui.SpecialChar.TICKET) + t_str,
            )
        if self._ticket_count_text:
            bui.textwidget(
                edit=self._ticket_count_text,
                text=bui.charstr(bui.SpecialChar.TICKET) + t_str,
            )

    def _launch(self, practice: bool = False) -> None:
        assert bui.app.classic is not None
        if self._launched:
            return
        self._launched = True
        launched = False

        # If they gave us an existing, non-consistent practice activity,
        # just restart it.
        if (
            self._tournament_activity is not None
            and not practice == self._tournament_activity.session.submit_score
        ):
            try:
                if not practice:
                    bui.apptimer(0.1, bui.getsound('drumRollShort').play)
                    # bui.apptimer(0.1, bui.getsound('cashRegister').play)
                    bui.screenmessage(
                        bui.Lstr(
                            translate=(
                                'serverResponses',
                                'Entering tournament...',
                            )
                        ),
                        color=(0, 1, 0),
                    )
                bui.apptimer(0 if practice else 0.3, self._transition_out)
                launched = True
                with self._tournament_activity.context:
                    self._tournament_activity.end(
                        {'outcome': 'restart'}, force=True
                    )

            # We can hit exceptions here if _tournament_activity ends before
            # our restart attempt happens.
            # In this case we'll fall back to launching a new session.
            # This is not ideal since players will have to rejoin, etc.,
            # but it works for now.
            except Exception:
                logging.exception('Error restarting tournament activity.')

        # If we had no existing activity (or were unable to restart it)
        # launch a new session.
        if not launched:
            if not practice:
                bui.apptimer(0.1, bui.getsound('drumRollShort').play)
                # bui.apptimer(0.1, bui.getsound('cashRegister').play)
                bui.screenmessage(
                    bui.Lstr(
                        translate=('serverResponses', 'Entering tournament...')
                    ),
                    color=(0, 1, 0),
                )
            bui.apptimer(
                0 if practice else 1.0,
                lambda: (
                    bui.app.classic.launch_coop_game(
                        self._tournament_info['game'],
                        args={
                            'min_players': self._tournament_info['minPlayers'],
                            'max_players': self._tournament_info['maxPlayers'],
                            'tournament_id': self._tournament_id,
                            'submit_score': not practice,
                        },
                    )
                    if bui.app.classic is not None
                    else None
                ),
            )
            bui.apptimer(0 if practice else 1.25, self._transition_out)

    def _on_pay_with_tickets_press(self) -> None:

        plus = bui.app.plus
        assert plus is not None
        classic = bui.app.classic
        assert classic is not None

        # If we're already entering, ignore.
        if self._entering:
            return

        if not self._have_valid_data:
            bui.screenmessage(
                bui.Lstr(resource='tournamentCheckingStateText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # If we don't have a price.
        if self._purchase_price is None:
            bui.screenmessage(
                bui.Lstr(resource='tournamentCheckingStateText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Deny if it looks like the tourney has ended.
        if self._seconds_remaining == 0:
            bui.screenmessage(
                bui.Lstr(resource='tournamentEndedText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        # Deny if we don't have enough tickets.
        ticket_count: int | None
        try:
            ticket_count = classic.tickets
        except Exception:
            # FIXME: should add a bui.NotSignedInError we can use here.
            ticket_count = None
        ticket_cost = self._purchase_price
        if ticket_count is not None and ticket_count < ticket_cost:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='notEnoughTicketsText'),
                color=(1, 0, 0),
            )
            # gettickets.show_get_tickets_prompt()
            self._transition_out()
            return

        cur_time = bui.apptime()
        self._last_ticket_press_time = cur_time

        if self._purchase_name is not None:
            assert isinstance(ticket_cost, int)
            plus.in_game_purchase(self._purchase_name, ticket_cost)

        self._entering = True
        plus.add_v1_account_transaction(
            {
                'type': 'ENTER_TOURNAMENT',
                'fee': self._fee,
                'tournamentID': self._tournament_id,
            }
        )
        plus.run_v1_account_transactions()
        self._launch()

    def _on_pay_with_ad_press(self) -> None:
        # If we're already entering, ignore.
        if self._entering:
            return

        if not self._have_valid_data:
            bui.screenmessage(
                bui.Lstr(resource='tournamentCheckingStateText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Deny if it looks like the tourney has ended.
        if self._seconds_remaining == 0:
            bui.screenmessage(
                bui.Lstr(resource='tournamentEndedText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        cur_time = bui.apptime()
        if cur_time - self._last_ad_press_time > 5.0:
            self._last_ad_press_time = cur_time
            assert bui.app.plus is not None
            bui.app.plus.ads.show_ad_2(
                'tournament_entry',
                on_completion_call=bui.WeakCall(self._on_ad_complete),
            )

    def _on_practice_press(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # If we're already entering, ignore.
        if self._entering:
            return

        # Deny if it looks like the tourney has ended.
        if self._seconds_remaining == 0:
            bui.screenmessage(
                bui.Lstr(resource='tournamentEndedText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        self._entering = True
        self._launch(practice=True)

    def _on_ad_complete(self, actually_showed: bool) -> None:
        plus = bui.app.plus
        assert plus is not None
        assert bui.app.classic is not None

        # Make sure any transactions the ad added got locally applied
        # (rewards added, etc.).
        plus.run_v1_account_transactions()

        # If we're already entering the tourney, ignore.
        if self._entering:
            return

        if not actually_showed:
            return

        # This should have awarded us the tournament_entry_ad purchase;
        # make sure that's present.
        # (otherwise the server will ignore our tournament entry anyway)
        if 'tournament_entry_ad' not in bui.app.classic.purchases:
            print('no tournament_entry_ad purchase present in _on_ad_complete')
            bui.screenmessage(bui.Lstr(resource='errorText'), color=(1, 0, 0))
            bui.getsound('error').play()
            return

        self._entering = True
        plus.add_v1_account_transaction(
            {
                'type': 'ENTER_TOURNAMENT',
                'fee': 'ad',
                'tournamentID': self._tournament_id,
            }
        )
        plus.run_v1_account_transactions()
        self._launch()

    def _on_cancel(self) -> None:
        plus = bui.app.plus
        assert plus is not None
        assert bui.app.classic is not None
        # Don't allow canceling for several seconds after poking an enter
        # button if it looks like we're waiting on a purchase or entering
        # the tournament.
        if (
            (bui.apptime() - self._last_ticket_press_time < 6.0)
            and self._purchase_name is not None
            and (
                plus.have_outstanding_v1_account_transactions()
                or self._purchase_name in bui.app.classic.purchases
                or self._entering
            )
        ):
            bui.getsound('error').play()
            return
        self._transition_out()

    def _transition_out(self) -> None:
        if not self.root_widget:
            return
        if not self._transitioning_out:
            self._transitioning_out = True
            self._save_state()
            bui.containerwidget(edit=self.root_widget, transition='out_scale')
            if self._on_close_call is not None:
                self._on_close_call()

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._on_cancel()
