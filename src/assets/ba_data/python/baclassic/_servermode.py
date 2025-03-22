# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to running the game in server-mode."""
from __future__ import annotations

import sys
import time
import logging
from typing import TYPE_CHECKING

from efro.terminal import Clr
from bacommon.servermanager import (
    ServerCommand,
    StartServerModeCommand,
    ShutdownCommand,
    ShutdownReason,
    ChatMessageCommand,
    ScreenMessageCommand,
    ClientListCommand,
    KickCommand,
)
import babase
import bascenev1

if TYPE_CHECKING:
    from typing import Any

    from bacommon.servermanager import ServerConfig


def _cmd(command_data: bytes) -> None:
    """Handle commands coming in from our server manager parent process."""
    import pickle

    assert babase.app.classic is not None

    command = pickle.loads(command_data)
    assert isinstance(command, ServerCommand)

    if isinstance(command, StartServerModeCommand):
        assert babase.app.classic.server is None
        babase.app.classic.server = ServerController(command.config)
        return

    if isinstance(command, ShutdownCommand):
        assert babase.app.classic.server is not None
        babase.app.classic.server.shutdown(
            reason=command.reason, immediate=command.immediate
        )
        return

    if isinstance(command, ChatMessageCommand):
        assert babase.app.classic.server is not None
        bascenev1.chatmessage(command.message, clients=command.clients)
        return

    if isinstance(command, ScreenMessageCommand):
        assert babase.app.classic.server is not None

        # Note: we have to do transient messages if
        # clients is specified, so they won't show up
        # in replays.
        bascenev1.broadcastmessage(
            command.message,
            color=command.color,
            clients=command.clients,
            transient=command.clients is not None,
        )
        return

    if isinstance(command, ClientListCommand):
        assert babase.app.classic.server is not None
        babase.app.classic.server.print_client_list()
        return

    if isinstance(command, KickCommand):
        assert babase.app.classic.server is not None
        babase.app.classic.server.kick(
            client_id=command.client_id, ban_time=command.ban_time
        )
        return

    print(
        f'{Clr.SRED}ERROR: server process'
        f' got unknown command: {type(command)}{Clr.RST}'
    )


class ServerController:
    """Overall controller for the app in server mode."""

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._playlist_name = '__default__'
        self._ran_access_check = False
        self._prep_timer: babase.AppTimer | None = None
        self._next_stuck_login_warn_time = time.time() + 10.0
        self._first_run = True
        self._shutdown_reason: ShutdownReason | None = None
        self._executing_shutdown = False

        # Make note if they want us to import a playlist; we'll need to
        # do that first if so.
        self._playlist_fetch_running = self._config.playlist_code is not None
        self._playlist_fetch_sent_request = False
        self._playlist_fetch_got_response = False
        self._playlist_fetch_code = -1

        # Now sit around doing any pre-launch prep such as waiting for
        # account sign-in or fetching playlists; this will kick off the
        # session once done.
        with babase.ContextRef.empty():
            self._prep_timer = babase.AppTimer(
                0.25, self._prepare_to_serve, repeat=True
            )

    def print_client_list(self) -> None:
        """Print info about all connected clients."""
        import json

        roster = bascenev1.get_game_roster()
        title1 = 'Client ID'
        title2 = 'Account Name'
        title3 = 'Players'
        col1 = 10
        col2 = 16
        out = (
            f'{Clr.BLD}'
            f'{title1:<{col1}} {title2:<{col2}} {title3}'
            f'{Clr.RST}'
        )
        for client in roster:
            if client['client_id'] == -1:
                continue
            spec = json.loads(client['spec_string'])
            name = spec['n']
            players = ', '.join(n['name'] for n in client['players'])
            clientid = client['client_id']
            out += f'\n{clientid:<{col1}} {name:<{col2}} {players}'
        print(out)

    def kick(self, client_id: int, ban_time: int | None) -> None:
        """Kick the provided client id.

        ban_time is provided in seconds.
        If ban_time is None, ban duration will be determined automatically.
        Pass 0 or a negative number for no ban time.
        """

        # FIXME: this case should be handled under the hood.
        if ban_time is None:
            ban_time = 300

        bascenev1.disconnect_client(client_id=client_id, ban_time=ban_time)

    def shutdown(self, reason: ShutdownReason, immediate: bool) -> None:
        """Set the app to quit either now or at the next clean opportunity."""
        self._shutdown_reason = reason
        if immediate:
            print(f'{Clr.SBLU}Immediate shutdown initiated.{Clr.RST}')
            self._execute_shutdown()
        else:
            print(
                f'{Clr.SBLU}Shutdown initiated;'
                f' server process will exit at the next clean opportunity.'
                f'{Clr.RST}'
            )

    def handle_transition(self) -> bool:
        """Handle transitioning to a new bascenev1.Session or quitting the app.

        Will be called once at the end of an activity that is marked as
        a good 'end-point' (such as a final score screen).
        Should return True if action will be handled by us; False if the
        session should just continue on it's merry way.
        """
        if self._shutdown_reason is not None:
            self._execute_shutdown()
            return True
        return False

    def _execute_shutdown(self) -> None:
        if self._executing_shutdown:
            return
        self._executing_shutdown = True
        timestrval = time.strftime('%c')
        if self._shutdown_reason is ShutdownReason.RESTARTING:
            bascenev1.broadcastmessage(
                babase.Lstr(resource='internal.serverRestartingText'),
                color=(1, 0.5, 0.0),
            )
            print(
                f'{Clr.SBLU}Exiting for server-restart'
                f' at {timestrval}.{Clr.RST}'
            )
        else:
            bascenev1.broadcastmessage(
                babase.Lstr(resource='internal.serverShuttingDownText'),
                color=(1, 0.5, 0.0),
            )
            print(
                f'{Clr.SBLU}Exiting for server-shutdown'
                f' at {timestrval}.{Clr.RST}'
            )
        with babase.ContextRef.empty():
            babase.apptimer(2.0, babase.quit)

    def _run_access_check(self) -> None:
        """Check with the master server to see if we're likely joinable."""
        assert babase.app.classic is not None

        babase.app.classic.master_server_v1_get(
            'bsAccessCheck',
            {
                'port': bascenev1.get_game_port(),
                'b': babase.app.env.engine_build_number,
            },
            callback=self._access_check_response,
        )

    def _access_check_response(self, data: dict[str, Any] | None) -> None:
        import os

        if data is None:
            print('error on UDP port access check (internet down?)')
        else:
            addr = data['address']
            port = data['port']
            show_addr = os.environ.get('BA_ACCESS_CHECK_VERBOSE', '0') == '1'
            if show_addr:
                addrstr = f' {addr}'
                poststr = ''
            else:
                addrstr = ''
                poststr = (
                    '\nSet environment variable BA_ACCESS_CHECK_VERBOSE=1'
                    ' for more info.'
                )
            if data['accessible']:
                print(
                    f'{Clr.SBLU}Master server access check of{addrstr}'
                    f' udp port {port} succeeded.\n'
                    f'Your server appears to be'
                    f' joinable from the internet.{poststr}{Clr.RST}'
                )
            else:
                print(
                    f'{Clr.SRED}Master server access check of{addrstr}'
                    f' udp port {port} failed.\n'
                    f'Your server does not appear to be'
                    f' joinable from the internet.{poststr}{Clr.RST}'
                )

    def _prepare_to_serve(self) -> None:
        """Run in a timer to do prep before beginning to serve."""
        plus = babase.app.plus
        assert plus is not None
        signed_in = plus.get_v1_account_state() == 'signed_in'
        if not signed_in:
            # Signing in to the local server account should not take long;
            # complain if it does...
            curtime = time.time()
            if curtime > self._next_stuck_login_warn_time:
                print('Still waiting for account sign-in...')
                self._next_stuck_login_warn_time = curtime + 10.0
            return

        can_launch = False

        # If we're fetching a playlist, we need to do that first.
        if not self._playlist_fetch_running:
            can_launch = True
        else:
            if not self._playlist_fetch_sent_request:
                print(
                    f'{Clr.SBLU}Requesting shared-playlist'
                    f' {self._config.playlist_code}...{Clr.RST}'
                )
                plus.add_v1_account_transaction(
                    {
                        'type': 'IMPORT_PLAYLIST',
                        'code': str(self._config.playlist_code),
                        'overwrite': True,
                    },
                    callback=self._on_playlist_fetch_response,
                )
                plus.run_v1_account_transactions()
                self._playlist_fetch_sent_request = True

            if self._playlist_fetch_got_response:
                self._playlist_fetch_running = False
                can_launch = True

        if can_launch:
            self._prep_timer = None
            babase.pushcall(self._launch_server_session)

    def _on_playlist_fetch_response(
        self,
        result: dict[str, Any] | None,
    ) -> None:
        if result is None:
            print('Error fetching playlist; aborting.')
            sys.exit(-1)

        # Once we get here, simply modify our config to use this playlist.
        typename = (
            'teams'
            if result['playlistType'] == 'Team Tournament'
            else 'ffa' if result['playlistType'] == 'Free-for-All' else '??'
        )
        plistname = result['playlistName']
        print(f'{Clr.SBLU}Got playlist: "{plistname}" ({typename}).{Clr.RST}')
        self._playlist_fetch_got_response = True
        self._config.session_type = typename
        self._playlist_name = result['playlistName']

    def _get_session_type(self) -> type[bascenev1.Session]:
        # Convert string session type to the class.
        # Hmm should we just keep this as a string?
        if self._config.session_type == 'ffa':
            return bascenev1.FreeForAllSession
        if self._config.session_type == 'teams':
            return bascenev1.DualTeamSession
        if self._config.session_type == 'coop':
            return bascenev1.CoopSession
        raise RuntimeError(
            f'Invalid session_type: "{self._config.session_type}"'
        )

    def _launch_server_session(self) -> None:
        """Kick off a host-session based on the current server config."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        app = babase.app
        classic = app.classic
        plus = app.plus
        assert plus is not None
        assert classic is not None
        appcfg = app.config
        sessiontype = self._get_session_type()

        if plus.get_v1_account_state() != 'signed_in':
            print(
                'WARNING: launch_server_session() expects to run '
                'with a signed in server account'
            )

        # If we didn't fetch a playlist but there's an inline one in the
        # server-config, pull it in to the game config and use it.
        if (
            self._config.playlist_code is None
            and self._config.playlist_inline is not None
        ):
            self._playlist_name = 'ServerModePlaylist'
            if sessiontype is bascenev1.FreeForAllSession:
                ptypename = 'Free-for-All'
            elif sessiontype is bascenev1.DualTeamSession:
                ptypename = 'Team Tournament'
            elif sessiontype is bascenev1.CoopSession:
                ptypename = 'Coop'
            else:
                raise RuntimeError(f'Unknown session type {sessiontype}')

            # Need to add this in a transaction instead of just setting
            # it directly or it will get overwritten by the
            # master-server.
            plus.add_v1_account_transaction(
                {
                    'type': 'ADD_PLAYLIST',
                    'playlistType': ptypename,
                    'playlistName': self._playlist_name,
                    'playlist': self._config.playlist_inline,
                }
            )
            plus.run_v1_account_transactions()

        if self._first_run:
            curtimestr = time.strftime('%c')
            startupmsg = (
                f'{Clr.BLD}{Clr.BLU}{babase.appnameupper()}'
                f' {app.env.engine_version}'
                f' ({app.env.engine_build_number})'
                f' entering server-mode {curtimestr}{Clr.RST}'
            )
            logging.info(startupmsg)

        if sessiontype is bascenev1.FreeForAllSession:
            appcfg['Free-for-All Playlist Selection'] = self._playlist_name
            appcfg['Free-for-All Playlist Randomize'] = (
                self._config.playlist_shuffle
            )
        elif sessiontype is bascenev1.DualTeamSession:
            appcfg['Team Tournament Playlist Selection'] = self._playlist_name
            appcfg['Team Tournament Playlist Randomize'] = (
                self._config.playlist_shuffle
            )
        elif sessiontype is bascenev1.CoopSession:
            classic.coop_session_args = {
                'campaign': self._config.coop_campaign,
                'level': self._config.coop_level,
            }
        else:
            raise RuntimeError(f'Unknown session type {sessiontype}')

        appcfg['Teams Series Length'] = self._config.teams_series_length
        appcfg['FFA Series Length'] = self._config.ffa_series_length

        # Deprecated; left here in order to not break mods.
        classic.teams_series_length = self._config.teams_series_length
        classic.ffa_series_length = self._config.ffa_series_length

        bascenev1.set_authenticate_clients(self._config.authenticate_clients)

        bascenev1.set_enable_default_kick_voting(
            self._config.enable_default_kick_voting
        )
        bascenev1.set_admins(self._config.admins)

        # Call set-enabled last (will push state to the cloud).
        bascenev1.set_public_party_max_size(self._config.max_party_size)
        bascenev1.set_public_party_queue_enabled(self._config.enable_queue)
        bascenev1.set_public_party_name(self._config.party_name)
        bascenev1.set_public_party_stats_url(self._config.stats_url)
        bascenev1.set_public_party_public_address_ipv4(
            self._config.public_ipv4_address
        )
        bascenev1.set_public_party_public_address_ipv6(
            self._config.public_ipv6_address
        )

        bascenev1.set_public_party_enabled(self._config.party_is_public)

        bascenev1.set_player_rejoin_cooldown(
            self._config.player_rejoin_cooldown
        )

        bascenev1.set_max_players_override(
            self._config.session_max_players_override
        )

        # And here.. we.. go.
        if self._config.stress_test_players is not None:
            # Special case: run a stress test.
            assert babase.app.classic is not None
            babase.app.classic.run_stress_test(
                playlist_type='Random',
                playlist_name='__default__',
                player_count=self._config.stress_test_players,
                round_duration=30,
            )
        else:
            bascenev1.new_host_session(sessiontype)

        # Run an access check if we're trying to make a public party.
        if not self._ran_access_check and self._config.party_is_public:
            self._run_access_check()
            self._ran_access_check = True
