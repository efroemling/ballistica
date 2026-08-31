# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for importing shared playlists."""

import time
from typing import TYPE_CHECKING, override

from efro.util import strict_partial
from bauiv1lib.sendinfo import SendInfoWindowLegacyModal
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1 import _builtinassets
from bauiv1 import _uiv1assets

if TYPE_CHECKING:
    from typing import Any, Callable


class SharePlaylistImportWindow(SendInfoWindowLegacyModal):
    """Window for importing a shared playlist."""

    def __init__(
        self,
        origin_widget: bui.Widget | None = None,
        on_success_callback: Callable[[], Any] | None = None,
    ):
        super().__init__(origin_widget=origin_widget)
        self._on_success_callback = on_success_callback

    def _on_import_response(self, response: dict[str, Any] | None) -> None:
        if response is None:
            bui.screenmessage(
                _commonassets.strings.values.error, color=(1, 0, 0)
            )
            _builtinassets.audio.error.get().play()
            return

        # Server-sent playlist-type values map to authored mode names
        # (type-checked refs); anything unknown displays verbatim.
        playlist_type_name = {
            'Team Tournament': _classicassets.strings.play_modes.teams,
            'Free-for-All': _classicassets.strings.play_modes.free_for_all,
        }.get(response['playlistType'])
        if playlist_type_name is None:
            playlist_type_name = bui.langstr_value(response['playlistType'])

        bui.screenmessage(
            _classicassets.strings.playlist.import_success(
                type=playlist_type_name,
                name=response['playlistName'],
            ),
            color=(0, 1, 0),
        )
        _builtinassets.audio.gun_cocking.get().play()
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
            callback=bui.WeakCallPartial(self._on_import_response),
        )
        plus.run_v1_account_transactions()
        bui.screenmessage(_commonassets.strings.status.importing)


class SharePlaylistResultsWindow(bui.Window):
    """Window for sharing playlists."""

    def __init__(
        self, name: str, code: str, origin: tuple[float, float] = (0.0, 0.0)
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
                darken_behind=True,
            )
        )
        _builtinassets.audio.cash_register.get().play()
        _uiv1assets.audio.swish.get().play()

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(40, self._height - 40),
            size=(50, 50),
            label=bui.charstr(bui.SpecialChar.CLOSE),
            textcolor=(1, 1, 1),
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
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
            text=_classicassets.strings.playlist.export_success(name=name),
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
            text=_classicassets.strings.playlist.import_instructions,
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
            text=code,
            maxwidth=self._width * 0.85,
        )
        if bui.clipboard_is_supported():
            bui.buttonwidget(
                parent=self._root_widget,
                size=(140, 40),
                textcolor=(1, 1, 1),
                color=(0.45, 0.63, 0.15),
                on_activate_call=strict_partial(self._copy_press, code),
                label=_classicassets.strings.gather.copy_code,
                position=(self._width * 0.5 - 70, 35),
                autoselect=True,
            )

    def close(self) -> None:
        """Close the window."""
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _copy_press(self, code: str) -> None:
        bui.clipboard_set_text(code)
        bui.screenmessage(_classicassets.strings.gather.copy_code_confirm)
