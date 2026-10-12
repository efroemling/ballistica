# Released under the MIT License. See LICENSE for details.
#
"""Music related functionality."""

import copy
import time
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

import babase
import bascenev1
from bascenev1 import MusicType, _classicassets

if TYPE_CHECKING:
    from typing import Callable, Any

    import bauiv1


#: After another app's music stops, how long to wait before resuming
#: game music. Long enough to ride out the brief 'stopped' gaps between
#: a music app's tracks and between the phases of a Siri interaction
#: (either would otherwise restart our music for a moment); short enough
#: that genuinely stopping your music brings ours back promptly. Only
#: that one transition waits -- yielding, and music with nothing else
#: playing, are immediate.
_OS_MUSIC_RESUME_DELAY_SECONDS = 3.0


class MusicPlayMode(Enum):
    """Influences behavior when playing music."""

    REGULAR = 'regular'
    TEST = 'test'


@dataclass
class AssetSoundtrackEntry:
    """A music entry using an internal asset."""

    assetname: str
    volume: float = 1.0
    loop: bool = True


def _audioref(name: str) -> str:
    """Qualified asset-package ref for a _classicassets audio asset."""
    # LEGACY: builds a qualified path by hand, which nothing should
    # do -- the parts are private now precisely to flag it. Kept
    # only until this file's callers hold handles instead; see
    # docs/followups.md "hand-built asset paths".
    # pylint: disable-next=protected-access
    return f'{_classicassets._ASSET_PACKAGE}:audio/{name}'


# What gets played by default for our different music types:
ASSET_SOUNDTRACK_ENTRIES: dict[MusicType, AssetSoundtrackEntry] = {
    MusicType.MENU: AssetSoundtrackEntry(_audioref('menu_music')),
    MusicType.VICTORY: AssetSoundtrackEntry(
        _audioref('victory_music'), volume=1.2, loop=False
    ),
    MusicType.CHAR_SELECT: AssetSoundtrackEntry(
        _audioref('char_select_music'), volume=0.4
    ),
    MusicType.RUN_AWAY: AssetSoundtrackEntry(
        _audioref('run_away_music'), volume=1.2
    ),
    MusicType.ONSLAUGHT: AssetSoundtrackEntry(
        _audioref('run_away_music'), volume=1.2
    ),
    MusicType.KEEP_AWAY: AssetSoundtrackEntry(
        _audioref('run_away_music'), volume=1.2
    ),
    MusicType.RACE: AssetSoundtrackEntry(
        _audioref('run_away_music'), volume=1.2
    ),
    MusicType.EPIC_RACE: AssetSoundtrackEntry(
        _audioref('slow_epic_music'), volume=1.2
    ),
    MusicType.SCORES: AssetSoundtrackEntry(
        _audioref('scores_epic_music'), volume=0.6, loop=False
    ),
    MusicType.GRAND_ROMP: AssetSoundtrackEntry(
        _audioref('grand_romp_music'), volume=1.2
    ),
    MusicType.TO_THE_DEATH: AssetSoundtrackEntry(
        _audioref('to_the_death_music'), volume=1.2
    ),
    MusicType.CHOSEN_ONE: AssetSoundtrackEntry(
        _audioref('survival_music'), volume=0.8
    ),
    MusicType.FORWARD_MARCH: AssetSoundtrackEntry(
        _audioref('forward_march_music'), volume=0.8
    ),
    MusicType.FLAG_CATCHER: AssetSoundtrackEntry(
        _audioref('flag_catcher_music'), volume=1.2
    ),
    MusicType.SURVIVAL: AssetSoundtrackEntry(
        _audioref('survival_music'), volume=0.8
    ),
    MusicType.EPIC: AssetSoundtrackEntry(
        _audioref('slow_epic_music'), volume=1.2
    ),
    MusicType.SPORTS: AssetSoundtrackEntry(
        _audioref('sports_music'), volume=0.8
    ),
    MusicType.HOCKEY: AssetSoundtrackEntry(
        _audioref('sports_music'), volume=0.8
    ),
    MusicType.FOOTBALL: AssetSoundtrackEntry(
        _audioref('sports_music'), volume=0.8
    ),
    MusicType.FLYING: AssetSoundtrackEntry(
        _audioref('flying_music'), volume=0.8
    ),
    MusicType.SCARY: AssetSoundtrackEntry(_audioref('scary_music'), volume=0.8),
    MusicType.MARCHING: AssetSoundtrackEntry(
        _audioref('when_johnny_comes_marching_home_music'), volume=0.8
    ),
}


class MusicSubsystem:
    """Subsystem for music playback in the app.

    Access the single shared instance of this class at 'ba.app.music'.
    """

    def __init__(self) -> None:
        # pylint: disable=cyclic-import
        # self._music_node: _bascenev1.Node | None = None
        self._playing_internal_music = False
        self._music_mode: MusicPlayMode = MusicPlayMode.REGULAR
        self._music_player: MusicPlayer | None = None
        self._music_player_type: type[MusicPlayer] | None = None
        self.music_types: dict[MusicPlayMode, MusicType | None] = {
            MusicPlayMode.REGULAR: None,
            MusicPlayMode.TEST: None,
        }

        # Yield-to-external-music state (see
        # docs/initiatives/soundtrack-modernization.md). Whether the
        # playback we last actually applied was yielding to another
        # app's music; lets us re-apply only on a real change.
        self._os_music_applied = False
        # The test soundtrack of the last TEST-mode request, so a yield
        # and resume mid-test replays it rather than the user's own.
        self._test_soundtrack: dict[str, Any] | None = None
        # Recent change times, for spotting a flapping platform signal.
        self._os_music_change_times: list[float] = []
        self._warned_os_music_flapping = False
        self._warned_first_os_music_yield = False
        # Set while another app's music has stopped but we're holding off
        # resuming ours (see _OS_MUSIC_RESUME_DELAY_SECONDS).
        self._os_music_resume_timer: babase.AppTimer | None = None

        # Set up custom music players for platforms that support them.
        # FIXME: should generalize this to support arbitrary players per
        # platform (which can be discovered via ba_meta).
        # Our standard asset playback should probably just be one of them
        # instead of a special case.
        if self.supports_soundtrack_entry_type('musicFile'):
            from baclassic.osmusic import OSMusicPlayer

            self._music_player_type = OSMusicPlayer
        elif self.supports_soundtrack_entry_type('iTunesPlaylist'):
            from baclassic.macmusicapp import MacMusicAppMusicPlayer

            self._music_player_type = MacMusicAppMusicPlayer

    def on_app_loading(self) -> None:
        """Should be called by app on_app_loading()."""

        # If we're using a non-default playlist, lets go ahead and get our
        # music-player going since it may hitch (better while we're faded
        # out than later).
        try:
            cfg = babase.app.config
            if 'Soundtrack' in cfg and cfg['Soundtrack'] not in [
                '__default__',
                'Default Soundtrack',
            ]:
                self.get_music_player()
        except Exception:
            logging.exception('Error prepping music-player.')

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

    def set_music_play_mode(
        self, mode: MusicPlayMode, force_restart: bool = False
    ) -> None:
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
        # Note to self; can't access babase.app.classic here because
        # we are called during its construction.
        env = babase.env()
        platform = env.get('platform')
        assert isinstance(platform, str)
        if entry_type == 'iTunesPlaylist':
            return platform == 'mac' and babase.is_xcode_build()
        if entry_type in ('musicFile', 'musicFolder'):
            return (
                platform == 'android'
                and babase.android_get_external_files_dir() is not None
            )
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
            elif (
                isinstance(entry, dict)
                and 'type' in entry
                and isinstance(entry['type'], str)
                and 'name' in entry
                and isinstance(entry['name'], str)
            ):
                entry_type = entry['type']
            else:
                raise TypeError(
                    'invalid soundtrack entry: '
                    + str(entry)
                    + ' (type '
                    + str(type(entry))
                    + ')'
                )
            if self.supports_soundtrack_entry_type(entry_type):
                return entry_type
            raise ValueError('invalid soundtrack entry:' + str(entry))
        except Exception:
            logging.exception('Error in get_soundtrack_entry_type.')
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
            if (
                isinstance(entry, dict)
                and 'type' in entry
                and isinstance(entry['type'], str)
                and 'name' in entry
                and isinstance(entry['name'], str)
            ):
                return entry['name']
            raise ValueError('invalid soundtrack entry:' + str(entry))
        except Exception:
            logging.exception('Error in get_soundtrack_entry_name.')
            return 'default'

    def on_app_unsuspend(self) -> None:
        """Should be run when the app resumes from a suspended state."""
        # Platforms re-report on foreground, but re-check here as a
        # safety net in case a change arrived while we were suspended.
        self._sync_os_music_state()

    def on_os_music_playing_changed(self, playing: bool) -> None:
        """Called when another app starts or stops playing music.

        Game music (internal or a user soundtrack) fades out while
        another app plays music and resumes when it stops. Sound
        effects are unaffected.

        :meta private:
        """
        now = time.monotonic()
        self._os_music_change_times = [
            t for t in self._os_music_change_times if now - t < 60.0
        ] + [now]
        if (
            len(self._os_music_change_times) > 10
            and not self._warned_os_music_flapping
        ):
            # A person toggling their music can't plausibly do this;
            # suggests a platform signal misreporting (e.g. counting
            # some short system sound as music). Warn once per run.
            self._warned_os_music_flapping = True
            logging.warning(
                'OS music-playing signal changed %d times in 60s'
                ' (platform %s); game music will keep starting/stopping.',
                len(self._os_music_change_times),
                babase.app.env.platform.value,
            )
        babase.audiolog.info(
            'OS music playing changed: %s (applied: %s).',
            playing,
            self._os_music_applied,
        )
        if babase.is_os_playing_music():
            # Other music is (back) on; any pending resume is moot.
            self._os_music_resume_timer = None
        elif self._os_music_applied and self._os_music_resume_timer is None:
            # Other music just stopped while we were yielding to it. Hold
            # off before resuming: gaps between tracks, and between the
            # phases of a Siri interaction, briefly read as 'stopped',
            # and resuming into them restarts our music for a moment.
            babase.audiolog.debug(
                'Other music stopped; resuming game music in %.1fs'
                ' unless it starts again.',
                _OS_MUSIC_RESUME_DELAY_SECONDS,
            )
            self._os_music_resume_timer = babase.AppTimer(
                _OS_MUSIC_RESUME_DELAY_SECONDS,
                babase.WeakCallStrict(self._on_os_music_resume_timer),
            )
        self._sync_os_music_state()

    def _on_os_music_resume_timer(self) -> None:
        self._os_music_resume_timer = None
        babase.audiolog.debug('Resume delay elapsed; re-syncing game music.')
        self._sync_os_music_state()

    def _os_music_yielding(self) -> bool:
        """Should game music currently yield to another app's?

        True while another app plays music, and also during the resume
        delay after it stops -- so a music change requested in that window
        (a round starting, say) waits too instead of slipping through.
        """
        return (
            babase.is_os_playing_music()
            or self._os_music_resume_timer is not None
        )

    def _sync_os_music_state(self) -> None:
        """Re-apply current music if yield state no longer matches."""
        if self._os_music_yielding() == self._os_music_applied:
            return
        mode = self._music_mode
        self.do_play_music(
            self.music_types[mode],
            mode=mode,
            testsoundtrack=(
                self._test_soundtrack if mode is MusicPlayMode.TEST else None
            ),
        )

    def do_play_music(
        self,
        musictype: MusicType | str | None,
        continuous: bool = False,
        mode: MusicPlayMode = MusicPlayMode.REGULAR,
        testsoundtrack: dict[str, Any] | None = None,
    ) -> None:
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

        with babase.ContextRef.empty():
            # If they don't want to restart music and we're already
            # playing what's requested, we're done.
            if continuous and self.music_types[mode] is musictype:
                babase.audiolog.debug(
                    'do_play_music: %s already current for %s'
                    ' (continuous); leaving as-is.',
                    musictype,
                    mode,
                )
                return
            self.music_types[mode] = musictype
            if mode is MusicPlayMode.TEST:
                self._test_soundtrack = testsoundtrack

            # If another app is playing music, all our operations
            # default to playing nothing (we still recorded the
            # requested type above, so it resumes when that stops).
            os_music_playing = self._os_music_yielding()
            if os_music_playing:
                if not self._warned_first_os_music_yield:
                    # Once per run, loud enough to reach us from the
                    # field: a platform signal that mistakes our own
                    # audio for another app's shows up as the same
                    # devices doing this seconds into every launch.
                    self._warned_first_os_music_yield = True
                    babase.audiolog.warning(
                        'Game music is yielding to another app\'s music'
                        ' for the first time this run (%.1fs after launch,'
                        ' platform %s). If no other app is playing music,'
                        ' this is a bug.',
                        babase.apptime(),
                        babase.app.env.platform.value,
                    )
                babase.audiolog.debug(
                    'do_play_music: OS reports music playing;'
                    ' playing nothing instead of %s.',
                    musictype,
                )
                musictype = None

            # If we're not in the mode this music is being set for,
            # don't actually change what's playing.
            if mode != self._music_mode:
                babase.audiolog.debug(
                    'do_play_music: %s requested for %s but current'
                    ' mode is %s; not changing playback.',
                    musictype,
                    mode,
                    self._music_mode,
                )
                return

            # Fade (rather than cut) if this is us starting to yield.
            fade_out = (
                1.0 if os_music_playing and not self._os_music_applied else 0.0
            )
            self._os_music_applied = os_music_playing

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
                babase.audiolog.debug(
                    'do_play_music: playing %s via music-player entry %s.',
                    musictype,
                    entry,
                )
                self._play_music_player_music(entry)

            # Handle via internal music.
            else:
                babase.audiolog.debug(
                    'do_play_music: playing %s via internal music.',
                    musictype,
                )
                self._play_internal_music(musictype, fade_out=fade_out)

    def _get_user_soundtrack(self) -> dict[str, Any]:
        """Return current user soundtrack or empty dict otherwise."""
        cfg = babase.app.config
        soundtrack: dict[str, Any] = {}
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
        # if self._music_node is not None:
        #     self._music_node.delete()
        #     self._music_node = None
        if self._playing_internal_music:
            bascenev1.set_internal_music(None)
            self._playing_internal_music = False

        # Do the thing.
        self.get_music_player().play(entry)

    def _play_internal_music(
        self, musictype: MusicType | None, fade_out: float = 0.0
    ) -> None:
        # Stop any existing music-player playback.
        if self._music_player is not None:
            self._music_player.stop()

        # Stop (or fade out) any existing internal music.
        # if self._music_node:
        #     self._music_node.delete()
        #     self._music_node = None
        if self._playing_internal_music:
            bascenev1.set_internal_music(None, fade_out=fade_out)
            self._playing_internal_music = False

        # Start up new internal music.
        if musictype is not None:
            entry = ASSET_SOUNDTRACK_ENTRIES.get(musictype)
            if entry is None:
                print(f"Unknown music: '{musictype}'")
                entry = ASSET_SOUNDTRACK_ENTRIES[MusicType.FLAG_CATCHER]

            # self._music_node = _bascenev1.newnode(
            #     type='sound',
            #     attrs={
            #         'sound': _bascenev1.getsound(entry.assetname),
            #         'positional': False,
            #         'music': True,
            #         'volume': entry.volume * 5.0,
            #         'loop': entry.loop,
            #     },
            # )
            bascenev1.set_internal_music(
                babase.simple_sound_from_ref(entry.assetname),
                volume=entry.volume * 5.0,
                loop=entry.loop,
            )
            self._playing_internal_music = True


class MusicPlayer:
    """Wrangles soundtrack music playback.

    Music can be played either through the game itself
    or via a platform-specific external player.
    """

    def __init__(self) -> None:
        self._have_set_initial_volume = False
        self._entry_to_play: Any = None
        self._volume = 1.0
        self._actually_playing = False

    def select_entry(
        self,
        callback: Callable[[Any], None],
        current_entry: Any,
        selection_target_name: str,
    ) -> bauiv1.MainWindow:
        """Summons a UI to select a new soundtrack entry."""
        return self.on_select_entry(
            callback, current_entry, selection_target_name
        )

    def set_volume(self, volume: float) -> None:
        """Set player volume (value should be between 0 and 1)."""
        self._volume = volume
        self.on_set_volume(volume)
        self._update_play_state()

    def play(self, entry: Any) -> None:
        """Play provided entry."""
        if not self._have_set_initial_volume:
            self._volume = babase.app.config.resolve('Music Volume')
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

    def on_select_entry(
        self,
        callback: Callable[[Any], None],
        current_entry: Any,
        selection_target_name: str,
    ) -> bauiv1.MainWindow:
        """Present a GUI to select an entry.

        The callback should be called with a valid entry or None to
        signify that the default soundtrack should be used.."""
        raise NotImplementedError()

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
            if self._entry_to_play is None or self._volume <= 0.0:
                self.on_stop()
                self._actually_playing = False


def do_play_music(*args: Any, **keywds: Any) -> None:
    """A passthrough used by the C++ layer."""
    assert babase.app.classic is not None
    babase.app.classic.music.do_play_music(*args, **keywds)
