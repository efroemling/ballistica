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
"""Functionality related to the server manager script."""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Optional, Any, Tuple
    from typing_extensions import Literal


@dataclass
class ServerConfig:
    """Configuration for the server manager script."""

    # Name of our server in the public parties list.
    party_name: str = 'FFA'

    # If True, your party will show up in the global public party list
    # Otherwise it will still be joinable via LAN or connecting by IP address.
    party_is_public: bool = True

    # UDP port to host on. Change this to work around firewalls or run multiple
    # servers on one machine.
    # 43210 is the default and the only port that will show up in the LAN
    # browser tab.
    port: int = 43210

    # Max devices in the party. Note that this does *NOT* mean max players.
    # Any device in the party can have more than one player on it if they have
    # multiple controllers. Also, this number currently includes the server so
    # generally make it 1 bigger than you need. Max-players is not currently
    # exposed but I'll try to add that soon.
    max_party_size: int = 6

    # Options here are 'ffa' (free-for-all) and 'teams'
    # This value is only used if you do not supply a playlist_code (see below).
    # In that case the default teams or free-for-all playlist gets used.
    session_type: str = 'ffa'

    # To host your own custom playlists, use the 'share' functionality in the
    # playlist editor in the regular version of the game.
    # This will give you a numeric code you can enter here to host that
    # playlist.
    playlist_code: Optional[int] = None

    # Whether to shuffle the playlist or play its games in designated order.
    playlist_shuffle: bool = True

    # If True, keeps team sizes equal by disallowing joining the largest team
    # (teams mode only).
    auto_balance_teams: bool = True

    # Whether to enable telnet access.
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
    enable_telnet: bool = False

    # Port used for telnet.
    telnet_port: int = 43250

    # This can be None for no password but PLEASE do not expose that to the
    # world or your machine will likely get owned.
    telnet_password: Optional[str] = 'changeme'

    # Series length in teams mode (7 == 'best-of-7' series; a team must
    # get 4 wins)
    teams_series_length: int = 7

    # Points to win in free-for-all mode (Points are awarded per game based on
    # performance)
    ffa_series_length: int = 24

    # If you provide a custom stats webpage for your server, you can use
    # this to provide a convenient in-game link to it in the server-browser
    # beside the server name.
    # if ${ACCOUNT} is present in the string, it will be replaced by the
    # currently-signed-in account's id. To fetch info about an account,
    # your backend server can use the following url:
    # http://bombsquadgame.com/accountquery?id=ACCOUNT_ID_HERE
    stats_url: Optional[str] = None

    # FIXME REMOVE
    quit: bool = False

    # FIXME REMOVE
    quit_reason: Optional[str] = None


# NOTE: as much as possible, communication from the server-manager to the
# child binary should go through this and not ad-hoc python string commands
# since this way is type safe.
class ServerCommand(Enum):
    """Command types that can be sent to the app in server-mode."""
    CONFIG = 'config'
    QUIT = 'quit'


@overload
def make_server_command(command: Literal[ServerCommand.CONFIG],
                        payload: ServerConfig) -> bytes:
    """Overload for CONFIG commands."""
    ...


@overload
def make_server_command(command: Literal[ServerCommand.QUIT],
                        payload: int) -> bytes:
    """Overload for QUIT commands."""
    ...


def make_server_command(command: ServerCommand, payload: Any) -> bytes:
    """Create a command that can be exec'ed on the server binary."""
    import pickle

    # Pickle this stuff down to bytes and wrap it in a command to
    # extract/run it on the other end.
    val = repr(pickle.dumps((command, payload)))
    assert '\n' not in val
    return f'import ba._server; ba._server._cmd({val})\n'.encode()


def extract_server_command(cmd: str) -> Tuple[ServerCommand, Any]:
    """Given a server-command string, returns command objects."""

    # Yes, eval is unsafe and all that, but this is only intended
    # for communication between a parent and child process so we
    # can live with it here.
    print('would extract', cmd)
    return ServerCommand.CONFIG, None
