# Released under the MIT License. See LICENSE for details.
#
"""Music playback using OS functionality exposed through the C++ layer."""
from __future__ import annotations

import os
import random
import threading
from typing import TYPE_CHECKING

import _ba
from ba._music import MusicPlayer

if TYPE_CHECKING:
    from typing import Callable, Any


class OSMusicPlayer(MusicPlayer):
    """Music player that talks to internal C++ layer for functionality.

    (internal)"""

    def __init__(self) -> None:
        super().__init__()
        self._want_to_play = False
        self._actually_playing = False

    @classmethod
    def get_valid_music_file_extensions(cls) -> list[str]:
        """Return file extensions for types playable on this device."""
        # FIXME: should ask the C++ layer for these; just hard-coding for now.
        return ['mp3', 'ogg', 'm4a', 'wav', 'flac', 'mid']

    def on_select_entry(
        self,
        callback: Callable[[Any], None],
        current_entry: Any,
        selection_target_name: str,
    ) -> Any:
        # pylint: disable=cyclic-import
        from bastd.ui.soundtrack.entrytypeselect import (
            SoundtrackEntryTypeSelectWindow,
        )

        return SoundtrackEntryTypeSelectWindow(
            callback, current_entry, selection_target_name
        )

    def on_set_volume(self, volume: float) -> None:
        _ba.music_player_set_volume(volume)

    def on_play(self, entry: Any) -> None:
        music = _ba.app.music
        entry_type = music.get_soundtrack_entry_type(entry)
        name = music.get_soundtrack_entry_name(entry)
        assert name is not None
        if entry_type == 'musicFile':
            self._want_to_play = self._actually_playing = True
            _ba.music_player_play(name)
        elif entry_type == 'musicFolder':

            # Launch a thread to scan this folder and give us a random
            # valid file within it.
            self._want_to_play = True
            self._actually_playing = False
            _PickFolderSongThread(
                name,
                self.get_valid_music_file_extensions(),
                self._on_play_folder_cb,
            ).start()

    def _on_play_folder_cb(
        self, result: str | list[str], error: str | None = None
    ) -> None:
        from ba import _language

        if error is not None:
            rstr = _language.Lstr(
                resource='internal.errorPlayingMusicText'
            ).evaluate()
            if isinstance(result, str):
                err_str = (
                    rstr.replace('${MUSIC}', os.path.basename(result))
                    + '; '
                    + str(error)
                )
            else:
                err_str = (
                    rstr.replace('${MUSIC}', '<multiple>') + '; ' + str(error)
                )
            _ba.screenmessage(err_str, color=(1, 0, 0))
            return

        # There's a chance a stop could have been issued before our thread
        # returned. If that's the case, don't play.
        if not self._want_to_play:
            print('_on_play_folder_cb called with _want_to_play False')
        else:
            self._actually_playing = True
            _ba.music_player_play(result)

    def on_stop(self) -> None:
        self._want_to_play = False
        self._actually_playing = False
        _ba.music_player_stop()

    def on_app_shutdown(self) -> None:
        _ba.music_player_shutdown()


class _PickFolderSongThread(threading.Thread):
    def __init__(
        self,
        path: str,
        valid_extensions: list[str],
        callback: Callable[[str | list[str], str | None], None],
    ):
        super().__init__()
        self._valid_extensions = valid_extensions
        self._callback = callback
        self._path = path

    def run(self) -> None:
        from ba import _language
        from ba._general import Call

        do_print_error = True
        try:
            _ba.set_thread_name('BA_PickFolderSongThread')
            all_files: list[str] = []
            valid_extensions = ['.' + x for x in self._valid_extensions]
            for root, _subdirs, filenames in os.walk(self._path):
                for fname in filenames:
                    if any(
                        fname.lower().endswith(ext) for ext in valid_extensions
                    ):
                        all_files.insert(
                            random.randrange(len(all_files) + 1),
                            root + '/' + fname,
                        )
            if not all_files:
                do_print_error = False
                raise RuntimeError(
                    _language.Lstr(
                        resource='internal.noMusicFilesInFolderText'
                    ).evaluate()
                )
            _ba.pushcall(
                Call(self._callback, all_files, None), from_other_thread=True
            )
        except Exception as exc:
            from ba import _error

            if do_print_error:
                _error.print_exception()
            try:
                err_str = str(exc)
            except Exception:
                err_str = '<ENCERR4523>'
            _ba.pushcall(
                Call(self._callback, self._path, err_str),
                from_other_thread=True,
            )
