# Released under the MIT License. See LICENSE for details.
#
"""Provides ConfirmWindow base class and commonly used derivatives."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any, Callable


class ConfirmWindow:
    """Window for answering simple yes/no questions."""

    def __init__(
        self,
        text: str | ba.Lstr = 'Are you sure?',
        action: Callable[[], Any] | None = None,
        width: float = 360.0,
        height: float = 100.0,
        cancel_button: bool = True,
        cancel_is_selected: bool = False,
        color: tuple[float, float, float] = (1, 1, 1),
        text_scale: float = 1.0,
        ok_text: str | ba.Lstr | None = None,
        cancel_text: str | ba.Lstr | None = None,
        origin_widget: ba.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        if ok_text is None:
            ok_text = ba.Lstr(resource='okText')
        if cancel_text is None:
            cancel_text = ba.Lstr(resource='cancelText')
        height += 40
        width = max(width, 360)
        self._action = action

        # if they provided an origin-widget, scale up from that
        self._transition_out: str | None
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = None
            scale_origin = None
            transition = 'in_right'

        uiscale = ba.app.ui.uiscale
        self.root_widget = ba.containerwidget(
            size=(width, height),
            transition=transition,
            toolbar_visibility='menu_minimal_no_back',
            parent=ba.internal.get_special_widget('overlay_stack'),
            scale=(
                2.1
                if uiscale is ba.UIScale.SMALL
                else 1.5
                if uiscale is ba.UIScale.MEDIUM
                else 1.0
            ),
            scale_origin_stack_offset=scale_origin,
        )

        ba.textwidget(
            parent=self.root_widget,
            position=(width * 0.5, height - 5 - (height - 75) * 0.5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=text,
            scale=text_scale,
            color=color,
            maxwidth=width * 0.9,
            max_height=height - 75,
        )

        cbtn: ba.Widget | None
        if cancel_button:
            cbtn = btn = ba.buttonwidget(
                parent=self.root_widget,
                autoselect=True,
                position=(20, 20),
                size=(150, 50),
                label=cancel_text,
                on_activate_call=self._cancel,
            )
            ba.containerwidget(edit=self.root_widget, cancel_button=btn)
            ok_button_h = width - 175
        else:
            # if they don't want a cancel button, we still want back presses to
            # be able to dismiss the window; just wire it up to do the ok
            # button
            ok_button_h = width * 0.5 - 75
            cbtn = None
        btn = ba.buttonwidget(
            parent=self.root_widget,
            autoselect=True,
            position=(ok_button_h, 20),
            size=(150, 50),
            label=ok_text,
            on_activate_call=self._ok,
        )

        # if they didn't want a cancel button, we still want to be able to hit
        # cancel/back/etc to dismiss the window
        if not cancel_button:
            ba.containerwidget(
                edit=self.root_widget, on_cancel_call=btn.activate
            )

        ba.containerwidget(
            edit=self.root_widget,
            selected_child=(
                cbtn if cbtn is not None and cancel_is_selected else btn
            ),
            start_button=btn,
        )

    def _cancel(self) -> None:
        ba.containerwidget(
            edit=self.root_widget,
            transition=(
                'out_right'
                if self._transition_out is None
                else self._transition_out
            ),
        )

    def _ok(self) -> None:
        if not self.root_widget:
            return
        ba.containerwidget(
            edit=self.root_widget,
            transition=(
                'out_left'
                if self._transition_out is None
                else self._transition_out
            ),
        )
        if self._action is not None:
            self._action()


class QuitWindow:
    """Popup window to confirm quitting."""

    def __init__(
        self,
        swish: bool = False,
        back: bool = False,
        origin_widget: ba.Widget | None = None,
    ):
        ui = ba.app.ui
        app = ba.app
        self._back = back

        # If there's already one of us up somewhere, kill it.
        if ui.quit_window is not None:
            ui.quit_window.delete()
            ui.quit_window = None
        if swish:
            ba.playsound(ba.getsound('swish'))
        quit_resource = (
            'quitGameText' if app.platform == 'mac' else 'exitGameText'
        )
        self._root_widget = ui.quit_window = ConfirmWindow(
            ba.Lstr(
                resource=quit_resource,
                subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))],
            ),
            self._fade_and_quit,
            origin_widget=origin_widget,
        ).root_widget

    def _fade_and_quit(self) -> None:
        ba.internal.fade_screen(
            False, time=0.2, endcall=lambda: ba.quit(soft=True, back=self._back)
        )
        ba.internal.lock_all_input()

        # Unlock and fade back in shortly.. just in case something goes wrong
        # (or on android where quit just backs out of our activity and
        # we may come back)
        ba.timer(0.3, ba.internal.unlock_all_input, timetype=ba.TimeType.REAL)
