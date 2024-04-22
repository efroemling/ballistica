# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup telling the user about the BSRemote app."""

from __future__ import annotations

from typing import override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui


class GetBSRemoteWindow(PopupWindow):
    """Popup telling the user about BSRemote app."""

    def __init__(self) -> None:
        position = (0.0, 0.0)
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        scale = (
            2.3
            if uiscale is bui.UIScale.SMALL
            else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
        )
        self._transitioning_out = False
        self._width = 570
        self._height = 350
        bg_color = (0.5, 0.4, 0.6)
        super().__init__(
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=bg_color,
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
        bui.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.5 - 110, self._height * 0.67 - 110),
            size=(220, 220),
            texture=bui.gettexture('multiplayerExamples'),
        )
        bui.textwidget(
            parent=self.root_widget,
            size=(0, 0),
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.9,
            position=(self._width * 0.5, 60),
            text=bui.Lstr(
                resource='remoteAppInfoShortText',
                subs=[
                    ('${APP_NAME}', bui.Lstr(resource='titleText')),
                    (
                        '${REMOTE_APP_NAME}',
                        bui.Lstr(resource='remote_app.app_name'),
                    ),
                ],
            ),
        )

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
