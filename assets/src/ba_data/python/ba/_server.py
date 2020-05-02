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
"""Functionality related to running the game in server-mode."""
from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING

from efro.terminal import Clr
from ba._enums import TimeType
from ba._freeforallsession import FreeForAllSession
from ba._dualteamsession import DualTeamSession
from bacommon.servermanager import ServerConfig, ServerCommand
import _ba

if TYPE_CHECKING:
    from typing import Optional, Dict, Any, Type
    import ba


def _cmd(command_data: bytes) -> None:
    """Handle commands coming in from the server manager."""
    import pickle
    command, payload = pickle.loads(command_data)
    assert isinstance(command, ServerCommand)

    # We expect to receive a config command to kick things off.
    if command is ServerCommand.CONFIG:
        assert isinstance(payload, ServerConfig)
        assert _ba.app.server is None
        _ba.app.server = ServerController(payload)
        return

    assert _ba.app.server is not None
    print('WOULD DO OTHER SERVER COMMAND')


class ServerController:
    """Overall controller for the app in server mode.

    Category: App Classes
    """

    def __init__(self, config: ServerConfig) -> None:

        self._config = config
        self._playlist_name = '__default__'
        self._ran_access_check = False
        self._run_server_wait_timer: Optional[ba.Timer] = None
        self._next_stuck_login_warn_time = time.time() + 10.0
        self._first_run = True

        # Make note if they want us to import a playlist;
        # we'll need to do that first if so.
        self._playlist_fetch_running = self._config.playlist_code is not None
        self._playlist_fetch_sent_request = False
        self._playlist_fetch_got_response = False
        self._playlist_fetch_code = -1

        self._config_server()

        # Now sit around until we're signed in and then
        # kick off the server.
        with _ba.Context('ui'):
            self._run_server_wait_timer = _ba.Timer(
                0.25,
                self._update_server_playlist_fetch,
                timetype=TimeType.REAL,
                repeat=True)

    def launch_server_session(self) -> None:
        """Kick off a host-session based on the current server config."""
        app = _ba.app
        appcfg = app.config

        sessiontype = self._get_session_type()

        if _ba.get_account_state() != 'signed_in':
            print('WARNING: launch_server_session() expects to run '
                  'with a signed in server account')

        if self._first_run:
            print((('BallisticaCore '
                    if app.headless_build else 'BallisticaCore ') +
                   str(app.version) + ' (' + str(app.build_number) +
                   ') entering server-mode ' + time.strftime('%c')))

        appcfg['Show Tutorial'] = False

        if sessiontype is FreeForAllSession:
            appcfg['Free-for-All Playlist Selection'] = self._playlist_name
            appcfg['Free-for-All Playlist Randomize'] = (
                self._config.playlist_shuffle)
        elif sessiontype is DualTeamSession:
            appcfg['Team Tournament Playlist Selection'] = self._playlist_name
            appcfg['Team Tournament Playlist Randomize'] = (
                self._config.playlist_shuffle)
        else:
            raise RuntimeError(f'Unknown session type {sessiontype}')

        appcfg['Port'] = self._config.port

        # Set series lengths.
        app.teams_series_length = self._config.teams_series_length
        app.ffa_series_length = self._config.ffa_series_length

        # And here we go.
        _ba.new_host_session(sessiontype)

        if not self._ran_access_check:
            self._run_access_check()
            self._ran_access_check = True

    def handle_transition(self) -> bool:
        """Handle transitioning to a new ba.Session or quitting the app.

        Will be called once at the end of an activity that is marked as
        a good 'end-point' (such as a final score screen).
        Should return True if action will be handled by us; False if the
        session should just continue on it's merry way.
        """
        print('FIXME: fill out server handle_transition()')
        # If the app is in server mode and this activity
        # if self._allow_server_transition and _ba.app.server_config_dirty:
        #     from ba import _server
        #     from ba._lang import Lstr
        #     from ba._general import Call
        #     from ba._enums import TimeType
        #     if _ba.app.server_config.get('quit', False):
        #         if not self._kicked_off_server_shutdown:
        #             if _ba.app.server_config.get(
        #                     'quit_reason') == 'restarting':
        #                 # FIXME: Should add a server-screen-message call
        #                 #  or something.
        #                 _ba.chat_message(
        #                     Lstr(resource='internal.serverRestartingText').
        #                     evaluate())
        #                 print(('Exiting for server-restart at ' +
        #                        time.strftime('%c')))
        #             else:
        #                 print(('Exiting for server-shutdown at ' +
        #                        time.strftime('%c')))
        #             with _ba.Context('ui'):
        #                 _ba.timer(2.0, _ba.quit, timetype=TimeType.REAL)
        #             self._kicked_off_server_shutdown = True
        #             return True
        #     else:
        #         if not self._kicked_off_server_restart:
        #             print(('Running updated server config at ' +
        #                    time.strftime('%c')))
        #             with _ba.Context('ui'):
        #                 _ba.timer(1.0,
        #                           Call(_ba.pushcall,
        #                                _server.launch_server_session),
        #                           timetype=TimeType.REAL)
        #             self._kicked_off_server_restart = True
        #             return True
        return False

    def _get_session_type(self) -> Type[ba.Session]:

        # Convert string session type to the class.
        # Hmm should we just keep this as a string?
        if self._config.session_type == 'ffa':
            return FreeForAllSession
        if self._config.session_type == 'teams':
            return DualTeamSession
        raise RuntimeError(
            f'Invalid session_type: "{self._config.session_type}"')

    def _update_server_playlist_fetch(self) -> None:

        signed_in = _ba.get_account_state() == 'signed_in'

        if not signed_in:

            # Signing in to the local server account should not take long;
            # complain if it does...
            curtime = time.time()
            if curtime > self._next_stuck_login_warn_time:
                print('Still waiting for account sign-in...')
                self._next_stuck_login_warn_time = curtime + 10.0
        else:
            can_launch = False

            # If we're trying to fetch a playlist, we do that first.
            if self._playlist_fetch_running:

                # Send request if we haven't.
                if not self._playlist_fetch_sent_request:

                    print(f'Requesting shared-playlist'
                          f' {self._config.playlist_code}...')

                    _ba.add_transaction(
                        {
                            'type': 'IMPORT_PLAYLIST',
                            'code': str(self._config.playlist_code),
                            'overwrite': True
                        },
                        callback=self._on_playlist_fetch_response)
                    _ba.run_transactions()

                    self._playlist_fetch_sent_request = True

                # If we got a valid result, forget the fetch ever
                # existed and move on.
                if self._playlist_fetch_got_response:
                    self._playlist_fetch_running = False
                    can_launch = True
            else:
                can_launch = True

            if can_launch:
                self._run_server_wait_timer = None
                _ba.pushcall(self.launch_server_session)

    def _on_playlist_fetch_response(
        self,
        result: Optional[Dict[str, Any]],
    ) -> None:
        if result is None:
            print('Error fetching playlist;' ' aborting.')
            sys.exit(-1)

        # Once we get here we simply modify our
        # config to use this playlist.
        type_name = (
            'teams' if result['playlistType'] == 'Team Tournament' else
            'ffa' if result['playlistType'] == 'Free-for-All' else '??')
        print(('Playlist \'' + result['playlistName'] + '\' (' + type_name +
               ') downloaded; running...'))

        self._playlist_fetch_got_response = True
        self._config.session_type = type_name
        self._playlist_name = (result['playlistName'])

    def _run_access_check(self) -> None:
        """Check with the master server to see if we're likely joinable."""
        from ba._netutils import serverget
        serverget(
            'bsAccessCheck',
            {
                'port': _ba.get_game_port(),
                'b': _ba.app.build_number
            },
            callback=self._access_check_response,
        )

    def _access_check_response(self, data: Optional[Dict[str, Any]]) -> None:
        gameport = _ba.get_game_port()
        if data is None:
            print('error on UDP port access check (internet down?)')
        else:
            if data['accessible']:
                print(f'{Clr.SGRN}UDP port {gameport} access check successful.'
                      f' Your server appears to be joinable from the'
                      f' internet.{Clr.RST}')
            else:
                print(f'{Clr.SRED}UDP port {gameport} access check failed.'
                      f' Your server does not appear to be joinable'
                      f' from the internet.{Clr.RST}')

    def _config_server(self) -> None:
        """Apply server config changes that can take effect immediately.

        (party name, etc)
        """

        _ba.app.config['Auto Balance Teams'] = (
            self._config.auto_balance_teams)

        _ba.set_public_party_max_size(self._config.max_party_size)
        _ba.set_public_party_name(self._config.party_name)
        _ba.set_public_party_stats_url(self._config.stats_url)

        # Call set-enabled last (will push state to the cloud).
        _ba.set_public_party_enabled(self._config.party_is_public)
