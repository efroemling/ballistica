# Released under the MIT License. See LICENSE for details.
#
"""Provides classic app subsystem."""
from __future__ import annotations

import random
import logging
import weakref
from typing import TYPE_CHECKING, override, assert_never

from efro.dataclassio import dataclass_from_dict
import babase
import bauiv1
import bascenev1

import _baclassic
from baclassic._music import MusicSubsystem
from baclassic._accountv1 import AccountV1Subsystem
from baclassic._ads import AdsSubsystem
from baclassic._net import MasterServerResponseType, MasterServerV1CallThread
from baclassic._achievement import AchievementSubsystem
from baclassic._tips import get_all_tips
from baclassic._store import StoreSubsystem
from baclassic import _input

if TYPE_CHECKING:
    from typing import Callable, Any, Sequence

    import bacommon.bs
    from bascenev1lib.actor import spazappearance
    from bauiv1lib.party import PartyWindow

    from baclassic._servermode import ServerController
    from baclassic._net import MasterServerCallback


class ClassicAppSubsystem(babase.AppSubsystem):
    """Subsystem for classic functionality in the app.

    The single shared instance of this app can be accessed at
    babase.app.classic. Note that it is possible for babase.app.classic to
    be None if the classic package is not present, and code should handle
    that case gracefully.
    """

    # pylint: disable=too-many-public-methods

    # noinspection PyUnresolvedReferences
    from baclassic._music import MusicPlayMode

    def __init__(self) -> None:
        super().__init__()
        self._env = babase.env()

        self.accounts = AccountV1Subsystem()
        self.ads = AdsSubsystem()
        self.ach = AchievementSubsystem()
        self.store = StoreSubsystem()
        self.music = MusicSubsystem()

        # Co-op Campaigns.
        self.campaigns: dict[str, bascenev1.Campaign] = {}
        self.custom_coop_practice_games: list[str] = []

        # Lobby.
        self.lobby_random_profile_index: int = 1
        self.lobby_random_char_index_offset = random.randrange(1000)
        self.lobby_account_profile_device_id: int | None = None

        # Misc.
        self.tips: list[str] = []
        self.stress_test_update_timer: babase.AppTimer | None = None
        self.stress_test_update_timer_2: babase.AppTimer | None = None
        self.value_test_defaults: dict = {}
        self.special_offer: dict | None = None
        self.ping_thread_count = 0
        self.allow_ticket_purchases: bool = True

        # Main Menu.
        self.main_menu_did_initial_transition = False
        self.main_menu_last_news_fetch_time: float | None = None

        # Spaz.
        self.spaz_appearances: dict[str, spazappearance.Appearance] = {}
        self.last_spaz_turbo_warn_time = babase.AppTime(-99999.0)

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
        self.teams_series_length = 7  # deprecated, left for old mods
        self.ffa_series_length = 24  # deprecated, left for old mods
        self.coop_session_args: dict = {}

        # UI.
        self.first_main_menu = True  # FIXME: Move to mainmenu class.
        self.did_menu_intro = False  # FIXME: Move to mainmenu class.
        self.main_menu_window_refresh_check_count = 0  # FIXME: Mv to mainmenu.
        self.invite_confirm_windows: list[Any] = []  # FIXME: Don't use Any.
        self.party_window: weakref.ref[PartyWindow] | None = None
        self.main_menu_resume_callbacks: list = []
        self.saved_ui_state: bauiv1.MainWindowState | None = None

        # Store.
        self.store_layout: dict[str, list[dict[str, Any]]] | None = None
        self.store_items: dict[str, dict] | None = None
        self.pro_sale_start_time: int | None = None
        self.pro_sale_start_val: int | None = None

    def add_main_menu_close_callback(self, call: Callable[[], Any]) -> None:
        """(internal)"""

        # If there's no main window up, just call immediately.
        if not babase.app.ui_v1.has_main_window():
            with babase.ContextRef.empty():
                call()
        else:
            self.main_menu_resume_callbacks.append(call)

    @property
    def platform(self) -> str:
        """Name of the current platform.

        Examples are: 'mac', 'windows', android'.
        """
        assert isinstance(self._env['platform'], str)
        return self._env['platform']

    def scene_v1_protocol_version(self) -> int:
        """(internal)"""
        return bascenev1.protocol_version()

    @property
    def subplatform(self) -> str:
        """String for subplatform.

        Can be empty. For the 'android' platform, subplatform may
        be 'google', 'amazon', etc.
        """
        assert isinstance(self._env['subplatform'], str)
        return self._env['subplatform']

    @property
    def legacy_user_agent_string(self) -> str:
        """String containing various bits of info about OS/device/etc."""
        assert isinstance(self._env['legacy_user_agent_string'], str)
        return self._env['legacy_user_agent_string']

    @override
    def on_app_loading(self) -> None:
        from bascenev1lib.actor import spazappearance
        from bascenev1lib import maps as stdmaps

        plus = babase.app.plus
        assert plus is not None

        env = babase.app.env
        cfg = babase.app.config

        self.music.on_app_loading()

        # Non-test, non-debug builds should generally be blessed; warn if not.
        # (so I don't accidentally release a build that can't play tourneys)
        if not env.debug and not env.test and not plus.is_blessed():
            babase.screenmessage('WARNING: NON-BLESSED BUILD', color=(1, 0, 0))

        stdmaps.register_all_maps()

        spazappearance.register_appearances()
        bascenev1.init_campaigns()

        launch_count = cfg.get('launchCount', 0)
        launch_count += 1

        # So we know how many times we've run the game at various
        # version milestones.
        for key in ('lc14173', 'lc14292'):
            cfg.setdefault(key, launch_count)

        cfg['launchCount'] = launch_count
        cfg.commit()

        # If there's a leftover log file, attempt to upload it to the
        # master-server and/or get rid of it.
        babase.handle_leftover_v1_cloud_log_file()

        self.accounts.on_app_loading()

    @override
    def on_app_suspend(self) -> None:
        self.accounts.on_app_suspend()

    @override
    def on_app_unsuspend(self) -> None:
        self.accounts.on_app_unsuspend()
        self.music.on_app_unsuspend()

    @override
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
            from babase import Lstr
            from bascenev1 import NodeActor

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
        from bauiv1lib.coop.level import CoopLevelLockedWindow

        assert babase.app.classic is not None

        if args is None:
            args = {}
        if game == '':
            raise ValueError('empty game name')
        campaignname, levelname = game.split(':')
        campaign = babase.app.classic.getcampaign(campaignname)

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

        # Save where we are in the UI to come back to when done.
        babase.app.classic.save_ui_state()

        # Ok, we're good to go.
        self.coop_session_args = {
            'campaign': campaignname,
            'level': levelname,
        }
        for arg_name, arg_val in list(args.items()):
            self.coop_session_args[arg_name] = arg_val

        def _fade_end() -> None:
            from bascenev1 import CoopSession

            try:
                bascenev1.new_host_session(CoopSession)
            except Exception:
                logging.exception('Error creating coopsession after fade end.')
                from bascenev1lib.mainmenu import MainMenuSession

                bascenev1.new_host_session(MainMenuSession)

        babase.fade_screen(False, endcall=_fade_end)
        return True

    def return_to_main_menu_session_gracefully(
        self, reset_ui: bool = True
    ) -> None:
        """Attempt to cleanly get back to the main menu."""
        # pylint: disable=cyclic-import
        from baclassic import _benchmark
        from bascenev1lib.mainmenu import MainMenuSession

        plus = babase.app.plus
        assert plus is not None

        if reset_ui:
            babase.app.ui_v1.clear_main_window()

        if isinstance(bascenev1.get_foreground_host_session(), MainMenuSession):
            # It may be possible we're on the main menu but the screen is faded
            # so fade back in.
            babase.fade_screen(True)
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
            babase.pushcall(
                babase.Call(bascenev1.new_host_session, MainMenuSession)
            )

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

    def game_begin_analytics(self) -> None:
        """(internal)"""
        from baclassic import _analytics

        _analytics.game_begin_analytics()

    @classmethod
    def json_prep(cls, data: Any) -> Any:
        """Return a json-friendly version of the provided data.

        This converts any tuples to lists and any bytes to strings
        (interpreted as utf-8, ignoring errors). Logs errors (just once)
        if any data is modified/discarded/unsupported.
        """

        if isinstance(data, dict):
            return dict(
                (cls.json_prep(key), cls.json_prep(value))
                for key, value in list(data.items())
            )
        if isinstance(data, list):
            return [cls.json_prep(element) for element in data]
        if isinstance(data, tuple):
            logging.exception('json_prep encountered tuple')
            return [cls.json_prep(element) for element in data]
        if isinstance(data, bytes):
            try:
                return data.decode(errors='ignore')
            except Exception:
                logging.exception('json_prep encountered utf-8 decode error')
                return data.decode(errors='ignore')
        if not isinstance(data, (str, float, bool, type(None), int)):
            logging.exception(
                'got unsupported type in json_prep: %s', type(data)
            )
        return data

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

    def set_tournament_prize_image(
        self, entry: dict[str, Any], index: int, image: bauiv1.Widget
    ) -> None:
        """Given a tournament entry, return strings for its prize levels."""
        from baclassic import _tournament

        return _tournament.set_tournament_prize_chest_image(entry, index, image)

    def create_in_game_tournament_prize_image(
        self,
        entry: dict[str, Any],
        index: int,
        position: tuple[float, float],
    ) -> None:
        """Given a tournament entry, return strings for its prize levels."""
        from baclassic import _tournament

        _tournament.create_in_game_tournament_prize_image(
            entry, index, position
        )

    def get_tournament_prize_strings(
        self, entry: dict[str, Any], include_tickets: bool
    ) -> list[str]:
        """Given a tournament entry, return strings for its prize levels."""
        from baclassic import _tournament

        return _tournament.get_tournament_prize_strings(
            entry, include_tickets=include_tickets
        )

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

    def run_cpu_benchmark(self) -> None:
        """Kick off a benchmark to test cpu speeds."""
        from baclassic._benchmark import run_cpu_benchmark

        run_cpu_benchmark()

    def run_media_reload_benchmark(self) -> None:
        """Kick off a benchmark to test media reloading speeds."""
        from baclassic._benchmark import run_media_reload_benchmark

        run_media_reload_benchmark()

    def run_stress_test(
        self,
        *,
        playlist_type: str = 'Random',
        playlist_name: str = '__default__',
        player_count: int = 8,
        round_duration: int = 30,
        attract_mode: bool = False,
    ) -> None:
        """Run a stress test."""
        from baclassic._benchmark import run_stress_test

        run_stress_test(
            playlist_type=playlist_type,
            playlist_name=playlist_name,
            player_count=player_count,
            round_duration=round_duration,
            attract_mode=attract_mode,
        )

    def get_input_device_mapped_value(
        self,
        device: bascenev1.InputDevice,
        name: str,
        default: bool = False,
    ) -> Any:
        """Return a mapped value for an input device.

        This checks the user config and falls back to default values
        where available.
        """
        return _input.get_input_device_mapped_value(
            device.name, device.unique_identifier, name, default
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
        return bascenev1.get_player_colors()

    def get_player_profile_icon(self, profilename: str) -> str:
        """Given a profile name, returns an icon string for it.

        (non-account profiles only)
        """
        return bascenev1.get_player_profile_icon(profilename)

    def get_player_profile_colors(
        self,
        profilename: str | None,
        profiles: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Given a profile, return colors for them."""
        return bascenev1.get_player_profile_colors(profilename, profiles)

    def get_foreground_host_session(self) -> bascenev1.Session | None:
        """(internal)"""
        return bascenev1.get_foreground_host_session()

    def get_foreground_host_activity(self) -> bascenev1.Activity | None:
        """(internal)"""
        return bascenev1.get_foreground_host_activity()

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
        bascenev1.set_master_server_source(source)

    def get_game_port(self) -> int:
        """(internal)"""
        return bascenev1.get_game_port()

    def v2_upgrade_window(self, login_name: str, code: str) -> None:
        """(internal)"""

        from bauiv1lib.v2upgrade import V2UpgradeWindow

        V2UpgradeWindow(login_name, code)

    def account_link_code_window(self, data: dict[str, Any]) -> None:
        """(internal)"""
        from bauiv1lib.account.link import AccountLinkCodeWindow

        AccountLinkCodeWindow(data)

    def server_dialog(self, delay: float, data: dict[str, Any]) -> None:
        """(internal)"""
        from bauiv1lib.serverdialog import (
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
            babase.apptimer(
                delay,
                babase.Call(ServerDialogWindow, sddata),
            )

    # def root_ui_ticket_icon_press(self) -> None:
    #     """(internal)"""
    #     from bauiv1lib.resourcetypeinfo import ResourceTypeInfoWindow

    #     ResourceTypeInfoWindow(
    #         origin_widget=bauiv1.get_special_widget('tickets_meter')
    #     )

    def show_url_window(self, address: str) -> None:
        """(internal)"""
        from bauiv1lib.url import ShowURLWindow

        ShowURLWindow(address)

    def quit_window(self, quit_type: babase.QuitType) -> None:
        """(internal)"""
        from bauiv1lib.confirm import QuitWindow

        QuitWindow(quit_type)

    def tournament_entry_window(
        self,
        tournament_id: str,
        *,
        tournament_activity: bascenev1.Activity | None = None,
        position: tuple[float, float] = (0.0, 0.0),
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        on_close_call: Callable[[], Any] | None = None,
    ) -> None:
        """(internal)"""
        from bauiv1lib.tournamententry import TournamentEntryWindow

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
        from bascenev1lib.mainmenu import MainMenuSession

        return MainMenuSession

    def profile_browser_window(
        self,
        transition: str = 'in_right',
        origin_widget: bauiv1.Widget | None = None,
        # in_main_menu: bool = True,
        selected_profile: str | None = None,
    ) -> None:
        """(internal)"""
        from bauiv1lib.profile.browser import ProfileBrowserWindow

        main_window = babase.app.ui_v1.get_main_window()
        if main_window is not None:
            logging.warning(
                'profile_browser_window()'
                ' called with existing main window; should not happen.'
            )
            return

        babase.app.ui_v1.set_main_window(
            ProfileBrowserWindow(
                transition=transition,
                selected_profile=selected_profile,
                origin_widget=origin_widget,
                minimal_toolbar=True,
            ),
            is_top_level=True,
            suppress_warning=True,
        )

    def preload_map_preview_media(self) -> None:
        """Preload media needed for map preview UIs.

        Category: **Asset Functions**
        """
        try:
            bauiv1.getmesh('level_select_button_opaque')
            bauiv1.getmesh('level_select_button_transparent')
            for maptype in list(self.maps.values()):
                map_tex_name = maptype.get_preview_texture_name()
                if map_tex_name is not None:
                    bauiv1.gettexture(map_tex_name)
        except Exception:
            logging.exception('Error preloading map preview media.')

    def party_icon_activate(self, origin: Sequence[float]) -> None:
        """(internal)"""
        from bauiv1lib.party import PartyWindow
        from babase import app

        assert app.env.gui

        # Play explicit swish sound so it occurs due to keypresses/etc.
        # This means we have to disable it for any button or else we get
        # double.
        bauiv1.getsound('swish').play()

        # If it exists, dismiss it; otherwise make a new one.
        party_window = (
            None if self.party_window is None else self.party_window()
        )
        if party_window is not None:
            party_window.close()
        else:
            self.party_window = weakref.ref(PartyWindow(origin=origin))

    def device_menu_press(self, device_id: int | None) -> None:
        """(internal)"""
        from bauiv1lib.ingamemenu import InGameMenuWindow
        from bauiv1 import set_ui_input_device

        assert babase.app is not None
        in_main_menu = babase.app.ui_v1.has_main_window()
        if not in_main_menu:
            set_ui_input_device(device_id)

            # Hack(ish). We play swish sound here so it happens for
            # device presses, but this means we need to disable default
            # swish sounds for any menu buttons or we'll get double.
            if babase.app.env.gui:
                bauiv1.getsound('swish').play()

            babase.app.ui_v1.set_main_window(
                InGameMenuWindow(), is_top_level=True, suppress_warning=True
            )

    def save_ui_state(self) -> None:
        """Store our current place in the UI."""
        ui = babase.app.ui_v1
        mainwindow = ui.get_main_window()
        if mainwindow is not None:
            self.saved_ui_state = ui.save_main_window_state(mainwindow)
        else:
            self.saved_ui_state = None

    def invoke_main_menu_ui(self) -> None:
        """Bring up main menu ui."""

        # Bring up the last place we were, or start at the main menu
        # otherwise.
        app = bauiv1.app
        env = app.env
        with bascenev1.ContextRef.empty():
            # from bauiv1lib import specialoffer

            assert app.classic is not None
            if app.env.headless:
                # UI stuff fails now in headless builds; avoid it.
                pass
            else:

                # When coming back from a kiosk-mode game, jump to the
                # kiosk start screen.
                if env.demo or env.arcade:
                    # pylint: disable=cyclic-import
                    from bauiv1lib.kiosk import KioskWindow

                    app.ui_v1.set_main_window(
                        KioskWindow(), is_top_level=True, suppress_warning=True
                    )
                else:
                    # If there's a saved ui state, restore that.
                    if self.saved_ui_state is not None:
                        app.ui_v1.restore_main_window_state(self.saved_ui_state)
                    else:
                        # Otherwise start fresh at the main menu.
                        from bauiv1lib.mainmenu import MainMenuWindow

                        app.ui_v1.set_main_window(
                            MainMenuWindow(transition=None),
                            is_top_level=True,
                            suppress_warning=True,
                        )

    @staticmethod
    def run_bs_client_effects(effects: list[bacommon.bs.ClientEffect]) -> None:
        """Run client effects sent from the master server."""
        from baclassic._clienteffect import run_bs_client_effects

        run_bs_client_effects(effects)

    @staticmethod
    def basic_client_ui_button_label_str(
        label: bacommon.bs.BasicClientUI.ButtonLabel,
    ) -> babase.Lstr:
        """Given a client-ui label, return an Lstr."""
        import bacommon.bs

        cls = bacommon.bs.BasicClientUI.ButtonLabel
        if label is cls.UNKNOWN:
            # Server should not be sending us unknown stuff; make noise
            # if they do.
            logging.error(
                'Got BasicClientUI.ButtonLabel.UNKNOWN; should not happen.'
            )
            return babase.Lstr(value='<error>')

        rsrc: str | None = None
        if label is cls.OK:
            rsrc = 'okText'
        elif label is cls.APPLY:
            rsrc = 'applyText'
        elif label is cls.CANCEL:
            rsrc = 'cancelText'
        elif label is cls.ACCEPT:
            rsrc = 'gatherWindow.partyInviteAcceptText'
        elif label is cls.DECLINE:
            rsrc = 'gatherWindow.partyInviteDeclineText'
        elif label is cls.IGNORE:
            rsrc = 'gatherWindow.partyInviteIgnoreText'
        elif label is cls.CLAIM:
            rsrc = 'claimText'
        elif label is cls.DISCARD:
            rsrc = 'discardText'
        else:
            assert_never(label)

        return babase.Lstr(resource=rsrc)
