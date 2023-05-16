# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the high level state of the app."""
from __future__ import annotations

from enum import Enum
import logging
from typing import TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property

import _babase
from babase._language import LanguageSubsystem
from babase._plugin import PluginSubsystem
from babase._meta import MetadataSubsystem
from babase._net import NetworkSubsystem
from babase._workspace import WorkspaceSubsystem
from babase._appcomponent import AppComponentSubsystem

if TYPE_CHECKING:
    from typing import Any
    import asyncio

    from efro.log import LogHandler
    import babase
    from babase._cloud import CloudSubsystem
    from babase._accountv2 import AccountV2Subsystem
    from babase._apputils import AppHealthMonitor

    # Would autogen this begin
    from baclassic import ClassicSubsystem
    from baplus import PlusSubsystem

    # Would autogen this end


class App:
    """A class for high level app functionality and state.

    Category: **App Classes**

    Use babase.app to access the single shared instance of this class.

    Note that properties not documented here should be considered internal
    and subject to change without warning.
    """

    # pylint: disable=too-many-public-methods

    # Implementations for these will be filled in by internal libs.
    accounts: AccountV2Subsystem
    cloud: CloudSubsystem

    # log_handler: LogHandler
    health_monitor: AppHealthMonitor

    class State(Enum):
        """High level state the app can be in."""

        # The app launch process has not yet begun.
        INITIAL = 0

        # Our app subsystems are being inited but should not yet interact.
        LAUNCHING = 1

        # App subsystems are inited and interacting, but the app has not
        # yet embarked on a high level course of action. It is doing initial
        # account logins, workspace & asset downloads, etc. in order to
        # prepare for this.
        LOADING = 2

        # All pieces are in place and the app is now doing its thing.
        RUNNING = 3

        # The app is backgrounded or otherwise suspended.
        PAUSED = 4

        # The app is shutting down.
        SHUTTING_DOWN = 5

    @property
    def aioloop(self) -> asyncio.AbstractEventLoop:
        """The logic thread's asyncio event loop.

        This allow async tasks to be run in the logic thread.
        Note that, at this time, the asyncio loop is encapsulated
        and explicitly stepped by the engine's logic thread loop and
        thus things like asyncio.get_running_loop() will not return this
        loop from most places in the logic thread; only from within a
        task explicitly created in this loop.
        """
        assert self._aioloop is not None
        return self._aioloop

    @property
    def build_number(self) -> int:
        """Integer build number.

        This value increases by at least 1 with each release of the game.
        It is independent of the human readable babase.App.version string.
        """
        assert isinstance(self._env['build_number'], int)
        return self._env['build_number']

    @property
    def device_name(self) -> str:
        """Name of the device running the game."""
        assert isinstance(self._env['device_name'], str)
        return self._env['device_name']

    @property
    def config_file_path(self) -> str:
        """Where the game's config file is stored on disk."""
        assert isinstance(self._env['config_file_path'], str)
        return self._env['config_file_path']

    @property
    def version(self) -> str:
        """Human-readable version string; something like '1.3.24'.

        This should not be interpreted as a number; it may contain
        string elements such as 'alpha', 'beta', 'test', etc.
        If a numeric version is needed, use 'babase.App.build_number'.
        """
        assert isinstance(self._env['version'], str)
        return self._env['version']

    @property
    def debug_build(self) -> bool:
        """Whether the app was compiled in debug mode.

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
    def data_directory(self) -> str:
        """Path where static app data lives."""
        assert isinstance(self._env['data_directory'], str)
        return self._env['data_directory']

    @property
    def python_directory_user(self) -> str | None:
        """Path where ballistica expects its custom user scripts (mods) to live.

        Be aware that this value may be None if ballistica is running in
        a non-standard environment, and that python-path modifications may
        cause modules to be loaded from other locations.
        """
        assert isinstance(self._env['python_directory_user'], (str, type(None)))
        return self._env['python_directory_user']

    @property
    def python_directory_app(self) -> str | None:
        """Path where ballistica expects its bundled modules to live.

        Be aware that this value may be None if ballistica is running in
        a non-standard environment, and that python-path modifications may
        cause modules to be loaded from other locations.
        """
        assert isinstance(self._env['python_directory_app'], (str, type(None)))
        return self._env['python_directory_app']

    @property
    def python_directory_app_site(self) -> str | None:
        """Path where ballistica expects its bundled pip modules to live.

        Be aware that this value may be None if ballistica is running in
        a non-standard environment, and that python-path modifications may
        cause modules to be loaded from other locations.
        """
        assert isinstance(
            self._env['python_directory_app_site'], (str, type(None))
        )
        return self._env['python_directory_app_site']

    @property
    def config(self) -> babase.AppConfig:
        """The babase.AppConfig instance representing the app's config state."""
        assert self._config is not None
        return self._config

    @property
    def api_version(self) -> int:
        """The app's api version.

        Only Python modules and packages associated with the current API
        version number will be detected by the game (see the ba_meta tag).
        This value will change whenever substantial backward-incompatible
        changes are introduced to ballistica APIs. When that happens,
        modules/packages should be updated accordingly and set to target
        the newer API version number.
        """
        from babase._meta import CURRENT_API_VERSION

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

    def __init__(self) -> None:
        """(internal)

        Do not instantiate this class; use babase.app to access
        the single shared instance.
        """

        self.state = self.State.INITIAL

        self._app_bootstrapping_complete = False
        self._called_on_app_launching = False
        self._launch_completed = False
        self._initial_sign_in_completed = False
        self._meta_scan_completed = False
        self._called_on_app_loading = False
        self._called_on_app_running = False
        self._app_paused = False

        # Config.
        self.config_file_healthy = False

        # This is incremented any time the app is backgrounded/foregrounded;
        # can be a simple way to determine if network data should be
        # refreshed/etc.
        self.fg_state = 0

        self._aioloop: asyncio.AbstractEventLoop | None = None

        self._env = _babase.env()
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

        # Default executor which can be used for misc background processing.
        # It should also be passed to any additional asyncio loops we create
        # so that everything shares the same single set of worker threads.
        self.threadpool = ThreadPoolExecutor(thread_name_prefix='baworker')

        self._config: babase.AppConfig | None = None

        self.components = AppComponentSubsystem()
        self.meta = MetadataSubsystem()
        self.plugins = PluginSubsystem()
        self.lang = LanguageSubsystem()
        self.net = NetworkSubsystem()
        self.workspaces = WorkspaceSubsystem()
        # self._classic: ClassicSubsystem | None = None

        self._asyncio_timer: babase.AppTimer | None = None

    def postinit(self) -> None:
        """Called after we are inited and assigned to babase.app."""

        # NOTE: the reason we need a postinit here is that
        # some of this stuff might try importing babase.app and that doesn't
        # exist yet as of our __init__() call.

        # Init classic if present.
        # classic_subsystem_type: type[ClassicSubsystem] | None
        # try:
        #     from baclassic import ClassicSubsystem

        #     classic_subsystem_type = ClassicSubsystem
        # except ImportError:
        #     classic_subsystem_type = None

        # if classic_subsystem_type is not None:
        #     self._classic = classic_subsystem_type()

    # Would autogen this begin

    @cached_property
    def classic(self) -> ClassicSubsystem | None:
        """Our classic subsystem."""

        try:
            from baclassic import ClassicSubsystem

            return ClassicSubsystem()
        except ImportError:
            return None
        except Exception:
            logging.exception('Error importing baclassic')
            return None

    @cached_property
    def plus(self) -> PlusSubsystem | None:
        """Our plus subsystem."""

        try:
            from baplus import PlusSubsystem

            return PlusSubsystem()
        except ImportError:
            return None
        except Exception:
            logging.exception('Error importing baplus')
            return None

    # Would autogen this begin

    def run(self) -> None:
        """Run the app to completion.

        Note that this only works on platforms where ballistica
        manages its own event loop.
        """
        _babase.run_app()

    def on_app_launching(self) -> None:
        """Called when the app is first entering the launching state."""
        # pylint: disable=cyclic-import
        from babase import _asyncio
        from babase import _appconfig
        from babase._apputils import log_dumped_app_state, AppHealthMonitor

        assert _babase.in_logic_thread()

        self._aioloop = _asyncio.setup_asyncio()
        self.health_monitor = AppHealthMonitor()

        # Only proceed if our config file is healthy so we don't
        # overwrite a broken one or whatnot and wipe out data.
        if not self.config_file_healthy:
            if self.classic is not None:
                handled = self.classic.show_config_error_window()
                if handled:
                    return

            # For now on other systems we just overwrite the bum config.
            # At this point settings are already set; lets just commit them
            # to disk.
            _appconfig.commit_app_config(force=True)

        # Get meta-system scanning built-in stuff in the bg.
        self.meta.start_scan(scan_complete_cb=self.on_meta_scan_complete)

        self.accounts.on_app_launching()

        # Make sure this runs after we init our accounts stuff, since
        # classic accounts key off of our v2 ones.
        if self.classic is not None:
            self.classic.on_app_launching()

        # If any traceback dumps happened last run, log and clear them.
        log_dumped_app_state()

        self._launch_completed = True
        self._update_state()

    def on_app_loading(self) -> None:
        """Called when initially entering the loading state."""

    def on_app_running(self) -> None:
        """Called when initially entering the running state."""

        self.plugins.on_app_running()

    def on_app_bootstrapping_complete(self) -> None:
        """Called by the C++ layer once its ready to rock."""
        assert _babase.in_logic_thread()
        assert not self._app_bootstrapping_complete
        self._app_bootstrapping_complete = True
        self._update_state()

    def on_meta_scan_complete(self) -> None:
        """Called by meta-scan when it is done doing its thing."""
        assert _babase.in_logic_thread()
        self.plugins.on_meta_scan_complete()

        assert not self._meta_scan_completed
        self._meta_scan_completed = True
        self._update_state()

    def _update_state(self) -> None:
        # pylint: disable=too-many-branches
        assert _babase.in_logic_thread()

        if self._app_paused:
            # Entering paused state:
            if self.state is not self.State.PAUSED:
                self.state = self.State.PAUSED
                self.on_app_pause()
        else:
            # Leaving paused state:
            if self.state is self.State.PAUSED:
                self.on_app_resume()

            # Handle initially entering or returning to other states.
            if self._initial_sign_in_completed and self._meta_scan_completed:
                if self.state != self.State.RUNNING:
                    self.state = self.State.RUNNING
                    _babase.bootlog('app state running')
                    if not self._called_on_app_running:
                        self._called_on_app_running = True
                        self.on_app_running()
            elif self._launch_completed:
                if self.state is not self.State.LOADING:
                    self.state = self.State.LOADING
                    _babase.bootlog('app state loading')
                    if not self._called_on_app_loading:
                        self._called_on_app_loading = True
                        self.on_app_loading()
            else:
                # Only thing left is launching. We shouldn't be getting
                # called before at least that is complete.
                assert self._app_bootstrapping_complete
                if self.state is not self.State.LAUNCHING:
                    self.state = self.State.LAUNCHING
                    _babase.bootlog('app state launching')
                    if not self._called_on_app_launching:
                        self._called_on_app_launching = True
                        self.on_app_launching()

    def pause(self) -> None:
        """Should be called by the native layer when the app pauses."""
        assert not self._app_paused  # Should avoid redundant calls.
        self._app_paused = True
        self._update_state()

    def resume(self) -> None:
        """Should be called by the native layer when the app resumes."""
        assert self._app_paused  # Should avoid redundant calls.
        self._app_paused = False
        self._update_state()

    def on_app_pause(self) -> None:
        """Called when the app goes to a paused state."""
        self.cloud.on_app_pause()
        self.plugins.on_app_pause()
        self.health_monitor.on_app_pause()
        if self.classic is not None:
            self.classic.on_app_pause()

    def on_app_resume(self) -> None:
        """Called when resuming."""
        self.fg_state += 1
        self.cloud.on_app_resume()
        self.plugins.on_app_resume()
        self.health_monitor.on_app_resume()
        if self.classic is not None:
            self.classic.on_app_resume()

    def on_app_shutdown(self) -> None:
        """(internal)"""
        self.state = self.State.SHUTTING_DOWN
        self.plugins.on_app_shutdown()
        if self.classic is not None:
            self.classic.on_app_shutdown()

    def read_config(self) -> None:
        """(internal)"""
        from babase._appconfig import read_config

        self._config, self.config_file_healthy = read_config()

    def handle_deep_link(self, url: str) -> None:
        """Handle a deep link URL."""
        from babase._language import Lstr

        appname = _babase.appname()
        if url.startswith(f'{appname}://code/'):
            code = url.replace(f'{appname}://code/', '')
            if self.classic is not None:
                self.classic.accounts.add_pending_promo_code(code)
        else:
            try:
                _babase.screenmessage(
                    Lstr(resource='errorText'), color=(1, 0, 0)
                )
                _babase.getsimplesound('error').play()
            except ImportError:
                pass

    def on_initial_sign_in_completed(self) -> None:
        """Callback to be run after initial sign-in (or lack thereof).

        This period includes things such as syncing account workspaces
        or other data so it may take a substantial amount of time.
        This should also run after a short amount of time if no login
        has occurred.
        """
        # Tell meta it can start scanning extra stuff that just showed up
        # (account workspaces).
        self.meta.start_extra_scan()

        self._initial_sign_in_completed = True
        self._update_state()
