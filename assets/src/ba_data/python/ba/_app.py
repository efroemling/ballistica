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
"""Functionality related to the high level state of the app."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    import ba
    from ba import _lang, _meta
    from ba.ui import UICleanupCheck
    from bastd.actor import spazappearance
    from typing import (Optional, Dict, Tuple, Set, Any, List, Type, Tuple,
                        Callable)


class App:
    """A class for high level app functionality and state.

    category: App Classes

    Use ba.app to access the single shared instance of this class.

    Note that properties not documented here should be considered internal
    and subject to change without warning.
    """
    # pylint: disable=too-many-public-methods

    # Note: many values here are simple method attrs and thus don't show
    # up in docs. If there's any that'd be useful to expose publicly, they
    # should be converted to properties so its possible to validate values
    # and provide docs.

    @property
    def build_number(self) -> int:
        """Integer build number.

        This value increases by at least 1 with each release of the game.
        It is independent of the human readable ba.App.version string.
        """
        return self._build_number

    @property
    def config_file_path(self) -> str:
        """Where the game's config file is stored on disk."""
        return self._config_file_path

    @property
    def locale(self) -> str:
        """Raw country/language code detected by the game (such as 'en_US').

        Generally for language-specific code you should look at
        ba.App.language, which is the language the game is using
        (which may differ from locale if the user sets a language, etc.)
        """
        return self._locale

    def can_display_language(self, language: str) -> bool:
        """Tell whether we can display a particular language.

        (internal)

        On some platforms we don't have unicode rendering yet
        which limits the languages we can draw.
        """

        # We don't yet support full unicode display on windows or linux :-(.
        if (language in ('Chinese', 'ChineseTraditional', 'Persian', 'Korean',
                         'Arabic', 'Hindi')
                and self.platform in ('windows', 'linux')):
            return False
        return True

    def _get_default_language(self) -> str:
        languages = {
            'de': 'German',
            'es': 'Spanish',
            'sk': 'Slovak',
            'it': 'Italian',
            'nl': 'Dutch',
            'da': 'Danish',
            'pt': 'Portuguese',
            'fr': 'French',
            'el': 'Greek',
            'ru': 'Russian',
            'pl': 'Polish',
            'sv': 'Swedish',
            'eo': 'Esperanto',
            'cs': 'Czech',
            'hr': 'Croatian',
            'hu': 'Hungarian',
            'be': 'Belarussian',
            'ro': 'Romanian',
            'ko': 'Korean',
            'fa': 'Persian',
            'ar': 'Arabic',
            'zh': 'Chinese',
            'tr': 'Turkish',
            'id': 'Indonesian',
            'sr': 'Serbian',
            'uk': 'Ukrainian',
            'hi': 'Hindi'
        }

        # Special case Chinese: specific variations map to traditional.
        # (otherwise will map to 'Chinese' which is simplified)
        if self.locale in ('zh_HANT', 'zh_TW'):
            language = 'ChineseTraditional'
        else:
            language = languages.get(self.locale[:2], 'English')
        if not self.can_display_language(language):
            language = 'English'
        return language

    @property
    def language(self) -> str:
        """The name of the language the game is running in.

        This can be selected explicitly by the user or may be set
        automatically based on ba.App.locale or other factors.
        """
        assert isinstance(self.config, dict)
        return self.config.get('Lang', self.default_language)

    @property
    def user_agent_string(self) -> str:
        """String containing various bits of info about OS/device/etc."""
        return self._user_agent_string

    @property
    def version(self) -> str:
        """Human-readable version string; something like '1.3.24'.

        This should not be interpreted as a number; it may contain
        string elements such as 'alpha', 'beta', 'test', etc.
        If a numeric version is needed, use 'ba.App.build_number'.
        """
        return self._version

    @property
    def debug_build(self) -> bool:
        """Whether the game was compiled in debug mode.

        Debug builds generally run substantially slower than non-debug
        builds due to compiler optimizations being disabled and extra
        checks being run.
        """
        return self._debug_build

    @property
    def test_build(self) -> bool:
        """Whether the game was compiled in test mode.

        Test mode enables extra checks and features that are useful for
        release testing but which do not slow the game down significantly.
        """
        return self._test_build

    @property
    def user_scripts_directory(self) -> str:
        """Path where the game is looking for custom user scripts."""
        return self._user_scripts_directory

    @property
    def system_scripts_directory(self) -> str:
        """Path where the game is looking for its bundled scripts."""
        return self._system_scripts_directory

    @property
    def config(self) -> ba.AppConfig:
        """The ba.AppConfig instance representing the app's config state."""
        assert self._config is not None
        return self._config

    @property
    def platform(self) -> str:
        """Name of the current platform.

        Examples are: 'mac', 'windows', android'.
        """
        return self._platform

    @property
    def subplatform(self) -> str:
        """String for subplatform.

        Can be empty. For the 'android' platform, subplatform may
        be 'google', 'amazon', etc.
        """
        return self._subplatform

    @property
    def api_version(self) -> int:
        """The game's api version.

        Only python modules and packages associated with the current api
        version will be detected by the game (see the ba_meta tag). This
        value will change whenever backward-incompatible changes are
        introduced to game apis; when that happens, scripts should be updated
        accordingly and set to target the new api.
        """
        from ba._meta import CURRENT_API_VERSION
        return CURRENT_API_VERSION

    @property
    def interface_type(self) -> str:
        """Interface mode the game is in; can be 'large', 'medium', or 'small'.

        'large' is used by system such as desktop PC where elements on screen
          remain usable even at small sizes, allowing more to be shown.
        'small' is used by small devices such as phones, where elements on
          screen must be larger to remain readable and usable.
        'medium' is used by tablets and other middle-of-the-road situations
          such as VR or TV.
        """
        return self._interface_type

    @property
    def on_tv(self) -> bool:
        """Bool value for if the game is running on a TV."""
        return self._on_tv

    @property
    def vr_mode(self) -> bool:
        """Bool value for if the game is running in VR."""
        return self._vr_mode

    @property
    def ui_bounds(self) -> Tuple[float, float, float, float]:
        """Bounds of the 'safe' screen area in ui space.

        This tuple contains: (x-min, x-max, y-min, y-max)
        """
        return _ba.uibounds()

    def __init__(self) -> None:
        """(internal)

        Do not instantiate this class; use ba.app to access
        the single shared instance.
        """
        # pylint: disable=too-many-statements
        from ba._music import MusicPlayMode

        # _test_https()

        # Config.
        self.config_file_healthy = False

        # This is incremented any time the app is backgrounded/foregrounded;
        # can be a simple way to determine if network data should be
        # refreshed/etc.
        self.fg_state = 0

        # Environment stuff.
        # (pulling these into attrs so we can type-check them)

        env = _ba.env()
        self._build_number: int = env['build_number']
        assert isinstance(self._build_number, int)
        self._config_file_path: str = env['config_file_path']
        assert isinstance(self._config_file_path, str)
        self._locale: str = env['locale']
        assert isinstance(self._locale, str)
        self._user_agent_string: str = env['user_agent_string']
        assert isinstance(self._user_agent_string, str)
        self._version: str = env['version']
        assert isinstance(self._version, str)
        self._debug_build: bool = env['debug_build']
        assert isinstance(self._debug_build, bool)
        self._test_build: bool = env['test_build']
        assert isinstance(self._test_build, bool)
        self._user_scripts_directory: str = env['user_scripts_directory']
        assert isinstance(self._user_scripts_directory, str)
        self._system_scripts_directory: str = env['system_scripts_directory']
        assert isinstance(self._system_scripts_directory, str)
        self._platform: str = env['platform']
        assert isinstance(self._platform, str)
        self._subplatform: str = env['subplatform']
        assert isinstance(self._subplatform, str)
        self._interface_type: str = env['interface_type']
        assert isinstance(self._interface_type, str)
        self._on_tv: bool = env['on_tv']
        assert isinstance(self._on_tv, bool)
        self._vr_mode: bool = env['vr_mode']
        assert isinstance(self._vr_mode, bool)
        self.protocol_version: int = env['protocol_version']
        assert isinstance(self.protocol_version, int)
        self.toolbar_test: bool = env['toolbar_test']
        assert isinstance(self.toolbar_test, bool)
        self.kiosk_mode: bool = env['kiosk_mode']
        assert isinstance(self.kiosk_mode, bool)

        # Misc.
        self.default_language = self._get_default_language()
        self.metascan: Optional[_meta.ScanResults] = None
        self.tips: List[str] = []
        self.stress_test_reset_timer: Optional[ba.Timer] = None
        self.suppress_debug_reports = False
        self.last_ad_completion_time: Optional[float] = None
        self.last_ad_was_short = False
        self.did_weak_call_warning = False
        self.ran_on_launch = False

        # If we try to run promo-codes due to launch-args/etc we might
        # not be signed in yet; go ahead and queue them up in that case.
        self.pending_promo_codes: List[str] = []
        self.last_in_game_ad_remove_message_show_time: Optional[float] = None
        self.log_have_new = False
        self.log_upload_timer_started = False
        self._config: Optional[ba.AppConfig] = None
        self.printed_live_object_warning = False
        self.last_post_purchase_message_time: Optional[float] = None

        # We include this extra hash with shared input-mapping names so
        # that we don't share mappings between differently-configured
        # systems. For instance, different android devices may give different
        # key values for the same controller type so we keep their mappings
        # distinct.
        self.input_map_hash: Optional[str] = None

        # Co-op Campaigns.
        self.campaigns: Dict[str, ba.Campaign] = {}

        # Server-Mode.
        self.server_config: Dict[str, Any] = {}
        self.server_config_dirty = False
        self.run_server_wait_timer: Optional[ba.Timer] = None
        self.server_playlist_fetch: Optional[Dict[str, Any]] = None
        self.launched_server = False
        self.run_server_first_run = True

        # Ads.
        self.last_ad_network = 'unknown'
        self.last_ad_network_set_time = time.time()
        self.ad_amt: Optional[float] = None
        self.last_ad_purpose = 'invalid'
        self.attempted_first_ad = False

        # Music.
        self.music: Optional[ba.Node] = None
        self.music_mode: ba.MusicPlayMode = MusicPlayMode.REGULAR
        self.music_player: Optional[ba.MusicPlayer] = None
        self.music_player_type: Optional[Type[ba.MusicPlayer]] = None
        self.music_types: Dict[ba.MusicPlayMode, Optional[ba.MusicType]] = {
            MusicPlayMode.REGULAR: None,
            MusicPlayMode.TEST: None
        }

        # Language.
        self.language_target: Optional[_lang.AttrDict] = None
        self.language_merged: Optional[_lang.AttrDict] = None

        # Achievements.
        self.achievements: List[ba.Achievement] = []
        self.achievements_to_display: (List[Tuple[ba.Achievement, bool]]) = []
        self.achievement_display_timer: Optional[_ba.Timer] = None
        self.last_achievement_display_time: float = 0.0
        self.achievement_completion_banner_slots: Set[int] = set()

        # Lobby.
        self.lobby_random_profile_index: int = 1
        self.lobby_random_char_index_offset: Optional[int] = None
        self.lobby_account_profile_device_id: Optional[int] = None

        # Main Menu.
        self.main_menu_did_initial_transition = False
        self.main_menu_last_news_fetch_time: Optional[float] = None

        # Spaz.
        self.spaz_appearances: Dict[str, spazappearance.Appearance] = {}
        self.last_spaz_turbo_warn_time: float = -99999.0

        # Maps.
        self.maps: Dict[str, Type[ba.Map]] = {}

        # Gameplay.
        self.teams_series_length = 7
        self.ffa_series_length = 24
        self.coop_session_args: dict = {}

        # UI.
        self.uicontroller: Optional[ba.UIController] = None
        self.main_menu_window: Optional[_ba.Widget] = None  # FIXME: Kill this.
        self.window_states: dict = {}  # FIXME: Kill this.
        self.windows: dict = {}  # FIXME: Kill this.
        self.main_window: Optional[str] = None  # FIXME: Kill this.
        self.main_menu_selection: Optional[str] = None  # FIXME: Kill this.
        self.have_party_queue_window = False
        self.quit_window: Any = None
        self.dismiss_wii_remotes_window_call: (Optional[Callable[[],
                                                                 Any]]) = None
        self.value_test_defaults: dict = {}
        self.main_menu_window_refresh_check_count = 0
        self.first_main_menu = True  # FIXME: Move to mainmenu class.
        self.did_menu_intro = False  # FIXME: Move to mainmenu class.
        self.main_menu_resume_callbacks: list = []  # can probably go away
        self.special_offer = None
        self.league_rank_cache: dict = {}
        self.tournament_info: dict = {}
        self.account_tournament_list: Optional[Tuple[int, List[str]]] = None
        self.ping_thread_count = 0
        self.invite_confirm_windows: List[Any] = []  # FIXME: Don't use Any.
        self.store_layout: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self.store_items: Optional[Dict[str, Dict]] = None
        self.pro_sale_start_time: Optional[int] = None
        self.pro_sale_start_val: Optional[int] = None
        self.party_window: Any = None  # FIXME: Don't use Any.
        self.title_color = (0.72, 0.7, 0.75)
        self.heading_color = (0.72, 0.7, 0.75)
        self.infotextcolor = (0.7, 0.9, 0.7)
        self.uicleanupchecks: List[UICleanupCheck] = []
        self.uiupkeeptimer: Optional[ba.Timer] = None
        self.delegate: Optional[ba.AppDelegate] = None

        # A few shortcuts.
        self.small_ui = env['interface_type'] == 'small'
        self.med_ui = env['interface_type'] == 'medium'
        self.large_ui = env['interface_type'] == 'large'
        self.toolbars = env.get('toolbar_test', True)

    def on_launch(self) -> None:
        """Runs after the app finishes bootstrapping.

        (internal)"""
        # FIXME: Break this up.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from ba import _apputils
        from ba import _appconfig
        from ba.ui import UIController, ui_upkeep
        from ba import _achievement
        from ba import _map
        from ba import _meta
        from ba import _music
        from ba import _campaign
        from bastd import appdelegate
        from bastd import maps as stdmaps
        from bastd.actor import spazappearance
        from ba._enums import TimeType

        cfg = self.config

        self.delegate = appdelegate.AppDelegate()

        self.uicontroller = UIController()
        _achievement.init_achievements()
        spazappearance.register_appearances()
        _campaign.init_campaigns()
        if _ba.env()['platform'] == 'android':
            self.music_player_type = _music.InternalMusicPlayer
        elif _ba.env()['platform'] == 'mac' and hasattr(
                _ba, 'mac_music_app_init'):
            self.music_player_type = _music.MacMusicAppMusicPlayer

        # FIXME: This should not be hard-coded.
        for maptype in [
                stdmaps.HockeyStadium, stdmaps.FootballStadium,
                stdmaps.Bridgit, stdmaps.BigG, stdmaps.Roundabout,
                stdmaps.MonkeyFace, stdmaps.ZigZag, stdmaps.ThePad,
                stdmaps.DoomShroom, stdmaps.LakeFrigid, stdmaps.TipTop,
                stdmaps.CragCastle, stdmaps.TowerD, stdmaps.HappyThoughts,
                stdmaps.StepRightUp, stdmaps.Courtyard, stdmaps.Rampage
        ]:
            _map.register_map(maptype)

        if self.debug_build:
            _apputils.suppress_debug_reports()

        # IMPORTANT - if tweaking UI stuff, you need to make sure it behaves
        # for small, medium, and large UI modes. (doesn't run off screen, etc).
        # Set these to 1 to test with different sizes. Generally small is used
        # on phones, medium is used on tablets, and large is on desktops or
        # large tablets.

        # Kick off our periodic UI upkeep.
        # FIXME: Can probably kill this if we do immediate UI death checks.
        self.uiupkeeptimer = _ba.Timer(2.6543,
                                       ui_upkeep,
                                       timetype=TimeType.REAL,
                                       repeat=True)

        if bool(False):  # force-test small UI
            self.small_ui = True
            self.med_ui = False
            with _ba.Context('ui'):
                _ba.pushcall(lambda: _ba.screenmessage(
                    'FORCING SMALL UI FOR TESTING', color=(1, 0, 1), log=True))

        if bool(False):  # force-test medium UI
            self.small_ui = False
            self.med_ui = True
            with _ba.Context('ui'):
                _ba.pushcall(lambda: _ba.screenmessage(
                    'FORCING MEDIUM UI FOR TESTING', color=(1, 0, 1
                                                            ), log=True))
        if bool(False):  # force-test large UI
            self.small_ui = False
            self.med_ui = False
            with _ba.Context('ui'):
                _ba.pushcall(lambda: _ba.screenmessage(
                    'FORCING LARGE UI FOR TESTING', color=(1, 0, 1), log=True))

        # If there's a leftover log file, attempt to upload
        # it to the server and/or get rid of it.
        _apputils.handle_leftover_log_file()
        try:
            _apputils.handle_leftover_log_file()
        except Exception:
            from ba import _error
            _error.print_exception('Error handling leftover log file')

        # Notify the user if we're using custom system scripts.
        # FIXME: This no longer works since sys-scripts is an absolute path;
        #  need to just add a proper call to query this.
        # if env['system_scripts_directory'] != 'data/scripts':
        #     ba.screenmessage("Using custom system scripts...",
        #                     color=(0, 1, 0))

        # Only do this stuff if our config file is healthy so we don't
        # overwrite a broken one or whatnot and wipe out data.
        if not self.config_file_healthy:
            if self.platform in ('mac', 'linux', 'windows'):
                from bastd.ui import configerror
                configerror.ConfigErrorWindow()
                return

            # For now on other systems we just overwrite the bum config.
            # At this point settings are already set; lets just commit them
            # to disk.
            _appconfig.commit_app_config(force=True)

        # If we're using a non-default playlist, lets go ahead and get our
        # music-player going since it may hitch (better while we're faded
        # out than later).
        try:
            if ('Soundtrack' in cfg and cfg['Soundtrack'] not in [
                    '__default__', 'Default Soundtrack'
            ]):
                _music.get_music_player()
        except Exception:
            from ba import _error
            _error.print_exception('error prepping music-player')

        launch_count = cfg.get('launchCount', 0)
        launch_count += 1

        # So we know how many times we've run the game at various
        # version milestones.
        for key in ('lc14173', 'lc14292'):
            cfg.setdefault(key, launch_count)

        # Debugging - make note if we're using the local test server so we
        # don't accidentally leave it on in a release.
        # FIXME - move this to native layer.
        server_addr = _ba.get_master_server_address()
        if 'localhost' in server_addr:
            _ba.timer(2.0,
                      lambda: _ba.screenmessage("Note: using local server",
                                                (1, 1, 0),
                                                log=True),
                      timetype=TimeType.REAL)
        elif 'test' in server_addr:
            _ba.timer(
                2.0,
                lambda: _ba.screenmessage("Note: using test server-module",
                                          (1, 1, 0),
                                          log=True),
                timetype=TimeType.REAL)

        cfg['launchCount'] = launch_count
        cfg.commit()

        # Run a test in a few seconds to see if we should pop up an existing
        # pending special offer.
        def check_special_offer() -> None:
            from bastd.ui import specialoffer
            config = self.config
            if ('pendingSpecialOffer' in config and _ba.get_public_login_id()
                    == config['pendingSpecialOffer']['a']):
                self.special_offer = config['pendingSpecialOffer']['o']
                specialoffer.show_offer()

        if self.subplatform != 'headless':
            _ba.timer(3.0, check_special_offer, timetype=TimeType.REAL)

        # Start scanning for things exposed via ba_meta.
        _meta.start_scan()

        # Auto-sign-in to a local account in a moment if we're set to.
        def do_auto_sign_in() -> None:
            if self.subplatform == 'headless':
                _ba.sign_in('Local')
            elif cfg.get('Auto Account State') == 'Local':
                _ba.sign_in('Local')

        _ba.pushcall(do_auto_sign_in)

        self.ran_on_launch = True

        # from ba._dependency import test_depset
        # test_depset()

    def read_config(self) -> None:
        """(internal)"""
        from ba import _appconfig
        self._config, self.config_file_healthy = _appconfig.read_config()

    def pause(self) -> None:
        """Pause the game due to a user request or menu popping up.

        If there's a foreground host-activity that says it's pausable, tell it
        to pause ..we now no longer pause if there are connected clients.
        """
        activity = _ba.get_foreground_host_activity()
        if (activity is not None and activity.allow_pausing
                and not _ba.have_connected_clients()):
            from ba import _gameutils, _actor, _lang
            # FIXME: Shouldn't be touching scene stuff here;
            #  should just pass the request on to the host-session.
            with _ba.Context(activity):
                globs = _gameutils.sharedobj('globals')
                if not globs.paused:
                    _ba.playsound(_ba.getsound('refWhistle'))
                    globs.paused = True

                # FIXME: This should not be an attr on Actor.
                activity.paused_text = _actor.Actor(
                    _ba.newnode(
                        'text',
                        attrs={
                            'text': _lang.Lstr(resource='pausedByHostText'),
                            'client_only': True,
                            'flatness': 1.0,
                            'h_align': 'center'
                        }))

    def resume(self) -> None:
        """Resume the game due to a user request or menu closing.

        If there's a foreground host-activity that's currently paused, tell it
        to resume.
        """
        from ba import _gameutils

        # FIXME: Shouldn't be touching scene stuff here;
        #  should just pass the request on to the host-session.
        activity = _ba.get_foreground_host_activity()
        if activity is not None:
            with _ba.Context(activity):
                globs = _gameutils.sharedobj('globals')
                if globs.paused:
                    _ba.playsound(_ba.getsound('refWhistle'))
                    globs.paused = False

                    # FIXME: This should not be an actor attr.
                    activity.paused_text = None

    def return_to_main_menu_session_gracefully(self) -> None:
        """Attempt to cleanly get back to the main menu."""
        # pylint: disable=cyclic-import
        from ba import _benchmark
        from ba._general import Call
        from bastd import mainmenu
        _ba.app.main_window = None
        if isinstance(_ba.get_foreground_host_session(),
                      mainmenu.MainMenuSession):
            # It may be possible we're on the main menu but the screen is faded
            # so fade back in.
            _ba.fade_screen(True)
            return

        _benchmark.stop_stress_test()  # Stop stress-test if in progress.

        # If we're in a host-session, tell them to end.
        # This lets them tear themselves down gracefully.
        host_session = _ba.get_foreground_host_session()
        if host_session is not None:

            # Kick off a little transaction so we'll hopefully have all the
            # latest account state when we get back to the menu.
            _ba.add_transaction({
                'type': 'END_SESSION',
                'sType': str(type(host_session))
            })
            _ba.run_transactions()

            host_session.end()

        # Otherwise just force the issue.
        else:
            _ba.pushcall(Call(_ba.new_host_session, mainmenu.MainMenuSession))

    def add_main_menu_close_callback(self, call: Callable[[], Any]) -> None:
        """(internal)"""

        # If there's no main menu up, just call immediately.
        if not self.main_menu_window:
            with _ba.Context('ui'):
                call()
        else:
            self.main_menu_resume_callbacks.append(call)

    def handle_app_pause(self) -> None:
        """Called when the app goes to a suspended state."""

    def handle_app_resume(self) -> None:
        """Run when the app resumes from a suspended state."""

        # If there's music playing externally, make sure we aren't playing
        # ours.
        from ba import _music
        _music.handle_app_resume()
        self.fg_state += 1

        # Mark our cached tourneys as invalid so anyone using them knows
        # they might be out of date.
        for entry in list(self.tournament_info.values()):
            entry['valid'] = False

    def launch_coop_game(self,
                         game: str,
                         force: bool = False,
                         args: Dict = None) -> bool:
        """High level way to launch a co-op session locally."""
        # pylint: disable=cyclic-import
        from ba._campaign import get_campaign
        from bastd.ui.coop.level import CoopLevelLockedWindow
        if args is None:
            args = {}
        if game == '':
            raise Exception("empty game name")
        campaignname, levelname = game.split(':')
        campaign = get_campaign(campaignname)
        levels = campaign.get_levels()

        # If this campaign is sequential, make sure we've completed the
        # one before this.
        if campaign.sequential and not force:
            for level in levels:
                if level.name == levelname:
                    break
                if not level.complete:
                    CoopLevelLockedWindow(
                        campaign.get_level(levelname).displayname,
                        campaign.get_level(level.name).displayname)
                    return False

        # Ok, we're good to go.
        self.coop_session_args = {'campaign': campaignname, 'level': levelname}
        for arg_name, arg_val in list(args.items()):
            self.coop_session_args[arg_name] = arg_val

        def _fade_end() -> None:
            from ba import _coopsession
            try:
                _ba.new_host_session(_coopsession.CoopSession)
            except Exception:
                from ba import _error
                _error.print_exception()
                from bastd import mainmenu
                _ba.new_host_session(mainmenu.MainMenuSession)

        _ba.fade_screen(False, endcall=_fade_end)
        return True

    def do_remove_in_game_ads_message(self) -> None:
        """(internal)"""
        from ba._lang import Lstr
        from ba._enums import TimeType

        # Print this message once every 10 minutes at most.
        tval = _ba.time(TimeType.REAL)
        if (self.last_in_game_ad_remove_message_show_time is None or
            (tval - self.last_in_game_ad_remove_message_show_time > 60 * 10)):
            self.last_in_game_ad_remove_message_show_time = tval
            with _ba.Context('ui'):
                _ba.timer(
                    1.0,
                    lambda: _ba.screenmessage(Lstr(
                        resource='removeInGameAdsText',
                        subs=[('${PRO}',
                               Lstr(resource='store.bombSquadProNameText')),
                              ('${APP_NAME}', Lstr(resource='titleText'))]),
                                              color=(1, 1, 0)),
                    timetype=TimeType.REAL)

    def shutdown(self) -> None:
        """(internal)"""
        if self.music_player is not None:
            self.music_player.shutdown()

    def handle_deep_link(self, url: str) -> None:
        """Handle a deep link URL."""
        from ba._lang import Lstr
        from ba._enums import TimeType
        if url.startswith('ballisticacore://code/'):
            code = url.replace('ballisticacore://code/', '')

            # If we're not signed in, queue up the code to run the next time we
            # are and issue a warning if we haven't signed in within the next
            # few seconds.
            if _ba.get_account_state() != 'signed_in':

                def check_pending_codes() -> None:
                    """(internal)"""

                    # If we're still not signed in and have pending codes,
                    # inform the user that they need to sign in to use them.
                    if _ba.app.pending_promo_codes:
                        _ba.screenmessage(
                            Lstr(resource='signInForPromoCodeText'),
                            color=(1, 0, 0))
                        _ba.playsound(_ba.getsound('error'))

                _ba.app.pending_promo_codes.append(code)
                _ba.timer(6.0, check_pending_codes, timetype=TimeType.REAL)
                return
            _ba.screenmessage(Lstr(resource='submittingPromoCodeText'),
                              color=(0, 1, 0))
            _ba.add_transaction({
                'type': 'PROMO_CODE',
                'expire_time': time.time() + 5,
                'code': code
            })
            _ba.run_transactions()
        else:
            _ba.screenmessage(Lstr(resource='errorText'), color=(1, 0, 0))
            _ba.playsound(_ba.getsound('error'))

    def _test_https(self) -> None:
        """Testing https support.

        (would be nice to get this working on our custom python builds; need
        to wrangle certificates somehow).
        """
        import urllib.request
        try:
            val = urllib.request.urlopen('https://example.com').read()
            print("HTTPS TEST SUCCESS", len(val))
        except Exception as exc:
            print("HTTPS TEST FAIL:", exc)
