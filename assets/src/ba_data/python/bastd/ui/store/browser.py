# Released under the MIT License. See LICENSE for details.
#
"""UI for browsing the store."""
# pylint: disable=too-many-lines
from __future__ import annotations

import time
import copy
import math
import logging
import weakref
from enum import Enum
from threading import Thread
from typing import TYPE_CHECKING

from efro.error import CommunicationError
import bacommon.cloud
import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence

MERCH_LINK_KEY = 'Merch Link'


class StoreBrowserWindow(ba.Window):
    """Window for browsing the store."""

    class TabID(Enum):
        """Our available tab types."""

        EXTRAS = 'extras'
        MAPS = 'maps'
        MINIGAMES = 'minigames'
        CHARACTERS = 'characters'
        ICONS = 'icons'

    def __init__(
        self,
        transition: str = 'in_right',
        modal: bool = False,
        show_tab: StoreBrowserWindow.TabID | None = None,
        on_close_call: Callable[[], Any] | None = None,
        back_location: str | None = None,
        origin_widget: ba.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from bastd.ui.tabs import TabRow
        from ba import SpecialChar

        app = ba.app
        uiscale = app.ui.uiscale

        ba.set_analytics_screen('Store Window')

        scale_origin: tuple[float, float] | None

        # If they provided an origin-widget, scale up from that.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self.button_infos: dict[str, dict[str, Any]] | None = None
        self.update_buttons_timer: ba.Timer | None = None
        self._status_textwidget_update_timer = None

        self._back_location = back_location
        self._on_close_call = on_close_call
        self._show_tab = show_tab
        self._modal = modal
        self._width = 1240 if uiscale is ba.UIScale.SMALL else 1040
        self._x_inset = x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (
            578
            if uiscale is ba.UIScale.SMALL
            else 645
            if uiscale is ba.UIScale.MEDIUM
            else 800
        )
        self._current_tab: StoreBrowserWindow.TabID | None = None
        extra_top = 30 if uiscale is ba.UIScale.SMALL else 0

        self._request: Any = None
        self._r = 'store'
        self._last_buy_time: float | None = None

        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height + extra_top),
                transition=transition,
                toolbar_visibility='menu_full',
                scale=(
                    1.3
                    if uiscale is ba.UIScale.SMALL
                    else 0.9
                    if uiscale is ba.UIScale.MEDIUM
                    else 0.8
                ),
                scale_origin_stack_offset=scale_origin,
                stack_offset=(
                    (0, -5)
                    if uiscale is ba.UIScale.SMALL
                    else (0, 0)
                    if uiscale is ba.UIScale.MEDIUM
                    else (0, 0)
                ),
            )
        )

        self._back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(70 + x_inset, self._height - 74),
            size=(140, 60),
            scale=1.1,
            autoselect=True,
            label=ba.Lstr(resource='doneText' if self._modal else 'backText'),
            button_type=None if self._modal else 'back',
            on_activate_call=self._back,
        )
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        self._ticket_count_text: ba.Widget | None = None
        self._get_tickets_button: ba.Widget | None = None

        if ba.app.allow_ticket_purchases:
            self._get_tickets_button = ba.buttonwidget(
                parent=self._root_widget,
                size=(210, 65),
                on_activate_call=self._on_get_more_tickets_press,
                autoselect=True,
                scale=0.9,
                text_scale=1.4,
                left_widget=self._back_button,
                color=(0.7, 0.5, 0.85),
                textcolor=(0.2, 1.0, 0.2),
                label=ba.Lstr(resource='getTicketsWindow.titleText'),
            )
        else:
            self._ticket_count_text = ba.textwidget(
                parent=self._root_widget,
                size=(210, 64),
                color=(0.2, 1.0, 0.2),
                h_align='center',
                v_align='center',
            )

        # Move this dynamically to keep it out of the way of the party icon.
        self._update_get_tickets_button_pos()
        self._get_ticket_pos_update_timer = ba.Timer(
            1.0,
            ba.WeakCall(self._update_get_tickets_button_pos),
            repeat=True,
            timetype=ba.TimeType.REAL,
        )
        if self._get_tickets_button:
            ba.widget(
                edit=self._back_button, right_widget=self._get_tickets_button
            )
        self._ticket_text_update_timer = ba.Timer(
            1.0,
            ba.WeakCall(self._update_tickets_text),
            timetype=ba.TimeType.REAL,
            repeat=True,
        )
        self._update_tickets_text()

        app = ba.app
        if app.platform in ['mac', 'ios'] and app.subplatform == 'appstore':
            ba.buttonwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - 70, 16),
                size=(230, 50),
                scale=0.65,
                on_activate_call=ba.WeakCall(self._restore_purchases),
                color=(0.35, 0.3, 0.4),
                selectable=False,
                textcolor=(0.55, 0.5, 0.6),
                label=ba.Lstr(resource='getTicketsWindow.restorePurchasesText'),
            )

        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 44),
            size=(0, 0),
            color=app.ui.title_color,
            scale=1.5,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='storeText'),
            maxwidth=420,
        )

        if not self._modal:
            ba.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=ba.charstr(SpecialChar.BACK),
            )

        scroll_buffer_h = 130 + 2 * x_inset
        tab_buffer_h = 250 + 2 * x_inset

        tabs_def = [
            (self.TabID.EXTRAS, ba.Lstr(resource=self._r + '.extrasText')),
            (self.TabID.MAPS, ba.Lstr(resource=self._r + '.mapsText')),
            (
                self.TabID.MINIGAMES,
                ba.Lstr(resource=self._r + '.miniGamesText'),
            ),
            (
                self.TabID.CHARACTERS,
                ba.Lstr(resource=self._r + '.charactersText'),
            ),
            (self.TabID.ICONS, ba.Lstr(resource=self._r + '.iconsText')),
        ]

        self._tab_row = TabRow(
            self._root_widget,
            tabs_def,
            pos=(tab_buffer_h * 0.5, self._height - 130),
            size=(self._width - tab_buffer_h, 50),
            on_select_call=self._set_tab,
        )

        self._purchasable_count_widgets: dict[
            StoreBrowserWindow.TabID, dict[str, Any]
        ] = {}

        # Create our purchasable-items tags and have them update over time.
        for tab_id, tab in self._tab_row.tabs.items():
            pos = tab.position
            size = tab.size
            button = tab.button
            rad = 10
            center = (pos[0] + 0.1 * size[0], pos[1] + 0.9 * size[1])
            img = ba.imagewidget(
                parent=self._root_widget,
                position=(center[0] - rad * 1.04, center[1] - rad * 1.15),
                size=(rad * 2.2, rad * 2.2),
                texture=ba.gettexture('circleShadow'),
                color=(1, 0, 0),
            )
            txt = ba.textwidget(
                parent=self._root_widget,
                position=center,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=1.4 * rad,
                scale=0.6,
                shadow=1.0,
                flatness=1.0,
            )
            rad = 20
            sale_img = ba.imagewidget(
                parent=self._root_widget,
                position=(center[0] - rad, center[1] - rad),
                size=(rad * 2, rad * 2),
                draw_controller=button,
                texture=ba.gettexture('circleZigZag'),
                color=(0.5, 0, 1.0),
            )
            sale_title_text = ba.textwidget(
                parent=self._root_widget,
                position=(center[0], center[1] + 0.24 * rad),
                size=(0, 0),
                h_align='center',
                v_align='center',
                draw_controller=button,
                maxwidth=1.4 * rad,
                scale=0.6,
                shadow=0.0,
                flatness=1.0,
                color=(0, 1, 0),
            )
            sale_time_text = ba.textwidget(
                parent=self._root_widget,
                position=(center[0], center[1] - 0.29 * rad),
                size=(0, 0),
                h_align='center',
                v_align='center',
                draw_controller=button,
                maxwidth=1.4 * rad,
                scale=0.4,
                shadow=0.0,
                flatness=1.0,
                color=(0, 1, 0),
            )
            self._purchasable_count_widgets[tab_id] = {
                'img': img,
                'text': txt,
                'sale_img': sale_img,
                'sale_title_text': sale_title_text,
                'sale_time_text': sale_time_text,
            }
        self._tab_update_timer = ba.Timer(
            1.0,
            ba.WeakCall(self._update_tabs),
            timetype=ba.TimeType.REAL,
            repeat=True,
        )
        self._update_tabs()

        if self._get_tickets_button:
            last_tab_button = self._tab_row.tabs[tabs_def[-1][0]].button
            ba.widget(
                edit=self._get_tickets_button, down_widget=last_tab_button
            )
            ba.widget(
                edit=last_tab_button,
                up_widget=self._get_tickets_button,
                right_widget=self._get_tickets_button,
            )

        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180

        self._scrollwidget: ba.Widget | None = None
        self._status_textwidget: ba.Widget | None = None
        self._restore_state()

    def _update_get_tickets_button_pos(self) -> None:
        uiscale = ba.app.ui.uiscale
        pos = (
            self._width
            - 252
            - (
                self._x_inset
                + (
                    47
                    if uiscale is ba.UIScale.SMALL
                    and ba.internal.is_party_icon_visible()
                    else 0
                )
            ),
            self._height - 70,
        )
        if self._get_tickets_button:
            ba.buttonwidget(edit=self._get_tickets_button, position=pos)
        if self._ticket_count_text:
            ba.textwidget(edit=self._ticket_count_text, position=pos)

    def _restore_purchases(self) -> None:
        from bastd.ui import account

        if ba.internal.get_v1_account_state() != 'signed_in':
            account.show_sign_in_prompt()
        else:
            ba.internal.restore_purchases()

    def _update_tabs(self) -> None:
        from ba.internal import (
            get_available_sale_time,
            get_available_purchase_count,
        )

        if not self._root_widget:
            return
        for tab_id, tab_data in list(self._purchasable_count_widgets.items()):
            sale_time = get_available_sale_time(tab_id.value)

            if sale_time is not None:
                ba.textwidget(
                    edit=tab_data['sale_title_text'],
                    text=ba.Lstr(resource='store.saleText'),
                )
                ba.textwidget(
                    edit=tab_data['sale_time_text'],
                    text=ba.timestring(
                        sale_time,
                        centi=False,
                        timeformat=ba.TimeFormat.MILLISECONDS,
                    ),
                )
                ba.imagewidget(edit=tab_data['sale_img'], opacity=1.0)
                count = 0
            else:
                ba.textwidget(edit=tab_data['sale_title_text'], text='')
                ba.textwidget(edit=tab_data['sale_time_text'], text='')
                ba.imagewidget(edit=tab_data['sale_img'], opacity=0.0)
                count = get_available_purchase_count(tab_id.value)

            if count > 0:
                ba.textwidget(edit=tab_data['text'], text=str(count))
                ba.imagewidget(edit=tab_data['img'], opacity=1.0)
            else:
                ba.textwidget(edit=tab_data['text'], text='')
                ba.imagewidget(edit=tab_data['img'], opacity=0.0)

    def _update_tickets_text(self) -> None:
        from ba import SpecialChar

        if not self._root_widget:
            return
        sval: str | ba.Lstr
        if ba.internal.get_v1_account_state() == 'signed_in':
            sval = ba.charstr(SpecialChar.TICKET) + str(
                ba.internal.get_v1_account_ticket_count()
            )
        else:
            sval = ba.Lstr(resource='getTicketsWindow.titleText')
        if self._get_tickets_button:
            ba.buttonwidget(edit=self._get_tickets_button, label=sval)
        if self._ticket_count_text:
            ba.textwidget(edit=self._ticket_count_text, text=sval)

    def _set_tab(self, tab_id: TabID) -> None:
        if self._current_tab is tab_id:
            return
        self._current_tab = tab_id

        # We wanna preserve our current tab between runs.
        cfg = ba.app.config
        cfg['Store Tab'] = tab_id.value
        cfg.commit()

        # Update tab colors based on which is selected.
        self._tab_row.update_appearance(tab_id)

        # (Re)create scroll widget.
        if self._scrollwidget:
            self._scrollwidget.delete()

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(
                (self._width - self._scroll_width) * 0.5,
                self._height - self._scroll_height - 79 - 48,
            ),
            size=(self._scroll_width, self._scroll_height),
            claims_left_right=True,
            claims_tab=True,
            selection_loops_to_parent=True,
        )

        # NOTE: this stuff is modified by the _Store class.
        # Should maybe clean that up.
        self.button_infos = {}
        self.update_buttons_timer = None

        # Show status over top.
        if self._status_textwidget:
            self._status_textwidget.delete()
        self._status_textwidget = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            color=(1, 0.7, 1, 0.5),
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource=self._r + '.loadingText'),
            maxwidth=self._scroll_width * 0.9,
        )

        class _Request:
            def __init__(self, window: StoreBrowserWindow):
                self._window = weakref.ref(window)
                data = {'tab': tab_id.value}
                ba.timer(
                    0.1,
                    ba.WeakCall(self._on_response, data),
                    timetype=ba.TimeType.REAL,
                )

            def _on_response(self, data: dict[str, Any] | None) -> None:
                # FIXME: clean this up.
                # pylint: disable=protected-access
                window = self._window()
                if window is not None and (window._request is self):
                    window._request = None
                    # noinspection PyProtectedMember
                    window._on_response(data)

        # Kick off a server request.
        self._request = _Request(self)

    # Actually start the purchase locally.
    def _purchase_check_result(
        self, item: str, is_ticket_purchase: bool, result: dict[str, Any] | None
    ) -> None:
        if result is None:
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(
                ba.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
        else:
            if is_ticket_purchase:
                if result['allow']:
                    price = ba.internal.get_v1_account_misc_read_val(
                        'price.' + item, None
                    )
                    if (
                        price is None
                        or not isinstance(price, int)
                        or price <= 0
                    ):
                        print(
                            'Error; got invalid local price of',
                            price,
                            'for item',
                            item,
                        )
                        ba.playsound(ba.getsound('error'))
                    else:
                        ba.playsound(ba.getsound('click01'))
                        ba.internal.in_game_purchase(item, price)
                else:
                    if result['reason'] == 'versionTooOld':
                        ba.playsound(ba.getsound('error'))
                        ba.screenmessage(
                            ba.Lstr(
                                resource='getTicketsWindow.versionTooOldText'
                            ),
                            color=(1, 0, 0),
                        )
                    else:
                        ba.playsound(ba.getsound('error'))
                        ba.screenmessage(
                            ba.Lstr(
                                resource='getTicketsWindow.unavailableText'
                            ),
                            color=(1, 0, 0),
                        )
            # Real in-app purchase.
            else:
                if result['allow']:
                    ba.internal.purchase(item)
                else:
                    if result['reason'] == 'versionTooOld':
                        ba.playsound(ba.getsound('error'))
                        ba.screenmessage(
                            ba.Lstr(
                                resource='getTicketsWindow.versionTooOldText'
                            ),
                            color=(1, 0, 0),
                        )
                    else:
                        ba.playsound(ba.getsound('error'))
                        ba.screenmessage(
                            ba.Lstr(
                                resource='getTicketsWindow.unavailableText'
                            ),
                            color=(1, 0, 0),
                        )

    def _do_purchase_check(
        self, item: str, is_ticket_purchase: bool = False
    ) -> None:
        from ba.internal import master_server_get

        # Here we ping the server to ask if it's valid for us to
        # purchase this. Better to fail now than after we've
        # paid locally.
        app = ba.app
        master_server_get(
            'bsAccountPurchaseCheck',
            {
                'item': item,
                'platform': app.platform,
                'subplatform': app.subplatform,
                'version': app.version,
                'buildNumber': app.build_number,
                'purchaseType': 'ticket' if is_ticket_purchase else 'real',
            },
            callback=ba.WeakCall(
                self._purchase_check_result, item, is_ticket_purchase
            ),
        )

    def buy(self, item: str) -> None:
        """Attempt to purchase the provided item."""
        from ba.internal import (
            get_available_sale_time,
            get_store_item_name_translated,
        )
        from bastd.ui import account
        from bastd.ui.confirm import ConfirmWindow
        from bastd.ui import getcurrency

        # Prevent pressing buy within a few seconds of the last press
        # (gives the buttons time to disable themselves and whatnot).
        curtime = ba.time(ba.TimeType.REAL)
        if (
            self._last_buy_time is not None
            and (curtime - self._last_buy_time) < 2.0
        ):
            ba.playsound(ba.getsound('error'))
        else:
            if ba.internal.get_v1_account_state() != 'signed_in':
                account.show_sign_in_prompt()
            else:
                self._last_buy_time = curtime

                # Merch is a special case - just a link.
                if item == 'merch':
                    url = ba.app.config.get('Merch Link')
                    if isinstance(url, str):
                        ba.open_url(url)

                # Pro is an actual IAP, and the rest are ticket purchases.
                elif item == 'pro':
                    ba.playsound(ba.getsound('click01'))

                    # Purchase either pro or pro_sale depending on whether
                    # there is a sale going on.
                    self._do_purchase_check(
                        'pro'
                        if get_available_sale_time('extras') is None
                        else 'pro_sale'
                    )
                else:
                    price = ba.internal.get_v1_account_misc_read_val(
                        'price.' + item, None
                    )
                    our_tickets = ba.internal.get_v1_account_ticket_count()
                    if price is not None and our_tickets < price:
                        ba.playsound(ba.getsound('error'))
                        getcurrency.show_get_tickets_prompt()
                    else:

                        def do_it() -> None:
                            self._do_purchase_check(
                                item, is_ticket_purchase=True
                            )

                        ba.playsound(ba.getsound('swish'))
                        ConfirmWindow(
                            ba.Lstr(
                                resource='store.purchaseConfirmText',
                                subs=[
                                    (
                                        '${ITEM}',
                                        get_store_item_name_translated(item),
                                    )
                                ],
                            ),
                            width=400,
                            height=120,
                            action=do_it,
                            ok_text=ba.Lstr(
                                resource='store.purchaseText',
                                fallback_resource='okText',
                            ),
                        )

    def _print_already_own(self, charname: str) -> None:
        ba.screenmessage(
            ba.Lstr(
                resource=self._r + '.alreadyOwnText',
                subs=[('${NAME}', charname)],
            ),
            color=(1, 0, 0),
        )
        ba.playsound(ba.getsound('error'))

    def update_buttons(self) -> None:
        """Update our buttons."""
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from ba.internal import get_available_sale_time
        from ba import SpecialChar

        if not self._root_widget:
            return
        import datetime

        sales_raw = ba.internal.get_v1_account_misc_read_val('sales', {})
        sales = {}
        try:
            # Look at the current set of sales; filter any with time remaining.
            for sale_item, sale_info in list(sales_raw.items()):
                to_end = (
                    datetime.datetime.utcfromtimestamp(sale_info['e'])
                    - datetime.datetime.utcnow()
                ).total_seconds()
                if to_end > 0:
                    sales[sale_item] = {
                        'to_end': to_end,
                        'original_price': sale_info['op'],
                    }
        except Exception:
            ba.print_exception('Error parsing sales.')

        assert self.button_infos is not None
        for b_type, b_info in self.button_infos.items():

            if b_type == 'merch':
                purchased = False
            elif b_type in ['upgrades.pro', 'pro']:
                purchased = ba.app.accounts_v1.have_pro()
            else:
                purchased = ba.internal.get_purchased(b_type)

            sale_opacity = 0.0
            sale_title_text: str | ba.Lstr = ''
            sale_time_text: str | ba.Lstr = ''

            if purchased:
                title_color = (0.8, 0.7, 0.9, 1.0)
                color = (0.63, 0.55, 0.78)
                extra_image_opacity = 0.5
                call = ba.WeakCall(self._print_already_own, b_info['name'])
                price_text = ''
                price_text_left = ''
                price_text_right = ''
                show_purchase_check = True
                description_color: Sequence[float] = (0.4, 1.0, 0.4, 0.4)
                description_color2: Sequence[float] = (0.0, 0.0, 0.0, 0.0)
                price_color = (0.5, 1, 0.5, 0.3)
            else:
                title_color = (0.7, 0.9, 0.7, 1.0)
                color = (0.4, 0.8, 0.1)
                extra_image_opacity = 1.0
                call = b_info['call'] if 'call' in b_info else None
                if b_type == 'merch':
                    price_text = ''
                    price_text_left = ''
                    price_text_right = ''
                elif b_type in ['upgrades.pro', 'pro']:
                    sale_time = get_available_sale_time('extras')
                    if sale_time is not None:
                        priceraw = ba.internal.get_price('pro')
                        price_text_left = (
                            priceraw if priceraw is not None else '?'
                        )
                        priceraw = ba.internal.get_price('pro_sale')
                        price_text_right = (
                            priceraw if priceraw is not None else '?'
                        )
                        sale_opacity = 1.0
                        price_text = ''
                        sale_title_text = ba.Lstr(resource='store.saleText')
                        sale_time_text = ba.timestring(
                            sale_time,
                            centi=False,
                            timeformat=ba.TimeFormat.MILLISECONDS,
                        )
                    else:
                        priceraw = ba.internal.get_price('pro')
                        price_text = priceraw if priceraw is not None else '?'
                        price_text_left = ''
                        price_text_right = ''
                else:
                    price = ba.internal.get_v1_account_misc_read_val(
                        'price.' + b_type, 0
                    )

                    # Color the button differently if we cant afford this.
                    if ba.internal.get_v1_account_state() == 'signed_in':
                        if ba.internal.get_v1_account_ticket_count() < price:
                            color = (0.6, 0.61, 0.6)
                    price_text = ba.charstr(ba.SpecialChar.TICKET) + str(
                        ba.internal.get_v1_account_misc_read_val(
                            'price.' + b_type, '?'
                        )
                    )
                    price_text_left = ''
                    price_text_right = ''

                    # TESTING:
                    if b_type in sales:
                        sale_opacity = 1.0
                        price_text_left = ba.charstr(SpecialChar.TICKET) + str(
                            sales[b_type]['original_price']
                        )
                        price_text_right = price_text
                        price_text = ''
                        sale_title_text = ba.Lstr(resource='store.saleText')
                        sale_time_text = ba.timestring(
                            int(sales[b_type]['to_end'] * 1000),
                            centi=False,
                            timeformat=ba.TimeFormat.MILLISECONDS,
                        )

                description_color = (0.5, 1.0, 0.5)
                description_color2 = (0.3, 1.0, 1.0)
                price_color = (0.2, 1, 0.2, 1.0)
                show_purchase_check = False

            if 'title_text' in b_info:
                ba.textwidget(edit=b_info['title_text'], color=title_color)
            if 'purchase_check' in b_info:
                ba.imagewidget(
                    edit=b_info['purchase_check'],
                    opacity=1.0 if show_purchase_check else 0.0,
                )
            if 'price_widget' in b_info:
                ba.textwidget(
                    edit=b_info['price_widget'],
                    text=price_text,
                    color=price_color,
                )
            if 'price_widget_left' in b_info:
                ba.textwidget(
                    edit=b_info['price_widget_left'], text=price_text_left
                )
            if 'price_widget_right' in b_info:
                ba.textwidget(
                    edit=b_info['price_widget_right'], text=price_text_right
                )
            if 'price_slash_widget' in b_info:
                ba.imagewidget(
                    edit=b_info['price_slash_widget'], opacity=sale_opacity
                )
            if 'sale_bg_widget' in b_info:
                ba.imagewidget(
                    edit=b_info['sale_bg_widget'], opacity=sale_opacity
                )
            if 'sale_title_widget' in b_info:
                ba.textwidget(
                    edit=b_info['sale_title_widget'], text=sale_title_text
                )
            if 'sale_time_widget' in b_info:
                ba.textwidget(
                    edit=b_info['sale_time_widget'], text=sale_time_text
                )
            if 'button' in b_info:
                ba.buttonwidget(
                    edit=b_info['button'], color=color, on_activate_call=call
                )
            if 'extra_backings' in b_info:
                for bck in b_info['extra_backings']:
                    ba.imagewidget(
                        edit=bck, color=color, opacity=extra_image_opacity
                    )
            if 'extra_images' in b_info:
                for img in b_info['extra_images']:
                    ba.imagewidget(edit=img, opacity=extra_image_opacity)
            if 'extra_texts' in b_info:
                for etxt in b_info['extra_texts']:
                    ba.textwidget(edit=etxt, color=description_color)
            if 'extra_texts_2' in b_info:
                for etxt in b_info['extra_texts_2']:
                    ba.textwidget(edit=etxt, color=description_color2)
            if 'descriptionText' in b_info:
                ba.textwidget(
                    edit=b_info['descriptionText'], color=description_color
                )

    def _on_response(self, data: dict[str, Any] | None) -> None:
        # pylint: disable=too-many-statements

        # clear status text..
        if self._status_textwidget:
            self._status_textwidget.delete()
            self._status_textwidget_update_timer = None

        if data is None:
            self._status_textwidget = ba.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, self._height * 0.5),
                size=(0, 0),
                scale=1.3,
                transition_delay=0.1,
                color=(1, 0.3, 0.3, 1.0),
                h_align='center',
                v_align='center',
                text=ba.Lstr(resource=self._r + '.loadErrorText'),
                maxwidth=self._scroll_width * 0.9,
            )
        else:

            class _Store:
                def __init__(
                    self,
                    store_window: StoreBrowserWindow,
                    sdata: dict[str, Any],
                    width: float,
                ):
                    from ba.internal import (
                        get_store_item_display_size,
                        get_store_layout,
                    )

                    self._store_window = store_window
                    self._width = width
                    store_data = get_store_layout()
                    self._tab = sdata['tab']
                    self._sections = copy.deepcopy(store_data[sdata['tab']])
                    self._height: float | None = None

                    uiscale = ba.app.ui.uiscale

                    # Pre-calc a few things and add them to store-data.
                    for section in self._sections:
                        if self._tab == 'characters':
                            dummy_name = 'characters.foo'
                        elif self._tab == 'extras':
                            dummy_name = 'pro'
                        elif self._tab == 'maps':
                            dummy_name = 'maps.foo'
                        elif self._tab == 'icons':
                            dummy_name = 'icons.foo'
                        else:
                            dummy_name = ''
                        section['button_size'] = get_store_item_display_size(
                            dummy_name
                        )
                        section['v_spacing'] = (
                            -25
                            if (
                                self._tab == 'extras'
                                and uiscale is ba.UIScale.SMALL
                            )
                            else -17
                            if self._tab == 'characters'
                            else 0
                        )
                        if 'title' not in section:
                            section['title'] = ''
                        section['x_offs'] = (
                            130
                            if self._tab == 'extras'
                            else 270
                            if self._tab == 'maps'
                            else 0
                        )
                        section['y_offs'] = (
                            20
                            if (
                                self._tab == 'extras'
                                and uiscale is ba.UIScale.SMALL
                                and ba.app.config.get('Merch Link')
                            )
                            else 55
                            if (
                                self._tab == 'extras'
                                and uiscale is ba.UIScale.SMALL
                            )
                            else -20
                            if self._tab == 'icons'
                            else 0
                        )

                def instantiate(
                    self, scrollwidget: ba.Widget, tab_button: ba.Widget
                ) -> None:
                    """Create the store."""
                    # pylint: disable=too-many-locals
                    # pylint: disable=too-many-branches
                    # pylint: disable=too-many-nested-blocks
                    from bastd.ui.store.item import (
                        instantiate_store_item_display,
                    )

                    title_spacing = 40
                    button_border = 20
                    button_spacing = 4
                    boffs_h = 40
                    self._height = 80.0

                    # Calc total height.
                    for i, section in enumerate(self._sections):
                        if section['title'] != '':
                            assert self._height is not None
                            self._height += title_spacing
                        b_width, b_height = section['button_size']
                        b_column_count = int(
                            math.floor(
                                (self._width - boffs_h - 20)
                                / (b_width + button_spacing)
                            )
                        )
                        b_row_count = int(
                            math.ceil(
                                float(len(section['items'])) / b_column_count
                            )
                        )
                        b_height_total = (
                            2 * button_border
                            + b_row_count * b_height
                            + (b_row_count - 1) * section['v_spacing']
                        )
                        self._height += b_height_total

                    assert self._height is not None
                    cnt2 = ba.containerwidget(
                        parent=scrollwidget,
                        scale=1.0,
                        size=(self._width, self._height),
                        background=False,
                        claims_left_right=True,
                        claims_tab=True,
                        selection_loops_to_parent=True,
                    )
                    v = self._height - 20

                    if self._tab == 'characters':
                        txt = ba.Lstr(
                            resource='store.howToSwitchCharactersText',
                            subs=[
                                (
                                    '${SETTINGS}',
                                    ba.Lstr(
                                        resource=(
                                            'accountSettingsWindow.titleText'
                                        )
                                    ),
                                ),
                                (
                                    '${PLAYER_PROFILES}',
                                    ba.Lstr(
                                        resource=(
                                            'playerProfilesWindow.titleText'
                                        )
                                    ),
                                ),
                            ],
                        )
                        ba.textwidget(
                            parent=cnt2,
                            text=txt,
                            size=(0, 0),
                            position=(self._width * 0.5, self._height - 28),
                            h_align='center',
                            v_align='center',
                            color=(0.7, 1, 0.7, 0.4),
                            scale=0.7,
                            shadow=0,
                            flatness=1.0,
                            maxwidth=700,
                            transition_delay=0.4,
                        )
                    elif self._tab == 'icons':
                        txt = ba.Lstr(
                            resource='store.howToUseIconsText',
                            subs=[
                                (
                                    '${SETTINGS}',
                                    ba.Lstr(resource='mainMenu.settingsText'),
                                ),
                                (
                                    '${PLAYER_PROFILES}',
                                    ba.Lstr(
                                        resource=(
                                            'playerProfilesWindow.titleText'
                                        )
                                    ),
                                ),
                            ],
                        )
                        ba.textwidget(
                            parent=cnt2,
                            text=txt,
                            size=(0, 0),
                            position=(self._width * 0.5, self._height - 28),
                            h_align='center',
                            v_align='center',
                            color=(0.7, 1, 0.7, 0.4),
                            scale=0.7,
                            shadow=0,
                            flatness=1.0,
                            maxwidth=700,
                            transition_delay=0.4,
                        )
                    elif self._tab == 'maps':
                        assert self._width is not None
                        assert self._height is not None
                        txt = ba.Lstr(resource='store.howToUseMapsText')
                        ba.textwidget(
                            parent=cnt2,
                            text=txt,
                            size=(0, 0),
                            position=(self._width * 0.5, self._height - 28),
                            h_align='center',
                            v_align='center',
                            color=(0.7, 1, 0.7, 0.4),
                            scale=0.7,
                            shadow=0,
                            flatness=1.0,
                            maxwidth=700,
                            transition_delay=0.4,
                        )

                    prev_row_buttons: list | None = None
                    this_row_buttons = []

                    delay = 0.3
                    for section in self._sections:
                        if section['title'] != '':
                            ba.textwidget(
                                parent=cnt2,
                                position=(60, v - title_spacing * 0.8),
                                size=(0, 0),
                                scale=1.0,
                                transition_delay=delay,
                                color=(0.7, 0.9, 0.7, 1),
                                h_align='left',
                                v_align='center',
                                text=ba.Lstr(resource=section['title']),
                                maxwidth=self._width * 0.7,
                            )
                            v -= title_spacing
                        delay = max(0.100, delay - 0.100)
                        v -= button_border
                        b_width, b_height = section['button_size']
                        b_count = len(section['items'])
                        b_column_count = int(
                            math.floor(
                                (self._width - boffs_h - 20)
                                / (b_width + button_spacing)
                            )
                        )
                        col = 0
                        item: dict[str, Any]
                        assert self._store_window.button_infos is not None
                        for i, item_name in enumerate(section['items']):
                            item = self._store_window.button_infos[
                                item_name
                            ] = {}
                            item['call'] = ba.WeakCall(
                                self._store_window.buy, item_name
                            )
                            if 'x_offs' in section:
                                boffs_h2 = section['x_offs']
                            else:
                                boffs_h2 = 0

                            if 'y_offs' in section:
                                boffs_v2 = section['y_offs']
                            else:
                                boffs_v2 = 0
                            b_pos = (
                                boffs_h
                                + boffs_h2
                                + (b_width + button_spacing) * col,
                                v - b_height + boffs_v2,
                            )
                            instantiate_store_item_display(
                                item_name,
                                item,
                                parent_widget=cnt2,
                                b_pos=b_pos,
                                boffs_h=boffs_h,
                                b_width=b_width,
                                b_height=b_height,
                                boffs_h2=boffs_h2,
                                boffs_v2=boffs_v2,
                                delay=delay,
                            )
                            btn = item['button']
                            delay = max(0.1, delay - 0.1)
                            this_row_buttons.append(btn)

                            # Wire this button to the equivalent in the
                            # previous row.
                            if prev_row_buttons is not None:
                                # pylint: disable=unsubscriptable-object
                                if len(prev_row_buttons) > col:
                                    ba.widget(
                                        edit=btn,
                                        up_widget=prev_row_buttons[col],
                                    )
                                    ba.widget(
                                        edit=prev_row_buttons[col],
                                        down_widget=btn,
                                    )

                                    # If we're the last button in our row,
                                    # wire any in the previous row past
                                    # our position to go to us if down is
                                    # pressed.
                                    if (
                                        col + 1 == b_column_count
                                        or i == b_count - 1
                                    ):
                                        for b_prev in prev_row_buttons[
                                            col + 1 :
                                        ]:
                                            ba.widget(
                                                edit=b_prev, down_widget=btn
                                            )
                                else:
                                    ba.widget(
                                        edit=btn, up_widget=prev_row_buttons[-1]
                                    )
                            else:
                                ba.widget(edit=btn, up_widget=tab_button)

                            col += 1
                            if col == b_column_count or i == b_count - 1:
                                prev_row_buttons = this_row_buttons
                                this_row_buttons = []
                                col = 0
                                v -= b_height
                                if i < b_count - 1:
                                    v -= section['v_spacing']

                        v -= button_border

                    # Set a timer to update these buttons periodically as long
                    # as we're alive (so if we buy one it will grey out, etc).
                    self._store_window.update_buttons_timer = ba.Timer(
                        0.5,
                        ba.WeakCall(self._store_window.update_buttons),
                        repeat=True,
                        timetype=ba.TimeType.REAL,
                    )

                    # Also update them immediately.
                    self._store_window.update_buttons()

            if self._current_tab in (
                self.TabID.EXTRAS,
                self.TabID.MINIGAMES,
                self.TabID.CHARACTERS,
                self.TabID.MAPS,
                self.TabID.ICONS,
            ):
                store = _Store(self, data, self._scroll_width)
                assert self._scrollwidget is not None
                store.instantiate(
                    scrollwidget=self._scrollwidget,
                    tab_button=self._tab_row.tabs[self._current_tab].button,
                )
            else:
                cnt = ba.containerwidget(
                    parent=self._scrollwidget,
                    scale=1.0,
                    size=(self._scroll_width, self._scroll_height * 0.95),
                    background=False,
                    claims_left_right=True,
                    claims_tab=True,
                    selection_loops_to_parent=True,
                )
                self._status_textwidget = ba.textwidget(
                    parent=cnt,
                    position=(
                        self._scroll_width * 0.5,
                        self._scroll_height * 0.5,
                    ),
                    size=(0, 0),
                    scale=1.3,
                    transition_delay=0.1,
                    color=(1, 1, 0.3, 1.0),
                    h_align='center',
                    v_align='center',
                    text=ba.Lstr(resource=self._r + '.comingSoonText'),
                    maxwidth=self._scroll_width * 0.9,
                )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            selected_tab_ids = [
                tab_id
                for tab_id, tab in self._tab_row.tabs.items()
                if sel == tab.button
            ]
            if sel == self._get_tickets_button:
                sel_name = 'GetTickets'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            elif sel == self._back_button:
                sel_name = 'Back'
            elif selected_tab_ids:
                assert len(selected_tab_ids) == 1
                sel_name = f'Tab:{selected_tab_ids[0].value}'
            else:
                raise ValueError(f'unrecognized selection \'{sel}\'')
            ba.app.ui.window_states[type(self)] = {
                'sel_name': sel_name,
            }
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        from efro.util import enum_by_value

        try:
            sel: ba.Widget | None
            sel_name = ba.app.ui.window_states.get(type(self), {}).get(
                'sel_name'
            )
            assert isinstance(sel_name, (str, type(None)))

            try:
                current_tab = enum_by_value(
                    self.TabID, ba.app.config.get('Store Tab')
                )
            except ValueError:
                current_tab = self.TabID.CHARACTERS

            if self._show_tab is not None:
                current_tab = self._show_tab
            if sel_name == 'GetTickets' and self._get_tickets_button:
                sel = self._get_tickets_button
            elif sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                try:
                    sel_tab_id = enum_by_value(
                        self.TabID, sel_name.split(':')[-1]
                    )
                except ValueError:
                    sel_tab_id = self.TabID.CHARACTERS
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                sel = self._tab_row.tabs[current_tab].button

            # If we were requested to show a tab, select it too..
            if (
                self._show_tab is not None
                and self._show_tab in self._tab_row.tabs
            ):
                sel = self._tab_row.tabs[self._show_tab].button
            self._set_tab(current_tab)
            if sel is not None:
                ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')

    def _on_get_more_tickets_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import show_sign_in_prompt
        from bastd.ui.getcurrency import GetCurrencyWindow

        if ba.internal.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        window = GetCurrencyWindow(
            from_modal_store=self._modal,
            store_back_location=self._back_location,
        ).get_root_widget()
        if not self._modal:
            ba.app.ui.set_main_menu_window(window)

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.coop.browser import CoopBrowserWindow
        from bastd.ui.mainmenu import MainMenuWindow

        self._save_state()
        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if not self._modal:
            if self._back_location == 'CoopBrowserWindow':
                ba.app.ui.set_main_menu_window(
                    CoopBrowserWindow(transition='in_left').get_root_widget()
                )
            else:
                ba.app.ui.set_main_menu_window(
                    MainMenuWindow(transition='in_left').get_root_widget()
                )
        if self._on_close_call is not None:
            self._on_close_call()


def _check_merch_availability_in_bg_thread() -> None:
    # pylint: disable=cell-var-from-loop

    # Merch is available from some countries only.
    # Make a reasonable check to ask the master-server about this at
    # launch and store the results.
    for _i in range(15):
        try:
            if ba.app.cloud.is_connected():
                response = ba.app.cloud.send_message(
                    bacommon.cloud.MerchAvailabilityMessage()
                )

                def _store_in_logic_thread() -> None:
                    cfg = ba.app.config
                    current: str | None = cfg.get(MERCH_LINK_KEY)
                    if not isinstance(current, str | None):
                        current = None
                    if current != response.url:
                        cfg[MERCH_LINK_KEY] = response.url
                        cfg.commit()

                # If we successfully get a response, kick it over to the
                # logic thread to store and we're done.
                ba.pushcall(_store_in_logic_thread, from_other_thread=True)
                return
        except CommunicationError:
            pass
        except Exception:
            logging.warning(
                'Unexpected error in merch-availability-check.', exc_info=True
            )
        time.sleep(1.1934)  # A bit randomized to avoid aliasing.


Thread(target=_check_merch_availability_in_bg_thread, daemon=True).start()
