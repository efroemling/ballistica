# Released under the MIT License. See LICENSE for details.
#
"""Music playback functionality using the Mac Music (formerly iTunes) app."""
from __future__ import annotations

import logging
import threading
from collections import deque
from typing import TYPE_CHECKING, override

import babase

from baclassic._music import MusicPlayer

if TYPE_CHECKING:
    from typing import Callable, Any

    import bauiv1


class MacMusicAppMusicPlayer(MusicPlayer):
    """A music-player that utilizes the macOS Music.app for playback.

    Allows selecting playlists as entries.
    """

    def __init__(self) -> None:
        super().__init__()
        self._thread = _MacMusicAppThread()
        self._thread.start()

    @override
    def on_select_entry(
        self,
        callback: Callable[[Any], None],
        current_entry: Any,
        selection_target_name: str,
    ) -> bauiv1.MainWindow:
        # pylint: disable=cyclic-import
        from bauiv1lib.soundtrack import entrytypeselect as etsel

        return etsel.SoundtrackEntryTypeSelectWindow(
            callback, current_entry, selection_target_name
        )

    @override
    def on_set_volume(self, volume: float) -> None:
        self._thread.set_volume(volume)

    def get_playlists(self, callback: Callable) -> None:
        """Asynchronously fetch the list of available iTunes playlists."""
        self._thread.get_playlists(callback)

    @override
    def on_play(self, entry: Any) -> None:
        assert babase.app.classic is not None
        music = babase.app.classic.music
        entry_type = music.get_soundtrack_entry_type(entry)
        if entry_type == 'iTunesPlaylist':
            self._thread.play_playlist(music.get_soundtrack_entry_name(entry))
        else:
            print(
                'MacMusicAppMusicPlayer passed unrecognized entry type:',
                entry_type,
            )

    @override
    def on_stop(self) -> None:
        self._thread.play_playlist(None)

    @override
    def on_app_shutdown(self) -> None:
        self._thread.shutdown()


class _MacMusicAppThread(threading.Thread):
    """Thread which wrangles Music.app playback"""

    def __init__(self) -> None:
        super().__init__()
        self._commands_available = threading.Event()
        self._commands = deque[list]()
        self._volume = 1.0
        self._current_playlist: str | None = None
        self._orig_volume: int | None = None

    @override
    def run(self) -> None:
        """Run the Music.app thread."""
        babase.set_thread_name('BA_MacMusicAppThread')

        # Let's mention to the user we're launching Music.app in case
        # it causes any funny business (this used to background the app
        # sometimes, though I think that is fixed now)
        def do_print() -> None:
            babase.apptimer(
                0.5,
                babase.Call(
                    babase.screenmessage,
                    babase.Lstr(resource='usingItunesText'),
                    (0, 1, 0),
                ),
            )

        babase.pushcall(do_print, from_other_thread=True)

        babase.mac_music_app_init()

        done = False
        while not done:
            self._commands_available.wait()
            self._commands_available.clear()

            # We're not protecting this list with a mutex but we're
            # just using it as a simple queue so it should be fine.
            while self._commands:
                cmd = self._commands.popleft()
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
                babase.mac_music_app_stop()
                babase.mac_music_app_set_volume(self._orig_volume)
            except Exception as exc:
                print('Error stopping iTunes music:', exc)
        elif self._volume > 0:
            # If volume was zero, store pre-playing volume and start
            # playing.
            if old_volume == 0.0:
                self._orig_volume = babase.mac_music_app_get_volume()
            self._update_mac_music_app_volume()
            if old_volume == 0.0:
                self._play_current_playlist()

    def play_playlist(self, musictype: str | None) -> None:
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
        self, target: Callable[[list[str]], None]
    ) -> None:
        try:
            playlists = babase.mac_music_app_get_playlists()
            playlists = [
                p
                for p in playlists
                if p
                not in [
                    'Music',
                    'Movies',
                    'TV Shows',
                    'Podcasts',
                    'iTunes\xa0U',
                    'Books',
                    'Genius',
                    'iTunes DJ',
                    'Music Videos',
                    'Home Videos',
                    'Voice Memos',
                    'Audiobooks',
                ]
            ]
            playlists.sort(key=lambda x: x.lower())
        except Exception as exc:
            print('Error getting iTunes playlists:', exc)
            playlists = []
        babase.pushcall(babase.Call(target, playlists), from_other_thread=True)

    def _handle_play_command(self, target: str | None) -> None:
        if target is None:
            if self._current_playlist is not None and self._volume > 0:
                try:
                    assert self._orig_volume is not None
                    babase.mac_music_app_stop()
                    babase.mac_music_app_set_volume(self._orig_volume)
                except Exception as exc:
                    print('Error stopping iTunes music:', exc)
            self._current_playlist = None
        else:
            # If we've got something playing with positive
            # volume, stop it.
            if self._current_playlist is not None and self._volume > 0:
                try:
                    assert self._orig_volume is not None
                    babase.mac_music_app_stop()
                    babase.mac_music_app_set_volume(self._orig_volume)
                except Exception as exc:
                    print('Error stopping iTunes music:', exc)

            # Set our playlist and play it if our volume is up.
            self._current_playlist = target
            if self._volume > 0:
                self._orig_volume = babase.mac_music_app_get_volume()
                self._update_mac_music_app_volume()
                self._play_current_playlist()

    def _handle_die_command(self) -> None:
        # Only stop if we've actually played something
        # (we don't want to kill music the user has playing).
        if self._current_playlist is not None and self._volume > 0:
            try:
                assert self._orig_volume is not None
                babase.mac_music_app_stop()
                babase.mac_music_app_set_volume(self._orig_volume)
            except Exception as exc:
                print('Error stopping iTunes music:', exc)

    def _play_current_playlist(self) -> None:
        try:
            assert self._current_playlist is not None
            if babase.mac_music_app_play_playlist(self._current_playlist):
                pass
            else:
                babase.pushcall(
                    babase.Call(
                        babase.screenmessage,
                        babase.app.lang.get_resource('playlistNotFoundText')
                        + ': \''
                        + self._current_playlist
                        + '\'',
                        (1, 0, 0),
                    ),
                    from_other_thread=True,
                )
        except Exception:
            logging.exception(
                "Error playing playlist '%s'.", self._current_playlist
            )

    def _update_mac_music_app_volume(self) -> None:
        babase.mac_music_app_set_volume(
            max(0, min(100, int(100.0 * self._volume)))
        )
