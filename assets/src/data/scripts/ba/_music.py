"""Music related functionality."""
from __future__ import annotations

import copy
import os
import random
import threading
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Callable, Any, List, Optional, Dict


class MusicPlayer:
    """Wrangles soundtrack music playback.

    Music can be played either through the game itself
    or via a platform-specific external player.
    """

    def __init__(self) -> None:
        self._have_set_initial_volume = False
        self._entry_to_play = None
        self._volume = 1.0
        self._actually_playing = False

    def select_entry(self, callback: Callable[[Any], None], current_entry: Any,
                     selection_target_name: str) -> Any:
        """Summons a UI to select a new soundtrack entry."""
        return self.on_select_entry(callback, current_entry,
                                    selection_target_name)

    def set_volume(self, volume: float) -> None:
        """Set player volume (value should be between 0 and 1)."""
        self._volume = volume
        self.on_set_volume(volume)
        self._update_play_state()

    def play(self, entry: Any) -> None:
        """Play provided entry."""
        if not self._have_set_initial_volume:
            self._volume = _ba.app.config.resolve('Music Volume')
            self.on_set_volume(self._volume)
            self._have_set_initial_volume = True
        self._entry_to_play = copy.deepcopy(entry)

        # If we're currently *actually* playing something,
        # switch to the new thing.
        # Otherwise update state which will start us playing *only*
        # if proper (volume > 0, etc).
        if self._actually_playing:
            self.on_play(self._entry_to_play)
        else:
            self._update_play_state()

    def stop(self) -> None:
        """Stop any playback that is occurring."""
        self._entry_to_play = None
        self._update_play_state()

    def shutdown(self) -> None:
        """Shutdown music playback completely."""
        self.on_shutdown()

    def on_select_entry(self, callback: Callable[[Any], None],
                        current_entry: Any, selection_target_name: str) -> Any:
        """Present a GUI to select an entry.

        The callback should be called with a valid entry or None to
        signify that the default soundtrack should be used.."""

    # Subclasses should override the following:
    def on_set_volume(self, volume: float) -> None:
        """Called when the volume should be changed."""

    def on_play(self, entry: Any) -> None:
        """Called when a new song/playlist/etc should be played."""

    def on_stop(self) -> None:
        """Called when the music should stop."""

    def on_shutdown(self) -> None:
        """Called on final app shutdown."""

    def _update_play_state(self) -> None:

        # If we aren't playing, should be, and have positive volume, do so.
        if not self._actually_playing:
            if self._entry_to_play is not None and self._volume > 0.0:
                self.on_play(self._entry_to_play)
                self._actually_playing = True
        else:
            if self._actually_playing and (self._entry_to_play is None
                                           or self._volume <= 0.0):
                self.on_stop()
                self._actually_playing = False


class InternalMusicPlayer(MusicPlayer):
    """Music player that talks to internal c layer functionality.

    (internal)"""

    def __init__(self) -> None:
        super().__init__()
        self._want_to_play = False
        self._actually_playing = False

    def on_select_entry(self, callback: Callable[[Any], None],
                        current_entry: Any, selection_target_name: str) -> Any:
        # pylint: disable=cyclic-import
        from bastd.ui.soundtrack.entrytypeselect import (
            SoundtrackEntryTypeSelectWindow)
        return SoundtrackEntryTypeSelectWindow(callback, current_entry,
                                               selection_target_name)

    def on_set_volume(self, volume: float) -> None:
        _ba.music_player_set_volume(volume)

    class _PickFolderSongThread(threading.Thread):

        def __init__(self, path: str, callback: Callable):
            super().__init__()
            self._callback = callback
            self._path = path

        def run(self) -> None:
            from ba import _lang
            from ba._general import Call
            try:
                _ba.set_thread_name("BA_PickFolderSongThread")
                all_files: List[str] = []
                valid_extensions = [
                    '.' + x for x in get_valid_music_file_extensions()
                ]
                for root, _subdirs, filenames in os.walk(self._path):
                    for fname in filenames:
                        if any(fname.lower().endswith(ext)
                               for ext in valid_extensions):
                            all_files.insert(
                                random.randrange(len(all_files) + 1),
                                root + '/' + fname)
                if not all_files:
                    raise Exception(
                        _lang.Lstr(resource='internal.noMusicFilesInFolderText'
                                   ).evaluate())
                _ba.pushcall(Call(self._callback, result=all_files),
                             from_other_thread=True)
            except Exception as exc:
                from ba import _error
                _error.print_exception()
                try:
                    err_str = str(exc)
                except Exception:
                    err_str = '<ENCERR4523>'
                _ba.pushcall(Call(self._callback,
                                  result=self._path,
                                  error=err_str),
                             from_other_thread=True)

    def on_play(self, entry: Any) -> None:
        entry_type = get_soundtrack_entry_type(entry)
        name = get_soundtrack_entry_name(entry)
        assert name is not None
        if entry_type == 'musicFile':
            self._want_to_play = self._actually_playing = True
            _ba.music_player_play(name)
        elif entry_type == 'musicFolder':

            # Launch a thread to scan this folder and give us a random
            # valid file within.
            self._want_to_play = True
            self._actually_playing = False
            self._PickFolderSongThread(name, self._on_play_folder_cb).start()

    def _on_play_folder_cb(self, result: str,
                           error: Optional[str] = None) -> None:
        from ba import _lang
        if error is not None:
            rstr = (_lang.Lstr(
                resource='internal.errorPlayingMusicText').evaluate())
            err_str = (rstr.replace('${MUSIC}', os.path.basename(result)) +
                       '; ' + str(error))
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

    def on_shutdown(self) -> None:
        _ba.music_player_shutdown()


# For internal music player.
def get_valid_music_file_extensions() -> List[str]:
    """Return file extensions for types playable on this device."""
    return ['mp3', 'ogg', 'm4a', 'wav', 'flac', 'mid']


class ITunesThread(threading.Thread):
    """Thread which wrangles iTunes/Music.app playback"""

    def __init__(self) -> None:
        super().__init__()
        self._commands_available = threading.Event()
        self._commands: List[List] = []
        self._volume = 1.0
        self._current_playlist: Optional[str] = None
        self._orig_volume: Optional[int] = None

    def run(self) -> None:
        """Run the iTunes/Music.app thread."""
        from ba._general import Call
        from ba._lang import Lstr
        from ba._enums import TimeType
        _ba.set_thread_name("BA_ITunesThread")
        _ba.itunes_init()

        # It looks like launching iTunes here on 10.7/10.8 knocks us
        # out of fullscreen; ick. That might be a bug, but for now we
        # can work around it by reactivating ourself after.
        def do_print() -> None:
            _ba.timer(1.0,
                      Call(_ba.screenmessage, Lstr(resource='usingItunesText'),
                           (0, 1, 0)),
                      timetype=TimeType.REAL)

        _ba.pushcall(do_print, from_other_thread=True)

        # Here we grab this to force the actual launch.
        # Currently (on 10.8 at least) this is causing a switch
        # away from our fullscreen window. to work around this we
        # explicitly focus our main window to bring ourself back.
        _ba.itunes_get_volume()
        _ba.pushcall(_ba.focus_window, from_other_thread=True)
        _ba.itunes_get_library_source()
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
                _ba.itunes_stop()
                _ba.itunes_set_volume(self._orig_volume)
            except Exception as exc:
                print('Error stopping iTunes music:', exc)
        elif self._volume > 0:

            # If volume was zero, store pre-playing volume and start
            # playing.
            if old_volume == 0.0:
                self._orig_volume = _ba.itunes_get_volume()
            self._update_itunes_volume()
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

    def _handle_get_playlists_command(self, target: str) -> None:
        from ba._general import Call
        try:
            playlists = _ba.itunes_get_playlists()
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
                    _ba.itunes_stop()
                    _ba.itunes_set_volume(self._orig_volume)
                except Exception as exc:
                    print('Error stopping iTunes music:', exc)
            self._current_playlist = None
        else:
            # If we've got something playing with positive
            # volume, stop it.
            if self._current_playlist is not None and self._volume > 0:
                try:
                    assert self._orig_volume is not None
                    _ba.itunes_stop()
                    _ba.itunes_set_volume(self._orig_volume)
                except Exception as exc:
                    print('Error stopping iTunes music:', exc)

            # Set our playlist and play it if our volume is up.
            self._current_playlist = target
            if self._volume > 0:
                self._orig_volume = (_ba.itunes_get_volume())
                self._update_itunes_volume()
                self._play_current_playlist()

    def _handle_die_command(self) -> None:

        # Only stop if we've actually played something
        # (we don't want to kill music the user has playing).
        if self._current_playlist is not None and self._volume > 0:
            try:
                assert self._orig_volume is not None
                _ba.itunes_stop()
                _ba.itunes_set_volume(self._orig_volume)
            except Exception as exc:
                print('Error stopping iTunes music:', exc)

    def _play_current_playlist(self) -> None:
        try:
            from ba import _lang
            from ba._general import Call
            assert self._current_playlist is not None
            if _ba.itunes_play_playlist(self._current_playlist):
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
                f"error playing playlist {self._current_playlist}")

    def _update_itunes_volume(self) -> None:
        _ba.itunes_set_volume(max(0, min(100, int(100.0 * self._volume))))


class MacITunesMusicPlayer(MusicPlayer):
    """A music-player that utilizes iTunes/Music.app for playback.

    Allows selecting playlists as entries.
    """

    def __init__(self) -> None:
        super().__init__()
        self._thread = ITunesThread()
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
        entry_type = get_soundtrack_entry_type(entry)
        if entry_type == 'iTunesPlaylist':
            self._thread.play_playlist(get_soundtrack_entry_name(entry))
        else:
            print('MacITunesMusicPlayer passed unrecognized entry type:',
                  entry_type)

    def on_stop(self) -> None:
        self._thread.play_playlist(None)

    def on_shutdown(self) -> None:
        self._thread.shutdown()


def have_music_player() -> bool:
    """Returns whether a music player is present."""
    return _ba.app.music_player_type is not None


def get_music_player() -> MusicPlayer:
    """Returns the system music player, instantiating if necessary."""
    app = _ba.app
    if app.music_player is None:
        if app.music_player_type is None:
            raise Exception("no music player type set")
        app.music_player = app.music_player_type()
    return app.music_player


def music_volume_changed(val: float) -> None:
    """Should be called when changing the music volume."""
    app = _ba.app
    if app.music_player is not None:
        app.music_player.set_volume(val)


def set_music_play_mode(mode: str, force_restart: bool = False) -> None:
    """Sets music play mode; used for soundtrack testing/etc."""
    app = _ba.app
    old_mode = app.music_mode
    app.music_mode = mode
    if old_mode != app.music_mode or force_restart:

        # If we're switching into test mode we don't
        # actually play anything until its requested.
        # If we're switching *out* of test mode though
        # we want to go back to whatever the normal song was.
        if mode == 'regular':
            do_play_music(app.music_types['regular'])


def supports_soundtrack_entry_type(entry_type: str) -> bool:
    """Return whether the provided soundtrack entry type is supported here."""
    uas = _ba.app.user_agent_string
    if entry_type == 'iTunesPlaylist':
        return 'Mac' in uas
    if entry_type in ('musicFile', 'musicFolder'):
        return ('android' in uas
                and _ba.android_get_external_storage_path() is not None)
    if entry_type == 'default':
        return True
    return False


def get_soundtrack_entry_type(entry: Any) -> str:
    """Given a soundtrack entry, returns its type, taking into
    account what is supported locally."""
    try:
        if entry is None:
            entry_type = 'default'

        # Simple string denotes iTunesPlaylist (legacy format).
        elif isinstance(entry, str):
            entry_type = 'iTunesPlaylist'

        # For other entries we expect type and name strings in a dict.
        elif (isinstance(entry, dict) and 'type' in entry
              and isinstance(entry['type'], str) and 'name' in entry
              and isinstance(entry['name'], str)):
            entry_type = entry['type']
        else:
            raise Exception("invalid soundtrack entry: " + str(entry) +
                            " (type " + str(type(entry)) + ")")
        if supports_soundtrack_entry_type(entry_type):
            return entry_type
        raise Exception("invalid soundtrack entry:" + str(entry))
    except Exception as exc:
        print('EXC on get_soundtrack_entry_type', exc)
        return 'default'


def get_soundtrack_entry_name(entry: Any) -> str:
    """Given a soundtrack entry, returns its name."""
    try:
        if entry is None:
            raise Exception('entry is None')

        # Simple string denotes an iTunesPlaylist name (legacy entry).
        if isinstance(entry, str):
            return entry

        # For other entries we expect type and name strings in a dict.
        if (isinstance(entry, dict) and 'type' in entry
                and isinstance(entry['type'], str) and 'name' in entry
                and isinstance(entry['name'], str)):
            return entry['name']
        raise Exception("invalid soundtrack entry:" + str(entry))
    except Exception:
        from ba import _error
        _error.print_exception()
        return 'default'


def setmusic(musictype: Optional[str], continuous: bool = False) -> None:
    """Set or stop the current music based on a string musictype.

    category: Gameplay Functions

    Current valid values for 'musictype': 'Menu', 'Victory', 'CharSelect',
    'RunAway', 'Onslaught', 'Keep Away', 'Race', 'Epic Race', 'Scores',
    'GrandRomp', 'ToTheDeath', 'Chosen One', 'ForwardMarch', 'FlagCatcher',
    'Survival', 'Epic', 'Sports', 'Hockey', 'Football', 'Flying', 'Scary',
    'Marching'.

    This function will handle loading and playing sound media as necessary,
    and also supports custom user soundtracks on specific platforms so the
    user can override particular game music with their own.

    Pass None to stop music.

    if 'continuous' is True the musictype passed is the same as what is already
    playing, the playing track will not be restarted.
    """
    from ba import _gameutils

    # All we do here now is set a few music attrs on the current globals
    # node. The foreground globals' current playing music then gets fed to
    # the do_play_music call below. This way we can seamlessly support custom
    # soundtracks in replays/etc since we're replaying an attr value set;
    # not an actual sound node create.
    gnode = _gameutils.sharedobj('globals')
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype
    gnode.music_count += 1


def handle_app_resume() -> None:
    """Should be run when the app resumes from a suspended state."""
    if _ba.is_os_playing_music():
        do_play_music(None)


def do_play_music(musictype: Optional[str],
                  continuous: bool = False,
                  mode: str = 'regular',
                  testsoundtrack: Dict = None) -> None:
    """Plays the requested music type/mode.

    For most cases setmusic() is the proper call to use, which itself calls
    this. Certain cases, however, such as soundtrack testing, may require
    calling this directly.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    app = _ba.app
    with _ba.Context('ui'):

        # If they don't want to restart music and we're already
        # playing what's requested, we're done.
        if continuous and app.music_types[mode] == musictype:
            return
        app.music_types[mode] = musictype
        cfg = app.config

        # If the OS tells us there's currently music playing,
        # all our operations default to playing nothing.
        if _ba.is_os_playing_music():
            musictype = None

        # If we're not in the mode this music is being set for,
        # don't actually change what's playing.
        if mode != app.music_mode:
            return

        # Some platforms have a special music-player for things like iTunes
        # soundtracks, mp3s, etc. if this is the case, attempt to grab an
        # entry for this music-type, and if we have one, have the music-player
        # play it.  If not, we'll play game music ourself.
        if musictype is not None and app.music_player_type is not None:
            try:
                soundtrack: Dict
                if testsoundtrack is not None:
                    soundtrack = testsoundtrack
                else:
                    soundtrack = cfg['Soundtracks'][cfg['Soundtrack']]
                entry = soundtrack[musictype]
            except Exception:
                entry = None
        else:
            entry = None

        # Go through music-player.
        if entry is not None:

            # Stop any existing internal music.
            if app.music is not None:
                app.music.delete()
                app.music = None

            # Play music-player music.
            get_music_player().play(entry)

        # Handle via internal music.
        else:
            if musictype is not None:
                loop = True
                if musictype == 'Menu':
                    filename = 'menuMusic'
                    volume = 5.0
                elif musictype == 'Victory':
                    filename = 'victoryMusic'
                    volume = 6.0
                    loop = False
                elif musictype == 'CharSelect':
                    filename = 'charSelectMusic'
                    volume = 2.0
                elif musictype == 'RunAway':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musictype == 'Onslaught':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musictype == 'Keep Away':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musictype == 'Race':
                    filename = 'runAwayMusic'
                    volume = 6.0
                elif musictype == 'Epic Race':
                    filename = 'slowEpicMusic'
                    volume = 6.0
                elif musictype == 'Scores':
                    filename = 'scoresEpicMusic'
                    volume = 3.0
                    loop = False
                elif musictype == 'GrandRomp':
                    filename = 'grandRompMusic'
                    volume = 6.0
                elif musictype == 'ToTheDeath':
                    filename = 'toTheDeathMusic'
                    volume = 6.0
                elif musictype == 'Chosen One':
                    filename = 'survivalMusic'
                    volume = 4.0
                elif musictype == 'ForwardMarch':
                    filename = 'forwardMarchMusic'
                    volume = 4.0
                elif musictype == 'FlagCatcher':
                    filename = 'flagCatcherMusic'
                    volume = 6.0
                elif musictype == 'Survival':
                    filename = 'survivalMusic'
                    volume = 4.0
                elif musictype == 'Epic':
                    filename = 'slowEpicMusic'
                    volume = 6.0
                elif musictype == 'Sports':
                    filename = 'sportsMusic'
                    volume = 4.0
                elif musictype == 'Hockey':
                    filename = 'sportsMusic'
                    volume = 4.0
                elif musictype == 'Football':
                    filename = 'sportsMusic'
                    volume = 4.0
                elif musictype == 'Flying':
                    filename = 'flyingMusic'
                    volume = 4.0
                elif musictype == 'Scary':
                    filename = 'scaryMusic'
                    volume = 4.0
                elif musictype == 'Marching':
                    filename = 'whenJohnnyComesMarchingHomeMusic'
                    volume = 4.0
                else:
                    print("Unknown music: '" + musictype + "'")
                    filename = 'flagCatcherMusic'
                    volume = 6.0

            # Stop any existing music-player playback.
            if app.music_player is not None:
                app.music_player.stop()

            # Stop any existing internal music.
            if app.music:
                app.music.delete()
                app.music = None

            # Start up new internal music.
            if musictype is not None:

                # FIXME: Currently this won't start playing if we're paused
                #  since attr values don't get updated until
                #  node updates happen.  :-(
                #  Update: hmm I don't think that's true anymore. Should check.
                app.music = _ba.newnode(type='sound',
                                        attrs={
                                            'sound': _ba.getsound(filename),
                                            'positional': False,
                                            'music': True,
                                            'volume': volume,
                                            'loop': loop
                                        })
