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
"""Defines a popup window for entering tournaments."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui import popup

if TYPE_CHECKING:
    from typing import Any, Tuple, Callable, Optional, Dict


class TournamentEntryWindow(popup.PopupWindow):
    """Popup window for entering tournaments."""

    def __init__(self,
                 tournament_id: str,
                 tournament_activity: ba.Activity = None,
                 position: Tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float = None,
                 offset: Tuple[float, float] = (0.0, 0.0),
                 on_close_call: Callable[[], Any] = None):
        # Needs some tidying.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        ba.set_analytics_screen('Tournament Entry Window')

        self._tournament_id = tournament_id
        self._tournament_info = (ba.app.tournament_info[self._tournament_id])

        # Set a few vars depending on the tourney fee.
        self._fee = self._tournament_info['fee']
        self._allow_ads = self._tournament_info['allowAds']
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
        else:
            if self._fee != 0:
                raise ValueError('invalid fee: ' + str(self._fee))
            self._purchase_name = 'tournament_entry_0'
            self._purchase_price_name = 'price.tournament_entry_0'

        self._purchase_price: Optional[int] = None

        self._on_close_call = on_close_call
        if scale is None:
            uiscale = ba.app.ui.uiscale
            scale = (2.3 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)
        self._delegate = delegate
        self._transitioning_out = False

        self._tournament_activity = tournament_activity

        self._width = 340
        self._height = 220

        bg_color = (0.5, 0.4, 0.6)

        # Creates our root_widget.
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=bg_color,
                                   offset=offset,
                                   toolbar_visibility='menu_currency')

        self._last_ad_press_time = -9999.0
        self._last_ticket_press_time = -9999.0
        self._entering = False
        self._launched = False

        # Show the ad button only if we support ads *and* it has a level 1 fee.
        self._do_ad_btn = (_ba.has_video_ads() and self._allow_ads)

        x_offs = 0 if self._do_ad_btn else 85

        self._cancel_button = ba.buttonwidget(parent=self.root_widget,
                                              position=(20, self._height - 30),
                                              size=(50, 50),
                                              scale=0.5,
                                              label='',
                                              color=bg_color,
                                              on_activate_call=self._on_cancel,
                                              autoselect=True,
                                              icon=ba.gettexture('crossOut'),
                                              iconscale=1.2)

        self._title_text = ba.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text=ba.Lstr(resource='tournamentEntryText'),
            maxwidth=200,
            color=(1, 1, 1, 0.4))

        btn = self._pay_with_tickets_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(30 + x_offs, 60),
            autoselect=True,
            button_type='square',
            size=(120, 120),
            label='',
            on_activate_call=self._on_pay_with_tickets_press)
        self._ticket_img_pos = (50 + x_offs, 94)
        self._ticket_img_pos_free = (50 + x_offs, 80)
        self._ticket_img = ba.imagewidget(parent=self.root_widget,
                                          draw_controller=btn,
                                          size=(80, 80),
                                          position=self._ticket_img_pos,
                                          texture=ba.gettexture('tickets'))
        self._ticket_cost_text_position = (87 + x_offs, 88)
        self._ticket_cost_text_position_free = (87 + x_offs, 120)
        self._ticket_cost_text = ba.textwidget(
            parent=self.root_widget,
            draw_controller=btn,
            position=self._ticket_cost_text_position,
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text='',
            maxwidth=95,
            color=(0, 1, 0))
        self._free_plays_remaining_text = ba.textwidget(
            parent=self.root_widget,
            draw_controller=btn,
            position=(87 + x_offs, 78),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.33,
            text='',
            maxwidth=95,
            color=(0, 0.8, 0))
        self._pay_with_ad_btn: Optional[ba.Widget]
        if self._do_ad_btn:
            btn = self._pay_with_ad_btn = ba.buttonwidget(
                parent=self.root_widget,
                position=(190, 60),
                autoselect=True,
                button_type='square',
                size=(120, 120),
                label='',
                on_activate_call=self._on_pay_with_ad_press)
            self._pay_with_ad_img = ba.imagewidget(parent=self.root_widget,
                                                   draw_controller=btn,
                                                   size=(80, 80),
                                                   position=(210, 94),
                                                   texture=ba.gettexture('tv'))

            self._ad_text_position = (251, 88)
            self._ad_text_position_remaining = (251, 92)
            have_ad_tries_remaining = (
                self._tournament_info['adTriesRemaining'] is not None)
            self._ad_text = ba.textwidget(
                parent=self.root_widget,
                draw_controller=btn,
                position=self._ad_text_position_remaining
                if have_ad_tries_remaining else self._ad_text_position,
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.6,
                text=ba.Lstr(resource='watchAVideoText',
                             fallback_resource='watchAnAdText'),
                maxwidth=95,
                color=(0, 1, 0))
            ad_plays_remaining_text = (
                '' if not have_ad_tries_remaining else '' +
                str(self._tournament_info['adTriesRemaining']))
            self._ad_plays_remaining_text = ba.textwidget(
                parent=self.root_widget,
                draw_controller=btn,
                position=(251, 78),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.33,
                text=ad_plays_remaining_text,
                maxwidth=95,
                color=(0, 0.8, 0))

            ba.textwidget(parent=self.root_widget,
                          position=(self._width * 0.5, 120),
                          size=(0, 0),
                          h_align='center',
                          v_align='center',
                          scale=0.6,
                          text=ba.Lstr(resource='orText',
                                       subs=[('${A}', ''), ('${B}', '')]),
                          maxwidth=35,
                          color=(1, 1, 1, 0.5))
        else:
            self._pay_with_ad_btn = None

        self._get_tickets_button: Optional[ba.Widget]
        if not ba.app.ui.use_toolbars:
            self._get_tickets_button = ba.buttonwidget(
                parent=self.root_widget,
                position=(self._width - 190 + 110, 15),
                autoselect=True,
                scale=0.6,
                size=(120, 60),
                textcolor=(0.2, 1, 0.2),
                label=ba.charstr(ba.SpecialChar.TICKET),
                color=(0.6, 0.4, 0.7),
                on_activate_call=self._on_get_tickets_press)
        else:
            self._get_tickets_button = None

        self._seconds_remaining = None

        ba.containerwidget(edit=self.root_widget,
                           cancel_button=self._cancel_button)

        # Let's also ask the server for info about this tournament
        # (time remaining, etc) so we can show the user time remaining,
        # disallow entry if time has run out, etc.
        xoffs = 104 if ba.app.ui.use_toolbars else 0
        self._time_remaining_text = ba.textwidget(parent=self.root_widget,
                                                  position=(70 + xoffs, 23),
                                                  size=(0, 0),
                                                  h_align='center',
                                                  v_align='center',
                                                  text='-',
                                                  scale=0.65,
                                                  maxwidth=100,
                                                  flatness=1.0,
                                                  color=(0.7, 0.7, 0.7))
        self._time_remaining_label_text = ba.textwidget(
            parent=self.root_widget,
            position=(70 + xoffs, 40),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='coopSelectWindow.timeRemainingText'),
            scale=0.45,
            flatness=1.0,
            maxwidth=100,
            color=(0.7, 0.7, 0.7))

        self._last_query_time: Optional[float] = None

        # If there seems to be a relatively-recent valid cached info for this
        # tournament, use it. Otherwise we'll kick off a query ourselves.
        if (self._tournament_id in ba.app.tournament_info
                and ba.app.tournament_info[self._tournament_id]['valid'] and
            (ba.time(ba.TimeType.REAL, ba.TimeFormat.MILLISECONDS) -
             ba.app.tournament_info[self._tournament_id]['timeReceived'] <
             1000 * 60 * 5)):
            try:
                info = ba.app.tournament_info[self._tournament_id]
                self._seconds_remaining = max(
                    0, info['timeRemaining'] - int(
                        (ba.time(ba.TimeType.REAL, ba.TimeFormat.MILLISECONDS)
                         - info['timeReceived']) / 1000))
                self._have_valid_data = True
                self._last_query_time = ba.time(ba.TimeType.REAL)
            except Exception:
                ba.print_exception('error using valid tourney data')
                self._have_valid_data = False
        else:
            self._have_valid_data = False

        self._fg_state = ba.app.fg_state
        self._running_query = False
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)
        self._update()
        self._restore_state()

    def _on_tournament_query_response(self, data: Optional[Dict[str,
                                                                Any]]) -> None:
        from ba.internal import cache_tournament_info
        self._running_query = False
        if data is not None:
            data = data['t']  # This used to be the whole payload.
            cache_tournament_info(data)
            self._seconds_remaining = ba.app.tournament_info[
                self._tournament_id]['timeRemaining']
            self._have_valid_data = True

    def _save_state(self) -> None:
        if not self.root_widget:
            return
        sel = self.root_widget.get_selected_child()
        if sel == self._pay_with_ad_btn:
            sel_name = 'Ad'
        else:
            sel_name = 'Tickets'
        cfg = ba.app.config
        cfg['Tournament Pay Selection'] = sel_name
        cfg.commit()

    def _restore_state(self) -> None:
        sel_name = ba.app.config.get('Tournament Pay Selection', 'Tickets')
        if sel_name == 'Ad' and self._pay_with_ad_btn is not None:
            sel = self._pay_with_ad_btn
        else:
            sel = self._pay_with_tickets_button
        ba.containerwidget(edit=self.root_widget, selected_child=sel)

    def _update(self) -> None:
        # We may outlive our widgets.
        if not self.root_widget:
            return

        # If we've been foregrounded/backgrounded we need to re-grab data.
        if self._fg_state != ba.app.fg_state:
            self._fg_state = ba.app.fg_state
            self._have_valid_data = False

        # If we need to run another tournament query, do so.
        if not self._running_query and (
            (self._last_query_time is None) or (not self._have_valid_data) or
            (ba.time(ba.TimeType.REAL) - self._last_query_time > 30.0)):
            _ba.tournament_query(args={
                'source':
                    'entry window' if self._tournament_activity is None else
                    'retry entry window'
            },
                                 callback=ba.WeakCall(
                                     self._on_tournament_query_response))
            self._last_query_time = ba.time(ba.TimeType.REAL)
            self._running_query = True

        # Grab the latest info on our tourney.
        self._tournament_info = ba.app.tournament_info[self._tournament_id]

        # If we don't have valid data always show a '-' for time.
        if not self._have_valid_data:
            ba.textwidget(edit=self._time_remaining_text, text='-')
        else:
            if self._seconds_remaining is not None:
                self._seconds_remaining = max(0, self._seconds_remaining - 1)
                ba.textwidget(edit=self._time_remaining_text,
                              text=ba.timestring(
                                  self._seconds_remaining * 1000,
                                  centi=False,
                                  timeformat=ba.TimeFormat.MILLISECONDS))

        # Keep price up-to-date and update the button with it.
        self._purchase_price = _ba.get_account_misc_read_val(
            self._purchase_price_name, None)

        ba.textwidget(
            edit=self._ticket_cost_text,
            text=(ba.Lstr(resource='getTicketsWindow.freeText')
                  if self._purchase_price == 0 else ba.Lstr(
                      resource='getTicketsWindow.ticketsText',
                      subs=[('${COUNT}', str(self._purchase_price)
                             if self._purchase_price is not None else '?')])),
            position=self._ticket_cost_text_position_free
            if self._purchase_price == 0 else self._ticket_cost_text_position,
            scale=1.0 if self._purchase_price == 0 else 0.6)

        ba.textwidget(
            edit=self._free_plays_remaining_text,
            text='' if
            (self._tournament_info['freeTriesRemaining'] in [None, 0]
             or self._purchase_price != 0) else '' +
            str(self._tournament_info['freeTriesRemaining']))

        ba.imagewidget(edit=self._ticket_img,
                       opacity=0.2 if self._purchase_price == 0 else 1.0,
                       position=self._ticket_img_pos_free
                       if self._purchase_price == 0 else self._ticket_img_pos)

        if self._do_ad_btn:
            enabled = _ba.have_incentivized_ad()
            have_ad_tries_remaining = (
                self._tournament_info['adTriesRemaining'] is not None
                and self._tournament_info['adTriesRemaining'] > 0)
            ba.textwidget(edit=self._ad_text,
                          position=self._ad_text_position_remaining if
                          have_ad_tries_remaining else self._ad_text_position,
                          color=(0, 1, 0) if enabled else (0.5, 0.5, 0.5))
            ba.imagewidget(edit=self._pay_with_ad_img,
                           opacity=1.0 if enabled else 0.2)
            ba.buttonwidget(edit=self._pay_with_ad_btn,
                            color=(0.5, 0.7, 0.2) if enabled else
                            (0.5, 0.5, 0.5))
            ad_plays_remaining_text = (
                '' if not have_ad_tries_remaining else '' +
                str(self._tournament_info['adTriesRemaining']))
            ba.textwidget(edit=self._ad_plays_remaining_text,
                          text=ad_plays_remaining_text,
                          color=(0, 0.8, 0) if enabled else (0.4, 0.4, 0.4))

        try:
            t_str = str(_ba.get_account_ticket_count())
        except Exception:
            t_str = '?'
        if self._get_tickets_button is not None:
            ba.buttonwidget(edit=self._get_tickets_button,
                            label=ba.charstr(ba.SpecialChar.TICKET) + t_str)

    def _launch(self) -> None:
        if self._launched:
            return
        self._launched = True
        launched = False

        # If they gave us an existing activity, just restart it.
        if self._tournament_activity is not None:
            try:
                ba.timer(0.1,
                         lambda: ba.playsound(ba.getsound('cashRegister')),
                         timetype=ba.TimeType.REAL)
                with ba.Context(self._tournament_activity):
                    self._tournament_activity.end({'outcome': 'restart'},
                                                  force=True)
                ba.timer(0.3, self._transition_out, timetype=ba.TimeType.REAL)
                launched = True
                ba.screenmessage(ba.Lstr(translate=('serverResponses',
                                                    'Entering tournament...')),
                                 color=(0, 1, 0))

            # We can hit exceptions here if _tournament_activity ends before
            # our restart attempt happens.
            # In this case we'll fall back to launching a new session.
            # This is not ideal since players will have to rejoin, etc.,
            # but it works for now.
            except Exception:
                ba.print_exception('Error restarting tournament activity.')

        # If we had no existing activity (or were unable to restart it)
        # launch a new session.
        if not launched:
            ba.timer(0.1,
                     lambda: ba.playsound(ba.getsound('cashRegister')),
                     timetype=ba.TimeType.REAL)
            ba.timer(
                1.0,
                lambda: ba.app.launch_coop_game(
                    self._tournament_info['game'],
                    args={
                        'min_players': self._tournament_info['minPlayers'],
                        'max_players': self._tournament_info['maxPlayers'],
                        'tournament_id': self._tournament_id
                    }),
                timetype=ba.TimeType.REAL)
            ba.timer(0.7, self._transition_out, timetype=ba.TimeType.REAL)
            ba.screenmessage(ba.Lstr(translate=('serverResponses',
                                                'Entering tournament...')),
                             color=(0, 1, 0))

    def _on_pay_with_tickets_press(self) -> None:
        from bastd.ui import getcurrency

        # If we're already entering, ignore.
        if self._entering:
            return

        if not self._have_valid_data:
            ba.screenmessage(ba.Lstr(resource='tournamentCheckingStateText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        # If we don't have a price.
        if self._purchase_price is None:
            ba.screenmessage(ba.Lstr(resource='tournamentCheckingStateText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        # Deny if it looks like the tourney has ended.
        if self._seconds_remaining == 0:
            ba.screenmessage(ba.Lstr(resource='tournamentEndedText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        # Deny if we don't have enough tickets.
        ticket_count: Optional[int]
        try:
            ticket_count = _ba.get_account_ticket_count()
        except Exception:
            # FIXME: should add a ba.NotSignedInError we can use here.
            ticket_count = None
        ticket_cost = self._purchase_price
        if ticket_count is not None and ticket_count < ticket_cost:
            getcurrency.show_get_tickets_prompt()
            ba.playsound(ba.getsound('error'))
            return

        cur_time = ba.time(ba.TimeType.REAL, ba.TimeFormat.MILLISECONDS)
        self._last_ticket_press_time = cur_time
        assert isinstance(ticket_cost, int)
        _ba.in_game_purchase(self._purchase_name, ticket_cost)

        self._entering = True
        _ba.add_transaction({
            'type': 'ENTER_TOURNAMENT',
            'fee': self._fee,
            'tournamentID': self._tournament_id
        })
        _ba.run_transactions()
        self._launch()

    def _on_pay_with_ad_press(self) -> None:
        from ba.internal import show_ad_2

        # If we're already entering, ignore.
        if self._entering:
            return

        if not self._have_valid_data:
            ba.screenmessage(ba.Lstr(resource='tournamentCheckingStateText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        # Deny if it looks like the tourney has ended.
        if self._seconds_remaining == 0:
            ba.screenmessage(ba.Lstr(resource='tournamentEndedText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        cur_time = ba.time(ba.TimeType.REAL)
        if cur_time - self._last_ad_press_time > 5.0:
            self._last_ad_press_time = cur_time
            show_ad_2('tournament_entry',
                      on_completion_call=ba.WeakCall(self._on_ad_complete))

    def _on_ad_complete(self, actually_showed: bool) -> None:

        # Make sure any transactions the ad added got locally applied
        # (rewards added, etc.).
        _ba.run_transactions()

        # If we're already entering the tourney, ignore.
        if self._entering:
            return

        if not actually_showed:
            return

        # This should have awarded us the tournament_entry_ad purchase;
        # make sure that's present.
        # (otherwise the server will ignore our tournament entry anyway)
        if not _ba.get_purchased('tournament_entry_ad'):
            print('no tournament_entry_ad purchase present in _on_ad_complete')
            ba.screenmessage(ba.Lstr(resource='errorText'), color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        self._entering = True
        _ba.add_transaction({
            'type': 'ENTER_TOURNAMENT',
            'fee': 'ad',
            'tournamentID': self._tournament_id
        })
        _ba.run_transactions()
        self._launch()

    def _on_get_tickets_press(self) -> None:
        from bastd.ui import getcurrency

        # If we're already entering, ignore presses.
        if self._entering:
            return

        # Bring up get-tickets window and then kill ourself (we're on the
        # overlay layer so we'd show up above it).
        getcurrency.GetCurrencyWindow(modal=True,
                                      origin_widget=self._get_tickets_button)
        self._transition_out()

    def _on_cancel(self) -> None:

        # Don't allow canceling for several seconds after poking an enter
        # button if it looks like we're waiting on a purchase or entering
        # the tournament.
        if ((ba.time(ba.TimeType.REAL, ba.TimeFormat.MILLISECONDS) -
             self._last_ticket_press_time < 6000) and
            (_ba.have_outstanding_transactions()
             or _ba.get_purchased(self._purchase_name) or self._entering)):
            ba.playsound(ba.getsound('error'))
            return
        self._transition_out()

    def _transition_out(self) -> None:
        if not self.root_widget:
            return
        if not self._transitioning_out:
            self._transitioning_out = True
            self._save_state()
            ba.containerwidget(edit=self.root_widget, transition='out_scale')
            if self._on_close_call is not None:
                self._on_close_call()

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._on_cancel()
