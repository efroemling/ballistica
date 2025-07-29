# Released under the MIT License. See LICENSE for details.
#
"""UI related to purchasing items."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class PurchaseWindow(bui.Window):
    """Window for purchasing one or more items."""

    def __init__(
        self,
        items: list[str],
        origin_widget: bui.Widget | None = None,
        header_text: bui.Lstr | None = None,
    ):
        from bauiv1lib.store.item import instantiate_store_item_display

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        store = bui.app.classic.store

        if header_text is None:
            header_text = bui.Lstr(
                resource='unlockThisText',
                fallback_resource='unlockThisInTheStoreText',
            )
        if len(items) != 1:
            raise ValueError('expected exactly 1 item')
        self._items = list(items)
        self._width = 580
        self._height = 520
        uiscale = bui.app.ui_v1.uiscale

        if origin_widget is not None:
            scale_origin = origin_widget.get_screen_space_center()
        else:
            scale_origin = None

        super().__init__(
            root_widget=bui.containerwidget(
                parent=bui.get_special_widget('overlay_stack'),
                size=(self._width, self._height),
                transition='in_scale',
                toolbar_visibility='menu_store',
                scale=(
                    1.2
                    if uiscale is bui.UIScale.SMALL
                    else 1.1 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                scale_origin_stack_offset=scale_origin,
                stack_offset=(
                    (0, -15) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            )
        )
        self._is_double = False
        self._title_text = bui.textwidget(
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
        size = store.get_store_item_display_size(items[0])
        display: dict[str, Any] = {}
        instantiate_store_item_display(
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
                price_str = plus.get_price(self._items[0])
                pyoffs = -15
            else:
                pyoffs = 0
                price = self._price = plus.get_v1_account_misc_read_val(
                    'price.' + str(items[0]), -1
                )
                price_str = bui.charstr(bui.SpecialChar.TICKET) + str(price)
            self._price_text = bui.textwidget(
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

        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(50, 40),
            size=(150, 60),
            scale=1.0,
            on_activate_call=self._cancel,
            autoselect=True,
            label=bui.Lstr(resource='cancelText'),
        )
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
            start_button=self._purchase_button,
            selected_child=self._purchase_button,
        )

    def _update(self) -> None:
        can_die = False

        plus = bui.app.plus
        assert plus is not None

        # We go away if we see that our target item is owned.
        if self._items == ['pro']:
            assert bui.app.classic is not None
            if bui.app.classic.accounts.have_pro():
                can_die = True
        else:
            assert bui.app.classic is not None
            if self._items[0] in bui.app.classic.purchases:
                can_die = True

        if can_die:
            bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _purchase(self) -> None:

        plus = bui.app.plus
        assert plus is not None
        classic = bui.app.classic
        assert classic is not None

        if self._items == ['pro']:
            plus.purchase('pro')
        else:
            ticket_count: int | None
            try:
                ticket_count = classic.tickets
            except Exception:
                ticket_count = None
            if ticket_count is not None and ticket_count < self._price:
                bui.getsound('error').play()
                bui.screenmessage(
                    bui.Lstr(resource='notEnoughTicketsText'),
                    color=(1, 0, 0),
                )
                return

            def do_it() -> None:
                assert plus is not None

                plus.in_game_purchase(self._items[0], self._price)

            bui.getsound('swish').play()
            do_it()

    def _cancel(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
