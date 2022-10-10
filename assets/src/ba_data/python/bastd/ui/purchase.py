# Released under the MIT License. See LICENSE for details.
#
"""UI related to purchasing items."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any


class PurchaseWindow(ba.Window):
    """Window for purchasing one or more items."""

    def __init__(
        self,
        items: list[str],
        transition: str = 'in_right',
        header_text: ba.Lstr | None = None,
    ):
        from ba.internal import get_store_item_display_size
        from bastd.ui.store import item as storeitemui

        if header_text is None:
            header_text = ba.Lstr(
                resource='unlockThisText',
                fallback_resource='unlockThisInTheStoreText',
            )
        if len(items) != 1:
            raise ValueError('expected exactly 1 item')
        self._items = list(items)
        self._width = 580
        self._height = 520
        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height),
                transition=transition,
                toolbar_visibility='menu_currency',
                scale=(
                    1.2
                    if uiscale is ba.UIScale.SMALL
                    else 1.1
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(0, -15)
                if uiscale is ba.UIScale.SMALL
                else (0, 0),
            )
        )
        self._is_double = False
        self._title_text = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 30),
            size=(0, 0),
            text=header_text,
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.9 - 120,
            scale=1.2,
            color=(1, 0.8, 0.3, 1),
        )
        size = get_store_item_display_size(items[0])
        display: dict[str, Any] = {}
        storeitemui.instantiate_store_item_display(
            items[0],
            display,
            parent_widget=self._root_widget,
            b_pos=(
                self._width * 0.5
                - size[0] * 0.5
                + 10
                - ((size[0] * 0.5 + 30) if self._is_double else 0),
                self._height * 0.5
                - size[1] * 0.5
                + 30
                + (20 if self._is_double else 0),
            ),
            b_width=size[0],
            b_height=size[1],
            button=False,
        )

        # Wire up the parts we need.
        if self._is_double:
            pass  # not working
        else:
            if self._items == ['pro']:
                price_str = ba.internal.get_price(self._items[0])
                pyoffs = -15
            else:
                pyoffs = 0
                price = self._price = ba.internal.get_v1_account_misc_read_val(
                    'price.' + str(items[0]), -1
                )
                price_str = ba.charstr(ba.SpecialChar.TICKET) + str(price)
            self._price_text = ba.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, 150 + pyoffs),
                size=(0, 0),
                text=price_str,
                h_align='center',
                v_align='center',
                maxwidth=self._width * 0.9,
                scale=1.4,
                color=(0.2, 1, 0.2),
            )

        self._update_timer = ba.Timer(
            1.0,
            ba.WeakCall(self._update),
            timetype=ba.TimeType.REAL,
            repeat=True,
        )

        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(50, 40),
            size=(150, 60),
            scale=1.0,
            on_activate_call=self._cancel,
            autoselect=True,
            label=ba.Lstr(resource='cancelText'),
        )
        self._purchase_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 200, 40),
            size=(150, 60),
            scale=1.0,
            on_activate_call=self._purchase,
            autoselect=True,
            label=ba.Lstr(resource='store.purchaseText'),
        )

        ba.containerwidget(
            edit=self._root_widget,
            cancel_button=self._cancel_button,
            start_button=self._purchase_button,
            selected_child=self._purchase_button,
        )

    def _update(self) -> None:
        can_die = False

        # We go away if we see that our target item is owned.
        if self._items == ['pro']:
            if ba.app.accounts_v1.have_pro():
                can_die = True
        else:
            if ba.internal.get_purchased(self._items[0]):
                can_die = True

        if can_die:
            ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _purchase(self) -> None:
        from bastd.ui import getcurrency

        if self._items == ['pro']:
            ba.internal.purchase('pro')
        else:
            ticket_count: int | None
            try:
                ticket_count = ba.internal.get_v1_account_ticket_count()
            except Exception:
                ticket_count = None
            if ticket_count is not None and ticket_count < self._price:
                getcurrency.show_get_tickets_prompt()
                ba.playsound(ba.getsound('error'))
                return

            def do_it() -> None:
                ba.internal.in_game_purchase(self._items[0], self._price)

            ba.playsound(ba.getsound('swish'))
            do_it()

    def _cancel(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
