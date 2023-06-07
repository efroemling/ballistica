# Released under the MIT License. See LICENSE for details.
#
"""Provides classic app subsystem."""
from __future__ import annotations

import random
import weakref
import logging
from typing import TYPE_CHECKING

from efro.dataclassio import dataclass_from_dict
import _babase
import _bauiv1
import _bascenev1
import bascenev1
from babase._general import Call
from babase._appsubsystem import AppSubsystem
from babase._general import AppTime
from bascenev1 import _profile
import _baclassic
from baclassic._music import MusicSubsystem
from baclassic._accountv1 import AccountV1Subsystem
from baclassic._ads import AdsSubsystem
from baclassic._net import MasterServerResponseType, MasterServerV1CallThread
from baclassic._achievement import AchievementSubsystem
from baclassic._tips import get_all_tips
from baclassic._store import StoreSubsystem
from baclassic._ui import UISubsystem
from baclassic import _input

if TYPE_CHECKING:
    from typing import Callable, Any, Sequence

    import babase
    import bauiv1
    import baclassic
    from bastd.actor import spazappearance
    from baclassic._appdelegate import AppDelegate
    from baclassic._servermode import ServerController
    from baclassic._net import MasterServerCallback


class ClassicSubsystem(AppSubsystem):
    """Subsystem for classic functionality in the app.

    The single shared instance of this app can be accessed at
    babase.app.classic. Note that it is possible for babase.app.classic to
    be None if the classic package is not present, and code should handle
    that case gracefully.
    """

    # pylint: disable=too-many-public-methods

    # Note: we pull the same things in here that are exposed in
    # baclassic/__init__.py. This way this version can be used for
    # runtime via babase.app.classic which enforces handling of the
    # package-not-present case.
    from bascenev1._level import Level
    from bascenev1._campaign import Campaign
    from bascenev1._lobby import Lobby, Chooser
    from baclassic._music import MusicPlayMode  # FIXME move 2 subsys

    def __init__(self) -> None:
        super().__init__()
        self._env = _babase.env()

        self.accounts = AccountV1Subsystem()
        self.ads = AdsSubsystem()
        self.ach = AchievementSubsystem()
        self.store = StoreSubsystem()
        self.music = MusicSubsystem()
        self.ui = UISubsystem()

        # Co-op Campaigns.
        self.campaigns: dict[str, bascenev1.Campaign] = {}
        self.custom_coop_practice_games: list[str] = []

        # Lobby.
        self.lobby_random_profile_index: int = 1
        self.lobby_random_char_index_offset = random.randrange(1000)
        self.lobby_account_profile_device_id: int | None = None

        # Misc.
        self.tips: list[str] = []
        self.stress_test_reset_timer: babase.AppTimer | None = None
        self.value_test_defaults: dict = {}
        self.special_offer: dict | None = None
        self.ping_thread_count = 0
        self.allow_ticket_purchases: bool = not _babase.app.iircade_mode

        # Main Menu.
        self.main_menu_did_initial_transition = False
        self.main_menu_last_news_fetch_time: float | None = None

        # Spaz.
        self.spaz_appearances: dict[str, spazappearance.Appearance] = {}
        self.last_spaz_turbo_warn_time = AppTime(-99999.0)

        # Server Mode.
        self.server: ServerController | None = None

        self.log_have_new = False
        self.log_upload_timer_started = False
        self.printed_live_object_warning = False

        # We include this extra hash with shared input-mapping names so
        # that we don't share mappings between differently-configured
        # systems. For instance, different android devices may give different
        # key values for the same controller type so we keep their mappings
        # distinct.
        self.input_map_hash: str | None = None

        # Maps.
        self.maps: dict[str, type[bascenev1.Map]] = {}

        # Gameplay.
        self.teams_series_length = 7
        self.ffa_series_length = 24
        self.coop_session_args: dict = {}

        # UI.
        self.first_main_menu = True  # FIXME: Move to mainmenu class.
        self.did_menu_intro = False  # FIXME: Move to mainmenu class.
        self.main_menu_window_refresh_check_count = 0  # FIXME: Mv to mainmenu.
        self.main_menu_resume_callbacks: list = []  # Can probably go away.
        self.invite_confirm_windows: list[Any] = []  # FIXME: Don't use Any.
        self.delegate: AppDelegate | None = None

        # Store.
        self.store_layout: dict[str, list[dict[str, Any]]] | None = None
        self.store_items: dict[str, dict] | None = None
        self.pro_sale_start_time: int | None = None
        self.pro_sale_start_val: int | None = None

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
    def user_agent_string(self) -> str:
        """String containing various bits of info about OS/device/etc."""
        assert isinstance(self._env['user_agent_string'], str)
        return self._env['user_agent_string']

    def add_main_menu_close_callback(self, call: Callable[[], Any]) -> None:
        """(internal)"""

        # If there's no main menu up, just call immediately.
        if not self.ui.has_main_menu_window():
            with _babase.ContextRef.empty():
                call()
        else:
            self.main_menu_resume_callbacks.append(call)

    def on_app_launching(self) -> None:
        """Called when the app is first entering the launching state."""
        # pylint: disable=too-many-locals
        from bascenev1 import _campaign
        from bascenev1 import _map
        from bastd.actor import spazappearance
        from bastd import maps as stdmaps
        from babase._apputils import handle_leftover_v1_cloud_log_file
        from baclassic._appdelegate import AppDelegate
        import bauiv1 as bui

        plus = bui.app.plus
        assert plus is not None

        cfg = _babase.app.config

        self.ui.on_app_launching()
        self.music.on_app_launching()

        self.delegate = AppDelegate()

        # Non-test, non-debug builds should generally be blessed; warn if not.
        # (so I don't accidentally release a build that can't play tourneys)
        if (
            not _babase.app.debug_build
            and not _babase.app.test_build
            and not plus.is_blessed()
        ):
            _babase.screenmessage('WARNING: NON-BLESSED BUILD', color=(1, 0, 0))

        # FIXME: This should not be hard-coded.
        for maptype in [
            stdmaps.HockeyStadium,
            stdmaps.FootballStadium,
            stdmaps.Bridgit,
            stdmaps.BigG,
            stdmaps.Roundabout,
            stdmaps.MonkeyFace,
            stdmaps.ZigZag,
            stdmaps.ThePad,
            stdmaps.DoomShroom,
            stdmaps.LakeFrigid,
            stdmaps.TipTop,
            stdmaps.CragCastle,
            stdmaps.TowerD,
            stdmaps.HappyThoughts,
            stdmaps.StepRightUp,
            stdmaps.Courtyard,
            stdmaps.Rampage,
        ]:
            _map.register_map(maptype)

        spazappearance.register_appearances()
        _campaign.init_campaigns()

        launch_count = cfg.get('launchCount', 0)
        launch_count += 1

        # So we know how many times we've run the game at various
        # version milestones.
        for key in ('lc14173', 'lc14292'):
            cfg.setdefault(key, launch_count)

        cfg['launchCount'] = launch_count
        cfg.commit()

        # Run a test in a few seconds to see if we should pop up an existing
        # pending special offer.
        def check_special_offer() -> None:
            plus = bui.app.plus
            assert plus is not None

            from bastd.ui.specialoffer import show_offer

            if (
                'pendingSpecialOffer' in cfg
                and plus.get_v1_account_public_login_id()
                == cfg['pendingSpecialOffer']['a']
            ):
                self.special_offer = cfg['pendingSpecialOffer']['o']
                show_offer()

        if not _babase.app.headless_mode:
            bui.apptimer(3.0, check_special_offer)

        # If there's a leftover log file, attempt to upload it to the
        # master-server and/or get rid of it.
        handle_leftover_v1_cloud_log_file()

        self.accounts.on_app_launching()

    def on_app_pause(self) -> None:
        self.accounts.on_app_pause()

    def on_app_resume(self) -> None:
        self.accounts.on_app_resume()
        self.music.on_app_resume()

    def on_app_shutdown(self) -> None:
        self.music.on_app_shutdown()

    def pause(self) -> None:
        """Pause the game due to a user request or menu popping up.

        If there's a foreground host-activity that says it's pausable, tell it
        to pause. Note: we now no longer pause if there are connected clients.
        """
        activity: bascenev1.Activity | None = (
            bascenev1.get_foreground_host_activity()
        )
        if (
            activity is not None
            and activity.allow_pausing
            and not bascenev1.have_connected_clients()
        ):
            from babase._language import Lstr
            from bascenev1._nodeactor import NodeActor

            # FIXME: Shouldn't be touching scene stuff here;
            #  should just pass the request on to the host-session.
            with activity.context:
                globs = activity.globalsnode
                if not globs.paused:
                    bascenev1.getsound('refWhistle').play()
                    globs.paused = True

                # FIXME: This should not be an attr on Actor.
                activity.paused_text = NodeActor(
                    bascenev1.newnode(
                        'text',
                        attrs={
                            'text': Lstr(resource='pausedByHostText'),
                            'client_only': True,
                            'flatness': 1.0,
                            'h_align': 'center',
                        },
                    )
                )

    def resume(self) -> None:
        """Resume the game due to a user request or menu closing.

        If there's a foreground host-activity that's currently paused, tell it
        to resume.
        """

        # FIXME: Shouldn't be touching scene stuff here;
        #  should just pass the request on to the host-session.
        activity = bascenev1.get_foreground_host_activity()
        if activity is not None:
            with activity.context:
                globs = activity.globalsnode
                if globs.paused:
                    bascenev1.getsound('refWhistle').play()
                    globs.paused = False

                    # FIXME: This should not be an actor attr.
                    activity.paused_text = None

    def add_coop_practice_level(self, level: bascenev1.Level) -> None:
        """Adds an individual level to the 'practice' section in Co-op."""

        # Assign this level to our catch-all campaign.
        self.campaigns['Challenges'].addlevel(level)

        # Make note to add it to our challenges UI.
        self.custom_coop_practice_games.append(f'Challenges:{level.name}')

    def launch_coop_game(
        self, game: str, force: bool = False, args: dict | None = None
    ) -> bool:
        """High level way to launch a local co-op session."""
        # pylint: disable=cyclic-import
        from bastd.ui.coop.level import CoopLevelLockedWindow

        assert _babase.app.classic is not None

        if args is None:
            args = {}
        if game == '':
            raise ValueError('empty game name')
        campaignname, levelname = game.split(':')
        campaign = _babase.app.classic.getcampaign(campaignname)

        # If this campaign is sequential, make sure we've completed the
        # one before this.
        if campaign.sequential and not force:
            for level in campaign.levels:
                if level.name == levelname:
                    break
                if not level.complete:
                    CoopLevelLockedWindow(
                        campaign.getlevel(levelname).displayname,
                        campaign.getlevel(level.name).displayname,
                    )
                    return False

        # Ok, we're good to go.
        self.coop_session_args = {
            'campaign': campaignname,
            'level': levelname,
        }
        for arg_name, arg_val in list(args.items()):
            self.coop_session_args[arg_name] = arg_val

        def _fade_end() -> None:
            from bascenev1 import _coopsession

            try:
                bascenev1.new_host_session(_coopsession.CoopSession)
            except Exception:
                logging.exception('Error creating coopsession after fade end.')
                from bastd.mainmenu import MainMenuSession

                bascenev1.new_host_session(MainMenuSession)

        _babase.fade_screen(False, endcall=_fade_end)
        return True

    def return_to_main_menu_session_gracefully(
        self, reset_ui: bool = True
    ) -> None:
        """Attempt to cleanly get back to the main menu."""
        # pylint: disable=cyclic-import
        from baclassic import _benchmark
        from bastd.mainmenu import MainMenuSession

        plus = _babase.app.plus
        assert plus is not None

        if reset_ui:
            self.ui.clear_main_menu_window()

        if isinstance(bascenev1.get_foreground_host_session(), MainMenuSession):
            # It may be possible we're on the main menu but the screen is faded
            # so fade back in.
            _babase.fade_screen(True)
            return

        _benchmark.stop_stress_test()  # Stop stress-test if in progress.

        # If we're in a host-session, tell them to end.
        # This lets them tear themselves down gracefully.
        host_session: bascenev1.Session | None = (
            bascenev1.get_foreground_host_session()
        )
        if host_session is not None:
            # Kick off a little transaction so we'll hopefully have all the
            # latest account state when we get back to the menu.
            plus.add_v1_account_transaction(
                {'type': 'END_SESSION', 'sType': str(type(host_session))}
            )
            plus.run_v1_account_transactions()

            host_session.end()

        # Otherwise just force the issue.
        else:
            _babase.pushcall(Call(bascenev1.new_host_session, MainMenuSession))

    def getmaps(self, playtype: str) -> list[str]:
        """Return a list of bascenev1.Map types supporting a playtype str.

        Category: **Asset Functions**

        Maps supporting a given playtype must provide a particular set of
        features and lend themselves to a certain style of play.

        Play Types:

        'melee'
          General fighting map.
          Has one or more 'spawn' locations.

        'team_flag'
          For games such as Capture The Flag where each team spawns by a flag.
          Has two or more 'spawn' locations, each with a corresponding 'flag'
          location (based on index).

        'single_flag'
          For games such as King of the Hill or Keep Away where multiple teams
          are fighting over a single flag.
          Has two or more 'spawn' locations and 1 'flag_default' location.

        'conquest'
          For games such as Conquest where flags are spread throughout the map
          - has 2+ 'flag' locations, 2+ 'spawn_by_flag' locations.

        'king_of_the_hill' - has 2+ 'spawn' locations,
           1+ 'flag_default' locations, and 1+ 'powerup_spawn' locations

        'hockey'
          For hockey games.
          Has two 'goal' locations, corresponding 'spawn' locations, and one
          'flag_default' location (for where puck spawns)

        'football'
          For football games.
          Has two 'goal' locations, corresponding 'spawn' locations, and one
          'flag_default' location (for where flag/ball/etc. spawns)

        'race'
          For racing games where players much touch each region in order.
          Has two or more 'race_point' locations.
        """
        return sorted(
            key
            for key, val in self.maps.items()
            if playtype in val.get_play_types()
        )

    def show_online_score_ui(
        self,
        show: str = 'general',
        game: str | None = None,
        game_version: str | None = None,
    ) -> None:
        """(internal)"""
        _bauiv1.show_online_score_ui(show, game, game_version)

    def game_begin_analytics(self) -> None:
        """(internal)"""
        from baclassic import _analytics

        _analytics.game_begin_analytics()

    def master_server_v1_get(
        self,
        request: str,
        data: dict[str, Any],
        callback: MasterServerCallback | None = None,
        response_type: MasterServerResponseType = MasterServerResponseType.JSON,
    ) -> None:
        """Make a call to the master server via a http GET."""

        MasterServerV1CallThread(
            request, 'get', data, callback, response_type
        ).start()

    def master_server_v1_post(
        self,
        request: str,
        data: dict[str, Any],
        callback: MasterServerCallback | None = None,
        response_type: MasterServerResponseType = MasterServerResponseType.JSON,
    ) -> None:
        """Make a call to the master server via a http POST."""
        MasterServerV1CallThread(
            request, 'post', data, callback, response_type
        ).start()

    def get_tournament_prize_strings(self, entry: dict[str, Any]) -> list[str]:
        """Given a tournament entry, return strings for its prize levels."""
        from baclassic import _tournament

        return _tournament.get_tournament_prize_strings(entry)

    def getcampaign(self, name: str) -> bascenev1.Campaign:
        """Return a campaign by name."""
        return self.campaigns[name]

    def get_next_tip(self) -> str:
        """Returns the next tip to be displayed."""
        if not self.tips:
            for tip in get_all_tips():
                self.tips.insert(random.randint(0, len(self.tips)), tip)
        tip = self.tips.pop()
        return tip

    def run_gpu_benchmark(self) -> None:
        """Kick off a benchmark to test gpu speeds."""
        from baclassic._benchmark import run_gpu_benchmark as run

        run()

    def run_cpu_benchmark(self) -> None:
        """Kick off a benchmark to test cpu speeds."""
        from baclassic._benchmark import run_cpu_benchmark as run

        run()

    def run_media_reload_benchmark(self) -> None:
        """Kick off a benchmark to test media reloading speeds."""
        from baclassic._benchmark import run_media_reload_benchmark as run

        run()

    def run_stress_test(
        self,
        playlist_type: str = 'Random',
        playlist_name: str = '__default__',
        player_count: int = 8,
        round_duration: int = 30,
    ) -> None:
        """Run a stress test."""
        from baclassic._benchmark import run_stress_test as run

        run(playlist_type, playlist_name, player_count, round_duration)

    def get_input_device_mapped_value(
        self, device: bascenev1.InputDevice, name: str
    ) -> Any:
        """Returns a mapped value for an input device.

        This checks the user config and falls back to default values
        where available.
        """
        return _input.get_input_device_mapped_value(
            device.name, device.unique_identifier, name
        )

    def get_input_device_map_hash(
        self, inputdevice: bascenev1.InputDevice
    ) -> str:
        """Given an input device, return hash based on its raw input values."""
        del inputdevice  # unused currently
        return _input.get_input_device_map_hash()

    def get_input_device_config(
        self, inputdevice: bascenev1.InputDevice, default: bool
    ) -> tuple[dict, str]:
        """Given an input device, return its config dict in the app config.

        The dict will be created if it does not exist.
        """
        return _input.get_input_device_config(
            inputdevice.name, inputdevice.unique_identifier, default
        )

    def get_player_colors(self) -> list[tuple[float, float, float]]:
        """Return user-selectable player colors."""
        return _profile.get_player_colors()

    def get_player_profile_icon(self, profilename: str) -> str:
        """Given a profile name, returns an icon string for it.

        (non-account profiles only)
        """
        return _profile.get_player_profile_icon(profilename)

    def get_player_profile_colors(
        self,
        profilename: str | None,
        profiles: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Given a profile, return colors for them."""
        return _profile.get_player_profile_colors(profilename, profiles)

    def get_foreground_host_session(self) -> bascenev1.Session | None:
        """(internal)"""
        return bascenev1.get_foreground_host_session()

    def get_foreground_host_activity(self) -> bascenev1.Activity | None:
        """(internal)"""
        return bascenev1.get_foreground_host_activity()

    def show_config_error_window(self) -> bool:
        """(internal)"""
        if self.platform in ('mac', 'linux', 'windows'):
            from bastd.ui.configerror import ConfigErrorWindow

            _babase.pushcall(ConfigErrorWindow)
            return True
        return False

    def value_test(
        self,
        arg: str,
        change: float | None = None,
        absolute: float | None = None,
    ) -> float:
        """(internal)"""
        return _baclassic.value_test(arg, change, absolute)

    def set_master_server_source(self, source: int) -> None:
        """(internal)"""
        _bascenev1.set_master_server_source(source)

    def get_game_port(self) -> int:
        """(internal)"""
        return _bascenev1.get_game_port()

    def v2_upgrade_window(self, login_name: str, code: str) -> None:
        """(internal)"""

        from bastd.ui.v2upgrade import V2UpgradeWindow

        V2UpgradeWindow(login_name, code)

    def account_link_code_window(self, data: dict[str, Any]) -> None:
        """(internal)"""
        from bastd.ui.account.link import AccountLinkCodeWindow

        AccountLinkCodeWindow(data)

    def server_dialog(self, delay: float, data: dict[str, Any]) -> None:
        """(internal)"""
        from bastd.ui.serverdialog import (
            ServerDialogData,
            ServerDialogWindow,
        )

        try:
            sddata = dataclass_from_dict(ServerDialogData, data)
        except Exception:
            sddata = None
            logging.warning(
                'Got malformatted ServerDialogData: %s',
                data,
            )
        if sddata is not None:
            _babase.apptimer(
                delay,
                Call(ServerDialogWindow, sddata),
            )

    def ticket_icon_press(self) -> None:
        """(internal)"""
        from bastd.ui.resourcetypeinfo import ResourceTypeInfoWindow

        ResourceTypeInfoWindow(
            origin_widget=_bauiv1.get_special_widget('tickets_info_button')
        )

    def party_icon_activate(self, origin: Sequence[float]) -> None:
        """(internal)"""
        from bastd.ui.party import PartyWindow
        from babase import app

        assert not app.headless_mode

        _bauiv1.getsound('swish').play()

        # If it exists, dismiss it; otherwise make a new one.
        if (
            self.ui.party_window is not None
            and self.ui.party_window() is not None
        ):
            self.ui.party_window().close()
        else:
            self.ui.party_window = weakref.ref(PartyWindow(origin=origin))

    def device_menu_press(self, device_id: int | None) -> None:
        """(internal)"""
        from bastd.ui.mainmenu import MainMenuWindow
        from bauiv1 import set_ui_input_device

        assert _babase.app is not None
        in_main_menu = self.ui.has_main_menu_window()
        if not in_main_menu:
            set_ui_input_device(device_id)

            if not _babase.app.headless_mode:
                _bauiv1.getsound('swish').play()

            self.ui.set_main_menu_window(MainMenuWindow().get_root_widget())

    def show_url_window(self, address: str) -> None:
        """(internal)"""
        from bastd.ui.url import ShowURLWindow

        ShowURLWindow(address)

    def quit_window(self) -> None:
        """(internal)"""
        from bastd.ui.confirm import QuitWindow

        QuitWindow()

    def get_draw_score_screen_activity(self) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.drawscore import DrawScoreScreenActivity

        return DrawScoreScreenActivity

    def get_team_series_victory_score_screen_activity(
        self,
    ) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.multiteamvictory import (
            TeamSeriesVictoryScoreScreenActivity,
        )

        return TeamSeriesVictoryScoreScreenActivity

    def get_team_victory_score_screen_activity(
        self,
    ) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.dualteamscore import TeamVictoryScoreScreenActivity

        return TeamVictoryScoreScreenActivity

    def get_free_for_all_victory_score_screen_activity(
        self,
    ) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.freeforallvictory import (
            FreeForAllVictoryScoreScreenActivity,
        )

        return FreeForAllVictoryScoreScreenActivity

    def get_coop_join_activity(self) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.coopjoin import CoopJoinActivity

        return CoopJoinActivity

    def get_coop_score_screen(self) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.coopscore import CoopScoreScreen

        return CoopScoreScreen

    def get_multi_team_join_activity(self) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.activity.multiteamjoin import MultiTeamJoinActivity

        return MultiTeamJoinActivity

    def get_tutorial_activity(self) -> type[bascenev1.Activity]:
        """(internal)"""
        from bastd.tutorial import TutorialActivity

        return TutorialActivity

    def tournament_entry_window(
        self,
        tournament_id: str,
        tournament_activity: bascenev1.Activity | None = None,
        position: tuple[float, float] = (0.0, 0.0),
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        on_close_call: Callable[[], Any] | None = None,
    ) -> None:
        """(internal)"""
        from bastd.ui.tournamententry import TournamentEntryWindow

        TournamentEntryWindow(
            tournament_id,
            tournament_activity,
            position,
            delegate,
            scale,
            offset,
            on_close_call,
        )

    def get_main_menu_session(self) -> type[bascenev1.Session]:
        """(internal)"""
        from bastd.mainmenu import MainMenuSession

        return MainMenuSession

    def continues_window(
        self,
        activity: bascenev1.Activity,
        cost: int,
        continue_call: Callable[[], Any],
        cancel_call: Callable[[], Any],
    ) -> None:
        """(internal)"""
        from bastd.ui.continues import ContinuesWindow

        ContinuesWindow(activity, cost, continue_call, cancel_call)

    def profile_browser_window(
        self,
        transition: str = 'in_right',
        in_main_menu: bool = True,
        selected_profile: str | None = None,
        origin_widget: bauiv1.Widget | None = None,
    ) -> None:
        """(internal)"""
        from bastd.ui.profile.browser import ProfileBrowserWindow

        ProfileBrowserWindow(
            transition, in_main_menu, selected_profile, origin_widget
        )
