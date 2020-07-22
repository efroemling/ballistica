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
import random
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    import ba
    from ba import _lang, _meta
    from bastd.actor import spazappearance
    from typing import Optional, Dict, Set, Any, Type, Tuple, Callable, List


class App:
    """A class for high level app functionality and state.

    Category: App Classes

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
        if (language in {
                'Chinese', 'ChineseTraditional', 'Persian', 'Korean', 'Arabic',
                'Hindi', 'Vietnamese'
        } and self.platform in ('windows', 'linux')):
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
            'vi': 'Vietnamese',
            'hi': 'Hindi'
        }

        # Special case for Chinese: specific variations map to traditional.
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
    def python_directory_user(self) -> str:
        """Path where the app looks for custom user scripts."""
        return self._python_directory_user

    @property
    def python_directory_app(self) -> str:
        """Path where the app looks for its bundled scripts."""
        return self._python_directory_app

    @property
    def python_directory_app_site(self) -> str:
        """Path containing pip packages bundled with the app."""
        return self._python_directory_app_site

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
        from ba._music import MusicController
        from ba._ui import UI

        # Config.
        self.config_file_healthy = False

        # This is incremented any time the app is backgrounded/foregrounded;
        # can be a simple way to determine if network data should be
        # refreshed/etc.
        self.fg_state = 0

        # Environment stuff.
        # (pulling these into attrs so we can type-check them and provide docs)
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
        self._python_directory_user: str = env['python_directory_user']
        assert isinstance(self._python_directory_user, str)
        self._python_directory_app: str = env['python_directory_app']
        assert isinstance(self._python_directory_app, str)
        self._python_directory_app_site: str = env['python_directory_app_site']
        assert isinstance(self._python_directory_app_site, str)
        self._platform: str = env['platform']
        assert isinstance(self._platform, str)
        self._subplatform: str = env['subplatform']
        assert isinstance(self._subplatform, str)
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
        self.headless_build: bool = env['headless_build']
        assert isinstance(self.headless_build, bool)

        # Plugins.
        self.potential_plugins: List[ba.PotentialPlugin] = []
        self.active_plugins: Dict[str, ba.Plugin] = {}

        # Misc.
        self.default_language = self._get_default_language()
        self.metascan: Optional[_meta.ScanResults] = None
        self.tips: List[str] = []
        self.stress_test_reset_timer: Optional[ba.Timer] = None
        self.last_ad_completion_time: Optional[float] = None
        self.last_ad_was_short = False
        self.did_weak_call_warning = False
        self.ran_on_app_launch = False

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

        # Server Mode.
        self.server: Optional[ba.ServerController] = None

        # Ads.
        self.last_ad_network = 'unknown'
        self.last_ad_network_set_time = time.time()
        self.ad_amt: Optional[float] = None
        self.last_ad_purpose = 'invalid'
        self.attempted_first_ad = False

        # Music.
        self.music = MusicController()

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
        self.lobby_random_char_index_offset = random.randrange(1000)
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
        self.coop_session_args: Dict = {}

        # UI.
        self.ui = UI()

        self.value_test_defaults: dict = {}
        self.first_main_menu = True  # FIXME: Move to mainmenu class.
        self.did_menu_intro = False  # FIXME: Move to mainmenu class.
        self.main_menu_window_refresh_check_count = 0  # FIXME: Mv to mainmenu.
        self.main_menu_resume_callbacks: list = []  # Can probably go away.
        self.special_offer: Optional[Dict] = None
        self.league_rank_cache: Dict = {}
        self.tournament_info: Dict = {}
        self.account_tournament_list: Optional[Tuple[int, List[str]]] = None
        self.ping_thread_count = 0
        self.invite_confirm_windows: List[Any] = []  # FIXME: Don't use Any.
        self.store_layout: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self.store_items: Optional[Dict[str, Dict]] = None
        self.pro_sale_start_time: Optional[int] = None
        self.pro_sale_start_val: Optional[int] = None

        self.delegate: Optional[ba.AppDelegate] = None

    def on_app_launch(self) -> None:
        """Runs after the app finishes bootstrapping.

        (internal)"""
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        # pylint: disable=too-many-statements
        from ba import _apputils
        from ba import _appconfig
        from ba import _achievement
        from ba import _map
        from ba import _meta
        from ba import _campaign
        from bastd import appdelegate
        from bastd import maps as stdmaps
        from bastd.actor import spazappearance
        from ba._enums import TimeType

        cfg = self.config

        self.delegate = appdelegate.AppDelegate()

        self.ui.on_app_launch()

        _achievement.init_achievements()
        spazappearance.register_appearances()
        _campaign.init_campaigns()

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

        # Non-test, non-debug builds should generally be blessed; warn if not.
        # (so I don't accidentally release a build that can't play tourneys)
        if (not self.debug_build and not self.test_build
                and not _ba.is_blessed()):
            _ba.screenmessage('WARNING: NON-BLESSED BUILD', color=(1, 0, 0))

        # If there's a leftover log file, attempt to upload it to the
        # master-server and/or get rid of it.
        _apputils.handle_leftover_log_file()

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

        self.music.on_app_launch()

        launch_count = cfg.get('launchCount', 0)
        launch_count += 1

        # So we know how many times we've run the game at various
        # version milestones.
        for key in ('lc14173', 'lc14292'):
            cfg.setdefault(key, launch_count)

        # Debugging - make note if we're using the local test server so we
        # don't accidentally leave it on in a release.
        # FIXME - should move this to the native layer.
        server_addr = _ba.get_master_server_address()
        if 'localhost' in server_addr:
            _ba.timer(2.0,
                      lambda: _ba.screenmessage('Note: using local server',
                                                (1, 1, 0),
                                                log=True),
                      timetype=TimeType.REAL)
        elif 'test' in server_addr:
            _ba.timer(
                2.0,
                lambda: _ba.screenmessage('Note: using test server-module',
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

        if not self.headless_build:
            _ba.timer(3.0, check_special_offer, timetype=TimeType.REAL)

        # Start scanning for things exposed via ba_meta.
        _meta.start_scan()

        # Auto-sign-in to a local account in a moment if we're set to.
        def do_auto_sign_in() -> None:
            if self.headless_build or cfg.get('Auto Account State') == 'Local':
                _ba.sign_in('Local')

        _ba.pushcall(do_auto_sign_in)

        # Load up our plugins and go ahead and call their on_app_launch calls.
        self.load_plugins()
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_launch()
            except Exception:
                from ba import _error
                _error.print_exception('Error in plugin on_app_launch()')

        self.ran_on_app_launch = True

        # from ba._dependency import test_depset
        # test_depset()

    def load_plugins(self) -> None:
        """(internal)"""
        from ba._general import getclass
        from ba._plugin import Plugin

        # Note: the plugins we load is purely based on what's enabled
        # in the app config. Our meta-scan gives us a list of available
        # plugins, but that is only used to give the user a list of plugins
        # that they can enable. (we wouldn't want to look at meta-scan here
        # anyway because it may not be done yet at this point in the launch)
        plugstates: Dict[str, Dict] = self.config.get('Plugins', {})
        assert isinstance(plugstates, dict)
        plugkeys: List[str] = sorted(key for key, val in plugstates.items()
                                     if val.get('enabled', False))
        for plugkey in plugkeys:
            try:
                cls = getclass(plugkey, Plugin)
            except Exception as exc:
                _ba.log(f"Error loading plugin class '{plugkey}': {exc}",
                        to_server=False)
                continue
            try:
                plugin = cls()
                assert plugkey not in self.active_plugins
                self.active_plugins[plugkey] = plugin
            except Exception:
                from ba import _error
                _error.print_exception(f'Error loading plugin: {plugkey}')

    def read_config(self) -> None:
        """(internal)"""
        from ba import _appconfig
        self._config, self.config_file_healthy = _appconfig.read_config()

    def pause(self) -> None:
        """Pause the game due to a user request or menu popping up.

        If there's a foreground host-activity that says it's pausable, tell it
        to pause ..we now no longer pause if there are connected clients.
        """
        activity: Optional[ba.Activity] = _ba.get_foreground_host_activity()
        if (activity is not None and activity.allow_pausing
                and not _ba.have_connected_clients()):
            from ba import _gameutils, _lang
            from ba._nodeactor import NodeActor

            # FIXME: Shouldn't be touching scene stuff here;
            #  should just pass the request on to the host-session.
            with _ba.Context(activity):
                globs = activity.globalsnode
                if not globs.paused:
                    _ba.playsound(_ba.getsound('refWhistle'))
                    globs.paused = True

                # FIXME: This should not be an attr on Actor.
                activity.paused_text = NodeActor(
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

        # FIXME: Shouldn't be touching scene stuff here;
        #  should just pass the request on to the host-session.
        activity = _ba.get_foreground_host_activity()
        if activity is not None:
            with _ba.Context(activity):
                globs = activity.globalsnode
                if globs.paused:
                    _ba.playsound(_ba.getsound('refWhistle'))
                    globs.paused = False

                    # FIXME: This should not be an actor attr.
                    activity.paused_text = None

    def return_to_main_menu_session_gracefully(self,
                                               reset_ui: bool = True) -> None:
        """Attempt to cleanly get back to the main menu."""
        # pylint: disable=cyclic-import
        from ba import _benchmark
        from ba._general import Call
        from bastd.mainmenu import MainMenuSession
        if reset_ui:
            _ba.app.ui.clear_main_menu_window()

        if isinstance(_ba.get_foreground_host_session(), MainMenuSession):
            # It may be possible we're on the main menu but the screen is faded
            # so fade back in.
            _ba.fade_screen(True)
            return

        _benchmark.stop_stress_test()  # Stop stress-test if in progress.

        # If we're in a host-session, tell them to end.
        # This lets them tear themselves down gracefully.
        host_session: Optional[ba.Session] = _ba.get_foreground_host_session()
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
            _ba.pushcall(Call(_ba.new_host_session, MainMenuSession))

    def add_main_menu_close_callback(self, call: Callable[[], Any]) -> None:
        """(internal)"""

        # If there's no main menu up, just call immediately.
        if not self.ui.has_main_menu_window():
            with _ba.Context('ui'):
                call()
        else:
            self.main_menu_resume_callbacks.append(call)

    def on_app_pause(self) -> None:
        """Called when the app goes to a suspended state."""

    def on_app_resume(self) -> None:
        """Run when the app resumes from a suspended state."""

        self.music.on_app_resume()

        self.fg_state += 1

        # Mark our cached tourneys as invalid so anyone using them knows
        # they might be out of date.
        for entry in list(self.tournament_info.values()):
            entry['valid'] = False

    def launch_coop_game(self,
                         game: str,
                         force: bool = False,
                         args: Dict = None) -> bool:
        """High level way to launch a local co-op session."""
        # pylint: disable=cyclic-import
        from ba._campaign import getcampaign
        from bastd.ui.coop.level import CoopLevelLockedWindow
        if args is None:
            args = {}
        if game == '':
            raise ValueError('empty game name')
        campaignname, levelname = game.split(':')
        campaign = getcampaign(campaignname)

        # If this campaign is sequential, make sure we've completed the
        # one before this.
        if campaign.sequential and not force:
            for level in campaign.levels:
                if level.name == levelname:
                    break
                if not level.complete:
                    CoopLevelLockedWindow(
                        campaign.getlevel(levelname).displayname,
                        campaign.getlevel(level.name).displayname)
                    return False

        # Ok, we're good to go.
        self.coop_session_args = {
            'campaign': campaignname,
            'level': levelname,
        }
        for arg_name, arg_val in list(args.items()):
            self.coop_session_args[arg_name] = arg_val

        def _fade_end() -> None:
            from ba import _coopsession
            try:
                _ba.new_host_session(_coopsession.CoopSession)
            except Exception:
                from ba import _error
                _error.print_exception()
                from bastd.mainmenu import MainMenuSession
                _ba.new_host_session(MainMenuSession)

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

    def on_app_shutdown(self) -> None:
        """(internal)"""
        self.music.on_app_shutdown()

    def handle_deep_link(self, url: str) -> None:
        """Handle a deep link URL."""
        from ba._lang import Lstr
        from ba._enums import TimeType
        appname = _ba.appname()
        if url.startswith(f'{appname}://code/'):
            code = url.replace(f'{appname}://code/', '')

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
            print('HTTPS TEST SUCCESS', len(val))
        except Exception as exc:
            print('HTTPS TEST FAIL:', exc)
