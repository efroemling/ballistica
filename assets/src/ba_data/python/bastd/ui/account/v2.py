# Released under the MIT License. See LICENSE for details.
#
"""V2 account ui bits."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba

if TYPE_CHECKING:
    from typing import Any, Optional


class V2SignInWindow(ba.Window):
    """A window allowing signing in to a v2 account."""

    def __init__(self, origin_widget: ba.Widget):
        from ba.internal import is_browser_likely_available
        logincode = '1412345'
        address = (
            f'{_ba.get_master_server_address(version=2)}?login={logincode}')
        self._width = 600
        self._height = 500
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            scale_origin_stack_offset=origin_widget.get_screen_space_center(),
            scale=(1.25 if uiscale is ba.UIScale.SMALL else
                   1.0 if uiscale is ba.UIScale.MEDIUM else 0.85)))

        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 85),
            size=(0, 0),
            text=ba.Lstr(
                resource='accountSettingsWindow.v2LinkInstructionsText'),
            color=ba.app.ui.title_color,
            maxwidth=self._width * 0.9,
            h_align='center',
            v_align='center')
        button_width = 450
        if is_browser_likely_available():
            ba.buttonwidget(parent=self._root_widget,
                            position=((self._width * 0.5 - button_width * 0.5),
                                      self._height - 175),
                            autoselect=True,
                            size=(button_width, 60),
                            label=ba.Lstr(value=address),
                            color=(0.55, 0.5, 0.6),
                            textcolor=(0.75, 0.7, 0.8),
                            on_activate_call=lambda: ba.open_url(address))
            qroffs = 0.0
        else:
            ba.textwidget(parent=self._root_widget,
                          position=(self._width * 0.5, self._height - 135),
                          size=(0, 0),
                          text=ba.Lstr(value=address),
                          flatness=1.0,
                          maxwidth=self._width,
                          scale=0.75,
                          h_align='center',
                          v_align='center')
            qroffs = 20.0

        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(30, self._height - 55),
            size=(130, 50),
            scale=0.8,
            label=ba.Lstr(resource='cancelText'),
            # color=(0.6, 0.5, 0.6),
            on_activate_call=self._done,
            autoselect=True,
            textcolor=(0.75, 0.7, 0.8),
            # icon=ba.gettexture('crossOut'),
            # iconscale=1.2
        )
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        qr_size = 270
        ba.imagewidget(parent=self._root_widget,
                       position=(self._width * 0.5 - qr_size * 0.5,
                                 self._height * 0.34 + qroffs - qr_size * 0.5),
                       size=(qr_size, qr_size),
                       texture=_ba.get_qrcode_texture(address))

    def _done(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
