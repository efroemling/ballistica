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
"""Functionality for running a BallisticaCore server."""
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
    from typing import Optional, List
    from types import FrameType


class App:
    """Runs a BallisticaCore server.

    Handles passing config values to the game and periodically restarting
    the game binary to keep things fresh.
    """

    def __init__(self) -> None:

        # We actually run from the 'dist' subdir.
        if not os.path.isdir('dist'):
            raise RuntimeError('"dist" directory not found.')
        os.chdir('dist')

        self._binary_path = self._get_binary_path()
        self._config = ServerConfig()

        # Print basic usage info in interactive mode.
        if sys.stdin.isatty():
            print('BallisticaCore server manager starting up...')

        self._input_commands: List[str] = []

        # The server-binary will get relaunched after this amount of time
        # (combats memory leaks or other cruft that has built up).
        self._restart_minutes = 360.0

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

    def _read_input(self) -> None:
        """Read from stdin and queue results for the app to handle."""
        while True:
            line = sys.stdin.readline()
            self._input_commands.append(line.strip())

    def run_interactive(self) -> None:
        """Run the app loop to completion."""
        import code
        import signal

        # Python will handle SIGINT for us (as KeyboardInterrupt) but we
        # need to register a SIGTERM handler if we want a chance to clean
        # up our child process when someone tells us to die. (and avoid
        # zombie processes)
        signal.signal(signal.SIGTERM, self._handle_term_signal)

        # Fire off a background thread to wrangle our server binaries.
        bgthread = threading.Thread(target=self._bg_thread_main)
        bgthread.start()

        # Now just sit in an interpreter.
        try:
            code.interact(banner='', exitmsg='')
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

    def _bg_thread_main(self) -> None:
        while not self._done:
            self._run_server_cycle()

    def _handle_term_signal(self, sig: int, frame: FrameType) -> None:
        """Handle signals (will always run in the main thread)."""
        del sig, frame  # Unused.
        raise SystemExit()

    def _run_server_cycle(self) -> None:
        """Bring up the server binary and run it until exit."""

        self._setup_process_config()

        # Launch the binary and grab its stdin;
        # we'll use this to feed it commands.
        self._process_launch_time = time.time()

        # We don't want our subprocess to respond to Ctrl-C; we want to handle
        # that ourself. So we need to do a bit of magic to accomplish that.
        args = [self._binary_path, '-cfgdir', 'ba_root']
        if sys.platform.startswith('win'):
            # https://msdn.microsoft.com/en-us/library/windows/
            # desktop/ms684863(v=vs.85).aspx
            # CREATE_NEW_PROCESS_GROUP=0x00000200 -> If this flag is
            # specified, CTRL+C signals will be disabled
            self._process = subprocess.Popen(args,
                                             stdin=subprocess.PIPE,
                                             creationflags=0x00000200)
        else:
            # Note: Python docs tell us preexec_fn is unsafe with threads.
            # https://docs.python.org/3/library/subprocess.html
            # Perhaps we should just give the ballistica binary itself an
            # option to ignore interrupt signals.
            self._process = subprocess.Popen(  # pylint: disable=W1509
                args,
                stdin=subprocess.PIPE,
                preexec_fn=self._subprocess_pre_exec)

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

    def _subprocess_pre_exec(self) -> None:
        """To ignore CTRL+C signal in the new process."""
        import signal
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def _setup_process_config(self) -> None:
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
            for incmd in self._input_commands:
                print('WOULD PASS ALONG COMMAND', incmd)
            self._input_commands = []

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
    App().run_interactive()
