# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup window to continue a game."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any, Callable


class ContinuesWindow(ba.Window):
    """A window to continue a game."""

    def __init__(
        self,
        activity: ba.Activity,
        cost: int,
        continue_call: Callable[[], Any],
        cancel_call: Callable[[], Any],
    ):
        self._activity = weakref.ref(activity)
        self._cost = cost
        self._continue_call = continue_call
        self._cancel_call = cancel_call
        self._start_count = self._count = 20
        self._width = 300
        self._height = 200
        self._transitioning_out = False
        super().__init__(
            ba.containerwidget(
                size=(self._width, self._height),
                background=False,
                toolbar_visibility='menu_currency',
                transition='in_scale',
                scale=1.5,
            )
        )
        txt = (
            ba.Lstr(resource='continuePurchaseText')
            .evaluate()
            .split('${PRICE}')
        )
        t_left = txt[0]
        t_left_width = ba.internal.get_string_width(
            t_left, suppress_warning=True
        )
        t_price = ba.charstr(ba.SpecialChar.TICKET) + str(self._cost)
        t_price_width = ba.internal.get_string_width(
            t_price, suppress_warning=True
        )
        t_right = txt[-1]
        t_right_width = ba.internal.get_string_width(
            t_right, suppress_warning=True
        )
        width_total_half = (t_left_width + t_price_width + t_right_width) * 0.5

        ba.textwidget(
            parent=self._root_widget,
            text=t_left,
            flatness=1.0,
            shadow=1.0,
            size=(0, 0),
            h_align='left',
            v_align='center',
            position=(self._width * 0.5 - width_total_half, self._height - 30),
        )
        ba.textwidget(
            parent=self._root_widget,
            text=t_price,
            flatness=1.0,
            shadow=1.0,
            color=(0.2, 1.0, 0.2),
            size=(0, 0),
            position=(
                self._width * 0.5 - width_total_half + t_left_width,
                self._height - 30,
            ),
            h_align='left',
            v_align='center',
        )
        ba.textwidget(
            parent=self._root_widget,
            text=t_right,
            flatness=1.0,
            shadow=1.0,
            size=(0, 0),
            h_align='left',
            v_align='center',
            position=(
                self._width * 0.5
                - width_total_half
                + t_left_width
                + t_price_width
                + 5,
                self._height - 30,
            ),
        )

        self._tickets_text_base: str | None
        self._tickets_text: ba.Widget | None
        if not ba.app.ui.use_toolbars:
            self._tickets_text_base = ba.Lstr(
                resource='getTicketsWindow.youHaveShortText',
                fallback_resource='getTicketsWindow.youHaveText',
            ).evaluate()
            self._tickets_text = ba.textwidget(
                parent=self._root_widget,
                text='',
                flatness=1.0,
                color=(0.2, 1.0, 0.2),
                shadow=1.0,
                position=(
                    self._width * 0.5 + width_total_half,
                    self._height - 50,
                ),
                size=(0, 0),
                scale=0.35,
                h_align='right',
                v_align='center',
            )
        else:
            self._tickets_text_base = None
            self._tickets_text = None

        self._counter_text = ba.textwidget(
            parent=self._root_widget,
            text=str(self._count),
            color=(0.7, 0.7, 0.7),
            scale=1.2,
            size=(0, 0),
            big=True,
            position=(self._width * 0.5, self._height - 80),
            flatness=1.0,
            shadow=1.0,
            h_align='center',
            v_align='center',
        )
        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(30, 30),
            size=(120, 50),
            label=ba.Lstr(resource='endText', fallback_resource='cancelText'),
            autoselect=True,
            enable_sound=False,
            on_activate_call=self._on_cancel_press,
        )
        self._continue_button = ba.buttonwidget(
            parent=self._root_widget,
            label=ba.Lstr(resource='continueText'),
            autoselect=True,
            position=(self._width - 130, 30),
            size=(120, 50),
            on_activate_call=self._on_continue_press,
        )
        ba.containerwidget(
            edit=self._root_widget,
            cancel_button=self._cancel_button,
            start_button=self._continue_button,
            selected_child=self._cancel_button,
        )

        self._counting_down = True
        self._countdown_timer = ba.Timer(
            1.0, ba.WeakCall(self._tick), repeat=True, timetype=ba.TimeType.REAL
        )

        # If there is foreground activity, suspend it.
        ba.app.pause()
        self._tick()

    def __del__(self) -> None:
        # If there is suspended foreground activity, resume it.
        ba.app.resume()

    def _tick(self) -> None:
        # if our target activity is gone or has ended, go away
        activity = self._activity()
        if activity is None or activity.has_ended():
            self._on_cancel()
            return

        if ba.internal.get_v1_account_state() == 'signed_in':
            sval = ba.charstr(ba.SpecialChar.TICKET) + str(
                ba.internal.get_v1_account_ticket_count()
            )
        else:
            sval = '?'
        if self._tickets_text is not None:
            assert self._tickets_text_base is not None
            ba.textwidget(
                edit=self._tickets_text,
                text=self._tickets_text_base.replace('${COUNT}', sval),
            )

        if self._counting_down:
            self._count -= 1
            ba.playsound(ba.getsound('tick'))
            if self._count <= 0:
                self._on_cancel()
            else:
                ba.textwidget(edit=self._counter_text, text=str(self._count))

    def _on_cancel_press(self) -> None:
        # disallow for first second
        if self._start_count - self._count < 2:
            ba.playsound(ba.getsound('error'))
        else:
            self._on_cancel()

    def _on_continue_press(self) -> None:
        from bastd.ui import getcurrency

        # Disallow for first second.
        if self._start_count - self._count < 2:
            ba.playsound(ba.getsound('error'))
        else:
            # If somehow we got signed out...
            if ba.internal.get_v1_account_state() != 'signed_in':
                ba.screenmessage(
                    ba.Lstr(resource='notSignedInText'), color=(1, 0, 0)
                )
                ba.playsound(ba.getsound('error'))
                return

            # If it appears we don't have enough tickets, offer to buy more.
            tickets = ba.internal.get_v1_account_ticket_count()
            if tickets < self._cost:
                # FIXME: Should we start the timer back up again after?
                self._counting_down = False
                ba.textwidget(edit=self._counter_text, text='')
                ba.playsound(ba.getsound('error'))
                getcurrency.show_get_tickets_prompt()
                return
            if not self._transitioning_out:
                ba.playsound(ba.getsound('swish'))
                self._transitioning_out = True
                ba.containerwidget(
                    edit=self._root_widget, transition='out_scale'
                )
                self._continue_call()

    def _on_cancel(self) -> None:
        if not self._transitioning_out:
            ba.playsound(ba.getsound('swish'))
            self._transitioning_out = True
            ba.containerwidget(edit=self._root_widget, transition='out_scale')
            self._cancel_call()
