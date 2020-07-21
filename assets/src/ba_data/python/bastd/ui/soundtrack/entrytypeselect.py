# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Provides UI for selecting soundtrack entry types."""
from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Callable, Optional


class SoundtrackEntryTypeSelectWindow(ba.Window):
    """Window for selecting a soundtrack entry type."""

    def __init__(self,
                 callback: Callable[[Any], Any],
                 current_entry: Any,
                 selection_target_name: str,
                 transition: str = 'in_right'):
        music = ba.app.music
        self._r = 'editSoundtrackWindow'

        self._callback = callback
        self._current_entry = copy.deepcopy(current_entry)

        self._width = 580
        self._height = 220
        spacing = 80

        # FIXME: Generalize this so new custom soundtrack types can add
        # themselves here.
        do_default = True
        do_mac_music_app_playlist = music.supports_soundtrack_entry_type(
            'iTunesPlaylist')
        do_music_file = music.supports_soundtrack_entry_type('musicFile')
        do_music_folder = music.supports_soundtrack_entry_type('musicFolder')

        if do_mac_music_app_playlist:
            self._height += spacing
        if do_music_file:
            self._height += spacing
        if do_music_folder:
            self._height += spacing

        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition=transition,
            scale=(1.7 if uiscale is ba.UIScale.SMALL else
                   1.4 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(35, self._height - 65),
                              size=(160, 60),
                              scale=0.8,
                              text_scale=1.2,
                              label=ba.Lstr(resource='cancelText'),
                              on_activate_call=self._on_cancel_press)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 32),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.selectASourceText'),
                      color=ba.app.ui.title_color,
                      maxwidth=230,
                      h_align='center',
                      v_align='center')

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 56),
                      size=(0, 0),
                      text=selection_target_name,
                      color=ba.app.ui.infotextcolor,
                      scale=0.7,
                      maxwidth=230,
                      h_align='center',
                      v_align='center')

        v = self._height - 155

        current_entry_type = music.get_soundtrack_entry_type(current_entry)

        if do_default:
            btn = ba.buttonwidget(parent=self._root_widget,
                                  size=(self._width - 100, 60),
                                  position=(50, v),
                                  label=ba.Lstr(resource=self._r +
                                                '.useDefaultGameMusicText'),
                                  on_activate_call=self._on_default_press)
            if current_entry_type == 'default':
                ba.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

        if do_mac_music_app_playlist:
            btn = ba.buttonwidget(
                parent=self._root_widget,
                size=(self._width - 100, 60),
                position=(50, v),
                label=ba.Lstr(resource=self._r + '.useITunesPlaylistText'),
                on_activate_call=self._on_mac_music_app_playlist_press,
                icon=None)
            if current_entry_type == 'iTunesPlaylist':
                ba.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

        if do_music_file:
            btn = ba.buttonwidget(parent=self._root_widget,
                                  size=(self._width - 100, 60),
                                  position=(50, v),
                                  label=ba.Lstr(resource=self._r +
                                                '.useMusicFileText'),
                                  on_activate_call=self._on_music_file_press,
                                  icon=ba.gettexture('file'))
            if current_entry_type == 'musicFile':
                ba.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

        if do_music_folder:
            btn = ba.buttonwidget(parent=self._root_widget,
                                  size=(self._width - 100, 60),
                                  position=(50, v),
                                  label=ba.Lstr(resource=self._r +
                                                '.useMusicFolderText'),
                                  on_activate_call=self._on_music_folder_press,
                                  icon=ba.gettexture('folder'),
                                  icon_color=(1.1, 0.8, 0.2))
            if current_entry_type == 'musicFolder':
                ba.containerwidget(edit=self._root_widget, selected_child=btn)
            v -= spacing

    def _on_mac_music_app_playlist_press(self) -> None:
        music = ba.app.music
        from bastd.ui.soundtrack import macmusicapp
        ba.containerwidget(edit=self._root_widget, transition='out_left')

        current_playlist_entry: Optional[str]
        if (music.get_soundtrack_entry_type(
                self._current_entry) == 'iTunesPlaylist'):
            current_playlist_entry = music.get_soundtrack_entry_name(
                self._current_entry)
        else:
            current_playlist_entry = None
        ba.app.ui.set_main_menu_window(
            macmusicapp.MacMusicAppPlaylistSelectWindow(
                self._callback, current_playlist_entry,
                self._current_entry).get_root_widget())

    def _on_music_file_press(self) -> None:
        from ba.osmusic import OSMusicPlayer
        from bastd.ui import fileselector
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        base_path = _ba.android_get_external_storage_path()
        ba.app.ui.set_main_menu_window(
            fileselector.FileSelectorWindow(
                base_path,
                callback=self._music_file_selector_cb,
                show_base_path=False,
                valid_file_extensions=(
                    OSMusicPlayer.get_valid_music_file_extensions()),
                allow_folders=False).get_root_widget())

    def _on_music_folder_press(self) -> None:
        from bastd.ui import fileselector
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        base_path = _ba.android_get_external_storage_path()
        ba.app.ui.set_main_menu_window(
            fileselector.FileSelectorWindow(
                base_path,
                callback=self._music_folder_selector_cb,
                show_base_path=False,
                valid_file_extensions=[],
                allow_folders=True).get_root_widget())

    def _music_file_selector_cb(self, result: Optional[str]) -> None:
        if result is None:
            self._callback(self._current_entry)
        else:
            self._callback({'type': 'musicFile', 'name': result})

    def _music_folder_selector_cb(self, result: Optional[str]) -> None:
        if result is None:
            self._callback(self._current_entry)
        else:
            self._callback({'type': 'musicFolder', 'name': result})

    def _on_default_press(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        self._callback(None)

    def _on_cancel_press(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        self._callback(self._current_entry)
