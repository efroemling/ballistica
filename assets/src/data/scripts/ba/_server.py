"""Functionality related to running the game in server-mode."""
from __future__ import annotations

import copy
import json
import os
import sys
import time
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Optional, Dict, Any, Type
    import ba


def config_server(config_file: str = None) -> None:
    """Run the game in server mode with the provided server config file."""

    from ba._enums import TimeType

    app = _ba.app

    # Read and store the provided server config and then delete the file it
    # came from.
    if config_file is not None:
        with open(config_file) as infile:
            app.server_config = json.loads(infile.read())
        os.remove(config_file)
    else:
        app.server_config = {}

    # Make note if they want us to import a playlist;
    # we'll need to do that first if so.
    playlist_code = app.server_config.get('playlist_code')
    if playlist_code is not None:
        app.server_playlist_fetch = {
            'sent_request': False,
            'got_response': False,
            'playlist_code': str(playlist_code)
        }

    # Apply config stuff that can take effect immediately (party name, etc).
    _config_server()

    # Launch the server only the first time through;
    # after that it will be self-sustaining.
    if not app.launched_server:

        # Now sit around until we're signed in and then kick off the server.
        with _ba.Context('ui'):

            def do_it() -> None:
                if _ba.get_account_state() == 'signed_in':
                    can_launch = False

                    # If we're trying to fetch a playlist, we do that first.
                    if app.server_playlist_fetch is not None:

                        # Send request if we haven't.
                        if not app.server_playlist_fetch['sent_request']:

                            def on_playlist_fetch_response(
                                    result: Optional[Dict[str, Any]]) -> None:
                                if result is None:
                                    print('Error fetching playlist; aborting.')
                                    sys.exit(-1)

                                # Once we get here we simply modify our
                                # config to use this playlist.
                                type_name = (
                                    'teams' if
                                    result['playlistType'] == 'Team Tournament'
                                    else 'ffa' if result['playlistType'] ==
                                    'Free-for-All' else '??')
                                print(('Playlist \'' + result['playlistName'] +
                                       '\' (' + type_name +
                                       ') downloaded; running...'))
                                assert app.server_playlist_fetch is not None
                                app.server_playlist_fetch['got_response'] = (
                                    True)
                                app.server_config['session_type'] = type_name
                                app.server_config['playlist_name'] = (
                                    result['playlistName'])

                            print(('Requesting shared-playlist ' + str(
                                app.server_playlist_fetch['playlist_code']) +
                                   '...'))
                            app.server_playlist_fetch['sent_request'] = True
                            _ba.add_transaction(
                                {
                                    'type':
                                        'IMPORT_PLAYLIST',
                                    'code':
                                        app.
                                        server_playlist_fetch['playlist_code'],
                                    'overwrite':
                                        True
                                },
                                callback=on_playlist_fetch_response)
                            _ba.run_transactions()

                        # If we got a valid result, forget the fetch ever
                        # existed and move on.
                        if app.server_playlist_fetch['got_response']:
                            app.server_playlist_fetch = None
                            can_launch = True
                    else:
                        can_launch = True
                    if can_launch:
                        app.run_server_wait_timer = None
                        _ba.pushcall(launch_server_session)

            app.run_server_wait_timer = _ba.Timer(0.25,
                                                  do_it,
                                                  timetype=TimeType.REAL,
                                                  repeat=True)
        app.launched_server = True


def launch_server_session() -> None:
    """Kick off a host-session based on the current server config."""
    from ba._netutils import serverget
    from ba import _freeforallsession
    from ba import _teamssession
    app = _ba.app
    servercfg = copy.deepcopy(app.server_config)
    appcfg = app.config

    # Convert string session type to the class.
    # Hmm should we just keep this as a string?
    session_type_name = servercfg.get('session_type', 'ffa')
    sessiontype: Type[ba.Session]
    if session_type_name == 'ffa':
        sessiontype = _freeforallsession.FreeForAllSession
    elif session_type_name == 'teams':
        sessiontype = _teamssession.TeamsSession
    else:
        raise Exception('invalid session_type value: ' + session_type_name)

    if _ba.get_account_state() != 'signed_in':
        print('WARNING: launch_server_session() expects to run '
              'with a signed in server account')

    if app.run_server_first_run:
        print((('BallisticaCore headless '
                if app.subplatform == 'headless' else 'BallisticaCore ') +
               str(app.version) + ' (' + str(app.build_number) +
               ') entering server-mode ' + time.strftime('%c')))

    playlist_shuffle = servercfg.get('playlist_shuffle', True)
    appcfg['Show Tutorial'] = False
    appcfg['Free-for-All Playlist Selection'] = (servercfg.get(
        'playlist_name', '__default__') if session_type_name == 'ffa' else
                                                 '__default__')
    appcfg['Free-for-All Playlist Randomize'] = playlist_shuffle
    appcfg['Team Tournament Playlist Selection'] = (servercfg.get(
        'playlist_name', '__default__') if session_type_name == 'teams' else
                                                    '__default__')
    appcfg['Team Tournament Playlist Randomize'] = playlist_shuffle
    appcfg['Port'] = servercfg.get('port', 43210)

    # Set series lengths.
    app.teams_series_length = servercfg.get('teams_series_length', 7)
    app.ffa_series_length = servercfg.get('ffa_series_length', 24)

    # And here we go.
    _ba.new_host_session(sessiontype)

    # Also lets fire off an access check if this is our first time
    # through (and they want a public party).
    if app.run_server_first_run:

        def access_check_response(data: Optional[Dict[str, Any]]) -> None:
            gameport = _ba.get_game_port()
            if data is None:
                print('error on UDP port access check (internet down?)')
            else:
                if data['accessible']:
                    print('UDP port', gameport,
                          ('access check successful. Your '
                           'server appears to be joinable '
                           'from the internet.'))
                else:
                    print('UDP port', gameport,
                          ('access check failed. Your server '
                           'does not appear to be joinable '
                           'from the internet.'))

        port = _ba.get_game_port()
        serverget('bsAccessCheck', {
            'port': port,
            'b': app.build_number
        },
                  callback=access_check_response)
    app.run_server_first_run = False
    app.server_config_dirty = False


def _config_server() -> None:
    """Apply server config changes that can take effect immediately.

    (party name, etc)
    """
    config = copy.deepcopy(_ba.app.server_config)

    # FIXME: Should make a proper low level config entry for this or
    #  else not store in in app.config. Probably shouldn't be going through
    #  the app config for this anyway since it should just be for this run.
    _ba.app.config['Auto Balance Teams'] = (config.get('auto_balance_teams',
                                                       True))

    _ba.set_public_party_max_size(config.get('max_party_size', 9))
    _ba.set_public_party_name(config.get('party_name', 'party'))
    _ba.set_public_party_stats_url(config.get('stats_url', ''))

    # Call set-enabled last (will push state).
    _ba.set_public_party_enabled(config.get('party_is_public', True))

    if not _ba.app.run_server_first_run:
        print('server config updated.')

    # FIXME: We could avoid setting this as dirty if the only changes have
    #  been ones here we can apply immediately. Could reduce cases where
    #  players have to rejoin.
    _ba.app.server_config_dirty = True
