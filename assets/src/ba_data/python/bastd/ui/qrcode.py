# Released under the MIT License. See LICENSE for details.
#
"""Provides functionality for displaying QR codes."""
from __future__ import annotations

import ba
from bastd.ui import popup


class QRCodeWindow(popup.PopupWindow):
    """Popup window that shows a QR code."""

    def __init__(self, origin_widget: ba.Widget, qr_tex: ba.Texture):

        position = origin_widget.get_screen_space_center()
        uiscale = ba.app.ui.uiscale
        scale = (
            2.3
            if uiscale is ba.UIScale.SMALL
            else 1.65
            if uiscale is ba.UIScale.MEDIUM
            else 1.23
        )
        self._transitioning_out = False
        self._width = 450
        self._height = 400
        bg_color = (0.5, 0.4, 0.6)
        popup.PopupWindow.__init__(
            self,
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=bg_color,
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
        ba.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.5 - 150, self._height * 0.5 - 150),
            size=(300, 300),
            texture=qr_tex,
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
