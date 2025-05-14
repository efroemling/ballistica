# Released under the MIT License. See LICENSE for details.
#
"""Provides ConfirmWindow base class and commonly used derivatives."""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class ConfirmWindow:
    """Window for answering simple yes/no questions."""

    def __init__(
        self,
        text: str | bui.Lstr | None = None,
        action: Callable[[], Any] | None = None,
        width: float = 360.0,
        height: float = 100.0,
        *,
        cancel_button: bool = True,
        cancel_is_selected: bool = False,
        color: tuple[float, float, float] = (1, 1, 1),
        text_scale: float = 1.0,
        ok_text: str | bui.Lstr | None = None,
        cancel_text: str | bui.Lstr | None = None,
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        if text is None:
            text = bui.Lstr(resource='areYouSureText')
        if ok_text is None:
            ok_text = bui.Lstr(resource='okText')
        if cancel_text is None:
            cancel_text = bui.Lstr(resource='cancelText')
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

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self.root_widget = bui.containerwidget(
            size=(width, height),
            transition=transition,
            toolbar_visibility='menu_minimal_no_back',
            parent=bui.get_special_widget('overlay_stack'),
            scale=(
                1.9
                if uiscale is bui.UIScale.SMALL
                else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
            ),
            scale_origin_stack_offset=scale_origin,
        )

        bui.textwidget(
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

        cbtn: bui.Widget | None
        if cancel_button:
            cbtn = btn = bui.buttonwidget(
                parent=self.root_widget,
                autoselect=True,
                position=(20, 20),
                size=(150, 50),
                label=cancel_text,
                on_activate_call=self._cancel,
            )
            bui.containerwidget(edit=self.root_widget, cancel_button=btn)
            ok_button_h = width - 175
        else:
            # if they don't want a cancel button, we still want back presses to
            # be able to dismiss the window; just wire it up to do the ok
            # button
            ok_button_h = width * 0.5 - 75
            cbtn = None
        btn = bui.buttonwidget(
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
            bui.containerwidget(
                edit=self.root_widget, on_cancel_call=btn.activate
            )

        bui.containerwidget(
            edit=self.root_widget,
            selected_child=(
                cbtn if cbtn is not None and cancel_is_selected else btn
            ),
            start_button=btn,
        )

    def _cancel(self) -> None:
        bui.containerwidget(
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
        bui.containerwidget(
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
        quit_type: bui.QuitType | None = None,
        swish: bool = False,
        origin_widget: bui.Widget | None = None,
    ):
        classic = bui.app.classic
        assert classic is not None
        ui = bui.app.ui_v1
        app = bui.app
        self._quit_type = quit_type

        # If there's already one of us up somewhere, kill it.
        if ui.quit_window is not None:
            ui.quit_window.delete()
            ui.quit_window = None
        if swish:
            bui.getsound('swish').play()

        if app.classic is None:
            if bui.do_once():
                logging.warning(
                    'QuitWindow needs to be updated to work without classic.'
                )
            quit_resource = 'exitGameText'
        else:
            quit_resource = (
                'quitGameText'
                if app.classic.platform == 'mac'
                else 'exitGameText'
            )
        self._root_widget = ui.quit_window = ConfirmWindow(
            bui.Lstr(
                resource=quit_resource,
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            lambda: (
                bui.quit(confirm=False, quit_type=self._quit_type)
                if self._quit_type is not None
                else bui.quit(confirm=False)
            ),
            origin_widget=origin_widget,
        ).root_widget
