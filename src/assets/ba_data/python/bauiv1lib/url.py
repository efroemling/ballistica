# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to URLs."""

from __future__ import annotations

import bauiv1 as bui


class ShowURLWindow(bui.Window):
    """A window presenting a URL to the user visually."""

    def __init__(self, address: str):
        # in some cases we might want to show it as a qr code
        # (for long URLs especially)
        app = bui.app
        assert app.classic is not None
        uiscale = app.ui_v1.uiscale
        self._address = address

        self._width = 800
        self._height = 450
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + 40),
                transition='in_right',
                scale=(
                    1.25
                    if uiscale is bui.UIScale.SMALL
                    else 1.25 if uiscale is bui.UIScale.MEDIUM else 1.25
                ),
            )
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 10),
            size=(0, 0),
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='directBrowserToURLText'),
            maxwidth=self._width * 0.95,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 60),
            size=(0, 0),
            scale=1.3,
            color=app.ui_v1.infotextcolor,
            h_align='center',
            v_align='center',
            text=address,
            maxwidth=self._width * 0.95,
        )
        button_width = 200

        qr_size = 220
        bui.imagewidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - qr_size * 0.5,
                self._height * 0.5 - qr_size * 0.5 + 10,
            ),
            size=(qr_size, qr_size),
            texture=bui.get_qrcode_texture(address),
        )

        xoffs = 0
        if bui.clipboard_is_supported():
            xoffs = -150
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5 - button_width * 0.5 + xoffs,
                    20,
                ),
                size=(button_width, 65),
                autoselect=True,
                label=bui.Lstr(resource='copyText'),
                on_activate_call=self._copy,
            )
            xoffs = 150

        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - button_width * 0.5 + xoffs, 20),
            size=(button_width, 65),
            autoselect=True,
            label=bui.Lstr(resource='doneText'),
            on_activate_call=self._done,
        )
        # we have no 'cancel' button but still want to be able to
        # hit back/escape/etc to leave..
        bui.containerwidget(
            edit=self._root_widget,
            selected_child=btn,
            start_button=btn,
            on_cancel_call=btn.activate,
        )

    def _copy(self) -> None:
        bui.clipboard_set_text(self._address)
        bui.screenmessage(bui.Lstr(resource='copyConfirmText'), color=(0, 1, 0))

    def _done(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_left')
