# Released under the MIT License. See LICENSE for details.
#
"""Provides a window which shows info about resource types."""

from __future__ import annotations

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui


class ResourceTypeInfoWindow(PopupWindow):
    """Popup window providing info about resource types."""

    def __init__(self, origin_widget: bui.Widget):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        scale = (
            2.3
            if uiscale is bui.UIScale.SMALL
            else 1.65
            if uiscale is bui.UIScale.MEDIUM
            else 1.23
        )
        self._transitioning_out = False
        self._width = 570
        self._height = 350
        bg_color = (0.5, 0.4, 0.6)
        super().__init__(
            size=(self._width, self._height),
            toolbar_visibility='inherit',
            scale=scale,
            bg_color=bg_color,
            position=origin_widget.get_screen_space_center(),
        )
        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
