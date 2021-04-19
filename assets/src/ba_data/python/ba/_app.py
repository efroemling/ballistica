# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the high level state of the app."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba
from ba._music import MusicSubsystem
from ba._language import LanguageSubsystem
from ba._ui import UISubsystem
from ba._achievement import AchievementSubsystem
from ba._plugin import PluginSubsystem
from ba._account import AccountSubsystem
from ba._meta import MetadataSubsystem
from ba._ads import AdsSubsystem

if TYPE_CHECKING:
    import ba
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

    @property
    def build_number(self) -> int:
        """Integer build number.

        This value increases by at least 1 with each release of the game.
        It is independent of the human readable ba.App.version string.
        """
        assert isinstance(self._env['build_number'], int)
        return self._env['build_number']

    @property
    def config_file_path(self) -> str:
        """Where the game's config file is stored on disk."""
        assert isinstance(self._env['config_file_path'], str)
        return self._env['config_file_path']

    @property
    def user_agent_string(self) -> str:
        """String containing various bits of info about OS/device/etc."""
        assert isinstance(self._env['user_agent_string'], str)
        return self._env['user_agent_string']

    @property
    def version(self) -> str:
        """Human-readable version string; something like '1.3.24'.

        This should not be interpreted as a number; it may contain
        string elements such as 'alpha', 'beta', 'test', etc.
        If a numeric version is needed, use 'ba.App.build_number'.
        """
        assert isinstance(self._env['version'], str)
        return self._env['version']

    @property
    def debug_build(self) -> bool:
        """Whether the game was compiled in debug mode.

        Debug builds generally run substantially slower than non-debug
        builds due to compiler optimizations being disabled and extra
        checks being run.
        """
        assert isinstance(self._env['debug_build'], bool)
        return self._env['debug_build']

    @property
    def test_build(self) -> bool:
        """Whether the game was compiled in test mode.

        Test mode enables extra checks and features that are useful for
        release testing but which do not slow the game down significantly.
        """
        assert isinstance(self._env['test_build'], bool)
        return self._env['test_build']

    @property
    def python_directory_user(self) -> str:
        """Path where the app looks for custom user scripts."""
        assert isinstance(self._env['python_directory_user'], str)
        return self._env['python_directory_user']

    @property
    def python_directory_app(self) -> str:
        """Path where the app looks for its bundled scripts."""
        assert isinstance(self._env['python_directory_app'], str)
        return self._env['python_directory_app']

    @property
    def python_directory_app_site(self) -> str:
        """Path containing pip packages bundled with the app."""
        assert isinstance(self._env['python_directory_app_site'], str)
        return self._env['python_directory_app_site']

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
        assert isinstance(self._env['platform'], str)
        return self._env['platform']

    @property
    def subplatform(self) -> str:
        """String for subplatform.

        Can be empty. For the 'android' platform, subplatform may
        be 'google', 'amazon', etc.
        """
        assert isinstance(self._env['subplatform'], str)
        return self._env['subplatform']

    @property
    def api_version(self) -> int:
        """The game's api version.

        Only Python modules and packages associated with the current API
        version number will be detected by the game (see the ba_meta tag).
        This value will change whenever backward-incompatible changes are
        introduced to game APIs. When that happens, scripts should be updated
        accordingly and set to target the new API version number.
        """
        from ba._meta import CURRENT_API_VERSION
        return CURRENT_API_VERSION

    @property
    def on_tv(self) -> bool:
        """Whether the game is currently running on a TV."""
        assert isinstance(self._env['on_tv'], bool)
        return self._env['on_tv']

    @property
    def vr_mode(self) -> bool:
        """Whether the game is currently running in VR."""
        assert isinstance(self._env['vr_mode'], bool)
        return self._env['vr_mode']

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

        # Config.
        self.config_file_healthy = False

        # This is incremented any time the app is backgrounded/foregrounded;
        # can be a simple way to determine if network data should be
        # refreshed/etc.
        self.fg_state = 0

        self._env = _ba.env()
        self.protocol_version: int = self._env['protocol_version']
        assert isinstance(self.protocol_version, int)
        self.toolbar_test: bool = self._env['toolbar_test']
        assert isinstance(self.toolbar_test, bool)
        self.demo_mode: bool = self._env['demo_mode']
        assert isinstance(self.demo_mode, bool)
        self.arcade_mode: bool = self._env['arcade_mode']
        assert isinstance(self.arcade_mode, bool)
        self.headless_mode: bool = self._env['headless_mode']
        assert isinstance(self.headless_mode, bool)
        self.iircade_mode: bool = self._env['iircade_mode']
        assert isinstance(self.iircade_mode, bool)
        self.allow_ticket_purchases: bool = not self.iircade_mode

        # Misc.
        self.tips: List[str] = []
        self.stress_test_reset_timer: Optional[ba.Timer] = None
        self.did_weak_call_warning = False
        self.ran_on_app_launch = False

        self.log_have_new = False
        self.log_upload_timer_started = False
        self._config: Optional[ba.AppConfig] = None
        self.printed_live_object_warning = False

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

        self.meta = MetadataSubsystem()
        self.accounts = AccountSubsystem()
        self.plugins = PluginSubsystem()
        self.music = MusicSubsystem()
        self.lang = LanguageSubsystem()
        self.ach = AchievementSubsystem()
        self.ui = UISubsystem()
        self.ads = AdsSubsystem()

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

        self.value_test_defaults: dict = {}
        self.first_main_menu = True  # FIXME: Move to mainmenu class.
        self.did_menu_intro = False  # FIXME: Move to mainmenu class.
        self.main_menu_window_refresh_check_count = 0  # FIXME: Mv to mainmenu.
        self.main_menu_resume_callbacks: list = []  # Can probably go away.
        self.special_offer: Optional[Dict] = None
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
        from ba import _apputils
        from ba import _appconfig
        from ba import _achievement
        from ba import _map
        from ba import _campaign
        from bastd import appdelegate
        from bastd import maps as stdmaps
        from bastd.actor import spazappearance
        from ba._enums import TimeType

        cfg = self.config

        self.delegate = appdelegate.AppDelegate()

        self.ui.on_app_launch()

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
                      lambda: _ba.screenmessage(
                          'Note: using local server',
                          (1, 1, 0),
                          log=True,
                      ),
                      timetype=TimeType.REAL)
        elif 'test' in server_addr:
            _ba.timer(2.0,
                      lambda: _ba.screenmessage(
                          'Note: using test server-module',
                          (1, 1, 0),
                          log=True,
                      ),
                      timetype=TimeType.REAL)

        cfg['launchCount'] = launch_count
        cfg.commit()

        # Run a test in a few seconds to see if we should pop up an existing
        # pending special offer.
        def check_special_offer() -> None:
            from bastd.ui.specialoffer import show_offer
            config = self.config
            if ('pendingSpecialOffer' in config and _ba.get_public_login_id()
                    == config['pendingSpecialOffer']['a']):
                self.special_offer = config['pendingSpecialOffer']['o']
                show_offer()

        if not self.headless_mode:
            _ba.timer(3.0, check_special_offer, timetype=TimeType.REAL)

        self.meta.on_app_launch()
        self.accounts.on_app_launch()
        self.plugins.on_app_launch()

        self.ran_on_app_launch = True

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
        activity: Optional[ba.Activity] = _ba.get_foreground_host_activity()
        if (activity is not None and activity.allow_pausing
                and not _ba.have_connected_clients()):
            from ba import _gameutils
            from ba._language import Lstr
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
                    _ba.newnode('text',
                                attrs={
                                    'text': Lstr(resource='pausedByHostText'),
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

        self.fg_state += 1
        self.accounts.on_app_resume()
        self.music.on_app_resume()

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

    def on_app_shutdown(self) -> None:
        """(internal)"""
        self.music.on_app_shutdown()

    def handle_deep_link(self, url: str) -> None:
        """Handle a deep link URL."""
        from ba._language import Lstr
        appname = _ba.appname()
        if url.startswith(f'{appname}://code/'):
            code = url.replace(f'{appname}://code/', '')
            self.accounts.add_pending_promo_code(code)
        else:
            _ba.screenmessage(Lstr(resource='errorText'), color=(1, 0, 0))
            _ba.playsound(_ba.getsound('error'))

    def _test_https(self) -> None:
        """Testing https support.

        (would be nice to get this working on our custom Python builds; need
        to wrangle certificates somehow).
        """
        import urllib.request
        try:
            val = urllib.request.urlopen('https://example.com').read()
            print('HTTPS TEST SUCCESS', len(val))
        except Exception as exc:
            print('HTTPS TEST FAIL:', exc)
