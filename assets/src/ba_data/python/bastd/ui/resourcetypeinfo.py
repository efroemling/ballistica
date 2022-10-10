# Released under the MIT License. See LICENSE for details.
#
"""Provides a window which shows info about resource types."""

from __future__ import annotations

import ba
from bastd.ui import popup


class ResourceTypeInfoWindow(popup.PopupWindow):
    """Popup window providing info about resource types."""

    def __init__(self, origin_widget: ba.Widget):
        uiscale = ba.app.ui.uiscale
        scale = (
            2.3
            if uiscale is ba.UIScale.SMALL
            else 1.65
            if uiscale is ba.UIScale.MEDIUM
            else 1.23
        )
        self._transitioning_out = False
        self._width = 570
        self._height = 350
        bg_color = (0.5, 0.4, 0.6)
        popup.PopupWindow.__init__(
            self,
            size=(self._width, self._height),
            toolbar_visibility='inherit',
            scale=scale,
            bg_color=bg_color,
            position=origin_widget.get_screen_space_center(),
        )
        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2,
        )

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()
