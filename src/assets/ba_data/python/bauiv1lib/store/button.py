# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for a button leading to the store."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable


class StoreButton:
    """A button leading to the store."""

    def __init__(
        self,
        parent: bui.Widget,
        position: Sequence[float],
        size: Sequence[float],
        scale: float,
        on_activate_call: Callable[[], Any] | None = None,
        transition_delay: float | None = None,
        color: Sequence[float] | None = None,
        textcolor: Sequence[float] | None = None,
        show_tickets: bool = False,
        button_type: str | None = None,
        sale_scale: float = 1.0,
    ):
        self._position = position
        self._size = size
        self._scale = scale

        if on_activate_call is None:
            on_activate_call = bui.WeakCall(self._default_on_activate_call)
        self._on_activate_call = on_activate_call

        self._button = bui.buttonwidget(
            parent=parent,
            size=size,
            label='' if show_tickets else bui.Lstr(resource='storeText'),
            scale=scale,
            autoselect=True,
            on_activate_call=self._on_activate,
            transition_delay=transition_delay,
            color=color,
            button_type=button_type,
        )

        self._title_text: bui.Widget | None
        self._ticket_text: bui.Widget | None

        if show_tickets:
            self._title_text = bui.textwidget(
                parent=parent,
                position=(
                    position[0] + size[0] * 0.5 * scale,
                    position[1] + size[1] * 0.65 * scale,
                ),
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=size[0] * scale * 0.65,
                text=bui.Lstr(resource='storeText'),
                draw_controller=self._button,
                scale=scale,
                transition_delay=transition_delay,
                color=textcolor,
            )
            self._ticket_text = bui.textwidget(
                parent=parent,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=size[0] * scale * 0.85,
                text='',
                color=(0.2, 1.0, 0.2),
                flatness=1.0,
                shadow=0.0,
                scale=scale * 0.6,
                transition_delay=transition_delay,
            )
        else:
            self._title_text = None
            self._ticket_text = None

        self._circle_rad = 12 * scale
        self._circle_center = (0.0, 0.0)
        self._sale_circle_center = (0.0, 0.0)

        self._available_purchase_backing = bui.imagewidget(
            parent=parent,
            color=(1, 0, 0),
            draw_controller=self._button,
            size=(2.2 * self._circle_rad, 2.2 * self._circle_rad),
            texture=bui.gettexture('circleShadow'),
            transition_delay=transition_delay,
        )
        self._available_purchase_text = bui.textwidget(
            parent=parent,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='',
            draw_controller=self._button,
            color=(1, 1, 1),
            flatness=1.0,
            shadow=1.0,
            scale=0.6 * scale,
            maxwidth=self._circle_rad * 1.4,
            transition_delay=transition_delay,
        )

        self._sale_circle_rad = 18 * scale * sale_scale
        self._sale_backing = bui.imagewidget(
            parent=parent,
            color=(0.5, 0, 1.0),
            draw_controller=self._button,
            size=(2 * self._sale_circle_rad, 2 * self._sale_circle_rad),
            texture=bui.gettexture('circleZigZag'),
            transition_delay=transition_delay,
        )
        self._sale_title_text = bui.textwidget(
            parent=parent,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=self._button,
            color=(0, 1, 0),
            flatness=1.0,
            shadow=0.0,
            scale=0.5 * scale * sale_scale,
            maxwidth=self._sale_circle_rad * 1.5,
            transition_delay=transition_delay,
        )
        self._sale_time_text = bui.textwidget(
            parent=parent,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=self._button,
            color=(0, 1, 0),
            flatness=1.0,
            shadow=0.0,
            scale=0.4 * scale * sale_scale,
            maxwidth=self._sale_circle_rad * 1.5,
            transition_delay=transition_delay,
        )

        self.set_position(position)
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

    def _on_activate(self) -> None:
        bui.increment_analytics_count('Store button press')
        self._on_activate_call()

    def set_position(self, position: Sequence[float]) -> None:
        """Set the button position."""
        self._position = position
        self._circle_center = (
            position[0] + 0.1 * self._size[0] * self._scale,
            position[1] + self._size[1] * self._scale * 0.8,
        )
        self._sale_circle_center = (
            position[0] + 0.07 * self._size[0] * self._scale,
            position[1] + self._size[1] * self._scale * 0.8,
        )

        if not self._button:
            return
        bui.buttonwidget(edit=self._button, position=self._position)
        if self._title_text is not None:
            bui.textwidget(
                edit=self._title_text,
                position=(
                    self._position[0] + self._size[0] * 0.5 * self._scale,
                    self._position[1] + self._size[1] * 0.65 * self._scale,
                ),
            )
        if self._ticket_text is not None:
            bui.textwidget(
                edit=self._ticket_text,
                position=(
                    position[0] + self._size[0] * 0.5 * self._scale,
                    position[1] + self._size[1] * 0.28 * self._scale,
                ),
                size=(0, 0),
            )
        bui.imagewidget(
            edit=self._available_purchase_backing,
            position=(
                self._circle_center[0] - self._circle_rad * 1.02,
                self._circle_center[1] - self._circle_rad * 1.13,
            ),
        )
        bui.textwidget(
            edit=self._available_purchase_text, position=self._circle_center
        )

        bui.imagewidget(
            edit=self._sale_backing,
            position=(
                self._sale_circle_center[0] - self._sale_circle_rad,
                self._sale_circle_center[1] - self._sale_circle_rad,
            ),
        )
        bui.textwidget(
            edit=self._sale_title_text,
            position=(
                self._sale_circle_center[0],
                self._sale_circle_center[1] + self._sale_circle_rad * 0.3,
            ),
        )
        bui.textwidget(
            edit=self._sale_time_text,
            position=(
                self._sale_circle_center[0],
                self._sale_circle_center[1] - self._sale_circle_rad * 0.3,
            ),
        )

    def _default_on_activate_call(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.account import show_sign_in_prompt
        from bauiv1lib.store.browser import StoreBrowserWindow

        plus = bui.app.plus
        assert plus is not None
        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        StoreBrowserWindow(modal=True, origin_widget=self._button)

    def get_button(self) -> bui.Widget:
        """Return the underlying button widget."""
        return self._button

    def _update(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import
        from babase import SpecialChar

        plus = bui.app.plus
        assert plus is not None
        assert bui.app.classic is not None
        store = bui.app.classic.store

        if not self._button:
            return  # Our instance may outlive our UI objects.

        if self._ticket_text is not None:
            if plus.get_v1_account_state() == 'signed_in':
                sval = bui.charstr(SpecialChar.TICKET) + str(
                    plus.get_v1_account_ticket_count()
                )
            else:
                sval = '-'
            bui.textwidget(edit=self._ticket_text, text=sval)
        available_purchases = store.get_available_purchase_count()

        # Old pro sale stuff..
        sale_time = store.get_available_sale_time('extras')

        # ..also look for new style sales.
        if sale_time is None:
            import datetime

            sales_raw = plus.get_v1_account_misc_read_val('sales', {})
            sale_times = []
            try:
                # Look at the current set of sales; filter any with time
                # remaining that we don't own.
                for sale_item, sale_info in list(sales_raw.items()):
                    if not plus.get_purchased(sale_item):
                        to_end = (
                            datetime.datetime.utcfromtimestamp(sale_info['e'])
                            - datetime.datetime.utcnow()
                        ).total_seconds()
                        if to_end > 0:
                            sale_times.append(to_end)
            except Exception:
                logging.exception('Error parsing sales.')
            if sale_times:
                sale_time = int(min(sale_times) * 1000)

        if sale_time is not None:
            bui.textwidget(
                edit=self._sale_title_text,
                text=bui.Lstr(resource='store.saleText'),
            )
            bui.textwidget(
                edit=self._sale_time_text,
                text=bui.timestring(sale_time / 1000.0, centi=False),
            )
            bui.imagewidget(edit=self._sale_backing, opacity=1.0)
            bui.imagewidget(edit=self._available_purchase_backing, opacity=1.0)
            bui.textwidget(edit=self._available_purchase_text, text='')
            bui.imagewidget(edit=self._available_purchase_backing, opacity=0.0)
        else:
            bui.imagewidget(edit=self._sale_backing, opacity=0.0)
            bui.textwidget(edit=self._sale_time_text, text='')
            bui.textwidget(edit=self._sale_title_text, text='')
            if available_purchases > 0:
                bui.textwidget(
                    edit=self._available_purchase_text,
                    text=str(available_purchases),
                )
                bui.imagewidget(
                    edit=self._available_purchase_backing, opacity=1.0
                )
            else:
                bui.textwidget(edit=self._available_purchase_text, text='')
                bui.imagewidget(
                    edit=self._available_purchase_backing, opacity=0.0
                )
