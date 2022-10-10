# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup telling the user about the BSRemote app."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.ui import popup

if TYPE_CHECKING:
    pass


class GetBSRemoteWindow(popup.PopupWindow):
    """Popup telling the user about BSRemote app."""

    def __init__(self) -> None:
        position = (0.0, 0.0)
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
            position=(self._width * 0.5 - 110, self._height * 0.67 - 110),
            size=(220, 220),
            texture=ba.gettexture('multiplayerExamples'),
        )
        ba.textwidget(
            parent=self.root_widget,
            size=(0, 0),
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.9,
            position=(self._width * 0.5, 60),
            text=ba.Lstr(
                resource='remoteAppInfoShortText',
                subs=[
                    ('${APP_NAME}', ba.Lstr(resource='titleText')),
                    (
                        '${REMOTE_APP_NAME}',
                        ba.Lstr(resource='remote_app.app_name'),
                    ),
                ],
            ),
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
