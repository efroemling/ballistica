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
"""Music playback functionality using the Mac Music (formerly iTunes) app."""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import _ba
from ba._music import MusicPlayer

if TYPE_CHECKING:
    from typing import List, Optional, Callable, Any


class MacMusicAppMusicPlayer(MusicPlayer):
    """A music-player that utilizes the macOS Music.app for playback.

    Allows selecting playlists as entries.
    """

    def __init__(self) -> None:
        super().__init__()
        self._thread = _MacMusicAppThread()
        self._thread.start()

    def on_select_entry(self, callback: Callable[[Any], None],
                        current_entry: Any, selection_target_name: str) -> Any:
        # pylint: disable=cyclic-import
        from bastd.ui.soundtrack import entrytypeselect as etsel
        return etsel.SoundtrackEntryTypeSelectWindow(callback, current_entry,
                                                     selection_target_name)

    def on_set_volume(self, volume: float) -> None:
        self._thread.set_volume(volume)

    def get_playlists(self, callback: Callable) -> None:
        """Asynchronously fetch the list of available iTunes playlists."""
        self._thread.get_playlists(callback)

    def on_play(self, entry: Any) -> None:
        music = _ba.app.music
        entry_type = music.get_soundtrack_entry_type(entry)
        if entry_type == 'iTunesPlaylist':
            self._thread.play_playlist(music.get_soundtrack_entry_name(entry))
        else:
            print('MacMusicAppMusicPlayer passed unrecognized entry type:',
                  entry_type)

    def on_stop(self) -> None:
        self._thread.play_playlist(None)

    def on_app_shutdown(self) -> None:
        self._thread.shutdown()


class _MacMusicAppThread(threading.Thread):
    """Thread which wrangles Music.app playback"""

    def __init__(self) -> None:
        super().__init__()
        self._commands_available = threading.Event()
        self._commands: List[List] = []
        self._volume = 1.0
        self._current_playlist: Optional[str] = None
        self._orig_volume: Optional[int] = None

    def run(self) -> None:
        """Run the Music.app thread."""
        from ba._general import Call
        from ba._lang import Lstr
        from ba._enums import TimeType
        _ba.set_thread_name('BA_MacMusicAppThread')
        _ba.mac_music_app_init()

        # Let's mention to the user we're launching Music.app in case
        # it causes any funny business (this used to background the app
        # sometimes, though I think that is fixed now)
        def do_print() -> None:
            _ba.timer(1.0,
                      Call(_ba.screenmessage, Lstr(resource='usingItunesText'),
                           (0, 1, 0)),
                      timetype=TimeType.REAL)

        _ba.pushcall(do_print, from_other_thread=True)

        # Here we grab this to force the actual launch.
        _ba.mac_music_app_get_volume()
        _ba.mac_music_app_get_library_source()
        done = False
        while not done:
            self._commands_available.wait()
            self._commands_available.clear()

            # We're not protecting this list with a mutex but we're
            # just using it as a simple queue so it should be fine.
            while self._commands:
                cmd = self._commands.pop(0)
                if cmd[0] == 'DIE':
                    self._handle_die_command()
                    done = True
                    break
                if cmd[0] == 'PLAY':
                    self._handle_play_command(target=cmd[1])
                elif cmd[0] == 'GET_PLAYLISTS':
                    self._handle_get_playlists_command(target=cmd[1])

                del cmd  # Allows the command data/callback/etc to be freed.

    def set_volume(self, volume: float) -> None:
        """Set volume to a value between 0 and 1."""
        old_volume = self._volume
        self._volume = volume

        # If we've got nothing we're supposed to be playing,
        # don't touch itunes/music.
        if self._current_playlist is None:
            return

        # If volume is going to zero, stop actually playing
        # but don't clear playlist.
        if old_volume > 0.0 and volume == 0.0:
            try:
                assert self._orig_volume is not None
                _ba.mac_music_app_stop()
                _ba.mac_music_app_set_volume(self._orig_volume)
            except Exception as exc:
                print('Error stopping iTunes music:', exc)
        elif self._volume > 0:

            # If volume was zero, store pre-playing volume and start
            # playing.
            if old_volume == 0.0:
                self._orig_volume = _ba.mac_music_app_get_volume()
            self._update_mac_music_app_volume()
            if old_volume == 0.0:
                self._play_current_playlist()

    def play_playlist(self, musictype: Optional[str]) -> None:
        """Play the given playlist."""
        self._commands.append(['PLAY', musictype])
        self._commands_available.set()

    def shutdown(self) -> None:
        """Request that the player shuts down."""
        self._commands.append(['DIE'])
        self._commands_available.set()
        self.join()

    def get_playlists(self, callback: Callable[[Any], None]) -> None:
        """Request the list of playlists."""
        self._commands.append(['GET_PLAYLISTS', callback])
        self._commands_available.set()

    def _handle_get_playlists_command(
            self, target: Callable[[List[str]], None]) -> None:
        from ba._general import Call
        try:
            playlists = _ba.mac_music_app_get_playlists()
            playlists = [
                p for p in playlists if p not in [
                    'Music', 'Movies', 'TV Shows', 'Podcasts', 'iTunes\xa0U',
                    'Books', 'Genius', 'iTunes DJ', 'Music Videos',
                    'Home Videos', 'Voice Memos', 'Audiobooks'
                ]
            ]
            playlists.sort(key=lambda x: x.lower())
        except Exception as exc:
            print('Error getting iTunes playlists:', exc)
            playlists = []
        _ba.pushcall(Call(target, playlists), from_other_thread=True)

    def _handle_play_command(self, target: Optional[str]) -> None:
        if target is None:
            if self._current_playlist is not None and self._volume > 0:
                try:
                    assert self._orig_volume is not None
                    _ba.mac_music_app_stop()
                    _ba.mac_music_app_set_volume(self._orig_volume)
                except Exception as exc:
                    print('Error stopping iTunes music:', exc)
            self._current_playlist = None
        else:
            # If we've got something playing with positive
            # volume, stop it.
            if self._current_playlist is not None and self._volume > 0:
                try:
                    assert self._orig_volume is not None
                    _ba.mac_music_app_stop()
                    _ba.mac_music_app_set_volume(self._orig_volume)
                except Exception as exc:
                    print('Error stopping iTunes music:', exc)

            # Set our playlist and play it if our volume is up.
            self._current_playlist = target
            if self._volume > 0:
                self._orig_volume = (_ba.mac_music_app_get_volume())
                self._update_mac_music_app_volume()
                self._play_current_playlist()

    def _handle_die_command(self) -> None:

        # Only stop if we've actually played something
        # (we don't want to kill music the user has playing).
        if self._current_playlist is not None and self._volume > 0:
            try:
                assert self._orig_volume is not None
                _ba.mac_music_app_stop()
                _ba.mac_music_app_set_volume(self._orig_volume)
            except Exception as exc:
                print('Error stopping iTunes music:', exc)

    def _play_current_playlist(self) -> None:
        try:
            from ba import _lang
            from ba._general import Call
            assert self._current_playlist is not None
            if _ba.mac_music_app_play_playlist(self._current_playlist):
                pass
            else:
                _ba.pushcall(Call(
                    _ba.screenmessage,
                    _lang.get_resource('playlistNotFoundText') + ': \'' +
                    self._current_playlist + '\'', (1, 0, 0)),
                             from_other_thread=True)
        except Exception:
            from ba import _error
            _error.print_exception(
                f'error playing playlist {self._current_playlist}')

    def _update_mac_music_app_volume(self) -> None:
        _ba.mac_music_app_set_volume(
            max(0, min(100, int(100.0 * self._volume))))
