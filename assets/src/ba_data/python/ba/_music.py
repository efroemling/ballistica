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
"""Music related functionality."""
from __future__ import annotations

import copy
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

import _ba

if TYPE_CHECKING:
    from typing import Callable, Any, Optional, Dict, Union, Type


class MusicType(Enum):
    """Types of music available to play in-game.

    Category: Enums

    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
    """
    MENU = 'Menu'
    VICTORY = 'Victory'
    CHAR_SELECT = 'CharSelect'
    RUN_AWAY = 'RunAway'
    ONSLAUGHT = 'Onslaught'
    KEEP_AWAY = 'Keep Away'
    RACE = 'Race'
    EPIC_RACE = 'Epic Race'
    SCORES = 'Scores'
    GRAND_ROMP = 'GrandRomp'
    TO_THE_DEATH = 'ToTheDeath'
    CHOSEN_ONE = 'Chosen One'
    FORWARD_MARCH = 'ForwardMarch'
    FLAG_CATCHER = 'FlagCatcher'
    SURVIVAL = 'Survival'
    EPIC = 'Epic'
    SPORTS = 'Sports'
    HOCKEY = 'Hockey'
    FOOTBALL = 'Football'
    FLYING = 'Flying'
    SCARY = 'Scary'
    MARCHING = 'Marching'


class MusicPlayMode(Enum):
    """Influences behavior when playing music.

    Category: Enums
    """
    REGULAR = 'regular'
    TEST = 'test'


@dataclass
class AssetSoundtrackEntry:
    """A music entry using an internal asset.

    Category: App Classes
    """
    assetname: str
    volume: float = 1.0
    loop: bool = True


# What gets played by default for our different music types:
ASSET_SOUNDTRACK_ENTRIES: Dict[MusicType, AssetSoundtrackEntry] = {
    MusicType.MENU:
        AssetSoundtrackEntry('menuMusic'),
    MusicType.VICTORY:
        AssetSoundtrackEntry('victoryMusic', volume=1.2, loop=False),
    MusicType.CHAR_SELECT:
        AssetSoundtrackEntry('charSelectMusic', volume=0.4),
    MusicType.RUN_AWAY:
        AssetSoundtrackEntry('runAwayMusic', volume=1.2),
    MusicType.ONSLAUGHT:
        AssetSoundtrackEntry('runAwayMusic', volume=1.2),
    MusicType.KEEP_AWAY:
        AssetSoundtrackEntry('runAwayMusic', volume=1.2),
    MusicType.RACE:
        AssetSoundtrackEntry('runAwayMusic', volume=1.2),
    MusicType.EPIC_RACE:
        AssetSoundtrackEntry('slowEpicMusic', volume=1.2),
    MusicType.SCORES:
        AssetSoundtrackEntry('scoresEpicMusic', volume=0.6, loop=False),
    MusicType.GRAND_ROMP:
        AssetSoundtrackEntry('grandRompMusic', volume=1.2),
    MusicType.TO_THE_DEATH:
        AssetSoundtrackEntry('toTheDeathMusic', volume=1.2),
    MusicType.CHOSEN_ONE:
        AssetSoundtrackEntry('survivalMusic', volume=0.8),
    MusicType.FORWARD_MARCH:
        AssetSoundtrackEntry('forwardMarchMusic', volume=0.8),
    MusicType.FLAG_CATCHER:
        AssetSoundtrackEntry('flagCatcherMusic', volume=1.2),
    MusicType.SURVIVAL:
        AssetSoundtrackEntry('survivalMusic', volume=0.8),
    MusicType.EPIC:
        AssetSoundtrackEntry('slowEpicMusic', volume=1.2),
    MusicType.SPORTS:
        AssetSoundtrackEntry('sportsMusic', volume=0.8),
    MusicType.HOCKEY:
        AssetSoundtrackEntry('sportsMusic', volume=0.8),
    MusicType.FOOTBALL:
        AssetSoundtrackEntry('sportsMusic', volume=0.8),
    MusicType.FLYING:
        AssetSoundtrackEntry('flyingMusic', volume=0.8),
    MusicType.SCARY:
        AssetSoundtrackEntry('scaryMusic', volume=0.8),
    MusicType.MARCHING:
        AssetSoundtrackEntry('whenJohnnyComesMarchingHomeMusic', volume=0.8),
}


class MusicController:
    """Controller for overall music playback in the app.

    Category: App Classes
    """

    def __init__(self) -> None:
        # pylint: disable=cyclic-import
        self._music_node: Optional[_ba.Node] = None
        self._music_mode: MusicPlayMode = MusicPlayMode.REGULAR
        self._music_player: Optional[MusicPlayer] = None
        self._music_player_type: Optional[Type[MusicPlayer]] = None
        self.music_types: Dict[MusicPlayMode, Optional[MusicType]] = {
            MusicPlayMode.REGULAR: None,
            MusicPlayMode.TEST: None
        }

        # Set up custom music players for platforms that support them.
        # FIXME: should generalize this to support arbitrary players per
        # platform (which can be discovered via ba_meta).
        # Our standard asset playback should probably just be one of them
        # instead of a special case.
        if self.supports_soundtrack_entry_type('musicFile'):
            from ba.osmusic import OSMusicPlayer
            self._music_player_type = OSMusicPlayer
        elif self.supports_soundtrack_entry_type('iTunesPlaylist'):
            from ba.macmusicapp import MacMusicAppMusicPlayer
            self._music_player_type = MacMusicAppMusicPlayer

    def on_app_launch(self) -> None:
        """Should be called by app on_app_launch()."""

        # If we're using a non-default playlist, lets go ahead and get our
        # music-player going since it may hitch (better while we're faded
        # out than later).
        try:
            cfg = _ba.app.config
            if ('Soundtrack' in cfg and cfg['Soundtrack']
                    not in ['__default__', 'Default Soundtrack']):
                self.get_music_player()
        except Exception:
            from ba import _error
            _error.print_exception('error prepping music-player')

    def on_app_shutdown(self) -> None:
        """Should be called when the app is shutting down."""
        if self._music_player is not None:
            self._music_player.shutdown()

    def have_music_player(self) -> bool:
        """Returns whether a music player is present."""
        return self._music_player_type is not None

    def get_music_player(self) -> MusicPlayer:
        """Returns the system music player, instantiating if necessary."""
        if self._music_player is None:
            if self._music_player_type is None:
                raise TypeError('no music player type set')
            self._music_player = self._music_player_type()
        return self._music_player

    def music_volume_changed(self, val: float) -> None:
        """Should be called when changing the music volume."""
        if self._music_player is not None:
            self._music_player.set_volume(val)

    def set_music_play_mode(self,
                            mode: MusicPlayMode,
                            force_restart: bool = False) -> None:
        """Sets music play mode; used for soundtrack testing/etc."""
        old_mode = self._music_mode
        self._music_mode = mode
        if old_mode != self._music_mode or force_restart:

            # If we're switching into test mode we don't
            # actually play anything until its requested.
            # If we're switching *out* of test mode though
            # we want to go back to whatever the normal song was.
            if mode is MusicPlayMode.REGULAR:
                mtype = self.music_types[MusicPlayMode.REGULAR]
                self.do_play_music(None if mtype is None else mtype.value)

    def supports_soundtrack_entry_type(self, entry_type: str) -> bool:
        """Return whether provided soundtrack entry type is supported here."""
        uas = _ba.env()['user_agent_string']
        assert isinstance(uas, str)

        # FIXME: Generalize this.
        if entry_type == 'iTunesPlaylist':
            return 'Mac' in uas
        if entry_type in ('musicFile', 'musicFolder'):
            return ('android' in uas
                    and _ba.android_get_external_storage_path() is not None)
        if entry_type == 'default':
            return True
        return False

    def get_soundtrack_entry_type(self, entry: Any) -> str:
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
                raise TypeError('invalid soundtrack entry: ' + str(entry) +
                                ' (type ' + str(type(entry)) + ')')
            if self.supports_soundtrack_entry_type(entry_type):
                return entry_type
            raise ValueError('invalid soundtrack entry:' + str(entry))
        except Exception:
            from ba import _error
            _error.print_exception()
            return 'default'

    def get_soundtrack_entry_name(self, entry: Any) -> str:
        """Given a soundtrack entry, returns its name."""
        try:
            if entry is None:
                raise TypeError('entry is None')

            # Simple string denotes an iTunesPlaylist name (legacy entry).
            if isinstance(entry, str):
                return entry

            # For other entries we expect type and name strings in a dict.
            if (isinstance(entry, dict) and 'type' in entry
                    and isinstance(entry['type'], str) and 'name' in entry
                    and isinstance(entry['name'], str)):
                return entry['name']
            raise ValueError('invalid soundtrack entry:' + str(entry))
        except Exception:
            from ba import _error
            _error.print_exception()
            return 'default'

    def on_app_resume(self) -> None:
        """Should be run when the app resumes from a suspended state."""
        if _ba.is_os_playing_music():
            self.do_play_music(None)

    def do_play_music(self,
                      musictype: Union[MusicType, str, None],
                      continuous: bool = False,
                      mode: MusicPlayMode = MusicPlayMode.REGULAR,
                      testsoundtrack: Dict[str, Any] = None) -> None:
        """Plays the requested music type/mode.

        For most cases, setmusic() is the proper call to use, which itself
        calls this. Certain cases, however, such as soundtrack testing, may
        require calling this directly.
        """

        # We can be passed a MusicType or the string value corresponding
        # to one.
        if musictype is not None:
            try:
                musictype = MusicType(musictype)
            except ValueError:
                print(f"Invalid music type: '{musictype}'")
                musictype = None

        with _ba.Context('ui'):

            # If they don't want to restart music and we're already
            # playing what's requested, we're done.
            if continuous and self.music_types[mode] is musictype:
                return
            self.music_types[mode] = musictype

            # If the OS tells us there's currently music playing,
            # all our operations default to playing nothing.
            if _ba.is_os_playing_music():
                musictype = None

            # If we're not in the mode this music is being set for,
            # don't actually change what's playing.
            if mode != self._music_mode:
                return

            # Some platforms have a special music-player for things like iTunes
            # soundtracks, mp3s, etc. if this is the case, attempt to grab an
            # entry for this music-type, and if we have one, have the
            # music-player play it.  If not, we'll play game music ourself.
            if musictype is not None and self._music_player_type is not None:
                if testsoundtrack is not None:
                    soundtrack = testsoundtrack
                else:
                    soundtrack = self._get_user_soundtrack()
                entry = soundtrack.get(musictype.value)
            else:
                entry = None

            # Go through music-player.
            if entry is not None:
                self._play_music_player_music(entry)

            # Handle via internal music.
            else:
                self._play_internal_music(musictype)

    def _get_user_soundtrack(self) -> Dict[str, Any]:
        """Return current user soundtrack or empty dict otherwise."""
        cfg = _ba.app.config
        soundtrack: Dict[str, Any] = {}
        soundtrackname = cfg.get('Soundtrack')
        if soundtrackname is not None and soundtrackname != '__default__':
            try:
                soundtrack = cfg.get('Soundtracks', {})[soundtrackname]
            except Exception as exc:
                print(f'Error looking up user soundtrack: {exc}')
                soundtrack = {}
        return soundtrack

    def _play_music_player_music(self, entry: Any) -> None:

        # Stop any existing internal music.
        if self._music_node is not None:
            self._music_node.delete()
            self._music_node = None

        # Do the thing.
        self.get_music_player().play(entry)

    def _play_internal_music(self, musictype: Optional[MusicType]) -> None:

        # Stop any existing music-player playback.
        if self._music_player is not None:
            self._music_player.stop()

        # Stop any existing internal music.
        if self._music_node:
            self._music_node.delete()
            self._music_node = None

        # Start up new internal music.
        if musictype is not None:

            entry = ASSET_SOUNDTRACK_ENTRIES.get(musictype)
            if entry is None:
                print(f"Unknown music: '{musictype}'")
                entry = ASSET_SOUNDTRACK_ENTRIES[MusicType.FLAG_CATCHER]

            self._music_node = _ba.newnode(
                type='sound',
                attrs={
                    'sound': _ba.getsound(entry.assetname),
                    'positional': False,
                    'music': True,
                    'volume': entry.volume * 5.0,
                    'loop': entry.loop
                })


class MusicPlayer:
    """Wrangles soundtrack music playback.

    Category: App Classes

    Music can be played either through the game itself
    or via a platform-specific external player.
    """

    def __init__(self) -> None:
        self._have_set_initial_volume = False
        self._entry_to_play: Optional[Any] = None
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
        self.on_app_shutdown()

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

    def on_app_shutdown(self) -> None:
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


def setmusic(musictype: Optional[MusicType], continuous: bool = False) -> None:
    """Tell the game to play (or stop playing) a certain type of music.

    category: Gameplay Functions

    This function will handle loading and playing sound assets as necessary,
    and also supports custom user soundtracks on specific platforms so the
    user can override particular game music with their own.

    Pass None to stop music.

    if 'continuous' is True and musictype is the same as what is already
    playing, the playing track will not be restarted.
    """
    from ba import _gameutils

    # All we do here now is set a few music attrs on the current globals
    # node. The foreground globals' current playing music then gets fed to
    # the do_play_music call in our music controller. This way we can
    # seamlessly support custom soundtracks in replays/etc since we're being
    # driven purely by node data.
    gnode = _ba.getactivity().globalsnode
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype.value
    gnode.music_count += 1


def do_play_music(*args: Any, **keywds: Any) -> None:
    """A passthrough used by the C++ layer."""
    _ba.app.music.do_play_music(*args, **keywds)
