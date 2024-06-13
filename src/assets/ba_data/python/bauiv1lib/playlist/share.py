# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for importing shared playlists."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, override

from bauiv1lib.sendinfo import SendInfoWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class SharePlaylistImportWindow(SendInfoWindow):
    """Window for importing a shared playlist."""

    def __init__(
        self,
        origin_widget: bui.Widget | None = None,
        on_success_callback: Callable[[], Any] | None = None,
    ):
        SendInfoWindow.__init__(
            self, modal=True, legacy_code_mode=True, origin_widget=origin_widget
        )
        self._on_success_callback = on_success_callback

    def _on_import_response(self, response: dict[str, Any] | None) -> None:
        if response is None:
            bui.screenmessage(bui.Lstr(resource='errorText'), color=(1, 0, 0))
            bui.getsound('error').play()
            return

        if response['playlistType'] == 'Team Tournament':
            playlist_type_name = bui.Lstr(resource='playModes.teamsText')
        elif response['playlistType'] == 'Free-for-All':
            playlist_type_name = bui.Lstr(resource='playModes.freeForAllText')
        else:
            playlist_type_name = bui.Lstr(value=response['playlistType'])

        bui.screenmessage(
            bui.Lstr(
                resource='importPlaylistSuccessText',
                subs=[
                    ('${TYPE}', playlist_type_name),
                    ('${NAME}', response['playlistName']),
                ],
            ),
            color=(0, 1, 0),
        )
        bui.getsound('gunCocking').play()
        if self._on_success_callback is not None:
            self._on_success_callback()
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

    @override
    def _do_enter(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        plus.add_v1_account_transaction(
            {
                'type': 'IMPORT_PLAYLIST',
                'expire_time': time.time() + 5,
                'code': bui.textwidget(query=self._text_field),
            },
            callback=bui.WeakCall(self._on_import_response),
        )
        plus.run_v1_account_transactions()
        bui.screenmessage(bui.Lstr(resource='importingText'))


class SharePlaylistResultsWindow(bui.Window):
    """Window for sharing playlists."""

    def __init__(
        self, name: str, data: str, origin: tuple[float, float] = (0.0, 0.0)
    ):
        del origin  # unused arg
        self._width = 450
        self._height = 300
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                color=(0.45, 0.63, 0.15),
                transition='in_scale',
                scale=(
                    1.8
                    if uiscale is bui.UIScale.SMALL
                    else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            )
        )
        bui.getsound('cashRegister').play()
        bui.getsound('swish').play()

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(40, self._height - 40),
            size=(50, 50),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.745),
            size=(0, 0),
            color=bui.app.ui_v1.infotextcolor,
            scale=1.0,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=bui.Lstr(
                resource='exportSuccessText', subs=[('${NAME}', name)]
            ),
            maxwidth=self._width * 0.85,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.645),
            size=(0, 0),
            color=bui.app.ui_v1.infotextcolor,
            scale=0.6,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='importPlaylistCodeInstructionsText'),
            maxwidth=self._width * 0.85,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.4),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=2.3,
            h_align='center',
            v_align='center',
            text=data,
            maxwidth=self._width * 0.85,
        )

    def close(self) -> None:
        """Close the window."""
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
