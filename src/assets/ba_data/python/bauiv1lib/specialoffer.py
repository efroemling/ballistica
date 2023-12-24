# Released under the MIT License. See LICENSE for details.
#
"""UI for presenting sales/etc."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class SpecialOfferWindow(bui.Window):
    """Window for presenting sales/etc."""

    def __init__(self, offer: dict[str, Any], transition: str = 'in_right'):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from babase import SpecialChar
        from bauiv1lib.store import item as storeitemui

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        store = bui.app.classic.store

        self._cancel_delay = offer.get('cancelDelay', 0)

        # First thing: if we're offering pro or an IAP, see if we have a
        # price for it.
        # If not, abort and go into zombie mode (the user should never see
        # us that way).

        real_price: str | None

        # Misnomer: 'pro' actually means offer 'pro_sale'.
        if offer['item'] in ['pro', 'pro_fullprice']:
            real_price = plus.get_price(
                'pro' if offer['item'] == 'pro_fullprice' else 'pro_sale'
            )
            if real_price is None and bui.app.env.debug:
                print('NOTE: Faking prices for debug build.')
                real_price = '$1.23'
            zombie = real_price is None
        elif isinstance(offer['price'], str):
            # (a string price implies IAP id)
            real_price = plus.get_price(offer['price'])
            if real_price is None and bui.app.env.debug:
                print('NOTE: Faking price for debug build.')
                real_price = '$1.23'
            zombie = real_price is None
        else:
            real_price = None
            zombie = False
        if real_price is None:
            real_price = '?'

        if offer['item'] in ['pro', 'pro_fullprice']:
            self._offer_item = 'pro'
        else:
            self._offer_item = offer['item']

        # If we wanted a real price but didn't find one, go zombie.
        if zombie:
            return

        # This can pop up suddenly, so lets block input for 1 second.
        bui.lock_all_input()
        bui.apptimer(1.0, bui.unlock_all_input)
        bui.getsound('ding').play()
        bui.apptimer(0.3, bui.getsound('ooh').play)
        self._offer = copy.deepcopy(offer)
        self._width = 580
        self._height = 590
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition=transition,
                scale=(
                    1.2
                    if uiscale is bui.UIScale.SMALL
                    else 1.15
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(0, -15)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
            )
        )
        self._is_bundle_sale = False
        try:
            if offer['item'] in ['pro', 'pro_fullprice']:
                original_price_str = plus.get_price('pro')
                if original_price_str is None:
                    original_price_str = '?'
                new_price_str = plus.get_price('pro_sale')
                if new_price_str is None:
                    new_price_str = '?'
                percent_off_text = ''
            else:
                # If the offer includes bonus tickets, it's a bundle-sale.
                if (
                    'bonusTickets' in offer
                    and offer['bonusTickets'] is not None
                ):
                    self._is_bundle_sale = True
                original_price = plus.get_v1_account_misc_read_val(
                    'price.' + self._offer_item, 9999
                )

                # For pure ticket prices we can show a percent-off.
                if isinstance(offer['price'], int):
                    new_price = offer['price']
                    tchar = bui.charstr(SpecialChar.TICKET)
                    original_price_str = tchar + str(original_price)
                    new_price_str = tchar + str(new_price)
                    percent_off = int(
                        round(
                            100.0 - (float(new_price) / original_price) * 100.0
                        )
                    )
                    percent_off_text = ' ' + bui.Lstr(
                        resource='store.salePercentText'
                    ).evaluate().replace('${PERCENT}', str(percent_off))
                else:
                    original_price_str = new_price_str = '?'
                    percent_off_text = ''

        except Exception:
            logging.exception('Error setting up special-offer: %s.', offer)
            original_price_str = new_price_str = '?'
            percent_off_text = ''

        # If its a bundle sale, change the title.
        if self._is_bundle_sale:
            sale_text = bui.Lstr(
                resource='store.saleBundleText',
                fallback_resource='store.saleText',
            ).evaluate()
        else:
            # For full pro we say 'Upgrade?' since its not really a sale.
            if offer['item'] == 'pro_fullprice':
                sale_text = bui.Lstr(
                    resource='store.upgradeQuestionText',
                    fallback_resource='store.saleExclaimText',
                ).evaluate()
            else:
                sale_text = bui.Lstr(
                    resource='store.saleExclaimText',
                    fallback_resource='store.saleText',
                ).evaluate()

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 40),
            size=(0, 0),
            text=sale_text
            + (
                (' ' + bui.Lstr(resource='store.oneTimeOnlyText').evaluate())
                if self._offer['oneTimeOnly']
                else ''
            )
            + percent_off_text,
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.9 - 220,
            scale=1.4,
            color=(0.3, 1, 0.3),
        )

        self._flash_on = False
        self._flashing_timer: bui.AppTimer | None = bui.AppTimer(
            0.05, bui.WeakCall(self._flash_cycle), repeat=True
        )
        bui.apptimer(0.6, bui.WeakCall(self._stop_flashing))

        size = store.get_store_item_display_size(self._offer_item)
        display: dict[str, Any] = {}
        storeitemui.instantiate_store_item_display(
            self._offer_item,
            display,
            parent_widget=self._root_widget,
            b_pos=(
                self._width * 0.5
                - size[0] * 0.5
                + 10
                - ((size[0] * 0.5 + 30) if self._is_bundle_sale else 0),
                self._height * 0.5
                - size[1] * 0.5
                + 20
                + (20 if self._is_bundle_sale else 0),
            ),
            b_width=size[0],
            b_height=size[1],
            button=not self._is_bundle_sale,
        )

        # Wire up the parts we need.
        if self._is_bundle_sale:
            self._plus_text = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, self._height * 0.5 + 50),
                size=(0, 0),
                text='+',
                h_align='center',
                v_align='center',
                maxwidth=self._width * 0.9,
                scale=1.4,
                color=(0.5, 0.5, 0.5),
            )
            self._plus_tickets = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 + 120, self._height * 0.5 + 50),
                size=(0, 0),
                text=bui.charstr(SpecialChar.TICKET_BACKING)
                + str(offer['bonusTickets']),
                h_align='center',
                v_align='center',
                maxwidth=self._width * 0.9,
                scale=2.5,
                color=(0.2, 1, 0.2),
            )
            self._price_text = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, 150),
                size=(0, 0),
                text=real_price,
                h_align='center',
                v_align='center',
                maxwidth=self._width * 0.9,
                scale=1.4,
                color=(0.2, 1, 0.2),
            )
            # Total-value if they supplied it.
            total_worth_item = offer.get('valueItem', None)
            if total_worth_item is not None:
                price = plus.get_price(total_worth_item)
                total_worth_price = (
                    store.get_clean_price(price) if price is not None else None
                )
                if total_worth_price is not None:
                    total_worth_text = bui.Lstr(
                        resource='store.totalWorthText',
                        subs=[('${TOTAL_WORTH}', total_worth_price)],
                    )
                    self._total_worth_text = bui.textwidget(
                        parent=self._root_widget,
                        text=total_worth_text,
                        position=(self._width * 0.5, 210),
                        scale=0.9,
                        maxwidth=self._width * 0.7,
                        size=(0, 0),
                        h_align='center',
                        v_align='center',
                        shadow=1.0,
                        flatness=1.0,
                        color=(0.3, 1, 1),
                    )

        elif offer['item'] == 'pro_fullprice':
            # for full-price pro we simply show full price
            bui.textwidget(edit=display['price_widget'], text=real_price)
            bui.buttonwidget(
                edit=display['button'], on_activate_call=self._purchase
            )
        else:
            # Show old/new prices otherwise (for pro sale).
            bui.buttonwidget(
                edit=display['button'], on_activate_call=self._purchase
            )
            bui.imagewidget(edit=display['price_slash_widget'], opacity=1.0)
            bui.textwidget(
                edit=display['price_widget_left'], text=original_price_str
            )
            bui.textwidget(
                edit=display['price_widget_right'], text=new_price_str
            )

        # Add ticket button only if this is ticket-purchasable.
        if isinstance(offer.get('price'), int):
            self._get_tickets_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(self._width - 125, self._height - 68),
                size=(90, 55),
                scale=1.0,
                button_type='square',
                color=(0.7, 0.5, 0.85),
                textcolor=(0.2, 1, 0.2),
                autoselect=True,
                label=bui.Lstr(resource='getTicketsWindow.titleText'),
                on_activate_call=self._on_get_more_tickets_press,
            )

            self._ticket_text_update_timer = bui.AppTimer(
                1.0, bui.WeakCall(self._update_tickets_text), repeat=True
            )
            self._update_tickets_text()

        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(50, 40)
            if self._is_bundle_sale
            else (self._width * 0.5 - 75, 40),
            size=(150, 60),
            scale=1.0,
            on_activate_call=self._cancel,
            autoselect=True,
            label=bui.Lstr(resource='noThanksText'),
        )
        self._cancel_countdown_text = bui.textwidget(
            parent=self._root_widget,
            text='',
            position=(50 + 150 + 20, 40 + 27)
            if self._is_bundle_sale
            else (self._width * 0.5 - 75 + 150 + 20, 40 + 27),
            scale=1.1,
            size=(0, 0),
            h_align='left',
            v_align='center',
            shadow=1.0,
            flatness=1.0,
            color=(0.6, 0.5, 0.5),
        )
        self._update_cancel_button_graphics()

        if self._is_bundle_sale:
            self._purchase_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(self._width - 200, 40),
                size=(150, 60),
                scale=1.0,
                on_activate_call=self._purchase,
                autoselect=True,
                label=bui.Lstr(resource='store.purchaseText'),
            )

        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=self._cancel_button,
            start_button=self._purchase_button
            if self._is_bundle_sale
            else None,
            selected_child=self._purchase_button
            if self._is_bundle_sale
            else display['button'],
        )

    def _stop_flashing(self) -> None:
        self._flashing_timer = None
        bui.textwidget(edit=self._title_text, color=(0.3, 1, 0.3))

    def _flash_cycle(self) -> None:
        if not self._root_widget:
            return
        self._flash_on = not self._flash_on
        bui.textwidget(
            edit=self._title_text,
            color=(0.3, 1, 0.3) if self._flash_on else (1, 0.5, 0),
        )

    def _update_cancel_button_graphics(self) -> None:
        bui.buttonwidget(
            edit=self._cancel_button,
            color=(0.5, 0.5, 0.5)
            if self._cancel_delay > 0
            else (0.7, 0.4, 0.34),
            textcolor=(0.5, 0.5, 0.5)
            if self._cancel_delay > 0
            else (0.9, 0.9, 1.0),
        )
        bui.textwidget(
            edit=self._cancel_countdown_text,
            text=str(self._cancel_delay) if self._cancel_delay > 0 else '',
        )

    def _update(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # If we've got seconds left on our countdown, update it.
        if self._cancel_delay > 0:
            self._cancel_delay = max(0, self._cancel_delay - 1)
            self._update_cancel_button_graphics()

        can_die = False

        # We go away if we see that our target item is owned.
        if self._offer_item == 'pro':
            assert bui.app.classic is not None
            if bui.app.classic.accounts.have_pro():
                can_die = True
        else:
            if plus.get_purchased(self._offer_item):
                can_die = True

        if can_die:
            self._transition_out('out_left')

    def _transition_out(self, transition: str = 'out_left') -> None:
        # Also clear any pending-special-offer we've stored at this point.
        cfg = bui.app.config
        if 'pendingSpecialOffer' in cfg:
            del cfg['pendingSpecialOffer']
            cfg.commit()

        bui.containerwidget(edit=self._root_widget, transition=transition)

    def _update_tickets_text(self) -> None:
        from babase import SpecialChar

        plus = bui.app.plus
        assert plus is not None

        if not self._root_widget:
            return
        sval: str | bui.Lstr
        if plus.get_v1_account_state() == 'signed_in':
            sval = bui.charstr(SpecialChar.TICKET) + str(
                plus.get_v1_account_ticket_count()
            )
        else:
            sval = bui.Lstr(resource='getTicketsWindow.titleText')
        bui.buttonwidget(edit=self._get_tickets_button, label=sval)

    def _on_get_more_tickets_press(self) -> None:
        from bauiv1lib import account
        from bauiv1lib import getcurrency

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        getcurrency.GetCurrencyWindow(modal=True).get_root_widget()

    def _purchase(self) -> None:
        from bauiv1lib import getcurrency
        from bauiv1lib import confirm

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        store = bui.app.classic.store

        if self._offer['item'] == 'pro':
            plus.purchase('pro_sale')
        elif self._offer['item'] == 'pro_fullprice':
            plus.purchase('pro')
        elif self._is_bundle_sale:
            # With bundle sales, the price is the name of the IAP.
            plus.purchase(self._offer['price'])
        else:
            ticket_count: int | None
            try:
                ticket_count = plus.get_v1_account_ticket_count()
            except Exception:
                ticket_count = None
            if ticket_count is not None and ticket_count < self._offer['price']:
                getcurrency.show_get_tickets_prompt()
                bui.getsound('error').play()
                return

            def do_it() -> None:
                assert plus is not None

                plus.in_game_purchase(
                    'offer:' + str(self._offer['id']), self._offer['price']
                )

            bui.getsound('swish').play()
            confirm.ConfirmWindow(
                bui.Lstr(
                    resource='store.purchaseConfirmText',
                    subs=[
                        (
                            '${ITEM}',
                            store.get_store_item_name_translated(
                                self._offer['item']
                            ),
                        )
                    ],
                ),
                width=400,
                height=120,
                action=do_it,
                ok_text=bui.Lstr(
                    resource='store.purchaseText', fallback_resource='okText'
                ),
            )

    def _cancel(self) -> None:
        if self._cancel_delay > 0:
            bui.getsound('error').play()
            return
        self._transition_out('out_right')


def show_offer() -> bool:
    """(internal)"""
    try:
        from bauiv1lib import feedback

        plus = bui.app.plus
        assert plus is not None

        app = bui.app
        if app.classic is None:
            raise RuntimeError(
                'Classic feature-set is required to show offers.'
            )

        # Space things out a bit so we don't hit the poor user with an
        # ad and then an in-game offer.
        has_been_long_enough_since_ad = True
        if app.classic.ads.last_ad_completion_time is not None and (
            bui.apptime() - app.classic.ads.last_ad_completion_time < 30.0
        ):
            has_been_long_enough_since_ad = False

        if (
            app.classic.special_offer is not None
            and has_been_long_enough_since_ad
        ):
            # Special case: for pro offers, store this in our prefs so
            # we can re-show it if the user kills us (set phasers to
            # 'NAG'!!!).
            if app.classic.special_offer.get('item') == 'pro_fullprice':
                cfg = app.config
                cfg['pendingSpecialOffer'] = {
                    'a': plus.get_v1_account_public_login_id(),
                    'o': app.classic.special_offer,
                }
                cfg.commit()

            if app.classic.special_offer['item'] == 'rating':
                # Go with a native thing if we've got one.
                if bui.native_review_request_supported():
                    bui.native_review_request()
                else:
                    if app.ui_v1.available:
                        feedback.ask_for_rating()
            else:
                if app.ui_v1.available:
                    SpecialOfferWindow(app.classic.special_offer)

            app.classic.special_offer = None
            return True
    except Exception:
        logging.exception('Error showing offer.')

    return False
