# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to using the macOS Music app for soundtracks."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class MacMusicAppPlaylistSelectWindow(bui.MainWindow):
    """Window for selecting an iTunes playlist."""

    def __init__(
        self,
        callback: Callable[[Any], Any],
        existing_playlist: str | None,
        existing_entry: Any,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        from baclassic.macmusicapp import MacMusicAppMusicPlayer

        self._r = 'editSoundtrackWindow'
        self._callback = callback
        self._existing_playlist = existing_playlist
        self._existing_entry = copy.deepcopy(existing_entry)
        self._width = 520.0
        self._height = 520.0
        self._spacing = 45.0
        v = self._height - 90.0
        v -= self._spacing * 1.0
        super().__init__(
            root_widget=bui.containerwidget(size=(self._width, self._height)),
            transition=transition,
            origin_widget=origin_widget,
        )
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, self._height - 65),
            size=(130, 50),
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self._back,
            autoselect=True,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        assert bui.app.classic is not None
        bui.textwidget(
            parent=self._root_widget,
            position=(20, self._height - 54),
            size=(self._width, 25),
            text=bui.Lstr(resource=f'{self._r}.selectAPlaylistText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            maxwidth=200,
        )
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(40, v - 340),
            size=(self._width - 80, 400),
            selection_loops_to_parent=True,
        )
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._column = bui.columnwidget(
            parent=self._scrollwidget,
            selection_loops_to_parent=True,
        )

        bui.textwidget(
            parent=self._column,
            size=(self._width - 80, 22),
            text=bui.Lstr(resource=f'{self._r}.fetchingITunesText'),
            color=(0.6, 0.9, 0.6, 1.0),
            scale=0.8,
        )
        assert bui.app.classic is not None
        musicplayer = bui.app.classic.music.get_music_player()
        assert isinstance(musicplayer, MacMusicAppMusicPlayer)
        musicplayer.get_playlists(self._playlists_cb)
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull stuff out of self here; if we do it in the lambda we wind
        # up keeping self alive which we don't want.
        callback = self._callback
        existing_playlist = self._existing_playlist
        existing_entry = self._existing_entry

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                callback=callback,
                existing_playlist=existing_playlist,
                existing_entry=existing_entry,
                transition=transition,
                origin_widget=origin_widget,
            )
        )

    def _playlists_cb(self, playlists: list[str]) -> None:
        if self._column:
            for widget in self._column.get_children():
                widget.delete()
            for i, playlist in enumerate(playlists):
                txt = bui.textwidget(
                    parent=self._column,
                    size=(self._width - 80, 30),
                    text=playlist,
                    v_align='center',
                    maxwidth=self._width - 110,
                    selectable=True,
                    on_activate_call=bui.Call(self._sel, playlist),
                    click_activate=True,
                )
                bui.widget(edit=txt, show_buffer_top=40, show_buffer_bottom=40)
                if playlist == self._existing_playlist:
                    bui.columnwidget(
                        edit=self._column, selected_child=txt, visible_child=txt
                    )
                if i == len(playlists) - 1:
                    bui.widget(edit=txt, down_widget=txt)

    def _sel(self, selection: str) -> None:
        if self._root_widget:
            # bui.containerwidget(
            # edit=self._root_widget, transition='out_right')
            self._callback({'type': 'iTunesPlaylist', 'name': selection})
            self.main_window_back()

    def _back(self) -> None:
        # bui.containerwidget(edit=self._root_widget, transition='out_right')
        self.main_window_back()
        self._callback(self._existing_entry)
