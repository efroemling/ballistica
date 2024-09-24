# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for selecting soundtrack entry types."""
from __future__ import annotations

import copy
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class SoundtrackEntryTypeSelectWindow(bui.MainWindow):
    """Window for selecting a soundtrack entry type."""

    def __init__(
        self,
        callback: Callable[[Any], Any],
        current_entry: Any,
        selection_target_name: str,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        assert bui.app.classic is not None
        music = bui.app.classic.music
        self._r = 'editSoundtrackWindow'

        self._selection_target_name = selection_target_name
        self._callback = callback
        self._current_entry = copy.deepcopy(current_entry)

        self._width = 580
        self._height = 220
        spacing = 80

        # FIXME: Generalize this so new custom soundtrack types can add
        # themselves here.
        do_default = True
        do_mac_music_app_playlist = music.supports_soundtrack_entry_type(
            'iTunesPlaylist'
        )
        do_music_file = music.supports_soundtrack_entry_type('musicFile')
        do_music_folder = music.supports_soundtrack_entry_type('musicFolder')

        if do_mac_music_app_playlist:
            self._height += spacing
        if do_music_file:
            self._height += spacing
        if do_music_folder:
            self._height += spacing

        uiscale = bui.app.ui_v1.uiscale

        # NOTE: When something is selected, we close our UI and kick off
        # another window which then calls us back when its done, so the
        # standard UI-cleanup-check complains that something is holding
        # on to our instance after its ui is gone. Should restructure in
        # a cleaner way, but just disabling that check for now.
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.7
                    if uiscale is bui.UIScale.SMALL
                    else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            ),
            cleanupcheck=False,
            transition=transition,
            origin_widget=origin_widget,
        )
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, self._height - 65),
            size=(160, 60),
            scale=0.8,
            text_scale=1.2,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self._on_cancel_press,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 32),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.selectASourceText'),
            color=bui.app.ui_v1.title_color,
            maxwidth=230,
            h_align='center',
            v_align='center',
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 56),
            size=(0, 0),
            text=selection_target_name,
            color=bui.app.ui_v1.infotextcolor,
            scale=0.7,
            maxwidth=230,
            h_align='center',
            v_align='center',
        )

        v = self._height - 155

        current_entry_type = music.get_soundtrack_entry_type(current_entry)

        if do_default:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                size=(self._width - 100, 60),
                position=(50, v),
                label=bui.Lstr(resource=f'{self._r}.useDefaultGameMusicText'),
                on_activate_call=self._on_default_press,
            )
            if current_entry_type == 'default':
                bui.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

        if do_mac_music_app_playlist:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                size=(self._width - 100, 60),
                position=(50, v),
                label=bui.Lstr(resource=f'{self._r}.useITunesPlaylistText'),
                on_activate_call=self._on_mac_music_app_playlist_press,
                icon=None,
            )
            if current_entry_type == 'iTunesPlaylist':
                bui.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

        if do_music_file:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                size=(self._width - 100, 60),
                position=(50, v),
                label=bui.Lstr(resource=f'{self._r}.useMusicFileText'),
                on_activate_call=self._on_music_file_press,
                icon=bui.gettexture('file'),
            )
            if current_entry_type == 'musicFile':
                bui.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

        if do_music_folder:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                size=(self._width - 100, 60),
                position=(50, v),
                label=bui.Lstr(resource=f'{self._r}.useMusicFolderText'),
                on_activate_call=self._on_music_folder_press,
                icon=bui.gettexture('folder'),
                icon_color=(1.1, 0.8, 0.2),
            )
            if current_entry_type == 'musicFolder':
                bui.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull these out of self here; if we reference self in the
        # lambda we'll keep our window alive which is bad.
        current_entry = self._current_entry
        callback = self._callback
        selection_target_name = self._selection_target_name

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                current_entry=current_entry,
                callback=callback,
                selection_target_name=selection_target_name,
            )
        )

    def _on_mac_music_app_playlist_press(self) -> None:
        assert bui.app.classic is not None
        music = bui.app.classic.music
        from bauiv1lib.soundtrack.macmusicapp import (
            MacMusicAppPlaylistSelectWindow,
        )

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        current_playlist_entry: str | None
        if (
            music.get_soundtrack_entry_type(self._current_entry)
            == 'iTunesPlaylist'
        ):
            current_playlist_entry = music.get_soundtrack_entry_name(
                self._current_entry
            )
        else:
            current_playlist_entry = None

        self.main_window_replace(
            MacMusicAppPlaylistSelectWindow(
                self._callback, current_playlist_entry, self._current_entry
            )
        )

    def _on_music_file_press(self) -> None:
        from babase import android_get_external_files_dir
        from baclassic.osmusic import OSMusicPlayer
        from bauiv1lib.fileselector import FileSelectorWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        base_path = android_get_external_files_dir()
        assert bui.app.classic is not None

        self.main_window_replace(
            FileSelectorWindow(
                base_path,
                callback=self._music_file_selector_cb,
                show_base_path=False,
                valid_file_extensions=(
                    OSMusicPlayer.get_valid_music_file_extensions()
                ),
                allow_folders=False,
            ),
        )

    def _on_music_folder_press(self) -> None:
        from bauiv1lib.fileselector import FileSelectorWindow
        from babase import android_get_external_files_dir

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        base_path = android_get_external_files_dir()
        assert bui.app.classic is not None

        self.main_window_replace(
            FileSelectorWindow(
                base_path,
                callback=self._music_folder_selector_cb,
                show_base_path=False,
                valid_file_extensions=[],
                allow_folders=True,
            ),
        )

    def _music_file_selector_cb(self, result: str | None) -> None:
        if result is None:
            self._callback(self._current_entry)
        else:
            self._callback({'type': 'musicFile', 'name': result})

    def _music_folder_selector_cb(self, result: str | None) -> None:
        if result is None:
            self._callback(self._current_entry)
        else:
            self._callback({'type': 'musicFolder', 'name': result})

    def _on_default_press(self) -> None:
        self.main_window_back()
        self._callback(None)

    def _on_cancel_press(self) -> None:
        self.main_window_back()
        self._callback(self._current_entry)
