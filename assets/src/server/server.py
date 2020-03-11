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

import copy
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any, Sequence


def _get_default_config() -> Dict[str, Any]:
    # Config values are initialized with defaults here.
    # You an add your own overrides in config.py.
    # noinspection PyDictCreation
    config: Dict[str, Any] = {}

    # Name of our server in the public parties list.
    config['party_name'] = 'FFA'

    # If True, your party will show up in the global public party list
    # Otherwise it will still be joinable via LAN or connecting by IP address.
    config['party_is_public'] = True

    # UDP port to host on. Change this to work around firewalls or run multiple
    # servers on one machine.
    # 43210 is the default and the only port that will show up in the LAN
    # browser tab.
    config['port'] = 43210

    # Max devices in the party. Note that this does *NOT* mean max players.
    # Any device in the party can have more than one player on it if they have
    # multiple controllers. Also, this number currently includes the server so
    # generally make it 1 bigger than you need. Max-players is not currently
    # exposed but I'll try to add that soon.
    config['max_party_size'] = 6

    # Options here are 'ffa' (free-for-all) and 'teams'
    # This value is only used if you do not supply a playlist_code (see below).
    # In that case the default teams or free-for-all playlist gets used.
    config['session_type'] = 'ffa'

    # To host your own custom playlists, use the 'share' functionality in the
    # playlist editor in the regular version of the game.
    # This will give you a numeric code you can enter here to host that
    # playlist.
    config['playlist_code'] = None

    # Whether to shuffle the playlist or play its games in designated order.
    config['playlist_shuffle'] = True

    # If True, keeps team sizes equal by disallowing joining the largest team
    # (teams mode only).
    config['auto_balance_teams'] = True

    # Whether to enable telnet access on port 43250
    # This allows you to run python commands on the server as it is running.
    # Note: you can now also run live commands via stdin so telnet is generally
    # unnecessary. BallisticaCore's telnet server is very simple so you may
    # have to turn off any fancy features in your telnet client to get it to
    # work. There is no password protection so make sure to only enable this
    # if access to this port is fully trusted (behind a firewall, etc).
    # IMPORTANT: Telnet is not encrypted at all, so you really should not
    # expose it's port to the world. If you need remote access, consider
    # connecting to your machine via ssh and running telnet to localhost
    # from there.
    config['enable_telnet'] = False

    # Port used for telnet.
    config['telnet_port'] = 43250

    # This can be None for no password but PLEASE do not expose that to the
    # world or your machine will likely get owned.
    config['telnet_password'] = 'changeme'

    # Series length in teams mode (7 == 'best-of-7' series; a team must
    # get 4 wins)
    config['teams_series_length'] = 7

    # Points to win in free-for-all mode (Points are awarded per game based on
    # performance)
    config['ffa_series_length'] = 24

    # If you provide a custom stats webpage for your server, you can use
    # this to provide a convenient in-game link to it in the server-browser
    # beside the server name.
    # if ${ACCOUNT} is present in the string, it will be replaced by the
    # currently-signed-in account's id.  To get info about an account,
    # you can use the following url:
    # http://bombsquadgame.com/accountquery?id=ACCOUNT_ID_HERE
    config['stats_url'] = ''

    return config


def _run_process_until_exit(process: subprocess.Popen,
                            input_commands: Sequence[str],
                            restart_minutes: int, config: Dict[str,
                                                               Any]) -> None:
    # So we pass our initial config.
    config_dirty = True

    launch_time = time.time()

    # Now just sleep and run commands until the server exits.
    while True:

        # Run any commands that came in through stdin.
        for cmd in input_commands:
            print("GOT INPUT COMMAND", cmd)
            old_config = copy.deepcopy(config)
            try:
                print('FIXME: input commands need updating for python 3')
                # exec(cmd)
            except Exception:
                traceback.print_exc()
            if config != old_config:
                config_dirty = True
        input_commands = []

        # Request a restart after a while.
        if (time.time() - launch_time > 60 * restart_minutes
                and not config['quit']):
            print('restart_minutes (' + str(restart_minutes) +
                  'm) elapsed; requesting server restart '
                  'at next clean opportunity...')
            config['quit'] = True
            config['quit_reason'] = 'restarting'
            config_dirty = True

        # Whenever the config changes, dump it to a json file and feed
        # it to the running server.
        # FIXME: We can probably just pass the new config directly
        #  instead of dumping it to a file and passing the path.
        if config_dirty:
            # Note: The game handles deleting this file for us once its
            # done with it.
            ftmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
            fname = ftmp.name
            ftmp.write(json.dumps(config))
            ftmp.close()

            # Note to self: Is there a type-safe way we could do this?
            assert process.stdin is not None
            process.stdin.write(('from ba import _server; '
                                 '_server.config_server(config_file=' +
                                 repr(fname) + ')\n').encode('utf-8'))
            process.stdin.flush()
            config_dirty = False

        code = process.poll()
        if code is not None:
            print('BallisticaCore exited with code ' + str(code))
            break

        time.sleep(1)


def _run_server_cycle(binary_path: str, config: Dict[str, Any],
                      input_commands: Sequence[str],
                      restart_minutes: int) -> None:
    """Bring up the server binary and run it until exit."""

    # Most of our config values we can feed to ballisticacore as it is running
    # (see below). However certain things such as network-port need to be
    # present in the config file at launch, so let's write that out first.
    if not os.path.exists('bacfg'):
        os.mkdir('bacfg')
    if os.path.exists('bacfg/config.json'):
        with open('bacfg/config.json') as infile:
            bacfg = json.loads(infile.read())
    else:
        bacfg = {}
    bacfg['Port'] = config['port']
    bacfg['Enable Telnet'] = config['enable_telnet']
    bacfg['Telnet Port'] = config['telnet_port']
    bacfg['Telnet Password'] = config['telnet_password']
    with open('bacfg/config.json', 'w') as outfile:
        outfile.write(json.dumps(bacfg))

    # Launch our binary and grab its stdin; we'll use this to feed
    # it commands.
    process = subprocess.Popen([binary_path, '-cfgdir', 'bacfg'],
                               stdin=subprocess.PIPE)

    # Set quit to True any time after launching the server to gracefully
    # quit it at the next clean opportunity (end of the current series,
    # etc).
    config['quit'] = False
    config['quit_reason'] = None

    try:
        _run_process_until_exit(process, input_commands, restart_minutes,
                                config)

    # If we hit ANY Exceptions (including KeyboardInterrupt) we want to kill
    # the server binary, so we need to catch BaseException.
    except BaseException:
        print("Killing server binary...")

        # First, ask it nicely to die and give it a moment.
        # If that doesn't work, bring down the hammer.
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Server binary's dead, Jim.")
        raise


def main() -> None:
    """Runs a BallisticaCore server.

    Handles passing config values to the game and periodically restarting
    the game binary to keep things fresh.
    """

    # We expect to be running from the dir where this script lives.
    script_dir = os.path.dirname(sys.argv[0])
    if script_dir != '':
        os.chdir(script_dir)

    config_path = './config.py'
    binary_path = None
    if os.name == 'nt':
        test_paths = 'bs_headless.exe', 'BallisticaCore.exe'
    else:
        test_paths = './bs_headless', './ballisticacore'
    for path in test_paths:
        if os.path.exists(path):
            binary_path = path
            break
    if binary_path is None:
        raise Exception('Unable to locate bs_headless binary.')

    config = _get_default_config()

    # If config.py exists, run it to apply any overrides it wants.
    if os.path.isfile(config_path):
        # pylint: disable=exec-used
        exec(compile(open(config_path).read(), config_path, 'exec'), globals(),
             config)

    # Launch a thread to read our stdin for commands; this lets us modify the
    # server as it runs.
    input_commands = []

    # Print a little spiel in interactive mode (make sure we do this before our
    # thread reads stdin).
    if sys.stdin.isatty():
        print("ballisticacore server wrapper starting up...\n"
              "tip: enter python commands via stdin to "
              "reconfigure the server on the fly:\n"
              "example: config['party_name'] = 'New Party Name'")

    class InputThread(threading.Thread):
        """A thread that just sits around waiting for input from stdin."""

        def run(self) -> None:
            while True:
                line = sys.stdin.readline()
                print('GOT LINE', line)
                input_commands.append(line.strip())

    thread = InputThread()

    # Set daemon mode so this thread's existence won't stop us from dying.
    thread.daemon = True
    thread.start()

    restart_server = True

    # The server-binary will get relaunched after this amount of time
    # (combats memory leaks or other cruft that has built up).
    restart_minutes = 360

    # The standard python exit/quit help messages don't apply here
    # so let's get rid of them.
    del __builtins__.exit
    del __builtins__.quit

    # Sleep for a moment to allow initial stdin data to get through.
    time.sleep(0.25)

    # Restart indefinitely until we're told not to.
    while restart_server:
        _run_server_cycle(binary_path, config, input_commands, restart_minutes)


if __name__ == '__main__':
    main()
