#!/usr/bin/env python3.12
# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""BallisticaKit server manager."""
from __future__ import annotations

import os
import sys
import time
import json
import signal
import tomllib
import logging
import subprocess
from pathlib import Path
from threading import Lock, Thread, current_thread
from typing import TYPE_CHECKING

# We make use of the bacommon and efro packages as well as site-packages
# included with our bundled Ballistica dist, so we need to add those
# paths before we import them.
sys.path += [
    str(Path(Path(__file__).parent, 'dist', 'ba_data', 'python')),
    str(Path(Path(__file__).parent, 'dist', 'ba_data', 'python-site-packages')),
]

from bacommon.servermanager import ServerConfig, StartServerModeCommand
from efro.dataclassio import dataclass_from_dict, dataclass_validate
from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from types import FrameType
    from bacommon.servermanager import ServerCommand

VERSION_STR = '1.3.3'

# Version history:
#
# 1.3.3
#
#  - Added log_levels dict in server config for setting levels on
#    individual loggers within the server binary. Can be useful for
#    debugging issues or just keeping better track of what the server is
#    up to. Check the logging tab in the dev console in the graphical
#    client to learn which loggers are available.
#
# 1.3.2
#
#  - Updated to use Python 3.12.
#
#  - Server config file is now in toml format instead of yaml.
#
#  - Server config can now be set to a .json file OR a .toml file.
#    By default it will look for 'config.json' and then 'config.toml'
#    in the same dir as this script.
#
# 1.3.1
#
#  - Windows binary is now named 'BallisticaKitHeadless.exe'.
#
# 1.3:
#
#  - Added show_tutorial config option.
#
#  - Added team_names config option.
#
#  - Added team_colors config option.
#
#  - Added playlist_inline config option.
#
# 1.2:
#
#  - Added optional --help arg.
#
#  - Added --config arg for specifying config file and --root for
#    ba_root path.
#
#  - Added noninteractive mode and --interactive/--noninteractive args
#    to explicitly enable/disable it (it is autodetected by default).
#
#  - Added explicit control for auto-restart: --no-auto-restart.
#
#  - Config file is now reloaded each time server binary is restarted;
#    no more need to bring down server wrapper to pick up changes.
#
#  - Now automatically restarts server binary when config file is
#    modified (use --no-config-auto-restart to disable that behavior).
#
# 1.1.1:
#
#  - Switched config reading to use
#    efro.dataclasses.dataclass_from_dict().
#
# 1.1.0:
#
#  - Added shutdown command.
#
#  - Changed restart to default to immediate=True.
#
#  - Added clean_exit_minutes, unclean_exit_minutes, and idle_exit_minutes.
#
# 1.0.0:
#
#  - Initial release.


class ServerManagerApp:
    """An app which manages BallisticaKit server execution.

    Handles configuring, launching, re-launching, and otherwise
    managing BallisticaKit operating in server mode.
    """

    # How many seconds we wait after asking our subprocess to do an immediate
    # shutdown before bringing down the hammer.
    IMMEDIATE_SHUTDOWN_TIME_LIMIT = 5.0

    def __init__(self) -> None:
        self._user_provided_config_path: str | None = None
        self._config = ServerConfig()
        self._ba_root_path = os.path.abspath('dist/ba_root')
        self._interactive = sys.stdin.isatty()
        self._wrapper_shutdown_desired = False
        self._done = False
        self._subprocess_commands: list[str | ServerCommand] = []
        self._subprocess_commands_lock = Lock()
        self._subprocess_force_kill_time: float | None = None
        self._auto_restart = True
        self._config_auto_restart = True
        self._config_mtime: float | None = None
        self._last_config_mtime_check_time: float | None = None
        self._should_report_subprocess_error = False
        self._running = False
        self._interpreter_start_time: float | None = None
        self._subprocess: subprocess.Popen[bytes] | None = None
        self._subprocess_launch_time: float | None = None
        self._subprocess_sent_config_auto_restart = False
        self._subprocess_sent_clean_exit = False
        self._subprocess_sent_unclean_exit = False
        self._subprocess_thread: Thread | None = None
        self._subprocess_exited_cleanly: bool | None = None
        self._did_multi_config_warning = False

        # This may override the above defaults.
        self._parse_command_line_args()

        # Do an initial config-load. If the config is invalid at this
        # point we can cleanly die; we're more resilient later on reload
        # attempts.
        self.load_config(strict=True, print_confirmation=False)

    @property
    def config(self) -> ServerConfig:
        """The current config for the app."""
        return self._config

    @config.setter
    def config(self, value: ServerConfig) -> None:
        dataclass_validate(value)
        self._config = value

    def _prerun(self) -> None:
        """Common code at the start of any run."""

        # Make sure we don't call run multiple times.
        if self._running:
            raise RuntimeError('Already running.')
        self._running = True

        dbgstr = 'debug' if __debug__ else 'opt'
        print(
            f'{Clr.CYN}{Clr.BLD}BallisticaKit server manager {VERSION_STR}'
            f' starting up ({dbgstr} mode)...{Clr.RST}',
            flush=True,
        )

        # Python will handle SIGINT for us (as KeyboardInterrupt) but we
        # need to register a SIGTERM handler so we have a chance to
        # clean up our subprocess when someone tells us to die. (and
        # avoid zombie processes)
        signal.signal(signal.SIGTERM, self._handle_term_signal)

        # During a run, we make the assumption that cwd is the dir
        # containing this script, so make that so. Up until now that may
        # not be the case (we support being called from any location).
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

        # Fire off a background thread to wrangle our server binaries.
        self._subprocess_thread = Thread(target=self._bg_thread_main)
        self._subprocess_thread.start()

    def _postrun(self) -> None:
        """Common code at the end of any run."""
        print(f'{Clr.CYN}Server manager shutting down...{Clr.RST}', flush=True)

        assert self._subprocess_thread is not None
        if self._subprocess_thread.is_alive():
            print(
                f'{Clr.CYN}Waiting for subprocess exit...{Clr.RST}', flush=True
            )

        # Mark ourselves as shutting down and wait for the process to
        # wrap up.
        self._done = True
        self._subprocess_thread.join()

        # If there's a server error we should care about, exit the
        # entire wrapper uncleanly.
        if self._should_report_subprocess_error:
            raise CleanError('Server subprocess exited uncleanly.')

    def run(self) -> None:
        """Do the thing."""
        if self._interactive:
            self._run_interactive()
        else:
            self._run_noninteractive()

    def _run_noninteractive(self) -> None:
        """Run the app loop to completion noninteractively."""
        self._prerun()
        try:
            while True:
                time.sleep(1.234)
        except KeyboardInterrupt:
            # Gracefully bow out if we kill ourself via keyboard.
            pass
        except SystemExit:
            # We get this from the builtin quit(), our signal handler,
            # etc. Need to catch this so we can clean up, otherwise
            # we'll be left in limbo with our process thread still
            # running.
            pass
        self._postrun()

    def _run_interactive(self) -> None:
        """Run the app loop to completion interactively."""
        import code

        self._prerun()

        # Print basic usage info for interactive mode.
        print(
            f"{Clr.CYN}Interactive mode enabled; use the 'mgr' object"
            f' to interact with the server.\n'
            f"Type 'help(mgr)' for more information.{Clr.RST}",
            flush=True,
        )

        context = {'__name__': '__console__', '__doc__': None, 'mgr': self}

        # Enable tab-completion if possible.
        self._enable_tab_completion(context)

        # Now just sit in an interpreter.
        #
        # TODO: make it possible to use IPython if the user has it
        # available.
        try:
            self._interpreter_start_time = time.time()
            code.interact(local=context, banner='', exitmsg='')
        except SystemExit:
            # We get this from the builtin quit(), our signal handler,
            # etc. Need to catch this so we can clean up, otherwise
            # we'll be left in limbo with our process thread still
            # running.
            pass
        except BaseException as exc:
            print(
                f'{Clr.SRED}Unexpected interpreter exception:'
                f' {exc} ({type(exc)}){Clr.RST}',
                flush=True,
            )

        self._postrun()

    def cmd(self, statement: str) -> None:
        """Exec a Python command on the current running server subprocess.

        Note that commands are executed asynchronously and no status or
        return value is accessible from this manager app.
        """
        if not isinstance(statement, str):
            raise TypeError(f'Expected a string arg; got {type(statement)}')
        with self._subprocess_commands_lock:
            self._subprocess_commands.append(statement)
        self._block_for_command_completion()

    def _block_for_command_completion(self) -> None:
        # Ideally we'd block here until the command was run so our
        # prompt would print after it's results. We currently don't get
        # any response from the app so the best we can do is block until
        # our bg thread has sent it. In the future we can perhaps add a
        # proper 'command port' interface for proper blocking two way
        # communication.
        while True:
            with self._subprocess_commands_lock:
                if not self._subprocess_commands:
                    break
            time.sleep(0.1)

        # One last short delay so if we come out *just* as the command
        # is sent we'll hopefully still give it enough time to
        # process/print.
        time.sleep(0.1)

    def screenmessage(
        self,
        message: str,
        color: tuple[float, float, float] | None = None,
        clients: list[int] | None = None,
    ) -> None:
        """Display a screen-message.

        This will have no name attached and not show up in chat history.
        They will show up in replays, however (unless clients is passed).
        """
        from bacommon.servermanager import ScreenMessageCommand

        self._enqueue_server_command(
            ScreenMessageCommand(message=message, color=color, clients=clients)
        )

    def chatmessage(
        self, message: str, clients: list[int] | None = None
    ) -> None:
        """Send a chat message from the server.

        This will have the server's name attached and will be logged
        in client chat windows, just like other chat messages.
        """
        from bacommon.servermanager import ChatMessageCommand

        self._enqueue_server_command(
            ChatMessageCommand(message=message, clients=clients)
        )

    def clientlist(self) -> None:
        """Print a list of connected clients."""
        from bacommon.servermanager import ClientListCommand

        self._enqueue_server_command(ClientListCommand())
        self._block_for_command_completion()

    def kick(self, client_id: int, ban_time: int | None = None) -> None:
        """Kick the client with the provided id.

        If ban_time is provided, the client will be banned for that
        length of time in seconds. If it is None, ban duration will
        be determined automatically. Pass 0 or a negative number for no
        ban time.
        """
        from bacommon.servermanager import KickCommand

        self._enqueue_server_command(
            KickCommand(client_id=client_id, ban_time=ban_time)
        )

    def restart(self, immediate: bool = True) -> None:
        """Restart the server subprocess.

        By default, the current server process will exit immediately.
        If 'immediate' is passed as False, however, it will instead exit at
        the next clean transition point (the end of a series, etc).
        """
        from bacommon.servermanager import ShutdownCommand, ShutdownReason

        self._enqueue_server_command(
            ShutdownCommand(
                reason=ShutdownReason.RESTARTING, immediate=immediate
            )
        )

        # If we're asking for an immediate restart but don't get one
        # within the grace period, bring down the hammer.
        if immediate:
            self._subprocess_force_kill_time = (
                time.time() + self.IMMEDIATE_SHUTDOWN_TIME_LIMIT
            )

    def shutdown(self, immediate: bool = True) -> None:
        """Shut down the server subprocess and exit the wrapper.

        By default, the current server process will exit immediately.
        If 'immediate' is passed as False, however, it will instead exit at
        the next clean transition point (the end of a series, etc).
        """
        from bacommon.servermanager import ShutdownCommand, ShutdownReason

        self._enqueue_server_command(
            ShutdownCommand(reason=ShutdownReason.NONE, immediate=immediate)
        )

        # An explicit shutdown means we know to bail completely once
        # this subprocess completes.
        self._wrapper_shutdown_desired = True

        # If we're asking for an immediate shutdown but don't get one
        # within the grace period, bring down the hammer.
        if immediate:
            self._subprocess_force_kill_time = (
                time.time() + self.IMMEDIATE_SHUTDOWN_TIME_LIMIT
            )

    def _parse_command_line_args(self) -> None:
        """Parse command line args."""
        # pylint: disable=too-many-branches

        i = 1
        argc = len(sys.argv)
        did_set_interactive = False
        while i < argc:
            arg = sys.argv[i]
            if arg == '--help':
                self.print_help()
                sys.exit(0)
            elif arg == '--config':
                if i + 1 >= argc:
                    raise CleanError('Expected a config path as next arg.')
                path = sys.argv[i + 1]
                if not os.path.exists(path):
                    raise CleanError(f"Supplied path does not exist: '{path}'.")
                # We need an abs path because we may be in a different
                # cwd currently than we will be during the run.
                self._user_provided_config_path = os.path.abspath(path)
                i += 2
            elif arg == '--root':
                if i + 1 >= argc:
                    raise CleanError('Expected a path as next arg.')
                path = sys.argv[i + 1]
                # Unlike config_path, this one doesn't have to exist
                # now. We do however need an abs path because we may be
                # in a different cwd currently than we will be during
                # the run.
                self._ba_root_path = os.path.abspath(path)
                i += 2
            elif arg == '--interactive':
                if did_set_interactive:
                    raise CleanError(
                        'interactive/noninteractive can only'
                        ' be specified once.'
                    )
                self._interactive = True
                did_set_interactive = True
                i += 1
            elif arg == '--noninteractive':
                if did_set_interactive:
                    raise CleanError(
                        'interactive/noninteractive can only'
                        ' be specified once.'
                    )
                self._interactive = False
                did_set_interactive = True
                i += 1
            elif arg == '--no-auto-restart':
                self._auto_restart = False
                i += 1
            elif arg == '--no-config-auto-restart':
                self._config_auto_restart = False
                i += 1
            else:
                raise CleanError(f"Invalid arg: '{arg}'.")

    @classmethod
    def _par(cls, txt: str) -> str:
        """Spit out a pretty paragraph for our help text."""
        import textwrap

        ind = ' ' * 2
        out = textwrap.fill(txt, 80, initial_indent=ind, subsequent_indent=ind)
        return f'{out}\n'

    @classmethod
    def print_help(cls) -> None:
        """Print app help."""
        filename = os.path.basename(__file__)
        out = (
            f'{Clr.BLD}{filename} usage:{Clr.RST}\n'
            + cls._par(
                'This script handles configuring, launching, re-launching,'
                ' and otherwise managing BallisticaKit operating'
                ' in server mode. It can be run with no arguments, but'
                ' accepts the following optional ones:'
            )
            + f'\n'
            f'{Clr.BLD}--help:{Clr.RST}\n'
            f'  Show this help.\n'
            f'\n'
            f'{Clr.BLD}--config [path]{Clr.RST}\n'
            + cls._par(
                'Set the config file read by the server script. The config'
                ' file contains most options for what kind of game to host.'
                ' It should be in toml or json format. If not specified,'
                ' the script will look for a file named \'config.toml\' or'
                ' \'config.json\' in the same directory as the script.'
            )
            + '\n'
            f'{Clr.BLD}--root [path]{Clr.RST}\n'
            + cls._par(
                'Set the ballistica root directory. This is where the server'
                ' binary will read and write its caches, state files,'
                ' downloaded assets to, etc. It needs to be a writable'
                ' directory. If not specified, the script will use the'
                ' \'dist/ba_root\' directory relative to itself.'
            )
            + '\n'
            f'{Clr.BLD}--interactive{Clr.RST}\n'
            f'{Clr.BLD}--noninteractive{Clr.RST}\n'
            + cls._par(
                'Specify whether the script should run interactively.'
                ' In interactive mode, the script creates a Python interpreter'
                ' and reads commands from stdin, allowing for live interaction'
                ' with the server. The server script will then exit when '
                'end-of-file is reached in stdin. Noninteractive mode creates'
                ' no interpreter and is more suited to being run in automated'
                ' scenarios. By default, interactive mode will be used if'
                ' a terminal is detected and noninteractive mode otherwise.'
            )
            + '\n'
            f'{Clr.BLD}--no-auto-restart{Clr.RST}\n'
            + cls._par(
                'Auto-restart is enabled by default, which means the'
                ' server manager will restart the server binary whenever'
                ' it exits (even when uncleanly). Disabling auto-restart'
                ' will cause the server manager to instead exit after a'
                ' single run and also to return error codes if the'
                ' server binary did so.'
            )
            + '\n'
            f'{Clr.BLD}--no-config-auto-restart{Clr.RST}\n'
            + cls._par(
                'By default, when auto-restart is enabled, the server binary'
                ' will be automatically restarted if changes to the server'
                ' config file are detected. This disables that behavior.'
            )
        )
        print(out)

    def load_config(self, strict: bool, print_confirmation: bool) -> None:
        """Load the config.

        If strict is True, errors will propagate upward.
        Otherwise, warnings will be printed and repeated attempts will be
        made to load the config. Eventually the function will give up
        and leave the existing config as-is.
        """
        retry_seconds = 3
        maxtries = 11
        for trynum in range(maxtries):
            try:
                self._config = self._load_config_from_file(
                    print_confirmation=print_confirmation
                )
                return
            except Exception as exc:
                if strict:
                    raise CleanError(
                        f'Error loading config file:\n{exc}'
                    ) from exc
                print(
                    f'{Clr.RED}Error loading config file:\n{exc}.{Clr.RST}',
                    flush=True,
                )
                if trynum == maxtries - 1:
                    print(
                        f'{Clr.RED}Max-tries reached; giving up.'
                        f' Existing config values will be used.{Clr.RST}',
                        flush=True,
                    )
                    break
                print(
                    f'{Clr.CYN}Please correct the error.'
                    f' Will re-attempt load in {retry_seconds}'
                    f' seconds. (attempt {trynum+1} of'
                    f' {maxtries-1}).{Clr.RST}',
                    flush=True,
                )

                for _j in range(retry_seconds):
                    # If the app is trying to die, drop what we're doing.
                    if self._done:
                        return
                    time.sleep(1)

    def _get_config_path(self) -> str:

        if self._user_provided_config_path is not None:
            return self._user_provided_config_path

        # Otherwise look for config.toml or config.json in the same dir
        # as our script. Need to work in abs paths since we may chdir when
        # we start running.
        toml_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'config.toml')
        )
        toml_exists = os.path.exists(toml_path)
        json_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'config.json')
        )
        json_exists = os.path.exists(json_path)

        # Warn if both configs are present.
        if toml_exists and json_exists and not self._did_multi_config_warning:
            self._did_multi_config_warning = True
            print(
                f'{Clr.YLW}Both config.toml and config.json'
                f' found; will use json.{Clr.RST}',
                flush=True,
            )
        if json_exists:
            return json_path
        return toml_path

    def _load_config_from_file(self, print_confirmation: bool) -> ServerConfig:
        out: ServerConfig | None = None

        config_path = self._get_config_path()

        if not os.path.exists(config_path):
            # Special case:
            #
            # If the user didn't provide a config path AND the default
            # config path does not exist, fall back to defaults.
            if not self._user_provided_config_path:
                if print_confirmation:
                    print(
                        f'{Clr.YLW}Default config file not found'
                        f' (\'{config_path}\'); using default'
                        f' config.{Clr.RST}',
                        flush=True,
                    )
                self._config_mtime = None
                self._last_config_mtime_check_time = time.time()
                return ServerConfig()

            # Don't be so lenient if the user pointed us at one though.
            raise RuntimeError(f"Config file not found: '{config_path}'.")

        with open(config_path, encoding='utf-8') as infile:
            if config_path.endswith('.toml'):
                user_config_raw = tomllib.loads(infile.read())
            elif config_path.endswith('.json'):
                user_config_raw = json.loads(infile.read())
            else:
                raise CleanError(
                    f"Invalid config file path '{config_path}';"
                    f" path must end with '.toml' or '.json'."
                )

        out = dataclass_from_dict(ServerConfig, user_config_raw)

        # Update our known mod-time since we know it exists.
        self._config_mtime = Path(config_path).stat().st_mtime
        self._last_config_mtime_check_time = time.time()

        if print_confirmation:
            print(
                f'{Clr.CYN}Valid server config file loaded.{Clr.RST}',
                flush=True,
            )
        return out

    def _enable_tab_completion(self, locs: dict) -> None:
        """Enable tab-completion on platforms where available (linux/mac)."""
        try:
            import readline
            import rlcompleter

            readline.set_completer(rlcompleter.Completer(locs).complete)
            readline.parse_and_bind('tab:complete')
        except ImportError:
            # This is expected (readline doesn't exist under windows).
            pass

    def _bg_thread_main(self) -> None:
        """Top level method run by our bg thread."""
        while not self._done:
            self._run_server_cycle()

    def _handle_term_signal(self, sig: int, frame: FrameType | None) -> None:
        """Handle signals (will always run in the main thread)."""
        del sig, frame  # Unused.
        sys.exit(1 if self._should_report_subprocess_error else 0)

    def _run_server_cycle(self) -> None:
        """Spin up the server subprocess and run it until exit."""
        # pylint: disable=consider-using-with

        # Reload our config, and update our overall behavior based on
        # it. We do non-strict this time to give the user repeated
        # attempts if if they mess up while modifying the config on the
        # fly.
        self.load_config(strict=False, print_confirmation=True)

        self._prep_subprocess_environment()

        # Launch the binary and grab its stdin; we'll use this to feed
        # it commands.
        self._subprocess_launch_time = time.time()

        # Set an environment var so the server process knows its being
        # run under us. This causes it to ignore ctrl-c presses and
        # other slight behavior tweaks. Hmm; should this be an argument
        # instead?
        os.environ['BA_SERVER_WRAPPER_MANAGED'] = '1'

        # Set an environment var to change the device name. Device name
        # is used while making connection with master server,
        # cloud-console recognize us with this name.
        os.environ['BA_DEVICE_NAME'] = self._config.party_name

        print(f'{Clr.CYN}Launching server subprocess...{Clr.RST}', flush=True)
        binary_name = (
            'BallisticaKitHeadless.exe'
            if os.name == 'nt'
            else './ballisticakit_headless'
        )
        assert self._ba_root_path is not None
        self._subprocess = None

        # Launch!
        try:
            self._subprocess = subprocess.Popen(
                [binary_name, '--config-dir', self._ba_root_path],
                stdin=subprocess.PIPE,
                cwd='dist',
            )
        except Exception as exc:
            self._subprocess_exited_cleanly = False
            print(
                f'{Clr.RED}Error launching server subprocess: {exc}{Clr.RST}',
                flush=True,
            )

        # Do the thing.
        try:
            self._run_subprocess_until_exit()
        except Exception as exc:
            print(
                f'{Clr.RED}Error running server subprocess: {exc}{Clr.RST}',
                flush=True,
            )

        self._kill_subprocess()

        assert self._subprocess_exited_cleanly is not None

        # EW: it seems that if we die before the main thread has fully
        # started up the interpreter, its possible that it will not
        # break out of its loop via the usual SystemExit that gets sent
        # when we die.
        if self._interactive:
            while (
                self._interpreter_start_time is None
                or time.time() - self._interpreter_start_time < 0.5
            ):
                time.sleep(0.1)

        # Avoid super fast death loops.
        if (
            not self._subprocess_exited_cleanly
            and self._auto_restart
            and not self._done
        ):
            time.sleep(5.0)

        # If they don't want auto-restart, we'll exit the whole wrapper.
        # (and with an error code if things ended badly).
        if not self._auto_restart:
            self._wrapper_shutdown_desired = True
            if not self._subprocess_exited_cleanly:
                self._should_report_subprocess_error = True

        self._reset_subprocess_vars()

        # If we want to die completely after this subprocess has ended,
        # tell the main thread to die.
        if self._wrapper_shutdown_desired:
            # Only do this if the main thread is not already waiting for
            # us to die; otherwise it can lead to deadlock. (we hang in
            # os.kill while main thread is blocked in Thread.join)
            if not self._done:
                self._done = True

                # This should break the main thread out of its blocking
                # interpreter call.
                os.kill(os.getpid(), signal.SIGTERM)

    def _prep_subprocess_environment(self) -> None:
        """Write files that must exist at process launch."""

        assert self._ba_root_path is not None
        os.makedirs(self._ba_root_path, exist_ok=True)
        cfgpath = os.path.join(self._ba_root_path, 'config.json')
        if os.path.exists(cfgpath):
            with open(cfgpath, encoding='utf-8') as infile:
                bincfg = json.loads(infile.read())
        else:
            bincfg = {}

        # Some of our config values translate directly into the
        # ballisticakit config file; the rest we pass at runtime.

        # IMPORTANT: Make sure we *ALWAYS* push values (or lack thereof)
        # through; otherwise stale values from previous runs can linger
        # in the bincfg.

        bincfg['Port'] = self._config.port
        bincfg['Auto Balance Teams'] = self._config.auto_balance_teams
        bincfg['Show Tutorial'] = self._config.show_tutorial

        binkey = 'SceneV1 Host Protocol'
        if self._config.protocol_version is not None:
            bincfg[binkey] = self._config.protocol_version
        elif binkey in bincfg:
            del bincfg[binkey]

        binkey = 'Custom Team Names'
        if self._config.team_names is not None:
            bincfg[binkey] = self._config.team_names
        elif binkey in bincfg:
            del bincfg[binkey]

        binkey = 'Custom Team Colors'
        if self._config.team_colors is not None:
            bincfg[binkey] = self._config.team_colors
        elif binkey in bincfg:
            del bincfg[binkey]

        bincfg['Idle Exit Minutes'] = self._config.idle_exit_minutes

        binkey = 'Log Levels'
        if self._config.log_levels is not None:
            # Users supply us log level names like NOTSET; convert those
            # to numeric vals which the engine expects.
            bincfg[binkey] = {
                key: logging.getLevelName(val)
                for key, val in self._config.log_levels.items()
            }
        elif binkey in bincfg:
            del bincfg[binkey]

        with open(cfgpath, 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(bincfg))

    def _enqueue_server_command(self, command: ServerCommand) -> None:
        """Enqueue a command to be sent to the server.

        Can be called from any thread.
        """
        with self._subprocess_commands_lock:
            self._subprocess_commands.append(command)

    def _send_server_command(self, command: ServerCommand) -> None:
        """Send a command to the server.

        Must be called from the server process thread.
        """
        import pickle

        assert current_thread() is self._subprocess_thread
        assert self._subprocess is not None
        assert self._subprocess.stdin is not None
        val = repr(pickle.dumps(command))
        assert '\n' not in val
        execcode = (
            f'import baclassic._servermode;'
            f' baclassic._servermode._cmd({val})\n'
        ).encode()
        self._subprocess.stdin.write(execcode)
        self._subprocess.stdin.flush()

    def _run_subprocess_until_exit(self) -> None:
        if self._subprocess is None:
            return

        assert current_thread() is self._subprocess_thread
        assert self._subprocess.stdin is not None

        # Send the initial server config which should kick things off
        # (but make sure its values are still valid first).
        dataclass_validate(self._config)
        self._send_server_command(StartServerModeCommand(self._config))

        while True:
            # If the app is trying to shut down, nope out immediately.
            if self._done:
                break

            # Pass along any commands to our process.
            with self._subprocess_commands_lock:
                for incmd in self._subprocess_commands:
                    # If we're passing a raw string to exec, no need to
                    # wrap it in any proper structure.
                    if isinstance(incmd, str):
                        self._subprocess.stdin.write((incmd + '\n').encode())
                        self._subprocess.stdin.flush()
                    else:
                        self._send_server_command(incmd)
                self._subprocess_commands = []

            # Request restarts/shut-downs for various reasons.
            self._request_shutdowns_or_restarts()

            # If they want to force-kill our subprocess, simply exit
            # this loop; the cleanup code will kill the process if its
            # still alive.
            if (
                self._subprocess_force_kill_time is not None
                and time.time() > self._subprocess_force_kill_time
            ):
                print(
                    f'{Clr.CYN}Immediate shutdown time limit'
                    f' ({self.IMMEDIATE_SHUTDOWN_TIME_LIMIT:.1f} seconds)'
                    f' expired; force-killing subprocess...{Clr.RST}',
                    flush=True,
                )
                break

            # Watch for the server process exiting..
            code: int | None = self._subprocess.poll()
            if code is not None:
                clr = Clr.CYN if code == 0 else Clr.RED
                print(
                    f'{clr}Server subprocess exited'
                    f' with code {code}.{Clr.RST}',
                    flush=True,
                )
                self._subprocess_exited_cleanly = code == 0
                break

            time.sleep(0.25)

    def _request_shutdowns_or_restarts(self) -> None:
        # pylint: disable=too-many-branches
        assert current_thread() is self._subprocess_thread
        assert self._subprocess_launch_time is not None
        now = time.time()
        minutes_since_launch = (now - self._subprocess_launch_time) / 60.0

        # If we're doing auto-restart with config changes, handle that.
        if (
            self._auto_restart
            and self._config_auto_restart
            and not self._subprocess_sent_config_auto_restart
        ):
            if (
                self._last_config_mtime_check_time is None
                or (now - self._last_config_mtime_check_time) > 3.123
            ):
                self._last_config_mtime_check_time = now
                mtime: float | None
                config_path = self._get_config_path()
                if os.path.isfile(config_path):
                    mtime = Path(config_path).stat().st_mtime
                else:
                    mtime = None
                if mtime != self._config_mtime:
                    print(
                        f'{Clr.CYN}Config-file change detected;'
                        f' requesting immediate restart.{Clr.RST}',
                        flush=True,
                    )
                    self.restart(immediate=True)
                    self._subprocess_sent_config_auto_restart = True

        # Attempt clean exit if our clean-exit-time passes (and enforce
        # a 6 hour max if not provided).
        clean_exit_minutes = 360.0
        if self._config.clean_exit_minutes is not None:
            clean_exit_minutes = min(
                clean_exit_minutes, self._config.clean_exit_minutes
            )
        if clean_exit_minutes is not None:
            if (
                minutes_since_launch > clean_exit_minutes
                and not self._subprocess_sent_clean_exit
            ):
                opname = 'restart' if self._auto_restart else 'shutdown'
                print(
                    f'{Clr.CYN}clean_exit_minutes'
                    f' ({clean_exit_minutes})'
                    f' elapsed; requesting soft'
                    f' {opname}.{Clr.RST}',
                    flush=True,
                )
                if self._auto_restart:
                    self.restart(immediate=False)
                else:
                    self.shutdown(immediate=False)
                self._subprocess_sent_clean_exit = True

        # Attempt unclean exit if our unclean-exit-time passes (and
        # enforce a 7 hour max if not provided).
        unclean_exit_minutes = 420.0
        if self._config.unclean_exit_minutes is not None:
            unclean_exit_minutes = min(
                unclean_exit_minutes, self._config.unclean_exit_minutes
            )
        if unclean_exit_minutes is not None:
            if (
                minutes_since_launch > unclean_exit_minutes
                and not self._subprocess_sent_unclean_exit
            ):
                opname = 'restart' if self._auto_restart else 'shutdown'
                print(
                    f'{Clr.CYN}unclean_exit_minutes'
                    f' ({unclean_exit_minutes})'
                    f' elapsed; requesting immediate'
                    f' {opname}.{Clr.RST}',
                    flush=True,
                )
                if self._auto_restart:
                    self.restart(immediate=True)
                else:
                    self.shutdown(immediate=True)
                self._subprocess_sent_unclean_exit = True

    def _reset_subprocess_vars(self) -> None:
        self._subprocess = None
        self._subprocess_launch_time = None
        self._subprocess_sent_config_auto_restart = False
        self._subprocess_sent_clean_exit = False
        self._subprocess_sent_unclean_exit = False
        self._subprocess_force_kill_time = None
        self._subprocess_exited_cleanly = None

    def _kill_subprocess(self) -> None:
        """End the server subprocess if it still exists."""
        assert current_thread() is self._subprocess_thread
        if self._subprocess is None:
            return

        print(f'{Clr.CYN}Stopping subprocess...{Clr.RST}', flush=True)

        # First, ask it nicely to die and give it a moment. If that
        # doesn't work, bring down the hammer.
        self._subprocess.terminate()
        try:
            self._subprocess.wait(timeout=10)
            self._subprocess_exited_cleanly = self._subprocess.returncode == 0
        except subprocess.TimeoutExpired:
            self._subprocess_exited_cleanly = False
            self._subprocess.kill()
        print(f'{Clr.CYN}Subprocess stopped.{Clr.RST}', flush=True)


def main() -> None:
    """Run the BallisticaKit server manager."""
    try:
        ServerManagerApp().run()
    except CleanError as exc:
        # For clean errors, do a simple print and fail; no
        # tracebacks/etc. Any others will bubble up and give us the
        # usual mess.
        exc.pretty_print()
        sys.exit(1)


if __name__ == '__main__':
    main()
