# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to URLs."""

from __future__ import annotations

import ba
import ba.internal


class ShowURLWindow(ba.Window):
    """A window presenting a URL to the user visually."""

    def __init__(self, address: str):

        # in some cases we might want to show it as a qr code
        # (for long URLs especially)
        app = ba.app
        uiscale = app.ui.uiscale
        self._address = address

        self._width = 800
        self._height = 450
        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height + 40),
                transition='in_right',
                scale=(
                    1.25
                    if uiscale is ba.UIScale.SMALL
                    else 1.25
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.25
                ),
            )
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 10),
            size=(0, 0),
            color=ba.app.ui.title_color,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='directBrowserToURLText'),
            maxwidth=self._width * 0.95,
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 60),
            size=(0, 0),
            scale=1.3,
            color=ba.app.ui.infotextcolor,
            h_align='center',
            v_align='center',
            text=address,
            maxwidth=self._width * 0.95,
        )
        button_width = 200

        qr_size = 220
        ba.imagewidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - qr_size * 0.5,
                self._height * 0.5 - qr_size * 0.5 + 10,
            ),
            size=(qr_size, qr_size),
            texture=ba.internal.get_qrcode_texture(address),
        )

        xoffs = 0
        if ba.clipboard_is_supported():
            xoffs = -150
            btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5 - button_width * 0.5 + xoffs,
                    20,
                ),
                size=(button_width, 65),
                autoselect=True,
                label=ba.Lstr(resource='copyText'),
                on_activate_call=self._copy,
            )
            xoffs = 150

        btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - button_width * 0.5 + xoffs, 20),
            size=(button_width, 65),
            autoselect=True,
            label=ba.Lstr(resource='doneText'),
            on_activate_call=self._done,
        )
        # we have no 'cancel' button but still want to be able to
        # hit back/escape/etc to leave..
        ba.containerwidget(
            edit=self._root_widget,
            selected_child=btn,
            start_button=btn,
            on_cancel_call=btn.activate,
        )

    def _copy(self) -> None:
        ba.clipboard_set_text(self._address)
        ba.screenmessage(ba.Lstr(resource='copyConfirmText'), color=(0, 1, 0))

    def _done(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_left')
