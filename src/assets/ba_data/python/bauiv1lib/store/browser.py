# Released under the MIT License. See LICENSE for details.
#
"""UI for browsing the store."""
# pylint: disable=too-many-lines
from __future__ import annotations

import os
import time
import copy
import math
import logging
import weakref
import datetime
from enum import Enum
from threading import Thread
from typing import TYPE_CHECKING, override

from efro.util import utc_now
from efro.error import CommunicationError
import bacommon.cloud
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence

MERCH_LINK_KEY = 'Merch Link'


class StoreBrowserWindow(bui.MainWindow):
    """Window for browsing the store."""

    class TabID(Enum):
        """Our available tab types."""

        # EXTRAS = 'extras'
        MAPS = 'maps'
        MINIGAMES = 'minigames'
        CHARACTERS = 'characters'
        ICONS = 'icons'

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        show_tab: StoreBrowserWindow.TabID | None = None,
        minimal_toolbars: bool = False,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from bauiv1lib.tabs import TabRow
        from bauiv1 import SpecialChar

        app = bui.app
        assert app.classic is not None
        uiscale = app.ui_v1.uiscale

        bui.set_analytics_screen('Store Window')

        self.button_infos: dict[str, dict[str, Any]] | None = None
        self.update_buttons_timer: bui.AppTimer | None = None
        self._status_textwidget_update_timer = None

        self._show_tab = show_tab
        self._width = (
            1800
            if uiscale is bui.UIScale.SMALL
            else 1000 if uiscale is bui.UIScale.MEDIUM else 1120
        )
        self._height = (
            1200
            if uiscale is bui.UIScale.SMALL
            else 700 if uiscale is bui.UIScale.MEDIUM else 800
        )
        self._current_tab: StoreBrowserWindow.TabID | None = None
        # extra_top = 30 if uiscale is bui.UIScale.SMALL else 0

        self.request: Any = None
        self._r = 'store'
        self._last_buy_time: float | None = None

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 0.9 if uiscale is bui.UIScale.MEDIUM else 0.8
        )

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 120, screensize[0] / scale)
        target_height = min(self._height - 140, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 59
        self._scroll_bottom = yoffs - 87 - self._scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_store'
                    if (uiscale is bui.UIScale.SMALL or minimal_toolbars)
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(70, yoffs - 37),
            size=(60, 60),
            scale=1.1,
            autoselect=True,
            label=bui.charstr(SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button.delete()
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        if (
            app.classic.platform in ['mac', 'ios']
            and app.classic.subplatform == 'appstore'
        ):
            bui.buttonwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - 70, 16),
                size=(230, 50),
                scale=0.65,
                on_activate_call=bui.WeakCall(self._restore_purchases),
                color=(0.35, 0.3, 0.4),
                selectable=False,
                textcolor=(0.55, 0.5, 0.6),
                label=bui.Lstr(
                    resource='getTicketsWindow.restorePurchasesText'
                ),
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                (
                    self._width * 0.5
                    + (
                        (self._scroll_width * -0.5 + 90.0)
                        if uiscale is bui.UIScale.SMALL
                        else 0.0
                    )
                ),
                yoffs - (62 if uiscale is bui.UIScale.SMALL else -3.0),
            ),
            size=(0, 0),
            color=app.ui_v1.title_color,
            scale=1.1 if uiscale is bui.UIScale.SMALL else 1.3,
            h_align='left' if uiscale is bui.UIScale.SMALL else 'center',
            v_align='center',
            text=bui.Lstr(resource='storeText'),
            maxwidth=100 if uiscale is bui.UIScale.SMALL else 290,
        )

        tabs_def = [
            # (self.TabID.EXTRAS, bui.Lstr(resource=f'{self._r}.extrasText')),
            (self.TabID.MAPS, bui.Lstr(resource=f'{self._r}.mapsText')),
            (
                self.TabID.MINIGAMES,
                bui.Lstr(resource=f'{self._r}.miniGamesText'),
            ),
            (
                self.TabID.CHARACTERS,
                bui.Lstr(resource=f'{self._r}.charactersText'),
            ),
            (self.TabID.ICONS, bui.Lstr(resource=f'{self._r}.iconsText')),
        ]

        tab_inset = 200 if uiscale is bui.UIScale.SMALL else 100
        self._tab_row = TabRow(
            self._root_widget,
            tabs_def,
            size=(self._scroll_width - 2.0 * tab_inset, 50),
            pos=(
                self._width * 0.5 - self._scroll_width * 0.5 + tab_inset,
                self._scroll_bottom + self._scroll_height - 4.0,
            ),
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
            img = bui.imagewidget(
                parent=self._root_widget,
                position=(center[0] - rad * 1.1, center[1] - rad * 1.2),
                size=(rad * 2.4, rad * 2.4),
                texture=bui.gettexture('circleShadow'),
                color=(1, 0, 0),
            )
            txt = bui.textwidget(
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
            sale_img = bui.imagewidget(
                parent=self._root_widget,
                position=(center[0] - rad, center[1] - rad),
                size=(rad * 2, rad * 2),
                draw_controller=button,
                texture=bui.gettexture('circleZigZag'),
                color=(0.5, 0, 1.0),
            )
            sale_title_text = bui.textwidget(
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
            sale_time_text = bui.textwidget(
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
        self._tab_update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update_tabs), repeat=True
        )
        self._update_tabs()

        if uiscale is bui.UIScale.SMALL:
            first_tab_button = self._tab_row.tabs[tabs_def[0][0]].button
            last_tab_button = self._tab_row.tabs[tabs_def[-1][0]].button
            bui.widget(
                edit=first_tab_button,
                left_widget=bui.get_special_widget('back_button'),
                up_widget=bui.get_special_widget('back_button'),
            )
            bui.widget(
                edit=last_tab_button,
                up_widget=bui.get_special_widget('tickets_meter'),
                right_widget=bui.get_special_widget('tickets_meter'),
            )

        # self._scroll_width = self._width - scroll_buffer_h
        # self._scroll_height = self._height - 180

        self._scrollwidget: bui.Widget | None = None
        self._status_textwidget: bui.Widget | None = None
        self._restore_state()

    def _restore_purchases(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt

        plus = bui.app.plus
        assert plus is not None
        if plus.accounts.primary is None:
            show_sign_in_prompt()
        else:
            plus.restore_purchases()

    def _update_tabs(self) -> None:
        assert bui.app.classic is not None
        store = bui.app.classic.store

        if not self._root_widget:
            return
        for tab_id, tab_data in list(self._purchasable_count_widgets.items()):
            sale_time = store.get_available_sale_time(tab_id.value)

            if sale_time is not None:
                bui.textwidget(
                    edit=tab_data['sale_title_text'],
                    text=bui.Lstr(resource='store.saleText'),
                )
                bui.textwidget(
                    edit=tab_data['sale_time_text'],
                    text=bui.timestring(sale_time / 1000.0, centi=False),
                )
                bui.imagewidget(edit=tab_data['sale_img'], opacity=1.0)
                count = 0
            else:
                bui.textwidget(edit=tab_data['sale_title_text'], text='')
                bui.textwidget(edit=tab_data['sale_time_text'], text='')
                bui.imagewidget(edit=tab_data['sale_img'], opacity=0.0)
                count = store.get_available_purchase_count(tab_id.value)

            if count > 0:
                bui.textwidget(edit=tab_data['text'], text=str(count))
                bui.imagewidget(edit=tab_data['img'], opacity=1.0)
            else:
                bui.textwidget(edit=tab_data['text'], text='')
                bui.imagewidget(edit=tab_data['img'], opacity=0.0)

    def _set_tab(self, tab_id: TabID) -> None:
        if self._current_tab is tab_id:
            return
        self._current_tab = tab_id

        # We wanna preserve our current tab between runs.
        cfg = bui.app.config
        cfg['Store Tab'] = tab_id.value
        cfg.commit()

        # Update tab colors based on which is selected.
        self._tab_row.update_appearance(tab_id)

        # (Re)create scroll widget.
        if self._scrollwidget:
            self._scrollwidget.delete()

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            position=(
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
            ),
            claims_left_right=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )

        # NOTE: this stuff is modified by the _Store class.
        # Should maybe clean that up.
        self.button_infos = {}
        self.update_buttons_timer = None

        # Show status over top.
        if self._status_textwidget:
            self._status_textwidget.delete()
        self._status_textwidget = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            color=(1, 0.7, 1, 0.5),
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource=f'{self._r}.loadingText'),
            maxwidth=self._scroll_width * 0.9,
        )

        # Kick off a server request.
        self.request = _Request(self, tab_id)

    # Actually start the purchase locally.
    def _purchase_check_result(
        self, item: str, is_ticket_purchase: bool, result: dict[str, Any] | None
    ) -> None:
        plus = bui.app.plus
        assert plus is not None
        if result is None:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
        else:
            if is_ticket_purchase:
                if result['allow']:
                    price = plus.get_v1_account_misc_read_val(
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
                        bui.getsound('error').play()
                    else:
                        bui.getsound('click01').play()
                        plus.in_game_purchase(item, price)
                else:
                    if result['reason'] == 'versionTooOld':
                        bui.getsound('error').play()
                        bui.screenmessage(
                            bui.Lstr(
                                resource='getTicketsWindow.versionTooOldText'
                            ),
                            color=(1, 0, 0),
                        )
                    else:
                        bui.getsound('error').play()
                        bui.screenmessage(
                            bui.Lstr(
                                resource='getTicketsWindow.unavailableText'
                            ),
                            color=(1, 0, 0),
                        )
            # Real in-app purchase.
            else:
                if result['allow']:
                    plus.purchase(item)
                else:
                    if result['reason'] == 'versionTooOld':
                        bui.getsound('error').play()
                        bui.screenmessage(
                            bui.Lstr(
                                resource='getTicketsWindow.versionTooOldText'
                            ),
                            color=(1, 0, 0),
                        )
                    else:
                        bui.getsound('error').play()
                        bui.screenmessage(
                            bui.Lstr(
                                resource='getTicketsWindow.unavailableText'
                            ),
                            color=(1, 0, 0),
                        )

    def _do_purchase_check(
        self, item: str, is_ticket_purchase: bool = False
    ) -> None:
        app = bui.app
        if app.classic is None:
            logging.warning('_do_purchase_check() requires classic.')
            return

        # Here we ping the server to ask if it's valid for us to
        # purchase this. Better to fail now than after we've
        # paid locally.

        app.classic.master_server_v1_get(
            'bsAccountPurchaseCheck',
            {
                'item': item,
                'platform': app.classic.platform,
                'subplatform': app.classic.subplatform,
                'version': app.env.engine_version,
                'buildNumber': app.env.engine_build_number,
                'purchaseType': 'ticket' if is_ticket_purchase else 'real',
            },
            callback=bui.WeakCall(
                self._purchase_check_result, item, is_ticket_purchase
            ),
        )

    def buy(self, item: str) -> None:
        """Attempt to purchase the provided item."""
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.confirm import ConfirmWindow

        assert bui.app.classic is not None
        store = bui.app.classic.store

        plus = bui.app.plus
        assert plus is not None
        classic = bui.app.classic
        assert classic is not None

        # Prevent pressing buy within a few seconds of the last press
        # (gives the buttons time to disable themselves and whatnot).
        curtime = bui.apptime()
        if (
            self._last_buy_time is not None
            and (curtime - self._last_buy_time) < 2.0
        ):
            bui.getsound('error').play()
        else:
            if plus.accounts.primary is None:
                show_sign_in_prompt()
            else:
                self._last_buy_time = curtime

                # Merch is a special case - just a link.
                if item == 'merch':
                    url = bui.app.config.get('Merch Link')
                    if isinstance(url, str):
                        bui.open_url(url)

                # Pro is an actual IAP, and the rest are ticket purchases.
                elif item == 'pro':
                    bui.getsound('click01').play()

                    # Purchase either pro or pro_sale depending on whether
                    # there is a sale going on.
                    self._do_purchase_check(
                        'pro'
                        if store.get_available_sale_time('extras') is None
                        else 'pro_sale'
                    )
                else:
                    price = plus.get_v1_account_misc_read_val(
                        'price.' + item, None
                    )
                    our_tickets = classic.tickets
                    if price is not None and our_tickets < price:
                        bui.getsound('error').play()
                        bui.screenmessage(
                            bui.Lstr(resource='notEnoughTicketsText'),
                            color=(1, 0, 0),
                        )
                        # gettickets.show_get_tickets_prompt()
                    else:

                        def do_it() -> None:
                            self._do_purchase_check(
                                item, is_ticket_purchase=True
                            )

                        bui.getsound('swish').play()
                        ConfirmWindow(
                            bui.Lstr(
                                resource='store.purchaseConfirmText',
                                subs=[
                                    (
                                        '${ITEM}',
                                        store.get_store_item_name_translated(
                                            item
                                        ),
                                    )
                                ],
                            ),
                            width=400,
                            height=120,
                            action=do_it,
                            ok_text=bui.Lstr(
                                resource='store.purchaseText',
                                fallback_resource='okText',
                            ),
                        )

    def _print_already_own(self, charname: str) -> None:
        bui.screenmessage(
            bui.Lstr(
                resource=f'{self._r}.alreadyOwnText',
                subs=[('${NAME}', charname)],
            ),
            color=(1, 0, 0),
        )
        bui.getsound('error').play()

    def update_buttons(self) -> None:
        """Update our buttons."""
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from bauiv1 import SpecialChar

        assert bui.app.classic is not None
        store = bui.app.classic.store

        plus = bui.app.plus
        assert plus is not None
        classic = bui.app.classic
        assert classic is not None

        if not self._root_widget:
            return

        sales_raw = plus.get_v1_account_misc_read_val('sales', {})
        sales = {}
        try:
            # Look at the current set of sales; filter any with time remaining.
            for sale_item, sale_info in list(sales_raw.items()):
                to_end = (
                    datetime.datetime.fromtimestamp(
                        sale_info['e'], datetime.UTC
                    )
                    - utc_now()
                ).total_seconds()
                if to_end > 0:
                    sales[sale_item] = {
                        'to_end': to_end,
                        'original_price': sale_info['op'],
                    }
        except Exception:
            logging.exception('Error parsing sales.')

        assert self.button_infos is not None
        for b_type, b_info in self.button_infos.items():
            if b_type == 'merch':
                purchased = False
            elif b_type in ['upgrades.pro', 'pro']:
                assert bui.app.classic is not None
                purchased = bui.app.classic.accounts.have_pro()
            else:
                assert bui.app.classic is not None
                purchased = b_type in bui.app.classic.purchases

            sale_opacity = 0.0
            sale_title_text: str | bui.Lstr = ''
            sale_time_text: str | bui.Lstr = ''

            call: Callable | None
            if purchased:
                title_color = (0.8, 0.7, 0.9, 1.0)
                color = (0.63, 0.55, 0.78)
                extra_image_opacity = 0.5
                call = bui.WeakCall(self._print_already_own, b_info['name'])
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
                    sale_time = store.get_available_sale_time('extras')
                    if sale_time is not None:
                        priceraw = plus.get_price('pro')
                        price_text_left = (
                            priceraw if priceraw is not None else '?'
                        )
                        priceraw = plus.get_price('pro_sale')
                        price_text_right = (
                            priceraw if priceraw is not None else '?'
                        )
                        sale_opacity = 1.0
                        price_text = ''
                        sale_title_text = bui.Lstr(resource='store.saleText')
                        sale_time_text = bui.timestring(
                            sale_time / 1000.0, centi=False
                        )
                    else:
                        priceraw = plus.get_price('pro')
                        price_text = priceraw if priceraw is not None else '?'
                        price_text_left = ''
                        price_text_right = ''
                else:
                    price = plus.get_v1_account_misc_read_val(
                        'price.' + b_type, 0
                    )

                    # Color the button differently if we cant afford this.
                    if plus.accounts.primary is not None:
                        if classic.tickets < price:
                            color = (0.6, 0.61, 0.6)
                    price_text = bui.charstr(bui.SpecialChar.TICKET) + str(
                        plus.get_v1_account_misc_read_val(
                            'price.' + b_type, '?'
                        )
                    )
                    price_text_left = ''
                    price_text_right = ''

                    # TESTING:
                    if b_type in sales:
                        sale_opacity = 1.0
                        price_text_left = bui.charstr(SpecialChar.TICKET) + str(
                            sales[b_type]['original_price']
                        )
                        price_text_right = price_text
                        price_text = ''
                        sale_title_text = bui.Lstr(resource='store.saleText')
                        sale_time_text = bui.timestring(
                            sales[b_type]['to_end'], centi=False
                        )

                description_color = (0.5, 1.0, 0.5)
                description_color2 = (0.3, 1.0, 1.0)
                price_color = (0.2, 1, 0.2, 1.0)
                show_purchase_check = False

            if 'title_text' in b_info:
                bui.textwidget(edit=b_info['title_text'], color=title_color)
            if 'purchase_check' in b_info:
                bui.imagewidget(
                    edit=b_info['purchase_check'],
                    opacity=1.0 if show_purchase_check else 0.0,
                )
            if 'price_widget' in b_info:
                bui.textwidget(
                    edit=b_info['price_widget'],
                    text=price_text,
                    color=price_color,
                )
            if 'price_widget_left' in b_info:
                bui.textwidget(
                    edit=b_info['price_widget_left'], text=price_text_left
                )
            if 'price_widget_right' in b_info:
                bui.textwidget(
                    edit=b_info['price_widget_right'], text=price_text_right
                )
            if 'price_slash_widget' in b_info:
                bui.imagewidget(
                    edit=b_info['price_slash_widget'], opacity=sale_opacity
                )
            if 'sale_bg_widget' in b_info:
                bui.imagewidget(
                    edit=b_info['sale_bg_widget'], opacity=sale_opacity
                )
            if 'sale_title_widget' in b_info:
                bui.textwidget(
                    edit=b_info['sale_title_widget'], text=sale_title_text
                )
            if 'sale_time_widget' in b_info:
                bui.textwidget(
                    edit=b_info['sale_time_widget'], text=sale_time_text
                )
            if 'button' in b_info:
                bui.buttonwidget(
                    edit=b_info['button'], color=color, on_activate_call=call
                )
            if 'extra_backings' in b_info:
                for bck in b_info['extra_backings']:
                    bui.imagewidget(
                        edit=bck, color=color, opacity=extra_image_opacity
                    )
            if 'extra_images' in b_info:
                for img in b_info['extra_images']:
                    bui.imagewidget(edit=img, opacity=extra_image_opacity)
            if 'extra_texts' in b_info:
                for etxt in b_info['extra_texts']:
                    bui.textwidget(edit=etxt, color=description_color)
            if 'extra_texts_2' in b_info:
                for etxt in b_info['extra_texts_2']:
                    bui.textwidget(edit=etxt, color=description_color2)
            if 'descriptionText' in b_info:
                bui.textwidget(
                    edit=b_info['descriptionText'], color=description_color
                )

    def _on_response(self, data: dict[str, Any] | None) -> None:

        # clear status text..
        if self._status_textwidget:
            self._status_textwidget.delete()
            self._status_textwidget_update_timer = None

        if data is None:
            self._status_textwidget = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, self._height * 0.5),
                size=(0, 0),
                scale=1.3,
                transition_delay=0.1,
                color=(1, 0.3, 0.3, 1.0),
                h_align='center',
                v_align='center',
                text=bui.Lstr(resource=f'{self._r}.loadErrorText'),
                maxwidth=self._scroll_width * 0.9,
            )
        else:

            if self._current_tab in (
                # self.TabID.EXTRAS,
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
                cnt = bui.containerwidget(
                    parent=self._scrollwidget,
                    scale=1.0,
                    size=(self._scroll_width, self._scroll_height * 0.95),
                    background=False,
                    claims_left_right=True,
                    selection_loops_to_parent=True,
                )
                self._status_textwidget = bui.textwidget(
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
                    text=bui.Lstr(resource=f'{self._r}.comingSoonText'),
                    maxwidth=self._scroll_width * 0.9,
                )

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

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            selected_tab_ids = [
                tab_id
                for tab_id, tab in self._tab_row.tabs.items()
                if sel == tab.button
            ]
            if sel == self._scrollwidget:
                sel_name = 'Scroll'
            elif sel == self._back_button:
                sel_name = 'Back'
            elif selected_tab_ids:
                assert len(selected_tab_ids) == 1
                sel_name = f'Tab:{selected_tab_ids[0].value}'
            else:
                raise ValueError(f'unrecognized selection \'{sel}\'')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = {
                'sel_name': sel_name,
            }
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:

        try:
            sel: bui.Widget | None
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            assert isinstance(sel_name, (str, type(None)))

            try:
                current_tab = self.TabID(bui.app.config.get('Store Tab'))
            except ValueError:
                current_tab = self.TabID.CHARACTERS

            if self._show_tab is not None:
                current_tab = self._show_tab
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                try:
                    sel_tab_id = self.TabID(sel_name.split(':')[-1])
                except ValueError:
                    sel_tab_id = self.TabID.CHARACTERS
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                sel = self._tab_row.tabs[current_tab].button

            # If we were requested to show a tab, select it too.
            if (
                self._show_tab is not None
                and self._show_tab in self._tab_row.tabs
            ):
                sel = self._tab_row.tabs[self._show_tab].button
            self._set_tab(current_tab)
            if sel is not None:
                bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)


def _check_merch_availability_in_bg_thread() -> None:
    # pylint: disable=cell-var-from-loop

    # Merch is available from some countries only. Make a reasonable
    # check to ask the master-server about this at launch and store the
    # results.
    plus = bui.app.plus
    assert plus is not None

    for _i in range(15):
        try:
            if plus.cloud.is_connected():
                response = plus.cloud.send_message(
                    bacommon.cloud.MerchAvailabilityMessage()
                )

                def _store_in_logic_thread() -> None:
                    cfg = bui.app.config
                    current = cfg.get(MERCH_LINK_KEY)
                    if not isinstance(current, str | None):
                        current = None
                    if current != response.url:
                        cfg[MERCH_LINK_KEY] = response.url
                        cfg.commit()

                # If we successfully get a response, kick it over to the
                # logic thread to store and we're done.
                bui.pushcall(_store_in_logic_thread, from_other_thread=True)
                return
        except CommunicationError:
            pass
        except Exception:
            logging.warning(
                'Unexpected error in merch-availability-check.', exc_info=True
            )
        time.sleep(1.1934)  # A bit randomized to avoid aliasing.


class _Store:
    def __init__(
        self,
        store_window: StoreBrowserWindow,
        sdata: dict[str, Any],
        width: float,
    ):
        assert bui.app.classic is not None
        cstore = bui.app.classic.store

        self._store_window = store_window
        self._width = width
        store_data = cstore.get_store_layout()
        self._tab = sdata['tab']
        self._sections = copy.deepcopy(store_data[sdata['tab']])
        self._height: float | None = None

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

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
            section['button_size'] = cstore.get_store_item_display_size(
                dummy_name
            )
            section['v_spacing'] = (
                -25
                if (self._tab == 'extras' and uiscale is bui.UIScale.SMALL)
                else -17 if self._tab == 'characters' else 0
            )
            if 'title' not in section:
                section['title'] = ''
            section['x_offs'] = 0.0
            # section['x_offs'] = (
            #     130
            #     if self._tab == 'extras'
            #     else 270 if self._tab == 'maps' else 0
            # )
            section['y_offs'] = (
                20
                if (
                    self._tab == 'extras'
                    and uiscale is bui.UIScale.SMALL
                    and bui.app.config.get('Merch Link')
                )
                else (
                    55
                    if (self._tab == 'extras' and uiscale is bui.UIScale.SMALL)
                    else -20 if self._tab == 'icons' else 0
                )
            )

    def instantiate(
        self, scrollwidget: bui.Widget, tab_button: bui.Widget
    ) -> None:
        """Create the store."""
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-nested-blocks
        from bauiv1lib.store.item import (
            instantiate_store_item_display,
        )

        title_spacing = 40
        button_border = 20
        button_spacing = 4
        boffs_h = 0.0
        self._height = 80.0

        # Calc total height.
        for i, section in enumerate(self._sections):
            if section['title'] != '':
                assert self._height is not None
                self._height += title_spacing
            b_width, b_height = section['button_size']
            b_count = len(section['items'])
            b_column_count = min(
                b_count,
                int(math.floor(self._width / (b_width + button_spacing))),
            )
            b_row_count = int(math.ceil(b_count / b_column_count))
            b_height_total = (
                2 * button_border
                + b_row_count * b_height
                + (b_row_count - 1) * section['v_spacing']
            )
            self._height += b_height_total

        assert self._height is not None
        cnt2 = bui.containerwidget(
            parent=scrollwidget,
            scale=1.0,
            size=(self._width, self._height),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )
        v = self._height - 20

        if self._tab == 'characters':
            txt = bui.Lstr(
                resource='store.howToSwitchCharactersText',
                subs=[
                    (
                        '${SETTINGS}',
                        bui.Lstr(resource='inventoryText'),
                    ),
                    (
                        '${PLAYER_PROFILES}',
                        bui.Lstr(resource='playerProfilesWindow.titleText'),
                    ),
                ],
            )
            bui.textwidget(
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
            txt = bui.Lstr(
                resource='store.howToUseIconsText',
                subs=[
                    (
                        '${SETTINGS}',
                        bui.Lstr(resource='mainMenu.settingsText'),
                    ),
                    (
                        '${PLAYER_PROFILES}',
                        bui.Lstr(resource='playerProfilesWindow.titleText'),
                    ),
                ],
            )
            bui.textwidget(
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
            txt = bui.Lstr(resource='store.howToUseMapsText')
            bui.textwidget(
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
                bui.textwidget(
                    parent=cnt2,
                    position=(
                        self._width * 0.5,
                        v - title_spacing * 0.8,
                    ),
                    size=(0, 0),
                    scale=1.0,
                    transition_delay=delay,
                    color=(0.7, 0.9, 0.7, 1),
                    h_align='center',
                    v_align='center',
                    text=bui.Lstr(resource=section['title']),
                    maxwidth=self._width * 0.7,
                )
                v -= title_spacing
            delay = max(0.100, delay - 0.100)
            v -= button_border
            b_width, b_height = section['button_size']
            b_count = len(section['items'])
            b_column_count = min(
                b_count,
                int(math.floor(self._width / (b_width + button_spacing))),
            )

            col = 0
            item: dict[str, Any]
            assert self._store_window.button_infos is not None
            for i, item_name in enumerate(section['items']):
                item = self._store_window.button_infos[item_name] = {}
                item['call'] = bui.WeakCall(self._store_window.buy, item_name)
                boffs_h2 = section.get('x_offs', 0.0)
                boffs_v2 = section.get('y_offs', 0.0)

                # Calc the diff between the space we use and
                # the space available and nudge us right by
                # half that to center things.
                boffs_h2 += 0.5 * (
                    self._width - ((b_width + button_spacing) * b_column_count)
                )

                b_pos = (
                    boffs_h + boffs_h2 + (b_width + button_spacing) * col,
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
                    if len(prev_row_buttons) > col:
                        bui.widget(
                            edit=btn,
                            up_widget=prev_row_buttons[col],
                        )
                        bui.widget(
                            edit=prev_row_buttons[col],
                            down_widget=btn,
                        )

                        # If we're the last button in our row,
                        # wire any in the previous row past
                        # our position to go to us if down is
                        # pressed.
                        if col + 1 == b_column_count or i == b_count - 1:
                            for b_prev in prev_row_buttons[col + 1 :]:
                                bui.widget(edit=b_prev, down_widget=btn)
                    else:
                        bui.widget(edit=btn, up_widget=prev_row_buttons[-1])
                else:
                    bui.widget(edit=btn, up_widget=tab_button)

                col += 1
                if col == b_column_count or i == b_count - 1:
                    prev_row_buttons = this_row_buttons
                    this_row_buttons = []
                    col = 0
                    v -= b_height
                    if i < b_count - 1:
                        v -= section['v_spacing']

            v -= button_border

        # Set a timer to update these buttons periodically
        # as long as we're alive (so if we buy one it will
        # grey out, etc).
        self._store_window.update_buttons_timer = bui.AppTimer(
            0.5,
            bui.WeakCall(self._store_window.update_buttons),
            repeat=True,
        )

        # Also update them immediately.
        self._store_window.update_buttons()


class _Request:
    def __init__(
        self, window: StoreBrowserWindow, tab_id: StoreBrowserWindow.TabID
    ):
        self._window = weakref.ref(window)
        data = {'tab': tab_id.value}
        bui.apptimer(0.1, bui.WeakCall(self._on_response, data))

    def _on_response(self, data: dict[str, Any] | None) -> None:
        # FIXME: clean this up.
        # pylint: disable=protected-access
        window = self._window()
        if window is not None and (window.request is self):
            window.request = None
            window._on_response(data)


# Slight hack; start checking merch availability in the bg (but only if
# it looks like we've been imported for use in a running app; don't want
# to do this during docs generation/etc.)

# NOTE: Disabling this for now since we're not showing the merch section
# (and want to purge all use of daemon threads).

# TODO: Should wire this up explicitly to app bootstrapping; not good to
# be kicking off work at module import time.
if (
    bool(False)
    and os.environ.get('BA_RUNNING_WITH_DUMMY_MODULES') != '1'
    and bui.app.state is not bui.AppState.NOT_STARTED
):
    Thread(target=_check_merch_availability_in_bg_thread).start()
