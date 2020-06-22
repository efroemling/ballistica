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
"""UI functionality for a button leading to the store."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, Optional


class StoreButton:
    """A button leading to the store."""

    def __init__(self,
                 parent: ba.Widget,
                 position: Sequence[float],
                 size: Sequence[float],
                 scale: float,
                 on_activate_call: Callable[[], Any] = None,
                 transition_delay: float = None,
                 color: Sequence[float] = None,
                 textcolor: Sequence[float] = None,
                 show_tickets: bool = False,
                 button_type: str = None,
                 sale_scale: float = 1.0):
        self._position = position
        self._size = size
        self._scale = scale

        if on_activate_call is None:
            on_activate_call = ba.WeakCall(self._default_on_activate_call)
        self._on_activate_call = on_activate_call

        self._button = ba.buttonwidget(
            parent=parent,
            size=size,
            label='' if show_tickets else ba.Lstr(resource='storeText'),
            scale=scale,
            autoselect=True,
            on_activate_call=self._on_activate,
            transition_delay=transition_delay,
            color=color,
            button_type=button_type)

        self._title_text: Optional[ba.Widget]
        self._ticket_text: Optional[ba.Widget]

        if show_tickets:
            self._title_text = ba.textwidget(
                parent=parent,
                position=(position[0] + size[0] * 0.5 * scale,
                          position[1] + size[1] * 0.65 * scale),
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=size[0] * scale * 0.65,
                text=ba.Lstr(resource='storeText'),
                draw_controller=self._button,
                scale=scale,
                transition_delay=transition_delay,
                color=textcolor)
            self._ticket_text = ba.textwidget(
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
                transition_delay=transition_delay)
        else:
            self._title_text = None
            self._ticket_text = None

        self._circle_rad = 12 * scale
        self._circle_center = (0.0, 0.0)
        self._sale_circle_center = (0.0, 0.0)

        self._available_purchase_backing = ba.imagewidget(
            parent=parent,
            color=(1, 0, 0),
            draw_controller=self._button,
            size=(2.2 * self._circle_rad, 2.2 * self._circle_rad),
            texture=ba.gettexture('circleShadow'),
            transition_delay=transition_delay)
        self._available_purchase_text = ba.textwidget(
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
            transition_delay=transition_delay)

        self._sale_circle_rad = 18 * scale * sale_scale
        self._sale_backing = ba.imagewidget(
            parent=parent,
            color=(0.5, 0, 1.0),
            draw_controller=self._button,
            size=(2 * self._sale_circle_rad, 2 * self._sale_circle_rad),
            texture=ba.gettexture('circleZigZag'),
            transition_delay=transition_delay)
        self._sale_title_text = ba.textwidget(
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
            transition_delay=transition_delay)
        self._sale_time_text = ba.textwidget(parent=parent,
                                             size=(0, 0),
                                             h_align='center',
                                             v_align='center',
                                             draw_controller=self._button,
                                             color=(0, 1, 0),
                                             flatness=1.0,
                                             shadow=0.0,
                                             scale=0.4 * scale * sale_scale,
                                             maxwidth=self._sale_circle_rad *
                                             1.5,
                                             transition_delay=transition_delay)

        self.set_position(position)
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)
        self._update()

    def _on_activate(self) -> None:
        _ba.increment_analytics_count('Store button press')
        self._on_activate_call()

    def set_position(self, position: Sequence[float]) -> None:
        """Set the button position."""
        self._position = position
        self._circle_center = (position[0] + 0.1 * self._size[0] * self._scale,
                               position[1] + self._size[1] * self._scale * 0.8)
        self._sale_circle_center = (position[0] +
                                    0.07 * self._size[0] * self._scale,
                                    position[1] +
                                    self._size[1] * self._scale * 0.8)

        if not self._button:
            return
        ba.buttonwidget(edit=self._button, position=self._position)
        if self._title_text is not None:
            ba.textwidget(edit=self._title_text,
                          position=(self._position[0] +
                                    self._size[0] * 0.5 * self._scale,
                                    self._position[1] +
                                    self._size[1] * 0.65 * self._scale))
        if self._ticket_text is not None:
            ba.textwidget(
                edit=self._ticket_text,
                position=(position[0] + self._size[0] * 0.5 * self._scale,
                          position[1] + self._size[1] * 0.28 * self._scale),
                size=(0, 0))
        ba.imagewidget(
            edit=self._available_purchase_backing,
            position=(self._circle_center[0] - self._circle_rad * 1.02,
                      self._circle_center[1] - self._circle_rad * 1.13))
        ba.textwidget(edit=self._available_purchase_text,
                      position=self._circle_center)

        ba.imagewidget(
            edit=self._sale_backing,
            position=(self._sale_circle_center[0] - self._sale_circle_rad,
                      self._sale_circle_center[1] - self._sale_circle_rad))
        ba.textwidget(edit=self._sale_title_text,
                      position=(self._sale_circle_center[0],
                                self._sale_circle_center[1] +
                                self._sale_circle_rad * 0.3))
        ba.textwidget(edit=self._sale_time_text,
                      position=(self._sale_circle_center[0],
                                self._sale_circle_center[1] -
                                self._sale_circle_rad * 0.3))

    def _default_on_activate_call(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import show_sign_in_prompt
        from bastd.ui.store.browser import StoreBrowserWindow
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        StoreBrowserWindow(modal=True, origin_widget=self._button)

    def get_button(self) -> ba.Widget:
        """Return the underlying button widget."""
        return self._button

    def _update(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import
        from ba import SpecialChar, TimeFormat
        from ba.internal import (get_available_sale_time,
                                 get_available_purchase_count)
        if not self._button:
            return  # Our instance may outlive our UI objects.

        if self._ticket_text is not None:
            if _ba.get_account_state() == 'signed_in':
                sval = ba.charstr(SpecialChar.TICKET) + str(
                    _ba.get_account_ticket_count())
            else:
                sval = '-'
            ba.textwidget(edit=self._ticket_text, text=sval)
        available_purchases = get_available_purchase_count()

        # Old pro sale stuff..
        sale_time = get_available_sale_time('extras')

        # ..also look for new style sales.
        if sale_time is None:
            import datetime
            sales_raw = _ba.get_account_misc_read_val('sales', {})
            sale_times = []
            try:
                # Look at the current set of sales; filter any with time
                # remaining that we don't own.
                for sale_item, sale_info in list(sales_raw.items()):
                    if not _ba.get_purchased(sale_item):
                        to_end = (datetime.datetime.utcfromtimestamp(
                            sale_info['e']) -
                                  datetime.datetime.utcnow()).total_seconds()
                        if to_end > 0:
                            sale_times.append(to_end)
            except Exception:
                ba.print_exception('Error parsing sales.')
            if sale_times:
                sale_time = int(min(sale_times) * 1000)

        if sale_time is not None:
            ba.textwidget(edit=self._sale_title_text,
                          text=ba.Lstr(resource='store.saleText'))
            ba.textwidget(edit=self._sale_time_text,
                          text=ba.timestring(
                              sale_time,
                              centi=False,
                              timeformat=TimeFormat.MILLISECONDS))
            ba.imagewidget(edit=self._sale_backing, opacity=1.0)
            ba.imagewidget(edit=self._available_purchase_backing, opacity=1.0)
            ba.textwidget(edit=self._available_purchase_text, text='')
            ba.imagewidget(edit=self._available_purchase_backing, opacity=0.0)
        else:
            ba.imagewidget(edit=self._sale_backing, opacity=0.0)
            ba.textwidget(edit=self._sale_time_text, text='')
            ba.textwidget(edit=self._sale_title_text, text='')
            if available_purchases > 0:
                ba.textwidget(edit=self._available_purchase_text,
                              text=str(available_purchases))
                ba.imagewidget(edit=self._available_purchase_backing,
                               opacity=1.0)
            else:
                ba.textwidget(edit=self._available_purchase_text, text='')
                ba.imagewidget(edit=self._available_purchase_backing,
                               opacity=0.0)
