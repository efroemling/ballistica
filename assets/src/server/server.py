#!/usr/bin/env python3.7
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
"""BallisticaCore server management."""
from __future__ import annotations

import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

# We make use of the bacommon package and site-packages included
# with our bundled Ballistica dist.
sys.path += [
    str(Path(os.getcwd(), 'dist', 'ba_data', 'python')),
    str(Path(os.getcwd(), 'dist', 'ba_data', 'python-site-packages'))
]

from bacommon.serverutils import (ServerConfig, ServerCommand,
                                  make_server_command)

if TYPE_CHECKING:
    from typing import Optional, List, Dict
    from types import FrameType


class ServerManagerApp:
    """An app which manages BallisticaCore server execution.

    Handles configuring, launching, re-launching, and controlling
    BallisticaCore binaries operating in server mode.
    """

    def __init__(self) -> None:

        # We actually run from the 'dist' subdir.
        if not os.path.isdir('dist'):
            raise RuntimeError('"dist" directory not found.')
        os.chdir('dist')

        self._binary_path = self._get_binary_path()
        self._config = ServerConfig()

        self._binary_commands: List[str] = []
        self._binary_commands_lock = threading.Lock()

        # The server-binary will get relaunched after this amount of time
        # (combats memory leaks or other cruft that has built up).
        self._restart_minutes = 360.0

        self._running_interactive = False
        self._done = False
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._process_launch_time: Optional[float] = None

    def _get_binary_path(self) -> str:
        """Locate the game binary that we'll use."""
        if os.name == 'nt':
            test_paths = ['ballisticacore_headless.exe']
        else:
            test_paths = ['./ballisticacore_headless']
        for path in test_paths:
            if os.path.exists(path):
                return path
        raise RuntimeError('Unable to locate ballisticacore_headless binary.')

    def _enable_tab_completion(self, locs: Dict) -> None:
        """Enable tab-completion on platforms where available (linux/mac)."""
        try:
            import readline
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(locs).complete)
            readline.parse_and_bind('tab:complete')
        except ImportError:
            # readline doesn't exist under windows; this is expected.
            pass

    def run_interactive(self) -> None:
        """Run the app loop to completion."""
        import code
        import signal

        if self._running_interactive:
            raise RuntimeError('Already running interactively.')
        self._running_interactive = True

        # Print basic usage info in interactive mode.
        if sys.stdin.isatty():
            print('BallisticaCore server manager starting up...\n'
                  'Use the "mgr" object to make live server adjustments.\n'
                  'Type "help(mgr)" for more information.')

        # Python will handle SIGINT for us (as KeyboardInterrupt) but we
        # need to register a SIGTERM handler if we want a chance to clean
        # up our child process when someone tells us to die. (and avoid
        # zombie processes)
        signal.signal(signal.SIGTERM, self._handle_term_signal)

        # Fire off a background thread to wrangle our server binaries.
        bgthread = threading.Thread(target=self._bg_thread_main)
        bgthread.start()

        # According to Python docs, default locals dict has __name__ set
        # to __console__ and __doc__ set to None; using that as start point.
        # https://docs.python.org/3/library/code.html
        locs = {'__name__': '__console__', '__doc__': None, 'mgr': self}

        # Enable tab-completion if possible.
        self._enable_tab_completion(locs)

        # Now just sit in an interpreter.
        try:
            code.interact(local=locs, banner='', exitmsg='')
        except SystemExit:
            # We get this from the builtin quit(), etc.
            # Need to catch this so we can clean up, otherwise we'll be
            # left in limbo with our BG thread still running.
            pass
        except BaseException as exc:
            print('Got unexpected exception: ', exc)

        # Mark ourselves as shutting down and wait for bgthread to wrap up.
        self._done = True
        bgthread.join()

    def cmd(self, statement: str) -> None:
        """Exec a Python command on the current running server binary.

        Note that commands are executed asynchronously and no status or
        return value is accessible from this manager app.
        """
        if not isinstance(statement, str):
            raise TypeError(f'Expected a string arg; got {type(statement)}')
        with self._binary_commands_lock:
            self._binary_commands.append(statement)

        # Ideally we'd block here until the command was run so our prompt would
        # print after it's results. We currently don't get any response from
        # the app so the best we can do is block until our bg thread has sent
        # it.
        # In the future we can perhaps add a proper 'command port' interface
        # for proper blocking two way communication.
        while True:
            with self._binary_commands_lock:
                if not self._binary_commands:
                    break
            time.sleep(0.1)

        # One last short delay so if we come out *just* as the command is sent
        # we'll hopefully still give it enough time to process/print.
        time.sleep(0.1)

    def _bg_thread_main(self) -> None:
        while not self._done:
            self._run_server_cycle()

    def _handle_term_signal(self, sig: int, frame: FrameType) -> None:
        """Handle signals (will always run in the main thread)."""
        del sig, frame  # Unused.
        raise SystemExit()

    def _run_server_cycle(self) -> None:
        """Bring up the server binary and run it until exit."""

        self._prep_process_environment()

        # Launch the binary and grab its stdin;
        # we'll use this to feed it commands.
        self._process_launch_time = time.time()

        # Set an environment var so the server process knows its being
        # run under us. This causes it to ignore ctrl-c presses and other
        # slight behavior tweaks. Hmm; should this be an argument instead?
        os.environ['BA_SERVER_WRAPPER_MANAGED'] = '1'

        self._process = subprocess.Popen(
            [self._binary_path, '-cfgdir', 'ba_root'], stdin=subprocess.PIPE)

        # Set quit to True any time after launching the server
        # to gracefully quit it at the next clean opportunity
        # (the end of the current series, etc).
        self._config.quit = False
        self._config.quit_reason = None

        # Do the thing.
        # No matter how this ends up, make sure the process is dead after.
        try:
            self._run_process_until_exit()
        finally:
            self._kill_process()

    def _prep_process_environment(self) -> None:
        """Write files that must exist at process launch."""
        os.makedirs('ba_root', exist_ok=True)
        if os.path.exists('ba_root/config.json'):
            with open('ba_root/config.json') as infile:
                bacfg = json.loads(infile.read())
        else:
            bacfg = {}
        bacfg['Port'] = self._config.port
        bacfg['Enable Telnet'] = self._config.enable_telnet
        bacfg['Telnet Port'] = self._config.telnet_port
        bacfg['Telnet Password'] = self._config.telnet_password
        with open('ba_root/config.json', 'w') as outfile:
            outfile.write(json.dumps(bacfg))

    def _run_process_until_exit(self) -> None:
        assert self._process is not None

        # Send the initial server config which should kick things off.
        cmd = make_server_command(ServerCommand.CONFIG, self._config)
        assert self._process.stdin is not None
        self._process.stdin.write(cmd)
        self._process.stdin.flush()

        while True:

            # If the app is trying to shut down, nope out immediately.
            if self._done:
                break

            # Pass along any commands to the subprocess..
            # FIXME add a lock for this...
            with self._binary_commands_lock:
                for incmd in self._binary_commands:
                    # We're passing a raw string to exec; no need to wrap it
                    # in any proper structure.
                    self._process.stdin.write((incmd + '\n').encode())
                    self._process.stdin.flush()
                self._binary_commands = []

            # Request a restart after a while.
            assert self._process_launch_time is not None
            if (time.time() - self._process_launch_time >
                (self._restart_minutes * 60.0) and not self._config.quit):
                print('restart_minutes (' + str(self._restart_minutes) +
                      'm) elapsed; requesting server restart '
                      'at next clean opportunity...')
                self._config.quit = True
                self._config.quit_reason = 'restarting'

            # Watch for the process exiting.
            code: Optional[int] = self._process.poll()
            if code is not None:
                print(f'Server process exited with code {code}.')
                time.sleep(1.0)  # Keep things from moving too fast.
                self._process = self._process_launch_time = None
                break

            time.sleep(0.25)

    def _kill_process(self) -> None:
        """End the server process if it still exists."""
        if self._process is None:
            return

        print('Stopping server process...')

        # First, ask it nicely to die and give it a moment.
        # If that doesn't work, bring down the hammer.
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
        self._process = self._process_launch_time = None
        print('Server process stopped.')


if __name__ == '__main__':
    ServerManagerApp().run_interactive()
