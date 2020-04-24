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

        # Launch a thread to listen for input
        # (in daemon mode so it won't prevent us from dying)
        self._input_commands: List[str] = []
        thread = threading.Thread(target=self._read_input)
        thread.daemon = True
        thread.start()

        # Print basic usage info in interactive mode.
        if sys.stdin.isatty():
            print("BallisticaCore Server wrapper starting up...")

        # The server-binary will get relaunched after this amount of time
        # (combats memory leaks or other cruft that has built up).
        self._restart_minutes = 360.0

        self._process: Optional[subprocess.Popen[bytes]] = None
        self._process_launch_time: Optional[float] = None

        # The standard python exit/quit help messages don't apply here
        # so let's get rid of them.
        del __builtins__.exit
        del __builtins__.quit

    def _get_binary_path(self) -> str:
        """Locate the game binary we'll run."""
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
            print('read line', line)
            self._input_commands.append(line.strip())

    def run(self) -> None:
        """Run the app loop to completion."""

        # We currently never stop until explicitly killed.
        while True:
            self._run_server_cycle()

    def _run_server_cycle(self) -> None:
        """Bring up the server binary and run it until exit."""

        self._setup_process_config()

        # Launch the binary and grab its stdin;
        # we'll use this to feed it commands.
        self._process_launch_time = time.time()
        self._process = subprocess.Popen(
            [self._binary_path, '-cfgdir', 'ba_root'], stdin=subprocess.PIPE)

        # Set quit to True any time after launching the server
        # to gracefully quit it at the next clean opportunity
        # (the end of the current series, etc).
        self._config.quit = False
        self._config.quit_reason = None

        # Do the thing.
        # If we hit ANY Exceptions (including KeyboardInterrupt),
        # we want to kill the server binary, so we need to catch BaseException.
        try:
            self._run_process_until_exit()
        except BaseException:
            self._kill_process()
            raise

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

        # Now just sleep and run commands until the process exits.
        while True:

            # Pass along any commands that have come in through stdin.
            for incmd in self._input_commands:
                print("WOULD PASS ALONG COMMAND", incmd)
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
                print('Server process exited with code ' + str(code))
                self._process = None
                self._process_launch_time = None
                break

            time.sleep(0.25)

    def _kill_process(self) -> None:
        """Forcefully end the server process."""
        print("Stopping server process...")
        assert self._process is not None

        # First, ask it nicely to die and give it a moment.
        # If that doesn't work, bring down the hammer.
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
        print("Server process stopped.")


if __name__ == '__main__':
    try:
        App().run()
    except KeyboardInterrupt:
        pass
